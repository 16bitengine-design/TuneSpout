"""Cartoon kids. Mix of skin tones, hair styles and clothes so every lesson
shows different children. Draw with draw_kid(); colors are plain RGB tuples."""
import math

from characters.common import ellipse

SKIN = [(255, 224, 189), (241, 194, 125), (224, 172, 105),
        (198, 134, 66), (141, 85, 36), (94, 56, 28)]
HAIR = [(30, 25, 25), (80, 50, 30), (140, 80, 40), (230, 190, 90), (60, 35, 25)]
SHIRTS = [(255, 105, 135), (80, 170, 230), (255, 170, 60),
          (120, 200, 110), (170, 120, 220), (250, 210, 70)]
PANTS = [(70, 90, 160), (90, 90, 110), (60, 120, 100)]
STYLES = ["short", "long", "bun", "curly"]


def _hair_front(d, cx, cy, r, color, style):
    d.pieslice([cx - r * 1.06, cy - r * 1.1, cx + r * 1.06, cy + r * 0.9],
               180, 360, fill=color)
    if style == "bun":
        ellipse(d, cx, cy - r * 1.15, r * 0.38, r * 0.38, color)
    elif style == "curly":
        for ang in range(200, 341, 28):
            a = math.radians(ang)
            ellipse(d, cx + r * 1.02 * math.cos(a), cy - r * 0.1 + r * math.sin(a),
                    r * 0.28, r * 0.28, color)


def draw_kid(d, cx, base_y, s, t, phase=0.0, skin=SKIN[1], hair=HAIR[0],
             style="short", shirt=SHIRTS[0], pants=PANTS[0], cheer=False):
    """Draw a kid standing with feet at base_y. s = scale, t = time (seconds)."""
    if cheer:
        bob = abs(math.sin(t * 4 + phase)) * 10 * s
    else:
        bob = math.sin(t * 3 + phase) * 3 * s
    y = base_y - bob

    r = 34 * s
    body_top = y - 105 * s
    cy = body_top - 30 * s
    if style == "long":  # hair behind the body, so it frames the face
        ellipse(d, cx, cy + 30 * s, r * 1.12, r * 1.5, hair)

    # legs and shoes
    for dx in (-14, 14):
        d.rounded_rectangle([cx + dx * s - 9 * s, y - 45 * s, cx + dx * s + 9 * s, y],
                            radius=int(6 * s), fill=pants)
        ellipse(d, cx + dx * s + 3 * s, y, 13 * s, 7 * s, (60, 50, 50))

    # body
    d.rounded_rectangle([cx - 30 * s, body_top, cx + 30 * s, y - 40 * s],
                        radius=int(18 * s), fill=shirt)

    # arms: left rests, right waves (both up when cheering)
    sh_y = body_top + 14 * s
    for side in (-1, 1):
        sx = cx + side * 30 * s
        if side == 1 or cheer:
            a = math.radians(-50 + 28 * math.sin(t * 5 + phase + side))
            if side == -1:
                a = math.radians(180 + 50 - 28 * math.sin(t * 5 + phase))
            hx, hy = sx + 52 * s * math.cos(a), sh_y + 52 * s * math.sin(a)
        else:
            hx, hy = sx - 10 * s, sh_y + 46 * s
        d.line([(sx, sh_y), (hx, hy)], fill=skin, width=int(12 * s))
        ellipse(d, hx, hy, 8 * s, 8 * s, skin)

    # head and hair
    ellipse(d, cx, cy, r, r, skin)
    _hair_front(d, cx, cy, r, hair, style)

    # face
    for ex in (-12, 12):
        ellipse(d, cx + ex * s, cy + 6 * s, 4 * s, 5 * s, (40, 30, 30))
    for ex in (-21, 21):
        ellipse(d, cx + ex * s, cy + 17 * s, 6 * s, 4 * s, (255, 150, 150))
    d.arc([cx - 11 * s, cy + 8 * s, cx + 11 * s, cy + 26 * s], 15, 165,
          fill=(150, 60, 60), width=max(1, int(3 * s)))
