"""TuneSpout brand: mascot, logo, avatar, banner, watermark, covers and the
automatic thumbnail made for every video. Everything is drawn by code, so the
look can be regenerated at any size and always matches the cartoons.

Run `python tools/make_brand_assets.py` to write the images into branding/.
"""
import copy
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import render
from characters.common import ellipse
from characters.cast import CAST_ANIMALS, CAST_KIDS, pal_genome
from characters.creatures import draw_creature, genome
from characters.kids import HAIR, PANTS, SHIRTS, SKIN, draw_kid

NAME = "TuneSpout"
TAGLINE = "Sing, count & learn every day!"

FONT_FILE = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "Fredoka.ttf"
SKY = (143, 208, 248)
SUN = (255, 225, 90)
PINK = (255, 105, 135)
NAVY = (60, 60, 90)
GREEN = (120, 200, 110)
PURPLE = (170, 120, 220)
ORANGE = (255, 150, 60)
BLUE = (70, 185, 235)       # mascot body
BLUE_LIGHT = (190, 235, 255)
BLUE_DARK = (40, 140, 200)
WHITE = (255, 255, 255)

K = 2  # draw at 2x, then shrink, for smooth edges

_fonts = {}


def font(size):
    """Fredoka Bold (rounded, friendly, open license)."""
    size = int(size)
    if size not in _fonts:
        f = ImageFont.truetype(str(FONT_FILE), size)
        f.set_variation_by_axes([700, 100])  # weight 700, width 100
        _fonts[size] = f
    return _fonts[size]


# ---------- pieces ----------

def note(d, x, y, s, color):
    """A music note. s is a size multiplier."""
    ellipse(d, x, y, 13 * s, 10 * s, color)
    d.line([(x + 11 * s, y - 2 * s), (x + 11 * s, y - 42 * s)], fill=color, width=max(2, int(4.5 * s)))
    d.polygon([(x + 11 * s, y - 42 * s), (x + 32 * s, y - 28 * s), (x + 11 * s, y - 22 * s)], fill=color)


def draw_spout(d, cx, base_y, s, t=0.0, notes=True):
    """Spout, the mascot: a round blue friend with a fountain of music notes on top."""
    y = base_y - abs(math.sin(t * 3)) * 5 * s
    bx, by = cx, y - 82 * s
    for sx in (-1, 1):  # feet
        ellipse(d, cx + sx * 30 * s, y - 4 * s, 24 * s, 12 * s, BLUE_DARK)
    ellipse(d, bx, by, 74 * s, 82 * s, BLUE)
    ellipse(d, bx, by + 20 * s, 46 * s, 52 * s, BLUE_LIGHT)
    for sx in (-1, 1):  # little arms
        ellipse(d, bx + sx * 80 * s, by + 4 * s - sx * 8 * s, 15 * s, 15 * s, BLUE)
    # a blowhole on top, like a friendly whale: water arcs up and falls back down
    top = by - 82 * s
    ellipse(d, bx, top + 3 * s, 24 * s, 9 * s, BLUE_DARK)
    ellipse(d, bx, top + 1 * s, 15 * s, 5 * s, (30, 90, 150))
    if notes:
        for sx in (-1, 1):  # two arching jets
            pts, wd = [], max(2, int(8 * s))
            for i in range(21):  # up, over, and back down onto the head
                u = i / 20
                pts.append((bx + sx * 62 * s * u, top - 62 * s * 4 * u * (1 - u) + 36 * s * u * u))
            d.line(pts, fill=BLUE, width=wd, joint="curve")
            for px, py in (pts[0], pts[-1]):  # round the ends
                ellipse(d, px, py, wd / 2, wd / 2, BLUE)
        for k, rad in enumerate((9, 8, 6)):  # drops rising in the middle
            ellipse(d, bx, top - (24 + k * 24) * s, rad * s * 0.8, rad * s, BLUE)
        note(d, bx - 12 * s, top - 106 * s, 1.15 * s, SUN)
        note(d, bx - 92 * s, top - 62 * s, 1.0 * s, PINK)
        note(d, bx + 66 * s, top - 62 * s, 1.0 * s, PURPLE)
    # happy face
    for sx in (-1, 1):
        ellipse(d, bx + sx * 26 * s, by - 18 * s, 19 * s, 23 * s, WHITE)
        ellipse(d, bx + sx * 26 * s + sx * 1 * s, by - 15 * s, 10 * s, 13 * s, (35, 40, 70))
        ellipse(d, bx + sx * 26 * s - 3 * s, by - 21 * s, 4 * s, 4 * s, WHITE)
        ellipse(d, bx + sx * 50 * s, by + 10 * s, 11 * s, 7 * s, (255, 150, 170))
    d.arc([bx - 26 * s, by - 10 * s, bx + 26 * s, by + 26 * s], 15, 165,
          fill=(30, 60, 110), width=max(2, int(5 * s)))


def wordmark(d, cx, cy, size):
    """TuneSpout in two colors with a white outline and a soft navy shadow."""
    f = font(size)
    a, b = "Tune", "Spout"
    wa, wb = d.textlength(a, font=f), d.textlength(b, font=f)
    x0 = cx - (wa + wb) / 2
    stroke = max(2, int(size * 0.085))
    off = max(2, int(size * 0.045))
    for text, x, col in ((a, x0, PINK), (b, x0 + wa, BLUE_DARK)):
        d.text((x + off, cy + off), text, font=f, fill=NAVY, stroke_width=stroke,
               stroke_fill=NAVY, anchor="lm")
        d.text((x, cy), text, font=f, fill=col, stroke_width=stroke, stroke_fill=WHITE, anchor="lm")


def pill(d, cx, cy, text, size, fill=WHITE, color=NAVY):
    f = font(size)
    tw = d.textlength(text, font=f)
    padx, pady = size * 0.7, size * 0.38
    d.rounded_rectangle([cx - tw / 2 - padx, cy - size / 2 - pady, cx + tw / 2 + padx, cy + size / 2 + pady],
                        radius=int(size), fill=fill)
    d.text((cx, cy), text, font=f, fill=color, anchor="mm")


def stroked(d, cx, cy, text, size, fill=PINK, max_width=None):
    """Big headline text with a white outline; shrinks to fit max_width."""
    while max_width and d.textlength(text, font=font(size)) > max_width and size > 20:
        size -= 4
    stroke = max(3, int(size * 0.09))
    off = max(2, int(size * 0.05))
    f = font(size)
    d.text((cx + off, cy + off), text, font=f, fill=NAVY, stroke_width=stroke, stroke_fill=NAVY, anchor="mm")
    d.text((cx, cy), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=WHITE, anchor="mm")


def _canvas(w, h, bg=True, pond=False):
    img = Image.new("RGBA", (w * K, h * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if bg:
        render.background(d, w * K, h * K, 0.0, pond=pond, u=w * K / 1280)
    return img, d


def _finish(img, w, h, rgb=True):
    out = img.resize((w, h), Image.LANCZOS)
    return out.convert("RGB") if rgb else out


# the channel art shows the real cast (order: Amina, Jomo, Kofi on the hills, Mei)
BRAND_KIDS = [{k: v for k, v in CAST_KIDS[i].items() if k != "name"} for i in (0, 1, 3, 2)]


def _sparkle_notes(d, spots):
    colors = [PINK, SUN, PURPLE, ORANGE, GREEN]
    for i, (x, y, s) in enumerate(spots):
        note(d, x * K, y * K, s * K, colors[i % len(colors)])


# ---------- assets ----------

def avatar(size=800):
    """Profile picture for YouTube and TikTok (shown as a circle, so keep to the middle)."""
    img, d = _canvas(size, size, bg=False)
    for y in range(size * K):  # sky gradient
        k = y / (size * K)
        d.line([(0, y), (size * K, y)], fill=(int(135 + 90 * k), int(206 + 30 * k), 250))
    ellipse(d, size * K * 0.25, size * K * 1.02, size * K * 0.6, size * K * 0.22, GREEN)
    ellipse(d, size * K * 0.85, size * K * 1.05, size * K * 0.6, size * K * 0.25, (96, 180, 96))
    # the notes reach about 320 units above the feet; keep them well inside the circle
    draw_spout(d, size * K / 2, size * K * 0.88, size * K / 800 * 1.85)
    return _finish(img, size, size)


def watermark(size=150):
    """Small transparent corner logo that YouTube shows on every video."""
    img, d = _canvas(size, size, bg=False)
    # without notes the mascot is about 175 units tall; fill ~85% of the square
    draw_spout(d, size * K / 2, size * K * 0.95, size * K * 0.85 / 175, notes=False)
    return _finish(img, size, size, rgb=False)


def banner(w=2560, h=1440):
    """YouTube channel banner. Text sits in the 1546x423 safe area; kids, pals and
    notes outside it appear on large screens and TVs."""
    img, d = _canvas(w, h)
    sparkle = [(210, 330, 1.7), (470, 640, 1.2), (2330, 380, 1.7), (2140, 700, 1.2),
               (110, 800, 1.1), (2450, 860, 1.1), (1180, 330, 1.3), (1780, 300, 1.4), (700, 250, 1.0)]
    _sparkle_notes(d, sparkle)
    # characters stand outside the safe area, on the hills
    for x, kid, ph in ((210, BRAND_KIDS[0], 0.0), (2350, BRAND_KIDS[1], 1.0)):
        draw_kid(d, x * K, 1335 * K, 2.2 * K, 0.5, ph, cheer=True, **kid)
    for x, key in ((480, "yumbi"), (2080, "lumbo")):
        draw_creature(d, x * K, 1340 * K, 2.4 * K, 0.5, x, pal_genome({"cast": key}))
    # centre: mascot on a cloud, name and tagline (all inside the safe area)
    for dx, rx, ry in ((-95, 95, 34), (0, 130, 44), (100, 100, 34)):
        ellipse(d, (800 + dx) * K, 925 * K, rx * K, ry * K, WHITE)
    draw_spout(d, 800 * K, 915 * K, 1.3 * K, 0.3)
    wordmark(d, 1500 * K, 690 * K, 190 * K)
    pill(d, 1500 * K, 845 * K, TAGLINE, 50 * K)
    return _finish(img, w, h)


def tiktok_cover(w=1080, h=1920):
    """Branded title card for TikTok (profile video, highlights, ads)."""
    img, d = _canvas(w, h)
    _sparkle_notes(d, [(140, 520, 1.6), (940, 600, 1.8), (110, 1000, 1.2), (960, 1060, 1.3)])
    wordmark(d, w / 2 * K, 330 * K, 165 * K)
    draw_spout(d, w / 2 * K, 1415 * K, 2.5 * K, 0.3)  # stands on the hill
    for x, kid in ((150, BRAND_KIDS[2]), (900, BRAND_KIDS[3])):  # waving hello, clear of the mascot
        draw_kid(d, x * K, 1560 * K, 2.4 * K, 0.5, x, cheer=False, **kid)
    pill(d, w / 2 * K, 1650 * K, "A new lesson every day!", 52 * K)
    return _finish(img, w, h)


def cast_sheet(w=1920, h=1080):
    """'Meet the friends': the four main kids and two animal pals, with their names."""
    img, d = _canvas(w, h)
    stroked(d, w / 2 * K, 150 * K, "Meet the friends!", 120 * K, max_width=w * 0.8 * K)
    xs = [0.09 + 0.15 * i for i in range(6)]
    for fx, kid in zip(xs, CAST_KIDS):
        draw_kid(d, fx * w * K, 800 * K, 2.6 * K, 0.5, fx * 9, cheer=False,
                 **{k: v for k, v in kid.items() if k != "name"})
        pill(d, fx * w * K, 900 * K, kid["name"], 54 * K)
    for fx, (key, animal) in zip(xs[4:], CAST_ANIMALS.items()):
        draw_creature(d, fx * w * K, 790 * K, 3.0 * K, 0.5, fx * 9, pal_genome({"cast": key}))
        pill(d, fx * w * K, 900 * K, animal["name"], 54 * K)
    pill(d, w / 2 * K, 1000 * K, "TuneSpout", 44 * K)
    return _finish(img, w, h)


HEADLINES = {
    "counting": "COUNT WITH US!", "addition": "LET'S ADD!", "subtraction": "TAKE AWAY!",
    "multiplication": "TIMES TABLES!", "division": "SHARE FAIRLY!", "plurals": "ONE & MANY!",
    "sports": "FUN SPORTS!", "teamscore": "TEAM GOALS!", "fairplay": "PLAY FAIR!",
    "animalsounds": "ANIMAL SOUNDS!", "babyanimals": "BABY ANIMALS!",
    "leadership": "BE A LEADER!", "reporting": "TELL A REPORT!",
    "planning": "MAKE A PLAN!", "kindwords": "KIND WORDS!", "findingout": "ASK & CHECK!",
    "phonics": "LETTER SOUNDS!", "spelling": "LET'S SPELL!",
}


def thumbnail(lesson, w=1280, h=720):
    """Video thumbnail: big kids, big things to count, big headline, brand name.
    Built to read at phone size."""
    from characters.items import draw_item
    from kids_scene import _clean_kid

    scenes = lesson["scenes"]
    kids = next(sc["kids"] for sc in scenes if sc.get("kids"))
    pals = next((sc["pals"] for sc in scenes if sc.get("pals")), [])
    with_items = [sc for sc in scenes if sc.get("items")]
    items = (with_items[-1]["items"] if with_items else {"type": "ball", "count": 3})

    img, d = _canvas(w, h)
    # kids on the hills, cheering
    for x, kid, ph in ((0.10, kids[0], 0.0), (0.90, kids[-1], 1.0)):
        draw_kid(d, x * w * K, 708 * K, 2.1 * K, 0.5, ph, cheer=True, **_clean_kid(kid))
    for pal, fx in zip(pals, (0.28, 0.72)):
        draw_creature(d, fx * w * K, 712 * K, 2.0 * K, 0.4, 0.0, pal_genome(pal))

    # the things from the lesson, as large as the space allows
    groups = items.get("split") or [items["count"]]
    order = [g for g, n in enumerate(groups) for _ in range(n)]
    n = len(order)
    per_row = n if n <= 5 else (5 if n <= 10 else 7)
    rows = math.ceil(n / per_row)
    r = min(70 * min(items.get("scale", 1), 2.2), 700 / (per_row * 2.3), 300 / (rows * 2.4)) * K
    step = r * 2.3
    for i, g in enumerate(order):
        row, col = divmod(i, per_row)
        n_in_row = min(per_row, len(order) - row * per_row)
        x = w * K / 2 + (col - (n_in_row - 1) / 2) * step
        y = h * 0.50 * K + (row - (rows - 1) / 2) * r * 2.4
        kind = items["types"][g] if items.get("types") else items["type"]
        draw_item(d, kind, x, y, r, group=g, t=0.4, phase=i * 0.7)  # no grey ghosts here

    stroked(d, w * 0.43 * K, 125 * K, HEADLINES.get(lesson.get("topic"), "LEARN WITH US!"), 135 * K,
            max_width=w * 0.72 * K)
    pill(d, w / 2 * K, (h - 48) * K, NAME, 38 * K)
    return _finish(img, w, h)


def json_safe(scene):
    """Scenes hold colours as lists in files and tuples in memory; the renderer wants either."""
    import json
    return json.loads(json.dumps(scene))


def write_all(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "avatar_800.png": avatar(800),               # YouTube + TikTok profile picture
        "youtube_banner_2560x1440.png": banner(),
        "youtube_watermark_150.png": watermark(150),
        "tiktok_cover_1080x1920.png": tiktok_cover(),
        "cast.png": cast_sheet(),
    }
    for name, img in files.items():
        img.save(out / name, optimize=True)
    return sorted(files)
