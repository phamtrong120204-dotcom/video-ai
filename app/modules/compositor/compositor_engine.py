"""
Dark Myth Stickman Auto-Studio - Production Video Compositor.

Implements IVideoCompositor interface, integrating AudioCompositor,
SoundLibrary, SfxTimelineMapper, and VideoAudioIntegrator.
"""

from pathlib import Path
import subprocess
import tempfile
import time
from typing import Any, Optional

from app.core.config import get_config
from app.core.exceptions import VideoCompositingError
from app.core.logger import get_logger
from app.interfaces.base_compositor import IVideoCompositor
from app.modules.audio.audio_compositor import AudioCompositor
from app.modules.audio.audio_models import AudioClip, AudioTimeline, AudioTrackType, DuckingConfig, MixConfig
from app.modules.audio.sfx_timeline_mapper import SfxTimelineMapper
from app.modules.audio.sound_library import SoundLibrary
from app.modules.audio.video_audio_integrator import VideoAudioIntegrator
from app.schemas.job_schema import (
    JobStatus,
    ProcessingStats,
    RenderResult,
    TechnicalMetadata,
)
from app.schemas.scene_schema import SceneSchema

logger = get_logger("modules.compositor.engine")


class DarkMythVideoCompositor(IVideoCompositor):
    """
    Production-grade video compositor combining G6 animation and G7 multi-track audio.
    Produces high-fidelity 1080x1920 (9:16) H.264 + AAC MP4 with synchronized SFX and ducked BGM.
    """

    def __init__(
        self,
        audio_compositor: Optional[AudioCompositor] = None,
        sound_library: Optional[SoundLibrary] = None,
        sfx_mapper: Optional[SfxTimelineMapper] = None,
        integrator: Optional[VideoAudioIntegrator] = None,
        bgm_theme: str = "battle_tension_percussion",
        bgm_volume_db: float = -6.0,
    ) -> None:
        self.sound_lib = sound_library or SoundLibrary()
        self.sound_lib.ensure_default_assets()
        self.audio_compositor = audio_compositor or AudioCompositor(
            mix_config=MixConfig(
                target_peak_dbfs=-0.5,
                ducking=DuckingConfig(attenuation_db=-14.0, attack_sec=0.08, release_sec=0.30),
            )
        )
        self.sfx_mapper = sfx_mapper or SfxTimelineMapper(sound_library=self.sound_lib)
        self.integrator = integrator or VideoAudioIntegrator(
            audio_compositor=self.audio_compositor,
            sfx_mapper=self.sfx_mapper,
        )
        self.bgm_theme = bgm_theme
        self.bgm_volume_db = bgm_volume_db

    def _generate_subtitles_srt(
        self,
        scenes: list[SceneSchema],
        scene_offsets: dict[int, float],
        output_srt: Path,
    ) -> Path:
        """Generates synchronized SRT subtitles with chunked readable lines."""
        def format_time(seconds: float) -> str:
            millis = int(round((seconds - int(seconds)) * 1000))
            s = int(seconds) % 60
            m = (int(seconds) // 60) % 60
            h = int(seconds) // 3600
            return f"{h:02d}:{m:02d}:{s:02d},{millis:03d}"

        lines: list[str] = []
        entry_idx = 1

        for scene in scenes:
            sid = scene.scene_id
            start_t = scene_offsets.get(sid, 0.0)
            dur = scene.audio_duration_sec or 3.0
            text = (scene.narration_text or "").strip()
            if not text:
                continue

            words = text.split()
            chunk_size = 8  # ~8 words per subtitle block for 9:16 mobile readability
            if len(words) <= chunk_size:
                chunks = [text]
            else:
                chunks = [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)]

            chunk_dur = dur / len(chunks)
            for i, chunk in enumerate(chunks):
                t0 = start_t + i * chunk_dur
                t1 = t0 + chunk_dur
                lines.append(str(entry_idx))
                lines.append(f"{format_time(t0)} --> {format_time(t1)}")
                lines.append(chunk)
                lines.append("")
                entry_idx += 1

        output_srt.parent.mkdir(parents=True, exist_ok=True)
        with open(output_srt, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return output_srt

    def compose_final_video(
        self,
        job_id: str,
        scenes: list[SceneSchema],
        scene_assets: dict[int, dict[str, Any]],
        output_path: Path,
    ) -> RenderResult:
        """
        Combines all scene video segments and master audio tracks into a single MP4 file.
        """
        t0 = time.perf_counter()
        if not scenes:
            raise VideoCompositingError("Cannot compose video with empty scenes list", job_id=job_id)

        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        work_dir = output_path.parent / f"work_{job_id}"
        work_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Compositing final video for job {job_id} ({len(scenes)} scenes) -> {output_path}")

        # 1. Validate assets and compute timeline offsets
        scene_offsets: dict[int, float] = {}
        current_offset = 0.0
        scene_video_paths: list[Path] = []

        for scene in scenes:
            sid = scene.scene_id
            if sid not in scene_assets:
                raise VideoCompositingError(f"Missing scene assets for scene {sid}", job_id=job_id)

            assets = scene_assets[sid]
            v_path = Path(assets.get("frames_path", ""))
            if not v_path.exists():
                raise VideoCompositingError(f"Scene video missing: {v_path}", job_id=job_id)

            scene_video_paths.append(v_path)
            scene_offsets[sid] = current_offset
            dur = scene.audio_duration_sec or float(assets.get("duration_sec", 3.0))
            current_offset += dur

        total_duration_sec = current_offset

        # 2. Build unified AudioTimeline
        audio_timeline = AudioTimeline()

        # Add voiceover clips with exact timing offsets
        for scene in scenes:
            sid = scene.scene_id
            assets = scene_assets[sid]
            voice_path = Path(assets.get("audio_path", ""))
            if voice_path.exists():
                audio_timeline.add_clip(
                    AudioClip(
                        track_type=AudioTrackType.VOICEOVER,
                        file_path=voice_path,
                        start_time_sec=scene_offsets[sid],
                        duration_sec=scene.audio_duration_sec,
                    )
                )

        # Add SFX cues for each scene
        for scene in scenes:
            sid = scene.scene_id
            offset = scene_offsets[sid]
            dur = scene.audio_duration_sec
            scene_tl = self.sfx_mapper.build_scene_timeline(
                scene=scene,
                scene_start_sec=offset,
                include_preset_sfx=True,
            )
            for clip in scene_tl.clips:
                if clip.track_type == AudioTrackType.SFX:
                    audio_timeline.add_clip(clip)

        # Add continuous BGM
        bgm_path = self.sound_lib.get_bgm_path(self.bgm_theme)
        if bgm_path and bgm_path.exists():
            audio_timeline.add_clip(
                AudioClip(
                    track_type=AudioTrackType.BGM,
                    file_path=bgm_path,
                    start_time_sec=0.0,
                    duration_sec=total_duration_sec,
                    gain_db=self.bgm_volume_db,
                    loop=True,
                    fade_out_sec=0.5,
                )
            )

        # 3. Mix master audio
        master_audio_path = work_dir / f"{job_id}_master.wav"
        self.audio_compositor.export_master(
            timeline=audio_timeline,
            output_path=master_audio_path,
            target_duration_sec=total_duration_sec,
            format="wav",
        )

        # 4. Concatenate scene videos if multiple, or use single
        if len(scene_video_paths) == 1:
            concat_video_path = scene_video_paths[0]
        else:
            concat_video_path = work_dir / f"{job_id}_video_concat.mp4"
            list_file = work_dir / "concat_list.txt"
            with open(list_file, "w", encoding="utf-8") as f:
                for vp in scene_video_paths:
                    # Windows paths need forward slashes for ffmpeg concat
                    safe_path = str(vp.resolve()).replace("\\", "/")
                    f.write(f"file '{safe_path}'\n")

            cfg = get_config()
            ffmpeg_bin = cfg.ffmpeg_path or r"C:\ffmpeg\bin\ffmpeg.exe"
            concat_cmd = [
                ffmpeg_bin,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(list_file),
                "-c", "copy",
                str(concat_video_path),
            ]
            res = subprocess.run(concat_cmd, capture_output=True, text=True, check=False)
            if res.returncode != 0:
                raise VideoCompositingError(f"FFmpeg video concatenation failed: {res.stderr}", job_id=job_id)

        # 5. Generate subtitles and mux video with master audio
        subtitles_srt_path = work_dir / f"{job_id}_subtitles.srt"
        try:
            self._generate_subtitles_srt(
                scenes=scenes,
                scene_offsets=scene_offsets,
                output_srt=subtitles_srt_path,
            )
        except Exception as e:
            logger.warning(f"Failed to generate subtitles: {e}")
            subtitles_srt_path = None

        self.integrator.mux_video_and_audio(
            video_path=concat_video_path,
            audio_path=master_audio_path,
            output_mp4_path=output_path,
            subtitles_path=subtitles_srt_path,
        )

        # 6. Gather technical metadata
        probe_info = self.integrator.probe_media(output_path)
        streams = probe_info.get("streams", [])
        v_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
        a_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})

        file_size_bytes = output_path.stat().st_size
        actual_dur = float(probe_info.get("format", {}).get("duration", total_duration_sec))
        elapsed_sec = round(time.perf_counter() - t0, 3)

        metadata = TechnicalMetadata(
            resolution=f"{v_stream.get('width', 1080)}x{v_stream.get('height', 1920)}",
            aspect_ratio="9:16",
            duration_sec=actual_dur,
            fps=30,
            video_codec=v_stream.get("codec_name", "h264"),
            audio_codec=a_stream.get("codec_name", "aac"),
            file_size_bytes=file_size_bytes,
        )
        stats = ProcessingStats(
            composite_time_sec=elapsed_sec,
            total_time_sec=elapsed_sec,
        )

        logger.info(
            f"Job {job_id} video compositing completed in {elapsed_sec}s: {output_path} ({file_size_bytes} bytes)"
        )

        return RenderResult(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            output_video_path=str(output_path),
            video_url=f"/api/videos/{output_path.name}",
            technical_metadata=metadata,
            processing_stats=stats,
        )
