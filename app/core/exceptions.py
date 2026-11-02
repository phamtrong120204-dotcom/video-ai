"""Domain-Specific Exception Hierarchy for Dark Myth Stickman Auto-Studio."""

from typing import Optional


class AutoStudioError(Exception):
    """Base exception for all errors inside Dark Myth Stickman Auto-Studio."""

    def __init__(
        self,
        message: str,
        *,
        job_id: Optional[str] = None,
        stage: str = "general",
        cause: Optional[Exception] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.job_id = job_id
        self.stage = stage
        self.cause = cause

    def __str__(self) -> str:
        prefix = f"[stage={self.stage}]"
        if self.job_id:
            prefix = f"[job_id={self.job_id}]{prefix}"
        return f"{prefix} {self.message}"


class ConfigurationError(AutoStudioError):
    """Raised when configuration or required directory setup is invalid."""

    def __init__(self, message: str, *, job_id: Optional[str] = None, cause: Optional[Exception] = None) -> None:
        super().__init__(message, job_id=job_id, stage="configuration", cause=cause)


class JobStateTransitionError(AutoStudioError):
    """Raised when an invalid job status transition or missing job is encountered."""

    def __init__(self, message: str, *, job_id: Optional[str] = None, cause: Optional[Exception] = None) -> None:
        super().__init__(message, job_id=job_id, stage="task_manager", cause=cause)


class ScriptParseError(AutoStudioError):
    """Raised during the script parsing stage (LLM or Rule-based parser failure)."""

    def __init__(self, message: str, *, job_id: Optional[str] = None, cause: Optional[Exception] = None) -> None:
        super().__init__(message, job_id=job_id, stage="parsing", cause=cause)


class AudioGenerationError(AutoStudioError):
    """Raised during Vietnamese TTS synthesis, duration measurement, or audio mixing."""

    def __init__(self, message: str, *, job_id: Optional[str] = None, cause: Optional[Exception] = None) -> None:
        super().__init__(message, job_id=job_id, stage="generating_audio", cause=cause)


class AnimationRenderError(AutoStudioError):
    """Raised during 2D procedural stickman rigging, notebook background, or VFX rendering."""

    def __init__(self, message: str, *, job_id: Optional[str] = None, cause: Optional[Exception] = None) -> None:
        super().__init__(message, job_id=job_id, stage="rendering_animation", cause=cause)


class VideoCompositingError(AutoStudioError):
    """Raised during final MP4 encoding, audio-video muxing, or ffprobe verification."""

    def __init__(self, message: str, *, job_id: Optional[str] = None, cause: Optional[Exception] = None) -> None:
        super().__init__(message, job_id=job_id, stage="compositing", cause=cause)


# Aliases matching common layer naming conventions
ParserError = ScriptParseError
AudioError = AudioGenerationError
RenderError = AnimationRenderError
CompositorError = VideoCompositingError
