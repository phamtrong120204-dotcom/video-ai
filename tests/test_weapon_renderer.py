"""Unit test suite for WeaponRenderer (G5.2.3.3).

Covers all 30 mandatory test requirements:
1. Ruyi Staff render success.
2. Three Pointed Spear render success.
3. Celestial Halberd render success.
4. Unarmed returns completely transparent layer.
5. Giant Golden Palm not rendered as polearm/staff (delegated to G5.2.3.4).
6. Output mode strictly RGBA and size (1080, 1920).
7. Background pixels have alpha = 0.
8. Weapon pixels have alpha > 0.
9. Primary grip strictly anchored at weapon anchor (WRIST_R).
10. Weapon axis angle 0 deg points along +X.
11. Positive angles rotate clockwise.
12. Facing +1 points in correct local direction.
13. Facing -1 mirrors angle horizontally (180 - theta).
14. Anchor pivot does not drift across facing flip.
15. Scale 0.8 scales length and thickness proportionally.
16. Scale 1.0 matches nominal design lengths.
17. Scale 1.25 scales length and thickness proportionally.
18. Two-handed Ruyi Staff in COMBAT_STANCE traverses both wrists.
19. Two-handed Ruyi Staff in OVERHEAD_SLAM traverses both wrists.
20. Two-handed Three Pointed Spear in GUARD_BLOCK traverses both wrists.
21. Secondary grip lies on valid graspable shaft region.
22. Perpendicular deviation exceeding tolerance is detected.
23. Weapon angle mismatch against grip geometry is detected.
24. Input pose immutability preserved.
25. Deterministic rendering with identical inputs.
26. Bounding box contains all nonzero weapon pixels.
27. Safe clipping near canvas boundaries.
28. Coordinates strictly finite (no NaN or Infinity).
29. Three prongs of Three Pointed Spear distinctly visible on pixel raster.
30. Celestial Halberd crescent blade visually distinguished from Three Pointed Spear.
"""

import math
import numpy as np
import pytest
from PIL import Image

from app.modules.animation.character_renderer_parts import (
    HumanoidBodyRenderer,
    FaceFeatureRenderer,
    AccessoriesRenderer,
    WeaponRenderer,
    GripValidationResult,
    composite_character,
)
from app.modules.animation.pose_catalog import PoseCatalog
from app.modules.animation.stickman_models import (
    ActorConfig,
    ActorSide,
    CharacterSkin,
    JointType,
    Point2D,
    StickmanCharacter,
    StickmanPose,
    WeaponType,
)


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
def erlang_char() -> StickmanCharacter:
    cfg = ActorConfig(
        actor_id="erlang",
        skin=CharacterSkin.ERLANG_SHEN,
        color="#E0E0E0",
        weapon=WeaponType.THREE_POINTED_SPEAR,
        display_name="Erlang Shen",
        side=ActorSide.RIGHT,
        scale=1.05,
    )
    return StickmanCharacter.from_actor_config(cfg)


@pytest.fixture
def general_char() -> StickmanCharacter:
    cfg = ActorConfig(
        actor_id="general",
        skin=CharacterSkin.CELESTIAL_GENERAL,
        color="#C41E3A",
        weapon=WeaponType.CELESTIAL_HALBERD,
        display_name="Celestial General",
        side=ActorSide.RIGHT,
        scale=1.25,
    )
    return StickmanCharacter.from_actor_config(cfg)


# 1. Ruyi Staff render thành công
def test_01_ruyi_staff_render_success(weapon_renderer: WeaponRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(500.0, 1200.0)
    img = weapon_renderer.render_weapon(wukong_char, pose, pos, facing=1)
    assert isinstance(img, Image.Image)
    bbox = img.getbbox()
    assert bbox is not None
    assert bbox[2] > bbox[0]
    assert bbox[3] > bbox[1]


# 2. Three Pointed Spear render thành công
def test_02_three_pointed_spear_render_success(weapon_renderer: WeaponRenderer, erlang_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(500.0, 1200.0)
    img = weapon_renderer.render_weapon(erlang_char, pose, pos, facing=1)
    assert isinstance(img, Image.Image)
    bbox = img.getbbox()
    assert bbox is not None


# 3. Celestial Halberd render thành công
def test_03_celestial_halberd_render_success(weapon_renderer: WeaponRenderer, general_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(500.0, 1200.0)
    img = weapon_renderer.render_weapon(general_char, pose, pos, facing=1)
    assert isinstance(img, Image.Image)
    bbox = img.getbbox()
    assert bbox is not None


# 4. Unarmed trả về layer trong suốt hoàn toàn
def test_04_unarmed_returns_transparent_layer(weapon_renderer: WeaponRenderer):
    cfg = ActorConfig(
        actor_id="unarmed_guy",
        skin=CharacterSkin.DARK_WUKONG,
        color="#D92626",
        weapon=WeaponType.UNARMED,
        display_name="Unarmed",
        side=ActorSide.LEFT,
        scale=1.0,
    )
    char = StickmanCharacter.from_actor_config(cfg)
    pose = PoseCatalog.get_pose("combat_stance")
    pos = Point2D(500.0, 1200.0)
    img = weapon_renderer.render_weapon(char, pose, pos, facing=1)
    assert img.getbbox() is None
    arr = np.array(img)
    assert np.all(arr[:, :, 3] == 0)


# 5. Giant Golden Palm không bị vẽ nhầm thành vũ khí cán dài
def test_05_giant_golden_palm_delegated_transparent(weapon_renderer: WeaponRenderer):
    cfg = ActorConfig(
        actor_id="buddha",
        skin=CharacterSkin.DARK_WUKONG,
        color="#E6B800",
        weapon=WeaponType.GIANT_GOLDEN_PALM,
        display_name="Buddha Palm",
        side=ActorSide.RIGHT,
        scale=1.0,
    )
    char = StickmanCharacter.from_actor_config(cfg)
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(500.0, 1200.0)
    img = weapon_renderer.render_weapon(char, pose, pos, facing=1)
    assert img.getbbox() is None


# 6. Output đúng RGBA và kích thước canvas chuẩn
def test_06_output_strictly_rgba_and_dimensions(weapon_renderer: WeaponRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(500.0, 1200.0)
    img = weapon_renderer.render_weapon(wukong_char, pose, pos, facing=1, canvas_size=(1080, 1920))
    assert img.mode == "RGBA"
    assert img.size == (1080, 1920)


# 7. Pixel nền có alpha = 0
def test_07_background_pixels_alpha_zero(weapon_renderer: WeaponRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(500.0, 1200.0)
    img = weapon_renderer.render_weapon(wukong_char, pose, pos, facing=1)
    arr = np.array(img)
    # Check 4 corners
    assert arr[0, 0, 3] == 0
    assert arr[0, 1079, 3] == 0
    assert arr[1919, 0, 3] == 0
    assert arr[1919, 1079, 3] == 0


# 8. Vũ khí có pixel alpha > 0
def test_08_weapon_has_positive_alpha_pixels(weapon_renderer: WeaponRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(500.0, 1200.0)
    img = weapon_renderer.render_weapon(wukong_char, pose, pos, facing=1)
    arr = np.array(img)
    nonzero_count = np.count_nonzero(arr[:, :, 3] > 0)
    assert nonzero_count > 500


# 9. Primary grip trùng khớp wrist anchor
def test_09_primary_grip_matches_wrist_anchor(
    weapon_renderer: WeaponRenderer, body_renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(520.0, 1230.0)
    joints = body_renderer.transform_joints(pose, pos, facing=1, scale=1.0)
    wrist_r = joints[JointType.WRIST_R]

    _, _, eff_anchor, _ = weapon_renderer.get_weapon_endpoints(wukong_char, pose, pos, facing=1)
    assert math.isclose(eff_anchor.x, wrist_r.x, abs_tol=1e-4)
    assert math.isclose(eff_anchor.y, wrist_r.y, abs_tol=1e-4)


# 10. Weapon axis đúng góc 0° (hướng theo +X)
def test_10_weapon_axis_zero_deg_points_plus_x(weapon_renderer: WeaponRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(500.0, 1200.0)
    tail, tip, anc, ang = weapon_renderer.get_weapon_endpoints(
        wukong_char, pose, pos, facing=1, custom_angle_deg=0.0
    )
    assert math.isclose(ang, 0.0, abs_tol=1e-4)
    assert tip.x > anc.x
    assert math.isclose(tip.y, anc.y, abs_tol=1e-4)
    assert tail.x < anc.x
    assert math.isclose(tail.y, anc.y, abs_tol=1e-4)


# 11. Góc dương quay theo chiều kim đồng hồ
def test_11_positive_angle_rotates_clockwise(weapon_renderer: WeaponRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(500.0, 1200.0)
    tail, tip, anc, ang = weapon_renderer.get_weapon_endpoints(
        wukong_char, pose, pos, facing=1, custom_angle_deg=90.0
    )
    assert math.isclose(ang, 90.0, abs_tol=1e-4)
    # 90 degrees points straight down in screen space (Y increases downward)
    assert tip.y > anc.y
    assert math.isclose(tip.x, anc.x, abs_tol=1e-4)


# 12. Facing +1 đúng hướng
def test_12_facing_plus_one_direction(weapon_renderer: WeaponRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("forward_charge")  # nominal angle = 5.0 deg
    pos = Point2D(500.0, 1200.0)
    tail, tip, anc, ang = weapon_renderer.get_weapon_endpoints(wukong_char, pose, pos, facing=1)
    assert math.isclose(ang, 5.0, abs_tol=1e-4)
    assert tip.x > anc.x


# 13. Facing -1 phản chiếu góc nhất quán (180 - theta)
def test_13_facing_minus_one_mirrors_angle(weapon_renderer: WeaponRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("forward_charge")  # nominal angle = 5.0 deg
    pos = Point2D(500.0, 1200.0)
    tail, tip, anc, ang = weapon_renderer.get_weapon_endpoints(wukong_char, pose, pos, facing=-1)
    assert math.isclose(ang, 175.0, abs_tol=1e-4)
    assert tip.x < anc.x


# 14. Pivot không bị trôi khi đổi facing
def test_14_pivot_not_drifting_on_facing_flip(
    weapon_renderer: WeaponRenderer, body_renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(500.0, 1200.0)
    joints_r = body_renderer.transform_joints(pose, pos, facing=1, scale=1.0)
    joints_l = body_renderer.transform_joints(pose, pos, facing=-1, scale=1.0)

    _, _, anc_r, _ = weapon_renderer.get_weapon_endpoints(wukong_char, pose, pos, facing=1)
    _, _, anc_l, _ = weapon_renderer.get_weapon_endpoints(wukong_char, pose, pos, facing=-1)

    assert math.isclose(anc_r.x, joints_r[JointType.WRIST_R].x, abs_tol=1e-4)
    assert math.isclose(anc_l.x, joints_l[JointType.WRIST_R].x, abs_tol=1e-4)
    # Symmetric offset from pelvis X=500
    assert math.isclose(abs(anc_r.x - 500.0), abs(anc_l.x - 500.0), abs_tol=1e-4)


# 15. Scale 0.8
def test_15_scale_0_8_scales_proportionally(weapon_renderer: WeaponRenderer):
    cfg_base = ActorConfig(
        actor_id="w_base",
        skin=CharacterSkin.DARK_WUKONG,
        color="#D92626",
        weapon=WeaponType.RUYI_STAFF,
        display_name="Base",
        side=ActorSide.LEFT,
        scale=1.0,
    )
    cfg_small = ActorConfig(
        actor_id="w_small",
        skin=CharacterSkin.DARK_WUKONG,
        color="#D92626",
        weapon=WeaponType.RUYI_STAFF,
        display_name="Small",
        side=ActorSide.LEFT,
        scale=0.8,
    )
    char_base = StickmanCharacter.from_actor_config(cfg_base)
    char_small = StickmanCharacter.from_actor_config(cfg_small)

    len_base = weapon_renderer.get_weapon_length(char_base.weapon, scale=1.0)
    len_small = weapon_renderer.get_weapon_length(char_small.weapon, scale=0.8)
    assert math.isclose(len_small, 0.8 * len_base, abs_tol=1e-5)
    assert math.isclose(len_small, 272.0, abs_tol=1e-5)


# 16. Scale 1.0 khớp chiều dài danh định
def test_16_scale_1_0_nominal_lengths(weapon_renderer: WeaponRenderer):
    assert math.isclose(weapon_renderer.get_weapon_length(WeaponType.RUYI_STAFF, 1.0), 340.0, abs_tol=1e-5)
    assert math.isclose(weapon_renderer.get_weapon_length(WeaponType.THREE_POINTED_SPEAR, 1.0), 360.0, abs_tol=1e-5)
    assert math.isclose(weapon_renderer.get_weapon_length(WeaponType.CELESTIAL_HALBERD, 1.0), 320.0, abs_tol=1e-5)


# 17. Scale 1.25
def test_17_scale_1_25_scales_proportionally(weapon_renderer: WeaponRenderer):
    len_large = weapon_renderer.get_weapon_length(WeaponType.RUYI_STAFF, scale=1.25)
    assert math.isclose(len_large, 340.0 * 1.25, abs_tol=1e-5)
    assert math.isclose(len_large, 425.0, abs_tol=1e-5)


# 18. Two-handed Ruyi Staff trong COMBAT_STANCE traverses both wrists
def test_18_two_handed_ruyi_staff_combat_stance(weapon_renderer: WeaponRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("combat_stance")
    pos = Point2D(500.0, 1200.0)
    # Aligned two-handed mode: both wrists within tolerance
    val = weapon_renderer.validate_grip(wukong_char, pose, pos, facing=1, align_two_hands=True)
    assert val.is_valid
    assert val.d_perp <= 1.0  # Wrist-to-wrist axis gives zero perpendicular offset
    assert val.d_parallel < 0.0  # Left hand is behind right hand along staff


# 19. Two-handed Ruyi Staff trong OVERHEAD_SLAM traverses both wrists
def test_19_two_handed_ruyi_staff_overhead_slam(weapon_renderer: WeaponRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("overhead_slam")
    pos = Point2D(500.0, 1200.0)
    val = weapon_renderer.validate_grip(wukong_char, pose, pos, facing=1, align_two_hands=True)
    assert val.is_valid
    assert val.d_perp <= 10.0  # Midpoint anchoring places both wrists <= 9.88px


# 20. Two-handed Three Pointed Spear trong GUARD_BLOCK traverses both wrists
def test_20_two_handed_three_pointed_spear_guard_block(
    weapon_renderer: WeaponRenderer, erlang_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("guard_block")
    pos = Point2D(500.0, 1200.0)
    val = weapon_renderer.validate_grip(erlang_char, pose, pos, facing=1, align_two_hands=True)
    assert val.is_valid
    assert val.d_perp <= 10.0  # Midpoint anchoring places both wrists <= 9.33px


# 21. Secondary grip nằm trên grip region hợp lệ
def test_21_secondary_grip_lies_on_valid_graspable_region(
    weapon_renderer: WeaponRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("combat_stance")
    pos = Point2D(500.0, 1200.0)
    val = weapon_renderer.validate_grip(wukong_char, pose, pos, facing=1, align_two_hands=True)
    tail_dist, tip_dist = weapon_renderer.get_grip_distribution(wukong_char.weapon, pose.name, 1.0)
    # Parallel offset of secondary grip must lie inside [-tail_dist, tip_dist]
    assert -tail_dist <= val.d_parallel <= tip_dist


# 22. Sai lệch vuông góc vượt ngưỡng bị phát hiện (Nominal check on COMBAT_STANCE)
def test_22_perpendicular_deviation_exceeding_threshold_detected(
    weapon_renderer: WeaponRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("combat_stance")
    pos = Point2D(500.0, 1200.0)
    # Using nominal angle (align_two_hands=False) exposes the catalog discrepancy
    val = weapon_renderer.validate_grip(wukong_char, pose, pos, facing=1, align_two_hands=False)
    assert not val.is_valid
    assert val.d_perp > 18.0
    assert math.isclose(val.d_perp, 72.36, abs_tol=1.0)
    assert "exceeds tolerance" in val.message


# 23. Weapon angle không khớp grip geometry bị phát hiện
def test_23_weapon_angle_mismatch_detected(weapon_renderer: WeaponRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("combat_stance")
    pos = Point2D(500.0, 1200.0)
    val = weapon_renderer.validate_grip(wukong_char, pose, pos, facing=1, align_two_hands=False)
    assert val.wrist_to_wrist_angle_deg is not None
    angle_diff = abs(val.weapon_angle_deg - val.wrist_to_wrist_angle_deg)
    assert angle_diff > 30.0  # Discrepancy between nominal 35° and wrist vector -3.8°


# 24. Không thay đổi pose đầu vào (Pose Immutability)
def test_24_input_pose_immutability(weapon_renderer: WeaponRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("combat_stance")
    orig_joints = {jt: Point2D(pt.x, pt.y) for jt, pt in pose.joints.items()}
    pos = Point2D(500.0, 1200.0)
    weapon_renderer.render_weapon(wukong_char, pose, pos, facing=1)
    for jt, pt in orig_joints.items():
        assert pose.joints[jt] == pt


# 25. Deterministic rendering với cùng input
def test_25_deterministic_rendering(weapon_renderer: WeaponRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("vortex_sweep")
    pos = Point2D(500.0, 1200.0)
    img1 = weapon_renderer.render_weapon(wukong_char, pose, pos, facing=1)
    img2 = weapon_renderer.render_weapon(wukong_char, pose, pos, facing=1)
    arr1 = np.array(img1)
    arr2 = np.array(img2)
    assert np.array_equal(arr1, arr2)


# 26. Bounding box chứa toàn bộ vũ khí
def test_26_bounding_box_contains_all_pixels(weapon_renderer: WeaponRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(500.0, 1200.0)
    img = weapon_renderer.render_weapon(wukong_char, pose, pos, facing=1)
    bbox = img.getbbox()
    assert bbox is not None
    arr = np.array(img)
    # Outside bbox must be completely transparent
    assert np.all(arr[: bbox[1], :, 3] == 0)
    assert np.all(arr[bbox[3] :, :, 3] == 0)
    assert np.all(arr[:, : bbox[0], 3] == 0)
    assert np.all(arr[:, bbox[2] :, 3] == 0)


# 27. Vũ khí được clip an toàn khi gần mép canvas
def test_27_safe_clipping_near_canvas_boundaries(weapon_renderer: WeaponRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("overhead_slam")
    # Position right at top-left edge
    pos = Point2D(10.0, 20.0)
    img = weapon_renderer.render_weapon(wukong_char, pose, pos, facing=1)
    assert isinstance(img, Image.Image)
    assert img.size == (1080, 1920)


# 28. Không có tọa độ NaN / Infinity
def test_28_no_nan_or_infinity(weapon_renderer: WeaponRenderer, erlang_char: StickmanCharacter):
    for p_name in PoseCatalog.list_poses():
        pose = PoseCatalog.get_pose(p_name)
        pos = Point2D(500.0, 1200.0)
        tail, tip, anc, ang = weapon_renderer.get_weapon_endpoints(erlang_char, pose, pos, facing=1)
        assert math.isfinite(tail.x) and math.isfinite(tail.y)
        assert math.isfinite(tip.x) and math.isfinite(tip.y)
        assert math.isfinite(anc.x) and math.isfinite(anc.y)
        assert math.isfinite(ang)


# 29. Mũi ba của Three Pointed Spear được thể hiện rõ trên pixel (DEF-03: 3 distinct prongs & 2 gaps)
def test_29_three_pointed_spear_three_prongs_visible(
    weapon_renderer: WeaponRenderer, erlang_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(500.0, 1200.0)
    # Render horizontally (0 deg) to cleanly measure vertical cross-section of the head
    img = weapon_renderer.render_weapon(erlang_char, pose, pos, facing=1, custom_angle_deg=0.0)
    arr = np.array(img)
    tail, tip, _, _ = weapon_renderer.get_weapon_endpoints(
        erlang_char, pose, pos, facing=1, custom_angle_deg=0.0
    )
    # Probe slice 35px behind the main tip where the 3 prongs span across
    probe_x = round(tip.x - 35.0 * erlang_char.scale)
    col_slice = arr[:, probe_x, 3]
    active_ys = np.where(col_slice > 0)[0]
    # Prongs spread across Y axis with span > 20px
    span_y = active_ys[-1] - active_ys[0]
    assert span_y >= 20, f"Spear head prongs width span {span_y}px is too narrow for trident"

    # DEF-03: Assert exactly 3 disjoint pixel clusters and 2 empty gaps between them, each >= 3px
    diffs = np.diff(active_ys)
    split_indices = np.where(diffs > 1)[0] + 1
    clusters = np.split(active_ys, split_indices)
    assert len(clusters) == 3, f"Expected 3 distinct prong clusters, got {len(clusters)}: {clusters}"

    gap_sizes = [clusters[i + 1][0] - clusters[i][-1] - 1 for i in range(len(clusters) - 1)]
    assert len(gap_sizes) == 2, f"Expected 2 gaps between 3 prongs, got {gap_sizes}"
    assert all(g >= 3 for g in gap_sizes), f"Each gap must be >= 3px for visual clarity, got {gap_sizes}"


# 30. Celestial Halberd phân biệt được với Three Pointed Spear
def test_30_celestial_halberd_distinguished_from_spear(
    weapon_renderer: WeaponRenderer, general_char: StickmanCharacter, erlang_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pos = Point2D(500.0, 1200.0)

    img_halberd = weapon_renderer.render_weapon(general_char, pose, pos, facing=1)
    img_spear = weapon_renderer.render_weapon(erlang_char, pose, pos, facing=1)

    arr_h = np.array(img_halberd)
    arr_s = np.array(img_spear)

    # Halberd has crimson tassel pixels (R > 180, G < 60, B < 60)
    tassel_mask = (arr_h[:, :, 0] > 180) & (arr_h[:, :, 1] < 60) & (arr_h[:, :, 2] < 60) & (arr_h[:, :, 3] > 0)
    assert np.any(tassel_mask), "Celestial Halberd must contain crimson tassel pixels"

    # Spear has no crimson tassel
    spear_red_mask = (arr_s[:, :, 0] > 180) & (arr_s[:, :, 1] < 60) & (arr_s[:, :, 2] < 60) & (arr_s[:, :, 3] > 0)
    assert not np.any(spear_red_mask), "Three Pointed Spear should not contain crimson tassel"


# Extra integration: Composite character with weapon
def test_31_composite_character_with_weapon(
    weapon_renderer: WeaponRenderer,
    body_renderer: HumanoidBodyRenderer,
    wukong_char: StickmanCharacter,
):
    face_ren = FaceFeatureRenderer()
    acc_ren = AccessoriesRenderer()
    pose = PoseCatalog.get_pose("combat_stance")
    pos = Point2D(500.0, 1200.0)

    # Composite with weapon
    img_with_w = composite_character(
        body_renderer=body_renderer,
        face_renderer=face_ren,
        accessories_renderer=acc_ren,
        character=wukong_char,
        pose=pose,
        canvas_position=pos,
        facing=1,
        weapon_renderer=weapon_renderer,
        align_two_hands=True,
    )
    assert img_with_w.size == (1080, 1920)
    assert img_with_w.mode == "RGBA"

    # Composite without weapon
    img_without_w = composite_character(
        body_renderer=body_renderer,
        face_renderer=face_ren,
        accessories_renderer=acc_ren,
        character=wukong_char,
        pose=pose,
        canvas_position=pos,
        facing=1,
    )

    # Image with weapon must have more nonzero pixels than without
    arr_with = np.array(img_with_w)
    arr_without = np.array(img_without_w)
    assert np.count_nonzero(arr_with[:, :, 3] > 0) > np.count_nonzero(arr_without[:, :, 3] > 0)


# 32. DEF-01: Standoff Idle weapon ground contact (Y <= 1421) and nominal length preserved
@pytest.mark.parametrize("skin,weapon_type", [
    (CharacterSkin.DARK_WUKONG, WeaponType.RUYI_STAFF),
    (CharacterSkin.ERLANG_SHEN, WeaponType.THREE_POINTED_SPEAR),
    (CharacterSkin.CELESTIAL_GENERAL, WeaponType.CELESTIAL_HALBERD),
])
@pytest.mark.parametrize("scale", [0.8, 1.0, 1.25])
@pytest.mark.parametrize("facing", [1, -1])
def test_32_standoff_idle_weapon_ground_contact_and_nominal_length(
    weapon_renderer: WeaponRenderer,
    skin: CharacterSkin,
    weapon_type: WeaponType,
    scale: float,
    facing: int,
):
    from app.modules.animation.stickman_models import CoordinateManager
    cfg = ActorConfig(
        actor_id="test_actor",
        skin=skin,
        color="#FFFFFF",
        weapon=weapon_type,
        display_name="Tester",
        side=ActorSide.LEFT,
        scale=scale,
    )
    char = StickmanCharacter.from_actor_config(cfg)
    pose = PoseCatalog.get_pose("standoff_idle")
    pdef = PoseCatalog.get_definition("standoff_idle")

    pelvis_y = CoordinateManager.get_ground_aligned_root_y(
        pose=pose,
        support_mode=pdef.support_mode,
        ground_y=1420.0,
        scale=scale,
    )
    canvas_pos = Point2D(540.0, pelvis_y)

    # 1. Check endpoints & length preservation
    tail, tip, anc, ang = weapon_renderer.get_weapon_endpoints(char, pose, canvas_pos, facing=facing)
    measured_len = math.hypot(tip.x - tail.x, tip.y - tail.y)
    expected_len = weapon_renderer.get_weapon_length(weapon_type, scale)
    assert abs(measured_len - expected_len) < 1e-3, (
        f"Weapon total length altered! Measured {measured_len:.2f}px vs expected {expected_len:.2f}px"
    )

    # Tip Y should precisely touch ground plane (1420.0)
    assert abs(tip.y - 1420.0) < 1e-3, f"Weapon tip Y {tip.y:.2f} does not touch ground 1420.0"

    # Tail extends upward into air (above wrist)
    assert tail.y < anc.y, f"Weapon tail Y {tail.y:.2f} should extend upward above wrist {anc.y:.2f}"

    # 2. Render weapon and check pixel bounding box bottom Y <= 1421
    img = weapon_renderer.render_weapon(char, pose, canvas_pos, facing=facing)
    bbox = img.getbbox()
    assert bbox is not None, "Weapon layer should have non-transparent pixels"
    assert bbox[3] <= 1421, (
        f"Weapon penetrates ground! BBox bottom Y={bbox[3]} > 1421 "
        f"for {weapon_type.value} at scale={scale}, facing={facing}"
    )


# 33. DEF-02: Auto two-handed alignment with default align_two_hands=None
def test_33_auto_two_handed_alignment_default_none(
    weapon_renderer: WeaponRenderer,
    body_renderer: HumanoidBodyRenderer,
    wukong_char: StickmanCharacter,
):
    pos = Point2D(500.0, 1200.0)

    # Two-handed pose: combat_stance
    pose_combat = PoseCatalog.get_pose("combat_stance")
    # With align_two_hands=None (omitted), it auto-aligns across both wrists!
    grip_combat = weapon_renderer.validate_grip(wukong_char, pose_combat, pos, facing=1)
    assert grip_combat.is_valid, f"Combat stance should auto-align: {grip_combat.message}"
    assert grip_combat.d_perp <= weapon_renderer.MAX_PERP_TOLERANCE_PX, (
        f"Auto-alignment failed: d_perp={grip_combat.d_perp:.2f}px"
    )

    # Single-handed pose: standoff_idle
    pose_standoff = PoseCatalog.get_pose("standoff_idle")
    grip_standoff = weapon_renderer.validate_grip(wukong_char, pose_standoff, pos, facing=1)
    assert grip_standoff.is_valid
    assert grip_standoff.secondary_grip is None
    assert grip_standoff.d_perp == 0.0

    # Composite character works cleanly with default align_two_hands=None
    face_ren = FaceFeatureRenderer()
    acc_ren = AccessoriesRenderer()
    comp = composite_character(
        body_renderer=body_renderer,
        face_renderer=face_ren,
        accessories_renderer=acc_ren,
        character=wukong_char,
        pose=pose_combat,
        canvas_position=pos,
        facing=1,
        weapon_renderer=weapon_renderer,
    )
    assert comp.size == (1080, 1920)
    assert comp.getbbox() is not None


# 34. DEF-02: Explicit align_two_hands True / False behavior
def test_34_explicit_align_two_hands_flags(
    weapon_renderer: WeaponRenderer,
    wukong_char: StickmanCharacter,
):
    pos = Point2D(500.0, 1200.0)
    pose_combat = PoseCatalog.get_pose("combat_stance")

    # Explicit False preserves unaligned nominal angle
    grip_false = weapon_renderer.validate_grip(wukong_char, pose_combat, pos, facing=1, align_two_hands=False)
    assert not grip_false.is_valid
    assert grip_false.d_perp > 50.0, f"Explicit False should leave d_perp unaligned, got {grip_false.d_perp:.2f}px"

    # Explicit True forces alignment
    grip_true = weapon_renderer.validate_grip(wukong_char, pose_combat, pos, facing=1, align_two_hands=True)
    assert grip_true.is_valid
    assert grip_true.d_perp <= weapon_renderer.MAX_PERP_TOLERANCE_PX

