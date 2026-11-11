"""Generate today's lesson (nothing is stored in the repo).

  python src/generate_lesson.py --topic auto --out out/lesson.json
  python src/generate_lesson.py --topic addition --seed 42 --out out/lesson.json

`auto` rotates through all topics by date; the seed defaults to today's date,
so every day gets a different, repeatable lesson.
"""
import argparse
import datetime
import json
from pathlib import Path

from generators import TOPICS, generate
from safety import check_lesson


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", default="auto", choices=["auto", *TOPICS])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--out", default="out/lesson.json")
    args = ap.parse_args()

    today = datetime.date.today()
    seed = args.seed if args.seed is not None else int(today.strftime("%Y%m%d"))
    topic = TOPICS[today.toordinal() % len(TOPICS)] if args.topic == "auto" else args.topic

    lesson = generate(topic, seed)
    check_lesson(lesson)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(lesson, indent=2, ensure_ascii=False))
    print(f"{topic} (seed {seed}): {lesson['title']}")


if __name__ == "__main__":
    main()
