# BỔN HỒ SƠ KÝ SỰ: ĐĂNG KÝ & QUẢN LÝ REPOSITORY KỸ THUẬT (`repository_registry.md`)
**Dự án:** Dark Myth Stickman Auto-Studio  
**Phiên bản:** 2.0.0 (Cập nhật tại Giai đoạn 2 — Nghiên cứu & Xác minh Thực tế)  

> **QUY TẮC BẮT BUỘC:** Mọi thư viện và repository trong bảng dưới đây đã được kiểm tra thực tế qua GitHub API / PyPI API ở Giai đoạn 2. AI Coding từ Giai đoạn 3 đến Giai đoạn 10 chỉ được phép sử dụng các gói có quyết định **"Sử dụng qua pip"** hoặc **"Binary hệ thống"**, tuyệt đối không tự ý bịa thêm thư viện ngoài danh sách này.

---

## 1. Bảng Tổng Hợp Toàn Bộ Các Thư Viện / Repository Đã Khảo Sát (Nhóm A – F)

| STT | Tên Thư viện / Repository | URL Chính Thức | Giấy Phép (License) | Nhóm | Trạng Thái Xác Minh Thực Tế | Quyết Định Đề Xuất |
| :-: | :--- | :--- | :--- | :-: | :--- | :--- |
| 1 | `filippocalippo/StykAnimate-App` | `https://github.com/filippocalippo/StykAnimate-App` | GPL-3.0 | **A** | **Đã lấy được** (1,359 stars, JS GUI App) | **Chờ người dùng / Chỉ tham khảo ý tưởng** (App vẽ tay bằng chuột, không phải thư viện Python tự động hóa) |
| 2 | `ManimCommunity/manim` | `https://github.com/ManimCommunity/manim` | MIT | **A** | **Đã lấy được** (PyPI `0.22.1`, 42k stars) | **Chỉ tham khảo kiến trúc** (Tham khảo hàm nội suy `rate_functions`/Easing; không cài vì phụ thuộc C nặng) |
| 3 | `numpy` (`numpy/numpy`) | `https://github.com/numpy/numpy` | BSD-3-Clause | **A, B** | **Đã lấy được** (PyPI `2.5.4`) | **Sử dụng qua pip** (Tính toán ma trận xương 2D, IK, Bezier, DSP tổng hợp âm thanh) |
| 4 | `Pillow` (`python-pillow/Pillow`) | `https://github.com/python-pillow/Pillow` | MIT-CMU | **A, B** | **Đã lấy được** (PyPI `13.0.0`) | **Sử dụng qua pip** (Vẽ nền giấy vở kẻ ngang, phụ đề tiếng Việt UTF-8, lớp phủ mực) |
| 5 | `opencv-python-headless` | `https://github.com/opencv/opencv-python` | Apache-2.0 | **A, B** | **Đã lấy được** (PyPI `5.0.0.93`) | **Sử dụng qua pip** (Vẽ khớp xương chống răng cưa `LINE_AA`, làm mờ hào quang `GaussianBlur`, biến đổi góc máy `warpAffine`) |
| 6 | `scipy` (`scipy/scipy`) | `https://github.com/scipy/scipy` | BSD-3-Clause | **A** | **Đã lấy được** (PyPI `1.18.1`) | **Sử dụng qua pip (Tùy chọn)** (Nội suy đường cong Spline và lọc tín hiệu âm thanh) |
| 7 | `pygame` (`pygame/pygame`) | `https://github.com/pygame/pygame` | LGPL-2.1 | **B** | **Đã lấy được** (PyPI `2.6.1`) | **Loại bỏ** (Không cần thiết khi đã có `opencv-python-headless` + `Pillow` chạy headless nhanh hơn) |
| 8 | `pythonarcade/arcade` | `https://github.com/pythonarcade/arcade` | MIT | **B** | **Đã lấy được** (PyPI `3.3.3`) | **Loại bỏ** (Yêu cầu OpenGL 3.3+ context / GPU, không tương thích máy chủ container không GPU) |
| 9 | `moderngl/moderngl` | `https://github.com/moderngl/moderngl` | MIT | **B** | **Đã lấy được** (PyPI `5.13.0`) | **Loại bỏ** (Yêu cầu EGL/OpenGL context, rủi ro lỗi trên môi trường headless CPU) |
| 10 | `Zulko/moviepy` | `https://github.com/Zulko/moviepy` | MIT | **C** | **Đã lấy được** (PyPI `2.2.1`, 15k stars) | **Chỉ tham khảo kiến trúc / Dự phòng** (Ưu tiên truyền frame qua `ffmpeg` pipe để giữ RAM `< 300MB`) |
| 11 | `kkroening/ffmpeg-python` | `https://github.com/kkroening/ffmpeg-python` | Apache-2.0 | **C** | **Đã lấy được** (PyPI `0.2.0`, 11k stars) | **Sử dụng qua pip** (Xây dựng luồng filter FFmpeg & quản lý tiến trình nén H.264 MP4) |
| 12 | `PyAV-Org/PyAV` (`av`) | `https://github.com/PyAV-Org/PyAV` | BSD-3-Clause | **C** | **Đã lấy được** (PyPI `19.0.2`, 3.3k stars) | **Loại bỏ / Dự phòng** (`ffmpeg` CLI + `ffmpeg-python` đã đáp ứng trọn vẹn và trực quan hơn) |
| 13 | `ffmpeg` & `ffprobe` (System) | `https://ffmpeg.org` | GPL / LGPL | **C, D** | **Đã cài đặt sẵn** (`4.4.2-0ubuntu0.22.04.1`) | **Binary hệ thống bắt buộc** (Mã hóa `libx264`, `yuv420p`, `aac`, đo thời lượng `ffprobe`) |
| 14 | `rany2/edge-tts` | `https://github.com/rany2/edge-tts` | MIT / GPL-3.0 | **D** | **Đã lấy được** (PyPI `7.3.1`, 12.4k stars) | **Sử dụng qua pip** (Tạo giọng đọc tiếng Việt `vi-VN-NamMinhNeural` miễn phí + phụ đề mốc thời gian) |
| 15 | `jiaaro/pydub` | `https://github.com/jiaaro/pydub` | MIT | **D** | **Đã lấy được** (PyPI `0.25.1`, 9.8k stars) | **Sử dụng qua pip** (Ghép thoại từng cảnh, chèn SFX theo mili-giây và trộn BGM có Audio Ducking) |
| 16 | `quodlibet/mutagen` | `https://github.com/quodlibet/mutagen` | GPL-2.0+ | **D** | **Đã lấy được** (PyPI `1.48.1`, 1.9k stars) | **Sử dụng qua pip** (Đo thời lượng tệp âm thanh `.mp3`/`.wav` tức thì kết hợp `ffprobe`) |
| 17 | `harry0703/MoneyPrinterTurbo` | `https://github.com/harry0703/MoneyPrinterTurbo` | MIT | **E** | **Đã lấy được** (136.6k stars) | **Chỉ tham khảo kiến trúc** (Tham khảo luồng điều phối Task Queue & tách câu phụ đề; không cài đặt) |
| 18 | `RayVentura/ShortGPT` | `https://github.com/RayVentura/ShortGPT` | MIT | **E** | **Đã lấy được** (8.0k stars) | **Chỉ tham khảo kiến trúc** (Tham khảo cơ chế đồng bộ thời lượng Audio-Visual; không cài đặt) |
| 19 | `python-telegram-bot` | `https://github.com/python-telegram-bot/python-telegram-bot` | LGPL-3.0 | **E** | **Đã lấy được** (PyPI `22.8`, 29.5k stars) | **Sử dụng qua pip** (Chạy Telegram Bot Long-polling nhận kịch bản và trả video `.mp4`) |
| 20 | `gradio-app/gradio` | `https://github.com/gradio-app/gradio` | Apache-2.0 | **E** | **Đã lấy được** (PyPI `6.31.0`, 43.9k stars) | **Loại bỏ** (Sử dụng giao diện Web React + Vite + Express cổng 3000 sẵn có của dự án để tối ưu) |
| 21 | `googleapis/python-genai` | `https://github.com/googleapis/python-genai` | Apache-2.0 | **E** | **Đã lấy được** (PyPI `2.34.0` / npm `@google/genai ^2.4.0`) | **Sử dụng qua pip / npm** (Gọi Gemini API phân tách kịch bản khi có key, tự động fallback về Rule-Based Parser khi không có key) |
| 22 | `pytest-dev/pytest` | `https://github.com/pytest-dev/pytest` | MIT | **F** | **Đã lấy được** (PyPI `9.2.0`, 14.6k stars) | **Sử dụng qua pip** (Chạy bộ kiểm thử tự động tại thư mục `tests/` qua các giai đoạn) |
| 23 | `pydantic/pydantic` | `https://github.com/pydantic/pydantic` | MIT | **F** | **Đã lấy được** (PyPI `2.14.2`, 29.2k stars) | **Sử dụng qua pip** (Xác thực nghiêm ngặt hợp đồng dữ liệu `ScriptInput`, `SceneSchema`, `JobStatus`, `RenderResult`) |
| 24 | Bộ chiêu thức & SFX Tây Du | Xem `docs/research/manual_repositories.md` | Nội bộ | **A, B, D** | **Chưa tìm được repo có sẵn** | **Chờ người dùng / Tự xây dựng nội bộ** (Triển khai theo thông số trong `agents/references/` và `agents/skills/`) |

---

## 2. Danh Sách Gói `requirements.txt` Chuẩn Hóa Cho Giai Đoạn 3+

Khi bước sang giai đoạn lập trình, chỉ các gói đã được duyệt dưới đây mới được phép đưa vào môi trường Python:
```text
numpy>=1.24.0
Pillow>=10.0.0
opencv-python-headless>=4.8.0
scipy>=1.10.0
edge-tts>=6.1.9
pydub>=0.25.1
mutagen>=1.46.0
ffmpeg-python>=0.2.0
pydantic>=2.5.0
pytest>=7.4.0
python-telegram-bot>=20.0
google-genai>=1.0.0
```
