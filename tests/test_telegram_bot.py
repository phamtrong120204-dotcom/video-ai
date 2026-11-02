"""
Dark Myth Stickman Auto-Studio - Stage 9: Telegram Bot Tests.

Tests Telegram command handlers, authorization whitelist, document processing,
path traversal security, and shared job service integration using mock updates.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.bot.telegram_bot import DarkMythTelegramBot
from app.schemas.job_schema import JobRecord, JobSource, JobStatus
from app.services.job_service import get_job_service


@pytest.fixture
def mock_bot():
    """Instantiate DarkMythTelegramBot with mock token and allowed users."""
    bot = DarkMythTelegramBot(
        token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        allowed_users=[1001, 1002],
    )
    return bot


def test_telegram_authorization(mock_bot):
    """Verify whitelist access control."""
    assert mock_bot.is_authorized(1001) is True
    assert mock_bot.is_authorized(1002) is True
    assert mock_bot.is_authorized(9999) is False

    # Empty whitelist allows all
    open_bot = DarkMythTelegramBot(token="test", allowed_users=[])
    assert open_bot.is_authorized(9999) is True


@pytest.mark.asyncio
async def test_cmd_start_authorized(mock_bot):
    """Verify /start response for authorized user."""
    update = MagicMock()
    update.effective_user.id = 1001
    update.effective_user.first_name = "Quan"
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    await mock_bot.cmd_start(update, context)
    update.message.reply_text.assert_called_once()
    reply_text = update.message.reply_text.call_args[0][0]
    assert "Chào mừng Quan" in reply_text
    assert "/generate" in reply_text


@pytest.mark.asyncio
async def test_cmd_start_unauthorized(mock_bot):
    """Verify /start response for unauthorized user."""
    update = MagicMock()
    update.effective_user.id = 9999
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    await mock_bot.cmd_start(update, context)
    update.message.reply_text.assert_called_once()
    assert "từ chối" in update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_cmd_generate(mock_bot):
    """Verify /generate command dispatches job to JobService."""
    update = MagicMock()
    update.effective_user.id = 1001
    update.effective_user.first_name = "Quan"
    update.effective_user.username = "quan_tg"
    update.effective_chat.id = 5555
    update.message.reply_text = AsyncMock()

    context = MagicMock()
    context.args = ["Cảnh", "1:", "Thiết", "Bảng", "xuất", "thế!"]

    with patch.object(mock_bot.job_service, "submit_raw_script", return_value="job_tg_12345") as mock_submit:
        await mock_bot.cmd_generate(update, context)
        mock_submit.assert_called_once()
        update.message.reply_text.assert_called_once()
        reply_text = update.message.reply_text.call_args[0][0]
        assert "khởi tạo tác vụ thành công" in reply_text
        assert mock_bot.last_user_job.get(1001) == "job_tg_12345"


@pytest.mark.asyncio
async def test_cmd_progress(mock_bot):
    """Verify /progress retrieves correct job status."""
    service = get_job_service()
    job_record = service.task_manager.create_job(job_id="job_progress_test_1")
    service.task_manager.transition_status(
        job_id="job_progress_test_1",
        new_status=JobStatus.PARSING,
        progress_percent=20,
        step_message="Đang phân tích kịch bản...",
    )
    mock_bot.last_user_job[1001] = "job_progress_test_1"

    update = MagicMock()
    update.effective_user.id = 1001
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.args = ["job_progress_test_1"]

    await mock_bot.cmd_progress(update, context)
    update.message.reply_text.assert_called_once()
    reply_text = update.message.reply_text.call_args[0][0]
    assert "job_progress_test_1" in reply_text
    assert "TIẾN ĐỘ TÁC VỤ" in reply_text


@pytest.mark.asyncio
async def test_cmd_download_path_traversal_defense(mock_bot):
    """Verify /download protects against path traversal attempts."""
    update = MagicMock()
    update.effective_user.id = 1001
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.args = ["../../etc/passwd"]

    await mock_bot.cmd_download(update, context)
    update.message.reply_text.assert_called_once()
    assert "Không tìm thấy video hoàn chỉnh" in update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_cmd_cancel(mock_bot):
    """Verify /cancel stops a job."""
    service = get_job_service()
    job_record = service.task_manager.create_job(job_id="job_cancel_test_1")

    update = MagicMock()
    update.effective_user.id = 1001
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.args = ["job_cancel_test_1"]

    with patch.object(service, "cancel_job", return_value=True):
        await mock_bot.cmd_cancel(update, context)
        update.message.reply_text.assert_called_once()
        reply_text = update.message.reply_text.call_args[0][0]
        assert "Đã hủy tác vụ" in reply_text


@pytest.mark.asyncio
async def test_handle_document_invalid_extension(mock_bot):
    """Verify rejecting files with unsupported extensions."""
    update = MagicMock()
    update.effective_user.id = 1001
    update.message.document.file_name = "malicious.exe"
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    await mock_bot.handle_document(update, context)
    update.message.reply_text.assert_called_once()
    assert "chỉ hỗ trợ file kịch bản định dạng `.txt` hoặc `.json`" in update.message.reply_text.call_args[0][0]
