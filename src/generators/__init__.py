"""Lesson generators. Each takes a seed and returns a lesson dict."""
from generators.language_lessons import plurals
from generators.math_lessons import addition, counting, division, multiplication, subtraction

GENERATORS = {
    "counting": counting,
    "addition": addition,
    "subtraction": subtraction,
    "multiplication": multiplication,
    "division": division,
    "plurals": plurals,
}
TOPICS = list(GENERATORS)


def generate(topic: str, seed: int) -> dict:
    return GENERATORS[topic](seed)
