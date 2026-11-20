"""Scene layout for lessons where kids work with things (count, add, share).

Scene keys (all optional except line):
  kids:     list of kid dicts (max 2 looks best)
  items:    {type, count, split:[group sizes], new_from, ghost, scale, types}
            scale makes each thing bigger (1 = counting size); types gives one thing per group
  equation: big text banner, e.g. "2 + 3 = 5"
  pals:     animal friends: {"cast": "yumbi"} for a cast animal, or {"seed": n} for an invented one
  extras:   small background kids (no names), drawn behind the main kids
  cheer:    true to make the kids jump for joy
  line:     the sentence spoken and shown on screen
"""
import math

from PIL import Image, ImageDraw

import lively
import render
from characters.cast import pal_genome
from characters.creatures import draw_creature
from characters.items import draw_item
from characters.common import ellipse
from characters.kids import draw_kid

COLOR_KEYS = ("skin", "hair", "shirt", "pants")
KID_X = {1: [0.14], 2: [0.12, 0.88]}
KID_X_TALL = {1: [0.27], 2: [0.21, 0.79]}  # the same, for the vertical video


FPS = 24
SPOTS_L, SPOTS_R = [0.16, 0.24, 0.32], [0.68, 0.76, 0.84]
MOVE = 0.9  # seconds it takes to walk to the next spot


def plan_positions(scenes):
    """Give every scene spots for the kids to stand at, and where they were in the scene
    before, so they walk around the meadow between scenes instead of standing still."""
    prev = None
    for i, sc in enumerate(scenes):
        n = len(sc.get("kids", []))
        if n == 2:
            xs = [SPOTS_L[(i * 5 + 1) % 3], SPOTS_R[(i * 7 + 2) % 3]]
        elif n == 1:
            xs = [SPOTS_L[(i * 5 + 1) % 3]]
        else:
            xs = []
        sc["_xs"], sc["_from"] = xs, prev or xs
        prev = xs


def _mouth(scene, t):
    """How open the mouth is right now, from the real audio level of this scene's line."""
    env = scene.get("_env")
    if not env:
        return None
    i = min(len(env) - 1, int(t * FPS))
    return env[i]


def _ball(d, x, y, r, t):
    """A beach ball: the animal friends toss it to each other."""
    ellipse(d, x, y, r, r, (255, 90, 90))
    for k, col in enumerate(((255, 220, 60), (80, 170, 240))):
        a = t * 4 + k * 2.1
        ellipse(d, x + math.cos(a) * r * 0.5, y + math.sin(a) * r * 0.5, r * 0.3, r * 0.3, col)
    ellipse(d, x - r * 0.3, y - r * 0.35, r * 0.2, r * 0.14, (255, 255, 255))


def _clean_kid(kid):
    out = {k: v for k, v in kid.items() if k not in ("name", "voice")}
    for key in COLOR_KEYS:
        if key in out:
            out[key] = tuple(out[key])
    return out


def draw_kids_scene(scene, t, size=(render.W, render.H)):
    SS = render.SS
    w, h = size[0] * SS, size[1] * SS
    tall = h > w  # vertical video: kids and pals share one row at the bottom, things go above
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    render.background(d, w, h, t, pond=False)
    lively.decor(d, w, h, t, scene.get("pillar"))  # floating letters, numbers, leaves... for today's subject
    ground = 0.92 if tall else 0.74
    sing = bool(scene.get("cheer"))

    # extras stand far back and small, so the main players stay the stars
    for i, kid in enumerate(scene.get("extras", [])):
        draw_kid(d, w * (0.36 + 0.28 * i if tall else 0.40 + 0.20 * i), h * (ground - 0.07 if tall else 0.73),
                 SS * (0.85 if tall else 0.62), t, phase=i * 2.1 + 0.7,
                 cheer=bool(scene.get("cheer")), **_clean_kid(kid))

    # kids stand at the sides so the middle stays free for the things they use
    kids = scene.get("kids", [])
    table = KID_X_TALL if tall else KID_X
    xs = table.get(len(kids), [(i + 1) / (len(kids) + 1) for i in range(len(kids))])
    speaker = scene.get("speaker")
    enter = 1.6  # seconds the cast takes to walk in during the first scene
    walk = bool(scene.get("enter")) and t < enter
    ease = 1 - (1 - min(1.0, t / enter)) ** 2 if scene.get("enter") else 1.0
    mouth = _mouth(scene, t)
    spots = scene.get("_xs") if tall and len(scene.get("_xs", [])) == len(kids) else None
    hand = None  # where the speaker's hand is: things are tossed from there
    for i, (kid, fx) in enumerate(zip(kids, xs)):
        is_speaker = (speaker is None and bool(scene.get("line"))) or kid.get("name") == speaker
        x, scale = (spots[i] if spots else fx), 1.6 if tall else 1.2
        x0 = scene["_from"][i] if spots and len(scene.get("_from", [])) == len(kids) else x
        if is_speaker and speaker is not None:  # the one who talks steps forward a little
            step = min(1.0, t / 0.4)
            x += (0.5 - x) * 0.16 * step
            scale *= 1 + 0.07 * step
        walking = False
        if spots and t < MOVE and abs(x0 - x) > 0.02 and not scene.get("enter"):
            k = t / MOVE
            x = x0 + (x - x0) * (1 - (1 - k) ** 2)  # walk over from the last spot
            walking = True
        if walk:  # kids walk in from the sides of the screen
            x = (-0.15 if fx < 0.5 else 1.15) + (x - (-0.15 if fx < 0.5 else 1.15)) * ease
        pointing = (1 if x < 0.5 else -1) if (is_speaker and speaker is not None and scene.get("items")
                                               and not walk) else 0
        if is_speaker:
            hand = (w * x + (1 if x < 0.5 else -1) * 60 * SS * scale, h * ground - 95 * SS * scale)
        party = bool(scene.get("equation")) and not is_speaker  # friends cheer when the answer appears
        draw_kid(d, w * x, h * ground, SS * scale, t, phase=i * 1.3,
                 cheer=sing or party, talking=is_speaker and bool(scene.get("line")),
                 walking=walk or walking, point=pointing, lead=kid.get("name") == scene.get("lead"),
                 mouth=mouth if is_speaker else None, **_clean_kid(kid))

    # the animal friends stand between the kids
    pals = scene.get("pals", [])
    if tall:
        pal_x = [0.55, 0.85] if len(kids) == 1 else [0.42, 0.58]
    else:
        pal_x = [0.28, 0.86] if len(kids) == 1 else [0.30, 0.70]
    for i, pal in enumerate(pals):
        px = pal_x[i] if i < 2 else 0.5
        if walk:  # the pals bound in from the right
            px = 1.2 + (px - 1.2) * ease
        talks = bool(scene.get("line")) and pal.get("name") == speaker
        draw_creature(d, w * px, h * (ground + 0.01 if tall else ground),
                      SS * (1.35 if tall else 1.0), t, i * 0.8, pal_genome(pal), singing=sing or talks, mouth=mouth if talks else None)

    if tall and len(pals) == 2 and not walk:  # the pals toss a ball back and forth
        u = (t / 1.4) % 1.0
        a, b = (0, 1) if int(t / 1.4) % 2 == 0 else (1, 0)
        bx = w * (pal_x[a] + (pal_x[b] - pal_x[a]) * u)
        by = h * (ground - 0.13) - math.sin(math.pi * u) * h * 0.07
        _ball(d, bx, by, 22 * SS, t)

    if tall:  # butterflies drift across the sky
        for k in range(2):
            bx = w * (0.5 + 0.42 * math.sin(t * 0.5 + k * 3.0))
            by = h * (0.2 + 0.05 * k) + math.sin(t * 1.3 + k) * h * 0.02 + h * 0.18 * k
            flap = abs(math.sin(t * 14 + k)) * 12 * SS + 3 * SS
            col = ((255, 140, 200), (255, 180, 70))[k]
            for sx in (-1, 1):
                ellipse(d, bx + sx * flap * 0.8, by, flap, flap * 1.2, col)
            ellipse(d, bx, by, 3 * SS, 10 * SS, (70, 50, 70))

    items = scene.get("items")
    if items:
        groups = items.get("split") or [items["count"]]
        total = sum(groups)
        ghost = items.get("ghost", 0)
        new_from = items.get("new_from", 0)
        group_of = [gi for gi, n in enumerate(groups) for _ in range(n)]
        if tall:  # up to six things in a row; more wrap onto a second row
            same = len(groups) > 1 and len(set(groups)) == 1 and groups[0] <= 6 and len(groups) <= 4
            per_row = groups[0] if same else min(total, 6)  # equal groups: one group on each row
            rows = -(-total // per_row)
            spacing = min(110 * SS, (w * 0.84) / per_row)
        else:
            per_row, rows = total, 1
            gap_units = 0.7 * (len(groups) - 1)
            spacing = min(86 * SS, (w * 0.66) / max(1, total + gap_units))
        gapx = 0 if tall else spacing * 0.7
        for idx in range(total):
            gi = group_of[idx]
            row, col = divmod(idx, per_row)
            in_row = min(per_row, total - row * per_row)
            if tall:
                x = w / 2 + (col - (in_row - 1) / 2) * spacing
                y = h * (0.35 + (row - (rows - 1) / 2) * 0.115)
            else:
                span = spacing * (total - 1) + gapx * (len(groups) - 1)
                x = w / 2 - span / 2 + idx * spacing + gi * gapx
                y = h * 0.42
            # things pop in one by one, starting at new_from
            pop = 1.0 if idx < new_from else min(1.0, max(0.0, (t - (idx - new_from) * 0.25) / (0.55 if tall else 0.3)))
            if pop > 0:
                kind = items["types"][gi] if items.get("types") else items["type"]
                if tall and hand and pop < 1.0:  # tossed from the speaker's hand in an arc
                    x = hand[0] + (x - hand[0]) * pop
                    y = hand[1] + (y - hand[1]) * pop - math.sin(math.pi * pop) * h * 0.10
                draw_item(d, kind, x, y, spacing * (0.46 if tall else 0.4) * items.get("scale", 1) * (0.5 + 0.5 * pop),
                          group=gi, ghost=idx >= total - ghost and ghost > 0, t=t, phase=idx * 0.7)

    eq = scene.get("equation")
    if eq:
        size_px = 84 * SS
        f = render.font(size_px)
        box = d.textbbox((0, 0), eq, font=f)
        while box[2] - box[0] > w * 0.8 and size_px > 20 * SS:  # shrink long banners to fit
            size_px = int(size_px * 0.92)
            f = render.font(size_px)
            box = d.textbbox((0, 0), eq, font=f)
        tw, th = box[2] - box[0], box[3] - box[1]
        cx, cy = w / 2, h * (0.115 if tall else 0.14)
        d.rounded_rectangle([cx - tw / 2 - 40 * SS, cy - th / 2 - 30 * SS,
                             cx + tw / 2 + 40 * SS, cy + th / 2 + 30 * SS],
                            radius=30 * SS, fill=(255, 255, 255))
        d.text((cx, cy), eq, font=f, fill=(255, 105, 135), anchor="mm")

    # extra life: confetti when celebrating, a sparkle burst at the start, a camera punch-in
    lively.confetti(d, w, h, t, on=bool(scene.get("cheer") or scene.get("equation")))
    lively.burst(d, w, h, t)
    img = lively.camera(img, t)
    d = ImageDraw.Draw(img)  # the caption is drawn after the zoom so it stays steady and readable

    render.draw_caption(d, w, h, scene.get("line", ""))
    return img.resize(size, Image.LANCZOS)
