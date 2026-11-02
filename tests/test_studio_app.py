"""
Dark Myth Stickman Auto-Studio - Stage 9: Studio Web UI Tests.

Tests Gradio UI components, template loaders, file parsers,
job submission, status polling, cancellation, history, and health diagnostics.
"""

from pathlib import Path
import tempfile
from unittest.mock import patch
import pytest

from app.schemas.job_schema import JobRecord, JobSource, JobStatus
from app.services.job_service import get_job_service
from app.ui.studio_app import (
    SAMPLE_SCRIPTS,
    build_studio_ui,
    cancel_current_job,
    get_history_table,
    get_system_health,
    load_template,
    poll_job_status,
    read_uploaded_file,
    submit_creation_job,
)


def test_load_template():
    """Verify script templates are loaded accurately."""
    tmpl_name = "Đại Chiến Thiên Cung (Tôn Ngộ Không vs Dương Tiễn)"
    text = load_template(tmpl_name)
    assert "Thiết Bảng Như Ý" in text
    assert "Nhị Lang Thần" in text

    unknown = load_template("Unknown Template")
    assert unknown == ""


def test_read_uploaded_file_txt():
    """Verify .txt script file reading."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
        f.write("Cảnh 1: Khói đen cuồn cuộn.\nCảnh 2: Thiết Bảng xuất thế!")
        tmp_path = Path(f.name)

    try:
        content = read_uploaded_file(tmp_path)
        assert "Khói đen cuồn cuộn" in content
        assert "Thiết Bảng xuất thế" in content
    finally:
        tmp_path.unlink(missing_ok=True)


def test_read_uploaded_file_json():
    """Verify .json script file reading."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as f:
        f.write('{"raw_text": "Cảnh 1: Phật chưởng trấn áp yêu ma."}')
        tmp_path = Path(f.name)

    try:
        content = read_uploaded_file(tmp_path)
        assert "Phật chưởng trấn áp yêu ma" in content
    finally:
        tmp_path.unlink(missing_ok=True)


def test_submit_creation_job_validation_error():
    """Verify empty script triggers clear user validation error."""
    job_id, status_html, prog, step, logs, video, dl = submit_creation_job(
        project_name="Test",
        script_text="   ",
        skin="dark_wukong",
        weapon="ruyi_staff",
        action_preset="heavy_charge_clash",
        voice_id="vi-VN-NamMinhNeural",
        voice_speed=1.05,
        bgm_theme="battle_tension_percussion",
    )
    assert job_id == ""
    assert "Vui lòng nhập nội dung kịch bản" in status_html
    assert prog == 0


def test_submit_creation_job_success():
    """Verify valid job submission dispatches job_id and queues task."""
    service = get_job_service()
    with patch.object(service, "_execute_job", return_value=None):
        job_id, status_html, prog, step, logs, video, dl = submit_creation_job(
            project_name="Gradio Test Run",
            script_text="Cảnh 1: Hắc Phong vạn trượng giáng thế!",
            skin="dark_wukong",
            weapon="ruyi_staff",
            action_preset="heavy_charge_clash",
            voice_id="vi-VN-NamMinhNeural",
            voice_speed=1.05,
            bgm_theme="battle_tension_percussion",
        )
        assert job_id.startswith("job_")
        assert "Đang xử lý" in status_html
        assert prog > 0


def test_poll_job_status_unknown_and_valid():
    """Verify poll_job_status handling for unknown vs existing jobs."""
    # Empty job_id
    html, prog, step, logs, vid, dl = poll_job_status("")
    assert "Sẵn sàng" in html

    # Unknown job_id
    html, prog, step, logs, vid, dl = poll_job_status("job_non_existent_999")
    assert "Không tìm thấy" in html

    # Existing job
    service = get_job_service()
    with patch.object(service, "_execute_job", return_value=None):
        job_id = service.submit_raw_script(
            raw_script_text="Cảnh 1: Tiên Đao trảm ma đại chiến thiên binh.",
            project_name="Poll Test",
        )
        html, prog, step, logs, vid, dl = poll_job_status(job_id)
        assert job_id in html or "QUEUED" in html or "PARSING" in html or "Đang" in html


def test_cancel_current_job():
    """Verify task cancellation helper."""
    assert "Không có tác vụ" in cancel_current_job("")
    service = get_job_service()
    with patch.object(service, "_execute_job", return_value=None):
        job_id = service.submit_raw_script(
            raw_script_text="Cảnh 1: Test cancel long running.",
            project_name="Cancel Test",
        )
        res = cancel_current_job(job_id)
        assert "Đã gửi tín hiệu" in res or "Không thể hủy" in res


def test_get_history_table():
    """Verify history table extraction."""
    rows = get_history_table()
    assert isinstance(rows, list)
    if rows:
        assert len(rows[0]) == 6


def test_get_system_health():
    """Verify diagnostic system health markdown output."""
    report = get_system_health()
    assert "BÁO CÁO TRẠNG THÁI HỆ THỐNG" in report
    assert "Python Version" in report
    assert "FFmpeg Binary" in report


def test_build_studio_ui_compilation():
    """Verify that build_studio_ui constructs complete Gradio Blocks without exception."""
    app = build_studio_ui()
    assert app is not None
    assert hasattr(app, "blocks")
