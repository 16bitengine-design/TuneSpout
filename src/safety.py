"""Simple guardrail: block lessons with unsafe words or hard language.

This is a first filter only. A human should still watch each video before
it goes public (set PRIVACY=private in the workflow until you trust it).
"""
import re

BLOCKLIST = {
    "kill", "die", "dead", "blood", "gun", "shoot", "hit", "punch", "fight",
    "stupid", "dumb", "hate", "ugly", "fat", "scary", "monster", "weapon",
}
MAX_WORDS_PER_LINE = 25  # short sentences suit under-12s


def check_lesson(lesson: dict) -> None:
    for i, sc in enumerate(lesson.get("scenes", []), 1):
        words = re.findall(r"[a-zA-Z']+", sc.get("line", "").lower())
        bad = BLOCKLIST.intersection(words)
        if bad:
            raise ValueError(f"Scene {i} has unsafe words: {sorted(bad)}")
        if len(words) > MAX_WORDS_PER_LINE:
            raise ValueError(f"Scene {i} is too long ({len(words)} words)")
    if not lesson.get("scenes"):
        raise ValueError("Lesson has no scenes")
