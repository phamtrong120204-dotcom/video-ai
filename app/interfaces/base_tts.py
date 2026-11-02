"""Abstract Interface for Vietnamese TTS & Audio Timing Engine (IAudioEngine)."""

from abc import ABC, abstractmethod
from pathlib import Path

from app.schemas.scene_schema import SceneSchema


class IAudioEngine(ABC):
    """Contract for generating scene voiceovers and returning exact measured audio duration."""

    @abstractmethod
    def generate_scene_audio(self, scene: SceneSchema, output_dir: Path) -> tuple[Path, float]:
        """
        Synthesize Vietnamese voiceover for `scene` into `output_dir`.

        Returns:
            tuple[Path, float]: (path_to_generated_audio_file, measured_duration_in_seconds)
        """
        raise NotImplementedError
