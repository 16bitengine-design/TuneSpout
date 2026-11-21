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
import real_photos
from characters.cast import voice_for
from kids_scene import plan_positions
from metadata import write_metadata
from safety import check_lesson

FPS = 24
SR = tts.SR
PAUSE = 0.6


def mouth_envelope(audio):
    """Mouth openness (0..1) for each video frame of a line, from its loudness, so the
    lips open on the sounds and close in the gaps. Empty for silent (test) audio."""
    hop = SR // FPS
    n = len(audio) // hop
    if n == 0:
        return []
    rms = np.sqrt(np.mean(audio[: n * hop].reshape(n, hop) ** 2, axis=1))
    if rms.max() < 1e-4:
        return []
    level = np.clip(rms / (np.percentile(rms, 90) + 1e-9), 0, 1) ** 0.8
    level[level < 0.12] = 0.0
    return [float(x) for x in np.convolve(level, [0.25, 0.5, 0.25], mode="same")]  # seconds of breathing room after each line


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

    # real photos: when a lesson names something from the real world, cut to a real photo of it
    cues, records = [], []
    try:
        lex = real_photos.Lexicon.load()
        cues = real_photos.cues_for_scenes(lesson["scenes"], durations, lex, pause=PAUSE)
        cues, records = real_photos.prepare_cues(cues, lex, size=(render.W, render.H))
    except Exception as err:  # photos are a bonus: never stop the daily video because of them
        print("Real photos skipped:", err)
        cues, records = [], []

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
    start = 0.0  # where this scene begins in the episode, so photo cues line up
    for sc, dur in zip(lesson["scenes"], durations):
        for f in range(int(dur * FPS)):
            t = start + f / FPS
            frame = render.draw_scene(sc, f / FPS)
            frame = real_photos.apply_cue(frame, real_photos.active_cue(cues, t), t)
            proc.stdin.write(frame.tobytes())
        start += dur
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg failed")

    # automatic titles, descriptions and hashtags
    write_metadata(lesson, out)
    real_photos.add_credits_to_meta(out / "meta.json", records)  # credits: YouTube description only
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
    for sc in lesson["scenes"]:  # [[orange]] style photo tags: keep for the photos, hide from voice and captions
        sc["_tagged"] = sc.get("line", "")
        sc["line"] = real_photos.strip_tags(sc["line"])
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # voice for each scene; scene length = length of its audio
    clips, durations = [], []
    for sc in lesson["scenes"]:
        voice, speed, pitch = (voice_for(sc.get("speaker")) or
                               (lesson.get("voice", "af_heart"), lesson.get("speed", 0.9),
                                lesson.get("pitch", 1.2)))
        a = tts.speak(sc["line"], voice, speed, pitch, fake=args.fake_tts)
        env = mouth_envelope(a)
        if env:
            sc["_env"] = env  # the mouths follow the real audio
        a = np.concatenate([a, np.zeros(int(PAUSE * SR), dtype=np.float32)])
        clips.append(a)
        durations.append(len(a) / SR)

    plan_positions(lesson["scenes"])  # who stands where, so the kids walk around

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
