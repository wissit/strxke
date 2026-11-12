# Sleighing the Night Shift Tee — Version Log

## [v2.1] - 2026-11-12
- **Photopea Cleaned Master Deployment & Media Gallery Refresh**:
  - Archived previous production files to `archive/v_20261112_122000/`.
  - Promoted user manually cleaned Photopea export to active `Master1_LightGarments.png` (4500x5400 @ 300 DPI) for light garments.
  - Derived `Master2_DarkGarments.png` from the cleaned source PSD with Vintage Cream `#F5F0E6` lettering and `#111111` perimeter separation strokes.
  - Staged both print masters to Shopify CDN:
    - Master 1: `https://cdn.shopify.com/s/files/1/1020/2385/6491/files/Master1_LightGarments_2da18b8b-5043-4294-8a5b-8316325f66de.png?v=1794479164` (Printful File ID: `1109388129`)
    - Master 2: `https://cdn.shopify.com/s/files/1/1020/2385/6491/files/Master2_DarkGarments_da8d823f-592c-40e9-b18d-3ca4785a3ed3.png?v=1794479178` (Printful File ID: `1109388216`)
  - Synchronized all 35 Printful variants to the new file IDs (Pepper -> Master 2, Khaki/Ivory/White/Granite -> Master 1).
  - Generated fresh 2000x2000 mockups from Printful Mockup API and cropped to 1:1 1500x1500px storefront standards.
  - Purged old images and uploaded 7 fresh standardized mockups to Shopify Product `15314919326059` with Pepper at Slot 1 linked to variants.
  - Zero strikethroughs verified (35/35 variants in stock).

## [v2.0] - 2026-11-11
- **Full STRXKE Catalog Standard Remediation**:
  - Clamped diffuse outer alpha haze (`alpha < 20` to 0), purging 137,925 faint noise pixels to eliminate DTG underbase white rim defect.
  - Built dedicated `Master1_LightGarments.png` with solid `#111111` dark charcoal typography for Light Garments (`Granite`, `Ivory`, `Khaki`, `White`).
  - Built dedicated `Master2_DarkGarments.png` with solid Vintage Cream `#F5F0E6` typography and outer `#111111` separation strokes for Dark Garments (`Pepper`).
  - Re-exported both masters at strict $4500 \times 5400\text{ px}$ @ 300 DPI.
  - Staged masters to Shopify CDN staging product `15324891971947` and registered permanent 300 DPI file IDs on Printful.
  - Added missing colorway `Granite` (`S`–`4XL`) to Shopify listing for mandatory lifestyle parity.
  - Standardized retail pricing across all 35 variants ($29.99 S–XL, $31.99 2XL, $32.99 3XL, $34.99 4XL) and set `inventory_policy: "continue"`.
  - Injected canonical Care and Comfort Colors 1717 Sizing `<details>` accordions and visual size guide graphic into storefront description.
  - Generated fresh raw $2000 \times 2000\text{ px}$ mockups from Printful Mockup API.
  - Cropped 1:1 $1500 \times 1500\text{ px}$ catalog flat-lays and curated headless lifestyle fits (Female Pepper & Male Granite).
  - Synchronized all 35 variants on Printful via `PUT /sync/variant/@{shopify_variant_id}` to active master file IDs.
