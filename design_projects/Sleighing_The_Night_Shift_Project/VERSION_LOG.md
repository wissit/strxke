# Sleighing the Night Shift Tee — Version Log

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
