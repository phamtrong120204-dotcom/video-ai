"""Gemini LLM Script Parser Engine using google-genai SDK."""

import json
import os
from typing import Optional

from app.core.config import get_config
from app.core.exceptions import ConfigurationError, ScriptParseError
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

logger = get_logger("gemini_parser")


class GeminiScriptParser(IScriptParser):
    """LLM-based Vietnamese script parser using official Google GenAI SDK with structured output."""

    SYSTEM_INSTRUCTION = """Bạn là Chuyên gia Phân tích Kịch bản Điện ảnh và Đạo diễn Hoạt hình Người Que Hắc Ám Tây Du (Dark Myth Stickman).
Nhiệm vụ của bạn là nhận kịch bản tiếng Việt thô và phân tích thành danh sách JSON các phân cảnh (SceneSchema).

BẮT BUỘC TUÂN THỦ CÁC QUY TẮC SAU:
1. Mỗi phân cảnh có thời lượng đọc phù hợp (1-2 câu hoàn chỉnh, 12-35 từ tiếng Việt). Không chia vụn câu văn.
2. Đánh số scene_id tuần tự từ 1.
3. Không bỏ sót bất kỳ tình tiết nào trong kịch bản gốc.
4. Chỉ sử dụng DUY NHẤT các giá trị Enum hợp lệ sau đây:
   - background_state: "clean_notebook", "ink_splattered", "torn_dark_myth", "heavenly_pressure"
   - actors[].skin: "dark_wukong", "erlang_shen", "celestial_general", "celestial_soldier_squad", "buddha_palm"
   - actors[].weapon: "ruyi_staff", "three_pointed_spear", "celestial_halberd", "giant_golden_palm", "unarmed"
   - actors[].side: "left", "right", "center", "top"
   - action_preset: "dark_aura_standoff", "heavy_charge_clash", "flurry_combo", "staff_vortex_sweep", "sky_leap_slam", "divine_eye_beam", "giant_palm_suppression", "knockback_recovery"
   - camera_movement: "static_wide", "zoom_in_dramatic", "zoom_punch_impact", "pan_vertical_down", "pan_vertical_up", "shake_heavy"
5. audio_duration_sec BẮT BUỘC đặt là 0.0 (chưa qua bước đo audio thực tế).
6. voice_audio_path đặt là null.
7. Trả về DUY NHẤT một mảng JSON thuần túy [ { ... }, { ... } ], không bọc trong markdown hoặc bất kỳ văn bản giải thích nào khác.
"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        cfg = get_config()
        self.api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY", cfg.gemini_api_key)
        self.model = model or getattr(cfg, "gemini_model", "gemini-2.5-flash")
        self._client = None

    def _get_client(self):
        """Lazily initialize Google GenAI Client."""
        if self._client is None:
            if not self.api_key or not self.api_key.strip():
                raise ConfigurationError("GEMINI_API_KEY is not configured or empty.")
            try:
                from google import genai
                from google.genai import types

                http_options = types.HttpOptions(timeout=15.0)
                self._client = genai.Client(api_key=self.api_key.strip(), http_options=http_options)
            except ImportError as e:
                raise ConfigurationError(f"Thư viện google-genai chưa được cài đặt: {e}") from e
        return self._client

    def parse(self, script_input: ScriptInput) -> list[SceneSchema]:
        """Call Gemini Flash to parse script into validated SceneSchema list."""
        raw_text = script_input.raw_script_text.strip()
        job_id = script_input.job_id

        if not raw_text:
            raise ScriptParseError("Kịch bản rỗng hoặc chỉ chứa khoảng trắng.", job_id=job_id)

        client = self._get_client()

        prompt = (
            f"Hãy phân tích kịch bản Hắc Ám Tây Du sau đây thành danh sách phân cảnh JSON chuẩn:\n\n"
            f"Tiêu đề: {script_input.title}\n"
            f"Nội dung kịch bản:\n{raw_text}\n"
        )

        try:
            logger.info(
                f"Calling Gemini API ({self.model}) to parse script...",
                extra={"job_id": job_id},
            )
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "system_instruction": self.SYSTEM_INSTRUCTION,
                    "response_mime_type": "application/json",
                    "temperature": 0.2,
                },
            )

            if not response or not response.text:
                raise ScriptParseError("Gemini API trả về nội dung rỗng.", job_id=job_id)

            response_text = response.text.strip()
            # Clean possible markdown wrapping if returned
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            parsed_data = json.loads(response_text)
            if not isinstance(parsed_data, list) or len(parsed_data) == 0:
                raise ScriptParseError("Gemini JSON không phải là mảng phân cảnh hoặc mảng rỗng.", job_id=job_id)

            scenes: list[SceneSchema] = []
            for idx, item in enumerate(parsed_data, start=1):
                # Ensure sequential scene_id
                item["scene_id"] = idx
                item["audio_duration_sec"] = 0.0
                item["voice_audio_path"] = None

                # Pydantic validation (strictly checks enums and field types)
                scene = SceneSchema.model_validate(item)
                scenes.append(scene)

            logger.info(
                f"GeminiScriptParser successfully parsed {len(scenes)} scenes.",
                extra={"job_id": job_id},
            )
            return scenes

        except json.JSONDecodeError as e:
            msg = f"Gemini trả về JSON không đúng cú pháp: {e}"
            logger.error(msg, extra={"job_id": job_id})
            raise ScriptParseError(msg, job_id=job_id) from e
        except Exception as e:
            msg = f"Lỗi gọi Gemini API ({type(e).__name__}): {e}"
            logger.error(msg, extra={"job_id": job_id})
            raise ScriptParseError(msg, job_id=job_id) from e
