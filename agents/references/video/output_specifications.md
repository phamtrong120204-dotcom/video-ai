# TÀI LIỆU THAM CHIẾU KỸ THUẬT: THÔNG SỐ CHUẨN VIDEO ĐẦU RA (`output_specifications.md`)
**Dự án:** Dark Myth Stickman Auto-Studio  
**Đối chiếu hợp đồng dữ liệu:** `docs/04_data_contracts.md` (`RenderResult.technical_metadata`)  

---

## 1. Bảng Thông Số Kỹ Thuật Bắt Buộc Cho Tệp Video Xuất Ra (`out/<job_id>.mp4`)

| Nhóm Thông Số | Tên Thuộc Tính | Giá Trị Chuẩn Bắt Buộc | Công Cụ Kiểm Chứng (`ffprobe` field) |
| :--- | :--- | :--- | :--- |
| **Container** | Định dạng tệp | `.mp4` (MPEG-4 Part 14) | `format.format_name` chứa `"mp4"` |
| **Container** | Cờ phát trực tuyến | `-movflags +faststart` | Phát ngay trên thẻ `<video>` HTML5 và Telegram |
| **Hình ảnh (Video)** | Tỷ lệ khung hình (`aspect_ratio`) | `9:16` (Vertical / Dọc) | `stream.display_aspect_ratio == "9:16"` |
| **Hình ảnh (Video)** | Độ phân giải chuẩn (`resolution`) | `1080x1920` (`width = 1080`, `height = 1920`) | `stream.width == 1080`, `stream.height == 1920` |
| **Hình ảnh (Video)** | Tốc độ khung hình (`fps`) | `30` FPS (`r_frame_rate = "30/1"`) | `stream.r_frame_rate == "30/1"` |
| **Hình ảnh (Video)** | Bộ mã hóa (`video_codec`) | `h264` (`libx264`) | `stream.codec_name == "h264"` |
| **Hình ảnh (Video)** | Định dạng điểm ảnh (`pix_fmt`) | `yuv420p` | `stream.pix_fmt == "yuv420p"` |
| **Hình ảnh (Video)** | Hệ số chất lượng (`CRF`) | `21` (`-preset fast`) | Đảm bảo nét vẽ mực và chữ phụ đề sắc nét, không bị nhòe khối |
| **Âm thanh (Audio)** | Bộ mã hóa (`audio_codec`) | `aac` | `stream.codec_name == "aac"` |
| **Âm thanh (Audio)** | Tần số lấy mẫu (`sample_rate`) | `44100 Hz` | `stream.sample_rate == "44100"` |
| **Âm thanh (Audio)** | Số kênh (`channels`) | `2` (Stereo) | `stream.channels == 2` |
| **Âm thanh (Audio)** | Tốc độ bit (`bitrate`) | `192 kbps` | `-b:a 192k` |
| **Thời lượng** | Thời lượng kịch bản đầy đủ | `60.0s – 180.0s` (1 – 3 phút) | `format.duration` khớp với $\sum \text{audio\_duration\_sec}$ (sai số $< 0.2\text{s}$) |

---

## 2. Quy Chuẩn Vùng Hiển Thị Phụ Đề Tiếng Việt Trên Khung Hình 9:16

Để phụ đề tiếng Việt không bị che khuất bởi giao diện của TikTok, YouTube Shorts, Reels hoặc Telegram Player:
- **Vị trí theo trục dọc ($Y$):** Tâm vùng phụ đề đặt tại $Y = 1580\text{ px}$ (cách mép dưới khung hình `340 px`).
- **Giới hạn chiều ngang ($X$):** $X \in [90, 990]\text{ px}$ (chiều rộng tối đa `900 px`, tự động ngắt dòng tối đa 2 dòng hiển thị cùng lúc, mỗi dòng khoảng `7 – 10 từ`).
- **Kiểu chữ & Tương phản:**
  - Cỡ chữ: `44 px` (Bold, hỗ trợ đầy đủ dấu tiếng Việt Unicode UTF-8).
  - Màu chữ: Trắng kem `#FFFDF7` hoặc Vàng kim `#FFD700` cho từ khóa nhấn mạnh, kèm viền đen dày `4 px` (`stroke_width=4, stroke_fill=(15, 15, 18)`) và nền băng mực mờ (`semi-transparent ink banner` độ mờ `65%`) giúp đọc rõ 100% trên nền giấy vở kẻ ngang.
