"""Pipeline Orchestrator Connecting Parser -> Audio -> Animation -> Compositor via Dependency Injection."""

from pathlib import Path
import shutil
import time
from typing import Any, Optional

from app.core.config import AppConfig, get_config
from app.core.exceptions import (
    AnimationRenderError,
    AudioGenerationError,
    AutoStudioError,
    ScriptParseError,
    VideoCompositingError,
)
from app.core.logger import get_logger, reset_log_job_id, set_log_job_id
from app.core.task_manager import TaskManager
from app.interfaces.base_animator import IAnimationEngine
from app.interfaces.base_compositor import IVideoCompositor
from app.interfaces.base_parser import IScriptParser
from app.interfaces.base_tts import IAudioEngine
from app.schemas.job_schema import JobStatus, RenderResult
from app.schemas.scene_schema import SceneSchema
from app.schemas.script_schema import ScriptInput


class PipelineOrchestrator:
    """
    Coordinates the end-to-end audio-driven stickman video generation pipeline.

    Strict Runtime Execution Order:
      1. Parse `ScriptInput` into `list[SceneSchema]` (`parsing`).
      2. For each scene, invoke `IAudioEngine.generate_scene_audio` FIRST (`generating_audio`),
         measure `duration_sec`, and write `audio_duration_sec` back into `SceneSchema`.
      3. For each scene, invoke `IAnimationEngine.render_scene_frames` using the exact
         `audio_duration_sec` measured in step 2 (`rendering_animation`).
      4. Invoke `IVideoCompositor.compose_final_video` to mux audio + frames into `.mp4` (`compositing`).
      5. Mark job `completed` in `TaskManager` and clean up `out/temp/<job_id>/`.
    """

    def __init__(
        self,
        parser: IScriptParser,
        audio_engine: IAudioEngine,
        animation_engine: IAnimationEngine,
        compositor: IVideoCompositor,
        task_manager: Optional[TaskManager] = None,
        config: Optional[AppConfig] = None,
        cleanup_temp_on_finish: bool = True,
    ) -> None:
        self.config = config or get_config()
        self.task_manager = task_manager or TaskManager(config=self.config)
        self.parser = parser
        self.audio_engine = audio_engine
        self.animation_engine = animation_engine
        self.compositor = compositor
        self.cleanup_temp_on_finish = cleanup_temp_on_finish
        self._logger = get_logger("pipeline.orchestrator")

    def run(self, script_input: ScriptInput) -> RenderResult:
        """Execute the full pipeline for `script_input` while tracking state in `TaskManager`."""
        job_id = script_input.job_id
        token = set_log_job_id(job_id)
        t_start = time.perf_counter()

        # Ensure a JobRecord exists in TaskManager
        try:
            self.task_manager.load_job(job_id)
        except Exception:
            self.task_manager.create_job(script_input)

        job_temp_dir = self.config.temp_dir / job_id
        audio_temp_dir = job_temp_dir / "audio"
        frames_temp_dir = job_temp_dir / "frames"
        output_video_path = self.config.out_dir / f"{job_id}.mp4"

        scenes: list[SceneSchema] = []
        scene_assets: dict[int, dict[str, Any]] = {}

        try:
            job_temp_dir.mkdir(parents=True, exist_ok=True)

            # STEP 1: PARSING
            t_parse_start = time.perf_counter()
            self.task_manager.transition_status(
                job_id,
                JobStatus.PARSING,
                progress_percent=10,
                step_message="Đang phân tích kịch bản thành danh sách phân cảnh (SceneSchema)...",
            )
            try:
                scenes = self.parser.parse(script_input)
            except AutoStudioError:
                raise
            except Exception as exc:
                raise ScriptParseError(f"Parser failed: {exc}", job_id=job_id, cause=exc) from exc

            if not scenes:
                raise ScriptParseError("Parser returned an empty list of scenes", job_id=job_id)
            parse_time_sec = round(time.perf_counter() - t_parse_start, 4)

            total_scenes = len(scenes)
            self.task_manager.transition_status(
                job_id,
                JobStatus.GENERATING_AUDIO,
                progress_percent=20,
                total_scenes=total_scenes,
                completed_scenes=0,
                step_message=f"Đang tạo giọng đọc tiếng Việt và đo thời lượng cho {total_scenes} cảnh...",
            )

            # STEP 2: GENERATING AUDIO FIRST (Audio-Driven Timing)
            t_tts_start = time.perf_counter()
            for idx, scene in enumerate(scenes, start=1):
                try:
                    audio_path, duration_sec = self.audio_engine.generate_scene_audio(scene, audio_temp_dir)
                except AutoStudioError:
                    raise
                except Exception as exc:
                    raise AudioGenerationError(
                        f"Audio generation failed on scene {scene.scene_id}: {exc}",
                        job_id=job_id,
                        cause=exc,
                    ) from exc

                if duration_sec <= 0.0:
                    raise AudioGenerationError(
                        f"Measured duration_sec must be > 0.0 for scene {scene.scene_id}, got {duration_sec}",
                        job_id=job_id,
                    )

                scene.audio_duration_sec = float(duration_sec)
                scene.voice_audio_path = str(audio_path)
                scene_assets[scene.scene_id] = {
                    "audio_path": Path(audio_path),
                    "duration_sec": float(duration_sec),
                }

                audio_progress = 20 + int((idx / total_scenes) * 15)
                self.task_manager.transition_status(
                    job_id,
                    JobStatus.GENERATING_AUDIO,
                    progress_percent=audio_progress,
                    step_message=f"Đã đo thời lượng giọng đọc cảnh {idx}/{total_scenes} ({duration_sec:.2f}s).",
                )
            tts_time_sec = round(time.perf_counter() - t_tts_start, 4)

            # STEP 3: RENDERING STICKMAN ANIMATION MATCHING EXACT AUDIO DURATION
            t_render_start = time.perf_counter()
            self.task_manager.transition_status(
                job_id,
                JobStatus.RENDERING_ANIMATION,
                progress_percent=40,
                step_message="Đang dựng hoạt hình người que khớp thời lượng thoại từng cảnh...",
            )
            for idx, scene in enumerate(scenes, start=1):
                try:
                    frames_path = self.animation_engine.render_scene_frames(
                        scene=scene,
                        duration_sec=scene.audio_duration_sec,
                        output_dir=frames_temp_dir,
                    )
                except AutoStudioError:
                    raise
                except Exception as exc:
                    raise AnimationRenderError(
                        f"Animation render failed on scene {scene.scene_id}: {exc}",
                        job_id=job_id,
                        cause=exc,
                    ) from exc

                scene_assets[scene.scene_id]["frames_path"] = Path(frames_path)
                anim_progress = 40 + int((idx / total_scenes) * 40)
                self.task_manager.transition_status(
                    job_id,
                    JobStatus.RENDERING_ANIMATION,
                    progress_percent=anim_progress,
                    completed_scenes=idx,
                    step_message=f"Đã dựng hoạt hình cảnh {idx}/{total_scenes}.",
                )
            render_time_sec = round(time.perf_counter() - t_render_start, 4)

            # STEP 4: COMPOSITING FINAL MP4
            t_comp_start = time.perf_counter()
            self.task_manager.transition_status(
                job_id,
                JobStatus.COMPOSITING,
                progress_percent=85,
                step_message="Đang trộn âm thanh (Voice + SFX + BGM) và kết xuất MP4 9:16...",
            )
            try:
                render_result = self.compositor.compose_final_video(
                    job_id=job_id,
                    scenes=scenes,
                    scene_assets=scene_assets,
                    output_path=output_video_path,
                )
            except AutoStudioError:
                raise
            except Exception as exc:
                raise VideoCompositingError(
                    f"Compositor failed: {exc}",
                    job_id=job_id,
                    cause=exc,
                ) from exc
            composite_time_sec = round(time.perf_counter() - t_comp_start, 4)
            total_time_sec = round(time.perf_counter() - t_start, 4)

            render_result.processing_stats.parse_time_sec = parse_time_sec
            render_result.processing_stats.tts_time_sec = tts_time_sec
            render_result.processing_stats.render_time_sec = render_time_sec
            render_result.processing_stats.composite_time_sec = composite_time_sec
            render_result.processing_stats.total_time_sec = total_time_sec

            # STEP 5: MARK COMPLETED
            self.task_manager.mark_completed(
                job_id=job_id,
                output_video_path=render_result.output_video_path or str(output_video_path),
            )
            return render_result

        except Exception as exc:
            error_msg = str(exc)
            try:
                self.task_manager.mark_failed(job_id=job_id, error_message=error_msg)
            except Exception:
                pass
            if isinstance(exc, AutoStudioError):
                raise
            raise AutoStudioError(error_msg, job_id=job_id, stage="pipeline", cause=exc) from exc

        finally:
            if self.cleanup_temp_on_finish and job_temp_dir.exists():
                shutil.rmtree(job_temp_dir, ignore_errors=True)
            reset_log_job_id(token)
