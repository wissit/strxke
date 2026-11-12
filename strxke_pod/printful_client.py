"""
STRXKE Apparel Co. - Reusable Printful API Client
=================================================
Handles Printful file registration, raw 2000x2000 mockup generation tasks
(with automatic 429 rate limit backoff), and variant synchronization via PUT /sync/variant/@{id}.
"""

import os
import time
import requests
from typing import Dict, List, Optional, Any

from .config import (
    PRINTFUL_API_BASE,
    COMFORT_COLORS_PRODUCT_ID,
    get_printful_api_key,
    get_master_layer,
    CATALOG_VARIANT_IDS,
    FLATLAY_REPRESENTATIVE_VARIANT_IDS,
    PRINT_POSITION_STANDARD,
)


class PrintfulClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_printful_api_key()
        if not self.api_key:
            raise ValueError("Printful API Key not found. Set PRINTFUL_API_KEY environment variable or ~/.env file.")
        self.base_url = PRINTFUL_API_BASE

    def get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # --- File Library Registration ---

    def register_file(self, cdn_url: str, filename: str) -> int:
        """Registers a public CDN image URL into Printful's File Library (POST /files)
        and returns the resulting Printful File ID."""
        url = f"{self.base_url}/files"
        payload = {
            "role": "default",
            "url": cdn_url,
            "filename": filename,
        }
        print(f"[PrintfulClient] Registering file: {filename} from {cdn_url}...")
        resp = requests.post(url, headers=self.get_headers(), json=payload, timeout=60)
        resp.raise_for_status()
        file_id = resp.json()["result"]["id"]
        print(f"[PrintfulClient] Registered -> Printful File ID: {file_id}")
        return file_id

    # --- Mockup Generator ---

    def create_mockup_task(
        self,
        variant_ids: List[int],
        image_url: str,
        option_groups: List[str],
        options: List[str],
        product_id: int = COMFORT_COLORS_PRODUCT_ID,
        format: str = "jpg",
        width: int = 2000,
    ) -> str:
        """Submits a mockup generation task with automatic 429 rate-limit backoff."""
        url = f"{self.base_url}/mockup-generator/create-task/{product_id}"
        payload = {
            "variant_ids": variant_ids,
            "format": format,
            "width": width,
            "product_options": {},
            "option_groups": option_groups,
            "options": options,
            "files": [
                {
                    "placement": "front",
                    "image_url": image_url,
                    "position": PRINT_POSITION_STANDARD,
                }
            ],
        }

        while True:
            resp = requests.post(url, headers=self.get_headers(), json=payload, timeout=60)
            if resp.status_code == 429:
                wait_s = int(resp.headers.get("Retry-After", 30))
                print(f"[PrintfulClient] Rate Limit 429 on create-task. Backing off for {wait_s}s...")
                time.sleep(wait_s + 2)
                continue
            resp.raise_for_status()
            task_key = resp.json()["result"]["task_key"]
            return task_key

    def poll_and_download_mockup(self, task_key: str, dest_path: str, poll_interval: int = 4) -> str:
        """Polls a mockup generation task until status='completed', then downloads the image to dest_path."""
        url = f"{self.base_url}/mockup-generator/task?task_key={task_key}"

        while True:
            time.sleep(poll_interval)
            resp = requests.get(url, headers=self.get_headers(), timeout=30)
            if resp.status_code == 429:
                wait_s = int(resp.headers.get("Retry-After", 15))
                time.sleep(wait_s + 2)
                continue
            resp.raise_for_status()
            res = resp.json()["result"]
            status = res["status"]

            if status == "completed":
                mockup_url = res["mockups"][0]["mockup_url"]
                img_data = requests.get(mockup_url, timeout=60).content
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, "wb") as f_out:
                    f_out.write(img_data)
                print(f"[PrintfulClient] Downloaded raw mockup -> {dest_path}")
                return dest_path
            elif status == "failed":
                raise RuntimeError(f"Mockup generation failed: {res}")
            print(f"[PrintfulClient] Mockup task {task_key} status: {status}...")

    def generate_flatlay_mockups(
        self,
        colorways: List[str],
        m1_url: str,
        m2_url: str,
        output_dir: str,
        force: bool = False,
    ) -> Dict[str, str]:
        """Generates raw 2000x2000 flat-lays for all requested colorways, skipping already generated ones unless force=True."""
        os.makedirs(output_dir, exist_ok=True)
        results = {}

        for color in colorways:
            dest_path = os.path.join(output_dir, f"{color}_Flat-Lay.jpg")
            if not force and os.path.exists(dest_path):
                print(f"[PrintfulClient] Flat-lay already exists: {dest_path}")
                results[color] = dest_path
                continue

            var_id = FLATLAY_REPRESENTATIVE_VARIANT_IDS[color]
            layer = get_master_layer(color)
            target_url = m2_url if layer == "Master 2" else m1_url

            print(f"[PrintfulClient] Generating {color} Flat-Lay ({layer}, var_id {var_id})...")
            task_key = self.create_mockup_task(
                variant_ids=[var_id],
                image_url=target_url,
                option_groups=["Flat"],
                options=["Front"],
            )
            self.poll_and_download_mockup(task_key, dest_path)
            results[color] = dest_path

        return results

    def generate_lifestyle_mockups(
        self,
        m1_url: str,
        m2_url: str,
        output_dir: str,
        force: bool = False,
    ) -> Dict[str, str]:
        """Generates the two standard lifestyle fit shots:
        - Female Pepper (Women's 2 Front, Master 2)
        - Male Granite (Men's Front, Master 1)"""
        os.makedirs(output_dir, exist_ok=True)
        results = {}

        # Female Pepper
        fem_path = os.path.join(output_dir, "Pepper_Female_Lifestyle.jpg")
        if force or not os.path.exists(fem_path):
            print("[PrintfulClient] Generating Female Pepper Lifestyle (Women's 2 Front, Master 2)...")
            task_key = self.create_mockup_task(
                variant_ids=[17695],
                image_url=m2_url,
                option_groups=["Women's 2"],
                options=["Front"],
            )
            self.poll_and_download_mockup(task_key, fem_path)
        results["Female Pepper"] = fem_path

        # Male Granite
        male_path = os.path.join(output_dir, "Granite_Male_Lifestyle.jpg")
        if force or not os.path.exists(male_path):
            print("[PrintfulClient] Generating Male Granite Lifestyle (Men's Front, Master 1)...")
            task_key = self.create_mockup_task(
                variant_ids=[17657],
                image_url=m1_url,
                option_groups=["Men's"],
                options=["Front"],
            )
            self.poll_and_download_mockup(task_key, male_path)
        results["Male Granite"] = male_path

        return results

    # --- Variant Synchronization ---

    def sync_variant(
        self,
        shopify_variant_id: str,
        catalog_variant_id: int,
        retail_price: str,
        sku: str,
        file_id: int,
        max_404_retries: int = 10,
    ) -> Dict[str, Any]:
        """Configures and activates a sync variant via PUT /sync/variant/@{shopify_variant_id}.
        Handles 429 rate limits with automatic sleep, and retries 404 while waiting for Shopify webhooks."""
        url = f"{self.base_url}/sync/variant/@{shopify_variant_id}"
        payload = {
            "external_id": str(shopify_variant_id),
            "variant_id": catalog_variant_id,
            "retail_price": str(retail_price),
            "sku": sku,
            "is_ignored": False,
            "files": [{"type": "default", "id": file_id}],
        }

        retries_404 = 0
        connection_retries = 0
        while True:
            try:
                resp = requests.put(url, headers=self.get_headers(), json=payload, timeout=30)
            except (requests.exceptions.RequestException, ConnectionError) as conn_err:
                connection_retries += 1
                if connection_retries > 5:
                    raise
                print(f"[PrintfulClient] Network connection error: {conn_err}. Retrying in 5s (attempt {connection_retries}/5)...")
                time.sleep(5)
                continue

            if resp.status_code == 429:
                wait_s = int(resp.headers.get("Retry-After", 30))
                print(f"[PrintfulClient] Rate Limit on sync variant @{shopify_variant_id}. Waiting {wait_s}s...")
                time.sleep(wait_s + 2)
                continue
            if resp.status_code == 200:
                sv = resp.json()["result"]["sync_variant"]
                return sv
            if resp.status_code == 404:
                retries_404 += 1
                if retries_404 > max_404_retries:
                    raise RuntimeError(f"Variant @{shopify_variant_id} not found on Printful after {max_404_retries} retries.")
                print(f"[PrintfulClient] 404 on @{shopify_variant_id} (Shopify webhook pending). Waiting 3s (retry {retries_404}/{max_404_retries})...")
                time.sleep(3)
                continue

            resp.raise_for_status()

    def sync_product_variants(
        self,
        shopify_variants: List[Dict[str, Any]],
        sync_product_id: int,
        m1_file_id: int,
        m2_file_id: int,
    ) -> int:
        """Syncs all Shopify variants on Printful, automatically mapping Master 1 or Master 2
        based on the garment colorway contrast matrix."""
        print(f"[PrintfulClient] Syncing {len(shopify_variants)} variants for Printful Product {sync_product_id}...")
        synced_count = 0

        for v in shopify_variants:
            color = v.get("option1")
            size = v.get("option2")
            if not color or not size or color not in CATALOG_VARIANT_IDS or size not in CATALOG_VARIANT_IDS[color]:
                continue

            cat_vid = CATALOG_VARIANT_IDS[color][size]
            layer = get_master_layer(color)
            file_id = m2_file_id if layer == "Master 2" else m1_file_id
            sku = v.get("sku") or f"2909954_{cat_vid}"

            self.sync_variant(
                shopify_variant_id=str(v["id"]),
                catalog_variant_id=cat_vid,
                retail_price=v.get("price", "29.99"),
                sku=sku,
                file_id=file_id,
            )
            synced_count += 1
            print(f"[PrintfulClient] Synced {color} / {size} -> {layer} File ID {file_id}.")
            time.sleep(0.4)

        print(f"[PrintfulClient] Completed sync for {synced_count} variants.")
        return synced_count
