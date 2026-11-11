"""Flat vector-style cartoon renderer (Pillow only, no paid services).

Style: bright flat colors, round shapes, gentle bouncing. Safe and simple for
kids under 12. Add more animals by writing another draw_<name>() function.
"""
import math
import textwrap
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
SS = 2  # supersampling for smooth edges

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "DejaVuSans-Bold.ttf",
]


def font(size: int):
    for p in FONT_PATHS:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def ellipse(d, cx, cy, rx, ry, fill, outline=None, width=0):
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill, outline=outline, width=width)


def background(d, w, h, t):
    # sky gradient
    for y in range(h):
        k = y / h
        d.line([(0, y), (w, y)], fill=(int(135 + 90 * k), int(206 + 30 * k), 250))
    # sun
    ellipse(d, w * 0.88, h * 0.16, 70 * SS, 70 * SS, (255, 223, 80))
    # drifting clouds
    for i, base in enumerate([0.15, 0.5, 0.75]):
        cx = ((base * w + t * 20 * SS * (1 + i * 0.3)) % (w + 400 * SS)) - 200 * SS
        cy = h * (0.12 + 0.07 * i)
        for dx, r in [(-45, 38), (0, 50), (50, 38)]:
            ellipse(d, cx + dx * SS, cy, r * SS, r * 0.75 * SS, (255, 255, 255))
    # hills and pond
    ellipse(d, w * 0.25, h * 1.05, w * 0.6, h * 0.35, (120, 200, 110))
    ellipse(d, w * 0.85, h * 1.1, w * 0.6, h * 0.4, (96, 180, 96))
    ellipse(d, w * 0.5, h * 0.78, w * 0.42, h * 0.13, (80, 170, 230))


def draw_duck(d, cx, cy, s, t, phase, color=(255, 214, 51)):
    bob = math.sin(t * 4 + phase) * 8 * s
    cy += bob
    ellipse(d, cx, cy, 55 * s, 40 * s, color)                    # body
    ellipse(d, cx - 15 * s, cy + 5 * s, 28 * s, 18 * s, (245, 190, 30))  # wing
    ellipse(d, cx + 40 * s, cy - 40 * s, 28 * s, 28 * s, color)  # head
    d.polygon([(cx + 62 * s, cy - 40 * s), (cx + 92 * s, cy - 32 * s),
               (cx + 62 * s, cy - 26 * s)], fill=(255, 140, 40))  # beak
    ellipse(d, cx + 46 * s, cy - 48 * s, 5 * s, 5 * s, (30, 30, 30))      # eye
    ellipse(d, cx + 44 * s, cy - 50 * s, 1.8 * s, 1.8 * s, (255, 255, 255))
    ellipse(d, cx + 30 * s, cy - 30 * s, 5 * s, 3 * s, (255, 150, 150))   # cheek


def draw_chick(d, cx, cy, s, t, phase):
    draw_duck(d, cx, cy, s, t, phase, color=(255, 236, 120))


def draw_fish(d, cx, cy, s, t, phase):
    cy += math.sin(t * 3 + phase) * 10 * s
    ellipse(d, cx, cy, 50 * s, 30 * s, (255, 140, 60))
    d.polygon([(cx - 45 * s, cy), (cx - 80 * s, cy - 25 * s), (cx - 80 * s, cy + 25 * s)],
              fill=(255, 110, 40))
    ellipse(d, cx + 25 * s, cy - 6 * s, 5 * s, 5 * s, (30, 30, 30))


ANIMALS = {"duck": draw_duck, "chick": draw_chick, "fish": draw_fish}


def draw_scene(scene: dict, t: float, size=(W, H)):
    """Return a PIL image for scene at time t (seconds)."""
    w, h = size[0] * SS, size[1] * SS
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    background(d, w, h, t)

    count = int(scene.get("count", 1))
    fn = ANIMALS.get(scene.get("animal", "duck"), draw_duck)
    scale = SS * (1.35 if count <= 3 else 1.05)
    gap = w / (count + 1)
    base_y = h * 0.66
    for i in range(count):
        # animals pop in one by one during the first 0.4s of each scene
        pop = min(1.0, max(0.0, (t - i * 0.25) / 0.3))
        if pop > 0:
            fn(d, gap * (i + 1), base_y, scale * (0.6 + 0.4 * pop), t, i * 0.9)

    # number badge
    bx, by, r = 140 * SS, 130 * SS, 90 * SS
    ellipse(d, bx, by, r, r, (255, 105, 135))
    ellipse(d, bx, by, r - 10 * SS, r - 10 * SS, (255, 255, 255))
    f = font(120 * SS)
    d.text((bx, by), str(count), font=f, fill=(255, 105, 135), anchor="mm")

    # caption box
    line = scene.get("line", "")
    cf = font(34 * SS)
    wrapped = "\n".join(textwrap.wrap(line, 42))
    box_h = 40 * SS * (wrapped.count("\n") + 1) + 40 * SS
    d.rounded_rectangle([60 * SS, h - box_h - 30 * SS, w - 60 * SS, h - 30 * SS],
                        radius=28 * SS, fill=(255, 255, 255))
    d.multiline_text((w / 2, h - 30 * SS - box_h / 2), wrapped, font=cf,
                     fill=(60, 60, 90), anchor="mm", align="center")
    return img.resize(size, Image.LANCZOS)
