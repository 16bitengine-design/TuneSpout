"""Remember what was posted each day, so a retry never posts twice and a
missed run is caught up by the backup run. Only uses the standard library.

The record lives in the `state` branch (checked out into ./state by the
workflow) as state/posted.json:
  {"2026-11-12": {"title": "...", "youtube": {...}, "tiktok": {...}}, "_last_run": "2026-11-12"}

  python src/state.py status [--force]   decide what is still to do today
  python src/state.py record youtube out/result_youtube.json
  python src/state.py merge other.json   combine two copies saved at the same moment
  python src/state.py verify             fail if a connected platform is still missing
"""
import argparse
import datetime
import json
import os
import sys
from pathlib import Path

KEEP_DAYS = 120
PLATFORMS = ("youtube", "tiktok")


def _file():
    return Path(os.environ.get("STATE_DIR", "state")) / "posted.json"


def today():
    return os.environ.get("DAY") or datetime.datetime.now(datetime.timezone.utc).date().isoformat()


def load():
    try:
        return json.loads(_file().read_text())
    except FileNotFoundError:
        return {}


def save(data):
    cutoff = (datetime.date.fromisoformat(today()) - datetime.timedelta(days=KEEP_DAYS)).isoformat()
    data = {k: v for k, v in data.items() if k.startswith("_") or k >= cutoff}  # keep the file small
    _file().parent.mkdir(parents=True, exist_ok=True)
    _file().write_text(json.dumps(data, indent=2, sort_keys=True))


def connected():
    """Platforms whose secrets are set."""
    names = []
    if not os.environ.get("BUFFER_API_KEY"):
        return names
    if os.environ.get("BUFFER_YOUTUBE_CHANNEL_ID"):
        names.append("youtube")
    if os.environ.get("BUFFER_TIKTOK_CHANNEL_ID"):
        names.append("tiktok")
    return names


def status(force=False):
    data = load()
    done = data.get(today(), {})
    plats = connected()
    result = {p: "off" if p not in plats else ("todo" if force or p not in done else "done") for p in PLATFORMS}
    # nothing connected = practice run (build and keep the files, post nowhere)
    pending = not plats or "todo" in result.values()
    result["pending"] = str(pending).lower()
    result["day"] = today()
    if pending:  # a daily heartbeat commit keeps GitHub from switching the schedule off
        data["_last_run"] = today()
        save(data)
    return result


def record(platform, result_file):
    path = Path(result_file)
    if not path.exists():
        print(f"No result file for {platform}; nothing to record.")
        return
    data = load()
    day = data.setdefault(today(), {})
    day[platform] = json.loads(path.read_text())
    lesson = Path(os.environ.get("LESSON_FILE", "out/lesson.json"))
    if lesson.exists():
        info = json.loads(lesson.read_text())
        day["title"], day["topic"] = info.get("title"), info.get("topic")
    save(data)
    print(f"Recorded {platform} for {today()}.")


def merge(other_file):
    """Fold another copy of posted.json into this one. Used when two runs saved at once:
    every platform either run posted is kept, and the newer heartbeat wins."""
    ours = json.loads(Path(other_file).read_text())
    data = load()
    for key, value in ours.items():
        if key.startswith("_"):
            data[key] = max(str(data.get(key, "")), str(value))
        elif isinstance(data.get(key), dict):
            data[key] = {**data[key], **value}
        else:
            data[key] = value
    save(data)


def missing():
    done = load().get(today(), {})
    return [p for p in connected() if p not in done]


def _write_outputs(values):
    out = os.environ.get("GITHUB_OUTPUT")
    lines = "".join(f"{k}={v}\n" for k, v in values.items())
    if out:
        with open(out, "a") as f:
            f.write(lines)
    print(lines, end="")


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status")
    s.add_argument("--force", action="store_true")
    r = sub.add_parser("record")
    r.add_argument("platform", choices=PLATFORMS)
    r.add_argument("result_file")
    m = sub.add_parser("merge")
    m.add_argument("other_file")
    sub.add_parser("verify")
    args = ap.parse_args(argv)

    if args.cmd == "status":
        _write_outputs(status(args.force))
    elif args.cmd == "record":
        record(args.platform, args.result_file)
    elif args.cmd == "merge":
        merge(args.other_file)
    else:
        left = missing()
        if left:
            print(f"::error::Not posted today: {', '.join(left)}")
            return 1
        print("Everything connected was posted today.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
