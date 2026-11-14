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

import episodes
import music
import render
import tts
import branding
from characters.cast import voice_for
from metadata import write_metadata
from safety import check_lesson

FPS = 24
SR = tts.SR
PAUSE = 0.6  # seconds of breathing room after each line


def render_episode(lesson, clips, durations, out):
    """Mix the audio, draw the frames and write one episode's files into out/."""
    out.mkdir(parents=True, exist_ok=True)
    voice = np.concatenate(clips)
    seconds = len(voice) / SR
    tune = lesson.get("tune")
    bed = music.tune_track(tune, seconds) if tune else music.backing_track(seconds)
    mix = np.clip(voice[: len(bed)] + bed[: len(voice)], -1, 1)
    wav = out / "audio.wav"
    sf.write(wav, mix, SR)

    mp4 = out / "video.mp4"
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{render.W}x{render.H}",
        "-r", str(FPS), "-i", "-", "-i", str(wav),
        "-vf", "scale=1080:1920:flags=lanczos",  # drawn at 720x1280, saved at full 1080x1920
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

    # automatic titles, descriptions and hashtags
    write_metadata(lesson, out)
    try:
        branding.thumbnail(lesson).save(out / "thumbnail.png", optimize=True)
    except StopIteration:  # a hand-written lesson with no kids: no thumbnail
        print("No kids in this lesson, so no thumbnail was made.")
    print(f"Done: {mp4} ({sum(durations):.1f}s, vertical 1080x1920)")


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

    # voice for each scene; scene length = length of its audio
    clips, durations = [], []
    for sc in lesson["scenes"]:
        voice, speed, pitch = (voice_for(sc.get("speaker")) or
                               (lesson.get("voice", "af_heart"), lesson.get("speed", 0.9),
                                lesson.get("pitch", 1.2)))
        a = tts.speak(sc["line"], voice, speed, pitch, fake=args.fake_tts)
        a = np.concatenate([a, np.zeros(int(PAUSE * SR), dtype=np.float32)])
        clips.append(a)
        durations.append(len(a) / SR)

    # one video, or (over three minutes) episodes of about two minutes each
    ranges = episodes.split(durations)
    folders = []
    for number, (first, last) in enumerate(ranges, 1):
        part = {**lesson, "scenes": lesson["scenes"][first:last],
                "title": episodes.episode_title(lesson["title"], number, len(ranges))}
        folder = out if len(ranges) == 1 else out / f"ep{number}"
        render_episode(part, clips[first:last], durations[first:last], folder)
        folders.append(str(folder.relative_to(out)) if folder != out else ".")
    (out / "episodes.json").write_text(json.dumps(folders))
    if len(ranges) > 1:
        print(f"Split into {len(ranges)} episodes.")


if __name__ == "__main__":
    main()
