"""
Unit and integration tests for Stage 6: Motion Interpolation & Animation Loop Engine.
Verifies bone rigidity (0.000 px error), easing, loop continuity, ground contact,
weapon tracking, frame generation, and MP4 video export.
"""

import math
from pathlib import Path
import subprocess

from PIL import Image
import pytest

from app.modules.animation.animation_loop import (
    AnimationLoopEngine,
    AnimationState,
    AnimationTrack,
    Keyframe,
)
from app.modules.animation.background_renderer import NotebookBackgroundRenderer
from app.modules.animation.buddha_palm_renderer import BuddhaPalmRenderer
from app.modules.animation.character_renderer_parts import (
    AccessoriesRenderer,
    FaceFeatureRenderer,
    HumanoidBodyRenderer,
    WeaponRenderer,
)
from app.modules.animation.interpolation_engine import (
    EasingFunction,
    InterpolationEngine,
    evaluate_easing,
    extract_bone_angles,
    interpolate_bone_angles,
    interpolate_poses,
    reconstruct_pose_from_angles,
)
from app.modules.animation.pose_catalog import PoseCatalog, PoseDefinition
from app.modules.animation.stickman_models import (
    CoordinateManager,
    HumanoidSkeleton,
    JointType,
    Point2D,
    RigidBoneValidator,
    StickmanCharacter,
    StickmanPose,
    SupportMode,
)
from app.schemas.scene_schema import ActorConfig, ActorSide, CharacterSkin, WeaponType


# -----------------------------------------------------------------------------
# 1. EASING TESTS
# -----------------------------------------------------------------------------

def test_easing_linear():
    """Verify linear easing behavior and clamping."""
    assert evaluate_easing(EasingFunction.LINEAR, 0.0) == 0.0
    assert evaluate_easing(EasingFunction.LINEAR, 0.5) == 0.5
    assert evaluate_easing(EasingFunction.LINEAR, 1.0) == 1.0
    # Clamping
    assert evaluate_easing(EasingFunction.LINEAR, -0.5) == 0.0
    assert evaluate_easing(EasingFunction.LINEAR, 1.5) == 1.0


def test_easing_curves_endpoints_and_monotonicity():
    """Verify all easing curves start at 0, end at 1, and remain monotonically non-decreasing."""
    curves = [
        EasingFunction.LINEAR,
        EasingFunction.EASE_IN,
        EasingFunction.EASE_OUT,
        EasingFunction.EASE_IN_OUT,
        EasingFunction.CUBIC_BEZIER,
    ]
    for curve in curves:
        val_0 = evaluate_easing(curve, 0.0)
        val_1 = evaluate_easing(curve, 1.0)
        assert abs(val_0) < 1e-6, f"{curve} failed at 0.0"
        assert abs(val_1 - 1.0) < 1e-6, f"{curve} failed at 1.0"

        # Check monotonic progression
        prev = 0.0
        for step in range(1, 21):
            t = step / 20.0
            cur = evaluate_easing(curve, t)
            assert cur >= prev - 1e-6, f"{curve} was not monotonic at t={t}"
            prev = cur


def test_easing_invalid_input():
    """Verify non-finite input raises ValueError."""
    with pytest.raises(ValueError, match="must be finite"):
        evaluate_easing(EasingFunction.LINEAR, float("nan"))
    with pytest.raises(ValueError, match="must be finite"):
        evaluate_easing(EasingFunction.LINEAR, float("inf"))


# -----------------------------------------------------------------------------
# 2. BONE ANGLE EXTRACTION & FORWARD KINEMATICS RIGIDITY
# -----------------------------------------------------------------------------

def test_bone_angle_extraction_all_catalog_poses():
    """Verify angle extraction produces valid finite radian angles for all catalog poses."""
    all_defs = PoseCatalog.get_all_definitions()
    for name, pdef in all_defs.items():
        angles = extract_bone_angles(pdef.pose)
        assert len(angles) == 13, f"Pose {name} did not yield 13 bone angles"
        for bone_name, angle in angles.items():
            assert -math.pi <= angle <= math.pi, f"Pose {name} bone {bone_name} angle {angle} outside [-pi, pi]"


def test_fk_pose_reconstruction_zero_distortion():
    """Verify reconstruct_pose_from_angles yields exactly 0.000 px length error."""
    pose = PoseCatalog.get_pose("combat_stance")
    angles = extract_bone_angles(pose)
    reconstructed = reconstruct_pose_from_angles(angles, pose_name="reconstructed_combat")

    val = RigidBoneValidator.validate(reconstructed)
    assert val.is_valid is True
    max_err = max(d.length_error for d in val.errors.values()) if val.errors else 0.0
    assert max_err < 1e-5, f"Reconstructed pose had bone distortion {max_err:.8f} px"


def test_angular_interpolation_shortest_path():
    """Verify interpolation takes the shorter circular arc across the +-pi boundary."""
    # 170 deg (2.967 rad) to -170 deg (-2.967 rad).
    # Shortest path is across pi (+20 deg), midpoint at pi (or -pi).
    ang_a = {"pelvis_chest": math.radians(170.0)}
    ang_b = {"pelvis_chest": math.radians(-170.0)}

    ang_mid = interpolate_bone_angles(ang_a, ang_b, 0.5)
    # The midpoint should be +-180 deg (+-pi)
    assert abs(abs(ang_mid["pelvis_chest"]) - math.pi) < 1e-5


def test_pose_interpolation_rigidity_all_transitions():
    """
    Core G6 Directives Test:
    Verify that across transitions between diverse poses, every intermediate
    frame (t = 0.1, 0.3, 0.5, 0.7, 0.9) maintains 100% rigid bones with 0.000 px error.
    """
    pairs = [
        ("standoff_idle", "combat_stance"),
        ("combat_stance", "forward_charge"),
        ("forward_charge", "overhead_slam"),
        ("overhead_slam", "vortex_sweep"),
        ("vortex_sweep", "guard_block"),
        ("guard_block", "knockback_slide"),
        ("knockback_slide", "mid_air_leap"),
        ("mid_air_leap", "standoff_idle"),
    ]

    for name_a, name_b in pairs:
        def_a = PoseCatalog.get_definition(name_a)
        def_b = PoseCatalog.get_definition(name_b)

        for step in [0.1, 0.3, 0.5, 0.7, 0.9]:
            interp_def = interpolate_poses(def_a, def_b, t=step, easing=EasingFunction.EASE_IN_OUT)
            val = RigidBoneValidator.validate(interp_def.pose)
            assert val.is_valid is True, f"Failed rigidity between {name_a} and {name_b} at t={step}"
            max_err = max(d.length_error for d in val.errors.values()) if val.errors else 0.0
            assert max_err < 1e-5, f"Excessive distortion {max_err} between {name_a} and {name_b} at t={step}"


def test_pose_interpolation_endpoints():
    """Verify t=0.0 returns def_a exactly, and t=1.0 returns def_b exactly."""
    def_a = PoseCatalog.get_definition("standoff_idle")
    def_b = PoseCatalog.get_definition("overhead_slam")

    res_0 = interpolate_poses(def_a, def_b, t=0.0)
    assert res_0.name == def_a.name
    res_1 = interpolate_poses(def_a, def_b, t=1.0)
    assert res_1.name == def_b.name


def test_pose_interpolation_weapon_angle_shortest_degree_path():
    """Verify weapon angle blends across 0/360 degree boundary along shortest arc."""
    def_a = PoseCatalog.get_definition("standoff_idle")  # weapon_angle_deg = 80.0
    # Create custom pose def with weapon_angle_deg = 350.0 and 10.0
    p1 = PoseDefinition(
        name="p1",
        pose=def_a.pose,
        support_mode=SupportMode.DOUBLE,
        elevation=0.0,
        weapon_anchor=JointType.WRIST_R,
        weapon_angle_deg=350.0,
    )
    p2 = PoseDefinition(
        name="p2",
        pose=def_a.pose,
        support_mode=SupportMode.DOUBLE,
        elevation=0.0,
        weapon_anchor=JointType.WRIST_R,
        weapon_angle_deg=10.0,
    )
    mid = interpolate_poses(p1, p2, 0.5)
    # The midpoint of 350 and 10 along shortest arc is 0 (or 360)
    assert mid.weapon_angle_deg is not None
    assert abs(mid.weapon_angle_deg - 0.0) < 1e-4 or abs(mid.weapon_angle_deg - 360.0) < 1e-4


def test_ground_clearance_no_penetration():
    """Verify that across all interpolated frames, no foot penetrates the ground plane (Y <= 1421.0)."""
    p_a = PoseCatalog.get_definition("standoff_idle")
    p_b = PoseCatalog.get_definition("combat_stance")
    p_c = PoseCatalog.get_definition("overhead_slam")

    for p1, p2 in [(p_a, p_b), (p_b, p_c), (p_c, p_a)]:
        for step in range(11):
            t = step / 10.0
            interp = interpolate_poses(p1, p2, t)
            root_y = CoordinateManager.get_ground_aligned_root_y(
                interp.pose,
                support_mode=interp.support_mode,
                ground_y=1420.0,
                scale=1.0,
                elevation=interp.elevation,
            )
            c_pose = CoordinateManager.transform_pose_to_canvas(
                interp.pose, Point2D(540.0, root_y), facing=1, scale=1.0
            )
            sp = CoordinateManager.get_support_points(c_pose)
            max_y = max(sp["foot_l_bottom"], sp["foot_r_bottom"])
            assert max_y <= 1421.0, f"Ground penetration detected: {max_y} px > 1421.0 px at t={t}"


# -----------------------------------------------------------------------------
# 3. ANIMATION LOOP & TIMELINE TESTS
# -----------------------------------------------------------------------------

def test_keyframe_validation():
    """Verify Keyframe input checks."""
    with pytest.raises(ValueError, match="time_sec must be non-negative"):
        Keyframe(time_sec=-1.0, pose_name="standoff_idle")
    with pytest.raises(ValueError, match="facing must be"):
        Keyframe(time_sec=0.0, pose_name="standoff_idle", facing=0)
    with pytest.raises(ValueError, match="must define either"):
        Keyframe(time_sec=0.0)


def test_animation_track_sorting_and_duration():
    """Verify keyframes are automatically sorted by time_sec and duration detected."""
    kf2 = Keyframe(time_sec=2.0, pose_name="combat_stance")
    kf1 = Keyframe(time_sec=0.0, pose_name="standoff_idle")
    kf3 = Keyframe(time_sec=1.0, pose_name="forward_charge")

    track = AnimationTrack(keyframes=[kf2, kf1, kf3])
    assert track.keyframes[0].time_sec == 0.0
    assert track.keyframes[1].time_sec == 1.0
    assert track.keyframes[2].time_sec == 2.0
    assert track.duration_sec == 2.0


def test_animation_loop_engine_seamless_looping():
    """Verify that looping track evaluated at t = duration + dt produces identical state as dt."""
    track = AnimationTrack(
        keyframes=[
            Keyframe(time_sec=0.0, pose_name="standoff_idle"),
            Keyframe(time_sec=1.0, pose_name="combat_stance"),
            Keyframe(time_sec=2.0, pose_name="standoff_idle"),
        ],
        duration_sec=2.0,
        loop=True,
    )
    engine = AnimationLoopEngine()

    state_03 = engine.get_state_at_time(track, time_sec=0.3)
    state_23 = engine.get_state_at_time(track, time_sec=2.3)
    state_43 = engine.get_state_at_time(track, time_sec=4.3)

    # All joints should match closely
    for j in JointType:
        pt_03 = state_03.pose_def.pose.joints[j]
        pt_23 = state_23.pose_def.pose.joints[j]
        pt_43 = state_43.pose_def.pose.joints[j]
        assert abs(pt_03.x - pt_23.x) < 1e-4
        assert abs(pt_03.y - pt_23.y) < 1e-4
        assert abs(pt_03.x - pt_43.x) < 1e-4
        assert abs(pt_03.y - pt_43.y) < 1e-4


def test_two_handed_weapon_tracking_through_animation():
    """
    Verify that when character transitions through two-handed weapon poses,
    the weapon attaches solidly across wrists without drifting.
    """
    track = AnimationTrack(
        keyframes=[
            Keyframe(time_sec=0.0, pose_name="combat_stance"),
            Keyframe(time_sec=1.0, pose_name="overhead_slam"),
        ],
        duration_sec=1.0,
        loop=False,
    )
    engine = AnimationLoopEngine()
    cfg = ActorConfig(
        actor_id="wukong_two_hand",
        display_name="Dark Wukong",
        side=ActorSide.LEFT,
        skin=CharacterSkin.DARK_WUKONG,
        weapon=WeaponType.RUYI_STAFF,
        scale=1.0,
    )
    char = StickmanCharacter.from_actor_config(cfg)

    for step in range(6):
        t = step / 5.0
        state = engine.get_state_at_time(track, time_sec=t)
        # Verify secondary_grip is maintained
        assert state.pose_def.secondary_grip == JointType.WRIST_L

        # Verify weapon endpoints calculate without error
        tail, tip, anchor, ang = engine.weapon_renderer.get_weapon_endpoints(
            character=char,
            pose=state.pose_def.pose,
            canvas_position=state.canvas_pos,
            facing=state.facing,
            pose_def=state.pose_def,
            align_two_hands=True,
        )
        total_len = math.hypot(tip.x - tail.x, tip.y - tail.y)
        expected_len = engine.weapon_renderer.get_weapon_length(WeaponType.RUYI_STAFF, 1.0)
        assert abs(total_len - expected_len) < 1e-2


def test_animation_loop_engine_generate_clip_frames():
    """Verify generate_clip_frames produces correctly sized RGBA frames."""
    track = AnimationTrack(
        keyframes=[
            Keyframe(time_sec=0.0, pose_name="standoff_idle"),
            Keyframe(time_sec=0.2, pose_name="combat_stance"),
        ],
        duration_sec=0.2,
        loop=False,
    )
    engine = AnimationLoopEngine()
    cfg = ActorConfig(
        actor_id="wukong",
        display_name="Dark Wukong",
        side=ActorSide.LEFT,
        skin=CharacterSkin.DARK_WUKONG,
        weapon=WeaponType.RUYI_STAFF,
        scale=1.0,
    )
    char = StickmanCharacter.from_actor_config(cfg)

    frames = engine.generate_clip_frames(track, char, fps=30)
    # 0.2 sec * 30 fps = 6 frames
    assert len(frames) == 6
    for f in frames:
        assert f.size == (1080, 1920)
        assert f.mode == "RGBA"


def test_animation_loop_engine_background_compositing():
    """Verify frames composite onto NotebookBackgroundRenderer background without error."""
    track = AnimationTrack(
        keyframes=[
            Keyframe(time_sec=0.0, pose_name="standoff_idle"),
            Keyframe(time_sec=0.1, pose_name="combat_stance"),
        ],
        duration_sec=0.1,
        loop=False,
    )
    bg_ren = NotebookBackgroundRenderer()
    bg_img = bg_ren.render_background(state="clean", seed=42)

    engine = AnimationLoopEngine()
    cfg = ActorConfig(
        actor_id="erlang",
        display_name="Erlang Shen",
        side=ActorSide.RIGHT,
        skin=CharacterSkin.ERLANG_SHEN,
        weapon=WeaponType.THREE_POINTED_SPEAR,
        scale=1.0,
    )
    char = StickmanCharacter.from_actor_config(cfg)

    frames = engine.generate_clip_frames(track, char, fps=10, background_image=bg_img)
    assert len(frames) == 1  # max(1, round(0.1*10)) = 1
    assert frames[0].size == (1080, 1920)


def test_animation_loop_engine_buddha_palm_integration():
    """Verify AnimationLoopEngine properly animates a Buddha Palm suppression sequence."""
    track = AnimationTrack(
        keyframes=[
            Keyframe(time_sec=0.0, pose_name="standoff_idle", elevation=100.0),
            Keyframe(time_sec=0.2, pose_name="mid_air_leap", elevation=0.0),
        ],
        duration_sec=0.2,
        loop=False,
    )
    engine = AnimationLoopEngine()
    cfg = ActorConfig(
        actor_id="buddha_actor",
        display_name="Buddha Palm",
        side=ActorSide.TOP,
        skin=CharacterSkin.BUDDHA_PALM,
        weapon=WeaponType.GIANT_GOLDEN_PALM,
        scale=1.0,
    )
    char = StickmanCharacter.from_actor_config(cfg)

    frames = engine.generate_clip_frames(track, char, fps=10)
    assert len(frames) >= 1
    # Check that pixels are drawn
    extrema = frames[0].getextrema()
    alpha_extrema = extrema[3]
    assert alpha_extrema[1] > 0, "Buddha Palm frame was completely transparent"


def test_animation_loop_engine_export_mp4_video(tmp_path: Path):
    """Verify export_mp4_video creates a valid playable H.264 MP4 file."""
    track = AnimationTrack(
        keyframes=[
            Keyframe(time_sec=0.0, pose_name="standoff_idle"),
            Keyframe(time_sec=0.1, pose_name="combat_stance"),
        ],
        duration_sec=0.1,
        loop=False,
    )
    engine = AnimationLoopEngine()
    cfg = ActorConfig(
        actor_id="wukong",
        display_name="Dark Wukong",
        side=ActorSide.LEFT,
        skin=CharacterSkin.DARK_WUKONG,
        weapon=WeaponType.RUYI_STAFF,
        scale=0.5,  # faster rendering
    )
    char = StickmanCharacter.from_actor_config(cfg)

    frames_dir = tmp_path / "frames"
    frames = engine.generate_clip_frames(track, char, fps=10, output_dir=frames_dir)

    mp4_out = tmp_path / "test_clip.mp4"
    engine.export_mp4_video(frames_dir, mp4_out, fps=10)

    assert mp4_out.exists()
    assert mp4_out.stat().st_size > 1000, "Exported MP4 file size is too small"

    # Verify with ffprobe
    probe_cmd = [
        r"C:\ffmpeg\bin\ffprobe.exe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,codec_name,pix_fmt",
        "-of", "default=noprint_wrappers=1",
        str(mp4_out),
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    assert "width=1080" in res.stdout
    assert "height=1920" in res.stdout
    assert "codec_name=h264" in res.stdout
    assert "pix_fmt=yuv420p" in res.stdout


def test_animation_loop_engine_single_keyframe():
    """Verify single-keyframe track returns valid consistent state at any arbitrary time."""
    track = AnimationTrack(
        keyframes=[Keyframe(time_sec=0.0, pose_name="standoff_idle")],
        duration_sec=3.0,
    )
    engine = AnimationLoopEngine()
    state_0 = engine.get_state_at_time(track, 0.0)
    state_5 = engine.get_state_at_time(track, 5.0)
    assert state_0.pose_def.name == "standoff_idle"
    assert state_5.pose_def.name == "standoff_idle"
    assert abs(state_0.canvas_pos.y - state_5.canvas_pos.y) < 1e-4


def test_facing_interpolation_flip():
    """Verify facing switches cleanly at t=0.5 when transitioning between opposite facing directions."""
    track = AnimationTrack(
        keyframes=[
            Keyframe(time_sec=0.0, pose_name="standoff_idle", facing=1),
            Keyframe(time_sec=1.0, pose_name="combat_stance", facing=-1),
        ],
        duration_sec=1.0,
        loop=False,
    )
    engine = AnimationLoopEngine()
    state_early = engine.get_state_at_time(track, 0.2)
    state_late = engine.get_state_at_time(track, 0.8)
    assert state_early.facing == 1
    assert state_late.facing == -1


def test_scale_invariance_rigidity():
    """Verify Forward Kinematics rigidity holds at arbitrary scales (0.5, 0.8, 1.25, 2.0)."""
    p_a = PoseCatalog.get_definition("standoff_idle")
    p_b = PoseCatalog.get_definition("combat_stance")
    interp = interpolate_poses(p_a, p_b, t=0.5)

    # Local pose must pass RigidBoneValidator
    val = RigidBoneValidator.validate(interp.pose)
    assert val.is_valid is True

    # Canvas transformed joints must scale lengths strictly proportionally
    for sc in [0.5, 0.8, 1.0, 1.25, 2.0]:
        canvas_joints = {
            j: CoordinateManager.local_to_canvas(pt, Point2D(540.0, 960.0), facing=1, scale=sc)
            for j, pt in interp.pose.joints.items()
        }
        for bone in HumanoidSkeleton.BONES:
            p1 = canvas_joints[bone.parent]
            p2 = canvas_joints[bone.child]
            measured_len = math.hypot(p2.x - p1.x, p2.y - p1.y)
            expected_len = bone.length * sc
            assert abs(measured_len - expected_len) < 1e-4, f"Bone {bone.name} scaled error at scale {sc}"


def test_airborne_elevation_support_mode():
    """Verify transition from ground to mid_air_leap sets SupportMode.AIRBORNE when elevated."""
    p_ground = PoseCatalog.get_definition("combat_stance")
    p_air = PoseCatalog.get_definition("mid_air_leap")  # elevation is 180.0
    interp = interpolate_poses(p_ground, p_air, t=0.5)
    assert interp.elevation > 0.0
    assert interp.support_mode == SupportMode.AIRBORNE


def test_deterministic_frame_rendering():
    """Verify identical parameters generate bit-identical pixel outputs."""
    track = AnimationTrack(
        keyframes=[
            Keyframe(time_sec=0.0, pose_name="standoff_idle"),
            Keyframe(time_sec=1.0, pose_name="combat_stance"),
        ],
        duration_sec=1.0,
        loop=False,
    )
    engine = AnimationLoopEngine()
    cfg = ActorConfig(
        actor_id="wukong",
        display_name="Dark Wukong",
        side=ActorSide.LEFT,
        skin=CharacterSkin.DARK_WUKONG,
        weapon=WeaponType.RUYI_STAFF,
        scale=0.5,
    )
    char = StickmanCharacter.from_actor_config(cfg)
    state = engine.get_state_at_time(track, 0.5)

    frame1 = engine.render_frame(char, state)
    frame2 = engine.render_frame(char, state)
    assert list(frame1.tobytes()) == list(frame2.tobytes())


def test_export_mp4_video_from_image_list(tmp_path: Path):
    """Verify export_mp4_video can stream in-memory PIL images directly to FFmpeg pipe."""
    engine = AnimationLoopEngine()
    # Generate 5 small RGBA images
    images = [
        Image.new("RGBA", (1080, 1920), (10, 10, 10 + i * 20, 255))
        for i in range(5)
    ]
    out_pipe_mp4 = tmp_path / "pipe_test.mp4"
    engine.export_mp4_video(images, out_pipe_mp4, fps=10)

    assert out_pipe_mp4.exists()
    assert out_pipe_mp4.stat().st_size > 500


def test_cubic_bezier_custom_points():
    """Verify cubic bezier evaluator handles custom control points."""
    # Fast acceleration curve (0.1, 0.9, 0.2, 1.0)
    val = evaluate_easing(EasingFunction.CUBIC_BEZIER, 0.5, p1=(0.1, 0.9), p2=(0.2, 1.0))
    assert 0.0 <= val <= 1.0
    assert val > 0.5, "Fast acceleration curve should reach > 0.5 at t=0.5"

