"""The recurring cast: the faces viewers meet in every video.

Main players: four kids (CAST_KIDS) and two animal friends (CAST_ANIMALS). Their looks
are fixed here, so they never change from video to video. Everyone else on screen
(background kids, invented objects) is an "extra" made fresh for each video and can
be swapped freely. To change the cast, edit this file only.
"""
CAST_KIDS = [
    {"name": "Amina", "skin": (141, 85, 36), "hair": (30, 25, 25), "style": "bun",
     "shirt": (255, 105, 135), "pants": (70, 90, 160)},
    {"name": "Leo", "skin": (241, 194, 125), "hair": (140, 80, 40), "style": "short",
     "shirt": (80, 170, 230), "pants": (90, 90, 110)},
    {"name": "Mei", "skin": (255, 224, 189), "hair": (30, 25, 25), "style": "long",
     "shirt": (120, 200, 110), "pants": (60, 120, 100)},
    {"name": "Kofi", "skin": (94, 56, 28), "hair": (30, 25, 25), "style": "curly",
     "shirt": (255, 170, 60), "pants": (70, 90, 160)},
]

# Two friendly animal pals who join every lesson.
CAST_ANIMALS = {
    "kibo": {"name": "Kibo", "body": (255, 225, 130), "ears": "round", "tail": "puff",
            "pattern": "spots", "scale": 1.0, "tall": 1.0},
    "mo": {"name": "Mo", "body": (170, 210, 255), "ears": "floppy", "tail": "curl",
           "pattern": "none", "scale": 1.05, "tall": 1.1},
}


def animal_genome(key):
    """The drawing recipe for a cast animal (same format as characters.creatures.genome)."""
    a = CAST_ANIMALS[key]
    body = a["body"]
    return {"body": body,
            "belly": tuple(min(255, c + 45) for c in body),
            "dark": tuple(int(c * 0.78) for c in body),
            "ears": a["ears"], "tail": a["tail"], "pattern": a["pattern"],
            "scale": a["scale"], "tall": a["tall"]}


def cast_pals():
    """The two animal friends as lesson data."""
    return [{"cast": key, "name": a["name"]} for key, a in CAST_ANIMALS.items()]


def pick_kids(rng, k):
    """k different main kids, rotating through the cast."""
    return [dict(kid) for kid in rng.sample(CAST_KIDS, k)]


def extra_kids(rng, k=2):
    """Random background kids (no names): the replaceable extras."""
    from characters.kids import HAIR, PANTS, SHIRTS, SKIN, STYLES
    return [{"skin": rng.choice(SKIN), "hair": rng.choice(HAIR), "style": rng.choice(STYLES),
             "shirt": rng.choice(SHIRTS), "pants": rng.choice(PANTS)} for _ in range(k)]


def check_cast():
    """A few sanity rules, run by the tests."""
    names = [k["name"] for k in CAST_KIDS] + [a["name"] for a in CAST_ANIMALS.values()]
    assert len(set(names)) == len(names), "cast names must be different"
    assert 3 <= len(CAST_KIDS) <= 5, "keep three to five main kids"
    assert len(CAST_ANIMALS) == 2
    return True



def pal_genome(pal):
    """Drawing recipe for any pal in a lesson: a cast animal or an invented one."""
    from characters.creatures import genome
    return animal_genome(pal["cast"]) if "cast" in pal else genome(pal["seed"])
