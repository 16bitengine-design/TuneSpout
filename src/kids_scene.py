"""Scene layout for lessons where kids work with things (count, add, share).

Scene keys (all optional except line):
  kids:     list of kid dicts (max 2 looks best)
  items:    {type, count, split:[group sizes], new_from, ghost, scale, types}
            scale makes each thing bigger (1 = counting size); types gives one thing per group
  equation: big text banner, e.g. "2 + 3 = 5"
  pals:     animal friends: {"cast": "zippa"} for a cast animal, or {"seed": n} for an invented one
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


def _clean_kid(kid):
    out = {k: v for k, v in kid.items() if k != "name"}
    for key in COLOR_KEYS:
        if key in out:
            out[key] = tuple(out[key])
    return out


def draw_kids_scene(scene, t, size=(render.W, render.H)):
    SS = render.SS
    w, h = size[0] * SS, size[1] * SS
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    render.background(d, w, h, t, pond=False)

    # extras stand far back and small, so the main players stay the stars
    for i, kid in enumerate(scene.get("extras", [])):
        draw_kid(d, w * (0.40 + 0.20 * i), h * 0.73, SS * 0.62, t, phase=i * 2.1 + 0.7,
                 cheer=bool(scene.get("cheer")), **_clean_kid(kid))

    # kids stand at the sides so the middle stays free for the things they use
    kids = scene.get("kids", [])
    xs = KID_X.get(len(kids), [(i + 1) / (len(kids) + 1) for i in range(len(kids))])
    for i, (kid, fx) in enumerate(zip(kids, xs)):
        draw_kid(d, w * fx, h * 0.74, SS * 1.2, t, phase=i * 1.3,
                 cheer=bool(scene.get("cheer")), **_clean_kid(kid))

    # an invented sidekick stands between a kid and the middle of the scene
    pals = scene.get("pals", [])
    pal_x = [0.28, 0.86] if len(kids) == 1 else [0.30, 0.70]
    for i, pal in enumerate(pals):
        draw_creature(d, w * (pal_x[i] if i < 2 else 0.5), h * 0.74, SS * 1.0, t, i * 0.8, pal_genome(pal))

    items = scene.get("items")
    if items:
        groups = items.get("split") or [items["count"]]
        total = sum(groups)
        ghost = items.get("ghost", 0)
        new_from = items.get("new_from", 0)
        gap_units = 0.7 * (len(groups) - 1)
        spacing = min(86 * SS, (w * 0.66) / max(1, total + gap_units))
        gapx = spacing * 0.7
        span = spacing * (total - 1) + gapx * (len(groups) - 1)
        x0 = w / 2 - span / 2
        idx = 0
        for gi, size_g in enumerate(groups):
            for _ in range(size_g):
                # things pop in one by one, starting at new_from
                pop = 1.0 if idx < new_from else min(1.0, max(0.0, (t - (idx - new_from) * 0.25) / 0.3))
                if pop > 0:
                    x = x0 + idx * spacing + gi * gapx
                    kind = items["types"][gi] if items.get("types") else items["type"]
                    draw_item(d, kind, x, h * 0.42, spacing * 0.4 * items.get("scale", 1) * (0.5 + 0.5 * pop),
                              group=gi, ghost=idx >= total - ghost and ghost > 0, t=t, phase=idx * 0.7)
                idx += 1

    eq = scene.get("equation")
    if eq:
        f = render.font(84 * SS)
        box = d.textbbox((0, 0), eq, font=f)
        tw, th = box[2] - box[0], box[3] - box[1]
        cx, cy = w / 2, h * 0.14
        d.rounded_rectangle([cx - tw / 2 - 40 * SS, cy - th / 2 - 30 * SS,
                             cx + tw / 2 + 40 * SS, cy + th / 2 + 30 * SS],
                            radius=30 * SS, fill=(255, 255, 255))
        d.text((cx, cy), eq, font=f, fill=(255, 105, 135), anchor="mm")

    render.draw_caption(d, w, h, scene.get("line", ""))
    return img.resize(size, Image.LANCZOS)
