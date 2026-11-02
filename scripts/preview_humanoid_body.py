"""Dark Myth Stickman Humanoid Body Preview Generator (G5.2.3.1).

Renders transparent RGBA stickman body previews for:
1. wukong_standoff.png (STANDOFF_IDLE, facing right)
2. wukong_combat_stance.png (COMBAT_STANCE, facing right)
3. erlang_standoff.png (STANDOFF_IDLE, facing left)
4. wukong_mid_air_leap.png (MID_AIR_LEAP, airborne elevation 400px)

Outputs to out/preview/stickman/body/.
"""

import json
import math
import os
from pathlib import Path
import sys
import time

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import numpy as np
from PIL import Image, ImageDraw

from app.modules.animation.character_renderer_parts import HumanoidBodyRenderer
from app.modules.animation.pose_catalog import PoseCatalog
from app.modules.animation.stickman_models import (
    CoordinateManager,
    Point2D,
    StickmanCharacter,
    SupportMode,
)
from app.schemas.scene_schema import ActorConfig, ActorSide, CharacterSkin, WeaponType


def create_preview_collage(
    items: list[tuple[str, Image.Image]],
    thumb_w: int = 360,
    thumb_h: int = 640,
) -> Image.Image:
    """Create a 2x2 comparison grid with subtle notebook grid background."""
    cols = 2
    rows = (len(items) + cols - 1) // cols
    margin = 30
    header_h = 50
    total_w = cols * thumb_w + (cols + 1) * margin
    total_h = rows * (thumb_h + header_h) + (rows + 1) * margin

    collage = Image.new("RGBA", (total_w, total_h), (24, 25, 30, 255))
    draw = ImageDraw.Draw(collage)

    # Subtle paper grid on collage background
    for gx in range(0, total_w, 20):
        draw.line([(gx, 0), (gx, total_h)], fill=(32, 34, 40, 255), width=1)
    for gy in range(0, total_h, 20):
        draw.line([(0, gy), (total_w, gy)], fill=(32, 34, 40, 255), width=1)

    for idx, (label, img) in enumerate(items):
        r = idx // cols
        c = idx % cols
        x = margin + c * (thumb_w + margin)
        y = margin + r * (thumb_h + header_h + margin)

        # Header title
        draw.text((x + 8, y + 14), label.upper(), fill=(230, 230, 240, 255))

        # Create paper preview card
        card = Image.new("RGBA", (thumb_w, thumb_h), (242, 237, 225, 255))
        card_draw = ImageDraw.Draw(card)

        # Draw ground line reference on card (y = 1420 scaled down: 1420 * 640 / 1920 = 473.3)
        ground_thumb_y = round(1420.0 * thumb_h / 1920.0)
        card_draw.line(
            [(0, ground_thumb_y), (thumb_w, ground_thumb_y)],
            fill=(180, 170, 160, 255),
            width=2,
        )

        # Resize character layer and alpha-composite onto paper card
        resized_char = img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        card = Image.alpha_composite(card, resized_char)

        collage.paste(card, (x, y + header_h))

        # Border around card
        draw.rectangle(
            [(x, y + header_h), (x + thumb_w - 1, y + header_h + thumb_h - 1)],
            outline=(80, 85, 100, 255),
            width=2,
        )

    return collage


def main() -> None:
    print("=" * 80)
    print(" DARK MYTH STICKMAN - HUMANOID BODY PREVIEW GENERATOR (G5.2.3.1)")
    print("=" * 80)

    out_dir = WORKSPACE_ROOT / "out" / "preview" / "stickman" / "body"
    out_dir.mkdir(parents=True, exist_ok=True)

    renderer = HumanoidBodyRenderer()

    # Define Characters
    wukong_config = ActorConfig(
        actor_id="wukong",
        skin=CharacterSkin.DARK_WUKONG,
        color="#DAA520",
        weapon=WeaponType.RUYI_STAFF,
        display_name="Tôn Ngộ Không",
        side=ActorSide.LEFT,
        scale=1.0,
    )
    wukong = StickmanCharacter.from_actor_config(wukong_config)

    erlang_config = ActorConfig(
        actor_id="erlang_shen",
        skin=CharacterSkin.ERLANG_SHEN,
        color="#00F0FF",
        weapon=WeaponType.THREE_POINTED_SPEAR,
        display_name="Dương Tiễn",
        side=ActorSide.RIGHT,
        scale=1.05,
    )
    erlang = StickmanCharacter.from_actor_config(erlang_config)

    # 4 Preview Configurations
    preview_configs = [
        {
            "filename": "wukong_standoff.png",
            "label": "Wukong Standoff Idle",
            "character": wukong,
            "pose_name": "standoff_idle",
            "support_mode": SupportMode.DOUBLE,
            "elevation": None,
            "pelvis_x": 400.0,
            "facing": 1,
        },
        {
            "filename": "wukong_combat_stance.png",
            "label": "Wukong Combat Stance",
            "character": wukong,
            "pose_name": "combat_stance",
            "support_mode": SupportMode.DOUBLE,
            "elevation": None,
            "pelvis_x": 420.0,
            "facing": 1,
        },
        {
            "filename": "erlang_standoff.png",
            "label": "Erlang Shen Standoff",
            "character": erlang,
            "pose_name": "standoff_idle",
            "support_mode": SupportMode.DOUBLE,
            "elevation": None,
            "pelvis_x": 680.0,
            "facing": -1,
        },
        {
            "filename": "wukong_mid_air_leap.png",
            "label": "Wukong Mid-Air Leap",
            "character": wukong,
            "pose_name": "mid_air_leap",
            "support_mode": SupportMode.AIRBORNE,
            "elevation": 400.0,
            "pelvis_x": 540.0,
            "facing": 1,
        },
    ]

    rendered_items: list[tuple[str, Image.Image]] = []
    metadata: list[dict] = []

    for cfg in preview_configs:
        start_t = time.perf_counter()
        pose = PoseCatalog.get_pose(cfg["pose_name"])

        # Determine pelvis Y using ground contact rules
        if cfg["support_mode"] == SupportMode.AIRBORNE:
            pelvis_y = CoordinateManager.get_ground_aligned_root_y(
                pose=pose,
                support_mode=SupportMode.AIRBORNE,
                ground_y=1420.0,
                scale=cfg["character"].scale,
                elevation=cfg["elevation"],
            )
        else:
            pelvis_y = CoordinateManager.get_ground_aligned_root_y(
                pose=pose,
                support_mode=cfg["support_mode"],
                ground_y=1420.0,
                scale=cfg["character"].scale,
            )

        pelvis_pos = Point2D(cfg["pelvis_x"], pelvis_y)

        # Render humanoid body
        img = renderer.render_body(
            character=cfg["character"],
            pose=pose,
            canvas_position=pelvis_pos,
            facing=cfg["facing"],
            canvas_size=(1080, 1920),
        )

        elapsed_ms = (time.perf_counter() - start_t) * 1000.0

        # Save transparent RGBA PNG
        out_path = out_dir / cfg["filename"]
        img.save(out_path, format="PNG", optimize=True)

        joint_bbox = renderer.get_joint_bounding_box(
            pose=pose,
            canvas_position=pelvis_pos,
            facing=cfg["facing"],
            scale=cfg["character"].scale,
            canvas_size=(1080, 1920),
        )
        prim_bbox = renderer.get_bounding_box(
            character=cfg["character"],
            pose=pose,
            canvas_position=pelvis_pos,
            facing=cfg["facing"],
            canvas_size=(1080, 1920),
        )
        pixel_bbox = img.getbbox()

        file_size_kb = out_path.stat().st_size / 1024.0
        arr = np.array(img)
        non_zero_px = int(np.count_nonzero(arr[:, :, 3] > 0))

        # Actual pixel contact Y
        ys, _ = np.nonzero(arr[:, :, 3] > 0)
        actual_min_y = int(np.min(ys))
        actual_max_y = int(np.max(ys))

        print(
            f" [OK] {cfg['filename']:<28} | Size: {file_size_kb:6.1f} KB | "
            f"Non-zero px: {non_zero_px:5d} | Prim BBox: {prim_bbox} | Pixel BBox: {pixel_bbox} | Time: {elapsed_ms:5.1f}ms"
        )

        rendered_items.append((cfg["label"], img))
        metadata.append(
            {
                "file": cfg["filename"],
                "character": cfg["character"].actor_id,
                "pose": cfg["pose_name"],
                "support_mode": cfg["support_mode"].value,
                "pelvis_canvas": {"x": pelvis_pos.x, "y": pelvis_pos.y},
                "facing": cfg["facing"],
                "scale": cfg["character"].scale,
                "geometric_joint_bbox": list(joint_bbox),
                "primitive_bbox": list(prim_bbox),
                "pixel_alpha_bbox": list(pixel_bbox) if pixel_bbox else None,
                "actual_pixel_y_range": [actual_min_y, actual_max_y],
                "non_zero_pixels": non_zero_px,
                "file_size_bytes": out_path.stat().st_size,
            }
        )

    # Generate 2x2 side-by-side comparison collage
    collage = create_preview_collage(rendered_items)
    collage_path = out_dir / "collage_humanoid_body_grid.png"
    collage.save(collage_path, format="PNG", optimize=True)
    print(f" [OK] collage_humanoid_body_grid.png | Size: {collage_path.stat().st_size / 1024.0:6.1f} KB")

    # Save metadata manifest
    manifest_path = out_dir / "preview_manifest.json"
    manifest_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f" [OK] preview_manifest.json          | Saved {len(metadata)} preview metadata records")

    print("=" * 80)
    print(" All humanoid body previews successfully generated at:")
    print(f" {out_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
