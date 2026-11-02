"""Unit tests for HumanoidBodyRenderer (G5.2.3.1).

Verifies the rendering of the 14-joint, 13-bone stickman body on transparent RGBA canvases:
- Pose drawing (Standoff, Combat, Leap)
- Canvas dimensions and RGBA mode
- Transparent background (alpha = 0) vs solid character (alpha > 0)
- Pelvis canvas coordinate contract
- Facing directions (+1 and -1) and horizontal symmetry
- Scale factors (0.8, 1.0, 1.25)
- Input immutability & deterministic rendering
- Bounding box accuracy covering all non-zero alpha pixels
- Boundary clipping & validation error handling
"""

import math
import numpy as np
import pytest
from PIL import Image

from app.modules.animation.character_renderer_parts import HumanoidBodyRenderer
from app.modules.animation.pose_catalog import PoseCatalog
from app.modules.animation.stickman_models import (
    CoordinateManager,
    JointType,
    Point2D,
    StickmanCharacter,
    StickmanPose,
    SupportMode,
)
from app.schemas.scene_schema import ActorConfig, ActorSide, CharacterSkin, WeaponType


@pytest.fixture
def renderer() -> HumanoidBodyRenderer:
    return HumanoidBodyRenderer()


@pytest.fixture
def wukong_char() -> StickmanCharacter:
    config = ActorConfig(
        actor_id="wukong",
        skin=CharacterSkin.DARK_WUKONG,
        color="#DAA520",
        weapon=WeaponType.RUYI_STAFF,
        display_name="Tôn Ngộ Không",
        side=ActorSide.LEFT,
        scale=1.0,
    )
    return StickmanCharacter.from_actor_config(config)


@pytest.fixture
def erlang_char() -> StickmanCharacter:
    config = ActorConfig(
        actor_id="erlang_shen",
        skin=CharacterSkin.ERLANG_SHEN,
        color="#00F0FF",
        weapon=WeaponType.THREE_POINTED_SPEAR,
        display_name="Dương Tiễn",
        side=ActorSide.RIGHT,
        scale=1.05,
    )
    return StickmanCharacter.from_actor_config(config)


# 1. Render STANDOFF_IDLE successfully
def test_01_render_standoff_idle_successfully(renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("standoff_idle")
    canvas_pos = Point2D(540.0, 1200.0)
    img = renderer.render_body(wukong_char, pose, canvas_pos, facing=1)

    assert isinstance(img, Image.Image)
    assert img.size == (1080, 1920)


# 2. Render COMBAT_STANCE successfully
def test_02_render_combat_stance_successfully(renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("combat_stance")
    canvas_pos = Point2D(540.0, 1200.0)
    img = renderer.render_body(wukong_char, pose, canvas_pos, facing=1)

    assert isinstance(img, Image.Image)
    assert img.size == (1080, 1920)


# 3. Render MID_AIR_LEAP successfully
def test_03_render_mid_air_leap_successfully(renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("mid_air_leap")
    canvas_pos = Point2D(540.0, 800.0)
    img = renderer.render_body(wukong_char, pose, canvas_pos, facing=1)

    assert isinstance(img, Image.Image)
    assert img.size == (1080, 1920)


# 4. Verify output dimensions match requested canvas_size
def test_04_verify_output_dimensions_match_requested(renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("standoff_idle")
    canvas_pos = Point2D(300.0, 400.0)
    custom_size = (600, 800)
    img = renderer.render_body(wukong_char, pose, canvas_pos, facing=1, canvas_size=custom_size)

    assert img.size == custom_size
    assert img.width == 600
    assert img.height == 800


# 5. Verify output mode is strictly 'RGBA'
def test_05_verify_output_mode_strictly_rgba(renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("standoff_idle")
    canvas_pos = Point2D(540.0, 1200.0)
    img = renderer.render_body(wukong_char, pose, canvas_pos, facing=1)

    assert img.mode == "RGBA"


# 6. Verify background pixels have alpha == 0
def test_06_verify_background_pixels_alpha_zero(renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("standoff_idle")
    canvas_pos = Point2D(540.0, 1200.0)
    img = renderer.render_body(wukong_char, pose, canvas_pos, facing=1)

    arr = np.array(img)
    # Corners should be pure transparent background
    assert arr[0, 0, 3] == 0
    assert arr[0, 1079, 3] == 0
    assert arr[1919, 0, 3] == 0
    assert arr[1919, 1079, 3] == 0

    # Total transparent pixels should be majority of canvas (> 90%)
    alpha_channel = arr[:, :, 3]
    transparent_ratio = np.count_nonzero(alpha_channel == 0) / alpha_channel.size
    assert transparent_ratio > 0.90


# 7. Verify character pixels have alpha > 0
def test_07_verify_character_pixels_alpha_positive(renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("standoff_idle")
    canvas_pos = Point2D(540.0, 1200.0)
    img = renderer.render_body(wukong_char, pose, canvas_pos, facing=1)

    arr = np.array(img)
    alpha_channel = arr[:, :, 3]
    non_zero_count = np.count_nonzero(alpha_channel > 0)
    # Humanoid body at 1080x1920 with 13 bones and head circle must draw thousands of pixels
    assert non_zero_count > 5000

    # Color of pelvis center pixel must match character stroke_color
    pelvis_pixel = arr[int(canvas_pos.y), int(canvas_pos.x)]
    assert tuple(pelvis_pixel) == wukong_char.stroke_color


# 8. Verify canvas_position is treated as PELVIS coordinate
def test_08_canvas_position_is_pelvis_coordinate(renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("standoff_idle")
    test_pos = Point2D(432.0, 987.0)

    transformed_joints = renderer.transform_joints(
        pose=pose,
        canvas_position=test_pos,
        facing=1,
        scale=wukong_char.scale,
    )

    pelvis_pt = transformed_joints[JointType.PELVIS]
    assert math.isclose(pelvis_pt.x, test_pos.x, abs_tol=1e-5)
    assert math.isclose(pelvis_pt.y, test_pos.y, abs_tol=1e-5)


# 9. Verify facing +1 (looks right)
def test_09_facing_positive_one_looks_right(renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("forward_charge")
    pelvis_x = 540.0
    joints_right = renderer.transform_joints(
        pose=pose,
        canvas_position=Point2D(pelvis_x, 1000.0),
        facing=1,
        scale=1.0,
    )

    # In forward charge facing right, head/chest/lead wrist should have x > pelvis_x
    head = joints_right[JointType.HEAD]
    assert head.x > pelvis_x


# 10. Verify facing -1 (looks left)
def test_10_facing_negative_one_looks_left(renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("forward_charge")
    pelvis_x = 540.0
    joints_left = renderer.transform_joints(
        pose=pose,
        canvas_position=Point2D(pelvis_x, 1000.0),
        facing=-1,
        scale=1.0,
    )

    # In forward charge facing left, head/chest/lead wrist should have x < pelvis_x
    head = joints_left[JointType.HEAD]
    assert head.x < pelvis_x


# 11. Verify geometric symmetry between facing +1 and -1 around pelvis X
def test_11_geometric_symmetry_between_facing_plus_and_minus(
    renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("combat_stance")
    # Choose pelvis centered in canvas
    canvas_size = (1000, 1000)
    canvas_pos = Point2D(500.0, 500.0)

    img_right = renderer.render_body(wukong_char, pose, canvas_pos, facing=1, canvas_size=canvas_size)
    img_left = renderer.render_body(wukong_char, pose, canvas_pos, facing=-1, canvas_size=canvas_size)

    # Horizontally flipping img_right around center X=500 must match img_left
    flipped_right = img_right.transpose(Image.FLIP_LEFT_RIGHT)

    arr_flipped = np.array(flipped_right)
    arr_left = np.array(img_left)

    # Difference in alpha channel between flipped right and left should be identical (allowing subpixel antialias <= 1px)
    diff = np.abs(arr_flipped[:, :, 3].astype(int) - arr_left[:, :, 3].astype(int))
    assert np.mean(diff) < 1.0  # Negligible rasterization rounding difference


# 12. Verify scale 0.8 scales properly
def test_12_scale_0_8_scales_properly(renderer: HumanoidBodyRenderer):
    pose = PoseCatalog.get_pose("standoff_idle")
    cfg_base = ActorConfig(
        actor_id="c1",
        skin=CharacterSkin.DARK_WUKONG,
        color="#DAA520",
        weapon=WeaponType.RUYI_STAFF,
        display_name="Base",
        side=ActorSide.LEFT,
        scale=1.0,
    )
    cfg_small = ActorConfig(
        actor_id="c2",
        skin=CharacterSkin.DARK_WUKONG,
        color="#DAA520",
        weapon=WeaponType.RUYI_STAFF,
        display_name="Small",
        side=ActorSide.LEFT,
        scale=0.8,
    )
    char_base = StickmanCharacter.from_actor_config(cfg_base)
    char_small = StickmanCharacter.from_actor_config(cfg_small)

    pos = Point2D(540.0, 1000.0)
    bbox_base = renderer.get_bounding_box(char_base, pose, pos, facing=1)
    bbox_small = renderer.get_bounding_box(char_small, pose, pos, facing=1)

    height_base = bbox_base[3] - bbox_base[1]
    height_small = bbox_small[3] - bbox_small[1]

    # Height should scale by approximately 0.8
    assert math.isclose(height_small / height_base, 0.8, rel_tol=0.05)


# 13. Verify scale 1.25 scales properly
def test_13_scale_1_25_scales_properly(renderer: HumanoidBodyRenderer):
    pose = PoseCatalog.get_pose("standoff_idle")
    cfg_base = ActorConfig(
        actor_id="c1",
        skin=CharacterSkin.DARK_WUKONG,
        color="#DAA520",
        weapon=WeaponType.RUYI_STAFF,
        display_name="Base",
        side=ActorSide.LEFT,
        scale=1.0,
    )
    cfg_large = ActorConfig(
        actor_id="c3",
        skin=CharacterSkin.DARK_WUKONG,
        color="#DAA520",
        weapon=WeaponType.RUYI_STAFF,
        display_name="Large",
        side=ActorSide.LEFT,
        scale=1.25,
    )
    char_base = StickmanCharacter.from_actor_config(cfg_base)
    char_large = StickmanCharacter.from_actor_config(cfg_large)

    pos = Point2D(540.0, 1000.0)
    bbox_base = renderer.get_bounding_box(char_base, pose, pos, facing=1)
    bbox_large = renderer.get_bounding_box(char_large, pose, pos, facing=1)

    height_base = bbox_base[3] - bbox_base[1]
    height_large = bbox_large[3] - bbox_large[1]

    # Height should scale by approximately 1.25
    assert math.isclose(height_large / height_base, 1.25, rel_tol=0.05)


# 14. Verify input pose is not mutated after rendering
def test_14_input_pose_immutability(renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("standoff_idle")
    head_before = pose.get_joint(JointType.HEAD)

    _ = renderer.render_body(wukong_char, pose, Point2D(540.0, 1200.0), facing=-1)

    head_after = pose.get_joint(JointType.HEAD)
    assert head_before == head_after


# 15. Verify deterministic rendering
def test_15_deterministic_rendering(renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter):
    pose = PoseCatalog.get_pose("combat_stance")
    pos = Point2D(540.0, 1200.0)

    img1 = renderer.render_body(wukong_char, pose, pos, facing=1)
    img2 = renderer.render_body(wukong_char, pose, pos, facing=1)

    arr1 = np.array(img1)
    arr2 = np.array(img2)
    assert np.array_equal(arr1, arr2)


# 16. Verify get_bounding_box() contains all non-zero alpha pixels
def test_16_bounding_box_contains_all_nonzero_pixels(
    renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter
):
    pose_names = ["standoff_idle", "combat_stance", "mid_air_leap", "overhead_slam"]
    for name in pose_names:
        pose = PoseCatalog.get_pose(name)
        pos = Point2D(540.0, 1000.0)
        img = renderer.render_body(wukong_char, pose, pos, facing=1)
        bbox = renderer.get_bounding_box(wukong_char, pose, pos, facing=1)

        arr = np.array(img)
        alpha = arr[:, :, 3]

        # Find actual pixel indices where alpha > 0
        ys, xs = np.nonzero(alpha > 0)
        assert len(ys) > 0

        actual_min_x, actual_max_x = int(np.min(xs)), int(np.max(xs))
        actual_min_y, actual_max_y = int(np.min(ys)), int(np.max(ys))

        min_x, min_y, max_x, max_y = bbox

        assert min_x <= actual_min_x, f"Pose {name}: min_x {min_x} > actual {actual_min_x}"
        assert max_x >= actual_max_x, f"Pose {name}: max_x {max_x} < actual {actual_max_x}"
        assert min_y <= actual_min_y, f"Pose {name}: min_y {min_y} > actual {actual_min_y}"
        assert max_y >= actual_max_y, f"Pose {name}: max_y {max_y} < actual {actual_max_y}"


# 17. Reject invalid pose or non-finite canvas coordinates
def test_17_reject_invalid_pose_or_nonfinite_coords(
    renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")

    # Invalid facing
    with pytest.raises(ValueError, match="Facing must be \\+1 or -1"):
        renderer.render_body(wukong_char, pose, Point2D(500.0, 500.0), facing=0)

    with pytest.raises(ValueError, match="Facing must be \\+1 or -1"):
        renderer.render_body(wukong_char, pose, Point2D(500.0, 500.0), facing=2)

    # Invalid scale via transform_joints
    with pytest.raises(ValueError, match="scale must be in range"):
        renderer.transform_joints(pose, Point2D(500.0, 500.0), facing=1, scale=-0.5)

    with pytest.raises(ValueError, match="scale must be in range"):
        renderer.transform_joints(pose, Point2D(500.0, 500.0), facing=1, scale=10.0)

    # Non-finite coordinates
    with pytest.raises(ValueError, match="coordinates must be finite"):
        Point2D(float("nan"), 0.0)

    with pytest.raises(ValueError, match="coordinates must be finite"):
        Point2D(0.0, float("inf"))


# 18. Render near canvas boundary without exceptions (clipping safety)
def test_18_render_near_canvas_boundary_safe_clipping(
    renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")

    # Position character partially outside the canvas
    boundary_positions = [
        Point2D(0.0, 0.0),          # Top-left corner
        Point2D(1080.0, 1920.0),    # Bottom-right corner
        Point2D(-100.0, 500.0),     # Partially off-screen left
        Point2D(1150.0, 500.0),     # Partially off-screen right
        Point2D(540.0, -50.0),      # Partially off-screen top
        Point2D(540.0, 2000.0),     # Partially off-screen bottom
    ]

    for pos in boundary_positions:
        img = renderer.render_body(wukong_char, pose, pos, facing=1)
        assert isinstance(img, Image.Image)
        assert img.size == (1080, 1920)

        bbox = renderer.get_bounding_box(wukong_char, pose, pos, facing=1)
        assert 0 <= bbox[0] <= 1080
        assert 0 <= bbox[2] <= 1080
        assert 0 <= bbox[1] <= 1920
        assert 0 <= bbox[3] <= 1920


# ==============================================================================
# G5.2.3.1.1 – HUMANOID BODY GROUND ALIGNMENT & BOUNDING BOX AUDIT TESTS
# ==============================================================================


# 19. BBox pixel alpha thực tế không bị nhầm với BBox có padding
def test_19_actual_pixel_bbox_not_confused_with_padded_bbox(
    renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pelvis_pos = Point2D(400.0, 1230.0)

    # A. Geometric Bounding Box từ joints
    joint_bbox = renderer.get_joint_bounding_box(pose, pelvis_pos, facing=1, scale=1.0)
    # B. Analytical Primitive Bounding Box
    prim_bbox = renderer.get_bounding_box(wukong_char, pose, pelvis_pos, facing=1)
    # C. Padded Bounding Box
    padded_bbox = renderer.get_padded_bounding_box(wukong_char, pose, pelvis_pos, facing=1, padding=20.0)

    # D. Actual Image Pixel BBox
    img = renderer.render_body(wukong_char, pose, pelvis_pos, facing=1)
    pixel_bbox = img.getbbox()  # Half-open: (min_x, min_y, max_x + 1, max_y + 1)

    # 1. Joint bbox is strictly inside primitive bbox
    assert joint_bbox[0] >= prim_bbox[0]
    assert joint_bbox[1] >= prim_bbox[1]
    assert joint_bbox[2] <= prim_bbox[2]
    assert joint_bbox[3] <= prim_bbox[3]

    # 2. Primitive bbox matches actual pixel bbox (allowing max 1px half-open/rasterization)
    assert prim_bbox[0] == pixel_bbox[0]
    assert prim_bbox[1] == pixel_bbox[1]
    assert prim_bbox[2] == pixel_bbox[2] - 1
    assert prim_bbox[3] == pixel_bbox[3] - 1

    # 3. Padded bbox is strictly larger than primitive bbox
    assert padded_bbox[0] < prim_bbox[0]
    assert padded_bbox[1] < prim_bbox[1]
    assert padded_bbox[2] > prim_bbox[2]
    assert padded_bbox[3] > prim_bbox[3]

    # 4. Joint bottom is 1415, Primitive bottom is 1420, Padded bottom is 1440
    assert joint_bbox[3] == 1415
    assert prim_bbox[3] == 1420
    assert padded_bbox[3] == 1440


# 20. Wukong Standoff không vẽ xuyên mặt đất
def test_20_wukong_standoff_does_not_penetrate_ground(
    renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pelvis_y = CoordinateManager.get_ground_aligned_root_y(
        pose=pose, support_mode=SupportMode.DOUBLE, ground_y=1420.0, scale=1.0
    )
    assert pelvis_y == 1230.0

    img = renderer.render_body(wukong_char, pose, Point2D(400.0, pelvis_y), facing=1)
    arr = np.array(img)

    # 1. Max Y of non-zero alpha pixels must be EXACTLY 1420 (on the ground line)
    pixel_bbox = img.getbbox()
    assert pixel_bbox[3] == 1421  # half-open upper bound -> max pixel Y is 1420

    # 2. No pixel below ground level (y >= 1421) has alpha > 0
    subground_alpha = arr[1421:, :, 3]
    assert np.all(subground_alpha == 0), "Found non-zero alpha pixels below ground line Y=1420"

    # 3. Ground contact line Y=1420 must contain support foot pixels
    ground_line_alpha = arr[1420, :, 3]
    assert np.any(ground_line_alpha > 0), "Support foot pixels must reach ground line Y=1420"


# 21. Wukong Combat Stance không vẽ xuyên mặt đất
def test_21_wukong_combat_stance_does_not_penetrate_ground(
    renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("combat_stance")
    pelvis_y = CoordinateManager.get_ground_aligned_root_y(
        pose=pose, support_mode=SupportMode.DOUBLE, ground_y=1420.0, scale=1.0
    )
    # Combat stance bent knees: contact Y in local space is 170.0, pelvis_y = 1420 - 170 = 1250.0
    assert pelvis_y == 1250.0

    img = renderer.render_body(wukong_char, pose, Point2D(420.0, pelvis_y), facing=1)
    arr = np.array(img)

    pixel_bbox = img.getbbox()
    assert pixel_bbox[3] == 1421  # max pixel Y is 1420

    # No pixels below ground
    subground_alpha = arr[1421:, :, 3]
    assert np.all(subground_alpha == 0)

    # Contact line has foot pixels
    assert np.any(arr[1420, :, 3] > 0)


# 22. Erlang Standoff không vẽ xuyên mặt đất khi scale 1.05
def test_22_erlang_standoff_scale_1_05_does_not_penetrate_ground(
    renderer: HumanoidBodyRenderer, erlang_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pelvis_y = CoordinateManager.get_ground_aligned_root_y(
        pose=pose, support_mode=SupportMode.DOUBLE, ground_y=1420.0, scale=erlang_char.scale
    )
    # 1420.0 - (190.0 * 1.05) = 1420.0 - 199.5 = 1220.5
    assert pelvis_y == pytest.approx(1220.5, abs=1e-5)

    img = renderer.render_body(
        erlang_char, pose, Point2D(680.0, pelvis_y), facing=-1
    )
    arr = np.array(img)

    pixel_bbox = img.getbbox()
    assert pixel_bbox[3] == 1421  # max pixel Y is 1420

    # Zero penetration below ground
    subground_alpha = arr[1421:, :, 3]
    assert np.all(subground_alpha == 0)

    # Foot touches ground line 1420
    assert np.any(arr[1420, :, 3] > 0)


# 23. Chân không trụ không bị ép xuống mặt đất
def test_23_non_support_foot_not_forced_to_ground(
    renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter
):
    base_pose = PoseCatalog.get_pose("standoff_idle")
    asym_joints = dict(base_pose.joints)
    # Lift right ankle by 50px (local Y: 185 -> 135)
    asym_joints[JointType.ANKLE_R] = Point2D(asym_joints[JointType.ANKLE_R].x + 30.0, 135.0)
    crane_pose = StickmanPose(name="crane_kick_left_support", joints=asym_joints)

    pelvis_y = CoordinateManager.get_ground_aligned_root_y(
        pose=crane_pose, support_mode=SupportMode.LEFT_ONLY, ground_y=1420.0, scale=1.0
    )
    # Root anchored strictly to left foot: 1420 - 190 = 1230.0
    assert pelvis_y == 1230.0

    img = renderer.render_body(wukong_char, crane_pose, Point2D(500.0, pelvis_y), facing=1)
    arr = np.array(img)

    # Transformed joints
    joints = renderer.transform_joints(crane_pose, Point2D(500.0, pelvis_y), facing=1, scale=1.0)
    ankle_l = joints[JointType.ANKLE_L]
    ankle_r = joints[JointType.ANKLE_R]

    assert ankle_l.y == 1415.0  # Left ankle on ground level (contact = 1420)
    assert ankle_r.y == 1365.0  # Right ankle elevated by 50px

    # Right foot region (around x=530, y in [1360, 1375]) has pixels
    right_foot_px = arr[1360:1375, 520:540, 3]
    assert np.any(right_foot_px > 0)

    # Right foot does not touch 1420
    # Left foot touches 1420 around x=500
    assert np.any(arr[1420, 490:510, 3] > 0)
    # Below right foot at ground level (x in [520, 540]), alpha should be zero
    assert np.all(arr[1420, 525:545, 3] == 0)


# 24. Facing trái không làm thay đổi ground contact
def test_24_left_facing_preserves_ground_contact(
    renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("standoff_idle")
    pelvis_y = 1230.0
    pelvis_x = 540.0

    img_right = renderer.render_body(wukong_char, pose, Point2D(pelvis_x, pelvis_y), facing=1)
    img_left = renderer.render_body(wukong_char, pose, Point2D(pelvis_x, pelvis_y), facing=-1)

    bbox_r = img_right.getbbox()
    bbox_l = img_left.getbbox()

    # Both must terminate at identical bottom Y
    assert bbox_r[3] == 1421
    assert bbox_l[3] == 1421

    arr_r = np.array(img_right)
    arr_l = np.array(img_left)

    # Both have zero pixels below ground
    assert np.all(arr_r[1421:, :, 3] == 0)
    assert np.all(arr_l[1421:, :, 3] == 0)

    # Both have foot pixels at ground line 1420
    assert np.any(arr_r[1420, :, 3] > 0)
    assert np.any(arr_l[1420, :, 3] > 0)


# 25. Kiểm tra head radius theo thiết kế (26px)
def test_25_head_radius_matches_design_26px(
    renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter
):
    # 1. Constant in CoordinateManager must be 26.0
    assert CoordinateManager.HEAD_RADIUS == 26.0

    # 2. Render standoff idle
    pose = PoseCatalog.get_pose("standoff_idle")
    pelvis_pos = Point2D(400.0, 1230.0)
    joints = renderer.transform_joints(pose, pelvis_pos, facing=1, scale=1.0)
    head_pt = joints[JointType.HEAD]

    # In standoff idle: pelvis is (400, 1230), head is at (400, 1062)
    assert head_pt.x == 400.0
    assert head_pt.y == 1062.0

    img = renderer.render_body(wukong_char, pose, pelvis_pos, facing=1)
    arr = np.array(img)

    # Inspect vertical slice at x = 400 around head (y < 1100)
    head_col_alpha = arr[:1100, 400, 3]
    head_ys = np.where(head_col_alpha > 0)[0]
    head_top_y = int(np.min(head_ys))

    # Topmost head pixel must be at head_pt.y - 26 = 1062 - 26 = 1036
    assert head_top_y == 1036
    assert head_pt.y - head_top_y == 26.0

    # Inspect horizontal slice at y = 1062 across head
    head_row_alpha = arr[1062, :, 3]
    head_xs = np.where(head_row_alpha > 0)[0]
    head_left_x = int(np.min(head_xs))
    head_right_x = int(np.max(head_xs))

    # Leftmost and rightmost pixels: 400 - 26 = 374, 400 + 26 = 426
    assert head_left_x == 374
    assert head_right_x == 426
    assert head_pt.x - head_left_x == 26.0
    assert head_right_x - head_pt.x == 26.0


# 26. Pose đầu vào không bị thay đổi sau render
def test_26_input_pose_preserved_across_audit_renders(
    renderer: HumanoidBodyRenderer, wukong_char: StickmanCharacter
):
    pose = PoseCatalog.get_pose("combat_stance")
    snapshot = {j: Point2D(p.x, p.y) for j, p in pose.joints.items()}

    # Perform multiple renders
    for facing in (+1, -1):
        for scale in (0.8, 1.0, 1.25):
            char = StickmanCharacter.from_actor_config(
                ActorConfig(
                    actor_id="test",
                    skin=CharacterSkin.DARK_WUKONG,
                    color="#DAA520",
                    weapon=WeaponType.RUYI_STAFF,
                    display_name="Test",
                    side=ActorSide.LEFT,
                    scale=scale,
                )
            )
            _ = renderer.render_body(char, pose, Point2D(500.0, 1000.0), facing=facing)

    # Verify every joint coordinate is completely unchanged
    for j, orig_pt in snapshot.items():
        curr_pt = pose.joints[j]
        assert curr_pt.x == orig_pt.x
        assert curr_pt.y == orig_pt.y

