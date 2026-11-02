"""
Dark Myth Stickman Auto-Studio - Stage 7: Preview Audio Integration Script.

Renders a complete, production-grade Dark Myth video with synchronized Vietnamese
narration voiceover (Edge-TTS), combat sound effects (SFX), background music (BGM),
continuous audio ducking, stem exports, and FFprobe verification.
"""

import json
import math
from pathlib import Path
import subprocess
import sys
import time

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_config
from app.modules.animation.animation_loop import (
    AnimationLoopEngine,
    AnimationTrack,
    Keyframe,
)
from app.modules.animation.background_renderer import NotebookBackgroundRenderer
from app.modules.animation.interpolation_engine import EasingFunction
from app.modules.animation.stickman_models import StickmanCharacter
from app.modules.audio.audio_compositor import AudioCompositor
from app.modules.audio.audio_models import AudioClip, AudioTimeline, AudioTrackType, DuckingConfig, MixConfig
from app.modules.audio.edge_tts_engine import EdgeTTSAudioEngine
from app.modules.audio.sfx_timeline_mapper import SfxTimelineMapper
from app.modules.audio.sound_library import SoundLibrary
from app.modules.audio.video_audio_integrator import VideoAudioIntegrator
from app.schemas.scene_schema import (
    ActionPreset,
    ActorConfig,
    ActorSide,
    BackgroundState,
    CameraMovement,
    CharacterSkin,
    SceneSchema,
    SfxEvent,
    WeaponType,
)


def main():
    print("=" * 70)
    print("STAGE 7: FULL AUDIO INTEGRATION DEMO PRODUCTION")
    print("=" * 70)

    out_dir = Path("out/preview/audio_integration")
    out_dir.mkdir(parents=True, exist_ok=True)
    stems_dir = out_dir / "stems"
    stems_dir.mkdir(parents=True, exist_ok=True)

    # 1. Initialize Engines
    print("\n[1/6] Initializing Audio & Animation Engines...")
    sound_lib = SoundLibrary()
    sound_lib.ensure_default_assets()

    tts_engine = EdgeTTSAudioEngine(voice_id="vi-VN-NamMinhNeural", voice_speed=1.05)
    bg_renderer = NotebookBackgroundRenderer()
    bg_image = bg_renderer.render_background(state="ink_splattered", seed=777)

    animation_engine = AnimationLoopEngine()
    audio_compositor = AudioCompositor(
        mix_config=MixConfig(
            sample_rate=44100,
            channels=2,
            target_peak_dbfs=-0.5,
            bgm_gain_db=-7.0,
            sfx_gain_db=0.0,
            voice_gain_db=1.0,
            ducking=DuckingConfig(attenuation_db=-12.0, attack_sec=0.20, release_sec=0.35),
        )
    )
    sfx_mapper = SfxTimelineMapper(sound_library=sound_lib)
    integrator = VideoAudioIntegrator(
        audio_compositor=audio_compositor,
        sfx_mapper=sfx_mapper,
        animation_engine=animation_engine,
    )

    # 2. Build Scene & Vietnamese Voiceover
    print("\n[2/6] Generating Vietnamese Voiceover Narration...")
    narration_text = "Tôn Ngộ Không hắc hóa vung Thiết Bảng Như Ý, giáng đòn sấm sét chấn động tam giới!"
    scene = SceneSchema(
        scene_id=1,
        narration_text=narration_text,
        audio_duration_sec=4.0,  # target duration
        background_state=BackgroundState.INK_SPLATTERED,
        actors=[
            ActorConfig(
                actor_id="wukong_hero",
                display_name="Ngộ Không Hắc Hóa",
                side=ActorSide.LEFT,
                skin=CharacterSkin.DARK_WUKONG,
                weapon=WeaponType.RUYI_STAFF,
                scale=1.0,
            )
        ],
        action_preset=ActionPreset.HEAVY_CHARGE_CLASH,
        camera_movement=CameraMovement.ZOOM_PUNCH_IMPACT,
        sfx_events=[
            SfxEvent(sfx_name="whoosh_heavy", time_offset=0.6, volume=0.85),
            SfxEvent(sfx_name="metal_weapon_clash", time_offset=1.4, volume=1.0),
            SfxEvent(sfx_name="paper_shockwave", time_offset=1.45, volume=0.9),
            SfxEvent(sfx_name="earth_shatter_slam", time_offset=2.1, volume=0.95),
            SfxEvent(sfx_name="vortex_spin_whoosh", time_offset=2.8, volume=0.8),
            SfxEvent(sfx_name="body_impact_sweep", time_offset=3.4, volume=0.85),
        ],
    )

    voice_path = None
    voice_dur = 4.0
    try:
        v_path, v_dur = tts_engine.generate_scene_audio(scene, out_dir / "temp_audio")
        voice_path = v_path
        voice_dur = v_dur
        print(f"  Edge-TTS voice generated: {voice_path} (duration: {voice_dur:.2f}s)")
    except Exception as exc:
        print(f"  Edge-TTS online failed ({exc}), using synthesized voice track for demo...")
        voice_path = sound_lib.get_sfx_path("dark_aura_hum")
        voice_dur = 4.0

    target_total_sec = max(4.0, voice_dur)
    scene.audio_duration_sec = target_total_sec
    scene.voice_audio_path = str(voice_path)

    # 3. Build Animation Track (G6)
    print("\n[3/6] Generating G6 Combat Animation Frames (1080x1920 @ 30 FPS)...")
    anim_track = AnimationTrack(
        keyframes=[
            Keyframe(time_sec=0.0, pose_name="standoff_idle", easing=EasingFunction.EASE_IN_OUT),
            Keyframe(time_sec=0.7, pose_name="combat_stance", easing=EasingFunction.EASE_IN),
            Keyframe(time_sec=1.4, pose_name="overhead_slam", easing=EasingFunction.EASE_OUT),
            Keyframe(time_sec=2.1, pose_name="forward_charge", easing=EasingFunction.EASE_IN_OUT),
            Keyframe(time_sec=2.8, pose_name="vortex_sweep", easing=EasingFunction.EASE_IN_OUT),
            Keyframe(time_sec=3.4, pose_name="guard_block", easing=EasingFunction.EASE_OUT),
            Keyframe(time_sec=target_total_sec, pose_name="standoff_idle", easing=EasingFunction.EASE_IN_OUT),
        ],
        duration_sec=target_total_sec,
        loop=False,
    )
    char = StickmanCharacter.from_actor_config(scene.actors[0])
    raw_video_path = out_dir / "dark_myth_video_only.mp4"
    frames = animation_engine.generate_clip_frames(
        track=anim_track,
        character=char,
        fps=30,
        background_image=bg_image,
    )
    animation_engine.export_mp4_video(frames, raw_video_path, fps=30)
    print(f"  Raw video rendered: {raw_video_path} ({len(frames)} frames)")

    # 4. Build Master Audio Timeline & Mix Stems (G7)
    print("\n[4/6] Compositing Audio Stems & Applying Sample-Accurate Ducking...")
    audio_timeline = sfx_mapper.build_scene_timeline(scene=scene, include_preset_sfx=False)

    # Add continuous BGM
    bgm_asset = sound_lib.get_bgm("dark_myth_orchestral")
    audio_timeline.add_clip(
        AudioClip(
            track_type=AudioTrackType.BGM,
            file_path=Path(bgm_asset.file_path),
            start_time_sec=0.0,
            duration_sec=target_total_sec,
            loop=True,
            fade_in_sec=0.5,
            fade_out_sec=0.8,
            metadata={"theme": "dark_myth_orchestral"},
        )
    )

    # Export stems
    stems = audio_compositor.export_stems(
        timeline=audio_timeline,
        output_dir=stems_dir,
        target_duration_sec=target_total_sec,
    )
    for stem_name, stem_file in stems.items():
        print(f"  Stem exported: {stem_name} -> {stem_file.name} ({stem_file.stat().st_size / 1024:.1f} KB)")

    master_audio_path = stems_dir / "master_mixed.wav"

    # 5. Multiplex into Final MP4
    print("\n[5/6] Muxing Video and Master Audio via FFmpeg...")
    final_mp4_path = out_dir / "dark_myth_combat_demo.mp4"
    integrator.mux_video_and_audio(
        video_path=raw_video_path,
        audio_path=master_audio_path,
        output_mp4_path=final_mp4_path,
    )
    print(f"  Final MP4 Created: {final_mp4_path} ({final_mp4_path.stat().st_size / 1024:.1f} KB)")

    # 6. Verify with FFprobe
    print("\n[6/6] Verifying Final MP4 Streams with FFprobe...")
    probe_data = integrator.probe_media(final_mp4_path)
    streams = probe_data.get("streams", [])
    v_stream = next(s for s in streams if s.get("codec_type") == "video")
    a_stream = next(s for s in streams if s.get("codec_type") == "audio")
    fmt = probe_data.get("format", {})

    print(f"  Video Stream: {v_stream.get('width')}x{v_stream.get('height')} @ {v_stream.get('r_frame_rate')} fps, codec={v_stream.get('codec_name')}, pix_fmt={v_stream.get('pix_fmt')}")
    print(f"  Audio Stream: {a_stream.get('sample_rate')} Hz, {a_stream.get('channels')} channels, codec={a_stream.get('codec_name')}, bitrate={int(a_stream.get('bit_rate', 192000)) // 1000} kbps")
    print(f"  Container Duration: {float(fmt.get('duration', 0.0)):.3f}s, Size: {int(fmt.get('size', 0)) / 1024:.1f} KB")

    manifest = {
        "stage": "G7 - SFX & Audio Integration Engine",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "narration_text": narration_text,
        "voice_file": str(voice_path),
        "target_duration_sec": target_total_sec,
        "artifacts": {
            "final_mp4": str(final_mp4_path),
            "video_only": str(raw_video_path),
            "master_audio": str(master_audio_path),
            "stems": {k: str(v) for k, v in stems.items()},
        },
        "ffprobe_summary": {
            "video_codec": v_stream.get("codec_name"),
            "width": v_stream.get("width"),
            "height": v_stream.get("height"),
            "fps": v_stream.get("r_frame_rate"),
            "audio_codec": a_stream.get("codec_name"),
            "sample_rate": a_stream.get("sample_rate"),
            "channels": a_stream.get("channels"),
            "duration_sec": fmt.get("duration"),
            "file_size_bytes": fmt.get("size"),
        },
    }

    manifest_path = out_dir / "audio_integration_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nManifest saved to: {manifest_path}")
    print("\nDEMO PRODUCTION COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
