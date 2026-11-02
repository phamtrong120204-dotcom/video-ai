# TÀI LIỆU HỢP ĐỒNG DỮ LIỆU & GIAO TIẾP LIÊN MODULE (DATA CONTRACTS)
**Dự án:** Dark Myth Stickman Auto-Studio  
**Phiên bản:** 1.0.0 (Giai đoạn 1 — Project Foundation)  
**Vai trò thiết kế:** Principal Software Architect  

> **QUY TẮC BẮT BUỘC:** Đây là "Bản Hiến Pháp Dữ Liệu" (Single Source of Truth) giữa toàn bộ các tầng trong hệ thống (Web UI, Telegram Bot, Task Orchestrator, Script Parser, Audio Engine, Stickman Animation Engine, Video Compositor). Mọi module viết ở các giai đoạn sau **bắt buộc** phải tuân thủ chính xác tên trường, kiểu dữ liệu và giá trị Enum được định nghĩa trong tài liệu này.

---

## 1. Định Dạng Kịch Bản Đầu Vào (`ScriptInput`)

Đối tượng truyền từ Tầng Giao Tiếp (Web App hoặc Telegram Bot) xuống Tầng Điều Phối Tác Vụ khi người dùng yêu cầu tạo video mới.

### 1.1. Bảng đặc tả trường dữ liệu (`ScriptInput`)

| Tên trường | Kiểu dữ liệu | Bắt buộc | Mặc định | Mô tả chi tiết |
| :--- | :--- | :---: | :--- | :--- |
| `job_id` | `string` | Có | Tự sinh | Mã định danh duy nhất của tác vụ (VD: `"job_20261031_a8f9"`). |
| `source_channel` | `enum` | Có | `"web_ui"` | Kênh gửi yêu cầu: `"web_ui"` \| `"telegram_bot"` \| `"cli_test"`. |
| `title` | `string` | Không | `"Hắc Ám Tây Du Ký Sự"` | Tiêu đề kịch bản hiển thị ở cảnh mở đầu và quản lý lịch sử. |
| `raw_script_text` | `string` | Có | - | Toàn bộ văn bản kịch bản tiếng Việt do người dùng nhập vào (tối thiểu 10 ký tự, tối đa 6000 ký tự). |
| `voice_id` | `string` | Không | `"vi-VN-NamMinhNeural"` | Mã giọng đọc tiếng Việt (`"vi-VN-NamMinhNeural"` hoặc `"vi-VN-HoaiMyNeural"`). |
| `voice_speed` | `number` | Không | `1.05` | Tốc độ đọc thuyết minh (`0.8` đến `1.3`). |
| `target_duration_sec` | `object` | Không | `{"min": 60, "max": 180}` | Khoảng thời lượng mục tiêu (tính bằng giây). |
| `render_config` | `object` | Không | Xem mẫu JSON | Cấu hình kết xuất hình ảnh (`width`: 1080, `height`: 1920, `fps`: 30, `burn_subtitles`: true, `bgm_theme`: `"dark_myth_orchestral"`). |
| `telegram_meta` | `object \| null` | Không | `null` | Thông tin `chat_id` và `message_id` nếu yêu cầu đến từ Telegram Bot để gửi trả video. |
| `created_at` | `string (ISO 8601)` | Có | Tự sinh | Thời điểm khởi tạo yêu cầu. |

### 1.2. Mẫu JSON chuẩn (`ScriptInput`)

```json
{
  "job_id": "job_20261031_89ab",
  "source_channel": "web_ui",
  "title": "Ngộ Không Hắc Hóa Đại Chiến Nhị Lang Thần",
  "raw_script_text": "Cảnh 1: Giữa trang giấy vở nhuốm mực đen, Tôn Ngộ Không mắt đỏ rực nắm chặt Thiết Bảng Như Ý đứng đối diện Nhị Lang Thần Dương Tiễn.\nCảnh 2: Nhị Lang Thần thét lớn, lao vút tới bổ mạnh Tam Tiêm Đảo xuống nhưng Ngộ Không vung gậy sắt đỡ đòn làm tóe lửa khắp mặt giấy.\nCảnh 3: Từ đỉnh trang giấy, Bàn tay Phật Tổ khổng lồ bất ngờ giáng xuống trấn áp cả bầu trời hắc ám!",
  "voice_id": "vi-VN-NamMinhNeural",
  "voice_speed": 1.05,
  "target_duration_sec": {
    "min": 60,
    "max": 180
  },
  "render_config": {
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "burn_subtitles": true,
    "bgm_theme": "dark_myth_orchestral"
  },
  "telegram_meta": null,
  "created_at": "2026-10-31T07:00:00.000Z"
}
```

---

## 2. Định Dạng Dữ Liệu Phân Cảnh (`SceneSchema`)

Đối tượng cốt lõi truyền từ **Script Parser** $\rightarrow$ **TTS Engine** (cập nhật `audio_duration_sec` và `voice_audio_path`) $\rightarrow$ **Stickman Animation Engine** (dựng hình và cập nhật `sfx_events`).

### 2.1. Các tập giá trị Enum chuẩn trong `SceneSchema`

- **`background_state` (Trạng thái nền giấy vở kẻ ngang):**
  - `"clean_notebook"`: Trang giấy vở học sinh nguyên vẹn, kẻ ngang xanh, lề đỏ.
  - `"ink_splattered"`: Trang giấy có các vệt mực đen/đỏ văng tung tóe do giao chiến.
  - `"torn_dark_myth"`: Trang giấy sẫm màu hắc ám, có vết nứt rách và tàn tro bay.
  - `"heavenly_pressure"`: Trang giấy ánh vàng uy nghiêm từ đỉnh đổ xuống (khi Thiên đình / Phật Tổ xuất hiện).
- **`character_type` (Loại nhân vật người que trong `actors`):**
  - `"dark_wukong"`: Tôn Ngộ Không Hắc Hóa (cầm Thiết Bảng Như Ý, mắt đỏ, khăn choàng rách).
  - `"erlang_shen"`: Nhị Lang Thần Dương Tiễn (cầm Tam Tiêm Đảo, Thiên Nhãn phát sáng).
  - `"celestial_general"`: Thiên Tướng / Cự Linh Thần (thân hình lớn, cầm búa/kích).
  - `"celestial_soldier_squad"`: Toán Thiên Binh cầm giáo dài.
  - `"buddha_palm"`: Bàn Tay Phật Tổ khổng lồ giáng từ đỉnh màn hình xuống.
- **`action_preset` (Kịch bản động tác chiến đấu của cảnh):**
  - `"dark_aura_standoff"`: Hai bên đứng đối diện tích tụ hắc khí / thần quang, khăn choàng bay.
  - `"heavy_charge_clash"`: Hai nhân vật lao vút vào nhau và va chạm vũ khí cực mạnh ở giữa màn hình.
  - `"flurry_combo"`: Liên hoàn đòn đánh tốc độ cao kèm tàn ảnh (afterimages) và tia lửa liên tục.
  - `"staff_vortex_sweep"`: Ngộ Không xoay tròn Thiết Bảng quét bay đám thiên binh.
  - `"sky_leap_slam"`: Nhảy vọt lên nửa trên trang giấy rồi bổ vũ khí chấn động mặt đất.
  - `"divine_eye_beam"`: Nhị Lang Thần phóng tia sáng từ Thiên Nhãn, đối phương vung gậy chắn.
  - `"giant_palm_suppression"`: Bàn tay Phật khổng lồ từ trên đỉnh khung hình 9:16 đè xuống, nhân vật bên dưới chống trả.
  - `"knockback_recovery"`: Nhân vật bị đánh văng trượt dài trên dòng kẻ giấy rồi cắm vũ khí phanh lại.
- **`camera_movement` (Chuyển động máy quay ảo 2D):**
  - `"static_wide"` | `"zoom_in_dramatic"` | `"zoom_punch_impact"` | `"pan_vertical_down"` | `"pan_vertical_up"` | `"shake_heavy"`

### 2.2. Bảng đặc tả trường dữ liệu (`SceneSchema`)

| Tên trường | Kiểu dữ liệu | Bắt buộc | Mô tả chi tiết |
| :--- | :--- | :---: | :--- |
| `scene_id` | `integer` | Có | Số thứ tự phân cảnh bắt đầu từ `1` (`1, 2, 3...`). |
| `narration_text` | `string` | Có | Lời dẫn truyện tiếng Việt của phân cảnh này (dùng để đọc TTS và hiển thị phụ đề). |
| `audio_duration_sec` | `number` | Có | Thời lượng thực tế của phân cảnh tính bằng giây (VD: `5.72`), bằng thời lượng giọng đọc thô đo bởi `Mutagen` cộng thêm `0.30s` đệm âm thanh (Audio Padding). Trước khi chạy TTS mang giá trị ước lượng, sau bước TTS được ghi đè bằng số đo chính xác. |
| `voice_audio_path` | `string \| null` | Không | Đường dẫn tới tệp âm thanh giọng đọc tạm của cảnh (VD: `"out/temp/job_01/scene_01.wav"`). |
| `background_state` | `enum` | Có | Trạng thái nền giấy vở kẻ ngang của phân cảnh. |
| `actors` | `array<ActorSpec>` | Có | Danh sách các nhân vật xuất hiện trong cảnh (gồm `actor_id`, `character_type`, `side`: `"left"`\|`"right"`\|`"top"`\|`"center"`, `weapon`, `scale`, `aura_color`). |
| `action_preset` | `enum` | Có | Mã động tác chiến đấu chủ đạo điều khiển hệ xương người que trong cảnh. |
| `camera_movement` | `enum` | Có | Hiệu ứng di chuyển và rung lắc máy quay trong cảnh. |
| `sfx_events` | `array<SfxEvent>` | Có | Danh sách các sự kiện âm thanh va chạm trong cảnh (`sfx_type`, `offset_sec` tính từ đầu cảnh, `volume` từ `0.0` đến `1.0`). |

### 2.3. Mẫu JSON chuẩn (`SceneSchema`)

```json
{
  "scene_id": 2,
  "narration_text": "Nhị Lang Thần thét lớn, lao vút tới bổ mạnh Tam Tiêm Đảo xuống nhưng Ngộ Không vung gậy sắt đỡ đòn làm tóe lửa khắp mặt giấy!",
  "audio_duration_sec": 6.25,
  "voice_audio_path": "out/temp/job_20261031_89ab/audio/scene_02_voice.wav",
  "background_state": "ink_splattered",
  "actors": [
    {
      "actor_id": "wukong_main",
      "character_type": "dark_wukong",
      "display_name": "Ngộ Không Hắc Hóa",
      "side": "left",
      "weapon": "ruyi_staff",
      "scale": 1.0,
      "aura_color": "#D92626"
    },
    {
      "actor_id": "erlang_boss",
      "character_type": "erlang_shen",
      "display_name": "Nhị Lang Thần",
      "side": "right",
      "weapon": "three_pointed_spear",
      "scale": 1.05,
      "aura_color": "#E6B800"
    }
  ],
  "action_preset": "heavy_charge_clash",
  "camera_movement": "zoom_punch_impact",
  "sfx_events": [
    {
      "sfx_type": "whoosh_heavy",
      "offset_sec": 0.85,
      "volume": 0.75
    },
    {
      "sfx_type": "metal_weapon_clash",
      "offset_sec": 2.40,
      "volume": 1.0
    },
    {
      "sfx_type": "paper_shockwave",
      "offset_sec": 2.45,
      "volume": 0.85
    }
  ]
}
```

---

## 3. Định Dạng Trạng Thái Tác Vụ (`JobStatus`)

Đối tượng dùng để đồng bộ trạng thái thời gian thực giữa Tầng Điều Phối (`Task Orchestrator`) với giao diện Web UI và thông báo Telegram Bot.

### 3.1. Danh sách 7 trạng thái chuẩn (`status` Enum)

| Giá trị Enum | Ý nghĩa trạng thái | Khoảng `%` tiến độ chuẩn |
| :--- | :--- | :---: |
| `"queued"` | Tác vụ đã được tiếp nhận và đang nằm trong hàng đợi xử lý. | `0% – 5%` |
| `"parsing"` | Đang phân tích kịch bản văn bản thành danh sách `SceneSchema`. | `5% – 15%` |
| `"generating_audio"` | Đang tạo giọng đọc tiếng Việt (TTS) và đo thời lượng từng phân cảnh. | `15% – 35%` |
| `"rendering_animation"` | Đang tính toán chuyển động xương người que và vẽ các khung hình 9:16. | `35% – 80%` |
| `"compositing"` | Đang trộn 3 kênh âm thanh (Voice + SFX + BGM) và đóng gói tệp `.mp4`. | `80% – 99%` |
| `"completed"` | Đã xuất tệp `.mp4` thành công và dọn dẹp xong tệp tạm. | `100%` |
| `"failed"` | Tác vụ dừng do lỗi; thông tin chi tiết nằm trong `error_detail`. | Giữ nguyên tại điểm lỗi |

### 3.2. Mẫu JSON chuẩn (`JobStatus`)

```json
{
  "job_id": "job_20261031_89ab",
  "status": "rendering_animation",
  "progress_percent": 58,
  "current_step_message": "Đang vẽ hoạt hình phân cảnh 5/9 (Ngộ Không giao chiến Nhị Lang Thần)...",
  "total_scenes": 9,
  "completed_scenes": 4,
  "started_at": "2026-10-31T07:00:02.000Z",
  "updated_at": "2026-10-31T07:00:45.000Z",
  "error_detail": null
}
```

---

## 4. Định Dạng Kết Quả Đầu Ra (`RenderResult`)

Đối tượng trả về khi tác vụ đạt trạng thái `"completed"` (hoặc `"failed"`), phục vụ việc phát video trên Web UI, tải xuống hoặc gửi tệp qua Telegram Bot.

### 4.1. Bảng đặc tả trường dữ liệu (`RenderResult`)

| Tên trường | Kiểu dữ liệu | Bắt buộc | Mô tả chi tiết |
| :--- | :--- | :---: | :--- |
| `job_id` | `string` | Có | Mã định danh của tác vụ. |
| `status` | `enum` | Có | `"completed"` hoặc `"failed"`. |
| `output_video_path` | `string \| null` | Có | Đường dẫn tương đối trên máy chủ tới file MP4 (VD: `"out/job_20261031_89ab.mp4"`). |
| `video_url` | `string \| null` | Có | Đường dẫn HTTP nội bộ để phát trên Web App (VD: `"/api/videos/job_20261031_89ab.mp4"`). |
| `technical_metadata` | `object \| null` | Có | Thông số thực tế của video đầu ra (kiểm chứng bằng `ffprobe`): `resolution` (`"1080x1920"`), `aspect_ratio` (`"9:16"`), `fps` (`30`), `duration_sec`, `file_size_bytes`, `video_codec` (`"h264"`), `audio_codec` (`"aac"`). |
| `scenes_summary` | `array<SceneSchema>` | Có | Danh sách toàn bộ phân cảnh đã kết xuất kèm thời lượng thực tế. |
| `processing_stats` | `object` | Có | Thời gian xử lý từng công đoạn (`parse_time_sec`, `tts_time_sec`, `render_time_sec`, `composite_time_sec`, `total_time_sec`) và phương thức parser/TTS đã dùng. |
| `completed_at` | `string (ISO 8601)` | Có | Thời điểm hoàn tất tác vụ. |
| `error_message` | `string \| null` | Không | Mô tả lỗi cụ thể nếu `status === "failed"`. |

### 4.2. Mẫu JSON chuẩn (`RenderResult`)

```json
{
  "job_id": "job_20261031_89ab",
  "status": "completed",
  "output_video_path": "out/job_20261031_89ab.mp4",
  "video_url": "/api/videos/job_20261031_89ab.mp4",
  "technical_metadata": {
    "resolution": "1080x1920",
    "aspect_ratio": "9:16",
    "fps": 30,
    "duration_sec": 74.6,
    "file_size_bytes": 18452910,
    "video_codec": "h264",
    "audio_codec": "aac"
  },
  "scenes_summary": [
    {
      "scene_id": 1,
      "narration_text": "Giữa trang giấy vở nhuốm mực đen, Tôn Ngộ Không mắt đỏ rực nắm chặt Thiết Bảng Như Ý đứng đối diện Nhị Lang Thần Dương Tiễn.",
      "audio_duration_sec": 7.12,
      "voice_audio_path": null,
      "background_state": "clean_notebook",
      "actors": [],
      "action_preset": "dark_aura_standoff",
      "camera_movement": "zoom_in_dramatic",
      "sfx_events": []
    }
  ],
  "processing_stats": {
    "parser_mode": "rule_based_fallback",
    "tts_engine": "edge_tts",
    "parse_time_sec": 0.12,
    "tts_time_sec": 4.85,
    "render_time_sec": 19.40,
    "composite_time_sec": 3.20,
    "total_time_sec": 27.57
  },
  "completed_at": "2026-10-31T07:01:12.000Z",
  "error_message": null
}
```
