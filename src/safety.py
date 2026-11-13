"""Simple guardrail: block lessons with unsafe words or hard language.

This is a first filter only. A human should still watch each video before
it goes public (set PRIVACY=private in the workflow until you trust it).
"""
import re

BLOCKLIST = {
    "kill", "die", "dead", "blood", "gun", "shoot", "hit", "punch", "fight",
    "stupid", "dumb", "hate", "ugly", "fat", "scary", "monster", "weapon",
}
# Words the channel owner never wants seen or heard, anywhere in a video (matched as the
# start of a word, so "pigs" and "piglet" are caught too). Add more here.
NEVER_USE = ("pig",)
MAX_WORDS_PER_LINE = 25  # short sentences suit under-12s


def _all_text(lesson):
    """Every piece of text a lesson can show or say: lines, banners, title, description, tags."""
    parts = [str(lesson.get(k, "")) for k in ("title", "description")] + [str(t) for t in lesson.get("tags", [])]
    for sc in lesson.get("scenes", []):
        parts += [str(sc.get("line", "")), str(sc.get("equation", ""))]
        parts += [str(v) for v in (sc.get("items") or {}).get("types", [])] + [str((sc.get("items") or {}).get("type", ""))]
    return " ".join(parts).lower()


def check_lesson(lesson: dict) -> None:
    for banned in NEVER_USE:
        if re.search(r"\b" + banned, _all_text(lesson)):
            raise ValueError(f"The word '{banned}' is never used in our videos")
    for i, sc in enumerate(lesson.get("scenes", []), 1):
        words = re.findall(r"[a-zA-Z']+", sc.get("line", "").lower())
        bad = BLOCKLIST.intersection(words)
        if bad:
            raise ValueError(f"Scene {i} has unsafe words: {sorted(bad)}")
        if len(words) > MAX_WORDS_PER_LINE:
            raise ValueError(f"Scene {i} is too long ({len(words)} words)")
    if not lesson.get("scenes"):
        raise ValueError("Lesson has no scenes")
