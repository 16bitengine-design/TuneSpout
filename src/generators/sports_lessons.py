"""Sports lessons: names of sports, team scores (adding), and fair play.
Gentle by design: no contact, nobody "beats" anyone, everyone cheers."""
import random

from generators.common import cap, lesson, make_kids, word

SPORTS = [
    ("football", "We pass the ball with our feet."),
    ("basketball", "We throw the ball up to the net."),
    ("running", "We run fast and then we rest."),
    ("swimming", "We swim and splash in the water."),
    ("jumping", "We jump up high like little frogs."),
    ("volleyball", "We pass the ball over the net."),
    ("tennis", "We send the ball back and forth."),
    ("cycling", "We ride our bikes on the path."),
]


def sports_names(seed):
    rng = random.Random(seed)
    kids = make_kids(rng, 2)
    A, B = kids[0]["name"], kids[1]["name"]
    picks = rng.sample(SPORTS, 3)
    scenes = [{"kids": kids, "line": f"Hello! We are {A} and {B}. Let us learn about sports!"}]
    for name, action in picks:
        scenes += [
            {"kids": kids, "equation": cap(name), "cheer": True,
             "line": f"This is {name}!"},
            {"kids": kids, "equation": cap(name), "line": action},
        ]
    scenes.append({"kids": kids, "cheer": True,
                   "line": "Sports are fun and keep us strong and healthy!"})
    return lesson(rng, f"Fun Sports with {A} and {B} | Sports for Kids",
                  f"Learn the names of sports and how we play them with {A} and {B}.",
                  ["sports", "sports for kids", "kids exercise", "kids learning"], scenes)


def team_score(seed):
    rng = random.Random(seed)
    kids = make_kids(rng, 2)
    A, B = kids[0]["name"], kids[1]["name"]
    scenes = [{"kids": kids,
               "line": f"Hi! We are {A} and {B}. We are on the same team. Let us add our goals!"}]
    for _ in range(3):
        a, b = rng.randint(1, 5), rng.randint(1, 5)
        t = a + b
        scenes += [
            {"kids": kids, "items": {"type": "ball", "count": a, "new_from": 0},
             "line": f"{A} scores {word(a)} {'goal' if a == 1 else 'goals'}."},
            {"kids": kids, "items": {"type": "ball", "count": t, "split": [a, b], "new_from": a},
             "line": f"{B} scores {word(b)} {'goal' if b == 1 else 'goals'}."},
            {"kids": kids, "items": {"type": "ball", "count": t, "split": [a, b], "new_from": t},
             "equation": f"{a} + {b} = {t}", "cheer": True,
             "line": f"Together our team has {word(t)} goals. Hooray!"},
        ]
    scenes.append({"kids": kids, "cheer": True, "line": "Teams win when friends work together!"})
    return lesson(rng, f"Team Goals with {A} and {B} | Adding with Sports",
                  f"Add up team goals with {A} and {B}. Math for kids through sports.",
                  ["sports math", "addition", "math for kids", "teamwork"], scenes)


def fair_play(seed):
    rng = random.Random(seed)
    kids = make_kids(rng, 2)
    A, B = kids[0]["name"], kids[1]["name"]
    rules = [
        ("Take turns", f"{A} goes first, then {B} goes next. We take turns."),
        ("Share the ball", "Everyone gets a turn with the ball. We share."),
        ("Cheer for friends", "We clap and cheer for every player."),
        ("Say well done", f"{B} says well done to {A}. Kind words feel good."),
    ]
    scenes = [{"kids": kids,
               "line": f"Hello! We are {A} and {B}. Today we learn how to play fair!"}]
    for title, line in rng.sample(rules, 3):
        scenes.append({"kids": kids, "equation": title, "line": line,
                       "items": {"type": "ball", "count": 2, "new_from": 0}})
    scenes.append({"kids": kids, "cheer": True,
                   "line": "When we play fair, everyone has fun!"})
    return lesson(rng, f"Playing Fair with {A} and {B} | Sports and Friendship",
                  f"Learn fair play: taking turns, sharing and cheering with {A} and {B}.",
                  ["fair play", "teamwork", "sports for kids", "people skills"], scenes)
