"""Split a long lesson into parts that are never longer than three minutes.

A lesson up to three minutes stays one video. A longer one is cut at scene
boundaries (never in the middle of a line) into the fewest parts that fit,
made as equal in length as the scenes allow.
"""
import math

LIMIT = 180.0  # the longest any part may be, in seconds


def split(durations, limit=LIMIT):
    """Scene lengths in seconds -> list of (first, last_exclusive) scene ranges."""
    total, n = sum(durations), len(durations)
    if total <= limit:
        return [(0, n)]
    parts = math.ceil(total / limit)
    while True:
        target = total / parts
        ranges, start, acc = [], 0, 0.0
        for i, d in enumerate(durations):
            # close the part when adding this scene would pass the limit,
            # or when it has reached its fair share (and more parts remain)
            if acc and (acc + d > limit or (acc >= target and len(ranges) < parts - 1)):
                ranges.append((start, i))
                start, acc = i, 0.0
            acc += d
        ranges.append((start, n))
        if all(sum(durations[a:b]) <= limit or b - a == 1 for a, b in ranges):
            return ranges
        parts += 1  # uneven scenes made a part too long: use one more part


def episode_title(title, number, total):
    """'Counting Fun | Sing along' -> 'Counting Fun | Sing along (Part 2 of 3)'."""
    return title if total == 1 else f"{title} (Part {number} of {total})"
