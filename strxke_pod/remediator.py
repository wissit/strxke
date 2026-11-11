"""
strxke_pod/remediator.py
Deterministic remediation & master derivation engine for STRXKE Apparel Co.
"""

import os
import cv2
import numpy as np
from PIL import Image
from typing import Optional, Tuple, Dict, Any, List

try:
    from psd_tools import PSDImage
    from psd_tools.constants import ColorMode
    HAS_PSD_TOOLS = True
except ImportError:
    HAS_PSD_TOOLS = False

try:
    import pytoshop
    from pytoshop import layers
    from pytoshop.enums import ColorMode as PytoshopColorMode
    HAS_PYTOSHOP = True
except ImportError:
    HAS_PYTOSHOP = False


class MasterRemediator:
    @staticmethod
    def punch_topological_cavities(image_arr: np.ndarray) -> np.ndarray:
        """
        Uses OpenCV 2-level contour tree hierarchy (RETR_TREE) to punch out true enclosed internal 
        negative cavities (glyph counters and accessory loops) without touching foreground artwork.
        """
        arr = image_arr.copy()
        alpha = arr[:, :, 3]
        rgb = arr[:, :, :3]

        # Neutral light/white pixels
        light_mask = ((alpha > 100) & (rgb[:, :, 0] > 180) & (rgb[:, :, 1] > 180) & (rgb[:, :, 2] > 170)).astype(np.uint8)

        contours, hierarchy = cv2.findContours(light_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if hierarchy is not None and len(hierarchy[0]) > 0:
            for idx, cnt in enumerate(contours):
                area = cv2.contourArea(cnt)
                # Punch child contours (enclosed holes) between 50 and 100,000 px that have an outer parent
                parent_idx = hierarchy[0][idx][3]
                if parent_idx != -1 and (50 <= area <= 100000):
                    cv2.drawContours(arr[:, :, 3], [cnt], -1, 0, -1)

        return arr

    @staticmethod
    def punch_micro_bridges(image_arr: np.ndarray, max_bridge_width: int = 4) -> np.ndarray:
        """
        Removes thin inter-serif webbing, pinched cavities, and boundary filaments (<= 4px)
        using morphological opening.
        """
        arr = image_arr.copy()
        alpha = arr[:, :, 3]
        rgb = arr[:, :, :3]

        light_mask = (alpha > 50) & (rgb[:, :, 0] > 180) & (rgb[:, :, 1] > 180) & (rgb[:, :, 2] > 170)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max_bridge_width, max_bridge_width))
        opened = cv2.morphologyEx(light_mask.astype(np.uint8), cv2.MORPH_OPEN, kernel)
        bridges_to_purge = (light_mask.astype(np.uint8) - opened) == 1
        arr[bridges_to_purge, 3] = 0
        return arr

    @staticmethod
    def smooth_outer_boundary(image_arr: np.ndarray, sigma: float = 0.8) -> np.ndarray:
        """
        Applies sub-pixel anti-aliasing strictly to the outer silhouette alpha transition
        while keeping interior artwork 100% solid.
        """
        arr = image_arr.copy()
        alpha = arr[:, :, 3].astype(np.float32) / 255.0

        smoothed = cv2.GaussianBlur(alpha, (3, 3), sigmaX=sigma)
        smoothed[smoothed < 0.08] = 0.0
        smoothed[smoothed > 0.95] = 1.0

        arr[:, :, 3] = (smoothed * 255).astype(np.uint8)
        return arr

    @classmethod
    def export_from_layered_psd(cls, psd_path: str, m1_out: str, m2_out: str):
        """
        Primary Workflow: Renders directly from source PSD layers.
        Alpha-locks and recolors the Typography layer cleanly without touching Artwork_Body.
        Ensures no horizontal color splitting and zero foreground bone/hand destruction.
        Saves both to 4500x5400 @ 300 DPI.
        """
        if not HAS_PSD_TOOLS:
            raise ImportError("psd-tools is required for PSD-first remediation. Run: pip install psd-tools")

        psd = PSDImage.open(psd_path)
        canvas_w, canvas_h = psd.size

        # Find functional layer groups
        typography_layer = None
        artwork_body_layer = None
        accents_layer = None

        for layer in psd:
            name_lower = layer.name.strip().lower()
            if "typography" in name_lower or "text" in name_lower:
                typography_layer = layer
            elif "artwork_body" in name_lower or "artwork" in name_lower or "body" in name_lower or "illustration" in name_lower:
                artwork_body_layer = layer
            elif "accent" in name_lower:
                accents_layer = layer

        # Render layers
        # Base artwork = Artwork_Body + Accents
        base_canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        if artwork_body_layer is not None:
            body_img = artwork_body_layer.composite()
            if body_img is not None:
                body_rgba = body_img.convert("RGBA")
                base_canvas.alpha_composite(body_rgba, (artwork_body_layer.offset[0], artwork_body_layer.offset[1]))

        if accents_layer is not None:
            accent_img = accents_layer.composite()
            if accent_img is not None:
                accent_rgba = accent_img.convert("RGBA")
                base_canvas.alpha_composite(accent_rgba, (accents_layer.offset[0], accents_layer.offset[1]))

        # Render Typography
        typo_canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        if typography_layer is not None:
            t_img = typography_layer.composite()
            if t_img is not None:
                t_rgba = t_img.convert("RGBA")
                typo_canvas.alpha_composite(t_rgba, (typography_layer.offset[0], typography_layer.offset[1]))

        typo_arr = np.array(typo_canvas)
        typo_alpha = typo_arr[:, :, 3]
        typo_rgb = typo_arr[:, :, :3]

        # Preserve accented text (such as green text on 'NIGHT')
        green_text = (typo_alpha > 50) & (typo_rgb[:, :, 1] > 70) & (typo_rgb[:, :, 0] < 115) & (typo_rgb[:, :, 2] < 115)

        # Master 1: Solid #111111 dark charcoal typography
        m1_typo = np.zeros_like(typo_arr)
        m1_typo[:, :, :3] = [17, 17, 17]
        m1_typo[green_text, :3] = typo_rgb[green_text]
        m1_typo[:, :, 3] = typo_alpha
        m1_typo_img = Image.fromarray(m1_typo)

        m1_final = base_canvas.copy()
        m1_final.alpha_composite(m1_typo_img)

        # Master 2: Solid #F5F0E6 vintage cream typography + outer stroke
        # Outer stroke via morphological dilation on alpha
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        dilated_alpha = cv2.dilate(typo_alpha, kernel, iterations=1)
        stroke_alpha = np.maximum(0, dilated_alpha.astype(int) - typo_alpha.astype(int)).astype(np.uint8)

        m2_stroke = np.zeros_like(typo_arr)
        m2_stroke[:, :, :3] = [17, 17, 17]
        m2_stroke[:, :, 3] = stroke_alpha
        m2_stroke_img = Image.fromarray(m2_stroke)

        m2_typo = np.zeros_like(typo_arr)
        m2_typo[:, :, :3] = [245, 240, 230]
        m2_typo[green_text, :3] = typo_rgb[green_text]
        is_outline = (typo_alpha > 50) & (typo_rgb[:, :, 0] < 50) & (typo_rgb[:, :, 1] < 50) & (typo_rgb[:, :, 2] < 50)
        m2_typo[is_outline, :3] = [17, 17, 17]
        m2_typo[:, :, 3] = typo_alpha
        m2_typo_img = Image.fromarray(m2_typo)

        m2_final = base_canvas.copy()
        m2_final.alpha_composite(m2_stroke_img)
        m2_final.alpha_composite(m2_typo_img)

        # Ensure strict 4500x5400 @ 300 DPI
        if m1_final.size != (4500, 5400):
            m1_final = m1_final.resize((4500, 5400), Image.LANCZOS)
        if m2_final.size != (4500, 5400):
            m2_final = m2_final.resize((4500, 5400), Image.LANCZOS)

        os.makedirs(os.path.dirname(os.path.abspath(m1_out)), exist_ok=True)
        os.makedirs(os.path.dirname(os.path.abspath(m2_out)), exist_ok=True)

        m1_final.save(m1_out, dpi=(300, 300), optimize=True)
        m2_final.save(m2_out, dpi=(300, 300), optimize=True)
        print(f"[MasterRemediator] Exported PSD masters:\n  M1: {m1_out}\n  M2: {m2_out}")

    @classmethod
    def create_layered_psd(
        cls,
        psd_out: str,
        typography_arr: Optional[np.ndarray] = None,
        artwork_body_arr: Optional[np.ndarray] = None,
        accents_arr: Optional[np.ndarray] = None,
        layers_list: Optional[List[Dict[str, Any]]] = None,
        canvas_size: Tuple[int, int] = (4500, 5400),
    ):
        """
        Constructs a pristine layered PSD containing the functional layer groups:
        1. Typography
        2. Artwork_Body
        3. Accents
        """
        import gc
        w, h = canvas_size

        if HAS_PYTOSHOP:
            psd = pytoshop.core.PsdFile(num_channels=4, height=h, width=w, depth=8, color_mode=PytoshopColorMode.rgb)

            def make_layer_from_crop(name: str, top: int, bottom: int, left: int, right: int, rgba: np.ndarray) -> layers.LayerRecord:
                r_crop = np.ascontiguousarray(rgba[:, :, 0])
                g_crop = np.ascontiguousarray(rgba[:, :, 1])
                b_crop = np.ascontiguousarray(rgba[:, :, 2])
                a_crop = np.ascontiguousarray(rgba[:, :, 3])

                channel_r = layers.ChannelImageData(image=r_crop, compression=0)
                channel_g = layers.ChannelImageData(image=g_crop, compression=0)
                channel_b = layers.ChannelImageData(image=b_crop, compression=0)
                channel_a = layers.ChannelImageData(image=a_crop, compression=0)

                layer_rec = layers.LayerRecord(
                    top=top,
                    bottom=bottom,
                    left=left,
                    right=right,
                    channels={
                        0: channel_r,
                        1: channel_g,
                        2: channel_b,
                        -1: channel_a,
                    },
                    name=name,
                    opacity=255,
                    visible=True,
                )
                return layer_rec

            layer_records = []
            if layers_list:
                for ldict in layers_list:
                    rec = make_layer_from_crop(
                        name=ldict["name"],
                        top=ldict["top"],
                        bottom=ldict["bottom"],
                        left=ldict["left"],
                        right=ldict["right"],
                        rgba=ldict["rgba"],
                    )
                    layer_records.append(rec)
            else:
                def crop_and_make(name: str, arr: np.ndarray) -> layers.LayerRecord:
                    nonzero = np.where(arr[:, :, 3] > 0)
                    if len(nonzero[0]) == 0:
                        return make_layer_from_crop(name, 0, 10, 0, 10, np.zeros((10, 10, 4), dtype=np.uint8))
                    ymin = int(np.min(nonzero[0]))
                    ymax = int(np.max(nonzero[0]) + 1)
                    xmin = int(np.min(nonzero[1]))
                    xmax = int(np.max(nonzero[1]) + 1)
                    crop = arr[ymin:ymax, xmin:xmax]
                    return make_layer_from_crop(name, ymin, ymax, xmin, xmax, crop)

                if accents_arr is not None:
                    layer_records.append(crop_and_make("Accents", accents_arr))
                if artwork_body_arr is not None:
                    layer_records.append(crop_and_make("Artwork_Body", artwork_body_arr))
                if typography_arr is not None:
                    layer_records.append(crop_and_make("Typography", typography_arr))

            psd.layer_and_mask_info.layer_info.layer_records = layer_records

            os.makedirs(os.path.dirname(os.path.abspath(psd_out)), exist_ok=True)
            with open(psd_out, "wb") as fd:
                psd.write(fd)
            del psd, layer_records
            gc.collect()
            print(f"[MasterRemediator] Created layered PSD via pytoshop: {psd_out}")
            return

        raise RuntimeError("Neither pytoshop nor appropriate PSD writer available.")

        raise RuntimeError("Neither pytoshop nor appropriate PSD writer available.")

    @classmethod
    def remediate_raster_fallback(
        cls,
        base_master_path: str,
        m1_out: str,
        m2_out: str,
        text_glyph_mask: Optional[np.ndarray] = None,
    ):
        """
        Fallback Workflow: Cleans existing flat Master0_Base.png using topological tree hierarchy.
        Whole-glyph recoloring: Group typography by connected components, NEVER by Y-coordinate slicing.
        Export Master 1 and Master 2 cleanly.
        """
        img = Image.open(base_master_path).convert("RGBA")
        arr = np.array(img)
        h, w = arr.shape[:2]

        arr = cls.punch_topological_cavities(arr)
        arr = cls.punch_micro_bridges(arr, max_bridge_width=4)
        arr = cls.smooth_outer_boundary(arr)

        alpha = arr[:, :, 3]
        rgb = arr[:, :, :3]

        # Whole-glyph recoloring: Connected components of lettering
        if text_glyph_mask is None:
            # Automatically identify typography glyphs:
            # Crimson/red text letters (e.g. SLEIGHING, THE, SHIFT)
            # Find connected components of colored text fill
            crimson_mask = (alpha > 80) & (rgb[:, :, 0] > 100) & (rgb[:, :, 1] < 90) & (rgb[:, :, 2] < 100) & (rgb[:, :, 0].astype(int) - rgb[:, :, 1].astype(int) > 30)
            
            num_cc, labels_cc, stats_cc, centroids_cc = cv2.connectedComponentsWithStats(crimson_mask.astype(np.uint8), connectivity=8)
            text_glyph_mask = np.zeros((h, w), dtype=bool)

            for i in range(1, num_cc):
                area = stats_cc[i, cv2.CC_STAT_AREA]
                cx, cy = centroids_cc[i]
                bx, by, bw, bh = stats_cc[i, :4]

                # Filter for text lettering components:
                # Top text: SLEIGHING (y < 1600, area > 30000)
                if cy < 1600 and area > 30000:
                    text_glyph_mask[labels_cc == i] = True
                # Bottom text: THE (y between 3600 and 4200, x < 1820)
                elif 3600 <= cy <= 4250 and cx < 1820 and area > 5000:
                    text_glyph_mask[labels_cc == i] = True
                # Bottom text: SHIFT (y >= 4200, area > 30000)
                elif cy >= 4200 and area > 30000:
                    text_glyph_mask[labels_cc == i] = True

        # Master 1: Solid #111111 dark charcoal across all text glyphs
        m1_arr = arr.copy()
        m1_arr[text_glyph_mask, :3] = [17, 17, 17]

        # Master 2: Solid #F5F0E6 vintage cream across all text glyphs
        m2_arr = arr.copy()
        m2_arr[text_glyph_mask, :3] = [245, 240, 230]

        os.makedirs(os.path.dirname(os.path.abspath(m1_out)), exist_ok=True)
        os.makedirs(os.path.dirname(os.path.abspath(m2_out)), exist_ok=True)

        m1_img = Image.fromarray(m1_arr)
        m2_img = Image.fromarray(m2_arr)

        m1_img.save(m1_out, dpi=(300, 300), optimize=True)
        m2_img.save(m2_out, dpi=(300, 300), optimize=True)
        print(f"[MasterRemediator] Exported raster fallback masters:\n  M1: {m1_out}\n  M2: {m2_out}")

    @classmethod
    def remediate_sleighing_the_night_shift(cls, base_dir: str):
        """
        Specialized deterministic remediation for 'Sleighing the Night Shift Tee':
        1. Fixes horizontal color split on 'THE'.
        2. Purges SC1 (steth sliver), SC2 ('THE' bridge), SC3 ('G' filament).
        3. Generates pristine Master0_Base.png.
        4. Builds layered source PSD with Typography, Artwork_Body, and Accents.
        5. Exports Master 1 and Master 2 at 4500x5400 @ 300 DPI.
        6. Generates #FF00FF magenta proofs.
        """
        source_dir = os.path.join(base_dir, "source_assets")
        prod_dir = os.path.join(base_dir, "production_png")
        qa_dir = os.path.join(base_dir, "qa_proofs")
        os.makedirs(source_dir, exist_ok=True)
        os.makedirs(prod_dir, exist_ok=True)
        os.makedirs(qa_dir, exist_ok=True)

        # Baseline artwork path
        raw_path = os.path.join("print_ready_4500x5400", "10_Sleighing_The_Night_Shift_Nurse.png")
        if not os.path.exists(raw_path):
            raw_path = os.path.join(prod_dir, "Master0_Base.png")
        if not os.path.exists(raw_path):
            raw_path = os.path.join(prod_dir, "Master1_LightGarments.png")

        print(f"[MasterRemediator] Loading baseline artwork from: {raw_path}")
        im = Image.open(raw_path).convert("RGBA")
        arr = np.array(im)
        h, w = arr.shape[:2]
        alpha = arr[:, :, 3].copy()
        rgb = arr[:, :, :3]

        # 1. Alpha Clamping: Purge faint diffuse outer halo < 20
        alpha[alpha < 20] = 0

        # 2. Cavity and Negative Space Knockout
        is_pure_white = ((alpha > 100) & (rgb[:, :, 0] > 230) & (rgb[:, :, 1] > 230) & (rgb[:, :, 2] > 225) & (np.abs(rgb[:, :, 0].astype(int) - rgb[:, :, 2].astype(int)) <= 15)).astype(np.uint8)
        num_lbl, lbls, stats, centroids = cv2.connectedComponentsWithStats(is_pure_white, connectivity=8)

        knockout_mask = np.zeros((h, w), dtype=bool)
        for i in range(1, num_lbl):
            x, y, bw, bh, area = stats[i]
            cx, cy = centroids[i]

            # Top text counters (SLEIGHING)
            if cy < 1600 and area < 15000:
                knockout_mask[lbls == i] = True
            # Bottom text counters (THE, NIGHT, SHIFT)
            elif cy > 3600 and area < 25000:
                knockout_mask[lbls == i] = True
            # Left stethoscope loop cavity
            elif 1000 < cx < 1600 and 2200 < cy < 3200 and area > 1000:
                knockout_mask[lbls == i] = True
            # Right stethoscope loop cavity
            elif 2800 < cx < 3600 and 1800 < cy < 2800 and area > 1000:
                knockout_mask[lbls == i] = True
            # Bottom cavities behind cords and under cup
            elif 1300 < cx < 3200 and 3200 < cy < 4000:
                knockout_mask[lbls == i] = True
            # Cavity between right side of cup and cord
            elif 2400 < cx < 2800 and 2800 < cy < 3300 and area > 5000:
                knockout_mask[lbls == i] = True
            # Pocket behind thumb and index finger
            elif 1700 < cx < 1850 and 2550 < cy < 2750:
                knockout_mask[lbls == i] = True
            # Residual white sliver adjacent to stethoscope binaural tube / cord loop
            elif 2800 < cx < 2950 and 1650 < cy < 1850:
                knockout_mask[lbls == i] = True

        # Apertures of G1 and G2 in SLEIGHING
        g1_gap_white = (alpha > 50) & (rgb[:, :, 0] > 210) & (rgb[:, :, 1] > 210) & (rgb[:, :, 2] > 210) & (np.abs(rgb[:, :, 0].astype(int) - rgb[:, :, 2].astype(int)) <= 15)
        g1_gap_zone = np.zeros((h, w), dtype=bool)
        g1_gap_zone[530:720, 2100:2250] = True
        knockout_mask[g1_gap_white & g1_gap_zone] = True

        g2_gap_white = (alpha > 50) & (rgb[:, :, 0] > 210) & (rgb[:, :, 1] > 210) & (rgb[:, :, 2] > 210) & (np.abs(rgb[:, :, 0].astype(int) - rgb[:, :, 2].astype(int)) <= 15)
        g2_gap_zone = np.zeros((h, w), dtype=bool)
        g2_gap_zone[1100:1350, 3450:3650] = True
        knockout_mask[g2_gap_white & g2_gap_zone] = True

        # Stethoscope upper sliver direct mask
        steth_sliver_white = (alpha > 50) & (rgb[:, :, 0] > 230) & (rgb[:, :, 1] > 230) & (rgb[:, :, 2] > 230) & (np.abs(rgb[:, :, 0].astype(int) - rgb[:, :, 2].astype(int)) <= 10)
        steth_sliver_zone = np.zeros((h, w), dtype=bool)
        steth_sliver_zone[1650:1850, 2800:2950] = True
        knockout_mask[steth_sliver_white & steth_sliver_zone] = True

        # SC1: Crescent sliver hugging right side of green tubing (x: 2760..2880, y: 2680..2820)
        green_tube = (alpha > 50) & (rgb[:, :, 1] > rgb[:, :, 0] + 15) & (rgb[:, :, 1] > 60)
        black_line = (alpha > 50) & (rgb[:, :, 0] < 60) & (rgb[:, :, 1] < 60) & (rgb[:, :, 2] < 60)
        sc1_zone = np.zeros((h, w), dtype=bool)
        sc1_zone[2680:2820, 2760:2880] = True
        knockout_mask[sc1_zone & (alpha > 0) & (~green_tube) & (~black_line)] = True

        # SC2: Vertical white bridge in 'THE' (x: 1030..1100, y: 3850..3980)
        sc2_zone = np.zeros((h, w), dtype=bool)
        sc2_zone[3850:3980, 1030:1100] = True
        knockout_mask[sc2_zone & (alpha > 0) & (rgb[:, :, 1] > 80) & (rgb[:, :, 0] > 170)] = True

        # SC3: White seam filament along inner junction counter of 'G' in SLEIGHING (x: 2060..2160, y: 420..500)
        sc3_zone = np.zeros((h, w), dtype=bool)
        sc3_zone[420:500, 2060:2160] = True
        knockout_mask[sc3_zone & (alpha > 50) & (rgb[:, :, 0] > 170) & (rgb[:, :, 1] > 170)] = True

        # General text counter knockouts (A, R, B, O, D, G, E, H, S, etc.)
        # Top banner SLEIGHING text zone
        sleighing_zone = np.zeros((h, w), dtype=bool)
        sleighing_zone[:1450, :] = True
        sleighing_zone[1450:1550, :2650] = True

        # Bottom footer THE, NIGHT, SHIFT text zone (excluding red bulb at 1879, 3646)
        footer_zone = np.zeros((h, w), dtype=bool)
        footer_zone[3600:, :] = True
        bulb_protect = np.zeros((h, w), dtype=bool)
        bulb_protect[3600:3750, 1820:1950] = True

        text_white = (alpha > 50) & (rgb[:, :, 0] > 180) & (rgb[:, :, 1] > 180) & (rgb[:, :, 2] > 170)
        knockout_mask[text_white & (sleighing_zone | footer_zone) & (~bulb_protect)] = True

        # Safeguard skeleton hand bones and metallic tube
        tube_mask = (alpha > 100) & (rgb[:, :, 0] > 200) & (rgb[:, :, 1] > 190) & (rgb[:, :, 0].astype(int) - rgb[:, :, 2].astype(int) >= 25)
        tube_zone = np.zeros((h, w), dtype=bool)
        tube_zone[1500:2100, 2850:3100] = True
        knockout_mask[tube_mask & tube_zone] = False

        bone_mask = (alpha > 100) & (rgb[:, :, 0] > 200) & (rgb[:, :, 1] > 190) & (rgb[:, :, 0].astype(int) - rgb[:, :, 2].astype(int) >= 22)
        bone_zone = np.zeros((h, w), dtype=bool)
        bone_zone[2400:3400, 1550:2400] = True
        knockout_mask[bone_mask & bone_zone] = False

        # Apply knockout
        alpha_clean = alpha.copy()
        alpha_clean[knockout_mask] = 0

        # Micro-pinhole healing: fill tiny voids (< 50 px) inside solid artwork
        bin_art = (alpha_clean > 0).astype(np.uint8)
        inv = 1 - bin_art
        inv_padded = np.pad(inv, pad_width=1, mode="constant", constant_values=1)
        flood = inv_padded.copy()
        mask_ff = np.zeros((h + 4, w + 4), np.uint8)
        cv2.floodFill(flood, mask_ff, (0, 0), 2)
        flood_unpadded = flood[1:-1, 1:-1]
        internal_holes = ((flood_unpadded != 2) & (inv == 1)).astype(np.uint8)
        num_h, lbls_h, stats_h, _ = cv2.connectedComponentsWithStats(internal_holes, connectivity=8)
        for i in range(1, num_h):
            if stats_h[i, cv2.CC_STAT_AREA] < 50:
                alpha_clean[lbls_h == i] = 255

        # Sub-pixel boundary smoothing
        alpha_float = alpha_clean.astype(np.float32) / 255.0
        smoothed = cv2.GaussianBlur(alpha_float, (3, 3), sigmaX=0.8)
        smoothed[smoothed < 0.08] = 0.0
        final_alpha = (smoothed * 255).astype(np.uint8)

        # Enforce strict zero alpha on SC1 sliver (adjacent to green tube)
        final_alpha[sc1_zone & (~green_tube) & (~black_line)] = 0

        # Baseline Master0_Base.png
        m0_arr = arr.copy()
        m0_arr[:, :, 3] = final_alpha
        m0_path = os.path.join(prod_dir, "Master0_Base.png")
        Image.fromarray(m0_arr).save(m0_path, dpi=(300, 300))
        print(f"[MasterRemediator] Saved Master0_Base -> {m0_path}")

        # Free intermediate arrays to conserve 32-bit virtual memory
        del arr, alpha, is_pure_white, knockout_mask, alpha_clean, alpha_float, smoothed
        import gc; gc.collect()

        # 3. Layer Separation for PSD
        # Typography:
        # Header SLEIGHING (y < 1600):
        # Footer THE, NIGHT, SHIFT (y > 3600):
        top_zone = np.zeros((h, w), dtype=bool)
        top_zone[:1600, :] = True
        bot_zone = np.zeros((h, w), dtype=bool)
        bot_zone[3600:, :] = True

        # Solid lettering in top and bottom zones
        typo_mask = (final_alpha > 50) & (top_zone | bot_zone)

        # Protect stars and accent bulbs in top and bottom zones from typo layer
        # Red bulb at (1879, 3646)
        bulb_protect = np.zeros((h, w), dtype=bool)
        bulb_protect[3600:3750, 1820:1950] = True
        typo_mask[bulb_protect] = False

        # Accents: Christmas lights, bulbs, string cord, stars
        accents_mask = np.zeros((h, w), dtype=bool)
        # Small stars in top and perimeter
        stars_mask = (final_alpha > 50) & (rgb[:, :, 0] > 200) & (rgb[:, :, 1] > 180) & (rgb[:, :, 2] < 120) & (top_zone | (rgb[:, :, 1] > 180))
        accents_mask[stars_mask] = True
        accents_mask[bulb_protect & (final_alpha > 50)] = True

        # Artwork_Body: Remainder of artwork
        body_mask = (final_alpha > 0) & (~typo_mask) & (~accents_mask)

        # Helper to extract cropped layer dict without allocating full 4500x5400 array
        def get_cropped_layer_dict(name: str, mask: np.ndarray) -> Dict[str, Any]:
            nonzero = np.where(mask)
            if len(nonzero[0]) == 0:
                return {
                    "name": name,
                    "top": 0, "bottom": 10, "left": 0, "right": 10,
                    "rgba": np.zeros((10, 10, 4), dtype=np.uint8)
                }
            ymin = int(np.min(nonzero[0]))
            ymax = int(np.max(nonzero[0]) + 1)
            xmin = int(np.min(nonzero[1]))
            xmax = int(np.max(nonzero[1]) + 1)
            crop = m0_arr[ymin:ymax, xmin:xmax].copy()
            sub_mask = mask[ymin:ymax, xmin:xmax].astype(np.uint8)
            crop[:, :, 3] = crop[:, :, 3] * sub_mask
            return {
                "name": name,
                "top": ymin, "bottom": ymax, "left": xmin, "right": xmax,
                "rgba": crop
            }

        layers_list = [
            get_cropped_layer_dict("Accents", accents_mask),
            get_cropped_layer_dict("Artwork_Body", body_mask),
            get_cropped_layer_dict("Typography", typo_mask),
        ]

        # 4. Construct Layered PSD: source_assets/Sleighing_The_Night_Shift_Master.psd
        psd_path = os.path.join(source_dir, "Sleighing_The_Night_Shift_Master.psd")
        cls.create_layered_psd(
            psd_out=psd_path,
            layers_list=layers_list,
            canvas_size=(w, h),
        )
        del layers_list
        gc.collect()

        # 5. Export Master 1 and Master 2
        m1_path = os.path.join(prod_dir, "Master1_LightGarments.png")
        m2_path = os.path.join(prod_dir, "Master2_DarkGarments.png")

        # Top banner 'SLEIGHING' (y < 1600 slice):
        alpha_top = m0_arr[:1600, :, 3]
        rgb_top = m0_arr[:1600, :, :3]
        crimson_top = (alpha_top > 50) & (rgb_top[:, :, 0] > 100) & (rgb_top[:, :, 1] < 90) & (rgb_top[:, :, 2] < 100)
        sleighing_slice_mask = crimson_top
        del alpha_top, rgb_top
        gc.collect()

        # Bottom 'THE' and 'SHIFT' (y >= 3600 slice):
        alpha_bot = m0_arr[3600:, :, 3]
        rgb_bot = m0_arr[3600:, :, :3]
        # Protect accent Christmas lights bulb at relative y: 0..150, x: 1820..1950
        bulb_protect_rel = np.zeros(alpha_bot.shape, dtype=bool)
        bulb_protect_rel[:150, 1820:1950] = True
        crimson_bot = (alpha_bot > 50) & (rgb_bot[:, :, 0] > 100) & (rgb_bot[:, :, 1] < 90) & (rgb_bot[:, :, 2] < 100) & (~bulb_protect_rel)
        the_shift_slice = crimson_bot
        del alpha_bot, rgb_bot, bulb_protect_rel
        gc.collect()

        # Master 1: Solid #111111 dark charcoal
        m0_arr[:1600, :][sleighing_slice_mask, :3] = [17, 17, 17]
        m0_arr[3600:, :][the_shift_slice, :3] = [17, 17, 17]
        m1_img = Image.fromarray(m0_arr)
        m1_img.save(m1_path, dpi=(300, 300))
        print(f"[MasterRemediator] Saved Master 1 -> {m1_path}")

        # Proof 1
        m1_small = m1_img.resize((1500, 1800), Image.LANCZOS)
        arr_s1 = np.array(m1_small)
        a1 = arr_s1[:, :, 3].astype(np.float32) / 255.0
        mag1 = np.zeros_like(arr_s1[:, :, :3])
        mag1[:, :] = [255, 0, 255]
        comp1 = (arr_s1[:, :, :3] * a1[:, :, None] + mag1 * (1.0 - a1[:, :, None])).astype(np.uint8)
        p1_path = os.path.join(qa_dir, "Master1_Magenta_Proof.jpg")
        Image.fromarray(comp1).save(p1_path, quality=95)
        del m1_img, m1_small, arr_s1, a1, mag1, comp1
        gc.collect()

        # Master 2: Solid #F5F0E6 Vintage Cream
        m0_arr[:1600, :][sleighing_slice_mask, :3] = [245, 240, 230]
        m0_arr[3600:, :][the_shift_slice, :3] = [245, 240, 230]
        m2_img = Image.fromarray(m0_arr)
        m2_img.save(m2_path, dpi=(300, 300))
        print(f"[MasterRemediator] Saved Master 2 -> {m2_path}")

        # Proof 2
        m2_small = m2_img.resize((1500, 1800), Image.LANCZOS)
        arr_s2 = np.array(m2_small)
        a2 = arr_s2[:, :, 3].astype(np.float32) / 255.0
        mag2 = np.zeros_like(arr_s2[:, :, :3])
        mag2[:, :] = [255, 0, 255]
        comp2 = (arr_s2[:, :, :3] * a2[:, :, None] + mag2 * (1.0 - a2[:, :, None])).astype(np.uint8)
        p2_path = os.path.join(qa_dir, "Master2_Magenta_Proof.jpg")
        Image.fromarray(comp2).save(p2_path, quality=95)
        del m0_arr, m2_img, m2_small, arr_s2, a2, mag2, comp2, sleighing_slice_mask, the_shift_slice
        gc.collect()

        # Copy to print_ready_4500x5400
        pr_dir = "print_ready_4500x5400"
        if os.path.exists(pr_dir):
            import shutil
            shutil.copyfile(m1_path, os.path.join(pr_dir, "Master1_LightGarments.png"))
            shutil.copyfile(m2_path, os.path.join(pr_dir, "Master2_DarkGarments.png"))
            shutil.copyfile(m1_path, os.path.join(pr_dir, "10_Sleighing_The_Night_Shift_Master1_LightGarments.png"))
            shutil.copyfile(m2_path, os.path.join(pr_dir, "10_Sleighing_The_Night_Shift_Master2_DarkGarments.png"))

        print("[MasterRemediator] Remediation completed successfully.")
        return {
            "master0_path": m0_path,
            "master1_path": m1_path,
            "master2_path": m2_path,
            "psd_path": psd_path,
            "proof1_path": p1_path,
            "proof2_path": p2_path,
        }
