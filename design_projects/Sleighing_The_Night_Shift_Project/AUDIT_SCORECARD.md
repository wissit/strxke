# STRXKE Apparel Co. -- 9-Point QA Audit Scorecard
**Product Title:** Sleighing the Night Shift Tee  
**Shopify Product ID:** `15314919326059`  
**Overall Audit Verdict:** **`FAIL`**  

| # | Audit Gate | Status | Evidence / Measurement | Specific Remediation |
| :-: | :--- | :---: | :--- | :--- |
| **1** | **Contrast Matrix & Master Separation** | `PASS` | 4500x5400 @ 300 DPI verified. Distinct RGB typography separation (3,310,304 px diff, 357 px alpha diff). | None. |
| **2** | **CDN Staging & Hash Verification** | `PASS` | Both masters verified against live CDN. Master 1 zero pixel difference vs CDN (exact match; CDN stripped metadata chunks).; Master 2 zero pixel difference vs CDN (exact match; CDN stripped metadata chunks). | None. |
| **3** | **Solid #FF00FF Magenta Proofing & Underbase** | `FAIL` | Master 1: FAIL [unpurged SC1 stethoscope sliver (419 px at x:2760..2880, y:2680..2820)]; Master 2: FAIL [unpurged SC1 stethoscope sliver (419 px at x:2760..2880, y:2680..2820)] | Purge SC1 sliver on Master 1 adjacent to stethoscope tubing.; Purge SC1 sliver on Master 2 adjacent to stethoscope tubing. |
| **4** | **Typography Integrity & Counter Knockouts** | `FAIL` | Master 1: FAIL [7 unpunched counter void(s) (851 px, e.g. bbox=[1355, 588, 11, 47], area=203px); jagged outer strokes (roughness=1.046, stair-ratio=0.109)]; Master 2: FAIL [jagged outer strokes (roughness=1.046, stair-ratio=0.109)] | Punch out trapped white ink in letter counters (A, R, B, O, D, g) and inter-letter/inter-serif gaps on Master 1 to transparent alpha.; Apply anti-aliased outer stroke smoothing on Master 1 to eliminate jagged stair-stepping / rough edges.; Apply anti-aliased outer stroke smoothing on Master 2 to eliminate jagged stair-stepping / rough edges. |
| **5** | **Workspace Hierarchy & Layered Source PSD Contract** | `PASS` | Pristine workspace hierarchy verified. PSD present (Master2_DarkGarments.psd) but missing functional layers (typo=False, body=False, accents=False). All production PNGs and metadata present. | None. |
| **6** | **Storefront Media Standard** | `PASS` | Slot 1 is 1:1 1500x1500 px; Pepper lifestyle parity verified; Granite lifestyle parity verified | None. |
| **7** | **Shopify Listing & Printful Sync Architecture** | `PASS` | Standard tiered pricing verified across all 35 variants; Zero strikethroughs (35/35 in stock); Storefront accordions & canonical size chart verified; Printful sync verified (100% of 35 variants active with active 300 DPI master file IDs) | None. |
| **8** | **Foreground Mass Conservation Gate** | `PASS` | Solid foreground mass conserved within 5% tolerance: Master 1: +0.00% delta (7,569,131 px vs baseline 7,569,131 px); Master 2: -0.00% delta (7,569,336 px vs baseline 7,569,131 px). | None. |
| **9** | **Typography Palette Uniformity Gate** | `PASS` | Master 1: PASS (uniform palette across all glyphs, max delta=37.2 <= 40.0); Master 2: PASS (uniform palette across all glyphs, max delta=8.4 <= 40.0) | None. |
