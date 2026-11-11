"""
STRXKE Apparel Co. - Central POD & Catalog Configuration
========================================================
Governs credentials, API endpoints, Comfort Colors 1717 catalog definitions,
contrast matrices, standard pricing tables, and default accordions.
"""

import os

# --- Shopify Admin Credentials ---
SHOP = os.environ.get("SHOPIFY_SHOP", "ussyju-wr")
CLIENT_ID = os.environ.get("SHOPIFY_CLIENT_ID", "9038860610a7bd58479abdccc52317a8")
def get_shopify_client_secret():
    secret = os.environ.get("SHOPIFY_CLIENT_SECRET")
    if secret:
        return secret
    env_path = os.path.expanduser("~/.env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("SHOPIFY_CLIENT_SECRET="):
                    return line.split("=", 1)[1].strip()
    return ""

CLIENT_SECRET = get_shopify_client_secret()
SHOPIFY_API_VERSION = "2024-04"

# Dedicated Shopify Draft Product used for staging master PNGs to get clean public CDN URLs
STAGING_PRODUCT_ID = os.environ.get("SHOPIFY_STAGING_PRODUCT_ID", "15341741146475")

# --- Printful Configuration ---
PRINTFUL_API_BASE = "https://api.printful.com"
COMFORT_COLORS_PRODUCT_ID = 586  # Comfort Colors 1717 Unisex Heavyweight Tee

def get_printful_api_key():
    token = os.environ.get("PRINTFUL_API_KEY")
    if token:
        return token
    env_path = os.path.expanduser("~/.env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("PRINTFUL_API_KEY="):
                    return line.split("=", 1)[1].strip()
    return None

# --- Comfort Colors 1717 Standard Pricing & Weight Specification ---
SIZE_SPECS = [
    {"size": "S",   "price": "29.99", "grams": 159},
    {"size": "M",   "price": "29.99", "grams": 179},
    {"size": "L",   "price": "29.99", "grams": 198},
    {"size": "XL",  "price": "29.99", "grams": 230},
    {"size": "2XL", "price": "31.99", "grams": 269},
    {"size": "3XL", "price": "32.99", "grams": 272},
    {"size": "4XL", "price": "34.99", "grams": 320},
]
SIZE_SPEC_MAP = {s["size"]: s for s in SIZE_SPECS}

# --- Comfort Colors 1717 Catalog Variant ID Matrix (Product 586) ---
CATALOG_VARIANT_IDS = {
    "Bay":       {"S": 17707, "M": 17708, "L": 17709, "XL": 17710, "2XL": 17711, "3XL": 17712, "4XL": 17713},
    "Black":     {"S": 15114, "M": 15115, "L": 15116, "XL": 15117, "2XL": 15118, "3XL": 16326, "4XL": 17500},
    "Blossom":   {"S": 16541, "M": 16542, "L": 16543, "XL": 16544, "2XL": 16545, "3XL": 16546, "4XL": 17503},
    "Blue Jean": {"S": 16511, "M": 16512, "L": 16513, "XL": 16514, "2XL": 16515, "3XL": 16516, "4XL": 17506},
    "Butter":    {"S": 15166, "M": 15167, "L": 15168, "XL": 15169, "2XL": 15170, "3XL": 16328, "4XL": 17511},
    "Chambray":  {"S": 17648, "M": 17649, "L": 17650, "XL": 17651, "2XL": 17652, "3XL": 17653, "4XL": 17654},
    "Crimson":   {"S": 16547, "M": 16548, "L": 16549, "XL": 16550, "2XL": 16551, "3XL": 16552, "4XL": 17513},
    "Granite":   {"S": 17655, "M": 17656, "L": 17657, "XL": 17658, "2XL": 17659, "3XL": 17660, "4XL": 17661},
    "Grey":      {"S": 15176, "M": 15177, "L": 15178, "XL": 15179, "2XL": 15180, "3XL": 16330, "4XL": 17501},
    "Ivory":     {"S": 16523, "M": 16524, "L": 16525, "XL": 16526, "2XL": 16527, "3XL": 16528, "4XL": 17507},
    "Khaki":     {"S": 21534, "M": 21535, "L": 21536, "XL": 21537, "2XL": 21538, "3XL": 21539, "4XL": 21540},
    "Pepper":    {"S": 17693, "M": 17694, "L": 17695, "XL": 17696, "2XL": 17697, "3XL": 17698, "4XL": 17699},
    "True Navy": {"S": 15181, "M": 15182, "L": 15183, "XL": 15184, "2XL": 15185, "3XL": 16332, "4XL": 17499},
    "White":     {"S": 15124, "M": 15125, "L": 15126, "XL": 15127, "2XL": 15128, "3XL": 16335, "4XL": 17508},
}

# --- Colorway & Artwork Contrast Matrix ---
# Dark Garments require Master 2 (Vintage Cream / Solid White text #F5F0E6)
# Light Garments require Master 1 (Dark Charcoal / Solid Black text #111111)
DARK_GARMENT_COLORS = {"Black", "Pepper", "Crimson", "Blue Jean", "Grey", "True Navy"}
LIGHT_GARMENT_COLORS = {"White", "Ivory", "Blossom", "Butter", "Chambray", "Khaki", "Bay", "Granite"}

def get_master_layer(color_name: str) -> str:
    """Returns 'Master 2' for dark garments, 'Master 1' for light garments."""
    if color_name in DARK_GARMENT_COLORS:
        return "Master 2"
    return "Master 1"

# Representative Printful variant ID used for generating flat-lay mockups (Medium or Large size)
FLATLAY_REPRESENTATIVE_VARIANT_IDS = {
    "Bay": 17709,
    "Black": 15116,
    "Blossom": 16543,
    "Blue Jean": 16513,
    "Butter": 15168,
    "Chambray": 17650,
    "Crimson": 16549,
    "Granite": 17657,
    "Grey": 15178,
    "Ivory": 16525,
    "Khaki": 21536,
    "Pepper": 17695,
    "True Navy": 15183,
    "White": 15126,
}

# Print placement standard for Printful Mockup Generator
PRINT_POSITION_STANDARD = {
    "area_width": 1800,
    "area_height": 2400,
    "width": 1800,
    "height": 2160,
    "top": 120,
    "left": 0,
}

# --- Storefront Description HTML Accordions Builder ---
SIZING_CARD_IMAGE_URL = "https://cdn.shopify.com/s/files/1/1020/2385/6491/files/comfort_colors_1717_size_guide_canonical.jpg?v=1793699622"

def build_storefront_body_html(lead_paragraph_html: str) -> str:
    """Constructs the canonical STRXKE product description with embedded
    Care & Sizing accordions (and NO duplicate HTML table)."""
    lead = lead_paragraph_html.strip()
    if not lead.startswith("<p>"):
        lead = f"<p>{lead}</p>"
        
    accordions = f"""
<details style="border: 1px solid #e5e5e5; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; background: #fafafa;">
<summary style="font-weight: 700; font-size: 15px; cursor: pointer; color: #111; list-style: none; display: flex; justify-content: space-between; align-items: center;">
<span>📏 Comfort Colors 1717 Sizing &amp; Fit Guide</span>
<span style="font-size: 18px; color: #666;">▾</span>
</summary>
<div style="margin-top: 14px; color: #333; line-height: 1.6; font-size: 14px;">
<p>Crafted on authentic <strong>Comfort Colors 1717</strong> unisex garment-dyed heavyweight t-shirts. Features a relaxed, boxy vintage streetwear fit with zero shrink (pre-shrunk 100% US ring-spun cotton, 6.1 oz/yd²).</p>
<ul style="margin: 8px 0 14px 20px;">
<li><strong>Standard Relaxed Fit:</strong> Order your normal unisex size.</li>
<li><strong>Oversized Streetwear Fit:</strong> Size up 1–2 sizes for an exaggerated drop-shoulder look.</li>
</ul>
<div style="text-align: center; margin: 16px 0;">
<img src="{SIZING_CARD_IMAGE_URL}" alt="Comfort Colors 1717 Size Chart (Inches)" style="max-width: 100%; border-radius: 8px; border: 1px solid #eee; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
</div>
</div>
</details>

<details style="border: 1px solid #e5e5e5; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; background: #fafafa;">
<summary style="font-weight: 700; font-size: 15px; cursor: pointer; color: #111; list-style: none; display: flex; justify-content: space-between; align-items: center;">
<span>🧼 Care &amp; Laundering Guide</span>
<span style="font-size: 18px; color: #666;">▾</span>
</summary>
<div style="margin-top: 14px; color: #333; line-height: 1.6; font-size: 14px;">
<ul style="margin: 8px 0 10px 20px;">
<li>Machine wash cold, inside-out, with like colors on gentle cycle.</li>
<li>Use mild detergent only; avoid fabric softeners and optical brighteners.</li>
<li>Tumble dry low or hang dry for longest print longevity.</li>
<li>Cool iron inside-out if needed; <strong>never iron directly over decoration</strong>.</li>
<li>Due to the nature of authentic garment dyeing, minor vintage shade variations are normal.</li>
</ul>
</div>
</details>"""
    return f"{lead}\n{accordions}"
