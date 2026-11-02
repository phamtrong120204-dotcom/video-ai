"""Skeleton / Stub Video Compositor Module (Phase 3 Contract Verification)."""

from pathlib import Path
from typing import Any

from app.core.exceptions import VideoCompositingError
from app.interfaces.base_compositor import IVideoCompositor
from app.schemas.job_schema import (
    JobStatus,
    ProcessingStats,
    RenderResult,
    TechnicalMetadata,
)
from app.schemas.scene_schema import SceneSchema


class StubVideoCompositor(IVideoCompositor):
    """Deterministic skeleton video compositor returning a validated RenderResult contract."""

    def compose_final_video(
        self,
        job_id: str,
        scenes: list[SceneSchema],
        scene_assets: dict[int, dict[str, Any]],
        output_path: Path,
    ) -> RenderResult:
        if not scenes:
            raise VideoCompositingError("Cannot compose video with empty scenes list", job_id=job_id)

        for scene in scenes:
            if scene.scene_id not in scene_assets:
                raise VideoCompositingError(
                    f"Missing rendered assets for scene_id={scene.scene_id}",
                    job_id=job_id,
                )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"MP4_STUB_CONTAINER_PHASE3")

        total_duration = round(sum(s.audio_duration_sec for s in scenes), 2)
        file_size = output_path.stat().st_size

        return RenderResult(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            output_video_path=str(output_path),
            video_url=f"/api/videos/{output_path.name}",
            technical_metadata=TechnicalMetadata(
                resolution="1080x1920",
                aspect_ratio="9:16",
                fps=30,
                duration_sec=total_duration,
                file_size_bytes=file_size,
                video_codec="h264",
                audio_codec="aac",
            ),
            scenes_summary=scenes,
            processing_stats=ProcessingStats(
                parser_mode="stub_parser",
                tts_engine="stub_audio",
            ),
        )


__all__ = ["StubVideoCompositor"]
