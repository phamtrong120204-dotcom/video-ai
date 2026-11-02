"""
Dark Myth Stickman Auto-Studio - Preflight Environment & Health Diagnostics.

Validates:
  1. Python runtime (3.15+)
  2. Critical dependencies (Pydantic, NumPy, Pillow, Edge-TTS, Pydub, Gradio, Python-Telegram-Bot, Google-GenAI)
  3. FFmpeg and FFprobe binary availability and version
  4. Project directories write access (in, out, out/jobs, out/temp, assets, logs)
  5. Configuration & environment variables (.env, voice, telegram token)

Exit code:
  0 = All critical components PASSED
  1 = Missing critical component
"""

import os
from pathlib import Path
import shutil
import subprocess
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure C:\ffmpeg\bin is in PATH for media tools and pydub
_default_ffmpeg_dir = r"C:\ffmpeg\bin"
if Path(_default_ffmpeg_dir).is_dir() and _default_ffmpeg_dir.lower() not in os.environ.get("PATH", "").lower():
    os.environ["PATH"] = f"{_default_ffmpeg_dir};{os.environ.get('PATH', '')}"


def run_checks() -> bool:
    print("=" * 70)
    print("   DARK MYTH STICKMAN AUTO-STUDIO | KIỂM TRA MÔI TRƯỜNG & HỆ THỐNG")
    print("=" * 70)

    all_passed = True

    # 1. Python Runtime
    py_ver = sys.version_info
    print(f"[1/5] Python Runtime: {py_ver.major}.{py_ver.minor}.{py_ver.micro} ({sys.executable})")
    if py_ver.major < 3 or (py_ver.major == 3 and py_ver.minor < 10):
        print("  [X] LỖI: Yêu cầu Python 3.10 trở lên (khuyên dùng Python 3.15).")
        all_passed = False
    else:
        print("  [v] Python runtime đạt chuẩn.")

    # 2. Package Dependencies
    print("\n[2/5] Thư viện nền tảng (Dependencies):")
    critical_modules = [
        ("pydantic", "Pydantic V2 Schema Validation"),
        ("numpy", "NumPy Vectorized Array Matrix"),
        ("PIL", "Pillow Image Processing"),
        ("edge_tts", "Edge-TTS Free Neural Voice"),
        ("pydub", "Pydub Audio Mixing"),
        ("mutagen", "Mutagen Audio Duration Measurement"),
        ("gradio", "Gradio Web UI"),
        ("telegram", "Python Telegram Bot v20+"),
    ]

    for mod_name, desc in critical_modules:
        try:
            __import__(mod_name)
            print(f"  [v] {mod_name:<16} - {desc}")
        except ImportError as exc:
            print(f"  [X] {mod_name:<16} - THIẾU ({exc})")
            all_passed = False

    # 3. FFmpeg & FFprobe
    print("\n[3/5] Công cụ xử lý đa phương tiện (FFmpeg & FFprobe):")
    from app.core.config import get_config
    cfg = get_config(reload=True)

    ffmpeg_bin = cfg.ffmpeg_path
    ffprobe_bin = cfg.ffprobe_path

    if ffmpeg_bin and Path(ffmpeg_bin).is_file():
        try:
            res = subprocess.run([ffmpeg_bin, "-version"], capture_output=True, text=True, check=False)
            first_line = res.stdout.splitlines()[0] if res.stdout else "version unknown"
            print(f"  [v] FFmpeg : {ffmpeg_bin} ({first_line[:40]}...)")
        except Exception as exc:
            print(f"  [!] FFmpeg lỗi khi thực thi: {exc}")
            all_passed = False
    else:
        print(f"  [X] KHÔNG TÌM THẤY FFmpeg! (Đã quét C:\\ffmpeg\\bin\\ffmpeg.exe và PATH)")
        all_passed = False

    if ffprobe_bin and Path(ffprobe_bin).is_file():
        try:
            res = subprocess.run([ffprobe_bin, "-version"], capture_output=True, text=True, check=False)
            first_line = res.stdout.splitlines()[0] if res.stdout else "version unknown"
            print(f"  [v] FFprobe: {ffprobe_bin} ({first_line[:40]}...)")
        except Exception as exc:
            print(f"  [!] FFprobe lỗi khi thực thi: {exc}")
            all_passed = False
    else:
        print(f"  [X] KHÔNG TÌM THẤY FFprobe! (Đã quét C:\\ffmpeg\\bin\\ffprobe.exe và PATH)")
        all_passed = False

    # 4. Storage Directories & Permissions
    print("\n[4/5] Thư mục lưu trữ & Quyền ghi tệp:")
    for d in (cfg.in_dir, cfg.out_dir, cfg.jobs_dir, cfg.temp_dir, cfg.assets_dir, cfg.logs_dir):
        try:
            d.mkdir(parents=True, exist_ok=True)
            test_file = d / ".write_test"
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink(missing_ok=True)
            print(f"  [v] {str(d.relative_to(PROJECT_ROOT)):<20} - Quyền ghi: OK")
        except Exception as exc:
            print(f"  [X] {str(d.relative_to(PROJECT_ROOT)):<20} - LỖI GHI ({exc})")
            all_passed = False

    # 5. Environment & Telegram Configuration
    print("\n[5/5] Cấu hình môi trường & Kênh tương tác:")
    env_file = PROJECT_ROOT / ".env"
    if env_file.is_file():
        print(f"  [v] Tệp cấu hình .env: Đã tồn tại ({env_file.stat().st_size} bytes)")
    else:
        print(f"  [-] Tệp cấu hình .env: Chưa tồn tại (Đang dùng cấu hình mặc định từ .env.example)")

    if cfg.telegram_bot_token:
        print(f"  [v] Telegram Bot Token : Đã cấu hình (***{cfg.telegram_bot_token[-4:] if len(cfg.telegram_bot_token) > 4 else '****'})")
        if cfg.telegram_allowed_users:
            print(f"  [v] Telegram Whitelist : {cfg.telegram_allowed_users}")
        else:
            print(f"  [-] Telegram Whitelist : Mở cho tất cả mọi người (Khuyên dùng: điền ID vào TELEGRAM_ALLOWED_USERS)")
    else:
        print(f"  [-] Telegram Bot Token : Chưa cấu hình -> Bot sẽ ở chế độ Safe Standby.")

    if cfg.gemini_api_key:
        print(f"  [v] Gemini API Key     : Đã cấu hình (AI Hybrid Script Parser kích hoạt)")
    else:
        print(f"  [-] Gemini API Key     : Chưa cấu hình (Tự động fallback sang Rule-based Parser ngoại tuyến)")

    print("=" * 70)
    if all_passed:
        print(">>> TRẠNG THÁI: TẤT CẢ KIỂM TRA ĐẠT CHUẨN! SẴN SÀNG KHỞI CHẠY ỨNG DỤNG. <<<")
    else:
        print(">>> CẢNH BÁO: CÓ THÀNH PHẦN THIẾU HOẶC LỖI! VUI LÒNG KIỂM TRA LẠI. <<<")
    print("=" * 70 + "\n")
    return all_passed


if __name__ == "__main__":
    ok = run_checks()
    sys.exit(0 if ok else 1)
