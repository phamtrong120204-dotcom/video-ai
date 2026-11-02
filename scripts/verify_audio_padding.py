"""Verification of Audio Processing: Pydub 0.30s Silence Padding + Mutagen Duration Measurement."""

import os
import subprocess
import sys
from pathlib import Path

# Add C:\ffmpeg\bin to local process PATH for pydub invocation
os.environ["PATH"] = r"C:\ffmpeg\bin;" + os.environ.get("PATH", "")

import mutagen.mp3
from pydub import AudioSegment


def generate_source_mp3(path: str, duration_sec: float = 2.0) -> None:
    """Generate a clean 440Hz test sine tone MP3 using portable FFmpeg."""
    cmd = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        "-y",
        "-f", "lavfi",
        "-i", f"sine=frequency=440:duration={duration_sec}",
        "-c:a", "libmp3lame",
        "-b:a", "128k",
        "-ar", "44100",
        path,
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)


def test_audio_padding_flow():
    print("==================================================")
    print("PRE-STAGE 4.2: AUDIO PADDING VERIFICATION")
    print("==================================================")

    out_dir = Path("out")
    out_dir.mkdir(parents=True, exist_ok=True)

    source_path = str(out_dir / "test_padding_source.mp3")
    padded_path = str(out_dir / "test_padding_padded.mp3")

    # 1. Prepare valid source MP3
    print("STEP 1: Generating source MP3 using FFmpeg...")
    generate_source_mp3(source_path, duration_sec=2.0)

    assert os.path.exists(source_path), "Source MP3 was not generated!"
    source_size = os.path.getsize(source_path)
    print(f"  Source file generated: {source_path} ({source_size} bytes)")
    assert source_size > 1024, "Source MP3 file too small!"

    # 2. Measure initial duration with Mutagen
    print("\nSTEP 2: Measuring initial duration with Mutagen...")
    meta_initial = mutagen.mp3.MP3(source_path)
    initial_duration = meta_initial.info.length
    sample_rate = meta_initial.info.sample_rate
    bitrate = meta_initial.info.bitrate
    print(f"  Initial Duration : {initial_duration:.3f}s")
    print(f"  Sample Rate      : {sample_rate} Hz")
    print(f"  Bitrate          : {bitrate} bps ({bitrate // 1000} kbps)")

    # 3. Load with Pydub and append 300ms (0.30s) silence
    print("\nSTEP 3: Opening with Pydub and appending 300ms (0.30s) silence...")
    sound = AudioSegment.from_file(source_path)
    initial_pydub_len_ms = len(sound)
    print(f"  Pydub parsed sound length: {initial_pydub_len_ms} ms")

    silence = AudioSegment.silent(duration=300)
    padded_sound = sound + silence
    padded_pydub_len_ms = len(padded_sound)
    delta_ms = padded_pydub_len_ms - initial_pydub_len_ms
    print(f"  Padded sound length: {padded_pydub_len_ms} ms (added {delta_ms} ms)")
    assert delta_ms == 300, f"Expected 300ms added, got {delta_ms}ms"

    # 4. Export padded sound to MP3
    print("\nSTEP 4: Exporting padded audio to MP3...")
    padded_sound.export(padded_path, format="mp3", bitrate="128k")

    assert os.path.exists(padded_path), "Padded MP3 was not exported!"
    padded_size = os.path.getsize(padded_path)
    print(f"  Padded file exported: {padded_path} ({padded_size} bytes)")
    assert padded_size > 1024, "Padded MP3 file too small!"

    # 5. Measure padded duration with Mutagen
    print("\nSTEP 5: Measuring padded duration with Mutagen...")
    meta_padded = mutagen.mp3.MP3(padded_path)
    padded_duration = meta_padded.info.length
    duration_delta = padded_duration - initial_duration
    print(f"  Padded Duration         : {padded_duration:.3f}s")
    print(f"  Delta (Padded - Initial): {duration_delta:.3f}s (Target: ~0.300s)")

    # 6. Verify duration increase is within acceptable MP3 frame tolerance
    print("\nSTEP 6: Validating duration delta tolerance...")
    # MP3 frames (1152 samples per frame = ~26.1ms at 44.1kHz) cause slight container padding
    assert 0.28 <= duration_delta <= 0.35, f"Delta {duration_delta:.3f}s outside acceptable range [0.28s, 0.35s]!"
    print(f"  Tolerance check PASSED: {duration_delta:.3f}s is within expected range [0.28s, 0.35s].")

    # 7. Check file integrity
    print("\nSTEP 7: Checking audio file integrity...")
    assert meta_padded.info.channels >= 1
    assert meta_padded.info.sample_rate == 44100
    assert padded_size > source_size, "Padded size should be greater than source size"
    print("  Audio integrity confirmed: channels, sample rate, and size verified.")

    # Cleanup test files
    if os.path.exists(source_path):
        os.remove(source_path)
    if os.path.exists(padded_path):
        os.remove(padded_path)
    print("  Cleaned up temporary test files.")

    print("\n==================================================")
    print("AUDIO PADDING VERIFICATION PASSED (ALL 7 STEPS)")
    print("==================================================")


if __name__ == "__main__":
    test_audio_padding_flow()
