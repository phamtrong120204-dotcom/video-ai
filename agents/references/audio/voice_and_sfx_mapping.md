# TÀI LIỆU THAM CHIẾU KỸ THUẬT: BẢNG ÁNH XẠ GIỌNG ĐỌC TIẾNG VIỆT & SỰ KIỆN ÂM THANH SFX (`voice_and_sfx_mapping.md`)
**Dự án:** Dark Myth Stickman Auto-Studio  
**Đối chiếu hợp đồng dữ liệu:** `docs/04_data_contracts.md` (`ScriptInput.voice_id`, `SceneSchema.sfx_events`)  

---

## 1. Bảng Ánh Xạ Mã Giọng Đọc Tiếng Việt (`edge-tts` Voice Profiles)

| Mã `voice_id` | Giới Tính & Phong Cách | Tốc Độ Khuyên Dùng (`voice_speed`) | Cao Độ (`pitch`) | Vai Trò Trong Dự Án Hắc Ám Tây Du |
| :--- | :--- | :---: | :---: | :--- |
| `"vi-VN-NamMinhNeural"` *(Mặc định)* | Nam — Trầm hùng, đanh thép, sử thi | `1.05` (`+5%`) | `-2Hz` | Giọng thuyết minh chính cho các trận đại chiến Ngộ Không – Nhị Lang Thần – Thiên Đình. |
| `"vi-VN-HoaiMyNeural"` | Nữ — Truyền cảm, rõ chữ, kể chuyện cổ tích hắc ám | `1.02` (`+2%`) | `+0Hz` | Giọng dẫn truyện mở đầu, hồi ức bi kịch hoặc lời dẫn giải huyền thoại. |
| `"offline_vi_synth"` *(Dự phòng tự động)* | Nội bộ — Bộ tổng hợp nhịp âm Offline | `1.00` | Chuẩn | Tự động kích hoạt khi máy tính không có kết nối mạng tới máy chủ Microsoft Edge. |

---

## 2. Bảng Ánh Xạ Các Sự Kiện Âm Thanh Va Chạm Chuẩn (`sfx_type`)

Mọi sự kiện trong `SceneSchema.sfx_events` sử dụng một trong các mã `sfx_type` chuẩn dưới đây. Hệ thống ưu tiên tải tệp `assets/sfx/<sfx_type>.wav`; nếu tệp chưa có sẵn, bộ `ProceduralSFXGenerator` tự động tổng hợp tệp `.wav` bằng thuật toán DSP (`numpy`) theo đúng công thức tần số trong bảng:

| STT | Mã `sfx_type` | Mô Tả Âm Thanh | Thời Lượng (`sec`) | Công Thức Tổng Hợp DSP (Fallback / Auto-Seed vào `assets/sfx/`) | Âm Lượng Mặc Định (`volume`) |
| :-: | :--- | :--- | :---: | :--- | :---: |
| 1 | `"whoosh_heavy"` | Tiếng vung Thiết Bảng / lao người xé gió nặng | `0.35s` | Band-pass filtered white noise quét tần số từ `180 Hz -> 620 Hz -> 140 Hz`, bao hình ADSR đỉnh tại `0.12s`. | `0.75` |
| 2 | `"staff_whoosh_fast"` | Tiếng múa gậy liên hoàn tốc độ cao | `0.18s` | Chuỗi xung noise hẹp quét nhanh `320 Hz -> 950 Hz`, decay nhanh `80ms`. | `0.65` |
| 3 | `"metal_weapon_clash"` | Tiếng Thiết Bảng đập mạnh vào Tam Tiêm Đảo tóe lửa | `0.45s` | Tổng hợp điều chế tần số (FM Metallic Synthesis) với các họa âm không nguyên (`f = [820, 1340, 2190, 3410] Hz`) + xung va chạm đầu `15ms`. | `1.00` |
| 4 | `"multi_clash_rapid"` | Chuỗi 4 tiếng binh khí chạm nhau dồn dập | `0.60s` | Lặp 4 xung `metal_weapon_clash` rút gọn cách nhau `130ms` với cao độ biến thiên nhẹ $\pm 8\%$. | `0.85` |
| 5 | `"paper_shockwave"` | Tiếng sóng xung kích làm rung mặt giấy vở | `0.50s` | Sóng sin trầm quét giảm tần số (`Sub-bass pitch drop: 140 Hz -> 38 Hz`) kết hợp tiếng sột soạt giấy căng (`high-frequency rustle`). | `0.85` |
| 6 | `"earth_shatter_slam"` | Tiếng gậy khổng lồ bổ nát mặt đất trang giấy | `0.75s` | Xung trầm cực mạnh `110 Hz -> 28 Hz` + lớp nhiễu trầm (`low-pass noise < 280 Hz`) ngân dài có độ méo hài (`tanh overdrive`). | `1.00` |
| 7 | `"vortex_spin_whoosh"` | Tiếng lốc xoáy gậy quét bay Thiên Binh | `0.80s` | Nhiễu lọc thông dải điều chế biên độ hình sin (`AM Tremolo 9 Hz`) tạo cảm giác xoay vòng liên tục. | `0.80` |
| 8 | `"divine_beam_charge"` | Tiếng tụ lực và phóng tia sáng Thiên Nhãn | `0.55s` | Sóng răng cưa (Sawtooth) tăng dần tần số `220 Hz -> 1480 Hz` kèm sóng hài bậc 2. | `0.80` |
| 9 | `"laser_clash_sizzle"` | Tiếng tia năng lượng chạm vào Thiết Bảng | `0.65s` | Sóng FM tần số cao `1600 Hz` trộn nhiễu tia lửa điện (`crackle impulses`). | `0.85` |
| 10 | `"heavenly_thunder_rumble"` | Tiếng sấm rền uy nghiêm khi Bàn Tay Phật xuất hiện | `1.10s` | Nhiễu hồng (Pink noise) lọc thông thấp `160 Hz` với biên độ gợn sóng nhiều đỉnh mô phỏng tiếng sấm vang xa. | `0.90` |
| 11 | `"giant_palm_boom"` | Tiếng Như Lai Thần Chưởng giáng xuống trấn áp | `0.95s` | Hợp âm trầm cộng hưởng (`55 Hz + 82.5 Hz + 110 Hz`) kèm xung chấn động cực đại đầu pha. | `1.00` |
| 12 | `"dark_aura_hum"` | Tiếng hắc khí trầm đục tỏa ra từ Ngộ Không | `0.90s` | Sóng trầm `65 Hz` điều chế pha chậm tạo âm thanh u tối huyền bí. | `0.55` |
| 13 | `"wind_howl"` | Tiếng gió lạnh thổi qua chiến trường trang giấy | `1.00s` | Nhiễu trắng qua bộ lọc cộng hưởng hẹp quét chậm quanh `420 Hz`. | `0.50` |
| 14 | `"body_impact_sweep"` / `"heavy_body_hit"` | Tiếng thân người trúng đòn văng đi | `0.30s` | Xung trầm ngắn `160 Hz -> 45 Hz` decay trong `180ms`. | `0.80` |
| 15 | `"weapon_ground_scrape"` | Tiếng cắm vũ khí trượt phanh trên mặt giấy | `0.45s` | Nhiễu ma sát kim loại (`800 Hz – 2400 Hz`) giảm dần biên độ. | `0.75` |

---

## 3. Cấu Hình Nhạc Nền Mặc Định (`bgm_theme`)

- **`"dark_myth_orchestral"` (Mặc định):** Giai điệu ngũ cung thứ (D-minor pentatonic: `D2, F2, G2, A2, C3`) kết hợp nhịp trống trận trầm hùng (`96 BPM`), tự động lặp liền mạch (seamless loop) theo tổng thời lượng video và áp dụng **Audio Ducking xuống 20%** (`-14 dB`) khi có giọng đọc thuyết minh.
