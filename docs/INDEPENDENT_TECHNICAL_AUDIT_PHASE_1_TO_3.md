# BÁO CÁO KIỂM ĐỊNH KỸ THUẬT ĐỘC LẬP (INDEPENDENT TECHNICAL AUDIT REPORT)
**Dự án:** Dark Myth Stickman Auto-Studio  
**Phạm vi kiểm định:** Giai đoạn 1 (Project Foundation), Giai đoạn 2 (Research & Resources), Giai đoạn 3 (Core Skeleton & Contracts)  
**Vai trò thực hiện:** Senior Software Architect, Senior Python Engineer, Video Pipeline Engineer & Lead QA  
**Ngày thực hiện:** 2026-10-31  
**Mục tiêu kiểm định:** Đánh giá độc lập, khách quan, dựa trên bằng chứng kỹ thuật thực tế (Evidence-First Verification) để xác định xem dự án đã thực sự hoàn thành Giai đoạn 1–3 và có đủ điều kiện chuyển sang Giai đoạn 4 hay chưa.

---

## A. EXECUTIVE SUMMARY (TÓM TẮT ĐIỀU HÀNH)

Sau quá trình rà soát mã nguồn, kiểm tra môi trường thực thi, chạy lại bộ kiểm thử tự động và đối chiếu hợp đồng kiến trúc, nhóm kiểm định đưa ra kết luận:

1. **Về Khung Kiến Trúc & Hợp Đồng Dữ Liệu (Giai đoạn 1 & 3):**
   - Bộ khung trừu tượng gồm Cấu hình (`AppConfig`), Ghi log cấu trúc (`logger.py`), Phân tầng ngoại lệ (`AutoStudioError`), Bộ quản lý tác vụ (`TaskManager`), Bộ điều phối luồng (`PipelineOrchestrator`), các Interface trừu tượng (`IScriptParser`, `IAudioEngine`, `IAnimationEngine`, `IVideoCompositor`) và Hợp đồng Schema Pydantic (`ScriptInput`, `SceneSchema`, `JobRecord`, `RenderResult`) **đã được xây dựng bài bản, cú pháp chuẩn xác và 20/20 bài unit test đều PASSED trên môi trường Windows (Python 3.15.2)**.
   - Nguyên tắc **Audio-First Timing** (đo thời lượng giọng đọc trước, truyền số giây sang bộ hoạt họa để tính số lượng khung hình) đã được thể hiện đúng trong luồng điều phối của `PipelineOrchestrator`.

2. **Về Bản Chất Mã Nguồn Thực Tế (Brutal Technical Reality):**
   - **Tất cả các module nghiệp vụ trong `app/modules/` hiện tại 100% là STUB / MOCK / FAKE:**
     - `StubScriptParser` chỉ cắt chuỗi theo dòng mới bằng Regex.
     - `StubAudioEngine` ghi 20 bytes chuỗi giả lập `b"RIFF_STUB_WAV_PHASE3"` và tính thời lượng giả lập theo số lượng từ. Chưa tích hợp `edge-tts`, `pydub` hay `mutagen`.
     - `StubAnimationEngine` chỉ ghi một tệp JSON manifest. Chưa hề vẽ bất kỳ một pixel hay khung hình nào bằng `OpenCV`, `Pillow` hay `numpy`.
     - `StubVideoCompositor` ghi 25 bytes chuỗi giả lập `b"MP4_STUB_CONTAINER_PHASE3"`. Chưa hề gọi FFmpeg, chưa hòa âm đa kênh và chưa tạo ra tệp video MP4 thực tế nào.
   - **Môi trường thiếu thành phần sống còn cho Pipeline Video/Audio:**
     - `ffmpeg` và `ffprobe` **chưa hề có mặt trong hệ thống Windows hiện tại** (`where.exe ffmpeg` trả về rỗng). Do đó, khả năng xuất video MP4 thực tế hiện đang ở trạng thái **BLOCKED**.
     - Trong 16 gói thư viện khai báo tại `requirements.txt`, hiện tại môi trường ảo `.venv` **mới chỉ cài đặt 4 gói phục vụ test khung xương** (`pydantic`, `python-dotenv`, `pytest`, `pytest-asyncio`). 12 gói nghiệp vụ còn lại chưa được cài đặt vào `.venv`.
   - **TaskManager có sai lệch giữa báo cáo trước và code thực tế:**
     - Báo cáo trước tuyên bố có `threading.Lock` ngăn Race Condition, nhưng mã nguồn `app/core/task_manager.py` thực tế **không hề có `threading.Lock`**.
     - Hàm lưu trạng thái `save_job()` ghi trực tiếp bằng `path.write_text()` mà không dùng cơ chế ghi an toàn (Atomic Write), có nguy cơ làm hỏng tệp JSON nếu hệ thống tắt đột ngột.
   - **Chưa có Entry Point khởi chạy ứng dụng:** Không có `main.py`, không có `app/main.py` và thư mục `scripts/` chỉ có `.gitkeep`. Tệp `README.md` vẫn giữ nguyên nội dung cũ của Google AI Studio (Node.js).

3. **Quyết định Nghiệm thu:** **CONDITIONALLY APPROVED (PHÊ DUYỆT CÓ ĐIỀU KIỆN)**.  
   Dự án đủ điều kiện bước vào Giai đoạn 4 với phạm vi giới hạn: Xây dựng module **Vietnamese TTS & Audio Timing Engine**, NHƯNG phải hoàn tất các điều kiện tiên quyết (Cài đặt FFmpeg trên Windows, cấu hình `FFMPEG_PATH` và cài đặt các package âm thanh vào `.venv`) trước khi thực hiện các bài test âm thanh thực tế.

---

## B. THÔNG TIN REPOSITORY VÀ MÔI TRƯỜNG THỰC THI

| Thông số | Trạng thái thực tế | Bằng chứng kiểm tra |
| :--- | :--- | :--- |
| **Đường dẫn dự án** | `C:\Users\phamtrong\Desktop\video agent` | Lệnh `Get-Location` |
| **Hệ điều hành** | Windows 11 Pro 64-bit (Build `10.0.26300.0`) | `[System.Environment]::OSVersion` |
| **Python Executable** | `C:\Users\phamtrong\Desktop\video agent\.venv\Scripts\python.exe` | `sys.executable` |
| **Phiên bản Python** | `Python 3.15.2` (MSC v.1951 64-bit, AMD64) | `sys.version` |
| **Môi trường ảo (.venv)** | Đã khởi tạo và hoạt động độc lập | Thư mục `.venv\` tồn tại |
| **Gói đã cài trong .venv**| 4 gói lõi: `pydantic 2.14.2`, `python-dotenv 1.2.4`, `pytest 9.2.0`, `pytest-asyncio 1.4.1` (+ các phụ thuộc) | `pip list` |
| **Gói chưa cài trong .venv**| 12 gói: `numpy`, `Pillow`, `opencv-python-headless`, `scipy`, `edge-tts`, `pydub`, `audioop-lts`, `mutagen`, `ffmpeg-python`, `python-telegram-bot`, `gradio`, `google-genai` | Đối chiếu `requirements.txt` vs `pip list` |
| **Trạng thái Git** | Đã khởi tạo kho `git init`, nhánh `master`, chưa có commit nào (tất cả files đang Untracked) | `git status` |
| **Trạng thái FFmpeg** | **KHÔNG TỒN TẠI TRÊN HỆ THỐNG (BLOCKED)** | `where.exe ffmpeg` $\rightarrow$ `Could not find files` |
| **Trạng thái ffprobe** | **KHÔNG TỒN TẠI TRÊN HỆ THỐNG (BLOCKED)** | `where.exe ffprobe` $\rightarrow$ `Could not find files` |

---

## C. BẢNG KIỂM ĐỊNH TOÀN DIỆN (AUDIT MATRIX)

| ID | Hạng mục kiểm định | Trạng thái | Bằng chứng thực tế | Vấn đề phát hiện | Mức độ | Hành động tiếp theo |
|:---:|:---|:---:|:---|:---|:---:|:---|
| **C01** | Cấu trúc thư mục nền tảng (`in/`, `out/`, `assets/`, `docs/`, `app/`, `tests/`) | **PASS** | `Get-ChildItem -Directory` hiển thị đầy đủ các thư mục theo chuẩn Giai đoạn 1. | Không có. | INFO | Duy trì cấu trúc. |
| **C02** | Điểm khởi chạy ứng dụng (Application Entry Point) | **FAIL** | Không có `main.py` ở root, không có `app/main.py`, `scripts/` rỗng. | Ứng dụng chỉ có thể chạy qua `pytest`, chưa có entry point để chạy độc lập. | **P2** | Tạo `app/main.py` hoặc `scripts/run_pipeline.py`. |
| **C03** | Tài liệu hướng dẫn vận hành (`README.md`) | **FAIL** | [README.md](file:///c:/Users/phamtrong/Desktop/video agent/README.md) chứa hướng dẫn `npm install` và `npm run dev` của Node.js. | Tài liệu hướng dẫn hoàn toàn lỗi thời, sai lệch 100% so với dự án Python. | **P3** | Viết lại `README.md` theo chuẩn Python / venv / pytest. |
| **C04** | Cơ chế cấu hình hệ thống (`AppConfig`) | **PASS** | `app/core/config.py` đọc `.env`, kiểm tra kích thước `1080x1920` và tạo thư mục tự động. | Thiếu thuộc tính cấu hình đường dẫn `ffmpeg_path` / `ffprobe_path`. | **P2** | Bổ sung `ffmpeg_path` vào `AppConfig` và `.env.example`. |
| **C05** | Hệ thống ghi log cấu trúc (`logger.py`) | **PASS** | Chạy kiểm thử sinh log `logs/app.log` có format `%(asctime)s \| %(levelname)s \| [job=%(job_id)s]`. | Không có. Đã kiểm chứng qua `test_logger_writes_structured_output_with_job_id`. | INFO | Duy trì sử dụng. |
| **C06** | Phân tầng ngoại lệ (`exceptions.py`) | **PASS** | Đầy đủ 6 lớp ngoại lệ kế thừa `AutoStudioError`. | Không có. Đã kiểm chứng qua unit test. | INFO | Duy trì sử dụng. |
| **C07** | Quản lý tác vụ & State Machine (`task_manager.py`) | **PASS** | Quản lý 7 trạng thái chuẩn, chặn bước nhảy bất hợp pháp, lưu JSON tại `out/jobs/`. | Không có `threading.Lock` như báo cáo cũ khẳng định; `save_job` chưa dùng Atomic Write. | **P2** | Bổ sung `threading.Lock` và ghi file tạm trước khi rename (`os.replace`). |
| **C08** | Hợp đồng Schema Pydantic (`app/schemas/`) | **PASS** | `ScriptInput`, `SceneSchema`, `JobRecord`, `RenderResult` đều kiểm tra ràng buộc chặt chẽ. | Có sự lệch tên trường (Schema Drift) giữa `docs/04` và code (được bù trừ qua alias). | **P2** | Chuẩn hóa tài liệu `docs/04` khớp với tên trường code hiện tại. |
| **C09** | Giao diện Interface trừu tượng (`app/interfaces/`) | **PASS** | 4 lớp ABC (`IScriptParser`, `IAudioEngine`, `IAnimationEngine`, `IVideoCompositor`) có chữ ký hàm chuẩn. | Không có. | INFO | Giữ nguyên làm hợp đồng phát triển các giai đoạn sau. |
| **C10** | Luồng điều phối toàn trình (`orchestrator.py`) | **PASS** | Thực thi đúng quy trình Audio-First Timing, bẫy lỗi cô lập và tự dọn dẹp thư mục tạm. | Các module thành phần kết nối hiện tại 100% là Stub/Mock. | INFO | Sẵn sàng thay thế Stub bằng Engine thực tế từ GĐ4. |
| **C11** | Triển khai Engine nghiệp vụ (`app/modules/`) | **FAIL** *(với vai trò production)* | `app/modules/*` chỉ gồm các Stub trả về dữ liệu mẫu (20B audio fake, 25B mp4 fake). | Toàn bộ chức năng thực tế của Giai đoạn 4, 5, 6, 7 chưa được triển khai (đúng lộ trình). | INFO | Sẽ triển khai tuần tự từ Giai đoạn 4. |
| **C12** | Môi trường FFmpeg & ffprobe | **BLOCKED** | Lệnh `where.exe ffmpeg` trả về mã lỗi 1, không tìm thấy executable. | Không thể chuyển đổi âm thanh MP3 hay kết xuất video MP4 thực tế. | **P1** | Bắt buộc cài đặt FFmpeg trên Windows trước khi chạy video. |
| **C13** | Khả năng tương thích Python 3.15 với thư viện GĐ4+ | **NOT VERIFIED** | Đã dry-run pip thấy wheel tồn tại, nhưng chưa cài đặt thực tế vào `.venv`. | Python 3.15 không có C compiler trên máy, nếu package nào thiếu wheel sẽ bị lỗi. | **P1** | Cài đặt thử nghiệm nhóm gói Giai đoạn 4 (`edge-tts`, `pydub`, `audioop-lts`, `mutagen`). |
| **C14** | Bộ kiểm thử tự động (`tests/`) | **PASS** | Chạy `pytest -v` vượt qua 20/20 bài test trong 0.22 giây. | Các bài test pipeline chỉ chứng minh luồng điều khiển với Stub, chưa kiểm thử implementation thật. | **P2** | Bổ sung integration test với file audio/video thật ở GĐ4+. |

---

## D. KẾT QUẢ KIỂM THỬ THỰC TẾ (TEST EXECUTION EVIDENCE)

### 1. Thông số Lượt chạy Kiểm thử
- **Lệnh thực thi:** `.\.venv\Scripts\pytest.exe -v --durations=0`
- **Môi trường thực thi:** Python 3.15.2, pytest-9.2.0, pluggy-1.7.0 trên Windows 11.
- **Tổng số test phát hiện:** 20 test cases.
- **Tổng số test chạy thực tế:** 20 test cases.
- **Kết quả:** **20 PASSED**, 0 FAILED, 0 ERROR, 0 SKIPPED.
- **Thời gian chạy:** 0.22 giây.

### 2. Phân loại Bản chất các Bài Test Hiện Có

```text
tests/
├── test_config_and_logger.py (5 tests - 100% KIỂM TRA CODE THỰC TẾ)
│   ├── test_package_imports_cleanly [PASSED] -> Kiểm tra import toàn bộ module nội bộ
│   ├── test_config_creates_required_directories_and_safe_defaults [PASSED] -> Kiểm tra tạo thư mục thực tế
│   ├── test_config_loads_custom_env_file [PASSED] -> Kiểm tra đọc file .env thực tế
│   ├── test_logger_writes_structured_output_with_job_id [PASSED] -> Kiểm tra ghi file log thực tế
│   └── test_layered_exceptions_format_job_id_and_stage [PASSED] -> Kiểm tra format chuỗi ngoại lệ
│
├── test_schemas.py (7 tests / 12 assertions - 100% KIỂM TRA CODE THỰC TẾ)
│   ├── test_valid_scene_schema_and_contract_compatibility [PASSED] -> Kiểm tra Schema & Alias
│   ├── test_scene_schema_rejects_invalid_data (6 tham số) [PASSED] -> Kiểm tra Validation Error
│   ├── test_script_input_validation [PASSED] -> Kiểm tra ràng buộc kịch bản đầu vào
│   └── test_job_record_and_render_result_validation [PASSED] -> Kiểm tra ràng buộc tác vụ
│
├── test_task_manager.py (4 tests - 100% KIỂM TRA CODE THỰC TẾ)
│   ├── test_task_manager_create_and_persist_job [PASSED] -> Kiểm tra tạo job và ghi file JSON
│   ├── test_task_manager_full_happy_path_transitions [PASSED] -> Kiểm tra luồng chuyển trạng thái
│   ├── test_task_manager_blocks_illegal_state_jump [PASSED] -> Kiểm tra chặn bước nhảy sai
│   └── test_task_manager_handles_job_failure_cleanly [PASSED] -> Kiểm tra trạng thái thất bại
│
└── test_pipeline_skeleton.py (2 tests - 100% DÙNG STUB / MOCK)
    ├── test_pipeline_orchestrator_end_to_end_with_stubs [PASSED]
    │   └── BẢN CHẤT: Kiểm tra thứ tự gọi hàm (Spy call_log) giữa các Stub.
    │       KHÔNG kiểm tra tạo âm thanh thật, KHÔNG kiểm tra vẽ hoạt họa thật, KHÔNG kiểm tra xuất MP4 thật.
    └── test_pipeline_orchestrator_catches_module_failure_and_marks_job_failed [PASSED]
        └── BẢN CHẤT: Sử dụng FailingAudioEngine giả lập để kiểm tra cơ chế bắt lỗi của Orchestrator.
```

### 3. Những Lỗ hổng Bộ Test Hiện Tại Chưa Bao Quát Được
1. **Chưa có kiểm thử đa luồng (Concurrency Test):** Chưa có bài test nào kiểm tra xem nếu 2 luồng cùng gọi `transition_status()` trên cùng một `job_id` thì trạng thái có bị ghi đè hỗn loạn hay không.
2. **Chưa có kiểm thử khả năng phục hồi sau sự cố (Crash Recovery Test):** Chưa kiểm tra trường hợp file JSON bị hỏng (0 byte hoặc JSON dở dang) thì `load_job()` xử lý ra sao.
3. **Chưa có kiểm thử tích hợp công cụ ngoại vi (External Tool Test):** Vì hệ thống chưa có FFmpeg, chưa có bài test nào gọi subprocess thực tế.

---

## E. DANH SÁCH LỖI VÀ VẤN ĐỀ KỸ THUẬT (DEFECT REGISTER)

### MỨC ĐỘ P1 — CRITICAL (Rủi ro nghiêm trọng cần giải quyết trước khi làm việc với Media)

#### [P1-01] Thiếu hoàn toàn Executable FFmpeg và ffprobe trên Hệ điều hành Windows
- **Mô tả:** Lệnh `where.exe ffmpeg` và `where.exe ffprobe` không tìm thấy bất kỳ tệp thực thi nào.
- **Bằng chứng:**
  ```powershell
  PS C:\Users\phamtrong\Desktop\video agent> where.exe ffmpeg
  INFO: Could not find files for the given pattern(s).
  ```
- **Tác động:** Khi triển khai Giai đoạn 4, `pydub` sẽ không thể chuyển đổi định dạng âm thanh (nếu dùng MP3/AAC) và ném ra lỗi `FileNotFoundError`. Ở Giai đoạn 7, toàn bộ pipeline kết xuất video sẽ dừng hoạt động vì không thể mở pipe encode H.264.
- **Phương án khắc phục:**
  1. Cài đặt FFmpeg trên Windows bằng lệnh PowerShell Admin: `winget install Gyan.FFmpeg`
  2. Hoặc tải bản build essentials từ `gyan.dev`, giải nén vào `C:\ffmpeg` và bổ sung `C:\ffmpeg\bin` vào biến môi trường `PATH`.

#### [P1-02] 12 Gói Thư viện Phục vụ Nghiệp vụ Chưa được Cài đặt vào Môi trường `.venv`
- **Mô tả:** Môi trường `.venv` hiện chỉ chứa các gói test skeleton. Các thư viện cho âm thanh (`edge-tts`, `pydub`, `audioop-lts`, `mutagen`) và đồ họa (`Pillow`, `numpy`, `opencv-python-headless`) chưa có mặt trong môi trường ảo.
- **Bằng chứng:** Kết quả `pip list` trong `.venv` chỉ liệt kê 14 package (chỉ gồm `pytest`, `pydantic`, `dotenv` và các package phụ thuộc trực tiếp).
- **Tác động:** Không thể bắt đầu viết mã nguồn thực tế cho Giai đoạn 4 nếu chưa cài đặt các gói âm thanh.
- **Phương án khắc phục:** Kích hoạt `.venv` và chạy lệnh cài đặt nhóm thư viện cho Giai đoạn 4:
  ```powershell
  .\.venv\Scripts\pip.exe install "edge-tts>=6.1.9" "pydub>=0.25.1" "audioop-lts>=0.2.1" "mutagen>=1.46.0"
  ```

---

### MỨC ĐỘ P2 — MAJOR (Vấn đề kiến trúc và độ tin cậy cần khắc phục sớm)

#### [P2-01] `TaskManager` Thiếu Cơ chế Khóa Đa Luồng (`threading.Lock`)
- **Mô tả:** Báo cáo kiểm toán trước đó khẳng định `TaskManager` dùng `threading.Lock()` để chống Race Condition. Tuy nhiên, rà soát mã nguồn `app/core/task_manager.py` cho thấy không có bất kỳ dòng nào import hay sử dụng `threading.Lock`.
- **Bằng chứng:** Lệnh tìm kiếm chuỗi `Select-String -Path "app\core\task_manager.py" -Pattern "Lock", "threading"` trả về kết quả rỗng.
- **Tác động:** Nếu sau này Web UI hoặc Telegram Bot gọi cập nhật trạng thái tác vụ đồng thời trên nhiều thread của async event loop, từ điển `_jobs` và file JSON có nguy cơ bị xung đột trạng thái (Race Condition).
- **Phương án khắc phục:** Thêm `self._lock = threading.Lock()` vào `TaskManager.__init__` và bọc khối `with self._lock:` trong các hàm `save_job`, `transition_status`, `mark_completed`, `mark_failed`.

#### [P2-02] Cơ chế Ghi File JSON của `TaskManager` Chưa An Toàn (Non-Atomic File Write)
- **Mô tả:** Hàm `save_job()` trong `app/core/task_manager.py` ghi đĩa bằng lệnh:
  ```python
  path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
  ```
- **Bằng chứng:** Mã nguồn tại dòng 60 tệp `app/core/task_manager.py`.
- **Tác động:** Nếu máy tính bị mất điện, process bị dừng đột ngột (SIGKILL) đúng lúc đang ghi file, tệp JSON sẽ bị cụt hoặc mang dung lượng 0 byte, khiến lần khởi động sau `load_job()` bị sập với lỗi `json.decoder.JSONDecodeError`.
- **Phương án khắc phục:** Ghi ra tệp tạm `.tmp` cùng thư mục, sau đó dùng `os.replace(temp_path, final_path)` để đảm bảo tính nguyên tử (Atomic Write) ở cấp độ hệ điều hành.

#### [P2-03] `AppConfig` Không Hỗ trợ Cấu hình Đường dẫn Tùy biến cho FFmpeg
- **Mô tả:** `app/core/config.py` không có trường `ffmpeg_path` hay đọc biến môi trường `FFMPEG_PATH`.
- **Bằng chứng:** Không có thuộc tính `ffmpeg_path` trong class `AppConfig`.
- **Tác động:** Trên Windows, người dùng thường không cài đặt FFmpeg vào thư mục hệ thống mà giải nén vào thư mục riêng. Nếu không có biến cấu hình, ứng dụng hoàn toàn bất lực trong việc tìm thấy FFmpeg nếu nó không nằm trong PATH toàn cục.
- **Phương án khắc phục:** Thêm `ffmpeg_path: Optional[str] = None` và `ffprobe_path: Optional[str] = None` vào `AppConfig`, nạp từ `os.getenv("FFMPEG_PATH")`.

#### [P2-04] `TaskManager.mark_completed` Không Kiểm tra Sự Tồn Tại Thực Tế của File Video
- **Mô tả:** Hàm `mark_completed` chấp nhận bất kỳ chuỗi đường dẫn nào và chuyển trạng thái sang `COMPLETED` mà không kiểm tra xem tệp có tồn tại trên đĩa hay có dung lượng $> 0$ hay không.
- **Bằng chứng:** Mã nguồn tại dòng 169–183 tệp `app/core/task_manager.py`.
- **Tác động:** Một tác vụ có thể được hệ thống báo "Thành công 100%" ngay cả khi video đầu ra bị lỗi không sinh ra được hoặc file 0 byte.
- **Phương án khắc phục:** Thêm điều kiện xác thực:
  ```python
  vid_path = Path(output_video_path)
  if not vid_path.exists() or vid_path.stat().st_size == 0:
      raise VideoCompositingError(f"Output video file does not exist or is empty: {output_video_path}", job_id=job_id)
  ```

#### [P2-05] Chưa có Điểm Khởi chạy Ứng dụng (Missing Entry Point)
- **Mô tả:** Dự án chưa có tệp `main.py`, `app/main.py` hoặc script CLI điều khiển trong `scripts/`.
- **Bằng chứng:** Thư mục gốc và thư mục `scripts/` không có tệp `.py` thực thi nào.
- **Tác động:** Lập trình viên hoặc người sử dụng không thể chạy thử pipeline từ dòng lệnh nếu không viết một đoạn mã Python tạm thời.
- **Phương án khắc phục:** Tạo `scripts/run_pipeline.py` cho phép nhập kịch bản mẫu và chạy thử pipeline trực tiếp trên terminal.

---

### MỨC ĐỘ P3 — MINOR (Cải thiện tài liệu và quản lý mã nguồn)

#### [P3-01] `README.md` Hoàn toàn Sai lệch So với Dự án Hiện tại
- **Mô tả:** [README.md](file:///c:/Users/phamtrong/Desktop/video agent/README.md) vẫn là hướng dẫn của template Google AI Studio Web (`npm install`, `npm run dev`).
- **Tác động:** Gây hiểu lầm nghiêm trọng cho bất kỳ ai clone hoặc đọc repository lần đầu.
- **Phương án khắc phục:** Viết lại `README.md` chuẩn: giới thiệu dự án, yêu cầu Python 3.10+, cách tạo `.venv`, cài đặt `requirements.txt`, thiết lập `.env` và chạy test `pytest`.

#### [P3-02] Kho Git Chưa Có Commit Đầu Tiên
- **Mô tả:** Đã chạy `git init` nhưng tất cả 14 tệp/thư mục đều đang ở trạng thái `Untracked`.
- **Phương án khắc phục:** Thực hiện `git add .` và tạo commit đầu tiên `feat: initialize project skeleton and phase 1-3 core contracts`.

---

## F. DANH SÁCH SAI LỆCH GIỮA TÀI LIỆU VÀ MÃ NGUỒN (SCHEMA & ARCHITECTURE DRIFT)

| Thành phần | Quy định trong `docs/04_data_contracts.md` | Triển khai thực tế trong `app/schemas/` | Nhận xét & Đánh giá mức độ |
| :--- | :--- | :--- | :--- |
| **Trạng thái nền vở** | `clean_notebook`, `ink_splattered`, `torn_dark_myth`, `heavenly_pressure` | `normal_page`, `cracked_page`, `dark_corrupted_page` (kèm alias) | Có sự phân nhánh danh pháp. Đã có validator bù trừ nhưng làm tăng độ phức tạp không cần thiết. |
| **Nhân vật người que**| Dùng `character_type` và `aura_color` trong `ActorSpec` | Dùng `skin` và `color` trong `ActorConfig` (kèm validator & property alias) | Mã nguồn Pydantic đã xử lý tốt tính tương thích ngược, nhưng tài liệu thiết kế chưa cập nhật. |
| **Sự kiện âm thanh** | Dùng `sfx_type` và `offset_sec` trong `SfxEvent` | Dùng `sfx_name` và `time_offset` trong `SFXEvent` (kèm validator & property alias) | Tương tự trên, cần thống nhất một nguồn sự thật duy nhất. |
| **Thông báo lỗi Job** | Dùng `error_detail` trong `JobRecord` | Dùng `error_message` trong `JobRecord` (kèm property alias `error_detail`) | Tương thích ngược hoạt động tốt trong test. |
| **Độ an toàn luồng TaskManager**| Báo cáo cũ ghi nhận có `threading.Lock` | Không có `threading.Lock` trong code | Sai lệch giữa báo cáo thẩm định và hiện trạng code thực tế. |

---

## G. PHẠM VI ĐÃ HOÀN THÀNH VÀ CHƯA HOÀN THÀNH

### 1. Những phần ĐÃ HOÀN THÀNH THỰC CHẤT (Verified & Tested)
- Cấu trúc thư mục dự án và tệp quản trị chuẩn mực (`AGENTS.md`, `PROJECT_STATUS.md`, `pytest.ini`, `.gitignore`).
- Tầng cấu hình tập trung (`AppConfig`), tự động nạp `.env` và tạo đủ cây thư mục.
- Tầng ghi log cấu trúc chuẩn công nghiệp (`JobLoggerAdapter` kết hợp `contextvars` gắn `[job=<id>]`).
- Tầng phân loại ngoại lệ nghiệp vụ (`AutoStudioError` hierarchy).
- Cỗ máy trạng thái tác vụ (`TaskManager`) kiểm soát chặt chẽ 7 trạng thái chuẩn.
- Toàn bộ Schema dữ liệu Pydantic v2 kiểm soát dữ liệu chặt chẽ và tương thích ngược.
- Bộ 4 Interface trừu tượng xác lập ranh giới giao tiếp rõ ràng giữa các tầng.
- Bộ điều phối `PipelineOrchestrator` thực thi đúng thứ tự **Audio-First Timing** và dọn dẹp thư mục tạm.
- Bộ kiểm thử tự động 20/20 test cases chạy ổn định, nhanh chóng trên Windows.

### 2. Những phần CHƯA HOÀN THÀNH / MỚI LÀ PLACEHOLDER HOẶC DỰ ĐỊNH
- **Script Parser:** Chưa tích hợp Gemini API hay bộ tách câu tiếng Việt offline (hiện dùng `StubScriptParser`).
- **Audio Engine:** Chưa tích hợp Edge TTS, chưa đo thời lượng thật bằng mutagen, chưa hòa âm ducking bằng pydub (hiện dùng `StubAudioEngine`).
- **Stickman Animation Engine:** Chưa có mã nguồn vẽ trang giấy kẻ ngang, chưa có khớp xương 2D FK/IK, chưa có hiệu ứng VFX/vệt chém (hiện dùng `StubAnimationEngine`).
- **Video Compositor:** Chưa có mã nguồn kết xuất video qua FFmpeg pipe (hiện dùng `StubVideoCompositor`).
- **Web UI & Telegram Bot:** Chưa được triển khai (thuộc Giai đoạn 8 & 9).
- **Executable FFmpeg:** Chưa được cài đặt trên máy chủ Windows.

---

## H. KẾ HOẠCH KHẮC PHỤC TINH GỌN (REMEDIATION PLAN)

Để dọn đường cho Giai đoạn 4 mà không gây xáo trộn kiến trúc, các hành động sau nên được thực hiện tuần tự:

1. **Bước 1 (Hạ tầng máy - Bắt buộc):**  
   Cài đặt `FFmpeg` trên máy Windows (qua winget hoặc tải thủ công và gán PATH). Kiểm tra lại bằng lệnh `ffmpeg -version` và `ffprobe -version` thành công.
2. **Bước 2 (Môi trường ảo - Bắt buộc):**  
   Cài đặt các gói phục vụ âm thanh của Giai đoạn 4 vào `.venv`:
   ```powershell
   .\.venv\Scripts\pip.exe install "edge-tts>=6.1.9" "pydub>=0.25.1" "audioop-lts>=0.2.1" "mutagen>=1.46.0"
   ```
3. **Bước 3 (Gia cố TaskManager & Config - Đề xuất nhanh):**  
   - Thêm `threading.Lock` vào `TaskManager`.
   - Cải tiến hàm `save_job` sử dụng cơ chế ghi an toàn (Atomic Write).
   - Bổ sung `ffmpeg_path` tùy biến vào `AppConfig`.
4. **Bước 4 (Dọn dẹp tài liệu):**  
   Cập nhật lại [README.md](file:///c:/Users/phamtrong/Desktop/video agent/README.md) theo đúng hướng dẫn chạy dự án Python trên Windows.

---

## I. QUYẾT ĐỊNH NGHIỆM THU CUỐI CÙNG

### **KẾT LUẬN: CONDITIONALLY APPROVED (PHÊ DUYỆT CÓ ĐIỀU KIỆN)**

**Lý do:**
1. Khung kiến trúc, giao diện trừu tượng, hợp đồng dữ liệu và bộ kiểm thử nền tảng của Giai đoạn 1–3 **đã hoàn thành vững chắc và đạt chuẩn kỹ thuật cao**.
2. Dự án **đủ điều kiện bắt đầu Giai đoạn 4 (Vietnamese TTS & Audio Timing Engine)** vì Giai đoạn 4 chỉ tập trung vào việc tạo giọng nói tiếng Việt và đo thời lượng, hoàn toàn độc lập với bộ dựng hình ảnh que (Giai đoạn 5) và bộ dựng video FFmpeg (Giai đoạn 7).
3. **Điều kiện ràng buộc (Prerequisites for Phase 4 Execution):**
   - Phải cài đặt các gói âm thanh (`edge-tts`, `pydub`, `audioop-lts`, `mutagen`) vào `.venv`.
   - Phải cấu hình hoặc cài đặt thành công `ffmpeg` trên máy Windows để `pydub` có thể giải mã và chuyển đổi âm thanh khi cần thiết.
