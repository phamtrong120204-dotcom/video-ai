"""
Dark Myth Stickman Auto-Studio - Stage 7: Sound Library & Asset Management.

Discovers, verifies, and catalogs production audio assets (Voice, SFX, BGM, Ambient).
Provides high-fidelity acoustic waveform synthesis for missing Dark Myth assets to ensure
100% offline autonomy, zero external cost, and deterministic audio pipeline verification.
"""

from dataclasses import asdict, dataclass
import json
import math
import os
from pathlib import Path
from typing import Optional, Union
import wave

import numpy as np

from app.core.config import get_config
from app.core.logger import get_logger

# Ensure C:\ffmpeg\bin is in PATH for pydub
_ffmpeg_bin_dir = r"C:\ffmpeg\bin"
if Path(_ffmpeg_bin_dir).is_dir() and _ffmpeg_bin_dir.lower() not in os.environ.get("PATH", "").lower():
    os.environ["PATH"] = f"{_ffmpeg_bin_dir};{os.environ.get('PATH', '')}"

from pydub import AudioSegment

logger = get_logger("sound_library")


@dataclass
class SoundAsset:
    """Metadata describing a single indexed sound asset."""

    name: str
    category: str  # "sfx", "bgm", "voice", "ambient"
    file_path: str
    duration_sec: float
    sample_rate: int
    channels: int
    format: str
    is_procedural: bool = False
    description: str = ""


class SoundLibrary:
    """
    Catalog and loader for audio assets.
    """

    DEFAULT_SFX_NAMES = [
        "whoosh_heavy",
        "metal_weapon_clash",
        "paper_shockwave",
        "staff_whoosh_fast",
        "multi_clash_rapid",
        "vortex_spin_whoosh",
        "body_impact_sweep",
        "sky_leap_whoosh",
        "earth_shatter_slam",
        "divine_beam_charge",
        "laser_clash_sizzle",
        "heavenly_thunder_rumble",
        "giant_palm_boom",
        "heavy_body_hit",
        "weapon_ground_scrape",
        "dark_aura_hum",
        "wind_howl",
    ]

    DEFAULT_BGM_THEMES = [
        "dark_myth_orchestral",
        "battle_tension_percussion",
    ]

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        cfg = get_config()
        self.root_dir = Path(root_dir) if root_dir else cfg.assets_dir / "audio"
        self.sfx_dir = self.root_dir / "sfx"
        self.bgm_dir = self.root_dir / "bgm"
        self.voice_dir = self.root_dir / "voice"
        self.ambient_dir = self.root_dir / "ambient"

        # Create asset directory structure
        for d in (self.sfx_dir, self.bgm_dir, self.voice_dir, self.ambient_dir):
            d.mkdir(parents=True, exist_ok=True)

        self._catalog: dict[str, SoundAsset] = {}
        self.refresh_catalog()

    def refresh_catalog(self) -> None:
        """Scan asset directories and index all recognized audio files."""
        self._catalog.clear()
        extensions = (".wav", ".mp3", ".ogg", ".flac", ".aac")

        for cat, directory in [
            ("sfx", self.sfx_dir),
            ("bgm", self.bgm_dir),
            ("voice", self.voice_dir),
            ("ambient", self.ambient_dir),
        ]:
            if not directory.exists():
                continue
            for item in directory.glob("*.*"):
                if item.suffix.lower() in extensions:
                    try:
                        seg = AudioSegment.from_file(item)
                        key = f"{cat}:{item.stem}"
                        self._catalog[key] = SoundAsset(
                            name=item.stem,
                            category=cat,
                            file_path=str(item.resolve()),
                            duration_sec=round(len(seg) / 1000.0, 3),
                            sample_rate=seg.frame_rate,
                            channels=seg.channels,
                            format=item.suffix.lstrip(".").lower(),
                            is_procedural=False,
                            description=f"Audio asset for {item.stem}",
                        )
                    except Exception as exc:
                        logger.warning(f"Could not load audio metadata for {item}: {exc}")

    def get_asset(self, category: str, name: str, auto_generate: bool = True) -> SoundAsset:
        """
        Retrieve a sound asset by category and name.
        If missing and auto_generate=True, synthesizes a procedural fallback asset.
        """
        key = f"{category}:{name}"
        if key in self._catalog:
            return self._catalog[key]

        # Check directly on disk in case file was recently added
        target_dir = getattr(self, f"{category}_dir", self.sfx_dir)
        for ext in (".wav", ".mp3", ".ogg"):
            candidate = target_dir / f"{name}{ext}"
            if candidate.is_file():
                self.refresh_catalog()
                if key in self._catalog:
                    return self._catalog[key]

        if not auto_generate:
            raise FileNotFoundError(f"Sound asset '{name}' in category '{category}' not found in {target_dir}")

        # Synthesize fallback asset
        asset = self._synthesize_asset(category, name)
        self._catalog[key] = asset
        return asset

    def get_sfx(self, name: str) -> SoundAsset:
        """Convenience method to retrieve an SFX asset."""
        return self.get_asset("sfx", name)

    def get_sfx_path(self, name: str) -> Path:
        """Return the absolute Path to an SFX file."""
        return Path(self.get_sfx(name).file_path)

    def get_bgm(self, theme: str) -> SoundAsset:
        """Convenience method to retrieve a BGM asset."""
        return self.get_asset("bgm", theme)

    def get_bgm_path(self, theme: str) -> Path:
        """Return the absolute Path to a BGM file."""
        return Path(self.get_bgm(theme).file_path)

    def list_assets(self, category: Optional[str] = None) -> list[SoundAsset]:
        """List all indexed sound assets, optionally filtered by category."""
        if category:
            return [a for a in self._catalog.values() if a.category == category]
        return list(self._catalog.values())

    def export_manifest(self, output_path: Optional[Path] = None) -> Path:
        """Export a JSON manifest of all available audio assets."""
        out = output_path or self.root_dir / "sound_assets_manifest.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "root_dir": str(self.root_dir),
            "asset_count": len(self._catalog),
            "assets": [asdict(a) for a in self._catalog.values()],
        }
        out.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return out

    def ensure_default_assets(self) -> None:
        """Ensure all 17 default Dark Myth SFX and 2 BGM themes exist."""
        for sfx_name in self.DEFAULT_SFX_NAMES:
            self.get_sfx(sfx_name)
        for bgm_theme in self.DEFAULT_BGM_THEMES:
            self.get_bgm(bgm_theme)
        self.export_manifest()

    # -------------------------------------------------------------------------
    # Procedural Audio Synthesis Engine
    # -------------------------------------------------------------------------
    def _synthesize_asset(self, category: str, name: str) -> SoundAsset:
        """Generate high-quality acoustic waveform for missing asset."""
        sr = 44100
        target_dir = getattr(self, f"{category}_dir", self.sfx_dir)
        target_path = target_dir / f"{name}.wav"

        if category == "bgm":
            stereo_pcm, duration_sec = self._generate_bgm_waveform(name, sr)
        else:
            stereo_pcm, duration_sec = self._generate_sfx_waveform(name, sr)

        # Write 16-bit stereo WAV file
        with wave.open(str(target_path), "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(stereo_pcm.tobytes())

        asset = SoundAsset(
            name=name,
            category=category,
            file_path=str(target_path.resolve()),
            duration_sec=duration_sec,
            sample_rate=sr,
            channels=2,
            format="wav",
            is_procedural=True,
            description=f"Procedurally synthesized {category} asset for {name}",
        )
        return asset

    def _generate_sfx_waveform(self, name: str, sr: int) -> tuple[np.ndarray, float]:
        """Synthesize specialized Dark Myth action sound effects."""
        np.random.seed(abs(hash(name)) % (2**31))

        if "whoosh" in name or "spin" in name:
            dur = 0.55 if "fast" in name else 0.85
            t = np.linspace(0, dur, int(sr * dur), endpoint=False)
            f0, f1 = (350, 950) if "fast" in name else (120, 550)
            freq = np.linspace(f0, f1, len(t))
            phase = 2 * np.pi * np.cumsum(freq) / sr
            env = np.sin(np.pi * t / dur) ** 2.2
            noise = (np.random.rand(len(t)) * 2 - 1) * env * 0.4
            sig = np.sin(phase) * env * 0.7 + noise
        elif "clash" in name or "metal" in name:
            dur = 0.70
            t = np.linspace(0, dur, int(sr * dur), endpoint=False)
            # Metallic inharmonic ringing sines + fast decaying impact noise
            ring = (
                np.sin(2 * np.pi * 1250 * t) * np.exp(-12 * t)
                + np.sin(2 * np.pi * 2480 * t) * np.exp(-18 * t)
                + np.sin(2 * np.pi * 3820 * t) * np.exp(-24 * t)
            )
            noise = (np.random.rand(len(t)) * 2 - 1) * np.exp(-40 * t) * 0.8
            sig = ring * 0.6 + noise * 0.4
        elif "shockwave" in name or "boom" in name or "slam" in name:
            dur = 1.20
            t = np.linspace(0, dur, int(sr * dur), endpoint=False)
            # Low sub-bass drop (80Hz down to 25Hz) + initial crack transient
            freq = 80.0 * np.exp(-3.5 * t) + 25.0
            phase = 2 * np.pi * np.cumsum(freq) / sr
            bass = np.sin(phase) * np.exp(-2.5 * t)
            transient = (np.random.rand(len(t)) * 2 - 1) * np.exp(-30 * t) * 0.7
            sig = bass * 0.8 + transient * 0.3
        elif "thunder" in name or "rumble" in name:
            dur = 1.80
            t = np.linspace(0, dur, int(sr * dur), endpoint=False)
            # Low rumble modulated noise
            low_mod = 0.5 + 0.5 * np.sin(2 * np.pi * 4.0 * t)
            noise = (np.random.rand(len(t)) * 2 - 1) * low_mod * np.exp(-1.5 * t)
            bass = np.sin(2 * np.pi * 45 * t) * np.exp(-1.2 * t)
            sig = bass * 0.6 + noise * 0.5
        elif "beam" in name or "laser" in name or "charge" in name:
            dur = 0.90
            t = np.linspace(0, dur, int(sr * dur), endpoint=False)
            # Rising harmonic energy whine
            freq = 400 + 1200 * (t / dur) ** 1.8
            phase = 2 * np.pi * np.cumsum(freq) / sr
            sig = np.sin(phase) * (0.2 + 0.8 * (t / dur))
        elif "hum" in name or "wind" in name:
            dur = 2.00
            t = np.linspace(0, dur, int(sr * dur), endpoint=False)
            drone = np.sin(2 * np.pi * 65 * t) + 0.4 * np.sin(2 * np.pi * 130 * t)
            wind = (np.random.rand(len(t)) * 2 - 1) * (0.3 + 0.2 * np.sin(2 * np.pi * 0.8 * t))
            sig = drone * 0.5 + wind * 0.4
        elif "scrape" in name or "hit" in name:
            dur = 0.65
            t = np.linspace(0, dur, int(sr * dur), endpoint=False)
            noise = (np.random.rand(len(t)) * 2 - 1) * np.exp(-8 * t)
            thud = np.sin(2 * np.pi * 110 * t) * np.exp(-15 * t)
            sig = thud * 0.6 + noise * 0.5
        else:
            # Generic impact
            dur = 0.50
            t = np.linspace(0, dur, int(sr * dur), endpoint=False)
            sig = np.sin(2 * np.pi * 220 * t) * np.exp(-10 * t)

        # Normalize and construct stereo
        peak = np.max(np.abs(sig))
        if peak > 1e-4:
            sig = (sig / peak) * 0.85
        pcm = (sig * 32767).astype(np.int16)
        stereo_pcm = np.column_stack([pcm, pcm]).flatten()
        return stereo_pcm, round(dur, 3)

    def _generate_bgm_waveform(self, theme: str, sr: int) -> tuple[np.ndarray, float]:
        """Synthesize an authentic Dark Myth orchestral background music track."""
        dur = 8.0  # 8-second seamless looping music track
        t = np.linspace(0, dur, int(sr * dur), endpoint=False)
        bpm = 110.0
        beat_interval = 60.0 / bpm

        # 1. War drum rhythmic pulse (Taiko style percussion)
        drums = np.zeros_like(t)
        for beat_idx in range(int(dur / beat_interval)):
            beat_time = beat_idx * beat_interval
            t_rel = t - beat_time
            mask = (t_rel >= 0.0) & (t_rel < 0.35)
            t_hit = t_rel[mask]
            # Low drum thud
            drum_thud = np.sin(2 * np.pi * 55.0 * t_hit) * np.exp(-14.0 * t_hit)
            drums[mask] += drum_thud

        # 2. Oriental pentatonic/modal minor string chord progression (D minor, F, G minor, A)
        chords = [
            (146.83, 220.00, 261.63),  # D3, A3, C4
            (174.61, 261.63, 329.63),  # F3, C4, E4
            (196.00, 293.66, 349.23),  # G3, D4, F4
            (220.00, 329.63, 440.00),  # A3, E4, A4
        ]
        harmony = np.zeros_like(t)
        chord_dur = dur / len(chords)
        for i, (f1, f2, f3) in enumerate(chords):
            t_start = i * chord_dur
            t_end = (i + 1) * chord_dur
            mask = (t >= t_start) & (t < t_end)
            t_sub = t[mask] - t_start
            # Tremolo string synth with vibrato
            vibrato = 1.0 + 0.015 * np.sin(2 * np.pi * 5.0 * t_sub)
            voice1 = np.sin(2 * np.pi * f1 * vibrato * t_sub)
            voice2 = np.sin(2 * np.pi * f2 * vibrato * t_sub)
            voice3 = np.sin(2 * np.pi * f3 * vibrato * t_sub)
            # Smooth envelope per chord
            chord_env = np.sin(np.pi * (t_sub / chord_dur)) ** 0.8
            harmony[mask] = (voice1 * 0.4 + voice2 * 0.35 + voice3 * 0.3) * chord_env

        # 3. Combine and normalize
        full_mix = harmony * 0.65 + drums * 0.45
        peak = np.max(np.abs(full_mix))
        if peak > 1e-4:
            full_mix = (full_mix / peak) * 0.80

        pcm = (full_mix * 32767).astype(np.int16)
        stereo_pcm = np.column_stack([pcm, pcm]).flatten()
        return stereo_pcm, round(dur, 3)
