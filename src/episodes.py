"""Split a long lesson into episodes of about two minutes.

A lesson up to three minutes stays one video. A longer one is cut at scene
boundaries (never in the middle of a line) into episodes near two minutes.
"""
TARGET = 120.0   # seconds an episode should be about
LIMIT = 180.0    # longer than this gets split
MIN_TAIL = 45.0  # a short last piece is folded into the episode before it


def split(durations, target=TARGET, limit=LIMIT, min_tail=MIN_TAIL):
    """Scene lengths in seconds -> list of (first, last_exclusive) scene ranges."""
    n = len(durations)
    if sum(durations) <= limit:
        return [(0, n)]
    ranges, start, acc = [], 0, 0.0
    for i, d in enumerate(durations):
        acc += d
        if acc >= target:
            ranges.append((start, i + 1))
            start, acc = i + 1, 0.0
    if start < n:
        if ranges and acc < min_tail:
            ranges[-1] = (ranges[-1][0], n)
        else:
            ranges.append((start, n))
    return ranges


def episode_title(title, number, total):
    """'Counting Fun | Sing along' -> 'Counting Fun | Sing along (Part 2 of 3)'."""
    return title if total == 1 else f"{title} (Part {number} of {total})"
