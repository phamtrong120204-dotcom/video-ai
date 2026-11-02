"""Audio Engine Module for Vietnamese TTS and Audio Timing."""

from app.interfaces.base_tts import IAudioEngine
from app.modules.audio.audio_compositor import AudioCompositor
from app.modules.audio.audio_models import (
    AudioClip,
    AudioTimeline,
    AudioTrackType,
    DuckingConfig,
    MixConfig,
)
from app.modules.audio.edge_tts_engine import EdgeTTSAudioEngine
from app.modules.audio.edge_tts_engine import EdgeTTSAudioEngine as AudioEngine
from app.modules.audio.sfx_timeline_mapper import (
    ACTION_PRESET_SFX_MAP,
    SfxTimelineMapper,
)
from app.modules.audio.sound_library import SoundAsset, SoundLibrary
from app.modules.audio.video_audio_integrator import VideoAudioIntegrator


class StubAudioEngine(IAudioEngine):
    """Deterministic skeleton audio engine generating placeholder audio artifact for mock tests."""

    def __init__(self, words_per_second: float = 3.2, min_duration_sec: float = 2.5) -> None:
        self.words_per_second = words_per_second
        self.min_duration_sec = min_duration_sec

    def generate_scene_audio(self, scene, output_dir):
        from pathlib import Path
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_path = output_dir / f"scene_{scene.scene_id:02d}_voice.wav"
        word_count = len(scene.narration_text.split())
        duration_sec = round(max(self.min_duration_sec, word_count / self.words_per_second), 2)
        audio_path.write_bytes(b"RIFF_STUB_WAV_PHASE3")
        scene.audio_duration_sec = duration_sec
        scene.voice_audio_path = str(audio_path.resolve())
        return audio_path, duration_sec


__all__ = [
    "EdgeTTSAudioEngine",
    "AudioEngine",
    "StubAudioEngine",
    "AudioClip",
    "AudioTrackType",
    "AudioTimeline",
    "DuckingConfig",
    "MixConfig",
    "SoundAsset",
    "SoundLibrary",
    "SfxTimelineMapper",
    "ACTION_PRESET_SFX_MAP",
    "AudioCompositor",
    "VideoAudioIntegrator",
]
