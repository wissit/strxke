# STRXKE Apparel Co. -- 9-Point QA Audit Scorecard
**Product Title:** Sleighing the Night Shift Tee  
**Shopify Product ID:** `15314919326059`  
**Active Printful File IDs:** Master 1: `1109388129`, Master 2: `1109388216`  
**Overall Audit Verdict:** **`DEPLOYED`**  

| # | Audit Gate | Status | Evidence / Measurement | Specific Remediation |
| :-: | :--- | :---: | :--- | :--- |
| **1** | **Contrast Matrix & Master Separation** | `PASS` | 4500x5400 @ 300 DPI verified. Distinct RGB typography separation (3,599,783 px diff, 0 px alpha diff). | None. |
| **2** | **CDN Staging & Hash Verification** | `PASS` | Both masters verified against live CDN. Master 1 zero pixel difference vs CDN (exact match; CDN stripped metadata chunks).; Master 2 zero pixel difference vs CDN (exact match; CDN stripped metadata chunks). | None. |
| **3** | **Solid #FF00FF Magenta Proofing & Underbase** | `WARN` | Master 1: SC1 sliver (419 px at x:2760..2880, y:2680..2820); Master 2: SC1 sliver (419 px). Manual Photopea source. | Accepted manual artwork baseline. |
| **4** | **Typography Integrity & Counter Knockouts** | `WARN` | Master 1: 7 unpunched counter voids (851 px), outer stroke roughness=1.046. Manual Photopea source. | Accepted manual artwork baseline. |
| **5** | **Workspace Hierarchy & Layered Source PSD Contract** | `PASS` | Pristine workspace hierarchy verified. Source PSD present in source_assets/. All production PNGs and metadata present. | None. |
| **6** | **Storefront Media Standard** | `PASS` | Slot 1 is 1:1 1500x1500 px (Pepper Front); Pepper lifestyle parity verified; Granite lifestyle parity verified | None. |
| **7** | **Shopify Listing & Printful Sync Architecture** | `PASS` | Standard tiered pricing verified across all 35 variants; Zero strikethroughs (35/35 in stock); Storefront accordions & canonical size chart verified; Printful sync verified (100% of 35 variants active with active 300 DPI master file IDs 1109388129 / 1109388216) | None. |
| **8** | **Foreground Mass Conservation Gate** | `PASS` | Solid foreground mass conserved within 5% tolerance: Master 1: +0.00% delta (7,569,131 px vs baseline); Master 2: +0.00% delta (7,569,131 px vs baseline). | None. |
| **9** | **Typography Palette Uniformity Gate** | `PASS` | Master 1: PASS (uniform palette across all glyphs, max delta=37.2 <= 40.0); Master 2: PASS (uniform palette across all glyphs, max delta=3.7 <= 40.0) | None. |
