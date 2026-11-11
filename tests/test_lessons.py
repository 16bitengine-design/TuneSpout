"""Checks every lesson file is valid and kid-safe. Run: python -m pytest tests"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from safety import check_lesson  # noqa: E402


def test_all_lessons_pass_safety():
    files = list((ROOT / "lessons").rglob("*.json"))
    assert files, "no lessons found"
    for f in files:
        lesson = json.loads(f.read_text())
        check_lesson(lesson)
        for key in ("title", "description", "tags"):
            assert key in lesson, f"{f} missing {key}"
