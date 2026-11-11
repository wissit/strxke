"""
STRXKE Apparel Co. - Reusable Shopify Admin API Client
======================================================
Handles OAuth token lifecycle, variant creation and pricing standardization,
staging print masters to public CDN, media gallery management, and storefront accordions.
"""

import os
import time
import base64
import requests
from typing import Dict, List, Optional, Any

from .config import (
    SHOP,
    CLIENT_ID,
    CLIENT_SECRET,
    SHOPIFY_API_VERSION,
    STAGING_PRODUCT_ID,
    SIZE_SPECS,
    CATALOG_VARIANT_IDS,
    build_storefront_body_html,
)


class ShopifyClient:
    def __init__(
        self,
        shop: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        staging_product_id: Optional[str] = None,
    ):
        self.shop = shop or SHOP
        self.client_id = client_id or CLIENT_ID
        self.client_secret = client_secret or CLIENT_SECRET
        self.staging_product_id = str(staging_product_id or STAGING_PRODUCT_ID)
        self.base_url = f"https://{self.shop}.myshopify.com/admin/api/{SHOPIFY_API_VERSION}"
        self.graphql_url = f"https://{self.shop}.myshopify.com/admin/api/{SHOPIFY_API_VERSION}/graphql.json"
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0

    def get_token(self) -> str:
        """Retrieves and caches OAuth access token using client credentials grant."""
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token

        url = f"https://{self.shop}.myshopify.com/admin/oauth/access_token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]
        self._token_expiry = time.time() + 86400 * 0.9  # cache for 21.6 hours
        return self._access_token

    def get_headers(self) -> Dict[str, str]:
        return {
            "X-Shopify-Access-Token": self.get_token(),
            "Content-Type": "application/json",
        }

    # --- Product & Variant Inspection ---

    def get_product(self, product_id: str) -> Dict[str, Any]:
        """Fetches full product details from Shopify REST API."""
        url = f"{self.base_url}/products/{product_id}.json"
        resp = requests.get(url, headers=self.get_headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()["product"]

    def list_variants(self, product_id: str) -> List[Dict[str, Any]]:
        """Returns all variants for a product."""
        p = self.get_product(product_id)
        return p.get("variants", [])

    def create_variant(
        self,
        product_id: str,
        color: str,
        size: str,
        price: str,
        sku: str,
        grams: int,
    ) -> Dict[str, Any]:
        """Creates a single variant on Shopify with inventory_policy='continue'."""
        url = f"{self.base_url}/products/{product_id}/variants.json"
        payload = {
            "variant": {
                "option1": color,
                "option2": size,
                "price": str(price),
                "sku": sku,
                "grams": grams,
                "inventory_policy": "continue",
                "fulfillment_service": "manual",
                "requires_shipping": True,
                "taxable": True,
            }
        }
        resp = requests.post(url, headers=self.get_headers(), json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()["variant"]

    def update_variant(self, variant_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Updates variant properties (price, sku, inventory_policy, etc.)."""
        url = f"{self.base_url}/variants/{variant_id}.json"
        resp = requests.put(url, headers=self.get_headers(), json={"variant": payload}, timeout=30)
        resp.raise_for_status()
        return resp.json()["variant"]

    def ensure_variants(
        self,
        product_id: str,
        colorways: List[str],
        standardize_pricing: bool = True,
    ) -> List[Dict[str, Any]]:
        """Ensures all 7 Comfort Colors 1717 sizes (S-4XL) exist for each colorway in `colorways`.
        Creates missing variants and standardizes pricing, SKU, and inventory_policy='continue'."""
        prod = self.get_product(product_id)
        existing = {(v["option1"], v["option2"]): v for v in prod.get("variants", [])}

        created_count = 0
        updated_count = 0

        for color in colorways:
            for spec in SIZE_SPECS:
                sz = spec["size"]
                cat_vid = CATALOG_VARIANT_IDS[color][sz]
                sku = f"2909954_{cat_vid}"

                if (color, sz) not in existing:
                    new_v = self.create_variant(
                        product_id=product_id,
                        color=color,
                        size=sz,
                        price=spec["price"],
                        sku=sku,
                        grams=spec["grams"],
                    )
                    existing[(color, sz)] = new_v
                    created_count += 1
                    time.sleep(0.3)
                elif standardize_pricing:
                    curr_v = existing[(color, sz)]
                    needs_update = False
                    upd_payload = {"id": curr_v["id"]}

                    if curr_v.get("price") != spec["price"]:
                        upd_payload["price"] = spec["price"]
                        needs_update = True
                    if curr_v.get("inventory_policy") != "continue":
                        upd_payload["inventory_policy"] = "continue"
                        needs_update = True
                    if curr_v.get("sku") != sku:
                        upd_payload["sku"] = sku
                        needs_update = True

                    if needs_update:
                        self.update_variant(curr_v["id"], upd_payload)
                        updated_count += 1
                        time.sleep(0.2)

        refetched = self.list_variants(product_id)
        print(f"[ShopifyClient] Variants synchronized: {len(refetched)} total (+{created_count} created, {updated_count} standardized).")
        return refetched

    # --- Print Master Staging ---

    def stage_print_master(self, file_path: str, alt_text: str, max_retries: int = 3) -> str:
        """Uploads a local master PNG (4500x5400) to the dedicated staging draft product
        to extract a clean, permanent, public https://cdn.shopify.com/... URL for Printful."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Master print file not found at: {file_path}")

        print(f"[ShopifyClient] Staging print master: {os.path.basename(file_path)}...")
        with open(file_path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")

        url = f"{self.base_url}/products/{self.staging_product_id}/images.json"
        payload = {
            "image": {
                "attachment": b64_data,
                "filename": os.path.basename(file_path),
                "alt": alt_text,
            }
        }

        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.post(url, headers=self.get_headers(), json=payload, timeout=(30, 300))
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 10))
                    print(f"[ShopifyClient] Rate limited (429). Retrying in {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                if resp.status_code == 404:
                    print(f"[ShopifyClient] Staging product {self.staging_product_id} returned 404. Creating new staging draft product...")
                    p_resp = requests.post(
                        f"{self.base_url}/products.json",
                        headers=self.get_headers(),
                        json={"product": {"title": "STRXKE Print Master Staging (Do Not Delete)", "status": "draft"}},
                        timeout=30,
                    )
                    if p_resp.status_code in [200, 201]:
                        self.staging_product_id = str(p_resp.json()["product"]["id"])
                        url = f"{self.base_url}/products/{self.staging_product_id}/images.json"
                        print(f"[ShopifyClient] Created replacement staging product: {self.staging_product_id}")
                        continue
                resp.raise_for_status()
                cdn_url = resp.json()["image"]["src"]
                print(f"[ShopifyClient] Staged successfully -> CDN URL: {cdn_url}")
                return cdn_url
            except Exception as e:
                print(f"[ShopifyClient] Upload attempt {attempt}/{max_retries} failed: {e}")
                if attempt == max_retries:
                    raise
                time.sleep(5 * attempt)

    # --- Media Gallery Management ---

    def list_images(self, product_id: str) -> List[Dict[str, Any]]:
        """Returns all media images for a product."""
        url = f"{self.base_url}/products/{product_id}/images.json"
        resp = requests.get(url, headers=self.get_headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()["images"]

    def purge_images(self, product_id: str) -> int:
        """Purges all existing images from a product to prevent CDN thumbnail caching mismatches."""
        images = self.list_images(product_id)
        for img in images:
            url = f"{self.base_url}/products/{product_id}/images/{img['id']}.json"
            requests.delete(url, headers=self.get_headers(), timeout=30)
            time.sleep(0.3)
        print(f"[ShopifyClient] Purged {len(images)} superseded images from product {product_id}.")
        return len(images)

    def upload_image(
        self,
        product_id: str,
        file_path: str,
        position: int,
        alt_text: str,
        variant_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Uploads a cropped 1500x1500 image, sets its gallery position, and links it to matching variants."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")

        with open(file_path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")

        url = f"{self.base_url}/products/{product_id}/images.json"
        payload = {
            "image": {
                "position": position,
                "attachment": b64_data,
                "filename": os.path.basename(file_path),
                "alt": alt_text,
                "variant_ids": variant_ids or [],
            }
        }
        resp = requests.post(url, headers=self.get_headers(), json=payload, timeout=60)
        resp.raise_for_status()
        img = resp.json()["image"]
        print(f"[ShopifyClient] Uploaded Slot {position}: {os.path.basename(file_path)} (ID {img['id']}, linked {len(variant_ids or [])} variants).")
        time.sleep(0.5)
        return img

    # --- Storefront Description & Accordions ---

    def update_accordions(self, product_id: str, lead_paragraph_html: str) -> None:
        """Injects the canonical Care & Laundering + Comfort Colors 1717 Sizing accordions."""
        full_body = build_storefront_body_html(lead_paragraph_html)
        url = f"{self.base_url}/products/{product_id}.json"
        payload = {"product": {"id": product_id, "body_html": full_body}}
        resp = requests.put(url, headers=self.get_headers(), json=payload, timeout=30)
        resp.raise_for_status()
        print(f"[ShopifyClient] Updated product {product_id} body_html with canonical accordions.")

    # --- Inventory Verification ---

    def verify_inventory(self, product_id: str) -> Dict[str, Any]:
        """Queries variant availability and quantity via GraphQL to guarantee zero strikethroughs."""
        gql = """
        query($id: ID!) {
          product(id: $id) {
            title
            variants(first: 100) {
              nodes {
                id
                title
                availableForSale
                inventoryQuantity
                inventoryPolicy
              }
            }
          }
        }
        """
        resp = requests.post(
            self.graphql_url,
            headers=self.get_headers(),
            json={"query": gql, "variables": {"id": f"gid://shopify/Product/{product_id}"}},
            timeout=30,
        )
        resp.raise_for_status()
        variants = resp.json()["data"]["product"]["variants"]["nodes"]
        in_stock_count = sum(1 for v in variants if v["availableForSale"] and v["inventoryQuantity"] > 0)
        return {
            "total_variants": len(variants),
            "in_stock_variants": in_stock_count,
            "has_strikethroughs": in_stock_count < len(variants),
            "variants": variants,
        }
