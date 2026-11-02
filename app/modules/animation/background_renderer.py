"""Procedural Notebook Paper Background Generator for Dark Myth Stickman Auto-Studio.

Renders realistic 9:16 student notebook paper backgrounds procedurally using NumPy and Pillow,
supporting all canonical BackgroundState presets (clean, ink splattered, cracked, torn, corrupted, heavenly).
"""

from enum import Enum
import math
from pathlib import Path
from typing import Optional, Union

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from app.core.logger import get_logger
from app.schemas.scene_schema import BackgroundState

logger = get_logger("background_renderer")


class NotebookBackgroundRenderer:
    """
    Procedural renderer generating high-resolution 9:16 student notebook paper canvases.

    Features:
      - 7 layered procedural pipeline (Base -> Fiber Texture -> Lighting -> Ruled Lines -> Margins -> State Effects -> Grading).
      - Strict reproducibility via seed control.
      - Vectorized NumPy noise generation for sub-second 1080x1920 render times.
      - Dynamic scaling supporting 1080x1920 (Production) and 540x960 (Preview).
      - Safe Character Combat Zone: Keeps central area clean for stickman action readability.
    """

    # Palette Constants
    COLOR_PAPER_CLEAN = (244, 239, 230)       # #F4EFE6 (Warm Ivory / Cream)
    COLOR_PAPER_INK = (236, 230, 218)         # #ECE6DA (Muted Cream)
    COLOR_PAPER_CRACKED = (222, 216, 204)     # #DED8CC (Weathered Cream)
    COLOR_PAPER_TORN = (195, 187, 175)        # #C3BBB0 (Dark Myth Ash Tint)
    COLOR_PAPER_CORRUPTED = (36, 33, 39)      # #242127 (Dark Corrupted Paper)
    COLOR_PAPER_HEAVENLY_TOP = (255, 236, 175)# #FFECB0 (Divine Golden Radiance)
    COLOR_PAPER_HEAVENLY_BOT = (238, 228, 212)# #EEE4D4 (Warm Parchment)

    COLOR_RULED_LINE = (155, 184, 211)        # #9BB8D3 (Classic Light Blue)
    COLOR_RULED_CORRUPTED = (62, 74, 88)      # Faint ghostly blue on dark paper
    COLOR_MARGIN_RED = (200, 75, 49)          # #C84B31 (Crimson Red)
    COLOR_MARGIN_CORRUPTED = (110, 38, 30)    # Weathered dried blood red

    COLOR_BINDER_HOLE = (65, 65, 70)          # Hole interior shadow
    COLOR_BINDER_RIM = (255, 255, 255, 70)    # Hole paper rim highlight

    def __init__(
        self,
        default_width: int = 1080,
        default_height: int = 1920,
    ) -> None:
        self.default_width = default_width
        self.default_height = default_height

    @staticmethod
    def normalize_state(state: Union[BackgroundState, str]) -> str:
        """Map any BackgroundState enum or string alias to canonical preset key."""
        if isinstance(state, BackgroundState):
            val = state.value
        else:
            val = str(state).strip().lower()

        if val in ("clean_notebook", "normal_page", "clean"):
            return "clean_notebook"
        if val in ("ink_splattered", "ink"):
            return "ink_splattered"
        if val in ("cracked_page", "cracked"):
            return "cracked_page"
        if val in ("torn_dark_myth", "torn"):
            return "torn_dark_myth"
        if val in ("dark_corrupted_page", "dark_corrupted", "corrupted"):
            return "dark_corrupted_page"
        if val in ("heavenly_pressure", "heavenly"):
            return "heavenly_pressure"

        valid_keys = [s.value for s in BackgroundState]
        raise ValueError(f"Unsupported BackgroundState '{state}'. Must be one of {valid_keys}")

    def render_background(
        self,
        state: Union[BackgroundState, str],
        width: Optional[int] = None,
        height: Optional[int] = None,
        seed: Optional[int] = None,
    ) -> Image.Image:
        """
        Procedurally render a complete RGB PIL Image background for `state`.

        Args:
            state: BackgroundState enum or string name.
            width: Width in pixels (defaults to 1080).
            height: Height in pixels (defaults to 1920).
            seed: Optional integer seed for deterministic procedural generation.

        Returns:
            PIL.Image.Image: RGB Image of size (width, height).
        """
        w = width or self.default_width
        h = height or self.default_height
        canonical_state = self.normalize_state(state)
        scale = w / 1080.0

        # Initialize deterministic RNG if seed provided, else entropy
        rng = np.random.default_rng(seed)

        # 1. Base Paper Gradient & Tint
        base_arr = self._generate_paper_base(w, h, canonical_state, scale)

        # 2. Paper Fiber & Grain Texture
        textured_arr = self._apply_paper_texture(base_arr, w, h, canonical_state, rng, scale)

        # 3. Vignette & Radial Lighting
        lit_arr = self._apply_vignette(textured_arr, w, h, canonical_state, scale)

        # Convert to PIL Image for crisp vector line and feature drawing
        base_img = Image.fromarray(lit_arr, mode="RGB")
        draw = ImageDraw.Draw(base_img, "RGBA")

        # 4. Horizontal Ruled Lines
        self._draw_ruled_lines(draw, w, h, canonical_state, scale)

        # 5. Vertical Red Margin Lines (Double Line)
        self._draw_margin_lines(draw, w, h, canonical_state, scale)

        # 6. Binder Holes along Left Margin
        self._draw_binder_holes(draw, w, h, canonical_state, scale)

        # 7. State-Specific Dark Myth Procedural Effects
        if canonical_state == "ink_splattered":
            base_img = self._apply_ink_splatters(base_img, w, h, rng, scale)
        elif canonical_state in ("cracked_page", "torn_dark_myth"):
            is_torn = (canonical_state == "torn_dark_myth")
            base_img = self._apply_paper_cracks_and_tears(base_img, w, h, rng, scale, is_torn=is_torn)
        elif canonical_state == "dark_corrupted_page":
            base_img = self._apply_dark_corruption(base_img, w, h, rng, scale)
        elif canonical_state == "heavenly_pressure":
            base_img = self._apply_heavenly_pressure(base_img, w, h, rng, scale)

        # 8. Final Color and Contrast Tuning
        final_img = self._apply_final_grading(base_img, canonical_state)
        return final_img

    def render_numpy(
        self,
        state: Union[BackgroundState, str],
        width: Optional[int] = None,
        height: Optional[int] = None,
        seed: Optional[int] = None,
    ) -> np.ndarray:
        """Render background and return as RGB numpy array of shape (height, width, 3), dtype=uint8."""
        img = self.render_background(state, width=width, height=height, seed=seed)
        return np.array(img, dtype=np.uint8)

    # -------------------------------------------------------------------------
    # Layer 1: Base Paper Color & Gradients
    # -------------------------------------------------------------------------
    def _generate_paper_base(self, w: int, h: int, state: str, scale: float) -> np.ndarray:
        if state == "heavenly_pressure":
            # Smooth vertical gradient from glowing gold at top to warm parchment at bottom
            y_coords = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
            c_top = np.array(self.COLOR_PAPER_HEAVENLY_TOP, dtype=np.float32)
            c_bot = np.array(self.COLOR_PAPER_HEAVENLY_BOT, dtype=np.float32)
            # Quadratic ease for golden radiance concentrated at top
            weights = y_coords ** 0.8
            base = (1.0 - weights) * c_top + weights * c_bot
            base_arr = np.repeat(base[:, None, :], w, axis=1)
        elif state == "dark_corrupted_page":
            base_arr = np.full((h, w, 3), self.COLOR_PAPER_CORRUPTED, dtype=np.float32)
        elif state == "torn_dark_myth":
            base_arr = np.full((h, w, 3), self.COLOR_PAPER_TORN, dtype=np.float32)
        elif state == "cracked_page":
            base_arr = np.full((h, w, 3), self.COLOR_PAPER_CRACKED, dtype=np.float32)
        elif state == "ink_splattered":
            base_arr = np.full((h, w, 3), self.COLOR_PAPER_INK, dtype=np.float32)
        else:  # clean_notebook
            base_arr = np.full((h, w, 3), self.COLOR_PAPER_CLEAN, dtype=np.float32)

        return base_arr

    # -------------------------------------------------------------------------
    # Layer 2: Natural Paper Texture (Cellulose Fibers & Grain)
    # -------------------------------------------------------------------------
    def _apply_paper_texture(
        self, base_arr: np.ndarray, w: int, h: int, state: str, rng: np.random.Generator, scale: float
    ) -> np.ndarray:
        # 1. High frequency micro-grain (paper tooth)
        noise_sigma = 2.2 if state != "dark_corrupted_page" else 1.8
        high_freq = rng.normal(loc=0.0, scale=noise_sigma, size=(h, w, 1)).astype(np.float32)

        # 2. Low frequency cloudiness / organic paper fiber variations
        # Generate coarse grid and upscale with PIL bilinear
        grid_w = max(16, int(round(w / 32)))
        grid_h = max(16, int(round(h / 32)))
        low_res = rng.uniform(low=-4.5, high=4.5, size=(grid_h, grid_w)).astype(np.float32)
        low_res_img = Image.fromarray(low_res, mode="F").resize((w, h), Image.Resampling.BILINEAR)
        low_freq = np.array(low_res_img, dtype=np.float32)[:, :, None]

        combined = base_arr + high_freq + low_freq
        return np.clip(combined, 0.0, 255.0)

    # -------------------------------------------------------------------------
    # Layer 3: Lighting & Vignette
    # -------------------------------------------------------------------------
    def _apply_vignette(
        self, arr: np.ndarray, w: int, h: int, state: str, scale: float
    ) -> np.ndarray:
        # Radial distance from center (aspect-ratio corrected)
        cx, cy = w / 2.0, h / 2.0
        y_grid, x_grid = np.ogrid[:h, :w]
        nx = (x_grid - cx) / (w * 0.55)
        ny = (y_grid - cy) / (h * 0.55)
        dist_sq = nx * nx + ny * ny

        if state == "dark_corrupted_page":
            # Heavy vignette from corners
            vig = np.clip(1.0 - 0.45 * (dist_sq ** 0.8), 0.45, 1.0)[:, :, None]
        elif state == "torn_dark_myth":
            vig = np.clip(1.0 - 0.28 * (dist_sq ** 0.8), 0.65, 1.0)[:, :, None]
        else:
            # Subtle natural paper lighting falloff
            vig = np.clip(1.0 - 0.08 * dist_sq, 0.90, 1.0)[:, :, None]

        result = arr * vig
        return np.clip(result, 0.0, 255.0).astype(np.uint8)

    # -------------------------------------------------------------------------
    # Layer 4: Horizontal Ruled Lines
    # -------------------------------------------------------------------------
    def _draw_ruled_lines(self, draw: ImageDraw.ImageDraw, w: int, h: int, state: str, scale: float) -> None:
        y_spacing = 48.0 * scale
        y_start = int(round(180.0 * scale))
        y_end = int(round(1820.0 * scale))
        line_width = max(1, int(round(2.0 * scale)))

        line_color = self.COLOR_RULED_LINE
        line_alpha = 180

        if state == "dark_corrupted_page":
            line_color = self.COLOR_RULED_CORRUPTED
            line_alpha = 110
        elif state == "torn_dark_myth":
            line_color = (135, 160, 185)
            line_alpha = 150
        elif state == "heavenly_pressure":
            line_color = (165, 185, 205)
            line_alpha = 190

        rgba = (*line_color, line_alpha)

        y = y_start
        while y <= y_end:
            draw.line([(0, y), (w, y)], fill=rgba, width=line_width)
            y += int(round(y_spacing))

    # -------------------------------------------------------------------------
    # Layer 5: Vertical Margin Lines (Double Red Line)
    # -------------------------------------------------------------------------
    def _draw_margin_lines(self, draw: ImageDraw.ImageDraw, w: int, h: int, state: str, scale: float) -> None:
        # Standard Vietnamese student notebook has double crimson lines on left margin
        x_base = 135.0 * scale
        x1 = int(round(x_base - 3.0 * scale))
        x2 = int(round(x_base + 3.0 * scale))
        line_width = max(1, int(round(2.0 * scale)))

        margin_color = self.COLOR_MARGIN_RED
        alpha = 210

        if state == "dark_corrupted_page":
            margin_color = self.COLOR_MARGIN_CORRUPTED
            alpha = 140
        elif state == "torn_dark_myth":
            margin_color = (175, 60, 40)
            alpha = 180

        rgba = (*margin_color, alpha)
        draw.line([(x1, 0), (x1, h)], fill=rgba, width=line_width)
        draw.line([(x2, 0), (x2, h)], fill=rgba, width=line_width)

    # -------------------------------------------------------------------------
    # Layer 6: Binder Holes
    # -------------------------------------------------------------------------
    def _draw_binder_holes(self, draw: ImageDraw.ImageDraw, w: int, h: int, state: str, scale: float) -> None:
        # 5 punched holes along left margin
        hole_x = int(round(65.0 * scale))
        radius = max(8, int(round(22.0 * scale)))
        y_positions = [260, 610, 960, 1310, 1660]

        hole_fill = (45, 45, 50, 240) if state != "dark_corrupted_page" else (20, 18, 22, 255)
        rim_color = (255, 255, 255, 55) if state != "dark_corrupted_page" else (90, 85, 95, 45)

        for base_y in y_positions:
            cy = int(round(base_y * scale))
            # Subtle white highlight rim on bottom-right
            draw.ellipse(
                [(hole_x - radius + 1, cy - radius + 1), (hole_x + radius + 1, cy + radius + 1)],
                fill=rim_color,
            )
            # Main dark hole
            draw.ellipse(
                [(hole_x - radius, cy - radius), (hole_x + radius, cy + radius)],
                fill=hole_fill,
            )
            # Inner top-left shadow
            draw.arc(
                [(hole_x - radius, cy - radius), (hole_x + radius, cy + radius)],
                start=180,
                end=270,
                fill=(20, 20, 25, 180),
                width=max(1, int(round(2 * scale))),
            )

    # -------------------------------------------------------------------------
    # Layer 7A: State Effect - Ink Splatters
    # -------------------------------------------------------------------------
    def _apply_ink_splatters(
        self, base_img: Image.Image, w: int, h: int, rng: np.random.Generator, scale: float
    ) -> Image.Image:
        """
        Draw realistic sumi-e ink droplets with satellite splashes.
        Preserves central character combat zone (cx +/- 250, cy +/- 400).
        """
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, "RGBA")

        # Define 4-7 primary splatter clusters in peripheral zones
        num_splatters = rng.integers(5, 8)

        # Peripheral zones: Top corners, left margin, bottom right, bottom ground
        candidate_zones = [
            (int(w * 0.18), int(h * 0.12)),   # Top Left
            (int(w * 0.82), int(h * 0.15)),   # Top Right
            (int(w * 0.88), int(h * 0.42)),   # Mid Right
            (int(w * 0.16), int(h * 0.65)),   # Mid Left
            (int(w * 0.80), int(h * 0.82)),   # Bottom Right
            (int(w * 0.28), int(h * 0.88)),   # Bottom Left
            (int(w * 0.50), int(h * 0.20)),   # Upper Center
        ]
        rng.shuffle(candidate_zones)

        for i in range(min(num_splatters, len(candidate_zones))):
            cx, cy = candidate_zones[i]
            # Jitter cluster center
            cx += int(rng.uniform(-35, 35) * scale)
            cy += int(rng.uniform(-40, 40) * scale)

            # 85% sumi-e black ink, 15% crimson ink splatter
            if rng.random() > 0.82:
                ink_rgb = (145, 24, 24)
            else:
                ink_rgb = (18, 18, 22)

            main_radius = rng.uniform(22.0, 55.0) * scale
            self._draw_organic_droplet(draw, cx, cy, main_radius, ink_rgb, rng, scale)

            # Generate satellite droplets radiating outwards
            num_satellites = rng.integers(6, 14)
            for _ in range(num_satellites):
                angle = rng.uniform(0, 2 * math.pi)
                dist = rng.uniform(main_radius * 1.2, main_radius * 3.4)
                sat_x = int(cx + math.cos(angle) * dist)
                sat_y = int(cy + math.sin(angle) * dist)

                if 0 <= sat_x < w and 0 <= sat_y < h:
                    sat_r = rng.uniform(2.0, 7.5) * scale
                    self._draw_organic_droplet(draw, sat_x, sat_y, sat_r, ink_rgb, rng, scale, alpha=235)

        # Blend ink overlay onto base paper
        return Image.alpha_composite(base_img.convert("RGBA"), overlay).convert("RGB")

    def _draw_organic_droplet(
        self,
        draw: ImageDraw.ImageDraw,
        cx: int,
        cy: int,
        radius: float,
        rgb: tuple[int, int, int],
        rng: np.random.Generator,
        scale: float,
        alpha: int = 245,
    ) -> None:
        """Draw an irregular ink droplet with ragged edge lobes."""
        num_points = rng.integers(12, 20)
        angles = np.linspace(0, 2 * math.pi, num_points, endpoint=False)
        points = []
        for a in angles:
            r = radius * rng.uniform(0.72, 1.28)
            px = cx + math.cos(a) * r
            py = cy + math.sin(a) * r
            points.append((px, py))

        rgba = (*rgb, alpha)
        draw.polygon(points, fill=rgba)

    # -------------------------------------------------------------------------
    # Layer 7B: State Effect - Cracks & Torn Paper
    # -------------------------------------------------------------------------
    def _apply_paper_cracks_and_tears(
        self, base_img: Image.Image, w: int, h: int, rng: np.random.Generator, scale: float, is_torn: bool = False
    ) -> Image.Image:
        """Draw procedural branching fracture fissures and optional torn paper drop shadow."""
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, "RGBA")

        # 1. Torn corner / boundary edge (if torn_dark_myth)
        if is_torn:
            self._draw_torn_void_edge(draw, w, h, rng, scale)

        # 2. Procedural Branching Cracks
        # Origins near bottom ground (impact point) or edges
        num_crack_epicenters = rng.integers(2, 4)
        epicenters = [
            (int(w * 0.50), int(h * 0.76)),  # Ground center clash
            (int(w * 0.85), int(h * 0.40)),  # Wall/right clash
            (int(w * 0.15), int(h * 0.35)),  # Left clash
        ]

        for i in range(num_crack_epicenters):
            start_x, start_y = epicenters[i % len(epicenters)]
            start_x += int(rng.uniform(-40, 40) * scale)
            start_y += int(rng.uniform(-30, 30) * scale)

            num_trunks = rng.integers(3, 6)
            for _ in range(num_trunks):
                base_angle = rng.uniform(0, 2 * math.pi)
                self._draw_crack_branch(draw, start_x, start_y, base_angle, depth=4, rng=rng, scale=scale)

        # If torn mode, sprinkle subtle dark floating ashes
        if is_torn:
            for _ in range(rng.integers(25, 45)):
                ax = int(rng.uniform(w * 0.05, w * 0.95))
                ay = int(rng.uniform(h * 0.10, h * 0.90))
                ar = rng.uniform(1.5, 4.0) * scale
                draw.ellipse([(ax - ar, ay - ar), (ax + ar, ay + ar)], fill=(28, 25, 30, 190))

        return Image.alpha_composite(base_img.convert("RGBA"), overlay).convert("RGB")

    def _draw_crack_branch(
        self,
        draw: ImageDraw.ImageDraw,
        x: float,
        y: float,
        angle: float,
        depth: int,
        rng: np.random.Generator,
        scale: float,
    ) -> None:
        if depth <= 0:
            return

        seg_len = rng.uniform(30.0, 75.0) * scale
        angle_delta = rng.uniform(-0.45, 0.45)
        new_angle = angle + angle_delta
        nx = x + math.cos(new_angle) * seg_len
        ny = y + math.sin(new_angle) * seg_len

        stroke_width = max(1, int(round((depth * 1.3) * scale)))
        fissure_color = (25, 22, 26, 235)
        highlight_color = (255, 250, 240, 75)

        # Draw highlight on side for 3D depth
        draw.line([(x + 1, y + 1), (nx + 1, ny + 1)], fill=highlight_color, width=stroke_width)
        # Draw dark fissure
        draw.line([(x, y), (nx, ny)], fill=fissure_color, width=stroke_width)

        # Branching continuation
        self._draw_crack_branch(draw, nx, ny, new_angle, depth - 1, rng, scale)
        if rng.random() > 0.45 and depth >= 2:
            fork_angle = new_angle + rng.choice([-0.75, 0.75])
            self._draw_crack_branch(draw, nx, ny, fork_angle, depth - 2, rng, scale)

    def _draw_torn_void_edge(
        self, draw: ImageDraw.ImageDraw, w: int, h: int, rng: np.random.Generator, scale: float
    ) -> None:
        """Draw a ragged torn paper corner showing dark void underneath."""
        # Top-right torn corner
        corner_w = int(w * rng.uniform(0.25, 0.38))
        corner_h = int(h * rng.uniform(0.12, 0.20))

        # Jagged tear line
        points = [(w, 0)]
        num_segs = 16
        for step in range(num_segs + 1):
            t = step / float(num_segs)
            px = (w - corner_w) + (t * corner_w)
            py = corner_h * (1.0 - t)
            # Add jagged paper tooth
            jitter = rng.uniform(-8.0, 8.0) * scale
            points.append((px + jitter, py + jitter))
        points.append((w, corner_h))
        points.append((w, 0))

        # Underneath dark abyss
        draw.polygon(points, fill=(18, 16, 22, 255))
        # White paper tear fiber border
        draw.line(points[1:-2], fill=(250, 245, 238, 220), width=max(2, int(round(3 * scale))))

    # -------------------------------------------------------------------------
    # Layer 7C: State Effect - Dark Corruption
    # -------------------------------------------------------------------------
    def _apply_dark_corruption(
        self, base_img: Image.Image, w: int, h: int, rng: np.random.Generator, scale: float
    ) -> Image.Image:
        """Draw creeping necrotic dark ink mist and ominous corruption tendrils."""
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, "RGBA")

        # 1. Dark bottom ground corruption miasma
        ground_y = int(1420 * scale)
        y_coords = np.linspace(0, 1, h - ground_y, dtype=np.float32)[:, None]
        fog_alpha = (y_coords ** 1.5) * 160.0
        fog_arr = np.zeros((h - ground_y, w, 4), dtype=np.uint8)
        fog_arr[:, :, 0] = 18  # R
        fog_arr[:, :, 1] = 14  # G
        fog_arr[:, :, 2] = 24  # B
        fog_arr[:, :, 3] = np.clip(fog_alpha, 0, 200).astype(np.uint8)

        fog_img = Image.fromarray(fog_arr, mode="RGBA")
        overlay.paste(fog_img, (0, ground_y), fog_img)

        # 2. Creeping dark tendrils from sides and bottom
        num_tendrils = rng.integers(6, 11)
        for _ in range(num_tendrils):
            start_x = int(rng.choice([rng.uniform(0, w * 0.25), rng.uniform(w * 0.75, w)]))
            start_y = int(rng.uniform(h * 0.70, h))
            self._draw_corruption_tendril(draw, start_x, start_y, rng, scale)

        return Image.alpha_composite(base_img.convert("RGBA"), overlay).convert("RGB")

    def _draw_corruption_tendril(
        self, draw: ImageDraw.ImageDraw, x: float, y: float, rng: np.random.Generator, scale: float
    ) -> None:
        """Draw a single winding dark ink tendril rising like smoke."""
        curr_x, curr_y = x, y
        angle = -math.pi / 2.0 + rng.uniform(-0.4, 0.4)  # Generally upwards
        num_nodes = rng.integers(8, 16)
        width = rng.uniform(3.0, 7.0) * scale

        for i in range(num_nodes):
            step = rng.uniform(20.0, 45.0) * scale
            angle += rng.uniform(-0.5, 0.5)
            nx = curr_x + math.cos(angle) * step
            ny = curr_y + math.sin(angle) * step

            alpha = int(220 * (1.0 - (i / num_nodes) * 0.7))
            stroke = max(1, int(round(width * (1.0 - (i / num_nodes) * 0.6))))
            draw.line([(curr_x, curr_y), (nx, ny)], fill=(12, 10, 16, alpha), width=stroke)
            curr_x, curr_y = nx, ny

    # -------------------------------------------------------------------------
    # Layer 7D: State Effect - Heavenly Pressure
    # -------------------------------------------------------------------------
    def _apply_heavenly_pressure(
        self, base_img: Image.Image, w: int, h: int, rng: np.random.Generator, scale: float
    ) -> Image.Image:
        """Draw divine golden volumetric light beams descending from the heavens."""
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, "RGBA")

        # Top center source (Buddha Palm / Celestial Heavens)
        apex_x = w / 2.0
        apex_y = -int(80.0 * scale)

        # Radiating golden volumetric beams
        num_rays = rng.integers(7, 12)
        bottom_spread = np.linspace(w * 0.05, w * 0.95, num_rays)
        rng.shuffle(bottom_spread)

        for bx in bottom_spread:
            beam_half_w = rng.uniform(40.0, 110.0) * scale
            p1 = (apex_x + rng.uniform(-30, 30) * scale, apex_y)
            p2 = (bx - beam_half_w, h)
            p3 = (bx + beam_half_w, h)

            ray_alpha = rng.integers(15, 38)
            draw.polygon([p1, p2, p3], fill=(255, 230, 130, ray_alpha))

        # Floating heavenly golden dust particles
        num_specks = rng.integers(40, 75)
        for _ in range(num_specks):
            px = int(rng.uniform(w * 0.1, w * 0.9))
            py = int(rng.uniform(h * 0.05, h * 0.85))
            pr = rng.uniform(1.8, 5.0) * scale
            p_alpha = rng.integers(120, 220)
            # Soft golden particle with halo
            draw.ellipse([(px - pr * 1.8, py - pr * 1.8), (px + pr * 1.8, py + pr * 1.8)], fill=(255, 240, 160, 40))
            draw.ellipse([(px - pr, py - pr), (px + pr, py + pr)], fill=(255, 248, 190, p_alpha))

        return Image.alpha_composite(base_img.convert("RGBA"), overlay).convert("RGB")

    # -------------------------------------------------------------------------
    # Layer 8: Final Color and Contrast Grading
    # -------------------------------------------------------------------------
    def _apply_final_grading(self, img: Image.Image, state: str) -> Image.Image:
        """Apply subtle artistic color and contrast balance."""
        if state == "dark_corrupted_page":
            # Slightly deepen shadows for dark myth mood
            arr = np.array(img, dtype=np.float32)
            arr = np.clip((arr - 10.0) * 1.05, 0.0, 255.0).astype(np.uint8)
            return Image.fromarray(arr, mode="RGB")
        return img
