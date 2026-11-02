"""Unit Tests for Pydantic Schemas (ScriptInput, SceneSchema, JobRecord, RenderResult)."""

import pytest
from pydantic import ValidationError

from app.schemas.job_schema import JobRecord, JobSource, JobStatus, RenderResult
from app.schemas.scene_schema import (
    ActionPreset,
    ActorConfig,
    BackgroundState,
    CameraMovement,
    CharacterSkin,
    SceneSchema,
    SFXEvent,
    WeaponType,
)
from app.schemas.script_schema import ScriptInput


def test_valid_scene_schema_and_contract_compatibility() -> None:
    """Verify SceneSchema accepts both Phase 3 fields and docs/04_data_contracts.md field aliases."""
    scene = SceneSchema(
        scene_id=1,
        narration_text="Ngộ Không vung Thiết Bảng Như Ý đập tan đội hình Thiên Binh!",
        audio_duration_sec=5.45,
        background_state=BackgroundState.CRACKED_PAGE,
        actors=[
            ActorConfig(
                actor_id="wukong_01",
                skin=CharacterSkin.DARK_WUKONG,
                color="#D92626",
                weapon=WeaponType.RUYI_STAFF,
            ),
            # Test docs/04_data_contracts.md alias keys (character_type, aura_color)
            ActorConfig.model_validate(
                {
                    "actor_id": "erlang_01",
                    "character_type": "erlang_shen",
                    "aura_color": "#E6B800",
                    "weapon": "three_pointed_spear",
                }
            ),
        ],
        action_preset=ActionPreset.STAFF_VORTEX_SWEEP,
        camera_movement=CameraMovement.SHAKE_HEAVY,
        sfx_events=[
            SFXEvent(sfx_name="metal_weapon_clash", time_offset=1.2, volume=0.95),
            SFXEvent.model_validate({"sfx_type": "paper_shockwave", "offset_sec": 1.5, "volume": 0.8}),
        ],
    )

    assert scene.scene_id == 1
    assert scene.background_state == BackgroundState.CRACKED_PAGE
    assert len(scene.actors) == 2
    assert scene.actors[1].skin == CharacterSkin.ERLANG_SHEN
    assert scene.actors[1].character_type == CharacterSkin.ERLANG_SHEN
    assert scene.sfx_events[1].sfx_name == "paper_shockwave"
    assert scene.sfx_events[1].time_offset == 1.5


@pytest.mark.parametrize(
    "invalid_payload,reason",
    [
        (
            {
                "scene_id": 0,  # Must be > 0
                "narration_text": "Câu thoại hợp lệ",
                "audio_duration_sec": 3.0,
                "background_state": "normal_page",
                "actors": [{"skin": "dark_wukong", "color": "#000", "weapon": "ruyi_staff"}],
                "action_preset": "heavy_charge_clash",
            },
            "scene_id must be > 0",
        ),
        (
            {
                "scene_id": 1,
                "narration_text": "   ",  # Blank narration
                "audio_duration_sec": 3.0,
                "background_state": "normal_page",
                "actors": [{"skin": "dark_wukong", "color": "#000", "weapon": "ruyi_staff"}],
                "action_preset": "heavy_charge_clash",
            },
            "narration_text cannot be blank",
        ),
        (
            {
                "scene_id": 1,
                "narration_text": "Câu thoại hợp lệ",
                "audio_duration_sec": -1.5,  # Negative duration
                "background_state": "normal_page",
                "actors": [{"skin": "dark_wukong", "color": "#000", "weapon": "ruyi_staff"}],
                "action_preset": "heavy_charge_clash",
            },
            "audio_duration_sec cannot be negative",
        ),
        (
            {
                "scene_id": 1,
                "narration_text": "Câu thoại hợp lệ",
                "audio_duration_sec": 4.0,
                "background_state": "normal_page",
                "actors": [{"skin": "dark_wukong", "color": "#000", "weapon": "ruyi_staff"}],
                "action_preset": "invalid_kamehameha_move",  # Invalid action preset
            },
            "invalid action_preset enum",
        ),
        (
            {
                "scene_id": 1,
                "narration_text": "Câu thoại hợp lệ",
                "audio_duration_sec": 4.0,
                "background_state": "invalid_galaxy_bg",  # Invalid background state
                "actors": [{"skin": "dark_wukong", "color": "#000", "weapon": "ruyi_staff"}],
                "action_preset": "heavy_charge_clash",
            },
            "invalid background_state enum",
        ),
        (
            {
                "scene_id": 1,
                "narration_text": "Câu thoại hợp lệ",
                "audio_duration_sec": 4.0,
                "background_state": "normal_page",
                "actors": [{"skin": "dark_wukong", "color": "#000", "weapon": "ruyi_staff"}],
                "action_preset": "heavy_charge_clash",
                "sfx_events": [{"sfx_name": "clash", "time_offset": -0.2}],  # Negative SFX offset
            },
            "sfx time_offset cannot be negative",
        ),
    ],
)
def test_scene_schema_rejects_invalid_data(invalid_payload: dict, reason: str) -> None:
    """Verify SceneSchema strictly blocks invalid scene_id, blank narration, negative duration, or unknown enums."""
    with pytest.raises(ValidationError):
        SceneSchema.model_validate(invalid_payload)


def test_script_input_validation() -> None:
    """Verify ScriptInput enforces minimum script length and valid duration bounds."""
    valid = ScriptInput(raw_script_text="Tôn Ngộ Không đại náo thiên cung trên trang giấy vở.")
    assert valid.job_id.startswith("job_")
    assert valid.render_config.width == 1080
    assert valid.render_config.height == 1920

    with pytest.raises(ValidationError):
        ScriptInput(raw_script_text="Quá ngắn")


def test_job_record_and_render_result_validation() -> None:
    """Verify JobRecord and RenderResult enforce progress bounds (0-100) and terminal states."""
    job = JobRecord(job_id="job_123", source=JobSource.TELEGRAM, status=JobStatus.QUEUED, progress_percent=0)
    assert job.status == JobStatus.QUEUED

    with pytest.raises(ValidationError):
        JobRecord(job_id="job_123", progress_percent=120)

    with pytest.raises(ValidationError):
        # Completed RenderResult requires output_video_path
        RenderResult(job_id="job_123", status=JobStatus.COMPLETED, output_video_path=None)

    failed_res = RenderResult(
        job_id="job_123",
        status=JobStatus.FAILED,
        output_video_path=None,
        error_message="Simulated failure",
    )
    assert failed_res.status == JobStatus.FAILED
