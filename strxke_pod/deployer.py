"""
STRXKE Apparel Co. - Unified Product Deployment Orchestrator
============================================================
Coordinates the end-to-end lifecycle for Comfort Colors 1717 products:
1. Master staging to Shopify CDN & Printful File Library registration.
2. Raw 2000x2000 mockup generation on Printful (flat-lays + lifestyle fits).
3. 1:1 catalog & headless lifestyle cropping.
4. Variant expansion & pricing standardization on Shopify.
5. Gallery hierarchy enforcement (Designated Featured Color at Slot 1).
6. Printful sync variant configuration (activating Shopify inventory to 9999).
7. Storefront description & accordion updates.
8. GraphQL inventory & availability verification.
"""

import os
import json
import time
from typing import Dict, List, Optional, Any

from .config import get_master_layer
from .shopify_client import ShopifyClient
from .printful_client import PrintfulClient
from .mockup_cropper import crop_all_storefront_assets


class ProductDeployer:
    def __init__(
        self,
        shopify_product_id: str,
        printful_sync_product_id: int,
        shopify_client: Optional[ShopifyClient] = None,
        printful_client: Optional[PrintfulClient] = None,
    ):
        self.shopify_product_id = str(shopify_product_id)
        self.printful_sync_product_id = int(printful_sync_product_id)
        self.shopify = shopify_client or ShopifyClient()
        self.printful = printful_client or PrintfulClient()

    def stage_masters(
        self,
        master1_path: str,
        master2_path: str,
        product_slug: str,
        cache_json_path: Optional[str] = None,
        force_reupload: bool = False,
    ) -> Dict[str, Any]:
        """Stages Master 1 and Master 2 PNGs to Shopify CDN and registers them in Printful File Library."""
        if not force_reupload and cache_json_path and os.path.exists(cache_json_path):
            with open(cache_json_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
                if all(k in cached for k in ["master1_file_id", "master2_file_id", "master1_cdn_url", "master2_cdn_url"]):
                    print(f"[Deployer] Using cached master file IDs from: {cache_json_path}")
                    return cached

        m1_cdn = self.shopify.stage_print_master(master1_path, f"{product_slug} Master 1 Light Garments")
        m1_file_id = self.printful.register_file(m1_cdn, f"{product_slug}_Master1_LightGarments.png")

        m2_cdn = self.shopify.stage_print_master(master2_path, f"{product_slug} Master 2 Dark Garments")
        m2_file_id = self.printful.register_file(m2_cdn, f"{product_slug}_Master2_DarkGarments.png")

        result = {
            "master1_cdn_url": m1_cdn,
            "master1_file_id": m1_file_id,
            "master2_cdn_url": m2_cdn,
            "master2_file_id": m2_file_id,
        }

        if cache_json_path:
            os.makedirs(os.path.dirname(cache_json_path), exist_ok=True)
            with open(cache_json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)

        return result

    def deploy(
        self,
        master1_path: str,
        master2_path: str,
        colorways: List[str],
        featured_color: str,
        product_slug: str,
        lead_description: str,
        base_dir: str,
        crop_type: str = "standing",
        masters_cache_path: Optional[str] = None,
        skip_mockup_generation: bool = False,
    ) -> Dict[str, Any]:
        """Runs the entire end-to-end production deployment pipeline."""
        print(f"\n=======================================================")
        print(f"Starting STRXKE POD Deployment for Product {self.shopify_product_id}")
        print(f"Featured Color: {featured_color} | Total Colorways: {len(colorways)}")
        print(f"=======================================================\n")

        raw_dir = os.path.join(base_dir, "mockups", "raw_2000x2000")
        flat_dir = os.path.join(base_dir, "mockups", "storefront", "flat_lays")
        life_dir = os.path.join(base_dir, "mockups", "storefront", "lifestyle")

        # 1. Stage Masters
        print("\n--- [Step 1/7] Staging Master Print Files ---")
        masters = self.stage_masters(
            master1_path=master1_path,
            master2_path=master2_path,
            product_slug=product_slug,
            cache_json_path=masters_cache_path,
        )

        # 2. Mockup Generation
        if not skip_mockup_generation:
            print("\n--- [Step 2/7] Generating Printful Raw 2000x2000 Mockups ---")
            self.printful.generate_flatlay_mockups(
                colorways=colorways,
                m1_url=masters["master1_cdn_url"],
                m2_url=masters["master2_cdn_url"],
                output_dir=raw_dir,
            )
            self.printful.generate_lifestyle_mockups(
                m1_url=masters["master1_cdn_url"],
                m2_url=masters["master2_cdn_url"],
                output_dir=raw_dir,
            )
        else:
            print("\n--- [Step 2/7] Skipping raw mockup generation (flag set) ---")

        # 3. Mathematical Cropping
        print("\n--- [Step 3/7] Cropping 1:1 Flat-Lays and Lifestyle Fits ---")
        cropped_assets = crop_all_storefront_assets(
            raw_dir=raw_dir,
            flat_out_dir=flat_dir,
            life_out_dir=life_dir,
            colorways=colorways,
            crop_type=crop_type,
            product_slug=product_slug,
        )

        # 4. Variant Expansion & Standardization on Shopify
        print("\n--- [Step 4/7] Ensuring All Shopify Variants & Standardizing Pricing ---")
        all_variants = self.shopify.ensure_variants(
            product_id=self.shopify_product_id,
            colorways=colorways,
            standardize_pricing=True,
        )

        variants_by_color = {}
        for v in all_variants:
            variants_by_color.setdefault(v["option1"], []).append(v["id"])

        # 5. Media Gallery Upload with Featured Color at Slot 1
        print("\n--- [Step 5/7] Uploading Standardized Mockups to Media Gallery ---")
        self.shopify.purge_images(self.shopify_product_id)

        # Build gallery sequence: Featured color first, then remaining colors, then lifestyles
        remaining_colors = [c for c in colorways if c != featured_color]
        ordered_colors = [featured_color] + remaining_colors

        upload_plan = []
        for color in ordered_colors:
            if color in cropped_assets:
                upload_plan.append((
                    color,
                    cropped_assets[color],
                    f"{product_slug} - {color} Front (Comfort Colors 1717 1:1 Catalog Standard)",
                    variants_by_color.get(color, []),
                ))

        if "Female Lifestyle" in cropped_assets:
            upload_plan.append((
                "Female Lifestyle",
                cropped_assets["Female Lifestyle"],
                f"{product_slug} - Female Fit Model (Pepper)",
                [],
            ))
        if "Male Lifestyle" in cropped_assets:
            upload_plan.append((
                "Male Lifestyle",
                cropped_assets["Male Lifestyle"],
                f"{product_slug} - Male Fit Model (Granite)",
                [],
            ))

        for idx, (label, fpath, alt, v_ids) in enumerate(upload_plan, start=1):
            self.shopify.upload_image(
                product_id=self.shopify_product_id,
                file_path=fpath,
                position=idx,
                alt_text=alt,
                variant_ids=v_ids,
            )

        # 6. Printful Variant Sync (triggers inventory webhook -> 9999)
        print("\n--- [Step 6/7] Synchronizing Variants on Printful ---")
        self.printful.sync_product_variants(
            shopify_variants=all_variants,
            sync_product_id=self.printful_sync_product_id,
            m1_file_id=masters["master1_file_id"],
            m2_file_id=masters["master2_file_id"],
        )

        # 7. Storefront Description Accordions
        print("\n--- [Step 7/7] Updating Storefront Description & Sizing Accordions ---")
        self.shopify.update_accordions(
            product_id=self.shopify_product_id,
            lead_paragraph_html=lead_description,
        )

        # 8. Live Verification
        print("\n--- [Verification] Verifying Live Storefront Inventory & Availability ---")
        time.sleep(3)
        status = self.shopify.verify_inventory(self.shopify_product_id)
        print(f"[Deployer] In-Stock: {status['in_stock_variants']}/{status['total_variants']} variants.")
        if status["has_strikethroughs"]:
            print("[WARN] Some variants still indicate out-of-stock. Webhooks may take an extra 30s to settle.")
        else:
            print("[SUCCESS] All variants are in stock with ZERO strikethroughs!")

        return {
            "shopify_product_id": self.shopify_product_id,
            "total_variants": status["total_variants"],
            "in_stock_variants": status["in_stock_variants"],
            "featured_color": featured_color,
            "images_uploaded": len(upload_plan),
        }
