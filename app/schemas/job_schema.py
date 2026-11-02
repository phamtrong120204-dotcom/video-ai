"""Job Lifecycle and Render Output Data Contracts (JobStatus, JobRecord, RenderResult)."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.scene_schema import SceneSchema
from app.schemas.script_schema import SourceChannel


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobStatus(str, Enum):
    """7 Canonical job states defined in docs/04_data_contracts.md."""

    QUEUED = "queued"
    PARSING = "parsing"
    GENERATING_AUDIO = "generating_audio"
    RENDERING_ANIMATION = "rendering_animation"
    COMPOSITING = "compositing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobSource(str, Enum):
    """Job trigger origin ('web', 'telegram', or contract equivalents)."""

    WEB = "web"
    TELEGRAM = "telegram"
    WEB_UI = "web_ui"
    TELEGRAM_BOT = "telegram_bot"
    CLI_TEST = "cli_test"


class JobRecord(BaseModel):
    """Persistent state record for a rendering job managed by TaskManager."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(..., min_length=3)
    source: JobSource = Field(default=JobSource.WEB)
    status: JobStatus = Field(default=JobStatus.QUEUED)
    progress_percent: int = Field(default=0, ge=0, le=100)
    current_step_message: str = Field(default="Tác vụ đang xếp hàng chờ xử lý...")
    total_scenes: int = Field(default=0, ge=0)
    completed_scenes: int = Field(default=0, ge=0)
    error_message: Optional[str] = Field(default=None)
    output_video_path: Optional[str] = Field(default=None)
    created_at: str = Field(default_factory=_utc_now_iso)
    updated_at: str = Field(default_factory=_utc_now_iso)

    @field_validator("job_id")
    @classmethod
    def validate_job_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("job_id cannot be empty")
        return cleaned

    @model_validator(mode="before")
    @classmethod
    def normalize_error_aliases(cls, data: object) -> object:
        """Accept `error_detail` alias from docs/04_data_contracts.md."""
        if isinstance(data, dict):
            copied = dict(data)
            if "error_detail" in copied and "error_message" not in copied:
                copied["error_message"] = copied.pop("error_detail")
            elif "error_detail" in copied:
                copied.pop("error_detail")
            if "source" in copied and isinstance(copied["source"], SourceChannel):
                copied["source"] = copied["source"].value
            return copied
        return data

    @property
    def error_detail(self) -> Optional[str]:
        """Alias property matching docs/04_data_contracts.md."""
        return self.error_message


class TechnicalMetadata(BaseModel):
    """Verified video output technical metadata (populated from ffprobe)."""

    model_config = ConfigDict(extra="forbid")

    resolution: str = Field(default="1080x1920")
    aspect_ratio: str = Field(default="9:16")
    fps: int = Field(default=30, gt=0)
    duration_sec: float = Field(default=0.0, ge=0.0)
    file_size_bytes: int = Field(default=0, ge=0)
    video_codec: str = Field(default="h264")
    audio_codec: str = Field(default="aac")


class ProcessingStats(BaseModel):
    """Execution timing and engine selection telemetry for a completed job."""

    model_config = ConfigDict(extra="forbid")

    parser_mode: str = Field(default="skeleton_stub")
    tts_engine: str = Field(default="skeleton_stub")
    parse_time_sec: float = Field(default=0.0, ge=0.0)
    tts_time_sec: float = Field(default=0.0, ge=0.0)
    render_time_sec: float = Field(default=0.0, ge=0.0)
    composite_time_sec: float = Field(default=0.0, ge=0.0)
    total_time_sec: float = Field(default=0.0, ge=0.0)


class RenderResult(BaseModel):
    """Final output payload returned when a rendering job finishes."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(..., min_length=3)
    status: JobStatus = Field(default=JobStatus.COMPLETED)
    output_video_path: Optional[str] = Field(default=None)
    video_url: Optional[str] = Field(default=None)
    technical_metadata: Optional[TechnicalMetadata] = Field(default_factory=TechnicalMetadata)
    scenes_summary: list[SceneSchema] = Field(default_factory=list)
    processing_stats: ProcessingStats = Field(default_factory=ProcessingStats)
    completed_at: str = Field(default_factory=_utc_now_iso)
    error_message: Optional[str] = Field(default=None)

    @model_validator(mode="after")
    def validate_terminal_status(self) -> "RenderResult":
        if self.status not in (JobStatus.COMPLETED, JobStatus.FAILED):
            raise ValueError(f"RenderResult status must be 'completed' or 'failed', got '{self.status}'")
        if self.status == JobStatus.COMPLETED and not self.output_video_path:
            raise ValueError("output_video_path is required when RenderResult status is 'completed'")
        return self
