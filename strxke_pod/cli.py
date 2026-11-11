"""
STRXKE Apparel Co. - Unified CLI Tool
=====================================
Usage:
    python -m strxke_pod.cli verify --product-id 15314853298539
    python -m strxke_pod.cli sync --product-id 15314853298539 --sync-id 486870394 --m1-file 1101761072 --m2-file 1101761242
    python -m strxke_pod.cli deploy --help
"""

import sys
import argparse
import json
from .shopify_client import ShopifyClient
from .printful_client import PrintfulClient
from .deployer import ProductDeployer
from .mockup_cropper import crop_all_storefront_assets
from .auditor import ListingAuditor
from .remediator import MasterRemediator


def cmd_verify(args):
    client = ShopifyClient()
    prod_id = args.product_id
    print(f"\n[Verify] Checking Product {prod_id}...")
    p = client.get_product(prod_id)
    print(f"Title: {p['title']}")
    print(f"Handle: {p['handle']}")
    print(f"Total Variants: {len(p.get('variants', []))}")
    print(f"Total Media Images: {len(p.get('images', []))}")
    if p.get("images"):
        print(f"Slot 1 (Featured Hero): {p['images'][0].get('alt')} (ID {p['images'][0]['id']})")

    res = client.verify_inventory(prod_id)
    print(f"\nInventory Availability: {res['in_stock_variants']}/{res['total_variants']} in stock.")
    if res["has_strikethroughs"]:
        print("[ALERT] Strikethroughs detected! Some variants have quantity <= 0:")
        for v in res["variants"]:
            if not v["availableForSale"] or v["inventoryQuantity"] <= 0:
                print(f"  - {v['title']}: qty={v['inventoryQuantity']}, policy={v['inventoryPolicy']}")
    else:
        print("[OK] ZERO strikethroughs! All variants available for purchase.")


def cmd_sync(args):
    s_client = ShopifyClient()
    p_client = PrintfulClient()
    variants = s_client.list_variants(args.product_id)
    p_client.sync_product_variants(
        shopify_variants=variants,
        sync_product_id=int(args.sync_id),
        m1_file_id=int(args.m1_file),
        m2_file_id=int(args.m2_file),
    )
    print("[OK] Printful synchronization complete.")


def cmd_crop(args):
    colors = args.colors.split(",") if args.colors else []
    crop_all_storefront_assets(
        raw_dir=args.raw_dir,
        flat_out_dir=args.flat_dir,
        life_out_dir=args.life_dir,
        colorways=colors,
        crop_type=args.crop_type,
        product_slug=args.slug,
    )
    print("[OK] Cropping complete.")


def cmd_deploy(args):
    colors = [c.strip() for c in args.colors.split(",") if c.strip()]
    deployer = ProductDeployer(
        shopify_product_id=args.product_id,
        printful_sync_product_id=int(args.sync_id),
    )
    deployer.deploy(
        master1_path=args.m1_path,
        master2_path=args.m2_path,
        colorways=colors,
        featured_color=args.featured,
        product_slug=args.slug,
        lead_description=args.desc,
        base_dir=args.base_dir,
        crop_type=args.crop_type,
        skip_mockup_generation=args.skip_mockups,
    )
    print("[OK] Deployment completed successfully.")


def cmd_audit(args):
    auditor = ListingAuditor(
        product_id=args.product_id,
        sync_product_id=int(args.sync_id) if args.sync_id else None,
        base_dir=args.base_dir,
    )
    res = auditor.run_audit()
    scorecard = auditor.print_markdown_scorecard(res)
    print("\n" + scorecard)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(scorecard)
        print(f"[OK] Audit scorecard saved to: {args.output}")


def cmd_remediate(args):
    import os
    base_dir = args.base_dir
    project_name = os.path.basename(os.path.normpath(base_dir))
    print(f"\n[Remediate] Running deterministic remediation for {project_name} in {base_dir}...")
    if "sleigh" in project_name.lower():
        res = MasterRemediator.remediate_sleighing_the_night_shift(base_dir)
    else:
        psd_path = os.path.join(base_dir, "source_assets", f"{project_name}_Master.psd")
        m1_path = os.path.join(base_dir, "production_png", "Master1_LightGarments.png")
        m2_path = os.path.join(base_dir, "production_png", "Master2_DarkGarments.png")
        if os.path.exists(psd_path):
            MasterRemediator.export_from_layered_psd(psd_path, m1_path, m2_path)
        else:
            base_m = os.path.join(base_dir, "production_png", "Master0_Base.png")
            MasterRemediator.remediate_raster_fallback(base_m, m1_path, m2_path)
    print("[OK] Deterministic remediation complete.")


def main():
    parser = argparse.ArgumentParser(description="STRXKE POD Automation CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # deploy
    p_dep = subparsers.add_parser("deploy", help="Run full end-to-end deployment pipeline")
    p_dep.add_argument("--product-id", required=True, help="Shopify product ID")
    p_dep.add_argument("--sync-id", required=True, help="Printful sync product ID")
    p_dep.add_argument("--m1-path", required=True, help="Path to Master 1 PNG (Light Garments)")
    p_dep.add_argument("--m2-path", required=True, help="Path to Master 2 PNG (Dark Garments)")
    p_dep.add_argument("--colors", required=True, help="Comma-separated colorways")
    p_dep.add_argument("--featured", required=True, help="Featured color for Slot 1")
    p_dep.add_argument("--slug", required=True, help="Product slug for naming")
    p_dep.add_argument("--desc", required=True, help="Lead paragraph HTML/text for description")
    p_dep.add_argument("--base-dir", required=True, help="Project directory")
    p_dep.add_argument("--crop-type", default="standing", choices=["standing", "seated"], help="Cropping formula")
    p_dep.add_argument("--skip-mockups", action="store_true", help="Skip mockup generation if already present")
    p_dep.set_defaults(func=cmd_deploy)

    # verify
    p_ver = subparsers.add_parser("verify", help="Verify Shopify product inventory and gallery slots")
    p_ver.add_argument("--product-id", required=True, help="Shopify product ID")
    p_ver.set_defaults(func=cmd_verify)

    # sync
    p_sync = subparsers.add_parser("sync", help="Synchronize Shopify variants to Printful")
    p_sync.add_argument("--product-id", required=True, help="Shopify product ID")
    p_sync.add_argument("--sync-id", required=True, help="Printful sync product ID")
    p_sync.add_argument("--m1-file", required=True, help="Printful File ID for Master 1")
    p_sync.add_argument("--m2-file", required=True, help="Printful File ID for Master 2")
    p_sync.set_defaults(func=cmd_sync)

    # crop
    p_crop = subparsers.add_parser("crop", help="Crop raw mockups to standardized 1500x1500 px")
    p_crop.add_argument("--raw-dir", required=True, help="Directory containing raw 2000x2000 JPGs")
    p_crop.add_argument("--flat-dir", required=True, help="Destination directory for 1:1 flat-lays")
    p_crop.add_argument("--life-dir", required=True, help="Destination directory for lifestyle mockups")
    p_crop.add_argument("--colors", required=True, help="Comma-separated colors (e.g. Pepper,Granite,White)")
    p_crop.add_argument("--crop-type", default="standing", choices=["standing", "seated"], help="Cropping formula")
    p_crop.add_argument("--slug", default="Product", help="Prefix for output filenames")
    p_crop.set_defaults(func=cmd_crop)

    # audit
    p_aud = subparsers.add_parser("audit", help="Run programmatic 9-point audit on a product listing")
    p_aud.add_argument("--product-id", required=True, help="Shopify product ID")
    p_aud.add_argument("--sync-id", help="Printful sync product ID")
    p_aud.add_argument("--base-dir", help="Project base directory")
    p_aud.add_argument("--output", help="Optional output markdown file path")
    p_aud.set_defaults(func=cmd_audit)

    # remediate
    p_rem = subparsers.add_parser("remediate", help="Run deterministic artwork remediation engine")
    p_rem.add_argument("--base-dir", required=True, help="Project base directory")
    p_rem.set_defaults(func=cmd_remediate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
