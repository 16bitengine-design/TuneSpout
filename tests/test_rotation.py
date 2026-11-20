"""Checks the daily subject rotation and the lively scene layer.
Run: python -m pytest tests"""
import datetime
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from generators import GENERATORS, PILLAR_OF, PILLARS, WEEK_PLAN, generate, pick_topic  # noqa: E402
import render  # noqa: E402

START = datetime.date(2026, 11, 16)  # a Monday


def test_every_topic_belongs_to_one_pillar():
    assert set(PILLAR_OF) == set(GENERATORS)
    assert sum(len(t) for t in PILLARS.values()) == len(GENERATORS)


def test_two_videos_a_day_are_different_subjects():
    for i in range(60):
        day = START + datetime.timedelta(days=i)
        assert PILLAR_OF[pick_topic(day, 1)] != PILLAR_OF[pick_topic(day, 2)], day


def test_no_subject_dominates_a_week():
    for week in range(8):
        days = [START + datetime.timedelta(days=week * 7 + d) for d in range(7)]
        counts = Counter(PILLAR_OF[pick_topic(day, s)] for day in days for s in (1, 2))
        assert set(counts) == set(PILLARS), "every subject appears each week"
        assert max(counts.values()) <= 3, counts


def test_topics_inside_a_subject_take_turns():
    seen = [pick_topic(START + datetime.timedelta(days=d), s)
            for d in range(70) for s in (1, 2) if PILLAR_OF[pick_topic(START + datetime.timedelta(days=d), s)] == "numeracy"]
    assert set(seen) == set(PILLARS["numeracy"])
    assert all(seen[i] != seen[i + 1] for i in range(len(seen) - 1))


def test_rotation_is_repeatable():
    day = datetime.date(2026, 12, 3)
    assert pick_topic(day, 1) == pick_topic(day, 1)


def test_week_plan_is_complete():
    assert len(WEEK_PLAN) == 7 and all(len(p) == 2 for p in WEEK_PLAN)


def test_scenes_draw_with_life_effects_in_every_subject():
    for topic in ("phonics", "addition", "animalsounds", "planning", "sports"):
        lesson = generate(topic, 5)
        assert lesson["pillar"] == PILLAR_OF[topic]
        for sc in lesson["scenes"][:3]:
            for t in (0.0, 0.3, 2.0):
                img = render.draw_scene(sc, t, size=(180, 320))
                assert img.size == (180, 320)
