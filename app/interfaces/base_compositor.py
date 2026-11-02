"""Abstract Interface for Video Compositor & Multi-Track Audio Mixer (IVideoCompositor)."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.schemas.job_schema import RenderResult
from app.schemas.scene_schema import SceneSchema


class IVideoCompositor(ABC):
    """Contract for mixing Voice + SFX + BGM and encoding the final 9:16 H.264 MP4."""

    @abstractmethod
    def compose_final_video(
        self,
        job_id: str,
        scenes: list[SceneSchema],
        scene_assets: dict[int, dict[str, Any]],
        output_path: Path,
    ) -> RenderResult:
        """
        Combine all rendered scene visual assets and audio tracks into `output_path` (.mp4).

        Returns:
            RenderResult: Validated final render result with technical metadata.
        """
        raise NotImplementedError
