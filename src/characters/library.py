"""Objects the system can draw, plus an inventor for words it has no recipe for.

draw_named("kite", ...) uses the recipe in LIBRARY. For an unknown word,
invent_recipe() builds a new, friendly object from the word itself, so the
same word always gives the same object and every video can use new things.
"""
import math
import random
import zlib

from characters.shapes import PALETTES, draw_recipe, palette


def E(x, y, rx, ry, c="main"):
    return {"t": "ellipse", "x": x, "y": y, "rx": rx, "ry": ry, "c": c}


def R(x, y, hw, hh, c="main", rad=0.15):
    return {"t": "rect", "x": x, "y": y, "hw": hw, "hh": hh, "rad": rad, "c": c}


def P(pts, c="main"):
    return {"t": "poly", "pts": pts, "c": c}


def L(pts, c="brown", w=0.08):
    return {"t": "line", "pts": pts, "c": c, "w": w}


def PIE(x, y, rx, ry, a0, a1, c="main"):
    return {"t": "pie", "x": x, "y": y, "rx": rx, "ry": ry, "a0": a0, "a1": a1, "c": c}


LIBRARY = {
    "kite": [P([[0, -1.1], [.8, 0], [0, 1], [-.8, 0]]), L([[0, -1.1], [0, 1]], "alt", .07),
             L([[-.8, 0], [.8, 0]], "alt", .07), L([[0, 1], [.2, 1.4], [-.2, 1.7]], "brown", .06)],
    "balloon": [L([[0, .9], [.1, 1.5]], "gray", .05), P([[0, .85], [.15, 1.05], [-.15, 1.05]], "dark"),
                E(0, -.2, .8, .95), E(-.28, -.5, .15, .25, "light")],
    "cup": [P([[-.7, -.7], [.7, -.7], [.5, .85], [-.5, .85]]), R(0, -.7, .75, .13, "alt", .1),
            E(.8, .0, .3, .3, "gray"), E(.8, .0, .17, .17, "white")],
    "book": [R(0, 0, .8, .95, "main", .1), R(.08, 0, .68, .83, "white", .05),
             R(-.74, 0, .1, .95, "dark", .05), L([[-.4, -.3], [.4, -.3]], "alt", .09),
             L([[-.4, .05], [.4, .05]], "alt", .09)],
    "cookie": [E(0, 0, 1, .95, "tan"), E(-.35, -.3, .14, .14, "brown"), E(.3, -.2, .14, .14, "brown"),
               E(-.1, .25, .14, .14, "brown"), E(.45, .35, .12, .12, "brown")],
    "boat": [P([[-.9, .2], [.9, .2], [.55, .85], [-.55, .85]]), L([[0, .2], [0, -1]], "brown", .07),
             P([[.05, -.95], [.8, .1], [.05, .1]], "alt")],
    "cake": [R(0, .35, .9, .5, "main", .12), R(0, -.2, .9, .12, "white", .08),
             R(0, -.45, .1, .3, "alt", .03), E(0, -.85, .1, .16, "yellow")],
    "hat": [P([[0, -1.1], [.75, .7], [-.75, .7]]), E(0, -1.1, .14, .14, "alt"),
            E(-.2, .1, .1, .1, "alt"), E(.2, .3, .1, .1, "alt"), R(0, .75, .85, .1, "alt", .05)],
    "bell": [PIE(0, .1, .85, .95, 180, 360, "yellow"), R(0, .3, .85, .2, "yellow", .08),
             E(0, .75, .2, .2, "brown")],
    "drum": [R(0, .1, .85, .65, "main", .1), E(0, -.55, .85, .28, "alt"),
             L([[-.8, -1], [-.1, -.55]], "brown", .09), L([[.8, -1], [.1, -.55]], "brown", .09)],
    "heart": [E(-.45, -.3, .55, .55), E(.45, -.3, .55, .55),
              P([[-.95, -.1], [.95, -.1], [0, 1]])],
    "umbrella": [L([[0, -.2], [0, .9], [.25, 1.05]], "brown", .08), PIE(0, -.2, 1, 1, 180, 360),
                 L([[-.35, -.2], [-.2, -.9]], "alt", .06), L([[.35, -.2], [.2, -.9]], "alt", .06)],
    "pencil": [R(0, 0, .2, .75, "yellow", .04), P([[-.2, .75], [.2, .75], [0, 1.1]], "tan"),
               P([[-.07, .95], [.07, .95], [0, 1.1]], "black"), R(0, -.85, .2, .15, "pink", .05)],
    "cloud": [E(-.45, .1, .5, .4), E(.1, -.1, .6, .55), E(.55, .15, .45, .35), R(.05, .35, .9, .2, "main", .1)],
    "house": [R(0, .35, .8, .6, "main", .06), P([[-1, -.2], [1, -.2], [0, -1]], "alt"),
              R(0, .6, .2, .35, "brown", .04), R(-.5, .2, .15, .15, "white", .02)],
    "tree": [R(0, .6, .15, .45, "brown", .04), E(0, -.25, .8, .8, "green"), E(-.3, -.4, .2, .2, "light")],
    "fish": [E(0, 0, .8, .5), P([[-.65, 0], [-1.1, -.45], [-1.1, .45]], "alt"), E(.42, -.1, .09, .09, "black")],
    "butterfly": [E(-.5, -.35, .5, .6), E(.5, -.35, .5, .6), E(-.4, .4, .38, .42, "alt"),
                  E(.4, .4, .38, .42, "alt"), R(0, 0, .08, .7, "black", .04)],
}


def has_recipe(name):
    return name in LIBRARY


def invent_recipe(name):
    """A new friendly object, always the same for the same word.

    Built from a random body shape (9 kinds, with random proportions), one or
    two decorations (8 kinds, with random counts and positions) and an optional
    happy face, so different words almost never look alike.
    """
    rng = random.Random(zlib.crc32(name.encode()))
    w, h = rng.uniform(.72, 1.0), rng.uniform(.75, 1.05)
    kind = rng.choice(["orb", "egg", "block", "tall", "bump", "drop", "ring", "pill", "star"])
    top = -h
    if kind == "orb":
        body = [E(0, 0, w, w)]; top = -w
    elif kind == "egg":
        body = [E(0, .05, w * .85, h)]
    elif kind == "block":
        body = [R(0, 0, w, h * .9, "main", rng.uniform(.15, .45))]; top = -h * .9
    elif kind == "tall":
        body = [R(0, 0, w * .65, h, "main", rng.uniform(.2, .5))]
    elif kind == "bump":
        body = [E(0, .15, w, h * .8), E(0, -.4, w * .6, h * .55)]; top = -.95
    elif kind == "drop":
        body = [P([[0, -1.1], [w * .8, .2], [-w * .8, .2]]), E(0, .25, w * .8, h * .75)]; top = -1.1
    elif kind == "ring":
        body = [E(0, 0, w, w), E(0, 0, w * rng.uniform(.3, .5), w * rng.uniform(.3, .5), "light")]; top = -w
    elif kind == "pill":
        body = [R(0, 0, w, h * .55, "main", .5)]; top = -h * .55
    else:  # star: 5 to 8 points with random depth
        n, inner = rng.randint(5, 8), rng.uniform(.45, .7)
        pts = []
        for i in range(2 * n):
            ang = math.radians(-90 + i * 180 / n)
            rad = 1.1 if i % 2 == 0 else 1.1 * inner
            pts.append([rad * math.cos(ang), rad * math.sin(ang)])
        body = [P(pts)]; top = -1.1

    extra = []
    for decor in rng.sample(["stripes", "dots", "band", "topper", "ears", "feet", "wings", "leaves"],
                            rng.choice([1, 1, 2])):
        if decor == "stripes":
            for k in range(rng.randint(1, 3)):
                extra.append(R(0, -.2 + k * .35, w * .8, .08 + .04 * rng.random(), "alt", .05))
        elif decor == "dots":
            for _ in range(rng.randint(2, 5)):
                extra.append(E(rng.uniform(-.5, .5), rng.uniform(-.5, .5), r := rng.uniform(.09, .17), r, "alt"))
        elif decor == "band":
            extra.append(R(0, rng.uniform(.3, .6), w * .9, rng.uniform(.1, .2), "alt", .05))
        elif decor == "topper":
            extra += [L([[0, top], [0, top - .25]], "brown", .08), E(0, top - .35, .18, .18, "alt")]
        elif decor == "ears":
            extra += [E(-w * .6, top + .1, .22, .25, "dark"), E(w * .6, top + .1, .22, .25, "dark")]
        elif decor == "feet":
            extra += [E(-w * .4, h * .95, .22, .12, "dark"), E(w * .4, h * .95, .22, .12, "dark")]
        elif decor == "wings":
            extra += [E(-w * 1.0, 0, .22, .35, "alt"), E(w * 1.0, 0, .22, .35, "alt")]
        else:  # leaves
            extra += [E(-.15, top - .1, .14, .26, "green"), E(.15, top - .1, .14, .26, "green")]

    face = []
    if rng.random() < 0.65:  # a tiny happy face makes things feel friendly
        gap, eye = rng.uniform(.2, .32), rng.uniform(.06, .1)
        face = [E(-gap, -.05, eye, eye * 1.3, "black"), E(gap, -.05, eye, eye * 1.3, "black"),
                {"t": "line", "pts": [[-.15, .25], [0, .35], [.15, .25]], "c": "black", "w": .05}]
    return body + extra + face


def pair_for(name):
    """Stable colours for an invented object so it keeps its look in a video."""
    return PALETTES[zlib.crc32(name.encode()) % len(PALETTES)]


def draw_named(d, name, x, y, r, group=0, ghost=False, t=0.0, phase=0.0):
    if name in LIBRARY:
        draw_recipe(d, LIBRARY[name], x, y, r, palette(group), ghost, t, phase)
    else:  # never fails: any word gets an object
        pair = PALETTES[(zlib.crc32(name.encode()) + group) % len(PALETTES)]
        draw_recipe(d, invent_recipe(name), x, y, r, palette(pair=pair), ghost, t, phase)
