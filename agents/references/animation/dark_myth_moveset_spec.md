# TÀI LIỆU THAM CHIẾU KỸ THUẬT: BẢNG THÔNG SỐ 8 CHIÊU THỨC & 4 NGOẠI HÌNH NHÂN VẬT HẮC ÁM TÂY DU (`dark_myth_moveset_spec.md`)
**Dự án:** Dark Myth Stickman Auto-Studio  
**Đối chiếu hợp đồng dữ liệu:** Khớp 100% với các giá trị Enum trong `docs/04_data_contracts.md`  

---

## 1. Bảng Thông Số Kỹ Thuật 4 Ngoại Hình Nhân Vật (`character_type`)

Mọi nhân vật được vẽ trên không gian chuẩn `1080 x 1920` với mặt đất tại $Y_{\text{ground}} = 1420\text{ px}$:

| Mã `character_type` | Tên Hiển Thị | Tỷ Lệ (`scale`) | Màu Nét Vẽ & Hào Quang (`aura_color`) | Phụ Kiện Đầu & Thân Đặc Trưng (Procedural Geometry) | Vũ Khí Mặc Định (`weapon`) |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `"dark_wukong"` | **Ngộ Không Hắc Hóa** | `1.00` | Thân đen mực `#141416`, Mắt đỏ `#FF1E1E`, Hào quang đỏ hắc ám `#D92626` | - Vòng Kim Cô gãy nát chữ V màu vàng kim `#E6B800` trên trán.<br>- **2 sợi lông chim trĩ dài `180px`** vẽ bằng đường cong Bezier bậc 3 uốn lượn phía sau đầu.<br>- Khăn choàng cổ màu đỏ thẫm rách đuôi bay ngược hướng di chuyển. | `"ruyi_staff"` (Thiết Bảng Như Ý đen viền đỏ, 2 đầu bọc vàng kim, biến thiên chiều dài `280px – 1300px`) |
| `"erlang_shen"` | **Nhị Lang Thần (Dương Tiễn)** | `1.05` | Thân đen xanh `#1A202C`, Thiên Nhãn phát sáng `#FFD700`, Hào quang vàng kim `#E6B800` | - Mũ chiến thần bạc có chóp nhọn.<br>- **Thiên Nhãn dọc giữa trán** phát tia sáng vàng kim.<br>- Giáp vai hai bên nhô cao góc cạnh và áo choàng trắng xám. | `"three_pointed_spear"` (Tam Tiêm Lưỡng Nhận Đảo dài `340px`, mũi đinh ba sắc nhọn ánh bạc) |
| `"celestial_general"` / `"celestial_soldier_squad"` | **Thiên Binh Thiên Tướng** | `0.95` (Binh) / `1.25` (Tướng) | Thân xám thép `#2D3748`, Hào quang lam nhạt `#63B3ED` | - Mũ trụ thiên binh có缨 (chùm tua đỏ trên đỉnh mũ).<br>- Khi xuất hiện ở chế độ `celestial_soldier_squad`, vẽ đội hình `3–5` người que xếp lớp có độ lệch pha chuyển động $\Delta \phi = 0.15$. | `"celestial_halberd"` (Trường thương / Đại kích dài `300px`) |
| `"buddha_palm"` | **Bàn Tay Phật Tổ (Như Lai Thần Chưởng)** | `3.50` | Viền mực đen đậm `#1A1817`, Lòng bàn tay tỏa kim quang `#F6AD55` | - Thực thể khổng lồ xuất hiện từ đỉnh khung hình ($Y \in [-200, 950]\text{ px}$), gồm 5 ngón tay khổng lồ, lòng bàn tay có ấn ký chữ Vạn / vòng tròn kim quang đồng tâm đè bẹp không gian bên dưới. | `"giant_golden_palm"` (Chưởng lực sóng xung kích bán kính `480px`) |

---

## 2. Bảng Thông Số Kỹ Thuật 8 Chiêu Thức Chiến Đấu (`action_preset`)

Mỗi chiêu thức được định nghĩa theo tiến độ chuẩn hóa $u = f / N_{\text{frames}} \in [0.0, 1.0]$ của phân cảnh:

| STT | Mã `action_preset` | Mô Tả Hình Ảnh & Quỹ Đạo Khớp Xương | Điểm Va Chạm ($u_{\text{impact}}$) | Hiệu Ứng VFX & Trang Giấy | Góc Máy Đề Xuất (`camera_movement`) | Sự Kiện SFX Tự Động (`sfx_type`) |
| :-: | :--- | :--- | :---: | :--- | :--- | :--- |
| 1 | `"dark_aura_standoff"` | Hai nhân vật đứng đối diện tại $X_L = 300, X_R = 780$, chống vũ khí xuống đất; lồng ngực thở nhịp nhàng, khăn choàng & lông chim trĩ bay mạnh, hắc khí và kim quang bốc lên đối chọi. | `0.50` (Xung đột khí thế) | Các hạt mực đen và tàn lửa bay ngược từ mặt đất lên trời (`40 particles`). | `"zoom_in_dramatic"` | `"dark_aura_hum"`, `"wind_howl"` |
| 2 | `"heavy_charge_clash"` | $u \in [0, 0.25]$: Hai bên hạ thấp trọng tâm tụ lực.<br>$u \in [0.25, 0.45]$: Lao vút vào tâm $X = 540$ để lại 4 tàn ảnh.<br>$u \in [0.45, 0.55]$: Giao binh tóe lửa, khựng hình Hitstop.<br>$u > 0.55$: Bật lùi tạo khoảng cách. | `0.45` | Vòng sóng xung kích trắng/đỏ bán kính `320px`, `25` tia lửa vàng/đỏ, 6 nhánh vết nứt giấy tại $(540, 1280)$. | `"zoom_punch_impact"` | `"whoosh_heavy"`, `"metal_weapon_clash"`, `"paper_shockwave"` |
| 3 | `"flurry_combo"` | Chuỗi 5 đòn đánh liên hoàn tốc độ siêu thanh tại vùng trung tâm; tay và vũ khí xoay góc $\pm 75^\circ$ tần số cao ($6\text{ Hz}$), tạo hiệu ứng hàng chục bóng gậy/thương đan chéo. | `0.25, 0.45, 0.65, 0.82` | Các vệt chém hình lưỡi liềm (Crescent Slash Trails) đan chéo liên tục và vết mực văng lên mặt giấy. | `"shake_heavy"` | `"staff_whoosh_fast"`, `"multi_clash_rapid"` |
| 4 | `"staff_vortex_sweep"` | Ngộ Không nhảy nhẹ lên $Y = 1220$, xoay tròn Thiết Bảng Như Ý $360^\circ \times 4$ vòng tạo cơn lốc mực đen-đỏ bán kính `360px`, đánh văng đội hình Thiên Binh về hai mép khung hình. | `0.35, 0.70` | Vòng xoáy lốc mực đồng tâm quanh nhân vật, các người que Thiên Binh bị xoay tròn văng ra biên. | `"static_wide"` | `"vortex_spin_whoosh"`, `"body_impact_sweep"` |
| 5 | `"sky_leap_slam"` | $u \in [0, 0.40]$: Ngộ Không bật nhảy vọt lên đỉnh trang giấy ($Y = 420$), Thiết Bảng Như Ý phóng đại gấp 3 lần.<br>$u \in [0.40, 0.60]$: Bổ thẳng đứng xuống mặt đất tại $Y = 1420$. | `0.60` | Cột sáng đỏ/đen dọc khung hình 9:16; mặt đất giấy vở nứt toác làm đôi, mảnh giấy bay lên. | `"pan_vertical_down"` | `"sky_leap_whoosh"`, `"earth_shatter_slam"` |
| 6 | `"divine_eye_beam"` | Nhị Lang Thần bay lơ lửng tại $(760, 720)$, mở Thiên Nhãn bắn chùm tia sáng vàng kim chéo xuống $(320, 1350)$; Ngộ Không dựng ngang Thiết Bảng đỡ chùm tia tạo màn chắn năng lượng. | `0.40` | Chùm tia laser vàng kim rộng `45px` có lõi trắng sáng và mưa tia lửa phản xạ quanh Thiết Bảng. | `"shake_heavy"` | `"divine_beam_charge"`, `"laser_clash_sizzle"` |
| 7 | `"giant_palm_suppression"` | Bàn Tay Phật Tổ khổng lồ (`scale = 3.5`) từ $Y = -150$ từ từ giáng xuống $Y = 820$; Ngộ Không ở dưới ($Y = 1380$) chống Thiết Bảng Như Ý phóng đại thẳng đứng đỡ lấy lòng bàn tay, hai chân lún sâu xuống mặt giấy. | `0.55` | Toàn bộ nửa trên trang giấy chuyển ánh vàng uy nghiêm, sóng khí ép cong các dòng kẻ ngang của trang vở. | `"pan_vertical_up"` | `"heavenly_thunder_rumble"`, `"giant_palm_boom"` |
| 8 | `"knockback_recovery"` | Nhân vật bị lực đánh hất văng từ $X = 540$ trượt dài về sát lề đỏ $X = 180$, cắm mạnh vũ khí xuống mặt giấy tạo rãnh mực đen dài để phanh lại, sau đó ngẩng đầu mắt sáng đỏ rực. | `0.20` (Trúng đòn), `0.65` (Cắm vũ khí phanh) | Vệt trượt mực đen dài `350px` trên mặt đất và bụi giấy cuốn theo chân nhân vật. | `"zoom_in_dramatic"` | `"heavy_body_hit"`, `"weapon_ground_scrape"` |
