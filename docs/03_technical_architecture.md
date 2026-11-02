# TÀI LIỆU KIẾN TRÚC KỸ THUẬT (TECHNICAL ARCHITECTURE)
**Dự án:** Dark Myth Stickman Auto-Studio  
**Phiên bản:** 1.0.0 (Giai đoạn 1 — Project Foundation)  
**Vai trò thiết kế:** Principal Software Architect  

---

## 1. Triết Lý Thiết Kế Kiến Trúc (Architectural Principles)

1. **Kiến trúc Phân tầng Độc lập (Layered Modular Architecture):** Mỗi tầng chỉ giao tiếp với tầng liền kề thông qua hợp đồng dữ liệu nghiêm ngặt (`docs/04_data_contracts.md`). Có thể thay thế từng module (ví dụ: đổi engine TTS hoặc đổi bộ vẽ Stickman) mà không ảnh hưởng các tầng khác.
2. **Thiết kế Chống Sập & Dự phòng Kép (Graceful Degradation & Offline Fallback):** Mọi thành phần có kết nối mạng (LLM Parser, Edge-TTS) đều bắt buộc có nhánh dự phòng chạy Offline 100% trên máy Local.
3. **Tiết kiệm Tài nguyên Tuyệt đối (Zero-Footprint Resource Management):** Không lưu hàng nghìn ảnh PNG không nén ra ổ cứng nếu có thể truyền luồng byte (`stdin pipe`) trực tiếp sang FFmpeg, hoặc phải xóa ngay lập tức từng phân cảnh sau khi ghép xong.

---

## 2. Sơ Đồ Kiến Trúc Phân Tầng (6-Tier Architecture Diagram)

```text
+-----------------------------------------------------------------------------------+
|                        TẦNG 1: GIAO TIẾP (INTERFACE LAYER)                        |
|   [ Web App UI (React + Vite :3000) ]        [ Telegram Bot Worker (Polling) ]    |
+-----------------------------------------+-----------------------------------------+
                                          | (REST API / Internal Job Dispatch)
                                          v
+-----------------------------------------------------------------------------------+
|               TẦNG 2: ĐIỀU PHỐI TÁC VỤ (TASK ORCHESTRATOR & QUEUE)                |
|   [ Job Manager ]  --->  [ FIFO Worker Queue ]  --->  [ State & Temp Cleaner ]    |
+-----------------------------------------+-----------------------------------------+
                                          |
        +---------------------------------+---------------------------------+
        |                                 |                                 |
        v                                 v                                 v
+-----------------------+     +-----------------------+     +-----------------------+
| TẦNG 3: PHÂN TÍCH     |     | TẦNG 4: ÂM THANH      |     | TẦNG 5: ĐỒ HỌA        |
| KỊCH BẢN              |     | (AUDIO ENGINE)        |     | & HOẠT HÌNH           |
| - Gemini Parser (Opt) |     | - Vietnamese TTS      |     | - Notebook Paper Gen  |
| - VN Rule Parser      |     | - Procedural SFX Gen  |     | - 2D Stickman Rig/IK  |
|   (100% Fallback)     |     | - BGM Auto-Ducker     |     | - Combat Choreography |
+-----------+-----------+     +-----------+-----------+     +-----------+-----------+
            |                             |                             |
            +-----------------------------+-----------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|               TẦNG 6: KẾT XUẤT VIDEO (VIDEO COMPOSITOR & RENDERER)                |
|   [ FFmpeg Pipe / Segment Encoder (H.264 1080x1920 30fps) ] ---> [ out/<id>.mp4 ] |
+-----------------------------------------------------------------------------------+
```

---

## 3. Thiết Kế Chi Tiết 6 Tầng Kỹ Thuật

### 3.1. Tầng 1: Tầng Giao Tiếp (Interface Layer — Web UI & Telegram Bot)
- **Local Web Studio UI (`Gradio` tại cổng `7860`):**
  - Giao diện người dùng thuần Python xây dựng bằng Gradio, loại bỏ hoàn toàn mã nguồn React/Vite/Node.js để đảm bảo kiến trúc 100% Python đồng nhất và triển khai cục bộ gọn nhẹ.
  - Cho phép người dùng: nhập kịch bản tiếng Việt, chọn giọng đọc (`NamMinh`, `HoaiMy`), cấu hình độ phân giải, kiểm tra bảng phân cảnh trích xuất (`SceneSchema[]`), theo dõi thanh tiến độ thời gian thực của 7 trạng thái tác vụ, và xem/tải trực tiếp video thành phẩm `.mp4` 9:16.
- **Telegram Bot Adapter (`app/interfaces/telegram_bot.py`):**
  - Chạy cơ chế **Long-Polling** bất đồng bộ trên framework Python (ví dụ: `python-telegram-bot` hoặc `aiogram`).
  - Khi nhận lệnh hoặc tin nhắn kịch bản, bot dispatch toàn bộ tiến trình render sang worker thread nền (qua `asyncio.to_thread`), tuyệt đối không chặn Event Loop của bot.
  - Chỉ kích hoạt khi biến môi trường `TELEGRAM_BOT_TOKEN` có giá trị hợp lệ. Nếu để trống, hệ thống chạy độc lập qua Local Web Studio UI mà không phát sinh lỗi.

### 3.2. Tầng 2: Tầng Điều Phối Tác Vụ (Task Orchestrator / Queue & Thread Isolation)
- **Quản lý vòng đời tác vụ (`Job Lifecycle`):**
  - Duy trì trạng thái từng tác vụ theo đúng chuỗi: `queued` $\rightarrow$ `parsing` $\rightarrow$ `generating_audio` $\rightarrow$ `rendering_animation` $\rightarrow$ `compositing` $\rightarrow$ `completed` (hoặc `failed`).
- **Kiến trúc đồng bộ cốt lõi & cách ly luồng (Synchronous Core & Thread Isolation):**
  - Toàn bộ nghiệp vụ nội bộ của `PipelineOrchestrator` và các Interface (`IScriptParser`, `IAudioEngine`, `IAnimationEngine`, `IVideoCompositor`) được thiết kế **hoàn toàn đồng bộ (Synchronous)** để đơn giản hóa việc quản lý luồng CPU-bound và subprocess I/O.
  - Khi được gọi từ các framework bất đồng bộ (Telegram Bot async loop hoặc FastAPI/Gradio), tác vụ render được dispatch sang worker thread thông qua `asyncio.to_thread(orchestrator.run, script_input)`.
  - Nhờ cơ chế worker thread, module TTS (`EdgeTTSAudioEngine`) có thể gọi `asyncio.run()` an toàn mà không xung đột với Event Loop chính của ứng dụng web/bot.
- **Hàng đợi xử lý tuần tự (Concurrency Control):**
  - Việc kết xuất video 1080x1920 tiêu tốn nhiều CPU. Tầng điều phối sử dụng hàng đợi **FIFO (First-In, First-Out)** với số luồng render đồng thời mặc định `MAX_CONCURRENT_JOBS = 1` để tránh treo máy khi người dùng gửi liên tiếp nhiều yêu cầu từ cả Web và Telegram.
- **Lưu trữ trạng thái (Job Persistence):**
  - Lưu metadata của từng Job dưới dạng tệp JSON nhẹ tại `out/jobs/<job_id>.json` để khi khởi động lại ứng dụng vẫn tra cứu được lịch sử.

### 3.3. Tầng 3: Tầng Phân Tích Kịch Bản (Script Parser + Fallback)
- **Nhiệm vụ:** Chuyển đổi văn bản thô (`ScriptInput`) thành mảng các đối tượng `SceneSchema` chuẩn hóa.
- **Chiến lược 2 lớp (Dual-Strategy Parsing):**
  1. **Lớp thông minh (Optional LLM Parser):** Nếu `GEMINI_API_KEY` được cấu hình, gọi Gemini Flash với JSON Schema nghiêm ngặt để phân tách câu thoại, gán nhân vật, chọn `action_preset`, góc máy và điểm rơi SFX.
  2. **Lớp cơ sở bất khả chiến bại (Deterministic Rule-Based Parser):**
     - Tách đoạn văn bản theo dấu chấm câu, xuống dòng hoặc từ khóa phân cảnh (`Cảnh 1:`, `Đoạn 1:`).
     - Gộp hoặc tách câu tự động sao cho mỗi phân cảnh có độ dài từ **12 – 35 từ tiếng Việt** (tương ứng ~4 – 10 giây đọc).
     - Đối chiếu từ điển thực thể Hắc Ám Tây Du (Ngộ Không, Nhị Lang Thần, Thiên Binh, Phật Tổ, Thiết Bảng, Tam Tiêm Đảo...) và từ điển động từ hành động (đập, chém, lao tới, đỡ đòn, xoay gậy, trấn áp...) để tự động sinh `actors`, `action_preset`, `camera_movement` và `sfx_events` hoàn toàn không cần Internet.

### 3.4. Tầng 4: Tầng Âm Thanh (TTS Engine & Audio Mixer)
- **Bộ tổng hợp giọng đọc tiếng Việt (Vietnamese TTS Engine — Quyết định Phương án B):**
  - **Chính (`Primary`):** Sử dụng `edge-tts` với giọng đọc tiếng Việt truyền cảm (`vi-VN-NamMinhNeural` cho giọng nam trầm hùng sử thi, `vi-VN-HoaiMyNeural` cho giọng nữ dẫn truyện). Tích hợp cơ chế retry backoff tự động (3 lần) và voice fallback nếu node dịch vụ giọng nam gặp gián đoạn tạm thời.
  - **Xử lý sự cố ngoại tuyến & giới hạn (Network Failure Handling - Strict Option B):**
    - Khi mất kết nối Internet hoặc toàn bộ chính sách retry của Edge-TTS thất bại, hệ thống phát sinh ngoại lệ `AudioGenerationError` rõ ràng và chuyển tác vụ sang trạng thái `failed`.
    - **Nghiêm cấm** tạo tệp âm thanh giả (sóng sin, tiếng ồn tĩnh hoặc WAV rỗng) để đánh lừa luồng render.
    - Việc tích hợp bộ tổng hợp ngoại tuyến mã nguồn mở (như Piper TTS kèm voice model VIVOS) tạm thời bị hoãn lại để rà soát đầy đủ tính pháp lý và bản quyền phân phối/thương mại. Hệ thống KHÔNG tuyên bố có Offline TTS thực thụ ở giai đoạn này.
- **Đo thời lượng chuẩn xác & Chuẩn hóa dòng thời gian (Audio Timing & Padding):**
  - Đo thời lượng tệp âm thanh MP3 thực tế bằng thư viện `mutagen.mp3.MP3`.
  - Bổ sung đệm âm thanh mặc định `0.30s` (Audio Padding) vào cuối mỗi câu thoại để giọng đọc không bị cụt và cho phép động tác nhân vật hoàn tất chu kỳ hồi chiêu (Recovery Frames).
- **Bộ tạo SFX & BGM (SFX & BGM Synthesizer / Library):**
  - Kết hợp các tệp âm thanh tĩnh trong `assets/sfx/`, `assets/bgm/` và bộ tổng hợp âm thanh toán học (Procedural Waveform Generator bằng sóng sin/noise có bộ lọc bao hình ADSR) cho tiếng va chạm binh khí (`metal_clash`), tiếng gậy xé gió (`whoosh_heavy`), tiếng nổ chấn động (`earth_slam`), và tiếng sấm (`thunder_crack`).
- **Bộ trộn âm thanh đa kênh (Multi-track Audio Mixer):**
  - Sử dụng bộ lọc âm thanh FFmpeg (`adelay`, `amix`, `sidechaincompress` / volume envelope) để ghép giọng đọc, chèn SFX đúng mili-giây và tự động hạ nhỏ nhạc nền (BGM Ducking) khi có tiếng thuyết minh (Voice: 0dB, SFX: -4.4dB, BGM Ducked: -14dB, BGM Idle: -7dB).

### 3.5. Tầng 5: Tầng Đồ Họa & Hoạt Hình (Procedural Stickman Animation Engine)
- **Hệ tọa độ chuẩn:** Không gian Canvas dọc `1080 x 1920` (hoặc tỷ lệ tương đương), gốc tọa độ `(0, 0)` ở góc trên bên trái, mặt đất giao chiến mặc định tại `Y = 1420`.
- **Trình tạo nền giấy vở (`NotebookPaperRenderer`):**
  - Vẽ nền giấy màu kem/xám cổ điển, kẻ các đường ngang màu xanh dương nhạt cách nhau `48px`, đường lề dọc màu đỏ ở `X = 140px`, hiệu ứng tối bốn góc (vignette) và các vết mực bắn tung tóe khi nhân vật trúng đòn.
- **Hệ thống xương người que (`StickmanRig2D`):**
  - Mỗi nhân vật được biểu diễn bằng cây khớp xương 2D (Hierarchical 2D Skeleton):
    - `root (hip)` $\rightarrow$ `spine` $\rightarrow$ `neck` $\rightarrow$ `head`
    - `neck` $\rightarrow$ `shoulder_L/R` $\rightarrow$ `elbow_L/R` $\rightarrow$ `hand_L/R` $\rightarrow$ `weapon_socket`
    - `hip` $\rightarrow$ `knee_L/R` $\rightarrow$ `ankle_L/R`
  - Trang bị lớp vẽ phụ kiện đặc trưng Hắc Ám Tây Du: Vòng Kim Cô, Lông vũ vương miện (Pheasant Feathers), Khăn choàng đỏ tính toán vật lý sóng lượn, Thiết Bảng Như Ý, Tam Tiêm Đảo, Bàn tay Phật khổng lồ.
- **Thư viện động tác chiến đấu (`CombatActionPresets`):**
  - Chứa các chuỗi Keyframe & hàm toán học nội suy (Cubic Ease-In-Out, Anticipation -> Fast Strike -> Impact Hitstop -> Follow-through Recovery) cho các thế đánh: `idle_aura`, `heavy_charge`, `weapon_clash`, `staff_flurry`, `sky_leap_strike`, `giant_palm_slam`, `knockback_slide`.

### 3.6. Tầng 6: Tầng Kết Xuất Video (Video Compositor & Renderer)
- **Hạ tầng Binary FFmpeg Đầy Đủ (FFmpeg & FFprobe Portable Strategy):**
  - Hệ thống yêu cầu bộ binary thực thi đầy đủ gồm cả `ffmpeg.exe` và `ffprobe.exe` (không dùng gói rút gọn `imageio-ffmpeg` do thiếu `ffprobe` phục vụ kiểm định kỹ thuật).
  - Đường dẫn binary được cấu hình linh hoạt qua biến môi trường `FFMPEG_PATH` và `FFPROBE_PATH` trong `.env` và nạp vào `AppConfig`. Nếu không cấu hình, hệ thống tìm kiếm trong `PATH` hệ thống hoặc thư mục mặc định `C:\ffmpeg\bin\`.
- **Luồng truyền khung hình trực tiếp (Direct FFmpeg Frame Piping):**
  - Thay vì ghi hàng nghìn tệp `.png` ra ổ cứng gây nghẽn I/O, Tầng Đồ Họa xuất bộ đệm khung hình (`rawvideo` RGB24 hoặc luồng ảnh nén nhẹ theo từng phân cảnh) đẩy trực tiếp qua `stdin` của tiến trình `ffmpeg`.
- **Cấu hình mã hóa chuẩn (Encoding Profile):**
  - Video: `-c:v libx264 -preset fast -crf 21 -pix_fmt yuv420p -vf scale=1080:1920`
  - Audio: `-c:a aac -b:a 192k -ar 44100`
  - Tối ưu phát trực tuyến: `-movflags +faststart` để trình duyệt Web và ứng dụng Telegram có thể phát video ngay lập tức mà không cần tải hết toàn bộ tệp.

---

## 4. Nguyên Tắc Cô Lập Lỗi & Quản Lý Tài Nguyên (Fault Isolation & Resource Governance)

### 4.1. Nguyên tắc cô lập lỗi (Fault Isolation)
- **Cô lập cấp độ Phân cảnh (Scene-Level Isolation):** Nếu việc vẽ một hiệu ứng phụ hoặc tải một tệp SFX nhỏ trong `scene_03` gặp sự cố, hệ thống ghi cảnh báo (warning log), bỏ qua hiệu ứng phụ đó và tiếp tục dựng cảnh với tư thế chiến đấu mặc định, không làm hỏng toàn bộ video 3 phút.
- **Cô lập cấp độ Kênh giao tiếp (Channel Isolation):** Lỗi mất kết nối mạng tới máy chủ Telegram hoàn toàn không ảnh hưởng đến Web App Local và tiến trình đang render trong hàng đợi.
- **Giới hạn thời gian thực thi (Execution Timeout):** Mỗi bước (TTS, Render từng cảnh, FFmpeg muxing) đều có `timeout` bảo vệ (ví dụ: tối đa 180 giây cho một lần gọi FFmpeg) để ngăn chặn tiến trình treo vĩnh viễn (zombie process).

### 4.2. Quản lý RAM, CPU và Ổ cứng (Resource Governance)
- **Quản lý RAM (Memory Ceiling):**
  - Không bao giờ giữ toàn bộ các khung hình của video 3 phút trong bộ nhớ RAM.
  -(Một khung hình 1080x1920 RGB chiếm ~6.2 MB; 3 phút ở 30 FPS là 5,400 khung hình $\approx 33.5\text{ GB RAM}$ nếu giữ trong bộ nhớ!).
  - **Giải pháp bắt buộc:** Khởi tạo đúng **1 bộ đệm khung hình (Single Frame Buffer ~6.2 MB)** trong RAM, vẽ xong khung hình thứ $i$ thì đẩy ngay vào đường ống FFmpeg (`ffmpeg.stdin.write(frame_bytes)`), sau đó tái sử dụng bộ đệm cho khung hình thứ $i+1$. Nhờ đó, mức tiêu thụ RAM luôn giữ ổn định dưới **300 MB** cho dù video dài 1 phút hay 3 phút.
- **Quản lý Ổ cứng & Tệp tạm (Disk & Temp File Hygiene):**
  - Mọi tệp âm thanh từng cảnh chỉ được tạo trong thư mục cô lập `out/temp/<job_id>/`.
  - Sử dụng khối `try ... finally` bắt buộc trong Tầng Điều Phối: Ngay khi tác vụ chuyển sang `completed` hoặc `failed`, thư mục `out/temp/<job_id>/` phải được xóa sạch hoàn toàn, chỉ giữ lại tệp kết quả cuối cùng `out/<job_id>.mp4` (~15 – 45 MB).
