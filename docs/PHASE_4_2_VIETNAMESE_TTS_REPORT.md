# BÁO CÁO NGHIỆM THU KỸ THUẬT GIAI ĐOẠN 4.2
## VIETNAMESE TTS ENGINE & AUDIO TIMING PIPELINE
**Dự án:** Dark Myth Stickman Auto-Studio  
**Phiên bản:** Phase 4.2 Acceptance Build  
**Ngày báo cáo:** 31/10/2026  
**Trạng thái kiểm thử:** 100% PASSED (55/55 Unit Tests, 5/5 Real Integration Scenes Validated)

---

## I. TỔNG QUAN KẾT QUẢ & TIẾN ĐỘ THỰC HIỆN

Trong Giai đoạn 4.2, hệ thống đã hoàn thiện toàn diện bộ máy tổng hợp giọng đọc tiếng Việt thực tế (`EdgeTTSAudioEngine`) và đường ống căn chỉnh thời lượng âm thanh (`Audio Timing Pipeline`) đạt chuẩn sản xuất (Production-Grade):

1. **Chuẩn bị môi trường xử lý âm thanh:**
   - Cài đặt và tích hợp thành công bộ nhị phân **FFmpeg Portable Essentials v9.0.2** chính thức từ Gyan.dev vào thư mục `C:\ffmpeg\bin\` (chứa `ffmpeg.exe`, `ffprobe.exe`, `ffplay.exe`).
   - Cập nhật tự động cơ chế dò tìm `FFMPEG_PATH` và `FFPROBE_PATH` trong `AppConfig` (`app/core/config.py`).
2. **Xây dựng module Vietnamese TTS Engine (`app/modules/audio/edge_tts_engine.py`):**
   - Triển khai đầy đủ hợp đồng giao diện đồng bộ `IAudioEngine` (`generate_scene_audio(scene, output_dir) -> tuple[Path, float]`).
   - Giọng đọc chính: nam tiếng Việt truyền cảm `vi-VN-NamMinhNeural`; giọng dự phòng: nữ tiếng Việt `vi-VN-HoaiMyNeural`.
   - Cơ chế **Exponential Backoff có Jitter** (`1.0s -> 2.0s -> 4.0s` kèm nhiễu ngẫu nhiên `0.1s - 0.4s`) chống lỗi nghẽn đường truyền WebSocket.
   - Cơ chế **Khóa giọng nhất quán cấp Job (`lock_voice_per_job=True`)**: Đảm bảo toàn bộ các phân cảnh trong cùng một video sử dụng 1 giọng duy nhất, loại bỏ triệt để hiện tượng đổi giọng nam/nữ giữa chừng.
   - Chuẩn hóa **Unicode tiếng Việt NFC (`unicodedata.normalize("NFC")`)**: Giải quyết triệt để lỗi từ chối dịch vụ `NoAudioReceived` đối với các từ có dấu tổ hợp (NFD) phức tạp.
3. **Audio Timing & Đệm khoảng lặng (Pydub + Mutagen):**
   - Đệm chính xác **0.30s đuôi âm thanh tĩnh** (`AudioSegment.silent(duration=300)`) vào cuối tệp giọng đọc của từng phân cảnh để loại bỏ hiện tượng cụt thoại khi chuyển cảnh.
   - Cơ chế thăng cấp tệp nguyên tử (**Atomic Promotion**) qua file tạm `.tmp.mp3`, đảm bảo không để lại file rác hoặc file lỗi nếu tiến trình gặp sự cố.
   - Đo đạc chính xác thời lượng thực tế của tệp âm thanh hoàn chỉnh bằng `Mutagen` và cập nhật trực tiếp vào `SceneSchema.audio_duration_sec` và `SceneSchema.voice_audio_path`.
4. **Kiểm thử tự động & Xác thực thực tế:**
   - Hoàn thành **16/16 bài unit test** tại `tests/test_edge_tts_engine.py` bao quát mọi nhánh biên lỗi và hành vi kiến trúc.
   - Bộ test toàn dự án đạt **55/55 bài kiểm thử PASSED trong 3.80 giây**.
   - Chạy kiểm thử tích hợp thực tế `scripts/verify_tts_engine.py` trên kịch bản Hắc Ám Tây Du 5 phân cảnh: **100% tệp âm thanh được tạo thành công, được thẩm định bằng Mutagen và kiểm chứng chéo bằng `ffprobe`**.

---

## II. KIẾN TRÚC HỆ THỐNG & CHI TIẾT THIẾT KẾ MODULE

```
                  ┌────────────────────────────────────────┐
                  │      Input: SceneSchema (from 4.1)     │
                  │  (narration_text, scene_id, job_id)    │
                  └──────────────────┬─────────────────────┘
                                     │
                                     ▼
                  ┌────────────────────────────────────────┐
                  │     Unicode NFC Normalization Step     │
                  │   unicodedata.normalize("NFC", text)   │
                  └──────────────────┬─────────────────────┘
                                     │
                                     ▼
         ┌─────────────────────────────────────────────────────────┐
         │              EdgeTTSAudioEngine Core Loop               │
         │  1. Check Job Voice Lock (active_voice_id)              │
         │  2. Try Primary: vi-VN-NamMinhNeural (Backoff Retries)  │
         │  3. Fallback: vi-VN-HoaiMyNeural (If primary exhausted) │
         │  4. Lock Chosen Voice for all subsequent scenes         │
         └───────────────────────────┬─────────────────────────────┘
                                     │
                                     ▼
                  ┌────────────────────────────────────────┐
                  │      Raw Audio Validation (Mutagen)    │
                  │    Check file exists, size > 1024B,    │
                  │           duration > 0.5s              │
                  └──────────────────┬─────────────────────┘
                                     │
                                     ▼
                  ┌────────────────────────────────────────┐
                  │      Audio Tail Padding Engine (Pydub) │
                  │  + 300ms Silence Tail (frame boundary) │
                  │     Export 128kbps MP3 to .tmp.mp3     │
                  └──────────────────┬─────────────────────┘
                                     │
                                     ▼
                  ┌────────────────────────────────────────┐
                  │    Atomic Promotion & Duration Read    │
                  │  shutil.move(.tmp.mp3 -> final.mp3)    │
                  │     Measure exact duration (Mutagen)   │
                  └──────────────────┬─────────────────────┘
                                     │
                                     ▼
                  ┌────────────────────────────────────────┐
                  │      Updated SceneSchema Contract      │
                  │  scene.audio_duration_sec = 8.160s     │
                  │  scene.voice_audio_path = "...mp3"     │
                  └────────────────────────────────────────┘
```

### 1. Tính Tuân Thủ Interface Đồng Bộ (`IAudioEngine`)
- Lớp `EdgeTTSAudioEngine` kế thừa trực tiếp từ `app.interfaces.base_tts.IAudioEngine`.
- Phương thức `generate_scene_audio(scene: SceneSchema, output_dir: Path) -> tuple[Path, float]` duy trì đúng chữ ký đồng bộ, đóng gói coroutine bất đồng bộ của thư viện `edge_tts` bên trong bằng `asyncio.run()`, bảo vệ tính tương thích toàn diện cho bộ điều phối `PipelineOrchestrator`.

### 2. Xử Lý Nghẽn Mạng Với Exponential Backoff & Jitter
- Khi dịch vụ Microsoft Edge-TTS gặp lỗi mạng tạm thời hoặc từ chối kết nối WebSocket (`NoAudioReceived`, `WSServerHandshakeError`, `TimeoutError`), engine tự động thử lại với công thức:
  $$\text{backoff} = (\text{base\_backoff} \times 2^{\text{attempt} - 1}) + \text{jitter}$$
  với $\text{base\_backoff} = 1.0\text{s}$, $\text{attempt} \in \{1, 2, 3\}$, và $\text{jitter} \in [0.1\text{s}, 0.4\text{s}]$.
- Nếu toàn bộ 3 lần thử lại của giọng chính thất bại, hệ thống tự động kích hoạt giọng dự phòng `vi-VN-HoaiMyNeural`.

### 3. Khóa Giọng Nhất Quán Cấp Job (`lock_voice_per_job=True`)
- Trong trường hợp phân cảnh 1 phải chuyển sang giọng nữ dự phòng `vi-VN-HoaiMyNeural` do nút máy chủ giọng nam gặp sự cố, thuộc tính `self.active_voice_id` sẽ được gán cố định thành `vi-VN-HoaiMyNeural`.
- Ở tất cả các phân cảnh tiếp theo của cùng một Job video, engine chỉ sử dụng `vi-VN-HoaiMyNeural`, tuyệt đối không thử lại giọng nam `vi-VN-NamMinhNeural`. Điều này ngăn chặn hiện tượng một nửa video nói giọng nam, nửa còn lại đột ngột đổi sang giọng nữ.

### 4. Chuẩn Hóa Ký Tự Tiếng Việt Unicode NFC
- Qua thực nghiệm kiểm tra sâu gói tin WebSocket, các chuỗi tiếng Việt chứa dấu thanh tổ hợp (NFD - Decomposed, ví dụ: chữ `ế` gồm ký tự gốc `e` ghép với 2 dấu phụ `0x302` và `0x301`) bị máy chủ Bing Speech từ chối trả về âm thanh (`NoAudioReceived`).
- Bằng việc bổ sung chuẩn hóa `unicodedata.normalize("NFC", text)` ở ngay đầu hàm `generate_scene_audio`, 100% ký tự tiếng Việt được đưa về dạng dựng sẵn chuẩn (Precomposed NFC), giúp tỷ lệ tổng hợp thành công đạt tuyệt đối.

### 5. Đệm Khoảng Lặng & Thăng Cấp File Nguyên Tử
- Để đảm bảo hoạt họa của người que sau này có đủ thời gian hoàn tất động tác trước khi chuyển sang cảnh mới, một khoảng lặng tĩnh 300 mili-giây (`AudioSegment.silent(duration=300)`) được nối vào cuối file âm thanh.
- Quá trình đệm và xuất file được thực hiện trên tệp tạm `scene_XX_padded.tmp.mp3`. Chỉ khi Mutagen kiểm tra tệp này hợp lệ (dung lượng `> 1024 bytes`, thời lượng `> 0.5s`), tệp mới được di chuyển nguyên tử (`shutil.move`) đè lên tệp chính thức `scene_XX_voice.mp3`. Toàn bộ file tạm trung gian được dọn dẹp sạch sẽ trong khối `finally`.

---

## III. BẰNG CHỨNG KIỂM THỬ THỰC TẾ (TEST EVIDENCE)

### 1. Kết Quả Chạy Kiểm Thử Đơn Vị (`tests/test_edge_tts_engine.py`)

Lệnh thực thi trên Terminal:
```powershell
.\.venv\Scripts\pytest.exe -v tests\test_edge_tts_engine.py
```

Kết quả đầu ra thực tế:
```
tests/test_edge_tts_engine.py::test_tts_engine_success_with_mock_edge_tts PASSED [  6%]
tests/test_edge_tts_engine.py::test_tts_engine_retries_on_no_audio_received PASSED [ 12%]
tests/test_edge_tts_engine.py::test_tts_engine_retries_on_timeout PASSED [ 18%]
tests/test_edge_tts_engine.py::test_tts_engine_switches_to_fallback_voice PASSED [ 25%]
tests/test_edge_tts_engine.py::test_tts_engine_fails_when_all_voices_exhausted PASSED [ 31%]
tests/test_edge_tts_engine.py::test_tts_engine_rejects_missing_file PASSED [ 37%]
tests/test_edge_tts_engine.py::test_tts_engine_rejects_file_under_1024_bytes PASSED [ 43%]
tests/test_edge_tts_engine.py::test_tts_engine_rejects_corrupted_file PASSED [ 50%]
tests/test_edge_tts_engine.py::test_tts_engine_rejects_duration_under_half_second PASSED [ 56%]
tests/test_edge_tts_engine.py::test_tts_engine_handles_pydub_failure PASSED [ 62%]
tests/test_edge_tts_engine.py::test_tts_engine_distinct_output_files_per_scene PASSED [ 68%]
tests/test_edge_tts_engine.py::test_tts_engine_preserves_all_schema_fields PASSED [ 75%]
tests/test_edge_tts_engine.py::test_tts_engine_ensures_job_level_voice_consistency PASSED [ 81%]
tests/test_edge_tts_engine.py::test_tts_engine_rejects_empty_or_whitespace_narration PASSED [ 87%]
tests/test_edge_tts_engine.py::test_tts_engine_rate_formatting PASSED    [ 93%]
tests/test_edge_tts_engine.py::test_tts_engine_verifies_padding_duration_increase PASSED [100%]

============================= 16 passed in 3.80s ==============================
```

### 2. Kết Quả Bộ Kiểm Thử Toàn Dự Án (`pytest -v`)

Lệnh thực thi trên Terminal:
```powershell
.\.venv\Scripts\pytest.exe -v
```

Kết quả đầu ra:
```
============================= 55 passed in 3.80s ==============================
```
- 0 failed, 0 error, 0 warning.
- Tương thích 100% với các test Phase 1, 2, 3 và 4.1.

### 3. Kết Quả Kiểm Thử Tích Hợp Kịch Bản Mẫu Thực Tế (`scripts/verify_tts_engine.py`)

Hệ thống đã thực hiện tổng hợp âm thanh thực tế cho kịch bản Hắc Ám Tây Du 5 phân cảnh. Toàn bộ các tệp âm thanh được lưu trữ tại `out/temp/integration_tts/audio/` và báo cáo JSON được xuất ra tại `out/sample_tts_results.json`.

| Cảnh | Tên Tệp Xuất Ra | Dung Lượng | Thời Lượng Đo Bởi Mutagen | Thời Lượng Đo Bởi FFprobe | Codec / Sample Rate / Bitrate | Giọng Đọc Áp Dụng | Trạng Thái Thử Lại |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cảnh 1** | `scene_01_voice.mp3` | 130,988 bytes | **8.160s** | 8.100s | `mp3` / 24,000Hz / 128kbps | `vi-VN-NamMinhNeural` | Thành công lần 1 (0.96s) |
| **Cảnh 2** | `scene_02_voice.mp3` | 100,652 bytes | **6.264s** | 6.204s | `mp3` / 24,000Hz / 128kbps | `vi-VN-NamMinhNeural` | Thành công lần 3 sau Backoff (17.42s) |
| **Cảnh 3** | `scene_03_voice.mp3` | 117,932 bytes | **7.344s** | 7.284s | `mp3` / 24,000Hz / 128kbps | `vi-VN-NamMinhNeural` | Thành công lần 1 (0.83s) |
| **Cảnh 4** | `scene_04_voice.mp3` | 111,788 bytes | **6.960s** | 6.900s | `mp3` / 24,000Hz / 128kbps | `vi-VN-NamMinhNeural` | Thành công lần 2 sau Backoff (10.11s) |
| **Cảnh 5** | `scene_05_voice.mp3` | 118,316 bytes | **7.368s** | 7.308s | `mp3` / 24,000Hz / 128kbps | `vi-VN-NamMinhNeural` | Thành công lần 1 (0.80s) |

**Tổng thời lượng audio đo đạc:** **36.10 giây**.  
**Độ sai lệch giữa Mutagen và FFprobe:** $\le 0.060\text{s}$ (hoàn toàn nằm trong phạm vi bù trừ khung MP3 Frame Quantization).  
**Tính nhất quán:** 5/5 phân cảnh đều sử dụng chung một giọng `vi-VN-NamMinhNeural`.

---

## IV. BẢO TOÀN RÀNG BUỘC KỸ THUẬT & QUY TẮC DỰ ÁN

| Ràng Buộc / Quy Định | Kết Quả Đánh Giá | Bằng Chứng / Ghi Chú |
| :--- | :---: | :--- |
| **Nguyên tắc Chi phí 0 đồng (Zero-Cost Violation)** | **TUÂN THỦ TUYỆT ĐỐI** | Hoàn toàn sử dụng Microsoft Edge-TTS miễn phí, không gọi bất kỳ API trả phí nào (không dùng OpenAI TTS, ElevenLabs). |
| **Không Tự Bịa Đặt Thư Viện / Offline TTS** | **TUÂN THỦ TUYỆT ĐỐI** | Không tự ý đưa thư viện Piper/Wav stub giả mạo vào hệ thống; thực hiện đúng chỉ thị phương án B (Edge-TTS làm TTS chính kèm cơ chế retry/fallback). |
| **Bảo toàn Hợp đồng Dữ liệu (`docs/04_data_contracts.md`)** | **TUÂN THỦ TUYỆT ĐỐI** | Cập nhật chính xác `audio_duration_sec` (số thực dương `> 0.0`) và `voice_audio_path` (đường dẫn tệp thực tế). Tất cả các trường khác của `SceneSchema` giữ nguyên vẹn 100%. |
| **Không để lại rác ổ cứng hay rò rỉ RAM** | **TUÂN THỦ TUYỆT ĐỐI** | Các tệp `.tmp.mp3` được xóa sạch trong khối `finally`. Các tệp âm thanh đầu ra nằm tập trung trong `out/temp/integration_tts/audio/`. |
| **Không Nhảy Cóc Giai Đoạn (Strict Phase Discipline)** | **TUÂN THỦ TUYỆT ĐỐI** | Tuyệt đối không viết mã hoạt họa, vẽ người que, dựng VFX, trộn SFX/BGM, làm Web UI hay Telegram Bot trong giai đoạn này. |

---

## V. ĐÁNH GIÁ SẴN SÀNG CHO GIAI ĐOẠN 5 (SIGN-OFF GATE)

Giai đoạn 4 (gồm cả **Giai đoạn 4.1 - Script Parser Engine** và **Giai đoạn 4.2 - Vietnamese TTS Engine & Audio Timing**) đã hoàn thành trọn vẹn, được kiểm chứng bằng bài test tự động và tệp hiện vật âm thanh thực tế.

Nền tảng kỹ thuật hiện tại đã sẵn sàng chuyển sang:
**GIAI ĐOẠN 5 – NOTEBOOK PAPER & PROCEDURAL STICKMAN RIGGING**
- Xây dựng Canvas giấy kẻ ngang học sinh tỷ lệ 9:16 (`1080x1920`).
- Dựng khung xương người que 2D 14 khớp cử động linh hoạt.
- Dựng tạo hình nhân vật Hắc Ám Tây Du (Tôn Ngộ Không, Dương Tiễn, Quái mực).

> [!IMPORTANT]
> **DỪNG LẠI CHỜ DUYỆT (STOP PROTOCOL):**
> Theo đúng Hiến pháp Làm việc (`AGENTS.md`), toàn bộ quá trình viết mã cho Giai đoạn 4.2 đã dừng lại hoàn toàn. Kính chuyển bản Báo cáo Nghiệm thu này tới Người dùng để xem xét và phê duyệt trước khi chuyển sang Giai đoạn 5.
