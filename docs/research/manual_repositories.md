# DANH SÁCH REPOSITORY & TÀI NGUYÊN CHỜ NGƯỜI DÙNG BỔ SUNG / XÁC NHẬN (`manual_repositories.md`)
**Dự án:** Dark Myth Stickman Auto-Studio  
**Giai đoạn:** Giai đoạn 2 — Nghiên cứu Repository & Chuẩn bị Tài liệu cho AI  
**Mục đích:** Tuân thủ tuyệt đối **Cơ chế Chống Bịa Đặt (Zero-Hallucination Policy)**. Mọi repository không thể tích hợp tự động bằng Python hoặc các tài nguyên chuyên biệt chưa có sẵn trên GitHub đều được liệt kê minh bạch tại đây kèm phương án thay thế để người dùng quyết định.

---

### [Nhóm A / Phần mềm Hoạt hình Người que StykAnimate-App & File mẫu `.stk` / `.piv`]
- **Repository mục tiêu:** `https://github.com/filippocalippo/StykAnimate-App`
- **Lý do chưa hoàn thành:** AI đã truy cập được metadata và README của `filippocalippo/StykAnimate-App` (GPL-3.0, viết bằng JavaScript), nhưng đây là **ứng dụng giao diện đồ họa (GUI Desktop/Web App)** để người dùng vẽ tay từng khung hình, **không phải thư viện Python headless** và không có CLI nhận kịch bản văn bản để tự động xuất video. Ngoài ra, chưa có kho file nhân vật `.stk` / `.piv` chủ đề Hắc Ám Tây Du đi kèm.
- **Từ khóa đề xuất cho người dùng tìm kiếm:** `stick figure animation engine python`, `2D skeletal animation python`, `pivot stk parser python`, `stykanimate templates`.
- **Vị trí để người dùng bổ sung đường dẫn/tài liệu:**
  - Đường dẫn repo / tài liệu bổ sung: `[ĐIỀN_VÀO_ĐÂY_NẾU_CÓ]`
  - Phương án đề xuất mặc định của hệ thống (nếu để trống): Sử dụng bộ dựng khung xương 2D toán học (`StickmanRig2D` bằng `numpy` + `Pillow` + `opencv-python-headless`) theo đúng đặc tả trong `agents/skills/animation/stickman_rigging_and_vfx.md`.
- **Trạng thái:** Chờ người dùng cung cấp / xác nhận phương án thay thế.

---

### [Nhóm A & B / Bộ dữ liệu Chuyển động Chiến đấu Người que Hắc Ám Tây Du (Dark Myth Combat Moveset Repo)]
- **Repository mục tiêu:** Chưa tìm được (Không tồn tại repository mã nguồn mở trên GitHub chứa sẵn các đòn đánh của Tôn Ngộ Không, Nhị Lang Thần, Bàn Tay Phật Tổ dưới dạng keyframe Python).
- **Lý do chưa hoàn thành:** Các dự án mã nguồn mở trên GitHub chỉ cung cấp thư viện đồ họa cơ bản (`Pillow`, `opencv`, `pygame`) chứ không có repo nào lập trình sẵn 8 chiêu thức Hắc Ám Tây Du (Thiết Bảng Như Ý phóng đại, xoay gậy lốc xoáy, Thiên Nhãn bắn tia sáng, Như Lai Thần Chưởng giáng xuống trang giấy vở).
- **Từ khóa đề xuất cho người dùng tìm kiếm:** `procedural stickman fight python`, `2d combat keyframe json`, `stickman fight choreography open source`.
- **Vị trí để người dùng bổ sung đường dẫn/tài liệu:**
  - Đường dẫn repo / file JSON keyframe bổ sung: `[ĐIỀN_VÀO_ĐÂY_NẾU_CÓ]`
  - Phương án đề xuất mặc định của hệ thống (nếu để trống): Tự lập trình đầy đủ 8 `action_preset` và 4 tạo hình nhân vật bằng phương trình nội suy khớp xương 2D theo bảng thông số đã thiết kế chi tiết tại `agents/references/animation/dark_myth_moveset_spec.md`.
- **Trạng thái:** Chờ người dùng cung cấp / xác nhận phương án thay thế.

---

### [Nhóm B / Thư viện Hiệu ứng Vết rách Giấy vở & Kiếm khí 2D (Procedural Slash Trails & Torn Notebook Paper VFX)]
- **Repository mục tiêu:** Chưa tìm được (Không có gói `pip` độc lập chuyên tạo hiệu ứng giấy vở học sinh bị rách/cháy mực và vệt chém tàn ảnh 2D trên môi trường không có GPU).
- **Lý do chưa hoàn thành:** Các thư viện game 2D như `arcade` hoặc `moderngl` yêu cầu OpenGL / GPU context hoặc cửa sổ X11 (máy chủ container hiện tại không có GPU rời), và cũng không có sẵn hiệu ứng giấy vở kẻ ngang.
- **Từ khóa đề xuất cho người dùng tìm kiếm:** `procedural 2d slash trail python opencv`, `notebook paper texture generator python`, `2d camera shake hitstop python`.
- **Vị trí để người dùng bổ sung đường dẫn/tài liệu:**
  - Đường dẫn repo / текстуra giấy vở bổ sung: `[ĐIỀN_VÀO_ĐÂY_NẾU_CÓ]`
  - Phương án đề xuất mặc định của hệ thống (nếu để trống): Vẽ thủ tục 100% bằng `numpy` + `Pillow` + `opencv-python-headless` (vẽ dòng kẻ ngang `#9BB8D3`, lề đỏ `#C84B31`, đa giác vết nứt giấy phân nhánh và lưu bộ đệm 5 frame trước để tạo tàn ảnh Alpha Trail).
- **Trạng thái:** Chờ người dùng cung cấp / xác nhận phương án thay thế.

---

### [Nhóm D / Kho Âm thanh Va chạm Binh khí & Nhạc nền Cổ trang Hắc Ám (Custom SFX & BGM Audio Pack)]
- **Repository mục tiêu:** Chưa tìm được repo GitHub chính thức chuyên chứa gói âm thanh `.wav` miễn phí bản quyền cho tiếng Thiết Bảng Như Ý, tiếng Tam Tiêm Đảo và nhạc nền Hắc Ám Tây Du.
- **Lý do chưa hoàn thành:** Các thư viện Python (`edge-tts`, `pydub`, `mutagen`) chỉ xử lý giọng đọc và trộn âm thanh, không đính kèm sẵn kho file `.wav` tiếng binh khí cổ trang.
- **Từ khóa đề xuất cho người dùng tìm kiếm:** `cc0 medieval weapon clash sfx pack github`, `royalty free dark chinese orchestral bgm`, `freesound metal staff hit wav`.
- **Vị trí để người dùng bổ sung đường dẫn/tài liệu:**
  - Đường dẫn thư mục chứa file `.wav`/`.mp3` của người dùng (có thể chép vào `assets/sfx/` và `assets/bgm/`): `[ĐIỀN_VÀO_ĐÂY_NẾU_CÓ]`
  - Phương án đề xuất mặc định của hệ thống (nếu để trống): Hệ thống tự động khởi tạo các tệp âm thanh `.wav` chuẩn vào `assets/sfx/` và `assets/bgm/` bằng **Bộ tổng hợp âm thanh toán học (`numpy` DSP Waveform Synthesizer: FM metallic synthesis cho tiếng gậy sắt/kiếm chạm, filtered white-noise sweep cho tiếng vung vũ khí xé gió, sub-bassboom cho tiếng nổ chấn động và chuỗi hợp âm ngũ cung trầm cho BGM)**, đồng thời tự động ưu tiên dùng file `.wav` của người dùng nếu người dùng chép file vào `assets/`.
- **Trạng thái:** Chờ người dùng cung cấp / xác nhận phương án thay thế.

---

### [Hệ thống Môi trường / Cài đặt `pip` vào `.venv` trên Máy chủ]
- **Repository / Gói hệ thống mục tiêu:** Gói hệ điều hành `python3.10-venv` / `python3-pip` (hoặc cài đặt các thư viện Python trong `agents/repository_registry.md`).
- **Lý do ghi nhận:** Như đã báo cáo trung thực ở Giai đoạn 1, môi trường Ubuntu hiện tại chưa cài sẵn gói `python3.10-venv` (`ensurepip`), nên `.venv` đang được tạo với cờ `--without-pip`.
- **Giải pháp kỹ thuật cho Giai đoạn 3 trở đi:**
  - Có thể nạp trực tiếp `pip` vào `.venv` bằng script chính thức `https://bootstrap.pypa.io/get-pip.py` (chạy bằng `.venv/bin/python3 get-pip.py` hoàn toàn không cần quyền `sudo apt`), sau đó cài đặt `edge-tts`, `pydub`, `mutagen`, `Pillow`, `opencv-python-headless`, `numpy`, `scipy`, `ffmpeg-python`, `pydantic`, `pytest`, `python-telegram-bot`, `google-genai`.
- **Vị trí để người dùng xác nhận:** `[XÁC_NHẬN_CHO_PHÉP_CÀI_PIP_TRONG_VENV_Ở_GĐ3]`
- **Trạng thái:** Chờ người dùng xác nhận khi chuyển sang Giai đoạn 3.
