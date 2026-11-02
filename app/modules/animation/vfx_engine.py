"""
Dark Myth Stickman Auto-Studio - Stage 8: Dark Corruption VFX Engine.

Master visual effects orchestrator coordinating:
  1. Notebook Background Warp Distortion
  2. Ground Fractures & Ink Splatters
  3. Character Dark Corruption Aura & Smoke Tendrils
  4. Humanoid Stickman Composite & Buddha Palm
  5. Weapon Motion Trails & Slash Ribbons
  6. Impact Clash Sparks & Expanding Shockwaves
"""

from collections import deque
import math
from pathlib import Path
from typing import Optional, Union

from PIL import Image

from app.core.logger import get_logger
from app.modules.animation.animation_loop import AnimationLoopEngine, AnimationTrack
from app.modules.animation.buddha_palm_renderer import BuddhaPalmRenderer
from app.modules.animation.character_renderer_parts import (
    AccessoriesRenderer,
    FaceFeatureRenderer,
    HumanoidBodyRenderer,
    WeaponRenderer,
    composite_character,
)
from app.modules.animation.stickman_models import CoordinateManager, Point2D, StickmanCharacter
from app.modules.animation.vfx_distortion import WarpDistortionField
from app.modules.animation.vfx_models import (
    VFXConfig,
    VFXEvent,
    VFXEventType,
    WarpProfile,
)
from app.modules.animation.vfx_motion_trail import MotionTrailRenderer
from app.modules.animation.vfx_particles import ParticleSystem
from app.schemas.scene_schema import ActionPreset, CharacterSkin, WeaponType

logger = get_logger("vfx_engine")


class DarkCorruptionVFXEngine:
    """
    Coordinates all 7 visual effects layers and integrates with G6 Animation & G7 Audio.
    """

    def __init__(
        self,
        config: Optional[VFXConfig] = None,
        body_renderer: Optional[HumanoidBodyRenderer] = None,
        face_renderer: Optional[FaceFeatureRenderer] = None,
        accessories_renderer: Optional[AccessoriesRenderer] = None,
        weapon_renderer: Optional[WeaponRenderer] = None,
        buddha_palm_renderer: Optional[BuddhaPalmRenderer] = None,
    ) -> None:
        self.config = config or VFXConfig()
        self.distortion_field = WarpDistortionField(
            width=self.config.canvas_width,
            height=self.config.canvas_height,
            grid_nx=self.config.warp_grid_nx,
            grid_ny=self.config.warp_grid_ny,
        )
        self.particle_system = ParticleSystem(config=self.config)
        self.motion_trail_renderer = MotionTrailRenderer(
            canvas_size=(self.config.canvas_width, self.config.canvas_height),
            max_history=6,
        )

        # Inherit G5 renderers
        self.body_renderer = body_renderer or HumanoidBodyRenderer()
        self.face_renderer = face_renderer or FaceFeatureRenderer()
        self.accessories_renderer = accessories_renderer or AccessoriesRenderer()
        self.buddha_palm_renderer = buddha_palm_renderer or BuddhaPalmRenderer()
        self.weapon_renderer = weapon_renderer or WeaponRenderer(
            body_renderer=self.body_renderer,
            buddha_palm_renderer=self.buddha_palm_renderer,
        )

        self._active_events: list[VFXEvent] = []

    @property
    def events(self) -> list[VFXEvent]:
        """Return the list of scheduled timeline VFX events."""
        return self._active_events

    def clear_events(self) -> None:
        """Clear all registered VFX events."""
        self._active_events.clear()
        self.motion_trail_renderer.reset()

    def add_event(self, event: VFXEvent) -> None:
        """Register a VFX event on the timeline."""
        self._active_events.append(event)
        self._active_events.sort(key=lambda ev: ev.start_time_sec)

    def map_action_preset_vfx(
        self,
        action_preset: Union[ActionPreset, str],
        scene_start_sec: float,
        scene_duration_sec: float,
        character_center: Point2D,
        intensity: float = 1.0,
    ) -> list[VFXEvent]:
        """
        Generate default Dark Myth VFX events corresponding to a combat ActionPreset.
        """
        preset_key = action_preset.value if isinstance(action_preset, ActionPreset) else str(action_preset)
        events: list[VFXEvent] = []

        if preset_key == "heavy_charge_clash":
            impact_t = scene_start_sec + (0.45 * scene_duration_sec)
            impact_pt = Point2D(540.0, 1280.0)
            events.append(VFXEvent(
                event_id="clash_sparks_01",
                event_type=VFXEventType.CLASH_SPARKS,
                start_time_sec=impact_t,
                duration_sec=0.55,
                center=impact_pt,
                intensity=intensity * 1.2,
                color=(255, 230, 100, 255),
            ))
            events.append(VFXEvent(
                event_id="shockwave_01",
                event_type=VFXEventType.SHOCKWAVE_RING,
                start_time_sec=impact_t,
                duration_sec=0.60,
                center=impact_pt,
                intensity=intensity,
                radius=320.0,
                color=(217, 38, 38, 255),
            ))
            events.append(VFXEvent(
                event_id="ground_cracks_01",
                event_type=VFXEventType.GROUND_CRACK,
                start_time_sec=impact_t,
                duration_sec=1.20,
                center=impact_pt,
                intensity=intensity,
                radius=260.0,
            ))

        elif preset_key in ("overhead_slam", "sky_leap_slam"):
            impact_t = scene_start_sec + (0.60 * scene_duration_sec)
            impact_pt = Point2D(540.0, 1420.0)
            events.append(VFXEvent(
                event_id="slam_shockwave",
                event_type=VFXEventType.SHOCKWAVE_RING,
                start_time_sec=impact_t,
                duration_sec=0.75,
                center=impact_pt,
                intensity=intensity * 1.3,
                radius=380.0,
                color=(217, 38, 38, 255),
            ))
            events.append(VFXEvent(
                event_id="slam_cracks",
                event_type=VFXEventType.GROUND_CRACK,
                start_time_sec=impact_t,
                duration_sec=1.50,
                center=impact_pt,
                intensity=intensity * 1.2,
                radius=320.0,
            ))
            events.append(VFXEvent(
                event_id="slam_dust",
                event_type=VFXEventType.PAPER_DUST,
                start_time_sec=impact_t,
                duration_sec=0.80,
                center=impact_pt,
                intensity=intensity,
            ))

        elif preset_key == "giant_palm_suppression":
            # Palm descent and ground crushing distortion
            warp_start = scene_start_sec + (0.25 * scene_duration_sec)
            warp_dur = 0.70 * scene_duration_sec
            impact_pt = Point2D(540.0, 850.0)
            events.append(VFXEvent(
                event_id="palm_warp_depression",
                event_type=VFXEventType.BACKGROUND_WARP,
                start_time_sec=warp_start,
                duration_sec=warp_dur,
                center=impact_pt,
                intensity=intensity * 1.25,
                radius=480.0,
                metadata={
                    "profile": WarpProfile.PALM_DEPRESSION,
                    "max_amplitude_px": 85.0,
                    "sigma_x": 340.0,
                    "sigma_y": 260.0,
                },
            ))
            events.append(VFXEvent(
                event_id="palm_shockwave",
                event_type=VFXEventType.SHOCKWAVE_RING,
                start_time_sec=scene_start_sec + (0.55 * scene_duration_sec),
                duration_sec=0.80,
                center=Point2D(540.0, 1420.0),
                intensity=intensity * 1.5,
                radius=480.0,
                color=(246, 173, 85, 255),  # Golden aura
            ))

        elif preset_key == "staff_vortex_sweep":
            start_t = scene_start_sec + (0.20 * scene_duration_sec)
            events.append(VFXEvent(
                event_id="vortex_shockwave",
                event_type=VFXEventType.SHOCKWAVE_RING,
                start_time_sec=start_t,
                duration_sec=0.70,
                center=character_center,
                intensity=intensity,
                radius=360.0,
                color=(217, 38, 38, 255),
            ))

        elif preset_key == "knockback_recovery":
            impact_t = scene_start_sec + (0.20 * scene_duration_sec)
            slide_t = scene_start_sec + (0.65 * scene_duration_sec)
            events.append(VFXEvent(
                event_id="knockback_sparks",
                event_type=VFXEventType.CLASH_SPARKS,
                start_time_sec=impact_t,
                duration_sec=0.45,
                center=character_center,
                intensity=intensity * 0.9,
            ))
            events.append(VFXEvent(
                event_id="slide_paper_dust",
                event_type=VFXEventType.PAPER_DUST,
                start_time_sec=slide_t,
                duration_sec=0.60,
                center=Point2D(250.0, 1420.0),
                intensity=intensity * 0.8,
            ))

        return events

    def render_frame_with_vfx(
        self,
        character: StickmanCharacter,
        pose_def: object,
        canvas_pos: Point2D,
        facing: int,
        current_time_sec: float,
        frame_idx: int,
        background_image: Optional[Image.Image] = None,
        align_two_hands: Optional[bool] = None,
        custom_vfx_events: Optional[list[VFXEvent]] = None,
        secondary_character: Optional[StickmanCharacter] = None,
        secondary_pose_def: Optional[object] = None,
        secondary_canvas_pos: Optional[Point2D] = None,
        secondary_facing: int = -1,
        buddha_palm_progress: Optional[float] = None,
    ) -> Image.Image:
        """
        Composite a single animation frame across all 7 VFX layers.
        Supports dual characters and dynamic celestial Buddha Palm overlay.
        """
        all_events = (custom_vfx_events or []) + self._active_events
        w, h = self.config.canvas_width, self.config.canvas_height

        # LAYER 1 & 2: Background with Warp Distortion Field
        if background_image is not None:
            bg_base = background_image
            if bg_base.size != (w, h):
                bg_base = bg_base.resize((w, h), Image.Resampling.LANCZOS)
            if self.config.enable_background_warp:
                bg_distorted = self.distortion_field.apply_distortion(
                    background_image=bg_base,
                    active_events=all_events,
                    current_time_sec=current_time_sec,
                )
            else:
                bg_distorted = bg_base
            composite = bg_distorted.convert("RGBA")
        else:
            composite = Image.new("RGBA", (w, h), (0, 0, 0, 0))

        # LAYER 3: Background Splatters / Ground Cracks / Paper Dust
        if self.config.enable_ground_cracks:
            for ev in all_events:
                u = ev.get_progress(current_time_sec)
                if u is not None and 0.0 <= u <= 1.0:
                    if ev.event_type == VFXEventType.GROUND_CRACK:
                        crack_layer = self.particle_system.render_ground_cracks(ev, progress=u)
                        composite = Image.alpha_composite(composite, crack_layer)
                    elif ev.event_type == VFXEventType.PAPER_DUST:
                        dust_layer = self.particle_system.render_paper_dust(ev, progress=u)
                        composite = Image.alpha_composite(composite, dust_layer)

        # LAYER 4: Character Back Effects (Dark Corruption Aura behind)
        if self.config.enable_dark_aura:
            # Secondary character back aura
            if secondary_character is not None and secondary_canvas_pos is not None:
                sec_aura_color = (230, 184, 0) if secondary_character.skin != CharacterSkin.DARK_WUKONG else (217, 38, 38)
                sec_back_aura = self.particle_system.render_dark_aura(
                    character_center=secondary_canvas_pos,
                    facing=secondary_facing,
                    scale=secondary_character.scale,
                    current_time_sec=current_time_sec,
                    aura_color=sec_aura_color,
                    num_particles=20,
                )
                composite = Image.alpha_composite(composite, sec_back_aura)

            # Primary character back aura
            aura_color = (217, 38, 38) if character.skin == CharacterSkin.DARK_WUKONG else (230, 184, 0)
            back_aura = self.particle_system.render_dark_aura(
                character_center=canvas_pos,
                facing=facing,
                scale=character.scale,
                current_time_sec=current_time_sec,
                aura_color=aura_color,
                num_particles=28,
            )
            composite = Image.alpha_composite(composite, back_aura)

        # LAYER 5: Character Stickman Composite
        # Secondary character (opponent) drawn behind primary
        if secondary_character is not None and secondary_pose_def is not None and secondary_canvas_pos is not None:
            sec_char_layer = composite_character(
                body_renderer=self.body_renderer,
                face_renderer=self.face_renderer,
                accessories_renderer=self.accessories_renderer,
                character=secondary_character,
                pose=secondary_pose_def.pose,
                canvas_position=secondary_canvas_pos,
                facing=secondary_facing,
                canvas_size=(w, h),
                weapon_renderer=self.weapon_renderer,
                pose_def=secondary_pose_def,
                custom_angle_deg=getattr(secondary_pose_def, "weapon_angle_deg", 0.0),
                buddha_palm_renderer=self.buddha_palm_renderer,
            )
            composite = Image.alpha_composite(composite, sec_char_layer)

        # Primary character composite
        char_layer = composite_character(
            body_renderer=self.body_renderer,
            face_renderer=self.face_renderer,
            accessories_renderer=self.accessories_renderer,
            character=character,
            pose=pose_def.pose,
            canvas_position=canvas_pos,
            facing=facing,
            canvas_size=(w, h),
            weapon_renderer=self.weapon_renderer,
            align_two_hands=align_two_hands,
            pose_def=pose_def,
            custom_angle_deg=pose_def.weapon_angle_deg,
            buddha_palm_renderer=self.buddha_palm_renderer,
        )
        composite = Image.alpha_composite(composite, char_layer)

        # LAYER 6: Weapon Motion Trail
        if self.config.enable_motion_trails:
            if secondary_character is not None and secondary_character.weapon != WeaponType.UNARMED and secondary_pose_def is not None and secondary_canvas_pos is not None:
                sec_tail_pt, sec_tip_pt, _, _ = self.weapon_renderer.get_weapon_endpoints(
                    character=secondary_character,
                    pose=secondary_pose_def.pose,
                    canvas_position=secondary_canvas_pos,
                    facing=secondary_facing,
                    pose_def=secondary_pose_def,
                )
                sec_trail_color = (230, 184, 0) if secondary_character.skin != CharacterSkin.DARK_WUKONG else (217, 38, 38)
                sec_trail_layer = self.motion_trail_renderer.render_trail(
                    current_tail=sec_tail_pt,
                    current_tip=sec_tip_pt,
                    frame_idx=frame_idx + 1000,
                    color=sec_trail_color,
                )
                composite = Image.alpha_composite(composite, sec_trail_layer)

            if character.weapon != WeaponType.UNARMED:
                tail_pt, tip_pt, _, _ = self.weapon_renderer.get_weapon_endpoints(
                    character=character,
                    pose=pose_def.pose,
                    canvas_position=canvas_pos,
                    facing=facing,
                    pose_def=pose_def,
                    align_two_hands=align_two_hands,
                )
                trail_color = (217, 38, 38) if character.skin == CharacterSkin.DARK_WUKONG else (230, 184, 0)
                trail_layer = self.motion_trail_renderer.render_trail(
                    current_tail=tail_pt,
                    current_tip=tip_pt,
                    frame_idx=frame_idx,
                    color=trail_color,
                )
                composite = Image.alpha_composite(composite, trail_layer)

        # SPECIAL LAYER: Celestial Buddha Palm Descent (when active)
        if buddha_palm_progress is not None:
            palm_y = -350.0 + buddha_palm_progress * 1150.0
            palm_layer = self.buddha_palm_renderer.render_palm(
                position=Point2D(540.0, palm_y),
                scale=2.4,
                facing=1,
                direction="down",
                descent_progress=buddha_palm_progress,
                canvas_size=(w, h),
            )
            composite = Image.alpha_composite(composite, palm_layer)

        # LAYER 7: Foreground Impact VFX (Clash Sparks, Shockwave Rings)
        for ev in all_events:
            u = ev.get_progress(current_time_sec)
            if u is not None and 0.0 <= u <= 1.0:
                if ev.event_type == VFXEventType.CLASH_SPARKS and self.config.enable_clash_sparks:
                    sparks_layer = self.particle_system.render_clash_sparks(ev, progress=u)
                    composite = Image.alpha_composite(composite, sparks_layer)
                elif ev.event_type == VFXEventType.SHOCKWAVE_RING:
                    shock_layer = self.particle_system.render_shockwave_ring(ev, progress=u)
                    composite = Image.alpha_composite(composite, shock_layer)

        return composite

    def generate_clip_frames_with_vfx(
        self,
        track: AnimationTrack,
        character: StickmanCharacter,
        fps: int = 30,
        background_image: Optional[Image.Image] = None,
        animation_engine: Optional[AnimationLoopEngine] = None,
        custom_vfx_events: Optional[list[VFXEvent]] = None,
        output_dir: Optional[Path] = None,
        frame_name_prefix: str = "vfx_frame",
        secondary_track: Optional[AnimationTrack] = None,
        secondary_character: Optional[StickmanCharacter] = None,
        buddha_palm_active: bool = False,
    ) -> list[Image.Image]:
        """
        Generate all frames for the given track including full VFX layers.
        Supports dual characters and dynamic Buddha Palm descent overlay.
        """
        anim = animation_engine or AnimationLoopEngine()
        total_frames = max(1, round(track.duration_sec * fps))
        frames: list[Image.Image] = []

        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)

        self.motion_trail_renderer.reset()

        for frame_idx in range(total_frames):
            time_sec = frame_idx / fps
            state = anim.get_state_at_time(
                track=track,
                time_sec=time_sec,
                scale=character.scale,
                ground_y=CoordinateManager.Y_GROUND,
            )

            sec_pose_def = None
            sec_canvas_pos = None
            sec_facing = -1
            if secondary_track is not None and secondary_character is not None:
                sec_state = anim.get_state_at_time(
                    track=secondary_track,
                    time_sec=time_sec,
                    scale=secondary_character.scale,
                    ground_y=CoordinateManager.Y_GROUND,
                )
                sec_pose_def = sec_state.pose_def
                sec_canvas_pos = sec_state.canvas_pos
                sec_facing = sec_state.facing

            palm_prog = None
            if buddha_palm_active:
                palm_prog = min(1.0, max(0.0, time_sec / max(1.0, track.duration_sec * 0.7)))

            frame_img = self.render_frame_with_vfx(
                character=character,
                pose_def=state.pose_def,
                canvas_pos=state.canvas_pos,
                facing=state.facing,
                current_time_sec=time_sec,
                frame_idx=frame_idx,
                background_image=background_image,
                custom_vfx_events=custom_vfx_events,
                secondary_character=secondary_character,
                secondary_pose_def=sec_pose_def,
                secondary_canvas_pos=sec_canvas_pos,
                secondary_facing=sec_facing,
                buddha_palm_progress=palm_prog,
            )

            if output_dir is not None:
                p = output_dir / f"{frame_name_prefix}_{frame_idx:04d}.png"
                frame_img.save(p, format="PNG")

            frames.append(frame_img)

        return frames
