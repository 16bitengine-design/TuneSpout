"""Real animals for the nature lessons: how they look, what they say, what their babies are called.

Each animal is a friendly front-facing face drawn from a recipe (see shapes.py). Babies are
the same animal drawn smaller, so a grown-up and its baby can stand side by side.
"""
from characters.library import LIBRARY, E, L, P


def _eyes(y=-.2, dx=.28, r=.09):
    return [E(-dx, y, r, r * 1.2, "black"), E(dx, y, r, r * 1.2, "black"),
            E(-dx + .03, y - .04, r * .35, r * .35, "white"), E(dx + .03, y - .04, r * .35, r * .35, "white")]


def _scaled(recipe, k, down):
    """The same recipe, smaller by k, standing on the same ground line."""
    out = []
    for op in recipe:
        new = dict(op)
        for key in ("x", "y", "rx", "ry", "hw", "hh", "w"):
            if key in new:
                new[key] = new[key] * k
        if "pts" in new:
            new["pts"] = [[px * k, py * k] for px, py in new["pts"]]
        if "y" in new:
            new["y"] += down
        if "pts" in new:
            new["pts"] = [[px, py + down] for px, py in new["pts"]]
        out.append(new)
    return out


ANIMAL_RECIPES = {
    "dog": [E(-.78, -.05, .3, .55, "brown"), E(.78, -.05, .3, .55, "brown"), E(0, 0, .8, .85, "tan"),
            E(0, .28, .42, .32, "cream"), E(0, .12, .14, .1, "black")] + _eyes() + [E(0, .52, .12, .14, "rose")],
    "cat": [P([[-.85, -.1], [-.6, -1.05], [-.1, -.6]], "orange"), P([[.85, -.1], [.6, -1.05], [.1, -.6]], "orange"),
            E(0, .05, .88, .8, "orange"), E(0, .3, .35, .25, "cream"), E(0, .14, .08, .06, "rose")] + _eyes(-.18, .32, .1)
           + [L([[-.45, .28], [-1.05, .2]], "dgray", .03), L([[-.45, .36], [-1.05, .44]], "dgray", .03),
              L([[.45, .28], [1.05, .2]], "dgray", .03), L([[.45, .36], [1.05, .44]], "dgray", .03),
              L([[-.1, -.78], [-.1, -.55]], "brown", .06), L([[.1, -.78], [.1, -.55]], "brown", .06)],
    "cow": [E(-.88, -.3, .3, .17, "dgray"), E(.88, -.3, .3, .17, "dgray"), E(0, 0, .75, .85, "white"),
            E(-.38, -.48, .3, .24, "dgray"), E(0, .42, .52, .38, "rose"), E(-.18, .44, .06, .08, "brown"),
            E(.18, .44, .06, .08, "brown")] + _eyes(-.15, .3),
    "duck": [E(0, .3, .92, .68, "yellow"), E(-.62, .3, .3, .42, "tan"), E(.62, .3, .3, .42, "tan"),
             E(0, -.4, .52, .5, "yellow"), E(0, -.22, .36, .17, "orange")] + _eyes(-.5, .22, .08),
    "sheep": [E(-.55, -.4, .45, .42, "cream"), E(.55, -.4, .45, .42, "cream"), E(0, -.62, .5, .42, "cream"),
              E(-.7, .1, .38, .4, "cream"), E(.7, .1, .38, .4, "cream"), E(0, .0, .55, .72, "dgray"),
              E(-.55, -.08, .2, .1, "dgray"), E(.55, -.08, .2, .1, "dgray")] + _eyes(-.08, .2, .08)
             + [E(0, .28, .1, .07, "rose")],
    "chicken": [E(0, .35, .85, .62, "white"), E(0, -.35, .46, .46, "white"),
                E(-.14, -.88, .13, .16, "red"), E(0, -.95, .15, .2, "red"), E(.14, -.88, .13, .16, "red"),
                P([[-.13, -.3], [.13, -.3], [0, -.08]], "orange"), E(0, -.04, .07, .13, "red")] + _eyes(-.45, .2, .07),
    "horse": [P([[-.4, -.8], [-.2, -1.15], [-.05, -.75]], "brown"), P([[.4, -.8], [.2, -1.15], [.05, -.75]], "brown"),
              E(0, 0, .55, .92, "brown"), L([[0, -.85], [0, -.2]], "dgray", .12), E(0, .6, .42, .3, "tan"),
              E(-.14, .66, .05, .07, "dgray"), E(.14, .66, .05, .07, "dgray")] + _eyes(-.3, .34, .07),
    "frog": [E(0, .2, .98, .7, "green"), E(-.5, -.45, .34, .34, "green"), E(.5, -.45, .34, .34, "green"),
             E(-.5, -.45, .2, .2, "white"), E(.5, -.45, .2, .2, "white"),
             E(-.5, -.43, .1, .12, "black"), E(.5, -.43, .1, .12, "black"),
             L([[-.5, .25], [-.25, .45], [.25, .45], [.5, .25]], "dgray", .05),
             E(-.62, .15, .12, .08, "pink"), E(.62, .15, .12, .08, "pink")],
}

# what they say and what their young are called
ANIMALS = {
    "dog": {"sound": "woof", "baby": "puppy"},
    "cat": {"sound": "meow", "baby": "kitten"},
    "cow": {"sound": "moo", "baby": "calf"},
    "duck": {"sound": "quack", "baby": "duckling"},
    "sheep": {"sound": "baa", "baby": "lamb"},
    "chicken": {"sound": "cluck", "baby": "chick"},
    "horse": {"sound": "neigh", "baby": "foal"},
    "frog": {"sound": "ribbit", "baby": "tadpole"},
}
BABY_SIZE = 0.6


def register():
    """Add the animals and their babies to the library the scene drawer uses."""
    for name, recipe in ANIMAL_RECIPES.items():
        LIBRARY[name] = recipe
        LIBRARY[ANIMALS[name]["baby"]] = _scaled(recipe, BABY_SIZE, 1 - BABY_SIZE)
    # a baby frog is a tadpole, which does not look like a small frog
    LIBRARY["tadpole"] = [P([[.15, .55], [1.0, .3], [.15, .85]], "dgray"), E(-.2, .6, .5, .42, "dgray"),
                          E(-.35, .5, .11, .13, "white"), E(-.08, .5, .11, .13, "white"),
                          E(-.33, .52, .05, .06, "black"), E(-.06, .52, .05, .06, "black")]


register()
