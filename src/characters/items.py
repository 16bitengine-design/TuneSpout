"""Things kids count, add and share. Each group in a scene gets its own color."""
import math

from characters.common import ellipse

COLORS = {
    "apple": [(230, 60, 60), (110, 190, 70), (250, 200, 60)],
    "star": [(255, 205, 50), (255, 150, 60), (255, 120, 170)],
    "ball": [(70, 140, 230), (255, 150, 50), (110, 200, 120)],
    "flower": [(255, 110, 160), (170, 120, 220), (255, 170, 60)],
}
GHOST_FILL = (225, 232, 240)
GHOST_LINE = (180, 190, 205)


def draw_item(d, kind, x, y, r, group=0, ghost=False, t=0.0, phase=0.0):
    y += math.sin(t * 3 + phase) * r * 0.08
    cols = COLORS.get(kind, COLORS["apple"])
    col = cols[group % len(cols)]
    fill = GHOST_FILL if ghost else col
    line = GHOST_LINE if ghost else None
    w = max(2, int(r * 0.08)) if ghost else 0

    if kind == "star":
        pts = []
        for i in range(10):
            ang = math.radians(-90 + i * 36)
            rad = r * (1.15 if i % 2 == 0 else 0.5)
            pts.append((x + rad * math.cos(ang), y + rad * math.sin(ang)))
        d.polygon(pts, fill=fill, outline=line, width=w)
    elif kind == "ball":
        ellipse(d, x, y, r, r, fill, line, w)
        if not ghost:
            d.arc([x - r, y - r, x + r, y + r], 200, 340, fill=(255, 255, 255),
                  width=max(2, int(r * 0.18)))
    elif kind == "flower":
        for i in range(5):
            ang = math.radians(-90 + i * 72)
            ellipse(d, x + r * 0.6 * math.cos(ang), y + r * 0.6 * math.sin(ang),
                    r * 0.45, r * 0.45, fill, line, w)
        ellipse(d, x, y, r * 0.35, r * 0.35, GHOST_LINE if ghost else (255, 230, 90))
    else:  # apple
        ellipse(d, x, y + r * 0.1, r, r * 0.95, fill, line, w)
        d.line([(x, y - r * 0.8), (x + r * 0.1, y - r * 1.2)],
               fill=GHOST_LINE if ghost else (110, 70, 40), width=max(2, int(r * 0.12)))
        ellipse(d, x + r * 0.4, y - r * 1.0, r * 0.3, r * 0.16,
                GHOST_LINE if ghost else (90, 190, 80))
