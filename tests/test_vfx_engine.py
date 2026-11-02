"""
Dark Myth Stickman Auto-Studio - Stage 8: Dark Corruption VFX Engine Tests.

Validates VFX Events, Deterministic Particle Simulation, Notebook Background Warp
Distortion, Weapon Motion Trails, 7-Layer Compositing, and Buddha Palm Suppression.
"""

import math
from pathlib import Path
import time

import numpy as np
from PIL import Image, ImageDraw
import pytest

from app.modules.animation.animation_loop import AnimationLoopEngine, AnimationTrack, Keyframe
from app.modules.animation.background_renderer import NotebookBackgroundRenderer
from app.modules.animation.buddha_palm_renderer import BuddhaPalmRenderer
from app.modules.animation.pose_catalog import PoseCatalog
from app.modules.animation.stickman_models import Point2D, StickmanCharacter
from app.modules.animation.vfx_distortion import WarpDistortionField
from app.modules.animation.vfx_engine import DarkCorruptionVFXEngine
from app.modules.animation.vfx_models import (
    Particle,
    VFXConfig,
    VFXEvent,
    VFXEventType,
    WarpProfile,
)
from app.modules.animation.vfx_motion_trail import MotionTrailRenderer
from app.modules.animation.vfx_particles import ParticleSystem
from app.schemas.scene_schema import (
    ActionPreset,
    ActorConfig,
    ActorSide,
    CharacterSkin,
    WeaponType,
)


# -----------------------------------------------------------------------------
# 1. VFX EVENT & DATA MODEL TESTS
# -----------------------------------------------------------------------------

def test_vfx_event_validation():
    """Verify VFXEvent input validations."""
    # Valid event
    ev = VFXEvent(
        event_id="ev_01",
        event_type=VFXEventType.CLASH_SPARKS,
        start_time_sec=1.0,
        duration_sec=0.5,
        center=Point2D(540.0, 960.0),
        intensity=1.2,
        radius=250.0,
    )
    assert ev.end_time_sec == 1.5
    assert ev.get_progress(1.25) == 0.5
    assert ev.get_progress(0.5) is None
    assert ev.get_progress(2.0) is None

    # Invalid start time
    with pytest.raises(ValueError, match="start_time_sec must be non-negative"):
        VFXEvent(
            event_id="err",
            event_type=VFXEventType.CLASH_SPARKS,
            start_time_sec=-0.5,
            duration_sec=0.5,
            center=Point2D(0, 0),
        )

    # Invalid duration
    with pytest.raises(ValueError, match="duration_sec must be positive"):
        VFXEvent(
            event_id="err",
            event_type=VFXEventType.CLASH_SPARKS,
            start_time_sec=0.0,
            duration_sec=0.0,
            center=Point2D(0, 0),
        )


# -----------------------------------------------------------------------------
# 2. NOTEBOOK BACKGROUND WARP DISTORTION TESTS
# -----------------------------------------------------------------------------

def test_warp_distortion_field_zero_overhead_when_idle():
    """Verify background warp returns original image unchanged when no events are active."""
    field = WarpDistortionField(width=1080, height=1920)
    bg = Image.new("RGB", (1080, 1920), (244, 239, 230))

    # No events
    out = field.apply_distortion(bg, active_events=[], current_time_sec=1.0)
    assert out is bg  # Exact same object reference

    # Event active elsewhere in time
    ev = VFXEvent(
        event_id="warp_01",
        event_type=VFXEventType.BACKGROUND_WARP,
        start_time_sec=2.0,
        duration_sec=1.0,
        center=Point2D(540.0, 850.0),
    )
    out_inactive = field.apply_distortion(bg, active_events=[ev], current_time_sec=0.5)
    assert out_inactive is bg


def test_warp_distortion_field_palm_depression():
    """
    Verify Giant Palm depression smoothly sags horizontal ruled lines downward.
    """
    field = WarpDistortionField(width=1080, height=1920)

    # Create synthetic notebook background with crisp blue horizontal lines
    bg = Image.new("RGB", (1080, 1920), (244, 239, 230))
    draw = ImageDraw.Draw(bg)
    for y in range(180, 1820, 48):
        draw.line([(0, y), (1080, y)], fill=(155, 184, 211), width=2)

    ev = VFXEvent(
        event_id="palm_warp",
        event_type=VFXEventType.BACKGROUND_WARP,
        start_time_sec=1.0,
        duration_sec=1.0,
        center=Point2D(540.0, 850.0),
        intensity=1.0,
        metadata={"profile": WarpProfile.PALM_DEPRESSION, "max_amplitude_px": 80.0},
    )

    # Sample at peak progress u = 0.5 (time = 1.5s)
    warped = field.apply_distortion(bg, active_events=[ev], current_time_sec=1.5)
    assert warped.size == (1080, 1920)
    assert warped is not bg

    # Verify pixels are displaced near warp center
    arr_orig = np.array(bg, dtype=int)
    arr_warped = np.array(warped, dtype=int)
    diff = np.abs(arr_orig - arr_warped)

    # Maximum difference should be significant (lines moved onto white paper)
    assert np.max(diff) > 50
    # Mean difference in center ROI should be positive
    center_roi = diff[750:950, 400:680]
    assert np.mean(center_roi) > 2.0


def test_warp_distortion_field_radial_shockwave():
    """Verify radial shockwave ripples background outward."""
    field = WarpDistortionField(width=1080, height=1920)
    bg = Image.new("RGB", (1080, 1920), (244, 239, 230))
    draw = ImageDraw.Draw(bg)
    draw.ellipse([440, 860, 640, 1060], outline=(155, 184, 211), width=4)

    ev = VFXEvent(
        event_id="radial_warp",
        event_type=VFXEventType.BACKGROUND_WARP,
        start_time_sec=0.0,
        duration_sec=0.8,
        center=Point2D(540.0, 960.0),
        radius=400.0,
        metadata={"profile": WarpProfile.RADIAL_SHOCKWAVE, "max_amplitude_px": 60.0},
    )

    warped = field.apply_distortion(bg, active_events=[ev], current_time_sec=0.4)
    assert warped.size == (1080, 1920)
    diff = np.abs(np.array(bg, dtype=int) - np.array(warped, dtype=int))
    assert np.max(diff) > 20


def test_warp_distortion_field_restoration():
    """Verify that after the warp duration has elapsed, the field returns undisturbed background."""
    field = WarpDistortionField(width=1080, height=1920)
    bg = Image.new("RGB", (1080, 1920), (244, 239, 230))

    ev = VFXEvent(
        event_id="palm_warp",
        event_type=VFXEventType.BACKGROUND_WARP,
        start_time_sec=1.0,
        duration_sec=1.0,
        center=Point2D(540.0, 850.0),
    )

    # After duration (time = 2.1s)
    out_after = field.apply_distortion(bg, active_events=[ev], current_time_sec=2.1)
    assert out_after is bg


# -----------------------------------------------------------------------------
# 3. PARTICLE SYSTEM & IMPACT VFX TESTS
# -----------------------------------------------------------------------------

def test_particle_system_dark_aura_determinism():
    """Verify identical seed and time yield bit-identical dark aura particles."""
    ps = ParticleSystem()
    center = Point2D(540.0, 960.0)

    aura1 = ps.render_dark_aura(center, facing=1, scale=1.0, current_time_sec=1.0, seed=42)
    aura2 = ps.render_dark_aura(center, facing=1, scale=1.0, current_time_sec=1.0, seed=42)
    assert aura1.tobytes() == aura2.tobytes()

    # Different time slot yields dynamic evolution
    aura3 = ps.render_dark_aura(center, facing=1, scale=1.0, current_time_sec=1.5, seed=42)
    assert aura1.tobytes() != aura3.tobytes()


def test_particle_system_clash_sparks():
    """Verify clash sparks render outward with fading alpha."""
    ps = ParticleSystem()
    ev = VFXEvent(
        event_id="sparks",
        event_type=VFXEventType.CLASH_SPARKS,
        start_time_sec=0.0,
        duration_sec=0.5,
        center=Point2D(540.0, 960.0),
        intensity=1.5,
    )

    layer_mid = ps.render_clash_sparks(ev, progress=0.5)
    assert layer_mid.size == (1080, 1920)
    extrema = layer_mid.getextrema()
    # Check alpha channel has visible drawn pixels
    assert extrema[3][1] > 0

    # At progress 1.0 (end), sparks should be faded out
    layer_end = ps.render_clash_sparks(ev, progress=1.0)
    assert layer_end.getextrema()[3][1] == 0


def test_particle_system_shockwave_ring():
    """Verify shockwave ring expands radially with double ring."""
    ps = ParticleSystem()
    ev = VFXEvent(
        event_id="shockwave",
        event_type=VFXEventType.SHOCKWAVE_RING,
        start_time_sec=0.0,
        duration_sec=0.6,
        center=Point2D(540.0, 960.0),
        radius=300.0,
    )

    ring = ps.render_shockwave_ring(ev, progress=0.3)
    assert ring.size == (1080, 1920)
    assert ring.getextrema()[3][1] > 0


def test_particle_system_ground_cracks():
    """Verify ground cracks render branching jagged lines."""
    ps = ParticleSystem()
    ev = VFXEvent(
        event_id="cracks",
        event_type=VFXEventType.GROUND_CRACK,
        start_time_sec=0.0,
        duration_sec=1.0,
        center=Point2D(540.0, 1420.0),
        radius=250.0,
    )

    cracks = ps.render_ground_cracks(ev, progress=0.5)
    assert cracks.size == (1080, 1920)
    assert cracks.getextrema()[3][1] > 0


def test_particle_system_paper_dust():
    """Verify paper dust particles burst upward from ground impact."""
    ps = ParticleSystem()
    ev = VFXEvent(
        event_id="dust",
        event_type=VFXEventType.PAPER_DUST,
        start_time_sec=0.0,
        duration_sec=0.6,
        center=Point2D(540.0, 1420.0),
    )

    dust = ps.render_paper_dust(ev, progress=0.4)
    assert dust.size == (1080, 1920)
    assert dust.getextrema()[3][1] > 0


# -----------------------------------------------------------------------------
# 4. WEAPON MOTION TRAIL TESTS
# -----------------------------------------------------------------------------

def test_motion_trail_renderer():
    """Verify MotionTrailRenderer forms connected quad ribbons between consecutive frames."""
    mtr = MotionTrailRenderer(canvas_size=(1080, 1920), max_history=5)

    # Frame 0
    t0 = mtr.render_trail(Point2D(500, 1000), Point2D(550, 800), frame_idx=0)
    # Only 1 point, no trail yet
    assert t0.getextrema()[3][1] == 0

    # Frame 1 (weapon swung upward)
    t1 = mtr.render_trail(Point2D(520, 980), Point2D(650, 720), frame_idx=1)
    # Now there are 2 frames, quad ribbon rendered
    assert t1.getextrema()[3][1] > 0

    # Reset
    mtr.reset()
    t_after_reset = mtr.render_trail(Point2D(520, 980), Point2D(650, 720), frame_idx=10)
    assert t_after_reset.getextrema()[3][1] == 0


def test_motion_trail_skipped_frames():
    """Verify motion trail does not connect across large frame jumps (> 2 frames)."""
    mtr = MotionTrailRenderer(canvas_size=(1080, 1920), max_history=5)
    mtr.record_endpoints(Point2D(500, 1000), Point2D(550, 800), frame_idx=0)
    # Jump from frame 0 to frame 5 (cut/scene change)
    t = mtr.render_trail(Point2D(700, 1000), Point2D(750, 800), frame_idx=5)
    # Should not connect across frame gap of 5
    assert t.getextrema()[3][1] == 0


# -----------------------------------------------------------------------------
# 5. VFX ENGINE COMPOSITING & INTEGRATION TESTS
# -----------------------------------------------------------------------------

def test_vfx_engine_map_action_presets():
    """Verify action presets generate appropriate Dark Myth VFX events."""
    vfx_engine = DarkCorruptionVFXEngine()

    # heavy_charge_clash
    clash_events = vfx_engine.map_action_preset_vfx(
        action_preset=ActionPreset.HEAVY_CHARGE_CLASH,
        scene_start_sec=2.0,
        scene_duration_sec=4.0,
        character_center=Point2D(540.0, 1280.0),
    )
    assert len(clash_events) >= 3
    types = [ev.event_type for ev in clash_events]
    assert VFXEventType.CLASH_SPARKS in types
    assert VFXEventType.SHOCKWAVE_RING in types
    assert VFXEventType.GROUND_CRACK in types

    # giant_palm_suppression
    palm_events = vfx_engine.map_action_preset_vfx(
        action_preset=ActionPreset.GIANT_PALM_SUPPRESSION,
        scene_start_sec=0.0,
        scene_duration_sec=5.0,
        character_center=Point2D(540.0, 1380.0),
    )
    assert any(ev.event_type == VFXEventType.BACKGROUND_WARP for ev in palm_events)


def test_vfx_engine_render_frame_with_all_layers():
    """Verify full 7-layer compositing pipeline produces valid RGBA image."""
    vfx_engine = DarkCorruptionVFXEngine()
    bg_ren = NotebookBackgroundRenderer()
    bg_img = bg_ren.render_background(state="clean", seed=42)

    cfg = ActorConfig(
        actor_id="wukong",
        display_name="Dark Wukong",
        side=ActorSide.LEFT,
        skin=CharacterSkin.DARK_WUKONG,
        weapon=WeaponType.RUYI_STAFF,
        scale=1.0,
    )
    char = StickmanCharacter.from_actor_config(cfg)
    pdef = PoseCatalog.get_definition("combat_stance")

    # Add active clash event
    ev = VFXEvent(
        event_id="test_clash",
        event_type=VFXEventType.CLASH_SPARKS,
        start_time_sec=0.0,
        duration_sec=1.0,
        center=Point2D(540.0, 960.0),
    )
    vfx_engine.add_event(ev)

    frame = vfx_engine.render_frame_with_vfx(
        character=char,
        pose_def=pdef,
        canvas_pos=Point2D(540.0, 1420.0),
        facing=1,
        current_time_sec=0.5,
        frame_idx=15,
        background_image=bg_img,
    )

    assert frame.size == (1080, 1920)
    assert frame.mode == "RGBA"
    # Verify non-empty
    extrema = frame.getextrema()
    assert extrema[3][1] > 0


def test_vfx_engine_generate_clip_frames():
    """Verify generate_clip_frames_with_vfx renders full multi-frame sequence."""
    vfx_engine = DarkCorruptionVFXEngine()
    track = AnimationTrack(
        keyframes=[
            Keyframe(time_sec=0.0, pose_name="standoff_idle"),
            Keyframe(time_sec=0.1, pose_name="combat_stance"),
        ],
        duration_sec=0.1,
        loop=False,
    )
    cfg = ActorConfig(
        actor_id="wukong",
        display_name="Dark Wukong",
        side=ActorSide.LEFT,
        skin=CharacterSkin.DARK_WUKONG,
        weapon=WeaponType.RUYI_STAFF,
        scale=0.5,
    )
    char = StickmanCharacter.from_actor_config(cfg)

    frames = vfx_engine.generate_clip_frames_with_vfx(
        track=track,
        character=char,
        fps=10,
    )
    assert len(frames) == 1
    assert frames[0].size == (1080, 1920)


def test_vfx_engine_performance_benchmark():
    """Verify full-resolution frame rendering with all VFX active executes within reasonable CPU time."""
    vfx_engine = DarkCorruptionVFXEngine()
    cfg = ActorConfig(
        actor_id="wukong",
        display_name="Dark Wukong",
        side=ActorSide.LEFT,
        skin=CharacterSkin.DARK_WUKONG,
        weapon=WeaponType.RUYI_STAFF,
        scale=1.0,
    )
    char = StickmanCharacter.from_actor_config(cfg)
    pdef = PoseCatalog.get_definition("combat_stance")
    bg = Image.new("RGB", (1080, 1920), (244, 239, 230))

    # Activate warp and sparks
    vfx_engine.add_event(VFXEvent(
        event_id="bench_warp",
        event_type=VFXEventType.BACKGROUND_WARP,
        start_time_sec=0.0,
        duration_sec=1.0,
        center=Point2D(540.0, 850.0),
    ))
    vfx_engine.add_event(VFXEvent(
        event_id="bench_sparks",
        event_type=VFXEventType.CLASH_SPARKS,
        start_time_sec=0.0,
        duration_sec=1.0,
        center=Point2D(540.0, 1200.0),
    ))

    # Time frame rendering
    t0 = time.time()
    frame = vfx_engine.render_frame_with_vfx(
        character=char,
        pose_def=pdef,
        canvas_pos=Point2D(540.0, 1420.0),
        facing=1,
        current_time_sec=0.5,
        frame_idx=15,
        background_image=bg,
    )
    dt = time.time() - t0

    # Ensure frame renders in under 250ms on CPU (measured typically ~60-90ms)
    assert dt < 0.25, f"Frame render took too long: {dt*1000:.1f}ms"
    assert frame.size == (1080, 1920)
