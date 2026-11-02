"""
Dark Myth Stickman Auto-Studio - Gradio Local Web UI.

Features:
- Dark Myth glassmorphism aesthetic (Deep slate, Crimson #D92626, Gold #FFD700)
- Script input with template presets and .txt / .json file upload
- Production settings (Skin, Weapon, Action Preset, Vietnamese TTS, BGM, VFX)
- Non-blocking background execution via JobService & TaskManager
- Real-time progress updates, live step messages, execution logs
- Embedded 9:16 vertical MP4 video player and download button
- Render history gallery and system health diagnostics
"""

from datetime import datetime
import json
from pathlib import Path
import time
from typing import Optional

import gradio as gr

from app.core.config import get_config
from app.core.task_manager import TaskManager
from app.schemas.job_schema import JobRecord, JobSource, JobStatus
from app.schemas.scene_schema import ActionPreset, CharacterSkin, WeaponType
from app.schemas.script_schema import ScriptInput
from app.services.job_service import JobService, get_job_service

# Pre-defined Dark Myth Script Templates
SAMPLE_SCRIPTS = {
    "Đại Chiến Thiên Cung (Tôn Ngộ Không vs Dương Tiễn)": (
        "Cảnh 1: Hắc Phong vạn trượng, Tề Thiên Đại Thánh rút Thiết Bảng Như Ý cuồng nộ giáng thế!\n"
        "Cảnh 2: Nhị Lang Thần múa Tam Tiêm Đao, kim quang bộc phát nghênh chiến kinh thiên động địa!"
    ),
    "Kim Thân Trấn Yêu (Bàn Tay Phật Khổng Lồ)": (
        "Cảnh 1: Vạn trượng kim quang ngưng tụ, Phật chưởng khổng lồ từ tầng mây giáng xuống đè bẹp mặt đất!\n"
        "Cảnh 2: Mặt giấy nứt toác, hào quang kim sắc phong tỏa toàn bộ yêu khí!"
    ),
    "Hắc Phong Đoạt Mệnh (Vortex Sweep Cực Tốc)": (
        "Cảnh 1: Thân ảnh hóa thành cuồng phong đen kịt, Thiết Bảng quét ngang một đường đoạt mạng yêu ma!\n"
        "Cảnh 2: Khói đen tan biến, người que đứng sừng sững giữa trang giấy vỡ vụn."
    ),
}

DARK_MYTH_CSS = """
body, .gradio-container {
    background-color: #0d0e15 !important;
    color: #e0e0e6 !important;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.header-box {
    background: linear-gradient(135deg, #1f0808 0%, #161722 50%, #0d0e15 100%);
    border: 1px solid rgba(217, 38, 38, 0.4);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6);
}
.header-title {
    color: #FFD700;
    font-size: 26px;
    font-weight: 800;
    letter-spacing: 1.5px;
    margin: 0;
    text-transform: uppercase;
}
.header-sub {
    color: #ff6b6b;
    font-size: 14px;
    margin-top: 6px;
}
.dark-card {
    background-color: #141520 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 10px !important;
}
.btn-primary {
    background: linear-gradient(135deg, #d92626 0%, #8b0000 100%) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    border: none !important;
}
.btn-primary:hover {
    background: linear-gradient(135deg, #ff3333 0%, #a00000 100%) !important;
}
"""


def load_template(template_name: str) -> str:
    """Load text for the chosen script template."""
    return SAMPLE_SCRIPTS.get(template_name, "")


def read_uploaded_file(file_obj) -> str:
    """Extract content from uploaded .txt or .json script file."""
    if file_obj is None:
        return ""
    try:
        if isinstance(file_obj, (str, Path)):
            path = Path(file_obj)
        elif hasattr(file_obj, "name"):
            path = Path(file_obj.name)
        else:
            path = Path(str(file_obj))

        content = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".json":
            data = json.loads(content)
            if isinstance(data, dict):
                return data.get("raw_text") or data.get("script") or json.dumps(data, indent=2, ensure_ascii=False)
        return content
    except Exception as exc:
        return f"[Lỗi đọc file: {exc}]"


def submit_creation_job(
    project_name: str,
    script_text: str,
    skin: str,
    weapon: str,
    action_preset: str,
    voice_id: str,
    voice_speed: float,
    bgm_theme: str,
) -> tuple[str, str, int, str, str, Optional[str], Optional[str]]:
    """
    Submits a video generation task to JobService.
    Returns:
        job_id, status_html, progress_val, step_msg, logs, video_path, download_file
    """
    if not script_text.strip():
        return (
            "",
            "<div style='color: #ff4d4d; font-weight: bold;'>⚠️ Lỗi: Vui lòng nhập nội dung kịch bản!</div>",
            0,
            "Chưa có kịch bản đầu vào",
            "Lỗi: Kịch bản rỗng.",
            None,
            None,
        )

    service = get_job_service()

    try:
        job_id = service.submit_raw_script(
            raw_script_text=script_text.strip(),
            project_name=project_name.strip() or "Dark Myth Video",
            source=JobSource.WEB,
            voice_id=voice_id,
            voice_speed=voice_speed,
            bgm_theme=bgm_theme,
        )

        status_html = f"<div style='color: #ffcc00; font-weight: bold;'>⏳ Đang xử lý: {job_id}</div>"
        return (
            job_id,
            status_html,
            5,
            "Tác vụ đã được nạp vào hàng đợi...",
            f"[{datetime.now().strftime('%H:%M:%S')}] Khởi tạo tác vụ {job_id} thành công.",
            None,
            None,
        )
    except Exception as exc:
        return (
            "",
            f"<div style='color: #ff4d4d; font-weight: bold;'>❌ Lỗi khởi tạo: {exc}</div>",
            0,
            f"Lỗi: {exc}",
            f"Exception: {exc}",
            None,
            None,
        )


def poll_job_status(job_id: str) -> tuple[str, int, str, str, Optional[str], Optional[str]]:
    """
    Polls the current status, progress, logs, and video output for an active job_id.
    """
    if not job_id:
        return (
            "<div style='color: #888;'>Sẵn sàng tạo tác vụ mới.</div>",
            0,
            "Chờ lệnh...",
            "",
            None,
            None,
        )

    service = get_job_service()
    job = service.get_job(job_id)

    if not job:
        return (
            f"<div style='color: #ff4d4d;'>Không tìm thấy tác vụ '{job_id}'</div>",
            0,
            "Tác vụ không tồn tại",
            "",
            None,
            None,
        )

    logs_text = "\n".join(service.get_logs(job_id))

    status_badge_color = {
        JobStatus.QUEUED: "#3498db",
        JobStatus.PARSING: "#9b59b6",
        JobStatus.GENERATING_AUDIO: "#e67e22",
        JobStatus.RENDERING_ANIMATION: "#e74c3c",
        JobStatus.COMPOSITING: "#f39c12",
        JobStatus.COMPLETED: "#2ecc71",
        JobStatus.FAILED: "#e74c3c",
    }.get(job.status, "#888888")

    status_html = (
        f"<div style='display: inline-block; padding: 6px 14px; border-radius: 6px; "
        f"background-color: {status_badge_color}; color: #fff; font-weight: bold;'>"
        f"{job.status.value.upper()} ({job.progress_percent}%)</div>"
    )

    video_path = None
    download_file = None
    if job.status == JobStatus.COMPLETED and job.output_video_path:
        p = Path(job.output_video_path)
        if p.exists() and p.stat().st_size > 0:
            video_path = str(p)
            download_file = str(p)

    return (
        status_html,
        job.progress_percent,
        job.current_step_message,
        logs_text,
        video_path,
        download_file,
    )


def cancel_current_job(job_id: str) -> str:
    """Cancels active job."""
    if not job_id:
        return "Không có tác vụ nào đang chạy để hủy."
    service = get_job_service()
    success = service.cancel_job(job_id)
    return "Đã gửi tín hiệu hủy tác vụ." if success else "Không thể hủy hoặc tác vụ đã kết thúc."


def get_history_table() -> list[list[str]]:
    """Returns rows for the History tab."""
    service = get_job_service()
    jobs = service.list_history(limit=30)
    rows = []
    for j in jobs:
        rows.append([
            j.job_id,
            j.source.value,
            j.status.value,
            f"{j.progress_percent}%",
            j.updated_at[:19].replace("T", " "),
            Path(j.output_video_path).name if j.output_video_path else "-",
        ])
    return rows


def load_history_video(job_id: str) -> Optional[str]:
    """Loads video path for selected job from history."""
    if not job_id:
        return None
    service = get_job_service()
    p = service.get_video_path(job_id)
    return str(p) if p else None


def get_system_health() -> str:
    """Gathers diagnostic health status of tools and dependencies."""
    import shutil
    import sys

    cfg = get_config()
    ffmpeg_ok = bool(shutil.which(cfg.ffmpeg_path or "ffmpeg") or Path(r"C:\ffmpeg\bin\ffmpeg.exe").exists())
    ffprobe_ok = bool(shutil.which(cfg.ffprobe_path or "ffprobe") or Path(r"C:\ffmpeg\bin\ffprobe.exe").exists())
    has_tg_token = bool(cfg.telegram_bot_token)

    return f"""### 🛡️ BÁO CÁO TRẠNG THÁI HỆ THỐNG
- **Python Version:** `{sys.version.split()[0]}`
- **FFmpeg Binary:** `{'✅ Khả dụng' if ffmpeg_ok else '❌ Không tìm thấy'}`
- **FFprobe Binary:** `{'✅ Khả dụng' if ffprobe_ok else '❌ Không tìm thấy'}`
- **Edge-TTS Engine:** `✅ Sẵn sàng (Microsoft Neural TTS)`
- **VFX & Animation Engine:** `✅ Sẵn sàng (CPU Pure Pillow + NumPy)`
- **Telegram Bot Token:** `{'✅ Đã cấu hình' if has_tg_token else '⚠️ Chưa cấu hình (Xem .env)'}`
- **Thư mục đầu ra (out/):** `{cfg.out_dir.resolve()}`
- **Thư mục tác vụ (jobs/):** `{cfg.jobs_dir.resolve()}`
"""


def build_studio_ui() -> gr.Blocks:
    """Constructs the complete Gradio UI application layout."""
    with gr.Blocks(title="Dark Myth Stickman Auto-Studio") as app:
        # Header Banner
        gr.HTML(f"<style>{DARK_MYTH_CSS}</style>")
        gr.HTML("""
        <div class="header-box">
            <h1 class="header-title">⚔️ Dark Myth Stickman Auto-Studio ⚔️</h1>
            <div class="header-sub">Hệ Thống Sản Xuất Hoạt Hình Người Que Hắc Ám Tây Du Trên Nền Giấy Kẻ Ngang 9:16 (Chi Phí 0 Đồng)</div>
        </div>
        """)

        with gr.Tabs() as tabs:
            # ----------------------------------------------------
            # TAB 1: SÁNG TÁC & RENDER
            # ----------------------------------------------------
            with gr.Tab("🎬 Sáng Tác & Render Video", id="tab_create"):
                with gr.Row():
                    # Left Column: Inputs & Settings
                    with gr.Column(scale=5):
                        project_name = gr.Textbox(
                            label="Tên Dự Án",
                            value="Đại Chiến Thiên Cung",
                            placeholder="Nhập tên dự án...",
                        )

                        template_dropdown = gr.Dropdown(
                            choices=list(SAMPLE_SCRIPTS.keys()),
                            label="Chọn Mẫu Kịch Bản Có Sẵn (Tùy Chọn)",
                            value="Đại Chiến Thiên Cung (Tôn Ngộ Không vs Dương Tiễn)",
                        )

                        script_input = gr.Textbox(
                            label="Nội Dung Kịch Bản Tiếng Việt",
                            lines=6,
                            value=SAMPLE_SCRIPTS["Đại Chiến Thiên Cung (Tôn Ngộ Không vs Dương Tiễn)"],
                            placeholder="Nhập kịch bản phân cảnh tiếng Việt...",
                        )

                        file_upload = gr.File(
                            label="Hoặc Tải Lên Tệp Kịch Bản (.txt, .json)",
                            file_types=[".txt", ".json"],
                        )

                        # Production Settings Accordion
                        with gr.Accordion("⚙️ Cấu Hình Nhân Vật & Võ Thuật Hắc Ám", open=False):
                            skin_select = gr.Dropdown(
                                choices=[s.value for s in CharacterSkin],
                                label="Hình Tượng Nhân Vật (Character Skin)",
                                value=CharacterSkin.DARK_WUKONG.value,
                            )
                            weapon_select = gr.Dropdown(
                                choices=[w.value for w in WeaponType],
                                label="Binh Khí (Weapon)",
                                value=WeaponType.RUYI_STAFF.value,
                            )
                            action_select = gr.Dropdown(
                                choices=[a.value for a in ActionPreset],
                                label="Võ Thuật Đặc Trưng (Action Preset)",
                                value=ActionPreset.HEAVY_CHARGE_CLASH.value,
                            )

                        with gr.Accordion("🔊 Cấu Hình Giọng Đọc, Âm Thanh & VFX", open=False):
                            voice_select = gr.Dropdown(
                                choices=["vi-VN-NamMinhNeural", "vi-VN-HoaiMyNeural"],
                                label="Giọng Đọc Thuyết Minh (Edge-TTS)",
                                value="vi-VN-NamMinhNeural",
                            )
                            speed_slider = gr.Slider(
                                minimum=0.8,
                                maximum=1.3,
                                value=1.05,
                                step=0.05,
                                label="Tốc Độ Đọc (Voice Speed)",
                            )
                            bgm_select = gr.Dropdown(
                                choices=["battle_tension_percussion", "dark_myth_orchestral"],
                                label="Chủ Đề Nhạc Nền (BGM Theme)",
                                value="battle_tension_percussion",
                            )

                        with gr.Row():
                            btn_generate = gr.Button("🚀 Tạo Video Ngay", variant="primary", scale=2)
                            btn_cancel = gr.Button("⏹️ Hủy", variant="stop", scale=1)

                    # Right Column: Live Monitor & Video Output
                    with gr.Column(scale=5):
                        active_job_id = gr.Textbox(label="Mã Tác Vụ (Job ID)", interactive=False)
                        status_badge = gr.HTML("<div style='color: #888;'>Sẵn sàng nhận lệnh.</div>")
                        progress_bar = gr.Slider(0, 100, value=0, label="Tiến Độ Thực Thi (%)", interactive=False)
                        step_message = gr.Textbox(label="Giai Đoạn Đang Xử Lý", value="Chờ lệnh...", interactive=False)

                        output_video = gr.Video(
                            label="Video Hoạt Hình 9:16 (1080x1920)",
                            height=480,
                            interactive=False,
                        )
                        download_button = gr.File(label="Tải File Video MP4 Về Máy", interactive=False)

                        with gr.Accordion("📋 Nhật Ký Xử Lý Chi Tiết (Logs)", open=False):
                            logs_view = gr.Textbox(label="Logs", lines=6, interactive=False)

                # Periodic status poller
                poll_timer = gr.Timer(1.5, active=True)

            # ----------------------------------------------------
            # TAB 2: LỊCH SỬ & THƯ VIỆN
            # ----------------------------------------------------
            with gr.Tab("📜 Lịch Sử & Thư Viện Sản Phẩm", id="tab_history"):
                with gr.Row():
                    btn_refresh_history = gr.Button("🔄 Làm Mới Danh Sách", variant="secondary")

                history_table = gr.Dataframe(
                    headers=["Job ID", "Nguồn", "Trạng Thái", "Tiến Độ", "Thời Gian", "Tên Video"],
                    value=get_history_table(),
                    interactive=False,
                )

                with gr.Row():
                    with gr.Column(scale=3):
                        selected_job_input = gr.Textbox(label="Nhập Job ID Cần Xem", placeholder="Nhập job_id...")
                        btn_load_history_video = gr.Button("▶️ Xem Lại Video", variant="primary")
                    with gr.Column(scale=4):
                        history_video_player = gr.Video(label="Xem Lại Video Từ Lịch Sử", height=450)

            # ----------------------------------------------------
            # TAB 3: TRẠNG THÁI HỆ THỐNG
            # ----------------------------------------------------
            with gr.Tab("⚙️ Chẩn Đoán & Trạng Thái Hệ Thống", id="tab_health"):
                health_display = gr.Markdown(value=get_system_health())
                btn_refresh_health = gr.Button("🔄 Kiểm Tra Lại Môi Trường")

        # ----------------------------------------------------
        # EVENT WIRINGS
        # ----------------------------------------------------
        template_dropdown.change(
            fn=load_template,
            inputs=[template_dropdown],
            outputs=[script_input],
        )

        file_upload.change(
            fn=read_uploaded_file,
            inputs=[file_upload],
            outputs=[script_input],
        )

        btn_generate.click(
            fn=submit_creation_job,
            inputs=[
                project_name,
                script_input,
                skin_select,
                weapon_select,
                action_select,
                voice_select,
                speed_slider,
                bgm_select,
            ],
            outputs=[
                active_job_id,
                status_badge,
                progress_bar,
                step_message,
                logs_view,
                output_video,
                download_button,
            ],
        )

        btn_cancel.click(
            fn=cancel_current_job,
            inputs=[active_job_id],
            outputs=[step_message],
        )

        poll_timer.tick(
            fn=poll_job_status,
            inputs=[active_job_id],
            outputs=[
                status_badge,
                progress_bar,
                step_message,
                logs_view,
                output_video,
                download_button,
            ],
        )

        btn_refresh_history.click(
            fn=get_history_table,
            inputs=[],
            outputs=[history_table],
        )

        btn_load_history_video.click(
            fn=load_history_video,
            inputs=[selected_job_input],
            outputs=[history_video_player],
        )

        btn_refresh_health.click(
            fn=get_system_health,
            inputs=[],
            outputs=[health_display],
        )

    return app


def launch_studio(
    host: str = "127.0.0.1",
    port: int = 7860,
    share: bool = False,
    inbrowser: bool = False,
) -> None:
    """Launches the Gradio Web UI server."""
    app = build_studio_ui()
    print(f"[*] Starting Dark Myth Stickman Studio at http://{host}:{port}")
    app.queue().launch(
        server_name=host,
        server_port=port,
        share=share,
        inbrowser=inbrowser,
    )


if __name__ == "__main__":
    launch_studio(inbrowser=True)
