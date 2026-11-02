"""Abstract Interface for Procedural 2D Stickman Animation Engine (IAnimationEngine)."""

from abc import ABC, abstractmethod
from pathlib import Path

from app.schemas.scene_schema import SceneSchema


class IAnimationEngine(ABC):
    """Contract for rendering 9:16 notebook-paper stickman combat frames synchronized to audio duration."""

    @abstractmethod
    def render_scene_frames(self, scene: SceneSchema, duration_sec: float, output_dir: Path) -> Path:
        """
        Render stickman animation frames for `scene` matching `duration_sec`.

        Returns:
            Path: Path to the rendered scene video segment or frame sequence manifest inside `output_dir`.
        """
        raise NotImplementedError
