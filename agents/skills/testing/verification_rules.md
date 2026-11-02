# KỸ NĂNG CHUYÊN MÔN: QUY CHUẨN KIỂM THỬ TỰ ĐỘNG & XÁC MINH HIỆN VẬT ĐẦU RA (`verification_rules.md`)
**Phạm vi áp dụng:** Toàn bộ Giai đoạn 3 đến Giai đoạn 10 (`tests/`)  
**Công cụ cốt lõi sử dụng:** `pytest` (hoặc `unittest`), `pydantic`, `ffprobe`, `ls -lh`  

---

## 1. Nguyên Tắc Kiểm Thử Theo Tầng (Layered Verification Strategy)

Theo Hiến pháp `AGENTS.md`, không một module nào được phép báo cáo hoàn thành nếu chưa có bài kiểm thử tự động trong thư mục `tests/` chạy xanh (`0 failed`) trên Terminal.

### 1.1. Kiểm thử Hợp đồng Dữ liệu & Bộ Phân tách Kịch bản (Giai đoạn 3)
- File test: `tests/test_phase3_parser.py`
- Nội dung bắt buộc kiểm tra:
  1. Khởi tạo `ScriptInput` hợp lệ và kiểm tra lỗi khi truyền kịch bản rỗng.
  2. Chạy **Rule-Based Vietnamese Parser** (không cần mạng / không cần API key) với kịch bản Hắc Ám Tây Du mẫu gồm ít nhất 3 cảnh.
  3. Xác nhận đầu ra là danh sách `list[SceneSchema]` khớp 100% với các Enum trong `docs/04_data_contracts.md` (`background_state`, `character_type`, `action_preset`, `camera_movement`, `sfx_events`).

### 1.2. Kiểm thử Động cơ Giọng đọc & Đo thời lượng (Giai đoạn 4)
- File test: `tests/test_phase4_audio_tts.py`
- Nội dung bắt buộc kiểm tra:
  1. Sinh tệp âm thanh thoại cho câu tiếng Việt mẫu.
  2. Xác nhận tệp `.wav`/`.mp3` tồn tại trên ổ đĩa và có dung lượng `os.path.getsize(path) > 1024` bytes.
  3. Đo `audio_duration_sec` bằng `ffprobe` và xác nhận `audio_duration_sec > 0.5` giây.
  4. Kiểm thử nhánh **Offline TTS Fallback** bằng cách giả lập mất kết nối để chứng minh hệ thống vẫn sinh được file `.wav` hợp lệ.

### 1.3. Kiểm thử Engine Vẽ Giấy Vở, Hệ Xương Người Que & VFX (Giai đoạn 5 & 6)
- File test: `tests/test_phase5_stickman_rig.py` và `tests/test_phase6_combat_vfx.py`
- Nội dung bắt buộc kiểm tra:
  1. Khởi tạo khung hình nền giấy vở kẻ ngang và kiểm tra `frame.shape == (1920, 1080, 3)` và `frame.dtype == np.uint8`.
  2. Kiểm tra cả 4 tạo hình nhân vật (`dark_wukong`, `erlang_shen`, `celestial_soldier_squad`, `buddha_palm`) và 8 `action_preset` tại các mốc tiến độ $u \in \{0.0, 0.25, 0.5, 0.75, 1.0\}$.
  3. Đảm bảo các điểm khớp xương nằm trong giới hạn an toàn, không sinh giá trị `NaN` hoặc `Inf`, và hình ảnh vẽ ra có độ lệch chuẩn pixel `np.std(frame) > 5.0` (chứng minh không phải khung hình trắng/đen rỗng).

### 1.4. Kiểm thử Trộn Âm thanh & Kết xuất Video MP4 (Giai đoạn 7)
- File test: `tests/test_phase7_compositor.py`
- Nội dung bắt buộc kiểm tra bằng `ffprobe`:
  1. Tệp `.mp4` sinh ra có dung lượng `> 50 KB`.
  2. Có đủ 2 luồng (`streams`):
     - Video stream: `codec_name == "h264"`, `width == 1080`, `height == 1920`, `pix_fmt == "yuv420p"`, `r_frame_rate == "30/1"`.
     - Audio stream: `codec_name == "aac"`, `duration > 0`.
  3. Thư mục tạm `out/temp/<job_id>/` đã được xóa sạch (`not temp_dir.exists()`).

---

## 2. Lệnh Chạy Kiểm Thử Chuẩn Trên Terminal

Khi chạy kiểm thử trong mỗi giai đoạn, thực thi tổ hợp lệnh sau và đính kèm nguyên văn kết quả vào báo cáo nghiệm thu:
```bash
# 1. Chạy bộ kiểm thử tự động Python
.venv/bin/python3 -m pytest -v tests/ || python3 -m unittest discover -s tests -v

# 2. Kiểm tra thông số thực tế của file video đầu ra (từ Giai đoạn 7 trở đi)
ffprobe -v error -show_entries format=filename,duration,size -show_entries stream=index,codec_type,codec_name,width,height,pix_fmt,r_frame_rate -of json out/<ten_file>.mp4
```
