"""Print the next lesson file to build (rotates through lessons/ by date)."""
import datetime
from pathlib import Path

files = sorted(Path("lessons").rglob("*.json"))
if not files:
    raise SystemExit("No lessons found")
print(files[datetime.date.today().toordinal() % len(files)])
