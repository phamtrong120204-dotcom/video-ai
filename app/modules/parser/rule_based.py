"""Deterministic Rule-Based Vietnamese Script Parser Engine (Offline)."""

import re
from typing import Optional

from app.core.exceptions import ScriptParseError
from app.core.logger import get_logger
from app.interfaces.base_parser import IScriptParser
from app.schemas.scene_schema import (
    ActionPreset,
    ActorConfig,
    ActorSide,
    BackgroundState,
    CameraMovement,
    CharacterSkin,
    SceneSchema,
    SFXEvent,
    WeaponType,
)
from app.schemas.script_schema import ScriptInput

logger = get_logger("rule_based_parser")


class RuleBasedScriptParser(IScriptParser):
    """Deterministic, 100% offline Vietnamese NLP parser converting ScriptInput into SceneSchema[]."""

    # Keyword mappings for Character recognition
    CHARACTER_KEYWORDS = [
        (
            CharacterSkin.DARK_WUKONG,
            "Ngộ Không Hắc Hóa",
            "#D92626",
            WeaponType.RUYI_STAFF,
            ActorSide.LEFT,
            1.0,
            ["ngộ không", "hầu vương", "tôn ngộ không", "mỹ hầu vương", "tề thiên", "thiết bảng", "kim cô"],
        ),
        (
            CharacterSkin.ERLANG_SHEN,
            "Nhị Lang Thần",
            "#E6B800",
            WeaponType.THREE_POINTED_SPEAR,
            ActorSide.RIGHT,
            1.05,
            ["nhị lang", "dương tiễn", "tam tiêm đảo", "thiên nhãn", "chiến thần"],
        ),
        (
            CharacterSkin.CELESTIAL_GENERAL,
            "Thiên Tướng",
            "#63B3ED",
            WeaponType.CELESTIAL_HALBERD,
            ActorSide.RIGHT,
            1.25,
            ["thiên tướng", "cự linh thần", "thiên vương"],
        ),
        (
            CharacterSkin.CELESTIAL_SOLDIER_SQUAD,
            "Thiên Binh",
            "#2D3748",
            WeaponType.CELESTIAL_HALBERD,
            ActorSide.RIGHT,
            0.95,
            ["thiên binh", "binh lính", "vạn binh", "quân đoàn thiên đình", "thiên quân"],
        ),
        (
            CharacterSkin.BUDDHA_PALM,
            "Bàn Tay Phật Tổ",
            "#F6AD55",
            WeaponType.GIANT_GOLDEN_PALM,
            ActorSide.TOP,
            3.5,
            ["bàn tay phật", "như lai", "phật tổ", "chưởng lực", "kim quang phật", "ấn ký chữ vạn"],
        ),
    ]

    # Keyword mappings for ActionPreset recognition
    ACTION_KEYWORDS = [
        (
            ActionPreset.GIANT_PALM_SUPPRESSION,
            ["bàn tay phật", "như lai thần chưởng", "giáng xuống", "trấn áp", "đè bẹp", "áp chế", "lún sâu"],
        ),
        (
            ActionPreset.DIVINE_EYE_BEAM,
            ["thiên nhãn", "bắn tia", "tia sáng", "chùm sáng", "laser", "kim quang xạ"],
        ),
        (
            ActionPreset.SKY_LEAP_SLAM,
            ["bật nhảy", "nhảy vọt", "bổ thẳng đứng", "từ trên cao giáng xuống", "phóng đại gậy", "đập nát đất", "bổ gậy"],
        ),
        (
            ActionPreset.STAFF_VORTEX_SWEEP,
            ["xoay gậy", "quét sạch", "cơn lốc", "vòng xoáy", "xoay tròn", "đánh văng", "quét ngang"],
        ),
        (
            ActionPreset.FLURRY_COMBO,
            ["liên hoàn", "tốc độ cao", "loạn đả", "chém liên tiếp", "siêu thanh", "hàng chục bóng", "dồn dập", "mưa đòn"],
        ),
        (
            ActionPreset.KNOCKBACK_RECOVERY,
            ["bị đánh văng", "hất văng", "bật lùi", "trượt dài", "cắm vũ khí", "hồi chiêu", "phanh lại", "ngã văng"],
        ),
        (
            ActionPreset.HEAVY_CHARGE_CLASH,
            ["lao tới", "lao vút", "bổ mạnh", "bổ xuống", "giao binh", "tóe lửa", "đỡ đòn", "va chạm", "đâm tới", "xung phong", "chém xuống"],
        ),
        (
            ActionPreset.DARK_AURA_STANDOFF,
            ["đối diện", "đối đầu", "khí thế", "đứng nhìn", "thế thủ", "hắc khí", "lườm", "đối chọi", "tĩnh lặng", "sát khí"],
        ),
    ]

    # Keyword mappings for BackgroundState recognition
    BACKGROUND_KEYWORDS = [
        (
            BackgroundState.HEAVENLY_PRESSURE,
            ["vàng kim", "phật", "thiên đình", "uy nghiêm", "kim quang", "ánh vàng"],
        ),
        (
            BackgroundState.TORN_DARK_MYTH,
            ["rách", "nứt", "hắc ám", "đen tối", "tàn tro", "hoang tàn", "nhuốm máu"],
        ),
        (
            BackgroundState.INK_SPLATTERED,
            ["mực bắn", "tóe lửa", "mực tung tóe", "vết mực", "nhuốm mực", "mực đen"],
        ),
        (
            BackgroundState.CLEAN_NOTEBOOK,
            ["trang giấy", "vở học sinh", "nguyên vẹn", "dòng kẻ"],
        ),
    ]

    # Keyword mappings for CameraMovement
    CAMERA_MAPPINGS = {
        ActionPreset.GIANT_PALM_SUPPRESSION: CameraMovement.PAN_VERTICAL_UP,
        ActionPreset.SKY_LEAP_SLAM: CameraMovement.PAN_VERTICAL_DOWN,
        ActionPreset.HEAVY_CHARGE_CLASH: CameraMovement.ZOOM_PUNCH_IMPACT,
        ActionPreset.FLURRY_COMBO: CameraMovement.SHAKE_HEAVY,
        ActionPreset.DIVINE_EYE_BEAM: CameraMovement.SHAKE_HEAVY,
        ActionPreset.DARK_AURA_STANDOFF: CameraMovement.ZOOM_IN_DRAMATIC,
        ActionPreset.KNOCKBACK_RECOVERY: CameraMovement.ZOOM_IN_DRAMATIC,
        ActionPreset.STAFF_VORTEX_SWEEP: CameraMovement.STATIC_WIDE,
    }

    # Default SFX generation per action
    SFX_MAPPINGS = {
        ActionPreset.HEAVY_CHARGE_CLASH: [
            SFXEvent(sfx_name="whoosh_heavy", time_offset=0.2, volume=0.85),
            SFXEvent(sfx_name="metal_weapon_clash", time_offset=0.5, volume=0.95),
        ],
        ActionPreset.FLURRY_COMBO: [
            SFXEvent(sfx_name="staff_whoosh_fast", time_offset=0.15, volume=0.8),
            SFXEvent(sfx_name="multi_clash_rapid", time_offset=0.55, volume=0.9),
        ],
        ActionPreset.STAFF_VORTEX_SWEEP: [
            SFXEvent(sfx_name="vortex_spin_whoosh", time_offset=0.3, volume=0.9),
            SFXEvent(sfx_name="body_impact_sweep", time_offset=0.7, volume=0.85),
        ],
        ActionPreset.SKY_LEAP_SLAM: [
            SFXEvent(sfx_name="sky_leap_whoosh", time_offset=0.2, volume=0.85),
            SFXEvent(sfx_name="earth_shatter_slam", time_offset=0.6, volume=1.0),
        ],
        ActionPreset.DIVINE_EYE_BEAM: [
            SFXEvent(sfx_name="divine_beam_charge", time_offset=0.2, volume=0.85),
            SFXEvent(sfx_name="laser_clash_sizzle", time_offset=0.5, volume=0.95),
        ],
        ActionPreset.GIANT_PALM_SUPPRESSION: [
            SFXEvent(sfx_name="heavenly_thunder_rumble", time_offset=0.2, volume=0.9),
            SFXEvent(sfx_name="giant_palm_boom", time_offset=0.7, volume=1.0),
        ],
        ActionPreset.KNOCKBACK_RECOVERY: [
            SFXEvent(sfx_name="heavy_body_hit", time_offset=0.2, volume=0.9),
            SFXEvent(sfx_name="weapon_ground_scrape", time_offset=0.6, volume=0.85),
        ],
        ActionPreset.DARK_AURA_STANDOFF: [
            SFXEvent(sfx_name="dark_aura_hum", time_offset=0.3, volume=0.75),
        ],
    }

    def parse(self, script_input: ScriptInput) -> list[SceneSchema]:
        """Parse raw Vietnamese script into validated SceneSchema objects."""
        raw_text = script_input.raw_script_text.strip()
        job_id = script_input.job_id

        if not raw_text:
            raise ScriptParseError("Kịch bản rỗng hoặc chỉ chứa khoảng trắng.", job_id=job_id)

        if len(raw_text) < 10:
            raise ScriptParseError(
                f"Kịch bản quá ngắn ({len(raw_text)} ký tự). Yêu cầu tối thiểu 10 ký tự.",
                job_id=job_id,
            )

        if len(raw_text) > 6000:
            raise ScriptParseError(
                f"Kịch bản vượt quá giới hạn tối đa ({len(raw_text)}/6000 ký tự).",
                job_id=job_id,
            )

        # 1. Segment script into scene narration texts
        segmented_texts = self._segment_into_scenes(raw_text, job_id=job_id)

        if not segmented_texts:
            raise ScriptParseError("Không thể phân tách kịch bản thành phân cảnh hợp lệ.", job_id=job_id)

        scenes: list[SceneSchema] = []
        for idx, text in enumerate(segmented_texts, start=1):
            scene = self._build_scene(scene_id=idx, narration_text=text, job_id=job_id)
            scenes.append(scene)

        logger.info(
            f"RuleBasedScriptParser successfully parsed {len(scenes)} scenes.",
            extra={"job_id": job_id},
        )
        return scenes

    def _segment_into_scenes(self, raw_text: str, job_id: str) -> list[str]:
        """Segment raw text using explicit headings or sentence/paragraph heuristics."""
        # Pattern matching: Cảnh 1:, Phân cảnh 2:, Đoạn 3:, Scene 4:
        heading_pattern = re.compile(
            r"(?:^|\n)\s*(?:cảnh|phân\s*cảnh|đoạn|scene)\s*(\d+)\s*[:.-]\s*",
            flags=re.IGNORECASE,
        )

        matches = list(heading_pattern.finditer(raw_text))

        if matches:
            # Case A: Explicit scene headings detected
            scenes_text: list[str] = []
            for i, match in enumerate(matches):
                start_content = match.end()
                end_content = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
                content = raw_text[start_content:end_content].strip()
                # Clean multiple internal newlines
                content = re.sub(r"\s+", " ", content).strip()
                if content:
                    scenes_text.append(content)
            if scenes_text:
                return scenes_text

        # Case B: No explicit headings - Segment by paragraph & sentence boundaries
        # Step B1: Split into paragraphs
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", raw_text) if p.strip()]

        # Step B2: Split each paragraph into complete sentences
        all_sentences: list[str] = []
        for p in paragraphs:
            # Sentence boundary split while retaining punctuation
            sentences = re.split(r"(?<=[.!?…])\s+", p)
            for s in sentences:
                cleaned_s = re.sub(r"\s+", " ", s).strip()
                if cleaned_s:
                    all_sentences.append(cleaned_s)

        if not all_sentences:
            return [re.sub(r"\s+", " ", raw_text).strip()]

        # Step B3: Group sentences into scenes of ~12 to 35 words
        scenes_text = []
        current_group: list[str] = []
        current_word_count = 0

        for sentence in all_sentences:
            words = sentence.split()
            word_count = len(words)

            # If adding this sentence keeps word count <= 35, or if current group is empty:
            if current_word_count == 0 or (current_word_count + word_count <= 35):
                current_group.append(sentence)
                current_word_count += word_count
            else:
                # Flush current group as a scene
                scenes_text.append(" ".join(current_group))
                current_group = [sentence]
                current_word_count = word_count

        if current_group:
            scenes_text.append(" ".join(current_group))

        return scenes_text

    def _build_scene(self, scene_id: int, narration_text: str, job_id: str) -> SceneSchema:
        """Construct a validated SceneSchema from narration text using NLP keywords."""
        lower_text = narration_text.lower()

        # 1. Recognize Characters
        actors: list[ActorConfig] = []
        matched_skins: set[CharacterSkin] = set()

        for skin, display_name, color, weapon, side, scale, keywords in self.CHARACTER_KEYWORDS:
            for kw in keywords:
                if kw in lower_text:
                    if skin not in matched_skins:
                        matched_skins.add(skin)
                        actors.append(
                            ActorConfig(
                                actor_id=f"{skin.value}_{scene_id}",
                                skin=skin,
                                color=color,
                                weapon=weapon,
                                display_name=display_name,
                                side=side,
                                scale=scale,
                            )
                        )
                    break

        # Safe Default: If no characters matched, default to Dark Wukong
        if not actors:
            logger.debug(
                f"Scene {scene_id}: No character detected, using default Dark Wukong.",
                extra={"job_id": job_id},
            )
            actors.append(
                ActorConfig(
                    actor_id=f"dark_wukong_{scene_id}",
                    skin=CharacterSkin.DARK_WUKONG,
                    color="#D92626",
                    weapon=WeaponType.RUYI_STAFF,
                    display_name="Ngộ Không Hắc Hóa",
                    side=ActorSide.LEFT,
                    scale=1.0,
                )
            )

        # If only 1 actor and it is an enemy, ensure Dark Wukong is present as the protagonist
        if len(actors) == 1 and actors[0].skin in (CharacterSkin.ERLANG_SHEN, CharacterSkin.CELESTIAL_GENERAL, CharacterSkin.CELESTIAL_SOLDIER_SQUAD):
            actors.insert(
                0,
                ActorConfig(
                    actor_id=f"dark_wukong_{scene_id}",
                    skin=CharacterSkin.DARK_WUKONG,
                    color="#D92626",
                    weapon=WeaponType.RUYI_STAFF,
                    display_name="Ngộ Không Hắc Hóa",
                    side=ActorSide.LEFT,
                    scale=1.0,
                ),
            )

        # If only 1 actor and it's on the left (Dark Wukong), check if context implies a standoff/clash with Erlang Shen
        elif len(actors) == 1 and actors[0].skin == CharacterSkin.DARK_WUKONG:
            # If clash keywords exist, add Erlang Shen as sparring opponent
            if any(k in lower_text for k in ["bổ kiếm", "tam tiêm", "nhị lang", "đối diện", "va chạm", "nghênh chiến", "giao chiến", "hai bên", "kinh thiên"]):
                actors.append(
                    ActorConfig(
                        actor_id=f"erlang_shen_{scene_id}",
                        skin=CharacterSkin.ERLANG_SHEN,
                        color="#E6B800",
                        weapon=WeaponType.THREE_POINTED_SPEAR,
                        display_name="Nhị Lang Thần",
                        side=ActorSide.RIGHT,
                        scale=1.05,
                    )
                )

        # 2. Recognize Action Preset
        action_preset: Optional[ActionPreset] = None
        for preset, keywords in self.ACTION_KEYWORDS:
            for kw in keywords:
                if kw in lower_text:
                    action_preset = preset
                    break
            if action_preset:
                break

        if not action_preset:
            logger.debug(
                f"Scene {scene_id}: No action preset detected, using default DARK_AURA_STANDOFF.",
                extra={"job_id": job_id},
            )
            action_preset = ActionPreset.DARK_AURA_STANDOFF

        # 3. Recognize Background State
        background_state: Optional[BackgroundState] = None
        for bg_state, keywords in self.BACKGROUND_KEYWORDS:
            for kw in keywords:
                if kw in lower_text:
                    background_state = bg_state
                    break
            if background_state:
                break

        if not background_state:
            # Default progression based on scene sequence or default clean notebook
            if action_preset in (ActionPreset.HEAVY_CHARGE_CLASH, ActionPreset.FLURRY_COMBO):
                background_state = BackgroundState.INK_SPLATTERED
            elif action_preset == ActionPreset.GIANT_PALM_SUPPRESSION:
                background_state = BackgroundState.HEAVENLY_PRESSURE
            elif action_preset in (ActionPreset.SKY_LEAP_SLAM, ActionPreset.KNOCKBACK_RECOVERY):
                background_state = BackgroundState.TORN_DARK_MYTH
            else:
                background_state = BackgroundState.CLEAN_NOTEBOOK

        # 4. Recognize Camera Movement
        camera_movement = self.CAMERA_MAPPINGS.get(action_preset, CameraMovement.STATIC_WIDE)

        # 5. Generate SFX Events
        sfx_events = [
            SFXEvent(sfx_name=e.sfx_name, time_offset=e.time_offset, volume=e.volume)
            for e in self.SFX_MAPPINGS.get(action_preset, [])
        ]

        # 6. Build SceneSchema
        return SceneSchema(
            scene_id=scene_id,
            narration_text=narration_text,
            audio_duration_sec=0.0,  # MUST BE 0.0 before AudioEngine measures it
            voice_audio_path=None,
            background_state=background_state,
            actors=actors,
            action_preset=action_preset,
            camera_movement=camera_movement,
            sfx_events=sfx_events,
        )
