"""
Dark Myth Stickman Auto-Studio - Stage 8: VFX Data Models & Events.

Defines VFX events, particle specifications, warp distortion profiles,
and compositing layer configurations for Dark Myth combat visual effects.
"""

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Optional

from app.modules.animation.stickman_models import Point2D


class VFXEventType(str, Enum):
    """Categorized visual effect event types."""

    CLASH_SPARKS = "clash_sparks"
    GROUND_CRACK = "ground_crack"
    SHOCKWAVE_RING = "shockwave_ring"
    BACKGROUND_WARP = "background_warp"
    MOTION_TRAIL = "motion_trail"
    DARK_AURA = "dark_aura"
    BUDDHA_PALM_AURA = "buddha_palm_aura"
    PAPER_DUST = "paper_dust"


class WarpProfile(str, Enum):
    """Type of background spatial distortion."""

    PALM_DEPRESSION = "palm_depression"  # Downward gravitational sag of horizontal ruled lines
    RADIAL_SHOCKWAVE = "radial_shockwave"  # Expanding circular ripple wave


@dataclass
class VFXEvent:
    """
    Timeline visual effect event.

    Attributes:
      event_id: Unique identifier for tracking and audio synchronization.
      event_type: VFXEventType enum.
      start_time_sec: Start timestamp in seconds.
      duration_sec: Lifespan duration in seconds.
      center: Coordinate center of the effect in Canvas Space (1080x1920).
      intensity: Magnitude multiplier (0.0 to 2.0).
      radius: Primary radius of influence in px.
      color: Primary RGBA color tuple.
      metadata: Arbitrary context parameters (e.g. action_preset, actor_id).
    """

    event_id: str
    event_type: VFXEventType
    start_time_sec: float
    duration_sec: float
    center: Point2D
    intensity: float = 1.0
    radius: float = 200.0
    color: tuple[int, int, int, int] = (217, 38, 38, 255)  # Dark Myth Crimson #D92626
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.start_time_sec < 0.0 or not math.isfinite(self.start_time_sec):
            raise ValueError(f"start_time_sec must be non-negative and finite, got {self.start_time_sec}")
        if self.duration_sec <= 0.0 or not math.isfinite(self.duration_sec):
            raise ValueError(f"duration_sec must be positive and finite, got {self.duration_sec}")
        if self.intensity < 0.0 or not math.isfinite(self.intensity):
            raise ValueError(f"intensity must be non-negative and finite, got {self.intensity}")
        if self.radius <= 0.0 or not math.isfinite(self.radius):
            raise ValueError(f"radius must be positive and finite, got {self.radius}")

    @property
    def end_time_sec(self) -> float:
        return self.start_time_sec + self.duration_sec

    def get_progress(self, current_time_sec: float) -> Optional[float]:
        """
        Return normalized progress in [0.0, 1.0] if current_time_sec is within
        the event's active window, or None if inactive.
        """
        if self.start_time_sec <= current_time_sec <= self.end_time_sec:
            return (current_time_sec - self.start_time_sec) / self.duration_sec
        return None


@dataclass
class Particle:
    """An individual animated particle."""

    x: float
    y: float
    vx: float
    vy: float
    radius: float
    color: tuple[int, int, int, int]
    age: float
    lifespan: float
    particle_type: str = "ember"

    @property
    def is_alive(self) -> bool:
        return self.age < self.lifespan

    @property
    def progress(self) -> float:
        return min(1.0, max(0.0, self.age / self.lifespan)) if self.lifespan > 0 else 1.0


@dataclass
class VFXConfig:
    """Global configuration for VFX Engine rendering."""

    canvas_width: int = 1080
    canvas_height: int = 1920
    max_particles: int = 250  # Cap on active CPU particles to prevent lag
    enable_motion_trails: bool = True
    enable_background_warp: bool = True
    enable_dark_aura: bool = True
    enable_clash_sparks: bool = True
    enable_ground_cracks: bool = True
    warp_grid_nx: int = 36  # Mesh horizontal subdivision
    warp_grid_ny: int = 64  # Mesh vertical subdivision
    seed: int = 108
