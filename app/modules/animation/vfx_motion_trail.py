"""
Dark Myth Stickman Auto-Studio - Stage 8: Weapon Motion Trail & Slash Ribbon System.

Connects weapon endpoint histories across frames into fluid anime/Dark Myth
style slash ribbons, motion blur sweeps, and energy cutting arcs.
"""

from collections import deque
import math
from typing import Optional

from PIL import Image, ImageDraw

from app.modules.animation.stickman_models import Point2D


class MotionTrailRenderer:
    """
    Renders trailing slash arcs and motion blur polygons following weapon endpoints.
    """

    def __init__(
        self,
        canvas_size: tuple[int, int] = (1080, 1920),
        max_history: int = 6,
    ) -> None:
        self.width, self.height = canvas_size
        self.max_history = max_history
        # History queue of tuples: (tail_pt, tip_pt, frame_idx)
        self._history: deque[tuple[Point2D, Point2D, int]] = deque(maxlen=max_history)

    def reset(self) -> None:
        """Clear weapon history buffer."""
        self._history.clear()

    def record_endpoints(self, tail_pt: Point2D, tip_pt: Point2D, frame_idx: int) -> None:
        """Record weapon endpoints for the current frame."""
        self._history.append((tail_pt, tip_pt, frame_idx))

    def render_trail(
        self,
        current_tail: Point2D,
        current_tip: Point2D,
        frame_idx: int,
        color: tuple[int, int, int] = (217, 38, 38),  # Crimson
        core_color: tuple[int, int, int] = (255, 255, 255),
    ) -> Image.Image:
        """
        Render a motion trail connecting recent weapon positions into a slash ribbon.
        """
        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Record current points
        self.record_endpoints(current_tail, current_tip, frame_idx)

        history_list = list(self._history)
        n = len(history_list)
        if n < 2:
            return img

        # Connect consecutive frames with quad ribbons
        for i in range(n - 1):
            tail_0, tip_0, f0 = history_list[i]
            tail_1, tip_1, f1 = history_list[i + 1]

            # Don't draw across skipped or disconnected frames
            if abs(f1 - f0) > 2:
                continue

            # Calculate motion distance
            tip_dist = math.hypot(tip_1.x - tip_0.x, tip_1.y - tip_0.y)
            if tip_dist < 4.0:
                continue

            # Normalized age factor: older frames are more transparent
            age_factor = (i + 1) / n  # 0.0 to 1.0
            alpha = int(max(15, min(180, age_factor * 180)))

            quad = [
                (tail_0.x, tail_0.y),
                (tip_0.x, tip_0.y),
                (tip_1.x, tip_1.y),
                (tail_1.x, tail_1.y),
            ]
            fill_rgba = (color[0], color[1], color[2], alpha)
            draw.polygon(quad, fill=fill_rgba)

            # Leading tip cutting edge
            edge_alpha = int(max(25, min(240, age_factor * 240)))
            draw.line(
                [(tip_0.x, tip_0.y), (tip_1.x, tip_1.y)],
                fill=(core_color[0], core_color[1], core_color[2], edge_alpha),
                width=max(2, round(3.0 * age_factor)),
            )

        return img
