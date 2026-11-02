# BÁO CÁO NGHIỆM THU KỸ THUẬT: FFMPEG PORTABLE & XỬ LÝ ÂM THANH PRE-STAGE 4.2
**Dự án:** Dark Myth Stickman Auto-Studio  
**Phạm vi:** Pre-Stage 4.2 – Xác minh FFmpeg Portable & Quy trình Đệm Âm thanh (Audio Padding)  
**Tài liệu tham chiếu:** `docs/PRE_STAGE_4_2_FFMPEG_VERIFICATION.md`  
**Ngày thực hiện:** 2026-10-31  
**Môi trường kiểm định:** Windows 11, Python 3.15.2 (`.venv`), Git master  
**Tiêu chuẩn chất lượng:** Evidence-First Verification (100% bằng chứng terminal thực tế)  

---

## 1. TRẠNG THÁI CÀI ĐẶT FFMPEG PORTABLE

| Thành phần | Vị trí cài đặt | Phiên bản thực tế | Trạng thái |
| :--- | :--- | :--- | :---: |
| **`ffmpeg.exe`** | `C:\ffmpeg\bin\ffmpeg.exe` | `ffmpeg version 9.0.2-essentials_build-www.gyan.dev` | **PASS** |
| **`ffprobe.exe`** | `C:\ffmpeg\bin\ffprobe.exe` | `ffprobe version 9.0.2-essentials_build-www.gyan.dev` | **PASS** |
| **`ffplay.exe`** | `C:\ffmpeg\bin\ffplay.exe` | `ffplay version 9.0.2-essentials_build-www.gyan.dev` | **PASS** |
| **Encoder H.264** | `libx264` tích hợp | `libx264 - H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10` | **PASS** |
| **Encoder Audio** | `aac` tích hợp | `aac - AAC (Advanced Audio Coding)` | **PASS** |
| **Encoder MP3** | `libmp3lame` tích hợp | `libmp3lame - MP3 (MPEG audio layer 3)` | **PASS** |

> [!NOTE]
> **Tuân thủ quy tắc bảo mật & Git:**
> - Toàn bộ binary được cài đặt tại `C:\ffmpeg\bin\`, **hoàn toàn nằm ngoài cây thư mục dự án**.
> - Không sửa đổi biến môi trường `PATH` toàn hệ thống (không yêu cầu quyền Administrator).
> - Không đưa bất kỳ tệp thực thi `.exe` nào vào repository hoặc lịch sử Git.
> - Đường dẫn được quản lý linh hoạt qua biến môi trường `FFMPEG_PATH` và `FFPROBE_PATH` trong `.env`.

---

## 2. BẰNG CHỨNG KIỂM THỬ FFMPEG & FFPROBE THỰC TẾ

Script thực thi kiểm định: [`scripts/verify_ffmpeg_portable.py`](file:///c:/Users/phamtrong/Desktop/video%20agent/scripts/verify_ffmpeg_portable.py)  
Lệnh chạy: `.\.venv\Scripts\python.exe scripts\verify_ffmpeg_portable.py`

### Đầu ra Terminal nguyên bản (Exit Code 0):
```text
==================================================
PRE-STAGE 4.2: FFMPEG PORTABLE VERIFICATION
==================================================
STEP 1: Checking binary existence...
  ffmpeg : C:\ffmpeg\bin\ffmpeg.exe -> True
  ffprobe: C:\ffmpeg\bin\ffprobe.exe -> True

STEP 2: Checking versions...
  [ffmpeg]  ffmpeg version 9.0.2-essentials_build-www.gyan.dev Copyright (c) 2000-2026 the FFmpeg developers
  [ffprobe] ffprobe version 9.0.2-essentials_build-www.gyan.dev Copyright (c) 2007-2026 the FFmpeg developers

STEP 3: Checking required encoders (libx264, aac)...
  Encoder libx264 available: True
  Encoder aac available    : True

STEP 4: Rendering 1.0s 1080x1920 test MP4 video with FFmpeg...
  Test MP4 generated successfully: C:\Users\phamtrong\Desktop\video agent\out\test_ffmpeg_probe.mp4
  File size: 9575 bytes (> 0)

STEP 5: Verifying video with ffprobe JSON metadata...
  Video Codec     : h264 (Expected: h264)
  Resolution      : 1080x1920 (Expected: 1080x1920)
  Audio Codec     : aac (Expected: aac)
  Duration        : 1.000s (Expected: ~1.0s)
  Cleaned up test video.

==================================================
FFMPEG & FFPROBE PORTABLE VERIFICATION: ALL 5 STEPS PASSED
==================================================
```

---

## 3. BẰNG CHỨNG XỬ LÝ ÂM THANH: ĐỆM 0,30 GIÂY SILENCE (AUDIO PADDING)

Script thực thi kiểm định: [`scripts/verify_audio_padding.py`](file:///c:/Users/phamtrong/Desktop/video%20agent/scripts/verify_audio_padding.py)  
Lệnh chạy: `.\.venv\Scripts\python.exe scripts\verify_audio_padding.py`

### Quy trình 7 bước đã kiểm chứng:
1. Tạo tệp âm thanh nguồn MP3 mẫu bằng FFmpeg (`sine 440Hz, 128 kbps, 44.1kHz`).
2. Đo thời lượng gốc bằng `mutagen.mp3.MP3`: **`2.038 giây`**.
3. Nạp vào `Pydub.AudioSegment` (độ dài đọc được: `2000 ms`), tạo khoảng lặng 300ms (`AudioSegment.silent(duration=300)`) và ghép nối: độ dài sau ghép đạt **`2300 ms`** (tăng đúng `300 ms`).
4. Xuất ra tệp MP3 mới (`out/test_padding_padded.mp3`).
5. Đo thời lượng sau đệm bằng `Mutagen`: **`2.351 giây`**.
6. So sánh độ tăng: $\Delta = 2.351 - 2.038 = \mathbf{0.313\text{ giây}}$.  
   *Giải thích kỹ thuật:* Chuẩn mã hóa MP3 (MPEG-1 Layer 3) hoạt động theo từng khung hình 1,152 mẫu âm thanh ($\approx 26.1\text{ms}$ tại 44.1kHz), do đó sai số lượng tử hóa khung MP3 từ 10–25ms là hoàn toàn tự nhiên và chuẩn xác theo đặc tả của chuẩn nén LAME/FFmpeg. Mức tăng $0.313\text{s}$ nằm hoàn hảo trong dải dung sai an toàn $[0.28\text{s}, 0.35\text{s}]$.
7. Kiểm chứng tệp không bị suy hao hoặc hỏng metadata: Số kênh mono/stereo được bảo toàn, sample rate `44100 Hz`, dung lượng tăng từ `33,061 bytes` lên `38,077 bytes`.

### Đầu ra Terminal nguyên bản (Exit Code 0):
```text
==================================================
PRE-STAGE 4.2: AUDIO PADDING VERIFICATION
==================================================
STEP 1: Generating source MP3 using FFmpeg...
  Source file generated: out\test_padding_source.mp3 (33061 bytes)

STEP 2: Measuring initial duration with Mutagen...
  Initial Duration : 2.038s
  Sample Rate      : 44100 Hz
  Bitrate          : 127997 bps (127 kbps)

STEP 3: Opening with Pydub and appending 300ms (0.30s) silence...
  Pydub parsed sound length: 2000 ms
  Padded sound length: 2300 ms (added 300 ms)

STEP 4: Exporting padded audio to MP3...
  Padded file exported: out\test_padding_padded.mp3 (38077 bytes)

STEP 5: Measuring padded duration with Mutagen...
  Padded Duration         : 2.351s
  Delta (Padded - Initial): 0.313s (Target: ~0.300s)

STEP 6: Validating duration delta tolerance...
  Tolerance check PASSED: 0.313s is within expected range [0.28s, 0.35s].

STEP 7: Checking audio file integrity...
  Audio integrity confirmed: channels, sample rate, and size verified.
  Cleaned up temporary test files.

==================================================
AUDIO PADDING VERIFICATION PASSED (ALL 7 STEPS)
==================================================
```

---

## 4. KIỂM TRA MANIFEST DEPENDENCIES (`requirements.txt`)

Đã đối chiếu trực tiếp danh mục thư viện trong [`requirements.txt`](file:///c:/Users/phamtrong/Desktop/video%20agent/requirements.txt):

| Tên Package | Khai Báo trong `requirements.txt` | Phiên Bản Đã Cài Đặt Trong `.venv` | Trạng Thái |
| :--- | :---: | :---: | :---: |
| `edge-tts` | `edge-tts>=6.1.9` (Dòng 9) | `7.3.1` | **PASS** |
| `pydub` | `pydub>=0.25.1` (Dòng 10) | `0.25.1` | **PASS** |
| `audioop-lts` | `audioop-lts>=0.2.1` (Dòng 11) | `0.2.2` | **PASS** (Tương thích Python 3.15) |
| `mutagen` | `mutagen>=1.46.0` (Dòng 12) | `1.48.1` | **PASS** |
| `google-genai` | `google-genai>=1.0.0` (Dòng 16) | `2.34.0` | **PASS** |

*Kết luận:* 100% các dependency phục vụ Audio Pipeline và Gemini SDK đã được khai báo chính thức trong manifest để đảm bảo môi trường có thể tái lập hoàn toàn trên bất kỳ máy trạm mới nào.

---

## 5. CẤU HÌNH ỨNG DỤNG (`AppConfig` & `.env`)

Đã bổ sung và hoàn thiện cơ chế phân giải đường dẫn binary động trong [`app/core/config.py`](file:///c:/Users/phamtrong/Desktop/video%20agent/app/core/config.py):

```python
# Resolve ffmpeg_path
raw_ffmpeg = os.getenv("FFMPEG_PATH", "").strip()
resolved_ffmpeg: Optional[str] = None
if raw_ffmpeg and Path(raw_ffmpeg).is_file():
    resolved_ffmpeg = str(Path(raw_ffmpeg).resolve())
elif shutil.which("ffmpeg"):
    resolved_ffmpeg = shutil.which("ffmpeg")
elif Path(r"C:\ffmpeg\bin\ffmpeg.exe").is_file():
    resolved_ffmpeg = str(Path(r"C:\ffmpeg\bin\ffmpeg.exe").resolve())

# Resolve ffprobe_path
raw_ffprobe = os.getenv("FFPROBE_PATH", "").strip()
resolved_ffprobe: Optional[str] = None
if raw_ffprobe and Path(raw_ffprobe).is_file():
    resolved_ffprobe = str(Path(raw_ffprobe).resolve())
elif shutil.which("ffprobe"):
    resolved_ffprobe = shutil.which("ffprobe")
elif Path(r"C:\ffmpeg\bin\ffprobe.exe").is_file():
    resolved_ffprobe = str(Path(r"C:\ffmpeg\bin\ffprobe.exe").resolve())
```

- **File mẫu [`.env.example`](file:///c:/Users/phamtrong/Desktop/video%20agent/.env.example):** Đã bổ sung 2 biến cấu hình chuẩn:
  ```ini
  FFMPEG_PATH="C:\\ffmpeg\\bin\\ffmpeg.exe"
  FFPROBE_PATH="C:\\ffmpeg\\bin\\ffprobe.exe"
  ```
- **File thực tế [`.env`](file:///c:/Users/phamtrong/Desktop/video%20agent/.env):** Đã nạp chính xác đường dẫn portable `C:\ffmpeg\bin\ffmpeg.exe` và `C:\ffmpeg\bin\ffprobe.exe`.
- **Kiểm thử Unit Test:** Bổ sung `test_config_resolves_ffmpeg_and_ffprobe_paths` vào `tests/test_config_and_logger.py`, nâng tổng số bài test toàn dự án lên **39/39 PASSED**.

---

## 6. DANH SÁCH VẤN ĐỀ CÒN TỒN TẠI & GIẢI PHÁP

1. **Cảnh báo Pydub khi không có biến môi trường PATH:**  
   - *Hiện tượng:* Khi `C:\ffmpeg\bin` không nằm trong biến môi trường `PATH` toàn hệ thống, Pydub có thể xuất cảnh báo RuntimeWarning nếu không được chỉ định converter trước.  
   - *Giải pháp đã tích hợp:* `AudioEngine` sẽ chủ động nạp `cfg.ffmpeg_path` vào `AudioSegment.converter` và chèn tạm vào `os.environ["PATH"]` trong phạm vi tiến trình chạy của Python, loại bỏ hoàn toàn cảnh báo này mà không cần can thiệp quyền Admin vào Windows Registry.

---

## 7. BẢNG TỔNG HỢP NGHIỆM THU (ACCEPTANCE MATRIX)

| STT | Hạng Mục Nghiệm Thu Pre-Stage 4.2 | Kết Quả Thực Tế | Đánh Giá |
| :-: | :--- | :--- | :---: |
| 1 | Cài đặt FFmpeg Portable đầy đủ tại `C:\ffmpeg\bin\` | Đã cài `ffmpeg.exe` (105MB) và `ffprobe.exe` (105MB), không yêu cầu quyền Admin | **PASS** |
| 2 | Kiểm tra `ffmpeg -version` & `ffprobe -version` | Phiên bản `9.0.2-essentials_build-www.gyan.dev` | **PASS** |
| 3 | Kiểm tra encoder `libx264` và `aac` | Đầy đủ cả 2 encoder cần thiết cho render video 9:16 | **PASS** |
| 4 | Render video MP4 1080x1920 & Thẩm định bằng `ffprobe` | Video sinh ra dung lượng > 0, codec `h264`, audio `aac`, kích thước `1080x1920`, thời lượng `1.0s` | **PASS** |
| 5 | Thử nghiệm đệm 0.30s silence bằng Pydub + Mutagen | Tăng từ `2.038s` lên `2.351s` ($\Delta = 0.313\text{s}$, đạt chuẩn dung sai MP3) | **PASS** |
| 6 | Kiểm tra manifest dependencies trong `requirements.txt` | 5/5 package (`edge-tts`, `pydub`, `audioop-lts`, `mutagen`, `google-genai`) đã khai báo chuẩn | **PASS** |
| 7 | Cấu hình `AppConfig`, `.env.example`, `.env` | Hỗ trợ `FFMPEG_PATH` và `FFPROBE_PATH`, có fallback và validation | **PASS** |
| 8 | Toàn bộ kiểm thử tự động toàn dự án (`pytest`) | **39/39 passed in 0.23s (0 failed)** | **PASS** |

---

> [!IMPORTANT]
> **KỶ LUẬT GIAI ĐOẠN:** Tôi tuân thủ tuyệt đối chỉ thị: **KHÔNG** triển khai TTS Engine, **KHÔNG** tạo file âm thanh giả, và **DỪNG LẠI HOÀN TOÀN TẠI ĐÂY** để chờ bạn xem xét, phê duyệt trước khi chuyển sang **Giai đoạn 4.2 – Vietnamese TTS Engine & Audio Timing Engine**.
