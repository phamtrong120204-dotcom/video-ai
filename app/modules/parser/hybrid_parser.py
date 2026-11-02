"""Hybrid Script Parser Orchestrator (Prioritizes Gemini with Rule-Based Fallback)."""

import os
from typing import Optional

from app.core.config import get_config
from app.core.logger import get_logger
from app.interfaces.base_parser import IScriptParser
from app.modules.parser.gemini_parser import GeminiScriptParser
from app.modules.parser.rule_based import RuleBasedScriptParser
from app.schemas.scene_schema import SceneSchema
from app.schemas.script_schema import ScriptInput

logger = get_logger("hybrid_parser")


class HybridScriptParser(IScriptParser):
    """Orchestrates script parsing by trying Gemini Flash first, falling back to Rule-Based parsing."""

    def __init__(
        self,
        gemini_parser: Optional[IScriptParser] = None,
        rule_based_parser: Optional[IScriptParser] = None,
    ) -> None:
        self.gemini_parser = gemini_parser
        self.rule_based_parser = rule_based_parser or RuleBasedScriptParser()

    def parse(self, script_input: ScriptInput) -> list[SceneSchema]:
        """Parse script using Gemini if API key is present, otherwise or upon error fallback to Rule-Based."""
        job_id = script_input.job_id
        cfg = get_config()
        api_key = os.getenv("GEMINI_API_KEY", cfg.gemini_api_key)

        # Check if Gemini parser should be used
        if api_key and api_key.strip():
            parser = self.gemini_parser or GeminiScriptParser(api_key=api_key.strip())
            try:
                logger.info(
                    "GEMINI_API_KEY detected. Attempting AI parsing via Gemini Flash...",
                    extra={"job_id": job_id},
                )
                scenes = parser.parse(script_input)
                if scenes and len(scenes) > 0:
                    logger.info(
                        f"Gemini parsing succeeded with {len(scenes)} scenes.",
                        extra={"job_id": job_id},
                    )
                    return scenes
            except Exception as e:
                logger.warning(
                    f"Gemini parsing failed ({type(e).__name__}: {e}). Gracefully falling back to RuleBasedScriptParser.",
                    extra={"job_id": job_id},
                )

        # Fallback to deterministic Rule-Based parser
        logger.info(
            "Using deterministic RuleBasedScriptParser (offline mode)...",
            extra={"job_id": job_id},
        )
        return self.rule_based_parser.parse(script_input)
