"""Abstract Interfaces Package."""

from app.interfaces.base_animator import IAnimationEngine
from app.interfaces.base_compositor import IVideoCompositor
from app.interfaces.base_parser import IScriptParser
from app.interfaces.base_tts import IAudioEngine

__all__ = [
    "IScriptParser",
    "IAudioEngine",
    "IAnimationEngine",
    "IVideoCompositor",
]
