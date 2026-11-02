"""
Dark Myth Stickman Auto-Studio - Pipeline Factory.

Constructs fully integrated, production-grade PipelineOrchestrator
connecting G4 Script Parser, G4/G7 Edge TTS Audio, G6/G8 Stickman VFX Animation,
and G7/G8 Video Compositor.
"""

from typing import Optional

from app.core.config import AppConfig, get_config
from app.core.task_manager import TaskManager
from app.modules.animation.animation_engine import DarkMythAnimationEngine
from app.modules.audio.edge_tts_engine import EdgeTTSAudioEngine
from app.modules.compositor.compositor_engine import DarkMythVideoCompositor
from app.modules.parser.hybrid_parser import HybridScriptParser
from app.pipeline.orchestrator import PipelineOrchestrator


def create_production_pipeline(
    config: Optional[AppConfig] = None,
    task_manager: Optional[TaskManager] = None,
    voice_id: str = "vi-VN-NamMinhNeural",
    voice_speed: float = 1.05,
    bgm_theme: str = "battle_tension_percussion",
    bgm_volume_db: float = -6.0,
    fps: int = 30,
    cleanup_temp_on_finish: bool = False,
) -> PipelineOrchestrator:
    """
    Instantiates and wires all real production modules into a PipelineOrchestrator.
    """
    cfg = config or get_config()
    tm = task_manager or TaskManager(config=cfg)

    # 1. G4 Parser: Hybrid (Gemini AI + Rule-based fallback)
    parser = HybridScriptParser()

    # 2. G4 Audio: Edge-TTS with multi-retry, HoaiMy fallback, and procedural wave fallback
    audio_engine = EdgeTTSAudioEngine(
        voice_id=voice_id,
        voice_speed=voice_speed,
    )

    # 3. G6/G8 Animation: DarkCorruptionVFXEngine + AnimationLoopEngine (1080x1920 30fps)
    animation_engine = DarkMythAnimationEngine(
        fps=fps,
    )

    # 4. G7/G8 Compositor: AudioCompositor + SfxTimelineMapper + VideoAudioIntegrator
    compositor = DarkMythVideoCompositor(
        bgm_theme=bgm_theme,
        bgm_volume_db=bgm_volume_db,
    )

    return PipelineOrchestrator(
        parser=parser,
        audio_engine=audio_engine,
        animation_engine=animation_engine,
        compositor=compositor,
        task_manager=tm,
        config=cfg,
        cleanup_temp_on_finish=cleanup_temp_on_finish,
    )
