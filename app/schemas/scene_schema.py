"""Scene Data Contracts (SceneSchema, ActorConfig, SFXEvent, CameraConfig, and Dark Myth Enums)."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class BackgroundState(str, Enum):
    """Notebook paper background states supporting both Phase 3 and Data Contract enum names."""

    # Phase 3 explicit enum values
    NORMAL_PAGE = "normal_page"
    CRACKED_PAGE = "cracked_page"
    DARK_CORRUPTED_PAGE = "dark_corrupted_page"

    # Data Contract (docs/04_data_contracts.md) canonical enum values
    CLEAN_NOTEBOOK = "clean_notebook"
    INK_SPLATTERED = "ink_splattered"
    TORN_DARK_MYTH = "torn_dark_myth"
    HEAVENLY_PRESSURE = "heavenly_pressure"


class CharacterSkin(str, Enum):
    """4 Approved Dark Myth character appearances / skins."""

    DARK_WUKONG = "dark_wukong"
    ERLANG_SHEN = "erlang_shen"
    CELESTIAL_GENERAL = "celestial_general"
    CELESTIAL_SOLDIER_SQUAD = "celestial_soldier_squad"
    BUDDHA_PALM = "buddha_palm"


class WeaponType(str, Enum):
    """Approved Dark Myth weapons."""

    RUYI_STAFF = "ruyi_staff"
    THREE_POINTED_SPEAR = "three_pointed_spear"
    CELESTIAL_HALBERD = "celestial_halberd"
    GIANT_GOLDEN_PALM = "giant_golden_palm"
    UNARMED = "unarmed"


class ActorSide(str, Enum):
    """Stage placement position on the 9:16 vertical canvas."""

    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    TOP = "top"


class ActionPreset(str, Enum):
    """8 Approved Dark Myth combat moveset presets."""

    DARK_AURA_STANDOFF = "dark_aura_standoff"
    HEAVY_CHARGE_CLASH = "heavy_charge_clash"
    FLURRY_COMBO = "flurry_combo"
    STAFF_VORTEX_SWEEP = "staff_vortex_sweep"
    SKY_LEAP_SLAM = "sky_leap_slam"
    DIVINE_EYE_BEAM = "divine_eye_beam"
    GIANT_PALM_SUPPRESSION = "giant_palm_suppression"
    KNOCKBACK_RECOVERY = "knockback_recovery"


class CameraMovement(str, Enum):
    """Approved 2D virtual camera movements."""

    STATIC_WIDE = "static_wide"
    ZOOM_IN_DRAMATIC = "zoom_in_dramatic"
    ZOOM_PUNCH_IMPACT = "zoom_punch_impact"
    PAN_VERTICAL_DOWN = "pan_vertical_down"
    PAN_VERTICAL_UP = "pan_vertical_up"
    SHAKE_HEAVY = "shake_heavy"


class CameraConfig(BaseModel):
    """Detailed camera movement configuration when structured camera settings are used."""

    model_config = ConfigDict(extra="forbid")

    movement: CameraMovement = Field(default=CameraMovement.STATIC_WIDE)
    zoom_factor: float = Field(default=1.0, ge=0.5, le=3.0)
    shake_intensity: float = Field(default=0.0, ge=0.0, le=1.0)


class ActorConfig(BaseModel):
    """Stickman actor appearance and stage configuration within a scene."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    actor_id: str = Field(default="actor_main", min_length=1)
    skin: CharacterSkin = Field(default=CharacterSkin.DARK_WUKONG)
    color: str = Field(default="#D92626", min_length=3)
    weapon: WeaponType = Field(default=WeaponType.RUYI_STAFF)
    display_name: str = Field(default="Ngộ Không Hắc Hóa", min_length=1)
    side: ActorSide = Field(default=ActorSide.LEFT)
    scale: float = Field(default=1.0, gt=0.1, le=5.0)

    @model_validator(mode="before")
    @classmethod
    def normalize_contract_aliases(cls, data: object) -> object:
        """Support both (skin, color) and (character_type, aura_color) from docs/04_data_contracts.md."""
        if isinstance(data, dict):
            copied = dict(data)
            if "character_type" in copied and "skin" not in copied:
                copied["skin"] = copied.pop("character_type")
            elif "character_type" in copied and "skin" in copied:
                copied.pop("character_type")

            if "aura_color" in copied and "color" not in copied:
                copied["color"] = copied.pop("aura_color")
            elif "aura_color" in copied and "color" in copied:
                copied.pop("aura_color")
            return copied
        return data

    @property
    def character_type(self) -> CharacterSkin:
        """Alias property matching docs/04_data_contracts.md."""
        return self.skin

    @property
    def aura_color(self) -> str:
        """Alias property matching docs/04_data_contracts.md."""
        return self.color


class SFXEvent(BaseModel):
    """Sound effect event triggered at a specific time offset inside a scene."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    sfx_name: str = Field(..., min_length=1, description="SFX identifier or filename (e.g. 'metal_weapon_clash')")
    time_offset: float = Field(default=0.0, ge=0.0, description="Offset in seconds from start of the scene (>= 0)")
    volume: float = Field(default=0.85, ge=0.0, le=1.0)

    @model_validator(mode="before")
    @classmethod
    def normalize_sfx_aliases(cls, data: object) -> object:
        """Support both (sfx_name/file_name, time_offset) and (sfx_type, offset_sec) from docs/04_data_contracts.md."""
        if isinstance(data, dict):
            copied = dict(data)
            for key in ("sfx_type", "file_name"):
                if key in copied and "sfx_name" not in copied:
                    copied["sfx_name"] = copied.pop(key)
                elif key in copied:
                    copied.pop(key)

            if "offset_sec" in copied and "time_offset" not in copied:
                copied["time_offset"] = copied.pop("offset_sec")
            elif "offset_sec" in copied:
                copied.pop("offset_sec")
            return copied
        return data

    @field_validator("sfx_name")
    @classmethod
    def validate_sfx_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("sfx_name cannot be blank")
        return cleaned

    @property
    def sfx_type(self) -> str:
        """Alias property matching docs/04_data_contracts.md."""
        return self.sfx_name

    @property
    def offset_sec(self) -> float:
        """Alias property matching docs/04_data_contracts.md."""
        return self.time_offset


class SceneSchema(BaseModel):
    """Strict data contract for a single animated scene passed across Parser -> Audio -> Animator -> Compositor."""

    model_config = ConfigDict(extra="forbid")

    scene_id: int = Field(..., gt=0, description="1-indexed scene sequence number (> 0)")
    narration_text: str = Field(..., min_length=1, description="Non-empty Vietnamese voiceover narration text")
    audio_duration_sec: float = Field(default=0.0, ge=0.0, description="Measured audio duration in seconds (>= 0)")
    voice_audio_path: Optional[str] = Field(default=None)
    background_state: BackgroundState = Field(default=BackgroundState.NORMAL_PAGE)
    actors: list[ActorConfig] = Field(default_factory=list, min_length=1)
    action_preset: ActionPreset = Field(default=ActionPreset.DARK_AURA_STANDOFF)
    camera_movement: CameraMovement = Field(default=CameraMovement.STATIC_WIDE)
    camera_config: Optional[CameraConfig] = Field(default=None)
    sfx_events: list[SFXEvent] = Field(default_factory=list)

    @field_validator("narration_text")
    @classmethod
    def validate_narration_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("narration_text cannot be empty or whitespace only")
        return cleaned


# Alias for compatibility with docs/04_data_contracts.md naming
ActorSpec = ActorConfig
SfxEvent = SFXEvent
