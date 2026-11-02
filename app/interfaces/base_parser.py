"""Abstract Interface for Script Parser Engine (IScriptParser)."""

from abc import ABC, abstractmethod

from app.schemas.scene_schema import SceneSchema
from app.schemas.script_schema import ScriptInput


class IScriptParser(ABC):
    """Contract for decomposing raw Vietnamese scripts into validated SceneSchema objects."""

    @abstractmethod
    def parse(self, script_input: ScriptInput) -> list[SceneSchema]:
        """Parse `script_input` into a non-empty ordered list of `SceneSchema` items."""
        raise NotImplementedError
