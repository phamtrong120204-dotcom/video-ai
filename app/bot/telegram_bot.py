"""
Dark Myth Stickman Auto-Studio - Telegram Bot Integration.

Provides Telegram control of the local Dark Myth video production pipeline:
- Commands: /start, /help, /status, /generate, /progress, /history, /download, /cancel
- Document upload (.txt, .json)
- Strict access control via TELEGRAM_ALLOWED_USERS whitelist
- Path traversal defense & safe error masking
- Shares the exact same JobService & TaskManager as Gradio Web UI
- Long-polling architecture optimized for local machine execution (0-cost)
"""

import asyncio
from datetime import datetime
import json
import logging
from pathlib import Path
import re
from typing import Optional

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.core.config import get_config
from app.core.logger import get_logger
from app.schemas.job_schema import JobRecord, JobSource, JobStatus
from app.schemas.script_schema import ScriptInput
from app.services.job_service import JobService, get_job_service

logger = get_logger("bot.telegram_bot")


class DarkMythTelegramBot:
    """
    Long-polling Telegram Bot controller for Dark Myth Auto-Studio.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        allowed_users: Optional[list[int]] = None,
        job_service: Optional[JobService] = None,
    ) -> None:
        cfg = get_config()
        self.token = token or cfg.telegram_bot_token or ""
        self.job_service = job_service or get_job_service()

        # Parse allowed users from config if not passed
        if allowed_users is not None:
            self.allowed_users = set(allowed_users)
        elif cfg.telegram_allowed_users:
            try:
                self.allowed_users = {
                    int(uid.strip())
                    for uid in cfg.telegram_allowed_users.split(",")
                    if uid.strip().isdigit()
                }
            except Exception:
                self.allowed_users = set()
        else:
            self.allowed_users = set()

        self.last_user_job: dict[int, str] = {}
        self.application: Optional[Application] = None

    @property
    def is_standby(self) -> bool:
        """Indicates whether bot is in Safe Standby mode (no token configured)."""
        return not bool(self.token)

    def is_authorized(self, user_id: int) -> bool:
        """Enforces access control whitelist. If allowed_users is empty, allows all."""
        if not self.allowed_users:
            return True
        return user_id in self.allowed_users

    # ----------------------------------------------------
    # COMMAND HANDLERS
    # ----------------------------------------------------
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /start command."""
        user = update.effective_user
        if not user or not self.is_authorized(user.id):
            await update.message.reply_text("⛔ Quyền truy cập bị từ chối. Bạn không nằm trong danh sách được phép.")
            return

        msg = (
            f"⚔️ **Chào mừng {user.first_name} đến với Dark Myth Auto-Studio!** ⚔️\n\n"
            "Xưởng sản xuất video hoạt hình người que Hắc Ám Tây Du (1080x1920 9:16) hoàn toàn tự động.\n\n"
            "📌 **Các lệnh chính:**\n"
            "• `/generate <kịch bản>` : Bắt đầu tạo video ngay\n"
            "• `/progress` : Xem tiến độ tác vụ đang thực thi\n"
            "• `/history` : Xem danh sách video đã render\n"
            "• `/download <job_id>` : Nhận file video MP4 trực tiếp\n"
            "• `/status` : Kiểm tra tình trạng máy chủ\n"
            "• `/cancel` : Hủy tác vụ đang chạy\n"
            "• `/help` : Hướng dẫn chi tiết\n\n"
            "💡 *Mẹo: Bạn có thể gửi file kịch bản `.txt` hoặc `.json` trực tiếp vào đây.*"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /help command."""
        user = update.effective_user
        if not user or not self.is_authorized(user.id):
            return

        msg = (
            "📖 **HƯỚNG DẪN ĐIỀU KHIỂN DARK MYTH STUDIO:**\n\n"
            "1. **Tạo video bằng văn bản:**\n"
            "`/generate Cảnh 1: Tôn Ngộ Không rút Thiết Bảng Như Ý đại náo thiên cung!`\n\n"
            "2. **Tạo video bằng tệp tin:**\n"
            "Kéo thả tệp `.txt` hoặc `.json` kịch bản phân cảnh vào khung chat.\n\n"
            "3. **Theo dõi tiến độ:**\n"
            "Gõ `/progress` để xem thanh tiến độ từ 0% đến 100% kèm bước thực thi.\n\n"
            "4. **Tải sản phẩm:**\n"
            "Sau khi hoàn tất, bot sẽ tự động gửi video, hoặc bạn dùng lệnh `/download <job_id>` để tải lại bất cứ lúc nào."
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /status command."""
        user = update.effective_user
        if not user or not self.is_authorized(user.id):
            return

        recent_jobs = self.job_service.list_history(limit=5)
        active_count = sum(1 for j in recent_jobs if j.status not in (JobStatus.COMPLETED, JobStatus.FAILED))

        msg = (
            "🛡️ **TRẠNG THÁI HỆ THỐNG:**\n\n"
            f"• **Máy chủ:** Đang hoạt động (Localhost)\n"
            f"• **Tác vụ đang chạy:** `{active_count}`\n"
            f"• **Tổng số sản phẩm:** `{len(recent_jobs)}` gần nhất\n"
            f"• **Quy chuẩn đầu ra:** `1080x1920 (9:16), 30 FPS, H.264 + AAC`\n"
            f"• **Âm thanh:** `Edge-TTS (vi-VN) + SFX + BGM Ducking`"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    async def cmd_generate(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /generate <script_text>."""
        user = update.effective_user
        if not user or not self.is_authorized(user.id):
            await update.message.reply_text("⛔ Bạn không có quyền thực hiện lệnh này.")
            return

        text = " ".join(context.args) if context.args else ""
        if not text.strip():
            await update.message.reply_text(
                "⚠️ Vui lòng nhập kịch bản sau lệnh `/generate`!\n"
                "Ví dụ: `/generate Cảnh 1: Hắc Phong vạn trượng, Tề Thiên giáng thế!`"
            )
            return

        chat_id = update.effective_chat.id
        try:
            job_id = self.job_service.submit_raw_script(
                raw_script_text=text.strip(),
                project_name=f"Telegram Job @{user.username or user.first_name}",
                source=JobSource.TELEGRAM,
                telegram_user_id=user.id,
                telegram_chat_id=chat_id,
            )
            self.last_user_job[user.id] = job_id

            await update.message.reply_text(
                f"🚀 **Đã khởi tạo tác vụ thành công!**\n\n"
                f"• **Job ID:** `{job_id}`\n"
                f"• **Trạng thái:** `Đang xử lý (0%)`\n\n"
                "Gõ `/progress` để xem tiến độ hoặc đợi bot gửi video khi hoàn thành.",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as exc:
            logger.error(f"Telegram generate error: {exc}")
            await update.message.reply_text(f"❌ Lỗi khởi tạo tác vụ: {str(exc)}")

    async def cmd_progress(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /progress [job_id]."""
        user = update.effective_user
        if not user or not self.is_authorized(user.id):
            return

        job_id = context.args[0] if context.args else self.last_user_job.get(user.id)
        if not job_id:
            await update.message.reply_text("⚠️ Chưa có tác vụ nào gần đây. Hãy dùng `/generate` để tạo mới.")
            return

        job = self.job_service.get_job(job_id)
        if not job:
            await update.message.reply_text(f"❌ Không tìm thấy thông tin tác vụ `{job_id}`.")
            return

        progress_bar_blocks = int(job.progress_percent / 10)
        bar = "█" * progress_bar_blocks + "░" * (10 - progress_bar_blocks)

        msg = (
            f"📊 **TIẾN ĐỘ TÁC VỤ:** `{job.job_id}`\n\n"
            f"• **Trạng thái:** `{job.status.value.upper()}`\n"
            f"• **Tiến độ:** `[{bar}] {job.progress_percent}%`\n"
            f"• **Bước hiện tại:** {job.current_step_message}\n"
        )
        if job.status == JobStatus.COMPLETED:
            msg += "\n✅ *Video đã hoàn thành! Dùng `/download` để tải về.*"
        elif job.status == JobStatus.FAILED:
            msg += f"\n❌ *Lỗi:* {job.error_message}"

        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    async def cmd_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /history command."""
        user = update.effective_user
        if not user or not self.is_authorized(user.id):
            return

        jobs = self.job_service.list_history(limit=8)
        if not jobs:
            await update.message.reply_text("Chưa có lịch sử tác vụ nào.")
            return

        lines = ["📜 **DANH SÁCH TÁC VỤ GẦN ĐÂY:**\n"]
        for j in jobs:
            status_icon = "✅" if j.status == JobStatus.COMPLETED else ("❌" if j.status == JobStatus.FAILED else "⏳")
            file_name = Path(j.output_video_path).name if j.output_video_path else "chưa có"
            lines.append(
                f"{status_icon} `{j.job_id}` | `{j.status.value}` ({j.progress_percent}%)\n"
                f"   📁 File: `{file_name}`\n"
            )

        lines.append("💡 *Dùng `/download <job_id>` để nhận video.*")
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

    async def cmd_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /download <job_id>."""
        user = update.effective_user
        if not user or not self.is_authorized(user.id):
            return

        job_id = context.args[0] if context.args else self.last_user_job.get(user.id)
        if not job_id:
            await update.message.reply_text("⚠️ Vui lòng chỉ định mã tác vụ: `/download <job_id>`")
            return

        # Security: sanitize job_id against path traversal
        clean_job_id = re.sub(r"[^a-zA-Z0-9_\-]", "", job_id)
        video_path = self.job_service.get_video_path(clean_job_id)

        if not video_path or not video_path.exists():
            await update.message.reply_text(f"❌ Không tìm thấy video hoàn chỉnh cho tác vụ `{clean_job_id}`.")
            return

        # Check file size (Telegram bot API max direct upload is 50MB)
        file_size_mb = video_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 49.0:
            await update.message.reply_text(
                f"⚠️ File video quá lớn ({file_size_mb:.1f} MB, giới hạn bot là 50MB).\n"
                f"Vui lòng tải trực tiếp từ máy tại đường dẫn: `{video_path}`"
            )
            return

        await update.message.reply_text(f"📤 Đang gửi video `{video_path.name}` ({file_size_mb:.2f} MB)...")
        try:
            with open(video_path, "rb") as vf:
                await update.message.reply_video(
                    video=vf,
                    caption=f"⚔️ Dark Myth Video - `{clean_job_id}`\n1080x1920 30FPS H.264",
                    supports_streaming=True,
                )
        except Exception as exc:
            logger.error(f"Failed to send video via Telegram: {exc}")
            await update.message.reply_text(f"❌ Lỗi gửi file: {exc}")

    async def cmd_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /cancel [job_id]."""
        user = update.effective_user
        if not user or not self.is_authorized(user.id):
            return

        job_id = context.args[0] if context.args else self.last_user_job.get(user.id)
        if not job_id:
            await update.message.reply_text("⚠️ Không tìm thấy tác vụ nào để hủy.")
            return

        clean_job_id = re.sub(r"[^a-zA-Z0-9_\-]", "", job_id)
        success = self.job_service.cancel_job(clean_job_id)
        if success:
            await update.message.reply_text(f"⏹️ Đã hủy tác vụ `{clean_job_id}` thành công.")
        else:
            await update.message.reply_text(f"⚠️ Không thể hủy tác vụ `{clean_job_id}` (có thể đã kết thúc hoặc không tồn tại).")

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handles document uploads (.txt or .json)."""
        user = update.effective_user
        if not user or not self.is_authorized(user.id):
            return

        doc = update.message.document
        if not doc:
            return

        file_name = doc.file_name or "script.txt"
        ext = Path(file_name).suffix.lower()
        if ext not in (".txt", ".json"):
            await update.message.reply_text("⚠️ Bot chỉ hỗ trợ file kịch bản định dạng `.txt` hoặc `.json`.")
            return

        # Max file size limit: 1MB
        if doc.file_size and doc.file_size > 1024 * 1024:
            await update.message.reply_text("⚠️ Dung lượng file kịch bản vượt quá 1MB.")
            return

        await update.message.reply_text(f"📥 Đang nhận file `{file_name}`...")
        try:
            tg_file = await context.bot.get_file(doc.file_id)
            file_bytes = await tg_file.download_as_bytearray()
            text_content = file_bytes.decode("utf-8")

            job_id = self.job_service.submit_raw_script(
                raw_script_text=text_content,
                project_name=f"Upload: {file_name}",
                source=JobSource.TELEGRAM,
                telegram_user_id=user.id,
                telegram_chat_id=update.effective_chat.id,
            )
            self.last_user_job[user.id] = job_id

            await update.message.reply_text(
                f"🚀 **Đã khởi tạo tác vụ từ file `{file_name}`!**\n\n"
                f"• **Job ID:** `{job_id}`\n"
                f"• **Trạng thái:** `Đang xử lý`\n\n"
                "Gõ `/progress` để theo dõi tiến độ.",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as exc:
            logger.error(f"Error handling document: {exc}")
            await update.message.reply_text(f"❌ Lỗi xử lý file kịch bản: {exc}")

    # ----------------------------------------------------
    # BOT RUNNER
    # ----------------------------------------------------
    def build_application(self) -> Application:
        """Builds Telegram Application with all registered handlers."""
        if not self.token:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN chưa được cấu hình! "
                "Vui lòng điền token vào tệp .env (xem .env.example)."
            )

        app = Application.builder().token(self.token).build()

        app.add_handler(CommandHandler("start", self.cmd_start))
        app.add_handler(CommandHandler("help", self.cmd_help))
        app.add_handler(CommandHandler("status", self.cmd_status))
        app.add_handler(CommandHandler("generate", self.cmd_generate))
        app.add_handler(CommandHandler("progress", self.cmd_progress))
        app.add_handler(CommandHandler("history", self.cmd_history))
        app.add_handler(CommandHandler("download", self.cmd_download))
        app.add_handler(CommandHandler("cancel", self.cmd_cancel))
        app.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))

        self.application = app
        return app

    def run_polling(self) -> None:
        """Starts long polling in the current process."""
        print("[*] Starting Dark Myth Telegram Bot (Long Polling)...")
        app = self.build_application()
        app.run_polling()


def start_telegram_bot() -> None:
    """Entry point to launch the Telegram bot."""
    bot = DarkMythTelegramBot()
    if not bot.token:
        print("[!] CẢNH BÁO: TELEGRAM_BOT_TOKEN chưa được điền trong .env.")
        print("    Vui lòng mở .env và điền TELEGRAM_BOT_TOKEN=<your_token_from_BotFather>.")
        return
    bot.run_polling()


if __name__ == "__main__":
    start_telegram_bot()
