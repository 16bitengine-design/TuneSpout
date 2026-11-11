"""Checks lessons are kid-safe, the math is right, and every scene draws.
Run: python -m pytest tests"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import music  # noqa: E402
import render  # noqa: E402
from generators import GENERATORS, generate  # noqa: E402
from safety import check_lesson  # noqa: E402


def _check_equation(eq):
    left, right = eq.split("=")
    a, op, b = left.split()
    a, b = int(a), int(b)
    result = {"+": a + b, "-": a - b, "×": a * b, "÷": a // b}[op]
    assert result == int(right), eq
    if op == "÷":
        assert a % b == 0, eq


def test_curated_lessons_pass_safety():
    for f in (ROOT / "lessons").rglob("*.json"):
        check_lesson(json.loads(f.read_text()))


def test_generated_lessons_are_safe_and_correct():
    for topic in GENERATORS:
        for seed in range(40):
            lesson = generate(topic, seed)
            check_lesson(lesson)
            for key in ("title", "description", "tags", "tune"):
                assert lesson.get(key), (topic, key)
            for sc in lesson["scenes"]:
                assert len(sc.get("kids", [])) <= 2
                items = sc.get("items")
                if items:
                    assert items["count"] <= 20
                    if items.get("split"):
                        assert sum(items["split"]) == items["count"]
                if "=" in sc.get("equation", ""):
                    _check_equation(sc["equation"])


def test_every_scene_renders():
    for topic in GENERATORS:
        lesson = json.loads(json.dumps(generate(topic, 7)))  # as read from a file
        for sc in lesson["scenes"]:
            for t in (0.0, 1.0):
                img = render.draw_scene(sc, t, size=(320, 180))
                assert img.size == (320, 180)


def test_tunes_have_right_length():
    for name in music.TUNES:
        assert len(music.tune_track(name, 3.0)) == 3 * music.SR
