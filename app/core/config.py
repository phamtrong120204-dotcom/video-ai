"""Central Configuration Management for Dark Myth Stickman Auto-Studio."""

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from app.core.exceptions import ConfigurationError

# Ensure C:\ffmpeg\bin is in PATH for all media tools and pydub
_default_ffmpeg_dir = r"C:\ffmpeg\bin"
if Path(_default_ffmpeg_dir).is_dir() and _default_ffmpeg_dir.lower() not in os.environ.get("PATH", "").lower():
    os.environ["PATH"] = f"{_default_ffmpeg_dir};{os.environ.get('PATH', '')}"


def _parse_resolution(res_str: str) -> tuple[int, int]:
    """Parse 'WIDTHxHEIGHT' string into integer (width, height) tuple."""
    try:
        parts = res_str.lower().strip().split("x")
        if len(parts) != 2:
            raise ValueError(f"Invalid resolution format: {res_str}")
        w, h = int(parts[0]), int(parts[1])
        if w <= 0 or h <= 0:
            raise ValueError("Width and height must be positive integers")
        return w, h
    except Exception as exc:
        raise ConfigurationError(f"Failed to parse RENDER_RESOLUTION='{res_str}': {exc}", cause=exc) from exc


@dataclass
class AppConfig:
    """Application-wide configuration loaded from environment variables with safe defaults."""

    base_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2])
    in_dir: Path = field(init=False)
    out_dir: Path = field(init=False)
    temp_dir: Path = field(init=False)
    jobs_dir: Path = field(init=False)
    assets_dir: Path = field(init=False)
    logs_dir: Path = field(init=False)

    video_width: int = 1080
    video_height: int = 1920
    video_fps: int = 30
    aspect_ratio: str = "9:16"
    default_voice_id: str = "vi-VN-NamMinhNeural"
    default_voice_speed: float = 1.05
    default_bgm_theme: str = "dark_myth_orchestral"

    gemini_api_key: str = ""
    telegram_bot_token: str = ""
    telegram_allowed_users: str = ""
    app_url: str = "http://localhost:3000"
    max_concurrent_jobs: int = 1
    ffmpeg_path: Optional[str] = None
    ffprobe_path: Optional[str] = None

    def __post_init__(self) -> None:
        self.base_dir = Path(self.base_dir).resolve()
        self.in_dir = self.base_dir / "in"
        self.out_dir = self.base_dir / "out"
        self.temp_dir = self.out_dir / "temp"
        self.jobs_dir = self.out_dir / "jobs"
        self.assets_dir = self.base_dir / "assets"
        self.logs_dir = self.base_dir / "logs"

        if self.video_width <= 0 or self.video_height <= 0:
            raise ConfigurationError(
                f"Invalid video dimensions: {self.video_width}x{self.video_height}"
            )
        if self.video_fps <= 0 or self.video_fps > 120:
            raise ConfigurationError(f"Invalid FPS setting: {self.video_fps}")

        self.ensure_directories()

    def ensure_directories(self) -> None:
        """Ensure all required runtime directories (in/, out/, assets/, logs/) exist."""
        for directory in (
            self.in_dir,
            self.out_dir,
            self.temp_dir,
            self.jobs_dir,
            self.assets_dir,
            self.logs_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(
        cls,
        env_file: Optional[Path] = None,
        base_dir: Optional[Path] = None,
    ) -> "AppConfig":
        """Load configuration from .env file and OS environment variables."""
        resolved_base = (base_dir or Path(__file__).resolve().parents[2]).resolve()
        target_env = env_file or (resolved_base / ".env")
        if target_env.exists():
            load_dotenv(dotenv_path=target_env, override=True if env_file is not None else False)

        res_str = os.getenv("RENDER_RESOLUTION", "1080x1920")
        width, height = _parse_resolution(res_str)

        fps_str = os.getenv("RENDER_FPS", "30")
        try:
            fps = int(fps_str)
        except ValueError as exc:
            raise ConfigurationError(f"Invalid RENDER_FPS='{fps_str}'", cause=exc) from exc

        # Resolve ffmpeg_path
        raw_ffmpeg = os.getenv("FFMPEG_PATH", "").strip()
        resolved_ffmpeg: Optional[str] = None
        if raw_ffmpeg and Path(raw_ffmpeg).is_file():
            resolved_ffmpeg = str(Path(raw_ffmpeg).resolve())
        elif shutil.which("ffmpeg"):
            resolved_ffmpeg = shutil.which("ffmpeg")
        elif Path(r"C:\ffmpeg\bin\ffmpeg.exe").is_file():
            resolved_ffmpeg = str(Path(r"C:\ffmpeg\bin\ffmpeg.exe").resolve())

        # Resolve ffprobe_path
        raw_ffprobe = os.getenv("FFPROBE_PATH", "").strip()
        resolved_ffprobe: Optional[str] = None
        if raw_ffprobe and Path(raw_ffprobe).is_file():
            resolved_ffprobe = str(Path(raw_ffprobe).resolve())
        elif shutil.which("ffprobe"):
            resolved_ffprobe = shutil.which("ffprobe")
        elif Path(r"C:\ffmpeg\bin\ffprobe.exe").is_file():
            resolved_ffprobe = str(Path(r"C:\ffmpeg\bin\ffprobe.exe").resolve())

        return cls(
            base_dir=resolved_base,
            video_width=width,
            video_height=height,
            video_fps=fps,
            default_voice_id=os.getenv("TTS_DEFAULT_VOICE", "vi-VN-NamMinhNeural") or "vi-VN-NamMinhNeural",
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_allowed_users=os.getenv("TELEGRAM_ALLOWED_USERS", ""),
            app_url=os.getenv("APP_URL", "http://localhost:3000") or "http://localhost:3000",
            ffmpeg_path=resolved_ffmpeg,
            ffprobe_path=resolved_ffprobe,
        )


_DEFAULT_CONFIG: Optional[AppConfig] = None


def get_config(reload: bool = False, base_dir: Optional[Path] = None) -> AppConfig:
    """Return singleton or freshly loaded AppConfig instance."""
    global _DEFAULT_CONFIG
    if base_dir is not None:
        return AppConfig.from_env(base_dir=base_dir)
    if _DEFAULT_CONFIG is None or reload:
        _DEFAULT_CONFIG = AppConfig.from_env()
    return _DEFAULT_CONFIG
