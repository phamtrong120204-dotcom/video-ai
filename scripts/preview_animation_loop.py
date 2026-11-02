"""
Dark Myth Stickman Auto-Studio - Stage 6: Preview Animation Loop Script.

Generates high-resolution visual contact sheets and full-fidelity H.264 MP4 videos
for combat animation loops (Dark Wukong Combat Loop & Buddha Palm Suppression).
Exports all artifacts into out/preview/stickman/animation_loop/.
"""

import json
import math
from pathlib import Path
import subprocess
import sys
import time

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image, ImageDraw, ImageFont

from app.modules.animation.animation_loop import (
    AnimationLoopEngine,
    AnimationTrack,
    Keyframe,
)
from app.modules.animation.background_renderer import NotebookBackgroundRenderer
from app.modules.animation.interpolation_engine import EasingFunction
from app.modules.animation.pose_catalog import PoseCatalog
from app.modules.animation.stickman_models import (
    CoordinateManager,
    Point2D,
    StickmanCharacter,
)
from app.schemas.scene_schema import ActorConfig, ActorSide, CharacterSkin, WeaponType


def create_contact_sheet(
    frames: list[Image.Image],
    frame_indices: list[int],
    titles: list[str],
    cols: int = 4,
    thumb_width: int = 270,
    thumb_height: int = 480,
    title_height: int = 36,
) -> Image.Image:
    """Combine selected sample frames into a high-density contact sheet."""
    n = len(frame_indices)
    rows = math.ceil(n / cols)
    sheet_w = cols * thumb_width
    sheet_h = rows * (thumb_height + title_height)

    sheet = Image.new("RGBA", (sheet_w, sheet_h), (26, 32, 44, 255))
    draw = ImageDraw.Draw(sheet)

    for i, (idx, caption) in enumerate(zip(frame_indices, titles)):
        r = i // cols
        c = i % cols
        x = c * thumb_width
        y = r * (thumb_height + title_height)

        thumb = frames[idx].resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x, y + title_height))

        # Title bar
        draw.rectangle([x, y, x + thumb_width, y + title_height], fill=(45, 55, 72, 255))
        draw.text((x + 8, y + 8), caption, fill=(247, 250, 252, 255))
        # Border
        draw.rectangle([x, y, x + thumb_width - 1, y + thumb_height + title_height - 1], outline=(113, 128, 150, 255))

    return sheet


def main():
    print("=" * 70)
    print("STAGE 6: GENERATING ANIMATION LOOP PREVIEWS & VIDEOS")
    print("=" * 70)

    out_dir = Path("out/preview/stickman/animation_loop")
    out_dir.mkdir(parents=True, exist_ok=True)

    engine = AnimationLoopEngine()
    bg_renderer = NotebookBackgroundRenderer()
    bg_image = bg_renderer.render_background(state="clean", seed=108)

    # -------------------------------------------------------------------------
    # 1. SCENARIO 1: Dark Wukong Combat Moveset Loop (4.0s @ 30 FPS = 120 frames)
    # -------------------------------------------------------------------------
    print("\n[1/3] Generating Dark Wukong Combat Loop...")
    wukong_track = AnimationTrack(
        keyframes=[
            Keyframe(time_sec=0.0, pose_name="standoff_idle", easing=EasingFunction.EASE_IN_OUT, description="Planted Idle"),
            Keyframe(time_sec=0.7, pose_name="combat_stance", easing=EasingFunction.EASE_IN, description="Combat Stance"),
            Keyframe(time_sec=1.3, pose_name="forward_charge", easing=EasingFunction.EASE_OUT, description="Forward Charge"),
            Keyframe(time_sec=1.9, pose_name="overhead_slam", easing=EasingFunction.EASE_IN_OUT, description="Overhead Slam"),
            Keyframe(time_sec=2.5, pose_name="vortex_sweep", easing=EasingFunction.EASE_IN_OUT, description="Vortex Sweep"),
            Keyframe(time_sec=3.1, pose_name="guard_block", easing=EasingFunction.EASE_OUT, description="Guard Recoil"),
            Keyframe(time_sec=3.6, pose_name="knockback_slide", easing=EasingFunction.EASE_IN_OUT, description="Slide Recovery"),
            Keyframe(time_sec=4.0, pose_name="standoff_idle", easing=EasingFunction.EASE_IN_OUT, description="Return to Idle"),
        ],
        duration_sec=4.0,
        loop=True,
        name="wukong_combat_loop",
    )

    wukong_cfg = ActorConfig(
        actor_id="dark_wukong_hero",
        display_name="Dark Wukong",
        side=ActorSide.LEFT,
        skin=CharacterSkin.DARK_WUKONG,
        weapon=WeaponType.RUYI_STAFF,
        scale=1.0,
    )
    wukong_char = StickmanCharacter.from_actor_config(wukong_cfg)

    t0 = time.time()
    wukong_frames = engine.generate_clip_frames(
        track=wukong_track,
        character=wukong_char,
        fps=30,
        background_image=bg_image,
    )
    render_time_wukong = time.time() - t0
    print(f"  Rendered {len(wukong_frames)} frames in {render_time_wukong:.2f}s ({len(wukong_frames)/render_time_wukong:.1f} fps)")

    # Export Wukong MP4 Video
    wukong_video_path = out_dir / "wukong_combat_loop.mp4"
    engine.export_mp4_video(wukong_frames, wukong_video_path, fps=30)
    print(f"  Exported video: {wukong_video_path} ({wukong_video_path.stat().st_size / 1024:.1f} KB)")

    # Generate Wukong Contact Sheet
    wukong_sample_indices = [0, 21, 39, 57, 75, 93, 108, 119]
    wukong_sample_titles = [
        "0.00s: Standoff Idle",
        "0.70s: Combat Stance",
        "1.30s: Forward Charge",
        "1.90s: Overhead Slam",
        "2.50s: Vortex Sweep",
        "3.10s: Guard Block",
        "3.60s: Slide Recovery",
        "3.97s: Loop Return",
    ]
    wukong_contact_sheet = create_contact_sheet(
        frames=wukong_frames,
        frame_indices=wukong_sample_indices,
        titles=wukong_sample_titles,
        cols=4,
    )
    wukong_sheet_path = out_dir / "wukong_combat_loop_contact_sheet.png"
    wukong_contact_sheet.save(wukong_sheet_path, format="PNG")
    print(f"  Saved contact sheet: {wukong_sheet_path}")

    # -------------------------------------------------------------------------
    # 2. SCENARIO 2: Buddha Palm Celestial Suppression (2.0s @ 30 FPS = 60 frames)
    # -------------------------------------------------------------------------
    print("\n[2/3] Generating Buddha Palm Suppression Sequence...")
    buddha_track = AnimationTrack(
        keyframes=[
            Keyframe(time_sec=0.0, pose_name="standoff_idle", elevation=350.0, easing=EasingFunction.EASE_IN, description="Palm High Descent"),
            Keyframe(time_sec=0.8, pose_name="combat_stance", elevation=150.0, easing=EasingFunction.EASE_IN, description="Palm Mid Descent"),
            Keyframe(time_sec=1.4, pose_name="overhead_slam", elevation=0.0, easing=EasingFunction.EASE_OUT, description="Impact & Slam"),
            Keyframe(time_sec=2.0, pose_name="overhead_slam", elevation=0.0, easing=EasingFunction.LINEAR, description="Ground Crushing"),
        ],
        duration_sec=2.0,
        loop=False,
        name="buddha_palm_suppression",
    )

    buddha_cfg = ActorConfig(
        actor_id="buddha_palm_entity",
        display_name="Buddha Palm",
        side=ActorSide.TOP,
        skin=CharacterSkin.BUDDHA_PALM,
        weapon=WeaponType.GIANT_GOLDEN_PALM,
        scale=1.0,
    )
    buddha_char = StickmanCharacter.from_actor_config(buddha_cfg)

    t0 = time.time()
    buddha_frames = engine.generate_clip_frames(
        track=buddha_track,
        character=buddha_char,
        fps=30,
        background_image=bg_image,
    )
    render_time_buddha = time.time() - t0
    print(f"  Rendered {len(buddha_frames)} frames in {render_time_buddha:.2f}s")

    # Export Buddha Palm MP4 Video
    buddha_video_path = out_dir / "buddha_palm_suppression.mp4"
    engine.export_mp4_video(buddha_frames, buddha_video_path, fps=30)
    print(f"  Exported video: {buddha_video_path} ({buddha_video_path.stat().st_size / 1024:.1f} KB)")

    # Generate Buddha Contact Sheet
    buddha_sample_indices = [0, 15, 30, 42, 50, 59]
    buddha_sample_titles = [
        "0.00s: Descent Start",
        "0.50s: Golden Descent",
        "1.00s: Mandalas Flare",
        "1.40s: Ground Impact",
        "1.67s: Seal Suppression",
        "2.00s: Crushed Ground",
    ]
    buddha_contact_sheet = create_contact_sheet(
        frames=buddha_frames,
        frame_indices=buddha_sample_indices,
        titles=buddha_sample_titles,
        cols=3,
    )
    buddha_sheet_path = out_dir / "buddha_palm_suppression_contact_sheet.png"
    buddha_contact_sheet.save(buddha_sheet_path, format="PNG")
    print(f"  Saved contact sheet: {buddha_sheet_path}")

    # -------------------------------------------------------------------------
    # 3. VERIFY VIDEOS WITH FFPROBE & WRITE MANIFEST
    # -------------------------------------------------------------------------
    print("\n[3/3] Inspecting video files with ffprobe...")
    manifest = {
        "stage": "G6 - Interpolation & Animation Loop Engine",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "resolution": "1080x1920 (9:16 vertical)",
        "videos": {},
    }

    for name, vpath in [("wukong_combat_loop", wukong_video_path), ("buddha_palm_suppression", buddha_video_path)]:
        probe_cmd = [
            r"C:\ffmpeg\bin\ffprobe.exe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,codec_name,pix_fmt,r_frame_rate,duration,nb_frames",
            "-of", "json",
            str(vpath),
        ]
        res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        probe_data = json.loads(res.stdout)["streams"][0]
        manifest["videos"][name] = {
            "path": str(vpath),
            "size_bytes": vpath.stat().st_size,
            "width": probe_data.get("width"),
            "height": probe_data.get("height"),
            "codec": probe_data.get("codec_name"),
            "pix_fmt": probe_data.get("pix_fmt"),
            "framerate": probe_data.get("r_frame_rate"),
            "nb_frames": probe_data.get("nb_frames"),
        }
        print(f"  {name}: {probe_data.get('width')}x{probe_data.get('height')}, {probe_data.get('codec_name')}, {probe_data.get('r_frame_rate')} fps, {probe_data.get('pix_fmt')}")

    manifest_path = out_dir / "animation_loop_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nManifest saved to: {manifest_path}")
    print("\nALL PREVIEW ASSETS SUCCESSFULLY GENERATED AND VERIFIED!")


if __name__ == "__main__":
    main()
