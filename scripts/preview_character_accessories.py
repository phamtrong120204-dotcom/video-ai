"""Dark Myth Stickman - Face & Accessories Preview Generator (G5.2.3.2).

Generates 6 character appearance previews:
1. Wukong Standoff - Facing Right
2. Wukong Standoff - Facing Left
3. Erlang Shen Standoff - Facing Right
4. Erlang Shen Guard Block - Facing Left
5. Celestial General - Facing Right
6. Celestial Soldier - Facing Left

Composites 4 layers:
  1. Back accessories (Scarf, Pheasant feathers, Cloaks)
  2. Humanoid body skeleton (Bones, Joint caps, Solid head)
  3. Facial features (Fiery red eyes, Divine Third Eye, Visor slits)
  4. Front accessories (Kim Cô, Spiked helmet, Pauldrons, Tassels)

Outputs to out/preview/stickman/accessories/.
"""

import json
from pathlib import Path
import sys
import time

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import numpy as np
from PIL import Image, ImageDraw

from app.modules.animation.character_renderer_parts import (
    AccessoriesRenderer,
    FaceFeatureRenderer,
    HumanoidBodyRenderer,
    composite_character,
)
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
    """Create a 2-row x 3-col comparison grid with subtle notebook grid background."""
    cols = 3
    rows = (len(items) + cols - 1) // cols
    margin = 25
    header_h = 45
    total_w = cols * thumb_w + (cols + 1) * margin
    total_h = rows * (thumb_h + header_h) + (rows + 1) * margin

    collage = Image.new("RGBA", (total_w, total_h), (22, 24, 28, 255))
    draw = ImageDraw.Draw(collage)

    # Subtle paper grid on collage background
    for gx in range(0, total_w, 20):
        draw.line([(gx, 0), (gx, total_h)], fill=(30, 32, 38, 255), width=1)
    for gy in range(0, total_h, 20):
        draw.line([(0, gy), (total_w, gy)], fill=(30, 32, 38, 255), width=1)

    for idx, (label, img) in enumerate(items):
        r = idx // cols
        c = idx % cols
        x = margin + c * (thumb_w + margin)
        y = margin + r * (thumb_h + header_h + margin)

        # Header title
        draw.text((x + 8, y + 12), label.upper(), fill=(235, 235, 245, 255))

        # Create paper preview card (vintage notebook paper color)
        card = Image.new("RGBA", (thumb_w, thumb_h), (243, 238, 227, 255))
        card_draw = ImageDraw.Draw(card)

        # Draw notebook horizontal lines
        step_y = round(32.0 * thumb_h / 1920.0)
        for ly in range(0, thumb_h, max(10, step_y * 2)):
            card_draw.line([(0, ly), (thumb_w, ly)], fill=(225, 220, 210, 255), width=1)

        # Draw ground line reference on card (y = 1420 scaled down: 1420 * 640 / 1920 = 473.3)
        ground_thumb_y = round(1420.0 * thumb_h / 1920.0)
        card_draw.line(
            [(0, ground_thumb_y), (thumb_w, ground_thumb_y)],
            fill=(180, 165, 150, 255),
            width=2,
        )

        # Resize character layer and alpha-composite onto paper card
        resized_char = img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        card = Image.alpha_composite(card, resized_char)

        collage.paste(card, (x, y + header_h))

        # Border around card
        draw.rectangle(
            [(x, y + header_h), (x + thumb_w - 1, y + header_h + thumb_h - 1)],
            outline=(75, 80, 95, 255),
            width=2,
        )

    return collage


def main() -> None:
    print("=" * 80)
    print(" DARK MYTH STICKMAN - FACE & ACCESSORIES PREVIEW GENERATOR (G5.2.3.2)")
    print("=" * 80)

    out_dir = WORKSPACE_ROOT / "out" / "preview" / "stickman" / "accessories"
    out_dir.mkdir(parents=True, exist_ok=True)

    body_renderer = HumanoidBodyRenderer()
    face_renderer = FaceFeatureRenderer()
    acc_renderer = AccessoriesRenderer()

    # Define the 4 character configurations
    wukong_cfg = ActorConfig(
        actor_id="dark_wukong",
        skin=CharacterSkin.DARK_WUKONG,
        color="#D92626",
        weapon=WeaponType.RUYI_STAFF,
        display_name="Ngộ Không Hắc Hóa",
        side=ActorSide.LEFT,
        scale=1.0,
    )
    wukong = StickmanCharacter.from_actor_config(wukong_cfg)

    erlang_cfg = ActorConfig(
        actor_id="erlang_shen",
        skin=CharacterSkin.ERLANG_SHEN,
        color="#E6B800",
        weapon=WeaponType.THREE_POINTED_SPEAR,
        display_name="Nhị Lang Thần (Dương Tiễn)",
        side=ActorSide.RIGHT,
        scale=1.05,
    )
    erlang = StickmanCharacter.from_actor_config(erlang_cfg)

    general_cfg = ActorConfig(
        actor_id="celestial_general",
        skin=CharacterSkin.CELESTIAL_GENERAL,
        color="#63B3ED",
        weapon=WeaponType.CELESTIAL_HALBERD,
        display_name="Thiên Tướng",
        side=ActorSide.RIGHT,
        scale=1.25,
    )
    general = StickmanCharacter.from_actor_config(general_cfg)

    soldier_cfg = ActorConfig(
        actor_id="celestial_soldier",
        skin=CharacterSkin.CELESTIAL_SOLDIER_SQUAD,
        color="#63B3ED",
        weapon=WeaponType.CELESTIAL_HALBERD,
        display_name="Thiên Binh",
        side=ActorSide.LEFT,
        scale=0.95,
    )
    soldier = StickmanCharacter.from_actor_config(soldier_cfg)

    # 6 Target Previews
    preview_configs = [
        {
            "filename": "wukong_standoff_right.png",
            "label": "Wukong Standoff - Facing Right",
            "character": wukong,
            "pose_name": "standoff_idle",
            "support_mode": SupportMode.DOUBLE,
            "pelvis_x": 420.0,
            "facing": 1,
        },
        {
            "filename": "wukong_standoff_left.png",
            "label": "Wukong Standoff - Facing Left",
            "character": wukong,
            "pose_name": "standoff_idle",
            "support_mode": SupportMode.DOUBLE,
            "pelvis_x": 660.0,
            "facing": -1,
        },
        {
            "filename": "erlang_standoff_right.png",
            "label": "Erlang Standoff - Facing Right",
            "character": erlang,
            "pose_name": "standoff_idle",
            "support_mode": SupportMode.DOUBLE,
            "pelvis_x": 420.0,
            "facing": 1,
        },
        {
            "filename": "erlang_guard_block_left.png",
            "label": "Erlang Guard Block - Facing Left",
            "character": erlang,
            "pose_name": "guard_block",
            "support_mode": SupportMode.DOUBLE,
            "pelvis_x": 660.0,
            "facing": -1,
        },
        {
            "filename": "celestial_general_right.png",
            "label": "Celestial General - Facing Right",
            "character": general,
            "pose_name": "standoff_idle",
            "support_mode": SupportMode.DOUBLE,
            "pelvis_x": 480.0,
            "facing": 1,
        },
        {
            "filename": "celestial_soldier_left.png",
            "label": "Celestial Soldier - Facing Left",
            "character": soldier,
            "pose_name": "standoff_idle",
            "support_mode": SupportMode.DOUBLE,
            "pelvis_x": 600.0,
            "facing": -1,
        },
    ]

    rendered_items: list[tuple[str, Image.Image]] = []
    metadata: list[dict] = []

    for cfg in preview_configs:
        start_t = time.perf_counter()
        pose = PoseCatalog.get_pose(cfg["pose_name"])

        pelvis_y = CoordinateManager.get_ground_aligned_root_y(
            pose=pose,
            support_mode=cfg["support_mode"],
            ground_y=1420.0,
            scale=cfg["character"].scale,
        )
        pelvis_pos = Point2D(cfg["pelvis_x"], pelvis_y)

        # 4-Step Composite
        img = composite_character(
            body_renderer=body_renderer,
            face_renderer=face_renderer,
            accessories_renderer=acc_renderer,
            character=cfg["character"],
            pose=pose,
            canvas_position=pelvis_pos,
            facing=cfg["facing"],
            canvas_size=(1080, 1920),
        )

        elapsed_ms = (time.perf_counter() - start_t) * 1000.0

        out_path = out_dir / cfg["filename"]
        img.save(out_path, format="PNG", optimize=True)

        file_size_kb = out_path.stat().st_size / 1024.0
        arr = np.array(img)
        non_zero_px = int(np.count_nonzero(arr[:, :, 3] > 0))
        bbox = img.getbbox()

        print(
            f" [OK] {cfg['filename']:<30} | Size: {file_size_kb:6.1f} KB | "
            f"Non-zero px: {non_zero_px:5d} | BBox: {bbox} | Time: {elapsed_ms:5.1f}ms"
        )

        rendered_items.append((cfg["label"], img))
        metadata.append(
            {
                "file": cfg["filename"],
                "character": cfg["character"].actor_id,
                "skin": cfg["character"].skin.value,
                "pose": cfg["pose_name"],
                "pelvis_canvas": {"x": pelvis_pos.x, "y": pelvis_pos.y},
                "facing": cfg["facing"],
                "scale": cfg["character"].scale,
                "pixel_alpha_bbox": list(bbox) if bbox else None,
                "non_zero_pixels": non_zero_px,
                "file_size_bytes": out_path.stat().st_size,
            }
        )

    # Generate 2x3 Collage
    collage = create_preview_collage(rendered_items)
    collage_path = out_dir / "collage_accessories_grid.png"
    collage.save(collage_path, format="PNG", optimize=True)
    print(f" [OK] collage_accessories_grid.png   | Size: {collage_path.stat().st_size / 1024.0:6.1f} KB")

    # Manifest
    manifest_path = out_dir / "preview_manifest.json"
    manifest_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f" [OK] preview_manifest.json          | Saved {len(metadata)} preview metadata records")

    print("=" * 80)
    print(" All character face & accessories previews successfully generated at:")
    print(f" {out_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
