# BÁO CÁO NGHIỆM THU KỸ THUẬT GIAI ĐOẠN 4.1 – SCRIPT PARSER ENGINE
**Dự án:** Dark Myth Stickman Auto-Studio  
**Phạm vi:** Giai đoạn 4.1 – Bộ Phân Tích Kịch Bản Tiếng Việt (Script Parser Engine)  
**Ngày lập:** 2026-10-31  
**Môi trường kiểm định:** Windows 11, Python 3.15.2 (`.venv`), Git master  
**Tiêu chuẩn chất lượng:** Evidence-First Verification (Bằng chứng terminal thực tế 100%)  

---

## 1. DANH SÁCH FILE ĐÃ TẠO VÀ CHỈNH SỬA

| STT | Đường Dẫn Tệp | Loại Hành Động | Vai Trò & Trách Nhiệm Kỹ Thuật |
| :-: | :--- | :---: | :--- |
| 1 | `app/modules/parser/rule_based.py` | Tạo mới | Bộ phân tích kịch bản tiếng Việt bằng luật (Rule-Based NLP), hoạt động ngoại tuyến 100%, không cần API key. |
| 2 | `app/modules/parser/gemini_parser.py` | Tạo mới | Bộ phân tích kịch bản bằng mô hình ngôn ngữ lớn qua SDK `google-genai` (Gemini Flash), cấu trúc JSON nghiêm ngặt. |
| 3 | `app/modules/parser/hybrid_parser.py` | Tạo mới | Bộ điều phối lai (Hybrid Orchestrator), ưu tiên gọi Gemini khi có `GEMINI_API_KEY` và tự động chuyển về Rule-Based khi lỗi/mất mạng. |
| 4 | `app/modules/parser/__init__.py` | Cập nhật | Xuất bản `RuleBasedScriptParser`, `GeminiScriptParser`, `HybridScriptParser` và giữ tương thích ngược `StubScriptParser`. |
| 5 | `tests/test_script_parser.py` | Tạo mới | Bộ 18 bài kiểm thử tự động chuyên sâu cho Stage 4.1 (Rule-based, Gemini mocks, Hybrid fallback, Pydantic validation). |
| 6 | `scripts/run_script_parser_sample.py` | Tạo mới | Script chạy kiểm thử tích hợp thực tế trên kịch bản trận chiến mẫu Hắc Ám Tây Du, xuất JSON phân cảnh. |
| 7 | `out/sample_parsed_scenes.json` | Sinh ra tự động | Tệp hiện vật JSON chứa 4 đối tượng `SceneSchema` hoàn chỉnh được sinh từ kịch bản mẫu qua parser thực tế. |

---

## 2. KIẾN TRÚC PARSER ĐÃ TRIỂN KHAI

Kiến trúc tuân thủ nghiêm ngặt giao diện chuẩn [`IScriptParser`](file:///c:/Users/phamtrong/Desktop/video%20agent/app/interfaces/base_parser.py) và hỗ trợ Dependency Injection:

```text
                                [ ScriptInput (Văn bản kịch bản tiếng Việt) ]
                                                     │
                                                     ▼
                                      ┌───────────────────────────────┐
                                      │      HybridScriptParser       │
                                      └──────────────┬────────────────┘
                                                     │
                             ┌───────────────────────┴───────────────────────┐
                             │ Có GEMINI_API_KEY?                            │ Không có API Key
                             ▼                                               ▼
              ┌──────────────────────────────┐                ┌──────────────────────────────┐
              │      GeminiScriptParser      │                │    RuleBasedScriptParser     │
              │   (SDK: google-genai 2.34)   │                │   (100% Offline Rule-Based)  │
              └──────────────┬───────────────┘                └──────────────┬───────────────┘
                             │                                               │
                             ├─ Thành công ──────────┐                       │
                             │                       │                       │
                             └─ Thất bại / Timeout ──┼───────────────────────►
                                (Graceful Fallback)  │
                                                     ▼
                                      [ list[SceneSchema] Chuẩn Hóa ]
                                      - scene_id: 1..N tuần tự
                                      - narration_text: sạch, giữ nguyên dấu
                                      - audio_duration_sec: 0.0 (chưa qua TTS)
                                      - voice_audio_path: None
                                      - actors: Enums chuẩn Dark Myth
                                      - action_preset: 8 chiêu thức
                                      - background_state: 4 trạng thái
                                      - camera_movement: 6 góc máy
                                      - sfx_events: offset & volume chuẩn
```

---

## 3. MÔ TẢ CHI TIẾT RULE-BASED VÀ GEMINI PARSER

### 3.1. RuleBasedScriptParser (Hoạt động ngoại tuyến 100%)
- **Cơ chế Phân tách Cảnh (Dual Segmentation Strategy):**
  - *Nhánh A (Có tiêu đề):* Nhận diện các tiêu đề phân cảnh tiếng Việt như `Cảnh 1:`, `Phân cảnh 2:`, `Đoạn 3:`, `Scene 4:`. Tự động tách đoạn nội dung tương ứng và loại bỏ phần tiền tố để câu dẫn truyện (`narration_text`) sạch sẽ cho bước tạo TTS.
  - *Nhánh B (Không có tiêu đề):* Phân rã văn bản theo đoạn văn (`\n\n`) và ranh giới kết thúc câu (`.`, `!`, `?`, `…`). Gom nhóm các câu hoàn chỉnh thành từng phân cảnh có độ dài từ **12 đến 35 từ tiếng Việt**. **Tuyệt đối không chia vụn câu văn** đang diễn đạt một hành động liền mạch.
- **Nhận diện Thực thể Nhân vật (`CharacterSkin`):**
  - Đối chiếu từ điển từ khóa tiếng Việt:
    - `"ngộ không"`, `"hầu vương"`, `"thiết bảng"`, `"kim cô"` $\rightarrow$ `dark_wukong` (`weapon="ruyi_staff"`, `color="#D92626"`, `side="left"`).
    - `"nhị lang"`, `"dương tiễn"`, `"tam tiêm đảo"`, `"thiên nhãn"` $\rightarrow$ `erlang_shen` (`weapon="three_pointed_spear"`, `color="#E6B800"`, `side="right"`).
    - `"thiên tướng"`, `"cự linh thần"` $\rightarrow$ `celestial_general` (`weapon="celestial_halberd"`, `color="#63B3ED"`).
    - `"thiên binh"`, `"vạn binh"`, `"quân đoàn"` $\rightarrow$ `celestial_soldier_squad` (`weapon="celestial_halberd"`, `color="#2D3748"`).
    - `"bàn tay phật"`, `"như lai"`, `"phật tổ"` $\rightarrow$ `buddha_palm` (`weapon="giant_golden_palm"`, `scale=3.5`, `side="top"`).
  - *Mặc định an toàn:* Nếu kịch bản không nhắc đến nhân vật nào, parser sử dụng `dark_wukong` làm nhân vật chính mặc định.
- **Nhận diện Chiêu thức & Hành động (`ActionPreset`):**
  - Nhận diện 8 chiêu thức chiến đấu chuẩn: `dark_aura_standoff`, `heavy_charge_clash`, `flurry_combo`, `staff_vortex_sweep`, `sky_leap_slam`, `divine_eye_beam`, `giant_palm_suppression`, `knockback_recovery`.
  - Phân biệt từ khóa gần giống để tránh nhận nhầm (ví dụ: *"bổ thẳng đứng gậy"* $\rightarrow$ `sky_leap_slam` chứ không nhầm sang `heavy_charge_clash`; *"xoay gậy"* $\rightarrow$ `staff_vortex_sweep` chứ không nhầm sang `flurry_combo`).
- **Nhận diện Nền giấy, Góc máy và SFX:**
  - Nền giấy: Tự động phát hiện `clean_notebook`, `ink_splattered`, `torn_dark_myth`, `heavenly_pressure`.
  - Góc máy: Tự động đồng bộ với tính chất chiêu thức (ví dụ: đè bàn tay $\rightarrow$ `pan_vertical_up`, bổ gậy từ trời $\rightarrow$ `pan_vertical_down`, va chạm $\rightarrow$ `zoom_punch_impact`).
  - SFX Events: Tự động gán các sự kiện âm thanh chuẩn (`metal_weapon_clash`, `whoosh_heavy`, `staff_whoosh_fast`, `earth_shatter_slam`, `giant_palm_boom`...).
- **Toàn vẹn Dữ liệu:**
  - `audio_duration_sec = 0.0` (tuyệt đối không bịa số đo thời lượng trước khi có Audio Engine).
  - `voice_audio_path = None`.

### 3.2. GeminiScriptParser (Phân tích thông minh qua LLM)
- **SDK chính thức:** Sử dụng `google-genai` (phiên bản `2.34.0`).
- **Mô hình mục tiêu:** `gemini-2.5-flash` với cấu hình `temperature=0.2` và `response_mime_type="application/json"`.
- **System Instruction Nghiêm ngặt:** Chỉ thị rõ ràng danh mục Enum hợp lệ, cấm bịa Enum ngoài schema, yêu cầu trả về mảng JSON thuần túy.
- **Thẩm định Pydantic hai lớp:** Toàn bộ đối tượng trả về từ Gemini đều phải đi qua `SceneSchema.model_validate()`. Nếu AI trả về Enum lạ hoặc sai kiểu, Pydantic lập tức phát hiện và kích hoạt nhánh ngoại lệ.

### 3.3. HybridScriptParser (Cơ chế Điều phối & Chịu lỗi)
- Kiểm tra sự tồn tại của `GEMINI_API_KEY`.
- Nếu có key: Thử gọi `GeminiScriptParser`. Nếu thành công, trả về kết quả AI.
- Nếu gặp bất kỳ sự cố nào (API key không hợp lệ, timeout, quota 429, JSON sai cú pháp, mất mạng): Ghi log mức `WARNING` và **tự động chuyển ngay sang `RuleBasedScriptParser`** mà không làm sập pipeline.

---

## 4. KẾT QUẢ KIỂM THỬ CHI TIẾT (PYTEST TEST SUITE)

Lệnh thực thi trên Terminal:
```powershell
.\.venv\Scripts\pytest.exe -v
```

Kết quả thực tế từ Terminal:
```text
============================= test session starts =============================
platform win32 -- Python 3.15.2, pytest-9.2.0, pluggy-1.7.0 -- C:\Users\phamtrong\Desktop\video agent\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\phamtrong\Desktop\video agent
configfile: pytest.ini
plugins: anyio-4.15.1, asyncio-1.4.1
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting ... collected 38 items

tests/test_config_and_logger.py::test_package_imports_cleanly PASSED     [  2%]
tests/test_config_and_logger.py::test_config_creates_required_directories_and_safe_defaults PASSED [  5%]
tests/test_config_and_logger.py::test_config_loads_custom_env_file PASSED [  7%]
tests/test_config_and_logger.py::test_logger_writes_structured_output_with_job_id PASSED [ 10%]
tests/test_config_and_logger.py::test_layered_exceptions_format_job_id_and_stage PASSED [ 13%]
tests/test_pipeline_skeleton.py::test_pipeline_orchestrator_end_to_end_with_stubs PASSED [ 15%]
tests/test_pipeline_skeleton.py::test_pipeline_orchestrator_catches_module_failure_and_marks_job_failed PASSED [ 18%]
tests/test_schemas.py::test_valid_scene_schema_and_contract_compatibility PASSED [ 21%]
tests/test_schemas.py::test_scene_schema_rejects_invalid_data[invalid_payload0-scene_id must be > 0] PASSED [ 23%]
tests/test_schemas.py::test_scene_schema_rejects_invalid_data[invalid_payload1-narration_text cannot be blank] PASSED [ 26%]
tests/test_schemas.py::test_scene_schema_rejects_invalid_data[invalid_payload2-audio_duration_sec cannot be negative] PASSED [ 28%]
tests/test_schemas.py::test_scene_schema_rejects_invalid_data[invalid_payload3-invalid action_preset enum] PASSED [ 31%]
tests/test_schemas.py::test_scene_schema_rejects_invalid_data[invalid_payload4-invalid background_state enum] PASSED [ 34%]
tests/test_schemas.py::test_scene_schema_rejects_invalid_data[invalid_payload5-sfx time_offset cannot be negative] PASSED [ 36%]
tests/test_schemas.py::test_script_input_validation PASSED               [ 39%]
tests/test_schemas.py::test_job_record_and_render_result_validation PASSED [ 42%]
tests/test_script_parser.py::test_parser_with_explicit_scene_headings PASSED [ 44%]
tests/test_script_parser.py::test_parser_without_scene_headings PASSED   [ 47%]
tests/test_script_parser.py::test_parser_vietnamese_diacritics_integrity PASSED [ 50%]
tests/test_script_parser.py::test_parser_multi_paragraph_and_multi_sentence PASSED [ 52%]
tests/test_script_parser.py::test_parser_recognizes_multiple_characters PASSED [ 55%]
tests/test_script_parser.py::test_parser_recognizes_distinct_action_presets PASSED [ 57%]
tests/test_script_parser.py::test_parser_distinguishes_similar_keywords PASSED [ 60%]
tests/test_script_parser.py::test_parser_rejects_empty_or_too_short_script PASSED [ 63%]
tests/test_script_parser.py::test_parser_handles_length_boundary PASSED  [ 65%]
tests/test_script_parser.py::test_parser_preserves_text_and_no_hallucinated_duration PASSED [ 68%]
tests/test_script_parser.py::test_gemini_parser_missing_api_key_raises_configuration_error PASSED [ 71%]
tests/test_script_parser.py::test_gemini_parser_valid_structured_json PASSED [ 73%]
tests/test_script_parser.py::test_gemini_parser_handles_malformed_json PASSED [ 76%]
tests/test_script_parser.py::test_gemini_parser_handles_timeout PASSED   [ 78%]
tests/test_script_parser.py::test_gemini_parser_handles_quota_exceeded PASSED [ 81%]
tests/test_script_parser.py::test_gemini_parser_rejects_invalid_enum PASSED [ 84%]
tests/test_script_parser.py::test_hybrid_parser_falls_back_when_no_api_key PASSED [ 86%]
tests/test_script_parser.py::test_hybrid_parser_falls_back_when_gemini_fails PASSED [ 89%]
tests/test_task_manager.py::test_task_manager_create_and_persist_job PASSED [ 92%]
tests/test_task_manager.py::test_task_manager_full_happy_path_transitions PASSED [ 94%]
tests/test_task_manager.py::test_task_manager_blocks_illegal_state_jump PASSED [ 97%]
tests/test_task_manager.py::test_task_manager_handles_job_failure_cleanly PASSED [100%]

============================= 38 passed in 0.25s ==============================
```

---

## 5. KẾT QUẢ PHÂN TÍCH KỊCH BẢN MẪU (INTEGRATION VERIFICATION)

Lệnh thực thi:
```powershell
.\.venv\Scripts\python.exe scripts\run_script_parser_sample.py
```

Đầu ra Terminal:
```text
==================================================
STAGE 4.1 SCRIPT PARSER INTEGRATION VERIFICATION
==================================================
Target Title: Ngộ Không Hắc Hóa Đại Chiến Nhị Lang Thần & Thiên Đình
Script Length: 453 characters
--------------------------------------------------
STEP 1: Executing RuleBasedScriptParser...
2026-10-31 17:01:22 | INFO    | autostudio.rule_based_parser | [job=job_20261031_806a80] | RuleBasedScriptParser successfully parsed 4 scenes.
  -> Generated 4 scenes.
STEP 2: Validating SceneSchema contracts...
  [Scene 1]
    Narration : Giữa trang giấy nhuốm mực đen u ám, Tôn Ngộ Không mắt đỏ rực...
    Action    : dark_aura_standoff
    Background: ink_splattered
    Camera    : zoom_in_dramatic
    Actors    : ['dark_wukong (ruyi_staff)', 'erlang_shen (three_pointed_spear)']
    SFX Events: ['dark_aura_hum']
  [Scene 2]
    Narration : Nhị Lang Thần thét lớn, lao vút tới bổ mạnh Tam Tiêm Đảo xuố...
    Action    : heavy_charge_clash
    Background: ink_splattered
    Camera    : zoom_punch_impact
    Actors    : ['dark_wukong (ruyi_staff)', 'erlang_shen (three_pointed_spear)']
    SFX Events: ['whoosh_heavy', 'metal_weapon_clash']
  [Scene 3]
    Narration : Hàng vạn thiên binh ùa xuống nhưng bị Ngộ Không xoay gậy tạo...
    Action    : staff_vortex_sweep
    Background: clean_notebook
    Camera    : static_wide
    Actors    : ['dark_wukong (ruyi_staff)', 'celestial_soldier_squad (celestial_halberd)']
    SFX Events: ['vortex_spin_whoosh', 'body_impact_sweep']
  [Scene 4]
    Narration : Từ đỉnh trang giấy, Bàn tay Phật Tổ khổng lồ giáng xuống trấ...
    Action    : giant_palm_suppression
    Background: heavenly_pressure
    Camera    : pan_vertical_up
    Actors    : ['buddha_palm (giant_golden_palm)']
    SFX Events: ['heavenly_thunder_rumble', 'giant_palm_boom']
STEP 3: Serialized JSON successfully exported to: C:\Users\phamtrong\Desktop\video agent\out\sample_parsed_scenes.json
  File size: 4467 bytes
STEP 4: Checking Live Gemini API Integration...
  Notice: GEMINI_API_KEY is not configured in environment.
  -> Live Gemini Integration Status: NOT VERIFIED (Waiting for user API key)
  -> All unit tests for Gemini error handling & Hybrid fallback have PASSED with mocks.
==================================================
INTEGRATION VERIFICATION FINISHED SUCCESSFULLY.
==================================================
```

---

## 6. HIỆN VẬT JSON SCENESCHEMA ĐẦU RA THỰC TẾ

Tệp hiện vật được xuất bản tại [`out/sample_parsed_scenes.json`](file:///c:/Users/phamtrong/Desktop/video%20agent/out/sample_parsed_scenes.json):

```json
[
  {
    "scene_id": 1,
    "narration_text": "Giữa trang giấy nhuốm mực đen u ám, Tôn Ngộ Không mắt đỏ rực chống Thiết Bảng Như Ý đứng đối diện Nhị Lang Thần.",
    "audio_duration_sec": 0.0,
    "voice_audio_path": null,
    "background_state": "ink_splattered",
    "actors": [
      {
        "actor_id": "dark_wukong_1",
        "skin": "dark_wukong",
        "color": "#D92626",
        "weapon": "ruyi_staff",
        "display_name": "Ngộ Không Hắc Hóa",
        "side": "left",
        "scale": 1.0
      },
      {
        "actor_id": "erlang_shen_1",
        "skin": "erlang_shen",
        "color": "#E6B800",
        "weapon": "three_pointed_spear",
        "display_name": "Nhị Lang Thần",
        "side": "right",
        "scale": 1.05
      }
    ],
    "action_preset": "dark_aura_standoff",
    "camera_movement": "zoom_in_dramatic",
    "camera_config": null,
    "sfx_events": [
      {
        "sfx_name": "dark_aura_hum",
        "time_offset": 0.3,
        "volume": 0.75
      }
    ]
  },
  {
    "scene_id": 2,
    "narration_text": "Nhị Lang Thần thét lớn, lao vút tới bổ mạnh Tam Tiêm Đảo xuống nhưng Ngộ Không vung gậy sắt đỡ đòn làm tóe lửa khắp mặt giấy!",
    "audio_duration_sec": 0.0,
    "voice_audio_path": null,
    "background_state": "ink_splattered",
    "actors": [
      {
        "actor_id": "dark_wukong_2",
        "skin": "dark_wukong",
        "color": "#D92626",
        "weapon": "ruyi_staff",
        "display_name": "Ngộ Không Hắc Hóa",
        "side": "left",
        "scale": 1.0
      },
      {
        "actor_id": "erlang_shen_2",
        "skin": "erlang_shen",
        "color": "#E6B800",
        "weapon": "three_pointed_spear",
        "display_name": "Nhị Lang Thần",
        "side": "right",
        "scale": 1.05
      }
    ],
    "action_preset": "heavy_charge_clash",
    "camera_movement": "zoom_punch_impact",
    "camera_config": null,
    "sfx_events": [
      {
        "sfx_name": "whoosh_heavy",
        "time_offset": 0.2,
        "volume": 0.85
      },
      {
        "sfx_name": "metal_weapon_clash",
        "time_offset": 0.5,
        "volume": 0.95
      }
    ]
  },
  {
    "scene_id": 3,
    "narration_text": "Hàng vạn thiên binh ùa xuống nhưng bị Ngộ Không xoay gậy tạo cơn lốc quét sạch đánh văng tứ phía!",
    "audio_duration_sec": 0.0,
    "voice_audio_path": null,
    "background_state": "clean_notebook",
    "actors": [
      {
        "actor_id": "dark_wukong_3",
        "skin": "dark_wukong",
        "color": "#D92626",
        "weapon": "ruyi_staff",
        "display_name": "Ngộ Không Hắc Hóa",
        "side": "left",
        "scale": 1.0
      },
      {
        "actor_id": "celestial_soldier_squad_3",
        "skin": "celestial_soldier_squad",
        "color": "#2D3748",
        "weapon": "celestial_halberd",
        "display_name": "Thiên Binh",
        "side": "right",
        "scale": 0.95
      }
    ],
    "action_preset": "staff_vortex_sweep",
    "camera_movement": "static_wide",
    "camera_config": null,
    "sfx_events": [
      {
        "sfx_name": "vortex_spin_whoosh",
        "time_offset": 0.3,
        "volume": 0.9
      },
      {
        "sfx_name": "body_impact_sweep",
        "time_offset": 0.7,
        "volume": 0.85
      }
    ]
  },
  {
    "scene_id": 4,
    "narration_text": "Từ đỉnh trang giấy, Bàn tay Phật Tổ khổng lồ giáng xuống trấn áp cả bầu trời hắc ám!",
    "audio_duration_sec": 0.0,
    "voice_audio_path": null,
    "background_state": "heavenly_pressure",
    "actors": [
      {
        "actor_id": "buddha_palm_4",
        "skin": "buddha_palm",
        "color": "#F6AD55",
        "weapon": "giant_golden_palm",
        "display_name": "Bàn Tay Phật Tổ",
        "side": "top",
        "scale": 3.5
      }
    ],
    "action_preset": "giant_palm_suppression",
    "camera_movement": "pan_vertical_up",
    "camera_config": null,
    "sfx_events": [
      {
        "sfx_name": "heavenly_thunder_rumble",
        "time_offset": 0.2,
        "volume": 0.9
      },
      {
        "sfx_name": "giant_palm_boom",
        "time_offset": 0.7,
        "volume": 1.0
      }
    ]
  }
]
```

---

## 7. DANH SÁCH LỖI VÀ GIỚI HẠN CÒN TỒN TẠI

1. **Giới hạn nhận diện ngữ nghĩa Rule-Based:** Bộ parser theo luật dựa trên từ khóa tiếng Việt Hắc Ám Tây Du. Nếu người dùng nhập kịch bản hoàn toàn không liên quan đến Tây Du Ký (ví dụ: thế giới hiện đại, người máy), parser sẽ áp dụng nhân vật mặc định (`dark_wukong`) và hành động mặc định (`dark_aura_standoff`). Đây là hành vi an toàn theo thiết kế.
2. **Ước lượng thời lượng chưa thực hiện:** Trường `audio_duration_sec` trong các phân cảnh xuất ra từ Parser luôn bằng `0.0` theo đúng hợp đồng. Thời lượng thực tế sẽ do `IAudioEngine` đo lường bằng `Mutagen` tại Giai đoạn 4.2.

---

## 8. NHỮNG BÀI TEST CHỈ DÙNG MOCK

Các bài test sau trong `tests/test_script_parser.py` sử dụng `unittest.mock` để kiểm thử logic xử lý ngoại lệ mà không tiêu tốn quota hoặc phụ thuộc mạng:
- `test_gemini_parser_valid_structured_json`: Mock kết quả JSON từ `genai.Client.models.generate_content`.
- `test_gemini_parser_handles_malformed_json`: Mock phản hồi JSON cú pháp vỡ để kiểm tra việc bắt lỗi `ScriptParseError`.
- `test_gemini_parser_handles_timeout`: Mock lỗi `TimeoutError` để kiểm tra bắt lỗi và ghi log.
- `test_gemini_parser_handles_quota_exceeded`: Mock mã lỗi `429 ResourceExhausted` từ Google Cloud.
- `test_gemini_parser_rejects_invalid_enum`: Mock AI trả về Enum lạ để kiểm tra cơ chế chặn của Pydantic.
- `test_hybrid_parser_falls_back_when_gemini_fails`: Mock lỗi từ Gemini để kiểm tra cơ chế tự động chuyển sang Rule-Based.

---

## 9. CÁC CHỨC NĂNG CHƯA ĐƯỢC XÁC MINH (NOT VERIFIED)

- **Gọi API Gemini Trực Tiếp Trên Mạng Thật (Live Gemini Network Call):** Ghi nhận trạng thái **NOT VERIFIED**.  
  *Nguyên nhân:* Biến môi trường `GEMINI_API_KEY` hiện chưa được cấu hình trong file `.env` cục bộ của người dùng. Hệ thống đã chuẩn bị sẵn sàng 100% mã nguồn SDK `google-genai` và sẽ tự động kích hoạt ngay khi người dùng điền key.

---

## 10. BẢNG QUYẾT ĐỊNH NGHIỆM THU (ACCEPTANCE MATRIX)

| STT | Tiêu Chí Nghiệm Thu Giai Đoạn 4.1 | Kết Quả Thực Tế | Đánh Giá |
| :-: | :--- | :--- | :---: |
| 1 | Phân tích kịch bản có tiêu đề (Cảnh 1, 2, 3...) | Tách chuẩn 4 cảnh, loại bỏ tiền tố thừa, scene_id tuần tự 1..4 | **PASS** |
| 2 | Phân tích kịch bản không có tiêu đề | Tách theo đoạn văn và câu hoàn chỉnh, không chia vụn hành động | **PASS** |
| 3 | Bảo tồn tiếng Việt có dấu 100% | Giữ nguyên dấu Unicode không méo dạng | **PASS** |
| 4 | Nhận diện 5 nhân vật chuẩn Dark Myth | Đã nhận diện đúng `dark_wukong`, `erlang_shen`, `celestial_general`, `celestial_soldier_squad`, `buddha_palm` | **PASS** |
| 5 | Nhận diện 8 chiêu thức `ActionPreset` | Khớp đúng 8 chiêu thức, có bộ lọc từ khóa chống nhầm lẫn | **PASS** |
| 6 | Nhận diện nền giấy, góc máy và sự kiện SFX | Đồng bộ hóa tự động với hành động của cảnh | **PASS** |
| 7 | Chặn kịch bản rỗng hoặc ngoài giới hạn | Bắt lỗi `ValidationError` & `ScriptParseError` chuẩn | **PASS** |
| 8 | Tuân thủ Hợp đồng dữ liệu `SceneSchema` | Pydantic validate thành công 100%, không bịa Enum ngoài schema | **PASS** |
| 9 | Giữ nguyên `audio_duration_sec == 0.0` | Không sinh thời lượng giả trước Audio Engine | **PASS** |
| 10 | Gemini Parser xử lý lỗi & Timeout | Đã kiểm thử qua 5 bài test Mock, không làm sập pipeline | **PASS** |
| 11 | Hybrid Fallback tự động | Tự chuyển về Rule-Based khi không có key hoặc khi AI lỗi | **PASS** |
| 12 | Bộ kiểm thử tự động toàn diện | `pytest` đạt **38/38 passed (0 failed)** trong `0.25s` | **PASS** |
| 13 | Kiểm thử tích hợp kịch bản mẫu | Đã chạy thực tế và xuất tệp `out/sample_parsed_scenes.json` | **PASS** |

---

> [!IMPORTANT]
> **KỶ LUẬT GIAI ĐOẠN:** Tôi đã hoàn thành toàn diện Giai đoạn 4.1 (Script Parser Engine), không triển khai TTS Engine, không tạo file audio giả, và đạt 38/38 test tự động. Tôi **DỪNG LẠI HOÀN TOÀN TẠI ĐÂY** để chờ người dùng nghiệm thu trước khi chuyển sang triển khai TTS Engine ở Giai đoạn 4.2.
