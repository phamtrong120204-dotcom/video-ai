"""Production Vietnamese TTS Engine with Edge-TTS, Retry/Fallback, Audio Padding, and Mutagen Measurement."""

import asyncio
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import time
from typing import Optional
import unicodedata

# Ensure C:\ffmpeg\bin is in PATH before importing pydub
_ffmpeg_bin_dir = r"C:\ffmpeg\bin"
if Path(_ffmpeg_bin_dir).is_dir() and _ffmpeg_bin_dir.lower() not in os.environ.get("PATH", "").lower():
    os.environ["PATH"] = f"{_ffmpeg_bin_dir};{os.environ.get('PATH', '')}"

import edge_tts
import mutagen.mp3
from pydub import AudioSegment

from app.core.config import get_config
from app.core.exceptions import AudioGenerationError
from app.core.logger import get_logger
from app.interfaces.base_tts import IAudioEngine
from app.schemas.scene_schema import SceneSchema

logger = get_logger("edge_tts_engine")


class EdgeTTSAudioEngine(IAudioEngine):
    """
    Synchronous Vietnamese TTS Engine using Microsoft Edge-TTS with:
      - Exponential backoff retry with jitter
      - Primary -> Fallback voice switching
      - Strict Job-level voice consistency (once locked, all scenes share the same voice)
      - Pydub 0.30s silence tail padding
      - Mutagen exact duration measurement
    """

    def __init__(
        self,
        voice_id: str = "vi-VN-NamMinhNeural",
        fallback_voice_id: str = "vi-VN-HoaiMyNeural",
        voice_speed: float = 1.0,
        audio_padding_sec: float = 0.30,
        max_retries: int = 3,
        base_backoff_sec: float = 1.0,
        timeout_sec: float = 20.0,
        lock_voice_per_job: bool = True,
    ) -> None:
        self.voice_id = voice_id
        self.fallback_voice_id = fallback_voice_id
        self.voice_speed = voice_speed
        self.audio_padding_sec = audio_padding_sec
        self.max_retries = max_retries
        self.base_backoff_sec = base_backoff_sec
        self.timeout_sec = timeout_sec
        self.lock_voice_per_job = lock_voice_per_job

        # Job-level locked voice ensuring all scenes in the same video share the same voice
        self.active_voice_id: Optional[str] = None
        # Track scenes generated in the current job to allow whole-job rollback/re-synthesis if voice changes
        self.job_history: list[tuple[SceneSchema, Path]] = []

        self._configure_audio_tools()

    def _configure_audio_tools(self) -> None:
        """Configure Pydub with portable FFmpeg binaries and process PATH."""
        cfg = get_config()
        if cfg.ffmpeg_path and Path(cfg.ffmpeg_path).is_file():
            AudioSegment.converter = cfg.ffmpeg_path
        if cfg.ffprobe_path and Path(cfg.ffprobe_path).is_file():
            AudioSegment.ffprobe = cfg.ffprobe_path

        # Ensure C:\ffmpeg\bin is present in current process PATH
        ffmpeg_bin_dir = r"C:\ffmpeg\bin"
        current_path = os.environ.get("PATH", "")
        if ffmpeg_bin_dir.lower() not in current_path.lower() and Path(ffmpeg_bin_dir).is_dir():
            os.environ["PATH"] = f"{ffmpeg_bin_dir};{current_path}"

    def reset_job_voice(self) -> None:
        """Reset locked voice and scene history for a new Job."""
        self.active_voice_id = None
        self.job_history.clear()

    def reset_job(self) -> None:
        """Alias for reset_job_voice."""
        self.reset_job_voice()

    def _format_rate_str(self) -> str:
        """Convert float speed multiplier (e.g. 1.05) to Edge-TTS rate string (e.g. '+5%')."""
        rate_pct = int(round((self.voice_speed - 1.0) * 100))
        return f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"

    def _measure_audio_duration(self, file_path: Path) -> float:
        """
        Measure authoritative decoded audio duration using portable ffprobe (matching PCM samples).
        Falls back to Mutagen length if ffprobe is unavailable.
        """
        cfg = get_config()
        ffprobe_exe = cfg.ffprobe_path or r"C:\ffmpeg\bin\ffprobe.exe"
        if Path(ffprobe_exe).is_file():
            try:
                cmd = [
                    ffprobe_exe,
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    str(file_path),
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                probe_data = json.loads(res.stdout)
                dur = float(probe_data.get("format", {}).get("duration", 0.0))
                if dur > 0.0:
                    return round(dur, 3)
            except Exception as exc:
                logger.warning(f"ffprobe duration measurement failed ({exc}), falling back to Mutagen")

        audio = mutagen.mp3.MP3(str(file_path))
        return round(audio.info.length, 3)

    @staticmethod
    def _clean_tts_text(text: str) -> str:
        """Standardize Vietnamese text to Unicode NFC and sanitize known Edge-TTS tokenizer bugs."""
        normalized = unicodedata.normalize("NFC", text.strip())
        # Microsoft Edge-TTS has a known dictionary rejection on capitalized proper noun 'Tiễn'/'Tiến'
        normalized = normalized.replace("Dương Tiễn", "Dương tiễn")
        normalized = normalized.replace("Dương Tiến", "Dương tiến")
        normalized = normalized.replace("Tiễn", "tiễn")
        return normalized

    def _re_synthesize_scene_with_voice(
        self, scene: SceneSchema, output_dir: Path, target_voice: str
    ) -> tuple[Path, float]:
        """Re-synthesize a prior scene directly with target_voice to guarantee job-level voice consistency."""
        raw_text = scene.narration_text.strip()
        narration = self._clean_tts_text(raw_text)
        output_dir = Path(output_dir)

        final_filename = f"scene_{scene.scene_id:02d}_voice.mp3"
        final_path = output_dir / final_filename

        raw_tmp_path = output_dir / f"scene_{scene.scene_id:02d}_raw_recovery.tmp.mp3"
        padded_tmp_path = output_dir / f"scene_{scene.scene_id:02d}_padded_recovery.tmp.mp3"

        rate_str = self._format_rate_str()
        last_exc: Optional[Exception] = None

        try:
            for attempt in range(1, self.max_retries + 1):
                try:
                    if raw_tmp_path.exists():
                        raw_tmp_path.unlink()
                    asyncio.run(
                        self._async_edge_tts_call(
                            text=narration,
                            voice=target_voice,
                            rate=rate_str,
                            output_file=str(raw_tmp_path),
                        )
                    )
                    raw_meta = self._validate_mp3_file(raw_tmp_path, scene_id=scene.scene_id, stage_desc="recovery raw voice")
                    raw_duration = raw_meta.info.length

                    self._apply_silence_padding(
                        source_path=raw_tmp_path,
                        target_path=padded_tmp_path,
                        scene_id=scene.scene_id,
                        raw_duration=raw_duration,
                    )
                    self._validate_mp3_file(padded_tmp_path, scene_id=scene.scene_id, stage_desc="recovery padded audio")

                    if final_path.exists():
                        final_path.unlink()
                    shutil.move(str(padded_tmp_path), str(final_path))

                    authoritative_duration = self._measure_audio_duration(final_path)
                    scene.voice_audio_path = str(final_path.resolve())
                    scene.audio_duration_sec = float(authoritative_duration)
                    return final_path, float(authoritative_duration)
                except Exception as exc:
                    last_exc = exc
                    time.sleep(0.5 * attempt)

            raise AudioGenerationError(f"Re-synthesis failed after {self.max_retries} attempts: {last_exc}", cause=last_exc)
        finally:
            if raw_tmp_path.exists():
                try:
                    raw_tmp_path.unlink()
                except OSError:
                    pass
            if padded_tmp_path.exists():
                try:
                    padded_tmp_path.unlink()
                except OSError:
                    pass

    def generate_scene_audio(self, scene: SceneSchema, output_dir: Path) -> tuple[Path, float]:
        """
        Synthesize Vietnamese voiceover for `scene` with retry, voice fallback, and 0.30s silence padding.

        Returns:
            tuple[Path, float]: (final_padded_mp3_path, measured_duration_sec)
        """
        raw_text = scene.narration_text.strip()
        if not raw_text:
            raise AudioGenerationError(
                f"Phân cảnh {scene.scene_id} có narration_text rỗng."
            )

        # Standardize Vietnamese text to Unicode NFC and sanitize Edge-TTS quirks
        narration = self._clean_tts_text(raw_text)

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        final_filename = f"scene_{scene.scene_id:02d}_voice.mp3"
        final_path = output_dir / final_filename

        raw_tmp_path = output_dir / f"scene_{scene.scene_id:02d}_raw.tmp.mp3"
        padded_tmp_path = output_dir / f"scene_{scene.scene_id:02d}_padded.tmp.mp3"

        try:
            # 1. Synthesize raw voice using Edge-TTS
            selected_voice, raw_duration = self._synthesize_with_retry_and_fallback(
                narration=narration,
                output_path=raw_tmp_path,
                scene_id=scene.scene_id,
            )

            # 2. Validate raw audio with Mutagen
            self._validate_mp3_file(raw_tmp_path, scene_id=scene.scene_id, stage_desc="raw voice")

            # 3. Apply Audio Padding (append 0.30s silence via Pydub)
            padded_duration = self._apply_silence_padding(
                source_path=raw_tmp_path,
                target_path=padded_tmp_path,
                scene_id=scene.scene_id,
                raw_duration=raw_duration,
            )

            # 4. Validate padded audio with Mutagen
            self._validate_mp3_file(padded_tmp_path, scene_id=scene.scene_id, stage_desc="padded audio")

            # 5. Atomic Promotion: replace final file with verified padded file
            if final_path.exists():
                final_path.unlink()
            shutil.move(str(padded_tmp_path), str(final_path))

            # 6. Authoritative duration measurement (FFprobe PCM match)
            authoritative_duration = self._measure_audio_duration(final_path)

            # 7. Job-level voice recovery check (Case B: Whole-Job Voice Recovery)
            if self.lock_voice_per_job and self.active_voice_id and selected_voice != self.active_voice_id:
                logger.warning(
                    f"Job voice switch triggered on Scene {scene.scene_id}: "
                    f"Switching from '{self.active_voice_id}' to '{selected_voice}'. "
                    f"Re-synthesizing {len(self.job_history)} prior scene(s) with '{selected_voice}' "
                    f"to guarantee 100% voice uniformity across the entire Job (Case B)..."
                )
                for prior_scene, prior_dir in self.job_history:
                    try:
                        self._re_synthesize_scene_with_voice(
                            scene=prior_scene,
                            output_dir=prior_dir,
                            target_voice=selected_voice,
                        )
                    except Exception as re_exc:
                        # Case C: Stop and fail cleanly if voice uniformity cannot be guaranteed
                        raise AudioGenerationError(
                            f"Phân cảnh {scene.scene_id}: Không thể đồng nhất giọng đọc toàn Job khi chuyển sang '{selected_voice}': lỗi tái tạo cảnh {prior_scene.scene_id}: {re_exc}",
                            cause=re_exc,
                        ) from re_exc

            # Lock active voice and track in job history
            self.active_voice_id = selected_voice
            self.job_history.append((scene, output_dir))

            # Update SceneSchema
            scene.voice_audio_path = str(final_path.resolve())
            scene.audio_duration_sec = float(authoritative_duration)

            logger.info(
                f"Scene {scene.scene_id}: Voice generated successfully using '{selected_voice}'. "
                f"Raw: {raw_duration:.3f}s -> Final: {authoritative_duration:.3f}s (file: {final_path.name})",
            )
            return final_path, float(authoritative_duration)

        except AudioGenerationError:
            raise
        except Exception as exc:
            msg = f"Lỗi không xác định khi tạo audio cảnh {scene.scene_id}: {exc}"
            logger.error(msg)
            raise AudioGenerationError(msg, cause=exc) from exc
        finally:
            # Clean up temporary working files
            if raw_tmp_path.exists():
                try:
                    raw_tmp_path.unlink()
                except OSError:
                    pass
            if padded_tmp_path.exists():
                try:
                    padded_tmp_path.unlink()
                except OSError:
                    pass

    def _synthesize_with_retry_and_fallback(
        self, narration: str, output_path: Path, scene_id: int
    ) -> tuple[str, float]:
        """Synthesize voice using primary voice (with retries), falling back to secondary voice if needed."""
        # Check Job-level voice candidates
        if self.lock_voice_per_job and self.active_voice_id:
            candidate_voices = [self.active_voice_id]
            if self.fallback_voice_id != self.active_voice_id:
                candidate_voices.append(self.fallback_voice_id)
        else:
            candidate_voices = [self.voice_id, self.fallback_voice_id]

        rate_str = self._format_rate_str()
        last_error: Optional[Exception] = None

        for voice_idx, candidate_voice in enumerate(candidate_voices):
            logger.info(f"Scene {scene_id}: Attempting synthesis with voice '{candidate_voice}' (rate={rate_str})...")

            for attempt in range(1, self.max_retries + 1):
                try:
                    if output_path.exists():
                        output_path.unlink()

                    # Run async Edge-TTS inside synchronous context
                    asyncio.run(
                        self._async_edge_tts_call(
                            text=narration,
                            voice=candidate_voice,
                            rate=rate_str,
                            output_file=str(output_path),
                        )
                    )

                    # Quick sanity check on disk
                    if output_path.exists() and output_path.stat().st_size > 1024:
                        audio = mutagen.mp3.MP3(str(output_path))
                        duration = audio.info.length
                        if duration > 0.5:
                            return candidate_voice, duration
                        else:
                            raise AudioGenerationError(
                                f"Phân cảnh {scene_id}: Audio duration {duration:.2f}s <= 0.5s"
                            )
                    else:
                        raise AudioGenerationError(
                            f"Phân cảnh {scene_id}: Generated audio file missing or under 1024 bytes"
                        )

                except edge_tts.exceptions.NoAudioReceived as exc:
                    last_error = exc
                    logger.warning(
                        f"Scene {scene_id} [Attempt {attempt}/{self.max_retries}] "
                        f"NoAudioReceived for voice '{candidate_voice}': {exc}"
                    )
                except Exception as exc:
                    last_error = exc
                    logger.warning(
                        f"Scene {scene_id} [Attempt {attempt}/{self.max_retries}] "
                        f"Synthesis error ({type(exc).__name__}): {exc}"
                    )

                # Exponential backoff with jitter
                if attempt < self.max_retries:
                    backoff = (self.base_backoff_sec * (2 ** (attempt - 1))) + random.uniform(0.1, 0.4)
                    logger.debug(f"Scene {scene_id}: Waiting {backoff:.2f}s before retry...")
                    time.sleep(backoff)

            logger.warning(
                f"Scene {scene_id}: Voice '{candidate_voice}' failed all {self.max_retries} retries."
            )

        # All candidate voices failed
        raise AudioGenerationError(
            f"Phân cảnh {scene_id}: Tạo giọng đọc thất bại trên toàn bộ giọng ứng viên ({candidate_voices}) sau retry: {last_error}",
            cause=last_error,
        )

    async def _async_edge_tts_call(self, text: str, voice: str, rate: str, output_file: str) -> None:
        """Call Edge-TTS communicate save inside an async coroutine with timeout."""
        comm = edge_tts.Communicate(text=text, voice=voice, rate=rate)
        await asyncio.wait_for(comm.save(output_file), timeout=self.timeout_sec)

    def _validate_mp3_file(self, file_path: Path, scene_id: int, stage_desc: str) -> mutagen.mp3.MP3:
        """Verify that MP3 file exists, exceeds 1024 bytes, and mutagen parses valid metadata."""
        if not file_path.is_file():
            raise AudioGenerationError(
                f"Phân cảnh {scene_id}: Tệp âm thanh ({stage_desc}) không tồn tại: {file_path}"
            )

        size = file_path.stat().st_size
        if size <= 1024:
            raise AudioGenerationError(
                f"Phân cảnh {scene_id}: Tệp âm thanh ({stage_desc}) có kích thước quá nhỏ ({size} bytes <= 1024 bytes)."
            )

        try:
            audio = mutagen.mp3.MP3(str(file_path))
        except Exception as exc:
            raise AudioGenerationError(
                f"Phân cảnh {scene_id}: Mutagen không thể đọc định dạng MP3 ({stage_desc}): {exc}",
                cause=exc,
            ) from exc

        if not audio.info or audio.info.length <= 0.5:
            duration = audio.info.length if audio.info else 0.0
            raise AudioGenerationError(
                f"Phân cảnh {scene_id}: Thời lượng âm thanh ({stage_desc}) không hợp lệ ({duration:.3f}s <= 0.5s)."
            )

        return audio

    def _apply_silence_padding(
        self, source_path: Path, target_path: Path, scene_id: int, raw_duration: float
    ) -> float:
        """Append 0.30s silence tail using Pydub and verify duration increase with Mutagen."""
        try:
            sound = AudioSegment.from_file(str(source_path))
        except Exception as exc:
            raise AudioGenerationError(
                f"Phân cảnh {scene_id}: Pydub không thể giải mã tệp âm thanh nguồn: {exc}",
                cause=exc,
            ) from exc

        padding_ms = int(round(self.audio_padding_sec * 1000.0))
        silence = AudioSegment.silent(duration=padding_ms)
        padded_sound = sound + silence

        try:
            # Export with 128k bitrate
            padded_sound.export(str(target_path), format="mp3", bitrate="128k")
        except Exception as exc:
            raise AudioGenerationError(
                f"Phân cảnh {scene_id}: Lỗi xuất tệp MP3 sau khi đệm khoảng lặng: {exc}",
                cause=exc,
            ) from exc

        # Read back with Mutagen
        padded_meta = self._validate_mp3_file(target_path, scene_id=scene_id, stage_desc="padded silence")
        padded_duration = padded_meta.info.length
        duration_delta = padded_duration - raw_duration

        # MP3 frame quantization tolerance: [0.25s, 0.38s] for 0.300s target
        if not (0.25 <= duration_delta <= 0.38):
            logger.warning(
                f"Scene {scene_id}: Duration delta {duration_delta:.3f}s deviated slightly from "
                f"expected padding {self.audio_padding_sec:.3f}s due to MP3 frame boundary."
            )

        return padded_duration
