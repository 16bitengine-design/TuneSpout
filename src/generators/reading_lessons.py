"""Reading lessons: letter sounds (phonics) and spelling short words.
Only things we can draw clearly are used, so the picture always matches the word."""
import random

import characters.animals  # noqa: F401  (adds the animals to the drawing library)
from generators.common import cap, lesson, make_kids

BIG = 2.4

# letter, how its sound is spelled out for the voice, a thing that starts with it
LETTERS = [
    ("a", "ah", "apple"), ("b", "buh", "ball"), ("c", "kuh", "cat"), ("d", "duh", "dog"),
    ("f", "fuh", "frog"), ("h", "huh", "hat"), ("k", "kuh", "kite"), ("p", "puh", "pig"),
    ("s", "sss", "star"), ("t", "tuh", "tree"), ("u", "uh", "umbrella"),
]

# short words we can both spell and draw
SPELL_WORDS = ["cat", "dog", "pig", "hat", "cup", "cow"]


def a_or_an(thing):
    return "an" if thing[0] in "aeiou" else "a"


def phonics(seed):
    rng = random.Random(seed)
    kids = make_kids(rng, 2)
    A, B = kids[0]["name"], kids[1]["name"]
    picks = rng.sample(LETTERS, 4)
    scenes = [{"kids": kids, "line": f"Hello! We are {A} and {B}. Let us learn letter sounds!"}]
    for letter, sound, thing in picks:
        shown = {"type": thing, "count": 1, "scale": BIG}
        banner = f"{letter.upper()} {letter}"
        scenes += [
            {"kids": kids, "items": shown, "equation": banner,
             "line": f"This is the letter {letter.upper()}. {letter.upper()} says, {sound}."},
            {"kids": kids, "items": shown, "equation": banner, "cheer": True,
             "line": f"{letter.upper()} is for {thing}!"},
            {"kids": kids, "items": shown, "equation": banner,
             "line": f"Say it with us: {sound}, {sound}, {thing}!"},
        ]
    letters = ", ".join(p[0].upper() for p in picks[:-1]) + f" and {picks[-1][0].upper()}"
    scenes.append({"kids": kids, "cheer": True,
                   "line": f"Hooray! Now you know the sounds of {letters}. Bye from {A} and {B}!"})
    return lesson(rng, f"Letter Sounds with {A} and {B} | Phonics for Kids",
                  f"Learn the sounds of the letters {letters} with {A} and {B}. Phonics for kids.",
                  ["phonics", "letter sounds", "learn to read", "kids learning"], scenes)


def spelling(seed):
    rng = random.Random(seed)
    kids = make_kids(rng, 2)
    A, B = kids[0]["name"], kids[1]["name"]
    picks = rng.sample(SPELL_WORDS, 3)
    scenes = [{"kids": kids, "line": f"Hi! We are {A} and {B}. Let us spell some words!"}]
    for word in picks:
        shown = {"type": word, "count": 1, "scale": BIG}
        scenes.append({"kids": kids, "items": shown, "equation": cap(word),
                       "line": f"This is {a_or_an(word)} {word}. Let us spell it!"})
        for i, letter in enumerate(word):
            scenes.append({"kids": kids, "items": shown, "equation": " ".join(word[:i + 1].upper()),
                           "line": f"{letter.upper()}!"})
        spelled = ", ".join(word.upper())
        scenes.append({"kids": kids, "items": shown, "equation": " ".join(word.upper()), "cheer": True,
                       "line": f"{spelled}. {cap(word)}! We spelled {word}!"})
    scenes.append({"kids": kids, "cheer": True,
                   "line": f"Great spelling! Bye from {A} and {B}!"})
    return lesson(rng, f"Spelling Fun with {A} and {B} | Spell Words for Kids",
                  f"Spell {picks[0]}, {picks[1]} and {picks[2]} one letter at a time with {A} and {B}.",
                  ["spelling for kids", "spell words", "learn to read", "kids learning"], scenes)
