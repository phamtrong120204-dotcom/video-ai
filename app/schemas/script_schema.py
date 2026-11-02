"""Script Input Data Contracts (ScriptInput, RenderConfig, TargetDuration, TelegramMeta)."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SourceChannel(str, Enum):
    """Supported input channels for submitting scripts."""

    WEB_UI = "web_ui"
    WEB = "web"
    TELEGRAM_BOT = "telegram_bot"
    TELEGRAM = "telegram"
    CLI_TEST = "cli_test"


class TargetDuration(BaseModel):
    """Target duration bounds in seconds for the generated video."""

    model_config = ConfigDict(extra="forbid")

    min: float = Field(default=60.0, ge=1.0, description="Minimum target video duration in seconds")
    max: float = Field(default=180.0, ge=5.0, description="Maximum target video duration in seconds")

    @model_validator(mode="after")
    def validate_bounds(self) -> "TargetDuration":
        if self.min > self.max:
            raise ValueError(f"target_duration_sec.min ({self.min}) cannot exceed max ({self.max})")
        return self


class RenderConfig(BaseModel):
    """Video rendering configuration parameters (9:16 vertical MP4)."""

    model_config = ConfigDict(extra="forbid")

    width: int = Field(default=1080, gt=0)
    height: int = Field(default=1920, gt=0)
    fps: int = Field(default=30, gt=0, le=120)
    burn_subtitles: bool = Field(default=True)
    bgm_theme: str = Field(default="dark_myth_orchestral", min_length=1)


class TelegramMeta(BaseModel):
    """Optional Telegram metadata when a job is triggered from the Telegram Bot."""

    model_config = ConfigDict(extra="forbid")

    chat_id: int | str
    message_id: Optional[int] = None
    username: Optional[str] = None


def _generate_job_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    short_hash = uuid4().hex[:6]
    return f"job_{timestamp}_{short_hash}"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ScriptInput(BaseModel):
    """Canonical input payload passed from Interface Layer to Task Orchestrator & Parser."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(default_factory=_generate_job_id, min_length=3)
    source_channel: SourceChannel = Field(default=SourceChannel.WEB_UI)
    title: str = Field(default="Hắc Ám Tây Du Ký Sự", min_length=1, max_length=200)
    raw_script_text: str = Field(..., min_length=10, max_length=6000)
    voice_id: str = Field(default="vi-VN-NamMinhNeural", min_length=3)
    voice_speed: float = Field(default=1.05, ge=0.5, le=2.0)
    target_duration_sec: TargetDuration = Field(default_factory=TargetDuration)
    render_config: RenderConfig = Field(default_factory=RenderConfig)
    telegram_meta: Optional[TelegramMeta] = Field(default=None)
    created_at: str = Field(default_factory=_utc_now_iso)

    @field_validator("raw_script_text")
    @classmethod
    def validate_script_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 10:
            raise ValueError("raw_script_text must contain at least 10 non-whitespace characters")
        return cleaned

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title cannot be blank")
        return cleaned
