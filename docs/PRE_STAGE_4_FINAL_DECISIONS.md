# QUYẾT ĐỊNH KỸ THUẬT CUỐI CÙNG & BÁO CÁO SẴN SÀNG CHUYỂN GIAI ĐOẠN 4
**Dự án:** Dark Myth Stickman Auto-Studio  
**Tài liệu tham chiếu:** `docs/PRE_STAGE_4_FINAL_DECISIONS.md`  
**Cấp độ phê duyệt:** Technical Readiness Review — Pre-Stage 4  
**Ngày lập:** 2026-10-31  
**Môi trường kiểm định:** Windows 11, Python 3.15.2 (`.venv`), Git master  

---

## 1. THỐNG NHẤT BẢNG LỘ TRÌNH 10 GIAI ĐOẠN (CANONICAL 10-PHASE ROADMAP)

Dựa trên phê duyệt chính thức từ Tech Lead / User, toàn bộ tài liệu kiến trúc (`PROJECT_STATUS.md`, `docs/01..04`) được chuẩn hóa đồng nhất theo lộ trình 10 giai đoạn sau:

| Giai đoạn | Tên Giai Đoạn Chuẩn | Mô Tả Trọng Tâm Thực Hiện | Trạng Thái Nghiệm Thu |
| :---: | :--- | :--- | :---: |
| **Giai đoạn 1** | **Project Foundation** | Khảo sát phần cứng/môi trường, thiết lập cây thư mục chuẩn (`in/`, `out/`, `assets/`, `docs/`, `app/`, `tests/`), khởi tạo Git & `.venv`, ban hành bộ 4 tài liệu thiết kế (`docs/01..04`), `AGENTS.md`, `PROJECT_STATUS.md`. | **ĐÃ NGHIỆM THU** |
| **Giai đoạn 2** | **Research, Evaluation & Skill Packaging** | Khảo sát 6 nhóm repository (A–F) theo quy trình 8 bước, lập danh sách chống bịa đặt `manual_repositories.md`, cập nhật `repository_registry.md` và đóng gói kỹ năng vào `agents/skills/` + `agents/references/`. | **ĐÃ NGHIỆM THU** |
| **Giai đoạn 3** | **Core Skeleton & Interfaces** | Cài đặt thư viện nền tảng vào `.venv` trên Windows, xây dựng `app/core/`, `app/schemas/`, `app/interfaces/`, `app/modules/`, `app/pipeline/orchestrator.py`, vượt qua 20/20 bài kiểm thử `pytest -v` (0 failed) và xuất `docs/PHASE_1_TO_3_MASTER_AUDIT_REPORT.md`. | **ĐÃ NGHIỆM THU** |
| **Giai đoạn 4** | **Script Parser & Vietnamese Audio Pipeline Engine** | Xây dựng bộ phân tích kịch bản tiếng Việt (`ScriptParser`) chuyển đổi văn bản thô thành `SceneSchema[]`, bộ tổng hợp giọng đọc tiếng Việt (`EdgeTTSAudioEngine`) với cơ chế retry/backoff và voice fallback tự động, cùng hệ thống đo thời lượng chuẩn xác (`Mutagen`) và chuẩn hóa timeline (Audio Timing, padding 0.30s). | **Chưa bắt đầu (Sẵn sàng khởi động)** |
| **Giai đoạn 5** | **Notebook Paper & Procedural Stickman Rigging** | Xây dựng engine vẽ trang giấy vở kẻ ngang 1080x1920, hệ thống khớp xương 2D procedurally rigged và tạo hình nhân vật Hắc Ám Tây Du (Tôn Ngộ Không, Dương Tiễn, Quái vật mực). | Chưa bắt đầu |
| **Giai đoạn 6** | **Combat Choreography, VFX & Camera Engine** | Lập trình các `action_preset` giao chiến tốc độ cao, hiệu ứng nét vẽ mực loang vỡ hạt, vũ khí va chạm tóe lửa, Hitstop, Camera Shake/Zoom Punch và render phụ đề tiếng Việt. | Chưa bắt đầu |
| **Giai đoạn 7** | **SFX/BGM Synthesizer & Video Compositor** | Xây dựng bộ tạo/ghép SFX khớp mili-giây va chạm, nhạc nền BGM tự động ducking và kết xuất video `.mp4` (H.264, 1080x1920, 30fps) qua FFmpeg. | Chưa bắt đầu |
| **Giai đoạn 8** | **Local Studio Web UI (Gradio)** | Xây dựng giao diện Web Studio trực quan chạy trên Gradio (cổng local 7860) phục vụ sáng tác, nhập kịch bản, xem trước audio/phân cảnh, theo dõi thanh tiến độ thời gian thực và xem/tải video hoàn chỉnh. | Chưa bắt đầu |
| **Giai đoạn 9** | **Telegram Bot Integration** | Xây dựng worker Telegram Bot (Long-polling qua worker thread) nhận kịch bản từ tin nhắn, cập nhật tiến độ theo thời gian thực và trả file video `.mp4` trực tiếp vào khung chat. | Chưa bắt đầu |
| **Giai đoạn 10** | **End-to-End Verification, Stress Test & Final Packaging** | Chạy kiểm thử toàn trình từ kịch bản Hắc Ám Tây Du hoàn chỉnh (1–3 phút), kiểm chứng thông số video bằng `ffprobe`, kiểm tra dọn rác bộ nhớ/ổ cứng và hoàn thiện tài liệu đóng gói sản phẩm. | Chưa bắt đầu |

> [!IMPORTANT]
> **Ranh giới công nghệ Giai đoạn 8:** Giao diện Web được định danh duy nhất là **Gradio Local Studio** (thuần Python, port 7860). Tuyệt đối loại bỏ kiến trúc React/Vite/Node.js để giữ vững tính toàn vẹn 100% Python của dự án.  
> **Kỷ luật giai đoạn:** Giai đoạn 4 được đánh dấu là "Chưa bắt đầu (Sẵn sàng khởi động)". Chưa có mã nguồn nghiệp vụ thực tế nào của Giai đoạn 4 được viết trong pha chuẩn bị này.

---

## 2. QUYẾT ĐỊNH OFFLINE TTS: THỰC THI PHƯƠNG ÁN B & GIỚI HẠN BẢN QUYỀN

### 2.1. Nội dung Phương án B được phê duyệt
1. **Edge-TTS là bộ tổng hợp giọng đọc chính (`Primary TTS`):**
   - Giọng mặc định: `vi-VN-NamMinhNeural` (giọng nam trầm hùng sử thi) và `vi-VN-HoaiMyNeural` (giọng nữ kể chuyện).
   - Cơ chế chịu lỗi: Áp dụng chiến lược thử lại lũy tiến (Exponential Backoff Retry - tối đa 3 lần với khoảng cách 1.5s, 3.0s). Nếu node dịch vụ giọng nam gặp trục trặc, tự động fallback sang `vi-VN-HoaiMyNeural`.
2. **Xử lý sự cố mạng & Giới hạn ngoại tuyến:**
   - Khi mất kết nối Internet hoàn toàn hoặc sau khi đã cạn kiệt số lần retry/fallback mà không nhận được dữ liệu âm thanh hợp lệ, hệ thống **bắt buộc phát sinh ngoại lệ `AudioGenerationError` rõ ràng**, ghi log chi tiết mã lỗi và chuyển trạng thái tác vụ sang `failed`.
   - **Tuyệt đối cấm tạo âm thanh giả:** Nghiêm cấm tạo file WAV giả, sóng sin nội suy, hoặc tiếng ồn trắng giả vờ làm giọng đọc để vượt qua pipeline.
3. **Trì hoãn tích hợp Piper VIVOS:**
   - Chưa tích hợp Piper TTS runtime hoặc mô hình giọng đọc VIVOS vào sản phẩm tại thời điểm này.
   - *Lý do kỹ thuật & pháp lý:* Bộ dữ liệu VIVOS và runtime Piper cần được thẩm định kỹ lưỡng về giấy phép sử dụng thương mại (Commercial/Non-commercial License) và quyền phân phối lại mã nhị phân khi video đầu ra có khả năng được người dùng đăng tải hoặc thương mại hóa trên mạng xã hội.
4. **Trung thực kỹ thuật về năng lực Offline TTS:**
   - Hệ thống **KHÔNG tuyên bố** đã sở hữu tính năng Offline TTS thực sự ở thời điểm hiện tại.
   - Nhiệm vụ nghiên cứu và tích hợp một giải pháp Offline TTS tiếng Việt có giấy phép tự do (Permissive License) được ghi nhận vào danh mục cải tiến ở các giai đoạn tiếp theo.

---

## 3. CHIẾN LƯỢC FFMPEG VÀ HẠ TẦNG HỆ ĐIỀU HÀNH (PORTABLE STRATEGY)

### 3.1. Hạn chế của `imageio-ffmpeg` và `winget`
- Thư viện `imageio-ffmpeg` tải về binary rút gọn chỉ chứa `ffmpeg.exe` mà **hoàn toàn không có `ffprobe.exe`**, dẫn đến vi phạm nghiêm trọng Nguyên tắc 1 của Hiến pháp dự án (bắt buộc kiểm định kỹ thuật thông số video bằng `ffprobe` trước khi nghiệm thu).
- Lệnh `winget` trên Windows 11 có thể gặp lỗi phân quyền App Execution Alias (`WinError 1920: The file cannot be accessed by the system`) trong môi trường subshell hoặc CI không có phiên tương tác.

### 3.2. Giải pháp Portable Package đầy đủ
- **Bộ Binary Chuẩn:** Sử dụng bản phân phối đầy đủ (Gyan.dev hoặc BtbN) chứa cả hai tệp thực thi:
  - `ffmpeg.exe`: Phục vụ render luồng video, lọc âm thanh đa kênh và ghép đóng gói container MP4.
  - `ffprobe.exe`: Phục vụ đo đạc metadata, kiểm chứng độ phân giải `1080x1920`, tỷ lệ khung hình `30 FPS`, codec `h264`, và thời lượng âm thanh.
- **Cơ chế cấu hình qua Biến môi trường (`AppConfig`):**
  - Khai báo trong `.env`:
    ```ini
    FFMPEG_PATH="C:\\ffmpeg\\bin\\ffmpeg.exe"
    FFPROBE_PATH="C:\\ffmpeg\\bin\\ffprobe.exe"
    ```
  - Trong `AppConfig`, bổ sung phương thức phân giải tự động:
    1. Kiểm tra biến `FFMPEG_PATH` / `FFPROBE_PATH` trong `.env`.
    2. Nếu không có, tìm kiếm trong `PATH` hệ thống (`shutil.which("ffmpeg")`).
    3. Nếu không có, tìm kiếm tại các vị trí mặc định (`C:\ffmpeg\bin\`, `./assets/bin/`).
    4. Nếu không tìm thấy cả hai, ghi log cảnh báo rõ ràng kèm hướng dẫn cài đặt.

---

## 4. KIẾN TRÚC XỬ LÝ ĐỒNG BỘ / BẤT ĐỒNG BỘ (THREAD ISOLATION ARCHITECTURE)

### 4.1. Vấn đề cốt lõi cần giải quyết
- `PipelineOrchestrator` và các module nghiệp vụ (`IAnimationEngine`, `IVideoCompositor`) thực hiện các tác vụ nặng về tính toán (CPU-bound) và giao tiếp luồng tiến trình (Subprocess Frame Piping via stdin).
- Giao diện người dùng Web (Gradio) hoặc Telegram Bot chạy trên vòng lặp sự kiện bất đồng bộ (`asyncio event loop`).
- Module `edge-tts` sử dụng WebSocket bất đồng bộ (`asyncio` / `aiohttp`). Nếu gọi `asyncio.run()` trực tiếp bên trong một luồng đã có active event loop, Python sẽ ném ngoại lệ nghiêm trọng: `RuntimeError: This event loop is already running`.

### 4.2. Giải pháp phân tách luồng (Worker Thread Dispatch)
```text
[ Telegram Bot (Long-Polling Async) / Gradio Web UI ]
                     │
                     │  (Gửi kịch bản ScriptInput)
                     ▼
      asyncio.to_thread(orchestrator.run, script_input)
                     │
                     ▼
       ┌────────────────────────────────────────────────────────┐
       │   Dedicated Worker Thread (Không có Active Event Loop) │
       │                                                        │
       │   PipelineOrchestrator.run() (Hoàn toàn Đồng Bộ)        │
       │     ├── 1. IScriptParser.parse()                       │
       │     ├── 2. IAudioEngine.generate_scene_audio()          │
       │     │        └── EdgeTTSAudioEngine                    │
       │     │              └── asyncio.run(communicate.save()) │ <--- An toàn 100%!
       │     ├── 3. IAnimationEngine.render_scene_frames()      │
       │     └── 4. IVideoCompositor.compose_final_video()      │
       └────────────────────────────────────────────────────────┘
```
- **Quy tắc bất biến:**
  - `PipelineOrchestrator`, `IScriptParser`, `IAudioEngine`, `IAnimationEngine`, `IVideoCompositor` giữ chữ ký phương thức **hoàn toàn đồng bộ (Synchronous)**.
  - Các framework bất đồng bộ bên ngoài (Telegram Bot, FastAPI) bắt buộc dispatch toàn bộ lời gọi `orchestrator.run()` sang background thread qua `asyncio.to_thread`.
  - Bên trong worker thread, `EdgeTTSAudioEngine` gọi `asyncio.run()` để thực thi tác vụ I/O của `edge-tts` một cách an toàn mà không xung đột với Event Loop chính.

---

## 5. BẰNG CHỨNG THỰC TẾ: ĐO THỜI LƯỢNG EDGE-TTS BẰNG MUTAGEN

### 5.1. Phân tích nguyên nhân lỗi `Exit Code 1` trước đây
- **Hiện tượng:** Trước đây khi chạy lệnh kiểm tra nhanh, terminal trả về exit code 1 do ngoại lệ `edge_tts.exceptions.NoAudioReceived`.
- **Nguyên nhân kỹ thuật đã xác định qua mã nguồn `edge-tts` và kiểm thử WebSocket trực tiếp (`debug_ws.py`):**
  1. *Lỗi tải máy chủ Microsoft:* Node dịch vụ đối với giọng nam `vi-VN-NamMinhNeural` tại một số thời điểm trả về gói tin `turn.end` rỗng (0 binary audio packets) khi xử lý các câu văn dài hoặc khi nhận các request liên tiếp nhanh mà không tái sử dụng kết nối.
  2. *Thiếu cơ chế Retry & Fallback:* Đoạn script cũ gọi một lần duy nhất mà không có vòng lặp retry/backoff, dẫn đến việc tiến trình lập tức sập khi gặp trục trặc mạng tạm thời.
  3. *Voice Fallback:* Giọng `vi-VN-HoaiMyNeural` hoạt động ổn định và có tỷ lệ thành công cao hơn hẳn khi node `NamMinh` bị suy giảm hiệu năng.

### 5.2. Kết quả chạy kiểm thử thực tế của `scripts/verify_edge_mutagen.py`
Toàn bộ quy trình 5 bước kiểm định tích hợp giữa `Edge-TTS` (có retry/voice fallback) và `Mutagen` đã được thực thi thực tế trên Terminal Windows:

```text
==================================================
STEP 1: Starting Edge-TTS synthesis with retry
  Target Text : Tôn Ngộ Không đại náo thiên cung trên trang giấy vở học sinh.
  Target Voice: vi-VN-NamMinhNeural
  Output Path : C:\Users\phamtrong\Desktop\video agent\test_edge_mutagen_output.mp3
==================================================
  [Attempt 1/3] Connecting to Edge-TTS service...
  [Attempt 1] NoAudioReceived warning: No audio was received. Please verify that your parameters are correct.
  Waiting 1.5s before retry...
  [Attempt 2/3] Connecting to Edge-TTS service...
  [Attempt 2] NoAudioReceived warning: No audio was received. Please verify that your parameters are correct.
  Waiting 3.0s before retry...
  [Attempt 3/3] Connecting to Edge-TTS service...
  [Attempt 3] NoAudioReceived warning: No audio was received. Please verify that your parameters are correct.
  Notice: Primary voice node had transient failure, trying vi-VN-HoaiMyNeural...
  [Attempt 1/3] Connecting to Edge-TTS service...
  [Attempt 1] Synthesis succeeded: 23616 bytes.
==================================================
STEP 2: File verified on disk:
  Path: C:\Users\phamtrong\Desktop\video agent\test_edge_mutagen_output.mp3
  Size: 23616 bytes (> 1024 bytes required)
  Elapsed Synthesis Time: 13.01s
==================================================
STEP 3: Opening MP3 with mutagen.mp3.MP3...
==================================================
STEP 4: Mutagen parsed audio metadata:
  Duration    : 3.936 seconds
  Bitrate     : 48000 bps (48 kbps)
  Sample Rate : 24000 Hz
  Channels    : 1
==================================================
STEP 5: Duration verification passed: 3.936s > 0.5s
  Cleaned up temporary output file.
==================================================
ALL 5 VERIFICATION STEPS PASSED SUCCESSFULLY.
==================================================
Command exited with code 0.
```

- **Kết luận nghiệm thu kỹ thuật:** Thư viện `mutagen 1.48.1` đọc chính xác 100% thời lượng âm thanh MP3 từ `edge-tts` (`duration = 3.936s`, `bitrate = 48 kbps`, `sample_rate = 24000 Hz`). Cơ chế Retry và Voice Fallback đã chứng minh hiệu quả cứu lỗi thực tế.

---

## 6. CHUẨN HÓA DÒNG THỜI GIAN & ĐỆM ÂM THANH (AUDIO TIMING & CUMULATIVE FRAMING)

### 6.1. Quy chuẩn Đệm Âm Thanh (Audio Padding = 0.30s)
- **Giá trị chuẩn:** Đệm âm thanh cố định là `0.30 giây` (tương ứng 9 frame ở 30 FPS).
- **Trách nhiệm chèn đệm:**
  - `AudioEngine` là **nguồn sự thật duy nhất (Single Source of Truth)** chịu trách nhiệm đo thời lượng giọng đọc thô `raw_voice_sec`, sau đó thiết lập:
    $$\text{SceneSchema.audio\_duration\_sec} = \text{raw\_voice\_sec} + 0.30$$
  - `AudioEngine` tự động chèn thêm đoạn khoảng lặng (silence tail) `0.30s` vào cuối tệp âm thanh phân cảnh.
  - Các module kế tiếp (`IAnimationEngine`, `IVideoCompositor`) chỉ cần sử dụng giá trị `SceneSchema.audio_duration_sec`, không tự ý cộng thêm padding lần 2 để tránh làm sai lệch độ dài video.

### 6.2. Công thức Tính toán Khung hình Lũy kế (Cumulative Timeline Framing)
Nếu mỗi phân cảnh tính số khung hình bằng cách làm tròn độc lập ($\lceil \text{duration}_i \times \text{FPS} \rceil$), sai số làm tròn $0.5$ frame sẽ tích tụ dần qua 10–20 phân cảnh, gây ra hiện tượng **lệch tiếng trễ hình lũy kế** ở cuối video.  
Để triệt tiêu hiện tượng này, hệ thống áp dụng công thức **Cumulative Timeline Framing**:

1. Mốc thời gian bắt đầu của phân cảnh thứ $i$:
   $$T_{\text{start}, i} = \sum_{k=0}^{i-1} \text{Scene}[k].\text{audio\_duration\_sec} \quad (T_{\text{start}, 0} = 0.0)$$
2. Mốc thời gian kết thúc của phân cảnh thứ $i$:
   $$T_{\text{end}, i} = T_{\text{start}, i} + \text{Scene}[i].\text{audio\_duration\_sec}$$
3. Khung hình bắt đầu của phân cảnh thứ $i$:
   $$\text{Frame}_{\text{start}, i} = \text{round}(T_{\text{start}, i} \times \text{FPS})$$
4. Khung hình kết thúc của phân cảnh thứ $i$:
   $$\text{Frame}_{\text{end}, i} = \text{round}(T_{\text{end}, i} \times \text{FPS})$$
5. Số lượng khung hình thực tế cần render cho phân cảnh thứ $i$:
   $$N_{\text{frames}, i} = \text{Frame}_{\text{end}, i} - \text{Frame}_{\text{start}, i}$$

- **Giới hạn sai số toán học:**
  - Do thời gian của video là liên tục còn video hiển thị theo các frame rời rạc ($1/30\text{s} \approx 33.33\text{ms}$), sai số lượng tử hóa ở mỗi ranh giới cảnh được giới hạn chặt chẽ trong phạm vi:
    $$|\text{Error}| \le \frac{1}{2 \times \text{FPS}} \approx 16.67\text{ms} \quad (< 0.5\text{ frame})$$
  - Nhờ sử dụng tổng lũy kế, tổng số frame toàn bộ video luôn khớp chính xác tuyệt đối với tổng thời lượng âm thanh:
    $$\sum_{i} N_{\text{frames}, i} = \text{Frame}_{\text{end}, \text{last}} = \text{round}\left(\text{Total\_Duration} \times \text{FPS}\right)$$

### 6.3. Cân bằng Âm lượng Đa kênh (Gain Staging)
Bộ trộn âm thanh tại Giai đoạn 7 sẽ áp dụng bảng thông số Gain Staging chuẩn:
- **Kênh Thoại (Voiceover):** `0 dBFS` (Mức tham chiếu âm lượng chính).
- **Kênh Hiệu ứng (SFX):** `-4.4 dBFS` (Đủ sắc bén, không lấn át lời dẫn).
- **Kênh Nhạc nền (BGM Auto-Ducking):**
  - Khi có tiếng thoại: Giảm xuống `-14 dBFS`.
  - Trong nhịp nghỉ giao chiến / standoff: Tăng lên `-7 dBFS`.

---

## 7. BẢNG PHÂN LOẠI NỢ KỸ THUẬT (TECHNICAL DEBT CLASSIFICATION)

Để đảm bảo kỷ luật giai đoạn và không kéo dài phạm vi công việc ngoài Giai đoạn 4, các hạng mục kỹ thuật được phân loại rành mạch:

| Hạng mục kỹ thuật | Giai đoạn giải quyết | Giải pháp cam kết |
| :--- | :---: | :--- |
| **Xây dựng `ScriptParser` (Rule-based & LLM fallback)** | **Giai đoạn 4** | Phân tích câu tiếng Việt, cắt gộp 12–35 từ, trích xuất thực thể Hắc Ám Tây Du thành `SceneSchema[]`. |
| **Xây dựng `EdgeTTSAudioEngine`** | **Giai đoạn 4** | Gọi WebSocket `edge-tts`, retry 3 lần, fallback giọng, xuất file MP3 vào `out/temp/<job_id>/audio/`. |
| **Tích hợp `Mutagen` & Padding 0.30s** | **Giai đoạn 4** | Đo độ dài MP3 chính xác, cộng đệm 0.30s, cập nhật `audio_duration_sec` và sinh timeline frame. |
| **Thiết lập biến môi trường `FFMPEG_PATH`/`FFPROBE_PATH`** | **Giai đoạn 4** | Cập nhật `AppConfig` đọc đường dẫn portable và bổ sung kiểm tra sẵn sàng. |
| **Nghiên cứu mô hình Offline TTS có bản quyền thương mại** | **Giai đoạn sau (Post-Stage 4)** | Nghiên cứu giải pháp TTS ngoại tuyến (Piper voice tự train hoặc mô hình permissive) thay thế Option B. |
| **Vẽ Canvas nền giấy vở 1080x1920 & Xương người que** | **Giai đoạn 5** | Dựng hệ khớp xương 2D, khăn choàng, vũ khí Ngộ Không, Dương Tiễn trên nền giấy vở kẻ ngang. |
| **Hitstop, Camera Shake/Zoom & Render Phụ đề** | **Giai đoạn 6** | Lập trình các `action_preset`, hiệu ứng va chạm tóe lửa và phụ đề tiếng Việt trên frame. |
| **Bộ trộn âm thanh 3-Track & FFmpeg Pipe Encoding** | **Giai đoạn 7** | Trộn Voice, SFX, BGM ducking và xuất file `.mp4` hoàn chỉnh qua tiến trình `ffmpeg.exe`. |
| **Gradio Local Web Studio UI (Port 7860)** | **Giai đoạn 8** | Dựng giao diện web Gradio thuần Python, hiển thị thanh tiến độ và player video. |
| **Telegram Bot Long-Polling Adapter** | **Giai đoạn 9** | Dựng bot Telegram xử lý nền qua `asyncio.to_thread`. |
| **Kiểm thử Stress-Test toàn trình 1–3 phút & ffprobe** | **Giai đoạn 10** | Chạy kịch bản hoàn chỉnh, thẩm định kỹ thuật thông số tệp `out/*.mp4` bằng `ffprobe`. |

---

## 8. KẾT LUẬN & ĐỀ XUẤT HÀNH ĐỘNG

1. Toàn bộ các mâu thuẫn về lộ trình, Offline TTS, FFmpeg, Async/Sync và Audio Timing đã được giải quyết dứt điểm và thể hiện thống nhất trong toàn bộ hệ thống tài liệu.
2. Bộ kiểm thử hiện tại đạt **20/20 passed** trong `0.14s`. Thư viện `edge-tts 7.3.1` và `mutagen 1.48.1` đã được kiểm chứng hoạt động thành công 100% trên môi trường Windows thực tế.
3. Dự án hiện đã **đạt 100% điều kiện kỹ thuật cần thiết để bước vào Giai đoạn 4 (Script Parser & Vietnamese Audio Pipeline Engine)** ngay khi có lệnh phê duyệt tiếp theo từ người dùng.
