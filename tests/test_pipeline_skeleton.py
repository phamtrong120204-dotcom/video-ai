"""Integration Tests for PipelineOrchestrator Skeleton (Audio-First Timing & Fault Isolation)."""

from pathlib import Path
from typing import Any
import pytest

from app.core.config import AppConfig
from app.core.exceptions import AnimationRenderError, AudioGenerationError, ScriptParseError
from app.core.task_manager import TaskManager
from app.interfaces.base_animator import IAnimationEngine
from app.interfaces.base_compositor import IVideoCompositor
from app.interfaces.base_parser import IScriptParser
from app.interfaces.base_tts import IAudioEngine
from app.modules.animation import StubAnimationEngine
from app.modules.audio import StubAudioEngine
from app.modules.compositor import StubVideoCompositor
from app.modules.parser import StubScriptParser
from app.pipeline.orchestrator import PipelineOrchestrator
from app.schemas.job_schema import JobStatus
from app.schemas.scene_schema import SceneSchema
from app.schemas.script_schema import ScriptInput


class OrderTrackingAudioEngine(StubAudioEngine):
    """Spy wrapper around StubAudioEngine recording call sequence and generated durations."""

    def __init__(self, call_log: list[str]) -> None:
        super().__init__()
        self.call_log = call_log

    def generate_scene_audio(self, scene: SceneSchema, output_dir: Path) -> tuple[Path, float]:
        self.call_log.append(f"audio:scene_{scene.scene_id}")
        return super().generate_scene_audio(scene, output_dir)


class OrderTrackingAnimationEngine(StubAnimationEngine):
    """Spy wrapper around StubAnimationEngine verifying it receives positive measured audio duration."""

    def __init__(self, call_log: list[str], received_durations: dict[int, float]) -> None:
        super().__init__()
        self.call_log = call_log
        self.received_durations = received_durations

    def render_scene_frames(self, scene: SceneSchema, duration_sec: float, output_dir: Path) -> Path:
        self.call_log.append(f"anim:scene_{scene.scene_id}")
        self.received_durations[scene.scene_id] = duration_sec
        return super().render_scene_frames(scene, duration_sec, output_dir)


def test_pipeline_orchestrator_end_to_end_with_stubs(
    isolated_config: AppConfig,
    task_manager: TaskManager,
    sample_script_input: ScriptInput,
) -> None:
    """
    Verify PipelineOrchestrator executes:
      Parser -> AudioEngine (measuring duration_sec) -> AnimationEngine (with exact duration_sec) -> Compositor
    and updates TaskManager to COMPLETED while cleaning up temp directory.
    """
    call_log: list[str] = []
    received_durations: dict[int, float] = {}

    orchestrator = PipelineOrchestrator(
        parser=StubScriptParser(),
        audio_engine=OrderTrackingAudioEngine(call_log),
        animation_engine=OrderTrackingAnimationEngine(call_log, received_durations),
        compositor=StubVideoCompositor(),
        task_manager=task_manager,
        config=isolated_config,
        cleanup_temp_on_finish=True,
    )

    result = orchestrator.run(sample_script_input)

    assert result.job_id == sample_script_input.job_id
    assert result.status == JobStatus.COMPLETED
    assert result.output_video_path is not None
    assert Path(result.output_video_path).exists()
    assert len(result.scenes_summary) == 3

    # Verify Audio-First order: all scene audio durations were generated before animation rendering
    assert call_log == [
        "audio:scene_1",
        "audio:scene_2",
        "audio:scene_3",
        "anim:scene_1",
        "anim:scene_2",
        "anim:scene_3",
    ]

    # Verify every scene's measured audio_duration_sec was positive and passed identically to AnimationEngine
    for scene in result.scenes_summary:
        assert scene.audio_duration_sec > 0.0
        assert received_durations[scene.scene_id] == scene.audio_duration_sec

    # Verify TaskManager final status is COMPLETED (100%) and temp folder was cleaned up
    job_record = task_manager.load_job(sample_script_input.job_id)
    assert job_record.status == JobStatus.COMPLETED
    assert job_record.progress_percent == 100
    assert not (isolated_config.temp_dir / sample_script_input.job_id).exists()


def test_pipeline_orchestrator_catches_module_failure_and_marks_job_failed(
    isolated_config: AppConfig,
    task_manager: TaskManager,
    sample_script_input: ScriptInput,
) -> None:
    """Verify that when a module raises an error, Orchestrator marks the job as FAILED and cleans up temp files."""

    class FailingAnimationEngine(IAnimationEngine):
        def render_scene_frames(self, scene: SceneSchema, duration_sec: float, output_dir: Path) -> Path:
            if scene.scene_id == 2:
                raise RuntimeError("Mô phỏng lỗi tràn ma trận xương ở cảnh 2")
            output_dir.mkdir(parents=True, exist_ok=True)
            p = output_dir / f"scene_{scene.scene_id}.json"
            p.write_text("{}", encoding="utf-8")
            return p

    orchestrator = PipelineOrchestrator(
        parser=StubScriptParser(),
        audio_engine=StubAudioEngine(),
        animation_engine=FailingAnimationEngine(),
        compositor=StubVideoCompositor(),
        task_manager=task_manager,
        config=isolated_config,
        cleanup_temp_on_finish=True,
    )

    with pytest.raises(AnimationRenderError) as exc_info:
        orchestrator.run(sample_script_input)

    assert "Mô phỏng lỗi tràn ma trận xương ở cảnh 2" in str(exc_info.value)

    # Verify job record was transitioned to FAILED with exact error cause and temp directory was cleaned
    failed_record = task_manager.load_job(sample_script_input.job_id)
    assert failed_record.status == JobStatus.FAILED
    assert failed_record.error_message is not None
    assert "Mô phỏng lỗi tràn ma trận xương ở cảnh 2" in failed_record.error_message
    assert not (isolated_config.temp_dir / sample_script_input.job_id).exists()
