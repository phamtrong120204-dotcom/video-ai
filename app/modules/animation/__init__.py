"""Skeleton / Stickman Animation Engine Module."""

import json
from pathlib import Path

from app.core.exceptions import AnimationRenderError
from app.interfaces.base_animator import IAnimationEngine
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
    GripValidationResult,
    HumanoidBodyRenderer,
    WeaponRenderer,
    composite_character,
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
    BoneDefinition,
    BoneValidationDetail,
    CoordinateManager,
    HumanoidSkeleton,
    JointType,
    Point2D,
    RigidBoneValidator,
    StickmanCharacter,
    StickmanPose,
    SupportMode,
    ValidationResult,
    generate_actor_seed,
    parse_hex_color,
)
from app.modules.animation.vfx_distortion import WarpDistortionField
from app.modules.animation.vfx_engine import DarkCorruptionVFXEngine
from app.modules.animation.vfx_models import (
    Particle,
    VFXConfig,
    VFXEvent,
    VFXEventType,
    WarpProfile,
)
from app.modules.animation.vfx_motion_trail import MotionTrailRenderer
from app.modules.animation.vfx_particles import ParticleSystem
from app.schemas.scene_schema import SceneSchema


class StubAnimationEngine(IAnimationEngine):
    """Deterministic skeleton animation engine verifying audio-driven frame count calculation."""

    def __init__(self, fps: int = 30) -> None:
        self.fps = fps

    def render_scene_frames(self, scene: SceneSchema, duration_sec: float, output_dir: Path) -> Path:
        if duration_sec <= 0.0:
            raise AnimationRenderError(
                f"Scene {scene.scene_id} requires positive duration_sec, got {duration_sec}"
            )

        output_dir.mkdir(parents=True, exist_ok=True)
        total_frames = max(1, round(duration_sec * self.fps))
        manifest_path = output_dir / f"scene_{scene.scene_id:02d}_frames.json"

        payload = {
            "scene_id": scene.scene_id,
            "duration_sec": duration_sec,
            "fps": self.fps,
            "total_frames": total_frames,
            "background_state": scene.background_state.value,
            "action_preset": scene.action_preset.value,
            "camera_movement": scene.camera_movement.value,
            "actor_count": len(scene.actors),
        }
        manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return manifest_path


__all__ = [
    "StubAnimationEngine",
    "NotebookBackgroundRenderer",
    "HumanoidBodyRenderer",
    "FaceFeatureRenderer",
    "AccessoriesRenderer",
    "WeaponRenderer",
    "BuddhaPalmRenderer",
    "GripValidationResult",
    "composite_character",
    "PoseCatalog",
    "PoseDefinition",
    "Point2D",
    "JointType",
    "BoneDefinition",
    "HumanoidSkeleton",
    "StickmanPose",
    "SupportMode",
    "BoneValidationDetail",
    "ValidationResult",
    "RigidBoneValidator",
    "CoordinateManager",
    "StickmanCharacter",
    "parse_hex_color",
    "generate_actor_seed",
    "EasingFunction",
    "evaluate_easing",
    "extract_bone_angles",
    "interpolate_bone_angles",
    "reconstruct_pose_from_angles",
    "interpolate_poses",
    "InterpolationEngine",
    "Keyframe",
    "AnimationTrack",
    "AnimationState",
    "AnimationLoopEngine",
    "VFXEventType",
    "WarpProfile",
    "VFXEvent",
    "Particle",
    "VFXConfig",
    "WarpDistortionField",
    "ParticleSystem",
    "MotionTrailRenderer",
    "DarkCorruptionVFXEngine",
]
