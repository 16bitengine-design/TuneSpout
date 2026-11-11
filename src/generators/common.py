"""Shared helpers for lesson generators. All lessons are built from a seed,
so the same seed always gives the same lesson and nothing needs to be stored."""
import random

from characters.creatures import new_pal
from characters.kids import HAIR, PANTS, SHIRTS, SKIN, STYLES

NAMES = ["Amina", "Leo", "Zuri", "Mateo", "Mei", "Sam", "Ravi", "Lila", "Kofi",
         "Nia", "Omar", "Ella", "Tariq", "Ana", "Jin", "Sara"]
# Things kids can count. Only words with a regular plural (add an s) belong here;
# any word works for drawing, because unknown words get an invented object.
_THINGS = ["apple", "star", "ball", "flower", "kite", "balloon", "cup", "book", "cookie",
           "boat", "cake", "hat", "bell", "drum", "heart", "umbrella", "pencil", "cloud",
           "house", "tree"]
ITEMS = {w: (w, w + "s") for w in _THINGS}
TUNES = ["twinkle", "mary", "row"]
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
         "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
         "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]


def word(n: int) -> str:
    return WORDS[n]


def cap(s: str) -> str:
    return s[0].upper() + s[1:]


def noun(item: str, n: int) -> str:
    return ITEMS[item][0 if n == 1 else 1]


def make_kids(rng: random.Random, k: int) -> list:
    """k different kids with varied skin, hair and clothes."""
    kids = []
    for name in rng.sample(NAMES, k):
        kids.append({
            "name": name,
            "skin": list(rng.choice(SKIN)),
            "hair": list(rng.choice(HAIR)),
            "style": rng.choice(STYLES),
            "shirt": list(rng.choice(SHIRTS)),
            "pants": list(rng.choice(PANTS)),
        })
    return kids


def lesson(rng, title, description, tags, scenes):
    tune = rng.choice(TUNES)
    # Often add an invented sidekick. Kids stay the main characters: the pal is
    # small, stands beside them, and has no lines of its own.
    if scenes and "kids" in scenes[0] and rng.random() < 0.6:
        pal = new_pal(rng)
        for sc in scenes:
            sc["pals"] = [pal]
        scenes.insert(1, {"kids": scenes[0]["kids"], "pals": [pal], "cheer": True,
                          "line": f"And this is our new friend {pal['name']}!"})
    return {
        "title": title,
        "description": description,
        "tags": tags,
        "voice": "af_heart",
        "speed": 0.9,
        "pitch": 1.2,
        "tune": tune,
        "scenes": scenes,
    }
