"""Dark Myth Stickman Pose Catalog (G5.2.2).

Provides 8 canonical, immutable combat poses constructed with rigorous Forward Kinematics.
All 13 bone segments in every pose strictly satisfy RigidBoneValidator with zero length error
(epsilon <= 0.5 px). All poses are oriented facing +X (right).
"""

from dataclasses import dataclass
import math
from typing import Optional

from app.modules.animation.stickman_models import (
    CoordinateManager,
    HumanoidSkeleton,
    JointType,
    Point2D,
    RigidBoneValidator,
    StickmanPose,
    SupportMode,
)


@dataclass(frozen=True)
class PoseDefinition:
    """Metadata and joint configuration for a canonical Dark Myth stickman pose."""

    name: str
    pose: StickmanPose
    support_mode: SupportMode
    elevation: Optional[float] = None
    weapon_anchor: JointType = JointType.WRIST_R
    weapon_angle_deg: float = 0.0
    secondary_grip: Optional[JointType] = None
    description: str = ""


def _clone_pose(pose: StickmanPose) -> StickmanPose:
    """Create an independent defensive deep copy of StickmanPose with fresh joints dictionary."""
    cloned_joints = {j: Point2D(pt.x, pt.y) for j, pt in pose.joints.items()}
    return StickmanPose(name=pose.name, joints=cloned_joints)


def _clone_definition(defn: PoseDefinition) -> PoseDefinition:
    """Create an independent defensive deep copy of PoseDefinition."""
    return PoseDefinition(
        name=defn.name,
        pose=_clone_pose(defn.pose),
        support_mode=defn.support_mode,
        elevation=defn.elevation,
        weapon_anchor=defn.weapon_anchor,
        weapon_angle_deg=defn.weapon_angle_deg,
        secondary_grip=defn.secondary_grip,
        description=defn.description,
    )


def _clean(v: float) -> float:
    return 0.0 if abs(v) < 1e-10 else round(v, 6)


def _pt(x: float, y: float) -> Point2D:
    return Point2D(_clean(x), _clean(y))


def _fk_pose(
    name: str,
    spine_deg: float,
    neck_deg: float,
    head_deg: float,
    shoulder_l_deg: float,
    elbow_l_deg: float,
    wrist_l_deg: float,
    shoulder_r_deg: float,
    elbow_r_deg: float,
    wrist_r_deg: float,
    thigh_l_deg: float,
    shin_l_deg: float,
    thigh_r_deg: float,
    shin_r_deg: float,
) -> StickmanPose:
    """
    Construct a StickmanPose using Forward Kinematics (FK) starting from PELVIS at (0, 0).

    Angles are measured in degrees in canvas space (+X right = 0 deg, +Y down = 90 deg,
    straight up = -90 deg, straight back = 180 deg).
    Because Euclidean distances are defined by L0 * (cos(theta), sin(theta)), bone length
    error is mathematically 0.000px, 100% compliant with RigidBoneValidator.
    """
    pelvis = _pt(0.0, 0.0)

    # Spine chain (pelvis -> chest -> neck -> head)
    r_spine = math.radians(spine_deg)
    chest = _pt(
        pelvis.x + 75.0 * math.cos(r_spine),
        pelvis.y + 75.0 * math.sin(r_spine),
    )

    r_neck = math.radians(neck_deg)
    neck = _pt(
        chest.x + 45.0 * math.cos(r_neck),
        chest.y + 45.0 * math.sin(r_neck),
    )

    r_head = math.radians(head_deg)
    head = _pt(
        neck.x + 48.0 * math.cos(r_head),
        neck.y + 48.0 * math.sin(r_head),
    )

    # Left arm chain (chest -> shoulder_l -> elbow_l -> wrist_l)
    r_sh_l = math.radians(shoulder_l_deg)
    shoulder_l = _pt(
        chest.x + 32.0 * math.cos(r_sh_l),
        chest.y + 32.0 * math.sin(r_sh_l),
    )

    r_el_l = math.radians(elbow_l_deg)
    elbow_l = _pt(
        shoulder_l.x + 68.0 * math.cos(r_el_l),
        shoulder_l.y + 68.0 * math.sin(r_el_l),
    )

    r_wr_l = math.radians(wrist_l_deg)
    wrist_l = _pt(
        elbow_l.x + 62.0 * math.cos(r_wr_l),
        elbow_l.y + 62.0 * math.sin(r_wr_l),
    )

    # Right arm chain (chest -> shoulder_r -> elbow_r -> wrist_r)
    r_sh_r = math.radians(shoulder_r_deg)
    shoulder_r = _pt(
        chest.x + 32.0 * math.cos(r_sh_r),
        chest.y + 32.0 * math.sin(r_sh_r),
    )

    r_el_r = math.radians(elbow_r_deg)
    elbow_r = _pt(
        shoulder_r.x + 68.0 * math.cos(r_el_r),
        shoulder_r.y + 68.0 * math.sin(r_el_r),
    )

    r_wr_r = math.radians(wrist_r_deg)
    wrist_r = _pt(
        elbow_r.x + 62.0 * math.cos(r_wr_r),
        elbow_r.y + 62.0 * math.sin(r_wr_r),
    )

    # Left leg chain (pelvis -> knee_l -> ankle_l)
    r_th_l = math.radians(thigh_l_deg)
    knee_l = _pt(
        pelvis.x + 95.0 * math.cos(r_th_l),
        pelvis.y + 95.0 * math.sin(r_th_l),
    )

    r_shn_l = math.radians(shin_l_deg)
    ankle_l = _pt(
        knee_l.x + 90.0 * math.cos(r_shn_l),
        knee_l.y + 90.0 * math.sin(r_shn_l),
    )

    # Right leg chain (pelvis -> knee_r -> ankle_r)
    r_th_r = math.radians(thigh_r_deg)
    knee_r = _pt(
        pelvis.x + 95.0 * math.cos(r_th_r),
        pelvis.y + 95.0 * math.sin(r_th_r),
    )

    r_shn_r = math.radians(shin_r_deg)
    ankle_r = _pt(
        knee_r.x + 90.0 * math.cos(r_shn_r),
        knee_r.y + 90.0 * math.sin(r_shn_r),
    )

    joints = {
        JointType.PELVIS: pelvis,
        JointType.CHEST: chest,
        JointType.NECK: neck,
        JointType.HEAD: head,
        JointType.SHOULDER_L: shoulder_l,
        JointType.ELBOW_L: elbow_l,
        JointType.WRIST_L: wrist_l,
        JointType.SHOULDER_R: shoulder_r,
        JointType.ELBOW_R: elbow_r,
        JointType.WRIST_R: wrist_r,
        JointType.KNEE_L: knee_l,
        JointType.ANKLE_L: ankle_l,
        JointType.KNEE_R: knee_r,
        JointType.ANKLE_R: ankle_r,
    }
    return StickmanPose(name=name, joints=joints)


def _build_standoff_idle() -> PoseDefinition:
    """1. STANDOFF_IDLE: Dignified vertical standing pose, feet grounded, weapon lowered."""
    pose = _fk_pose(
        name="standoff_idle",
        spine_deg=-90.0,
        neck_deg=-90.0,
        head_deg=-90.0,
        shoulder_l_deg=180.0,
        elbow_l_deg=90.0,
        wrist_l_deg=90.0,
        shoulder_r_deg=0.0,
        elbow_r_deg=90.0,
        wrist_r_deg=90.0,
        thigh_l_deg=90.0,
        shin_l_deg=90.0,
        thigh_r_deg=90.0,
        shin_r_deg=90.0,
    )
    return PoseDefinition(
        name="standoff_idle",
        pose=pose,
        support_mode=SupportMode.DOUBLE,
        elevation=0.0,
        weapon_anchor=JointType.WRIST_R,
        weapon_angle_deg=80.0,
        description="Dignified vertical standoff stance facing opponent, both feet grounded.",
    )


def _build_combat_stance() -> PoseDefinition:
    """2. COMBAT_STANCE: Lowered center of gravity, bent knees (exact equal contact Y=170.0), hands raised."""
    # Thigh L 75 deg, Shin L 125.539 deg -> Ankle L Y = 165.0, X = -27.73
    # Thigh R 60 deg, Shin R 66.809 deg  -> Ankle R Y = 165.0, X = +82.95
    # Contact Y = 165.0 + 5.0 = 170.0 px for both feet (zero error Double Support)
    pose = _fk_pose(
        name="combat_stance",
        spine_deg=-78.0,
        neck_deg=-82.0,
        head_deg=-82.0,
        shoulder_l_deg=160.0,
        elbow_l_deg=90.0,
        wrist_l_deg=-30.0,
        shoulder_r_deg=15.0,
        elbow_r_deg=45.0,
        wrist_r_deg=-15.0,
        thigh_l_deg=75.0,
        shin_l_deg=125.53654515175755,
        thigh_r_deg=60.0,
        shin_r_deg=66.80873795672996,
    )
    return PoseDefinition(
        name="combat_stance",
        pose=pose,
        support_mode=SupportMode.DOUBLE,
        elevation=0.0,
        weapon_anchor=JointType.WRIST_R,
        weapon_angle_deg=35.0,
        secondary_grip=JointType.WRIST_L,
        description="Combat ready stance with lowered center of gravity, crouched knees, hands guarded.",
    )


def _build_forward_charge() -> PoseDefinition:
    """3. FORWARD_CHARGE: Torso lunging forward at 35 deg from vertical, front foot lead support, weapon thrusting."""
    pose = _fk_pose(
        name="forward_charge",
        spine_deg=-55.0,  # 35 deg lean from vertical -90
        neck_deg=-50.0,
        head_deg=-45.0,
        shoulder_l_deg=160.0,
        elbow_l_deg=170.0,
        wrist_l_deg=175.0,
        shoulder_r_deg=10.0,
        elbow_r_deg=5.0,
        wrist_r_deg=0.0,
        thigh_l_deg=165.0,  # Trailing leg kicking back high
        shin_l_deg=175.0,
        thigh_r_deg=50.0,   # Leading front leg planted on ground
        shin_r_deg=80.0,
    )
    return PoseDefinition(
        name="forward_charge",
        pose=pose,
        support_mode=SupportMode.RIGHT_ONLY,
        elevation=0.0,
        weapon_anchor=JointType.WRIST_R,
        weapon_angle_deg=5.0,
        description="High speed forward charge with aggressive forward torso lean and weapon thrust.",
    )


def _build_overhead_slam() -> PoseDefinition:
    """4. OVERHEAD_SLAM: Both arms raised above head, torso arched back, preparing devastating ground slam."""
    # Both feet grounded at equal Ankle Y = 180.0 px (Contact Y = 185.0 px)
    pose = _fk_pose(
        name="overhead_slam",
        spine_deg=-105.0,  # Arched back 15 deg
        neck_deg=-100.0,
        head_deg=-85.0,
        shoulder_l_deg=-85.0,
        elbow_l_deg=-75.0,
        wrist_l_deg=-65.0,
        shoulder_r_deg=-80.0,
        elbow_r_deg=-85.0,
        wrist_r_deg=-75.0,
        thigh_l_deg=80.0,
        shin_l_deg=106.16154781311559,  # Y = 180.0
        thigh_r_deg=75.0,
        shin_r_deg=78.64078576356133,   # Y = 180.0
    )
    return PoseDefinition(
        name="overhead_slam",
        pose=pose,
        support_mode=SupportMode.DOUBLE,
        elevation=0.0,
        weapon_anchor=JointType.WRIST_R,
        weapon_angle_deg=-70.0,
        secondary_grip=JointType.WRIST_L,
        description="Two-handed overhead weapon raise with arched spine preparing ground slam.",
    )


def _build_mid_air_leap() -> PoseDefinition:
    """5. MID_AIR_LEAP: Airborne jump, tucked knees, soaring upward into upper half of canvas."""
    pose = _fk_pose(
        name="mid_air_leap",
        spine_deg=-80.0,
        neck_deg=-80.0,
        head_deg=-75.0,
        shoulder_l_deg=-140.0,
        elbow_l_deg=-100.0,
        wrist_l_deg=-60.0,
        shoulder_r_deg=-30.0,
        elbow_r_deg=-15.0,
        wrist_r_deg=10.0,
        thigh_l_deg=140.0,  # Tucked back
        shin_l_deg=30.0,
        thigh_r_deg=35.0,   # Tucked forward
        shin_r_deg=115.0,
    )
    return PoseDefinition(
        name="mid_air_leap",
        pose=pose,
        support_mode=SupportMode.AIRBORNE,
        elevation=500.0,  # Default elevation 500px above ground reference
        weapon_anchor=JointType.WRIST_R,
        weapon_angle_deg=-30.0,
        description="Airborne soaring leap with tucked knees into upper canvas region.",
    )


def _build_guard_block() -> PoseDefinition:
    """6. GUARD_BLOCK: Defensive angle, arms crossed forming vertical barrier before torso."""
    # Both feet grounded at equal Ankle Y = 175.0 px (Contact Y = 180.0 px)
    pose = _fk_pose(
        name="guard_block",
        spine_deg=-95.0,
        neck_deg=-95.0,
        head_deg=-90.0,
        shoulder_l_deg=-10.0,
        elbow_l_deg=80.0,
        wrist_l_deg=-85.0,
        shoulder_r_deg=10.0,
        elbow_r_deg=100.0,
        wrist_r_deg=-80.0,
        thigh_l_deg=75.0,
        shin_l_deg=112.35333808225772,  # Y = 175.0
        thigh_r_deg=68.0,
        shin_r_deg=74.96120883220438,   # Y = 175.0
    )
    return PoseDefinition(
        name="guard_block",
        pose=pose,
        support_mode=SupportMode.DOUBLE,
        elevation=0.0,
        weapon_anchor=JointType.WRIST_R,
        weapon_angle_deg=88.0,
        secondary_grip=JointType.WRIST_L,
        description="Defensive guard posture with crossed forearms locking weapon vertically before chest.",
    )


def _build_vortex_sweep() -> PoseDefinition:
    """7. VORTEX_SWEEP: Left leg support anchor, right leg sweeping in mid-air, horizontal 360 weapon swing."""
    pose = _fk_pose(
        name="vortex_sweep",
        spine_deg=-75.0,
        neck_deg=-70.0,
        head_deg=-65.0,
        shoulder_l_deg=180.0,
        elbow_l_deg=180.0,
        wrist_l_deg=180.0,
        shoulder_r_deg=0.0,
        elbow_r_deg=0.0,
        wrist_r_deg=0.0,
        thigh_l_deg=90.0,  # Left leg firmly planted as pivot
        shin_l_deg=90.0,
        thigh_r_deg=15.0,  # Right leg sweeping horizontally above ground
        shin_r_deg=10.0,
    )
    return PoseDefinition(
        name="vortex_sweep",
        pose=pose,
        support_mode=SupportMode.LEFT_ONLY,
        elevation=0.0,
        weapon_anchor=JointType.WRIST_R,
        weapon_angle_deg=0.0,
        description="Dynamic vortex spin on left pivot foot with outstretched horizontal weapon swing.",
    )


def _build_knockback_slide() -> PoseDefinition:
    """8. KNOCKBACK_SLIDE: Torso recoiling backward 45 deg, left leg bracing slide, weapon ground-braking."""
    pose = _fk_pose(
        name="knockback_slide",
        spine_deg=-135.0,  # Reeled backward 45 deg
        neck_deg=-125.0,
        head_deg=-100.0,
        shoulder_l_deg=-150.0,
        elbow_l_deg=-110.0,
        wrist_l_deg=-70.0,
        shoulder_r_deg=30.0,
        elbow_r_deg=65.0,
        wrist_r_deg=105.0,
        thigh_l_deg=50.0,   # Left leg extended forward bracing the slide
        shin_l_deg=35.0,
        thigh_r_deg=-15.0,  # Right leg kicked back up in recoil
        shin_r_deg=25.0,
    )
    return PoseDefinition(
        name="knockback_slide",
        pose=pose,
        support_mode=SupportMode.LEFT_ONLY,
        elevation=0.0,
        weapon_anchor=JointType.WRIST_R,
        weapon_angle_deg=125.0,
        description="Heavy knockback recoil sliding across paper ground with bracing foot and weapon friction.",
    )


class PoseCatalog:
    """
    Registry of the 8 canonical Dark Myth stickman combat poses.

    Guarantees:
      - 100% Euclidean bone length preservation (FK construction).
      - Strict compliance with RigidBoneValidator (epsilon <= 0.5 px).
      - Accurate support mode and ground alignment metadata.
      - Immutable returns preventing catalog corruption.
    """

    STANDOFF_IDLE = "standoff_idle"
    COMBAT_STANCE = "combat_stance"
    FORWARD_CHARGE = "forward_charge"
    OVERHEAD_SLAM = "overhead_slam"
    MID_AIR_LEAP = "mid_air_leap"
    GUARD_BLOCK = "guard_block"
    VORTEX_SWEEP = "vortex_sweep"
    KNOCKBACK_SLIDE = "knockback_slide"

    ALL_POSES: tuple[str, ...] = (
        STANDOFF_IDLE,
        COMBAT_STANCE,
        FORWARD_CHARGE,
        OVERHEAD_SLAM,
        MID_AIR_LEAP,
        GUARD_BLOCK,
        VORTEX_SWEEP,
        KNOCKBACK_SLIDE,
    )

    # Internal singleton registry populated once
    _DEFINITIONS: dict[str, PoseDefinition] = {
        STANDOFF_IDLE: _build_standoff_idle(),
        COMBAT_STANCE: _build_combat_stance(),
        FORWARD_CHARGE: _build_forward_charge(),
        OVERHEAD_SLAM: _build_overhead_slam(),
        MID_AIR_LEAP: _build_mid_air_leap(),
        GUARD_BLOCK: _build_guard_block(),
        VORTEX_SWEEP: _build_vortex_sweep(),
        KNOCKBACK_SLIDE: _build_knockback_slide(),
    }

    @classmethod
    def normalize_name(cls, name: str) -> str:
        """Normalize input pose identifier to canonical lower_snake_case key."""
        cleaned = str(name).lower().strip().replace(" ", "_").replace("-", "_")
        if cleaned in cls._DEFINITIONS:
            return cleaned
        # Check alias variations
        alias_map = {
            "idle": cls.STANDOFF_IDLE,
            "standoff": cls.STANDOFF_IDLE,
            "combat": cls.COMBAT_STANCE,
            "stance": cls.COMBAT_STANCE,
            "charge": cls.FORWARD_CHARGE,
            "slam": cls.OVERHEAD_SLAM,
            "leap": cls.MID_AIR_LEAP,
            "jump": cls.MID_AIR_LEAP,
            "block": cls.GUARD_BLOCK,
            "guard": cls.GUARD_BLOCK,
            "sweep": cls.VORTEX_SWEEP,
            "vortex": cls.VORTEX_SWEEP,
            "knockback": cls.KNOCKBACK_SLIDE,
            "slide": cls.KNOCKBACK_SLIDE,
        }
        if cleaned in alias_map:
            return alias_map[cleaned]
        raise KeyError(
            f"Unknown pose '{name}'. Valid canonical poses: {list(cls.ALL_POSES)}"
        )

    @classmethod
    def get_definition(cls, name: str) -> PoseDefinition:
        """Retrieve full PoseDefinition metadata for named pose with defensive deep copy."""
        canonical_name = cls.normalize_name(name)
        raw_defn = cls._DEFINITIONS[canonical_name]
        return _clone_definition(raw_defn)

    @classmethod
    def get_pose(cls, name: str) -> StickmanPose:
        """Retrieve StickmanPose joint configuration with defensive deep copy of joints dict."""
        defn = cls.get_definition(name)
        return defn.pose

    @classmethod
    def list_poses(cls) -> list[str]:
        """Return list of all 8 canonical pose names."""
        return list(cls.ALL_POSES)

    @classmethod
    def get_all_definitions(cls) -> dict[str, PoseDefinition]:
        """Return dictionary mapping of all 8 pose definitions with defensive deep copy."""
        return {k: _clone_definition(v) for k, v in cls._DEFINITIONS.items()}
        """Return dictionary mapping of all 8 pose definitions."""
        return dict(cls._DEFINITIONS)
