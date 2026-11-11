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


# Public-domain melodies (centuries old), written out as (note, beats).
# We synthesize them ourselves, so there are no recording rights to worry about.
NOTES = {"C3": 130.81, "G3": 196.00, "C4": 261.63, "D4": 293.66, "E4": 329.63,
         "F4": 349.23, "G4": 392.00, "A4": 440.00}
TUNES = {
    # Twinkle, Twinkle, Little Star (French melody, 1700s)
    "twinkle": (100, [("C4", 1), ("C4", 1), ("G4", 1), ("G4", 1), ("A4", 1), ("A4", 1), ("G4", 2),
                      ("F4", 1), ("F4", 1), ("E4", 1), ("E4", 1), ("D4", 1), ("D4", 1), ("C4", 2),
                      ("G4", 1), ("G4", 1), ("F4", 1), ("F4", 1), ("E4", 1), ("E4", 1), ("D4", 2),
                      ("G4", 1), ("G4", 1), ("F4", 1), ("F4", 1), ("E4", 1), ("E4", 1), ("D4", 2)]),
    # Mary Had a Little Lamb (1830s)
    "mary": (110, [("E4", 1), ("D4", 1), ("C4", 1), ("D4", 1), ("E4", 1), ("E4", 1), ("E4", 2),
                   ("D4", 1), ("D4", 1), ("D4", 2), ("E4", 1), ("G4", 1), ("G4", 2),
                   ("E4", 1), ("D4", 1), ("C4", 1), ("D4", 1), ("E4", 1), ("E4", 1), ("E4", 1),
                   ("E4", 1), ("D4", 1), ("D4", 1), ("E4", 1), ("D4", 1), ("C4", 2)]),
    # Row, Row, Row Your Boat (1850s)
    "row": (100, [("C4", 1), ("C4", 1), ("C4", 0.75), ("D4", 0.25), ("E4", 2),
                  ("E4", 0.75), ("D4", 0.25), ("E4", 0.75), ("F4", 0.25), ("G4", 2)]),
}


def tune_track(name: str, seconds: float, volume: float = 0.14) -> np.ndarray:
    """Loop a public-domain tune for `seconds`, with a soft bass underneath."""
    bpm, notes = TUNES[name]
    beat = 60.0 / bpm
    melody, bass = [], []
    total, i = 0.0, 0
    while total < seconds:
        for n, beats in notes:
            melody.append(_note(NOTES[n], beats * beat))
            total += beats * beat
            if total >= seconds:
                break
    n = int(seconds * SR)
    audio = np.concatenate(melody)[:n]
    audio = np.pad(audio, (0, n - len(audio)))  # rounding can leave it a sample short
    # one low bass note every 4 beats
    step = int(4 * beat * SR)
    for start in range(0, len(audio), step):
        root = NOTES["C3"] if (start // step) % 2 == 0 else NOTES["G3"]
        seg = _note(root, 4 * beat)[: len(audio) - start]
        audio[start:start + len(seg)] += 0.5 * seg
    return (audio * volume).astype(np.float32)


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
