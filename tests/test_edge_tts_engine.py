"""Unit Tests for Stage 4.2 EdgeTTSAudioEngine and Audio Timing."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import mutagen.mp3
import pytest

from app.core.exceptions import AudioGenerationError
from app.modules.audio.edge_tts_engine import EdgeTTSAudioEngine
from app.schemas.scene_schema import (
    ActionPreset,
    ActorConfig,
    BackgroundState,
    CameraMovement,
    CharacterSkin,
    SceneSchema,
    SFXEvent,
)


def _make_sample_scene(scene_id: int = 1, text: str = "Tôn Ngộ Không đại náo thiên cung.") -> SceneSchema:
    return SceneSchema(
        scene_id=scene_id,
        narration_text=text,
        audio_duration_sec=0.0,
        voice_audio_path=None,
        background_state=BackgroundState.CLEAN_NOTEBOOK,
        actors=[
            ActorConfig(actor_id="wukong", skin=CharacterSkin.DARK_WUKONG, display_name="Ngộ Không"),
        ],
        action_preset=ActionPreset.DARK_AURA_STANDOFF,
        camera_movement=CameraMovement.STATIC_WIDE,
        sfx_events=[SFXEvent(sfx_name="dark_aura_hum", time_offset=0.2)],
    )


def _create_mock_mp3_on_disk(path: Path, duration_sec: float = 2.0, sample_rate: int = 44100):
    """Write an MP3 file using ffmpeg to guarantee valid Mutagen & Pydub decoding."""
    import subprocess
    cmd = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        "-y",
        "-f", "lavfi",
        "-i", f"sine=frequency=440:duration={duration_sec}",
        "-c:a", "libmp3lame",
        "-b:a", "128k",
        "-ar", str(sample_rate),
        str(path),
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)


# ---------------------------------------------------------------------------
# UNIT TESTS
# ---------------------------------------------------------------------------


def test_tts_engine_success_with_mock_edge_tts(tmp_path: Path):
    """Case 1: Successful voice synthesis and padding using mock Edge-TTS."""
    engine = EdgeTTSAudioEngine(max_retries=1)
    scene = _make_sample_scene(1)

    async def fake_edge_tts_call(text, voice, rate, output_file):
        _create_mock_mp3_on_disk(Path(output_file), duration_sec=1.5)

    with patch.object(engine, "_async_edge_tts_call", side_effect=fake_edge_tts_call):
        final_path, duration = engine.generate_scene_audio(scene, tmp_path)

        assert final_path.is_file()
        assert final_path.name == "scene_01_voice.mp3"
        # 1.5s voice + 0.3s padding = ~1.8s
        assert 1.75 <= duration <= 1.88
        assert scene.voice_audio_path == str(final_path.resolve())
        assert scene.audio_duration_sec == duration


def test_tts_engine_retries_on_no_audio_received(tmp_path: Path):
    """Case 2: Engine retries when edge-tts raises NoAudioReceived and succeeds on retry."""
    import edge_tts.exceptions

    engine = EdgeTTSAudioEngine(max_retries=3, base_backoff_sec=0.01)
    scene = _make_sample_scene(1)

    call_count = 0

    async def fake_flaky_call(text, voice, rate, output_file):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise edge_tts.exceptions.NoAudioReceived("No audio received from WebSocket")
        _create_mock_mp3_on_disk(Path(output_file), duration_sec=1.2)

    with patch.object(engine, "_async_edge_tts_call", side_effect=fake_flaky_call):
        final_path, duration = engine.generate_scene_audio(scene, tmp_path)

        assert call_count == 2
        assert final_path.is_file()
        assert duration > 1.4


def test_tts_engine_retries_on_timeout(tmp_path: Path):
    """Case 3: Engine retries when async call times out."""
    engine = EdgeTTSAudioEngine(max_retries=2, base_backoff_sec=0.01)
    scene = _make_sample_scene(1)

    call_count = 0

    async def fake_timeout_call(text, voice, rate, output_file):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise TimeoutError("WebSocket connection timed out")
        _create_mock_mp3_on_disk(Path(output_file), duration_sec=1.0)

    with patch.object(engine, "_async_edge_tts_call", side_effect=fake_timeout_call):
        final_path, duration = engine.generate_scene_audio(scene, tmp_path)

        assert call_count == 2
        assert final_path.is_file()


def test_tts_engine_switches_to_fallback_voice(tmp_path: Path):
    """Case 4: When primary voice fails all retries, switches to fallback voice and locks it."""
    import edge_tts.exceptions

    engine = EdgeTTSAudioEngine(
        voice_id="vi-VN-NamMinhNeural",
        fallback_voice_id="vi-VN-HoaiMyNeural",
        max_retries=2,
        base_backoff_sec=0.01,
        lock_voice_per_job=True,
    )
    scene = _make_sample_scene(1)

    used_voices = []

    async def fake_voice_switch(text, voice, rate, output_file):
        used_voices.append(voice)
        if voice == "vi-VN-NamMinhNeural":
            raise edge_tts.exceptions.NoAudioReceived("NamMinh node outage")
        _create_mock_mp3_on_disk(Path(output_file), duration_sec=1.5)

    with patch.object(engine, "_async_edge_tts_call", side_effect=fake_voice_switch):
        final_path, duration = engine.generate_scene_audio(scene, tmp_path)

        # 2 failed calls on NamMinh + 1 success on HoaiMy
        assert used_voices == [
            "vi-VN-NamMinhNeural",
            "vi-VN-NamMinhNeural",
            "vi-VN-HoaiMyNeural",
        ]
        assert final_path.is_file()
        assert engine.active_voice_id == "vi-VN-HoaiMyNeural"


def test_tts_engine_fails_when_all_voices_exhausted(tmp_path: Path):
    """Case 5: When both primary and fallback voices fail -> raises AudioGenerationError."""
    import edge_tts.exceptions

    engine = EdgeTTSAudioEngine(max_retries=2, base_backoff_sec=0.01)
    scene = _make_sample_scene(1)

    async def all_fail_call(text, voice, rate, output_file):
        raise edge_tts.exceptions.NoAudioReceived("All nodes down")

    with patch.object(engine, "_async_edge_tts_call", side_effect=all_fail_call):
        with pytest.raises(AudioGenerationError) as exc_info:
            engine.generate_scene_audio(scene, tmp_path)

        assert "Tạo giọng đọc thất bại trên toàn bộ giọng ứng viên" in str(exc_info.value)


def test_tts_engine_rejects_missing_file(tmp_path: Path):
    """Case 6: If Edge-TTS fails to produce file on disk -> raises AudioGenerationError."""
    engine = EdgeTTSAudioEngine(max_retries=1, base_backoff_sec=0.01)
    scene = _make_sample_scene(1)

    async def noop_call(text, voice, rate, output_file):
        # Do not create file
        pass

    with patch.object(engine, "_async_edge_tts_call", side_effect=noop_call):
        with pytest.raises(AudioGenerationError):
            engine.generate_scene_audio(scene, tmp_path)


def test_tts_engine_rejects_file_under_1024_bytes(tmp_path: Path):
    """Case 7: If Edge-TTS file is under 1024 bytes -> raises AudioGenerationError."""
    engine = EdgeTTSAudioEngine(max_retries=1, base_backoff_sec=0.01)
    scene = _make_sample_scene(1)

    async def small_file_call(text, voice, rate, output_file):
        Path(output_file).write_bytes(b"TOO_SMALL_DATA_MOCK")

    with patch.object(engine, "_async_edge_tts_call", side_effect=small_file_call):
        with pytest.raises(AudioGenerationError):
            engine.generate_scene_audio(scene, tmp_path)


def test_tts_engine_rejects_corrupted_file(tmp_path: Path):
    """Case 8: If file is > 1024 bytes of garbage not parsable by Mutagen -> raises AudioGenerationError."""
    engine = EdgeTTSAudioEngine(max_retries=1, base_backoff_sec=0.01)
    scene = _make_sample_scene(1)

    async def garbage_file_call(text, voice, rate, output_file):
        Path(output_file).write_bytes(b"CORRUPTED_GARBAGE_BYTES" * 100)

    with patch.object(engine, "_async_edge_tts_call", side_effect=garbage_file_call):
        with pytest.raises(AudioGenerationError):
            engine.generate_scene_audio(scene, tmp_path)


def test_tts_engine_rejects_duration_under_half_second(tmp_path: Path):
    """Case 9: If file duration is <= 0.5s -> raises AudioGenerationError."""
    engine = EdgeTTSAudioEngine(max_retries=1, base_backoff_sec=0.01)
    scene = _make_sample_scene(1)

    async def ultra_short_call(text, voice, rate, output_file):
        _create_mock_mp3_on_disk(Path(output_file), duration_sec=0.3)

    with patch.object(engine, "_async_edge_tts_call", side_effect=ultra_short_call):
        with pytest.raises(AudioGenerationError):
            engine.generate_scene_audio(scene, tmp_path)


def test_tts_engine_handles_pydub_failure(tmp_path: Path):
    """Case 10 & 11: If Pydub or FFmpeg fails during padding -> cleans up and raises AudioGenerationError."""
    engine = EdgeTTSAudioEngine(max_retries=1)
    scene = _make_sample_scene(1)

    async def valid_call(text, voice, rate, output_file):
        _create_mock_mp3_on_disk(Path(output_file), duration_sec=1.5)

    with patch.object(engine, "_async_edge_tts_call", side_effect=valid_call):
        with patch("pydub.AudioSegment.from_file", side_effect=RuntimeError("FFmpeg decode crashed")):
            with pytest.raises(AudioGenerationError) as exc_info:
                engine.generate_scene_audio(scene, tmp_path)

            assert "Pydub không thể giải mã" in str(exc_info.value)


def test_tts_engine_distinct_output_files_per_scene(tmp_path: Path):
    """Case 13 & 14: Two scenes have distinct filenames and do not overwrite each other."""
    engine = EdgeTTSAudioEngine(max_retries=1)
    scene1 = _make_sample_scene(1, "Cảnh thứ nhất.")
    scene2 = _make_sample_scene(2, "Cảnh thứ hai.")

    async def fake_tts_call(text, voice, rate, output_file):
        _create_mock_mp3_on_disk(Path(output_file), duration_sec=1.0)

    with patch.object(engine, "_async_edge_tts_call", side_effect=fake_tts_call):
        path1, dur1 = engine.generate_scene_audio(scene1, tmp_path)
        path2, dur2 = engine.generate_scene_audio(scene2, tmp_path)

        assert path1 != path2
        assert path1.name == "scene_01_voice.mp3"
        assert path2.name == "scene_02_voice.mp3"
        assert path1.is_file() and path2.is_file()


def test_tts_engine_preserves_all_schema_fields(tmp_path: Path):
    """Case 15: Engine preserves character, action_preset, background, and camera settings."""
    engine = EdgeTTSAudioEngine(max_retries=1)
    scene = SceneSchema(
        scene_id=5,
        narration_text="Bàn tay Phật giáng xuống.",
        audio_duration_sec=0.0,
        voice_audio_path=None,
        background_state=BackgroundState.HEAVENLY_PRESSURE,
        actors=[
            ActorConfig(actor_id="buddha", skin=CharacterSkin.BUDDHA_PALM, display_name="Phật Tổ"),
        ],
        action_preset=ActionPreset.GIANT_PALM_SUPPRESSION,
        camera_movement=CameraMovement.PAN_VERTICAL_UP,
        sfx_events=[SFXEvent(sfx_name="giant_palm_boom", time_offset=0.5)],
    )

    async def fake_tts_call(text, voice, rate, output_file):
        _create_mock_mp3_on_disk(Path(output_file), duration_sec=2.0)

    with patch.object(engine, "_async_edge_tts_call", side_effect=fake_tts_call):
        final_path, duration = engine.generate_scene_audio(scene, tmp_path)

        # Updated fields
        assert scene.voice_audio_path == str(final_path.resolve())
        assert scene.audio_duration_sec == duration
        # Preserved fields
        assert scene.narration_text == "Bàn tay Phật giáng xuống."
        assert scene.background_state == BackgroundState.HEAVENLY_PRESSURE
        assert scene.action_preset == ActionPreset.GIANT_PALM_SUPPRESSION
        assert scene.camera_movement == CameraMovement.PAN_VERTICAL_UP
        assert scene.actors[0].skin == CharacterSkin.BUDDHA_PALM
        assert scene.sfx_events[0].sfx_name == "giant_palm_boom"


def test_tts_engine_ensures_job_level_voice_consistency(tmp_path: Path):
    """Case 16: Voice consistency locked across entire Job when fallback occurs on Scene 1."""
    import edge_tts.exceptions

    engine = EdgeTTSAudioEngine(
        voice_id="vi-VN-NamMinhNeural",
        fallback_voice_id="vi-VN-HoaiMyNeural",
        max_retries=2,
        base_backoff_sec=0.01,
        lock_voice_per_job=True,
    )
    scene1 = _make_sample_scene(1, "Cảnh đầu tiên.")
    scene2 = _make_sample_scene(2, "Cảnh thứ hai tiếp theo.")

    used_voices_log = []

    async def mock_tts_run(text, voice, rate, output_file):
        used_voices_log.append((text, voice))
        if voice == "vi-VN-NamMinhNeural":
            raise edge_tts.exceptions.NoAudioReceived("Primary voice down")
        _create_mock_mp3_on_disk(Path(output_file), duration_sec=1.0)

    with patch.object(engine, "_async_edge_tts_call", side_effect=mock_tts_run):
        # Scene 1 triggers fallback to HoaiMy
        engine.generate_scene_audio(scene1, tmp_path)
        assert engine.active_voice_id == "vi-VN-HoaiMyNeural"

        # Scene 2 MUST immediately use HoaiMyNeural without trying NamMinh again
        engine.generate_scene_audio(scene2, tmp_path)

        # Verify calls:
        # Scene 1: NamMinh (fail), NamMinh (fail) -> HoaiMy (success)
        # Scene 2: HoaiMy directly (success)!
        scene2_voices = [v for t, v in used_voices_log if t == "Cảnh thứ hai tiếp theo."]
        assert scene2_voices == ["vi-VN-HoaiMyNeural"]


def test_tts_engine_rejects_empty_or_whitespace_narration(tmp_path: Path):
    """Case 12: Empty or whitespace narration string raises AudioGenerationError if bypassed into engine."""
    engine = EdgeTTSAudioEngine()
    scene = _make_sample_scene(1, "Valid text initially")

    object.__setattr__(scene, "narration_text", "   \t\n  ")
    with pytest.raises(AudioGenerationError) as exc:
        engine.generate_scene_audio(scene, tmp_path)
    assert "narration_text rỗng" in str(exc.value)

    object.__setattr__(scene, "narration_text", "")
    with pytest.raises(AudioGenerationError) as exc2:
        engine.generate_scene_audio(scene, tmp_path)
    assert "narration_text rỗng" in str(exc2.value)


def test_tts_engine_rate_formatting():
    """Case 17: Edge-TTS speed percentage string formatting."""
    assert EdgeTTSAudioEngine(voice_speed=1.0)._format_rate_str() == "+0%"
    assert EdgeTTSAudioEngine(voice_speed=1.05)._format_rate_str() == "+5%"
    assert EdgeTTSAudioEngine(voice_speed=1.20)._format_rate_str() == "+20%"
    assert EdgeTTSAudioEngine(voice_speed=0.90)._format_rate_str() == "-10%"
    assert EdgeTTSAudioEngine(voice_speed=0.85)._format_rate_str() == "-15%"


def test_tts_engine_verifies_padding_duration_increase(tmp_path: Path):
    """Case 18: Verify silence padding adds ~0.30s to duration."""
    engine = EdgeTTSAudioEngine(audio_padding_sec=0.30)
    raw_path = tmp_path / "raw.mp3"
    padded_path = tmp_path / "padded.mp3"

    _create_mock_mp3_on_disk(raw_path, duration_sec=1.50)
    raw_meta = mutagen.mp3.MP3(str(raw_path))
    raw_dur = raw_meta.info.length

    padded_dur = engine._apply_silence_padding(raw_path, padded_path, scene_id=1, raw_duration=raw_dur)
    delta = padded_dur - raw_dur
    assert 0.25 <= delta <= 0.38
    assert padded_dur > raw_dur


def test_tts_engine_mid_job_fallback_recovery_resynthesizes_prior_scenes(tmp_path: Path):
    """
    Case 19 (Section III Required):
    Mid-job fallback recovery (Case B):
      - Scene 1 succeeds with NamMinhNeural.
      - Scene 2 fails on NamMinhNeural across all retries, falls back to HoaiMyNeural.
      - Engine detects mid-job voice change and automatically re-synthesizes Scene 1 with HoaiMyNeural.
      - Scene 3-5 continue with HoaiMyNeural.
      - Result: 100% of scenes in the Job have unified voice (HoaiMyNeural).
    """
    import edge_tts.exceptions

    engine = EdgeTTSAudioEngine(
        voice_id="vi-VN-NamMinhNeural",
        fallback_voice_id="vi-VN-HoaiMyNeural",
        max_retries=2,
        base_backoff_sec=0.01,
        lock_voice_per_job=True,
    )

    scenes = [_make_sample_scene(i, f"Nội dung phân cảnh số {i}.") for i in range(1, 6)]
    call_log = []

    async def mock_mid_job_fail(text, voice, rate, output_file):
        call_log.append((text, voice))
        # Scene 2 fails on NamMinh
        if "phân cảnh số 2" in text and voice == "vi-VN-NamMinhNeural":
            raise edge_tts.exceptions.NoAudioReceived("NamMinh failed on scene 2")
        _create_mock_mp3_on_disk(Path(output_file), duration_sec=1.2)

    with patch.object(engine, "_async_edge_tts_call", side_effect=mock_mid_job_fail):
        # 1. Run Scene 1
        path1, dur1 = engine.generate_scene_audio(scenes[0], tmp_path)
        assert engine.active_voice_id == "vi-VN-NamMinhNeural"

        # 2. Run Scene 2 (NamMinh fails, switches to HoaiMy, re-synthesizes Scene 1 with HoaiMy)
        path2, dur2 = engine.generate_scene_audio(scenes[1], tmp_path)
        assert engine.active_voice_id == "vi-VN-HoaiMyNeural"

        # 3. Run Scene 3, 4, 5
        path3, dur3 = engine.generate_scene_audio(scenes[2], tmp_path)
        path4, dur4 = engine.generate_scene_audio(scenes[3], tmp_path)
        path5, dur5 = engine.generate_scene_audio(scenes[4], tmp_path)

        # Assert all 5 files exist and have valid durations
        for p in [path1, path2, path3, path4, path5]:
            assert p.is_file()

        # Check call log details:
        # Scene 1 initial: (Scene 1, NamMinh)
        # Scene 2: (Scene 2, NamMinh x2 fail) -> (Scene 2, HoaiMy)
        # Whole-job Recovery: (Scene 1, HoaiMy)
        # Scene 3: (Scene 3, HoaiMy)
        # Scene 4: (Scene 4, HoaiMy)
        # Scene 5: (Scene 5, HoaiMy)
        hoaimy_calls = [c for c in call_log if c[1] == "vi-VN-HoaiMyNeural"]
        assert len(hoaimy_calls) == 5  # Scenes 2, 1 (recovery), 3, 4, 5!
        assert engine.active_voice_id == "vi-VN-HoaiMyNeural"


def test_tts_engine_mid_job_fallback_fails_cleanly_if_prior_scene_cannot_be_resynthesized(tmp_path: Path):
    """
    Case 20 (Section III Case C):
    If mid-job voice fallback occurs, but re-synthesizing prior scene fails,
    engine stops immediately and raises AudioGenerationError, preventing mixed-voice outputs.
    """
    import edge_tts.exceptions

    engine = EdgeTTSAudioEngine(
        voice_id="vi-VN-NamMinhNeural",
        fallback_voice_id="vi-VN-HoaiMyNeural",
        max_retries=1,
        base_backoff_sec=0.01,
        lock_voice_per_job=True,
    )

    scene1 = _make_sample_scene(1, "Phân cảnh một.")
    scene2 = _make_sample_scene(2, "Phân cảnh hai.")

    async def flaky_call(text, voice, rate, output_file):
        if "hai" in text and voice == "vi-VN-NamMinhNeural":
            raise edge_tts.exceptions.NoAudioReceived("NamMinh outage on scene 2")
        if "một" in text and voice == "vi-VN-HoaiMyNeural":
            raise RuntimeError("Disk write failed during scene 1 recovery")
        _create_mock_mp3_on_disk(Path(output_file), duration_sec=1.0)

    with patch.object(engine, "_async_edge_tts_call", side_effect=flaky_call):
        engine.generate_scene_audio(scene1, tmp_path)

        with pytest.raises(AudioGenerationError) as exc_info:
            engine.generate_scene_audio(scene2, tmp_path)

        assert "Không thể đồng nhất giọng đọc toàn Job" in str(exc_info.value)

