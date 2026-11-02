"""Dark Myth Stickman - Weapon Renderer Preview Generator (G5.2.3.3).

Generates 9 high-definition character weapon previews:
1. Wukong - Standoff - Ruyi Staff - One Hand - Facing Right
2. Wukong - Combat Stance - Ruyi Staff - Two Hands - Facing Right
3. Wukong - Overhead Slam - Ruyi Staff - Two Hands - Facing Right
4. Wukong - Vortex Sweep - Ruyi Staff - One Hand - Facing Right
5. Erlang Shen - Standoff - Three Pointed Spear - Facing Right
6. Erlang Shen - Guard Block - Three Pointed Spear - Two Hands - Facing Left
7. Celestial General - Celestial Halberd - Facing Right
8. Celestial General - Celestial Halberd - Facing Left
9. Wukong - Combat Stance - Unarmed - Reference

Composites full character hierarchy:
  1. Back accessories (Scarf, Feathers, Cloak)
  2. Humanoid body skeleton (Bones, Joint caps, Head circle)
  3. Weapon layer (Ruyi Staff, Three Pointed Spear, Celestial Halberd)
  4. Facial features (Red eyes, Third Eye, Visor)
  5. Front accessories (Kim Cô, Helmets, Armor)

Outputs to out/preview/stickman/weapons/.
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
    WeaponRenderer,
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
    """Create a 3-row x 3-col comparison grid with subtle dark notebook grid background."""
    cols = 3
    rows = (len(items) + cols - 1) // cols
    margin = 25
    header_h = 45
    total_w = cols * thumb_w + (cols + 1) * margin
    total_h = rows * (thumb_h + header_h) + (rows + 1) * margin

    collage = Image.new("RGBA", (total_w, total_h), (20, 22, 26, 255))
    draw = ImageDraw.Draw(collage)

    # Subtle paper grid on collage background
    for gx in range(0, total_w, 20):
        draw.line([(gx, 0), (gx, total_h)], fill=(28, 32, 38, 255), width=1)
    for gy in range(0, total_h, 20):
        draw.line([(0, gy), (total_w, gy)], fill=(28, 32, 38, 255), width=1)

    for idx, (label, img) in enumerate(items):
        r = idx // cols
        c = idx % cols
        x = margin + c * (thumb_w + margin)
        y = margin + r * (thumb_h + header_h + margin)

        # Draw card background
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
    output_dir = WORKSPACE_ROOT / "out" / "preview" / "stickman" / "weapons"
    output_dir.mkdir(parents=True, exist_ok=True)

    body_renderer = HumanoidBodyRenderer()
    face_renderer = FaceFeatureRenderer()
    accessories_renderer = AccessoriesRenderer()
    weapon_renderer = WeaponRenderer()

    # Actor configurations
    wukong_staff_cfg = ActorConfig(
        actor_id="wukong_staff",
        skin=CharacterSkin.DARK_WUKONG,
        color="#D92626",
        weapon=WeaponType.RUYI_STAFF,
        display_name="Dark Wukong",
        side=ActorSide.LEFT,
        scale=1.0,
    )
    wukong_unarmed_cfg = ActorConfig(
        actor_id="wukong_unarmed",
        skin=CharacterSkin.DARK_WUKONG,
        color="#D92626",
        weapon=WeaponType.UNARMED,
        display_name="Dark Wukong Unarmed",
        side=ActorSide.LEFT,
        scale=1.0,
    )
    erlang_cfg = ActorConfig(
        actor_id="erlang_spear",
        skin=CharacterSkin.ERLANG_SHEN,
        color="#E0E0E0",
        weapon=WeaponType.THREE_POINTED_SPEAR,
        display_name="Erlang Shen",
        side=ActorSide.RIGHT,
        scale=1.05,
    )
    general_cfg = ActorConfig(
        actor_id="general_halberd",
        skin=CharacterSkin.CELESTIAL_GENERAL,
        color="#C41E3A",
        weapon=WeaponType.CELESTIAL_HALBERD,
        display_name="Celestial General",
        side=ActorSide.RIGHT,
        scale=1.20,
    )

    char_wukong = StickmanCharacter.from_actor_config(wukong_staff_cfg)
    char_unarmed = StickmanCharacter.from_actor_config(wukong_unarmed_cfg)
    char_erlang = StickmanCharacter.from_actor_config(erlang_cfg)
    char_general = StickmanCharacter.from_actor_config(general_cfg)

    # 9 Preview scenarios
    scenarios = [
        # 1. Wukong - Standoff - Ruyi Staff - One Hand - Right
        (
            "wukong_standoff_ruyi_right.png",
            "1. Wukong - Standoff (Ruyi Staff)",
            char_wukong,
            "standoff_idle",
            420.0,
            1,
            False,
        ),
        # 2. Wukong - Combat Stance - Ruyi Staff - Two Hands - Right
        (
            "wukong_combat_ruyi_twohands.png",
            "2. Wukong - Combat (Two-Hand Staff)",
            char_wukong,
            "combat_stance",
            420.0,
            1,
            True,
        ),
        # 3. Wukong - Overhead Slam - Ruyi Staff - Two Hands - Right
        (
            "wukong_overhead_ruyi_twohands.png",
            "3. Wukong - Overhead Slam (Two Hands)",
            char_wukong,
            "overhead_slam",
            480.0,
            1,
            True,
        ),
        # 4. Wukong - Vortex Sweep - Ruyi Staff - Right
        (
            "wukong_vortex_ruyi_onehand.png",
            "4. Wukong - Vortex Sweep (Spin Staff)",
            char_wukong,
            "vortex_sweep",
            500.0,
            1,
            False,
        ),
        # 5. Erlang - Standoff - Three Pointed Spear - Right
        (
            "erlang_standoff_spear_right.png",
            "5. Erlang - Standoff (Trident Spear)",
            char_erlang,
            "standoff_idle",
            420.0,
            1,
            False,
        ),
        # 6. Erlang - Guard Block - Three Pointed Spear - Two Hands - Left
        (
            "erlang_guard_spear_twohands_left.png",
            "6. Erlang - Guard Block (Two Hands Left)",
            char_erlang,
            "guard_block",
            660.0,
            -1,
            True,
        ),
        # 7. Celestial General - Celestial Halberd - Right
        (
            "general_halberd_right.png",
            "7. Celestial General - Halberd (Right)",
            char_general,
            "standoff_idle",
            400.0,
            1,
            False,
        ),
        # 8. Celestial General - Celestial Halberd - Left
        (
            "general_halberd_left.png",
            "8. Celestial General - Halberd (Left)",
            char_general,
            "standoff_idle",
            680.0,
            -1,
            False,
        ),
        # 9. Wukong - Combat Stance - Unarmed - Reference
        (
            "wukong_combat_unarmed.png",
            "9. Wukong - Combat Stance (Unarmed)",
            char_unarmed,
            "combat_stance",
            420.0,
            1,
            False,
        ),
    ]

    manifest = []
    collage_items = []

    print("=" * 80)
    print(" DARK MYTH STICKMAN - WEAPON RENDERER PREVIEW GENERATOR (G5.2.3.3)")
    print("=" * 80)

    for filename, label, character, pose_name, canvas_x, facing, align_two_hands in scenarios:
        t0 = time.perf_counter()
        pose = PoseCatalog.get_pose(pose_name)
        pdef = PoseCatalog.get_definition(pose_name)

        # Coordinate calculation via CoordinateManager
        pelvis_y = CoordinateManager.get_ground_aligned_root_y(
            pose=pose,
            support_mode=pdef.support_mode,
            ground_y=1420.0,
            scale=character.scale,
        )
        pelvis_pt = Point2D(canvas_x, pelvis_y)

        # Composite full character with weapon
        comp_img = composite_character(
            body_renderer=body_renderer,
            face_renderer=face_renderer,
            accessories_renderer=accessories_renderer,
            character=character,
            pose=pose,
            canvas_position=pelvis_pt,
            facing=facing,
            weapon_renderer=weapon_renderer,
            align_two_hands=align_two_hands,
        )

        # Save individual PNG
        filepath = output_dir / filename
        comp_img.save(filepath, format="PNG", optimize=True)
        t_elapsed = (time.perf_counter() - t0) * 1000.0

        # Validate grip geometry
        grip_val = weapon_renderer.validate_grip(
            character=character,
            pose=pose,
            canvas_position=pelvis_pt,
            facing=facing,
            pose_def=pdef,
            align_two_hands=align_two_hands,
        )

        bbox = comp_img.getbbox()
        arr = np.array(comp_img)
        non_zero_px = int(np.count_nonzero(arr[:, :, 3] > 0))
        file_size = filepath.stat().st_size

        manifest.append(
            {
                "file": filename,
                "character": character.actor_id,
                "skin": character.skin.value,
                "weapon": character.weapon.value,
                "pose": pose_name,
                "pelvis_canvas": {"x": pelvis_pt.x, "y": pelvis_pt.y},
                "facing": facing,
                "scale": character.scale,
                "align_two_hands": align_two_hands,
                "grip_validation": {
                    "is_valid": grip_val.is_valid,
                    "d_perp": round(grip_val.d_perp, 2),
                    "d_parallel": round(grip_val.d_parallel, 2),
                    "weapon_angle_deg": round(grip_val.weapon_angle_deg, 2),
                    "message": grip_val.message,
                },
                "pixel_alpha_bbox": list(bbox) if bbox else None,
                "non_zero_pixels": non_zero_px,
                "file_size_bytes": file_size,
            }
        )
        collage_items.append((label, comp_img))

        print(
            f" [OK] {filename:38} | Size: {file_size/1024:6.1f} KB | Non-zero px: {non_zero_px:6d} | "
            f"BBox: {bbox} | Time: {t_elapsed:5.1f}ms"
        )

    # Generate collage
    collage_img = create_preview_collage(collage_items)
    collage_path = output_dir / "collage_weapons_grid.png"
    collage_img.save(collage_path, format="PNG", optimize=True)
    print(f" [OK] collage_weapons_grid.png               | Size: {collage_path.stat().st_size/1024:6.1f} KB")

    # Save manifest
    manifest_path = output_dir / "preview_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f" [OK] preview_manifest.json                  | Saved {len(manifest)} preview metadata records")
    print("=" * 80)
    print(f" All weapon previews successfully generated at:\n {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
