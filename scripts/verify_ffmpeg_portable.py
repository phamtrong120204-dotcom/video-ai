"""Verification Script for FFmpeg Portable (Binary existence, version, codecs, test MP4 render & ffprobe)."""

import json
import os
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list[str]) -> str:
    """Run command and return stdout as string, raise on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def verify_ffmpeg():
    print("==================================================")
    print("PRE-STAGE 4.2: FFMPEG PORTABLE VERIFICATION")
    print("==================================================")

    ffmpeg_bin = Path(r"C:\ffmpeg\bin\ffmpeg.exe")
    ffprobe_bin = Path(r"C:\ffmpeg\bin\ffprobe.exe")

    # 1. Check executable paths
    print("STEP 1: Checking binary existence...")
    print(f"  ffmpeg : {ffmpeg_bin} -> {ffmpeg_bin.is_file()}")
    print(f"  ffprobe: {ffprobe_bin} -> {ffprobe_bin.is_file()}")

    if not ffmpeg_bin.is_file() or not ffprobe_bin.is_file():
        print("ERROR: FFmpeg or FFprobe executable not found!", file=sys.stderr)
        sys.exit(1)

    # 2. Check versions
    print("\nSTEP 2: Checking versions...")
    ffmpeg_ver = run_cmd([str(ffmpeg_bin), "-version"]).splitlines()[0]
    ffprobe_ver = run_cmd([str(ffprobe_bin), "-version"]).splitlines()[0]
    print(f"  [ffmpeg]  {ffmpeg_ver}")
    print(f"  [ffprobe] {ffprobe_ver}")

    # 3. Check encoders
    print("\nSTEP 3: Checking required encoders (libx264, aac)...")
    encoders_out = run_cmd([str(ffmpeg_bin), "-encoders"])

    has_libx264 = "libx264" in encoders_out
    has_aac = "aac" in encoders_out

    print(f"  Encoder libx264 available: {has_libx264}")
    print(f"  Encoder aac available    : {has_aac}")

    if not has_libx264 or not has_aac:
        print("ERROR: Required encoders missing!", file=sys.stderr)
        sys.exit(2)

    # 4. Generate 1-second 1080x1920 test MP4
    print("\nSTEP 4: Rendering 1.0s 1080x1920 test MP4 video with FFmpeg...")
    test_video_path = Path("out") / "test_ffmpeg_probe.mp4"
    test_video_path.parent.mkdir(parents=True, exist_ok=True)
    if test_video_path.exists():
        test_video_path.unlink()

    render_cmd = [
        str(ffmpeg_bin),
        "-y",
        "-f", "lavfi",
        "-i", "color=c=black:s=1080x1920:r=30:d=1.0",
        "-f", "lavfi",
        "-i", "anullsrc=r=44100:cl=mono",
        "-t", "1.0",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        str(test_video_path.resolve()),
    ]
    subprocess.run(render_cmd, capture_output=True, text=True, check=True)

    assert test_video_path.is_file(), "Test MP4 video was not created!"
    file_size = test_video_path.stat().st_size
    print(f"  Test MP4 generated successfully: {test_video_path.resolve()}")
    print(f"  File size: {file_size} bytes (> 0)")
    assert file_size > 1024, "File size too small!"

    # 5. Inspect with ffprobe (JSON output)
    print("\nSTEP 5: Verifying video with ffprobe JSON metadata...")
    probe_cmd = [
        str(ffprobe_bin),
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(test_video_path.resolve()),
    ]
    probe_json_str = run_cmd(probe_cmd)
    probe_data = json.loads(probe_json_str)

    streams = probe_data.get("streams", [])
    format_info = probe_data.get("format", {})

    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

    assert len(video_streams) == 1, "Expected 1 video stream"
    assert len(audio_streams) == 1, "Expected 1 audio stream"

    v_stream = video_streams[0]
    a_stream = audio_streams[0]

    v_codec = v_stream.get("codec_name")
    v_width = v_stream.get("width")
    v_height = v_stream.get("height")
    a_codec = a_stream.get("codec_name")
    duration = float(format_info.get("duration", 0.0))

    print(f"  Video Codec     : {v_codec} (Expected: h264)")
    print(f"  Resolution      : {v_width}x{v_height} (Expected: 1080x1920)")
    print(f"  Audio Codec     : {a_codec} (Expected: aac)")
    print(f"  Duration        : {duration:.3f}s (Expected: ~1.0s)")

    assert v_codec == "h264", f"Video codec mismatch: {v_codec}"
    assert v_width == 1080 and v_height == 1920, f"Resolution mismatch: {v_width}x{v_height}"
    assert a_codec == "aac", f"Audio codec mismatch: {a_codec}"
    assert 0.9 <= duration <= 1.2, f"Duration mismatch: {duration}"

    # Cleanup
    if test_video_path.exists():
        test_video_path.unlink()
        print("  Cleaned up test video.")

    print("\n==================================================")
    print("FFMPEG & FFPROBE PORTABLE VERIFICATION: ALL 5 STEPS PASSED")
    print("==================================================")


if __name__ == "__main__":
    verify_ffmpeg()
