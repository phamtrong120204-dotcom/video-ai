"""
Dark Myth Stickman Auto-Studio - Stage 7: Audio Compositor & Mixer.

Implements high-fidelity multi-track audio compositing, sample-accurate BGM ducking,
soft peak limiting to prevent clipping, stem isolation, and synchronized audio export.
"""

import math
import os
from pathlib import Path
from typing import Optional, Union

import numpy as np

# Ensure C:\ffmpeg\bin is in PATH for pydub
_ffmpeg_bin_dir = r"C:\ffmpeg\bin"
if Path(_ffmpeg_bin_dir).is_dir() and _ffmpeg_bin_dir.lower() not in os.environ.get("PATH", "").lower():
    os.environ["PATH"] = f"{_ffmpeg_bin_dir};{os.environ.get('PATH', '')}"

from pydub import AudioSegment

from app.core.logger import get_logger
from app.modules.audio.audio_models import (
    AudioClip,
    AudioTimeline,
    AudioTrackType,
    DuckingConfig,
    MixConfig,
)

logger = get_logger("audio_compositor")


class AudioCompositor:
    """
    Orchestrates multi-stem audio compositing, ducking, and export.
    """

    def __init__(self, mix_config: Optional[MixConfig] = None) -> None:
        self.config = mix_config or MixConfig()

    def _normalize_clip_audio(self, clip: AudioClip) -> AudioSegment:
        """Load and normalize source audio clip to project master audio specifications."""
        if not clip.file_path.is_file():
            raise FileNotFoundError(f"Source audio file not found: {clip.file_path}")

        seg = AudioSegment.from_file(clip.file_path)
        seg = seg.set_frame_rate(self.config.sample_rate)
        seg = seg.set_channels(self.config.channels)
        seg = seg.set_sample_width(self.config.sample_width)

        # Seek offset
        if clip.offset_sec > 0.0:
            offset_ms = int(clip.offset_sec * 1000)
            seg = seg[offset_ms:] if len(seg) > offset_ms else AudioSegment.silent(duration=10)

        # Duration & Loop
        if clip.duration_sec is not None:
            target_ms = int(clip.duration_sec * 1000)
            if clip.loop and len(seg) > 0 and len(seg) < target_ms:
                # Loop until target duration
                loops_needed = math.ceil(target_ms / len(seg))
                seg = (seg * loops_needed)[:target_ms]
            else:
                seg = seg[:target_ms]

        # Gain adjustment
        if clip.gain_db != 0.0:
            seg = seg.apply_gain(clip.gain_db)

        # Fades
        if clip.fade_in_sec > 0.0:
            fade_in_ms = min(len(seg), int(clip.fade_in_sec * 1000))
            seg = seg.fade_in(fade_in_ms)
        if clip.fade_out_sec > 0.0:
            fade_out_ms = min(len(seg), int(clip.fade_out_sec * 1000))
            seg = seg.fade_out(fade_out_ms)

        return seg

    def apply_audio_ducking(
        self,
        bgm_segment: AudioSegment,
        voice_intervals: list[tuple[float, float]],
        ducking_config: Optional[DuckingConfig] = None,
    ) -> AudioSegment:
        """
        Apply sample-accurate continuous gain envelope ducking to the BGM track.

        During speech intervals, attenuates BGM volume smoothly by ducking_config.attenuation_db.
        """
        cfg = ducking_config or self.config.ducking
        if not cfg.enabled or not voice_intervals or len(bgm_segment) == 0:
            return bgm_segment

        sr = bgm_segment.frame_rate
        total_samples = int(len(bgm_segment) * sr / 1000.0)
        gain_env = np.ones(total_samples, dtype=np.float32)

        att_factor = 10.0 ** (cfg.attenuation_db / 20.0)
        att_sec = cfg.attack_sec
        rel_sec = cfg.release_sec

        # Merge closely adjacent intervals
        sorted_intervals = sorted(voice_intervals, key=lambda x: x[0])
        merged: list[tuple[float, float]] = [sorted_intervals[0]]
        for start, end in sorted_intervals[1:]:
            prev_s, prev_e = merged[-1]
            if start <= prev_e + cfg.merge_gap_sec:
                merged[-1] = (prev_s, max(prev_e, end))
            else:
                merged.append((start, end))

        # Generate smooth continuous ducking envelope
        for v_start, v_end in merged:
            # 1. Attack ramp down: [v_start - att_sec, v_start]
            i_att_start = max(0, int((v_start - att_sec) * sr))
            i_att_end = max(0, min(total_samples, int(v_start * sr)))
            if i_att_end > i_att_start:
                ramp_down = np.linspace(1.0, att_factor, i_att_end - i_att_start)
                gain_env[i_att_start:i_att_end] = np.minimum(gain_env[i_att_start:i_att_end], ramp_down)

            # 2. Hold ducked volume: [v_start, v_end]
            i_hold_start = i_att_end
            i_hold_end = max(0, min(total_samples, int(v_end * sr)))
            if i_hold_end > i_hold_start:
                gain_env[i_hold_start:i_hold_end] = np.minimum(gain_env[i_hold_start:i_hold_end], att_factor)

            # 3. Release ramp up: [v_end, v_end + rel_sec]
            i_rel_start = i_hold_end
            i_rel_end = max(0, min(total_samples, int((v_end + rel_sec) * sr)))
            if i_rel_end > i_rel_start:
                ramp_up = np.linspace(att_factor, 1.0, i_rel_end - i_rel_start)
                gain_env[i_rel_start:i_rel_end] = np.minimum(gain_env[i_rel_start:i_rel_end], ramp_up)

        # Apply gain envelope to raw PCM samples
        samples = np.frombuffer(bgm_segment.raw_data, dtype=np.int16).reshape(-1, bgm_segment.channels)
        n_apply = min(len(samples), len(gain_env))
        ducked_samples = (samples[:n_apply] * gain_env[:n_apply, None]).astype(np.int16)
        if n_apply < len(samples):
            ducked_samples = np.vstack([ducked_samples, samples[n_apply:]])

        return AudioSegment(
            ducked_samples.tobytes(),
            frame_rate=sr,
            sample_width=bgm_segment.sample_width,
            channels=bgm_segment.channels,
        )

    def render_stems(
        self,
        timeline: AudioTimeline,
        target_duration_sec: Optional[float] = None,
    ) -> dict[AudioTrackType, AudioSegment]:
        """
        Render isolated audio stems: VOICEOVER, SFX, BGM, and AMBIENT.
        """
        eff_duration = target_duration_sec or timeline.total_duration_sec
        if eff_duration <= 0.0:
            eff_duration = 1.0
        total_ms = int(round(eff_duration * 1000.0))

        stems: dict[AudioTrackType, AudioSegment] = {
            t: AudioSegment.silent(
                duration=total_ms,
                frame_rate=self.config.sample_rate,
            ).set_channels(self.config.channels).set_sample_width(self.config.sample_width)
            for t in AudioTrackType
        }

        # 1. Place individual clips into their respective stem
        for clip in timeline.clips:
            if not clip.enabled:
                continue
            clip_audio = self._normalize_clip_audio(clip)
            pos_ms = int(round(clip.start_time_sec * 1000.0))
            if pos_ms < total_ms:
                stems[clip.track_type] = stems[clip.track_type].overlay(clip_audio, position=pos_ms)

        # 2. Apply master track gains
        stems[AudioTrackType.VOICEOVER] = stems[AudioTrackType.VOICEOVER].apply_gain(self.config.voice_gain_db)
        stems[AudioTrackType.SFX] = stems[AudioTrackType.SFX].apply_gain(self.config.sfx_gain_db)
        stems[AudioTrackType.BGM] = stems[AudioTrackType.BGM].apply_gain(self.config.bgm_gain_db)
        stems[AudioTrackType.AMBIENT] = stems[AudioTrackType.AMBIENT].apply_gain(self.config.ambient_gain_db)

        # 3. Apply BGM ducking during voiceover
        voice_intervals = timeline.get_voiceover_intervals()
        stems[AudioTrackType.BGM] = self.apply_audio_ducking(
            stems[AudioTrackType.BGM],
            voice_intervals=voice_intervals,
            ducking_config=self.config.ducking,
        )

        # 4. Enforce strict duration on all stems
        for t in AudioTrackType:
            stem = stems[t]
            if len(stem) < total_ms:
                stem = stem + AudioSegment.silent(
                    duration=total_ms - len(stem),
                    frame_rate=self.config.sample_rate,
                ).set_channels(self.config.channels).set_sample_width(self.config.sample_width)
            else:
                stem = stem[:total_ms]
            stems[t] = stem

        return stems

    def mix_timeline(
        self,
        timeline: AudioTimeline,
        target_duration_sec: Optional[float] = None,
    ) -> AudioSegment:
        """
        Composite all stems into a single master audio mix with soft peak limiting.
        """
        stems = self.render_stems(timeline, target_duration_sec=target_duration_sec)
        eff_duration = target_duration_sec or timeline.total_duration_sec
        total_ms = int(round(eff_duration * 1000.0))

        master = AudioSegment.silent(
            duration=total_ms,
            frame_rate=self.config.sample_rate,
        ).set_channels(self.config.channels).set_sample_width(self.config.sample_width)

        # Layer stems in priority order: Ambient -> BGM -> SFX -> Voiceover
        master = master.overlay(stems[AudioTrackType.AMBIENT])
        master = master.overlay(stems[AudioTrackType.BGM])
        master = master.overlay(stems[AudioTrackType.SFX])
        master = master.overlay(stems[AudioTrackType.VOICEOVER])

        # Soft peak limiter to prevent clipping
        if master.max_dBFS > self.config.target_peak_dbfs:
            attenuation = (master.max_dBFS - self.config.target_peak_dbfs) + 0.05
            logger.info(f"Limiter active: attenuating master by {attenuation:.2f} dBFS to prevent clipping")
            master = master.apply_gain(-attenuation)

        # Final duration trim/pad
        if len(master) < total_ms:
            master = master + AudioSegment.silent(duration=total_ms - len(master), frame_rate=self.config.sample_rate)
        else:
            master = master[:total_ms]

        return master

    def export_master(
        self,
        timeline: AudioTimeline,
        output_path: Path,
        target_duration_sec: Optional[float] = None,
        format: str = "wav",
    ) -> Path:
        """Export composite master audio to disk."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        mixed = self.mix_timeline(timeline, target_duration_sec=target_duration_sec)
        mixed.export(str(output_path), format=format)
        return output_path

    def export_stems(
        self,
        timeline: AudioTimeline,
        output_dir: Path,
        target_duration_sec: Optional[float] = None,
    ) -> dict[str, Path]:
        """Export isolated stem audio files and master mix to directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        stems = self.render_stems(timeline, target_duration_sec=target_duration_sec)
        results: dict[str, Path] = {}

        for track_type, stem in stems.items():
            stem_path = output_dir / f"stem_{track_type.value}.wav"
            stem.export(str(stem_path), format="wav")
            results[track_type.value] = stem_path

        master_path = output_dir / "master_mixed.wav"
        self.export_master(timeline, master_path, target_duration_sec=target_duration_sec, format="wav")
        results["master"] = master_path

        return results
