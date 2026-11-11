"""Tiny code-generated nursery-style backing track (no copyrighted music)."""
import numpy as np

SR = 24000
# C major pentatonic: always sounds happy, never clashes
SCALE = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25]
PATTERN = [0, 2, 4, 2, 3, 1, 2, 0]  # simple repeating tune


def _note(freq: float, dur: float) -> np.ndarray:
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    tone = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * 2 * freq * t)
    env = np.minimum(1, t / 0.02) * np.exp(-3.0 * t / dur)  # pluck-like
    return (tone * env).astype(np.float32)


def backing_track(seconds: float, bpm: int = 100, volume: float = 0.12) -> np.ndarray:
    beat = 60.0 / bpm
    out = []
    total = 0.0
    i = 0
    while total < seconds:
        out.append(_note(SCALE[PATTERN[i % len(PATTERN)]], beat))
        total += beat
        i += 1
    audio = np.concatenate(out)[: int(seconds * SR)]
    return (audio * volume).astype(np.float32)
