# KỸ NĂNG CHUYÊN MÔN: TẠO GIỌNG ĐỌC TIẾNG VIỆT, ĐO THỜI LƯỢNG & TRỘN ÂM THANH ĐA KÊNH (`tts_and_audio_mixing.md`)
**Phạm vi áp dụng:** Giai đoạn 4 & Giai đoạn 7 (`app/audio/`)  
**Thư viện cốt lõi sử dụng:** `edge-tts`, `pydub`, `mutagen`, `ffmpeg` / `ffprobe`, `wave`, `numpy`  

---

## 1. Quy Chuẩn Tạo Giọng Đọc Tiếng Việt (`edge-tts` + Offline Fallback)

### 1.1. Luồng chính: Sử dụng `edge-tts` (Miễn phí, Giọng Neural)
- Mã giọng đọc mặc định:
  - Giọng nam trầm hùng sử thi: `"vi-VN-NamMinhNeural"`
  - Giọng nữ dẫn truyện: `"vi-VN-HoaiMyNeural"`
- Quy đổi tốc độ đọc `voice_speed` (ví dụ `1.05` $\rightarrow$ `"+5%"`, `0.95` $\rightarrow$ `"-5%"`):
  ```python
  import edge_tts

  async def synthesize_scene_voice(text: str, output_path: str, voice: str = "vi-VN-NamMinhNeural", speed: float = 1.05):
      rate_pct = int(round((speed - 1.0) * 100))
      rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"
      communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate_str)
      await communicate.save(output_path)
  ```
- Sau khi `edge-tts` lưu tệp `.mp3`, chuẩn hóa sang `.wav` (`PCM 16-bit, 44100 Hz, Stereo`) bằng `ffmpeg` hoặc `pydub` để sẵn sàng ghép nối chính xác tới từng mẫu âm thanh (sample-accurate).

### 1.2. Luồng dự phòng bắt buộc (Offline Local TTS / Synthesizer Fallback)
Nếu máy chủ mất kết nối Internet hoặc `edge-tts` gặp lỗi mạng:
- Hệ thống **tuyệt đối không được crash**.
- Tự động tính toán thời lượng đọc tiếng Việt thực tế dựa trên số từ của `narration_text` (tốc độ chuẩn `3.2 từ/giây` nhân với `voice_speed`, tối thiểu `2.5 giây/cảnh`) và sinh tệp `.wav` dự phòng có âm sắc trầm dẫn nhịp kèm khoảng nghỉ tự nhiên, đồng thời ghi nhận `"tts_engine": "offline_fallback"` trong `RenderResult.processing_stats`.

---

## 2. Đo Thời Lượng Thực Tế Để Điều Khiển Số Lượng Khung Hình Hoạt Hình

Nguyên tắc bất di bất dịch của dự án: **Âm thanh quyết định số khung hình hoạt hình (Audio-First Timing)**.
1. Ngay sau khi tạo xong tệp âm thanh thoại của phân cảnh thứ $i$, đo thời lượng thực tế $D_{\text{voice}, i}$ (giây) bằng `ffprobe` hoặc `mutagen` / `wave`:
   ```python
   import subprocess, json

   def measure_audio_duration_sec(file_path: str) -> float:
       cmd = [
           "ffprobe", "-v", "error",
           "-show_entries", "format=duration",
           "-of", "json", file_path
       ]
       out = subprocess.check_output(cmd, text=True)
       duration = float(json.loads(out)["format"]["duration"])
       return round(max(duration, 0.1), 3)
   ```
2. Cộng thêm khoảng đệm nhịp nghỉ cuối câu $P_{\text{pad}} = 0.25\text{ s}$ (chèn silence vào cuối file thoại của cảnh) và cập nhật `scene.audio_duration_sec = D_voice + P_pad`.
3. Tổng số khung hình mà `Stickman Animation Engine` phải vẽ cho phân cảnh $i$ là:
   $$N_{\text{frames}, i} = \max\left(1, \; \text{round}(\text{scene.audio\_duration\_sec} \times \text{FPS})\right)$$
   Nhờ công thức này, tổng thời lượng chuỗi khung hình và tổng thời lượng chuỗi âm thanh khớp nhau tuyệt đối đến từng phần trăm giây, không bao giờ xảy ra hiện tượng lệch tiếng (audio drift) dù video kéo dài 3 phút.

---

## 3. Thuật Toán Trộn Âm Thanh 3 Lớp (Voice 100% + SFX 60% + BGM Audio Ducking 20%)

### 3.1. Bảng cân bằng âm lượng chuẩn (Gain Staging & Ducking)

| Kênh âm thanh (Track) | Tỷ lệ biên độ mục tiêu | Mức quy đổi Decibel (dB) | Quy tắc hoạt động |
| :--- | :---: | :---: | :--- |
| **Track 1: Giọng đọc (Voiceover)** | **100%** (`1.00`) | `0.0 dB` (Chuẩn hóa đỉnh `-1 dBFS`) | Luôn rõ ràng nhất, làm trục thời gian gốc của toàn bộ video. |
| **Track 2: Âm thanh va chạm (SFX)** | **60%** (`0.60`) | `-4.4 dB` (nhân với `sfx_event.volume`) | Chèn chính xác vào vị trí mili-giây: $T_{\text{global\_ms}} = \left( \sum_{k < i} D_k + \text{offset\_sec} \right) \times 1000$. |
| **Track 3: Nhạc nền (BGM Ducking)** | **20%** khi có thoại (`0.20`)<br>**45%** khi nghỉ thoại (`0.45`) | `-14.0 dB` (khi đang đọc thoại)<br>`-7.0 dB` (khi giao chiến không lời) | Tự động hạ âm lượng (Audio Ducking) khi Track 1 có tiếng nói và nâng nhẹ lên ở các khoảng nghỉ chuyển cảnh. |

### 3.2. Công thức trộn bằng `pydub` / `numpy` DSP
Để tránh hiện tượng vỡ tiếng (clipping) khi cả 3 kênh phát cùng lúc tại điểm va chạm vũ khí:
1. Quy đổi cả 3 kênh về cùng chuẩn `44100 Hz, 16-bit Stereo` (mảng số thực `float32` trong khoảng $[-1.0, 1.0]$).
2. Tính tổng có trọng số:
   $$S_{\text{mix}}(t) = 1.0 \cdot S_{\text{voice}}(t) + 0.60 \cdot S_{\text{sfx}}(t) + w_{\text{duck}}(t) \cdot S_{\text{bgm}}(t)$$
   trong đó $w_{\text{duck}}(t) = 0.20$ khi $|S_{\text{voice}}(t)|_{\text{RMS}} > \epsilon$ và chuyển mượt về $0.45$ ở khoảng lặng với hằng số thời gian làm mượt `attack = 50ms`, `release = 250ms`.
3. Áp dụng bộ giới hạn mềm (**Soft Limiter / Peak Normalization** ở ngưỡng `0.95` tương đương `-0.4 dBFS`):
   $$S_{\text{final}}(t) = \tanh\left(S_{\text{mix}}(t)\right) \times 0.95$$
   Sau đó xuất ra tệp `out/temp/<job_id>/master_audio.wav`.
