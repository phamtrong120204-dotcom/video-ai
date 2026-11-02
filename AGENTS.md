# HIẾN PHÁP LÀM VIỆC DÀNH CHO AI CODING (AGENTS CONSTITUTION)
**Dự án:** Dark Myth Stickman Auto-Studio  
**Phạm vi áp dụng:** Bắt buộc xuyên suốt toàn bộ 10 Giai đoạn phát triển dự án.

---

## I. BỐN NGUYÊN TẮC TỐI THƯỢNG (SUPREME DIRECTIVES)

1. **Bằng Chứng Kiểm Thử Trước Khi Báo Cáo (Evidence-First Verification):**
   - **NGHIÊM CẤM** tuyên bố "Đã hoàn thành", "Đã chạy tốt" hoặc đánh dấu `[x]` vào `PROJECT_STATUS.md` khi chưa trực tiếp chạy lệnh kiểm thử trên Terminal (và kiểm tra file đầu ra bằng `ffprobe`, unit test hoặc trình duyệt thực tế ở các giai đoạn tương ứng).
   - Mọi báo cáo nghiệm thu phải đính kèm kết quả đầu ra thực tế từ Terminal.

2. **Kỷ Luật Giai Đoạn & Không Nhảy Bước (Strict Phase Discipline):**
   - Dự án gồm 10 giai đoạn độc lập. Ở giai đoạn nào chỉ được phép thực hiện đúng phạm vi của giai đoạn đó.
   - Sau khi hoàn thành các hạng mục của một giai đoạn và xuất báo cáo nghiệm thu, AI phải **DỪNG LẠI HOÀN TOÀN** để chờ người dùng phê duyệt trước khi bước sang giai đoạn kế tiếp.

3. **Bảo Toàn Kiến Trúc & Hợp Đồng Dữ Liệu (Contract & Architecture Integrity):**
   - Không tự ý thay đổi cấu trúc thư mục hoặc thay đổi tên trường dữ liệu đã quy định trong `docs/04_data_contracts.md`.
   - Nếu phát hiện nhu cầu bắt buộc phải mở rộng schema, phải cập nhật `docs/04_data_contracts.md` trước, giải thích rõ lý do trong báo cáo và đảm bảo tương thích ngược.

4. **Trung Thực Kỹ Thuật Tuyệt Đối (Brutal Technical Honesty):**
   - Nếu hệ thống thiếu thư viện, gặp giới hạn quyền hệ điều hành, mất kết nối mạng hoặc một tính năng phải chuyển sang nhánh Fallback, phải báo cáo rõ ràng nguyên nhân và giải pháp thực tế. Tuyệt đối không che giấu lỗi bằng dữ liệu giả (mock/stub trả về kết quả rỗng).

---

## II. QUY TRÌNH BẮT BUỘC TRƯỚC KHI VIẾT CODE (PRE-CODING PROTOCOL)

Trước khi viết hoặc chỉnh sửa bất kỳ dòng code nào từ Giai đoạn 2 đến Giai đoạn 10, AI Coding bắt buộc phải thực hiện tuần tự 4 bước sau:

1. **Bước 1 — Đọc Bảng Tiến Độ:** Đọc `PROJECT_STATUS.md` để xác nhận chính xác giai đoạn hiện tại và danh sách tiêu chí nghiệm thu (Acceptance Criteria).
2. **Bước 2 — Đọc Kiến Trúc & Hợp Đồng Dữ Liệu:** Đọc `docs/03_technical_architecture.md` và `docs/04_data_contracts.md` để nắm rõ kiểu dữ liệu đầu vào/đầu ra (`ScriptInput`, `SceneSchema`, `JobStatus`, `RenderResult`).
3. **Bước 3 — Kiểm Tra Kho Thư Viện & Kỹ Năng:** Đọc `agents/repository_registry.md` và các tài liệu kỹ năng chuyên môn trong `agents/skills/` (hoặc `agents/references/`) tương ứng với module sắp xây dựng.
4. **Bước 4 — Thiết Lập Bài Kiểm Thử (Test-First Mindset):** Xác định rõ lệnh terminal hoặc script kiểm thử sẽ dùng để chứng minh module hoạt động đúng sau khi viết code.

---

## III. QUY TẮC TUÂN THỦ HỢP ĐỒNG DỮ LIỆU (`docs/04_data_contracts.md`)

1. **Kiểm tra hợp lệ đầu vào/đầu ra (Schema Validation):**
   - Mọi dữ liệu truyền từ `Script Parser` sang `Audio Engine` và `Stickman Animation Engine` phải khớp 100% với cấu trúc `SceneSchema`.
   - Trường `audio_duration_sec` phải là số thực dương (`> 0.0`) được đo từ tệp âm thanh thực tế trước khi truyền vào bộ dựng hoạt hình.
2. **Trạng thái tác vụ chuẩn (`JobStatus`):**
   - Chỉ sử dụng đúng 7 trạng thái chuẩn: `queued`, `parsing`, `generating_audio`, `rendering_animation`, `compositing`, `completed`, `failed`.
3. **Thông số kỹ thuật đầu ra (`RenderResult`):**
   - Video xuất ra tại thư mục `out/` bắt buộc đạt tỷ lệ dọc `9:16` (`1080x1920`), định dạng `.mp4` (`h264` + `aac`, `yuv420p`) và kiểm tra được bằng `ffprobe`.

---

## IV. CÁC ĐIỀU CẤM TUYỆT ĐỐI (STRICT PROHIBITIONS)

1. **CẤM tự bịa đặt (Hallucinate) Repository hoặc Thư viện:**
   - Không được viết lệnh `pip install` hoặc `npm install` đối với bất kỳ thư viện nào chưa được kiểm chứng tồn tại thực tế và chưa được ghi nhận trong `agents/repository_registry.md`.
2. **CẤM sử dụng dịch vụ hoặc thư viện trả phí (Zero-Cost Violation):**
   - Nghiêm cấm tích hợp các API bắt buộc trả phí (như OpenAI TTS trả phí, ElevenLabs trả phí, dịch vụ Cloud Render trả phí).
   - Mọi tính năng phải chạy được với chi phí **0 đồng** trên máy Local và luôn có nhánh dự phòng Offline (Rule-based Parser, Offline TTS synthesizer fallback).
3. **CẤM làm tràn RAM hoặc để lại rác ổ cứng:**
   - Không lưu trữ toàn bộ mảng khung hình không nén của cả video dài 1–3 phút trong RAM.
   - Không để lại hàng nghìn tệp ảnh tạm trong `out/` sau khi tác vụ đã kết thúc.
4. **CẤM lưu khóa bí mật (API Keys / Tokens) vào mã nguồn:**
   - Mọi khóa cấu hình (`GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`) chỉ được đọc từ biến môi trường (`.env`) và tuyệt đối không được ghi cứng (hardcode) vào code hay tài liệu.

---

## V. QUY TRÌNH KIỂM THỬ & NGHIỆM THU TỪNG GIAI ĐOẠN (ACCEPTANCE GATE)

Mỗi giai đoạn chỉ được coi là hoàn tất khi vượt qua cổng nghiệm thu 4 bước:
1. **Kiểm tra cấu trúc & cú pháp (Syntax & Lint Check):** Không có lỗi biên dịch hoặc lỗi cú pháp Python / TypeScript.
2. **Chạy Unit Test / Integration Script:** Thực thi bộ test tự động trong thư mục `tests/` hoặc `scripts/` của giai đoạn đó.
3. **Kiểm tra hiện vật đầu ra (Artifact Verification):** Dùng lệnh hệ thống (`ls -lh`, `ffprobe`, `file`) để xác nhận tệp sinh ra có dung lượng `> 0`, đúng định dạng, đúng độ phân giải và thời lượng.
4. **Cập nhật `PROJECT_STATUS.md` & Xuất Báo Cáo Nghiệm Thu:** Ghi rõ kết quả kiểm thử thực tế và dừng lại chờ người dùng duyệt.
