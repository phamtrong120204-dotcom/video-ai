"""Unit Tests for TaskManager Job Lifecycle, State Transitions, and JSON Persistence."""

import pytest

from app.core.exceptions import JobStateTransitionError
from app.core.task_manager import TaskManager
from app.schemas.job_schema import JobSource, JobStatus
from app.schemas.script_schema import ScriptInput


def test_task_manager_create_and_persist_job(
    task_manager: TaskManager,
    sample_script_input: ScriptInput,
) -> None:
    """Verify TaskManager creates a queued job, writes its JSON file, and pops it in FIFO order."""
    record = task_manager.create_job(sample_script_input)
    assert record.job_id == sample_script_input.job_id
    assert record.status == JobStatus.QUEUED
    assert record.progress_percent == 0

    json_file = task_manager.jobs_dir / f"{record.job_id}.json"
    assert json_file.exists()

    dequeued = task_manager.pop_next_queued_job()
    assert dequeued is not None
    assert dequeued.job_id == record.job_id
    assert task_manager.pop_next_queued_job() is None


def test_task_manager_full_happy_path_transitions(task_manager: TaskManager) -> None:
    """Verify valid state transitions from queued -> parsing -> generating_audio -> rendering_animation -> compositing -> completed."""
    record = task_manager.create_job(job_id="job_happy_01", source=JobSource.WEB)

    task_manager.transition_status(record.job_id, JobStatus.PARSING, progress_percent=12)
    task_manager.transition_status(record.job_id, JobStatus.GENERATING_AUDIO, progress_percent=30, total_scenes=3)
    task_manager.transition_status(
        record.job_id,
        JobStatus.RENDERING_ANIMATION,
        progress_percent=65,
        completed_scenes=2,
    )
    task_manager.transition_status(record.job_id, JobStatus.COMPOSITING, progress_percent=90)
    final_record = task_manager.mark_completed(record.job_id, output_video_path="out/job_happy_01.mp4")

    assert final_record.status == JobStatus.COMPLETED
    assert final_record.progress_percent == 100
    assert final_record.output_video_path == "out/job_happy_01.mp4"


def test_task_manager_blocks_illegal_state_jump(task_manager: TaskManager) -> None:
    """Verify TaskManager prevents skipping required stages (e.g. queued directly to compositing)."""
    record = task_manager.create_job(job_id="job_illegal_01", source=JobSource.TELEGRAM)

    with pytest.raises(JobStateTransitionError):
        task_manager.transition_status(record.job_id, JobStatus.COMPOSITING)


def test_task_manager_handles_job_failure_cleanly(task_manager: TaskManager) -> None:
    """Verify TaskManager transitions an active job to FAILED and prevents further transitions after failure."""
    record = task_manager.create_job(job_id="job_fail_01", source=JobSource.WEB)
    task_manager.transition_status(record.job_id, JobStatus.PARSING)

    failed = task_manager.mark_failed(record.job_id, error_message="Lỗi phân tách kịch bản thử nghiệm")
    assert failed.status == JobStatus.FAILED
    assert failed.error_message == "Lỗi phân tách kịch bản thử nghiệm"

    # Terminal jobs cannot transition back to active states
    with pytest.raises(JobStateTransitionError):
        task_manager.transition_status(record.job_id, JobStatus.GENERATING_AUDIO)
