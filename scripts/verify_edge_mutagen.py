"""Verification Script for Edge-TTS + Mutagen Integration.

Tests Edge-TTS synthesis with retry/backoff and verifies duration with Mutagen.
"""

import asyncio
import os
import sys
import time

import edge_tts
import mutagen.mp3


async def synthesize_with_retry(
    text: str, voice: str, output_path: str, max_retries: int = 3
) -> bool:
    """Synthesize speech using Edge-TTS with exponential backoff retry."""
    for attempt in range(1, max_retries + 1):
        try:
            print(f"  [Attempt {attempt}/{max_retries}] Connecting to Edge-TTS service...")
            if os.path.exists(output_path):
                os.remove(output_path)

            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)

            if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
                print(f"  [Attempt {attempt}] Synthesis succeeded: {os.path.getsize(output_path)} bytes.")
                return True
            else:
                print(f"  [Attempt {attempt}] File too small or missing, retrying...")
        except edge_tts.exceptions.NoAudioReceived as e:
            print(f"  [Attempt {attempt}] NoAudioReceived warning: {e}")
        except Exception as e:
            print(f"  [Attempt {attempt}] Unexpected error: {type(e).__name__}: {e}")

        if attempt < max_retries:
            wait_time = attempt * 1.5
            print(f"  Waiting {wait_time:.1f}s before retry...")
            await asyncio.sleep(wait_time)

    return False


async def run_verification():
    test_file = os.path.abspath("test_edge_mutagen_output.mp3")
    text = "Tôn Ngộ Không đại náo thiên cung trên trang giấy vở học sinh."
    voice = "vi-VN-NamMinhNeural"

    print("==================================================")
    print("STEP 1: Starting Edge-TTS synthesis with retry")
    print(f"  Target Text : {text}")
    print(f"  Target Voice: {voice}")
    print(f"  Output Path : {test_file}")
    print("==================================================")

    start_time = time.time()
    success = await synthesize_with_retry(text, voice, test_file, max_retries=3)
    elapsed = time.time() - start_time

    if not success:
        # Fallback to secondary voice vi-VN-HoaiMyNeural if NamMinh service node is degraded
        print("  Notice: Primary voice node had transient failure, trying vi-VN-HoaiMyNeural...")
        voice = "vi-VN-HoaiMyNeural"
        success = await synthesize_with_retry(text, voice, test_file, max_retries=3)
        if not success:
            print(f"ERROR: Synthesis failed after all retries across voices!", file=sys.stderr)
            sys.exit(1)

    # STEP 2: Verify file existence and size > 0
    if not os.path.exists(test_file):
        print(f"ERROR: File {test_file} does not exist!", file=sys.stderr)
        sys.exit(1)

    file_size = os.path.getsize(test_file)
    print("==================================================")
    print("STEP 2: File verified on disk:")
    print(f"  Path: {test_file}")
    print(f"  Size: {file_size} bytes (> 1024 bytes required)")
    print(f"  Elapsed Synthesis Time: {elapsed:.2f}s")
    print("==================================================")

    if file_size <= 1024:
        print(f"ERROR: File size {file_size} is <= 1024 bytes!", file=sys.stderr)
        sys.exit(2)

    # STEP 3 & 4: Mutagen reads duration and metadata
    print("STEP 3: Opening MP3 with mutagen.mp3.MP3...")
    audio = mutagen.mp3.MP3(test_file)

    duration = audio.info.length
    bitrate = audio.info.bitrate
    sample_rate = audio.info.sample_rate
    channels = audio.info.channels

    print("==================================================")
    print("STEP 4: Mutagen parsed audio metadata:")
    print(f"  Duration    : {duration:.3f} seconds")
    print(f"  Bitrate     : {bitrate} bps ({bitrate // 1000} kbps)")
    print(f"  Sample Rate : {sample_rate} Hz")
    print(f"  Channels    : {channels}")
    print("==================================================")

    # STEP 5: Confirm duration > 0.5s
    if duration <= 0.5:
        print(f"ERROR: Duration {duration}s <= 0.5s!", file=sys.stderr)
        sys.exit(3)

    print(f"STEP 5: Duration verification passed: {duration:.3f}s > 0.5s")

    # Cleanup temporary test file
    if os.path.exists(test_file):
        os.remove(test_file)
        print("  Cleaned up temporary output file.")

    print("==================================================")
    print("ALL 5 VERIFICATION STEPS PASSED SUCCESSFULLY.")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_verification())
