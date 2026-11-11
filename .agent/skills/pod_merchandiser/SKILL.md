---
name: pod_merchandiser
description: Automated merchandising curator for STRXKE Apparel Co. Analyzes graphic mood, subject niche, and palette dominance to determine product types, select colorway palettes (6-8 colors), and nominate the Slot 1 featured mockup color while strictly maintaining Pepper and Granite parity.
---

# STRXKE Merchandising & Curation Engine

## Objective
Prevent storefront catalog bloat and decision paralysis. Rather than dumping all garment blanks and colors onto a listing, this skill curates a tailored product mix and colorway assortment for each design while preserving technical and visual standards.

---

## 1. Merchandising Selection Rules

### A. Mandatory Baseline Constraints
1. **Mandatory Lifestyle Parity:** **Pepper** (Master 2, Dark) and **Granite** (Master 1, Light) MUST ALWAYS be included in every t-shirt offering to maintain full gallery parity with the Female Pepper and Male Granite lifestyle fit cards.
2. **Master Contrast Separation:** Every selected colorway must cleanly map to either Master 1 (#111111 typography) or Master 2 (#F5F0E6 typography). Never choose a color that creates muddy legibility.
3. **Palette Size Ceiling:** Standard catalog listings should offer **6 to 8 colors total** (including Pepper and Granite) to optimize conversion rates.

### B. Product Form-Factor Determination Logic
* **Graphic Density & Complexity:**
  * **T-Shirt Only (CC 1717):** High-detail summer graphics, short-sleeve/seasonal themes, medical scrubs/indoor shift themes, lightweight humorous text.
  * **Tee + Crewneck (CC 1566):** Vintage distressed collegiate text, autumn/winter themes, cozy sarcastic animals ("Fueled by Spite Cat", "Catmas Tree").
  * **Tee + Crewneck + Hoodie (IND4000 / Gildan 18500):** Bold streetwear graphics, edgy dark humor, winter outdoor motifs, motorcycle/skate styles.
  *(Note: For hoodies, ensure graphic height does not collide with the front kangaroo pocket).*

### C. Niche-to-Color Archetype Matrix

| Mood / Subculture | Curated Colorway Selection | Recommended Featured (Slot 1) |
| :--- | :--- | :--- |
| **Medical / Clinical / Night Shift** | Pepper, Granite, Bay, Chambray, White, Blossom, Blue Jean | **Bay** or **Chambray** (Clinical scrubs vibe) |
| **Dark Sarcasm / Spite / Anti-Social** | Pepper, Granite, Black, Crimson, Grey, Ivory | **Pepper** or **Black** (Understated washed vintage) |
| **Earthy / Vintage Outdoors / Trades** | Pepper, Granite, Khaki, Bay, Butter, True Navy | **Khaki** or **Pepper** (Rugged workwear wash) |
| **Whimsical / Domestic / Pets** | Pepper, Granite, Blossom, Butter, Ivory, Chambray | **Ivory** or **Blossom** (Warm, soft hand-feel) |
| **Holiday / Winter Chaos** | Pepper, Granite, Crimson, Bay, White, True Navy | **Crimson** (Festive vintage red) |

---

## 2. Programmatic Selection Algorithm (CLI Output)

The agent inspects `design_projects/<Project_Name>/` and generates `merchandising_spec.json`:

```json
{
  "product_slug": "Night_Shift_Crew_Raccoon_Nurse",
  "niche": "Healthcare / Night Shift",
  "recommended_products": ["comfort_colors_1717"],
  "featured_color": "Bay",
  "selected_colorways": [
    "Bay",
    "Pepper",
    "Granite",
    "Chambray",
    "White",
    "Blossom",
    "Blue Jean"
  ],
  "reasoning": "Bay selected as hero to reflect hospital surgical scrubs. Pepper and Granite included for mandatory lifestyle parity. Light/Dark master balance: 4 Light (M1), 3 Dark (M2)."
}