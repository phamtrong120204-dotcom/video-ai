"""
Dark Myth Stickman Auto-Studio - Stage 6: Animation Loop Engine.

Orchestrates multi-keyframe animation tracks, seamless looping, timeline sequencing,
frame rendering using G5 compositing pipeline, and MP4 video export via FFmpeg.
"""

from dataclasses import dataclass
import math
from pathlib import Path
import subprocess
from typing import Optional, Union

from PIL import Image

from app.modules.animation.buddha_palm_renderer import BuddhaPalmRenderer
from app.modules.animation.character_renderer_parts import (
    AccessoriesRenderer,
    FaceFeatureRenderer,
    HumanoidBodyRenderer,
    WeaponRenderer,
    composite_character,
)
from app.modules.animation.interpolation_engine import (
    EasingFunction,
    evaluate_easing,
    interpolate_poses,
)
from app.modules.animation.pose_catalog import PoseCatalog, PoseDefinition
from app.modules.animation.stickman_models import (
    CoordinateManager,
    Point2D,
    StickmanCharacter,
    SupportMode,
)


@dataclass(frozen=True)
class Keyframe:
    """
    Keyframe definition along an animation timeline.

    Attributes:
      time_sec: Timestamp in seconds (must be >= 0.0).
      pose_name: Named pose from PoseCatalog (e.g. "standoff_idle", "combat_stance").
      custom_pose_def: Optional explicit PoseDefinition (overrides pose_name).
      canvas_pos: Optional explicit root (pelvis) position in Canvas Space.
                  If None or Y is omitted, Y is ground-aligned automatically.
      facing: Direction character faces (+1 right, -1 left).
      elevation: Optional elevation in px above ground (overrides pose elevation).
      easing: Easing function transitioning into the NEXT keyframe.
      description: Descriptive note for this keyframe.
    """

    time_sec: float
    pose_name: Optional[str] = None
    custom_pose_def: Optional[PoseDefinition] = None
    canvas_pos: Optional[Point2D] = None
    facing: int = 1
    elevation: Optional[float] = None
    easing: EasingFunction = EasingFunction.EASE_IN_OUT
    description: str = ""

    def __post_init__(self) -> None:
        if self.time_sec < 0.0 or not math.isfinite(self.time_sec):
            raise ValueError(f"Keyframe time_sec must be non-negative and finite, got {self.time_sec}")
        if self.facing not in (+1, -1):
            raise ValueError(f"Keyframe facing must be +1 or -1, got {self.facing}")
        if self.pose_name is None and self.custom_pose_def is None:
            raise ValueError("Keyframe must define either 'pose_name' or 'custom_pose_def'")

    def get_pose_definition(self) -> PoseDefinition:
        """Resolve the effective PoseDefinition for this keyframe."""
        if self.custom_pose_def is not None:
            base_def = self.custom_pose_def
        else:
            assert self.pose_name is not None
            base_def = PoseCatalog.get_definition(self.pose_name)

        if self.elevation is not None and self.elevation != base_def.elevation:
            eff_supp = SupportMode.AIRBORNE if self.elevation > 0.5 else base_def.support_mode
            return PoseDefinition(
                name=base_def.name,
                pose=base_def.pose,
                support_mode=eff_supp,
                elevation=float(self.elevation),
                weapon_anchor=base_def.weapon_anchor,
                weapon_angle_deg=base_def.weapon_angle_deg,
                secondary_grip=base_def.secondary_grip,
                description=base_def.description,
            )
        return base_def


@dataclass
class AnimationTrack:
    """
    An animation track containing a sequence of keyframes.
    """

    keyframes: list[Keyframe]
    duration_sec: float = 0.0
    loop: bool = True
    name: str = "dark_myth_track"

    def __post_init__(self) -> None:
        if not self.keyframes:
            raise ValueError("AnimationTrack must contain at least one Keyframe")
        # Ensure chronological ordering
        self.keyframes = sorted(self.keyframes, key=lambda kf: kf.time_sec)
        if self.duration_sec <= 0.0:
            if len(self.keyframes) > 1:
                self.duration_sec = self.keyframes[-1].time_sec
            else:
                self.duration_sec = 1.0


@dataclass(frozen=True)
class AnimationState:
    """The evaluated character state at a specific point in time."""

    time_sec: float
    pose_def: PoseDefinition
    canvas_pos: Point2D
    facing: int


class AnimationLoopEngine:
    """
    Animation loop and timeline orchestrator.
    """

    def __init__(
        self,
        body_renderer: Optional[HumanoidBodyRenderer] = None,
        face_renderer: Optional[FaceFeatureRenderer] = None,
        accessories_renderer: Optional[AccessoriesRenderer] = None,
        weapon_renderer: Optional[WeaponRenderer] = None,
        buddha_palm_renderer: Optional[BuddhaPalmRenderer] = None,
    ) -> None:
        self.body_renderer = body_renderer or HumanoidBodyRenderer()
        self.face_renderer = face_renderer or FaceFeatureRenderer()
        self.accessories_renderer = accessories_renderer or AccessoriesRenderer()
        self.buddha_palm_renderer = buddha_palm_renderer or BuddhaPalmRenderer()
        self.weapon_renderer = weapon_renderer or WeaponRenderer(
            body_renderer=self.body_renderer,
            buddha_palm_renderer=self.buddha_palm_renderer,
        )

    def get_state_at_time(
        self,
        track: AnimationTrack,
        time_sec: float,
        scale: float = 1.0,
        ground_y: float = CoordinateManager.Y_GROUND,
        default_x: float = 540.0,
    ) -> AnimationState:
        """
        Sample the animation track at time_sec, resolving keyframe interpolation,
        seamless looping, and ground contact coordinates.
        """
        if not math.isfinite(time_sec):
            raise ValueError(f"time_sec must be finite, got {time_sec}")

        # 1. Timeline wrapping
        if track.loop and track.duration_sec > 0.0:
            cur_t = time_sec % track.duration_sec
        else:
            cur_t = max(0.0, min(time_sec, track.duration_sec))

        kfs = track.keyframes
        n = len(kfs)

        if n == 1:
            kf = kfs[0]
            pdef = kf.get_pose_definition()
            pos_x = kf.canvas_pos.x if kf.canvas_pos else default_x
            if kf.canvas_pos and math.isfinite(kf.canvas_pos.y):
                pos_y = kf.canvas_pos.y
            else:
                pos_y = CoordinateManager.get_ground_aligned_root_y(
                    pdef.pose,
                    support_mode=pdef.support_mode,
                    ground_y=ground_y,
                    scale=scale,
                    elevation=pdef.elevation,
                )
            return AnimationState(time_sec=time_sec, pose_def=pdef, canvas_pos=Point2D(pos_x, pos_y), facing=kf.facing)

        # 2. Keyframe segment location
        kf_prev: Keyframe
        kf_next: Keyframe
        segment_prog: float
        easing_func: EasingFunction

        if cur_t <= kfs[0].time_sec:
            if track.loop and kfs[0].time_sec > 0.0:
                kf_prev = kfs[-1]
                kf_next = kfs[0]
                wrap_dur = (track.duration_sec - kf_prev.time_sec) + kf_next.time_sec
                dt = (track.duration_sec - kf_prev.time_sec) + cur_t
                segment_prog = dt / wrap_dur if wrap_dur > 1e-6 else 0.0
                easing_func = kf_prev.easing
            else:
                kf_prev = kfs[0]
                kf_next = kfs[0]
                segment_prog = 0.0
                easing_func = kfs[0].easing
        elif cur_t >= kfs[-1].time_sec:
            if track.loop and track.duration_sec > kfs[-1].time_sec:
                kf_prev = kfs[-1]
                kf_next = kfs[0]
                wrap_dur = track.duration_sec - kf_prev.time_sec + kf_next.time_sec
                dt = cur_t - kf_prev.time_sec
                segment_prog = dt / wrap_dur if wrap_dur > 1e-6 else 0.0
                easing_func = kf_prev.easing
            else:
                kf_prev = kfs[-1]
                kf_next = kfs[-1]
                segment_prog = 0.0
                easing_func = kfs[-1].easing
        else:
            # cur_t is inside [kfs[0].time_sec, kfs[-1].time_sec]
            kf_prev = kfs[0]
            kf_next = kfs[-1]
            for i in range(n - 1):
                if kfs[i].time_sec <= cur_t <= kfs[i + 1].time_sec:
                    kf_prev = kfs[i]
                    kf_next = kfs[i + 1]
                    break
            dur = kf_next.time_sec - kf_prev.time_sec
            segment_prog = (cur_t - kf_prev.time_sec) / dur if dur > 1e-6 else 0.0
            easing_func = kf_prev.easing

        # 3. Pose interpolation
        if kf_prev is kf_next or segment_prog <= 0.0:
            interp_pdef = kf_prev.get_pose_definition()
            eased_t = 0.0
        elif segment_prog >= 1.0:
            interp_pdef = kf_next.get_pose_definition()
            eased_t = 1.0
        else:
            interp_pdef = interpolate_poses(
                kf_prev.get_pose_definition(),
                kf_next.get_pose_definition(),
                t=segment_prog,
                easing=easing_func,
            )
            eased_t = evaluate_easing(easing_func, segment_prog)

        # 4. Canvas Position interpolation
        # X coordinate
        prev_x = kf_prev.canvas_pos.x if kf_prev.canvas_pos else default_x
        next_x = kf_next.canvas_pos.x if kf_next.canvas_pos else default_x
        pos_x = (1.0 - eased_t) * prev_x + eased_t * next_x

        # Y coordinate: check if both keyframes have explicit Y
        if kf_prev.canvas_pos and kf_next.canvas_pos:
            pos_y = (1.0 - eased_t) * kf_prev.canvas_pos.y + eased_t * kf_next.canvas_pos.y
        else:
            pos_y = CoordinateManager.get_ground_aligned_root_y(
                interp_pdef.pose,
                support_mode=interp_pdef.support_mode,
                ground_y=ground_y,
                scale=scale,
                elevation=interp_pdef.elevation,
            )

        # 5. Facing resolution
        if kf_prev.facing == kf_next.facing:
            facing = kf_prev.facing
        else:
            facing = kf_prev.facing if eased_t < 0.5 else kf_next.facing

        return AnimationState(
            time_sec=time_sec,
            pose_def=interp_pdef,
            canvas_pos=Point2D(pos_x, pos_y),
            facing=facing,
        )

    def render_frame(
        self,
        character: StickmanCharacter,
        state: AnimationState,
        background_image: Optional[Image.Image] = None,
        canvas_size: tuple[int, int] = (1080, 1920),
        align_two_hands: Optional[bool] = None,
        palm_direction: str = "down",
        palm_descent_progress: float = 1.0,
        palm_layer_order: str = "foreground",
    ) -> Image.Image:
        """
        Render a single animated frame for the character at the specified AnimationState.
        """
        char_layer = composite_character(
            body_renderer=self.body_renderer,
            face_renderer=self.face_renderer,
            accessories_renderer=self.accessories_renderer,
            character=character,
            pose=state.pose_def.pose,
            canvas_position=state.canvas_pos,
            facing=state.facing,
            canvas_size=canvas_size,
            weapon_renderer=self.weapon_renderer,
            align_two_hands=align_two_hands,
            pose_def=state.pose_def,
            custom_angle_deg=state.pose_def.weapon_angle_deg,
            buddha_palm_renderer=self.buddha_palm_renderer,
            palm_direction=palm_direction,
            palm_descent_progress=palm_descent_progress,
            palm_layer_order=palm_layer_order,
        )

        if background_image is not None:
            # Background compositing
            if background_image.size != canvas_size:
                bg = background_image.resize(canvas_size, Image.Resampling.LANCZOS).convert("RGBA")
            else:
                bg = background_image.convert("RGBA")
            return Image.alpha_composite(bg, char_layer)

        return char_layer

    def generate_clip_frames(
        self,
        track: AnimationTrack,
        character: StickmanCharacter,
        fps: int = 30,
        background_image: Optional[Image.Image] = None,
        canvas_size: tuple[int, int] = (1080, 1920),
        output_dir: Optional[Path] = None,
        frame_name_prefix: str = "frame",
        align_two_hands: Optional[bool] = None,
    ) -> list[Image.Image]:
        """
        Generate all frames for the given track at the specified frame rate.

        If output_dir is provided, saves each frame as PNG to disk to prevent RAM bloat.
        """
        if fps <= 0:
            raise ValueError(f"fps must be positive, got {fps}")

        total_frames = max(1, round(track.duration_sec * fps))
        frames: list[Image.Image] = []

        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)

        for frame_idx in range(total_frames):
            time_sec = frame_idx / fps
            state = self.get_state_at_time(
                track=track,
                time_sec=time_sec,
                scale=character.scale,
                ground_y=CoordinateManager.Y_GROUND,
            )
            frame_img = self.render_frame(
                character=character,
                state=state,
                background_image=background_image,
                canvas_size=canvas_size,
                align_two_hands=align_two_hands,
            )

            if output_dir is not None:
                frame_path = output_dir / f"{frame_name_prefix}_{frame_idx:04d}.png"
                frame_img.save(frame_path, format="PNG")

            frames.append(frame_img)

        return frames

    @staticmethod
    def export_mp4_video(
        frames_or_dir: Union[list[Image.Image], Path],
        output_mp4_path: Path,
        fps: int = 30,
        ffmpeg_path: str = r"C:\ffmpeg\bin\ffmpeg.exe",
    ) -> Path:
        """
        Export animation frames to an H.264 MP4 video file using FFmpeg.

        Parameters:
          frames_or_dir: Either a list of PIL Images, or a Path to a directory
                         containing 'frame_%04d.png' files.
          output_mp4_path: Destination .mp4 file path.
          fps: Target framerate (default 30).
          ffmpeg_path: Absolute path to FFmpeg binary.

        Returns:
          Path to created video file.
        """
        output_mp4_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(frames_or_dir, Path) and frames_or_dir.is_dir():
            input_pattern = str(frames_or_dir / "frame_%04d.png")
            cmd = [
                ffmpeg_path,
                "-y",
                "-framerate", str(fps),
                "-i", input_pattern,
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                str(output_mp4_path),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if res.returncode != 0:
                raise RuntimeError(f"FFmpeg error ({res.returncode}): {res.stderr}")
            return output_mp4_path

        elif isinstance(frames_or_dir, list):
            # Stream frames via pipe to avoid disk roundtrip
            cmd = [
                ffmpeg_path,
                "-y",
                "-f", "image2pipe",
                "-vcodec", "png",
                "-framerate", str(fps),
                "-i", "-",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                str(output_mp4_path),
            ]
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for img in frames_or_dir:
                img.save(process.stdin, format="PNG")
            _, stderr = process.communicate()
            if process.returncode != 0:
                raise RuntimeError(f"FFmpeg error ({process.returncode}): {stderr.decode('utf-8', errors='replace')}")
            return output_mp4_path

        raise ValueError(f"Invalid frames_or_dir: {frames_or_dir}")
