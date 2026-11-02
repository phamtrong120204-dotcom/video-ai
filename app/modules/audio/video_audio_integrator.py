"""
Dark Myth Stickman Auto-Studio - Stage 7: Video Audio Integrator.

Connects G6 animation video with G7 audio compositing, providing FFmpeg-powered
multiplexing, duration alignment, stream verification, and end-to-end clip generation.
"""

import json
import math
import os
from pathlib import Path
import subprocess
from typing import Optional, Union

from app.core.config import get_config
from app.core.logger import get_logger
from app.modules.animation.animation_loop import AnimationLoopEngine, AnimationTrack
from app.modules.animation.stickman_models import StickmanCharacter
from app.modules.audio.audio_compositor import AudioCompositor
from app.modules.audio.audio_models import AudioTimeline, MixConfig
from app.modules.audio.sfx_timeline_mapper import SfxTimelineMapper
from app.schemas.scene_schema import SceneSchema

logger = get_logger("video_audio_integrator")


class VideoAudioIntegrator:
    """
    End-to-end integrator uniting video frames, audio stems, and final MP4 delivery.
    """

    def __init__(
        self,
        audio_compositor: Optional[AudioCompositor] = None,
        sfx_mapper: Optional[SfxTimelineMapper] = None,
        animation_engine: Optional[AnimationLoopEngine] = None,
        ffmpeg_path: Optional[str] = None,
        ffprobe_path: Optional[str] = None,
    ) -> None:
        cfg = get_config()
        self.audio_compositor = audio_compositor or AudioCompositor()
        self.sfx_mapper = sfx_mapper or SfxTimelineMapper()
        self.animation_engine = animation_engine or AnimationLoopEngine()
        self.ffmpeg_path = ffmpeg_path or cfg.ffmpeg_path or r"C:\ffmpeg\bin\ffmpeg.exe"
        self.ffprobe_path = ffprobe_path or cfg.ffprobe_path or r"C:\ffmpeg\bin\ffprobe.exe"

    def probe_media(self, file_path: Path) -> dict:
        """
        Extract stream and format details using ffprobe.
        """
        if not file_path.is_file():
            raise FileNotFoundError(f"Media file not found: {file_path}")

        cmd = [
            self.ffprobe_path,
            "-v", "error",
            "-print_format", "json",
            "-show_streams",
            "-show_format",
            str(file_path),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(res.stdout)

    def mux_video_and_audio(
        self,
        video_path: Path,
        audio_path: Path,
        output_mp4_path: Path,
        audio_codec: str = "aac",
        audio_bitrate: str = "192k",
        subtitles_path: Optional[Path] = None,
    ) -> Path:
        """
        Multiplex an existing video file and audio file into a synchronized MP4.
        If subtitles_path is provided, burns synchronized subtitles onto the video.
        Otherwise uses stream copy for video (-c:v copy) to prevent generational loss.
        """
        if not video_path.is_file():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if not audio_path.is_file():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        output_mp4_path.parent.mkdir(parents=True, exist_ok=True)

        if subtitles_path is not None and subtitles_path.is_file():
            safe_srt = str(subtitles_path.resolve()).replace(os.sep, "/").replace(":", r"\:")
            vf_sub = (
                f"subtitles='{safe_srt}':force_style='PlayResX=1080,PlayResY=1920,Fontname=Arial,FontSize=42,"
                f"PrimaryColour=&H0000D7FF,OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=1,MarginV=180,Alignment=2'"
            )
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i", str(video_path),
                "-i", str(audio_path),
                "-vf", vf_sub,
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "20",
                "-pix_fmt", "yuv420p",
                "-c:a", audio_codec,
                "-b:a", audio_bitrate,
                "-movflags", "+faststart",
                "-shortest",
                str(output_mp4_path),
            ]
        else:
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i", str(video_path),
                "-i", str(audio_path),
                "-c:v", "copy",
                "-c:a", audio_codec,
                "-b:a", audio_bitrate,
                "-movflags", "+faststart",
                "-shortest",
                str(output_mp4_path),
            ]

        logger.info(f"Muxing {video_path.name} + {audio_path.name} -> {output_mp4_path.name}")
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg muxing failed (code {res.returncode}): {res.stderr}")

        # Verify muxed output streams
        probe = self.probe_media(output_mp4_path)
        streams = probe.get("streams", [])
        v_streams = [s for s in streams if s.get("codec_type") == "video"]
        a_streams = [s for s in streams if s.get("codec_type") == "audio"]

        if not v_streams:
            raise RuntimeError(f"Output MP4 missing video stream: {output_mp4_path}")
        if not a_streams:
            raise RuntimeError(f"Output MP4 missing audio stream: {output_mp4_path}")

        return output_mp4_path

    def render_complete_scene(
        self,
        scene: SceneSchema,
        character: StickmanCharacter,
        track: AnimationTrack,
        output_dir: Path,
        clip_name: str = "scene_clip",
        fps: int = 30,
        bgm_theme: Optional[str] = "dark_myth_orchestral",
        background_image: Optional[object] = None,
    ) -> dict[str, Path]:
        """
        Render a full scene from scratch:
          1. Generates animation frames & export video via G6 AnimationLoopEngine.
          2. Builds audio timeline via SfxTimelineMapper.
          3. Mixes master audio and stems via AudioCompositor.
          4. Muxes video and audio into final MP4.

        Returns dictionary of all generated artifact paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        dur = scene.audio_duration_sec

        # 1. Video export
        raw_video_path = output_dir / f"{clip_name}_video_only.mp4"
        frames = self.animation_engine.generate_clip_frames(
            track=track,
            character=character,
            fps=fps,
            background_image=background_image,
        )
        self.animation_engine.export_mp4_video(frames, raw_video_path, fps=fps, ffmpeg_path=self.ffmpeg_path)

        # 2. Audio timeline & mixing
        audio_timeline = self.sfx_mapper.build_scene_timeline(scene=scene)
        # Ensure BGM clip if theme specified
        if bgm_theme:
            bgm_asset = self.sfx_mapper.sound_library.get_bgm(bgm_theme)
            from app.modules.audio.audio_models import AudioClip, AudioTrackType
            audio_timeline.add_clip(
                AudioClip(
                    track_type=AudioTrackType.BGM,
                    file_path=Path(bgm_asset.file_path),
                    start_time_sec=0.0,
                    duration_sec=dur,
                    loop=True,
                    fade_in_sec=0.5,
                    fade_out_sec=0.8,
                )
            )

        master_audio_path = output_dir / f"{clip_name}_master.wav"
        self.audio_compositor.export_master(
            timeline=audio_timeline,
            output_path=master_audio_path,
            target_duration_sec=dur,
        )

        # Export stems
        stems = self.audio_compositor.export_stems(
            timeline=audio_timeline,
            output_dir=output_dir / "stems",
            target_duration_sec=dur,
        )

        # 3. Mux into final MP4
        final_mp4_path = output_dir / f"{clip_name}_final.mp4"
        self.mux_video_and_audio(
            video_path=raw_video_path,
            audio_path=master_audio_path,
            output_mp4_path=final_mp4_path,
        )

        results = {
            "video_only": raw_video_path,
            "master_audio": master_audio_path,
            "final_mp4": final_mp4_path,
            **stems,
        }
        return results
