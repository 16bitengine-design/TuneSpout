"""Lesson generators. Each takes a seed and returns a lesson dict."""
import random

from generators.language_lessons import plurals
from generators.life_skills import finding_out, kind_words, leadership, planning, reporting
from generators.math_lessons import addition, counting, division, multiplication, subtraction
from generators.nature_lessons import animal_sounds, baby_animals
from generators.reading_lessons import phonics, spelling
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
    "animalsounds": animal_sounds,
    "babyanimals": baby_animals,
    "phonics": phonics,
    "spelling": spelling,
    "planning": planning,
    "kindwords": kind_words,
    "findingout": finding_out,
    "leadership": leadership,
    "reporting": reporting,
}
TOPICS = list(GENERATORS)

# Subjects ("pillars") the channel rotates through. Each day has two videos and the two
# are always different subjects, so no day (or week) is all one subject.
PILLARS = {
    "literacy": ["phonics", "spelling", "plurals"],
    "numeracy": ["counting", "addition", "subtraction", "multiplication", "division"],
    "animals": ["animalsounds", "babyanimals"],
    "life_skills": ["planning", "kindwords", "findingout", "leadership", "reporting"],
    "sports": ["sports", "teamscore", "fairplay"],
}
PILLAR_OF = {topic: pillar for pillar, topics in PILLARS.items() for topic in topics}

# Monday..Sunday, two videos a day (video 1, video 2). Edit this table to change the rotation.
WEEK_PLAN = [
    ("literacy", "numeracy"),      # Mon
    ("animals", "life_skills"),    # Tue
    ("sports", "literacy"),        # Wed
    ("numeracy", "animals"),       # Thu
    ("life_skills", "sports"),     # Fri
    ("literacy", "animals"),       # Sat
    ("life_skills", "numeracy"),   # Sun
]


def pick_topic(day, slot: int = 1) -> str:
    """The topic for a given date and video slot (1 or 2), rotating subjects every day.
    Inside a subject the topics take turns, so nothing repeats until the subject's list is used up."""
    plan = [p for pair in WEEK_PLAN for p in pair]
    week = (day.toordinal() - day.weekday()) // 7
    pos = day.weekday() * 2 + (2 if slot >= 2 else 1) - 1
    pillar = plan[pos]
    turn = week * plan.count(pillar) + plan[:pos].count(pillar)
    topics = PILLARS[pillar]
    return topics[turn % len(topics)]

# How long each topic's lesson should run, in minutes: (shortest, longest).
# Easy ideas stay short, harder ones get more examples. Anything over 3 minutes is
# cut into parts of at most 3 minutes (see episodes.py). Edit freely; the whole
# range is kept between MIN_MINUTES and MAX_MINUTES.
MIN_MINUTES, MAX_MINUTES = 1.0, 9.0
TOPIC_MINUTES = {
    "counting": (1.0, 2.0),
    "leadership": (2.0, 3.5),
    "reporting": (1.5, 3.0),
    "planning": (1.5, 3.0),
    "kindwords": (1.5, 3.0),
    "findingout": (1.5, 3.0),
    "phonics": (1.5, 3.0),
    "spelling": (2.0, 4.0),
    "animalsounds": (1.5, 3.0),
    "babyanimals": (1.5, 3.0),
    "plurals": (1.5, 3.0),
    "fairplay": (1.5, 3.0),
    "sports": (2.0, 4.0),
    "addition": (2.0, 4.0),
    "subtraction": (2.0, 4.0),
    "teamscore": (2.0, 4.0),
    "multiplication": (3.0, 6.0),
    "division": (3.0, 6.0),
}


def target_minutes(topic: str, seed: int) -> float:
    """Today's length for a topic: a repeatable pick inside its range."""
    low, high = TOPIC_MINUTES[topic]
    low, high = max(low, MIN_MINUTES), min(high, MAX_MINUTES)
    return round(random.Random(seed * 31 + 7).uniform(low, high) * 4) / 4  # nearest quarter minute


def generate(topic: str, seed: int) -> dict:
    lesson = GENERATORS[topic](seed)
    lesson["topic"] = topic  # used for automatic descriptions and hashtags
    lesson["pillar"] = PILLAR_OF[topic]  # used to theme the background of each scene
    for scene in lesson["scenes"]:
        scene.setdefault("pillar", lesson["pillar"])
    return lesson


def estimate_seconds(scenes):
    """Rough running time: about 2.2 spoken words a second plus a pause after each line."""
    return sum(len(sc["line"].split()) / 2.2 + 0.6 for sc in scenes)


def generate_long(topic: str, seed: int, minutes: float) -> dict:
    """A longer lesson: the same topic with new friends and new examples, one segment
    after another, until it runs about `minutes`. make_video cuts it into parts of
    three minutes at most. Every segment keeps its own opening; all but the last
    drop their closing line so the show only says goodbye once."""
    minutes = min(max(minutes, MIN_MINUTES), MAX_MINUTES)
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
