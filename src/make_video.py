"""Build one video from a lesson JSON.

Usage:
  python src/generate_lesson.py --topic addition --out out/lesson.json
  python src/make_video.py out/lesson.json              # real Kokoro voice
  python src/make_video.py out/lesson.json --fake-tts   # offline test
"""
import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

import music
import render
import tts
from metadata import write_metadata
from safety import check_lesson

FPS = 24
SR = tts.SR
PAUSE = 0.6  # seconds of breathing room after each line


def make_vertical(src, dst):
    """9:16 copy for TikTok: the video centered on a sky-blue top and green bottom."""
    graph = ("color=c=0x8fd0f8:s=1080x1920,drawbox=y=1100:w=1080:h=820:color=0x78c86e:t=fill[bg];"
             "[0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2:shortest=1,format=yuv420p")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
                    "-filter_complex", graph, "-c:v", "libx264", "-preset", "veryfast",
                    "-c:a", "copy", str(dst)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson")
    ap.add_argument("--out", default="out")
    ap.add_argument("--fake-tts", action="store_true")
    args = ap.parse_args()

    lesson = json.loads(Path(args.lesson).read_text())
    check_lesson(lesson)  # raises if anything is not kid-safe
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # 1) voice for each scene; scene length = length of its audio
    clips, durations = [], []
    for sc in lesson["scenes"]:
        a = tts.speak(sc["line"], lesson.get("voice", "af_heart"),
                      lesson.get("speed", 0.9), lesson.get("pitch", 1.2),
                      fake=args.fake_tts)
        a = np.concatenate([a, np.zeros(int(PAUSE * SR), dtype=np.float32)])
        clips.append(a)
        durations.append(len(a) / SR)

    voice = np.concatenate(clips)
    seconds = len(voice) / SR
    tune = lesson.get("tune")
    bed = music.tune_track(tune, seconds) if tune else music.backing_track(seconds)
    mix = np.clip(voice[: len(bed)] + bed[: len(voice)], -1, 1)
    wav = out / "audio.wav"
    sf.write(wav, mix, SR)

    # 2) frames piped straight into ffmpeg
    mp4 = out / "video.mp4"
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{render.W}x{render.H}",
        "-r", str(FPS), "-i", "-", "-i", str(wav),
        "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-shortest", str(mp4),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for sc, dur in zip(lesson["scenes"], durations):
        for f in range(int(dur * FPS)):
            frame = render.draw_scene(sc, f / FPS)
            proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg failed")

    # 3) automatic titles, descriptions and hashtags, plus the vertical TikTok version
    write_metadata(lesson, out)
    make_vertical(mp4, out / "video_vertical.mp4")
    print(f"Done: {mp4} and video_vertical.mp4 ({sum(durations):.1f}s)")


if __name__ == "__main__":
    main()
