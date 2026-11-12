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


def estimate_seconds(scenes):
    """Rough running time: about 2.2 spoken words a second plus a pause after each line."""
    return sum(len(sc["line"].split()) / 2.2 + 0.6 for sc in scenes)


def generate_long(topic: str, seed: int, minutes: float) -> dict:
    """A longer lesson: the same topic with new friends and new examples, one segment
    after another, until it runs about `minutes`. make_video cuts it into parts of
    three minutes at most. Every segment keeps its own opening; all but the last
    drop their closing line so the show only says goodbye once."""
    lesson = generate(topic, seed)
    segments = [list(lesson["scenes"])]
    n = 0
    while sum(estimate_seconds(seg) for seg in segments) < minutes * 60 and n < 40:
        n += 1
        more = generate(topic, seed + 1000 * n)
        segments[-1] = segments[-1][:-1]
        segments.append(list(more["scenes"]))
    lesson["scenes"] = [sc for seg in segments for sc in seg]
    return lesson
