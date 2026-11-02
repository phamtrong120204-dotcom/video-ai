"""Integration Verification Script for Stage 4.2 Vietnamese TTS Engine & Audio Timing.

This script tests the end-to-end integration between:
1. RuleBasedScriptParser (Vietnamese text -> SceneSchema[])
2. EdgeTTSAudioEngine (Real Edge-TTS synthesis + 0.30s silence padding + Mutagen measurement)
3. FFprobe cross-verification of real generated MP3 audio files.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import time

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

# Ensure C:\ffmpeg\bin is in PATH
FFMPEG_BIN_DIR = r"C:\ffmpeg\bin"
if Path(FFMPEG_BIN_DIR).is_dir() and FFMPEG_BIN_DIR.lower() not in os.environ.get("PATH", "").lower():
    os.environ["PATH"] = f"{FFMPEG_BIN_DIR};{os.environ.get('PATH', '')}"

import mutagen.mp3

from app.core.config import get_config
from app.core.logger import get_logger
from app.modules.audio.edge_tts_engine import EdgeTTSAudioEngine
from app.modules.parser import RuleBasedScriptParser
from app.schemas.script_schema import ScriptInput, SourceChannel

logger = get_logger("verify_tts_integration")

SAMPLE_5_SCENE_SCRIPT = """Cảnh 1: Giữa trang giấy nhuốm mực đen u ám, Tôn Ngộ Không tay nắm chặt Như Ý Kim Cô Bổng, đôi mắt đỏ rực đứng đối diện chiến thần Nhị Lang Thần.
Cảnh 2: Nhị Lang Thần vung Tam Tiêm Đao chém xé toạc không gian, từng vệt mực đen bắn tung tóe quanh chiến trường.
Cảnh 3: Ngộ Không gầm vang một tiếng, thân hình bộc phát hắc khí cuồn cuộn, vung Thiết Bổng đánh tan thế công của thiên binh vạn mã.
Cảnh 4: Bầu trời trang vở bỗng rạn nứt dữ dội, một bàn tay Phật Tổ khổng lồ từ tầng mây đen giáng thẳng xuống đỉnh đầu Thạch Hầu.
Cảnh 5: Kim Cô Bổng gãy đôi cắm sâu vào mặt giấy, bóng đen Ngộ Không ngạo nghễ ngước nhìn trời cao dù thân xác đang dần hóa thành tro bụi."""


def run_ffprobe(file_path: Path, ffprobe_exe: str) -> dict:
    """Extract format and audio stream info using portable ffprobe."""
    cmd = [
        ffprobe_exe,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(file_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


def main():
    print("=" * 80)
    print("STAGE 4.2: VIETNAMESE TTS ENGINE & AUDIO TIMING INTEGRATION VERIFICATION")
    print("=" * 80)

    cfg = get_config()
    ffprobe_exe = cfg.ffprobe_path or r"C:\ffmpeg\bin\ffprobe.exe"
    if not Path(ffprobe_exe).is_file():
        print(f"ERROR: ffprobe not found at {ffprobe_exe}")
        sys.exit(1)

    output_dir = WORKSPACE_ROOT / "out" / "temp" / "integration_tts" / "audio"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Parse Script to SceneSchema[]
    print("\n[Step 1] Parsing 5-scene Vietnamese dark myth script...")
    parser = RuleBasedScriptParser()
    script_input = ScriptInput(
        job_id="job_integration_stage_4_2",
        source_channel=SourceChannel.CLI_TEST,
        title="Đại Thánh Trầm Luân - 5 Phân Cảnh Thử Nghiệm",
        raw_script_text=SAMPLE_5_SCENE_SCRIPT,
        voice_id="vi-VN-NamMinhNeural",
        voice_speed=1.05,
    )
    scenes = parser.parse(script_input)
    print(f"-> Parsed {len(scenes)} scenes successfully:")
    for s in scenes:
        print(f"   Scene {s.scene_id}: action={s.action_preset.value}, bg={s.background_state.value}")
        print(f"   Narration: {s.narration_text[:60]}...")

    assert len(scenes) == 5, f"Expected 5 scenes, got {len(scenes)}"

    # 2. Instantiate EdgeTTSAudioEngine
    print("\n[Step 2] Initializing EdgeTTSAudioEngine (speed=1.05, padding=0.30s)...")
    engine = EdgeTTSAudioEngine(
        voice_id="vi-VN-NamMinhNeural",
        fallback_voice_id="vi-VN-HoaiMyNeural",
        voice_speed=1.05,
        audio_padding_sec=0.30,
        max_retries=3,
        base_backoff_sec=1.0,
        lock_voice_per_job=True,
    )

    # 3. Generate Audio for all 5 scenes
    print("\n[Step 3] Calling Edge-TTS online API and applying audio padding for each scene...")
    results = []
    total_start_time = time.time()

    for idx, scene in enumerate(scenes, start=1):
        print(f"\n--- Synthesizing Scene {scene.scene_id}/5 ---")
        scene_start = time.time()
        final_path, duration = engine.generate_scene_audio(scene, output_dir)
        elapsed = time.time() - scene_start

        # Cross-verify with Mutagen
        mut_file = mutagen.mp3.MP3(str(final_path))
        file_size = final_path.stat().st_size
        mut_duration = mut_file.info.length
        mut_bitrate = mut_file.info.bitrate
        mut_sample_rate = mut_file.info.sample_rate
        mut_channels = mut_file.info.channels

        # Cross-verify with FFprobe
        probe_data = run_ffprobe(final_path, ffprobe_exe)
        probe_format = probe_data.get("format", {})
        probe_duration = float(probe_format.get("duration", 0.0))
        audio_streams = [s for s in probe_data.get("streams", []) if s.get("codec_type") == "audio"]
        codec_name = audio_streams[0].get("codec_name") if audio_streams else "unknown"

        print(f"   File: {final_path.name}")
        print(f"   Size: {file_size:,} bytes")
        print(f"   Synthesis & Padding Time: {elapsed:.2f}s")
        print(f"   Mutagen Measured Duration: {mut_duration:.3f}s")
        print(f"   FFprobe Measured Duration: {probe_duration:.3f}s")
        print(f"   Audio Codec: {codec_name}, Sample Rate: {mut_sample_rate}Hz, Bitrate: {mut_bitrate // 1000}kbps")
        print(f"   Scene Schema duration updated: {scene.audio_duration_sec:.3f}s")
        print(f"   Scene Schema path updated: {scene.voice_audio_path}")

        # Assertions
        assert final_path.is_file(), f"File {final_path} does not exist"
        assert file_size > 1024, f"File {final_path} size {file_size} <= 1024 bytes"
        assert mut_duration > 1.0, f"Duration {mut_duration}s too short"
        assert abs(mut_duration - probe_duration) < 0.1, "Mutagen and FFprobe duration mismatch"
        assert abs(scene.audio_duration_sec - probe_duration) < 1e-3, "SceneSchema duration mismatch with authoritative FFprobe duration"
        assert codec_name == "mp3", f"Expected mp3 codec, got {codec_name}"

        results.append({
            "scene_id": scene.scene_id,
            "narration_text": scene.narration_text,
            "filename": final_path.name,
            "file_path": str(final_path.resolve()),
            "file_size_bytes": file_size,
            "elapsed_synthesis_sec": round(elapsed, 2),
            "audio_duration_sec": round(mut_duration, 3),
            "ffprobe_duration_sec": round(probe_duration, 3),
            "bitrate_kbps": mut_bitrate // 1000,
            "sample_rate_hz": mut_sample_rate,
            "channels": mut_channels,
            "active_voice_id": engine.active_voice_id,
        })
        time.sleep(0.5)

    total_elapsed = time.time() - total_start_time
    total_audio_duration = sum(r["audio_duration_sec"] for r in results)

    # 4. Save structured results JSON
    report_data = {
        "status": "success",
        "job_id": script_input.job_id,
        "title": script_input.title,
        "active_voice_id": engine.active_voice_id,
        "total_scenes": len(results),
        "total_audio_duration_sec": round(total_audio_duration, 3),
        "total_pipeline_elapsed_sec": round(total_elapsed, 2),
        "output_directory": str(output_dir.resolve()),
        "scenes": results,
    }

    report_path = WORKSPACE_ROOT / "out" / "sample_tts_results.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("INTEGRATION VERIFICATION SUMMARY:")
    print(f"Total Scenes: {len(results)}")
    print(f"Total Audio Duration: {total_audio_duration:.2f} seconds")
    print(f"Total Generation Time: {total_elapsed:.2f} seconds")
    print(f"Active Voice Used: {engine.active_voice_id}")
    print(f"Report saved to: {report_path}")
    print("ALL 5 SCENES GENERATED, PADDED, MUTAGEN-VERIFIED, AND FFPROBE-VALIDATED!")
    print("=" * 80)


if __name__ == "__main__":
    main()
