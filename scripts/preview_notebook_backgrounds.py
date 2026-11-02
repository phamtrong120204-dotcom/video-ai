"""Procedural Notebook Backgrounds Preview Generator.

Renders high-resolution 1080x1920 and 540x960 preview PNGs for all canonical BackgroundStates
into out/preview/backgrounds/, along with a multi-panel comparison collage.
"""

import json
import os
from pathlib import Path
import sys
import time

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from PIL import Image, ImageDraw, ImageFont

from app.modules.animation.background_renderer import NotebookBackgroundRenderer
from app.schemas.scene_schema import BackgroundState


def create_comparison_grid(images: list[tuple[str, Image.Image]], thumb_w: int = 360, thumb_h: int = 640) -> Image.Image:
    """Create a 2-row x 3-column side-by-side comparison collage."""
    cols = 3
    rows = (len(images) + cols - 1) // cols
    margin = 24
    header_h = 50
    total_w = cols * thumb_w + (cols + 1) * margin
    total_h = rows * (thumb_h + header_h) + (rows + 1) * margin

    collage = Image.new("RGB", (total_w, total_h), (25, 25, 30))
    draw = ImageDraw.Draw(collage)

    for idx, (label, img) in enumerate(images):
        r = idx // cols
        c = idx % cols
        x = margin + c * (thumb_w + margin)
        y = margin + r * (thumb_h + header_h + margin)

        # Draw label header
        draw.text((x + 10, y + 10), label.upper(), fill=(240, 240, 245))

        # Resize preview and paste
        resized = img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        collage.paste(resized, (x, y + header_h))

        # Thin white border around thumbnail
        draw.rectangle(
            [(x, y + header_h), (x + thumb_w - 1, y + header_h + thumb_h - 1)],
            outline=(100, 100, 115),
            width=2,
        )

    return collage


def main():
    print("=" * 80)
    print("STAGE 5.1: PROCEDURAL NOTEBOOK BACKGROUND ENGINE - PREVIEW GENERATOR")
    print("=" * 80)

    output_dir = WORKSPACE_ROOT / "out" / "preview" / "backgrounds"
    output_dir.mkdir(parents=True, exist_ok=True)

    renderer = NotebookBackgroundRenderer(default_width=1080, default_height=1920)

    # 6 Canonical States
    states = [
        BackgroundState.CLEAN_NOTEBOOK,
        BackgroundState.INK_SPLATTERED,
        BackgroundState.CRACKED_PAGE,
        BackgroundState.TORN_DARK_MYTH,
        BackgroundState.DARK_CORRUPTED_PAGE,
        BackgroundState.HEAVENLY_PRESSURE,
    ]

    fixed_seed = 20261031
    manifest_records = []
    comparison_images = []

    print(f"\nTarget Directory: {output_dir.resolve()}")
    print(f"Fixed Seed: {fixed_seed}\n")

    for state in states:
        canonical_name = renderer.normalize_state(state)
        print(f"[*] Rendering state: {state.value} (canonical: {canonical_name})...")

        # 1. Full Production Resolution (1080x1920)
        t0 = time.time()
        img_1080 = renderer.render_background(state, width=1080, height=1920, seed=fixed_seed)
        render_time_1080 = time.time() - t0

        file_1080 = output_dir / f"bg_{canonical_name}_1080x1920.png"
        img_1080.save(file_1080, format="PNG", optimize=True)
        size_1080 = file_1080.stat().st_size

        # 2. Preview Resolution (540x960)
        t1 = time.time()
        img_540 = renderer.render_background(state, width=540, height=960, seed=fixed_seed)
        render_time_540 = time.time() - t1

        file_540 = output_dir / f"bg_{canonical_name}_540x960.png"
        img_540.save(file_540, format="PNG", optimize=True)
        size_540 = file_540.stat().st_size

        comparison_images.append((canonical_name, img_1080))

        print(f"    -> 1080x1920: {file_1080.name} ({size_1080 / 1024:.1f} KB) in {render_time_1080:.3f}s")
        print(f"    -> 540x960:   {file_540.name} ({size_540 / 1024:.1f} KB) in {render_time_540:.3f}s")

        manifest_records.append({
            "state_enum": state.value,
            "canonical_name": canonical_name,
            "seed": fixed_seed,
            "full_res": {
                "filename": file_1080.name,
                "resolution": "1080x1920",
                "filesize_bytes": size_1080,
                "render_time_sec": round(render_time_1080, 4),
            },
            "preview_res": {
                "filename": file_540.name,
                "resolution": "540x960",
                "filesize_bytes": size_540,
                "render_time_sec": round(render_time_540, 4),
            },
        })

    # 3. Create Comparison Collage
    print("\n[*] Generating multi-state comparison collage...")
    collage = create_comparison_grid(comparison_images)
    collage_file = output_dir / "all_states_comparison_grid.png"
    collage.save(collage_file, format="PNG", optimize=True)
    print(f"    -> Collage saved: {collage_file.name} ({collage_file.stat().st_size / 1024:.1f} KB)")

    # 4. Save Manifest JSON
    manifest_file = output_dir / "manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "seed": fixed_seed,
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_states": len(states),
                "collage": collage_file.name,
                "records": manifest_records,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"[*] Manifest saved to: {manifest_file.name}")

    print("\n" + "=" * 80)
    print("ALL NOTEBOOK BACKGROUND PREVIEWS SUCCESSFULLY GENERATED!")
    print("=" * 80)


if __name__ == "__main__":
    main()
