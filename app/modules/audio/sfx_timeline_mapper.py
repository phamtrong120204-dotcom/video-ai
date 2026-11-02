"""
Dark Myth Stickman Auto-Studio - Stage 7: SFX Timeline Mapper.

Maps Dark Myth combat action presets, explicit scene SFX events, narration voiceover,
and background music onto a master AudioTimeline.
"""

from pathlib import Path
from typing import Optional, Union

from app.core.logger import get_logger
from app.modules.audio.audio_models import AudioClip, AudioTimeline, AudioTrackType
from app.modules.audio.sound_library import SoundLibrary
from app.schemas.scene_schema import ActionPreset, SceneSchema, SfxEvent

logger = get_logger("sfx_timeline_mapper")


# Mapping of ActionPresets to automatic Dark Myth SFX cues (relative progress u in [0.0, 1.0])
ACTION_PRESET_SFX_MAP: dict[str, list[tuple[float, str, float]]] = {
    # (relative_progress_u, sfx_name, volume)
    "dark_aura_standoff": [
        (0.15, "dark_aura_hum", 0.70),
        (0.50, "wind_howl", 0.65),
    ],
    "heavy_charge_clash": [
        (0.25, "whoosh_heavy", 0.80),
        (0.45, "metal_weapon_clash", 1.00),
        (0.47, "paper_shockwave", 0.85),
    ],
    "flurry_combo": [
        (0.20, "staff_whoosh_fast", 0.75),
        (0.40, "multi_clash_rapid", 0.90),
        (0.65, "multi_clash_rapid", 0.90),
    ],
    "staff_vortex_sweep": [
        (0.30, "vortex_spin_whoosh", 0.85),
        (0.70, "body_impact_sweep", 0.90),
    ],
    "sky_leap_slam": [
        (0.20, "sky_leap_whoosh", 0.80),
        (0.60, "earth_shatter_slam", 1.00),
    ],
    "divine_eye_beam": [
        (0.20, "divine_beam_charge", 0.75),
        (0.40, "laser_clash_sizzle", 0.95),
    ],
    "giant_palm_suppression": [
        (0.20, "heavenly_thunder_rumble", 0.80),
        (0.55, "giant_palm_boom", 1.00),
    ],
    "knockback_recovery": [
        (0.20, "heavy_body_hit", 0.85),
        (0.65, "weapon_ground_scrape", 0.80),
    ],
}


class SfxTimelineMapper:
    """
    Translates scene schemas and action presets into concrete AudioClips placed on an AudioTimeline.
    """

    def __init__(self, sound_library: Optional[SoundLibrary] = None) -> None:
        self.sound_library = sound_library or SoundLibrary()

    def map_action_preset_sfx(
        self,
        action_preset: Union[ActionPreset, str],
        scene_start_sec: float,
        scene_duration_sec: float,
    ) -> list[AudioClip]:
        """
        Generate default SFX clips corresponding to an ActionPreset based on dark_myth_moveset_spec.md.
        """
        preset_key = action_preset.value if isinstance(action_preset, ActionPreset) else str(action_preset)
        cues = ACTION_PRESET_SFX_MAP.get(preset_key, [])
        clips: list[AudioClip] = []

        for u, sfx_name, vol in cues:
            try:
                asset = self.sound_library.get_sfx(sfx_name)
                start_t = scene_start_sec + (u * scene_duration_sec)
                gain_db = 20.0 * (vol - 1.0) if vol < 1.0 else 0.0  # approximate dB reduction
                clips.append(
                    AudioClip(
                        track_type=AudioTrackType.SFX,
                        file_path=Path(asset.file_path),
                        start_time_sec=round(start_t, 3),
                        duration_sec=asset.duration_sec,
                        gain_db=round(gain_db, 2),
                        metadata={"sfx_name": sfx_name, "preset": preset_key, "source": "action_preset"},
                    )
                )
            except Exception as exc:
                logger.warning(f"Could not map preset SFX '{sfx_name}': {exc}")

        return clips

    def map_scene_sfx_events(
        self,
        scene: SceneSchema,
        scene_start_sec: float,
    ) -> list[AudioClip]:
        """
        Map explicit SFXEvents defined in SceneSchema into AudioClips.
        """
        clips: list[AudioClip] = []
        for event in scene.sfx_events:
            sfx_name = event.sfx_name
            offset = event.time_offset
            vol = event.volume
            try:
                asset = self.sound_library.get_sfx(sfx_name)
                start_t = scene_start_sec + offset
                gain_db = 20.0 * (vol - 1.0) if vol < 1.0 else 0.0
                clips.append(
                    AudioClip(
                        track_type=AudioTrackType.SFX,
                        file_path=Path(asset.file_path),
                        start_time_sec=round(start_t, 3),
                        duration_sec=asset.duration_sec,
                        gain_db=round(gain_db, 2),
                        metadata={"sfx_name": sfx_name, "scene_id": scene.scene_id, "source": "scene_sfx_event"},
                    )
                )
            except Exception as exc:
                logger.warning(f"Could not map scene SFX event '{sfx_name}': {exc}")

        return clips

    def build_scene_timeline(
        self,
        scene: SceneSchema,
        scene_start_sec: float = 0.0,
        include_preset_sfx: bool = True,
    ) -> AudioTimeline:
        """
        Build an AudioTimeline for a single scene containing narration and all SFX.
        """
        timeline = AudioTimeline(name=f"scene_{scene.scene_id}_timeline")

        # 1. Voiceover clip
        if scene.voice_audio_path and Path(scene.voice_audio_path).is_file():
            timeline.add_clip(
                AudioClip(
                    track_type=AudioTrackType.VOICEOVER,
                    file_path=Path(scene.voice_audio_path),
                    start_time_sec=scene_start_sec,
                    duration_sec=scene.audio_duration_sec,
                    metadata={"scene_id": scene.scene_id, "text": scene.narration_text},
                )
            )

        # 2. Explicit scene SFX events
        for clip in self.map_scene_sfx_events(scene, scene_start_sec):
            timeline.add_clip(clip)

        # 3. Action Preset SFX (if enabled and no explicit events override)
        if include_preset_sfx:
            for clip in self.map_action_preset_sfx(scene.action_preset, scene_start_sec, scene.audio_duration_sec):
                timeline.add_clip(clip)

        return timeline

    def build_full_timeline(
        self,
        scenes: list[SceneSchema],
        bgm_theme: Optional[str] = "dark_myth_orchestral",
        include_preset_sfx: bool = True,
    ) -> AudioTimeline:
        """
        Build a master AudioTimeline for an entire multi-scene video sequence,
        incorporating voiceover, action SFX, and continuous BGM.
        """
        timeline = AudioTimeline(name="master_video_timeline")
        current_time_sec = 0.0

        for scene in scenes:
            scene_tl = self.build_scene_timeline(
                scene=scene,
                scene_start_sec=current_time_sec,
                include_preset_sfx=include_preset_sfx,
            )
            for clip in scene_tl.clips:
                timeline.add_clip(clip)
            current_time_sec += scene.audio_duration_sec

        timeline.total_duration_sec = current_time_sec

        # Add Background Music (BGM) spanning the full video duration
        if bgm_theme:
            try:
                bgm_asset = self.sound_library.get_bgm(bgm_theme)
                timeline.add_clip(
                    AudioClip(
                        track_type=AudioTrackType.BGM,
                        file_path=Path(bgm_asset.file_path),
                        start_time_sec=0.0,
                        duration_sec=timeline.total_duration_sec,
                        loop=True,
                        fade_in_sec=0.8,
                        fade_out_sec=1.2,
                        metadata={"bgm_theme": bgm_theme},
                    )
                )
            except Exception as exc:
                logger.warning(f"Could not add BGM theme '{bgm_theme}': {exc}")

        return timeline
