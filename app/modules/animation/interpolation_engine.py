"""
Dark Myth Stickman Auto-Studio - Stage 6: Motion Interpolation Engine.

Implements Forward Kinematics (FK) Bone Angle Interpolation ensuring 100% rigid bone
length preservation (0.000 px length error) across all intermediate frames (t in [0, 1]).
Provides standard and custom easing curves, ground support resolution, and weapon alignment.
"""

from enum import Enum
import math
from typing import Optional, Union

from app.modules.animation.pose_catalog import PoseCatalog, PoseDefinition
from app.modules.animation.stickman_models import (
    BoneDefinition,
    CoordinateManager,
    HumanoidSkeleton,
    JointType,
    Point2D,
    RigidBoneValidator,
    StickmanPose,
    SupportMode,
)


class EasingFunction(str, Enum):
    """Standard easing function types for Dark Myth combat motions."""

    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    CUBIC_BEZIER = "cubic_bezier"


# Hierarchical reconstruction order rooted at PELVIS
TREE_ORDER: list[str] = [
    "pelvis_chest",
    "chest_neck",
    "neck_head",
    "chest_shoulder_l",
    "shoulder_l_elbow_l",
    "elbow_l_wrist_l",
    "chest_shoulder_r",
    "shoulder_r_elbow_r",
    "elbow_r_wrist_r",
    "pelvis_knee_l",
    "knee_l_ankle_l",
    "pelvis_knee_r",
    "knee_r_ankle_r",
]

BONES_BY_NAME: dict[str, BoneDefinition] = {b.name: b for b in HumanoidSkeleton.BONES}


def evaluate_easing(
    easing: Union[EasingFunction, str],
    t: float,
    p1: tuple[float, float] = (0.25, 0.1),
    p2: tuple[float, float] = (0.25, 1.0),
) -> float:
    """
    Evaluate easing curve at progress t in [0.0, 1.0].

    Parameters:
      easing: EasingFunction enum or string ("linear", "ease_in", "ease_out", "ease_in_out", "cubic_bezier").
      t: Normalized linear progress in [0.0, 1.0].
      p1, p2: Control points (x1, y1) and (x2, y2) for CUBIC_BEZIER easing.

    Returns:
      Eased progress value in [0.0, 1.0].
    """
    if not math.isfinite(t):
        raise ValueError(f"Progress t must be finite, got {t}")

    clamped_t = max(0.0, min(1.0, float(t)))
    if clamped_t <= 0.0:
        return 0.0
    if clamped_t >= 1.0:
        return 1.0

    mode = EasingFunction(str(easing).lower()) if not isinstance(easing, EasingFunction) else easing

    if mode == EasingFunction.LINEAR:
        return clamped_t
    elif mode == EasingFunction.EASE_IN:
        return clamped_t * clamped_t
    elif mode == EasingFunction.EASE_OUT:
        return clamped_t * (2.0 - clamped_t)
    elif mode == EasingFunction.EASE_IN_OUT:
        if clamped_t < 0.5:
            return 2.0 * clamped_t * clamped_t
        return -1.0 + (4.0 - 2.0 * clamped_t) * clamped_t
    elif mode == EasingFunction.CUBIC_BEZIER:
        x1, y1 = p1
        x2, y2 = p2
        # Solve B_x(u) = clamped_t using binary search
        low, high = 0.0, 1.0
        u = clamped_t
        for _ in range(25):
            # B_x(u) = 3*(1-u)^2 * u * x1 + 3*(1-u)*u^2 * x2 + u^3
            one_minus_u = 1.0 - u
            bx = 3.0 * (one_minus_u**2) * u * x1 + 3.0 * one_minus_u * (u**2) * x2 + (u**3)
            if abs(bx - clamped_t) < 1e-7:
                break
            if bx < clamped_t:
                low = u
            else:
                high = u
            u = (low + high) / 2.0
        one_minus_u = 1.0 - u
        by = 3.0 * (one_minus_u**2) * u * y1 + 3.0 * one_minus_u * (u**2) * y2 + (u**3)
        return max(0.0, min(1.0, by))

    raise ValueError(f"Unsupported easing mode: {easing}")


def extract_bone_angles(pose: StickmanPose) -> dict[str, float]:
    """
    Extract the orientation angle (in radians) for all 13 canonical bones.

    Returns:
      Dictionary mapping bone name -> angle in [-pi, pi].
    """
    angles: dict[str, float] = {}
    for bone in HumanoidSkeleton.BONES:
        p_parent = pose.joints[bone.parent]
        p_child = pose.joints[bone.child]
        dx = p_child.x - p_parent.x
        dy = p_child.y - p_parent.y
        angles[bone.name] = math.atan2(dy, dx)
    return angles


def interpolate_bone_angles(
    angles_a: dict[str, float],
    angles_b: dict[str, float],
    t: float,
) -> dict[str, float]:
    """
    Interpolate bone angles along the shortest circular arc distance.

    Formula:
      diff = (angle_b - angle_a + pi) % (2 * pi) - pi
      angle(t) = angle_a + t * diff
    """
    interpolated: dict[str, float] = {}
    two_pi = 2.0 * math.pi
    for bone_name, ang_a in angles_a.items():
        ang_b = angles_b[bone_name]
        diff = (ang_b - ang_a + math.pi) % two_pi - math.pi
        interpolated[bone_name] = ang_a + t * diff
    return interpolated


def reconstruct_pose_from_angles(
    angles: dict[str, float],
    pose_name: str = "interpolated",
) -> StickmanPose:
    """
    Reconstruct a complete 14-joint StickmanPose from bone angles using Forward Kinematics.

    Starts with PELVIS at (0.0, 0.0) and sequentially computes child joints along TREE_ORDER.
    This guarantees 0.000 px length error for every single bone.
    """
    joints: dict[JointType, Point2D] = {JointType.PELVIS: Point2D(0.0, 0.0)}

    for b_name in TREE_ORDER:
        bone = BONES_BY_NAME[b_name]
        parent_pt = joints[bone.parent]
        ang = angles[b_name]
        joints[bone.child] = Point2D(
            x=parent_pt.x + bone.length * math.cos(ang),
            y=parent_pt.y + bone.length * math.sin(ang),
        )

    pose = StickmanPose(name=pose_name, joints=joints)
    # Verification assertion: strictly rigid
    val = RigidBoneValidator.validate(pose)
    if not val.is_valid:
        raise ValueError(f"Reconstructed pose failed rigidity check: {val.errors}")

    return pose


def interpolate_poses(
    pose_def_a: PoseDefinition,
    pose_def_b: PoseDefinition,
    t: float,
    easing: Union[EasingFunction, str] = EasingFunction.LINEAR,
    name: Optional[str] = None,
) -> PoseDefinition:
    """
    Interpolate between two PoseDefinitions at normalized progress t in [0.0, 1.0].

    Features:
      - 100% rigid bone length preservation using Forward Kinematics.
      - Shortest arc angular interpolation for all 13 joints.
      - Continuous weapon angle interpolation along shortest degree arc.
      - Ground support mode resolution preventing floor clipping.
      - Linear elevation blending.
    """
    if not math.isfinite(t):
        raise ValueError(f"Progress t must be finite, got {t}")

    clamped_t = max(0.0, min(1.0, float(t)))
    eased_t = evaluate_easing(easing, clamped_t)

    if clamped_t <= 0.0:
        return pose_def_a
    if clamped_t >= 1.0:
        return pose_def_b

    # 1. Bone angles & FK pose reconstruction
    ang_a = extract_bone_angles(pose_def_a.pose)
    ang_b = extract_bone_angles(pose_def_b.pose)
    ang_t = interpolate_bone_angles(ang_a, ang_b, eased_t)

    interp_name = name or f"{pose_def_a.name}_to_{pose_def_b.name}_{clamped_t:.2f}"
    interp_pose = reconstruct_pose_from_angles(ang_t, pose_name=interp_name)

    # 2. Elevation interpolation
    interp_elevation = (1.0 - eased_t) * pose_def_a.elevation + eased_t * pose_def_b.elevation

    # 3. Weapon angle interpolation (shortest degree path)
    interp_weapon_angle: Optional[float] = None
    if pose_def_a.weapon_angle_deg is not None and pose_def_b.weapon_angle_deg is not None:
        deg_diff = (pose_def_b.weapon_angle_deg - pose_def_a.weapon_angle_deg + 180.0) % 360.0 - 180.0
        interp_weapon_angle = pose_def_a.weapon_angle_deg + eased_t * deg_diff
    elif pose_def_a.weapon_angle_deg is not None:
        interp_weapon_angle = pose_def_a.weapon_angle_deg
    elif pose_def_b.weapon_angle_deg is not None:
        interp_weapon_angle = pose_def_b.weapon_angle_deg

    # 4. Weapon anchor & secondary grip continuity
    interp_anchor = pose_def_a.weapon_anchor if eased_t < 0.5 else pose_def_b.weapon_anchor
    if pose_def_a.secondary_grip is not None and pose_def_b.secondary_grip is not None:
        interp_secondary_grip: Optional[JointType] = JointType.WRIST_L
    elif pose_def_a.secondary_grip is not None and eased_t < 0.5:
        interp_secondary_grip = pose_def_a.secondary_grip
    elif pose_def_b.secondary_grip is not None and eased_t >= 0.5:
        interp_secondary_grip = pose_def_b.secondary_grip
    else:
        interp_secondary_grip = None

    # 5. Support mode resolution (Zero ground clipping guarantee)
    if interp_elevation > 0.5 or (
        pose_def_a.support_mode == SupportMode.AIRBORNE and pose_def_b.support_mode == SupportMode.AIRBORNE
    ):
        interp_support = SupportMode.AIRBORNE
    else:
        sp = CoordinateManager.get_support_points(interp_pose)
        diff = abs(sp["foot_l_bottom"] - sp["foot_r_bottom"])
        if diff <= 1.5:
            interp_support = SupportMode.DOUBLE
        else:
            # Anchor to whichever foot is lowest in local space so neither foot penetrates ground
            interp_support = (
                SupportMode.LEFT_ONLY if sp["foot_l_bottom"] >= sp["foot_r_bottom"] else SupportMode.RIGHT_ONLY
            )

    desc = f"Interpolated pose from {pose_def_a.name} to {pose_def_b.name} (t={clamped_t:.2f}, eased={eased_t:.2f})"

    return PoseDefinition(
        name=interp_name,
        pose=interp_pose,
        support_mode=interp_support,
        elevation=interp_elevation,
        weapon_anchor=interp_anchor,
        weapon_angle_deg=interp_weapon_angle,
        secondary_grip=interp_secondary_grip,
        description=desc,
    )


class InterpolationEngine:
    """
    Stateless high-level motion interpolation service.
    """

    @staticmethod
    def evaluate_easing(
        easing: Union[EasingFunction, str],
        t: float,
        p1: tuple[float, float] = (0.25, 0.1),
        p2: tuple[float, float] = (0.25, 1.0),
    ) -> float:
        return evaluate_easing(easing, t, p1=p1, p2=p2)

    @staticmethod
    def extract_bone_angles(pose: StickmanPose) -> dict[str, float]:
        return extract_bone_angles(pose)

    @staticmethod
    def interpolate_bone_angles(
        angles_a: dict[str, float],
        angles_b: dict[str, float],
        t: float,
    ) -> dict[str, float]:
        return interpolate_bone_angles(angles_a, angles_b, t)

    @staticmethod
    def reconstruct_pose_from_angles(
        angles: dict[str, float],
        pose_name: str = "interpolated",
    ) -> StickmanPose:
        return reconstruct_pose_from_angles(angles, pose_name=pose_name)

    @staticmethod
    def interpolate_poses(
        pose_def_a: PoseDefinition,
        pose_def_b: PoseDefinition,
        t: float,
        easing: Union[EasingFunction, str] = EasingFunction.LINEAR,
        name: Optional[str] = None,
    ) -> PoseDefinition:
        return interpolate_poses(pose_def_a, pose_def_b, t, easing=easing, name=name)
