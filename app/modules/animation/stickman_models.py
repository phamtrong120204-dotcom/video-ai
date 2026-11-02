"""Foundation Data Models and Kinematic Rigging for Dark Myth Stickman.

Defines the 14-joint humanoid skeleton, 13 rigid bone segments, immutable pose
representations, strict rigid length validator, coordinate transformation manager,
and actor character data structures.
"""

from dataclasses import dataclass
from enum import Enum
import hashlib
import math
from typing import Optional, Union

from app.core.logger import get_logger
from app.schemas.scene_schema import ActorConfig, ActorSide, CharacterSkin, WeaponType

logger = get_logger("stickman_models")


@dataclass(frozen=True)
class Point2D:
    """Immutable 2D geometric coordinate with strict finite value validation."""

    x: float
    y: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.x) or not math.isfinite(self.y):
            raise ValueError(f"Point2D coordinates must be finite numbers, got x={self.x}, y={self.y}")

    def distance_to(self, other: "Point2D") -> float:
        """Euclidean distance to another point."""
        return math.hypot(self.x - other.x, self.y - other.y)

    def as_tuple(self) -> tuple[float, float]:
        """Convert to (x, y) tuple."""
        return (self.x, self.y)

    def __add__(self, other: "Point2D") -> "Point2D":
        return Point2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Point2D") -> "Point2D":
        return Point2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Point2D":
        return Point2D(self.x * scalar, self.y * scalar)


class JointType(str, Enum):
    """The 14 canonical anatomical joints of the Dark Myth stickman humanoid skeleton."""

    HEAD = "head"
    NECK = "neck"
    CHEST = "chest"
    PELVIS = "pelvis"  # Root joint
    SHOULDER_L = "shoulder_l"
    ELBOW_L = "elbow_l"
    WRIST_L = "wrist_l"
    SHOULDER_R = "shoulder_r"
    ELBOW_R = "elbow_r"
    WRIST_R = "wrist_r"
    KNEE_L = "knee_l"
    ANKLE_L = "ankle_l"
    KNEE_R = "knee_r"
    ANKLE_R = "ankle_r"


class SupportMode(str, Enum):
    """Ground contact support mode for stickman stance and root alignment."""

    DOUBLE = "double"        # Both feet act as ground contact points simultaneously
    LEFT_ONLY = "left_only"  # Only left foot is the ground anchor; right foot is unconstrained
    RIGHT_ONLY = "right_only"# Only right foot is the ground anchor; left foot is unconstrained
    AIRBORNE = "airborne"    # Neither foot touches ground (jumping, leaping, or flying)


@dataclass(frozen=True)
class BoneDefinition:
    """Immutable definition of a rigid bone segment linking a parent joint to a child joint."""

    name: str
    parent: JointType
    child: JointType
    length: float
    stroke_width: int

    def __post_init__(self) -> None:
        if self.length <= 0.0 or not math.isfinite(self.length):
            raise ValueError(f"Bone '{self.name}' must have positive finite length, got {self.length}")
        if self.stroke_width <= 0:
            raise ValueError(f"Bone '{self.name}' must have positive stroke width, got {self.stroke_width}")


class HumanoidSkeleton:
    """
    Canonical 14-joint, 13-bone humanoid stickman skeleton topology.

    Topological Hierarchy:
      PELVIS (ROOT)
        ├── CHEST
        │     ├── NECK
        │     │     └── HEAD
        │     ├── SHOULDER_L
        │     │     └── ELBOW_L
        │     │           └── WRIST_L
        │     └── SHOULDER_R
        │           └── ELBOW_R
        │                 └── WRIST_R
        ├── KNEE_L
        │     └── ANKLE_L
        └── KNEE_R
              └── ANKLE_R
    """

    ROOT_JOINT: JointType = JointType.PELVIS

    JOINTS: tuple[JointType, ...] = (
        JointType.HEAD,
        JointType.NECK,
        JointType.CHEST,
        JointType.PELVIS,
        JointType.SHOULDER_L,
        JointType.ELBOW_L,
        JointType.WRIST_L,
        JointType.SHOULDER_R,
        JointType.ELBOW_R,
        JointType.WRIST_R,
        JointType.KNEE_L,
        JointType.ANKLE_L,
        JointType.KNEE_R,
        JointType.ANKLE_R,
    )

    BONES: tuple[BoneDefinition, ...] = (
        BoneDefinition("neck_head", JointType.NECK, JointType.HEAD, 48.0, 10),
        BoneDefinition("chest_neck", JointType.CHEST, JointType.NECK, 45.0, 12),
        BoneDefinition("pelvis_chest", JointType.PELVIS, JointType.CHEST, 75.0, 14),
        BoneDefinition("chest_shoulder_l", JointType.CHEST, JointType.SHOULDER_L, 32.0, 10),
        BoneDefinition("shoulder_l_elbow_l", JointType.SHOULDER_L, JointType.ELBOW_L, 68.0, 9),
        BoneDefinition("elbow_l_wrist_l", JointType.ELBOW_L, JointType.WRIST_L, 62.0, 8),
        BoneDefinition("chest_shoulder_r", JointType.CHEST, JointType.SHOULDER_R, 32.0, 10),
        BoneDefinition("shoulder_r_elbow_r", JointType.SHOULDER_R, JointType.ELBOW_R, 68.0, 9),
        BoneDefinition("elbow_r_wrist_r", JointType.ELBOW_R, JointType.WRIST_R, 62.0, 8),
        BoneDefinition("pelvis_knee_l", JointType.PELVIS, JointType.KNEE_L, 95.0, 12),
        BoneDefinition("knee_l_ankle_l", JointType.KNEE_L, JointType.ANKLE_L, 90.0, 10),
        BoneDefinition("pelvis_knee_r", JointType.PELVIS, JointType.KNEE_R, 95.0, 12),
        BoneDefinition("knee_r_ankle_r", JointType.KNEE_R, JointType.ANKLE_R, 90.0, 10),
    )

    # Topological order guarantees parent is visited before child
    TOPOLOGICAL_ORDER: tuple[JointType, ...] = (
        JointType.PELVIS,
        JointType.CHEST,
        JointType.NECK,
        JointType.HEAD,
        JointType.SHOULDER_L,
        JointType.ELBOW_L,
        JointType.WRIST_L,
        JointType.SHOULDER_R,
        JointType.ELBOW_R,
        JointType.WRIST_R,
        JointType.KNEE_L,
        JointType.ANKLE_L,
        JointType.KNEE_R,
        JointType.ANKLE_R,
    )

    PARENT_MAP: dict[JointType, Optional[JointType]] = {
        JointType.PELVIS: None,
        JointType.CHEST: JointType.PELVIS,
        JointType.NECK: JointType.CHEST,
        JointType.HEAD: JointType.NECK,
        JointType.SHOULDER_L: JointType.CHEST,
        JointType.ELBOW_L: JointType.SHOULDER_L,
        JointType.WRIST_L: JointType.ELBOW_L,
        JointType.SHOULDER_R: JointType.CHEST,
        JointType.ELBOW_R: JointType.SHOULDER_R,
        JointType.WRIST_R: JointType.ELBOW_R,
        JointType.KNEE_L: JointType.PELVIS,
        JointType.ANKLE_L: JointType.KNEE_L,
        JointType.KNEE_R: JointType.PELVIS,
        JointType.ANKLE_R: JointType.KNEE_R,
    }

    CHILDREN_MAP: dict[JointType, tuple[JointType, ...]] = {
        JointType.PELVIS: (JointType.CHEST, JointType.KNEE_L, JointType.KNEE_R),
        JointType.CHEST: (JointType.NECK, JointType.SHOULDER_L, JointType.SHOULDER_R),
        JointType.NECK: (JointType.HEAD,),
        JointType.HEAD: (),
        JointType.SHOULDER_L: (JointType.ELBOW_L,),
        JointType.ELBOW_L: (JointType.WRIST_L,),
        JointType.WRIST_L: (),
        JointType.SHOULDER_R: (JointType.ELBOW_R,),
        JointType.ELBOW_R: (JointType.WRIST_R,),
        JointType.WRIST_R: (),
        JointType.KNEE_L: (JointType.ANKLE_L,),
        JointType.ANKLE_L: (),
        JointType.KNEE_R: (JointType.ANKLE_R,),
        JointType.ANKLE_R: (),
    }

    REST_LENGTHS: dict[str, float] = {b.name: b.length for b in BONES}

    @classmethod
    def create_neutral_standing_pose(cls, name: str = "neutral_standing") -> "StickmanPose":
        """
        Create the canonical neutral vertical standing pose facing +X.

        Key local coordinate geometry (scale = 1.0):
          - Pelvis: (0, 0)
          - Chest: (0, -75)
          - Neck: (0, -120)
          - Head center: (0, -168)
          - Shoulder L: (-32, -75), Elbow L: (-32, -7), Wrist L: (-32, 55)
          - Shoulder R: (+32, -75), Elbow R: (+32, -7), Wrist R: (+32, 55)
          - Knee L/R: (0, 95)
          - Ankle L/R: (0, 185)
          - All 13 Euclidean bone distances are 100% exact to 0.000px error.
        """
        joints = {
            JointType.PELVIS: Point2D(0.0, 0.0),
            JointType.CHEST: Point2D(0.0, -75.0),
            JointType.NECK: Point2D(0.0, -120.0),
            JointType.HEAD: Point2D(0.0, -168.0),
            JointType.SHOULDER_L: Point2D(-32.0, -75.0),
            JointType.ELBOW_L: Point2D(-32.0, -7.0),
            JointType.WRIST_L: Point2D(-32.0, 55.0),
            JointType.SHOULDER_R: Point2D(32.0, -75.0),
            JointType.ELBOW_R: Point2D(32.0, -7.0),
            JointType.WRIST_R: Point2D(32.0, 55.0),
            JointType.KNEE_L: Point2D(0.0, 95.0),
            JointType.ANKLE_L: Point2D(0.0, 185.0),
            JointType.KNEE_R: Point2D(0.0, 95.0),
            JointType.ANKLE_R: Point2D(0.0, 185.0),
        }
        return StickmanPose(name=name, joints=joints)


@dataclass(frozen=True)
class StickmanPose:
    """
    Immutable representation of stickman joint positions in Local Pose Space.

    Guarantees presence of all 14 canonical joints.
    """

    name: str
    joints: dict[JointType, Point2D]

    def __post_init__(self) -> None:
        missing = set(HumanoidSkeleton.JOINTS) - set(self.joints.keys())
        if missing:
            missing_names = sorted(j.value for j in missing)
            raise ValueError(f"StickmanPose '{self.name}' is missing required joints: {missing_names}")

    def get_joint(self, joint: JointType) -> Point2D:
        """Get joint coordinate."""
        return self.joints[joint]


@dataclass(frozen=True)
class BoneValidationDetail:
    """Validation telemetry for a single bone segment."""

    bone_name: str
    parent: JointType
    child: JointType
    expected_length: float
    actual_length: float
    deviation: float
    is_valid: bool


@dataclass(frozen=True)
class ValidationResult:
    """Full skeleton validation result."""

    is_valid: bool
    details: tuple[BoneValidationDetail, ...]
    errors: tuple[str, ...]


class RigidBoneValidator:
    """
    Validates Euclidean distances between connected joints against canonical rest lengths.

    Default tolerance: epsilon = 0.5 px.
    """

    DEFAULT_EPSILON: float = 0.5

    @classmethod
    def validate(cls, pose: StickmanPose, epsilon: float = DEFAULT_EPSILON) -> ValidationResult:
        """
        Validate pose bone lengths without altering the pose.

        Returns ValidationResult with details for each of the 13 bones.
        """
        details: list[BoneValidationDetail] = []
        errors: list[str] = []

        for bone in HumanoidSkeleton.BONES:
            p_parent = pose.joints[bone.parent]
            p_child = pose.joints[bone.child]
            actual = p_parent.distance_to(p_child)
            dev = abs(actual - bone.length)
            valid = dev <= epsilon

            if not valid:
                msg = (
                    f"Bone '{bone.name}' ({bone.parent.value}->{bone.child.value}) "
                    f"length error: expected {bone.length:.2f}px, got {actual:.2f}px (diff {dev:.3f}px > {epsilon}px)"
                )
                errors.append(msg)

            details.append(
                BoneValidationDetail(
                    bone_name=bone.name,
                    parent=bone.parent,
                    child=bone.child,
                    expected_length=bone.length,
                    actual_length=actual,
                    deviation=dev,
                    is_valid=valid,
                )
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            details=tuple(details),
            errors=tuple(errors),
        )

    @classmethod
    def enforce_rigid_lengths(
        cls, pose: StickmanPose, name: Optional[str] = None
    ) -> StickmanPose:
        """
        Construct and return a NEW pose where all bone segments are projected along
        their joint-direction vectors to match the canonical rest lengths exactly.

        Does not mutate the input pose.
        """
        new_joints: dict[JointType, Point2D] = {}
        # Pelvis is root, fixed at original coordinate
        new_joints[HumanoidSkeleton.ROOT_JOINT] = pose.joints[HumanoidSkeleton.ROOT_JOINT]

        # Traverse in topological order: parent is guaranteed resolved before child
        for joint in HumanoidSkeleton.TOPOLOGICAL_ORDER:
            parent = HumanoidSkeleton.PARENT_MAP[joint]
            if parent is None:
                continue

            p_parent = new_joints[parent]
            p_child_orig = pose.joints[joint]

            # Find matching bone definition
            bone_len: Optional[float] = None
            for b in HumanoidSkeleton.BONES:
                if b.parent == parent and b.child == joint:
                    bone_len = b.length
                    break

            if bone_len is None:
                raise RuntimeError(f"Topology error: No bone defined between {parent} and {joint}")

            dx = p_child_orig.x - p_parent.x
            dy = p_child_orig.y - p_parent.y
            dist = math.hypot(dx, dy)

            if dist < 1e-6:
                # Default direction downwards if parent and child coincide
                ux, uy = 0.0, 1.0
            else:
                ux, uy = dx / dist, dy / dist

            new_joints[joint] = Point2D(
                x=p_parent.x + ux * bone_len,
                y=p_parent.y + uy * bone_len,
            )

        out_name = name or f"{pose.name}_enforced"
        return StickmanPose(name=out_name, joints=new_joints)


class CoordinateManager:
    """
    Manages coordinate transformations between Local Pose Space and 1080x1920 Canvas Space.

    Distinguishes:
      - Local Ankle joint center vs Foot contact point (+5px)
      - Ground line (Y_ground = 1420 px)
      - Ground contact alignment and elevation
      - Single-point facing direction (+1 or -1)
    """

    Y_GROUND: float = 1420.0
    FOOT_EXTENT: float = 5.0  # Distance from ankle joint center to bottom of foot sole
    HEAD_RADIUS: float = 26.0
    CANONICAL_GROUND_REFERENCE: float = 190.0  # Local Y contact of neutral standing feet (185 ankle + 5 foot)

    @classmethod
    def get_facing(cls, side: ActorSide, override_facing: Optional[int] = None) -> int:
        """
        Determine single-point facing direction (+1 or -1).

        Rules:
          - ActorSide.LEFT  -> +1 (looks right towards opponent)
          - ActorSide.RIGHT -> -1 (looks left towards opponent)
          - ActorSide.CENTER-> override_facing if provided else +1
          - ActorSide.TOP   -> requires explicit override_facing (+1 or -1)
        """
        if override_facing is not None:
            if override_facing not in (+1, -1):
                raise ValueError(f"override_facing must be +1 or -1, got {override_facing}")
            return override_facing

        if side == ActorSide.LEFT:
            return +1
        elif side == ActorSide.RIGHT:
            return -1
        elif side == ActorSide.CENTER:
            return +1
        elif side == ActorSide.TOP:
            raise ValueError(
                "ActorSide.TOP does not convey facing direction; an explicit override_facing (+1 or -1) is required."
            )
        raise ValueError(f"Unsupported ActorSide: {side}")

    @classmethod
    def get_support_points(cls, pose: StickmanPose) -> dict[str, float]:
        """Return the lowest contact Y for each foot in Local Pose Space."""
        left_foot_bottom = pose.joints[JointType.ANKLE_L].y + cls.FOOT_EXTENT
        right_foot_bottom = pose.joints[JointType.ANKLE_R].y + cls.FOOT_EXTENT
        return {
            "ankle_l_center": pose.joints[JointType.ANKLE_L].y,
            "ankle_r_center": pose.joints[JointType.ANKLE_R].y,
            "foot_l_bottom": left_foot_bottom,
            "foot_r_bottom": right_foot_bottom,
        }

    @classmethod
    def get_ground_contact_y(cls, pose: StickmanPose) -> float:
        """Return the lowest foot contact Y in Local Pose Space across both feet."""
        sp = cls.get_support_points(pose)
        return max(sp["foot_l_bottom"], sp["foot_r_bottom"])

    @classmethod
    def normalize_support_mode(cls, mode: Union[SupportMode, str]) -> SupportMode:
        """Normalize input support mode string or enum into canonical SupportMode."""
        if isinstance(mode, SupportMode):
            return mode
        cleaned = str(mode).lower().strip()
        if cleaned in ("double", "both", "two_feet"):
            return SupportMode.DOUBLE
        elif cleaned in ("left_only", "left", "left_foot"):
            return SupportMode.LEFT_ONLY
        elif cleaned in ("right_only", "right", "right_foot"):
            return SupportMode.RIGHT_ONLY
        elif cleaned in ("airborne", "none", "no_support", "jump", "fly"):
            return SupportMode.AIRBORNE
        raise ValueError(
            f"Invalid support_mode: '{mode}'. Allowed values: {[m.value for m in SupportMode]}"
        )

    @classmethod
    def get_ground_aligned_root_y(
        cls,
        pose: StickmanPose,
        support_mode: Union[SupportMode, str] = SupportMode.DOUBLE,
        ground_y: float = Y_GROUND,
        scale: float = 1.0,
        elevation: Optional[float] = None,
        explicit_canvas_y: Optional[float] = None,
        double_support_tolerance: float = 1.5,
    ) -> float:
        """
        Calculate ground-aligned canvas pelvis Y with strict support foot semantics.

        Modes:
          - SupportMode.DOUBLE:
              Both feet must align to the ground plane within double_support_tolerance.
              Raises ValueError if feet contact heights are incompatible.
          - SupportMode.LEFT_ONLY:
              Left foot is the sole support anchor. Right foot may be lifted or kicking.
          - SupportMode.RIGHT_ONLY:
              Right foot is the sole support anchor. Left foot may be lifted or kicking.
          - SupportMode.AIRBORNE:
              Neither foot touches ground. Requires explicit elevation or explicit_canvas_y.
        """
        mode = cls.normalize_support_mode(support_mode)

        if scale <= 0.1 or scale > 5.0 or not math.isfinite(scale):
            raise ValueError(f"scale must be in range (0.1, 5.0], got {scale}")

        sp = cls.get_support_points(pose)

        if mode == SupportMode.DOUBLE:
            diff = abs(sp["foot_l_bottom"] - sp["foot_r_bottom"])
            if diff > double_support_tolerance:
                raise ValueError(
                    f"Incompatible double support: left foot contact ({sp['foot_l_bottom']:.2f}px) "
                    f"and right foot contact ({sp['foot_r_bottom']:.2f}px) differ by {diff:.2f}px "
                    f"> tolerance {double_support_tolerance:.2f}px. "
                    f"Use SupportMode.LEFT_ONLY or SupportMode.RIGHT_ONLY for asymmetric stance."
                )
            contact_local_y = (sp["foot_l_bottom"] + sp["foot_r_bottom"]) / 2.0
            elev = elevation if elevation is not None else 0.0
            return float(ground_y - (contact_local_y * scale) - elev)

        elif mode == SupportMode.LEFT_ONLY:
            contact_local_y = sp["foot_l_bottom"]
            elev = elevation if elevation is not None else 0.0
            return float(ground_y - (contact_local_y * scale) - elev)

        elif mode == SupportMode.RIGHT_ONLY:
            contact_local_y = sp["foot_r_bottom"]
            elev = elevation if elevation is not None else 0.0
            return float(ground_y - (contact_local_y * scale) - elev)

        elif mode == SupportMode.AIRBORNE:
            if explicit_canvas_y is not None:
                if not math.isfinite(explicit_canvas_y):
                    raise ValueError(f"explicit_canvas_y must be finite, got {explicit_canvas_y}")
                return float(explicit_canvas_y)
            if elevation is not None:
                if not math.isfinite(elevation):
                    raise ValueError(f"elevation must be finite, got {elevation}")
                # Ground reference is standard neutral standing foot contact (190px at scale 1.0)
                # pelvis_y = ground_y - (ground_reference_offset * scale) - elevation
                return float(ground_y - (cls.CANONICAL_GROUND_REFERENCE * scale) - elevation)
            raise ValueError(
                "SupportMode.AIRBORNE requires either 'explicit_canvas_y' or 'elevation' to be specified."
            )

        raise ValueError(f"Unhandled support mode: {mode}")

    @classmethod
    def get_canvas_pelvis_y(
        cls,
        pose: StickmanPose,
        scale: float = 1.0,
        elevation: float = 0.0,
        ground_y: float = Y_GROUND,
        support_mode: Optional[Union[SupportMode, str]] = None,
    ) -> float:
        """
        Legacy-compatible canvas pelvis calculation.

        If support_mode is provided, delegates to get_ground_aligned_root_y.
        If support_mode is None:
          - If pose has symmetric feet (|diff| <= 1.5), uses DOUBLE support.
          - If pose has asymmetric feet, gracefully uses the lowest contact point
            (preserving exact G5.2.1 behavior for legacy callers).
        """
        if support_mode is not None:
            return cls.get_ground_aligned_root_y(
                pose=pose,
                support_mode=support_mode,
                ground_y=ground_y,
                scale=scale,
                elevation=elevation,
            )
        sp = cls.get_support_points(pose)
        diff = abs(sp["foot_l_bottom"] - sp["foot_r_bottom"])
        if diff <= 1.5:
            contact_y = (sp["foot_l_bottom"] + sp["foot_r_bottom"]) / 2.0
        else:
            contact_y = max(sp["foot_l_bottom"], sp["foot_r_bottom"])
        return float(ground_y - (contact_y * scale) - elevation)

    @classmethod
    def local_to_canvas(
        cls,
        point: Point2D,
        pelvis_canvas: Point2D,
        facing: int = 1,
        scale: float = 1.0,
    ) -> Point2D:
        """Transform a single point from local space to canvas space."""
        if facing not in (+1, -1):
            raise ValueError(f"Facing must be +1 or -1, got {facing}")
        return Point2D(
            x=pelvis_canvas.x + (point.x * facing * scale),
            y=pelvis_canvas.y + (point.y * scale),
        )

    @classmethod
    def transform_pose_to_canvas(
        cls,
        pose: StickmanPose,
        pelvis_canvas: Point2D,
        facing: int = 1,
        scale: float = 1.0,
    ) -> StickmanPose:
        """Transform all 14 joints of a pose into Canvas Space."""
        canvas_joints = {
            joint: cls.local_to_canvas(p, pelvis_canvas, facing=facing, scale=scale)
            for joint, p in pose.joints.items()
        }
        return StickmanPose(name=f"{pose.name}_canvas", joints=canvas_joints)


def parse_hex_color(hex_str: str) -> tuple[int, int, int, int]:
    """Parse #RGB, #RRGGBB, or #RRGGBBAA hex string into an RGBA integer tuple."""
    cleaned = hex_str.strip().lstrip("#")
    if len(cleaned) == 3:
        r, g, b = (int(c * 2, 16) for c in cleaned)
        return (r, g, b, 255)
    elif len(cleaned) == 6:
        r = int(cleaned[0:2], 16)
        g = int(cleaned[2:4], 16)
        b = int(cleaned[4:6], 16)
        return (r, g, b, 255)
    elif len(cleaned) == 8:
        r = int(cleaned[0:2], 16)
        g = int(cleaned[2:4], 16)
        b = int(cleaned[4:6], 16)
        a = int(cleaned[6:8], 16)
        return (r, g, b, a)
    raise ValueError(f"Invalid hex color string: '{hex_str}'")


def generate_actor_seed(actor_id: str, extra_salt: str = "") -> int:
    """
    Generate deterministic 32-bit unsigned integer seed from actor_id using SHA-256.

    Reproducible across independent Python processes and runtime environments.
    """
    raw = f"{actor_id.strip()}_{extra_salt}".encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    return int.from_bytes(digest[:4], byteorder="big", signed=False)


@dataclass(frozen=True)
class StickmanCharacter:
    """
    Data model representing a configured stickman character on stage.

    Immutable and verified compatible with ActorConfig data contract.
    """

    actor_id: str
    skin: CharacterSkin
    stroke_color: tuple[int, int, int, int]
    aura_color: tuple[int, int, int, int]
    weapon: WeaponType
    scale: float
    side: ActorSide
    display_name: str
    seed: int

    def __post_init__(self) -> None:
        if not self.actor_id or not self.actor_id.strip():
            raise ValueError("actor_id cannot be empty or blank")
        if self.scale <= 0.1 or self.scale > 5.0 or not math.isfinite(self.scale):
            raise ValueError(f"scale must be in range (0.1, 5.0], got {self.scale}")

        for name, col in (("stroke_color", self.stroke_color), ("aura_color", self.aura_color)):
            if len(col) != 4 or any(not (0 <= c <= 255) for c in col):
                raise ValueError(f"{name} must be an RGBA 4-tuple with values in [0, 255], got {col}")

    @classmethod
    def from_actor_config(cls, config: ActorConfig) -> "StickmanCharacter":
        """
        Construct StickmanCharacter from approved ActorConfig contract without schema changes.

        Stroke colors are determined by skin:
          - dark_wukong: #141416 (Dark ink black)
          - erlang_shen: #1A202C (Dark slate steel)
          - celestial_general / celestial_soldier_squad: #2D3748 (Steel grey)
          - buddha_palm: #1A1817 (Ancient ink bronze)
        """
        aura_rgba = parse_hex_color(config.color)

        if config.skin == CharacterSkin.DARK_WUKONG:
            stroke_rgba = (20, 20, 22, 255)  # #141416
        elif config.skin == CharacterSkin.ERLANG_SHEN:
            stroke_rgba = (26, 32, 44, 255)  # #1A202C
        elif config.skin in (CharacterSkin.CELESTIAL_GENERAL, CharacterSkin.CELESTIAL_SOLDIER_SQUAD):
            stroke_rgba = (45, 55, 72, 255)  # #2D3748
        elif config.skin == CharacterSkin.BUDDHA_PALM:
            stroke_rgba = (26, 24, 23, 255)  # #1A1817
        else:
            stroke_rgba = (20, 20, 22, 255)

        seed = generate_actor_seed(config.actor_id)

        return cls(
            actor_id=config.actor_id,
            skin=config.skin,
            stroke_color=stroke_rgba,
            aura_color=aura_rgba,
            weapon=config.weapon,
            scale=config.scale,
            side=config.side,
            display_name=config.display_name,
            seed=seed,
        )
