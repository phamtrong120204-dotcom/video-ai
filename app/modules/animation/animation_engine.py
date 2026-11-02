"""
Dark Myth Stickman Auto-Studio - Production Animation Engine.

Implements IAnimationEngine interface, integrating AnimationLoopEngine,
PoseCatalog, StickmanCharacter renderers, and DarkCorruptionVFXEngine.
"""

import math
from pathlib import Path
from typing import Optional

from PIL import Image

from app.core.exceptions import AnimationRenderError
from app.core.logger import get_logger
from app.interfaces.base_animator import IAnimationEngine
from app.modules.animation.animation_loop import AnimationLoopEngine, AnimationTrack, Keyframe
from app.modules.animation.background_renderer import NotebookBackgroundRenderer
from app.modules.animation.interpolation_engine import EasingFunction
from app.modules.animation.stickman_models import Point2D, StickmanCharacter
from app.modules.animation.vfx_engine import DarkCorruptionVFXEngine
from app.modules.animation.vfx_models import VFXConfig
from app.schemas.scene_schema import (
    ActionPreset,
    ActorConfig,
    ActorSide,
    BackgroundState,
    CharacterSkin,
    SceneSchema,
    WeaponType,
)

logger = get_logger("modules.animation.engine")


class DarkMythAnimationEngine(IAnimationEngine):
    """
    Production-grade stickman animation engine implementing IAnimationEngine.
    Renders 1080x1920 30FPS combat scenes with 7-layer Dark Corruption VFX.
    """

    def __init__(
        self,
        animation_loop: Optional[AnimationLoopEngine] = None,
        vfx_engine: Optional[DarkCorruptionVFXEngine] = None,
        background_renderer: Optional[NotebookBackgroundRenderer] = None,
        fps: int = 30,
    ) -> None:
        self.fps = fps
        self.animation_loop = animation_loop or AnimationLoopEngine()
        self.vfx_engine = vfx_engine or DarkCorruptionVFXEngine()
        self.bg_renderer = background_renderer or NotebookBackgroundRenderer()

    def _build_actor_track(
        self,
        actor: ActorConfig,
        action_preset: Optional[ActionPreset],
        duration_sec: float,
        is_primary: bool = True,
    ) -> tuple[StickmanCharacter, AnimationTrack]:
        """
        Constructs StickmanCharacter and high-speed, dynamic martial arts AnimationTrack.
        Animates rapid combos, evasions, and clashes at 0.2s - 0.4s per action.
        """
        char = StickmanCharacter.from_actor_config(actor)
        facing = +1 if actor.side in (ActorSide.LEFT, ActorSide.CENTER) else -1
        base_x = 380.0 if facing > 0 else 700.0

        preset = action_preset or ActionPreset.HEAVY_CHARGE_CLASH
        preset_key = preset.value if hasattr(preset, "value") else str(preset)

        kfs: list[Keyframe] = []

        if preset_key == "giant_palm_suppression":
            # Defiant struggle against crushing heavenly gravity
            hero_x = 520.0 if facing > 0 else 560.0
            kfs.append(Keyframe(time_sec=0.0, pose_name="standoff_idle", canvas_pos=Point2D(hero_x, 1350.0), facing=facing, easing=EasingFunction.EASE_OUT))
            kfs.append(Keyframe(time_sec=round(min(1.2, duration_sec * 0.15), 3), pose_name="combat_stance", canvas_pos=Point2D(hero_x, 1350.0), facing=facing, easing=EasingFunction.EASE_IN))
            kfs.append(Keyframe(time_sec=round(min(3.5, duration_sec * 0.35), 3), pose_name="guard_block", canvas_pos=Point2D(hero_x, 1390.0), facing=facing, easing=EasingFunction.EASE_OUT))
            kfs.append(Keyframe(time_sec=round(min(6.0, duration_sec * 0.55), 3), pose_name="combat_stance", canvas_pos=Point2D(hero_x, 1370.0), facing=facing, easing=EasingFunction.EASE_IN))
            # Explosive defiant air counter-attack
            kfs.append(Keyframe(time_sec=round(min(7.5, duration_sec * 0.70), 3), pose_name="mid_air_leap", canvas_pos=Point2D(hero_x, 1140.0), facing=facing, easing=EasingFunction.EASE_OUT))
            kfs.append(Keyframe(time_sec=round(min(8.2, duration_sec * 0.78), 3), pose_name="overhead_slam", canvas_pos=Point2D(hero_x, 1200.0), facing=facing, easing=EasingFunction.EASE_IN))
            kfs.append(Keyframe(time_sec=round(min(9.5, duration_sec * 0.88), 3), pose_name="knockback_slide", canvas_pos=Point2D(hero_x - 30.0 * facing, 1350.0), facing=facing, easing=EasingFunction.EASE_OUT))
            kfs.append(Keyframe(time_sec=duration_sec, pose_name="combat_stance", canvas_pos=Point2D(hero_x, 1350.0), facing=facing, easing=EasingFunction.EASE_IN_OUT))
        else:
            # High-octane martial arts sequence generator
            t = 0.0
            kfs.append(Keyframe(time_sec=0.0, pose_name="standoff_idle", canvas_pos=Point2D(base_x, 1350.0), facing=facing, easing=EasingFunction.EASE_OUT))
            intro_dur = min(0.6, duration_sec * 0.08)
            t = intro_dur
            kfs.append(Keyframe(time_sec=round(t, 3), pose_name="combat_stance", canvas_pos=Point2D(base_x + 15.0 * facing, 1350.0), facing=facing, easing=EasingFunction.EASE_IN))

            # Define fast combo modules (0.2s - 0.4s per move)
            if is_primary:
                # Primary fighter (Wukong) combos
                combos = [
                    # Combo 1: Dash Slash -> Slam -> Parry Block
                    [
                        (0.25, "forward_charge", 490.0, 1350.0, EasingFunction.EASE_IN),
                        (0.28, "overhead_slam", 530.0, 1350.0, EasingFunction.EASE_OUT),
                        (0.32, "guard_block", 460.0, 1350.0, EasingFunction.EASE_IN_OUT),
                        (0.35, "combat_stance", 420.0, 1350.0, EasingFunction.EASE_IN_OUT),
                    ],
                    # Combo 2: Flash Step -> Whirlwind Vortex -> Leap Slam
                    [
                        (0.22, "forward_charge", 480.0, 1350.0, EasingFunction.EASE_IN),
                        (0.38, "vortex_sweep", 530.0, 1350.0, EasingFunction.EASE_IN_OUT),
                        (0.32, "mid_air_leap", 470.0, 1140.0, EasingFunction.EASE_OUT),
                        (0.30, "overhead_slam", 540.0, 1350.0, EasingFunction.EASE_IN),
                        (0.32, "knockback_slide", 400.0, 1350.0, EasingFunction.EASE_OUT),
                        (0.30, "combat_stance", 420.0, 1350.0, EasingFunction.EASE_IN_OUT),
                    ],
                    # Combo 3: Multi-strike Flurry
                    [
                        (0.25, "forward_charge", 510.0, 1350.0, EasingFunction.EASE_IN),
                        (0.25, "overhead_slam", 530.0, 1350.0, EasingFunction.EASE_OUT),
                        (0.35, "vortex_sweep", 510.0, 1350.0, EasingFunction.EASE_IN_OUT),
                        (0.30, "guard_block", 450.0, 1350.0, EasingFunction.EASE_OUT),
                        (0.35, "combat_stance", 410.0, 1350.0, EasingFunction.EASE_IN_OUT),
                    ],
                ]
            else:
                # Secondary opponent combos (mirrors & counters Wukong)
                combos = [
                    # Combo 1 Reaction: Intercept Block -> Recoil -> Spear Counter
                    [
                        (0.25, "guard_block", 590.0, 1350.0, EasingFunction.EASE_OUT),
                        (0.28, "knockback_slide", 650.0, 1350.0, EasingFunction.EASE_OUT),
                        (0.32, "forward_charge", 580.0, 1350.0, EasingFunction.EASE_IN),
                        (0.35, "combat_stance", 640.0, 1350.0, EasingFunction.EASE_IN_OUT),
                    ],
                    # Combo 2 Reaction: Jump Evasion -> Downward Spear Cleave -> Defense
                    [
                        (0.22, "guard_block", 600.0, 1350.0, EasingFunction.EASE_IN_OUT),
                        (0.38, "mid_air_leap", 650.0, 1140.0, EasingFunction.EASE_OUT),
                        (0.32, "overhead_slam", 580.0, 1350.0, EasingFunction.EASE_IN),
                        (0.30, "knockback_slide", 660.0, 1350.0, EasingFunction.EASE_OUT),
                        (0.32, "combat_stance", 650.0, 1350.0, EasingFunction.EASE_IN_OUT),
                        (0.30, "guard_block", 640.0, 1350.0, EasingFunction.EASE_IN_OUT),
                    ],
                    # Combo 3 Reaction: High-speed Clash
                    [
                        (0.25, "forward_charge", 570.0, 1350.0, EasingFunction.EASE_IN),
                        (0.25, "guard_block", 590.0, 1350.0, EasingFunction.EASE_OUT),
                        (0.35, "overhead_slam", 570.0, 1350.0, EasingFunction.EASE_IN_OUT),
                        (0.30, "knockback_slide", 660.0, 1350.0, EasingFunction.EASE_OUT),
                        (0.35, "combat_stance", 650.0, 1350.0, EasingFunction.EASE_IN_OUT),
                    ],
                ]

            combo_idx = 0
            climax_reserve = min(1.2, duration_sec * 0.15)
            while t + 1.2 < duration_sec - climax_reserve:
                combo = combos[combo_idx % len(combos)]
                combo_idx += 1
                for dt, pose, px, py, ease in combo:
                    if t + dt >= duration_sec - climax_reserve:
                        break
                    t += dt
                    actual_x = px if facing > 0 else (1080.0 - px)
                    kfs.append(Keyframe(time_sec=round(t, 3), pose_name=pose, canvas_pos=Point2D(actual_x, py), facing=facing, easing=ease))

            # Climax Finish & Return to lethal Standoff
            rem = duration_sec - t
            if rem > 0.6:
                t += rem * 0.4
                leap_x = 440.0 if facing > 0 else 640.0
                kfs.append(Keyframe(time_sec=round(t, 3), pose_name="mid_air_leap", canvas_pos=Point2D(leap_x, 1140.0), facing=facing, easing=EasingFunction.EASE_OUT))
                t += rem * 0.35
                slam_x = 510.0 if facing > 0 else 570.0
                kfs.append(Keyframe(time_sec=round(t, 3), pose_name="overhead_slam", canvas_pos=Point2D(slam_x, 1350.0), facing=facing, easing=EasingFunction.EASE_IN))

            kfs.append(Keyframe(time_sec=duration_sec, pose_name="standoff_idle", canvas_pos=Point2D(base_x, 1350.0), facing=facing, easing=EasingFunction.EASE_IN_OUT))

        track = AnimationTrack(keyframes=kfs, duration_sec=duration_sec, loop=False)
        return char, track

    def render_scene_frames(self, scene: SceneSchema, duration_sec: float, output_dir: Path) -> Path:
        """
        Renders stickman animation frames for `scene` matching `duration_sec` exactly,
        and saves the scene video to `output_dir / f"scene_{scene.scene_id}.mp4"`.
        Supports dual characters and celestial Buddha Palm descent.
        """
        if duration_sec <= 0.0 or not math.isfinite(duration_sec):
            raise AnimationRenderError(f"Invalid duration_sec: {duration_sec}")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        scene_frames_dir = output_dir / f"scene_{scene.scene_id}_frames"
        scene_frames_dir.mkdir(parents=True, exist_ok=True)
        scene_video_path = output_dir / f"scene_{scene.scene_id}.mp4"

        logger.info(
            f"Rendering scene {scene.scene_id}: {duration_sec:.2f}s ({round(duration_sec * self.fps)} frames)"
        )

        # 1. Resolve actors (primary & secondary)
        actors = scene.actors or []
        buddha_palm_active = (scene.action_preset == ActionPreset.GIANT_PALM_SUPPRESSION)

        if not actors:
            primary_actor = ActorConfig(
                actor_id="dark_wukong",
                display_name="Dark Wukong",
                side=ActorSide.LEFT,
                skin=CharacterSkin.DARK_WUKONG,
                weapon=WeaponType.RUYI_STAFF,
                scale=1.05,
            )
            secondary_actor = None
        elif len(actors) == 1:
            if actors[0].skin == CharacterSkin.BUDDHA_PALM:
                # Wukong defies the descending Buddha Palm
                primary_actor = ActorConfig(
                    actor_id=f"dark_wukong_defiant_{scene.scene_id}",
                    display_name="Dark Wukong",
                    side=ActorSide.LEFT,
                    skin=CharacterSkin.DARK_WUKONG,
                    weapon=WeaponType.RUYI_STAFF,
                    scale=1.05,
                )
                secondary_actor = None
                buddha_palm_active = True
            else:
                primary_actor = actors[0]
                secondary_actor = None
        else:
            primary_actor = actors[0]
            secondary_actor = actors[1]
            if any(a.skin == CharacterSkin.BUDDHA_PALM for a in actors):
                buddha_palm_active = True

        char1, track1 = self._build_actor_track(
            actor=primary_actor,
            action_preset=scene.action_preset,
            duration_sec=duration_sec,
            is_primary=True,
        )

        char2, track2 = None, None
        if secondary_actor is not None:
            char2, track2 = self._build_actor_track(
                actor=secondary_actor,
                action_preset=scene.action_preset,
                duration_sec=duration_sec,
                is_primary=False,
            )

        # 2. Render background
        base_bg = self.bg_renderer.render_background(
            state=scene.background_state or BackgroundState.NORMAL_PAGE,
            seed=scene.scene_id * 101,
        )

        # 3. Schedule VFX events
        self.vfx_engine.clear_events()
        vfx_events = self.vfx_engine.map_action_preset_vfx(
            action_preset=scene.action_preset or ActionPreset.HEAVY_CHARGE_CLASH,
            scene_start_sec=0.0,
            scene_duration_sec=duration_sec,
            character_center=Point2D(540.0, 1350.0),
            intensity=1.2,
        )
        for ev in vfx_events:
            self.vfx_engine.add_event(ev)

        # 4. Generate all frames with 7-layer VFX Engine
        frames = self.vfx_engine.generate_clip_frames_with_vfx(
            track=track1,
            character=char1,
            fps=self.fps,
            background_image=base_bg,
            animation_engine=self.animation_loop,
            output_dir=scene_frames_dir,
            frame_name_prefix=f"s{scene.scene_id}_frame",
            secondary_track=track2,
            secondary_character=char2,
            buddha_palm_active=buddha_palm_active,
        )

        # 5. Export scene video MP4
        self.animation_loop.export_mp4_video(
            frames_or_dir=frames,
            output_mp4_path=scene_video_path,
            fps=self.fps,
        )

        logger.info(f"Scene {scene.scene_id} animation rendered successfully: {scene_video_path}")
        return scene_video_path
