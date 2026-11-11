"""Regenerate the TuneSpout brand images into branding/.

  python tools/make_brand_assets.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import branding  # noqa: E402

for name in branding.write_all(ROOT / "branding"):
    print("wrote branding/" + name)
