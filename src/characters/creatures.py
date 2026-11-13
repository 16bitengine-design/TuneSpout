"""Invented friendly creatures (sidekicks) made from a seed.

Every creature gets its own colours, ears, tail, pattern and a made-up name.
All designs are round and gentle: no teeth, claws, horns or scary faces.
"""
import math
import random

from characters.common import ellipse
from characters.shapes import NAMED

BODY_COLORS = [(255, 170, 120), (170, 210, 255), (200, 170, 255), (160, 220, 160),
               (255, 200, 220), (255, 225, 130), (150, 225, 225), (255, 190, 100)]
EARS = ["round", "pointy", "floppy", "antenna", "none"]
TAILS = ["curl", "puff", "fin", "none"]
PATTERNS = ["none", "spots", "stripes"]
SYLLABLES = ["zib", "bo", "mi", "lo", "pip", "fu", "ta", "nim", "kee", "wu", "do", "ra",
             "fli", "mo", "pu", "zee", "lu", "bee", "tu", "nox", "jo", "pa"]
# names must never contain these pieces, even inside a longer word
BANNED_PIECES = {"kill", "die", "dead", "blood", "gun", "hit", "fat", "hate", "dumb", "ugly", "poo", "butt", "pig"}


def make_name(rng):
    for _ in range(50):
        name = "".join(rng.choice(SYLLABLES) for _ in range(rng.choice([2, 2, 3])))
        if not any(b in name for b in BANNED_PIECES):
            return name.capitalize()
    return "Bobo"


def genome(seed):
    rng = random.Random(seed)
    body = rng.choice(BODY_COLORS)
    return {
        "body": body,
        "belly": tuple(min(255, c + 45) for c in body),
        "dark": tuple(int(c * 0.78) for c in body),
        "ears": rng.choice(EARS),
        "tail": rng.choice(TAILS),
        "pattern": rng.choice(PATTERNS),
        "scale": rng.uniform(0.85, 1.1),
        "tall": rng.uniform(0.9, 1.15),
    }


def new_pal(rng):
    """A new sidekick for a video: its seed (to draw it) and its name."""
    seed = rng.randrange(1_000_000)
    return {"seed": seed, "name": make_name(random.Random(seed))}


def draw_creature(d, cx, base_y, s, t, phase, g):
    s *= g["scale"]
    bob = abs(math.sin(t * 3 + phase)) * 6 * s
    y = base_y - bob
    bx, by = cx, y - 40 * s
    rx, ry = 42 * s, 38 * s * g["tall"]

    # tail (behind the body)
    if g["tail"] == "curl":
        d.arc([bx + rx * .6, by - 5 * s, bx + rx * 1.6, by + 45 * s], 200, 100, fill=g["dark"], width=int(9 * s))
    elif g["tail"] == "puff":
        ellipse(d, bx + rx * 1.05, by + 5 * s, 16 * s, 16 * s, g["belly"])
    elif g["tail"] == "fin":
        d.polygon([(bx + rx * .8, by), (bx + rx * 1.6, by - 22 * s), (bx + rx * 1.6, by + 22 * s)], fill=g["dark"])

    # ears and antenna (behind the head)
    top = by - ry
    if g["ears"] == "round":
        for sx in (-1, 1):
            ellipse(d, bx + sx * rx * .6, top + 6 * s, 14 * s, 14 * s, g["dark"])
    elif g["ears"] == "pointy":
        for sx in (-1, 1):
            d.polygon([(bx + sx * rx * .25, top + 8 * s), (bx + sx * rx * .85, top + 10 * s),
                       (bx + sx * rx * .65, top - 22 * s)], fill=g["dark"])
    elif g["ears"] == "floppy":
        for sx in (-1, 1):
            ellipse(d, bx + sx * rx * .85, by - ry * .35, 12 * s, 26 * s, g["dark"])
    elif g["ears"] == "antenna":
        for sx in (-1, 1):
            d.line([(bx + sx * 10 * s, top + 6 * s), (bx + sx * 20 * s, top - 22 * s)], fill=g["dark"], width=int(4 * s))
            ellipse(d, bx + sx * 20 * s, top - 24 * s, 7 * s, 7 * s, NAMED["yellow"])

    # feet, body, belly
    for sx in (-1, 1):
        ellipse(d, bx + sx * 18 * s, y, 15 * s, 8 * s, g["dark"])
    ellipse(d, bx, by, rx, ry, g["body"])
    ellipse(d, bx, by + 12 * s, rx * .65, ry * .6, g["belly"])

    # pattern
    if g["pattern"] == "spots":
        for dx, dy in ((-24, -14), (22, -20), (-6, -26), (28, 2)):
            ellipse(d, bx + dx * s, by + dy * s, 5 * s, 5 * s, g["dark"])
    elif g["pattern"] == "stripes":
        for dx in (-18, 0, 18):
            d.line([(bx + dx * s, by - ry + 4 * s), (bx + dx * s, by - ry + 22 * s)], fill=g["dark"], width=int(5 * s))

    # little arms waving
    for sx in (-1, 1):
        a = math.sin(t * 4 + phase + sx) * 10 * s
        ellipse(d, bx + sx * (rx + 3 * s), by + 6 * s - a, 8 * s, 8 * s, g["body"])

    # happy face
    for sx in (-1, 1):
        ellipse(d, bx + sx * 13 * s, by - 8 * s, 6 * s, 7 * s, (255, 255, 255))
        ellipse(d, bx + sx * 13 * s, by - 7 * s, 3 * s, 4 * s, (40, 30, 40))
        ellipse(d, bx + sx * 25 * s, by + 4 * s, 6 * s, 4 * s, (255, 150, 150))
    d.arc([bx - 10 * s, by - 2 * s, bx + 10 * s, by + 14 * s], 15, 165,
          fill=(150, 60, 60), width=max(1, int(3 * s)))
