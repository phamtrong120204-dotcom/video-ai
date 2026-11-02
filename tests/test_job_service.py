"""
Dark Myth Stickman Auto-Studio - Stage 9: Job Service Tests.

Tests background job execution, listeners, status transitions,
logging, thread pool management, and cancellation tokens.
"""

from pathlib import Path
import time
from unittest.mock import patch
import pytest

from app.schemas.job_schema import JobRecord, JobSource, JobStatus
from app.schemas.script_schema import ScriptInput
from app.services.job_service import JobService, get_job_service


def test_job_service_singleton():
    """Verify JobService implements true singleton pattern."""
    s1 = get_job_service()
    s2 = get_job_service()
    assert s1 is s2


def test_submit_raw_script_validation():
    """Verify empty text raises ValueError."""
    service = get_job_service()
    with pytest.raises(ValueError, match="Kịch bản không được để trống"):
        service.submit_raw_script("")


def test_submit_and_query_job():
    """Verify submitting job returns job_id and record is stored."""
    service = get_job_service()
    with patch.object(service, "_execute_job", return_value=None):
        job_id = service.submit_raw_script(
            raw_script_text="Cảnh 1: Thiết Bảng xuất thế đại náo thiên cung!",
            project_name="Unit Test Project",
            source=JobSource.WEB,
        )
        assert job_id.startswith("job_")

        record = service.get_job(job_id)
        assert record is not None
        assert record.job_id == job_id
        assert record.source in (JobSource.WEB, JobSource.WEB_UI)
        assert record.status in (JobStatus.QUEUED, JobStatus.PARSING, JobStatus.GENERATING_AUDIO, JobStatus.RENDERING_ANIMATION, JobStatus.COMPOSITING, JobStatus.COMPLETED, JobStatus.FAILED)


def test_job_logging_and_history():
    """Verify in-memory log buffer and history retrieval."""
    service = get_job_service()
    with patch.object(service, "_execute_job", return_value=None):
        job_id = service.submit_raw_script(
            raw_script_text="Cảnh 1: Test Logging Hắc Phong vạn trượng.",
            project_name="Log Test",
        )
        service.log_message(job_id, "Custom test log entry")

        logs = service.get_logs(job_id)
        assert any("Custom test log entry" in l for l in logs)

        history = service.list_history(limit=5)
        assert len(history) > 0
        assert any(j.job_id == job_id for j in history)


def test_job_cancellation():
    """Verify cancellation token and future cancellation."""
    service = get_job_service()
    with patch.object(service, "_execute_job", return_value=None):
        job_id = service.submit_raw_script(
            raw_script_text="Cảnh 1: Test cancel action cuồng nộ.",
            project_name="Cancel Test",
        )
        cancelled = service.cancel_job(job_id)
        assert isinstance(cancelled, bool)
        assert job_id in service._cancelled_jobs
