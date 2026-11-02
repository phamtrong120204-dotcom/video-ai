"""
Dark Myth Stickman Auto-Studio - Stage 8: Particle & Impact Visual Effects System.

Generates deterministic particle effects including Dark Corruption Aura,
Weapon Clash Sparks, Ground Lightning/Paper Fractures, Shockwaves, and Paper Dust.
"""

import math
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw

from app.modules.animation.stickman_models import Point2D
from app.modules.animation.vfx_models import Particle, VFXConfig, VFXEvent, VFXEventType


class ParticleSystem:
    """
    Manages deterministic particle simulation and procedural impact effects.
    """

    def __init__(self, config: Optional[VFXConfig] = None) -> None:
        self.config = config or VFXConfig()

    def render_dark_aura(
        self,
        character_center: Point2D,
        facing: int,
        scale: float,
        current_time_sec: float,
        aura_color: tuple[int, int, int] = (217, 38, 38),  # Crimson #D92626
        num_particles: int = 35,
        seed: int = 42,
    ) -> Image.Image:
        """
        Render rising dark ink smoke and burning embers trailing the character.
        """
        w, h = self.config.canvas_width, self.config.canvas_height
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Deterministic RNG based on seed and time bucket
        time_slot = int(current_time_sec * 30.0)
        rng = np.random.default_rng(seed + time_slot)

        # 1. Rising dark smoke tendrils & embers
        for i in range(num_particles):
            # Spawn in elliptical region around character hips/chest
            angle = rng.uniform(0, 2 * math.pi)
            dist_x = rng.uniform(-40.0, 40.0) * scale
            dist_y = rng.uniform(-100.0, 30.0) * scale

            # Phase offset based on particle index and time
            phase = (current_time_sec * 2.5 + i * 0.15) % 1.0
            # Upward draft
            y_offset = -phase * 120.0 * scale
            # Horizontal sinuous drift
            x_drift = math.sin(current_time_sec * 6.0 + i) * 18.0 * scale - (facing * phase * 25.0 * scale)

            px = character_center.x + dist_x + x_drift
            py = character_center.y + dist_y + y_offset

            # Size shrinks as it rises
            rad = max(1.5, (1.0 - phase) * rng.uniform(3.5, 9.0) * scale)
            # Alpha fades out near top
            alpha = int(max(0, min(255, (1.0 - phase) * 220)))

            if i % 3 == 0:
                # Black ink vapor
                draw.ellipse(
                    [px - rad, py - rad, px + rad, py + rad],
                    fill=(20, 18, 22, alpha),
                )
            else:
                # Glowing crimson/gold ember
                draw.ellipse(
                    [px - rad, py - rad, px + rad, py + rad],
                    fill=(aura_color[0], aura_color[1], aura_color[2], alpha),
                )

        return img

    def render_clash_sparks(
        self,
        event: VFXEvent,
        progress: float,
        num_sparks: int = 40,
        seed: int = 101,
    ) -> Image.Image:
        """
        Render explosive high-speed clash sparks radiating from impact center.
        """
        w, h = self.config.canvas_width, self.config.canvas_height
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        rng = np.random.default_rng(seed + int(event.start_time_sec * 100))
        center = event.center
        intensity = event.intensity

        # Sparks expand radially with gravity and drag
        alpha = int(max(0, min(255, (1.0 - progress) * 255)))
        t_flight = progress * event.duration_sec

        for i in range(num_sparks):
            ang = rng.uniform(0, 2 * math.pi)
            speed = rng.uniform(250.0, 750.0) * intensity
            # Drag deceleration
            drag = math.exp(-3.0 * progress)
            dist = speed * t_flight * drag

            # Gravity drops sparks downward
            gravity = 400.0 * (t_flight**2)

            px = center.x + math.cos(ang) * dist
            py = center.y + math.sin(ang) * dist + gravity

            # Particle tail
            tail_len = max(3.0, (1.0 - progress) * 14.0 * intensity)
            tail_x = px - math.cos(ang) * tail_len
            tail_y = py - math.sin(ang) * tail_len

            # Spark color: white core, golden/crimson rim
            spark_color = (
                (255, 255, 255, alpha) if i % 2 == 0
                else (event.color[0], event.color[1], event.color[2], alpha)
            )
            draw.line([(tail_x, tail_y), (px, py)], fill=spark_color, width=max(1, round(2.0 * intensity)))

        return img

    def render_shockwave_ring(
        self,
        event: VFXEvent,
        progress: float,
    ) -> Image.Image:
        """
        Render an expanding circular shockwave ring with soft falloff.
        """
        w, h = self.config.canvas_width, self.config.canvas_height
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Radius expands from 0 to event.radius
        current_r = max(5.0, event.radius * progress * event.intensity)
        alpha = int(max(0, min(255, (1.0 - progress) * 220)))

        # Outer colored ring
        thickness = max(2.0, (1.0 - progress) * 8.0 * event.intensity)
        r_outer = current_r
        r_inner = max(1.0, current_r - thickness)

        draw.ellipse(
            [event.center.x - r_outer, event.center.y - r_outer, event.center.x + r_outer, event.center.y + r_outer],
            outline=(event.color[0], event.color[1], event.color[2], alpha),
            width=max(2, round(thickness)),
        )

        # Inner white flash ring
        if progress < 0.4:
            flash_alpha = int((1.0 - (progress / 0.4)) * 180)
            flash_r = max(1.0, current_r * 0.75)
            draw.ellipse(
                [event.center.x - flash_r, event.center.y - flash_r, event.center.x + flash_r, event.center.y + flash_r],
                outline=(255, 255, 255, flash_alpha),
                width=2,
            )

        return img

    def render_ground_cracks(
        self,
        event: VFXEvent,
        progress: float,
        num_branches: int = 8,
        seed: int = 202,
    ) -> Image.Image:
        """
        Render jagged paper fracture / lightning cracks on the ground plane.
        """
        w, h = self.config.canvas_width, self.config.canvas_height
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        rng = np.random.default_rng(seed + int(event.start_time_sec * 50))
        center = event.center
        max_reach = event.radius * event.intensity

        # Cracks burst out fast and fade slowly
        reach_prog = min(1.0, progress / 0.25)
        fade_prog = max(0.0, min(1.0, (progress - 0.4) / 0.6)) if progress > 0.4 else 0.0
        alpha = int(max(0, min(255, (1.0 - fade_prog) * 230)))

        for branch_idx in range(num_branches):
            base_angle = (branch_idx / num_branches) * 2 * math.pi + rng.uniform(-0.15, 0.15)
            cur_pt = (center.x, center.y)
            num_segments = 7
            seg_len = (max_reach * reach_prog) / num_segments

            for seg_idx in range(num_segments):
                # Jagged angular deviation
                dev = rng.uniform(-0.45, 0.45)
                ang = base_angle + dev
                next_pt = (
                    cur_pt[0] + seg_len * math.cos(ang),
                    cur_pt[1] + seg_len * math.sin(ang),
                )
                width = max(1, round((1.0 - (seg_idx / num_segments)) * 4.0 * event.intensity))

                # Draw crack segment: Dark ink core + crimson edge
                draw.line([cur_pt, next_pt], fill=(217, 38, 38, alpha // 2), width=width + 2)
                draw.line([cur_pt, next_pt], fill=(22, 18, 16, alpha), width=width)
                cur_pt = next_pt

        return img

    def render_paper_dust(
        self,
        event: VFXEvent,
        progress: float,
        num_particles: int = 25,
        seed: int = 303,
    ) -> Image.Image:
        """
        Render torn paper fragments bursting upon heavy ground impact.
        """
        w, h = self.config.canvas_width, self.config.canvas_height
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        rng = np.random.default_rng(seed + int(event.start_time_sec * 70))
        center = event.center
        alpha = int(max(0, min(255, (1.0 - progress) * 220)))

        for i in range(num_particles):
            ang = rng.uniform(math.pi * 1.05, math.pi * 1.95)  # Eject upwards from ground
            speed = rng.uniform(180.0, 520.0) * event.intensity
            t_fly = progress * event.duration_sec
            dist = speed * t_fly * math.exp(-2.5 * progress)
            gravity = 350.0 * (t_fly**2)

            px = center.x + math.cos(ang) * dist
            py = center.y + math.sin(ang) * dist + gravity

            # Tiny irregular polygon paper scrap
            size = rng.uniform(2.5, 6.0)
            rot = progress * rng.uniform(6.0, 18.0)
            cos_r, sin_r = math.cos(rot), math.sin(rot)

            poly = [
                (px - size * cos_r, py - size * sin_r),
                (px + size * sin_r, py - size * cos_r),
                (px + size * cos_r, py + size * sin_r),
                (px - size * sin_r, py + size * cos_r),
            ]
            draw.polygon(poly, fill=(244, 239, 230, alpha), outline=(155, 184, 211, alpha // 2))

        return img
