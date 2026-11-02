"""
Dark Myth Stickman Auto-Studio - Stage 7: Comprehensive Audio Compositor & Integration Tests.

Validates Audio Models, Timeline Sequencing, SoundLibrary, SfxTimelineMapper,
Continuous Audio Ducking, Overlapping SFX, Soft Peak Limiting, Stem Isolation,
FFmpeg Muxing, and FFprobe Stream Verification.
"""

import math
from pathlib import Path
import subprocess

import pytest

from app.modules.animation.animation_loop import AnimationLoopEngine, AnimationTrack, Keyframe
from app.modules.animation.stickman_models import CoordinateManager, Point2D, StickmanCharacter
from app.modules.audio.audio_compositor import AudioCompositor
from app.modules.audio.audio_models import (
    AudioClip,
    AudioTimeline,
    AudioTrackType,
    DuckingConfig,
    MixConfig,
)
from app.modules.audio.sfx_timeline_mapper import SfxTimelineMapper
from app.modules.audio.sound_library import SoundAsset, SoundLibrary
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


# -----------------------------------------------------------------------------
# 1. AUDIO MODEL & TIMELINE TESTS
# -----------------------------------------------------------------------------

def test_audio_clip_validation(tmp_path: Path):
    """Verify input validation on AudioClip parameters."""
    dummy_file = tmp_path / "dummy.wav"
    dummy_file.write_bytes(b"RIFFdummyWAVE")

    # Valid clip
    clip = AudioClip(
        track_type=AudioTrackType.SFX,
        file_path=dummy_file,
        start_time_sec=1.5,
        duration_sec=0.5,
        gain_db=-3.0,
    )
    assert clip.start_time_sec == 1.5
    assert clip.gain_db == -3.0

    # Negative start time
    with pytest.raises(ValueError, match="start_time_sec must be non-negative"):
        AudioClip(track_type=AudioTrackType.SFX, file_path=dummy_file, start_time_sec=-0.1)

    # Non-positive duration
    with pytest.raises(ValueError, match="duration_sec must be positive"):
        AudioClip(track_type=AudioTrackType.SFX, file_path=dummy_file, start_time_sec=0.0, duration_sec=0.0)

    # Negative offset
    with pytest.raises(ValueError, match="offset_sec must be non-negative"):
        AudioClip(track_type=AudioTrackType.SFX, file_path=dummy_file, start_time_sec=0.0, offset_sec=-1.0)


def test_audio_timeline_add_and_sort(tmp_path: Path):
    """Verify timeline maintains chronological clip ordering and total duration."""
    dummy_file = tmp_path / "dummy.wav"
    dummy_file.write_bytes(b"RIFFdummyWAVE")

    tl = AudioTimeline()
    c1 = AudioClip(track_type=AudioTrackType.SFX, file_path=dummy_file, start_time_sec=2.0, duration_sec=1.0)
    c2 = AudioClip(track_type=AudioTrackType.VOICEOVER, file_path=dummy_file, start_time_sec=0.5, duration_sec=2.0)
    c3 = AudioClip(track_type=AudioTrackType.BGM, file_path=dummy_file, start_time_sec=0.0, duration_sec=5.0)

    tl.add_clip(c1)
    tl.add_clip(c2)
    tl.add_clip(c3)

    assert tl.clips[0] == c3  # start 0.0
    assert tl.clips[1] == c2  # start 0.5
    assert tl.clips[2] == c1  # start 2.0
    assert tl.total_duration_sec == 5.0

    # Test filtering by type
    assert len(tl.get_clips_by_type(AudioTrackType.SFX)) == 1
    assert len(tl.get_clips_by_type(AudioTrackType.VOICEOVER)) == 1
    assert len(tl.get_clips_by_type(AudioTrackType.BGM)) == 1


def test_voiceover_intervals_merging(tmp_path: Path):
    """Verify voiceover intervals are properly extracted and merged for ducking."""
    dummy_file = tmp_path / "dummy.wav"
    dummy_file.write_bytes(b"RIFFdummyWAVE")

    tl = AudioTimeline()
    # Interval 1: [0.5, 1.5]
    tl.add_clip(AudioClip(track_type=AudioTrackType.VOICEOVER, file_path=dummy_file, start_time_sec=0.5, duration_sec=1.0))
    # Interval 2: [1.52, 2.5] (adjacent, should merge)
    tl.add_clip(AudioClip(track_type=AudioTrackType.VOICEOVER, file_path=dummy_file, start_time_sec=1.52, duration_sec=0.98))
    # Interval 3: [4.0, 5.0] (separate)
    tl.add_clip(AudioClip(track_type=AudioTrackType.VOICEOVER, file_path=dummy_file, start_time_sec=4.0, duration_sec=1.0))

    intervals = tl.get_voiceover_intervals()
    assert len(intervals) == 2
    assert abs(intervals[0][0] - 0.5) < 1e-4
    assert abs(intervals[0][1] - 2.5) < 1e-4
    assert abs(intervals[1][0] - 4.0) < 1e-4
    assert abs(intervals[1][1] - 5.0) < 1e-4


# -----------------------------------------------------------------------------
# 2. SOUND LIBRARY & ASSET MANAGEMENT TESTS
# -----------------------------------------------------------------------------

def test_sound_library_catalog_and_synthesis(tmp_path: Path):
    """Verify SoundLibrary catalogs existing assets and synthesizes missing ones."""
    lib = SoundLibrary(root_dir=tmp_path / "audio_assets")
    assert lib.sfx_dir.exists()
    assert lib.bgm_dir.exists()

    # Get metal clash SFX (synthesized on demand)
    asset = lib.get_sfx("metal_weapon_clash")
    assert Path(asset.file_path).is_file()
    assert asset.sample_rate == 44100
    assert asset.channels == 2
    assert asset.duration_sec > 0.3
    assert asset.is_procedural is True

    # Get BGM asset
    bgm_asset = lib.get_bgm("dark_myth_orchestral")
    assert Path(bgm_asset.file_path).is_file()
    assert bgm_asset.duration_sec >= 5.0

    # Export manifest
    manifest_path = lib.export_manifest()
    assert manifest_path.is_file()


def test_sound_library_missing_asset_error(tmp_path: Path):
    """Verify missing asset with auto_generate=False raises FileNotFoundError."""
    lib = SoundLibrary(root_dir=tmp_path / "audio_assets")
    with pytest.raises(FileNotFoundError, match="not found in"):
        lib.get_asset("sfx", "non_existent_sfx_999", auto_generate=False)


# -----------------------------------------------------------------------------
# 3. SFX TIMELINE MAPPER TESTS
# -----------------------------------------------------------------------------

def test_sfx_timeline_mapper_action_presets():
    """Verify ActionPresets map to corresponding SFX clips with accurate relative timing."""
    mapper = SfxTimelineMapper()

    # Map heavy_charge_clash (duration = 4.0s)
    clips = mapper.map_action_preset_sfx("heavy_charge_clash", scene_start_sec=10.0, scene_duration_sec=4.0)
    assert len(clips) >= 3
    sfx_names = [c.metadata.get("sfx_name") for c in clips]
    assert "whoosh_heavy" in sfx_names
    assert "metal_weapon_clash" in sfx_names
    assert "paper_shockwave" in sfx_names

    # Check timestamps: 10.0 + (0.45 * 4.0) = 11.8s for clash
    clash_clip = next(c for c in clips if c.metadata.get("sfx_name") == "metal_weapon_clash")
    assert abs(clash_clip.start_time_sec - 11.80) < 0.05


def test_sfx_timeline_mapper_scene_schema(tmp_path: Path):
    """Verify SceneSchema with voice, preset, and explicit events maps to complete AudioTimeline."""
    dummy_voice = tmp_path / "voice_01.wav"
    # Create simple WAV
    from pydub import AudioSegment
    AudioSegment.silent(duration=3000).export(str(dummy_voice), format="wav")

    scene = SceneSchema(
        scene_id=1,
        narration_text="Tôn Ngộ Không vung gậy sắt đỡ đòn làm tóe lửa khắp mặt giấy!",
        audio_duration_sec=3.0,
        voice_audio_path=str(dummy_voice),
        background_state=BackgroundState.INK_SPLATTERED,
        actors=[
            ActorConfig(
                actor_id="wukong",
                display_name="Dark Wukong",
                skin=CharacterSkin.DARK_WUKONG,
                side=ActorSide.LEFT,
                weapon=WeaponType.RUYI_STAFF,
            )
        ],
        action_preset=ActionPreset.HEAVY_CHARGE_CLASH,
        camera_movement=CameraMovement.ZOOM_PUNCH_IMPACT,
        sfx_events=[
            SfxEvent(sfx_name="paper_shockwave", time_offset=1.2, volume=0.9),
        ],
    )

    mapper = SfxTimelineMapper()
    tl = mapper.build_scene_timeline(scene=scene, scene_start_sec=2.0)

    # Should contain 1 voiceover + 1 explicit sfx + 3 preset sfx
    voice_clips = tl.get_clips_by_type(AudioTrackType.VOICEOVER)
    sfx_clips = tl.get_clips_by_type(AudioTrackType.SFX)

    assert len(voice_clips) == 1
    assert voice_clips[0].start_time_sec == 2.0
    assert len(sfx_clips) >= 4


# -----------------------------------------------------------------------------
# 4. AUDIO COMPOSITOR & DUCKING TESTS
# -----------------------------------------------------------------------------

def test_audio_ducking_volume_envelope():
    """Verify sample-accurate ducking reduces BGM volume during speech and restores smoothly."""
    compositor = AudioCompositor()
    sr = 44100
    # 5.0 seconds of constant sine wave BGM
    dur_ms = 5000
    from pydub.generators import Sine
    sine_bgm = Sine(440).to_audio_segment(duration=dur_ms).set_frame_rate(sr).set_channels(2)
    base_volume = sine_bgm.max_dBFS

    # Speech between 1.5s and 3.5s
    voice_intervals = [(1.5, 3.5)]
    ducking_cfg = DuckingConfig(attenuation_db=-12.0, attack_sec=0.20, release_sec=0.35)

    ducked_bgm = compositor.apply_audio_ducking(sine_bgm, voice_intervals, ducking_cfg)
    assert len(ducked_bgm) == dur_ms

    # Test before speech (0.5s - 1.0s): should be near base volume
    early_slice = ducked_bgm[500:1000]
    assert abs(early_slice.max_dBFS - base_volume) < 0.5

    # Test mid-speech (2.0s - 3.0s): should be attenuated by ~12 dB
    mid_slice = ducked_bgm[2000:3000]
    expected_ducked = base_volume - 12.0
    assert abs(mid_slice.max_dBFS - expected_ducked) < 1.0

    # Test after speech (4.2s - 4.8s): should be fully restored to base volume
    late_slice = ducked_bgm[4200:4800]
    assert abs(late_slice.max_dBFS - base_volume) < 0.5


def test_audio_compositor_overlapping_sfx(tmp_path: Path):
    """Verify multiple overlapping SFX clips composite without crashing or clipping."""
    lib = SoundLibrary(root_dir=tmp_path / "audio")
    sfx1 = lib.get_sfx_path("metal_weapon_clash")
    sfx2 = lib.get_sfx_path("paper_shockwave")
    sfx3 = lib.get_sfx_path("whoosh_heavy")

    tl = AudioTimeline()
    # 3 overlapping SFX clips within 0.1s of each other
    tl.add_clip(AudioClip(track_type=AudioTrackType.SFX, file_path=sfx1, start_time_sec=0.5, duration_sec=0.7))
    tl.add_clip(AudioClip(track_type=AudioTrackType.SFX, file_path=sfx2, start_time_sec=0.55, duration_sec=1.0))
    tl.add_clip(AudioClip(track_type=AudioTrackType.SFX, file_path=sfx3, start_time_sec=0.6, duration_sec=0.8))

    compositor = AudioCompositor()
    mixed = compositor.mix_timeline(tl, target_duration_sec=2.5)

    assert len(mixed) == 2500
    assert mixed.max_dBFS <= -0.5, f"Peak limiter failed, max_dBFS = {mixed.max_dBFS}"


def test_audio_compositor_soft_limiter():
    """Verify soft peak limiter caps audio at target_peak_dbfs when sum exceeds headroom."""
    compositor = AudioCompositor(MixConfig(target_peak_dbfs=-1.0))
    from pydub.generators import Sine
    # Create very loud sine
    loud_sine = Sine(440).to_audio_segment(duration=1000).apply_gain(10.0)

    # Build timeline with 3 loud overlapping clips
    from pydub import AudioSegment
    sr = 44100
    tl = AudioTimeline()
    tmp_loud = Path("out/temp/loud_test.wav")
    tmp_loud.parent.mkdir(parents=True, exist_ok=True)
    loud_sine.export(str(tmp_loud), format="wav")

    tl.add_clip(AudioClip(track_type=AudioTrackType.SFX, file_path=tmp_loud, start_time_sec=0.0, duration_sec=1.0))
    tl.add_clip(AudioClip(track_type=AudioTrackType.SFX, file_path=tmp_loud, start_time_sec=0.0, duration_sec=1.0))
    tl.add_clip(AudioClip(track_type=AudioTrackType.SFX, file_path=tmp_loud, start_time_sec=0.0, duration_sec=1.0))

    mixed = compositor.mix_timeline(tl, target_duration_sec=1.0)
    assert mixed.max_dBFS <= -1.0 + 1e-4, f"Limiter exceeded: {mixed.max_dBFS}"


def test_audio_compositor_stem_export(tmp_path: Path):
    """Verify export_stems exports individual stem files and master audio."""
    lib = SoundLibrary(root_dir=tmp_path / "audio")
    sfx = lib.get_sfx_path("metal_weapon_clash")
    bgm = lib.get_bgm_path("dark_myth_orchestral")

    tl = AudioTimeline()
    tl.add_clip(AudioClip(track_type=AudioTrackType.SFX, file_path=sfx, start_time_sec=0.5))
    tl.add_clip(AudioClip(track_type=AudioTrackType.BGM, file_path=bgm, start_time_sec=0.0, duration_sec=3.0, loop=True))

    compositor = AudioCompositor()
    stems = compositor.export_stems(tl, output_dir=tmp_path / "stems", target_duration_sec=3.0)

    assert "sfx" in stems and stems["sfx"].is_file()
    assert "bgm" in stems and stems["bgm"].is_file()
    assert "master" in stems and stems["master"].is_file()


# -----------------------------------------------------------------------------
# 5. VIDEO AUDIO INTEGRATOR & FFMPEG MUXING TESTS
# -----------------------------------------------------------------------------

def test_video_audio_mux_and_ffprobe(tmp_path: Path):
    """Verify FFmpeg multiplexing of video and audio into playable MP4 and ffprobe inspection."""
    integrator = VideoAudioIntegrator()

    # Reuse wukong_combat_loop.mp4 from G6 if present, else create small test video
    existing_video = Path("out/preview/stickman/animation_loop/wukong_combat_loop.mp4")
    if not existing_video.is_file():
        # Create minimal video
        from PIL import Image
        engine = AnimationLoopEngine()
        track = AnimationTrack(
            keyframes=[Keyframe(time_sec=0.0, pose_name="standoff_idle")],
            duration_sec=0.5,
        )
        cfg = ActorConfig(
            actor_id="wukong",
            display_name="Dark Wukong",
            side=ActorSide.LEFT,
            skin=CharacterSkin.DARK_WUKONG,
            weapon=WeaponType.RUYI_STAFF,
            scale=0.5,
        )
        char = StickmanCharacter.from_actor_config(cfg)
        frames = engine.generate_clip_frames(track, char, fps=10)
        existing_video = tmp_path / "raw_video.mp4"
        engine.export_mp4_video(frames, existing_video, fps=10)

    # Create 4.0-second test audio file
    lib = SoundLibrary()
    bgm = lib.get_bgm_path("dark_myth_orchestral")
    tl = AudioTimeline()
    tl.add_clip(AudioClip(track_type=AudioTrackType.BGM, file_path=bgm, start_time_sec=0.0, duration_sec=4.0, loop=True))
    audio_path = tmp_path / "test_audio.wav"
    integrator.audio_compositor.export_master(tl, audio_path, target_duration_sec=4.0)

    # Mux
    out_mp4 = tmp_path / "muxed_output.mp4"
    integrator.mux_video_and_audio(
        video_path=existing_video,
        audio_path=audio_path,
        output_mp4_path=out_mp4,
    )

    assert out_mp4.is_file()
    assert out_mp4.stat().st_size > 1000

    # Probe and verify both streams
    probe = integrator.probe_media(out_mp4)
    streams = probe["streams"]
    v_stream = next(s for s in streams if s["codec_type"] == "video")
    a_stream = next(s for s in streams if s["codec_type"] == "audio")

    assert v_stream["codec_name"] == "h264"
    assert a_stream["codec_name"] == "aac"
    assert a_stream["channels"] == 2
    assert int(a_stream["sample_rate"]) == 44100


def test_deterministic_audio_mixing(tmp_path: Path):
    """Verify identical AudioTimeline and MixConfig yield byte-identical master audio."""
    lib = SoundLibrary()
    sfx = lib.get_sfx_path("metal_weapon_clash")
    tl = AudioTimeline()
    tl.add_clip(AudioClip(track_type=AudioTrackType.SFX, file_path=sfx, start_time_sec=0.2, gain_db=-2.0))

    compositor = AudioCompositor()
    out1 = tmp_path / "mix1.wav"
    out2 = tmp_path / "mix2.wav"

    compositor.export_master(tl, out1, target_duration_sec=1.5)
    compositor.export_master(tl, out2, target_duration_sec=1.5)

    assert out1.read_bytes() == out2.read_bytes()


def test_disabled_audio_clips(tmp_path: Path):
    """Verify disabled AudioClip is excluded from stems and master mix."""
    lib = SoundLibrary()
    sfx = lib.get_sfx_path("metal_weapon_clash")
    tl = AudioTimeline()
    tl.add_clip(AudioClip(track_type=AudioTrackType.SFX, file_path=sfx, start_time_sec=0.2, enabled=False))

    compositor = AudioCompositor()
    stems = compositor.render_stems(tl, target_duration_sec=1.0)
    # The SFX stem should be completely silent
    assert stems[AudioTrackType.SFX].max_dBFS == -float("inf")


def test_channel_and_sample_rate_conversion(tmp_path: Path):
    """Verify clips with different sample rates and mono channels are converted to 44.1kHz stereo."""
    from pydub.generators import Sine
    # Create 22050 Hz Mono audio
    mono_22k = Sine(440).to_audio_segment(duration=1000).set_frame_rate(22050).set_channels(1)
    mono_path = tmp_path / "mono_22k.wav"
    mono_22k.export(str(mono_path), format="wav")

    tl = AudioTimeline()
    tl.add_clip(AudioClip(track_type=AudioTrackType.SFX, file_path=mono_path, start_time_sec=0.0, duration_sec=1.0))

    compositor = AudioCompositor(MixConfig(sample_rate=44100, channels=2))
    master = compositor.mix_timeline(tl, target_duration_sec=1.0)

    assert master.frame_rate == 44100
    assert master.channels == 2
    assert len(master) == 1000


def test_audio_compositor_missing_file_raises_error():
    """Verify non-existent audio file raises FileNotFoundError during normalization."""
    tl = AudioTimeline()
    tl.add_clip(AudioClip(track_type=AudioTrackType.SFX, file_path=Path("non_existent_file_xyz.wav"), start_time_sec=0.0))
    compositor = AudioCompositor()
    with pytest.raises(FileNotFoundError, match="not found"):
        compositor.mix_timeline(tl, target_duration_sec=1.0)


def test_video_audio_integrator_render_complete_scene(tmp_path: Path):
    """Verify render_complete_scene generates all video, audio, stems, and final MP4 artifacts."""
    integrator = VideoAudioIntegrator()

    dummy_voice = tmp_path / "voice_01.wav"
    from pydub import AudioSegment
    AudioSegment.silent(duration=1500).export(str(dummy_voice), format="wav")

    scene = SceneSchema(
        scene_id=1,
        narration_text="Ngộ Không vung Thiết Bảng đỡ đòn Nhị Lang Thần!",
        audio_duration_sec=1.5,
        voice_audio_path=str(dummy_voice),
        background_state=BackgroundState.INK_SPLATTERED,
        actors=[
            ActorConfig(
                actor_id="wukong",
                display_name="Dark Wukong",
                side=ActorSide.LEFT,
                skin=CharacterSkin.DARK_WUKONG,
                weapon=WeaponType.RUYI_STAFF,
                scale=0.5,
            )
        ],
        action_preset=ActionPreset.HEAVY_CHARGE_CLASH,
        camera_movement=CameraMovement.ZOOM_PUNCH_IMPACT,
        sfx_events=[],
    )

    char = StickmanCharacter.from_actor_config(scene.actors[0])
    track = AnimationTrack(
        keyframes=[
            Keyframe(time_sec=0.0, pose_name="standoff_idle"),
            Keyframe(time_sec=1.5, pose_name="combat_stance"),
        ],
        duration_sec=1.5,
        loop=False,
    )

    out_scene_dir = tmp_path / "scene_output"
    artifacts = integrator.render_complete_scene(
        scene=scene,
        character=char,
        track=track,
        output_dir=out_scene_dir,
        clip_name="scene_01",
        fps=10,  # fast test fps
    )

    assert artifacts["final_mp4"].is_file()
    assert artifacts["master_audio"].is_file()
    assert artifacts["video_only"].is_file()

    # Probe final MP4
    probe = integrator.probe_media(artifacts["final_mp4"])
    streams = probe["streams"]
    assert any(s["codec_type"] == "video" for s in streams)
    assert any(s["codec_type"] == "audio" for s in streams)

