"""Life and thinking skills: planning in steps, kind words, and finding out answers.
Gentle and positive. Every problem is solved with kindness, patience or a good question."""
import random

import characters.animals  # noqa: F401  (adds the animals to the drawing library)
from generators.common import cap, lesson, make_kids

BIG = 2.4

# a goal and three steps, each shown with something we can draw
PLANS = [
    ("have a birthday party", [("balloon", "First, we blow up the balloons."),
                               ("cake", "Next, we bake a yummy cake."),
                               ("heart", "Last, we invite our friends and share.")]),
    ("fly a kite", [("kite", "First, we pick a kite."),
                    ("cloud", "Next, we check that the sky is clear."),
                    ("heart", "Last, we run and let the kite fly.")]),
    ("go out in the rain", [("umbrella", "First, we get our umbrella."),
                            ("hat", "Next, we put on our hats."),
                            ("cloud", "Last, we splash outside!")]),
    ("share a story", [("book", "First, we choose a book."),
                       ("pencil", "Next, we draw our favorite part."),
                       ("heart", "Last, we tell the story to a friend.")]),
]

# magic words and a kind moment for each
KIND_WORDS = [
    ("please", "cookie", "When we ask for something, we say please."),
    ("thank you", "heart", "When someone helps us, we say thank you."),
    ("sorry", "heart", "If we make a mistake, we say sorry and help fix it."),
    ("can I help", "book", "When a friend needs a hand, we ask, can I help?"),
    ("you go first", "ball", "When we share, we can say, you go first."),
]

# questions we can answer by looking and checking
FACTS = [
    ("What does a duck say?", "duck", "A duck says quack.", "quack"),
    ("What is a baby cow called?", "calf", "A baby cow is called a calf.", "calf"),
    ("What does a cat say?", "cat", "A cat says meow.", "meow"),
    ("What does a dog say?", "dog", "A dog says woof.", "woof"),
    ("What is a baby sheep called?", "lamb", "A baby sheep is called a lamb.", "lamb"),
]


def planning(seed):
    rng = random.Random(seed)
    kids = make_kids(rng, 2)
    A, B = kids[0]["name"], kids[1]["name"]
    goal, steps = rng.choice(PLANS)
    scenes = [{"kids": kids, "line": f"Hello! We are {A} and {B}. Today we make a plan to {goal}!"},
              {"kids": kids, "equation": "Plan", "line": "A plan is the steps we do, one at a time."}]
    for number, ((thing, line), label) in enumerate(zip(steps, ("First", "Next", "Last")), 1):
        scenes.append({"kids": kids, "items": {"type": thing, "count": 1, "scale": BIG},
                       "equation": f"{number}. {label}", "line": line, "cheer": number == 3})
    scenes.append({"kids": kids, "cheer": True,
                   "line": f"We did it! Plans make big jobs easy. Bye from {A} and {B}!"})
    return lesson(rng, f"Let's Make a Plan with {A} and {B} | First, Next, Last",
                  f"Learn to plan in three steps and {goal} with {A} and {B}. Life skills for kids.",
                  ["planning for kids", "first next last", "life skills", "kids learning"], scenes)


def kind_words(seed):
    rng = random.Random(seed)
    kids = make_kids(rng, 2)
    A, B = kids[0]["name"], kids[1]["name"]
    picks = rng.sample(KIND_WORDS, 4)
    scenes = [{"kids": kids, "line": f"Hi! We are {A} and {B}. Let us learn kind words!"}]
    for phrase, thing, line in picks:
        shown = {"type": thing, "count": 1, "scale": BIG}
        scenes += [
            {"kids": kids, "items": shown, "equation": cap(phrase), "line": line},
            {"kids": kids, "items": shown, "equation": cap(phrase), "cheer": True,
             "line": f"Say it with us: {phrase}!"},
        ]
    scenes.append({"kids": kids, "cheer": True,
                   "line": f"Kind words make everyone smile! Bye from {A} and {B}!"})
    return lesson(rng, f"Kind Words with {A} and {B} | Manners for Kids",
                  f"Learn kind words like please and thank you with {A} and {B}. People skills for kids.",
                  ["kind words", "manners for kids", "people skills", "kids learning"], scenes)


def finding_out(seed):
    rng = random.Random(seed)
    kids = make_kids(rng, 2)
    A, B = kids[0]["name"], kids[1]["name"]
    question, thing, answer, key = rng.choice(FACTS)
    shown = {"type": thing, "count": 1, "scale": BIG}
    scenes = [
        {"kids": kids, "line": f"Hello! We are {A} and {B}. Today we find out an answer!"},
        {"kids": kids, "equation": "Ask", "line": f"First, we ask a question. {question}"},
        {"kids": kids, "items": {"type": "book", "count": 1, "scale": BIG}, "equation": "Look",
         "line": "Next, we look in a book to find the answer."},
        {"kids": kids, "items": shown, "equation": "Found it!", "cheer": True, "line": answer},
        {"kids": kids, "items": shown, "equation": "Check",
         "line": f"Last, we check with a friend. {B} says the same thing. We found the right answer!"},
        {"kids": kids, "cheer": True,
         "line": f"Ask, look and check! Now you can find out answers too. Bye from {A} and {B}!"},
    ]
    return lesson(rng, f"Ask, Look, Check with {A} and {B} | Finding Answers for Kids",
                  f"Learn how to ask a question and check the answer with {A} and {B}. Research skills for kids.",
                  ["research for kids", "asking questions", "thinking skills", "kids learning"], scenes)
