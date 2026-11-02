"""
Dark Myth Stickman Auto-Studio - Job Service & Background Task Worker.

Provides thread-safe job management, asynchronous non-blocking pipeline execution,
cancellation tokens, progress tracking, and history queries for both Gradio Web UI
and Telegram Bot.
"""

from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import time
from typing import Any, Callable, Optional, Union

from app.core.config import AppConfig, get_config
from app.core.exceptions import JobStateTransitionError
from app.core.logger import get_logger
from app.core.task_manager import TaskManager
from app.pipeline.factory import create_production_pipeline
from app.pipeline.orchestrator import PipelineOrchestrator
from app.schemas.job_schema import JobRecord, JobSource, JobStatus, RenderResult
from app.schemas.script_schema import RenderConfig, ScriptInput, SourceChannel, TargetDuration, TelegramMeta

logger = get_logger("services.job_service")


class JobService:
    """
    Central background task service uniting Gradio Web UI and Telegram Bot.
    Guarantees shared state, zero file collisions, non-blocking execution, and cancellation.
    """

    _instance: Optional["JobService"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        task_manager: Optional[TaskManager] = None,
        orchestrator: Optional[PipelineOrchestrator] = None,
        max_workers: int = 2,
    ) -> None:
        if getattr(self, "_initialized", False):
            return

        self.config = config or get_config()
        self.task_manager = task_manager or TaskManager(config=self.config)
        self.orchestrator = orchestrator or create_production_pipeline(
            config=self.config,
            task_manager=self.task_manager,
        )
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="JobWorker")
        self._active_futures: dict[str, Future] = {}
        self._cancelled_jobs: set[str] = set()
        self._job_logs: dict[str, list[str]] = {}
        self._listeners: list[Callable[[JobRecord], None]] = []
        self._initialized = True
        logger.info(f"JobService initialized with {max_workers} background workers")

    def add_listener(self, callback: Callable[[JobRecord], None]) -> None:
        """Register a callback invoked whenever job status changes."""
        self._listeners.append(callback)

    def _notify(self, record: JobRecord) -> None:
        for cb in self._listeners:
            try:
                cb(record)
            except Exception as exc:
                logger.warning(f"Error in job listener callback: {exc}")

    def log_message(self, job_id: str, message: str) -> None:
        """Append log message to in-memory job buffer."""
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}"
        if job_id not in self._job_logs:
            self._job_logs[job_id] = []
        self._job_logs[job_id].append(formatted)
        logger.info(f"[{job_id}] {message}", extra={"job_id": job_id})

    def get_logs(self, job_id: str) -> list[str]:
        """Retrieve execution logs for job."""
        return self._job_logs.get(job_id, [])

    def submit_script_input(
        self,
        script_input: ScriptInput,
        on_complete: Optional[Callable[[RenderResult], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> str:
        """
        Submits a ScriptInput task to the background thread pool.
        Returns the job_id immediately without blocking the caller.
        """
        job_id = script_input.job_id
        record = self.task_manager.create_job(script_input)
        self.log_message(job_id, f"Tác vụ khởi tạo từ nguồn '{record.source.value}'.")
        self._notify(record)

        future = self.executor.submit(
            self._execute_job,
            script_input=script_input,
            on_complete=on_complete,
            on_error=on_error,
        )
        self._active_futures[job_id] = future
        return job_id

    def submit_raw_script(
        self,
        raw_script_text: str,
        project_name: str = "Dark Myth Project",
        source: JobSource = JobSource.WEB,
        telegram_user_id: Optional[int] = None,
        telegram_chat_id: Optional[int] = None,
        voice_id: str = "vi-VN-NamMinhNeural",
        voice_speed: float = 1.05,
        bgm_theme: str = "battle_tension_percussion",
    ) -> str:
        """
        Convenience method to construct ScriptInput and dispatch execution.
        """
        cleaned = raw_script_text.strip()
        if not cleaned:
            raise ValueError("Kịch bản không được để trống!")
        if len(cleaned) < 10:
            raise ValueError("Kịch bản phải chứa ít nhất 10 ký tự!")

        source_channel = SourceChannel.TELEGRAM_BOT if source == JobSource.TELEGRAM else SourceChannel.WEB_UI
        tg_meta = TelegramMeta(chat_id=telegram_chat_id) if telegram_chat_id else None

        script_input = ScriptInput(
            raw_script_text=cleaned,
            title=project_name.strip() or "Dark Myth Video",
            source_channel=source_channel,
            voice_id=voice_id,
            voice_speed=voice_speed,
            telegram_meta=tg_meta,
            render_config=RenderConfig(bgm_theme=bgm_theme),
        )

        return self.submit_script_input(script_input)

    def _execute_job(
        self,
        script_input: ScriptInput,
        on_complete: Optional[Callable[[RenderResult], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> None:
        """Worker thread entry point executing the pipeline orchestrator."""
        job_id = script_input.job_id
        self.log_message(job_id, "Bắt đầu luồng xử lý sản xuất video...")

        try:
            if job_id in self._cancelled_jobs:
                self.log_message(job_id, "Tác vụ đã bị hủy trước khi chạy.")
                try:
                    rec = self.task_manager.load_job(job_id)
                    if rec.status != JobStatus.FAILED:
                        self.task_manager.mark_failed(job_id, "Tác vụ đã bị người dùng hủy.")
                except Exception:
                    pass
                return

            result = self.orchestrator.run(script_input)

            self.log_message(
                job_id,
                f"Sản xuất thành công! File: {result.output_video_path} "
                f"({result.technical_metadata.file_size_bytes / (1024 * 1024):.2f} MB, {result.technical_metadata.duration_sec:.2f}s)"
            )
            updated_record = self.task_manager.load_job(job_id)
            self._notify(updated_record)

            if on_complete:
                on_complete(result)

        except Exception as exc:
            self.log_message(job_id, f"LỖI: {str(exc)}")
            logger.exception(f"Job {job_id} encountered an exception: {exc}")
            try:
                self.task_manager.mark_failed(job_id, str(exc))
            except Exception:
                pass
            updated_record = self.task_manager.load_job(job_id)
            self._notify(updated_record)

            if on_error:
                on_error(exc)

        finally:
            self._active_futures.pop(job_id, None)

    def cancel_job(self, job_id: str) -> bool:
        """Attempts to cancel a running or queued job."""
        self._cancelled_jobs.add(job_id)
        future = self._active_futures.get(job_id)
        if future and not future.done():
            cancelled = future.cancel()
            self.log_message(job_id, "Đã gửi tín hiệu hủy tác vụ.")
            try:
                self.task_manager.mark_failed(job_id, "Tác vụ đã bị người dùng hủy.")
            except Exception:
                pass
            return True
        return False

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        """Fetch job state from TaskManager."""
        try:
            return self.task_manager.load_job(job_id)
        except Exception:
            return None

    def list_history(self, limit: int = 20) -> list[JobRecord]:
        """Returns list of past jobs sorted in reverse chronological order."""
        jobs = self.task_manager.list_jobs()
        # Sort by updated_at or created_at descending
        jobs.sort(key=lambda j: j.updated_at, reverse=True)
        return jobs[:limit]

    def get_video_path(self, job_id: str) -> Optional[Path]:
        """Returns verified Path to the output video if completed and exists."""
        job = self.get_job(job_id)
        if not job or job.status != JobStatus.COMPLETED or not job.output_video_path:
            return None
        p = Path(job.output_video_path)
        if p.exists() and p.stat().st_size > 0:
            return p
        return None


def get_job_service() -> JobService:
    """Singleton getter for JobService."""
    return JobService()
