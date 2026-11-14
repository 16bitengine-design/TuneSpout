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


def _hold(sc, line, speaker, **extra):
    """A new short scene that keeps the picture of `sc` but has a new line and speaker."""
    new = {k: v for k, v in sc.items() if k not in ("line", "speaker", "cheer", "enter")}
    if new.get("items"):  # things already on screen do not pop in again
        items = dict(new["items"])
        items["new_from"] = sum(items.get("split") or [items["count"]])
        new["items"] = items
    new.update(line=line, speaker=speaker, **extra)
    return new


def _direct(rng, scenes, pals):
    """Give every video a lead kid who teaches, shares the teaching with a friend, and
    animal pals who ask questions. Scenes get 'speaker' (a cast name) and 'lead'."""
    kids = scenes[0]["kids"]
    lead = kids[0]["name"]
    helper = kids[1]["name"] if len(kids) > 1 else None
    yum, lum = pals[0]["name"], pals[1]["name"]
    asker, other = (yum, lum) if rng.random() < 0.5 else (lum, yum)
    for sc in scenes:
        sc["lead"] = lead
        sc.setdefault("speaker", lead)
    scenes[0]["enter"] = True  # the cast walks in at the start
    intro = scenes[0]
    scenes[1:1] = [
        _hold(intro, f"Look! {yum} and {lum} came to play too!", lead, cheer=True),
        _hold(intro, f"Hi {lead}! Can we learn with you today?", asker),
        _hold(intro, f"Yes! Come with me, friends. I will show you!", lead),
    ]
    body_start, last = 4, len(scenes) - 1  # scenes[last] is the goodbye
    n = last - body_start
    if n >= 6:  # a pal asks a question, the lead answers
        at = body_start + n // 3
        scenes[at:at] = [_hold(scenes[at - 1], "Wow! Can you show us another one?", other),
                         _hold(scenes[at - 1], f"Of course, {other}! Here is another one.", lead)]
        last += 2
    if helper and n >= 6:  # the lead hands over: the friend teaches a part
        at = body_start + 2 + (last - body_start) // 2
        scenes[at:at] = [_hold(scenes[at - 1], f"{helper}, would you like to show the next part?", lead),
                         _hold(scenes[at - 1], f"Yes, {lead}! I know this one. Watch me!", helper)]
        last += 2
        for sc in scenes[at + 2:at + 4]:
            if sc is not scenes[last]:
                sc["speaker"] = helper
    if helper:  # the finale: knowledge is shared
        scenes[last:last] = [
            _hold(scenes[last - 1], "Now you know it too! Share what you know with a friend.", lead),
            _hold(scenes[last - 1], f"Thank you, {lead}! Sharing makes learning fun!", helper)]


def lesson(rng, title, description, tags, scenes):
    tune = rng.choice(TUNES)
    # The two cast animals join every lesson beside the kids. Two replaceable extras
    # (random background kids) stand behind, so each video looks a little different.
    if scenes and "kids" in scenes[0]:
        pals, extras = cast_pals(), extra_kids(rng, 2)
        for sc in scenes:
            sc["pals"] = pals
            sc["extras"] = extras
        _direct(rng, scenes, pals)
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
