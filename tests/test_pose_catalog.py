"""Comprehensive Unit Tests for Dark Myth Pose Catalog (G5.2.2).

Verifies all 8 canonical poses, mathematical bone length integrity, posture features,
metadata, ground alignment compatibility, and immutability.
"""

import math
import pytest

from app.modules.animation.pose_catalog import PoseCatalog, PoseDefinition
from app.modules.animation.stickman_models import (
    CoordinateManager,
    HumanoidSkeleton,
    JointType,
    Point2D,
    RigidBoneValidator,
    StickmanPose,
    SupportMode,
)


class TestPoseCatalogTopologyAndRigidIntegrity:
    """Tests 1-6: Catalog completeness, unique names, 14 joints, and zero-error rigid bone validation."""

    def test_01_catalog_has_all_eight_poses(self) -> None:
        """Requirement 1: Catalog provides exactly eight canonical combat poses."""
        poses = PoseCatalog.list_poses()
        assert len(poses) == 8
        expected = {
            "standoff_idle",
            "combat_stance",
            "forward_charge",
            "overhead_slam",
            "mid_air_leap",
            "guard_block",
            "vortex_sweep",
            "knockback_slide",
        }
        assert set(poses) == expected

    def test_02_no_missing_or_duplicate_pose_names(self) -> None:
        """Requirement 2: No missing or duplicated pose identifiers."""
        all_defs = PoseCatalog.get_all_definitions()
        assert len(all_defs) == 8
        names = list(all_defs.keys())
        assert len(names) == len(set(names))

    def test_03_each_pose_contains_all_14_joints(self) -> None:
        """Requirement 3: Every pose contains all 14 canonical JointType items."""
        for name in PoseCatalog.list_poses() :
            pose = PoseCatalog.get_pose(name)
            assert len(pose.joints) == 14
            for joint in HumanoidSkeleton.JOINTS:
                assert joint in pose.joints, f"Pose '{name}' is missing joint {joint.value}"

    def test_04_no_nan_or_infinity_coordinates(self) -> None:
        """Requirement 4: All coordinates are finite numbers (no NaN or Inf)."""
        for name in PoseCatalog.list_poses():
            pose = PoseCatalog.get_pose(name)
            for joint, pt in pose.joints.items():
                assert math.isfinite(pt.x), f"Pose '{name}' joint {joint} has non-finite x={pt.x}"
                assert math.isfinite(pt.y), f"Pose '{name}' joint {joint} has non-finite y={pt.y}"

    def test_05_all_13_bones_pass_rigid_validator_for_all_poses(self) -> None:
        """Requirement 5: Every single pose satisfies RigidBoneValidator across all 13 bones."""
        for name in PoseCatalog.list_poses():
            pose = PoseCatalog.get_pose(name)
            result = RigidBoneValidator.validate(pose, epsilon=0.5)
            assert result.is_valid is True, f"Pose '{name}' failed validation with errors: {result.errors}"
            assert len(result.details) == 13

    def test_06_bone_deviation_strictly_under_half_pixel(self) -> None:
        """Requirement 6: Bone deviation is strictly <= 0.5 px (in fact < 1e-4 px via FK)."""
        for name in PoseCatalog.list_poses():
            pose = PoseCatalog.get_pose(name)
            result = RigidBoneValidator.validate(pose, epsilon=0.5)
            for detail in result.details:
                assert detail.deviation <= 0.5, (
                    f"Pose '{name}' bone '{detail.bone_name}' deviation {detail.deviation} > 0.5px"
                )
                # Verify pure FK precision
                assert detail.deviation == pytest.approx(0.0, abs=1e-4)


class TestPoseAnatomicalFeatures:
    """Tests 7-14: Verification of specific posture characteristics for each of the 8 poses."""

    def test_07_standoff_idle_posture_features(self) -> None:
        """Requirement 7: STANDOFF_IDLE has upright spine, vertical neck, and grounded feet."""
        defn = PoseCatalog.get_definition("standoff_idle")
        pose = defn.pose

        # Pelvis at (0, 0), chest directly above at (0, -75), neck at (0, -120), head at (0, -168)
        assert pose.joints[JointType.PELVIS].x == pytest.approx(0.0, abs=1e-5)
        assert pose.joints[JointType.CHEST].x == pytest.approx(0.0, abs=1e-5)
        assert pose.joints[JointType.HEAD].x == pytest.approx(0.0, abs=1e-5)
        assert pose.joints[JointType.CHEST].y < pose.joints[JointType.PELVIS].y
        assert pose.joints[JointType.HEAD].y < pose.joints[JointType.CHEST].y

        # Double support with ankle Y = 185
        assert pose.joints[JointType.ANKLE_L].y == pytest.approx(185.0, abs=1e-5)
        assert pose.joints[JointType.ANKLE_R].y == pytest.approx(185.0, abs=1e-5)
        assert defn.support_mode == SupportMode.DOUBLE

    def test_08_combat_stance_crouched_and_bent_knees(self) -> None:
        """Requirement 8: COMBAT_STANCE has lowered center of gravity, bent knees, and forward torso."""
        defn = PoseCatalog.get_definition("combat_stance")
        pose = defn.pose

        # Center of gravity lowered: ankle Y is 165.0 px (crouched by 20px compared to 185 standing)
        assert pose.joints[JointType.ANKLE_L].y == pytest.approx(165.0, abs=1e-5)
        assert pose.joints[JointType.ANKLE_R].y == pytest.approx(165.0, abs=1e-5)
        assert defn.support_mode == SupportMode.DOUBLE

        # Wide stance: Left foot back, Right foot forward
        assert pose.joints[JointType.ANKLE_L].x < 0.0
        assert pose.joints[JointType.ANKLE_R].x > 0.0

        # Torso leans forward (+X)
        assert pose.joints[JointType.CHEST].x > pose.joints[JointType.PELVIS].x

    def test_09_forward_charge_aggressive_forward_lean(self) -> None:
        """Requirement 9: FORWARD_CHARGE has torso leaning forward ~35 deg from vertical."""
        defn = PoseCatalog.get_definition("forward_charge")
        pose = defn.pose

        # Chest is significantly forward (+X) relative to pelvis
        assert pose.joints[JointType.CHEST].x > 35.0
        # Right foot lead support planted, left foot trailing back in extension
        assert pose.joints[JointType.ANKLE_L].x < -50.0  # Trailing leg kicked back
        assert defn.support_mode == SupportMode.RIGHT_ONLY
        assert defn.weapon_angle_deg == pytest.approx(5.0, abs=1e-5)  # Thrusting forward

    def test_10_overhead_slam_arms_raised_above_head(self) -> None:
        """Requirement 10: OVERHEAD_SLAM has both hands raised higher than head."""
        defn = PoseCatalog.get_definition("overhead_slam")
        pose = defn.pose

        head_y = pose.joints[JointType.HEAD].y
        wrist_l_y = pose.joints[JointType.WRIST_L].y
        wrist_r_y = pose.joints[JointType.WRIST_R].y

        # Hands raised above head (y coordinate is more negative)
        assert wrist_l_y < head_y
        assert wrist_r_y < head_y

        # Spine arched backward (chest x is negative relative to pelvis)
        assert pose.joints[JointType.CHEST].x < 0.0
        assert defn.support_mode == SupportMode.DOUBLE

    def test_11_mid_air_leap_airborne_elevation(self) -> None:
        """Requirement 11: MID_AIR_LEAP uses SupportMode.AIRBORNE with default elevation."""
        defn = PoseCatalog.get_definition("mid_air_leap")
        assert defn.support_mode == SupportMode.AIRBORNE
        assert defn.elevation is not None
        assert defn.elevation >= 400.0  # High leap (500px)

        # Knees are tucked up (ankle Y is much higher than standing 185)
        pose = defn.pose
        assert pose.joints[JointType.ANKLE_L].y < 120.0
        assert pose.joints[JointType.ANKLE_R].y < 140.0

    def test_12_guard_block_arms_forming_defensive_shield(self) -> None:
        """Requirement 12: GUARD_BLOCK has crossed forearms locking weapon vertically before chest."""
        defn = PoseCatalog.get_definition("guard_block")
        pose = defn.pose

        # Both wrists positioned in front of chest
        chest_x = pose.joints[JointType.CHEST].x
        assert pose.joints[JointType.WRIST_R].x > chest_x
        # Weapon angle near vertical (88 deg)
        assert defn.weapon_angle_deg == pytest.approx(88.0, abs=1e-5)
        assert defn.support_mode == SupportMode.DOUBLE

    def test_13_vortex_sweep_single_pivot_leg_and_sweeping_leg(self) -> None:
        """Requirement 13: VORTEX_SWEEP has one pivot leg and one outstretched sweeping leg."""
        defn = PoseCatalog.get_definition("vortex_sweep")
        pose = defn.pose

        assert defn.support_mode == SupportMode.LEFT_ONLY

        # Left leg is planted at ground contact (ankle Y = 185)
        assert pose.joints[JointType.ANKLE_L].y == pytest.approx(185.0, abs=1e-5)
        # Right leg is sweeping high above ground (ankle Y near 24px)
        assert pose.joints[JointType.ANKLE_R].y < 50.0
        assert pose.joints[JointType.ANKLE_R].x > 150.0  # Sweeping wide forward

        # Horizontal weapon swing
        assert defn.weapon_angle_deg == pytest.approx(0.0, abs=1e-5)

    def test_14_knockback_slide_torso_recoiling_backward(self) -> None:
        """Requirement 14: KNOCKBACK_SLIDE has torso reeled backward and braking foot."""
        defn = PoseCatalog.get_definition("knockback_slide")
        pose = defn.pose

        # Torso heavily tilted back (-X)
        assert pose.joints[JointType.CHEST].x < -40.0
        assert defn.support_mode == SupportMode.LEFT_ONLY

        # Weapon scraping ground (steep braking angle)
        assert defn.weapon_angle_deg > 100.0


class TestMetadataAndGroundIntegration:
    """Tests 15-20: Metadata verification, immutability, error handling, and coordinate alignment."""

    def test_15_support_mode_metadata_verified_for_all_poses(self) -> None:
        """Requirement 15: SupportMode metadata is correctly configured across all 8 poses."""
        expected_modes = {
            "standoff_idle": SupportMode.DOUBLE,
            "combat_stance": SupportMode.DOUBLE,
            "forward_charge": SupportMode.RIGHT_ONLY,
            "overhead_slam": SupportMode.DOUBLE,
            "mid_air_leap": SupportMode.AIRBORNE,
            "guard_block": SupportMode.DOUBLE,
            "vortex_sweep": SupportMode.LEFT_ONLY,
            "knockback_slide": SupportMode.LEFT_ONLY,
        }
        for name, exp_mode in expected_modes.items():
            defn = PoseCatalog.get_definition(name)
            assert defn.support_mode == exp_mode

    def test_16_airborne_elevation_metadata_verification(self) -> None:
        """Requirement 16: Airborne poses have positive finite elevation metadata."""
        defn = PoseCatalog.get_definition("mid_air_leap")
        assert defn.support_mode == SupportMode.AIRBORNE
        assert defn.elevation is not None
        assert math.isfinite(defn.elevation)
        assert defn.elevation > 0.0

    def test_17_returned_pose_does_not_mutate_catalog(self) -> None:
        """Requirement 17: Querying poses does not allow caller to mutate the internal catalog."""
        pose1 = PoseCatalog.get_pose("standoff_idle")
        head_pt = pose1.joints[JointType.HEAD]

        # Attempt to modify a copy or external dict
        mutated_joints = dict(pose1.joints)
        mutated_joints[JointType.HEAD] = Point2D(999.0, 999.0)

        # Retrieve again from catalog
        pose2 = PoseCatalog.get_pose("standoff_idle")
        assert pose2.joints[JointType.HEAD] == head_pt
        assert pose2.joints[JointType.HEAD] != Point2D(999.0, 999.0)

    def test_18_invalid_pose_name_raises_key_error(self) -> None:
        """Requirement 18: Requesting non-existent pose raises clear KeyError."""
        with pytest.raises(KeyError, match="Unknown pose 'ninja_kick'"):
            PoseCatalog.get_pose("ninja_kick")

        with pytest.raises(KeyError, match="Unknown pose 'dragon_punch'"):
            PoseCatalog.get_definition("dragon_punch")

    def test_19_ground_contact_alignment_compatibility(self) -> None:
        """Requirement 19: All grounded poses compute valid canvas pelvis Y via CoordinateManager."""
        ground_y = 1420.0
        for name in PoseCatalog.list_poses():
            defn = PoseCatalog.get_definition(name)
            if defn.support_mode in (SupportMode.DOUBLE, SupportMode.LEFT_ONLY, SupportMode.RIGHT_ONLY):
                root_y = CoordinateManager.get_ground_aligned_root_y(
                    pose=defn.pose,
                    support_mode=defn.support_mode,
                    ground_y=ground_y,
                    scale=1.0,
                )
                assert math.isfinite(root_y)
                # Ensure calculated pelvis Y is reasonably above ground
                assert root_y < ground_y
                assert root_y > ground_y - 300.0  # Standing height is ~190px

    def test_20_legacy_api_compatibility_with_asymmetric_poses(self) -> None:
        """Requirement 20: Legacy get_canvas_pelvis_y functions seamlessly with all catalog poses."""
        for name in PoseCatalog.list_poses():
            pose = PoseCatalog.get_pose(name)
            # Call legacy API with positional arguments
            root_y = CoordinateManager.get_canvas_pelvis_y(pose, 1.0, 0.0, 1420.0)
            assert math.isfinite(root_y)
            assert root_y < 1420.0


class TestPoseCatalogImmutabilityAndDefensiveCopy:
    """G5.2.3.0.1 Immutability Audit: Proves internal PoseCatalog cannot be mutated by callers."""

    def test_21_direct_mutation_of_get_pose_joints_does_not_affect_catalog(self) -> None:
        """Modifying joints dict on pose returned from get_pose() does not corrupt catalog."""
        pose = PoseCatalog.get_pose("standoff_idle")
        orig_head = Point2D(0.0, -168.0)
        assert pose.joints[JointType.HEAD] == orig_head

        # Direct in-place mutation of the joints dict
        pose.joints[JointType.HEAD] = Point2D(999.0, 999.0)
        assert pose.joints[JointType.HEAD] == Point2D(999.0, 999.0)

        # Fresh retrieval must remain pristine
        fresh_pose = PoseCatalog.get_pose("standoff_idle")
        assert fresh_pose.joints[JointType.HEAD] == orig_head
        assert fresh_pose.joints[JointType.HEAD] != Point2D(999.0, 999.0)

    def test_22_direct_mutation_of_get_definition_joints_does_not_affect_catalog(self) -> None:
        """Modifying joints dict on pose inside PoseDefinition does not corrupt catalog."""
        defn = PoseCatalog.get_definition("combat_stance")
        orig_pelvis = Point2D(0.0, 0.0)
        assert defn.pose.joints[JointType.PELVIS] == orig_pelvis

        # Mutate definition's pose joints
        defn.pose.joints[JointType.PELVIS] = Point2D(777.0, 888.0)
        assert defn.pose.joints[JointType.PELVIS] == Point2D(777.0, 888.0)

        # Fresh definition must remain pristine
        fresh_defn = PoseCatalog.get_definition("combat_stance")
        assert fresh_defn.pose.joints[JointType.PELVIS] == orig_pelvis

    def test_23_direct_mutation_of_get_all_definitions_does_not_affect_catalog(self) -> None:
        """Modifying dict or elements returned by get_all_definitions() does not corrupt catalog."""
        all_defs = PoseCatalog.get_all_definitions()
        assert len(all_defs) == 8

        # Mutate joint inside one entry and delete another entry
        all_defs["standoff_idle"].pose.joints[JointType.ANKLE_L] = Point2D(123.0, 456.0)
        del all_defs["combat_stance"]
        assert len(all_defs) == 7

        # Fresh get_all_definitions must be complete and uncorrupted
        fresh_defs = PoseCatalog.get_all_definitions()
        assert len(fresh_defs) == 8
        assert "combat_stance" in fresh_defs
        assert fresh_defs["standoff_idle"].pose.joints[JointType.ANKLE_L] == Point2D(0.0, 185.0)

    def test_24_two_consecutive_calls_return_independent_instances(self) -> None:
        """Consecutive queries return distinct dictionary and object instances."""
        pose_a = PoseCatalog.get_pose("forward_charge")
        pose_b = PoseCatalog.get_pose("forward_charge")

        assert pose_a is not pose_b
        assert pose_a.joints is not pose_b.joints
        # But contents are geometrically equal
        assert pose_a.joints == pose_b.joints

    def test_25_two_handed_secondary_grip_metadata(self) -> None:
        """Verify secondary_grip metadata for two-handed poses vs single-handed poses."""
        two_handed_poses = {"combat_stance", "overhead_slam", "guard_block"}
        single_handed_poses = set(PoseCatalog.list_poses()) - two_handed_poses

        for name in two_handed_poses:
            defn = PoseCatalog.get_definition(name)
            assert defn.secondary_grip == JointType.WRIST_L, f"Pose '{name}' should have WRIST_L as secondary_grip"

        for name in single_handed_poses:
            defn = PoseCatalog.get_definition(name)
            assert defn.secondary_grip is None, f"Pose '{name}' should have secondary_grip=None"

