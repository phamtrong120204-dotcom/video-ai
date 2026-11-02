"""Script Parser Module for Dark Myth Stickman Auto-Studio."""

from app.modules.parser.gemini_parser import GeminiScriptParser
from app.modules.parser.hybrid_parser import HybridScriptParser
from app.modules.parser.rule_based import RuleBasedScriptParser

# Maintain backward compatibility for Phase 3 tests
from app.modules.parser.rule_based import RuleBasedScriptParser as StubScriptParser

# Default production parser
ScriptParser = HybridScriptParser

__all__ = [
    "RuleBasedScriptParser",
    "GeminiScriptParser",
    "HybridScriptParser",
    "StubScriptParser",
    "ScriptParser",
]
