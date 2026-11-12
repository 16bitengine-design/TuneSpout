"""Shared helpers for lesson generators. All lessons are built from a seed,
so the same seed always gives the same lesson and nothing needs to be stored."""
import random

from characters.cast import cast_pals, extra_kids, pick_kids

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
    """k of the recurring main kids (see characters/cast.py)."""
    return pick_kids(rng, k)


def lesson(rng, title, description, tags, scenes):
    tune = rng.choice(TUNES)
    # The two cast animals join every lesson beside the kids. Two replaceable extras
    # (random background kids) stand behind, so each video looks a little different.
    if scenes and "kids" in scenes[0]:
        pals, extras = cast_pals(), extra_kids(rng, 2)
        for sc in scenes:
            sc["pals"] = pals
            sc["extras"] = extras
        scenes.insert(1, {"kids": scenes[0]["kids"], "pals": pals, "extras": extras, "cheer": True,
                          "line": f"Look! {pals[0]['name']} and {pals[1]['name']} came to play too!"})
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
