# BÁO CÁO NGHIỆM THU KỸ THUẬT GIAI ĐOẠN 5.1
## PROCEDURAL NOTEBOOK BACKGROUND ENGINE
**Dự án:** Dark Myth Stickman Auto-Studio  
**Chuyên gia thực hiện:** Senior Computer Graphics Engineer, Procedural Art Developer & Lead QA  
**Ngày báo cáo:** 31/10/2026  
**Trạng thái kiểm thử:** 100% PASSED (67/67 Unit Tests, 13 Image Previews Generated)

---

## 1. KIẾN TRÚC BACKGROUND RENDERER

Module `NotebookBackgroundRenderer` được triển khai tại [`app/modules/animation/background_renderer.py`](file:///c:/Users/phamtrong/Desktop/video%20agent/app/modules/animation/background_renderer.py). Module này hoạt động hoàn toàn độc lập, thuần toán học hình ảnh (Procedural Image Synthesis) thông qua sự kết hợp giữa **NumPy** (tạo ma trận màu, texture sợi cellulose và vignette) và **Pillow (PIL)** (vẽ vector các đường kẻ ngang, đường lề kép, lỗ đục gáy vở và các hiệu ứng nứt rách/mực văng).

### Sơ Đồ Kiến Trúc Xử Lý 7 Tầng (Layered Rendering Pipeline)

```
       [Input: BackgroundState, width, height, seed]
                            │
                            ▼
     ┌──────────────────────────────────────────────┐
     │  Layer 1: Paper Base Gradient & Color Tint   │
     │   (NumPy float32 base array - Warm Cream)    │
     └──────────────────────┬───────────────────────┘
                            │
                            ▼
     ┌──────────────────────────────────────────────┐
     │  Layer 2: Natural Paper Texture & Fibers     │
     │   (High-freq grain + Low-freq organic cloud) │
     └──────────────────────┬───────────────────────┘
                            │
                            ▼
     ┌──────────────────────────────────────────────┐
     │  Layer 3: Lighting & Soft Radial Vignette    │
     │   (Gentle corner falloff for paper depth)    │
     └──────────────────────┬───────────────────────┘
                            │
                            ▼  [Convert to PIL Canvas]
     ┌──────────────────────────────────────────────┐
     │  Layer 4: Vector Student Notebook Elements   │
     │   - Horizontal Ruled Lines (Light Blue)      │
     │   - Vertical Margin Lines (Double Crimson)   │
     │   - Left Binder Punch Holes (with 3D shadow) │
     └──────────────────────┬───────────────────────┘
                            │
                            ▼
     ┌──────────────────────────────────────────────┐
     │  Layer 5: Dark Myth State-Specific Effects   │
     │   - Ink Splatters (Combat-Zone safe)         │
     │   - Procedural Branching Fractures & Tears   │
     │   - Necrotic Dark Corruption Tendrils & Fog  │
     │   - Divine Golden Volumetric Beams & Dust    │
     └──────────────────────┬───────────────────────┘
                            │
                            ▼
     ┌──────────────────────────────────────────────┐
     │  Layer 6: Artistic Color & Contrast Balance  │
     └──────────────────────┬───────────────────────┘
                            │
                            ▼
            [Output: RGB PIL Image / NumPy Array]
```

---

## 2. CÁC TRẠNG THÁI NỀN ĐÃ TRIỂN KHAI

Hệ thống hỗ trợ 100% tất cả các giá trị `BackgroundState` trong `SceneSchema` và Data Contract:

1. **`clean_notebook` (đồng thời bao quát `normal_page`):**
   - Giấy học sinh ngả vàng kem ấm `#F4EFE6`.
   - Các dòng kẻ ngang xanh nhạt `#9BB8D3`, khoảng cách chuẩn $\Delta Y = 48\text{ px}$.
   - Đường lề đỏ kép `#C84B31` cách mép trái $135\text{ px}$.
   - 5 lỗ đóng gáy vở có bóng đổ 3D bên lề trái ($X = 65\text{ px}$).
2. **`ink_splattered`:**
   - Nền kem nhạt hơi xám `#ECE6DA`.
   - Vết mực đen Sumi-e tự nhiên và điểm xuyết vết mực đỏ thẫm văng tung tóe.
   - **Bảo vệ vùng chiến đấu (Combat Zone Protection):** Vết mực lớn được bố trí ở các góc và rìa trang giấy, vùng trung tâm ($X \in [35\%, 65\%], Y \in [40\%, 65\%]$) luôn được giữ sạch để không che khuất mặt hoặc vũ khí của nhân vật người que.
3. **`cracked_page`:**
   - Nền giấy phong hóa `#DED8CC`.
   - Các vết nứt gãy khúc phân nhánh ngẫu nhiên (Procedural Branching Fractures) bắt nguồn từ tâm chấn va chạm dưới đất hoặc từ các mép giấy, có rãnh đen kèm viền nổi sáng màu tạo cảm giác nứt toác 3D.
4. **`torn_dark_myth`:**
   - Nền giấy sẫm màu tàn tro `#C3BBB0`.
   - Góc trên bên phải bị rách toạc để lộ khoảng đen hư vô bên dưới kèm rìa xơ giấy trắng và bóng đổ.
   - Các hạt tàn tro đen bay lơ lửng trên mặt giấy.
5. **`dark_corrupted_page`:**
   - Nền giấy chuyển hoàn toàn sang tông hắc ám `#242127`.
   - Các dòng kẻ ngang và đường lề bị đổi màu tối mờ ảo nhưng vẫn nhận diện rõ cấu trúc trang vở.
   - Lớp sương mù tà khí từ mặt đất bốc lên kèm các tua mực đen uốn lượn như khói đen creeping từ các mép giấy.
6. **`heavenly_pressure`:**
   - Nền chuyển sắc gradient hoàng kim từ đỉnh `#FFECB0` xuống chân `#EEE4D4`.
   - Các luồng thần quang (Volumetric Light Beams) từ đỉnh trời giáng xuống.
   - Bụi vàng phát sáng lấp lánh (Golden Dust Particles) lơ lửng trong không gian.

---

## 3. BẢNG PALETTE MÀU SẮC CHUẨN

| Tên Thành Phần | Mã Hex | Giá Trị RGB | Mô Tả & Mục Đích |
| :--- | :---: | :---: | :--- |
| **Clean Paper Base** | `#F4EFE6` | `(244, 239, 230)` | Màu giấy vở bãi bằng ngả vàng kem ấm, chống mỏi mắt |
| **Ink Splatter Base** | `#ECE6DA` | `(236, 230, 218)` | Màu giấy hơi xám nhẹ sau khi thấm mực |
| **Cracked Paper Base** | `#DED8CC` | `(222, 216, 204)` | Màu giấy phong hóa, khô giòn dễ gãy vỡ |
| **Torn Myth Base** | `#C3BBB0` | `(195, 187, 175)` | Màu tro xám của trang giấy bị cháy xém mép |
| **Corrupted Paper Base**| `#242127` | `(36, 33, 39)` | Nền giấy đen hắc hóa sẫm màu |
| **Heavenly Gold Top** | `#FFECB0` | `(255, 236, 175)` | Ánh sáng vàng Phật Quang chiếu từ đỉnh trời |
| **Ruled Line Standard** | `#9BB8D3` | `(155, 184, 211)` | Dòng kẻ ngang xanh da trời nhạt truyền thống |
| **Ruled Line Corrupted**| `#3E4A58` | `(62, 74, 88)` | Dòng kẻ xanh xám mờ trên nền giấy tối |
| **Margin Double Red** | `#C84B31` | `(200, 75, 49)` | Đường lề vở đôi màu đỏ son học sinh |
| **Sumi-e Black Ink** | `#121216` | `(18, 18, 22)` | Mực tàu đen đậm đặc nét bút lông |
| **Blood Splatter Red** | `#911818` | `(145, 24, 24)` | Vết mực đỏ son sẫm điểm xuyết |

---

## 4. BẰNG CHỨNG XUẤT ẢNH PREVIEW THỰC TẾ

Đã khởi chạy kịch bản kết xuất tự động [`scripts/preview_notebook_backgrounds.py`](file:///c:/Users/phamtrong/Desktop/video%20agent/scripts/preview_notebook_backgrounds.py) và tạo đầy đủ các tệp tại thư mục `out/preview/backgrounds/`:

| STT | Trạng Thái Nền | Tên Tệp PNG (1080x1920) | Dung Lượng (Full-HD) | Thời Gian Render | Tên Tệp PNG (540x960) | Dung Lượng (Preview) |
| :---: | :--- | :--- | :---: | :---: | :--- | :---: |
| **1** | `clean_notebook` | `bg_clean_notebook_1080x1920.png` | 2,151 KB | 0.181s | `bg_clean_notebook_540x960.png` | 560 KB |
| **2** | `ink_splattered` | `bg_ink_splattered_1080x1920.png` | 2,169 KB | 0.207s | `bg_ink_splattered_540x960.png` | 566 KB |
| **3** | `cracked_page` | `bg_cracked_page_1080x1920.png` | 2,183 KB | 0.186s | `bg_cracked_page_540x960.png` | 570 KB |
| **4** | `torn_dark_myth` | `bg_torn_dark_myth_1080x1920.png` | 2,110 KB | 0.235s | `bg_torn_dark_myth_540x960.png` | 559 KB |
| **5** | `dark_corrupted_page` | `bg_dark_corrupted_page_1080x1920.png` | 1,976 KB | 0.282s | `bg_dark_corrupted_page_540x960.png` | 503 KB |
| **6** | `heavenly_pressure` | `bg_heavenly_pressure_1080x1920.png` | 2,278 KB | 0.192s | `bg_heavenly_pressure_540x960.png` | 592 KB |
| **-** | **Collage Tổng Hợp**| `all_states_comparison_grid.png` | 1,141 KB | 0.080s | *(Lưới so sánh trực quan 6 trạng thái nền)* | - |

> Người dùng có thể mở trực tiếp tệp [`out/preview/backgrounds/all_states_comparison_grid.png`](file:///c:/Users/phamtrong/Desktop/video%20agent/out/preview/backgrounds/all_states_comparison_grid.png) để xem toàn bộ 6 trạng thái nền cạnh nhau.

---

## 5. KẾT QUẢ KIỂM THỬ ĐƠN VỊ & TOÀN DỰ ÁN

### A. Kiểm Thử Đơn Vị Background Renderer (`tests/test_background_renderer.py`)
- `test_renderer_supports_all_background_states`: PASSED (Đủ 7 enums).
- `test_renderer_correct_dimensions_production`: PASSED (1080x1920, RGB, uint8).
- `test_renderer_correct_dimensions_preview`: PASSED (540x960, RGB).
- `test_renderer_not_empty_or_solid_black`: PASSED (Không rỗng, phương sai > 5.0).
- `test_renderer_deterministic_with_same_seed`: PASSED (Cùng seed ra ảnh trùng khớp từng bit 100%).
- `test_renderer_variations_with_different_seeds`: PASSED (Khác seed tạo biến thể vân hạt khác nhau).
- `test_renderer_visual_distinction_between_states`: PASSED (Độ lệch màu giữa Clean và Dark > 100 đơn vị).
- `test_renderer_handles_invalid_state`: PASSED (Bắt lỗi ValueError khi truyền state lạ).
- `test_renderer_combat_zone_safety_on_ink_splatters`: PASSED (Vùng giữa màn hình không bị che lấp).
- `test_renderer_does_not_mutate_scene_schema`: PASSED (Bảo tồn hợp đồng dữ liệu).

### B. Kiểm Thử Toàn Bộ Dự Án (`pytest -v`)
```
============================= 67 passed in 6.59s =============================
```
- 67/67 bài kiểm thử PASSED (0 failed, 0 warning).
- Không gây hồi quy hay xung đột với các module Giai đoạn 1, 2, 3, 4.

---

## 6. ĐO ĐẠC HIỆU NĂNG & TIÊU THỤ BỘ NHỚ RAM

Lệnh thực nghiệm đo bộ nhớ với `tracemalloc`:
```python
Render Time (1080x1920): 0.215s
Current RAM: 0.72 MB, Peak RAM: 180.72 MB
```
- **Thời gian render:** Chỉ mất trung bình **$0.20\text{ giây}$** cho một tấm ảnh Full-HD 1080x1920.
- **Mức tiêu thụ RAM đỉnh (Peak Memory):** Đạt **$180.72\text{ MB}$**, thấp hơn nhiều so với ngưỡng trần an toàn $300\text{ MB}$.
- **Giải phóng bộ nhớ:** Bộ nhớ RAM tự động hạ về **$0.72\text{ MB}$** ngay sau khi hàm render kết thúc nhờ cơ chế không lưu đệm mảng ảnh không cần thiết.

---

## 7. CÁC HẠN CHẾ & LƯU Ý THẨM MỸ CẦN NGƯỜI DÙNG XEM XÉT

1. **Độ sắc nét của vết nứt và xơ giấy rách:**
   - Các vết nứt hiện được vẽ theo thuật toán phân nhánh đệ quy ngẫu nhiên (Brownian fractal-like walk). Người dùng cần mở xem ảnh `bg_cracked_page_1080x1920.png` và `bg_torn_dark_myth_1080x1920.png` để đánh giá xem độ gồ ghề của vết nứt đã vừa mắt chưa, có cần tăng thêm độ dày hoặc số lượng nhánh con không.
2. **Mật độ tia sáng hoàng kim trong `heavenly_pressure`:**
   - Luồng sáng vàng hiện có từ 7 đến 12 nan quạt tỏa từ đỉnh trời. Người dùng có thể kiểm tra ảnh `bg_heavenly_pressure_1080x1920.png` xem độ mờ và độ ấm của ánh vàng có cần sáng hơn hoặc dịu hơn không.

---

## 8. KẾT LUẬN NGHIỆM THU

### **ĐÁNH GIÁ: PASS (HOÀN THÀNH GIAI ĐOẠN 5.1)**

Toàn bộ các tiêu chí kỹ thuật của Giai đoạn 5.1 đã hoàn thành trọn vẹn, vượt qua tất cả các bài kiểm thử tự động và xuất đầy đủ ảnh hiện vật xem trước.

> [!IMPORTANT]
> **DỪNG LẠI CHỜ DUYỆT (STOP PROTOCOL):**
> Tuân thủ Hiến pháp làm việc (`AGENTS.md`), toàn bộ quá trình viết mã đã dừng lại hoàn toàn. Tôi **KHÔNG** tự ý chuyển sang Giai đoạn 5.2. Kính mời Người dùng kiểm tra bộ ảnh preview và phê duyệt trước khi bắt tay xây dựng **Giai đoạn 5.2 – 2D Procedural Stickman Rigging Engine**!
