"""Structured Logging System (Console + logs/app.log with job_id context)."""

import contextvars
import logging
import sys
from pathlib import Path
from typing import Optional

from app.core.config import get_config

_CURRENT_JOB_ID: contextvars.ContextVar[str] = contextvars.ContextVar("current_job_id", default="-")


def set_log_job_id(job_id: Optional[str]) -> contextvars.Token[str]:
    """Bind a job_id into the current execution context for log enrichment."""
    return _CURRENT_JOB_ID.set(job_id if job_id else "-")


def reset_log_job_id(token: contextvars.Token[str]) -> None:
    """Reset the contextvar job_id using its token."""
    _CURRENT_JOB_ID.reset(token)


class JobContextFilter(logging.Filter):
    """Injects `job_id` attribute into every LogRecord."""

    def __init__(self, explicit_job_id: Optional[str] = None) -> None:
        super().__init__()
        self.explicit_job_id = explicit_job_id

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "job_id") or not getattr(record, "job_id", None):
            record.job_id = self.explicit_job_id or _CURRENT_JOB_ID.get()
        return True


class JobLoggerAdapter(logging.LoggerAdapter):
    """LoggerAdapter that guarantees job_id is attached to every log message."""

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        extra = kwargs.setdefault("extra", {})
        if "job_id" not in extra:
            extra["job_id"] = self.extra.get("job_id") or _CURRENT_JOB_ID.get()
        return msg, kwargs


LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | [job=%(job_id)s] | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
) -> Path:
    """Configure root 'autostudio' logger with Console and File handlers."""
    cfg = get_config()
    target_log_file = log_file or (cfg.logs_dir / "app.log")
    target_log_file.parent.mkdir(parents=True, exist_ok=True)

    base_logger = logging.getLogger("autostudio")
    base_logger.setLevel(level)
    base_logger.propagate = False

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)
    job_filter = JobContextFilter()

    # Clear existing handlers to avoid duplicate entries when reconfigured in tests
    for handler in list(base_logger.handlers):
        base_logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(job_filter)

    file_handler = logging.FileHandler(target_log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(job_filter)

    base_logger.addHandler(console_handler)
    base_logger.addHandler(file_handler)

    return target_log_file


def get_logger(
    module_name: str,
    job_id: Optional[str] = None,
    log_file: Optional[Path] = None,
) -> JobLoggerAdapter:
    """Get a structured logger for a specific module with optional bound job_id."""
    base_logger = logging.getLogger("autostudio")
    if not base_logger.handlers or log_file is not None:
        setup_logging(log_file=log_file)

    full_name = module_name if module_name.startswith("autostudio") else f"autostudio.{module_name}"
    child_logger = logging.getLogger(full_name)
    child_logger.addFilter(JobContextFilter(explicit_job_id=job_id))
    return JobLoggerAdapter(child_logger, {"job_id": job_id})
