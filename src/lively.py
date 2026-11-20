"""Extra life for every scene: themed floating decorations, confetti, a sparkle burst when a
scene starts, and a camera "punch-in" that settles. All drawn by code with Pillow only.

Used by kids_scene.draw_kids_scene. Everything is gentle and kid-safe: stars, letters,
numbers, leaves, hearts and balls drifting in the sky.
"""
import math
import random
from functools import lru_cache

from PIL import Image

import render
from characters.common import ellipse

PALETTE = [(255, 90, 90), (255, 200, 60), (80, 170, 240), (120, 210, 120), (255, 130, 200)]
DECOR_GLYPHS = {
    "literacy": list("ABCDEFGMPSTabcdm"),
    "numeracy": list("1234567890+="),
}
_rng = random.Random(2026)
# fixed layout so the same frame always looks the same: (x, y, speed, phase, colour index)
_DECOR = [(_rng.random(), 0.05 + 0.32 * _rng.random(), 0.006 + 0.01 * _rng.random(),
           _rng.random() * 6.28, i % len(PALETTE)) for i, _ in enumerate(range(7))]
_CONFETTI = [(_rng.random(), 0.25 + 0.4 * _rng.random(), _rng.random(),
              4 + 5 * _rng.random(), i % len(PALETTE)) for i in range(40)]


@lru_cache(maxsize=None)
def _font(size):
    return render.font(size)


def star(d, x, y, r, fill, spin=0.0):
    pts = []
    for k in range(10):
        a = spin + k * math.pi / 5 - math.pi / 2
        rad = r if k % 2 == 0 else r * 0.45
        pts.append((x + math.cos(a) * rad, y + math.sin(a) * rad))
    d.polygon(pts, fill=fill)


def _heart(d, x, y, r, fill):
    ellipse(d, x - r * 0.5, y - r * 0.3, r * 0.55, r * 0.55, fill)
    ellipse(d, x + r * 0.5, y - r * 0.3, r * 0.55, r * 0.55, fill)
    d.polygon([(x - r * 1.03, y - r * 0.05), (x + r * 1.03, y - r * 0.05), (x, y + r * 1.05)], fill=fill)


def decor(d, w, h, t, pillar):
    """Things that drift across the sky and match today's subject."""
    u = render.SS
    for i, (fx, fy, speed, phase, ci) in enumerate(_DECOR):
        x = ((fx + t * speed) % 1.0) * w
        y = h * fy + math.sin(t * 1.6 + phase) * 12 * u
        col = PALETTE[ci]
        if pillar in DECOR_GLYPHS:
            glyphs = DECOR_GLYPHS[pillar]
            d.text((x, y), glyphs[(i * 5) % len(glyphs)], font=_font(int(54 * u)), fill=col, anchor="mm")
        elif pillar == "animals":  # leaves and little flowers
            if i % 2:
                ellipse(d, x, y, 16 * u, 9 * u, (110, 195, 110))
            else:
                for k in range(5):
                    a = t * 0.8 + k * 1.2566
                    ellipse(d, x + math.cos(a) * 10 * u, y + math.sin(a) * 10 * u, 7 * u, 7 * u, (255, 160, 200))
                ellipse(d, x, y, 6 * u, 6 * u, (255, 220, 80))
        elif pillar == "sports":  # balls bouncing gently in the sky
            ellipse(d, x, y, 15 * u, 15 * u, col)
            ellipse(d, x - 4 * u, y - 5 * u, 5 * u, 3.5 * u, (255, 255, 255))
        else:  # life skills (and anything else): hearts and stars
            if i % 2:
                _heart(d, x, y, 14 * u, col)
            else:
                star(d, x, y, 17 * u, col, spin=t)


def confetti(d, w, h, t, on):
    """Confetti falls whenever the kids are celebrating."""
    if not on:
        return
    u = render.SS
    for fx, speed, phase, size, ci in _CONFETTI:
        y = ((t * speed * 0.9 + phase) % 1.0) * h * 1.1 - h * 0.05
        x = w * fx + math.sin(t * 3 + phase * 9) * 14 * u
        s = size * u
        d.rectangle([x - s * 0.5, y - s * 0.3, x + s * 0.5, y + s * 0.3], fill=PALETTE[ci])


def burst(d, w, h, t):
    """A quick ring of sparkles when a scene begins."""
    dur = 0.8
    if t >= dur:
        return
    k = t / dur
    u = render.SS
    cx, cy = w / 2, h * 0.30
    for n in range(8):
        a = n * math.pi / 4 + 0.4
        dist = (60 + 330 * (1 - (1 - k) ** 2)) * u
        r = 22 * u * (1 - k) + 3 * u
        star(d, cx + math.cos(a) * dist, cy + math.sin(a) * dist, r, PALETTE[n % len(PALETTE)], spin=k * 3)


def camera(img, t):
    """Punch in when a scene starts, then ease back with a slow float. Returns a same-size image."""
    s = 1 + 0.05 * math.exp(-5 * t) + 0.012 * (1 + math.sin(t * 0.9)) / 2
    w, h = img.size
    cw, ch = w / s, h / s
    box = ((w - cw) / 2, (h - ch) / 2, (w + cw) / 2, (h + ch) / 2)
    return img.resize((w, h), Image.BILINEAR, box=box)
