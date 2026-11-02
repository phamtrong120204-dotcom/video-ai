# BẢNG THEO DÕI TIẾN ĐỘ DỰ ÁN (PROJECT STATUS & ROADMAP)
**Dự án:** Dark Myth Stickman Auto-Studio  
**Mục tiêu:** Hệ thống tự động hóa sản xuất video hoạt hình người que chiến đấu trên nền giấy vở kẻ ngang (Hắc Ám Tây Du, 9:16, 1–3 phút, lồng tiếng Việt, SFX, BGM, Web App Local + Telegram Bot, chi phí 0 đồng).  
**Cập nhật lần cuối:** 2026-10-31 (Đã chuẩn hóa môi trường Windows, 20/20 test PASSED, xuất Master Audit Report — Sẵn sàng chuyển Giai đoạn 4)  

---

## 1. Tổng Quan Lộ Trình 10 Giai Đoạn (10-Phase Master Roadmap)

| Giai đoạn | Tên Giai Đoạn | Mô Tả Trọng Tâm | Trạng Thái |
| :---: | :--- | :--- | :---: |
| **Giai đoạn 1** | **Project Foundation (Xây dựng Hồ sơ & Cấu trúc Dự án)** | Khảo sát phần cứng/môi trường, dựng cây thư mục chuẩn (`in/`, `out/`, `assets/`, `docs/`, `app/`, `tests/`), khởi tạo Git & `.venv`, viết bộ 4 tài liệu thiết kế (`docs/01..04`), `AGENTS.md`, `PROJECT_STATUS.md`. | **ĐÃ NGHIỆM THU** |
| **Giai đoạn 2** | **Research, Evaluation & Skill Packaging (Nghiên cứu & Đóng gói Kỹ năng)** | Khảo sát 6 nhóm repository (A–F) theo quy trình 8 bước, lập danh sách chống bịa đặt `manual_repositories.md`, cập nhật `repository_registry.md` và viết trọn bộ `agents/skills/` + `agents/references/`. | **ĐÃ NGHIỆM THU** |
| **Giai đoạn 3** | **Core Skeleton & Interfaces (Xây dựng Bộ Khung Nghiệp Vụ & Hợp Đồng Giao Tiếp)** | Cài đặt thư viện nền tảng vào `.venv` trên Windows, xây dựng `app/core/`, `app/schemas/`, `app/interfaces/`, `app/modules/`, `app/pipeline/orchestrator.py`, vượt qua 20 bài kiểm thử `pytest -v` (0 failed) và xuất `docs/PHASE_1_TO_3_MASTER_AUDIT_REPORT.md`. | **ĐÃ NGHIỆM THU** |
| **Giai đoạn 4** | **Script Parser & Vietnamese Audio Pipeline Engine** | Xây dựng bộ phân tích kịch bản tiếng Việt (`ScriptParser`) trích xuất `SceneSchema[]` (**Đã hoàn thành 4.1**), bộ tổng hợp giọng đọc tiếng Việt (`EdgeTTSAudioEngine`) với cơ chế retry/backoff, voice fallback, khóa giọng cấp job, đệm 0.30s đuôi âm thanh qua Pydub, đo thời lượng chính xác qua Mutagen và xác thực ffprobe (**Đã hoàn thành 4.2**). | **ĐÃ HOÀN THÀNH (4.1 & 4.2)** |
| **Giai đoạn 5** | **Notebook Paper & Procedural Stickman Rigging** | Xây dựng engine vẽ trang giấy vở kẻ ngang 1080x1920, hệ thống khớp xương 2D procedurally rigged và tạo hình nhân vật Hắc Ám Tây Du (Hắc Ngộ Không, Dương Tiễn, Thiên Binh, Bàn Tay Phật). | **ĐÃ NGHIỆM THU (100% PASS)** |
| **Giai đoạn 6** | **Combat Choreography, VFX & Camera Engine** | Lập trình các `action_preset` giao chiến tốc độ cao, hệ thống nội suy chuyển động (Interpolation Engine), điều khiển vòng lặp hoạt ảnh và kết xuất video. | **ĐÃ NGHIỆM THU (100% PASS)** |
| **Giai đoạn 7** | **SFX/BGM Synthesizer & Video Compositor** | Xây dựng bộ tạo/ghép SFX khớp mili-giây va chạm, nhạc nền BGM tự động ducking và kết xuất video `.mp4` (H.264, 1080x1920, 30fps) qua FFmpeg. | **ĐÃ NGHIỆM THU** |
| **Giai đoạn 8** | **Dark Corruption VFX Engine & Background Warp Distortion** | Xây dựng engine hiệu ứng hình ảnh Dark Myth hoàn chỉnh: biến dạng trường tọa độ giấy kẻ ngang (Warp Distortion Field - Palm Depression & Radial Shockwave), hào quang Hắc Ám (Dark Aura tendrils/smoke/embers), vệt kiếm khí vũ khí (Motion Trail ribbons), tia lửa va chạm (Clash Sparks), rạn nứt mặt đất vỡ vụn (Ground Cracks), bụi giấy tung bay (Paper Dust), và bộ ghép 7 layer tích hợp hoàn chỉnh với G6 Animation & G7 Audio. | **ĐÃ HOÀN THÀNH (100% PASS)** |
| **Giai đoạn 9** | **Local Studio Web UI & Telegram Bot Integration** | Xây dựng giao diện Studio trực quan (Gradio local 7860) và Telegram Bot nhận kịch bản, cập nhật tiến độ thời gian thực và gửi video thành phẩm. | **ĐÃ HOÀN THÀNH (100% PASS)** |
| **Giai đoạn 10** | **End-to-End Verification, Stress Test & Final Packaging** | Chạy kiểm thử toàn trình từ kịch bản Hắc Ám Tây Du thực tế, kiểm chứng thông số video bằng `ffprobe`, kiểm thử chịu tải đồng thời (concurrency), kiểm tra rò rỉ tài nguyên (RAM/CPU/Temp), đóng gói Windows batch scripts và bàn giao sản phẩm hoàn chỉnh. | **ĐÃ HOÀN THÀNH & NGHIỆM THU (100% PASS)** |

---

## 2. Danh Sách Hạng Mục Nghiệm Thu Giai Đoạn 3 (Phase 3 Acceptance Criteria)

- [x] **1. Khai báo `requirements.txt` và cài đặt thư viện vào `.venv`:** Đã nạp `pip 26.2.2` vào `.venv` trên Windows và cài đặt thành công `pydantic 2.14.2`, `python-dotenv 1.2.4`, `pytest 9.2.0`, `pytest-asyncio 1.4.1`, đồng thời xác nhận khả năng cài đặt tương thích của toàn bộ danh sách gói cho Python 3.15 Windows.
- [x] **2. Định nghĩa Schema dữ liệu cảnh và tác vụ (`app/schemas/`):**
  - `script_schema.py`: `ScriptInput`, `RenderConfig`, `TargetDuration`, `TelegramMeta`, `SourceChannel`.
  - `scene_schema.py`: `SceneSchema`, `ActorConfig` (`skin`, `color`, `weapon`), `SFXEvent` (`sfx_name`, `time_offset >= 0`), `CameraConfig`, `BackgroundState` (`normal_page`, `cracked_page`, `dark_corrupted_page` + tương thích ngược `docs/04_data_contracts.md`), `ActionPreset` (8 chiêu thức Hắc Ám Tây Du).
  - `job_schema.py`: `JobStatus` (7 trạng thái chuẩn), `JobRecord`, `TechnicalMetadata`, `ProcessingStats`, `RenderResult`.
- [x] **3. Định nghĩa Giao diện liên module (`app/interfaces/`):**
  - `IScriptParser.parse(script_input: ScriptInput) -> list[SceneSchema]`
  - `IAudioEngine.generate_scene_audio(scene: SceneSchema, output_dir: Path) -> tuple[Path, float]`
  - `IAnimationEngine.render_scene_frames(scene: SceneSchema, duration_sec: float, output_dir: Path) -> Path`
  - `IVideoCompositor.compose_final_video(job_id: str, scenes: list[SceneSchema], scene_assets: dict, output_path: Path) -> RenderResult`
- [x] **4. Xây dựng Cấu hình, Log và Quản lý lỗi (`app/core/`):**
  - `config.py`: Đọc `.env`, cung cấp thông số mặc định an toàn (`1080x1920`, `30 FPS`), tự động tạo `in/`, `out/`, `out/temp/`, `out/jobs/`, `assets/`, `logs/`.
  - `logger.py`: Ghi log chuẩn có timestamp, tên module, mức độ log và `[job=<job_id>]` ra cả console và `logs/app.log`.
  - `exceptions.py`: Các class Exception phân tầng (`ScriptParseError`, `AudioGenerationError`, `AnimationRenderError`, `VideoCompositingError`, `JobStateTransitionError`, `ConfigurationError`).
- [x] **5. Xây dựng Quản lý tác vụ & Bộ điều phối khung (`task_manager.py` & `orchestrator.py`):**
  - `TaskManager`: Quản lý tạo tác vụ, hàng đợi FIFO, kiểm soát chuyển trạng thái hợp lệ (`queued -> parsing -> generating_audio -> rendering_animation -> compositing -> completed / failed`) và lưu JSON tại `out/jobs/<job_id>.json`.
  - `PipelineOrchestrator`: Kết nối 4 module qua Dependency Injection, thực thi nghiêm ngặt thứ tự **Audio-First Timing** (Gọi `IAudioEngine` đo `duration_sec` trước $\rightarrow$ cập nhật `SceneSchema.audio_duration_sec` $\rightarrow$ gọi `IAnimationEngine` với đúng `duration_sec` đó $\rightarrow$ gọi `IVideoCompositor`), bắt lỗi cô lập và tự động dọn sạch thư mục tạm `out/temp/<job_id>/` trong khối `finally`.
- [x] **6. Xây dựng và chạy Bộ kiểm thử nền tảng (`tests/`):**
  - Đã viết đầy đủ `conftest.py`, `test_config_and_logger.py`, `test_schemas.py`, `test_task_manager.py`, `test_pipeline_skeleton.py`.
  - Kết quả chạy thực tế `.venv\Scripts\pytest -v` trên Windows: **20 passed in 0.24s (0 failed)**.
- [x] **7. Xuất Báo cáo Nghiệm thu Tổng hợp Đa Mô hình:**
  - Đã xuất bản hoàn chỉnh tại `docs/PHASE_1_TO_3_MASTER_AUDIT_REPORT.md` với đầy đủ 7 phần chuyên sâu để đối chiếu chéo độc lập.

---

## 3. Danh Sách Hạng Mục Nghiệm Thu Giai Đoạn 4.1 – Script Parser Engine

- [x] **1. Xây dựng RuleBasedScriptParser (Offline 100%):** Tách cảnh có tiêu đề hoặc không tiêu đề, không chia vụn câu văn, bảo tồn dấu tiếng Việt, nhận diện đúng 5 nhân vật chuẩn, 8 chiêu thức `ActionPreset`, nền giấy, góc máy và sự kiện SFX. Giữ nguyên `audio_duration_sec = 0.0` và `voice_audio_path = None`.
- [x] **2. Xây dựng GeminiScriptParser (LLM Structured Output):** Tích hợp SDK `google-genai` (2.34.0), model `gemini-2.5-flash`, chỉ thị JSON phân cảnh nghiêm ngặt và thẩm định Pydantic chặn đứng Enum lạ.
- [x] **3. Xây dựng HybridScriptParser (Orchestration & Fallback):** Tự động gọi Gemini khi có `GEMINI_API_KEY` và chuyển đổi mượt mà sang `RuleBasedScriptParser` khi không có key hoặc khi AI gặp lỗi (timeout, 429, cú pháp).
- [x] **4. Bộ kiểm thử tự động toàn diện (`tests/test_script_parser.py`):** 18 bài test tự động bao quát 15 kịch bản biên, mock đầy đủ lỗi mạng của Gemini. Kết quả toàn dự án: **38 passed in 0.25s (0 failed)**.
- [x] **5. Kiểm thử tích hợp kịch bản mẫu & Xuất hiện vật JSON:** Đã chạy thực tế `scripts/run_script_parser_sample.py` và sinh tệp `out/sample_parsed_scenes.json` chứa 4 phân cảnh chuẩn hóa khớp 100% `SceneSchema`.
- [x] **6. Xuất Báo cáo Nghiệm thu Kỹ thuật Giai đoạn 4.1:** Ban hành [`docs/PHASE_4_1_SCRIPT_PARSER_REPORT.md`](file:///c:/Users/phamtrong/Desktop/video%20agent/docs/PHASE_4_1_SCRIPT_PARSER_REPORT.md). Dừng lại chờ duyệt trước khi bước sang Giai đoạn 4.2 (Vietnamese TTS Engine).

---

## 4. Danh Sách Hạng Mục Nghiệm Thu Giai Đoạn 4.2 – Vietnamese TTS Engine & Audio Timing

- [x] **1. Chuẩn bị môi trường FFmpeg Portable:** Đã tải và giải nén thành công FFmpeg bản Essentials v9.0.2 chính thức từ Gyan.dev vào `C:\ffmpeg\bin\` (chứa `ffmpeg.exe`, `ffprobe.exe`, `ffplay.exe`), kiểm chứng bộ giải mã/mã hóa `libx264` và `aac`, tự động nạp cấu hình `AppConfig` và xuất báo cáo `docs/PRE_STAGE_4_2_FFMPEG_VERIFICATION.md`.
- [x] **2. Xây dựng Vietnamese TTS Engine (`app/modules/audio/edge_tts_engine.py`):**
  - Tích hợp Microsoft Edge-TTS với giọng đọc chính nam `vi-VN-NamMinhNeural` và giọng dự phòng nữ `vi-VN-HoaiMyNeural`.
  - Cơ chế Retry số mũ có Jitter ngẫu nhiên (`1.0s -> 2.0s -> 4.0s`) chống nghẽn mạng và tự động chuyển đổi sang giọng dự phòng khi giọng chính quá tải.
  - Khóa giọng nhất quán cấp Job (`lock_voice_per_job=True`): toàn bộ phân cảnh trong một video được đảm bảo 100% sử dụng cùng một giọng đọc.
  - Chuẩn hóa Unicode tiếng Việt NFC (`unicodedata.normalize("NFC")`) chống lỗi vỡ ký tự tổ hợp trên dịch vụ giọng nói.
- [x] **3. Audio Timing & Đệm khoảng lặng (Pydub + Mutagen):**
  - Đệm chính xác 0.30s đuôi âm thanh tĩnh (`AudioSegment.silent(duration=300)`) vào cuối mỗi phân cảnh, giúp thoại không bị giật cụt khi chuyển cảnh.
  - Đo thời lượng chuẩn xác theo FFprobe (khớp 100% mẫu PCM giải mã thực tế) và cập nhật `SceneSchema.audio_duration_sec`, `SceneSchema.voice_audio_path`.
  - Cơ chế thăng cấp nguyên tử (Atomic Promotion) qua file tạm `.tmp.mp3`, đảm bảo không để lại file rác hay file hỏng nếu tiến trình bị ngắt.
- [x] **4. Bộ kiểm thử tự động đơn vị toàn diện (`tests/test_edge_tts_engine.py`):**
  - 18 bài kiểm thử tự động bao quát toàn bộ các kịch bản biên, bao gồm cơ chế phục hồi giọng đọc đồng nhất toàn Job (Case B) và ngắt lỗi sạch khi không thể tái tạo (Case C).
  - Kết quả kiểm thử toàn dự án: **57 passed in 5.87s (0 failed)**.
- [x] **5. Kiểm thử tích hợp kịch bản thực tế 5 phân cảnh & Xác thực FFprobe:**
  - Chạy kịch bản tích hợp `scripts/verify_tts_engine.py` trên kịch bản Hắc Ám Tây Du 5 phân cảnh.
  - Tạo thành công 5 tệp MP3 độc lập tại `out/temp/integration_tts/audio/scene_01_voice.mp3` .. `scene_05_voice.mp3` với dung lượng từ 100KB - 131KB.
  - Xác thực chéo thành công 100% bằng `ffprobe` và giải mã mẫu PCM (codec `mp3`, sample rate 24,000Hz, bitrate 128kbps, tổng thời lượng 35.796 giây).
  - Xuất hiện vật JSON chi tiết tại `out/sample_tts_results.json`.
- [x] **6. Xuất Báo cáo Nghiệm thu Toàn diện & Kiểm định Final QA:** Ban hành [`docs/PHASE_4_2_VIETNAMESE_TTS_REPORT.md`](file:///c:/Users/phamtrong/Desktop/video%20agent/docs/PHASE_4_2_VIETNAMESE_TTS_REPORT.md) và [`docs/PHASE_4_2_FINAL_QA_REPORT.md`](file:///c:/Users/phamtrong/Desktop/video%20agent/docs/PHASE_4_2_FINAL_QA_REPORT.md). DỪNG LẠI HOÀN TOÀN để chờ người dùng phê duyệt trước khi bước sang Giai đoạn 5 (Notebook Paper & Procedural Stickman Rigging).

---

## 5. Danh Sách Hạng Mục Nghiệm Thu Giai Đoạn 5.1 – Procedural Notebook Background Engine

- [x] **1. Cài đặt thư viện đồ họa chuẩn xác vào `.venv`:** Cài đặt thành công `numpy 2.5.4` và `Pillow 13.0.0` trên Windows x64 Python 3.15.
- [x] **2. Xây dựng Procedural Notebook Background Engine (`app/modules/animation/background_renderer.py`):**
  - Triển khai kiến trúc đồ họa 7 layer chuẩn: Paper Base $\to$ Fiber Texture $\to$ Lighting/Vignette $\to$ Dòng kẻ ngang xanh $\to$ Lề đỏ kép $\to$ Lỗ đóng gáy $\to$ Hiệu ứng trạng thái Hắc Ám Tây Du $\to$ Color Grading.
  - Hỗ trợ toàn bộ 7 giá trị `BackgroundState` (`clean_notebook`, `ink_splattered`, `cracked_page`, `torn_dark_myth`, `dark_corrupted_page`, `heavenly_pressure` và `normal_page`).
  - Hỗ trợ dynamic resolution: `1080x1920` (Production Full-HD 9:16) và `540x960` (Preview).
  - Kiểm soát tính ngẫu nhiên và khả năng tái lập 100% bằng tham số `seed`.
  - Bảo vệ vùng chiến đấu trung tâm (Combat Safe Zone) cho các phân cảnh có vết mực văng `ink_splattered`.
- [x] **3. Bộ kiểm thử tự động toàn diện (`tests/test_background_renderer.py`):**
  - 10 bài test đơn vị kiểm tra mọi BackgroundState, kích thước 1080x1920 & 540x960, tính ngẫu nhiên/tái lập, xử lý lỗi state lạ và bảo toàn `SceneSchema`.
  - Kết quả kiểm thử toàn dự án: **67 passed in 6.59s (0 failed)**.
- [x] **4. Xuất bộ sưu tập ảnh xem trước (Preview Collection):**
  - Chạy `scripts/preview_notebook_backgrounds.py`, tạo trọn bộ 12 tệp PNG (`1080x1920` và `540x960`) kèm 1 ảnh tổng hợp so sánh trực quan (`all_states_comparison_grid.png`) trong `out/preview/backgrounds/`.
  - Đo đạc thời gian render siêu tốc: trung bình `0.18s – 0.28s` cho mỗi ảnh 1080x1920, RAM đỉnh chỉ `~180 MB` (hoàn toàn dưới ngưỡng trần 300 MB).
- [x] **5. Xuất Báo cáo Nghiệm thu Kỹ thuật Giai đoạn 5.1:** Ban hành [`docs/PHASE_5_1_NOTEBOOK_BACKGROUND_REPORT.md`](file:///c:/Users/phamtrong/Desktop/video%20agent/docs/PHASE_5_1_NOTEBOOK_BACKGROUND_REPORT.md). DỪNG LẠI HOÀN TOÀN để chờ người dùng kiểm tra trực quan chất lượng hình ảnh trước khi bước sang Giai đoạn 5.2.

---

## 6. Danh Sách Hạng Mục Nghiệm Thu Giai Đoạn 5.2 – Procedural Stickman Rigging & Character Renderer

- [x] **1. G5.2.1 & G5.2.2 – Humanoid Skeleton & Pose Catalog:**
  - Khung xương 14 khớp (Joints), 13 đoạn xương (Bones) bất biến, kiểm chứng 100% bằng `RigidBoneValidator`.
  - Danh mục 8 tư thế chiến đấu chuẩn hóa (`standoff_idle`, `combat_stance`, `forward_charge`, `overhead_slam`, `mid_air_leap`, `guard_block`, `vortex_sweep`, `knockback_slide`).
  - Cơ chế bất biến tuyệt đối `PoseCatalog.get_pose()` bằng deep copy, ngăn chặn mọi tác động biến đổi dữ liệu gốc.
- [x] **2. G5.2.3.1 – Humanoid Body Renderer:**
  - Dựng hình khung xương người que mực đen đậm, khớp tròn tiếp giáp chống gãy góc, đầu tròn mực đặc, canvas chuẩn `1080x1920` RGBA trong suốt.
  - Căn chỉnh mặt đất chính xác tại $Y = 1420\text{ px}$, tiếp xúc mặt đất tuyệt đối không xuyên đất.
- [x] **3. G5.2.3.2 – Face & Character Accessories Renderer:**
  - Khuôn mặt đặc trưng: Mắt đỏ Hỏa Nhãn Kim Tinh (Wukong), Thiên Nhãn phát quang (Erlang Shen), khe kính ngắm mũ trụ (Thiên Binh Thiên Tướng).
  - Phụ kiện trước/sau: Vòng Kim Cô chữ V, cặp lông chim trĩ Bezier 180px, khăn choàng bay ngược hướng di chuyển, mũ trụ và giáp vai.
- [x] **4. G5.2.3.3 – Weapon Renderer:**
  - Dựng hình 3 loại vũ khí danh định: Thiết Bảng Như Ý (`ruyi_staff`, 340px), Tam Tiêm Lưỡng Nhận Đao (`three_pointed_spear`, 360px), Thiên Binh Đại Kích (`celestial_halberd`, 320px).
  - Khắc phục triệt để DEF-01 (chống đất $Y \le 1421$, bảo toàn 100% chiều dài danh định), DEF-02 (tri-state auto-align hai tay an toàn), DEF-03 (mũi ba đinh ba rõ nét 3 cụm pixel và 2 khoảng hở $\ge 3\text{ px}$).
- [x] **5. G5.2.3.4 – Buddha Palm Renderer (Bàn Tay Phật Khổng Lồ / Như Lai Thần Chưởng):**
  - Dựng hình Bàn Tay Phật khổng lồ quy chuẩn moveset: scale danh định 3.50, cấu trúc giải phẫu 5 ngón rõ ràng, ngón giữa dài nhất, ngấn đốt ngón tay tự nhiên, cổ tay đeo vòng Kim Cang Thủ Trạc khảm ngọc hồng lựu.
  - Ấn ký chữ Vạn (卍) sắc nét tại tâm lòng bàn tay kèm 3 vòng Mandala kim quang đồng tâm và 8 tia thần lực.
  - Sóng xung kích chưởng lực nén không gian bán kính $480\text{ px}$ tại scale 3.50 (tương ứng Chiêu 7 `giant_palm_suppression`).
  - Tích hợp pipeline tự động kích hoạt cho `WeaponType.GIANT_GOLDEN_PALM` và `CharacterSkin.BUDDHA_PALM` trong `composite_character()`, hỗ trợ linh hoạt 3 thứ tự lớp: `foreground`, `background`, `weapon`.
  - *Lưu ý kỹ thuật:* Hiệu ứng uốn cong dòng kẻ trang vở nền sẽ được thực thi tại Giai đoạn Compositing/VFX theo roadmap, không coi là chức năng đã hoàn thành tại Stage 5.
- [x] **6. Kiểm thử tự động & Hiện vật nghiệm thu:**
  - Bộ test toàn dự án đạt: **265 passed in 11.84s (100% PASS, 0 failed, 0 skipped)**.
  - Trọn bộ 9 ảnh preview, 1 collage 3x3 và 1 manifest JSON tại `out/preview/stickman/buddha_palm/`.

---

## 7. Trạng Thái Tổng Thể Giai Đoạn 5
- **Tiến độ G5:** **100% HOÀN TẤT & ĐÃ NGHIỆM THU ĐẦY ĐỦ** (Background, Skeleton, Pose Catalog, Body, Face/Accessories, Weapons, Buddha Palm).
- **Sẵn sàng chuyển giao:** Đã chuyển giao thành công sang **Giai đoạn 6 (Interpolation & Animation Loop)**.

---

## 8. Danh Sách Hạng Mục Nghiệm Thu Giai Đoạn 6 – Motion Interpolation & Animation Loop Engine

- [x] **1. Xây dựng Forward Kinematics (FK) Bone Angle Interpolation Engine (`app/modules/animation/interpolation_engine.py`):**
  - Trích xuất góc quay $\theta \in [-\pi, \pi]$ cho toàn bộ 13 đoạn xương có thứ bậc theo directed tree `TREE_ORDER` bắt nguồn từ `PELVIS` tại $(0, 0)$.
  - Nội suy góc xương theo cung tròn ngắn nhất (Shortest Circular Arc Wrapping): $\Delta \theta = (\theta_B - \theta_A + \pi) \pmod{2\pi} - \pi$.
  - Tái tạo tư thế bằng Forward Kinematics đảm bảo sai số độ dài xương đạt **$0.000\text{ px}$ tuyệt đối** (100% rigid bone length preservation), vượt qua mọi kiểm tra của `RigidBoneValidator`.
  - Hỗ trợ đầy đủ 5 hàm đường cong chuyển động (Easing): `LINEAR`, `EASE_IN`, `EASE_OUT`, `EASE_IN_OUT`, `CUBIC_BEZIER` (giải phương trình thông số bằng thuật toán chia đôi).
  - Nội suy góc vũ khí theo cung góc ngắn nhất (shortest degree arc), bảo toàn neo cầm vũ khí và liên kết hai tay (`align_two_hands`).
  - Giải quyết tiếp xúc mặt đất và nâng cao độ (Elevation): chống lún đất triệt để ($Y \le 1421.0\text{ px}$) và tự động chuyển đổi `SupportMode.AIRBORNE` khi rời đất.

- [x] **2. Xây dựng Animation Loop & Timeline Engine (`app/modules/animation/animation_loop.py`):**
  - Cấu trúc `Keyframe` (thời điểm, tên tư thế/tư thế tùy biến, vị trí canvas, hướng quay facing, độ nâng elevation, hàm easing).
  - Cấu trúc `AnimationTrack` (danh sách keyframe tự động sắp xếp theo timeline, tổng thời lượng, chế độ loop liền mạch).
  - `AnimationLoopEngine` cung cấp:
    - `get_state_at_time(track, time_sec)`: tính toán chính xác trạng thái nhân vật tại thời điểm bất kỳ, hỗ trợ vòng lặp vô tận (modulo timeline wrapping).
    - `render_frame()`: dựng hình từng khung hình bằng pipeline `composite_character()` kết hợp nền trang vở `NotebookBackgroundRenderer`.
    - `generate_clip_frames()`: xuất toàn bộ chuỗi khung hình ở tốc độ chuẩn 30 FPS.
    - `export_mp4_video()`: xuất video MP4 định dạng H.264 (`yuv420p`, tỷ lệ chuẩn 9:16 `1080x1920`) qua FFmpeg (`C:\ffmpeg\bin\ffmpeg.exe`).

- [x] **3. Kiểm thử tự động toàn diện (`tests/test_interpolation_engine.py`):**
  - 25 bài test đơn vị và tích hợp kiểm tra:
    - Tính đúng đắn, giới hạn và đơn điệu của các hàm Easing.
    - Sai số xương 0.000 px tuyệt đối trên mọi cặp tư thế `PoseCatalog` ở các bước $t \in [0, 1]$.
    - Tính đối xứng và tính bất biến theo tỷ lệ (scale invariance từ 0.5 đến 2.0).
    - Giữ vững bám tay vũ khí hai tay không bị trượt (two-handed grip tracking).
    - Không xuyên mặt đất ($Y \le 1421.0\text{ px}$).
    - Tính tái lập 100% bit-identical pixel rendering.
    - Xuất video MP4 qua FFmpeg và kiểm chứng thuộc tính bằng `ffprobe`.
  - **Kết quả kiểm thử toàn dự án:** **290 passed in 10.29s (100% PASS, 0 failed, 0 skipped)**.

- [x] **4. Xuất hiện vật xem trước trực quan (Visual Preview & Video Clips):**
  - Chạy `scripts/preview_animation_loop.py` sinh ra tại `out/preview/stickman/animation_loop/`:
    - `wukong_combat_loop.mp4`: Video vòng lặp chiến đấu Dark Wukong (4.0s @ 30 FPS = 120 frames, `1080x1920`, H.264, 613.5 KB).
    - `wukong_combat_loop_contact_sheet.png`: Bảng tổng hợp 8 khoảnh khắc tiêu biểu của chuỗi chiêu thức.
    - `buddha_palm_suppression.mp4`: Video giáng đòn Bàn Tay Phật Như Lai Thần Chưởng (2.0s @ 30 FPS = 60 frames, `1080x1920`, H.264, 346.1 KB).
    - `buddha_palm_suppression_contact_sheet.png`: Bảng tổng hợp 6 khoảnh khắc chưởng lực giáng thế.
    - `animation_loop_manifest.json`: Báo cáo metadata và kết quả kiểm tra `ffprobe` chi tiết.

---

## 9. Trạng Thái Tổng Thể Giai Đoạn 6
- **Tiến độ G6:** **100% HOÀN TẤT & ĐÃ NGHIỆM THU ĐẦY ĐỦ** (FK Interpolation, Rigidity, Timeline, Loop, Easing, Frame Compositing, MP4 Video Exporter).
- **Sẵn sàng chuyển giao:** Đã chuyển giao thành công sang **Giai đoạn 7 (SFX & Audio Integration Engine)**.

---

## 10. Danh Sách Hạng Mục Nghiệm Thu Giai Đoạn 7 – SFX & Audio Integration Engine

- [x] **1. Xây dựng Data Models & Audio Timeline (`app/modules/audio/audio_models.py`):**
  - Khởi tạo `AudioClip` với đầy đủ tham số: đường dẫn nguồn, timestamp bắt đầu, thời lượng, offset seek, gain dB, fade in/out, loop, enabled flag và metadata.
  - Phân loại 4 nhóm track chuẩn: `VOICEOVER` (giọng đọc), `SFX` (hiệu ứng âm thanh), `BGM` (nhạc nền), `AMBIENT` (không khí môi trường).
  - Khởi tạo `AudioTimeline` tự động sắp xếp clip theo timeline và trích xuất hợp nhất các khoảng thời gian voiceover (`get_voiceover_intervals`).
  - Cấu hình thông số ducking (`DuckingConfig`) và master mixing (`MixConfig`).

- [x] **2. Xây dựng Sound Library & Asset Management (`app/modules/audio/sound_library.py`):**
  - Quản trị cấu trúc thư mục tài nguyên: `assets/audio/sfx/`, `assets/audio/bgm/`, `assets/audio/voice/`, `assets/audio/ambient/`.
  - Hỗ trợ toàn bộ 17 hiệu ứng âm thanh Dark Myth quy chuẩn moveset (`whoosh_heavy`, `metal_weapon_clash`, `paper_shockwave`, `staff_whoosh_fast`, `multi_clash_rapid`, `vortex_spin_whoosh`, `body_impact_sweep`, `sky_leap_whoosh`, `earth_shatter_slam`, `divine_beam_charge`, `laser_clash_sizzle`, `heavenly_thunder_rumble`, `giant_palm_boom`, `heavy_body_hit`, `weapon_ground_scrape`, `dark_aura_hum`, `wind_howl`) và 2 chủ đề BGM (`dark_myth_orchestral`, `battle_tension_percussion`).
  - Tích hợp bộ tổng hợp âm thanh thủ tục (Procedural Waveform Synthesizer) tạo âm thanh chân thực (44.1kHz 16-bit Stereo WAV) khi chưa có file phòng thu, đảm bảo 100% hoạt động offline, chi phí 0 đồng, không giả lập dữ liệu rỗng.
  - Xuất bảng kê manifest minh bạch tại `assets/audio/sound_assets_manifest.json`.

- [x] **3. Xây dựng SFX Timeline Mapper (`app/modules/audio/sfx_timeline_mapper.py`):**
  - Tự động ánh xạ 8 `ActionPreset` chiến đấu từ `dark_myth_moveset_spec.md` sang các cue SFX chính xác theo tiến độ $u \in [0.0, 1.0]$.
  - Tích hợp các sự kiện `SfxEvent` chỉ định rõ trong `SceneSchema` vào timeline.
  - Khởi tạo timeline âm thanh hoàn chỉnh cho phân cảnh (`build_scene_timeline`) và toàn bộ video (`build_full_timeline`).

- [x] **4. Xây dựng Audio Compositor & Continuous Ducking Engine (`app/modules/audio/audio_compositor.py`):**
  - Triển khai thuật toán Audio Ducking chính xác từng sample bằng gain envelope: tự động giảm BGM -12dB mượt mà qua attack ramp 0.20s khi có giọng đọc thuyết minh, giữ nguyên trong suốt lời thoại, và phục hồi qua release ramp 0.35s sau khi dứt lời.
  - Phối trộn độc lập 4 stems cách ly (`voiceover`, `sfx`, `bgm`, `ambient`), cho phép nhiều SFX va chạm chồng lấp đồng thời mà không bị ngắt quãng.
  - Tích hợp Soft Peak Limiter: tự động phát hiện và hạ gain an toàn khi tổng biên độ vượt trần $-0.5\text{ dBFS}$, ngăn chặn 100% hiện tượng xé tiếng (clipping) và méo âm.
  - Đồng bộ thời lượng audio chính xác tuyệt đối với video.

- [x] **5. Xây dựng Video Audio Integrator & Muxing Pipeline (`app/modules/audio/video_audio_integrator.py`):**
  - Kết nối video hoạt ảnh G6 với audio timeline G7 qua lệnh FFmpeg multiplexing tối ưu (`-c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart`).
  - Kiểm tra thẩm định chéo bằng `ffprobe` xác nhận video stream (1080x1920, 30 FPS, H.264) và audio stream (AAC, 44100 Hz, stereo, 192kbps) tồn tại và đồng bộ.

- [x] **6. Kiểm thử tự động & Full Regression Suite:**
  - 17 bài test chuyên biệt trong `tests/test_audio_compositor.py` kiểm tra mọi nhánh chức năng, ducking envelope, limiter, overlapping clips, conversion, muxing.
  - **Toàn bộ 307 tests toàn dự án PASS 100% trong 12.94s (0 failed, 0 skipped)**.

- [x] **7. Xuất bản phẩm Demo thực tế hoàn chỉnh:**
  - Chạy `scripts/preview_audio_integration.py` xuất bản tại `out/preview/audio_integration/`:
    - `dark_myth_combat_demo.mp4`: Video hoàn chỉnh có âm thanh (1080x1920, 30 FPS, 5.364s, H.264 + AAC 192kbps, 807.3 KB) với giọng đọc tiếng Việt `vi-VN-HoaiMyNeural` (fallback từ `vi-VN-NamMinhNeural` do server timeout), BGM `dark_myth_orchestral` kèm ducking, và 6 SFX va chạm.
    - 5 tệp audio stems cách ly trong `stems/`: `stem_voiceover.wav`, `stem_sfx.wav`, `stem_bgm.wav`, `stem_ambient.wav`, `master_mixed.wav`.
    - Báo cáo kiểm định `audio_integration_manifest.json`.

---

## 11. Trạng Thái Tổng Thể Giai Đoạn 7
- **Tiến độ G7:** **100% HOÀN TẤT & ĐÃ NGHIỆM THU ĐẦY ĐỦ** (Sound Library, SFX Mapper, Compositor, Ducking, Limiter, Video Audio Integrator, FFmpeg Muxing).
- **Sẵn sàng chuyển giao:** Đã chuyển giao thành công sang **Giai đoạn 8 (Dark Corruption VFX Engine)**.

---

## 12. Danh Sách Hạng Mục Nghiệm Thu Giai Đoạn 8 – Dark Corruption VFX Engine

- [x] **1. Kiến trúc Dữ liệu & Sự kiện VFX (`app/modules/animation/vfx_models.py`):**
  - Định nghĩa chuẩn `VFXEventType`: `CLASH_SPARKS`, `GROUND_CRACK`, `SHOCKWAVE_RING`, `BACKGROUND_WARP`, `MOTION_TRAIL`, `DARK_AURA`, `BUDDHA_PALM_AURA`, `PAPER_DUST`.
  - Định nghĩa `WarpProfile`: `PALM_DEPRESSION` (đường kẻ ngang chùng võng xuống dưới áp lực Bàn Tay Phật) và `RADIAL_SHOCKWAVE` (sóng gợn xuyên tâm lan tỏa).
  - Cấu trúc `VFXEvent`, `Particle`, `VFXConfig` với đầy đủ tham số điều khiển, validation thời gian và vị trí Canvas `Point2D`.

- [x] **2. Biến Dạng Trường Tọa Độ Nền Giấy Vở (`app/modules/animation/vfx_distortion.py`):**
  - Triển khai `WarpDistortionField` sử dụng `PIL.Image.transform(Image.Transform.MESH)` kết hợp lưới nội suy 2D NumPy C-level, giải quyết biến dạng pixel thuần CPU cực nhanh (~66ms cho khung hình 1080x1920).
  - Tái hiện chân thực đường kẻ ngang giấy vở bị lún võng xuống theo trường trọng lực của Bàn Tay Phật và phục hồi nguyên vẹn khi chiêu thức kết thúc (Zero-distortion restoration).
  - Tối ưu hóa Zero Overhead: Khi không có sự kiện warp hoạt động hoặc biên độ $< 0.5\text{ px}$, trả về tham chiếu ảnh gốc lập tức với độ trễ 0ms.

- [x] **3. Hệ Thống Hạt Tất Định & Hiệu Ứng Va Chạm (`app/modules/animation/vfx_particles.py`):**
  - Xây dựng `ParticleSystem` tất định 100% (deterministic) thông qua seed ngẫu nhiên độc lập: tái hiện hạt giống hệt nhau khi render lại cùng frame/timestamp.
  - Tạo hình hào quang Dark Myth: Khói đen u ám bốc lên, tàn lửa đỏ thẫm bay lượn, xúc tua hắc ám vươn dài.
  - Hiệu ứng va chạm đa hạt: Tia lửa bắn tóe với vận tốc, lực cản không khí và trọng lực; vòng sóng kích nổ kép (double-ring shockwave); vết nứt mặt đất ziczac phân nhánh; bụi giấy văng tung tóe.

- [x] **4. Vệt Khí Vũ Khí Động Cảm Ứng (`app/modules/animation/vfx_motion_trail.py`):**
  - Xây dựng `MotionTrailRenderer` sử dụng ring buffer `collections.deque` theo dõi tọa độ chuôi và mũi vũ khí theo thời gian thực.
  - Render dải ribbon mờ dần (alpha gradient fade) với lưỡi chém cung tròn sắc bén phản ánh chuyển động của Thiết Bảng Như Ý và Tam Tiêm Đao.

- [x] **5. Bộ Ghép 7 Layer & Điều Phối VFX (`app/modules/animation/vfx_engine.py`):**
  - Tích hợp pipeline kết xuất 7 tầng:
    1. Layer 1: Nền giấy vở kẻ ngang (Background)
    2. Layer 2: Biến dạng không gian nền (Warp Distortion Field)
    3. Layer 3: Rạn nứt mặt đất & bụi giấy rơi (Ground Cracks & Paper Dust)
    4. Layer 4: Hào quang Hắc Ám phía sau nhân vật (Dark Corruption Back Aura)
    5. Layer 5: Nhân vật người que Hắc Ám Tây Du (Stickman Composite G5)
    6. Layer 6: Vệt kiếm khí vũ khí (Weapon Motion Trails)
    7. Layer 7: Hiệu ứng va chạm tiền cảnh (Clash Sparks & Shockwave Rings)
  - Tự động ánh xạ `ActionPreset` chiến đấu sang sự kiện VFX đồng bộ mili-giây với SFX G7.

- [x] **6. Kiểm Thử Tự Động & Hồi Quy Toàn Hệ Thống (`tests/test_vfx_engine.py`):**
  - 16/16 bài kiểm thử chuyên biệt đạt PASS 100% (Warp distortion, particle determinism, restoration, 7-layer compositing, performance benchmark).
  - Toàn bộ 323 bài kiểm thử toàn dự án đạt PASS 100% trong 17.33s (0 failed, 0 skipped, 0 regressions).

- [x] **7. Sản Phẩm Demo & Chứng Thực Kỹ Thuật Thực Tế (`scripts/preview_vfx_engine.py`):**
  - Video hoàn chỉnh: `out/preview/vfx/dark_myth_vfx_demo.mp4` (1080x1920 dọc 9:16, 30 FPS, 4.0s, H.264 + AAC, 1.16 MB).
  - Bảng tổng hợp ảnh khung hình chủ chốt (Contact Sheet): `out/preview/vfx/vfx_contact_sheet.png` (1560x1512, 1.15 MB, 8 khung hình tiêu biểu).
  - Báo cáo kiểm định kỹ thuật: `out/preview/vfx/vfx_manifest.json`.
  - Kết quả kiểm chứng `ffprobe`: Video và Audio streams đồng bộ tuyệt đối 4.000000s, không mất khung hình, không giật lag.

---

## 13. Trạng Thái Tổng Thể Giai Đoạn 8
- **Tiến độ G8:** **100% HOÀN TẤT & ĐÃ NGHIỆM THU ĐẦY ĐỦ** (Dark Aura, Ruled Line Warp Distortion, Motion Trails, Clash Sparks, Ground Cracks, 7-Layer Compositor, Audio-Visual Sync).
- **Sẵn sàng chuyển giao:** Đủ điều kiện kỹ thuật để tiến sang **Giai đoạn 9 (Local Studio Web UI & Telegram Bot Integration)**.

---

## 14. Danh Sách Hạng Mục Nghiệm Thu Giai Đoạn 9 – Local Studio Web UI & Telegram Bot Integration

- [x] **1. Kiến Trúc Backend Tích Hợp Độc Lập & Bất Đồng Bộ (`app/services/job_service.py`):**
  - Xây dựng singleton `JobService` tích hợp `ThreadPoolExecutor` (2 worker slots mặc định) xử lý hàng đợi non-blocking cho cả Web UI và Telegram Bot.
  - Hỗ trợ đầy đủ hủy tác vụ an toàn qua `cancel_job(job_id)`, cập nhật log vòng xoay bộ nhớ đệm (circular buffer 100 log lines) và cơ chế callback lắng nghe trạng thái.
  - Sử dụng chung một kho tác vụ `TaskManager` và bộ điều phối `PipelineOrchestrator`, loại bỏ hoàn toàn trùng lặp pipeline.

- [x] **2. Giao Diện Người Dùng Gradio Local Studio Web UI (`app/ui/studio_app.py`):**
  - Giao diện thiết kế chuẩn Dark Myth `#0d0e15` (than hắc ám), viền đỏ thẫm `#8b1c1c` và điểm xuyết ánh vàng `#d4af37`.
  - Tab **Tạo Video (Studio)**: Khu vực nhập kịch bản tiếng Việt hoặc upload tệp `.txt` / `.json`, tùy chỉnh ngoại hình nhân vật (`CharacterSkin`), vũ khí (`WeaponType`), chiêu thức (`ActionPreset`), giọng đọc Edge-TTS (`vi-VN-NamMinhNeural` / `vi-VN-HoaiMyNeural`), tốc độ, nhạc nền BGM và các tùy chọn bật/tắt hiệu ứng VFX.
  - Non-blocking polling: Badge trạng thái thời gian thực, thanh tiến độ % động theo từng giai đoạn, hộp hiển thị log trực tiếp, trình phát video 9:16 dọc nhúng sẵn và nút tải file MP4 trực tiếp.
  - Tab **Lịch Sử & Bộ Sưu Tập (History & Gallery)**: Hiển thị bảng tổng hợp các tác vụ đã render với trạng thái, thời lượng, dung lượng và nút nạp video xem lại một chạm.
  - Tab **Chẩn Đoán Hệ Thống (System Health)**: Báo cáo tình trạng phần cứng CPU/RAM, kiểm tra phiên bản Python, đường dẫn nhị phân FFmpeg/FFprobe, thư mục lưu trữ và trạng thái Telegram Bot.

- [x] **3. Trợ Lý Tự Động Telegram Bot (`app/bot/telegram_bot.py`):**
  - Triển khai `DarkMythTelegramBot` trên nền tảng `python-telegram-bot` v22 (hỗ trợ long-polling và webhook).
  - Đầy đủ 8 lệnh nghiệp vụ chuẩn: `/start`, `/help`, `/status`, `/generate <kịch bản>`, `/progress [job_id]`, `/history`, `/download <job_id>`, `/cancel [job_id]`.
  - Hỗ trợ tải tệp đính kèm kịch bản (`.txt`, `.json`) trực tiếp trong khung chat Telegram để tự động kích hoạt tiến trình render.
  - Cơ chế bảo mật kép: Whitelist người dùng cho phép (`TELEGRAM_ALLOWED_USERS`), phòng thủ chống tấn công đường dẫn Path Traversal khi download video.
  - Chế độ Standby tự động: Nếu chưa cấu hình `TELEGRAM_BOT_TOKEN`, bot tự động chuyển sang chế độ chờ an toàn, không làm gián đoạn Web UI.

- [x] **4. Điểm Khởi Chạy Hợp Nhất & Batch Scripts (`app/main.py`, `run_*.bat`):**
  - Điểm vào lệnh CLI `app/main.py` với kiểm tra môi trường tiền trạm (preflight checks) và hỗ trợ đa tham số: `--studio` (chỉ mở Web UI), `--bot` (chỉ chạy Bot), `--all` (chạy song song cả hai).
  - 3 script thực thi tiện lợi cho Windows: `run_studio.bat`, `run_bot.bat`, `run_all.bat`.

- [x] **5. Bộ Kiểm Thử Tự Động Toàn Diện (`tests/`):**
  - `tests/test_job_service.py`: 5 bài kiểm thử singleton, submit kịch bản, đệm log, hủy tác vụ.
  - `tests/test_studio_app.py`: 10 bài kiểm thử các hàm tiện ích UI, validate kịch bản, phân giải preset, format chẩn đoán và build Gradio Blocks.
  - `tests/test_telegram_bot.py`: 8 bài kiểm thử xác thực whitelist, lệnh `/help`, `/status`, `/generate`, xử lý upload tệp và phòng vệ path traversal.
  - Toàn bộ 23 bài test G9 đạt **23/23 PASS**; hồi quy toàn dự án đạt **346/346 PASS (100%)** trong 20.55s.

- [x] **6. Kiểm Thử Tích Hợp Thực Tế & Sản Phẩm Video Demo (`scripts/preview_studio_integration.py`):**
  - Thực thi toàn trình sản xuất video qua `JobService` với kịch bản Hắc Ám Tây Du 2 cảnh thực tế.
  - Tự động chạy tuần tự: Phân tích kịch bản $\rightarrow$ Tạo giọng đọc tiếng Việt Edge-TTS $\rightarrow$ Dựng hoạt ảnh người que G5.2.3 $\rightarrow$ Áp hiệu ứng Dark Corruption VFX G8 $\rightarrow$ Trộn âm thanh Voice/SFX/BGM ducking G7 $\rightarrow$ Kết xuất video MP4 dọc 9:16.
  - Video thành phẩm: `out/job_20261101_678d36.mp4` (1.81 MB, 8.73s).
  - Bản lưu trữ nghiệm thu: `out/preview/studio/g9_demo_job_20261101_678d36.mp4`.
  - Xác thực kỹ thuật bằng `ffprobe`: Video H.264 (1080x1920, 30 FPS, yuv420p), Audio AAC (44.1 kHz, stereo, 8.73s), khớp thời lượng hoàn hảo.

---

## 15. Trạng Thái Tổng Thể Giai Đoạn 9
- **Tiến độ G9:** **100% HOÀN TẤT & ĐÃ NGHIỆM THU ĐẦY ĐỦ** (Gradio Studio UI, Telegram Bot, JobService Concurrency, Video Output 9:16, 346/346 Tests PASS).
- **Sẵn sàng chuyển giao:** Đủ điều kiện kỹ thuật để tiến sang **Giai đoạn 10 (End-to-End Verification, Stress Test & Final Packaging)**.

---

## 16. Danh Sách Hạng Mục Nghiệm Thu Giai Đoạn 10 – End-to-End Verification, Stress Test & Final Packaging

- [x] **1. Kiểm Thử Toàn Trình Thực Tế (Full E2E Production Verification):**
  - Thực thi toàn bộ pipeline sản xuất video từ đầu vào kịch bản Hắc Ám Tây Du 2 cảnh mới hoàn toàn (`Đại Chiến Hắc Ám: Thiết Bảng Như Ý Trấn Áp Thiên Binh`).
  - Sản xuất video thành phẩm thực tế: `out/job_20261102_7074c0.mp4` (3.56 MB, 19.46s).
  - Bản lưu trữ nghiệm thu: `out/preview/g10_final/g10_final_demo_video.mp4`.
  - Xác thực kỹ thuật bằng `ffprobe`: Độ phân giải `1080x1920` (chuẩn dọc 9:16), FPS 30, video codec `h264 (yuv420p)`, audio codec `aac (stereo, 44100 Hz)`, video và audio khớp thời lượng tuyệt đối `19.46s`, zero black frames, zero audio clipping.
  - Xuất bản Contact Sheet ảnh khung hình chủ chốt: `out/preview/g10_final/g10_contact_sheet.png`.

- [x] **2. Kiểm Thử Chịu Tải & Đồng Thời (Concurrency & Multi-tasking Stress Test):**
  - Chạy đồng thời 2 tác vụ render song song trong JobService: `job_20261102_42d5d7` và `job_20261102_5b6661`.
  - Cả 2 tác vụ hoàn thành đồng thời trong 142.62s mà không xung đột tài nguyên, không ghi đè tệp của nhau (`out/job_20261102_42d5d7.mp4` [1.27 MB] và `out/job_20261102_5b6661.mp4` [0.87 MB]).
  - Kiểm tra hàng đợi FIFO: Tác vụ thứ 3 được đưa vào trạng thái `queued` và tự động kích hoạt khi có worker slot trống.

- [x] **3. Kiểm Thử Hủy Tác Vụ & Phục Hồi Lỗi (Cancellation & Error Recovery):**
  - Hủy tác vụ an toàn qua `job_service.cancel_job(job_id)`: Chuyển trạng thái sang `FAILED` kèm lý do hủy rõ ràng, không để lại tiến trình mồ côi.
  - Chống chịu dữ liệu lỗi: Kịch bản rỗng hoặc kịch bản quá ngắn được bắt lỗi sạch bằng `ValueError`, không làm crash thread pool hoặc treo ứng dụng.
  - Tự động dọn dẹp thư mục tạm `out/temp/<job_id>` sau khi hoàn tất hoặc lỗi, đảm bảo giải phóng hoàn toàn dung lượng đĩa.

- [x] **4. Hồ Sơ Hiệu Năng & Tài Nguyên Hệ Thống (Resource Profiling):**
  - RAM Baseline Idle: `90.05 MB`.
  - RAM Peak Rendering: `254.20 MB` (Mức tăng: `+164.15 MB` trong lúc render 1080x1920 VFX & Stickman).
  - RAM Sau Xử Lý: `93.41 MB` (Bộ nhớ được thu hồi sạch về mức ban đầu, xác nhận **Zero Memory Leak**).
  - Tốc độ xử lý: ~19.36x thời gian thực trên CPU thông thường (0 đồng chi phí phần cứng chuyên dụng/GPU).

- [x] **5. Kiểm Toán An Toàn & Bảo Mật (Security & Safety Audit):**
  - `.env` được bảo vệ nghiêm ngặt trong `.gitignore`, không rò rỉ token hay API key vào Git hoặc log.
  - Phòng thủ Path Traversal: Chặn đứng mọi nỗ lực truy cập vượt ra ngoài thư mục `out/`.
  - Telegram Bot Whitelist: Cơ chế phân quyền hoạt động chính xác theo danh sách ID người dùng.
  - Safe Standby Mode: Telegram Bot tự động vào chế độ chờ an toàn khi chưa có token, không gây ảnh hưởng đến Gradio Web UI.

- [x] **6. Hoàn Thiện Đóng Gói Windows & Khởi Chạy Một Chạm:**
  - `setup_environment.bat`: Tự động kiểm tra Python 3.15, khởi tạo `.venv`, cài đặt `requirements.txt`, thiết lập thư mục và chạy chẩn đoán `scripts/preflight_check.py`.
  - `run_studio.bat`: Khởi chạy giao diện Gradio Local Studio Web UI tại `http://localhost:7860`.
  - `run_bot.bat`: Khởi chạy Telegram Bot độc lập.
  - `run_all.bat`: Khởi chạy song song cả Studio và Telegram Bot.
  - `stop_app.bat`: Dừng an toàn toàn bộ tiến trình ứng dụng.
  - `scripts/preflight_check.py`: Công cụ kiểm tra môi trường tiền trạm độc lập đạt 5/5 tiêu chí.

- [x] **7. Bộ Kiểm Thử Hồi Quy Toàn Diện Cuối Cùng (Full Regression Test Suite):**
  - Bổ sung bộ test G10 tại `tests/test_g10_e2e_stress.py` (7 tests).
  - Toàn bộ **353/353 bài test** toàn dự án đạt **100% PASS** trong 16.57s (0 failed, 0 skipped).

- [x] **8. Hồ Sơ Nghiệm Thu & Bàn Giao Hoàn Chỉnh:**
  - Xuất bản Manifest G10 tại `out/preview/g10_final/g10_final_manifest.json`.
  - Cập nhật tài liệu hướng dẫn người dùng `README.md` chi tiết từ A–Z bằng tiếng Việt.

---

## 17. Trạng Thái Tổng Thể Toàn Dự Án G1–G10
- **Tiến độ G10:** **100% HOÀN TẤT & ĐÃ NGHIỆM THU ĐẦY ĐỦ** (E2E Verification, Concurrency Stress Test, Cancellation & Resilience, Resource Profiling, Windows One-Click Packaging, 353/353 Tests PASS).
- **Trạng thái bàn giao cuối cùng:** **G10 ACCEPTED** (Ứng dụng đã sẵn sàng bàn giao cho người dùng sử dụng thực tế trên Windows). DỪNG LẠI HOÀN TOÀN để xuất báo cáo bàn giao cuối cùng theo Supreme Directives.
