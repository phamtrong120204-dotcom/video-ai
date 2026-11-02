"""
Dark Myth Stickman Auto-Studio - Unified Application Entry Point.

Usage:
    python app/main.py --studio   # Run Local Studio Web UI (Gradio)
    python app/main.py --bot      # Run Telegram Bot (Long polling)
    python app/main.py --all      # Run both Studio and Telegram Bot in parallel
"""

import argparse
from pathlib import Path
import shutil
import sys
import threading
import time

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.bot.telegram_bot import DarkMythTelegramBot
from app.core.config import get_config
from app.core.logger import get_logger
from app.ui.studio_app import launch_studio

logger = get_logger("main")


def run_preflight_checks() -> bool:
    """Validates local environment, directories, FFmpeg, and Python runtime."""
    print("=" * 65)
    print("  DARK MYTH STICKMAN AUTO-STUDIO | KIỂM TRA MÔI TRƯỜNG")
    print("=" * 65)

    all_ok = True
    cfg = get_config()

    # 1. Python version check
    py_ver = sys.version_info
    print(f"[*] Python Runtime: {py_ver.major}.{py_ver.minor}.{py_ver.micro} ... OK")

    # 2. Check Directories
    for d in (cfg.in_dir, cfg.out_dir, cfg.jobs_dir, cfg.temp_dir, cfg.assets_dir):
        d.mkdir(parents=True, exist_ok=True)
    print(f"[*] Thư mục dự án (in, out, jobs, temp, assets) ... OK")

    # 3. Check FFmpeg and FFprobe
    ffmpeg_ok = bool(shutil.which(cfg.ffmpeg_path or "ffmpeg") or Path(r"C:\ffmpeg\bin\ffmpeg.exe").exists())
    ffprobe_ok = bool(shutil.which(cfg.ffprobe_path or "ffprobe") or Path(r"C:\ffmpeg\bin\ffprobe.exe").exists())

    if ffmpeg_ok:
        print(f"[*] FFmpeg Binary ... OK ({cfg.ffmpeg_path or 'C:/ffmpeg/bin/ffmpeg.exe'})")
    else:
        print(f"[!] CẢNH BÁO: Không tìm thấy FFmpeg binary.")
        all_ok = False

    if ffprobe_ok:
        print(f"[*] FFprobe Binary ... OK ({cfg.ffprobe_path or 'C:/ffmpeg/bin/ffprobe.exe'})")
    else:
        print(f"[!] CẢNH BÁO: Không tìm thấy FFprobe binary.")
        all_ok = False

    # 4. Check Telegram Bot Token
    if cfg.telegram_bot_token:
        print(f"[*] Telegram Bot Token: Đã cấu hình (******)")
    else:
        print(f"[-] Telegram Bot Token: Chưa điền trong .env (Bot sẽ chạy ở chế độ Standby)")

    print("=" * 65 + "\n")
    return all_ok


def start_studio_service(port: int = 7860, inbrowser: bool = True) -> None:
    """Launches Gradio Studio."""
    launch_studio(port=port, inbrowser=inbrowser)


def start_bot_service() -> None:
    """Launches Telegram Bot."""
    bot = DarkMythTelegramBot()
    if not bot.token:
        print("[!] Không thể khởi động Telegram Bot vì TELEGRAM_BOT_TOKEN chưa có trong .env.")
        print("    Vui lòng sao chép .env.example sang .env và điền mã token BotFather.")
        return
    bot.run_polling()


def main():
    parser = argparse.ArgumentParser(description="Dark Myth Stickman Auto-Studio Launcher")
    parser.add_argument("--studio", action="store_true", help="Launch Gradio Local Studio Web UI")
    parser.add_argument("--bot", action="store_true", help="Launch Telegram Bot (Long polling)")
    parser.add_argument("--all", action="store_true", help="Launch both Studio and Telegram Bot")
    parser.add_argument("--port", type=int, default=7860, help="Gradio Studio Port (default: 7860)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")

    args = parser.parse_args()

    # Default to studio if no mode flag specified
    if not (args.studio or args.bot or args.all):
        args.studio = True

    run_preflight_checks()

    if args.all:
        print("[*] Starting both Local Studio and Telegram Bot...")
        bot_thread = threading.Thread(target=start_bot_service, daemon=True, name="TelegramBotThread")
        bot_thread.start()
        start_studio_service(port=args.port, inbrowser=not args.no_browser)

    elif args.bot:
        start_bot_service()

    elif args.studio:
        start_studio_service(port=args.port, inbrowser=not args.no_browser)


if __name__ == "__main__":
    main()
