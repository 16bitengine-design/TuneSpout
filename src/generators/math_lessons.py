"""Counting, adding, subtracting, multiplying and dividing with kids and objects."""
import random

from generators.common import ITEMS, cap, lesson, make_kids, noun, word


def _distinct(rng, count, make):
    out = []
    while len(out) < count:
        p = make()
        if p not in out:
            out.append(p)
    return out


def counting(seed):
    rng = random.Random(seed)
    (kid,) = make_kids(rng, 1)
    name = kid["name"]
    item = rng.choice(list(ITEMS))
    n = rng.randint(5, 10)
    scenes = [{"kids": [kid],
               "line": f"Hello friends! I am {name}. Let us count {ITEMS[item][1]} together!"}]
    for i in range(1, n + 1):
        scenes.append({"kids": [kid], "equation": str(i),
                       "items": {"type": item, "count": i, "new_from": i - 1},
                       "line": f"{cap(word(i))} {noun(item, i)}!"})
    scenes.append({"kids": [kid], "cheer": True, "equation": str(n),
                   "items": {"type": item, "count": n, "new_from": n},
                   "line": f"{cap(word(n))} {noun(item, n)} in all. Great counting, {name}!"})
    return lesson(rng, f"Count to {n} with {name} | Counting Song for Kids",
                  f"Count {ITEMS[item][1]} from 1 to {n} with {name}. Fun counting for kids.",
                  ["counting", "numbers", "learn to count", "kids song"], scenes)


def addition(seed):
    rng = random.Random(seed)
    a_kid, b_kid = make_kids(rng, 2)
    A, B = a_kid["name"], b_kid["name"]
    kids = [a_kid, b_kid]
    item = rng.choice(list(ITEMS))
    top = rng.choice([10, 10, 20])

    def make():
        a = rng.randint(1, top - 1)
        return (a, rng.randint(1, top - a))

    scenes = [{"kids": kids,
               "line": f"Hello! We are {A} and {B}. Today we learn to add {ITEMS[item][1]}!"}]
    for a, b in _distinct(rng, 3, make):
        t = a + b
        scenes += [
            {"kids": kids, "items": {"type": item, "count": a, "new_from": 0},
             "line": f"{A} has {word(a)} {noun(item, a)}."},
            {"kids": kids, "items": {"type": item, "count": t, "split": [a, b], "new_from": a},
             "line": f"{B} gives {word(b)} more."},
            {"kids": kids, "items": {"type": item, "count": t, "split": [a, b], "new_from": t},
             "equation": f"{a} + {b} = {t}",
             "line": f"{cap(word(a))} plus {word(b)} makes {word(t)}!"},
        ]
    scenes.append({"kids": kids, "cheer": True, "line": "Great adding! Now you can try it too!"})
    return lesson(rng, f"Adding with {A} and {B} | Addition for Kids",
                  f"Learn to add numbers up to {top} with {A} and {B}.",
                  ["addition", "math for kids", "learn to add", "kids math"], scenes)


def subtraction(seed):
    rng = random.Random(seed)
    a_kid, b_kid = make_kids(rng, 2)
    A, B = a_kid["name"], b_kid["name"]
    kids = [a_kid, b_kid]
    item = rng.choice(list(ITEMS))
    top = rng.choice([10, 10, 20])

    def make():
        a = rng.randint(3, top)
        return (a, rng.randint(1, a - 1))

    scenes = [{"kids": kids,
               "line": f"Hi! I am {A}. This is {B}. Let us learn to take away {ITEMS[item][1]}!"}]
    for a, b in _distinct(rng, 3, make):
        r = a - b
        scenes += [
            {"kids": kids, "items": {"type": item, "count": a, "new_from": 0},
             "line": f"{A} has {word(a)} {noun(item, a)}."},
            {"kids": kids, "items": {"type": item, "count": a, "split": [r, b], "ghost": b, "new_from": a},
             "line": f"{A} gives {word(b)} to {B}. How many are left?"},
            {"kids": kids, "items": {"type": item, "count": a, "split": [r, b], "ghost": b, "new_from": a},
             "equation": f"{a} - {b} = {r}",
             "line": f"{cap(word(a))} take away {word(b)} leaves {word(r)}!"},
        ]
    scenes.append({"kids": kids, "cheer": True, "line": "Great job! Sharing and counting is fun!"})
    return lesson(rng, f"Taking Away with {A} and {B} | Subtraction for Kids",
                  f"Learn to subtract numbers up to {top} with {A} and {B}.",
                  ["subtraction", "math for kids", "take away", "kids math"], scenes)


def multiplication(seed):
    rng = random.Random(seed)
    a_kid, b_kid = make_kids(rng, 2)
    A, B = a_kid["name"], b_kid["name"]
    kids = [a_kid, b_kid]
    item = rng.choice(list(ITEMS))

    def make():
        return (rng.randint(2, 4), rng.randint(2, 5))  # n groups of m

    scenes = [{"kids": kids,
               "line": f"Hello! We are {A} and {B}. Today we learn about groups!"}]
    for n, m in _distinct(rng, 2, make):
        t = n * m
        groups = {"type": item, "count": t, "split": [m] * n}
        skips = ", ".join(word(m * i) for i in range(1, n + 1))
        scenes += [
            {"kids": kids, "items": dict(groups, new_from=0),
             "line": f"Here are {word(n)} groups of {word(m)}."},
            {"kids": kids, "items": dict(groups, new_from=t),
             "line": f"Let us count them: {skips}."},
            {"kids": kids, "items": dict(groups, new_from=t), "equation": f"{n} × {m} = {t}",
             "line": f"{cap(word(n))} times {word(m)} is {word(t)}!"},
        ]
    scenes.append({"kids": kids, "cheer": True, "line": "Great work! Groups make counting fast!"})
    return lesson(rng, f"Groups and Times Tables with {A} and {B} | Multiplication for Kids",
                  f"Learn multiplication as groups of things with {A} and {B}.",
                  ["multiplication", "times tables", "math for kids", "kids math"], scenes)


def division(seed):
    rng = random.Random(seed)
    a_kid, b_kid = make_kids(rng, 2)
    A, B = a_kid["name"], b_kid["name"]
    kids = [a_kid, b_kid]
    item = rng.choice(list(ITEMS))

    scenes = [{"kids": kids,
               "line": f"Hello! We are {A} and {B}. Today we learn to share fairly!"}]
    for m in rng.sample(range(2, 6), 3):  # each kid gets m, so 2*m things to share
        t = 2 * m
        scenes += [
            {"kids": kids, "items": {"type": item, "count": t, "new_from": 0},
             "line": f"{A} and {B} have {word(t)} {noun(item, t)} to share."},
            {"kids": kids, "items": {"type": item, "count": t, "split": [m, m], "new_from": t},
             "line": f"One for {A}, one for {B}, until they are all shared."},
            {"kids": kids, "items": {"type": item, "count": t, "split": [m, m], "new_from": t},
             "equation": f"{t} ÷ 2 = {m}",
             "line": f"{cap(word(t))} shared between two is {word(m)} each!"},
        ]
    scenes.append({"kids": kids, "cheer": True, "line": "Great sharing! Fair shares make friends happy!"})
    return lesson(rng, f"Sharing Fairly with {A} and {B} | Division for Kids",
                  f"Learn division as fair sharing with {A} and {B}.",
                  ["division", "sharing", "math for kids", "kids math"], scenes)
