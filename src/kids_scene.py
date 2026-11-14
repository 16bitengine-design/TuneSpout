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
from PIL import Image, ImageDraw

import render
from characters.cast import pal_genome
from characters.creatures import draw_creature
from characters.items import draw_item
from characters.kids import draw_kid

COLOR_KEYS = ("skin", "hair", "shirt", "pants")
KID_X = {1: [0.14], 2: [0.12, 0.88]}
KID_X_TALL = {1: [0.27], 2: [0.21, 0.79]}  # the same, for the vertical video


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
    for i, (kid, fx) in enumerate(zip(kids, xs)):
        is_speaker = (speaker is None and bool(scene.get("line"))) or kid.get("name") == speaker
        x, scale = fx, 1.6 if tall else 1.2
        if is_speaker and speaker is not None:  # the one who talks steps forward a little
            step = min(1.0, t / 0.4)
            x += (0.5 - fx) * 0.16 * step
            scale *= 1 + 0.07 * step
        if walk:  # kids walk in from the sides of the screen
            x = (-0.15 if fx < 0.5 else 1.15) + (x - (-0.15 if fx < 0.5 else 1.15)) * ease
        pointing = (1 if fx < 0.5 else -1) if (is_speaker and speaker is not None and scene.get("items")
                                                and not walk) else 0
        draw_kid(d, w * x, h * ground, SS * scale, t, phase=i * 1.3,
                 cheer=sing, talking=is_speaker and bool(scene.get("line")),
                 walking=walk, point=pointing, lead=kid.get("name") == scene.get("lead"),
                 **_clean_kid(kid))

    # the animal friends stand between the kids
    pals = scene.get("pals", [])
    if tall:
        pal_x = [0.55, 0.85] if len(kids) == 1 else [0.40, 0.60]
    else:
        pal_x = [0.28, 0.86] if len(kids) == 1 else [0.30, 0.70]
    for i, pal in enumerate(pals):
        px = pal_x[i] if i < 2 else 0.5
        if walk:  # the pals bound in from the right
            px = 1.2 + (px - 1.2) * ease
        talks = bool(scene.get("line")) and pal.get("name") == speaker
        draw_creature(d, w * px, h * (ground + 0.01 if tall else ground),
                      SS * (1.35 if tall else 1.0), t, i * 0.8, pal_genome(pal), singing=sing or talks)

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
            pop = 1.0 if idx < new_from else min(1.0, max(0.0, (t - (idx - new_from) * 0.25) / 0.3))
            if pop > 0:
                kind = items["types"][gi] if items.get("types") else items["type"]
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

    render.draw_caption(d, w, h, scene.get("line", ""))
    return img.resize(size, Image.LANCZOS)
