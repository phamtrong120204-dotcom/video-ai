"""
Visual Preview Generator for Buddha Palm Renderer (G5.2.3.4).

Generates 9 comprehensive test scenarios, composite collage, and manifest metadata JSON:
1. Nominal scale 3.50 descending palm (central view).
2. Descent top entry from heaven (Y = -150.0).
3. Descent impact suppression at Y = 820.0 (chiêu 7 moveset spec).
4. Compact scale 1.0 showing delicate anatomical proportions.
5. Medium scale 2.2 showing balanced screen coverage.
6. Ascending lotus mudra posture (direction="up").
7. Left-facing mirrored palm (facing = -1).
8. Pure ink contour and anatomical lines without aura (inspection mode).
9. Full character composite: Dark Wukong resisting Buddha Palm suppression.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import numpy as np
from PIL import Image, ImageDraw

from app.modules.animation.buddha_palm_renderer import BuddhaPalmRenderer
from app.modules.animation.character_renderer_parts import (
    AccessoriesRenderer,
    FaceFeatureRenderer,
    HumanoidBodyRenderer,
    WeaponRenderer,
    composite_character,
)
from app.modules.animation.pose_catalog import PoseCatalog
from app.modules.animation.stickman_models import (
    ActorConfig,
    ActorSide,
    CharacterSkin,
    CoordinateManager,
    Point2D,
    StickmanCharacter,
    WeaponType,
)


def create_preview_collage(
    items: list[tuple[str, Image.Image]],
    thumb_w: int = 360,
    thumb_h: int = 640,
) -> Image.Image:
    """Create a 3-row x 3-col comparison grid with dark paper grid background."""
    cols = 3
    rows = (len(items) + cols - 1) // cols
    margin = 25
    header_h = 45
    total_w = cols * thumb_w + (cols + 1) * margin
    total_h = rows * (thumb_h + header_h) + (rows + 1) * margin

    collage = Image.new("RGBA", (total_w, total_h), (20, 22, 26, 255))
    draw = ImageDraw.Draw(collage)

    # Subtle paper grid on background
    for gx in range(0, total_w, 20):
        draw.line([(gx, 0), (gx, total_h)], fill=(28, 32, 38, 255), width=1)
    for gy in range(0, total_h, 20):
        draw.line([(0, gy), (total_w, gy)], fill=(28, 32, 38, 255), width=1)

    for idx, (label, img) in enumerate(items):
        r = idx // cols
        c = idx % cols
        x = margin + c * (thumb_w + margin)
        y = margin + r * (thumb_h + header_h + margin)

        # Draw card container
        draw.rectangle(
            [x - 4, y - 4, x + thumb_w + 4, y + thumb_h + header_h + 4],
            fill=(14, 16, 20, 255),
            outline=(60, 68, 80, 255),
            width=1,
        )

        # Draw header text
        draw.text((x + 8, y + 12), label, fill=(220, 225, 235, 255))

        # Downscale full preview image to card thumbnail
        thumb = img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        collage.alpha_composite(thumb, (x, y + header_h))

    return collage


def main() -> None:
    output_dir = WORKSPACE_ROOT / "out" / "preview" / "stickman" / "buddha_palm"
    output_dir.mkdir(parents=True, exist_ok=True)

    palm_renderer = BuddhaPalmRenderer()
    body_renderer = HumanoidBodyRenderer()
    face_renderer = FaceFeatureRenderer()
    acc_renderer = AccessoriesRenderer()
    weapon_renderer = WeaponRenderer()

    # Actor config for Wukong composite
    wukong_cfg = ActorConfig(
        actor_id="wukong_staff",
        skin=CharacterSkin.DARK_WUKONG,
        color="#D92626",
        weapon=WeaponType.RUYI_STAFF,
        display_name="Dark Wukong",
        side=ActorSide.LEFT,
        scale=1.0,
    )
    char_wukong = StickmanCharacter.from_actor_config(wukong_cfg)

    # 9 Preview Scenarios
    scenarios = [
        # 1. Nominal scale 3.50 central descent
        {
            "filename": "buddha_palm_nominal_scale_3_5.png",
            "label": "1. Nominal Scale 3.50 (Descent)",
            "type": "standalone",
            "pos": Point2D(540.0, 500.0),
            "scale": 3.50,
            "facing": 1,
            "direction": "down",
            "progress": 0.6,
            "show_aura": True,
            "show_seal": True,
            "show_shockwave": True,
        },
        # 2. Descent entry from heaven Y = -150
        {
            "filename": "buddha_palm_descent_top_entry.png",
            "label": "2. Top Entry (Y = -150 px)",
            "type": "standalone",
            "pos": Point2D(540.0, -150.0),
            "scale": 3.50,
            "facing": 1,
            "direction": "down",
            "progress": 0.15,
            "show_aura": True,
            "show_seal": True,
            "show_shockwave": True,
        },
        # 3. Descent suppression impact at Y = 820
        {
            "filename": "buddha_palm_descent_suppression_y820.png",
            "label": "3. Suppression Impact (Y = 820 px)",
            "type": "standalone",
            "pos": Point2D(540.0, 820.0),
            "scale": 3.50,
            "facing": 1,
            "direction": "down",
            "progress": 1.0,
            "show_aura": True,
            "show_seal": True,
            "show_shockwave": True,
        },
        # 4. Compact scale 1.0
        {
            "filename": "buddha_palm_scale_1_0_compact.png",
            "label": "4. Compact Scale 1.0 (Anatomy)",
            "type": "standalone",
            "pos": Point2D(540.0, 700.0),
            "scale": 1.0,
            "facing": 1,
            "direction": "down",
            "progress": 1.0,
            "show_aura": True,
            "show_seal": True,
            "show_shockwave": True,
        },
        # 5. Medium scale 2.2
        {
            "filename": "buddha_palm_scale_2_2_medium.png",
            "label": "5. Medium Scale 2.20",
            "type": "standalone",
            "pos": Point2D(540.0, 600.0),
            "scale": 2.20,
            "facing": 1,
            "direction": "down",
            "progress": 0.8,
            "show_aura": True,
            "show_seal": True,
            "show_shockwave": True,
        },
        # 6. Ascending lotus mudra (direction="up")
        {
            "filename": "buddha_palm_direction_up_mudra.png",
            "label": "6. Lotus Mudra (Direction Up)",
            "type": "standalone",
            "pos": Point2D(540.0, 1100.0),
            "scale": 3.0,
            "facing": 1,
            "direction": "up",
            "progress": 0.9,
            "show_aura": True,
            "show_seal": True,
            "show_shockwave": True,
        },
        # 7. Left facing mirrored palm (facing = -1)
        {
            "filename": "buddha_palm_facing_left_mirrored.png",
            "label": "7. Mirrored Left (Facing -1)",
            "type": "standalone",
            "pos": Point2D(540.0, 500.0),
            "scale": 3.50,
            "facing": -1,
            "direction": "down",
            "progress": 0.7,
            "show_aura": True,
            "show_seal": True,
            "show_shockwave": True,
        },
        # 8. Pure ink contour & creases (inspection mode)
        {
            "filename": "buddha_palm_isolated_contour_no_aura.png",
            "label": "8. Pure Ink & Creases (No Aura)",
            "type": "standalone",
            "pos": Point2D(540.0, 600.0),
            "scale": 2.80,
            "facing": 1,
            "direction": "down",
            "progress": 1.0,
            "show_aura": False,
            "show_seal": True,
            "show_shockwave": False,
        },
        # 9. Composite: Wukong resisting Buddha Palm suppression
        {
            "filename": "buddha_palm_composite_wukong_suppression.png",
            "label": "9. Wukong vs Buddha Palm (Chiêu 7)",
            "type": "composite",
            "pos": Point2D(540.0, 680.0),
            "scale": 3.50,
            "facing": 1,
            "direction": "down",
            "progress": 0.9,
            "show_aura": True,
            "show_seal": True,
            "show_shockwave": True,
        },
    ]

    manifest = []
    collage_items = []

    print("=" * 80)
    print(" DARK MYTH STICKMAN - BUDDHA PALM PREVIEW GENERATOR (G5.2.3.4)")
    print("=" * 80)

    for sc in scenarios:
        t0 = time.perf_counter()
        fn = sc["filename"]
        lbl = sc["label"]
        pos = sc["pos"]
        sc_val = sc["scale"]
        facing = sc["facing"]
        direction = sc["direction"]
        progress = sc["progress"]

        if sc["type"] == "standalone":
            img = palm_renderer.render_palm(
                position=pos,
                scale=sc_val,
                facing=facing,
                direction=direction,
                descent_progress=progress,
                show_aura=sc["show_aura"],
                show_seal=sc["show_seal"],
                show_shockwave=sc["show_shockwave"],
            )
        else:
            # Composite with Wukong in overhead slam stance
            pose = PoseCatalog.get_pose("overhead_slam")
            pdef = PoseCatalog.get_definition("overhead_slam")
            pelvis_y = CoordinateManager.get_ground_aligned_root_y(
                pose=pose,
                support_mode=pdef.support_mode,
                ground_y=1420.0,
                scale=char_wukong.scale,
            )
            wukong_pos = Point2D(540.0, pelvis_y)

            img = composite_character(
                body_renderer=body_renderer,
                face_renderer=face_renderer,
                accessories_renderer=acc_renderer,
                character=char_wukong,
                pose=pose,
                canvas_position=wukong_pos,
                facing=1,
                weapon_renderer=weapon_renderer,
                buddha_palm_renderer=palm_renderer,
                palm_position=pos,
                palm_scale=sc_val,
                palm_direction=direction,
                palm_descent_progress=progress,
                palm_layer_order="foreground",
            )

        filepath = output_dir / fn
        img.save(filepath, format="PNG", optimize=True)
        t_elapsed = (time.perf_counter() - t0) * 1000.0

        bbox = img.getbbox()
        arr = np.array(img)
        non_zero_px = int(np.count_nonzero(arr[:, :, 3] > 0))
        file_sz = filepath.stat().st_size

        tips = palm_renderer.get_finger_tips(pos, scale=sc_val, facing=facing, direction=direction)
        tips_dict = {k: {"x": round(v.x, 1), "y": round(v.y, 1)} for k, v in tips.items()}

        manifest.append(
            {
                "file": fn,
                "label": lbl,
                "type": sc["type"],
                "palm_position": {"x": pos.x, "y": pos.y},
                "scale": sc_val,
                "facing": facing,
                "direction": direction,
                "descent_progress": progress,
                "fingertips": tips_dict,
                "pixel_alpha_bbox": list(bbox) if bbox else None,
                "non_zero_pixels": non_zero_px,
                "file_size_bytes": file_sz,
            }
        )
        collage_items.append((lbl, img))

        print(
            f" [OK] {fn:44} | Size: {file_sz/1024:6.1f} KB | Non-zero px: {non_zero_px:7d} | "
            f"BBox: {bbox} | Time: {t_elapsed:5.1f}ms"
        )

    # Generate collage
    collage_img = create_preview_collage(collage_items)
    collage_path = output_dir / "collage_buddha_palm_grid.png"
    collage_img.save(collage_path, format="PNG", optimize=True)
    print(f" [OK] collage_buddha_palm_grid.png                 | Size: {collage_path.stat().st_size/1024:6.1f} KB")

    # Save manifest
    manifest_path = output_dir / "preview_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f" [OK] preview_manifest.json                    | Saved {len(manifest)} preview metadata records")
    print("=" * 80)
    print(f" All Buddha Palm previews successfully generated at:\n {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
