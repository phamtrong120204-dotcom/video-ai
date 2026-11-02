"""
Dark Myth Stickman Auto-Studio - Stage 8: Notebook Background Warp Distortion.

Implements coordinate warp distortion fields on the notebook background canvas,
producing physical bending of horizontal ruled lines under the pressure of the
Giant Buddha Palm (giant_palm_suppression) and expanding combat shockwaves.
"""

import math
from typing import Optional, Union

import numpy as np
from PIL import Image

from app.modules.animation.stickman_models import Point2D
from app.modules.animation.vfx_models import VFXEvent, VFXEventType, WarpProfile


class WarpDistortionField:
    """
    Manages spatial coordinate deformation across the notebook paper background.
    """

    def __init__(
        self,
        width: int = 1080,
        height: int = 1920,
        grid_nx: int = 36,
        grid_ny: int = 64,
    ) -> None:
        self.width = width
        self.height = height
        self.grid_nx = grid_nx
        self.grid_ny = grid_ny

        # Precompute base mesh coordinates
        self.xs = np.linspace(0, self.width, self.grid_nx + 1)
        self.ys = np.linspace(0, self.height, self.grid_ny + 1)
        self.base_X, self.base_Y = np.meshgrid(self.xs, self.ys)

        # Precompute target bounding boxes for PIL Transform.MESH
        self._target_boxes: list[tuple[int, int, int, int]] = []
        for j in range(self.grid_ny):
            for i in range(self.grid_nx):
                self._target_boxes.append((
                    int(self.xs[i]),
                    int(self.ys[j]),
                    int(self.xs[i + 1]),
                    int(self.ys[j + 1]),
                ))

    def apply_distortion(
        self,
        background_image: Image.Image,
        active_events: list[VFXEvent],
        current_time_sec: float,
    ) -> Image.Image:
        """
        Apply active warp events onto the background image.

        If no warp events are active, returns the pristine background image directly
        with zero computational overhead.
        """
        # Filter active background warp events
        warp_events: list[tuple[VFXEvent, float]] = []
        for ev in active_events:
            if ev.event_type == VFXEventType.BACKGROUND_WARP:
                u = ev.get_progress(current_time_sec)
                if u is not None and 0.0 <= u <= 1.0:
                    warp_events.append((ev, u))

        if not warp_events:
            return background_image

        # Cumulative displacement arrays
        delta_X = np.zeros_like(self.base_X)
        delta_Y = np.zeros_like(self.base_Y)
        has_significant_warp = False

        for ev, u in warp_events:
            profile = ev.metadata.get("profile", WarpProfile.PALM_DEPRESSION)
            x0 = ev.center.x
            y0 = ev.center.y
            max_amp = ev.metadata.get("max_amplitude_px", 80.0) * ev.intensity

            # Temporal envelope: rises to peak at mid-duration, smooth decay
            # A(u) = max_amp * sin(pi * u)
            amp = max_amp * math.sin(math.pi * u)

            if abs(amp) < 0.5:
                continue

            has_significant_warp = True

            if profile == WarpProfile.PALM_DEPRESSION:
                # Downward gravitational sag under the Giant Palm
                sigma_x = ev.metadata.get("sigma_x", 320.0)
                sigma_y = ev.metadata.get("sigma_y", 240.0)
                weight = np.exp(-((self.base_X - x0) ** 2 / (2 * sigma_x**2) + (self.base_Y - y0) ** 2 / (2 * sigma_y**2)))
                # Sags lines downward: source Y is above target Y
                delta_Y -= amp * weight

            elif profile == WarpProfile.RADIAL_SHOCKWAVE:
                # Outward expanding ripple wave
                r_max = ev.radius
                r_current = max(10.0, r_max * u)
                sigma = ev.metadata.get("wave_thickness", 60.0)

                dist = np.hypot(self.base_X - x0, self.base_Y - y0)
                wave_profile = np.sin(np.pi * (dist - r_current) / sigma) * np.exp(-((dist - r_current) ** 2) / (2 * sigma**2))
                radial_disp = amp * wave_profile

                # Radial vector
                dist_safe = np.maximum(dist, 1e-4)
                ux = (self.base_X - x0) / dist_safe
                uy = (self.base_Y - y0) / dist_safe

                delta_X -= radial_disp * ux
                delta_Y -= radial_disp * uy

        if not has_significant_warp:
            return background_image

        src_X = self.base_X + delta_X
        src_Y = self.base_Y + delta_Y

        # Build mesh quad data
        mesh_data: list[tuple[tuple[int, int, int, int], tuple[float, ...]]] = []
        box_idx = 0
        for j in range(self.grid_ny):
            for i in range(self.grid_nx):
                target_box = self._target_boxes[box_idx]
                box_idx += 1
                source_quad = (
                    float(src_X[j, i]), float(src_Y[j, i]),
                    float(src_X[j + 1, i]), float(src_Y[j + 1, i]),
                    float(src_X[j + 1, i + 1]), float(src_Y[j + 1, i + 1]),
                    float(src_X[j, i + 1]), float(src_Y[j, i + 1]),
                )
                mesh_data.append((target_box, source_quad))

        # Perform high-performance PIL MESH warp
        return background_image.transform(
            (self.width, self.height),
            Image.Transform.MESH,
            mesh_data,
            resample=Image.Resampling.BILINEAR,
        )
