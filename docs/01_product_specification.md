# TÀI LIỆU ĐẶC TẢ SẢN PHẨM (PRODUCT SPECIFICATION)
**Dự án:** Dark Myth Stickman Auto-Studio  
**Phiên bản:** 1.0.0 (Giai đoạn 1 — Project Foundation)  
**Vai trò thiết kế:** Principal Software Architect  

---

## 1. Tầm Nhìn & Mục Tiêu Sản Phẩm (Product Vision & Objectives)

**Dark Myth Stickman Auto-Studio** là hệ thống phần mềm tự động hóa toàn trình (End-to-End Automation Pipeline) giúp chuyển đổi kịch bản văn bản tiếng Việt thành video hoạt hình 2D người que (Stickman) giao chiến tốc độ cao trên nền giấy vở học sinh kẻ ngang, lấy cảm hứng từ vũ trụ **Hắc Ám Tây Du (Dark Myth: Journey to the West)**.

Hệ thống giải quyết bài toán sản xuất video ngắn/trung bình (Shorts / Reels / TikTok / YouTube Vertical) thời lượng **1 đến 3 phút** mà không đòi hỏi người dùng phải vẽ tay từng khung hình (frame-by-frame animation), không cần phần mềm dựng phim nặng nề, và hoạt động hoàn toàn với **chi phí vận hành 0 đồng ($0 Operational Cost)** ngay trên máy tính cá nhân.

---

## 2. Phong Cách Nghệ Thuật & Chủ Đề (Visual Style & Dark Myth Theme)

### 2.1. Bối cảnh nền giấy vở kẻ ngang (Notebook Paper Aesthetic)
- **Chất liệu nền (Canvas):** Mô phỏng trang giấy vở học sinh kẻ ngang (ruled notebook paper) với:
  - Tông màu giấy ngả vàng cổ điển hoặc xám tro hắc ám (`#F4EFE6` ở trạng thái bình thường, chuyển dần sang `#D8CFC2` hoặc rách cháy đen ở cao trào).
  - Các đường kẻ ngang màu xanh nhạt (`#9BB8D3`) cách đều nhau theo chiều dọc 1080x1920.
  - Đường lề dọc màu đỏ thẫm (`#C84B31`) bên trái khung hình.
  - Hiệu ứng vết mực tàu loang (ink splatters), vết rách giấy hoặc trang vở rung chuyển khi có đòn đánh chấn động.

### 2.2. Hệ thống nhân vật Hắc Ám Tây Du (Dark Myth Stickman Cast)
Các nhân vật được vẽ bằng thuật toán hình học (Procedural Vector/Canvas Rigging) với nét bút mực đen/đỏ đặc trưng, dễ nhận diện qua vũ khí, hào quang và phụ kiện đầu:
1. **Ngộ Không Hắc Hóa (Dark Wukong):**
   - Thân người que nét mực đen đậm, mắt phát sáng đỏ rực, vòng Kim Cô gãy nát hoặc tỏa hắc khí, khăn choàng cổ rách bay theo gió.
   - Vũ khí: **Thiết Bảng Như Ý (Ruyi Jingu Bang)** có thể phóng to, thu nhỏ, xoay tròn tạo lốc xoáy hoặc đập nát mặt giấy.
2. **Nhị Lang Thần — Dương Tiễn (Erlang Shen):**
   - Người que dáng cao, trán có Thiên Nhãn phát tia sáng vàng/bạch kim, giáp vai sắc nhọn.
   - Vũ khí: **Tam Tiêm Lưỡng Nhận Đảo (Three-Pointed Double-Edged Spear)** và Thiên Nhãn thần quang.
3. **Thiên Binh Thiên Tướng (Celestial Soldiers & Generals):**
   - Đội quân người que cầm giáo dài, khiên trận, kiếm khí tạo thành biển người bao vây.
4. **Cự Linh Thần / Bàn Tay Phật Tổ (Giant Bosses & Buddha Palm):**
   - Thực thể khổng lồ chiếm trọn nửa trên khung hình 9:16; Bàn tay Như Lai bằng nét vẽ mực vàng/đen khổng lồ từ đỉnh trang giấy giáng xuống đè bẹp không gian.

### 2.3. Ngôn ngữ chuyển động & chiến đấu (Combat Choreography)
- Nhịp độ nhanh, dứt khoát (High-octane stickman combat): lướt nhanh để lại tàn ảnh (afterimage/motion trail), đỡ đòn tóe lửa (clash sparks), dừng hình chấn động 2–3 frame khi trúng đòn nặng (hitstop/impact frame), văng đập vào lề giấy (knockback), và rung lắc máy quay (camera shake + zoom punch).

---

## 3. Thông Số Kỹ Thuật Đầu Ra (Technical Output Specifications)

| Hạng mục | Thông số chuẩn | Ghi chú kỹ thuật |
| :--- | :--- | :--- |
| **Định dạng tệp (Container)** | `.mp4` | Tương thích mọi nền tảng (TikTok, Reels, YouTube Shorts, Telegram) |
| **Tỷ lệ khung hình (Aspect Ratio)** | `9:16` (Dọc / Vertical) | Độ phân giải chuẩn Full HD Vertical: `1080 x 1920` pixels (hỗ trợ chế độ Draft `540 x 960` để preview nhanh) |
| **Tốc độ khung hình (Frame Rate)** | `30 FPS` (hoặc `60 FPS` tùy chọn) | Mặc định 30 FPS để tối ưu tốc độ render trên CPU phổ thông |
| **Video Codec** | `H.264 (libx264)` | Pixel format `yuv420p`, preset `fast`/`medium`, CRF `20–23` |
| **Audio Codec** | `AAC` | Tần số lấy mẫu `44.1 kHz` hoặc `48 kHz`, Stereo 2 kênh, Bitrate `192 kbps` |
| **Thời lượng mục tiêu** | `60 giây – 180 giây` (1–3 phút) | Tự động co giãn chính xác theo tổng thời lượng giọng đọc từng phân cảnh |
| **Thành phần âm thanh** | 3 lớp âm thanh đồng bộ | 1. **Voiceover tiếng Việt** (rõ chữ, trầm hùng)<br>2. **SFX chiến đấu** (tiếng gậy sắt, sấm sét, nổ, kiếm chạm)<br>3. **BGM** (nhạc nền cổ trang hắc ám, tự động giảm âm lượng - ducking khi có giọng đọc) |
| **Phụ đề (Subtitles)** | Burn-in Subtitle tiếng Việt | Hiển thị trực tiếp trên trang giấy (kiểu chữ viết tay/mực đậm) khớp từng câu thoại |

---

## 4. Ràng Buộc Cốt Lõi: Chi Phí Vận Hành 0 Đồng ($0 Cost Constraint)

1. **Xử lý 100% Local (Trên máy tính cá nhân):**
   - Toàn bộ quá trình dựng hình người que, tổng hợp âm thanh và xuất video `.mp4` đều chạy trực tiếp trên CPU/RAM của máy chủ Local thông qua Python và FFmpeg.
2. **Không phụ thuộc dịch vụ trả phí:**
   - **Giọng đọc (TTS):** Sử dụng thư viện miễn phí không cần API key (`edge-tts` với giọng tiếng Việt Neural chất lượng cao) kèm cơ chế dự phòng (Offline TTS / WAV synthesizer dự phòng khi mất mạng).
   - **Phân tích kịch bản (Script Parsing):** Có sẵn bộ phân tích kịch bản bằng tập luật và từ khóa tiếng Việt (**Deterministic Rule-Based Parser**) hoạt động hoàn toàn miễn phí và không cần Internet. Nếu người dùng cấu hình `GEMINI_API_KEY` (gói miễn phí của Google AI Studio), hệ thống có thể dùng LLM để làm giàu mô tả cảnh, nhưng luôn tự động chuyển về Rule-Based Parser nếu không có key hoặc hết hạn mức.
   - **Tài nguyên âm thanh (SFX & BGM):** Tự động tổng hợp bằng thuật toán âm thanh số (Procedural Audio Synthesis cho tiếng va chạm kim loại, tiếng gió, tiếng nổ trầm, nhịp trống chiến trận) kết hợp kho tài nguyên miễn phí bản quyền (CC0) trong thư mục `assets/`.

---

## 5. Hai Kênh Vận Hành Song Song (Dual Operation Channels)

Hệ thống cung cấp 2 giao diện điều khiển song song, dùng chung một lõi xử lý (Core Pipeline):

### Kênh 1: Web App Local (Giao diện điều khiển tại máy)
- Chạy trực tiếp trên trình duyệt (cổng `3000`).
- Cho phép người dùng:
  - Dán kịch bản văn bản tiếng Việt (hoặc chọn kịch bản mẫu Hắc Ám Tây Du).
  - Xem trước cấu trúc các phân cảnh (Scene Breakdown), chỉnh sửa nhân vật, hành động, góc máy.
  - Bấm nút khởi chạy tiến trình tạo video, theo dõi thanh tiến độ thời gian thực (Queued -> Parsing -> Audio -> Animation -> Compositing -> Completed).
  - Xem trực tiếp video `.mp4` tỷ lệ 9:16 ngay trên trình duyệt và tải tệp về máy.

### Kênh 2: Telegram Bot (Điều khiển từ xa qua điện thoại)
- Hoạt động qua cơ chế Long-Polling (chỉ cần điền `TELEGRAM_BOT_TOKEN` từ `@BotFather`, không cần thuê tên miền hay mở port router).
- Cho phép người dùng:
  - Gửi tin nhắn văn bản chứa kịch bản trực tiếp vào khung chat Telegram.
  - Nhận thông báo cập nhật trạng thái xử lý theo từng bước.
  - Nhận lại tệp video `.mp4` hoàn chỉnh ngay trong cuộc trò chuyện Telegram khi quá trình kết xuất hoàn tất.

---

## 6. Giới Hạn Phạm Vi (Out of Scope)
- Không sử dụng mô hình Diffusion tạo video nặng (như Sora, Runway, Stable Video Diffusion) đòi hỏi GPU VRAM 24GB+ hoặc tốn phí cloud.
- Không yêu cầu người dùng biết sử dụng phần mềm đồ họa (After Effects, Blender, Spine2D).
