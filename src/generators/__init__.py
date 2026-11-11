"""Lesson generators. Each takes a seed and returns a lesson dict."""
from generators.language_lessons import plurals
from generators.math_lessons import addition, counting, division, multiplication, subtraction
from generators.sports_lessons import fair_play, sports_names, team_score

GENERATORS = {
    "counting": counting,
    "addition": addition,
    "subtraction": subtraction,
    "multiplication": multiplication,
    "division": division,
    "plurals": plurals,
    "sports": sports_names,
    "teamscore": team_score,
    "fairplay": fair_play,
}
TOPICS = list(GENERATORS)


def generate(topic: str, seed: int) -> dict:
    lesson = GENERATORS[topic](seed)
    lesson["topic"] = topic  # used for automatic descriptions and hashtags
    return lesson
