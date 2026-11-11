---
name: catalog_product_media_standard
description: STRXKE Apparel Co. catalog media, mockup cropping, and variant sync standard for Comfort Colors 1717 listings. Governs color contrast matrices, 1:1 square flat-lays, headless lifestyle crops, Shopify variant creation & image linkage, Printful @external_id sync, and description accordions.
---

# Catalog Product Media Standard (Comfort Colors 1717)

## Purpose & Scope
This skill provides the mandatory guidelines, automation workflows, and mathematical cropping formulas for standardizing product media, Printful variant synchronization, colorway expansion, and storefront metadata across STRXKE Apparel Co. (`strxkeapparel.com`).

Whenever a Comfort Colors 1717 product is created, updated, expanded with new colors, or audited, follow this protocol without deviation.

---

## 1. Colorway & Artwork Contrast Matrix

Every graphic design must exist in two distinct production master files ($4500 \times 5400\text{ px}$ @ 300 DPI) to guarantee high visual contrast and legibility:

| Category | Comfort Colors 1717 Colorways | Production Layer | Lettering Color & Hex |
| :--- | :--- | :--- | :--- |
| **Light Garments** | White, Ivory, Blossom, Butter, Chambray, Khaki, Bay, Granite | **Master 1** | Solid Dark Charcoal / Black (`#111111`) |
| **Dark Garments** | Black, Pepper, Crimson, Blue Jean, Grey, True Navy | **Master 2** | Solid Vintage Cream / White (`#F5F0E6`) |

### Critical Artwork & Versioning Rules:
- **Never assign white/cream artwork to light garments:** Leads to unreadable, faint graphics on White, Ivory, Blossom, Butter, Chambray, Bay, Granite, etc.
- **Never assign dark artwork to dark garments:** Results in unreadable graphics on Black, Pepper, Crimson, Blue Jean, Grey, True Navy.
- **Artwork Silhouette & Alpha Isolation:** Maintain 100% pure transparency strictly outside the outer graphic silhouette with zero diffuse haze, unmasked background halos, or trapped negative space pockets on non-black garments. Ensure lower jacket/torso silhouettes finish with organic detailing and natural tapering above the typography anchor.
- **Strict Versioning & Archiving:** Whenever production print masters or storefront mockup crops are updated (e.g., `v2.3` -> `v3.0`), archive the previous production files and crops into versioned subfolders (`archive/vX.Y_.../`) before writing new masters. Ensure Printful fulfillment files and storefront mockups represent the exact same approved design version.

---

## 2. Printful Mockup Generation API Standard

When generating raw mockups via Printful Mockup Generator API (`POST /mockup-generator/create-task/586`):
- **Format:** `jpg`
- **Width:** `2000` (provides crisp $2000 \times 2000\text{ px}$ master source files)
- **Print Area Position (Front):**
  `area_width: 1800`, `area_height: 2400`, `width: 1800`, `height: 2160`, `top: 120`, `left: 0`
- **Public CDN Staging Pattern:**
  - Upload local Master 1 and Master 2 PNGs to the dedicated Shopify Draft Staging Product (`15324891971947`) to obtain clean public `https://cdn.shopify.com/...` URLs before calling Printful's `/files` or `/mockup-generator/create-task/586` endpoints.
- **Required Option Groups:**
  - **Flat-Lays:** `option_groups: ["Flat"]`, `options: ["Front"]`
  - **Front Male Model (Granite — `variant_ids: [17657]`):** `option_groups: ["Men's"]`, `options: ["Front"]` (use **Master 1** `#111111` dark lettering)
  - **Front Standing Female Model (Pepper — `variant_ids: [17695]`):** `option_groups: ["Women's 2"]`, `options: ["Front"]` (use **Master 2** `#F5F0E6` cream lettering)
    *(Note: `"Women's"` gives the walking/action pose; `"Women's 2"` gives the approved standing studio pose with hands on hips).*

> [!WARNING]
> **Never reuse old mockup crops when print artwork is updated.** Always generate fresh $2000 \times 2000\text{ px}$ raw renders directly from the active Master 1 and Master 2 CDN files before performing flat-lay or lifestyle cropping.

---

## 3. Primary Flat-Lay Mockup Standard (1:1 Catalog Crop)

All offered garment colorways must receive a standardized 1:1 square crop centered on the chest artwork:
- **Output Format:** Strict 1:1 square JPG (`1500 x 1500 px`), quality 95.
- **Bounding Box Formula (on $2000 \times 2000\text{ px}$ Raw Source):**
  - **Standing Full-Body Character Designs (e.g., "Night Shift Raccoon Nurse"):**
    - Box: `(400, 220, 1600, 1420)` ($1200 \times 1200\text{ px} \longrightarrow 1500 \times 1500\text{ px}$)
    - **Top ($Y=220$):** Anchored at the inner Comfort Colors neck tag ribbing, preserving tag authenticity without clipping.
    - **Bottom ($Y=1420$):** Exactly 2.5 inches ($148\text{ px}$) below the baseline text line, displaying full character anatomy (legs, pants, tail, clogs).
    - **Sides ($X=400..1600$):** Centered at $X=1000$, ensuring artwork occupies ~70–75% of the square's width while eliminating excess outer sleeve margins.
  - **Seated / Compact Full-Character Designs (e.g., "Fueled by Spite Cat Tee"):**
    - Box: `(431, 242, 1521, 1332)` ($1090 \times 1090\text{ px} \longrightarrow 1500 \times 1500\text{ px}$)
    - **Top ($Y=242$):** Anchored tight at the inner neck ribbing / Comfort Colors collar tag line ($Y=242..308$), eliminating excess neck cutout dead space while aligning the top typography arc to $Y=378\text{ px}$ on the $1500 \times 1500\text{ px}$ card.
    - **Bottom ($Y=1332$):** Cropped $129\text{ px}$ (~2.25 inches) below the baseline text `"& ICED COFFEE"` ($Y=1203$), cutting out lower midriff fabric and aligning the bottom text to $Y=1322\text{ px}$ on the $1500 \times 1500\text{ px}$ card.
    - **Sides ($X=431..1521$):** Centered on the graphic centerline ($X=976$), eliminating all outer sleeve and side torso background strips so the collection grid card matches the exact visual density of standing full-body designs.

---

## 4. Curated Headless Lifestyle Fit Standard (Final 2 Gallery Slots)

Every Comfort Colors 1717 product listing MUST include two curated headless lifestyle shots appended to the final two slots of the product media gallery:

> [!IMPORTANT]
> **Mandatory Lifestyle Colorway Parity:** Because the two standard lifestyle fit shots feature **Pepper** (Female Fit) and **Granite** (Male Fit), **both Pepper (Dark Garment -> Master 2 `#F5F0E6`) and Granite (Light Garment -> Master 1 `#111111`) must always be offered as active purchasable colorways** on every product (with their standardized 1:1 flat-lay mockups generated, cropped, and mapped to all 7 size variants `S`–`4XL` on Shopify and synced on Printful). Never display a lifestyle mockup colorway that cannot be selected and purchased in the variant selector.

### Female Fit Model (Pepper / High-Waisted Jeans — Penultimate Gallery Slot)
- **Source:** Printful `Women's 2` -> `Front` ($2000 \times 2000\text{ px}$, `variant_ids: [17695]`, rendered with **Master 2** `#F5F0E6` cream lettering).
- **Bounding Box (Tight Aligned Standard):** `(680, 345, 1220, 885)` ($540 \times 540\text{ px} \longrightarrow 1500 \times 1500\text{ px}$)
- **Top Boundary ($Y=345$):** Anchored strictly at the front ribbed collar seam. **Zero throat skin, chin, jawline, or facial skin.**
- **Bottom Boundary ($Y=885$):** Crops right below the front jean button/waistband seam. **Strictly eliminates all mid-thigh denim.**
- **Horizontal Framing ($X=680..1220$):** Centered at $X=950$, trimming excess outer arm/background space so the shirt chest and artwork command the center ~75% of the frame, matching the scale and impact of the male counterpart.
- **Graphic Completeness:** 100% of the artwork (from top arched text to bottom text line) is fully visible.

### Male Fit Model (Granite / Cargo Shorts — Final Gallery Slot)
- **Source:** Printful `Men's` -> `Front` ($2000 \times 2000\text{ px}$, `variant_ids: [17657]`, rendered with **Master 1** `#111111` dark lettering).
- **Bounding Box:** `(592, 570, 1412, 1390)` ($820 \times 820\text{ px} \longrightarrow 1500 \times 1500\text{ px}$)
- **Top Boundary ($Y=570$):** Anchored at the front ribbed collar seam. **Zero neck skin or jawline.**
- **Bottom Boundary ($Y=1390$):** Crops 2–3 inches below the baseline text; completely excludes the pants/shorts waistband.
- **Horizontal Framing ($X=592..1412$):** Crops inward through the upper biceps; excludes forearms, wrists, and hands.

---

## 5. Product Gallery Hierarchy & Variant Swatch Linkage (Shopify)

The Shopify product gallery must always place **all offered color flat-lays first** (`Slots 1..N`), followed by the **two headless lifestyle fit mockups** at `Slots N+1` and `N+2`:

- **11-Color Catalog Listing (e.g., "Night Shift Raccoon Nurse" — `15314035704171`, 77 Variants, 13 Slots):**
  - `Slots 1–11`: Flat-Lays (`Bay` or `Black` at Slot 1 as Featured Collection Card, plus `Pepper`, `Crimson`, `Blue Jean`, `Grey`, `Granite`, `Khaki`, `Blossom`, `Ivory`, `White`) — each linked to its 7 size variants (`77` links total).
  - `Slot 12`: Female Headless Lifestyle Fit (`Pepper`, `0` variants linked).
  - `Slot 13`: Male Headless Lifestyle Fit (`Granite`, `0` variants linked).
- **7-Color Catalog Listing (e.g., "Fueled by Spite Cat Tee" — `15313539105131`, 49 Variants, 9 Slots):**
  - `Slots 1–7`: Flat-Lays (`Bay` at Slot 1 as Featured Collection Card, `Pepper` at Slot 2, `Granite` at Slot 3, `Butter` at Slot 4, `Blossom` at Slot 5, `Chambray` at Slot 6, `Ivory` at Slot 7) — each linked to its 7 size variants (`49` links total).
  - `Slot 8`: Female Headless Lifestyle Fit (`Pepper`, `0` variants linked).
  - `Slot 9`: Male Headless Lifestyle Fit (`Granite`, `0` variants linked).

### Variant Image Mapping Protocol:
1. Every color flat-lay image ID must be mapped to all 7 matching size variants (`S`, `M`, `L`, `XL`, `2XL`, `3XL`, `4XL`).
2. **Purge Obsolete Media:** Delete all test or superseded image IDs from the Shopify product after uploading new assets. Leaving old images causes Shopify CDN thumbnail caching mismatches on swatch selection.

---

## 6. Adding & Syncing New Colorways End-to-End (Shopify <-> Printful Protocol)

When adding new Comfort Colors 1717 colorways (such as **Pepper** and **Granite**) to an existing Shopify + Printful product, follow this 3-step API workflow (reference implementation: [`scripts_and_tools/add_pepper_and_granite_to_fueled_by_spite.py`](file:///c:/code/Tshirt_POD/scripts_and_tools/add_pepper_and_granite_to_fueled_by_spite.py)):

### Step A: Create the 7 Size Variants (`S`–`4XL`) per Color on Shopify
Call `POST /admin/api/2024-04/products/{product_id}/variants.json` for each size using these exact Comfort Colors 1717 retail price & weight specifications:

| Size | Standard Retail Price | Custom Retail Price (tagged `custom`) | Weight (`grams`) | SKU Format | Inventory Policy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **S** | `$29.99` | `$34.99` | `159` | `2909954_{catalog_variant_id}` | `"continue"` |
| **M** | `$29.99` | `$34.99` | `179` | `2909954_{catalog_variant_id}` | `"continue"` |
| **L** | `$29.99` | `$34.99` | `198` | `2909954_{catalog_variant_id}` | `"continue"` |
| **XL** | `$29.99` | `$34.99` | `230` | `2909954_{catalog_variant_id}` | `"continue"` |
| **2XL** | `$31.99` | `$36.99` | `269` | `2909954_{catalog_variant_id}` | `"continue"` |
| **3XL** | `$32.99` | `$37.99` | `272` | `2909954_{catalog_variant_id}` | `"continue"` |
| **4XL** | `$34.99` | `$39.99` | `320` | `2909954_{catalog_variant_id}` | `"continue"` |

*(Note: Because the custom Shopify Admin API client does not hold `write_inventory` scope, set `"inventory_policy": "continue"` and omit `"inventory_management"` on creation so new variants are immediately in stock on the storefront while Printful's integration syncs inventory).*

### Step B: Comfort Colors 1717 (Product `586`) Printful Catalog Variant ID Matrix

| Colorway | Category / Master | **S** | **M** | **L** | **XL** | **2XL** | **3XL** | **4XL** |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Bay** | Light (**Master 1**) | `17707` | `17708` | `17709` | `17710` | `17711` | `17712` | `17713` |
| **Black** | Dark (**Master 2**) | `15114` | `15115` | `15116` | `15117` | `15118` | `16326` | `17500` |
| **Blossom** | Light (**Master 1**) | `16541` | `16542` | `16543` | `16544` | `16545` | `16546` | `17503` |
| **Blue Jean** | Dark (**Master 2**) | `16511` | `16512` | `16513` | `16514` | `16515` | `16516` | `17506` |
| **Butter** | Light (**Master 1**) | `15166` | `15167` | `15168` | `15169` | `15170` | `16328` | `17511` |
| **Chambray** | Light (**Master 1**) | `17648` | `17649` | `17650` | `17651` | `17652` | `17653` | `17654` |
| **Crimson** | Dark (**Master 2**) | `16547` | `16548` | `16549` | `16550` | `16551` | `16552` | `17513` |
| **Granite** | Light (**Master 1**) | `17655` | `17656` | `17657` | `17658` | `17659` | `17660` | `17661` |
| **Grey** | Dark (**Master 2**) | `15176` | `15177` | `15178` | `15179` | `15180` | `16330` | `17501` |
| **Ivory** | Light (**Master 1**) | `16523` | `16524` | `16525` | `16526` | `16527` | `16528` | `17507` |
| **Khaki** | Light (**Master 1**) | `21534` | `21535` | `21536` | `21537` | `21538` | `21539` | `21540` |
| **Pepper** | Dark (**Master 2**) | `17693` | `17694` | `17695` | `17696` | `17697` | `17698` | `17699` |
| **True Navy** | Dark (**Master 2**) | `15181` | `15182` | `15183` | `15184` | `15185` | `16332` | `17499` |
| **White** | Light (**Master 1**) | `15124` | `15125` | `15126` | `15127` | `15128` | `16335` | `17508` |

### Step C: Sync New Shopify Variants on Printful via `PUT /sync/variant/@{shopify_variant_id}`
Because the store is an Ecommerce Platform Integration store on Printful (`/store/products` returns `400`), Printful automatically imports newly created Shopify variants via webhook. Configure and link each new variant immediately by calling `PUT https://api.printful.com/sync/variant/@{shopify_variant_id}` with:
```json
{
  "external_id": "<shopify_variant_id>",
  "variant_id": 17693,
  "retail_price": "29.99",
  "sku": "2909954_17693",
  "is_ignored": false,
  "files": [
    {
      "type": "default",
      "id": "<printful_master1_or_master2_file_id>"
    }
  ]
}
```
Always wrap `PUT /sync/variant/@{shopify_variant_id}` in a `while True` retry loop that inspects `r.status_code == 429` and sleeps `int(r.headers.get("Retry-After", 30)) + 2` seconds.

---

## 7. Storefront Description Accordions

Inject standard `<details>` blocks into the product `body_html` matching the clean brand layout:

1. **🧼 Care & Laundering Guide:**
   - Wash cold inside-out, tumble dry low, non-chlorine bleach, cool iron inside-out (never iron print), pigment-dye disclaimer.
2. **📏 Comfort Colors 1717 Sizing & Fit:**
   - Fabric summary: Heavyweight 6.1 oz/yd² 100% ring-spun US cotton, relaxed vintage boxy fit, pre-shrunk.
   - Embedded Visual Sizing Card:
     `<div style="text-align: center; margin: 14px 0;"><img src="https://cdn.shopify.com/s/files/1/1020/2385/6491/files/comfort_colors_1717_size_guide_canonical.jpg?v=1793699622" alt="Comfort Colors 1717 Size Guide" style="max-width: 100%; border-radius: 8px; border: 1px solid #eee; box-shadow: 0 2px 8px rgba(0,0,0,0.06);"></div>`
   - **NO DUPLICATE HTML TABLE:** Do NOT append an HTML `<table>` below the sizing image. The graphic size card already provides all measurements (Chest Width & Length for sizes S through 4XL). Adding a table creates unnecessary visual duplication on both mobile and desktop.

---

## 8. Standardized Python Package: `strxke_pod`

All automation, API syncs, mockup generation, and image cropping workflows are packaged in the reusable module [`c:\code\Tshirt_POD\strxke_pod`](file:///c:/code/Tshirt_POD/strxke_pod). **Do not write ad-hoc or throwaway sync scripts**; use this package for all future and existing products.

### Modules Overview:
- **`strxke_pod.config`**: Credentials, Comfort Colors 1717 catalog variant matrix (all 13 colors), size specs, contrast mapping (`Master 1` vs `Master 2`), and accordion generator.
- **`strxke_pod.shopify_client`**: `ShopifyClient` with OAuth token caching, variant expansion (`ensure_variants`), public CDN print master staging (`stage_print_master`), media gallery upload and purging, and GraphQL inventory verification (`verify_inventory`).
- **`strxke_pod.printful_client`**: `PrintfulClient` with automated 429 rate limit backoff, file registration (`register_file`), 2000x2000 mockup batch generation (`generate_flatlay_mockups`, `generate_lifestyle_mockups`), and variant sync (`sync_variant`, `sync_product_variants`).
- **`strxke_pod.mockup_cropper`**: Mathematical cropping formulas for 1:1 flat-lays (`standing` vs `seated`) and headless lifestyle fits (`crop_female_lifestyle`, `crop_male_lifestyle`).
- **`strxke_pod.deployer`**: `ProductDeployer` for 1-call end-to-end product deployments.
- **`strxke_pod.cli`**: CLI tool for quick verification and operations.

### Python Usage Example:
```python
from strxke_pod import ProductDeployer

deployer = ProductDeployer(shopify_product_id="15314853298539", printful_sync_product_id=486870394)
deployer.deploy(
    master1_path=r"path/to/Master1_LightGarments.png",
    master2_path=r"path/to/Master2_DarkGarments.png",
    colorways=["Pepper", "Granite", "White", "Black", "Bay", "Blossom", "Butter", "Ivory"],
    featured_color="Pepper",
    product_slug="Sleigh_Bells",
    lead_description="For the emergency department heroes navigating the busiest shift of the year...",
    base_dir=r"c:\code\Tshirt_POD\design_projects\Sleigh_Bells_Trauma_Calls_Project",
    crop_type="standing",
)
```

### CLI Usage Example:
```bash
# Verify zero strikethroughs and gallery order
python -m strxke_pod.cli verify --product-id 15314853298539

# Sync all variants on Printful
python -m strxke_pod.cli sync --product-id 15314853298539 --sync-id 486870394 --m1-file 1101761072 --m2-file 1101761242
```
