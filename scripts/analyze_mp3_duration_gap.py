"""In-depth QA analysis of MP3 duration discrepancies across Mutagen, FFprobe, and decoded PCM samples."""

import json
from pathlib import Path
import subprocess
import mutagen.mp3

FFMPEG_EXE = r"C:\ffmpeg\bin\ffmpeg.exe"
FFPROBE_EXE = r"C:\ffmpeg\bin\ffprobe.exe"
AUDIO_DIR = Path("out/temp/integration_tts/audio")


def analyze_file(mp3_path: Path):
    # 1. Mutagen
    mut = mutagen.mp3.MP3(str(mp3_path))
    mut_dur = mut.info.length
    mut_bitrate = mut.info.bitrate
    mut_sample_rate = mut.info.sample_rate
    mut_channels = mut.info.channels

    # 2. FFprobe format & stream
    cmd_probe = [
        FFPROBE_EXE,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(mp3_path),
    ]
    probe_res = subprocess.run(cmd_probe, capture_output=True, text=True, check=True)
    probe_data = json.loads(probe_res.stdout)
    fmt_dur = float(probe_data.get("format", {}).get("duration", 0.0))
    
    stream_info = probe_data.get("streams", [{}])[0]
    stream_dur = float(stream_info.get("duration", 0.0)) if "duration" in stream_info else None
    stream_sr = int(stream_info.get("sample_rate", mut_sample_rate))
    stream_channels = int(stream_info.get("channels", mut_channels))

    # 3. Decode MP3 to raw PCM (s16le) with FFmpeg
    # We do NOT resample: we keep original sample rate and channels
    cmd_decode = [
        FFMPEG_EXE,
        "-v", "quiet",
        "-i", str(mp3_path),
        "-f", "s16le",
        "-acodec", "pcm_s16le",
        "-"
    ]
    decode_res = subprocess.run(cmd_decode, capture_output=True, check=True)
    pcm_bytes = decode_res.stdout
    bytes_per_sample = 2 * stream_channels
    pcm_samples = len(pcm_bytes) // bytes_per_sample
    pcm_dur = pcm_samples / stream_sr

    # 4. Check frames and packet count using ffprobe
    cmd_packets = [
        FFPROBE_EXE,
        "-v", "error",
        "-select_streams", "a:0",
        "-count_frames",
        "-show_entries", "stream=nb_read_frames",
        "-print_format", "json",
        str(mp3_path)
    ]
    pkt_res = subprocess.run(cmd_packets, capture_output=True, text=True, check=True)
    pkt_data = json.loads(pkt_res.stdout)
    nb_frames = int(pkt_data["streams"][0].get("nb_read_frames", 0))

    # Samples per MP3 frame: MPEG 2 / 2.5 Layer III is 576 samples per frame (at 24000Hz), MPEG 1 Layer III is 1152 samples
    # For MPEG-2/2.5 Layer III (24000Hz), 1 frame = 576 samples
    samples_per_frame = 576 if mut_sample_rate in (16000, 22050, 24000) else 1152
    frame_calc_duration = (nb_frames * samples_per_frame) / stream_sr

    return {
        "file": mp3_path.name,
        "sample_rate": stream_sr,
        "channels": stream_channels,
        "nb_frames": nb_frames,
        "samples_per_frame": samples_per_frame,
        "mutagen_duration": mut_dur,
        "ffprobe_format_duration": fmt_dur,
        "ffprobe_stream_duration": stream_dur,
        "pcm_samples": pcm_samples,
        "pcm_duration": pcm_dur,
        "frame_calc_duration": frame_calc_duration,
        "delta_mutagen_pcm": mut_dur - pcm_dur,
        "delta_ffprobe_pcm": fmt_dur - pcm_dur,
        "delta_mutagen_ffprobe": mut_dur - fmt_dur,
    }


def main():
    files = sorted(AUDIO_DIR.glob("scene_*_voice.mp3"))
    results = []
    for f in files:
        res = analyze_file(f)
        results.append(res)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
