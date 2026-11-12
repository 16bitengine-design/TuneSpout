"""Draw anything from a small recipe (a list of shapes).

A recipe is plain data, so new objects need no new drawing code. Units: the
object fits roughly in a circle of radius 1, y points down. Each shape has a
colour that is either a named colour or a palette role (main, alt, dark, light).

  {"t": "ellipse", "x": 0, "y": 0, "rx": 1, "ry": .9, "c": "main"}
  {"t": "rect", "x": 0, "y": 0, "hw": .8, "hh": .6, "rad": .2, "c": "alt"}
  {"t": "poly", "pts": [[0,-1],[.8,.8],[-.8,.8]], "c": "main"}
  {"t": "line", "pts": [[0,0],[0,1]], "w": .1, "c": "brown"}
  {"t": "pie", "x": 0, "y": 0, "rx": 1, "ry": 1, "a0": 180, "a1": 360, "c": "main"}
"""
import math

from characters.common import ellipse

NAMED = {
    "white": (255, 255, 255), "brown": (130, 85, 50), "green": (90, 190, 80),
    "yellow": (255, 225, 90), "black": (50, 45, 55), "red": (230, 60, 60),
    "blue": (80, 150, 230), "gray": (180, 185, 195), "pink": (255, 150, 170),
    "orange": (255, 150, 60), "tan": (235, 200, 150), "purple": (170, 120, 220),
    "cream": (255, 244, 214), "dgray": (110, 110, 125), "rose": (240, 120, 145),
}
GHOST_FILL = (225, 232, 240)
GHOST_LINE = (180, 190, 205)

# (main, alt) pairs; the group number picks one so groups look different
PALETTES = [
    ("red", "yellow"), ("blue", "orange"), ("green", "pink"),
    ("purple", "yellow"), ("orange", "blue"), ("pink", "green"),
]


def _shade(rgb, k):
    return tuple(max(0, min(255, int(c * k))) for c in rgb)


def palette(group=0, pair=None):
    main, alt = pair or PALETTES[group % len(PALETTES)]
    m, a = NAMED[main], NAMED[alt]
    return {"main": m, "alt": a, "dark": _shade(m, 0.7), "light": _shade(m, 1.25)}


def _color(name, pal):
    return pal.get(name) or NAMED.get(name) or pal["main"]


def draw_recipe(d, recipe, x, y, r, pal, ghost=False, t=0.0, phase=0.0, bob=0.08):
    y += math.sin(t * 3 + phase) * r * bob
    lw = max(2, int(r * 0.08))
    for op in recipe:
        kind = op["t"]
        fill = GHOST_FILL if ghost else _color(op.get("c", "main"), pal)
        edge = GHOST_LINE if ghost else None
        if kind == "ellipse":
            ellipse(d, x + op["x"] * r, y + op["y"] * r, op["rx"] * r, op["ry"] * r,
                    fill, edge, lw if ghost else 0)
        elif kind == "rect":
            cx, cy = x + op["x"] * r, y + op["y"] * r
            d.rounded_rectangle([cx - op["hw"] * r, cy - op["hh"] * r,
                                 cx + op["hw"] * r, cy + op["hh"] * r],
                                radius=max(1, int(op.get("rad", 0) * r)),
                                fill=fill, outline=edge, width=lw if ghost else 0)
        elif kind == "poly":
            d.polygon([(x + px * r, y + py * r) for px, py in op["pts"]],
                      fill=fill, outline=edge, width=lw if ghost else 0)
        elif kind == "line":
            pts = [(x + px * r, y + py * r) for px, py in op["pts"]]
            d.line(pts, fill=GHOST_LINE if ghost else fill,
                   width=max(2, int(op.get("w", 0.08) * r)), joint="curve")
        elif kind == "pie":
            cx, cy = x + op["x"] * r, y + op["y"] * r
            d.pieslice([cx - op["rx"] * r, cy - op["ry"] * r, cx + op["rx"] * r, cy + op["ry"] * r],
                       op["a0"], op["a1"], fill=fill, outline=edge, width=lw if ghost else 0)
        else:
            raise ValueError(f"unknown shape type: {kind}")
