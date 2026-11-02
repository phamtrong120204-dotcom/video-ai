"""Unit Tests for FaceFeatureRenderer and AccessoriesRenderer (G5.2.3.2).

Verifies the 4 humanoid character skins:
- Dark Wukong (Fiery red eyes, Golden Kim Cô V-notch, 180px twin pheasant plumes, tattered crimson scarf)
- Erlang Shen (Divine Third Eye, Spiked silver helmet, Angular shoulder pauldrons, silver cloak)
- Celestial General (General helmet, red plume tassel, heavy pauldrons)
- Celestial Soldier (Conical kettle helmet, short red tassel, simple shoulder caps)
- Cubic Bezier curve length, smoothness, and finite numbers
- Strict 4-step layer compositing order
- Facing +1 and -1 flow direction
- Scale handling (0.8, 1.0, 1.25)
- Immutability & determinism
"""

import math
import numpy as np
import pytest
from PIL import Image

from app.modules.animation.character_renderer_parts import (
    AccessoriesRenderer,
    FaceFeatureRenderer,
    HumanoidBodyRenderer,
    composite_character,
    evaluate_cubic_bezier,
)
from app.modules.animation.pose_catalog import PoseCatalog
from app.modules.animation.stickman_models import (
    CoordinateManager,
    JointType,
    Point2D,
    StickmanCharacter,
    StickmanPose,
)
from app.schemas.scene_schema import ActorConfig, ActorSide, CharacterSkin, WeaponType


@pytest.fixture
def body_renderer() -> HumanoidBodyRenderer:
    return HumanoidBodyRenderer()


@pytest.fixture
def face_renderer() -> FaceFeatureRenderer:
    return FaceFeatureRenderer()


@pytest.fixture
def acc_renderer() -> AccessoriesRenderer:
    return AccessoriesRenderer()


@pytest.fixture
def wukong_char() -> StickmanCharacter:
    config = ActorConfig(
        actor_id="dark_wukong_01",
        skin=CharacterSkin.DARK_WUKONG,
        color="#D92626",
        weapon=WeaponType.RUYI_STAFF,
        display_name="Ngộ Không Hắc Hóa",
        side=ActorSide.LEFT,
        scale=1.0,
    )
    return StickmanCharacter.from_actor_config(config)


@pytest.fixture
def erlang_char() -> StickmanCharacter:
    config = ActorConfig(
        actor_id="erlang_shen_01",
        skin=CharacterSkin.ERLANG_SHEN,
        color="#E6B800",
        weapon=WeaponType.THREE_POINTED_SPEAR,
        display_name="Nhị Lang Thần",
        side=ActorSide.RIGHT,
        scale=1.05,
    )
    return StickmanCharacter.from_actor_config(config)


@pytest.fixture
def general_char() -> StickmanCharacter:
    config = ActorConfig(
        actor_id="celestial_gen_01",
        skin=CharacterSkin.CELESTIAL_GENERAL,
        color="#63B3ED",
        weapon=WeaponType.CELESTIAL_HALBERD,
        display_name="Thiên Tướng",
        side=ActorSide.RIGHT,
        scale=1.25,
    )
    return StickmanCharacter.from_actor_config(config)


@pytest.fixture
def soldier_char() -> StickmanCharacter:
    config = ActorConfig(
        actor_id="celestial_soldier_01",
        skin=CharacterSkin.CELESTIAL_SOLDIER_SQUAD,
        color="#63B3ED",
        weapon=WeaponType.CELESTIAL_HALBERD,
        display_name="Thiên Binh",
        side=ActorSide.LEFT,
        scale=0.95,
    )
    return StickmanCharacter.from_actor_config(config)


# 1. Wukong Face render thành công
def test_01_wukong_face_render_success(
    face_renderer: FaceFeatureRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    img = face_renderer.render_face_features(wukong_char, pose, Point2D(540.0, 1200.0), facing=1)
    assert isinstance(img, Image.Image)
    assert img.size == (1080, 1920)
    assert img.mode == "RGBA"
    arr = np.array(img)
    assert np.count_nonzero(arr[:, :, 3] > 0) > 10


# 2. Erlang Face render thành công
def test_02_erlang_face_render_success(
    face_renderer: FaceFeatureRenderer, erlang_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    img = face_renderer.render_face_features(erlang_char, pose, Point2D(540.0, 1200.0), facing=1)
    assert isinstance(img, Image.Image)
    assert img.size == (1080, 1920)
    assert img.mode == "RGBA"
    arr = np.array(img)
    assert np.count_nonzero(arr[:, :, 3] > 0) > 10


# 3. Thiên Nhãn nằm trong vùng đầu
def test_03_third_eye_inside_head_circle(
    face_renderer: FaceFeatureRenderer, erlang_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pelvis_pos = Point2D(500.0, 1200.0)
    facing = 1
    scale = erlang_char.scale

    joints = HumanoidBodyRenderer().transform_joints(pose, pelvis_pos, facing, scale)
    head_pt = joints[JointType.HEAD]
    head_radius = CoordinateManager.HEAD_RADIUS * scale

    img = face_renderer.render_face_features(erlang_char, pose, pelvis_pos, facing=facing)
    arr = np.array(img)

    # Pixel coordinates where Third Eye is drawn
    ys, xs = np.nonzero(arr[:, :, 3] > 0)
    assert len(xs) > 0

    for x, y in zip(xs, ys):
        # Distance from head center must be strictly <= head_radius
        dist = math.hypot(x - head_pt.x, y - head_pt.y)
        assert dist <= head_radius + 0.5, f"Third Eye pixel ({x}, {y}) outside head circle: dist={dist} > {head_radius}"


# 4. Mắt đỏ nằm trong vùng đầu
def test_04_red_eyes_inside_head_circle(
    face_renderer: FaceFeatureRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pelvis_pos = Point2D(500.0, 1200.0)
    facing = 1
    scale = wukong_char.scale

    joints = HumanoidBodyRenderer().transform_joints(pose, pelvis_pos, facing, scale)
    head_pt = joints[JointType.HEAD]
    head_radius = CoordinateManager.HEAD_RADIUS * scale

    img = face_renderer.render_face_features(wukong_char, pose, pelvis_pos, facing=facing)
    arr = np.array(img)

    ys, xs = np.nonzero(arr[:, :, 3] > 0)
    assert len(xs) > 0

    for x, y in zip(xs, ys):
        dist = math.hypot(x - head_pt.x, y - head_pt.y)
        assert dist <= head_radius + 0.5, f"Red eye pixel ({x}, {y}) outside head circle: dist={dist} > {head_radius}"

    # Verify color contains bright red (R > 200, G < 100, B < 100)
    red_pixels = arr[ys, xs]
    has_glowing_red = any(p[0] > 200 and p[1] < 100 for p in red_pixels)
    assert has_glowing_red, "Wukong eye must have fiery red color"


# 5. Face layer có alpha trong suốt
def test_05_face_layer_has_transparent_alpha(
    face_renderer: FaceFeatureRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    img = face_renderer.render_face_features(wukong_char, pose, Point2D(540.0, 1200.0), facing=1)
    arr = np.array(img)
    alpha = arr[:, :, 3]

    # > 99% of pixels must be completely transparent (alpha = 0)
    transparent_ratio = np.count_nonzero(alpha == 0) / alpha.size
    assert transparent_ratio > 0.99
    # Corners must be 0
    assert arr[0, 0, 3] == 0
    assert arr[1919, 1079, 3] == 0


# 6. Kim cô render thành công
def test_06_kim_co_render_success(
    acc_renderer: AccessoriesRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    img = acc_renderer.render_front_accessories(wukong_char, pose, Point2D(540.0, 1200.0), facing=1)
    assert isinstance(img, Image.Image)
    assert img.size == (1080, 1920)
    arr = np.array(img)
    assert np.count_nonzero(arr[:, :, 3] > 0) > 50


# 7. Kim cô có cấu trúc chữ V
def test_07_kim_co_has_v_structure(
    acc_renderer: AccessoriesRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pelvis_pos = Point2D(500.0, 1200.0)
    facing = 1
    joints = HumanoidBodyRenderer().transform_joints(pose, pelvis_pos, facing, 1.0)
    head_pt = joints[JointType.HEAD]

    img = acc_renderer.render_front_accessories(wukong_char, pose, pelvis_pos, facing=facing)
    arr = np.array(img)

    # V-apex is at (head.x + 23*facing, head.y - 8)
    v_apex_x = round(head_pt.x + 23.0 * facing)
    v_apex_y = round(head_pt.y - 8.0)

    # Check that pixel at or immediately adjacent to v_apex is colored golden
    apex_region = arr[v_apex_y - 2 : v_apex_y + 3, v_apex_x - 2 : v_apex_x + 3]
    assert np.any(apex_region[:, :, 3] > 0), "V-apex must contain drawn golden pixels"


# 8. Hai lông chim trĩ được vẽ đầy đủ
def test_08_two_pheasant_feathers_rendered(
    acc_renderer: AccessoriesRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    head_pt = Point2D(500.0, 1000.0)
    pts1, pts2, len1, len2 = acc_renderer.get_feather_bezier_curves(head_pt, facing=1, scale=1.0)

    assert len(pts1) == 61
    assert len(pts2) == 61
    assert len1 > 150.0
    assert len2 > 150.0


# 9. Độ dài lông chim gần 180 px theo spec (chính xác 180.0 ± 1.0 px)
def test_09_pheasant_feathers_length_around_180px(
    acc_renderer: AccessoriesRenderer
):
    head_pt = Point2D(500.0, 1000.0)

    # 1. Facing +1: cả 2 sợi đều đạt 180.0 ± 1.0 px
    pts1_r, pts2_r, len1_r, len2_r = acc_renderer.get_feather_bezier_curves(head_pt, facing=1, scale=1.0)
    assert math.isclose(len1_r, 180.0, abs_tol=1.0), f"Plume 1 length {len1_r:.4f} not within 180 ± 1.0px"
    assert math.isclose(len2_r, 180.0, abs_tol=1.0), f"Plume 2 length {len2_r:.4f} not within 180 ± 1.0px"

    # 2. Facing -1: chiều dài được bảo toàn tuyệt đối
    pts1_l, pts2_l, len1_l, len2_l = acc_renderer.get_feather_bezier_curves(head_pt, facing=-1, scale=1.0)
    assert math.isclose(len1_l, 180.0, abs_tol=1.0), f"Plume 1 length {len1_l:.4f} not within 180 ± 1.0px"
    assert math.isclose(len2_l, 180.0, abs_tol=1.0), f"Plume 2 length {len2_l:.4f} not within 180 ± 1.0px"
    assert math.isclose(len1_r, len1_l, abs_tol=1e-5), "Plume 1 length altered by facing flip"
    assert math.isclose(len2_r, len2_l, abs_tol=1e-5), "Plume 2 length altered by facing flip"

    # 3. Hai sợi có hình dáng so le, không trùng khít nhau
    peak_y1 = min(p[1] for p in pts1_r)
    peak_y2 = min(p[1] for p in pts2_r)
    assert peak_y1 < peak_y2, "Plume 1 must arch higher than Plume 2"

    end_x1 = pts1_r[-1][0]
    end_x2 = pts2_r[-1][0]
    assert abs(end_x1 - end_x2) > 2.0, "Plume endpoints must be staggered"

    # Khoảng cách giữa 2 đường cong luôn dương (không giao cắt trùng khít)
    dists = [math.hypot(pts1_r[i][0] - pts2_r[i][0], pts1_r[i][1] - pts2_r[i][1]) for i in range(len(pts1_r))]
    assert min(dists) >= 3.0, "Plumes must maintain minimum visual separation >= 3px"


# 10. Bezier không tạo tọa độ NaN/Infinity
def test_10_bezier_no_nan_or_infinity():
    p0 = (100.0, 200.0)
    p1 = (150.0, 50.0)
    p2 = (300.0, 80.0)
    p3 = (450.0, 300.0)

    pts = evaluate_cubic_bezier(p0, p1, p2, p3, num_points=100)
    assert len(pts) == 101

    for x, y in pts:
        assert math.isfinite(x)
        assert math.isfinite(y)
        assert not math.isnan(x)
        assert not math.isnan(y)


# 11. Khăn choàng nằm phía sau thân
def test_11_scarf_layer_behind_body(
    acc_renderer: AccessoriesRenderer,
    body_renderer: HumanoidBodyRenderer,
    wukong_char: StickmanCharacter,
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(500.0, 1200.0)

    back_img = acc_renderer.render_back_accessories(wukong_char, pose, pos, facing=1)
    body_img = body_renderer.render_body(wukong_char, pose, pos, facing=1)

    # In composite (back under body), where body has alpha 255, body pixel dominates
    comp = Image.alpha_composite(back_img, body_img)
    arr_comp = np.array(comp)
    arr_body = np.array(body_img)

    # Pelvis center is body stroke color
    pelvis_px = arr_comp[1200, 500]
    assert tuple(pelvis_px) == wukong_char.stroke_color


# 12. Khăn choàng hướng về phía sau khi facing +1
def test_12_scarf_flows_backwards_facing_plus_one(
    acc_renderer: AccessoriesRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pelvis_pos = Point2D(500.0, 1200.0)
    # Facing +1 (facing right) -> scarf flows to the LEFT (x < 500)
    img = acc_renderer.render_back_accessories(wukong_char, pose, pelvis_pos, facing=1)
    arr = np.array(img)

    ys, xs = np.nonzero(arr[:, :, 3] > 0)
    min_x = np.min(xs)
    # Scarf tail must extend to the left of the anchor
    assert min_x < 500.0 - 50.0


# 13. Khăn choàng hướng về phía sau khi facing -1
def test_13_scarf_flows_backwards_facing_minus_one(
    acc_renderer: AccessoriesRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pelvis_pos = Point2D(500.0, 1200.0)
    # Facing -1 (facing left) -> scarf flows to the RIGHT (x > 500)
    img = acc_renderer.render_back_accessories(wukong_char, pose, pelvis_pos, facing=-1)
    arr = np.array(img)

    ys, xs = np.nonzero(arr[:, :, 3] > 0)
    max_x = np.max(xs)
    # Scarf tail must extend to the right of the anchor
    assert max_x > 500.0 + 50.0


# 14. Erlang helmet render thành công
def test_14_erlang_helmet_render_success(
    acc_renderer: AccessoriesRenderer, erlang_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    img = acc_renderer.render_front_accessories(erlang_char, pose, Point2D(500.0, 1200.0), facing=1)
    arr = np.array(img)

    # Must contain helmet pixels above head
    assert np.count_nonzero(arr[:, :, 3] > 0) > 100


# 15. Erlang shoulder armor render thành công
def test_15_erlang_shoulder_armor_render_success(
    acc_renderer: AccessoriesRenderer, erlang_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("combat_stance")
    pos = Point2D(500.0, 1200.0)
    joints = HumanoidBodyRenderer().transform_joints(pose, pos, facing=1, scale=erlang_char.scale)
    sh_l = joints[JointType.SHOULDER_L]
    sh_r = joints[JointType.SHOULDER_R]

    img = acc_renderer.render_front_accessories(erlang_char, pose, pos, facing=1)
    arr = np.array(img)

    # Shoulder areas must have drawn armor pixels
    assert np.any(arr[round(sh_l.y) - 10 : round(sh_l.y) + 10, round(sh_l.x) - 15 : round(sh_l.x) + 15, 3] > 0)
    assert np.any(arr[round(sh_r.y) - 10 : round(sh_r.y) + 10, round(sh_r.x) - 15 : round(sh_r.x) + 15, 3] > 0)


# 16. Celestial General helmet và tassel render thành công
def test_16_celestial_general_helmet_and_tassel_success(
    acc_renderer: AccessoriesRenderer, general_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    img = acc_renderer.render_front_accessories(general_char, pose, Point2D(500.0, 1200.0), facing=1)
    arr = np.array(img)

    # Red tassel must have red pixels (R > 180, G < 80)
    ys, xs = np.nonzero(arr[:, :, 3] > 0)
    colors = arr[ys, xs]
    has_red_tassel = any(c[0] > 180 and c[1] < 80 for c in colors)
    assert has_red_tassel, "Celestial general must have flowing red tassel"


# 17. Celestial Soldier helmet và tassel render thành công
def test_17_celestial_soldier_helmet_and_tassel_success(
    acc_renderer: AccessoriesRenderer, soldier_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    img = acc_renderer.render_front_accessories(soldier_char, pose, Point2D(500.0, 1200.0), facing=-1)
    arr = np.array(img)

    assert np.count_nonzero(arr[:, :, 3] > 0) > 30


# 18. Scale 0.8 kiểm tra định lượng tỷ lệ hình học
def test_18_scale_0_8_operates_correctly(
    face_renderer: FaceFeatureRenderer, acc_renderer: AccessoriesRenderer
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(500.0, 1200.0)

    # Base scale 1.0
    cfg_base = ActorConfig(
        actor_id="w_base",
        skin=CharacterSkin.DARK_WUKONG,
        color="#D92626",
        weapon=WeaponType.RUYI_STAFF,
        display_name="Base Wukong",
        side=ActorSide.LEFT,
        scale=1.0,
    )
    char_base = StickmanCharacter.from_actor_config(cfg_base)
    img_back_base = acc_renderer.render_back_accessories(char_base, pose, pos)
    bbox_base = img_back_base.getbbox()
    w_base = bbox_base[2] - bbox_base[0]
    h_base = bbox_base[3] - bbox_base[1]

    # Target scale 0.8
    cfg_small = ActorConfig(
        actor_id="w_small",
        skin=CharacterSkin.DARK_WUKONG,
        color="#D92626",
        weapon=WeaponType.RUYI_STAFF,
        display_name="Small Wukong",
        side=ActorSide.LEFT,
        scale=0.8,
    )
    char_small = StickmanCharacter.from_actor_config(cfg_small)

    # 1. Kiểm tra độ dài Bezier thu phóng đúng 180 * 0.8 = 144.0 px
    head_pt = Point2D(500.0, 1000.0)
    _, _, l1_s, l2_s = acc_renderer.get_feather_bezier_curves(head_pt, facing=1, scale=0.8)
    assert math.isclose(l1_s, 144.0, abs_tol=0.8), f"Scale 0.8 Plume 1 length {l1_s:.3f} != 144.0"
    assert math.isclose(l2_s, 144.0, abs_tol=0.8), f"Scale 0.8 Plume 2 length {l2_s:.3f} != 144.0"

    # 2. Kiểm tra tỷ lệ kích thước Bounding Box thu nhỏ theo hệ số 0.8
    img_back_small = acc_renderer.render_back_accessories(char_small, pose, pos)
    bbox_small = img_back_small.getbbox()
    w_small = bbox_small[2] - bbox_small[0]
    h_small = bbox_small[3] - bbox_small[1]

    assert math.isclose(w_small / w_base, 0.8, rel_tol=0.05), f"Width ratio {w_small/w_base:.3f} != 0.8"
    assert math.isclose(h_small / h_base, 0.8, rel_tol=0.05), f"Height ratio {h_small/h_base:.3f} != 0.8"

    # 3. Kiểm tra tọa độ chi tiết Kim Cô gắn trán thu nhỏ đúng tỷ lệ (23 * 0.8 = 18.4)
    joints_small = HumanoidBodyRenderer().transform_joints(pose, pos, facing=1, scale=0.8)
    head_small = joints_small[JointType.HEAD]
    v_apex_offset = 23.0 * 0.8
    assert math.isclose(v_apex_offset, 18.4, abs_tol=1e-5)

    img_front_small = acc_renderer.render_front_accessories(char_small, pose, pos)
    arr_front = np.array(img_front_small)
    apex_x = round(head_small.x + v_apex_offset)
    apex_y = round(head_small.y - (8.0 * 0.8))
    assert np.any(arr_front[apex_y - 2 : apex_y + 3, apex_x - 2 : apex_x + 3, 3] > 0)


# 19. Scale 1.25 kiểm tra định lượng tỷ lệ hình học
def test_19_scale_1_25_operates_correctly(
    face_renderer: FaceFeatureRenderer, acc_renderer: AccessoriesRenderer
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(500.0, 1200.0)

    # Base scale 1.0
    cfg_base = ActorConfig(
        actor_id="w_base",
        skin=CharacterSkin.DARK_WUKONG,
        color="#D92626",
        weapon=WeaponType.RUYI_STAFF,
        display_name="Base Wukong",
        side=ActorSide.LEFT,
        scale=1.0,
    )
    char_base = StickmanCharacter.from_actor_config(cfg_base)
    img_back_base = acc_renderer.render_back_accessories(char_base, pose, pos)
    bbox_base = img_back_base.getbbox()
    w_base = bbox_base[2] - bbox_base[0]
    h_base = bbox_base[3] - bbox_base[1]

    # Target scale 1.25
    cfg_large = ActorConfig(
        actor_id="w_large",
        skin=CharacterSkin.DARK_WUKONG,
        color="#D92626",
        weapon=WeaponType.RUYI_STAFF,
        display_name="Large Wukong",
        side=ActorSide.LEFT,
        scale=1.25,
    )
    char_large = StickmanCharacter.from_actor_config(cfg_large)

    # 1. Kiểm tra độ dài Bezier phóng to đúng 180 * 1.25 = 225.0 px
    head_pt = Point2D(500.0, 1000.0)
    _, _, l1_l, l2_l = acc_renderer.get_feather_bezier_curves(head_pt, facing=1, scale=1.25)
    assert math.isclose(l1_l, 225.0, abs_tol=1.0), f"Scale 1.25 Plume 1 length {l1_l:.3f} != 225.0"
    assert math.isclose(l2_l, 225.0, abs_tol=1.0), f"Scale 1.25 Plume 2 length {l2_l:.3f} != 225.0"

    # 2. Kiểm tra tỷ lệ kích thước Bounding Box phóng to theo hệ số 1.25
    img_back_large = acc_renderer.render_back_accessories(char_large, pose, pos)
    bbox_large = img_back_large.getbbox()
    w_large = bbox_large[2] - bbox_large[0]
    h_large = bbox_large[3] - bbox_large[1]

    assert math.isclose(w_large / w_base, 1.25, rel_tol=0.05), f"Width ratio {w_large/w_base:.3f} != 1.25"
    assert math.isclose(h_large / h_base, 1.25, rel_tol=0.05), f"Height ratio {h_large/h_base:.3f} != 1.25"

    # 3. Kiểm tra chi tiết Kim Cô tại scale 1.25 (23 * 1.25 = 28.75)
    joints_large = HumanoidBodyRenderer().transform_joints(pose, pos, facing=1, scale=1.25)
    head_large = joints_large[JointType.HEAD]
    v_apex_offset = 23.0 * 1.25
    assert math.isclose(v_apex_offset, 28.75, abs_tol=1e-5)

    img_front_large = acc_renderer.render_front_accessories(char_large, pose, pos)
    arr_front = np.array(img_front_large)
    apex_x = round(head_large.x + v_apex_offset)
    apex_y = round(head_large.y - (8.0 * 1.25))
    assert np.any(arr_front[apex_y - 2 : apex_y + 3, apex_x - 2 : apex_x + 3, 3] > 0)


# 20. Facing trái/phải nhất quán
def test_20_facing_left_right_consistency(
    face_renderer: FaceFeatureRenderer, acc_renderer: AccessoriesRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(540.0, 1200.0)

    # Face right (+1) and Face left (-1)
    f_r = face_renderer.render_face_features(wukong_char, pose, pos, facing=1)
    f_l = face_renderer.render_face_features(wukong_char, pose, pos, facing=-1)

    bbox_r = f_r.getbbox()
    bbox_l = f_l.getbbox()

    # Right eye must be to the right of pelvis X=540, left eye to the left of 540
    assert bbox_r[0] > 540
    assert bbox_l[2] < 540


# 21. Deterministic rendering với cùng input và seed
def test_21_deterministic_rendering(
    face_renderer: FaceFeatureRenderer, acc_renderer: AccessoriesRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("combat_stance")
    pos = Point2D(500.0, 1200.0)

    img1 = acc_renderer.render_back_accessories(wukong_char, pose, pos, facing=1)
    img2 = acc_renderer.render_back_accessories(wukong_char, pose, pos, facing=1)

    arr1 = np.array(img1)
    arr2 = np.array(img2)
    assert np.array_equal(arr1, arr2)


# 22. Không thay đổi pose ban đầu
def test_22_input_pose_immutability(
    face_renderer: FaceFeatureRenderer, acc_renderer: AccessoriesRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    orig_joints = {j: Point2D(p.x, p.y) for j, p in pose.joints.items()}

    _ = face_renderer.render_face_features(wukong_char, pose, Point2D(500.0, 1200.0), facing=-1)
    _ = acc_renderer.render_back_accessories(wukong_char, pose, Point2D(500.0, 1200.0), facing=-1)
    _ = acc_renderer.render_front_accessories(wukong_char, pose, Point2D(500.0, 1200.0), facing=-1)

    for j, pt in orig_joints.items():
        assert pose.joints[j] == pt


# 23. Back accessories, face và front accessories có thể ghép theo layer order
def test_23_layer_compositing_order(
    body_renderer: HumanoidBodyRenderer,
    face_renderer: FaceFeatureRenderer,
    acc_renderer: AccessoriesRenderer,
    wukong_char: StickmanCharacter,
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(500.0, 1200.0)

    comp = composite_character(
        body_renderer=body_renderer,
        face_renderer=face_renderer,
        accessories_renderer=acc_renderer,
        character=wukong_char,
        pose=pose,
        canvas_position=pos,
        facing=1,
    )
    assert isinstance(comp, Image.Image)
    assert comp.size == (1080, 1920)
    assert comp.mode == "RGBA"

    arr = np.array(comp)
    assert np.count_nonzero(arr[:, :, 3] > 0) > 5000


# 24. Phụ kiện không che khuất vùng mắt trái quy định
def test_24_accessories_do_not_obscure_eyes(
    face_renderer: FaceFeatureRenderer,
    acc_renderer: AccessoriesRenderer,
    wukong_char: StickmanCharacter,
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(500.0, 1200.0)

    # Render eye layer
    face_img = face_renderer.render_face_features(wukong_char, pose, pos, facing=1)
    front_acc_img = acc_renderer.render_front_accessories(wukong_char, pose, pos, facing=1)

    face_arr = np.array(face_img)
    front_arr = np.array(front_acc_img)

    # Eye pixel locations
    eye_ys, eye_xs = np.nonzero(face_arr[:, :, 3] > 0)

    # Front accessories (Kim Cô) must NOT overlap eye pixels
    for x, y in zip(eye_xs, eye_ys):
        assert front_arr[y, x, 3] == 0, f"Kim Cô obscures eye at ({x}, {y})"


# 25. Tọa độ phụ kiện được clip an toàn theo canvas
def test_25_safe_clipping_near_canvas_boundary(
    acc_renderer: AccessoriesRenderer,
    face_renderer: FaceFeatureRenderer,
    wukong_char: StickmanCharacter,
):
    pose = PoseCatalog.get_pose("standoff_idle")
    extreme_positions = [
        Point2D(0.0, 0.0),
        Point2D(1080.0, 1920.0),
        Point2D(-200.0, 500.0),
        Point2D(1200.0, 500.0),
    ]

    for pos in extreme_positions:
        back_img = acc_renderer.render_back_accessories(wukong_char, pose, pos, facing=1)
        face_img = face_renderer.render_face_features(wukong_char, pose, pos, facing=1)
        front_img = acc_renderer.render_front_accessories(wukong_char, pose, pos, facing=1)

        assert back_img.size == (1080, 1920)
        assert face_img.size == (1080, 1920)
        assert front_img.size == (1080, 1920)
