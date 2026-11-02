"""Unit tests for Stage 5.1 Procedural Notebook Background Renderer."""

from pathlib import Path
import numpy as np
from PIL import Image
import pytest

from app.modules.animation.background_renderer import NotebookBackgroundRenderer
from app.schemas.scene_schema import BackgroundState, SceneSchema


@pytest.fixture
def renderer() -> NotebookBackgroundRenderer:
    return NotebookBackgroundRenderer(default_width=1080, default_height=1920)


def test_renderer_supports_all_background_states(renderer: NotebookBackgroundRenderer):
    """Test 1: Every canonical and Phase 3 BackgroundState enum value is supported."""
    for state in BackgroundState:
        img = renderer.render_background(state, width=270, height=480, seed=42)
        assert isinstance(img, Image.Image)
        assert img.size == (270, 480)
        assert img.mode == "RGB"


def test_renderer_correct_dimensions_production(renderer: NotebookBackgroundRenderer):
    """Test 2: Full production resolution (1080x1920) has exact dimension and RGB mode."""
    img = renderer.render_background(BackgroundState.CLEAN_NOTEBOOK, width=1080, height=1920, seed=123)
    assert img.size == (1080, 1920)
    assert img.mode == "RGB"

    arr = renderer.render_numpy(BackgroundState.CLEAN_NOTEBOOK, width=1080, height=1920, seed=123)
    assert arr.shape == (1920, 1080, 3)
    assert arr.dtype == np.uint8


def test_renderer_correct_dimensions_preview(renderer: NotebookBackgroundRenderer):
    """Test 3: Preview resolution (540x960) has exact dimension and RGB mode."""
    img = renderer.render_background(BackgroundState.CLEAN_NOTEBOOK, width=540, height=960, seed=456)
    assert img.size == (540, 960)
    assert img.mode == "RGB"


def test_renderer_not_empty_or_solid_black(renderer: NotebookBackgroundRenderer):
    """Test 4: Rendered images contain varied pixels (not blank or uninitialized)."""
    for state in [BackgroundState.CLEAN_NOTEBOOK, BackgroundState.DARK_CORRUPTED_PAGE, BackgroundState.HEAVENLY_PRESSURE]:
        arr = renderer.render_numpy(state, width=270, height=480, seed=101)
        mean_val = float(np.mean(arr))
        std_val = float(np.std(arr))

        # Must not be pitch black uninitialized buffer (even dark corrupted has mean > 10.0)
        assert mean_val > 10.0
        # Must have non-zero variance (texture + lines + features)
        assert std_val > 5.0


def test_renderer_deterministic_with_same_seed(renderer: NotebookBackgroundRenderer):
    """Test 5: The same seed produces bit-identical images."""
    arr1 = renderer.render_numpy(BackgroundState.INK_SPLATTERED, width=540, height=960, seed=999)
    arr2 = renderer.render_numpy(BackgroundState.INK_SPLATTERED, width=540, height=960, seed=999)
    assert np.array_equal(arr1, arr2)


def test_renderer_variations_with_different_seeds(renderer: NotebookBackgroundRenderer):
    """Test 6: Different seeds produce distinct procedural variations."""
    arr1 = renderer.render_numpy(BackgroundState.INK_SPLATTERED, width=540, height=960, seed=111)
    arr2 = renderer.render_numpy(BackgroundState.INK_SPLATTERED, width=540, height=960, seed=222)
    assert not np.array_equal(arr1, arr2)


def test_renderer_visual_distinction_between_states(renderer: NotebookBackgroundRenderer):
    """Test 7: Different background states have distinct color palettes and visual signatures."""
    clean_arr = renderer.render_numpy(BackgroundState.CLEAN_NOTEBOOK, width=270, height=480, seed=1)
    dark_arr = renderer.render_numpy(BackgroundState.DARK_CORRUPTED_PAGE, width=270, height=480, seed=1)
    heavenly_arr = renderer.render_numpy(BackgroundState.HEAVENLY_PRESSURE, width=270, height=480, seed=1)

    # Clean paper is bright cream (mean ~230)
    assert np.mean(clean_arr) > 200.0
    # Dark corrupted paper is deep charcoal (mean ~40-60)
    assert np.mean(dark_arr) < 90.0
    # Heavenly pressure has golden warmth (red/green higher than blue)
    assert np.mean(heavenly_arr[:, :, 0]) > np.mean(heavenly_arr[:, :, 2])

    # Direct pixel array difference must be substantial
    diff_clean_dark = np.mean(np.abs(clean_arr.astype(float) - dark_arr.astype(float)))
    assert diff_clean_dark > 100.0


def test_renderer_handles_invalid_state(renderer: NotebookBackgroundRenderer):
    """Test 8: Invalid BackgroundState raises ValueError with informative message."""
    with pytest.raises(ValueError) as exc_info:
        renderer.render_background("neon_cyberpunk_matrix")
    assert "Unsupported BackgroundState" in str(exc_info.value)


def test_renderer_combat_zone_safety_on_ink_splatters(renderer: NotebookBackgroundRenderer):
    """Test 9: Ink splatters are kept predominantly in the periphery, leaving center combat zone clear."""
    # In clean notebook, center is clean cream
    clean_arr = renderer.render_numpy(BackgroundState.CLEAN_NOTEBOOK, width=540, height=960, seed=42)
    ink_arr = renderer.render_numpy(BackgroundState.INK_SPLATTERED, width=540, height=960, seed=42)

    # Center box: X in [35%, 65%], Y in [40%, 65%]
    h, w, _ = clean_arr.shape
    y1, y2 = int(h * 0.40), int(h * 0.65)
    x1, x2 = int(w * 0.35), int(w * 0.65)

    center_clean = clean_arr[y1:y2, x1:x2].astype(float)
    center_ink = ink_arr[y1:y2, x1:x2].astype(float)

    # Mean difference in center should be very small (subtle texture only, no massive black splatter blocking combat)
    diff = np.mean(np.abs(center_clean - center_ink))
    assert diff < 15.0


def test_renderer_does_not_mutate_scene_schema():
    """Test 10: Calling background renderer does not mutate or violate SceneSchema."""
    scene = SceneSchema(
        scene_id=1,
        narration_text="Tôn Ngộ Không đối diện Nhị Lang Thần.",
        audio_duration_sec=5.0,
        voice_audio_path="out/temp/scene_01.mp3",
        background_state=BackgroundState.CRACKED_PAGE,
    )
    renderer = NotebookBackgroundRenderer()
    img = renderer.render_background(scene.background_state, width=270, height=480, seed=77)

    assert img.size == (270, 480)
    assert scene.scene_id == 1
    assert scene.background_state == BackgroundState.CRACKED_PAGE
    assert scene.audio_duration_sec == 5.0
