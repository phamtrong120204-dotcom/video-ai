"""
Buddha Palm Renderer (Bàn Tay Phật Khổng Lồ - Như Lai Thần Chưởng)
Module: app.modules.animation.buddha_palm_renderer
Specification: dark_myth_moveset_spec.md (Character: buddha_palm, Weapon: giant_golden_palm, Action: giant_palm_suppression)
Phase: G5.2.3.4 (Stage 5 Stickman Animation Engine)

Visual Language & Dark Myth Aesthetic:
  - Giant Celestial Palm (Thực thể khổng lồ xuất hiện từ đỉnh khung hình Y in [-200, 950] px).
  - Clear Anatomical Proportions: Palm base, thenar eminence, thumb, index, middle, ring, pinky.
  - Phalanx Creases & Knuckles: Natural curved joint creases eliminate flat cartoon appearance.
  - Sacred Wan Seal (Ấn ký chữ Vạn 卍) & Concentric Golden Mandalas at palm center.
  - Chưởng lực sóng xung kích (Shockwave pressure rings, nominal radius 480px at scale 3.5).
  - Color Palette:
      * Outer Ink Stroke: #1A1817 (26, 24, 23, 255)
      * Palm Gilded Bronze: #D69E2E (214, 158, 46, 255)
      * Luminous Gold Core: #FEFCBF (254, 252, 191, 255)
      * Sacred Amber Aura: #F6AD55 (246, 173, 85, 255)
      * Vajra Ruby Accent: #C53030 (197, 48, 48, 255)
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw

from app.modules.animation.stickman_models import Point2D

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BuddhaPalmGeometry:
    """Calculated geometry points for all elements of the Buddha Palm."""

    palm_center: Point2D
    wrist_center: Point2D
    thumb_tip: Point2D
    index_tip: Point2D
    middle_tip: Point2D
    ring_tip: Point2D
    pinky_tip: Point2D
    effective_scale: float
    facing: int
    direction: str
    rotation_deg: float


class BuddhaPalmRenderer:
    """
    Renders the Giant Buddha Palm (Bàn Tay Phật Tổ Khổng Lồ) on an isolated RGBA canvas.

    Supports:
      - Nominal Scale: 3.50 (moveset spec) with flexible range [0.1, 5.0].
      - Descent progression Y in [-200, 950] px (giant_palm_suppression).
      - Direction: "down" (descending strike from heaven) or "up" (ascending mudra).
      - Facing: +1 (standard right-handed palm) or -1 (mirrored left-handed palm).
      - Arbitrary rotation angle: rotation_deg (clockwise degrees).
      - Concentric golden mandalas and sacred Wan Seal (卍) at palm center.
      - Shockwave pressure halo (nominal radius 480px at scale 3.50).
    """

    DEFAULT_CANVAS_SIZE: tuple[int, int] = (1080, 1920)
    NOMINAL_SCALE: float = 3.50
    NOMINAL_SHOCKWAVE_RADIUS: float = 480.0

    # Color definitions (Dark Myth palette)
    COLOR_INK_STROKE: tuple[int, int, int, int] = (26, 24, 23, 255)  # #1A1817
    COLOR_PALM_BRONZE: tuple[int, int, int, int] = (214, 158, 46, 255)  # #D69E2E
    COLOR_PALM_HIGHLIGHT: tuple[int, int, int, int] = (254, 252, 191, 255)  # #FEFCBF
    COLOR_AURA_GLOW: tuple[int, int, int, int] = (246, 173, 85, 255)  # #F6AD55
    COLOR_MANDALA_GOLD: tuple[int, int, int, int] = (236, 201, 75, 255)  # #ECC94B
    COLOR_RUBY_ACCENT: tuple[int, int, int, int] = (197, 48, 48, 255)  # #C53030

    def __init__(self) -> None:
        pass

    @staticmethod
    def _rotate_pt(pt: tuple[float, float], center: tuple[float, float], rad: float) -> tuple[float, float]:
        """Rotate a 2D point (x, y) around center by rad radians."""
        if abs(rad) < 1e-6:
            return pt
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        dx = pt[0] - center[0]
        dy = pt[1] - center[1]
        return (
            center[0] + dx * cos_a - dy * sin_a,
            center[1] + dx * sin_a + dy * cos_a,
        )

    def get_finger_tips(
        self,
        position: Point2D,
        scale: float = NOMINAL_SCALE,
        facing: int = 1,
        direction: str = "down",
        rotation_deg: float = 0.0,
    ) -> dict[str, Point2D]:
        """
        Compute exact canvas coordinates for all 5 fingertips.

        Returns:
          Dictionary mapping: 'thumb', 'index', 'middle', 'ring', 'pinky' -> Point2D
        """
        if facing not in (+1, -1):
            raise ValueError(f"Facing must be +1 or -1, got {facing}")
        if scale <= 0.1 or scale > 5.0 or not math.isfinite(scale):
            raise ValueError(f"Scale must be in range (0.1, 5.0], got {scale}")
        if direction not in ("down", "up"):
            raise ValueError(f"Direction must be 'down' or 'up', got {direction}")

        dir_y = 1.0 if direction == "down" else -1.0
        rad = math.radians(rotation_deg)
        cx, cy = position.x, position.y

        # Unrotated local fingertip offsets relative to palm center (scale = 1.0)
        # For direction="down": fingers extend towards +Y
        raw_offsets = {
            "thumb": (-82.0 * facing, 35.0 * dir_y),
            "index": (-28.0 * facing, 128.0 * dir_y),
            "middle": (-4.0 * facing, 152.0 * dir_y),
            "ring": (17.0 * facing, 136.0 * dir_y),
            "pinky": (44.0 * facing, 102.0 * dir_y),
        }

        tips = {}
        for name, (dx, dy) in raw_offsets.items():
            world_x = cx + dx * scale
            world_y = cy + dy * scale
            rot_x, rot_y = self._rotate_pt((world_x, world_y), (cx, cy), rad)
            tips[name] = Point2D(rot_x, rot_y)

        return tips

    def get_palm_bounding_box(
        self,
        position: Point2D,
        scale: float = NOMINAL_SCALE,
        facing: int = 1,
        direction: str = "down",
        rotation_deg: float = 0.0,
        include_shockwave: bool = True,
    ) -> tuple[float, float, float, float]:
        """
        Compute theoretical geometric bounding box (min_x, min_y, max_x, max_y).
        """
        tips = self.get_finger_tips(position, scale, facing, direction, rotation_deg)
        pts = [(p.x, p.y) for p in tips.values()]
        pts.append((position.x, position.y))

        # Add wrist and arm points
        dir_y = 1.0 if direction == "down" else -1.0
        rad = math.radians(rotation_deg)
        wrist_local_y = -65.0 * dir_y * scale
        for wx in (-45.0, 45.0):
            pt = (position.x + wx * scale, position.y + wrist_local_y)
            pts.append(self._rotate_pt(pt, (position.x, position.y), rad))

        if include_shockwave:
            r = self.NOMINAL_SHOCKWAVE_RADIUS * (scale / self.NOMINAL_SCALE)
            pts.extend([
                (position.x - r, position.y),
                (position.x + r, position.y),
                (position.x, position.y - r),
                (position.x, position.y + r),
            ])

        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    def render_palm(
        self,
        position: Point2D,
        scale: float = NOMINAL_SCALE,
        facing: int = 1,
        direction: str = "down",
        rotation_deg: float = 0.0,
        descent_progress: float = 1.0,
        show_aura: bool = True,
        show_seal: bool = True,
        show_shockwave: bool = True,
        canvas_size: tuple[int, int] = DEFAULT_CANVAS_SIZE,
        custom_stroke_color: Optional[tuple[int, int, int, int]] = None,
        custom_aura_color: Optional[tuple[int, int, int, int]] = None,
    ) -> Image.Image:
        """
        Render the Giant Buddha Palm onto an isolated RGBA canvas.

        Parameters:
          position: Palm center coordinate on canvas.
          scale: Scaling multiplier (default 3.50).
          facing: +1 for right-handed orientation, -1 for mirrored left-handed.
          direction: "down" (fingers pointing downward, wrist above) or "up".
          rotation_deg: Clockwise rotation in degrees around palm center.
          descent_progress: [0.0, 1.0] indicating descent completion.
          show_aura: Whether to render golden radiant aura.
          show_seal: Whether to render Wan Seal (卍) and sacred concentric mandalas.
          show_shockwave: Whether to render golden crushing shockwave arcs.
          canvas_size: Canvas dimensions (width, height), default (1080, 1920).
          custom_stroke_color: Override outline color (default #1A1817).
          custom_aura_color: Override aura glow color (default #F6AD55).

        Returns:
          Transparent RGBA PIL Image.
        """
        if facing not in (+1, -1):
            raise ValueError(f"Facing must be +1 or -1, got {facing}")
        if scale <= 0.1 or scale > 5.0 or not math.isfinite(scale):
            raise ValueError(f"Scale must be in range (0.1, 5.0], got {scale}")
        if direction not in ("down", "up"):
            raise ValueError(f"Direction must be 'down' or 'up', got {direction}")
        if not (math.isfinite(position.x) and math.isfinite(position.y)):
            raise ValueError(f"Position coordinates must be finite, got {position}")

        width, height = canvas_size
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        stroke_col = custom_stroke_color or self.COLOR_INK_STROKE
        aura_col = custom_aura_color or self.COLOR_AURA_GLOW

        cx, cy = position.x, position.y
        rad = math.radians(rotation_deg)
        dir_y = 1.0 if direction == "down" else -1.0

        # 1. Background Aura Glow & Shockwave Layer
        if show_shockwave:
            self._render_shockwaves(
                draw=draw,
                center=(cx, cy),
                scale=scale,
                facing=facing,
                dir_y=dir_y,
                rad=rad,
                progress=descent_progress,
                aura_col=aura_col,
            )

        if show_aura:
            self._render_aura_glow(
                draw=draw,
                center=(cx, cy),
                scale=scale,
                facing=facing,
                dir_y=dir_y,
                rad=rad,
                aura_col=aura_col,
            )

        # 2. Forearm & Celestial Wrist Base
        self._render_forearm_and_wrist(
            draw=draw,
            center=(cx, cy),
            scale=scale,
            facing=facing,
            dir_y=dir_y,
            rad=rad,
            stroke_col=stroke_col,
        )

        # 3. Main Palm Foundation (Palmar surface & Thenar/Hypothenar eminences)
        self._render_palm_body(
            draw=draw,
            center=(cx, cy),
            scale=scale,
            facing=facing,
            dir_y=dir_y,
            rad=rad,
            stroke_col=stroke_col,
        )

        # 4. Five Distinct Sculpted Fingers with Knuckle Creases
        self._render_fingers(
            draw=draw,
            center=(cx, cy),
            scale=scale,
            facing=facing,
            dir_y=dir_y,
            rad=rad,
            stroke_col=stroke_col,
        )

        # 5. Sacred Wan Seal (卍) & Radiant Mandalas
        if show_seal:
            self._render_sacred_seal_and_mandalas(
                draw=draw,
                center=(cx, cy),
                scale=scale,
                rad=rad,
                stroke_col=stroke_col,
                mandala_col=self.COLOR_MANDALA_GOLD,
            )

        return img

    def _render_shockwaves(
        self,
        draw: ImageDraw.ImageDraw,
        center: tuple[float, float],
        scale: float,
        facing: int,
        dir_y: float,
        rad: float,
        progress: float,
        aura_col: tuple[int, int, int, int],
    ) -> None:
        """Render expanding shockwave pressure arcs and air compression rings."""
        cx, cy = center
        base_r = self.NOMINAL_SHOCKWAVE_RADIUS * (scale / self.NOMINAL_SCALE) * max(0.2, progress)

        # Outer compressive shockwave ellipse below the palm
        for r_ratio, alpha_mult, w_mult in [(1.0, 0.45, 4.0), (0.80, 0.65, 3.0), (0.60, 0.85, 2.5)]:
            r = base_r * r_ratio
            color = (aura_col[0], aura_col[1], aura_col[2], int(aura_col[3] * alpha_mult))
            w = max(1, round(w_mult * scale))

            # Elliptical arc points ahead of fingertips
            arc_pts = []
            for deg in range(-65, 66, 5):
                th = math.radians(deg)
                local_x = r * math.sin(th)
                local_y = (130.0 * dir_y * scale) + (r * 0.45 * math.cos(th) * dir_y)
                world_x = cx + local_x
                world_y = cy + local_y
                arc_pts.append(self._rotate_pt((world_x, world_y), (cx, cy), rad))

            if len(arc_pts) >= 2:
                draw.line(arc_pts, fill=color, width=w)

    def _render_aura_glow(
        self,
        draw: ImageDraw.ImageDraw,
        center: tuple[float, float],
        scale: float,
        facing: int,
        dir_y: float,
        rad: float,
        aura_col: tuple[int, int, int, int],
    ) -> None:
        """Render soft multi-tier radiant golden aura surrounding the palm."""
        cx, cy = center
        r_palm = 110.0 * scale
        for aura_r, a_factor in [(r_palm * 1.35, 35), (r_palm * 1.18, 65), (r_palm * 1.05, 110)]:
            col = (aura_col[0], aura_col[1], aura_col[2], a_factor)
            # Oval surrounding the palm center
            pts = []
            for deg in range(0, 360, 15):
                th = math.radians(deg)
                x = cx + aura_r * math.cos(th)
                y = cy + aura_r * 1.15 * math.sin(th)
                pts.append(self._rotate_pt((x, y), (cx, cy), rad))
            draw.polygon(pts, fill=col)

    def _render_forearm_and_wrist(
        self,
        draw: ImageDraw.ImageDraw,
        center: tuple[float, float],
        scale: float,
        facing: int,
        dir_y: float,
        rad: float,
        stroke_col: tuple[int, int, int, int],
    ) -> None:
        """Render celestial forearm extending into the heavens with golden vajra wristlet."""
        cx, cy = center
        w_stroke = max(2, round(4.0 * scale))

        # Forearm polygon extending upwards into heaven
        arm_top_y = cy - (320.0 * dir_y * scale)
        wrist_y = cy - (65.0 * dir_y * scale)
        w_top = 44.0 * scale
        w_wrist = 40.0 * scale

        arm_pts_raw = [
            (cx - w_top, arm_top_y),
            (cx + w_top, arm_top_y),
            (cx + w_wrist, wrist_y),
            (cx - w_wrist, wrist_y),
        ]
        arm_pts = [self._rotate_pt(p, (cx, cy), rad) for p in arm_pts_raw]
        draw.polygon(arm_pts, fill=self.COLOR_PALM_BRONZE, outline=stroke_col)

        # Vajra Wristlet (Vòng Kim Cang Thủ Trạc)
        wristlet_h = 18.0 * scale
        w_band = 48.0 * scale
        wristlet_raw = [
            (cx - w_band, wrist_y - wristlet_h * dir_y * 0.5),
            (cx + w_band, wrist_y - wristlet_h * dir_y * 0.5),
            (cx + w_band, wrist_y + wristlet_h * dir_y * 0.5),
            (cx - w_band, wrist_y + wristlet_h * dir_y * 0.5),
        ]
        wristlet_pts = [self._rotate_pt(p, (cx, cy), rad) for p in wristlet_raw]
        draw.polygon(wristlet_pts, fill=self.COLOR_MANDALA_GOLD, outline=stroke_col)

        # Central Vajra Ruby Oval
        ruby_w = 8.0 * scale
        ruby_h = 10.0 * scale
        ruby_raw = [
            (cx - ruby_w, wrist_y),
            (cx, wrist_y - ruby_h * dir_y),
            (cx + ruby_w, wrist_y),
            (cx, wrist_y + ruby_h * dir_y),
        ]
        ruby_pts = [self._rotate_pt(p, (cx, cy), rad) for p in ruby_raw]
        draw.polygon(ruby_pts, fill=self.COLOR_RUBY_ACCENT, outline=stroke_col)

    def _render_palm_body(
        self,
        draw: ImageDraw.ImageDraw,
        center: tuple[float, float],
        scale: float,
        facing: int,
        dir_y: float,
        rad: float,
        stroke_col: tuple[int, int, int, int],
    ) -> None:
        """Render the anatomical core palm body with golden highlight."""
        cx, cy = center
        w_stroke = max(2, round(4.0 * scale))

        # Anatomical palm contour (Thenar eminence on thumb side, hypothenar on pinky side)
        # Thumb side is at -X * facing, pinky side at +X * facing
        raw_palm_outline = [
            (-38.0 * facing, -65.0 * dir_y),  # Wrist inner
            (-54.0 * facing, -30.0 * dir_y),  # Thenar eminence upper
            (-60.0 * facing, -5.0 * dir_y),   # Thenar eminence peak (mô cái)
            (-48.0 * facing, 25.0 * dir_y),   # Base of index finger
            (-32.0 * facing, 38.0 * dir_y),   # Knuckle index
            (-6.0 * facing, 44.0 * dir_y),    # Knuckle middle
            (20.0 * facing, 40.0 * dir_y),    # Knuckle ring
            (42.0 * facing, 32.0 * dir_y),    # Knuckle pinky
            (56.0 * facing, 12.0 * dir_y),    # Hypothenar upper
            (54.0 * facing, -20.0 * dir_y),   # Hypothenar mid (mô út)
            (40.0 * facing, -65.0 * dir_y),   # Wrist outer
        ]
        world_palm = [
            self._rotate_pt((cx + x * scale, cy + y * scale), (cx, cy), rad)
            for x, y in raw_palm_outline
        ]
        draw.polygon(world_palm, fill=self.COLOR_PALM_BRONZE, outline=stroke_col)

        # Luminous golden highlight at palm center
        raw_hl = []
        for deg in range(0, 360, 20):
            th = math.radians(deg)
            hx = 32.0 * math.cos(th)
            hy = 36.0 * math.sin(th)
            raw_hl.append((hx, hy))
        world_hl = [
            self._rotate_pt((cx + x * scale, cy + y * scale), (cx, cy), rad)
            for x, y in raw_hl
        ]
        draw.polygon(world_hl, fill=self.COLOR_PALM_HIGHLIGHT)

    def _render_fingers(
        self,
        draw: ImageDraw.ImageDraw,
        center: tuple[float, float],
        scale: float,
        facing: int,
        dir_y: float,
        rad: float,
        stroke_col: tuple[int, int, int, int],
    ) -> None:
        """Render each of the 5 distinct sculpted fingers with interdigital clefts and creases."""
        cx, cy = center
        w_stroke = max(2, round(3.5 * scale))
        w_crease = max(1, round(2.0 * scale))

        # 1. Thumb (Ngón cái)
        thumb_poly_raw = [
            (-45.0 * facing, -16.0 * dir_y),  # Webbing root
            (-64.0 * facing, 2.0 * dir_y),    # Outer proximal
            (-84.0 * facing, 26.0 * dir_y),   # Outer distal
            (-82.0 * facing, 36.0 * dir_y),   # Thumb tip
            (-70.0 * facing, 34.0 * dir_y),   # Inner distal
            (-52.0 * facing, 16.0 * dir_y),   # Inner proximal
            (-38.0 * facing, -2.0 * dir_y),   # Inner base
        ]
        thumb_pts = [
            self._rotate_pt((cx + x * scale, cy + y * scale), (cx, cy), rad)
            for x, y in thumb_poly_raw
        ]
        draw.polygon(thumb_pts, fill=self.COLOR_PALM_BRONZE, outline=stroke_col)

        # Thumb knuckle creases
        for c_p1, c_p2 in [
            ((-66.0 * facing, 4.0 * dir_y), (-54.0 * facing, 14.0 * dir_y)),
            ((-76.0 * facing, 22.0 * dir_y), (-68.0 * facing, 28.0 * dir_y)),
        ]:
            pt1 = self._rotate_pt((cx + c_p1[0] * scale, cy + c_p1[1] * scale), (cx, cy), rad)
            pt2 = self._rotate_pt((cx + c_p2[0] * scale, cy + c_p2[1] * scale), (cx, cy), rad)
            draw.line([pt1, pt2], fill=stroke_col, width=w_crease)

        # 2. Index Finger (Ngón trỏ)
        index_poly_raw = [
            (-39.0 * facing, 34.0 * dir_y),
            (-39.0 * facing, 80.0 * dir_y),
            (-36.0 * facing, 122.0 * dir_y),
            (-28.0 * facing, 128.0 * dir_y),  # Tip
            (-20.0 * facing, 122.0 * dir_y),
            (-19.0 * facing, 80.0 * dir_y),
            (-19.0 * facing, 38.0 * dir_y),
        ]
        index_pts = [
            self._rotate_pt((cx + x * scale, cy + y * scale), (cx, cy), rad)
            for x, y in index_poly_raw
        ]
        draw.polygon(index_pts, fill=self.COLOR_PALM_BRONZE, outline=stroke_col)

        # Index creases
        for cy_c in [68.0, 102.0]:
            p1 = self._rotate_pt((cx - 37.0 * facing * scale, cy + cy_c * dir_y * scale), (cx, cy), rad)
            p2 = self._rotate_pt((cx - 21.0 * facing * scale, cy + cy_c * dir_y * scale), (cx, cy), rad)
            draw.line([p1, p2], fill=stroke_col, width=w_crease)

        # 3. Middle Finger (Ngón giữa - Longest finger)
        mid_poly_raw = [
            (-17.0 * facing, 40.0 * dir_y),
            (-17.0 * facing, 95.0 * dir_y),
            (-14.0 * facing, 146.0 * dir_y),
            (-4.0 * facing, 152.0 * dir_y),  # Tip
            (6.0 * facing, 146.0 * dir_y),
            (7.0 * facing, 95.0 * dir_y),
            (7.0 * facing, 40.0 * dir_y),
        ]
        mid_pts = [
            self._rotate_pt((cx + x * scale, cy + y * scale), (cx, cy), rad)
            for x, y in mid_poly_raw
        ]
        draw.polygon(mid_pts, fill=self.COLOR_PALM_BRONZE, outline=stroke_col)

        # Middle creases
        for cy_c in [78.0, 118.0]:
            p1 = self._rotate_pt((cx - 15.0 * facing * scale, cy + cy_c * dir_y * scale), (cx, cy), rad)
            p2 = self._rotate_pt((cx + 5.0 * facing * scale, cy + cy_c * dir_y * scale), (cx, cy), rad)
            draw.line([p1, p2], fill=stroke_col, width=w_crease)

        # 4. Ring Finger (Ngón áp út)
        ring_poly_raw = [
            (9.0 * facing, 38.0 * dir_y),
            (9.0 * facing, 88.0 * dir_y),
            (11.0 * facing, 130.0 * dir_y),
            (17.0 * facing, 136.0 * dir_y),  # Tip
            (25.0 * facing, 130.0 * dir_y),
            (27.0 * facing, 88.0 * dir_y),
            (27.0 * facing, 36.0 * dir_y),
        ]
        ring_pts = [
            self._rotate_pt((cx + x * scale, cy + y * scale), (cx, cy), rad)
            for x, y in ring_poly_raw
        ]
        draw.polygon(ring_pts, fill=self.COLOR_PALM_BRONZE, outline=stroke_col)

        # Ring creases
        for cy_c in [74.0, 108.0]:
            p1 = self._rotate_pt((cx + 10.0 * facing * scale, cy + cy_c * dir_y * scale), (cx, cy), rad)
            p2 = self._rotate_pt((cx + 25.0 * facing * scale, cy + cy_c * dir_y * scale), (cx, cy), rad)
            draw.line([p1, p2], fill=stroke_col, width=w_crease)

        # 5. Pinky Finger (Ngón út - Elegant lotus curve)
        pinky_poly_raw = [
            (29.0 * facing, 34.0 * dir_y),
            (31.0 * facing, 68.0 * dir_y),
            (36.0 * facing, 98.0 * dir_y),
            (44.0 * facing, 102.0 * dir_y),  # Tip
            (50.0 * facing, 95.0 * dir_y),
            (47.0 * facing, 65.0 * dir_y),
            (43.0 * facing, 30.0 * dir_y),
        ]
        pinky_pts = [
            self._rotate_pt((cx + x * scale, cy + y * scale), (cx, cy), rad)
            for x, y in pinky_poly_raw
        ]
        draw.polygon(pinky_pts, fill=self.COLOR_PALM_BRONZE, outline=stroke_col)

        # Pinky creases
        for cy_c in [58.0, 82.0]:
            p1 = self._rotate_pt((cx + 31.0 * facing * scale, cy + cy_c * dir_y * scale), (cx, cy), rad)
            p2 = self._rotate_pt((cx + 46.0 * facing * scale, cy + cy_c * dir_y * scale), (cx, cy), rad)
            draw.line([p1, p2], fill=stroke_col, width=w_crease)

    def _render_sacred_seal_and_mandalas(
        self,
        draw: ImageDraw.ImageDraw,
        center: tuple[float, float],
        scale: float,
        rad: float,
        stroke_col: tuple[int, int, int, int],
        mandala_col: tuple[int, int, int, int],
    ) -> None:
        """Render concentric golden mandala circles and sacred Wan Seal (卍) at palm center."""
        cx, cy = center
        w_mandala = max(1, round(2.0 * scale))
        w_wan = max(2, round(3.5 * scale))

        # 1. Concentric Golden Mandala Rings
        for r_base in [26.0, 48.0, 72.0]:
            r = r_base * scale
            ring_pts = []
            for deg in range(0, 360, 10):
                th = math.radians(deg)
                px = cx + r * math.cos(th)
                py = cy + r * math.sin(th)
                ring_pts.append(self._rotate_pt((px, py), (cx, cy), rad))
            ring_pts.append(ring_pts[0])
            draw.line(ring_pts, fill=mandala_col, width=w_mandala)

        # 8 Radiating sacred rays between ring 1 and ring 2
        for deg in range(0, 360, 45):
            th = math.radians(deg)
            r1 = 28.0 * scale
            r2 = 46.0 * scale
            p1 = self._rotate_pt((cx + r1 * math.cos(th), cy + r1 * math.sin(th)), (cx, cy), rad)
            p2 = self._rotate_pt((cx + r2 * math.cos(th), cy + r2 * math.sin(th)), (cx, cy), rad)
            draw.line([p1, p2], fill=mandala_col, width=w_mandala)

        # 2. Sacred Wan Seal (Ấn Ký Chữ Vạn 卍)
        L = 14.0 * scale
        # 5 Segments forming the sacred swastika 卍
        # Central horizontal and vertical bars + 4 hooked arms
        segments = [
            # Central horizontal
            ((-L, 0.0), (L, 0.0)),
            # Central vertical
            ((0.0, -L), (0.0, L)),
            # Top arm bends left
            ((0.0, -L), (-L, -L)),
            # Bottom arm bends right
            ((0.0, L), (L, L)),
            # Left arm bends down
            ((-L, 0.0), (-L, L)),
            # Right arm bends up
            ((L, 0.0), (L, -L)),
        ]

        # Draw gold underlay stroke for halo contrast
        w_under = w_wan + max(2, round(2.0 * scale))
        for (x1, y1), (x2, y2) in segments:
            pt1 = self._rotate_pt((cx + x1, cy + y1), (cx, cy), rad)
            pt2 = self._rotate_pt((cx + x2, cy + y2), (cx, cy), rad)
            draw.line([pt1, pt2], fill=mandala_col, width=w_under)

        # Draw ink core stroke
        for (x1, y1), (x2, y2) in segments:
            pt1 = self._rotate_pt((cx + x1, cy + y1), (cx, cy), rad)
            pt2 = self._rotate_pt((cx + x2, cy + y2), (cx, cy), rad)
            draw.line([pt1, pt2], fill=stroke_col, width=w_wan)
