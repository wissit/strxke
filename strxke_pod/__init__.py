"""
STRXKE POD Automation Package
=============================
Standardized toolkit for Shopify & Printful integration, Comfort Colors 1717
media standardization, variant synchronization, and storefront metadata.
"""

from .config import (
    SHOP,
    CLIENT_ID,
    CLIENT_SECRET,
    STAGING_PRODUCT_ID,
    COMFORT_COLORS_PRODUCT_ID,
    SIZE_SPECS,
    CATALOG_VARIANT_IDS,
    DARK_GARMENT_COLORS,
    LIGHT_GARMENT_COLORS,
    get_master_layer,
    build_storefront_body_html,
)
from .shopify_client import ShopifyClient
from .printful_client import PrintfulClient
from .mockup_cropper import (
    crop_flatlay,
    crop_female_lifestyle,
    crop_male_lifestyle,
    crop_all_storefront_assets,
)
from .deployer import ProductDeployer

__all__ = [
    "SHOP",
    "CLIENT_ID",
    "CLIENT_SECRET",
    "STAGING_PRODUCT_ID",
    "COMFORT_COLORS_PRODUCT_ID",
    "SIZE_SPECS",
    "CATALOG_VARIANT_IDS",
    "DARK_GARMENT_COLORS",
    "LIGHT_GARMENT_COLORS",
    "get_master_layer",
    "build_storefront_body_html",
    "ShopifyClient",
    "PrintfulClient",
    "crop_flatlay",
    "crop_female_lifestyle",
    "crop_male_lifestyle",
    "crop_all_storefront_assets",
    "ProductDeployer",
]
