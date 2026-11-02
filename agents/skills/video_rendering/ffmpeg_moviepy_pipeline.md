# KỸ NĂNG CHUYÊN MÔN: KẾT XUẤT VIDEO MP4 9:16, QUẢN LÝ RAM & DỌN DẸP TỆP TẠM (`ffmpeg_moviepy_pipeline.md`)
**Phạm vi áp dụng:** Giai đoạn 7 (`app/compositor/`)  
**Công cụ cốt lõi sử dụng:** `ffmpeg` CLI (`subprocess.Popen`), `ffmpeg-python`, `numpy`  

---

## 1. Nguyên Tắc Cốt Lõi: Truyền Luồng Khung Hình Trực Tiếp (Zero-RAM-Bloat Frame Piping)

Một khung hình chưa nén độ phân giải `1080 x 1920` hệ màu `RGB24` chiếm dung lượng:
$$1080 \times 1920 \times 3\text{ bytes} = 6,220,800\text{ bytes} \approx 5.93\text{ MiB}$$
Nếu video dài 3 phút (180 giây) ở tốc độ `30 FPS` ($5,400\text{ frames}$), việc lưu mảng các khung hình trong RAM sẽ chiếm tới **32 GiB RAM** (gây tràn bộ nhớ ngay lập tức), hoặc nếu lưu 5,400 ảnh `.png` ra ổ cứng sẽ gây nghẽn I/O nghiêm trọng.

### Giải pháp chuẩn bắt buộc:
Khởi tạo tiến trình `ffmpeg` nhận luồng `rawvideo` trực tiếp qua `stdin` (`subprocess.PIPE`) và chỉ giữ **duy nhất 1 khung hình hiện tại** trong RAM tại mỗi thời điểm.

---

## 2. Cấu Hình Lệnh FFmpeg Chuẩn Hóa Đầu Ra 9:16 (`1080x1920`, `30 FPS`)

Khi đã có tệp âm thanh tổng hợp `master_audio.wav` (đã trộn Voice + SFX + BGM) và bộ sinh khung hình theo từng phân cảnh:

```python
import subprocess
import numpy as np

def build_ffmpeg_encode_cmd(
    audio_path: str,
    output_mp4_path: str,
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
) -> list[str]:
    return [
        "ffmpeg",
        "-y",                           # Ghi đè file đích nếu đã tồn tại
        "-f", "rawvideo",               # Định dạng luồng đầu vào từ pipe
        "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24",            # Khớp với mảng numpy (H, W, 3) uint8 RGB
        "-s", f"{width}x{height}",      # Chuẩn dọc 9:16: 1080x1920
        "-r", str(fps),                 # Tốc độ khung hình: 30 FPS
        "-i", "-",                      # Input 0: đọc video frames từ stdin pipe
        "-i", audio_path,               # Input 1: đọc luồng âm thanh đã trộn
        "-c:v", "libx264",              # Codec H.264 tương thích mọi thiết bị
        "-preset", "fast",              # Cân bằng tốc độ render trên 4 vCPU và dung lượng
        "-crf", "21",                   # Chất lượng hình ảnh sắc nét cho nét vẽ mực trên giấy
        "-pix_fmt", "yuv420p",          # Bắt buộc để phát được trên Web Browser, iOS, Telegram
        "-c:a", "aac",                  # Codec âm thanh chuẩn MP4
        "-b:a", "192k",
        "-ar", "44100",
        "-ac", "2",
        "-movflags", "+faststart",      # Đưa moov atom lên đầu file để phát streaming tức thì
        "-shortest",                    # Khớp chính xác thời lượng giữa luồng hình và tiếng
        output_mp4_path,
    ]
```

---

## 3. Quy Trình Ghi Luồng Frame An Toàn & Chống Treo Pipe (Deadlock Prevention)

1. **Kiểm tra kích thước mảng trước khi ghi:**
   Mọi khung hình `frame` trước khi đẩy vào `proc.stdin.write(frame.tobytes())` bắt buộc phải thỏa mãn:
   - `frame.shape == (1920, 1080, 3)` (Chiều cao `1920` trước, chiều rộng `1080` sau theo chuẩn mảng 2D của NumPy).
   - `frame.dtype == np.uint8` và `frame.flags['C_CONTIGUOUS'] == True` (dùng `np.ascontiguousarray(frame)` nếu cần).
2. **Đóng `stdin` và kiểm tra mã thoát:**
   - Sau khi ghi xong frame cuối cùng của cảnh cuối cùng, đóng `proc.stdin.close()`, đọc `stderr` và gọi `proc.wait(timeout=180)`.
   - Nếu `proc.returncode != 0`, phải ném ngoại lệ kèm nội dung `stderr` thực tế của FFmpeg để tầng điều phối ghi nhận vào `JobStatus.error_detail`.

---

## 4. Quy Tắc Quản Lý Thư Mục Tạm & Dọn Rác (`try...finally` Cleanup Protocol)

1. **Cô lập theo `job_id`:**
   - Mọi tệp âm thanh từng phân cảnh (`scene_01_voice.mp3`, `scene_01_voice.wav`, `master_audio.wav`) chỉ được phép tạo bên trong thư mục riêng của tác vụ: `out/temp/<job_id>/`.
2. **Cơ chế tự động dọn dẹp 100%:**
   - Trong `Task Orchestrator` hoặc `Video Compositor`, quá trình kết xuất luôn phải nằm trong khối `try ... finally`:
   ```python
   import shutil
   from pathlib import Path

   temp_dir = Path("out") / "temp" / job_id
   try:
       # Thực thi tạo audio, dựng hình và xuất out/<job_id>.mp4
       ...
   finally:
       if temp_dir.exists():
           shutil.rmtree(temp_dir, ignore_errors=True)
   ```
3. **Kiểm chứng tệp đầu ra bằng `ffprobe`:**
   - Trước khi đánh dấu tác vụ `completed`, bắt buộc gọi `ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height,r_frame_rate,pix_fmt -of json out/<job_id>.mp4` để điền số liệu thật 100% vào đối tượng `RenderResult.technical_metadata`.
