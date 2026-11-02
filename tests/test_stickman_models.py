"""Unit Tests for Dark Myth Stickman Skeleton, Rigid Bone Validator, and Character Models (G5.2.1)."""

import math
import subprocess
import sys

import pytest

from app.modules.animation.stickman_models import (
    BoneDefinition,
    CoordinateManager,
    HumanoidSkeleton,
    JointType,
    Point2D,
    RigidBoneValidator,
    StickmanCharacter,
    StickmanPose,
    SupportMode,
    generate_actor_seed,
    parse_hex_color,
)
from app.schemas.scene_schema import ActorConfig, ActorSide, CharacterSkin, WeaponType


class TestStickmanSkeletonTopology:
    """Tests 1-5: Verification of 14 joints, 13 bones, topology tree, and rest lengths."""

    def test_01_all_14_joints_defined(self) -> None:
        """Requirement 1: Verify exactly 14 canonical JointType items exist."""
        expected_joints = {
            "head",
            "neck",
            "chest",
            "pelvis",
            "shoulder_l",
            "elbow_l",
            "wrist_l",
            "shoulder_r",
            "elbow_r",
            "wrist_r",
            "knee_l",
            "ankle_l",
            "knee_r",
            "ankle_r",
        }
        actual_joints = {j.value for j in JointType}
        assert actual_joints == expected_joints
        assert len(HumanoidSkeleton.JOINTS) == 14

    def test_02_all_13_bones_defined(self) -> None:
        """Requirement 2: Verify exactly 13 BoneDefinition segments are defined."""
        assert len(HumanoidSkeleton.BONES) == 13
        bone_names = [b.name for b in HumanoidSkeleton.BONES]
        assert len(set(bone_names)) == 13, "Bone names must be unique"

    def test_03_no_orphaned_joints(self) -> None:
        """Requirement 3: Verify no joint is orphaned (all non-root joints have parent)."""
        for joint in HumanoidSkeleton.JOINTS:
            if joint == HumanoidSkeleton.ROOT_JOINT:
                assert HumanoidSkeleton.PARENT_MAP[joint] is None
            else:
                parent = HumanoidSkeleton.PARENT_MAP[joint]
                assert parent is not None, f"Joint {joint} is orphaned with no parent"
                assert parent in HumanoidSkeleton.JOINTS, f"Parent {parent} is invalid"

    def test_04_parent_child_relationships(self) -> None:
        """Requirement 4: Verify bidirectional parent-child consistency."""
        for joint, children in HumanoidSkeleton.CHILDREN_MAP.items():
            for child in children:
                assert HumanoidSkeleton.PARENT_MAP[child] == joint, (
                    f"Child {child} does not reference parent {joint}"
                )

        # Confirm Pelvis has 3 direct children: chest, knee_l, knee_r
        pelvis_children = set(HumanoidSkeleton.CHILDREN_MAP[JointType.PELVIS])
        assert pelvis_children == {JointType.CHEST, JointType.KNEE_L, JointType.KNEE_R}

        # Confirm Chest has 3 direct children: neck, shoulder_l, shoulder_r
        chest_children = set(HumanoidSkeleton.CHILDREN_MAP[JointType.CHEST])
        assert chest_children == {JointType.NECK, JointType.SHOULDER_L, JointType.SHOULDER_R}

    def test_05_canonical_rest_lengths(self) -> None:
        """Requirement 5: Verify exact rest lengths for all 13 bones matching G5.2.0 spec."""
        expected_lengths = {
            "neck_head": 48.0,
            "chest_neck": 45.0,
            "pelvis_chest": 75.0,
            "chest_shoulder_l": 32.0,
            "shoulder_l_elbow_l": 68.0,
            "elbow_l_wrist_l": 62.0,
            "chest_shoulder_r": 32.0,
            "shoulder_r_elbow_r": 68.0,
            "elbow_r_wrist_r": 62.0,
            "pelvis_knee_l": 95.0,
            "knee_l_ankle_l": 90.0,
            "pelvis_knee_r": 95.0,
            "knee_r_ankle_r": 90.0,
        }
        for bone in HumanoidSkeleton.BONES:
            assert bone.length == pytest.approx(expected_lengths[bone.name], abs=1e-5)


class TestPoseAndRigidValidation:
    """Tests 6-10: Pose creation, validation rejection, and non-mutating rigid bone validator."""

    def test_06_reject_pose_with_missing_joints(self) -> None:
        """Requirement 6: Reject pose that omits any of the 14 joints."""
        full_pose = HumanoidSkeleton.create_neutral_standing_pose()
        incomplete_joints = {k: v for k, v in full_pose.joints.items() if k != JointType.HEAD}

        with pytest.raises(ValueError, match="missing required joints.*head"):
            StickmanPose(name="missing_head", joints=incomplete_joints)

    def test_07_reject_nan_or_inf_coordinates(self) -> None:
        """Requirement 7: Reject NaN or Infinity coordinates in Point2D."""
        with pytest.raises(ValueError, match="finite numbers.*nan"):
            Point2D(float("nan"), 100.0)

        with pytest.raises(ValueError, match="finite numbers.*inf"):
            Point2D(0.0, float("inf"))

        with pytest.raises(ValueError, match="finite numbers.*-inf"):
            Point2D(float("-inf"), 0.0)

    def test_08_validator_pass_for_canonical_pose(self) -> None:
        """Requirement 8: Neutral standing pose passes rigid validation with zero error."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        result = RigidBoneValidator.validate(pose, epsilon=0.5)

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.details) == 13

        for detail in result.details:
            assert detail.is_valid is True
            assert detail.deviation == pytest.approx(0.0, abs=1e-4)

    def test_09_validator_fail_for_stretched_bone(self) -> None:
        """Requirement 9: Validator fails when any bone distance deviates beyond epsilon."""
        canonical = HumanoidSkeleton.create_neutral_standing_pose()
        corrupted_joints = dict(canonical.joints)
        # Stretch head 15px upwards (from -168 to -183)
        corrupted_joints[JointType.HEAD] = Point2D(0.0, -183.0)

        bad_pose = StickmanPose(name="stretched_head", joints=corrupted_joints)
        result = RigidBoneValidator.validate(bad_pose, epsilon=0.5)

        assert result.is_valid is False
        assert len(result.errors) >= 1
        assert any("neck_head" in err for err in result.errors)

    def test_10_validation_does_not_mutate_original_pose(self) -> None:
        """Requirement 10: Validation and enforcement do not mutate the input pose."""
        canonical = HumanoidSkeleton.create_neutral_standing_pose()
        orig_head_pos = canonical.joints[JointType.HEAD]

        corrupted_joints = dict(canonical.joints)
        corrupted_joints[JointType.HEAD] = Point2D(0.0, -183.0)
        bad_pose = StickmanPose(name="bad_pose", joints=corrupted_joints)

        # Run validation
        RigidBoneValidator.validate(bad_pose)
        assert bad_pose.joints[JointType.HEAD] == Point2D(0.0, -183.0)

        # Run enforcement
        enforced = RigidBoneValidator.enforce_rigid_lengths(bad_pose)
        # bad_pose remains stretched
        assert bad_pose.joints[JointType.HEAD] == Point2D(0.0, -183.0)
        # enforced is a new pose with head reset to exact rest length
        assert enforced.joints[JointType.HEAD] == orig_head_pos
        enforced_res = RigidBoneValidator.validate(enforced)
        assert enforced_res.is_valid is True


class TestCoordinateManager:
    """Tests 11-14: Ground contact, ankle center vs foot extent, facing, and canvas mapping."""

    def test_11_ground_anchor_formula(self) -> None:
        """Requirement 11: Canvas pelvis Y correctly anchors feet to ground line."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        # For standing pose at scale=1.0, elevation=0.0:
        # local contact Y = 190.0, canvas pelvis Y must be exactly 1420 - 190 = 1230.0
        pelvis_y = CoordinateManager.get_canvas_pelvis_y(pose, scale=1.0, elevation=0.0)
        assert pelvis_y == pytest.approx(1230.0, abs=1e-5)

        # With elevation 300px (airborne):
        elev_pelvis_y = CoordinateManager.get_canvas_pelvis_y(pose, scale=1.0, elevation=300.0)
        assert elev_pelvis_y == pytest.approx(930.0, abs=1e-5)

    def test_12_distinguish_ankle_center_and_foot_contact(self) -> None:
        """Requirement 12: Ankle center (185px) and foot sole contact (190px) are distinct."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        sp = CoordinateManager.get_support_points(pose)

        assert sp["ankle_l_center"] == pytest.approx(185.0, abs=1e-5)
        assert sp["ankle_r_center"] == pytest.approx(185.0, abs=1e-5)
        assert sp["foot_l_bottom"] == pytest.approx(190.0, abs=1e-5)
        assert sp["foot_r_bottom"] == pytest.approx(190.0, abs=1e-5)

        # Test asymmetric stance (one leg bent up)
        asym_joints = dict(pose.joints)
        asym_joints[JointType.ANKLE_L] = Point2D(-30.0, 140.0)  # lifted
        asym_pose = StickmanPose(name="one_leg", joints=asym_joints)

        asym_sp = CoordinateManager.get_support_points(asym_pose)
        assert asym_sp["foot_l_bottom"] == pytest.approx(145.0, abs=1e-5)
        assert asym_sp["foot_r_bottom"] == pytest.approx(190.0, abs=1e-5)
        # Lowest contact must track the standing right foot (190px)
        assert CoordinateManager.get_ground_contact_y(asym_pose) == pytest.approx(190.0, abs=1e-5)

    def test_13_facing_direction_rules(self) -> None:
        """Requirement 13: LEFT->+1, RIGHT->-1, CENTER->+1, TOP requires override."""
        assert CoordinateManager.get_facing(ActorSide.LEFT) == +1
        assert CoordinateManager.get_facing(ActorSide.RIGHT) == -1
        assert CoordinateManager.get_facing(ActorSide.CENTER) == +1
        assert CoordinateManager.get_facing(ActorSide.CENTER, override_facing=-1) == -1

        # TOP without override raises ValueError
        with pytest.raises(ValueError, match="ActorSide.TOP does not convey facing direction"):
            CoordinateManager.get_facing(ActorSide.TOP)

        # TOP with explicit override passes
        assert CoordinateManager.get_facing(ActorSide.TOP, override_facing=+1) == +1
        assert CoordinateManager.get_facing(ActorSide.TOP, override_facing=-1) == -1

    def test_14_local_to_canvas_transformation(self) -> None:
        """Requirement 14: Local coordinates map correctly with facing and scale."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        pelvis_canvas = Point2D(540.0, 1230.0)

        # Facing Right (+1), scale 1.0
        canvas_pose_r = CoordinateManager.transform_pose_to_canvas(
            pose, pelvis_canvas, facing=+1, scale=1.0
        )
        assert canvas_pose_r.joints[JointType.PELVIS] == Point2D(540.0, 1230.0)
        assert canvas_pose_r.joints[JointType.SHOULDER_R] == Point2D(540.0 + 32.0, 1230.0 - 75.0)
        assert canvas_pose_r.joints[JointType.SHOULDER_L] == Point2D(540.0 - 32.0, 1230.0 - 75.0)
        assert canvas_pose_r.joints[JointType.ANKLE_R] == Point2D(540.0, 1415.0)

        # Facing Left (-1), scale 1.0 (X should mirror around 540)
        canvas_pose_l = CoordinateManager.transform_pose_to_canvas(
            pose, pelvis_canvas, facing=-1, scale=1.0
        )
        assert canvas_pose_l.joints[JointType.PELVIS] == Point2D(540.0, 1230.0)
        # Local +32 facing -1 maps to 540 - 32 = 508
        assert canvas_pose_l.joints[JointType.SHOULDER_R] == Point2D(540.0 - 32.0, 1230.0 - 75.0)
        # Local -32 facing -1 maps to 540 + 32 = 572
        assert canvas_pose_l.joints[JointType.SHOULDER_L] == Point2D(540.0 + 32.0, 1230.0 - 75.0)


class TestCharacterModelAndDeterministicSeed:
    """Tests 15-17: ActorConfig mapping, scale constraints, and cross-process deterministic seed."""

    def test_15_reject_invalid_scale(self) -> None:
        """Requirement 15: Scale <= 0.1 or > 5.0 or non-finite is rejected."""
        with pytest.raises(ValueError, match="scale must be in range"):
            StickmanCharacter(
                actor_id="wukong",
                skin=CharacterSkin.DARK_WUKONG,
                stroke_color=(20, 20, 22, 255),
                aura_color=(217, 38, 38, 255),
                weapon=WeaponType.RUYI_STAFF,
                scale=0.05,  # <= 0.1
                side=ActorSide.LEFT,
                display_name="Ngộ Không",
                seed=12345,
            )

        with pytest.raises(ValueError, match="scale must be in range"):
            StickmanCharacter(
                actor_id="wukong",
                skin=CharacterSkin.DARK_WUKONG,
                stroke_color=(20, 20, 22, 255),
                aura_color=(217, 38, 38, 255),
                weapon=WeaponType.RUYI_STAFF,
                scale=5.5,  # > 5.0
                side=ActorSide.LEFT,
                display_name="Ngộ Không",
                seed=12345,
            )

    def test_16_from_actor_config_compatibility(self) -> None:
        """Requirement 16: Character seamlessly constructed from ActorConfig."""
        config = ActorConfig(
            actor_id="wukong_boss",
            skin=CharacterSkin.DARK_WUKONG,
            color="#D92626",
            weapon=WeaponType.RUYI_STAFF,
            display_name="Ngộ Không Hắc Hóa",
            side=ActorSide.LEFT,
            scale=1.1,
        )
        char = StickmanCharacter.from_actor_config(config)

        assert char.actor_id == "wukong_boss"
        assert char.skin == CharacterSkin.DARK_WUKONG
        assert char.stroke_color == (20, 20, 22, 255)  # #141416
        assert char.aura_color == (217, 38, 38, 255)   # #D92626
        assert char.weapon == WeaponType.RUYI_STAFF
        assert char.scale == 1.1
        assert char.side == ActorSide.LEFT
        assert char.display_name == "Ngộ Không Hắc Hóa"
        assert char.seed > 0

    def test_17_deterministic_seed_across_independent_processes(self) -> None:
        """Requirement 17: SHA-256 seed is identical across independent Python processes."""
        actor_id = "dark_wukong_hero_01"
        in_process_seed = generate_actor_seed(actor_id)

        # Run external Python subprocess to verify process-independence
        cmd = [
            sys.executable,
            "-c",
            f"from app.modules.animation.stickman_models import generate_actor_seed; print(generate_actor_seed('{actor_id}'))",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        sub_seed = int(result.stdout.strip())

        assert in_process_seed == sub_seed, (
            f"Seed mismatch across processes: in-proc={in_process_seed}, sub-proc={sub_seed}"
        )


class TestGroundContactAndSupportFeet:
    """G5.2.1.1 Audit: Verification of 3 ground contact support modes (Double, Single, Airborne)."""

    def test_01_double_support_both_feet_grounded(self) -> None:
        """Item 1: Both feet on ground in neutral standing pose align to ground_y."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        root_y = CoordinateManager.get_ground_aligned_root_y(
            pose, support_mode=SupportMode.DOUBLE, ground_y=1420.0, scale=1.0
        )
        assert root_y == pytest.approx(1230.0, abs=1e-5)

        # Confirm both feet bottom points land exactly on 1420.0
        left_foot_bottom_canvas = root_y + (pose.joints[JointType.ANKLE_L].y + CoordinateManager.FOOT_EXTENT)
        right_foot_bottom_canvas = root_y + (pose.joints[JointType.ANKLE_R].y + CoordinateManager.FOOT_EXTENT)
        assert left_foot_bottom_canvas == pytest.approx(1420.0, abs=1e-5)
        assert right_foot_bottom_canvas == pytest.approx(1420.0, abs=1e-5)

    def test_02_single_support_left_foot_anchors_pelvis(self) -> None:
        """Item 2: Left foot is sole support anchor; pelvis Y calculated from left foot."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        asym_joints = dict(pose.joints)
        # Lift right foot by 45px (ankle Y: 185 -> 140)
        asym_joints[JointType.ANKLE_R] = Point2D(20.0, 140.0)
        asym_pose = StickmanPose(name="kick_right", joints=asym_joints)

        root_y = CoordinateManager.get_ground_aligned_root_y(
            asym_pose, support_mode=SupportMode.LEFT_ONLY, ground_y=1420.0, scale=1.0
        )
        # Root Y is anchored to left foot: 1420 - 190 = 1230
        assert root_y == pytest.approx(1230.0, abs=1e-5)
        left_bottom = root_y + (asym_pose.joints[JointType.ANKLE_L].y + CoordinateManager.FOOT_EXTENT)
        assert left_bottom == pytest.approx(1420.0, abs=1e-5)

    def test_03_single_support_right_foot_anchors_pelvis(self) -> None:
        """Item 3: Right foot is sole support anchor; pelvis Y calculated from right foot."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        asym_joints = dict(pose.joints)
        # Lift left foot by 55px (ankle Y: 185 -> 130)
        asym_joints[JointType.ANKLE_L] = Point2D(-20.0, 130.0)
        asym_pose = StickmanPose(name="kick_left", joints=asym_joints)

        root_y = CoordinateManager.get_ground_aligned_root_y(
            asym_pose, support_mode=SupportMode.RIGHT_ONLY, ground_y=1420.0, scale=1.0
        )
        # Root Y is anchored to right foot: 1420 - 190 = 1230
        assert root_y == pytest.approx(1230.0, abs=1e-5)
        right_bottom = root_y + (asym_pose.joints[JointType.ANKLE_R].y + CoordinateManager.FOOT_EXTENT)
        assert right_bottom == pytest.approx(1420.0, abs=1e-5)

    def test_04_non_support_foot_lifted_above_ground(self) -> None:
        """Item 4: Non-support foot is strictly elevated above ground line Y_ground."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        asym_joints = dict(pose.joints)
        asym_joints[JointType.ANKLE_R] = Point2D(25.0, 140.0)  # lifted
        asym_pose = StickmanPose(name="stork_stance", joints=asym_joints)

        root_y = CoordinateManager.get_ground_aligned_root_y(
            asym_pose, support_mode=SupportMode.LEFT_ONLY, ground_y=1420.0, scale=1.0
        )
        right_foot_canvas = root_y + (asym_pose.joints[JointType.ANKLE_R].y + CoordinateManager.FOOT_EXTENT)
        # Raised foot canvas Y must be strictly smaller than 1420.0 (higher on canvas)
        assert right_foot_canvas < 1420.0
        assert right_foot_canvas == pytest.approx(1230.0 + 145.0, abs=1e-5)  # 1375.0 (45px clearance)

    def test_05_airborne_jump_with_elevation(self) -> None:
        """Item 5: Jumping character uses elevation relative to ground reference."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        jump_elevation = 400.0  # 400px above ground reference (190px)

        root_y = CoordinateManager.get_ground_aligned_root_y(
            pose, support_mode=SupportMode.AIRBORNE, ground_y=1420.0, elevation=jump_elevation
        )
        # pelvis_y = 1420 - 190 - 400 = 830.0
        assert root_y == pytest.approx(830.0, abs=1e-5)

        # Feet are floating in air, 400px above ground
        foot_bottom_canvas = root_y + 190.0
        assert foot_bottom_canvas == pytest.approx(1020.0, abs=1e-5)
        assert foot_bottom_canvas < 1420.0
        assert foot_bottom_canvas < 1420.0

    def test_06_airborne_flight_with_explicit_canvas_y(self) -> None:
        """Item 6: Flying entity (e.g. Erlang Shen at Y=720) uses explicit_canvas_y."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        fly_y = 720.0

        root_y = CoordinateManager.get_ground_aligned_root_y(
            pose, support_mode=SupportMode.AIRBORNE, explicit_canvas_y=fly_y
        )
        assert root_y == pytest.approx(720.0, abs=1e-5)

    def test_07_double_support_incompatible_feet_rejected(self) -> None:
        """Item 7: Double support raises ValueError if feet contact heights differ beyond tolerance."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        asym_joints = dict(pose.joints)
        asym_joints[JointType.ANKLE_R] = Point2D(10.0, 160.0)  # 25px height difference
        incompatible_pose = StickmanPose(name="incompatible_double", joints=asym_joints)

        with pytest.raises(ValueError, match="Incompatible double support.*differ by 25.00px"):
            CoordinateManager.get_ground_aligned_root_y(
                incompatible_pose, support_mode=SupportMode.DOUBLE, double_support_tolerance=1.5
            )

    def test_08_ground_aligned_scale_greater_than_one(self) -> None:
        """Item 8: Correct ground alignment when scale > 1.0 (e.g. scale = 1.25)."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        scale = 1.25

        root_y = CoordinateManager.get_ground_aligned_root_y(
            pose, support_mode=SupportMode.DOUBLE, ground_y=1420.0, scale=scale
        )
        # Expected root: 1420 - (190.0 * 1.25) = 1420 - 237.5 = 1182.5
        assert root_y == pytest.approx(1182.5, abs=1e-5)

        # Foot bottom on canvas: 1182.5 + (190.0 * 1.25) = 1420.0
        foot_bottom_canvas = root_y + (190.0 * scale)
        assert foot_bottom_canvas == pytest.approx(1420.0, abs=1e-5)

    def test_09_ground_aligned_scale_less_than_one(self) -> None:
        """Item 9: Correct ground alignment when scale < 1.0 (e.g. scale = 0.8)."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        scale = 0.8

        root_y = CoordinateManager.get_ground_aligned_root_y(
            pose, support_mode=SupportMode.DOUBLE, ground_y=1420.0, scale=scale
        )
        # Expected root: 1420 - (190.0 * 0.8) = 1420 - 152.0 = 1268.0
        assert root_y == pytest.approx(1268.0, abs=1e-5)

        # Foot bottom on canvas: 1268.0 + (190.0 * 0.8) = 1420.0
        foot_bottom_canvas = root_y + (190.0 * scale)
        assert foot_bottom_canvas == pytest.approx(1420.0, abs=1e-5)

    def test_10_ground_aligned_does_not_mutate_pose(self) -> None:
        """Item 10: Input pose remains 100% immutable across all support mode calculations."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        orig_pelvis = pose.joints[JointType.PELVIS]
        orig_ankle_l = pose.joints[JointType.ANKLE_L]
        orig_ankle_r = pose.joints[JointType.ANKLE_R]

        # Execute multiple alignment queries
        CoordinateManager.get_ground_aligned_root_y(pose, support_mode=SupportMode.DOUBLE)
        CoordinateManager.get_ground_aligned_root_y(pose, support_mode=SupportMode.LEFT_ONLY)
        CoordinateManager.get_ground_aligned_root_y(pose, support_mode=SupportMode.RIGHT_ONLY)
        CoordinateManager.get_ground_aligned_root_y(
            pose, support_mode=SupportMode.AIRBORNE, explicit_canvas_y=500.0
        )

        assert pose.joints[JointType.PELVIS] == orig_pelvis
        assert pose.joints[JointType.ANKLE_L] == orig_ankle_l
        assert pose.joints[JointType.ANKLE_R] == orig_ankle_r

    def test_11_reject_invalid_support_mode_and_parameters(self) -> None:
        """Item 11: Rejects unknown support mode, missing airborne parameters, and invalid scale."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()

        # Invalid mode name
        with pytest.raises(ValueError, match="Invalid support_mode: 'invalid_mode'"):
            CoordinateManager.get_ground_aligned_root_y(pose, support_mode="invalid_mode")

        # Airborne with neither explicit_canvas_y nor elevation
        with pytest.raises(ValueError, match="SupportMode.AIRBORNE requires either 'explicit_canvas_y' or 'elevation'"):
            CoordinateManager.get_ground_aligned_root_y(pose, support_mode=SupportMode.AIRBORNE)

        # Invalid scale
        with pytest.raises(ValueError, match="scale must be in range"):
            CoordinateManager.get_ground_aligned_root_y(pose, scale=0.05)
        with pytest.raises(ValueError, match="scale must be in range"):
            CoordinateManager.get_ground_aligned_root_y(pose, scale=6.0)


class TestAirborneElevationAndBackwardCompatibility:
    """G5.2.1.2 Audit: Verification of Airborne elevation semantics, Double Support X-variation, and Legacy API."""

    def test_01_airborne_elevation_zero_matches_ground_reference(self) -> None:
        """Item 1: AIRBORNE elevation 0 matches standard ground reference root position (1230.0)."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        root_y = CoordinateManager.get_ground_aligned_root_y(
            pose, support_mode=SupportMode.AIRBORNE, ground_y=1420.0, scale=1.0, elevation=0.0
        )
        # pelvis_y = 1420 - (190 * 1.0) - 0 = 1230.0
        assert root_y == pytest.approx(1230.0, abs=1e-5)

    def test_02_airborne_elevation_400_yields_830(self) -> None:
        """Item 2: AIRBORNE elevation 400 yields pelvis Y = 830 in canonical configuration."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        root_y = CoordinateManager.get_ground_aligned_root_y(
            pose, support_mode=SupportMode.AIRBORNE, ground_y=1420.0, scale=1.0, elevation=400.0
        )
        # pelvis_y = 1420 - 190 - 400 = 830.0
        assert root_y == pytest.approx(830.0, abs=1e-5)

    def test_03_airborne_elevation_800_yields_430(self) -> None:
        """Item 3: AIRBORNE elevation 800 yields pelvis Y = 430 (Sky leap slam)."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        root_y = CoordinateManager.get_ground_aligned_root_y(
            pose, support_mode=SupportMode.AIRBORNE, ground_y=1420.0, scale=1.0, elevation=800.0
        )
        # pelvis_y = 1420 - 190 - 800 = 430.0
        assert root_y == pytest.approx(430.0, abs=1e-5)

    def test_04_airborne_with_scale_1_25(self) -> None:
        """Item 4: AIRBORNE with scale 1.25 correctly scales ground reference offset."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        scale = 1.25
        elevation = 400.0
        root_y = CoordinateManager.get_ground_aligned_root_y(
            pose, support_mode=SupportMode.AIRBORNE, ground_y=1420.0, scale=scale, elevation=elevation
        )
        # pelvis_y = 1420 - (190 * 1.25) - 400 = 1420 - 237.5 - 400 = 782.5
        assert root_y == pytest.approx(782.5, abs=1e-5)

    def test_05_airborne_with_explicit_canvas_y(self) -> None:
        """Item 5: AIRBORNE with explicit_canvas_y = 720 yields exact 720.0."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        root_y = CoordinateManager.get_ground_aligned_root_y(
            pose, support_mode=SupportMode.AIRBORNE, explicit_canvas_y=720.0
        )
        assert root_y == pytest.approx(720.0, abs=1e-5)

    def test_06_explicit_canvas_y_not_double_applied_with_elevation(self) -> None:
        """Item 6: explicit_canvas_y takes precedence and is not offset by elevation."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        root_y = CoordinateManager.get_ground_aligned_root_y(
            pose, support_mode=SupportMode.AIRBORNE, explicit_canvas_y=720.0, elevation=400.0
        )
        # Must return exactly 720.0, ignoring elevation
        assert root_y == pytest.approx(720.0, abs=1e-5)

    def test_07_legacy_api_positional_arguments(self) -> None:
        """Item 7: Legacy API get_canvas_pelvis_y called with positional arguments."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        # Positional: pose, scale=1.0, elevation=300.0, ground_y=1420.0
        root_y = CoordinateManager.get_canvas_pelvis_y(pose, 1.0, 300.0, 1420.0)
        assert root_y == pytest.approx(930.0, abs=1e-5)

        # Positional with asymmetric pose (G5.2.1 backward compatibility)
        asym_joints = dict(pose.joints)
        asym_joints[JointType.ANKLE_L] = Point2D(-30.0, 140.0)  # lifted
        asym_pose = StickmanPose(name="asym_legacy", joints=asym_joints)
        asym_root_y = CoordinateManager.get_canvas_pelvis_y(asym_pose, 1.0, 0.0, 1420.0)
        assert asym_root_y == pytest.approx(1230.0, abs=1e-5)

    def test_08_legacy_api_keyword_arguments(self) -> None:
        """Item 8: Legacy API get_canvas_pelvis_y called with keyword arguments."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        root_y = CoordinateManager.get_canvas_pelvis_y(
            pose, scale=1.25, elevation=50.0, ground_y=1420.0
        )
        # 1420 - (190 * 1.25) - 50 = 1420 - 237.5 - 50 = 1132.5
        assert root_y == pytest.approx(1132.5, abs=1e-5)

    def test_09_different_x_same_y_passes_double_support(self) -> None:
        """Item 9: Feet with different X coordinates (wide stance) but equal Y PASS Double Support."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        wide_joints = dict(pose.joints)
        # Left foot wide at X = -50, Right foot wide at X = +50, both at Y = 185
        wide_joints[JointType.ANKLE_L] = Point2D(-50.0, 185.0)
        wide_joints[JointType.ANKLE_R] = Point2D(50.0, 185.0)
        wide_pose = StickmanPose(name="wide_stance", joints=wide_joints)

        root_y = CoordinateManager.get_ground_aligned_root_y(
            wide_pose, support_mode=SupportMode.DOUBLE, ground_y=1420.0, scale=1.0
        )
        assert root_y == pytest.approx(1230.0, abs=1e-5)

    def test_10_different_y_exceeding_tolerance_rejected(self) -> None:
        """Item 10: Feet with Y difference exceeding tolerance are rejected with ValueError."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        uneven_joints = dict(pose.joints)
        # Left foot at 185, Right foot at 175 (diff = 10px > 1.5px tolerance)
        uneven_joints[JointType.ANKLE_L] = Point2D(0.0, 185.0)
        uneven_joints[JointType.ANKLE_R] = Point2D(0.0, 175.0)
        uneven_pose = StickmanPose(name="uneven_feet", joints=uneven_joints)

        with pytest.raises(ValueError, match="Incompatible double support.*differ by 10.00px"):
            CoordinateManager.get_ground_aligned_root_y(
                uneven_pose, support_mode=SupportMode.DOUBLE, double_support_tolerance=1.5
            )

    def test_11_input_pose_immutability(self) -> None:
        """Item 11: Input pose is strictly preserved across all calculations without mutation."""
        pose = HumanoidSkeleton.create_neutral_standing_pose()
        orig_joints_snapshot = {k: Point2D(v.x, v.y) for k, v in pose.joints.items()}

        # Perform multiple calculations
        CoordinateManager.get_ground_aligned_root_y(pose, support_mode=SupportMode.AIRBORNE, elevation=400.0)
        CoordinateManager.get_ground_aligned_root_y(pose, support_mode=SupportMode.AIRBORNE, explicit_canvas_y=720.0)
        CoordinateManager.get_canvas_pelvis_y(pose, 1.0, 100.0, 1420.0)

        for joint_type, original_point in orig_joints_snapshot.items():
            current_point = pose.joints[joint_type]
            assert current_point.x == original_point.x
            assert current_point.y == original_point.y


