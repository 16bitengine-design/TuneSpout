"""Nature lessons: animal names and sounds, and the names of baby animals."""
import random

import characters.animals  # noqa: F401  (adds the animals to the drawing library)
from characters.animals import ANIMALS
from generators.common import cap, lesson, make_kids

BIG = 2.6  # a single animal is shown large in the middle of the scene


def animal_sounds(seed):
    rng = random.Random(seed)
    kids = make_kids(rng, 2)
    A, B = kids[0]["name"], kids[1]["name"]
    picks = rng.sample(list(ANIMALS), 4)
    scenes = [{"kids": kids, "line": f"Hello! We are {A} and {B}. Let us learn animal sounds!"}]
    for name in picks:
        sound = ANIMALS[name]["sound"]
        shown = {"type": name, "count": 1, "scale": BIG}
        scenes += [
            {"kids": kids, "items": shown, "equation": cap(name), "line": f"Look! This is a {name}."},
            {"kids": kids, "items": shown, "equation": cap(name), "cheer": True,
             "line": f"The {name} says, {sound}, {sound}!"},
            {"kids": kids, "items": shown, "equation": cap(name),
             "line": f"Can you say it? {cap(sound)}, {sound}!"},
        ]
    scenes.append({"kids": kids, "cheer": True,
                   "line": f"Great job! Now you know four animal sounds. See you soon, from {A} and {B}!"})
    return lesson(rng, f"Animal Sounds with {A} and {B} | Animals for Kids",
                  f"Learn what the {picks[0]}, the {picks[1]}, the {picks[2]} and the {picks[3]} say, with {A} and {B}.",
                  ["animal sounds", "animals for kids", "farm animals", "kids learning"], scenes)


def baby_animals(seed):
    rng = random.Random(seed)
    kids = make_kids(rng, 2)
    A, B = kids[0]["name"], kids[1]["name"]
    picks = rng.sample(list(ANIMALS), 4)
    scenes = [{"kids": kids, "line": f"Hi! We are {A} and {B}. Let us meet some baby animals!"}]
    for name in picks:
        baby = ANIMALS[name]["baby"]
        scenes += [
            {"kids": kids, "items": {"type": name, "count": 1, "scale": BIG}, "equation": cap(name),
             "line": f"This is a {name}."},
            {"kids": kids, "items": {"types": [name, baby], "count": 2, "split": [1, 1], "scale": BIG},
             "equation": cap(baby), "cheer": True,
             "line": f"A baby {name} is called a {baby}!"},
            {"kids": kids, "items": {"types": [name, baby], "count": 2, "split": [1, 1], "scale": BIG},
             "equation": cap(baby), "line": f"Say it with us: {baby}!"},
        ]
    scenes.append({"kids": kids, "cheer": True,
                   "line": f"Hooray! Now you know four baby animals. Bye from {A} and {B}!"})
    return lesson(rng, f"Baby Animals with {A} and {B} | Animals for Kids",
                  f"Learn the names of baby animals: {ANIMALS[picks[0]]['baby']}, {ANIMALS[picks[1]]['baby']}, "
                  f"{ANIMALS[picks[2]]['baby']} and {ANIMALS[picks[3]]['baby']}, with {A} and {B}.",
                  ["baby animals", "animals for kids", "young animals", "kids learning"], scenes)
