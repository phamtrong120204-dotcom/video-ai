"""
Dark Myth Stickman Auto-Studio - Stage 7: Audio Models & Configuration.

Data models for audio clips, tracks, timeline containers, ducking configurations,
and master mixing specifications.
"""

from dataclasses import dataclass, field
from enum import Enum
import math
from pathlib import Path
from typing import Optional, Union


class AudioTrackType(str, Enum):
    """Categorized audio track groups."""

    VOICEOVER = "voiceover"
    SFX = "sfx"
    BGM = "bgm"
    AMBIENT = "ambient"


@dataclass
class AudioClip:
    """
    Individual audio clip placed at a specific time in the timeline.

    Attributes:
      track_type: AudioTrackType categorization.
      file_path: Path to the source audio file.
      start_time_sec: Start timestamp in seconds on the master timeline.
      duration_sec: Optional playback duration. If None, uses source file length.
      offset_sec: Seek offset within the source file before playback.
      gain_db: Volume adjustment in decibels (0.0 = unity, negative = quieter, positive = louder).
      fade_in_sec: Fade in duration in seconds.
      fade_out_sec: Fade out duration in seconds.
      loop: Whether to loop this clip if duration_sec exceeds source length.
      enabled: Whether this clip is active during mixing.
      metadata: Arbitrary metadata (e.g. sfx_name, scene_id).
    """

    track_type: AudioTrackType
    file_path: Path
    start_time_sec: float
    duration_sec: Optional[float] = None
    offset_sec: float = 0.0
    gain_db: float = 0.0
    fade_in_sec: float = 0.0
    fade_out_sec: float = 0.0
    loop: bool = False
    enabled: bool = True
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not math.isfinite(self.start_time_sec) or self.start_time_sec < 0.0:
            raise ValueError(f"start_time_sec must be non-negative and finite, got {self.start_time_sec}")
        if self.duration_sec is not None:
            if not math.isfinite(self.duration_sec) or self.duration_sec <= 0.0:
                raise ValueError(f"duration_sec must be positive and finite if specified, got {self.duration_sec}")
        if not math.isfinite(self.offset_sec) or self.offset_sec < 0.0:
            raise ValueError(f"offset_sec must be non-negative and finite, got {self.offset_sec}")
        if not math.isfinite(self.gain_db):
            raise ValueError(f"gain_db must be finite, got {self.gain_db}")
        if self.fade_in_sec < 0.0 or self.fade_out_sec < 0.0:
            raise ValueError("fade_in_sec and fade_out_sec must be non-negative")
        self.file_path = Path(self.file_path)


@dataclass
class DuckingConfig:
    """
    Configuration parameters for automatic BGM volume ducking during voiceover.
    """

    attenuation_db: float = -12.0  # Decibels by which BGM is reduced during narration
    attack_sec: float = 0.20  # Duration over which BGM ramps down before narration
    release_sec: float = 0.35  # Duration over which BGM recovers after narration
    merge_gap_sec: float = 0.25  # Merge voiceover intervals closer than this to prevent pumping
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.attenuation_db > 0.0:
            raise ValueError(f"attenuation_db should typically be negative (attenuating), got {self.attenuation_db}")
        if self.attack_sec < 0.0 or self.release_sec < 0.0 or self.merge_gap_sec < 0.0:
            raise ValueError("Timing parameters for ducking must be non-negative")


@dataclass
class MixConfig:
    """
    Master audio compositing and mixing configuration.
    """

    sample_rate: int = 44100
    channels: int = 2
    sample_width: int = 2  # 16-bit PCM
    target_peak_dbfs: float = -0.5  # Soft limiter peak ceiling in dBFS
    voice_gain_db: float = 0.0  # Master voiceover gain
    sfx_gain_db: float = 0.0  # Master SFX gain
    bgm_gain_db: float = -6.0  # Master BGM baseline gain (relative to voice)
    ambient_gain_db: float = -10.0  # Master ambient baseline gain
    ducking: DuckingConfig = field(default_factory=DuckingConfig)

    def __post_init__(self) -> None:
        if self.sample_rate not in (22050, 44100, 48000):
            raise ValueError(f"Unsupported sample_rate: {self.sample_rate}")
        if self.channels not in (1, 2):
            raise ValueError(f"Unsupported channel count: {self.channels}")
        if self.sample_width not in (1, 2, 4):
            raise ValueError(f"Unsupported sample width: {self.sample_width}")


@dataclass
class AudioTimeline:
    """
    Timeline orchestrating all audio events for a single scene or entire video.
    """

    clips: list[AudioClip] = field(default_factory=list)
    total_duration_sec: float = 0.0
    name: str = "master_audio_timeline"

    def add_clip(self, clip: AudioClip) -> None:
        """Add an AudioClip and keep clips sorted chronologically."""
        self.clips.append(clip)
        self.clips.sort(key=lambda c: c.start_time_sec)
        clip_end = clip.start_time_sec + (clip.duration_sec or 0.0)
        if clip_end > self.total_duration_sec:
            self.total_duration_sec = clip_end

    def get_clips_by_type(self, track_type: AudioTrackType) -> list[AudioClip]:
        """Return all active clips matching the specified track type."""
        return [c for c in self.clips if c.track_type == track_type and c.enabled]

    def get_voiceover_intervals(self) -> list[tuple[float, float]]:
        """
        Extract active (start_sec, end_sec) intervals for all voiceover clips,
        merging overlapping or closely adjacent intervals.
        """
        raw_intervals: list[tuple[float, float]] = []
        for c in self.get_clips_by_type(AudioTrackType.VOICEOVER):
            if c.duration_sec is not None and c.duration_sec > 0:
                raw_intervals.append((c.start_time_sec, c.start_time_sec + c.duration_sec))

        if not raw_intervals:
            return []

        raw_intervals.sort(key=lambda x: x[0])
        merged: list[tuple[float, float]] = [raw_intervals[0]]

        for start, end in raw_intervals[1:]:
            prev_start, prev_end = merged[-1]
            if start <= prev_end + 0.05:  # Adjacent or overlapping
                merged[-1] = (prev_start, max(prev_end, end))
            else:
                merged.append((start, end))

        return merged
