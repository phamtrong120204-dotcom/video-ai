# Dark Myth Stickman Auto-Studio
**Hệ thống tự động hóa sản xuất video hoạt hình người que chiến đấu trên nền giấy vở kẻ ngang (Hắc Ám Tây Du)**

> Dự án mã nguồn mở chuẩn hoá sản xuất video ngắn (9:16 dọc, 1080x1920, 30 FPS, H.264/AAC), chi phí 0 đồng trên máy tính cá nhân (Local CPU), tích hợp giọng đọc tiếng Việt Edge-TTS, hiệu ứng võ thuật Hắc Ám (Dark Corruption VFX Engine), SFX/BGM tự động ducking, Gradio Local Studio Web UI và Telegram Bot.

---

## 🌟 Tính Năng Nổi Bật

- **Chi Phí 0 Đồng & Chạy Thuần Local (Local CPU):** Không phụ thuộc bất kỳ API dịch vụ trả phí nào (không tốn tiền GPU cloud hay ElevenLabs/OpenAI TTS). Hoạt động mượt mà trên CPU thông thường.
- **Kịch Bản & Giọng Đọc Tiếng Việt:** Phân tích kịch bản thông minh (Hybrid AI Gemini Flash + Rule-based fallback ngoại tuyến), tự động đo thời lượng thoại tiếng Việt để điều tiết tốc độ hoạt hình (Audio-First Timing).
- **Hoạt Ảnh Người Que Động (Procedural Stickman Animation):** Hệ thống khớp xương 2D rigging với các nhân vật đặc trưng (Hắc Ngộ Không, Dương Tiễn, Thiên Binh) và vũ khí Dark Myth (Thiết Bảng Như Ý, Tam Tiêm Đao, Thiên Binh Đại Kích, Bàn Tay Phật Khổng Lồ).
- **Hiệu Ứng Hắc Ám (Dark Corruption VFX Engine):**
  - Biến dạng tọa độ đường kẻ ngang giấy vở (Warp Distortion Field - Palm Depression & Shockwave).
  - Khói đen u ám, tàn lửa, xúc tua Hắc Ám, tia lửa va chạm (Clash Sparks) và bụi giấy tung bay (Paper Dust).
  - Vệt kiếm khí vũ khí chuyển động (Motion Trails).
- **Âm Thanh & Nhạc Nền Tự Động:** Tự động đồng bộ SFX theo từng frame va chạm, ghép nhạc nền Dark Myth phong cách điện ảnh với cơ chế tự động giảm âm khi có lời thoại (Audio Ducking) và bộ giới hạn âm lượng chống vỡ tiếng (Limiter).
- **Giao Diện Studio Trực Quan (Gradio 6):** Thiết kế Dark Myth phong cách than hắc ám (`#0d0e15`), viền đỏ thẫm và vàng kim; hỗ trợ nhập kịch bản, upload tệp, tùy biến nhân vật/vũ khí/chiêu thức, xem tiến độ trực tiếp, phát video 9:16 và tải về một chạm.
- **Điều Khiển Qua Telegram Bot:** Nhận kịch bản qua tin nhắn chat hoặc file đính kèm, cập nhật tiến độ render thời gian thực, gửi video kết quả trực tiếp với cơ chế whitelist bảo mật và chế độ Safe Standby an toàn.

---

## 🛠️ Yêu Cầu Môi Trường (Prerequisites)

1. **Hệ điều hành:** Windows 10 hoặc Windows 11 (64-bit).
2. **Python:** Phiên bản 3.10 trở lên (khuyên dùng Python 3.15).
3. **FFmpeg & FFprobe:** Đã cài đặt tại `C:\ffmpeg\bin\` (hoặc có trong biến môi trường `PATH`).

---

## 🚀 Hướng Dẫn Cài Đặt Lần Đầu (First-Time Setup)

Dự án cung cấp công cụ tự động hóa toàn bộ quy trình thiết lập:

### Bước 1: Chạy file cài đặt tự động
Nhấp đúp chuột vào file:
```cmd
setup_environment.bat
```
Script sẽ tự động:
1. Kiểm tra phiên bản Python trên máy bạn.
2. Khởi tạo môi trường ảo `.venv` (nếu chưa có).
3. Tải và cài đặt toàn bộ các thư viện cần thiết trong `requirements.txt`.
4. Tạo tệp `.env` mặc định từ `.env.example` (nếu chưa có).
5. Thực hiện kiểm tra toàn diện hệ thống qua `scripts/preflight_check.py`.

---

## ⚙️ Cấu Hình Biến Môi Trường (`.env`)

Mở tệp `.env` trong thư mục gốc bằng Notepad hoặc VS Code để cấu hình:

```env
# 1. Khóa Gemini API (Tùy chọn)
# Dùng để phân tích kịch bản bằng AI Gemini Flash. Nếu để trống, hệ thống sẽ tự động chuyển sang bộ phân tích Rule-based ngoại tuyến mà không tốn phí.
GEMINI_API_KEY=""

# 2. Telegram Bot Token (Tùy chọn)
# Lấy từ @BotFather nếu bạn muốn bật bot Telegram. Nếu để trống, bot sẽ ở chế độ Safe Standby mà không gây lỗi.
TELEGRAM_BOT_TOKEN=""

# 3. Danh sách người dùng Telegram được phép (Whitelist)
# Nhập các ID tài khoản Telegram, phân tách bằng dấu phẩy (Ví dụ: "12345678,87654321"). Để trống nếu muốn cho phép mọi người dùng.
TELEGRAM_ALLOWED_USERS=""

# 4. Giọng đọc tiếng Việt mặc định (Edge-TTS miễn phí)
# Nam: vi-VN-NamMinhNeural | Nữ: vi-VN-HoaiMyNeural
TTS_DEFAULT_VOICE="vi-VN-NamMinhNeural"

# 5. Cấu hình video xuất xưởng
RENDER_FPS="30"
RENDER_RESOLUTION="1080x1920"

# 6. Đường dẫn FFmpeg và FFprobe
FFMPEG_PATH="C:\\ffmpeg\\bin\\ffmpeg.exe"
FFPROBE_PATH="C:\\ffmpeg\\bin\\ffprobe.exe"
```

---

## 🖥️ Cách Khởi Động & Sử Dụng Ứng Dụng

Sau khi thiết lập môi trường, bạn có thể khởi chạy ứng dụng bằng 1 thao tác nhấp chuột:

### 1. Khởi chạy Local Studio Web UI (Gradio)
Nhấp đúp chuột vào:
```cmd
run_studio.bat
```
- Trình duyệt sẽ tự động mở giao diện tại địa chỉ: `http://localhost:7860`.
- **Cách dùng:**
  1. Nhập tiêu đề dự án và nội dung kịch bản vào ô văn bản (hoặc tải lên file `.txt` / `.json`).
  2. Chọn nhân vật (Hắc Ngộ Không, Dương Tiễn, Thiên Binh), vũ khí (Thiết Bảng Như Ý, Tam Tiêm Đao, Thiên Binh Đại Kích, Bàn Tay Phật) và chiêu thức giao chiến.
  3. Chọn giọng đọc tiếng Việt và nhạc nền BGM.
  4. Nhấn nút **"Bắt Đầu Sản Xuất Video"**.
  5. Theo dõi tiến độ thời gian thực qua thanh phần trăm (%) và bảng log.
  6. Khi hoàn tất, video 9:16 sẽ hiển thị ngay trong trình phát video nhúng; bạn có thể xem trực tiếp hoặc nhấn nút **"Tải Video Thành Phẩm (.mp4)"**.
  7. Chuyển sang tab **"Lịch Sử & Bộ Sưu Tập"** để xem lại các video đã render trước đó.

### 2. Khởi chạy Telegram Bot
Nhấp đúp chuột vào:
```cmd
run_bot.bat
```
- Bot sẽ kết nối và lắng nghe tin nhắn từ Telegram.
- **Lưu ý:** Cần điền `TELEGRAM_BOT_TOKEN` trong tệp `.env`. Nếu chưa điền, bot sẽ thông báo và dừng ở chế độ chờ an toàn.

### 3. Khởi chạy Cả Web UI & Telegram Bot Đồng Thời
Nhấp đúp chuột vào:
```cmd
run_all.bat
```
- Cả hai dịch vụ sẽ chạy song song trên cùng một máy, chia sẻ chung một hàng đợi tác vụ `JobService` duy nhất (không lo xung đột file hay tài nguyên).

### 4. Dừng ứng dụng an toàn
Nhấp đúp chuột vào:
```cmd
stop_app.bat
```
- Script sẽ tự động đóng các tiến trình Python của Studio và Bot đang chạy ngầm.

---

## 🤖 Các Lệnh Điều Khiển Trên Telegram Bot

Khi Telegram Bot đang chạy, bạn có thể gửi các lệnh sau:

| Lệnh | Ý nghĩa |
| :--- | :--- |
| `/start` | Bắt đầu trò chuyện và kiểm tra quyền truy cập |
| `/help` | Xem danh sách lệnh và ví dụ định dạng kịch bản |
| `/status` | Xem số lượng worker rảnh/bận và tác vụ đang xử lý |
| `/generate <kịch bản>` | Gửi kịch bản trực tiếp trong tin nhắn để bắt đầu render video |
| `/progress [job_id]` | Tra cứu tiến độ % và trạng thái hiện tại của tác vụ |
| `/history` | Xem 5 tác vụ sản xuất gần nhất |
| `/download <job_id>` | Tải video MP4 thành phẩm về máy |
| `/cancel [job_id]` | Hủy một tác vụ đang chạy hoặc đang trong hàng đợi |
| *Gửi file `.txt` / `.json`* | Bot tự động đọc kịch bản từ file đính kèm và tạo tác vụ |

---

## 🧪 Kiểm Thử Tự Động (Automated Testing)

Chạy toàn bộ 353 bài kiểm thử của dự án:
```cmd
.\.venv\Scripts\pytest.exe -q
```
*Kết quả tiêu chuẩn:* `353 passed in ~16s (100% PASS, 0 failed, 0 skipped)`

Để chạy kiểm tra chẩn đoán hệ thống độc lập:
```cmd
.\.venv\Scripts\python.exe scripts\preflight_check.py
```

---

## 📁 Thư Mục Sản Phẩm & Dữ Liệu Đầu Ra

- `out/`: Chứa tất cả các video MP4 thành phẩm đã xuất xưởng (`job_<id>.mp4`).
- `out/jobs/`: Chứa hồ sơ nhật ký tác vụ dưới định dạng JSON (`job_<id>.json`).
- `out/preview/g10_final/`: Chứa video mẫu nghiệm thu cuối cùng (`g10_final_demo_video.mp4`), ảnh Contact Sheet (`g10_contact_sheet.png`) và hồ sơ kiểm định (`g10_final_manifest.json`).
- `logs/`: Chứa nhật ký hệ thống toàn trình (`logs/app.log`).

---

## 🔧 Xử Lý Các Sự Cố Thường Gặp (Troubleshooting)

1. **Lỗi "Không tìm thấy FFmpeg binary":**
   - Đảm bảo bạn đã giải nén FFmpeg vào thư mục `C:\ffmpeg\bin\` (chứa `ffmpeg.exe` và `ffprobe.exe`), hoặc kiểm tra đường dẫn `FFMPEG_PATH` trong tệp `.env`.
2. **Cổng 7860 đã bị chiếm dụng (Port 7860 in use):**
   - Khởi chạy Studio với cổng khác bằng lệnh:
     ```cmd
     .\.venv\Scripts\python.exe app\main.py --studio --port 7861
     ```
3. **Telegram Bot không phản hồi:**
   - Kiểm tra xem bạn đã điền `TELEGRAM_BOT_TOKEN` hợp lệ trong `.env` chưa.
   - Nếu đã điền `TELEGRAM_ALLOWED_USERS`, kiểm tra xem ID Telegram của bạn đã được thêm vào danh sách chưa (gửi `/start` tới bot `@userinfobot` để lấy User ID của bạn).
4. **Lỗi mạng khi tải giọng đọc Edge-TTS:**
   - Hệ thống có cơ chế tự động thử lại 3 lần kèm backoff. Đảm bảo máy tính có kết nối Internet để tải giọng đọc tiếng Việt miễn phí từ Microsoft Edge Neural TTS.

---

## 📜 Bản Quyền & Giấy Phép
Dự án được xây dựng hoàn toàn độc lập theo chuẩn mô-đun hóa, phục vụ mục tiêu sản xuất video võ thuật người que phong cách Hắc Ám Tây Du với chi phí 0 đồng trên máy tính cá nhân.
