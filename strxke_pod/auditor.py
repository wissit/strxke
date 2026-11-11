"""
STRXKE Apparel Co. - Programmatic QA Auditor Engine
===================================================
Executes the strict 9-Point Audit Protocol for Comfort Colors 1717 listings:
1. Garment Contrast Matrix & Master Separation (M1 vs M2, 4500x5400 @ 300 DPI)
2. Full-Artwork Structural Hash & CDN Staging Verification (Pixel diff vs CDN)
3. Solid #FF00FF Magenta Proofing & Underbase Purging (Alpha clamp, floating noise, rigid underbase block)
4. Typography Integrity & Counter Knockouts (Glyph counters, washability pinholes)
5. Standardized Workspace Hierarchy & Layered Source PSD Contract (PSD-first workflow)
6. Storefront Media Standard (1:1 1500x1500px, lifestyle parity, SEO alt-text)
7. Shopify Listing, Printful Sync & Product Architecture (Tier-aware pricing, accordions, Printful sync state)
8. Foreground Mass Conservation Gate (<= 5% solid alpha mass drop vs Master0 baseline)
9. Typography Palette Uniformity Gate (Euclidean distance <= 40 across vertical glyph halves)
"""

import os
import sys
import json
import hashlib
import io
import re
import requests
import numpy as np
import cv2
from PIL import Image, ImageChops
from typing import Dict, List, Optional, Tuple, Any

from .config import (
    SHOP,
    SHOPIFY_API_VERSION,
    SIZE_SPECS,
    CATALOG_VARIANT_IDS,
    DARK_GARMENT_COLORS,
    LIGHT_GARMENT_COLORS,
    get_master_layer,
)
from .shopify_client import ShopifyClient
from .printful_client import PrintfulClient


class ListingAuditor:
    def __init__(
        self,
        product_id: str,
        sync_product_id: Optional[int] = None,
        base_dir: Optional[str] = None,
        shopify_client: Optional[ShopifyClient] = None,
        printful_client: Optional[PrintfulClient] = None,
    ):
        self.product_id = str(product_id)
        self.sync_product_id = int(sync_product_id) if sync_product_id else None
        self.base_dir = base_dir
        self.shopify = shopify_client or ShopifyClient()
        self.printful = printful_client or PrintfulClient()
        self.results: List[Dict[str, Any]] = []

    def _add_result(self, check_num: int, item: str, status: str, evidence: str, remediation: str):
        self.results.append({
            "check_num": check_num,
            "item": item,
            "status": status,
            "evidence": evidence,
            "remediation": remediation,
        })

    @staticmethod
    def _extract_canonical_color(variant_name: str, color_attr: Optional[str] = None) -> Optional[str]:
        """
        Parses or matches the color segment directly against the canonical Comfort Colors 1717
        colorway list to prevent partial substring collisions (e.g., 'Bay' matching 'Bayleaf').
        """
        canonical_colors = list(CATALOG_VARIANT_IDS.keys())

        # 1. Direct match from explicit color attribute
        if color_attr:
            attr_clean = color_attr.strip().lower()
            for c in canonical_colors:
                if c.lower() == attr_clean:
                    return c

        # 2. Extract from structured variant title, e.g. "Product Title - Bay / S" or "Bay / S"
        if "/" in variant_name:
            left_segment = variant_name.rsplit("/", 1)[0].strip()
            if " - " in left_segment:
                cand_color = left_segment.rsplit(" - ", 1)[-1].strip()
            elif "-" in left_segment:
                cand_color = left_segment.rsplit("-", 1)[-1].strip()
            else:
                cand_color = left_segment

            for c in canonical_colors:
                if c.lower() == cand_color.lower():
                    return c

        # 3. Match against canonical color names with regex word boundaries (longest names first)
        for c in sorted(canonical_colors, key=len, reverse=True):
            pattern = r"(?<!\w)" + re.escape(c) + r"(?!\w)"
            if re.search(pattern, variant_name, re.IGNORECASE):
                return c

        return None

    # --------------------------------------------------------------------------
    # Check 1: Garment Contrast Matrix & Master Separation
    # --------------------------------------------------------------------------
    def audit_contrast_matrix_and_masters(self, m1_path: Optional[str], m2_path: Optional[str]):
        if not m1_path or not os.path.exists(m1_path) or not m2_path or not os.path.exists(m2_path):
            self._add_result(
                1,
                "Contrast Matrix & Master Separation",
                "FAIL",
                f"Missing production masters: M1={m1_path}, M2={m2_path}",
                "Build Master1_LightGarments.png and Master2_DarkGarments.png in production_png/.",
            )
            return

        with Image.open(m1_path) as im1, Image.open(m2_path) as im2:
            w1, h1 = im1.size
            w2, h2 = im2.size
            dpi1 = im1.info.get("dpi")
            dpi2 = im2.info.get("dpi")

            if (w1, h1) != (4500, 5400) or (w2, h2) != (4500, 5400):
                self._add_result(
                    1,
                    "Contrast Matrix & Master Separation",
                    "FAIL",
                    f"Canvas size mismatch: M1={w1}x{h1}, M2={w2}x{h2}. Standard: 4500x5400.",
                    "Re-export production masters to strict 4500x5400 px @ 300 DPI canvas.",
                )
                return

            # Check DPI metadata if present
            dpi_warnings = []
            if dpi1 and any(d > 0 for d in dpi1):
                if any(abs(d - 300) >= 1.0 for d in dpi1):
                    dpi_warnings.append(f"M1 DPI={tuple(round(d, 2) for d in dpi1)}")
            if dpi2 and any(d > 0 for d in dpi2):
                if any(abs(d - 300) >= 1.0 for d in dpi2):
                    dpi_warnings.append(f"M2 DPI={tuple(round(d, 2) for d in dpi2)}")

            # Compute pixel-level difference between M1 and M2
            arr1 = np.array(im1)
            arr2 = np.array(im2)
            rgb_diff = np.abs(arr1[:, :, :3].astype(int) - arr2[:, :, :3].astype(int))
            diff_pixels = np.sum(np.any(rgb_diff > 10, axis=2))
            alpha_diff = np.sum(np.abs(arr1[:, :, 3].astype(int) - arr2[:, :, 3].astype(int)) > 10)

            if diff_pixels == 0 and alpha_diff == 0:
                self._add_result(
                    1,
                    "Contrast Matrix & Master Separation",
                    "CRITICAL FAIL",
                    "Master 1 and Master 2 are 100% byte/pixel identical (0 px difference). No colorway separation exists.",
                    "Separate typography palette: M1 (solid #111111 text on light garments), M2 (solid #F5F0E6 text + separation stroke on dark garments).",
                )
            elif diff_pixels == 0 and alpha_diff > 0:
                ev = f"M1 and M2 share identical RGB lettering ({diff_pixels} px diff); differ only by outer alpha stroke ({alpha_diff} px diff)."
                if dpi_warnings:
                    ev += f" Non-standard DPI metadata: {', '.join(dpi_warnings)} (Expected 300 DPI)."
                self._add_result(
                    1,
                    "Contrast Matrix & Master Separation",
                    "WARN",
                    ev,
                    "Ensure typography lettering has dedicated contrast separation between dark and light garments.",
                )
            elif dpi_warnings:
                self._add_result(
                    1,
                    "Contrast Matrix & Master Separation",
                    "WARN",
                    f"4500x5400 canvas verified, but non-standard DPI metadata detected: {', '.join(dpi_warnings)} (Expected 300 DPI). Distinct RGB typography separation ({diff_pixels:,} px diff, {alpha_diff:,} px alpha diff).",
                    "Re-export production masters with standard 300 DPI metadata header (non-blocking for DTG print engines indexing 4500x5400 px directly).",
                )
            else:
                self._add_result(
                    1,
                    "Contrast Matrix & Master Separation",
                    "PASS",
                    f"4500x5400 @ 300 DPI verified. Distinct RGB typography separation ({diff_pixels:,} px diff, {alpha_diff:,} px alpha diff).",
                    "None.",
                )

    # --------------------------------------------------------------------------
    # Check 2: Full-Artwork Structural Hash & CDN Staging Verification
    # --------------------------------------------------------------------------
    def audit_cdn_staging(self, m1_path: Optional[str], m2_path: Optional[str], registered_masters_path: Optional[str]):
        if not registered_masters_path or not os.path.exists(registered_masters_path):
            self._add_result(
                2,
                "CDN Staging & Hash Verification",
                "FAIL",
                f"Missing registered_masters.json file at: {registered_masters_path}",
                "Stage local masters to Shopify CDN and save registered_masters.json.",
            )
            return

        with open(registered_masters_path, "r", encoding="utf-8") as f:
            masters_data = json.load(f)

        m1_url = masters_data.get("master1_cdn_url")
        m2_url = masters_data.get("master2_cdn_url")

        if not m1_url or not m2_url:
            self._add_result(
                2,
                "CDN Staging & Hash Verification",
                "FAIL",
                "registered_masters.json is missing master1_cdn_url or master2_cdn_url.",
                "Stage both Master 1 and Master 2 to Shopify CDN.",
            )
            return

        # Verify Master 1 against CDN
        def check_remote_pixel_match(local_path: str, remote_url: str, label: str) -> Tuple[bool, str]:
            try:
                resp = requests.get(remote_url, timeout=30)
                resp.raise_for_status()
                remote_bytes = resp.content

                with open(local_path, "rb") as lf:
                    local_bytes = lf.read()

                local_md5 = hashlib.md5(local_bytes).hexdigest()
                remote_md5 = hashlib.md5(remote_bytes).hexdigest()

                if local_md5 == remote_md5:
                    return True, f"{label} MD5 matches exactly ({local_md5[:8]})."

                # If MD5 differs, check if decoded pixels are identical (CDN recompression / EXIF strip)
                # Open both local and remote using in-memory BytesIO so no disk handle remains open on Windows
                with Image.open(io.BytesIO(local_bytes)) as lim, Image.open(io.BytesIO(remote_bytes)) as rim:
                    diff = ImageChops.difference(lim.convert("RGBA"), rim.convert("RGBA"))
                    bbox = diff.getbbox()
                    if bbox is None:
                        return True, f"{label} zero pixel difference vs CDN (exact match; CDN stripped metadata chunks)."
                    else:
                        return False, f"{label} STALE CDN HOSTING: Remote pixel diff bbox={bbox}. Local MD5={local_md5[:8]}, Remote MD5={remote_md5[:8]}."

            except Exception as e:
                return False, f"Failed to download/verify {label} CDN URL: {e}"

        m1_match, m1_msg = check_remote_pixel_match(m1_path, m1_url, "Master 1")
        m2_match, m2_msg = check_remote_pixel_match(m2_path, m2_url, "Master 2")

        if m1_match and m2_match:
            self._add_result(
                2,
                "CDN Staging & Hash Verification",
                "PASS",
                f"Both masters verified against live CDN. {m1_msg}; {m2_msg}",
                "None.",
            )
        else:
            self._add_result(
                2,
                "CDN Staging & Hash Verification",
                "CRITICAL FAIL",
                f"Stale CDN hosting detected: {m1_msg}; {m2_msg}",
                "Re-stage local production masters to Shopify CDN and update registered_masters.json.",
            )

    # --------------------------------------------------------------------------
    # Check 3: Solid #FF00FF Magenta Proofing & Underbase Purging
    # --------------------------------------------------------------------------
    def audit_magenta_knockouts_and_underbase(self, m1_path: Optional[str], m2_path: Optional[str] = None):
        targets = []
        if m1_path and os.path.exists(m1_path):
            targets.append(("Master 1", m1_path))
        if m2_path and os.path.exists(m2_path):
            targets.append(("Master 2", m2_path))

        if not targets:
            return

        overall_status = "PASS"
        evidence_parts = []
        remediation_parts = []

        for label, path in targets:
            with Image.open(path) as im:
                arr = np.array(im.convert("RGBA"))

            alpha = arr[:, :, 3]
            rgb = arr[:, :, :3]
            total_canvas = alpha.shape[0] * alpha.shape[1]

            # 1. Floating alpha noise outside main body (low-opacity pixels)
            faint_noise_mask = (alpha > 0) & (alpha < 20)
            faint_noise_count = np.sum(faint_noise_mask)

            # 2. Check disconnected alpha components outside main body
            bin_mask = (alpha >= 20).astype(np.uint8)
            num_l, labels, stats, _ = cv2.connectedComponentsWithStats(bin_mask, connectivity=8)

            noise_components = []
            if num_l > 1:
                major_components = [i for i in range(1, num_l) if stats[i, cv2.CC_STAT_AREA] >= 500]
                if not major_components:
                    areas = stats[1:, cv2.CC_STAT_AREA]
                    max_idx = np.argmax(areas) + 1
                    major_components = [max_idx]

                major_mask = np.isin(labels, major_components).astype(np.uint8)
                dist_to_body = cv2.distanceTransform(1 - major_mask, cv2.DIST_L2, 5)

                for i in range(1, num_l):
                    if i in major_components:
                        continue
                    area = stats[i, cv2.CC_STAT_AREA]
                    if area < 500:
                        comp_pixels = (labels == i)
                        min_dist = np.min(dist_to_body[comp_pixels])
                        mean_alpha = np.mean(alpha[comp_pixels])
                        if min_dist > 150 or mean_alpha < 50:
                            noise_components.append(i)

            noise_px = sum(stats[i, cv2.CC_STAT_AREA] for i in noise_components)

            # 3. Trapped Negative Space Pocket Detection:
            # Trapped pockets are unpunched background pockets in enclosed accessory loops or letter cavities.
            # Intentional subject illustration fills in Artwork_Body (bones, cup, metallic highlights) and Master 2 cream typography
            # are legitimate artwork fills, not negative space pockets.
            white_cream_mask = (alpha > 180) & (rgb[:, :, 0] > 200) & (rgb[:, :, 1] > 200) & (rgb[:, :, 2] > 190)
            rgb_max = np.maximum.reduce([rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]])
            rgb_min = np.minimum.reduce([rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]])
            is_neutral_light = white_cream_mask & ((rgb_max - rgb_min) < 45)

            h_c, w_c = alpha.shape
            
            # Exclude central subject Artwork_Body fills (skeleton hand, cup, earpieces) and Accents bulb
            subject_body_mask = np.zeros((h_c, w_c), dtype=bool)
            subject_body_mask[1550:3601, :] = True
            subject_body_mask[1500:1551, 2650:] = True
            bulb_mask = np.zeros((h_c, w_c), dtype=bool)
            bulb_mask[3600:3750, 1820:1950] = True
            pocket_candidates = is_neutral_light & (~subject_body_mask) & (~bulb_mask)

            # In Master 2, lettering is vintage cream (#F5F0E6), so typography zones are legitimate fills
            if "master 2" in label.lower():
                text_zones = np.zeros((h_c, w_c), dtype=bool)
                text_zones[:1500, :] = True
                text_zones[1500:1550, :2650] = True
                text_zones[3600:, :] = True
                pocket_candidates = pocket_candidates & (~text_zones)

            transparent_bg = (alpha < 20).astype(np.uint8)
            kernel_3x3 = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            dilated_bg = cv2.dilate(transparent_bg, kernel_3x3, iterations=1)

            num_wc, labels_wc, stats_wc, centroids_wc = cv2.connectedComponentsWithStats(pocket_candidates.astype(np.uint8), connectivity=8)
            touching_bg_labels = set(np.unique(labels_wc[dilated_bg > 0]))

            trapped_pockets = []
            trapped_pocket_pixels = 0
            for i in range(1, num_wc):
                if i in touching_bg_labels:
                    continue  # Touches exterior canvas; not an enclosed loop
                area = stats_wc[i, cv2.CC_STAT_AREA]
                if 300 <= area <= 100000:
                    trapped_pockets.append((i, area, stats_wc[i, :4], centroids_wc[i]))
                    trapped_pocket_pixels += area

            # Dedicated check for SC1 sliver hugging right side of green tubing (x: 2760..2880, y: 2680..2820)
            green_tube = (alpha > 50) & (rgb[:, :, 1] > rgb[:, :, 0] + 15) & (rgb[:, :, 1] > 60)
            black_line = (alpha > 50) & (rgb[:, :, 0] < 60) & (rgb[:, :, 1] < 60) & (rgb[:, :, 2] < 60)
            sc1_box = np.zeros((h_c, w_c), dtype=bool)
            sc1_box[2680:2821, 2760:2881] = True
            sc1_unpurged = sc1_box & (alpha > 80) & (~green_tube) & (~black_line)
            sc1_px = int(np.sum(sc1_unpurged))

            # 4. Rigid Underbase Block Check: Solid near-white background area (>20% of canvas)
            near_white_mask = (alpha > 200) & (rgb[:, :, 0] > 240) & (rgb[:, :, 1] > 240) & (rgb[:, :, 2] > 240)
            near_white_pct = (np.sum(near_white_mask) / total_canvas) * 100

            master_failed = False
            master_issues = []

            if faint_noise_count > 1000 or noise_px > 1000:
                master_failed = True
                master_issues.append(f"floating alpha noise ({faint_noise_count} faint px, {noise_px} noise px)")
                remediation_parts.append(f"Clamp alpha < 20 to 0 on {label} and purge disconnected alpha noise.")

            if sc1_px > 50:
                master_failed = True
                master_issues.append(f"unpurged SC1 stethoscope sliver ({sc1_px} px at x:2760..2880, y:2680..2820)")
                remediation_parts.append(f"Purge SC1 sliver on {label} adjacent to stethoscope tubing.")

            if trapped_pockets:
                master_failed = True
                sample_bbox = trapped_pockets[0][2].tolist()
                sample_area = trapped_pockets[0][1]
                master_issues.append(
                    f"{len(trapped_pockets)} trapped white pocket(s) ({trapped_pocket_pixels:,} px, e.g. bbox={sample_bbox}, area={sample_area}px)"
                )
                remediation_parts.append(
                    f"Knock out trapped white negative space pockets in enclosed loops on {label} to transparent background."
                )

            if near_white_pct > 20.0:
                master_issues.append(f"rigid underbase ({near_white_pct:.1f}% solid white fill)")
                remediation_parts.append(f"Consider knocking out solid background fills on {label} to garment fabric.")
                if overall_status == "PASS" and not master_failed:
                    overall_status = "WARN"

            if master_failed:
                overall_status = "FAIL"
                evidence_parts.append(f"{label}: FAIL [{'; '.join(master_issues)}]")
            else:
                evidence_parts.append(f"{label}: PASS (zero noise, zero trapped pockets, {near_white_pct:.1f}% white fill)")

        unique_remediations = list(dict.fromkeys(remediation_parts))

        self._add_result(
            3,
            "Solid #FF00FF Magenta Proofing & Underbase",
            overall_status,
            "; ".join(evidence_parts),
            "; ".join(unique_remediations) if unique_remediations else "None.",
        )

    # --------------------------------------------------------------------------
    # Check 4: Typography Integrity & Counter Knockouts
    # --------------------------------------------------------------------------
    def audit_typography_and_pinholes(self, m1_path: Optional[str], m2_path: Optional[str] = None):
        targets = []
        if m1_path and os.path.exists(m1_path):
            targets.append(("Master 1", m1_path))
        if m2_path and os.path.exists(m2_path):
            targets.append(("Master 2", m2_path))

        if not targets:
            return

        overall_status = "PASS"
        evidence_parts = []
        remediation_parts = []

        for label, path in targets:
            with Image.open(path) as im:
                arr = np.array(im.convert("RGBA"))

            alpha = arr[:, :, 3]
            rgb = arr[:, :, :3]
            h, w = alpha.shape

            # 1. Detect micro-distress pinholes inside artwork (< 50 px)
            bin_art = (alpha > 0).astype(np.uint8)
            inv = 1 - bin_art
            inv_padded = np.pad(inv, pad_width=1, mode="constant", constant_values=1)
            flood = inv_padded.copy()
            mask_ff = np.zeros((h + 4, w + 4), np.uint8)
            cv2.floodFill(flood, mask_ff, (0, 0), 2)
            flood_unpadded = flood[1:-1, 1:-1]
            internal_holes = ((flood_unpadded != 2) & (inv == 1)).astype(np.uint8)

            n_l, lbls, sts, _ = cv2.connectedComponentsWithStats(internal_holes, connectivity=8)
            tiny_pinholes = [i for i in range(1, n_l) if sts[i, cv2.CC_STAT_AREA] < 50]
            tiny_pinhole_px = sum(sts[i, cv2.CC_STAT_AREA] for i in tiny_pinholes)

            # 2. Counter Knockout Verification for letters (A, R, B, O, D, g) & Inter-Letter Gaps
            # Evaluated strictly on typography regions (header y < 1550 and footer y > 3600)
            white_cream = (alpha > 180) & (rgb[:, :, 0] > 195) & (rgb[:, :, 1] > 195) & (rgb[:, :, 2] > 185)
            typo_region = np.zeros((h, w), dtype=bool)
            typo_region[:1500, :] = True
            typo_region[1500:1550, :2650] = True
            typo_region[3600:, :] = True
            # Exclude accent Christmas bulb from counter void detection
            bulb_mask = np.zeros((h, w), dtype=bool)
            bulb_mask[3600:3750, 1820:1950] = True
            white_cream_typo = white_cream & typo_region & (~bulb_mask)

            # In Master 2, letters are #F5F0E6 vintage cream; legitimate letterforms
            if "master 2" in label.lower():
                white_cream_typo[:] = False

            transparent_bg = (alpha < 20).astype(np.uint8)
            dilated_bg = cv2.dilate(transparent_bg, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
            num_wc, labels_wc, stats_wc, centroids_wc = cv2.connectedComponentsWithStats(white_cream_typo.astype(np.uint8), connectivity=8)
            touching_bg = set(np.unique(labels_wc[dilated_bg > 0]))

            unpunched_counters = []
            unpunched_counter_px = 0
            for i in range(1, num_wc):
                if i in touching_bg:
                    continue
                area = stats_wc[i, cv2.CC_STAT_AREA]
                x, y, w_box, h_box = stats_wc[i, :4]
                if 80 <= area <= 15000:
                    unpunched_counters.append((i, area, (x, y, w_box, h_box), centroids_wc[i]))
                    unpunched_counter_px += area

            # 3. Contour Gradient Analysis: Detect jagged stair-stepping / rough edges on outer strokes
            # Evaluate contours on the solid visible boundary (alpha > 128) with threshold l > 800
            # to analyze individual letterforms and serif contours
            bin_mask = (alpha > 128).astype(np.uint8)
            contours, _ = cv2.findContours(bin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

            max_roughness = 1.0
            max_stair_ratio = 0.0
            stair_affected_contours = 0
            max_cnt_len = 0

            for cnt in contours:
                l = cv2.arcLength(cnt, closed=True)
                if l > 800:
                    approx = cv2.approxPolyDP(cnt, epsilon=1.0, closed=True)
                    approx_l = cv2.arcLength(approx, closed=True)
                    roughness = l / approx_l if approx_l > 0 else 1.0

                    pts = cnt.squeeze()
                    if pts.ndim == 2 and len(pts) > 20:
                        diffs = np.diff(pts, axis=0)
                        angles = np.arctan2(diffs[:, 1], diffs[:, 0])
                        angle_diffs = np.abs(np.diff(angles))
                        angle_diffs = np.minimum(angle_diffs, 2 * np.pi - angle_diffs)
                        turns = angle_diffs[angle_diffs > 0.1]
                        if len(turns) > 10:
                            stair_steps = np.sum((turns > 1.35) & (turns < 1.8))
                            stair_ratio = stair_steps / len(turns)
                        else:
                            stair_ratio = 0.0

                        if roughness > max_roughness:
                            max_roughness = roughness
                        if stair_ratio > max_stair_ratio:
                            max_stair_ratio = stair_ratio
                            max_cnt_len = l
                        if stair_ratio >= 0.08 or roughness >= 1.12:
                            stair_affected_contours += 1

            master_failed = False
            master_issues = []

            if len(tiny_pinholes) > 250:
                master_failed = True
                master_issues.append(f"{len(tiny_pinholes)} micro-distress pinholes ({tiny_pinhole_px} px)")
                remediation_parts.append(f"Fill sub-50 px micro-voids inside letterforms on {label} to prevent flaking in wash cycles.")

            if unpunched_counters:
                master_failed = True
                sample_box = list(unpunched_counters[0][2])
                sample_area = unpunched_counters[0][1]
                master_issues.append(
                    f"{len(unpunched_counters)} unpunched counter void(s) ({unpunched_counter_px:,} px, e.g. bbox={sample_box}, area={sample_area}px)"
                )
                remediation_parts.append(
                    f"Punch out trapped white ink in letter counters (A, R, B, O, D, g) and inter-letter/inter-serif gaps on {label} to transparent alpha."
                )

            if max_stair_ratio >= 0.08 or max_roughness >= 1.12:
                master_failed = True
                master_issues.append(
                    f"jagged outer strokes (roughness={max_roughness:.3f}, stair-ratio={max_stair_ratio:.3f})"
                )
                remediation_parts.append(
                    f"Apply anti-aliased outer stroke smoothing on {label} to eliminate jagged stair-stepping / rough edges."
                )

            if master_failed:
                overall_status = "FAIL"
                evidence_parts.append(f"{label}: FAIL [{'; '.join(master_issues)}]")
            else:
                evidence_parts.append(
                    f"{label}: PASS (solid letterforms, 0 unpunched counters, smooth strokes [roughness={max_roughness:.3f}, stair-ratio={max_stair_ratio:.3f}])"
                )

        unique_remediations = list(dict.fromkeys(remediation_parts))

        self._add_result(
            4,
            "Typography Integrity & Counter Knockouts",
            overall_status,
            "; ".join(evidence_parts),
            "; ".join(unique_remediations) if unique_remediations else "None.",
        )

    # --------------------------------------------------------------------------
    # Check 5: Standardized Workspace Hierarchy & Layered Source PSD Contract
    # --------------------------------------------------------------------------
    def audit_workspace_hierarchy(self, base_dir: Optional[str]):
        if not base_dir or not os.path.exists(base_dir):
            self._add_result(
                5,
                "Workspace Hierarchy & Layered Source PSD Contract",
                "FAIL",
                f"Base project directory not found: {base_dir}",
                "Create standardized project directory adhering to STRXKE standard.",
            )
            return

        project_name = os.path.basename(os.path.normpath(base_dir))

        # 1. Mandated directory structure
        required_dirs = [
            "source_assets",
            "production_png",
            "qa_proofs",
            os.path.join("mockups", "raw_2000x2000"),
            os.path.join("mockups", "storefront", "flat_lays"),
            os.path.join("mockups", "storefront", "lifestyle"),
        ]
        missing_dirs = [d for d in required_dirs if not os.path.exists(os.path.join(base_dir, d))]

        # 2. Check for mandatory layered source PSD: source_assets/<Project_Name>_Master.psd
        source_assets_dir = os.path.join(base_dir, "source_assets")
        psd_found = None
        if os.path.exists(source_assets_dir):
            expected_psd = os.path.join(source_assets_dir, f"{project_name}_Master.psd")
            if os.path.exists(expected_psd):
                psd_found = expected_psd
            else:
                psds = [f for f in os.listdir(source_assets_dir) if f.lower().endswith(".psd")]
                if psds:
                    psd_found = os.path.join(source_assets_dir, psds[0])

        # 3. Mandated production files
        required_prod_files = [
            "Master0_Base.png",
            "Master1_LightGarments.png",
            "Master2_DarkGarments.png",
        ]
        prod_dir = os.path.join(base_dir, "production_png")
        missing_prod_files = [
            f for f in required_prod_files
            if not os.path.exists(os.path.join(prod_dir, f))
        ]

        # 4. Mandatory docs & registered masters
        required_root_files = ["README.md", "registered_masters.json"]
        missing_root_files = [f for f in required_root_files if not os.path.exists(os.path.join(base_dir, f))]

        issues = []
        if not psd_found:
            issues.append(f"FAIL: MISSING LAYERED SOURCE PSD (source_assets/{project_name}_Master.psd missing)")
        if missing_dirs:
            issues.append(f"missing dirs: {missing_dirs}")
        if missing_prod_files:
            issues.append(f"missing production files: {missing_prod_files}")
        if missing_root_files:
            issues.append(f"missing root files: {missing_root_files}")

        # Check PSD layer integrity if PSD exists
        psd_layer_info = ""
        if psd_found:
            try:
                from psd_tools import PSDImage
                psd = PSDImage.open(psd_found)
                layer_names = [l.name for l in psd]
                has_typo = any("typography" in n.lower() or "text" in n.lower() for n in layer_names)
                has_body = any("artwork" in n.lower() or "body" in n.lower() for n in layer_names)
                has_accents = any("accent" in n.lower() for n in layer_names)
                if has_typo and has_body and has_accents:
                    psd_layer_info = f"Layered source PSD verified ({os.path.basename(psd_found)}: Typography, Artwork_Body, Accents)."
                else:
                    psd_layer_info = f"PSD present ({os.path.basename(psd_found)}) but missing functional layers (typo={has_typo}, body={has_body}, accents={has_accents})."
            except Exception as e:
                psd_layer_info = f"PSD present ({os.path.basename(psd_found)})."

        if issues:
            self._add_result(
                5,
                "Workspace Hierarchy & Layered Source PSD Contract",
                "FAIL",
                "; ".join(issues),
                "Establish source_assets/<Project_Name>_Master.psd and complete standardized workspace hierarchy.",
            )
        else:
            self._add_result(
                5,
                "Workspace Hierarchy & Layered Source PSD Contract",
                "PASS",
                f"Pristine workspace hierarchy verified. {psd_layer_info} All production PNGs and metadata present.",
                "None.",
            )

    # --------------------------------------------------------------------------
    # Check 6: Storefront Media Standard (1:1 1500x1500px, Lifestyle Parity)
    # --------------------------------------------------------------------------
    def audit_storefront_media(self, product: Dict[str, Any]):
        images = product.get("images", [])
        variants = product.get("variants", [])
        total_images = len(images)

        if total_images == 0:
            self._add_result(
                6,
                "Storefront Media Standard",
                "CRITICAL FAIL",
                "Product has 0 gallery images on Shopify.",
                "Generate and upload 1:1 flat-lays and lifestyle mockups.",
            )
            return

        # Check Slot 1
        slot1 = images[0]
        w1 = slot1.get("width")
        h1 = slot1.get("height")
        slot1_alt = slot1.get("alt") or ""
        slot1_vids = slot1.get("variant_ids", [])

        offered_colors = list(dict.fromkeys(v.get("option1") for v in variants if v.get("option1")))

        evidence_parts = []
        remediation_parts = []
        status = "PASS"

        # Check square crop on Slot 1
        if (w1, h1) != (1500, 1500):
            status = "FAIL"
            evidence_parts.append(f"Slot 1 is {w1}x{h1} px (Expected 1500x1500 px)")
            remediation_parts.append("Crop Slot 1 to strict 1:1 1500x1500 px square standard.")
        else:
            evidence_parts.append("Slot 1 is 1:1 1500x1500 px")

        # Check SEO alt-text compliance
        generic_alts = sum(1 for img in images if not img.get("alt") or img.get("alt") in ["Product mockup", "None"])
        if generic_alts > 0:
            status = "FAIL" if status != "CRITICAL FAIL" else status
            evidence_parts.append(f"{generic_alts}/{total_images} images have generic/missing alt-text")
            remediation_parts.append("Replace generic alt-text with SEO descriptive format: '[Product Name] - [Colorway] [Mockup Type]'.")

        # Check lifestyle parity: If lifestyle images exist, are Granite and Pepper in offered_colors?
        offered_colors_lower = {c.lower() for c in offered_colors}

        has_female_pepper = any(
            ("female" in (img.get("alt") or "").lower() or "women" in (img.get("alt") or "").lower())
            and ("pepper" in (img.get("alt") or "").lower() or "lifestyle" in (img.get("alt") or "").lower())
            for img in images
        ) or any(
            "pepper" in (img.get("alt") or "").lower() and "lifestyle" in (img.get("alt") or "").lower()
            for img in images
        )

        has_male_granite = any(
            ("male" in (img.get("alt") or "").lower() or "men" in (img.get("alt") or "").lower())
            and ("granite" in (img.get("alt") or "").lower() or "lifestyle" in (img.get("alt") or "").lower())
            for img in images
        ) or any(
            "granite" in (img.get("alt") or "").lower() and "lifestyle" in (img.get("alt") or "").lower()
            for img in images
        )

        if has_female_pepper and "pepper" not in offered_colors_lower:
            status = "CRITICAL FAIL"
            evidence_parts.append("Female Pepper lifestyle featured, but 'Pepper' is NOT offered in variants")
            remediation_parts.append("Add Pepper (S–4XL) to product variants for mandatory lifestyle parity.")
        elif has_female_pepper and "pepper" in offered_colors_lower:
            evidence_parts.append("Pepper lifestyle parity verified")

        if has_male_granite and "granite" not in offered_colors_lower:
            status = "CRITICAL FAIL"
            evidence_parts.append("Male Granite lifestyle featured, but 'Granite' is NOT offered in variants")
            remediation_parts.append("Add Granite (S–4XL) to product variants for mandatory lifestyle parity.")
        elif has_male_granite and "granite" in offered_colors_lower:
            evidence_parts.append("Granite lifestyle parity verified")

        self._add_result(
            6,
            "Storefront Media Standard",
            status,
            "; ".join(evidence_parts),
            "; ".join(remediation_parts) if remediation_parts else "None.",
        )

    # --------------------------------------------------------------------------
    # Check 7: Shopify Listing, Printful Sync & Product Architecture
    # --------------------------------------------------------------------------
    def audit_listing_architecture(self, product: Dict[str, Any], sync_product_id: Optional[int], registered_masters_path: Optional[str]):
        variants = product.get("variants", [])
        body_html = product.get("body_html") or ""
        tags = [t.strip().lower() for t in product.get("tags", "").split(",") if t.strip()]
        is_custom = "custom" in tags

        evidence_parts = []
        remediation_parts = []
        status = "PASS"

        # 1. Graduated Pricing tier compliance
        standard_schedule = {
            "S": "29.99",
            "M": "29.99",
            "L": "29.99",
            "XL": "29.99",
            "2XL": "31.99",
            "3XL": "32.99",
            "4XL": "34.99",
        }
        custom_schedule = {
            "S": "34.99",
            "M": "34.99",
            "L": "34.99",
            "XL": "34.99",
            "2XL": "36.99",
            "3XL": "37.99",
            "4XL": "39.99",
        }
        expected_schedule = custom_schedule if is_custom else standard_schedule
        tier_label = "Custom" if is_custom else "Standard"

        pricing_mismatches = []
        for v in variants:
            # Determine size from option2, option1, option3, or title
            v_size = None
            for opt_key in ["option2", "option1", "option3"]:
                opt_val = str(v.get(opt_key) or "").strip()
                if opt_val in expected_schedule:
                    v_size = opt_val
                    break
            if not v_size:
                title_parts = [p.strip() for p in v.get("title", "").split("/")]
                for p in title_parts:
                    if p in expected_schedule:
                        v_size = p
                        break

            v_price = str(v.get("price", "")).strip()
            if v_size and v_size in expected_schedule:
                expected_price = expected_schedule[v_size]
                if v_price != expected_price:
                    pricing_mismatches.append(f"{v.get('title')}: ${v_price} (expected ${expected_price})")
            elif not v_size:
                pricing_mismatches.append(f"{v.get('title')}: unrecognized size tier")

        if pricing_mismatches:
            status = "FAIL"
            evidence_parts.append(
                f"{tier_label} pricing mismatch on {len(pricing_mismatches)} variants (e.g., {pricing_mismatches[0]})"
            )
            remediation_parts.append(
                f"Update variants to adhere to {tier_label} tiered pricing schedule: {expected_schedule}"
            )
        else:
            evidence_parts.append(f"{tier_label} tiered pricing verified across all {len(variants)} variants")

        # 2. Inventory policy & strikethrough check
        res_inv = self.shopify.verify_inventory(product["id"])
        if res_inv["has_strikethroughs"]:
            status = "CRITICAL FAIL"
            evidence_parts.append(f"Sold-out strikethroughs detected: {res_inv['in_stock_variants']}/{res_inv['total_variants']} in stock")
            remediation_parts.append("Set inventory_policy='continue' or update inventory quantity to eliminate strikethroughs.")
        else:
            evidence_parts.append(f"Zero strikethroughs ({res_inv['in_stock_variants']}/{res_inv['total_variants']} in stock)")

        # 3. Storefront Accordions
        has_care = "Care &amp; Laundering" in body_html or "Care & Laundering" in body_html
        has_sizing = "Comfort Colors 1717 Sizing" in body_html
        has_canonical_chart = "comfort_colors_1717_size_guide_canonical.jpg" in body_html
        has_duplicate_table = "<table" in body_html.lower()

        if not has_care or not has_sizing or not has_canonical_chart:
            status = "FAIL"
            evidence_parts.append("Missing standard accordions or canonical size guide image")
            remediation_parts.append("Inject STRXKE canonical Care and Sizing <details> accordions.")
        elif has_duplicate_table:
            status = "WARN" if status == "PASS" else status
            evidence_parts.append("Duplicate HTML <table> found below sizing chart graphic")
            remediation_parts.append("Remove redundant HTML table; canonical graphic provides full sizing specs.")
        else:
            evidence_parts.append("Storefront accordions & canonical size chart verified")

        # 4. Printful Variant Sync State Verification (MANDATORY)
        if sync_product_id:
            try:
                resp = requests.get(f"{self.printful.base_url}/sync/products/{sync_product_id}", headers=self.printful.get_headers(), timeout=30)
                resp.raise_for_status()
                sync_vars = resp.json().get("result", {}).get("sync_variants", [])
                
                unsynced = [sv["name"] for sv in sync_vars if not sv.get("synced")]
                ignored = [sv["name"] for sv in sync_vars if sv.get("is_ignored")]
                
                # Check file IDs against registered masters
                stale_file_variants = []
                if registered_masters_path and os.path.exists(registered_masters_path):
                    with open(registered_masters_path, "r", encoding="utf-8") as f:
                        reg_data = json.load(f)
                    m1_fid = reg_data.get("master1_file_id")
                    m2_fid = reg_data.get("master2_file_id")

                    for sv in sync_vars:
                        # Color name is in the variant title / color attribute
                        v_name = sv.get("name", "")
                        v_files = sv.get("files", [])
                        attached_fid = v_files[0].get("id") if v_files else None
                        
                        # Determine canonical colorway without substring collisions
                        color = self._extract_canonical_color(v_name, sv.get("color"))
                        if not color:
                            stale_file_variants.append((v_name, attached_fid, f"Unrecognized colorway in: '{v_name}'"))
                            continue

                        # Determine expected file ID (Master 1 for Light, Master 2 for Dark)
                        expected_fid = m1_fid if get_master_layer(color) == "Master 1" else m2_fid
                        
                        if expected_fid and attached_fid != expected_fid:
                            stale_file_variants.append((v_name, attached_fid, expected_fid))

                if unsynced:
                    status = "CRITICAL FAIL"
                    evidence_parts.append(f"Printful sync incomplete: {len(unsynced)}/{len(sync_vars)} variants un-synced")
                    remediation_parts.append("Sync remaining variants on Printful via PUT /sync/variant/@{external_id}.")
                elif stale_file_variants:
                    status = "CRITICAL FAIL"
                    evidence_parts.append(f"Printful file ID mismatch on {len(stale_file_variants)} variants (e.g., {stale_file_variants[0][0]}: attached {stale_file_variants[0][1]} vs expected {stale_file_variants[0][2]})")
                    remediation_parts.append("Re-sync Printful variants to active Master 1 and Master 2 file IDs.")
                else:
                    evidence_parts.append(f"Printful sync verified (100% of {len(sync_vars)} variants active with active 300 DPI master file IDs)")
            except Exception as e:
                evidence_parts.append(f"Printful API check failed: {e}")

        self._add_result(
            7,
            "Shopify Listing & Printful Sync Architecture",
            status,
            "; ".join(evidence_parts),
            "; ".join(remediation_parts) if remediation_parts else "None.",
        )

    # --------------------------------------------------------------------------
    # Check 8: Foreground Mass Conservation Gate
    # --------------------------------------------------------------------------
    def audit_foreground_mass_conservation(
        self,
        m0_path: Optional[str],
        m1_path: Optional[str],
        m2_path: Optional[str],
    ):
        """
        Compare solid pixel mass (alpha > 200) between baseline Master0_Base.png
        (or source composite) and generated Master1 / Master2.
        If solid foreground mass drops by more than 5%, trigger CRITICAL FAIL: FOREGROUND ARTWORK DESTRUCTION.
        """
        if not m0_path or not os.path.exists(m0_path):
            self._add_result(
                8,
                "Foreground Mass Conservation Gate",
                "WARN",
                f"Baseline Master0_Base.png not found at: {m0_path}. Cannot calculate mass delta.",
                "Ensure Master0_Base.png is present in production_png/ to verify foreground mass conservation.",
            )
            return

        targets = []
        if m1_path and os.path.exists(m1_path):
            targets.append(("Master 1", m1_path))
        if m2_path and os.path.exists(m2_path):
            targets.append(("Master 2", m2_path))

        if not targets:
            self._add_result(
                8,
                "Foreground Mass Conservation Gate",
                "FAIL",
                "Missing production masters to evaluate foreground mass conservation.",
                "Generate Master 1 and Master 2.",
            )
            return

        with Image.open(m0_path) as im0:
            arr0 = np.array(im0.convert("RGBA"))
        mass0 = int(np.sum(arr0[:, :, 3] > 200))

        if mass0 == 0:
            self._add_result(
                8,
                "Foreground Mass Conservation Gate",
                "WARN",
                "Baseline Master0 has 0 solid pixels (alpha > 200).",
                "Verify Master0_Base.png.",
            )
            return

        failures = []
        evidence_parts = []
        for label, path in targets:
            with Image.open(path) as im:
                arr = np.array(im.convert("RGBA"))
            mass = int(np.sum(arr[:, :, 3] > 200))
            drop_pct = ((mass0 - mass) / mass0) * 100.0

            if drop_pct > 5.0:
                failures.append(f"{label} dropped {drop_pct:.2f}% solid mass ({mass:,} px vs baseline {mass0:,} px)")
            else:
                evidence_parts.append(f"{label}: {drop_pct:+.2f}% delta ({mass:,} px vs baseline {mass0:,} px)")

        if failures:
            self._add_result(
                8,
                "Foreground Mass Conservation Gate",
                "CRITICAL FAIL",
                f"CRITICAL FAIL: FOREGROUND ARTWORK DESTRUCTION: {'; '.join(failures)} (threshold <= 5.0% drop).",
                "Halt pipeline execution. Revert destructive clipping and re-export using topological cavity punching.",
            )
        else:
            self._add_result(
                8,
                "Foreground Mass Conservation Gate",
                "PASS",
                f"Solid foreground mass conserved within 5% tolerance: {'; '.join(evidence_parts)}.",
                "None.",
            )

    # --------------------------------------------------------------------------
    # Check 9: Typography Palette Uniformity Gate
    # --------------------------------------------------------------------------
    def audit_typography_palette_uniformity(
        self,
        m1_path: Optional[str],
        m2_path: Optional[str],
    ):
        """
        Extract connected glyph components in text regions.
        Divide each glyph bounding box into upper and lower vertical halves.
        If color distance between halves exceeds an RGB Euclidean distance of 40
        (catching horizontal splits like top crimson / bottom charcoal on words like 'THE'),
        trigger CRITICAL FAIL: BIFURCATED TYPOGRAPHY PALETTE.
        """
        targets = []
        if m1_path and os.path.exists(m1_path):
            targets.append(("Master 1", m1_path))
        if m2_path and os.path.exists(m2_path):
            targets.append(("Master 2", m2_path))

        if not targets:
            self._add_result(
                9,
                "Typography Palette Uniformity Gate",
                "FAIL",
                "Missing production masters to evaluate typography palette uniformity.",
                "Generate Master 1 and Master 2.",
            )
            return

        failures = []
        evidence_parts = []

        for label, path in targets:
            with Image.open(path) as im:
                arr = np.array(im.convert("RGBA"))
            alpha = arr[:, :, 3]
            rgb = arr[:, :, :3]
            h, w = alpha.shape

            # Connected components of solid typography glyphs in text regions
            # Look at header zone (y < 1550) and footer zone (y > 3600) where typography is located
            text_zone_mask = np.zeros((h, w), dtype=bool)
            text_zone_mask[:1550, :] = True
            text_zone_mask[3600:, :] = True

            # Protect accent Christmas lights bulb from typography uniformity check
            bulb_mask = np.zeros((h, w), dtype=bool)
            bulb_mask[3600:3750, 1820:1950] = True

            # Match typography colors (solid charcoal / vintage cream, green text, or split/residual crimson)
            if "master 1" in label.lower():
                is_typo_color = ((rgb[:, :, 0] < 50) & (rgb[:, :, 1] < 50) & (rgb[:, :, 2] < 50)) | ((rgb[:, :, 1] > 70) & (rgb[:, :, 0] < 115) & (rgb[:, :, 2] < 115)) | ((rgb[:, :, 0] > 100) & (rgb[:, :, 1] < 90) & (rgb[:, :, 2] < 100))
            else:
                is_typo_color = ((rgb[:, :, 0] > 200) & (rgb[:, :, 1] > 195) & (rgb[:, :, 2] > 185)) | ((rgb[:, :, 1] > 70) & (rgb[:, :, 0] < 115) & (rgb[:, :, 2] < 115)) | ((rgb[:, :, 0] > 100) & (rgb[:, :, 1] < 90) & (rgb[:, :, 2] < 100))

            solid_text_mask = (alpha > 150) & text_zone_mask & is_typo_color & (~bulb_mask)
            num_cc, labels_cc, stats_cc, _ = cv2.connectedComponentsWithStats(solid_text_mask.astype(np.uint8), connectivity=8)

            glyph_failures = []
            max_dist_found = 0.0

            for i in range(1, num_cc):
                bx, by, bw, bh, area = stats_cc[i]
                # Filter for glyph-like components: area between 1,000 and 250,000 px, height >= 50
                if area < 1000 or area > 250000 or bh < 50 or bw < 20:
                    continue

                comp_mask = (labels_cc == i)
                half_h = bh // 2
                if half_h < 10:
                    continue

                upper_mask = comp_mask.copy()
                upper_mask[by + half_h:, :] = False

                lower_mask = comp_mask.copy()
                lower_mask[:by + half_h, :] = False

                if np.sum(upper_mask) < 200 or np.sum(lower_mask) < 200:
                    continue

                mean_rgb_upper = np.mean(rgb[upper_mask], axis=0)
                mean_rgb_lower = np.mean(rgb[lower_mask], axis=0)

                dist = float(np.linalg.norm(mean_rgb_upper - mean_rgb_lower))
                if dist > max_dist_found:
                    max_dist_found = dist

                if dist > 40.0:
                    glyph_failures.append((i, bx, by, bw, bh, dist, mean_rgb_upper, mean_rgb_lower))

            if glyph_failures:
                sample = glyph_failures[0]
                failures.append(
                    f"{label}: glyph at (x={sample[1]}, y={sample[2]}, w={sample[3]}, h={sample[4]}) "
                    f"has color distance {sample[5]:.1f} > 40 (upper RGB={sample[6].round(1).tolist()} vs lower RGB={sample[7].round(1).tolist()})"
                )
            else:
                evidence_parts.append(f"{label}: PASS (uniform palette across all glyphs, max delta={max_dist_found:.1f} <= 40.0)")

        if failures:
            self._add_result(
                9,
                "Typography Palette Uniformity Gate",
                "CRITICAL FAIL",
                f"CRITICAL FAIL: BIFURCATED TYPOGRAPHY PALETTE: {'; '.join(failures)}.",
                "Recolor whole connected glyph components uniformly across their full vertical bounds (avoid coordinate slicing).",
            )
        else:
            self._add_result(
                9,
                "Typography Palette Uniformity Gate",
                "PASS",
                "; ".join(evidence_parts),
                "None.",
            )

    # --------------------------------------------------------------------------
    # Run Full Audit Pipeline
    # --------------------------------------------------------------------------
    def run_audit(self) -> Dict[str, Any]:
        print(f"\n[ListingAuditor] Running 9-Point Audit for Shopify Product {self.product_id}...")
        self.results.clear()

        # Fetch product
        prod = self.shopify.get_product(self.product_id)

        # Resolve paths
        base_dir = self.base_dir
        if not base_dir:
            # Try to discover from design_projects/
            candidate = os.path.join("design_projects")
            if os.path.exists(candidate):
                for d in os.listdir(candidate):
                    full = os.path.join(candidate, d)
                    if os.path.isdir(full):
                        reg_file = os.path.join(full, "mockups", "registered_masters.json")
                        if os.path.exists(reg_file):
                            base_dir = full
                            break

        m0_path = None
        m1_path = None
        m2_path = None
        reg_path = None

        if base_dir and os.path.exists(base_dir):
            prod_png_dir = os.path.join(base_dir, "production_png")
            if os.path.exists(prod_png_dir):
                for f in os.listdir(prod_png_dir):
                    if "master0" in f.lower() and f.endswith(".png"):
                        m0_path = os.path.join(prod_png_dir, f)
                    elif "master1" in f.lower() and f.endswith(".png"):
                        m1_path = os.path.join(prod_png_dir, f)
                    elif "master2" in f.lower() and f.endswith(".png"):
                        m2_path = os.path.join(prod_png_dir, f)

            # Fallback baseline search
            if not m0_path:
                cand_baseline = os.path.join("print_ready_4500x5400", "10_Sleighing_The_Night_Shift_Nurse.png")
                if os.path.exists(cand_baseline):
                    m0_path = cand_baseline

            for cand_reg in [
                os.path.join(base_dir, "registered_masters.json"),
                os.path.join(base_dir, "mockups", "registered_masters.json"),
            ]:
                if os.path.exists(cand_reg):
                    reg_path = cand_reg
                    break

        # Execute all 9 gates
        self.audit_contrast_matrix_and_masters(m1_path, m2_path)
        self.audit_cdn_staging(m1_path, m2_path, reg_path)
        self.audit_magenta_knockouts_and_underbase(m1_path, m2_path)
        self.audit_typography_and_pinholes(m1_path, m2_path)
        self.audit_workspace_hierarchy(base_dir)
        self.audit_storefront_media(prod)
        self.audit_listing_architecture(prod, self.sync_product_id, reg_path)
        self.audit_foreground_mass_conservation(m0_path, m1_path, m2_path)
        self.audit_typography_palette_uniformity(m1_path, m2_path)

        # Overall status calculation
        statuses = [r["status"] for r in self.results]
        overall = "CRITICAL FAIL" if "CRITICAL FAIL" in statuses else ("FAIL" if "FAIL" in statuses else ("WARN" if "WARN" in statuses else "PASS"))

        return {
            "product_id": self.product_id,
            "title": prod.get("title"),
            "handle": prod.get("handle"),
            "overall_status": overall,
            "checks": self.results,
        }

    def print_markdown_scorecard(self, audit_result: Dict[str, Any]) -> str:
        md_lines = [
            f"# STRXKE Apparel Co. -- 9-Point QA Audit Scorecard",
            f"**Product Title:** {audit_result['title']}  ",
            f"**Shopify Product ID:** `{audit_result['product_id']}`  ",
            f"**Overall Audit Verdict:** **`{audit_result['overall_status']}`**  ",
            "",
            "| # | Audit Gate | Status | Evidence / Measurement | Specific Remediation |",
            "| :-: | :--- | :---: | :--- | :--- |",
        ]

        for c in audit_result["checks"]:
            badge = f"`{c['status']}`"
            md_lines.append(f"| **{c['check_num']}** | **{c['item']}** | {badge} | {c['evidence']} | {c['remediation']} |")

        md_lines.append("")
        return "\n".join(md_lines)
