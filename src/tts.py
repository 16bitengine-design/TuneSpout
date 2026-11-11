"""Text-to-speech with Kokoro (open source, runs on CPU).

Kokoro has no true child voices. We use a bright female voice and raise the
pitch slightly (resampling) so it sounds younger. Do NOT clone a real child's
voice without a parent's written consent.
"""
import numpy as np

SR = 24000


def _pitch_up(audio: np.ndarray, factor: float) -> np.ndarray:
    """Raise pitch by `factor` (also shortens audio; compensate with speed)."""
    if abs(factor - 1.0) < 1e-3:
        return audio
    n = int(len(audio) / factor)
    x_old = np.linspace(0, 1, len(audio), endpoint=False)
    x_new = np.linspace(0, 1, n, endpoint=False)
    return np.interp(x_new, x_old, audio).astype(np.float32)


_pipe = None


def _get_pipe():
    global _pipe
    if _pipe is None:
        from kokoro import KPipeline  # pip install kokoro
        _pipe = KPipeline(lang_code="a")  # American English
    return _pipe


def speak(text: str, voice: str = "af_heart", speed: float = 0.9,
          pitch: float = 1.2, fake: bool = False) -> np.ndarray:
    """Return mono float32 audio at 24 kHz for `text`."""
    if fake:  # offline test mode: silence sized like speech
        seconds = max(1.5, len(text.split()) * 0.45)
        return np.zeros(int(seconds * SR), dtype=np.float32)
    pipe = _get_pipe()
    chunks = []
    # slow down by `speed`, and pre-compensate for the pitch resample
    for _, _, audio in pipe(text, voice=voice, speed=speed / pitch):
        chunks.append(np.asarray(audio, dtype=np.float32))
    audio = np.concatenate(chunks) if chunks else np.zeros(SR, dtype=np.float32)
    return _pitch_up(audio, pitch)
