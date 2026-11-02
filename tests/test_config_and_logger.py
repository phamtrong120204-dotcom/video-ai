"""Unit Tests for Core Configuration, Directory Bootstrapping, Logging, and Package Imports."""

from pathlib import Path
import pytest

import app
from app.core.config import AppConfig, get_config
from app.core.exceptions import (
    AnimationRenderError,
    AudioGenerationError,
    AutoStudioError,
    ConfigurationError,
    ScriptParseError,
    VideoCompositingError,
)
from app.core.logger import get_logger, reset_log_job_id, set_log_job_id, setup_logging


def test_package_imports_cleanly() -> None:
    """Verify that all Phase 3 packages and submodules import without syntax or circular errors."""
    import app.core
    import app.interfaces
    import app.modules
    import app.pipeline
    import app.schemas

    assert hasattr(app, "__version__")
    assert hasattr(app.core, "TaskManager")
    assert hasattr(app.interfaces, "IScriptParser")
    assert hasattr(app.modules, "StubScriptParser")
    assert hasattr(app.pipeline, "PipelineOrchestrator")
    assert hasattr(app.schemas, "SceneSchema")


def test_config_creates_required_directories_and_safe_defaults(tmp_path: Path) -> None:
    """Verify AppConfig initializes default 1080x1920@30fps settings and creates in/, out/, assets/, logs/."""
    cfg = AppConfig(base_dir=tmp_path)

    assert cfg.video_width == 1080
    assert cfg.video_height == 1920
    assert cfg.video_fps == 30
    assert cfg.aspect_ratio == "9:16"
    assert cfg.default_voice_id == "vi-VN-NamMinhNeural"

    assert cfg.in_dir.is_dir()
    assert cfg.out_dir.is_dir()
    assert cfg.temp_dir.is_dir()
    assert cfg.jobs_dir.is_dir()
    assert cfg.assets_dir.is_dir()
    assert cfg.logs_dir.is_dir()


def test_config_loads_custom_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify AppConfig.from_env reads custom .env settings and rejects invalid resolution/FPS."""
    monkeypatch.delenv("RENDER_RESOLUTION", raising=False)
    monkeypatch.delenv("RENDER_FPS", raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        "RENDER_RESOLUTION=540x960\nRENDER_FPS=60\nTTS_DEFAULT_VOICE=vi-VN-HoaiMyNeural\n",
        encoding="utf-8",
    )

    cfg = AppConfig.from_env(env_file=env_file, base_dir=tmp_path)
    assert cfg.video_width == 540
    assert cfg.video_height == 960
    assert cfg.video_fps == 60
    assert cfg.default_voice_id == "vi-VN-HoaiMyNeural"

    with pytest.raises(ConfigurationError):
        AppConfig(base_dir=tmp_path, video_width=-100, video_height=1920)

    with pytest.raises(ConfigurationError):
        AppConfig(base_dir=tmp_path, video_fps=0)


def test_config_resolves_ffmpeg_and_ffprobe_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify AppConfig resolves FFMPEG_PATH and FFPROBE_PATH from env or defaults."""
    fake_ffmpeg = tmp_path / "fake_ffmpeg.exe"
    fake_ffprobe = tmp_path / "fake_ffprobe.exe"
    fake_ffmpeg.write_text("fake", encoding="utf-8")
    fake_ffprobe.write_text("fake", encoding="utf-8")

    env_file = tmp_path / ".env"
    env_file.write_text(
        f"FFMPEG_PATH={fake_ffmpeg}\nFFPROBE_PATH={fake_ffprobe}\n",
        encoding="utf-8",
    )

    # Use monkeypatch so that temporary test env values are automatically cleaned up
    monkeypatch.setenv("FFMPEG_PATH", str(fake_ffmpeg))
    monkeypatch.setenv("FFPROBE_PATH", str(fake_ffprobe))

    cfg = AppConfig.from_env(env_file=env_file, base_dir=tmp_path)
    assert cfg.ffmpeg_path == str(fake_ffmpeg.resolve())
    assert cfg.ffprobe_path == str(fake_ffprobe.resolve())


def test_logger_writes_structured_output_with_job_id(tmp_path: Path) -> None:
    """Verify structured logger writes timestamp, level, module name, and job_id to logs/app.log."""
    log_path = tmp_path / "logs" / "app.log"
    setup_logging(log_file=log_path)

    token = set_log_job_id("job_log_test_99")
    try:
        logger = get_logger("parser.unit_test", log_file=log_path)
        logger.info("Khởi tạo kiểm thử phân tách kịch bản Hắc Ám Tây Du")
        logger.warning("Cảnh báo chuyển sang nhánh Rule-Based Fallback")
    finally:
        reset_log_job_id(token)

    assert log_path.exists()
    content = log_path.read_text(encoding="utf-8")
    assert "INFO" in content
    assert "WARNING" in content
    assert "autostudio.parser.unit_test" in content
    assert "[job=job_log_test_99]" in content
    assert "Khởi tạo kiểm thử phân tách kịch bản Hắc Ám Tây Du" in content


def test_layered_exceptions_format_job_id_and_stage() -> None:
    """Verify custom exception classes preserve job_id, stage, and cause."""
    err = ScriptParseError("Kịch bản không hợp lệ", job_id="job_err_01")
    assert isinstance(err, AutoStudioError)
    assert err.stage == "parsing"
    assert "[job_id=job_err_01][stage=parsing]" in str(err)

    assert AudioGenerationError("TTS lỗi").stage == "generating_audio"
    assert AnimationRenderError("Rig lỗi").stage == "rendering_animation"
    assert VideoCompositingError("FFmpeg lỗi").stage == "compositing"
