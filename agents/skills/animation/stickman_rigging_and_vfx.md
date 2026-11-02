# KỸ NĂNG CHUYÊN MÔN: TOÁN HỌC DỰNG XƯƠNG NGƯỜI QUE 2D, NỀN GIẤY VỞ & HIỆU ỨNG HẮC ÁM TÂY DU (`stickman_rigging_and_vfx.md`)
**Phạm vi áp dụng:** Giai đoạn 5 & Giai đoạn 6 (`app/animation/`)  
**Thư viện cốt lõi sử dụng:** `numpy`, `Pillow (PIL)`, `opencv-python-headless (cv2)`, `math`  

---

## 1. Quy Chuẩn Không Gian Tọa Độ & Nền Giấy Vở Kẻ Ngang (Notebook Paper Canvas)

### 1.1. Hệ tọa độ chuẩn 9:16
- Khung hình chuẩn: Rộng $W = 1080\text{ px}$, Cao $H = 1920\text{ px}$, 3 kênh màu RGB (`dtype=np.uint8`, shape `(1920, 1080, 3)`).
- Đường mặt đất giao chiến (Ground Plane): $Y_{\text{ground}} = 1420\text{ px}$.
- Vùng an toàn phụ đề tiếng Việt (Subtitle Safe Zone): $Y \in [1480, 1740]\text{ px}$, $X \in [80, 1000]\text{ px}$.

### 1.2. Thuật toán vẽ nền giấy vở kẻ ngang (`NotebookPaperRenderer`)
Để tối ưu tốc độ render (không vẽ lại các dòng kẻ tĩnh trên từng frame từ đầu), hệ thống khởi tạo sẵn **Bộ đệm Nền Tĩnh (Base Paper Layer)** cho mỗi trạng thái `background_state` và chỉ sao chép (`base_paper.copy()`) ở đầu mỗi frame:
1. **Màu nền giấy gốc:**
   - `"clean_notebook"`: Kem ấm `#F4EFE6` $\rightarrow$ RGB `(244, 239, 230)`.
   - `"ink_splattered"`: Kem xám `#EAE3D5` $\rightarrow$ RGB `(234, 227, 213)`.
   - `"torn_dark_myth"`: Xám tro hắc ám `#C8C0B4` $\rightarrow$ RGB `(200, 192, 180)` kèm tối bốn góc (Vignette).
   - `"heavenly_pressure"`: Ánh vàng hoàng kim từ đỉnh trang giấy đổ xuống (`gradient` từ `#FFE89E` ở $Y=0$ xuống `#EAE3D5` ở $Y=1920$).
2. **Dòng kẻ ngang học sinh (Horizontal Ruled Lines):**
   - Khoảng cách dòng: $\Delta Y = 48\text{ px}$, bắt đầu từ $Y_{\text{start}} = 180\text{ px}$ đến $Y_{\text{end}} = 1820\text{ px}$.
   - Màu dòng kẻ: Xanh nhạt `#9BB8D3` $\rightarrow$ RGB `(155, 184, 211)`, độ dày `2 px`.
3. **Đường lề dọc (Vertical Margin Line):**
   - Tọa độ $X_{\text{margin}} = 135\text{ px}$, kéo dài từ $Y = 0$ đến $Y = 1920$.
   - Màu lề: Đỏ thẫm `#C84B31` $\rightarrow$ RGB `(200, 75, 49)`, độ dày `3 px` (vẽ 2 đường song song cách nhau `6 px` để tạo cảm giác vở học sinh truyền thống).
4. **Lỗ đóng gáy vở (Binder Holes):**
   - Vẽ 5 hình tròn màu xám đậm `(70, 70, 75)` bán kính $R = 22\text{ px}$ dọc theo lề trái tại $X = 65\text{ px}$, $Y \in \{260, 610, 960, 1310, 1660\}\text{ px}$.

---

## 2. Hệ Thống Khớp Xương 2D (2D Hierarchical Stickman Rigging)

### 2.1. Cấu trúc cây khớp xương chuẩn (`StickmanSkeleton`)
Mọi nhân vật người que được định nghĩa bởi điểm gốc `hip = (x_root, y_root)` và tỷ lệ nhân vật `scale` ($S$, mặc định $S = 1.0$). Chiều dài các đoạn xương chuẩn (ở $S = 1.0$):
- $L_{\text{torso}} = 130\text{ px}$ (từ `hip` lên `neck`).
- $L_{\text{head\_radius}} = 34\text{ px}$ (tâm `head_center` cách `neck` một đoạn $40\text{ px}$).
- $L_{\text{upper\_arm}} = 65\text{ px}$, $L_{\text{forearm}} = 62\text{ px}$.
- $L_{\text{thigh}} = 78\text{ px}$, $L_{\text{calf}} = 76\text{ px}$.

### 2.2. Công thức Động học Thuận (Forward Kinematics - FK)
Với góc tương đối của mỗi khớp $\theta$ (tính bằng radian, góc $0$ hướng sang phải, chiều dương thuận chiều kim đồng hồ trên hệ tọa độ màn hình $Y$ hướng xuống):
$$\begin{aligned}
\mathbf{P}_{\text{neck}} &= \mathbf{P}_{\text{hip}} + S \cdot L_{\text{torso}} \cdot \begin{bmatrix} \cos(\theta_{\text{torso}}) \\ \sin(\theta_{\text{torso}}) \end{bmatrix} \\
\mathbf{P}_{\text{elbow}} &= \mathbf{P}_{\text{neck}} + S \cdot L_{\text{upper\_arm}} \cdot \begin{bmatrix} \cos(\theta_{\text{torso}} + \theta_{\text{shoulder}}) \\ \sin(\theta_{\text{torso}} + \theta_{\text{shoulder}}) \end{bmatrix} \\
\mathbf{P}_{\text{hand}} &= \mathbf{P}_{\text{elbow}} + S \cdot L_{\text{forearm}} \cdot \begin{bmatrix} \cos(\theta_{\text{torso}} + \theta_{\text{shoulder}} + \theta_{\text{elbow}}) \\ \sin(\theta_{\text{torso}} + \theta_{\text{shoulder}} + \theta_{\text{elbow}}) \end{bmatrix}
\end{aligned}$$
Tương tự cho chân trái/phải (`hip` $\rightarrow$ `knee` $\rightarrow$ `ankle`).

### 2.3. Công thức Động học Ngược 2 Đoạn Xương (2-Bone Analytic Inverse Kinematics - IK)
Khi cần bàn tay nắm chặt điểm giữa cây Thiết Bảng hoặc bàn chân bám chắc trên mặt đất tại tọa độ mục tiêu $\mathbf{T} = (x_t, y_t)$ tính từ gốc khớp $\mathbf{O} = (x_0, y_0)$ với độ dài 2 đoạn xương $L_1, L_2$:
1. Tính khoảng cách $d = \min\left(\|\mathbf{T} - \mathbf{O}\|_2, \; 0.999 \cdot (L_1 + L_2)\right)$ và $d = \max\left(d, \; |L_1 - L_2| + 10^{-3}\right)$.
2. Góc hướng tới mục tiêu: $\alpha = \text{atan2}(y_t - y_0, \; x_t - x_0)$.
3. Theo định lý Cosin:
   $$\cos(\beta) = \text{clip}\left(\frac{L_1^2 + d^2 - L_2^2}{2 L_1 d}, -1.0, 1.0\right), \quad \cos(\gamma) = \text{clip}\left(\frac{L_1^2 + L_2^2 - d^2}{2 L_1 L_2}, -1.0, 1.0\right)$$
4. Tọa độ khớp giữa (khuỷu tay / đầu gối) với hướng gập khớp $k \in \{-1, +1\}$:
   $$\theta_1 = \alpha + k \cdot \arccos(\beta), \quad \mathbf{P}_{\text{mid}} = \mathbf{O} + L_1 \begin{bmatrix} \cos\theta_1 \\ \sin\theta_1 \end{bmatrix}$$

---

## 3. Nội Suy Chuyển Động & Nhịp Điệu Chiến Đấu (Easing & Keyframe Interpolation)

Không bao giờ nội suy tuyến tính đơn điệu (`lerp` thuần) cho các đòn đánh vì sẽ làm chuyển động bị máy móc. Mọi chiêu thức chia tiến độ chuẩn hóa $u \in [0.0, 1.0]$ thành 4 pha:
1. **Pha Tụ Lực (Anticipation, $u \in [0.0, 0.25]$):** Lùi nhẹ hoặc vung vũ khí ra sau theo hàm `ease_out_quad(t) = 1 - (1 - t)^2`.
2. **Pha Xuất Chiêu Tốc Độ Cao (Strike, $u \in [0.25, 0.45]$):** Lao vút tới điểm va chạm theo hàm mũ `ease_in_expo(t) = t^4`.
3. **Pha Chấn Động (Impact Hitstop, $u \in [0.45, 0.52]$):** Giữ nguyên tư thế va chạm trong `2–3 frames`, kích hoạt tia lửa, vết nứt giấy và `Camera Shake`.
4. **Pha Thu Chiêu / Hồi Thế (Follow-through & Recovery, $u \in [0.52, 1.0]$):** Hàm giảm chấn đàn hồi:
   $$\text{ease\_out\_back}(t) = 1 + c_3 (t - 1)^3 + c_1 (t - 1)^2 \quad (c_1 = 1.70158, \; c_3 = c_1 + 1)$$

---

## 4. Kỹ Thuật Vẽ Phụ Kiện Đặc Trưng Hắc Ám Tây Du

### 4.1. Hai sợi lông chim trĩ trên mũ Ngộ Không (Cubic Bezier Pheasant Feathers)
Từ đỉnh đầu $\mathbf{P}_0 = \mathbf{P}_{\text{head}} + (0, -R_{\text{head}})$, vẽ 2 đường cong Bezier bậc 3 dài $180\text{ px}$ uốn lượn theo vận tốc di chuyển và sóng hình sin theo thời gian $t$:
$$\mathbf{B}(s) = (1-s)^3 \mathbf{P}_0 + 3(1-s)^2 s \mathbf{P}_1 + 3(1-s) s^2 \mathbf{P}_2 + s^3 \mathbf{P}_3, \quad s \in [0, 1]$$
Trong đó điểm điều khiển cuối $\mathbf{P}_3$ dao động theo $\Delta y = 18 \sin(8\pi t - \phi)$ để hai sợi lông vũ luôn tung bay sống động ngay cả khi đứng yên.

### 4.2. Thiết Bảng Như Ý Phóng Đại (Dynamic Ruyi Jingu Bang)
- Được định nghĩa bởi tâm nắm tay $\mathbf{P}_{\text{grip}}$, góc xoay $\theta_{\text{staff}}$, bán kính thân gậy $r_{\text{staff}}(t)$ và nửa chiều dài $L_{\text{half}}(t)$.
- Khi thi triển chiêu thức khổng lồ, $L_{\text{half}}(t)$ tăng từ $140\text{ px}$ lên $650\text{ px}$ và $r_{\text{staff}}(t)$ tăng từ $6\text{ px}$ lên $28\text{ px}$; hai đầu gậy vẽ bọc kim cô màu vàng kim `#E6B800` chiếm `18%` chiều dài mỗi đầu, thân giữa màu đen mực viền đỏ hắc khí `#D92626`.

### 4.3. Hiệu ứng Vết Nứt Trang Giấy & Tia Lửa Va Chạm (Paper Crack & Clash Sparks)
- **Vết nứt trang giấy (Procedural Lightning/Paper Fracture):** Từ tâm chấn $\mathbf{C}_{\text{impact}}$, phát sinh $N = 6 \dots 10$ nhánh tia gãy khúc, mỗi nhánh gồm $8$ đoạn thẳng nối tiếp:
  $$\mathbf{V}_{k+1} = \mathbf{V}_k + \ell_k \begin{bmatrix} \cos(\phi_0 + \delta_k) \\ \sin(\phi_0 + \delta_k) \end{bmatrix}, \quad \delta_k \sim \mathcal{U}(-0.45, 0.45)\text{ rad}$$
  Độ dày nét vẽ giảm dần từ `5 px` ở tâm xuống `1 px` ở ngọn, màu đen mực `(25, 22, 20)` kèm viền đỏ sẫm.
- **Tàn ảnh chuyển động (Motion Afterimages):** Lưu tối đa `4` tư thế xương gần nhất trong bộ đệm vòng (Ring Buffer `collections.deque(maxlen=4)`), vẽ lại với độ mờ giảm dần ($\alpha \in \{0.35, 0.22, 0.12, 0.05\}$) trước khi vẽ nhân vật chính.
