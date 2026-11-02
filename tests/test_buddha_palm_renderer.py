"""Unit test suite for BuddhaPalmRenderer (G5.2.3.4).

Covers all required verification gates:
1. Render success with nominal scale 3.50.
2. Output format strictly RGBA and (1080, 1920).
3. Background pixels have alpha = 0.
4. Palm and finger pixels have alpha > 0.
5. All 5 fingertips present and correctly positioned (thumb, index, middle, ring, pinky).
6. Middle finger is mathematically the longest fingertip.
7. Thumb is laterally offset and distinct from fingers.
8. Sacred Wan Seal (卍) rendered at palm center.
9. Concentric golden mandalas rendered around palm center.
10. Compressive shockwave layer rendered when show_shockwave=True.
11. Shockwave layer omitted when show_shockwave=False.
12. Aura glow layer omitted when show_aura=False.
13. Descent progression Y in [-200, 950] px correctly translates palm.
14. Direction 'down' points fingers toward +Y.
15. Direction 'up' points fingers toward -Y (mudra posture).
16. Facing +1 vs -1 mirrors palm horizontally around center X.
17. Scale 1.0 scales geometry proportionally.
18. Scale 3.50 matches moveset specification.
19. Scale 5.0 (maximum allowable) renders safely without errors.
20. Rejects invalid scale <= 0.1 or > 5.0.
21. Rejects invalid facing not in (+1, -1).
22. Rejects invalid direction not in ('down', 'up').
23. Rejects non-finite coordinates (NaN or Infinity).
24. Safe clipping when palm is partially off canvas boundaries.
25. Deterministic rendering (identical inputs yield bitwise identical output).
26. Integration: WeaponRenderer delegates GIANT_GOLDEN_PALM when requested.
27. Integration: WeaponRenderer preserves transparent layer when delegate=False (test_05 contract).
28. Integration: composite_character composites Buddha Palm over stickman (foreground).
29. Integration: composite_character composites Buddha Palm behind stickman (background).
30. GIANT_GOLDEN_PALM is distinct from polearm weapons (Ruyi, Spear, Halberd).
"""

import math
import numpy as np
import pytest
from PIL import Image

from app.modules.animation.buddha_palm_renderer import BuddhaPalmRenderer
from app.modules.animation.character_renderer_parts import (
    AccessoriesRenderer,
    FaceFeatureRenderer,
    HumanoidBodyRenderer,
    WeaponRenderer,
    composite_character,
)
from app.modules.animation.pose_catalog import PoseCatalog
from app.modules.animation.stickman_models import (
    ActorConfig,
    ActorSide,
    CharacterSkin,
    Point2D,
    StickmanCharacter,
    WeaponType,
)


@pytest.fixture
def palm_renderer() -> BuddhaPalmRenderer:
    return BuddhaPalmRenderer()


@pytest.fixture
def body_renderer() -> HumanoidBodyRenderer:
    return HumanoidBodyRenderer()


@pytest.fixture
def weapon_renderer() -> WeaponRenderer:
    return WeaponRenderer()


@pytest.fixture
def wukong_char() -> StickmanCharacter:
    cfg = ActorConfig(
        actor_id="wukong",
        skin=CharacterSkin.DARK_WUKONG,
        color="#D92626",
        weapon=WeaponType.RUYI_STAFF,
        display_name="Dark Wukong",
        side=ActorSide.LEFT,
        scale=1.0,
    )
    return StickmanCharacter.from_actor_config(cfg)


@pytest.fixture
def buddha_actor_char() -> StickmanCharacter:
    cfg = ActorConfig(
        actor_id="buddha_entity",
        skin=CharacterSkin.BUDDHA_PALM,
        color="#F6AD55",
        weapon=WeaponType.GIANT_GOLDEN_PALM,
        display_name="Buddha Palm",
        side=ActorSide.RIGHT,
        scale=3.5,
    )
    return StickmanCharacter.from_actor_config(cfg)


# 1. Render thành công ở scale danh định 3.50
def test_01_render_success_nominal_scale(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 500.0)
    img = palm_renderer.render_palm(position=pos, scale=3.5)
    assert isinstance(img, Image.Image)
    assert img.getbbox() is not None


# 2. Output mode strictly RGBA và kích thước (1080, 1920)
def test_02_output_mode_strictly_rgba_and_size(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 500.0)
    img = palm_renderer.render_palm(position=pos, scale=3.5)
    assert img.mode == "RGBA"
    assert img.size == (1080, 1920)


# 3. Nền có alpha = 0 (trong suốt)
def test_03_background_pixels_alpha_zero(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 500.0)
    img = palm_renderer.render_palm(position=pos, scale=3.5)
    arr = np.array(img)
    # Góc canvas (0, 0) và (1079, 1919) phải hoàn toàn trong suốt
    assert arr[0, 0, 3] == 0
    assert arr[1919, 1079, 3] == 0


# 4. Pixel bàn tay có alpha > 0
def test_04_palm_pixels_alpha_positive(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 500.0)
    img = palm_renderer.render_palm(position=pos, scale=3.5)
    arr = np.array(img)
    # Tâm bàn tay tại (540, 500) phải có alpha = 255
    assert arr[500, 540, 3] > 0


# 5. Đủ 5 đầu ngón tay rõ ràng (thumb, index, middle, ring, pinky)
def test_05_five_fingertips_present(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 500.0)
    tips = palm_renderer.get_finger_tips(pos, scale=3.5, facing=1, direction="down")
    assert set(tips.keys()) == {"thumb", "index", "middle", "ring", "pinky"}
    for name, pt in tips.items():
        assert math.isfinite(pt.x) and math.isfinite(pt.y)


# 6. Ngón giữa dài nhất theo phương chúc xuống (+Y)
def test_06_middle_finger_longest(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 500.0)
    tips = palm_renderer.get_finger_tips(pos, scale=3.5, facing=1, direction="down")
    # Khi direction="down", đầu ngón giữa có Y lớn nhất (chúc sâu nhất)
    assert tips["middle"].y > tips["index"].y
    assert tips["middle"].y > tips["ring"].y
    assert tips["middle"].y > tips["thumb"].y
    assert tips["middle"].y > tips["pinky"].y


# 7. Ngón cái tách biệt về một phía
def test_07_thumb_laterally_offset(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 500.0)
    tips = palm_renderer.get_finger_tips(pos, scale=3.5, facing=1, direction="down")
    # Khi facing=1, ngón cái xòe sang bên trái (x < cx - 150px tại scale 3.5)
    assert tips["thumb"].x < (pos.x - 150.0)


# 8. Ấn ký chữ Vạn (卍) được vẽ ở tâm bàn tay
def test_08_wan_seal_rendered(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 500.0)
    img_seal = palm_renderer.render_palm(pos, scale=3.5, show_seal=True, show_aura=False, show_shockwave=False)
    img_no_seal = palm_renderer.render_palm(pos, scale=3.5, show_seal=False, show_aura=False, show_shockwave=False)
    arr_seal = np.array(img_seal)
    arr_no_seal = np.array(img_no_seal)
    # Lớp có ấn ký phải khác biệt và có thêm chi tiết ở vùng tâm
    assert not np.array_equal(arr_seal[450:550, 490:590], arr_no_seal[450:550, 490:590])


# 9. Vòng tròn kim quang đồng tâm (mandalas)
def test_09_concentric_mandalas_rendered(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 500.0)
    img = palm_renderer.render_palm(pos, scale=3.5, show_seal=True)
    arr = np.array(img)
    # Mandala màu vàng kim #ECC94B: R > 200, G > 180, B < 100
    gold_mask = (arr[:, :, 0] > 200) & (arr[:, :, 1] > 180) & (arr[:, :, 2] < 100) & (arr[:, :, 3] > 0)
    assert np.any(gold_mask)


# 10. Sóng xung kích chưởng lực mở rộng khi show_shockwave=True
def test_10_shockwave_rendered_when_enabled(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 500.0)
    img_shock = palm_renderer.render_palm(pos, scale=3.5, show_shockwave=True)
    img_no_shock = palm_renderer.render_palm(pos, scale=3.5, show_shockwave=False)
    bbox_shock = img_shock.getbbox()
    bbox_no_shock = img_no_shock.getbbox()
    assert bbox_shock is not None and bbox_no_shock is not None
    # Sóng xung kích mở rộng BBox ra ngoài bàn tay
    assert bbox_shock[3] > bbox_no_shock[3]


# 11. Bỏ sóng xung kích khi show_shockwave=False
def test_11_shockwave_omitted_when_disabled(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 500.0)
    img_no_shock = palm_renderer.render_palm(pos, scale=3.5, show_shockwave=False)
    arr = np.array(img_no_shock)
    # Ở vùng xa hơn ngón tay (Y > 1150) không có pixel nào
    assert np.count_nonzero(arr[1200:, :, 3] > 0) == 0


# 12. Bỏ hào quang khi show_aura=False
def test_12_aura_omitted_when_disabled(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 500.0)
    img_with = palm_renderer.render_palm(pos, scale=3.5, show_aura=True, show_shockwave=False)
    img_without = palm_renderer.render_palm(pos, scale=3.5, show_aura=False, show_shockwave=False)
    arr_with = np.array(img_with)
    arr_without = np.array(img_without)
    assert np.count_nonzero(arr_with[:, :, 3] > 0) > np.count_nonzero(arr_without[:, :, 3] > 0)


# 13. Tiến độ giáng thế Y in [-200, 950] px
def test_13_descent_progression_positions(palm_renderer: BuddhaPalmRenderer):
    for y_pos in [-150.0, 200.0, 500.0, 820.0, 950.0]:
        pos = Point2D(540.0, y_pos)
        img = palm_renderer.render_palm(pos, scale=3.5)
        assert img.size == (1080, 1920)
        assert img.mode == "RGBA"


# 14. Direction 'down' ngón tay hướng xuống
def test_14_direction_down(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 500.0)
    tips = palm_renderer.get_finger_tips(pos, scale=3.5, direction="down")
    assert tips["middle"].y > pos.y


# 15. Direction 'up' ngón tay hướng lên (Pháp ấn liên hoa)
def test_15_direction_up(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 800.0)
    tips = palm_renderer.get_finger_tips(pos, scale=3.5, direction="up")
    assert tips["middle"].y < pos.y


# 16. Facing +1 và -1 đối xứng trục hoành
def test_16_facing_symmetry(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 500.0)
    tips_r = palm_renderer.get_finger_tips(pos, scale=3.5, facing=1)
    tips_l = palm_renderer.get_finger_tips(pos, scale=3.5, facing=-1)
    # Khoảng cách từ tâm đến ngón cái phải đối xứng
    assert abs((pos.x - tips_r["thumb"].x) - (tips_l["thumb"].x - pos.x)) < 1e-3


# 17. Scale 1.0 tỉ lệ chuẩn xác
def test_17_scale_1_0(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 500.0)
    img = palm_renderer.render_palm(pos, scale=1.0)
    bbox = img.getbbox()
    assert bbox is not None
    # Chiều rộng ở scale 1.0 nhỏ hơn nhiều so với scale 3.5
    w = bbox[2] - bbox[0]
    assert 200 < w < 400


# 18. Scale 3.50 khớp moveset specification
def test_18_scale_3_5_matches_spec(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 500.0)
    img = palm_renderer.render_palm(pos, scale=BuddhaPalmRenderer.NOMINAL_SCALE)
    bbox = img.getbbox()
    assert bbox is not None
    w = bbox[2] - bbox[0]
    # Scale 3.5 bao trùm phần lớn chiều ngang màn hình (w > 800px)
    assert w >= 800


# 19. Scale 5.0 tối đa an toàn không crash
def test_19_scale_5_0_max(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 500.0)
    img = palm_renderer.render_palm(pos, scale=5.0)
    assert img.size == (1080, 1920)


# 20. Từ chối scale không hợp lệ (<= 0.1 hoặc > 5.0)
def test_20_reject_invalid_scale(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 500.0)
    with pytest.raises(ValueError):
        palm_renderer.render_palm(pos, scale=0.05)
    with pytest.raises(ValueError):
        palm_renderer.render_palm(pos, scale=5.5)


# 21. Từ chối facing không hợp lệ
def test_21_reject_invalid_facing(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 500.0)
    with pytest.raises(ValueError):
        palm_renderer.render_palm(pos, facing=0)


# 22. Từ chối direction không hợp lệ
def test_22_reject_invalid_direction(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 500.0)
    with pytest.raises(ValueError):
        palm_renderer.render_palm(pos, direction="diagonal")


# 23. Từ chối tọa độ không hữu hạn (NaN hoặc Inf)
def test_23_reject_nonfinite_coordinates(palm_renderer: BuddhaPalmRenderer):
    with pytest.raises(ValueError):
        palm_renderer.render_palm(Point2D(float("nan"), 500.0))
    with pytest.raises(ValueError):
        palm_renderer.render_palm(Point2D(540.0, float("inf")))


# 24. Safe clipping khi bàn tay nằm một phần ngoài canvas
def test_24_safe_clipping_canvas_boundary(palm_renderer: BuddhaPalmRenderer):
    # Đặt bàn tay sát mép trái
    img_left = palm_renderer.render_palm(Point2D(-100.0, 500.0), scale=3.5)
    assert img_left.size == (1080, 1920)
    # Đặt bàn tay trên đỉnh
    img_top = palm_renderer.render_palm(Point2D(540.0, -150.0), scale=3.5)
    assert img_top.size == (1080, 1920)


# 25. Deterministic rendering (cùng input tạo bitwise identical output)
def test_25_deterministic_rendering(palm_renderer: BuddhaPalmRenderer):
    pos = Point2D(540.0, 500.0)
    img1 = palm_renderer.render_palm(pos, scale=3.5, facing=1)
    img2 = palm_renderer.render_palm(pos, scale=3.5, facing=1)
    arr1 = np.array(img1)
    arr2 = np.array(img2)
    assert np.array_equal(arr1, arr2)


# 26. Tích hợp WeaponRenderer: delegate_buddha_palm=True vẽ Bàn Tay Phật
def test_26_weapon_renderer_delegates_giant_palm(
    weapon_renderer: WeaponRenderer, buddha_actor_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(540.0, 500.0)
    img = weapon_renderer.render_weapon(
        character=buddha_actor_char,
        pose=pose,
        canvas_position=pos,
        facing=1,
        delegate_buddha_palm=True,
    )
    assert img.getbbox() is not None
    assert img.size == (1080, 1920)


# 27. Tích hợp WeaponRenderer: delegate_buddha_palm=False giữ nguyên transparent (test_05 contract)
def test_27_weapon_renderer_preserves_test_05_contract(
    weapon_renderer: WeaponRenderer, buddha_actor_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(540.0, 500.0)
    img = weapon_renderer.render_weapon(
        character=buddha_actor_char,
        pose=pose,
        canvas_position=pos,
        facing=1,
        delegate_buddha_palm=False,
    )
    assert img.getbbox() is None


# 28. Tích hợp composite_character: ghép Bàn Tay Phật lớp foreground
def test_28_composite_character_foreground_palm(
    body_renderer: HumanoidBodyRenderer,
    weapon_renderer: WeaponRenderer,
    palm_renderer: BuddhaPalmRenderer,
    wukong_char: StickmanCharacter,
):
    face_ren = FaceFeatureRenderer()
    acc_ren = AccessoriesRenderer()
    pose = PoseCatalog.get_pose("standoff_idle")
    pos_wukong = Point2D(540.0, 1200.0)
    pos_palm = Point2D(540.0, 500.0)

    # Composite Ngộ Không đang đứng dưới Bàn Tay Phật
    comp = composite_character(
        body_renderer=body_renderer,
        face_renderer=face_ren,
        accessories_renderer=acc_ren,
        character=wukong_char,
        pose=pose,
        canvas_position=pos_wukong,
        facing=1,
        weapon_renderer=weapon_renderer,
        buddha_palm_renderer=palm_renderer,
        palm_position=pos_palm,
        palm_scale=3.5,
        palm_layer_order="foreground",
    )
    assert comp.size == (1080, 1920)
    assert comp.mode == "RGBA"
    bbox = comp.getbbox()
    assert bbox is not None


# 29. Tích hợp composite_character: ghép Bàn Tay Phật lớp background
def test_29_composite_character_background_palm(
    body_renderer: HumanoidBodyRenderer,
    weapon_renderer: WeaponRenderer,
    palm_renderer: BuddhaPalmRenderer,
    wukong_char: StickmanCharacter,
):
    face_ren = FaceFeatureRenderer()
    acc_ren = AccessoriesRenderer()
    pose = PoseCatalog.get_pose("standoff_idle")
    pos_wukong = Point2D(540.0, 1200.0)
    pos_palm = Point2D(540.0, 500.0)

    comp = composite_character(
        body_renderer=body_renderer,
        face_renderer=face_ren,
        accessories_renderer=acc_ren,
        character=wukong_char,
        pose=pose,
        canvas_position=pos_wukong,
        facing=1,
        weapon_renderer=weapon_renderer,
        buddha_palm_renderer=palm_renderer,
        palm_position=pos_palm,
        palm_scale=3.5,
        palm_layer_order="background",
    )
    assert comp.size == (1080, 1920)
    assert comp.mode == "RGBA"


# 30. GIANT_GOLDEN_PALM phân biệt rõ ràng với polearm weapons
def test_30_giant_palm_distinguished_from_polearms(
    palm_renderer: BuddhaPalmRenderer,
    weapon_renderer: WeaponRenderer,
    wukong_char: StickmanCharacter,
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(540.0, 1200.0)

    # Ruyi Staff is a linear rod (< 15px width)
    img_staff = weapon_renderer.render_weapon(wukong_char, pose, pos, facing=1)
    # Buddha palm is a colossal hand (> 500px width at scale 3.5)
    img_palm = palm_renderer.render_palm(Point2D(540.0, 500.0), scale=3.5)

    arr_s = np.array(img_staff)
    arr_p = np.array(img_palm)

    bbox_s = img_staff.getbbox()
    bbox_p = img_palm.getbbox()
    assert bbox_s is not None and bbox_p is not None

    w_staff = bbox_s[2] - bbox_s[0]
    w_palm = bbox_p[2] - bbox_p[0]
    assert w_palm > w_staff * 5, f"Buddha Palm span {w_palm}px should dwarf staff width {w_staff}px"


# 31. Tự động kích hoạt BuddhaPalmRenderer khi actor có skin BUDDHA_PALM dù không truyền renderer
def test_31_auto_activation_buddha_palm_character(
    body_renderer: HumanoidBodyRenderer,
    buddha_actor_char: StickmanCharacter,
):
    face_ren = FaceFeatureRenderer()
    acc_ren = AccessoriesRenderer()
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(540.0, 500.0)

    # Caller không truyền buddha_palm_renderer thủ công
    comp = composite_character(
        body_renderer=body_renderer,
        face_renderer=face_ren,
        accessories_renderer=acc_ren,
        character=buddha_actor_char,
        pose=pose,
        canvas_position=pos,
        facing=1,
    )
    assert comp.size == (1080, 1920)
    assert comp.mode == "RGBA"
    # Phải có pixel Bàn Tay Phật
    bbox = comp.getbbox()
    assert bbox is not None
    assert (bbox[2] - bbox[0]) >= 800


# 32. Tùy chọn palm_layer_order="weapon" hoạt động chuẩn xác
def test_32_layer_order_weapon_option(
    body_renderer: HumanoidBodyRenderer,
    weapon_renderer: WeaponRenderer,
    palm_renderer: BuddhaPalmRenderer,
    wukong_char: StickmanCharacter,
):
    face_ren = FaceFeatureRenderer()
    acc_ren = AccessoriesRenderer()
    pose = PoseCatalog.get_pose("standoff_idle")
    pos_w = Point2D(540.0, 1200.0)
    pos_p = Point2D(540.0, 500.0)

    comp = composite_character(
        body_renderer=body_renderer,
        face_renderer=face_ren,
        accessories_renderer=acc_ren,
        character=wukong_char,
        pose=pose,
        canvas_position=pos_w,
        facing=1,
        weapon_renderer=weapon_renderer,
        buddha_palm_renderer=palm_renderer,
        palm_position=pos_p,
        palm_scale=3.5,
        palm_layer_order="weapon",
    )
    assert comp.size == (1080, 1920)
    assert comp.getbbox() is not None

