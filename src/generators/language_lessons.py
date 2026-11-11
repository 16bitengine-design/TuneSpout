"""English lessons: plurals (one and many)."""
import random

from generators.common import ITEMS, cap, lesson, make_kids, word


def plurals(seed):
    rng = random.Random(seed)
    kid_a, kid_b = make_kids(rng, 2)
    kids = [kid_a, kid_b]
    scenes = [{"kids": kids,
               "line": f"Hi! We are {kid_a['name']} and {kid_b['name']}. Let us learn about one and many!"}]
    for item in rng.sample(list(ITEMS), 3):
        sing, plur = ITEMS[item]
        k = rng.randint(2, 5)
        scenes += [
            {"kids": kids, "items": {"type": item, "count": 1, "new_from": 0},
             "equation": f"1 {sing}", "line": f"One {sing}."},
            {"kids": kids, "items": {"type": item, "count": k, "new_from": 0},
             "equation": f"{k} {plur}", "line": f"{cap(word(k))} {plur}!"},
        ]
    scenes.append({"kids": kids, "cheer": True,
                   "line": "When there is more than one, we add an s!"})
    return lesson(rng, f"One and Many with {kid_a['name']} and {kid_b['name']} | Plurals for Kids",
                  "Learn plural words: one apple, many apples. English for kids.",
                  ["plurals", "english for kids", "learn english", "kids learning"], scenes)
