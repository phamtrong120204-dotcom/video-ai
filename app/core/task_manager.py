"""Task Manager & Job Lifecycle State Machine for Dark Myth Stickman Auto-Studio."""

from collections import deque
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Optional

from app.core.config import AppConfig, get_config
from app.core.exceptions import JobStateTransitionError
from app.core.logger import get_logger
from app.schemas.job_schema import JobRecord, JobSource, JobStatus
from app.schemas.script_schema import ScriptInput


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# Valid forward and failure state transitions
_ALLOWED_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.QUEUED: {JobStatus.PARSING, JobStatus.FAILED},
    JobStatus.PARSING: {JobStatus.GENERATING_AUDIO, JobStatus.FAILED},
    JobStatus.GENERATING_AUDIO: {JobStatus.RENDERING_ANIMATION, JobStatus.FAILED},
    JobStatus.RENDERING_ANIMATION: {JobStatus.COMPOSITING, JobStatus.FAILED},
    JobStatus.COMPOSITING: {JobStatus.COMPLETED, JobStatus.FAILED},
    JobStatus.COMPLETED: set(),
    JobStatus.FAILED: set(),
}

_DEFAULT_PROGRESS_BY_STATUS: dict[JobStatus, int] = {
    JobStatus.QUEUED: 0,
    JobStatus.PARSING: 10,
    JobStatus.GENERATING_AUDIO: 25,
    JobStatus.RENDERING_ANIMATION: 55,
    JobStatus.COMPOSITING: 85,
    JobStatus.COMPLETED: 100,
}


class TaskManager:
    """Manages job creation, FIFO queue, state transitions, and JSON state persistence."""

    def __init__(self, config: Optional[AppConfig] = None, jobs_dir: Optional[Path] = None) -> None:
        self.config = config or get_config()
        self.jobs_dir = (jobs_dir or self.config.jobs_dir).resolve()
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self._jobs: dict[str, JobRecord] = {}
        self._queue: deque[str] = deque()
        self._logger = get_logger("core.task_manager")

    def _job_file_path(self, job_id: str) -> Path:
        return self.jobs_dir / f"{job_id}.json"

    def save_job(self, record: JobRecord) -> Path:
        """Persist JobRecord to JSON on disk."""
        record.updated_at = _utc_now_iso()
        self._jobs[record.job_id] = record
        path = self._job_file_path(record.job_id)
        path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        return path

    def load_job(self, job_id: str) -> JobRecord:
        """Load JobRecord from memory cache or JSON file on disk."""
        if job_id in self._jobs:
            return self._jobs[job_id]
        path = self._job_file_path(job_id)
        if not path.exists():
            raise JobStateTransitionError(f"Job '{job_id}' not found", job_id=job_id)
        data = json.loads(path.read_text(encoding="utf-8"))
        record = JobRecord.model_validate(data)
        self._jobs[job_id] = record
        return record

    def create_job(
        self,
        script_input: Optional[ScriptInput] = None,
        *,
        job_id: Optional[str] = None,
        source: JobSource | str = JobSource.WEB,
    ) -> JobRecord:
        """Create a new queued JobRecord and push its job_id into the FIFO queue."""
        resolved_job_id = job_id or (script_input.job_id if script_input else None)
        if not resolved_job_id:
            from app.schemas.script_schema import _generate_job_id

            resolved_job_id = _generate_job_id()

        resolved_source = (
            JobSource(script_input.source_channel.value)
            if script_input is not None
            else JobSource(source)
        )

        record = JobRecord(
            job_id=resolved_job_id,
            source=resolved_source,
            status=JobStatus.QUEUED,
            progress_percent=0,
            current_step_message="Tác vụ đã được đưa vào hàng đợi.",
        )
        self.save_job(record)
        self._queue.append(record.job_id)
        self._logger.info(f"Created new job '{record.job_id}' from source '{record.source.value}'", extra={"job_id": record.job_id})
        return record

    def pop_next_queued_job(self) -> Optional[JobRecord]:
        """Dequeue the next job waiting in the FIFO queue."""
        while self._queue:
            next_id = self._queue.popleft()
            record = self.load_job(next_id)
            if record.status == JobStatus.QUEUED:
                return record
        return None

    def transition_status(
        self,
        job_id: str,
        new_status: JobStatus,
        *,
        progress_percent: Optional[int] = None,
        step_message: Optional[str] = None,
        total_scenes: Optional[int] = None,
        completed_scenes: Optional[int] = None,
        output_video_path: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> JobRecord:
        """Validate and transition a job to `new_status`, persisting the updated state."""
        record = self.load_job(job_id)
        current = record.status

        if new_status != current:
            allowed = _ALLOWED_TRANSITIONS.get(current, set())
            if new_status not in allowed:
                raise JobStateTransitionError(
                    f"Invalid state transition from '{current.value}' to '{new_status.value}'",
                    job_id=job_id,
                )

        record.status = new_status
        if progress_percent is not None:
            if not (0 <= progress_percent <= 100):
                raise JobStateTransitionError(
                    f"progress_percent must be between 0 and 100, got {progress_percent}",
                    job_id=job_id,
                )
            record.progress_percent = progress_percent
        elif new_status in _DEFAULT_PROGRESS_BY_STATUS:
            record.progress_percent = max(record.progress_percent, _DEFAULT_PROGRESS_BY_STATUS[new_status])

        if step_message is not None:
            record.current_step_message = step_message
        if total_scenes is not None:
            record.total_scenes = total_scenes
        if completed_scenes is not None:
            record.completed_scenes = completed_scenes
        if output_video_path is not None:
            record.output_video_path = output_video_path
        if error_message is not None:
            record.error_message = error_message

        self.save_job(record)
        self._logger.info(
            f"Job status -> {record.status.value} ({record.progress_percent}%): {record.current_step_message}",
            extra={"job_id": job_id},
        )
        return record

    def mark_completed(
        self,
        job_id: str,
        output_video_path: str | Path,
        step_message: str = "Đã kết xuất video MP4 hoàn tất.",
    ) -> JobRecord:
        """Transition a job to COMPLETED with 100% progress and output video path."""
        return self.transition_status(
            job_id=job_id,
            new_status=JobStatus.COMPLETED,
            progress_percent=100,
            step_message=step_message,
            output_video_path=str(output_video_path),
        )

    def mark_failed(self, job_id: str, error_message: str) -> JobRecord:
        """Transition a job to FAILED and record the exact error cause."""
        record = self.load_job(job_id)
        if record.status in (JobStatus.COMPLETED, JobStatus.FAILED):
            raise JobStateTransitionError(
                f"Cannot mark terminal job ({record.status.value}) as failed",
                job_id=job_id,
            )
        record.status = JobStatus.FAILED
        record.error_message = error_message
        record.current_step_message = f"Tác vụ thất bại: {error_message}"
        self.save_job(record)
        self._logger.error(f"Job failed: {error_message}", extra={"job_id": job_id})
        return record

    def list_jobs(self) -> list[JobRecord]:
        """List all persisted jobs sorted by creation time."""
        for json_file in sorted(self.jobs_dir.glob("*.json")):
            job_id = json_file.stem
            if job_id not in self._jobs:
                self.load_job(job_id)
        return list(self._jobs.values())
