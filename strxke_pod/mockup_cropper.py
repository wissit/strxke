"""
STRXKE Apparel Co. - Mockup Cropping Engine
===========================================
Implements the exact mathematical cropping standards from `catalog_product_media_standard`
for Comfort Colors 1717 products:
- 1:1 Flat-Lays (Standing vs. Seated character formulas -> 1500x1500 px @ Quality 95)
- Headless Lifestyle Fits:
    - Female Fit (Pepper / High-Waisted Jeans -> 1500x1500 px @ Quality 95)
    - Male Fit (Granite / Cargo Shorts -> 1500x1500 px @ Quality 95)
"""

import os
from typing import Dict, List, Tuple
from PIL import Image

# 1:1 Square Flat-Lay Bounding Boxes on 2000x2000 px Raw Sources
FLAT_CROP_BOX_STANDING = (400, 220, 1600, 1420)  # 1200x1200 px
FLAT_CROP_BOX_SEATED = (431, 242, 1521, 1332)    # 1090x1090 px

# Headless Lifestyle Fits on 2000x2000 px Raw Sources
LIFESTYLE_CROP_BOX_FEMALE = (680, 345, 1220, 885)   # 540x540 px (Ribbed collar to jean waistband)
LIFESTYLE_CROP_BOX_MALE = (592, 570, 1412, 1390)    # 820x820 px (Ribbed collar to above shorts)


def crop_flatlay(
    raw_path: str,
    output_path: str,
    crop_type: str = "standing",
    target_size: Tuple[int, int] = (1500, 1500),
    quality: int = 95,
) -> str:
    """Crops a raw 2000x2000 flat-lay to strict 1:1 square catalog standard."""
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw flat-lay file not found: {raw_path}")

    box = FLAT_CROP_BOX_SEATED if crop_type.lower() == "seated" else FLAT_CROP_BOX_STANDING
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with Image.open(raw_path) as im:
        cropped = im.convert("RGB").crop(box).resize(target_size, Image.Resampling.LANCZOS)
        cropped.save(output_path, format="JPEG", quality=quality, optimize=True)

    print(f"[MockupCropper] Cropped Flat-Lay ({crop_type}) -> {output_path}")
    return output_path


def crop_female_lifestyle(
    raw_path: str,
    output_path: str,
    target_size: Tuple[int, int] = (1500, 1500),
    quality: int = 95,
) -> str:
    """Crops raw female lifestyle shot (Pepper / High-Waisted Jeans) to strict headless standard:
    zero neck/throat skin, chin, or mid-thigh denim."""
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw female lifestyle file not found: {raw_path}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with Image.open(raw_path) as im:
        cropped = im.convert("RGB").crop(LIFESTYLE_CROP_BOX_FEMALE).resize(target_size, Image.Resampling.LANCZOS)
        cropped.save(output_path, format="JPEG", quality=quality, optimize=True)

    print(f"[MockupCropper] Cropped Female Lifestyle -> {output_path}")
    return output_path


def crop_male_lifestyle(
    raw_path: str,
    output_path: str,
    target_size: Tuple[int, int] = (1500, 1500),
    quality: int = 95,
) -> str:
    """Crops raw male lifestyle shot (Granite / Cargo Shorts) to strict headless standard:
    anchored at collar seam, excluding shorts waistband and forearms."""
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw male lifestyle file not found: {raw_path}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with Image.open(raw_path) as im:
        cropped = im.convert("RGB").crop(LIFESTYLE_CROP_BOX_MALE).resize(target_size, Image.Resampling.LANCZOS)
        cropped.save(output_path, format="JPEG", quality=quality, optimize=True)

    print(f"[MockupCropper] Cropped Male Lifestyle -> {output_path}")
    return output_path


def crop_all_storefront_assets(
    raw_dir: str,
    flat_out_dir: str,
    life_out_dir: str,
    colorways: List[str],
    crop_type: str = "standing",
    product_slug: str = "Product",
) -> Dict[str, str]:
    """Crops all available flat-lays and lifestyle mockups in `raw_dir` to `flat_out_dir` and `life_out_dir`."""
    results = {}

    for color in colorways:
        raw_name = f"{color}_Flat-Lay.jpg"
        raw_path = os.path.join(raw_dir, raw_name)
        if os.path.exists(raw_path):
            out_name = f"{product_slug}_{color}_FlatLay_1500x1500.jpg"
            out_path = os.path.join(flat_out_dir, out_name)
            crop_flatlay(raw_path, out_path, crop_type=crop_type)
            results[color] = out_path

    # Female Lifestyle
    fem_raw = os.path.join(raw_dir, "Pepper_Female_Lifestyle.jpg")
    if os.path.exists(fem_raw):
        fem_out = os.path.join(life_out_dir, f"{product_slug}_Pepper_Female_Headless_1500x1500.jpg")
        crop_female_lifestyle(fem_raw, fem_out)
        results["Female Lifestyle"] = fem_out

    # Male Lifestyle
    male_raw = os.path.join(raw_dir, "Granite_Male_Lifestyle.jpg")
    if os.path.exists(male_raw):
        male_out = os.path.join(life_out_dir, f"{product_slug}_Granite_Male_Headless_1500x1500.jpg")
        crop_male_lifestyle(male_raw, male_out)
        results["Male Lifestyle"] = male_out

    return results
