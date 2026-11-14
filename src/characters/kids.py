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
             style="short", shirt=SHIRTS[0], pants=PANTS[0], cheer=False, talking=False):
    """Draw a kid standing with feet at base_y. s = scale, t = time (seconds).
    Always moving: bouncing to the beat, swaying, swinging arms, stepping from foot to
    foot and blinking. cheer = big jumps with both arms up; talking = the mouth opens
    and closes."""
    beat = t * 3.4 + phase
    hop = abs(math.sin(beat)) * (22 if cheer else 7) * s
    sway = math.sin(t * 1.8 + phase) * 6 * s
    y = base_y - hop

    r = 34 * s
    body_top = y - 105 * s
    bx = cx + sway                                           # the body leans side to side
    hx0 = cx + sway * 1.7                                    # the head leans a little more
    cy = body_top - 30 * s + math.sin(beat * 2) * 2 * s      # and nods to the beat
    if style == "long":  # hair behind the body, so it frames the face
        ellipse(d, hx0, cy + 30 * s, r * 1.12, r * 1.5, hair)

    # legs and shoes: the feet take turns lifting
    for dx, turn in ((-14, 0.0), (14, math.pi)):
        lift = max(0.0, math.sin(beat * 2 + turn)) * (4 if cheer else 9) * s
        d.rounded_rectangle([bx + dx * s - 9 * s, y - 45 * s, bx + dx * s + 9 * s, y - lift],
                            radius=int(6 * s), fill=pants)
        ellipse(d, bx + dx * s + 3 * s, y - lift, 13 * s, 7 * s, (60, 50, 50))

    # body
    d.rounded_rectangle([bx - 30 * s, body_top, bx + 30 * s, y - 40 * s],
                        radius=int(18 * s), fill=shirt)

    # arms: the right one waves, the left one swings (both wave when cheering)
    sh_y = body_top + 14 * s
    for side in (-1, 1):
        sx = bx + side * 30 * s
        if side == 1 or cheer:
            a = math.radians(-50 + 34 * math.sin(t * 6 + phase + side))
            if side == -1:
                a = math.radians(180 + 50 - 34 * math.sin(t * 6 + phase))
            hx, hy = sx + 52 * s * math.cos(a), sh_y + 52 * s * math.sin(a)
        else:
            a = math.radians(112 + 22 * math.sin(beat + 1))
            hx, hy = sx + 46 * s * math.cos(a), sh_y + 46 * s * math.sin(a)
        d.line([(sx, sh_y), (hx, hy)], fill=skin, width=int(12 * s))
        ellipse(d, hx, hy, 8 * s, 8 * s, skin)

    # head and hair
    ellipse(d, hx0, cy, r, r, skin)
    _hair_front(d, hx0, cy, r, hair, style)

    # face: eyes blink every few seconds
    blink = (t + phase * 0.7) % 3.3 < 0.14
    for ex in (-12, 12):
        if blink:
            d.line([(hx0 + (ex - 5) * s, cy + 7 * s), (hx0 + (ex + 5) * s, cy + 7 * s)],
                   fill=(40, 30, 30), width=max(1, int(2.5 * s)))
        else:
            ellipse(d, hx0 + ex * s, cy + 6 * s, 4 * s, 5 * s, (40, 30, 30))
    for ex in (-21, 21):
        ellipse(d, hx0 + ex * s, cy + 17 * s, 6 * s, 4 * s, (255, 150, 150))
    if talking:  # mouth opens and closes while the lesson is spoken
        open_ = abs(math.sin(t * 9 + phase * 2))
        mh = (2.5 + 8 * open_) * s
        ellipse(d, hx0, cy + 18 * s, 8 * s, mh, (150, 45, 65))
        if open_ > 0.55:
            ellipse(d, hx0, cy + 18 * s + mh * 0.45, 5 * s, mh * 0.45, (255, 130, 140))
    else:
        d.arc([hx0 - 11 * s, cy + 8 * s, hx0 + 11 * s, cy + 26 * s], 15, 165,
              fill=(150, 60, 60), width=max(1, int(3 * s)))
