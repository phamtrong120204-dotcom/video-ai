"""Comprehensive Automated Test Suite for Stage 4.1 Script Parser Engine."""

import json
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.core.exceptions import ConfigurationError, ScriptParseError
from app.modules.parser.gemini_parser import GeminiScriptParser
from app.modules.parser.hybrid_parser import HybridScriptParser
from app.modules.parser.rule_based import RuleBasedScriptParser
from app.schemas.scene_schema import (
    ActionPreset,
    BackgroundState,
    CameraMovement,
    CharacterSkin,
    SceneSchema,
)
from app.schemas.script_schema import ScriptInput


# ---------------------------------------------------------------------------
# RULE-BASED PARSER TESTS
# ---------------------------------------------------------------------------


def test_parser_with_explicit_scene_headings():
    """Case 1: Script with explicit headings (Cảnh 1:, Cảnh 2:, Phân cảnh 3:)."""
    parser = RuleBasedScriptParser()
    raw = (
        "Cảnh 1: Giữa trang giấy vở nhuốm mực đen, Tôn Ngộ Không mắt đỏ rực đứng đối diện Nhị Lang Thần.\n"
        "Cảnh 2: Nhị Lang Thần thét lớn lao tới bổ mạnh Tam Tiêm Đảo làm tóe lửa khắp mặt giấy.\n"
        "Phân cảnh 3: Từ đỉnh trời cao, Bàn tay Phật Tổ khổng lồ giáng xuống trấn áp cả không gian!"
    )
    payload = ScriptInput(raw_script_text=raw, title="Đại Chiến Thiên Đình")
    scenes = parser.parse(payload)

    assert len(scenes) == 3
    assert [s.scene_id for s in scenes] == [1, 2, 3]
    # Check that scene prefixes were stripped from narration
    assert not scenes[0].narration_text.lower().startswith("cảnh 1:")
    assert "tôn ngộ không" in scenes[0].narration_text.lower()
    assert scenes[0].audio_duration_sec == 0.0
    assert scenes[0].voice_audio_path is None


def test_parser_without_scene_headings():
    """Case 2: Script without explicit scene headings (segmented by sentences & word count)."""
    parser = RuleBasedScriptParser()
    raw = (
        "Giữa trang giấy vở nhuốm mực đen u ám, Tôn Ngộ Không mắt đỏ rực cầm Thiết Bảng Như Ý đứng gầm thét. "
        "Nhị Lang Thần Dương Tiễn từ xa cầm Tam Tiêm Đảo lao vút tới bổ mạnh xuống. "
        "Ngộ Không nhảy vọt lên cao rồi bổ thẳng gậy sắt xuống mặt đất làm rách toạc cả trang giấy."
    )
    payload = ScriptInput(raw_script_text=raw, title="Chiến Trận Không Tiêu Đề")
    scenes = parser.parse(payload)

    assert len(scenes) >= 2
    assert [s.scene_id for s in scenes] == list(range(1, len(scenes) + 1))
    for scene in scenes:
        assert isinstance(scene, SceneSchema)
        assert len(scene.narration_text.strip()) > 0
        assert scene.audio_duration_sec == 0.0


def test_parser_vietnamese_diacritics_integrity():
    """Case 3: Vietnamese diacritics are preserved with 100% fidelity."""
    parser = RuleBasedScriptParser()
    raw = "Cảnh 1: Thiết Bảng Như Ý xoay tít mù mịt, quét sạch ngàn vạn thiên binh rơi rụng tơi bời khắp trang giấy."
    payload = ScriptInput(raw_script_text=raw)
    scenes = parser.parse(payload)

    assert len(scenes) == 1
    # Check diacritic preservation
    assert "Thiết Bảng Như Ý" in scenes[0].narration_text
    assert "quét sạch" in scenes[0].narration_text


def test_parser_multi_paragraph_and_multi_sentence():
    """Case 4: Multi-paragraph input handles blank lines and complex structures."""
    parser = RuleBasedScriptParser()
    raw = """
    Tôn Ngộ Không mắt rực lửa đứng sừng sững giữa trang giấy vở kẻ ngang. Hắc khí bao quanh thân thể cuồn cuộn như mây đen bão tố.

    Nhị Lang Thần mở Thiên Nhãn bắn ra chùm tia sáng vàng kim dữ dội. Chùm sáng xé toạc không gian giấy vở lao thẳng về phía Ngộ Không.

    Ngộ Không xoay gậy tạo cơn lốc cực lớn đánh văng toán thiên binh ra rìa trang giấy!
    """
    payload = ScriptInput(raw_script_text=raw)
    scenes = parser.parse(payload)

    assert len(scenes) >= 3
    # Check sequential IDs
    assert [s.scene_id for s in scenes] == list(range(1, len(scenes) + 1))


def test_parser_recognizes_multiple_characters():
    """Case 5: Recognizes dark_wukong, erlang_shen, celestial_general, celestial_soldier_squad, buddha_palm."""
    parser = RuleBasedScriptParser()

    # 1. Wukong & Erlang
    s1 = parser.parse(ScriptInput(raw_script_text="Cảnh 1: Ngộ Không và Nhị Lang Thần Dương Tiễn đối đầu kịch liệt."))[0]
    skins1 = [a.skin for a in s1.actors]
    assert CharacterSkin.DARK_WUKONG in skins1
    assert CharacterSkin.ERLANG_SHEN in skins1

    # 2. Celestial General & Soldiers
    s2 = parser.parse(ScriptInput(raw_script_text="Cảnh 1: Thiên Tướng chỉ huy vạn thiên binh ùa tới vây hãm."))[0]
    skins2 = [a.skin for a in s2.actors]
    assert CharacterSkin.CELESTIAL_GENERAL in skins2
    assert CharacterSkin.CELESTIAL_SOLDIER_SQUAD in skins2

    # 3. Buddha Palm
    s3 = parser.parse(ScriptInput(raw_script_text="Cảnh 1: Bàn tay Phật Tổ khổng lồ từ trời cao giáng xuống."))[0]
    skins3 = [a.skin for a in s3.actors]
    assert CharacterSkin.BUDDHA_PALM in skins3


def test_parser_recognizes_distinct_action_presets():
    """Case 6: Recognizes distinct Dark Myth combat action presets."""
    parser = RuleBasedScriptParser()

    mapping = [
        ("Ngộ Không đứng đối diện tỏa hắc khí uy nghiêm.", ActionPreset.DARK_AURA_STANDOFF),
        ("Nhị Lang Thần lao tới bổ mạnh giáo xuống làm tóe lửa giao binh.", ActionPreset.HEAVY_CHARGE_CLASH),
        ("Tung ra chuỗi đòn liên hoàn dồn dập tốc độ cao.", ActionPreset.FLURRY_COMBO),
        ("Ngộ Không xoay gậy tạo cơn lốc quét sạch đội hình quân địch.", ActionPreset.STAFF_VORTEX_SWEEP),
        ("Ngộ Không bật nhảy vọt lên rồi bổ thẳng đứng gậy sắt xuống đất.", ActionPreset.SKY_LEAP_SLAM),
        ("Nhị Lang Thần mở Thiên Nhãn bắn tia chùm sáng vàng kim.", ActionPreset.DIVINE_EYE_BEAM),
        ("Bàn tay Phật Tổ từ trên trời giáng xuống trấn áp tất cả.", ActionPreset.GIANT_PALM_SUPPRESSION),
        ("Ngộ Không bị hất văng trượt dài trên mặt giấy rồi phanh lại.", ActionPreset.KNOCKBACK_RECOVERY),
    ]

    for text, expected_preset in mapping:
        scenes = parser.parse(ScriptInput(raw_script_text=f"Cảnh 1: {text}"))
        assert scenes[0].action_preset == expected_preset, f"Failed for text: {text}"


def test_parser_distinguishes_similar_keywords():
    """Case 7: Similar keywords do not cause misclassification."""
    parser = RuleBasedScriptParser()

    # "bổ thẳng đứng gậy" -> SKY_LEAP_SLAM, not HEAVY_CHARGE_CLASH
    s1 = parser.parse(ScriptInput(raw_script_text="Cảnh 1: Ngộ Không nhảy vọt lên cao bổ thẳng đứng gậy sắt xuống đất."))[0]
    assert s1.action_preset == ActionPreset.SKY_LEAP_SLAM

    # "xoay gậy quét sạch" -> STAFF_VORTEX_SWEEP, not FLURRY_COMBO
    s2 = parser.parse(ScriptInput(raw_script_text="Cảnh 1: Ngộ Không xoay gậy vòng xoáy quét sạch hàng vạn thiên binh."))[0]
    assert s2.action_preset == ActionPreset.STAFF_VORTEX_SWEEP


def test_parser_rejects_empty_or_too_short_script():
    """Case 8 & 9: Reject empty, whitespace-only, or under 10 chars."""
    parser = RuleBasedScriptParser()

    with pytest.raises(ValidationError):
        ScriptInput(raw_script_text="")

    with pytest.raises(ValidationError):
        ScriptInput(raw_script_text="   \n   ")

    with pytest.raises(ValidationError):
        ScriptInput(raw_script_text="Quá ngắn")


def test_parser_handles_length_boundary():
    """Case 9: Character length boundary (up to 6000 chars valid)."""
    parser = RuleBasedScriptParser()
    valid_text = "Cảnh 1: Tôn Ngộ Không đại chiến Nhị Lang Thần. " * 30
    assert len(valid_text) > 500 and len(valid_text) < 6000
    scenes = parser.parse(ScriptInput(raw_script_text=valid_text))
    assert len(scenes) > 0


def test_parser_preserves_text_and_no_hallucinated_duration():
    """Check text completeness and audio_duration_sec == 0.0."""
    parser = RuleBasedScriptParser()
    raw = (
        "Cảnh 1: Giữa trang giấy vở học sinh, Ngộ Không đứng đối diện Nhị Lang Thần.\n"
        "Cảnh 2: Hai bên lao vào giao chiến tóe lửa khắp nơi.\n"
        "Cảnh 3: Bàn tay Phật Tổ từ trên mây giáng xuống trấn áp."
    )
    scenes = parser.parse(ScriptInput(raw_script_text=raw))
    assert len(scenes) == 3
    for s in scenes:
        assert s.audio_duration_sec == 0.0
        assert s.voice_audio_path is None
        assert len(s.actors) >= 1
        assert s.action_preset in list(ActionPreset)
        assert s.background_state in list(BackgroundState)
        assert s.camera_movement in list(CameraMovement)


# ---------------------------------------------------------------------------
# GEMINI PARSER MOCKED TESTS
# ---------------------------------------------------------------------------


def test_gemini_parser_missing_api_key_raises_configuration_error():
    """Case 14: Gemini parser raises ConfigurationError when API key is missing."""
    with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
        parser = GeminiScriptParser(api_key="")
        with pytest.raises(ConfigurationError):
            parser.parse(ScriptInput(raw_script_text="Cảnh 1: Tôn Ngộ Không đại náo thiên cung."))


def test_gemini_parser_valid_structured_json():
    """Gemini parser successfully parses valid structured JSON."""
    mock_json_response = json.dumps([
        {
            "scene_id": 1,
            "narration_text": "Tôn Ngộ Không mắt đỏ rực đứng đối diện Nhị Lang Thần.",
            "background_state": "clean_notebook",
            "actors": [
                {
                    "actor_id": "wukong_1",
                    "skin": "dark_wukong",
                    "color": "#D92626",
                    "weapon": "ruyi_staff",
                    "display_name": "Ngộ Không Hắc Hóa",
                    "side": "left",
                    "scale": 1.0,
                },
                {
                    "actor_id": "erlang_1",
                    "skin": "erlang_shen",
                    "color": "#E6B800",
                    "weapon": "three_pointed_spear",
                    "display_name": "Nhị Lang Thần",
                    "side": "right",
                    "scale": 1.05,
                },
            ],
            "action_preset": "dark_aura_standoff",
            "camera_movement": "zoom_in_dramatic",
            "sfx_events": [{"sfx_name": "dark_aura_hum", "time_offset": 0.5, "volume": 0.8}],
        }
    ])

    parser = GeminiScriptParser(api_key="fake_test_key")
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = mock_json_response
    mock_client.models.generate_content.return_value = mock_response

    with patch.object(parser, "_get_client", return_value=mock_client):
        scenes = parser.parse(ScriptInput(raw_script_text="Cảnh 1: Ngộ Không đối diện Nhị Lang Thần."))
        assert len(scenes) == 1
        assert scenes[0].scene_id == 1
        assert scenes[0].action_preset == ActionPreset.DARK_AURA_STANDOFF
        assert scenes[0].actors[0].skin == CharacterSkin.DARK_WUKONG
        assert scenes[0].audio_duration_sec == 0.0


def test_gemini_parser_handles_malformed_json():
    """Case 11: Gemini returns malformed JSON -> raises ScriptParseError."""
    parser = GeminiScriptParser(api_key="fake_test_key")
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "NOT_A_VALID_JSON_STRING {{{[[["
    mock_client.models.generate_content.return_value = mock_response

    with patch.object(parser, "_get_client", return_value=mock_client):
        with pytest.raises(ScriptParseError) as exc_info:
            parser.parse(ScriptInput(raw_script_text="Cảnh 1: Tôn Ngộ Không đại náo thiên cung."))
        assert "JSON không đúng cú pháp" in str(exc_info.value)


def test_gemini_parser_handles_timeout():
    """Case 12: Gemini API call times out -> raises ScriptParseError."""
    parser = GeminiScriptParser(api_key="fake_test_key")
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = TimeoutError("Deadline exceeded")

    with patch.object(parser, "_get_client", return_value=mock_client):
        with pytest.raises(ScriptParseError) as exc_info:
            parser.parse(ScriptInput(raw_script_text="Cảnh 1: Tôn Ngộ Không đại náo thiên cung."))
        assert "Lỗi gọi Gemini API" in str(exc_info.value)


def test_gemini_parser_handles_quota_exceeded():
    """Case 13: Gemini API quota exceeded -> raises ScriptParseError."""
    parser = GeminiScriptParser(api_key="fake_test_key")
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("ResourceExhausted: 429 Quota Exceeded")

    with patch.object(parser, "_get_client", return_value=mock_client):
        with pytest.raises(ScriptParseError) as exc_info:
            parser.parse(ScriptInput(raw_script_text="Cảnh 1: Tôn Ngộ Không đại náo thiên cung."))
        assert "ResourceExhausted" in str(exc_info.value)


def test_gemini_parser_rejects_invalid_enum():
    """Case 10: Gemini returns an invalid/hallucinated Enum value -> rejected by Pydantic."""
    mock_invalid_enum_json = json.dumps([
        {
            "scene_id": 1,
            "narration_text": "Cảnh đánh nhau.",
            "background_state": "INVALID_HALLUCINATED_BG",
            "actors": [{"skin": "dark_wukong"}],
            "action_preset": "dark_aura_standoff",
            "camera_movement": "static_wide",
        }
    ])

    parser = GeminiScriptParser(api_key="fake_test_key")
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = mock_invalid_enum_json
    mock_client.models.generate_content.return_value = mock_response

    with patch.object(parser, "_get_client", return_value=mock_client):
        with pytest.raises(ScriptParseError) as exc_info:
            parser.parse(ScriptInput(raw_script_text="Cảnh 1: Tôn Ngộ Không đại náo thiên cung."))
        assert "ValidationError" in str(exc_info.value)


# ---------------------------------------------------------------------------
# HYBRID PARSER FALLBACK TESTS
# ---------------------------------------------------------------------------


def test_hybrid_parser_falls_back_when_no_api_key():
    """Case 14 & 15: Hybrid falls back to RuleBased when no GEMINI_API_KEY is present."""
    with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
        hybrid = HybridScriptParser()
        raw = "Cảnh 1: Ngộ Không mắt đỏ rực đứng đối diện Nhị Lang Thần."
        scenes = hybrid.parse(ScriptInput(raw_script_text=raw))
        assert len(scenes) == 1
        assert scenes[0].action_preset == ActionPreset.DARK_AURA_STANDOFF


def test_hybrid_parser_falls_back_when_gemini_fails():
    """Case 15: Hybrid falls back to RuleBased when Gemini raises an exception."""
    mock_gemini = MagicMock(spec=GeminiScriptParser)
    mock_gemini.parse.side_effect = ScriptParseError("Gemini Server 500 error")

    mock_rule_based = RuleBasedScriptParser()

    with patch.dict("os.environ", {"GEMINI_API_KEY": "dummy_key"}):
        hybrid = HybridScriptParser(gemini_parser=mock_gemini, rule_based_parser=mock_rule_based)
        raw = "Cảnh 1: Ngộ Không lao vút tới bổ mạnh gậy sắt vào Tam Tiêm Đảo làm tóe lửa."
        scenes = hybrid.parse(ScriptInput(raw_script_text=raw))

        assert len(scenes) == 1
        assert scenes[0].action_preset == ActionPreset.HEAVY_CHARGE_CLASH
        mock_gemini.parse.assert_called_once()
