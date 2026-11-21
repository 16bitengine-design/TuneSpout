"""Real-world photo pipeline for the kids learning channel.

Rule for this project: whenever a lesson mentions something that exists in the
real world (duck, frog, dog, table, tree, fruit, money, house ...), learners
see a REAL PHOTO of it, not a cartoon drawing. Cartoon characters (Amina,
Jomo, Mei, Kofi, Yumbi, Lumbo) stay animated; the thing being taught is a photo.

Flow
----
1. ``Lexicon.find_terms(text)``   -> which real-world words appear in a script
2. ``get_photo(term)``            -> download a free-licence photo (cached)
3. ``make_card(photo, label)``    -> 9:16 card, whole photo uncropped + word label
4. ``plan_cues(words)``           -> when each card appears (word timestamps)
5. ``apply_cue(frame, cue, t)``   -> cut away from the cartoon frame to the photo card

Secrets come only from environment variables (GitHub Secrets):
PEXELS_API_KEY, PIXABAY_API_KEY. Wikimedia Commons needs no key.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from functools import lru_cache
from typing import Iterable, Optional, Protocol

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
LEXICON_PATH = ROOT / "config" / "real_world_terms.json"
CACHE_DIR = Path(os.environ.get("PHOTO_CACHE_DIR", ROOT / "cache" / "photos"))
CARD_DIR = Path(os.environ.get("PHOTO_CARD_DIR", ROOT / "cache" / "cards"))

# ---------------------------------------------------------------- safety ----
try:  # the repo's channel-wide list (src/ is on sys.path, like the other modules)
    from safety import NEVER_USE as _NEVER_USE  # type: ignore
except Exception:  # pragma: no cover
    _NEVER_USE = ("pig",)
# Prefixes, exactly like safety.check_lesson: "pig" also catches pigs, piglet, ...
BANNED = tuple({str(w).lower() for w in _NEVER_USE} | {"pig"})

# Words in a photo's tags/description that make it unsuitable for children.
UNSAFE_TAGS = {
    "blood", "dead", "corpse", "roadkill", "hunting", "hunter", "gun", "weapon",
    "knife", "fight", "fighting", "injured", "slaughter", "butcher", "dissection",
    "nude", "bikini", "sexy", "alcohol", "beer", "wine", "cigarette", "smoking",
    "skull", "scary", "horror", "cage", "trap", "taxidermy",
}


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z']+", text.lower()))


def is_banned(text: str) -> bool:
    return any(w.startswith(BANNED) for w in _words(text))


# Copyright / rights risks a licence does NOT cover: identifiable people (model releases),
# logos and brands (trademarks), and artwork/characters (someone else's creation).
RIGHTS_RISK_TAGS = {
    "man", "men", "woman", "women", "boy", "girl", "child", "children", "kid", "kids", "baby",
    "people", "person", "family", "face", "portrait", "model", "couple", "student", "students",
    "logo", "brand", "trademark", "poster", "painting", "artwork", "illustration", "drawing",
    "cartoon", "sculpture", "statue", "mural", "graffiti", "toy", "toys", "lego", "disney",
    "mickey", "mascot", "sign", "label", "packaging", "magazine", "newspaper", "screenshot",
    "watermark", "getty", "shutterstock", "istock", "alamy",
}


def is_unsafe(text: str) -> bool:
    w = _words(text)
    return bool(w & UNSAFE_TAGS) or is_banned(text)


def has_rights_risk(text: str) -> bool:
    """True when tags/description suggest people, logos, artwork or stock-agency marks."""
    return bool(_words(text) & RIGHTS_RISK_TAGS)


def license_allowed(lic: str, allow_cc_by: Optional[bool] = None) -> bool:
    """Strict: CC0 / public domain always; CC BY (attribution only) only if ALLOW_CC_BY=1.
    ShareAlike, NonCommercial and NoDerivatives licences are never accepted."""
    if allow_cc_by is None:
        allow_cc_by = os.environ.get("ALLOW_CC_BY", "0") == "1"
    l = lic.strip().lower()
    if l.startswith(("cc0", "public domain", "pdm", "pd ")) or l == "pd":
        return True
    return bool(allow_cc_by and re.match(r"cc[ -]by[ -]\d", l))


# --------------------------------------------------------------- lexicon ----
TAG_RE = re.compile(r"\[\[([a-z]+)\]\]")


def strip_tags(text: str) -> str:
    """Remove [[tag]] markers so subtitles/TTS never see them."""
    return TAG_RE.sub(r"\1", text)


def _plural(term: str, irregular: dict[str, str]) -> str:
    if term in irregular:
        return irregular[term]
    if re.search(r"(s|x|z|ch|sh)$", term):
        return term + "es"
    if re.search(r"[^aeiou]y$", term):
        return term[:-1] + "ies"
    return term + "s"


@dataclass
class Lexicon:
    entries: dict[str, dict]            # base term -> {"query":..., "category":...}
    forms: dict[str, str]               # surface form -> base term
    ambiguous: set[str] = field(default_factory=set)

    @classmethod
    def load(cls, path: Path = LEXICON_PATH) -> "Lexicon":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        irregular = data.get("irregular_plurals", {})
        entries: dict[str, dict] = {}
        forms: dict[str, str] = {}
        for category, items in data["categories"].items():
            for term, info in items.items():
                if is_banned(term):
                    raise ValueError(f"'{term}' is on the banned list; remove it from the lexicon")
                entry = dict(info or {})
                entry.setdefault("query", term)
                entry["category"] = category
                entries[term] = entry
                forms[term] = term
                forms[_plural(term, irregular)] = term
        return cls(entries, forms, set(data.get("ambiguous", [])))

    def term_for(self, word: str) -> Optional[str]:
        """Base term for one script word, or None. Honors [[tag]] for ambiguous words."""
        w = word.strip().lower().strip(".,!?;:\"'()")
        tagged = TAG_RE.fullmatch(w)
        if tagged:
            return self.forms.get(tagged.group(1))
        base = self.forms.get(w)
        if base is None or base in self.ambiguous:
            return None
        return base

    def find_terms(self, text: str) -> list[str]:
        """Unique base terms in order of first appearance."""
        seen: list[str] = []
        for tok in re.findall(r"\[\[[a-z]+\]\]|[A-Za-z']+", text):
            base = self.term_for(tok)
            if base and base not in seen:
                seen.append(base)
        return seen


# ------------------------------------------------------------- providers ----
@dataclass
class Candidate:
    url: str
    source: str
    author: str = ""
    page_url: str = ""
    license: str = ""
    tags: str = ""


class Provider(Protocol):
    name: str

    def search(self, query: str) -> list[Candidate]: ...


def _get(url: str, **kw):
    import requests  # lazy: tests run without network

    resp = requests.get(url, timeout=20, **kw)
    resp.raise_for_status()
    return resp


class PixabayProvider:
    name = "pixabay"

    def __init__(self, key: Optional[str] = None):
        self.key = key or os.environ.get("PIXABAY_API_KEY")

    def search(self, query: str) -> list[Candidate]:
        if not self.key:
            return []
        data = _get(
            "https://pixabay.com/api/",
            params={"key": self.key, "q": query, "image_type": "photo", "safesearch": "true",
                    "per_page": 20, "min_width": 1000, "order": "popular"},
        ).json()
        return [Candidate(h["largeImageURL"], self.name, h.get("user", ""), h.get("pageURL", ""),
                          "Pixabay Content License", h.get("tags", "")) for h in data.get("hits", [])]


class PexelsProvider:
    name = "pexels"

    def __init__(self, key: Optional[str] = None):
        self.key = key or os.environ.get("PEXELS_API_KEY")

    def search(self, query: str) -> list[Candidate]:
        if not self.key:
            return []
        data = _get("https://api.pexels.com/v1/search", headers={"Authorization": self.key},
                    params={"query": query, "per_page": 20}).json()
        return [Candidate(p["src"].get("large2x") or p["src"]["original"], self.name,
                          p.get("photographer", ""), p.get("url", ""), "Pexels License",
                          p.get("alt", "")) for p in data.get("photos", [])]


class WikimediaProvider:
    """Keyless fallback. Only public-domain / CC0 files (CC BY only if ALLOW_CC_BY=1)."""
    name = "wikimedia"

    def search(self, query: str) -> list[Candidate]:
        data = _get("https://commons.wikimedia.org/w/api.php", params={
            "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
            "gsrsearch": f"{query} filetype:bitmap", "gsrlimit": 15, "prop": "imageinfo",
            "iiprop": "url|extmetadata|size", "iiurlwidth": 1600}).json()
        out = []
        for page in (data.get("query", {}).get("pages", {})).values():
            info = (page.get("imageinfo") or [{}])[0]
            meta = info.get("extmetadata", {})
            lic = meta.get("LicenseShortName", {}).get("value", "")
            if not license_allowed(lic):
                continue
            desc = re.sub(r"<[^>]+>", "", meta.get("ImageDescription", {}).get("value", ""))
            author = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", ""))
            out.append(Candidate(info.get("thumburl") or info.get("url", ""), self.name, author,
                                 info.get("descriptionurl", ""), lic, desc))
        return out


def default_providers() -> list[Provider]:
    return [PixabayProvider(), PexelsProvider(), WikimediaProvider()]


# --------------------------------------------------------------- quality ----
MIN_SHORT_SIDE = 800
MIN_SHARPNESS = 40.0


def sharpness(img: Image.Image) -> float:
    """Variance of a Laplacian over the centre of the photo (higher = sharper)."""
    g = ImageOps.grayscale(img)
    w, h = g.size
    g = g.crop((int(w * .15), int(h * .15), int(w * .85), int(h * .85)))
    g.thumbnail((640, 640))
    a = np.asarray(g, dtype=np.float32)
    lap = 4 * a[1:-1, 1:-1] - a[:-2, 1:-1] - a[2:, 1:-1] - a[1:-1, :-2] - a[1:-1, 2:]
    return float(lap.var())


def check_image(img: Image.Image) -> tuple[bool, str]:
    if min(img.size) < MIN_SHORT_SIDE:
        return False, f"too small {img.size}"
    s = sharpness(img)
    if s < MIN_SHARPNESS:
        return False, f"too blurry ({s:.0f})"
    return True, "ok"


# ----------------------------------------------------------------- fetch ----
@dataclass
class PhotoRecord:
    term: str
    path: str
    source: str
    author: str
    page_url: str
    license: str
    query: str
    retrieved: str = ""


def _download(url: str) -> bytes:
    resp = _get(url, stream=True)
    data = resp.raw.read(15 * 1024 * 1024 + 1, decode_content=True)
    if len(data) > 15 * 1024 * 1024:
        raise ValueError("image too large")
    return data


def get_photo(term: str, lex: Lexicon, providers: Optional[Iterable[Provider]] = None,
              cache_dir: Path = CACHE_DIR, refresh: bool = False,
              downloader=_download) -> Optional[PhotoRecord]:
    """Return a cached or freshly fetched real photo for ``term`` (None if nothing passes)."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    img_path, meta_path = cache_dir / f"{term}.jpg", cache_dir / f"{term}.json"
    if img_path.exists() and meta_path.exists() and not refresh:
        return PhotoRecord(**json.loads(meta_path.read_text()))

    query = lex.entries[term]["query"]
    if is_banned(query) or is_banned(term):
        raise ValueError(f"'{term}' is banned for this channel")

    for provider in (providers if providers is not None else default_providers()):
        try:
            candidates = provider.search(query)
        except Exception as exc:  # network/API problem: try the next provider
            print(f"[photos] {provider.name} failed for '{term}': {exc}")
            continue
        for cand in candidates[:10]:
            if is_unsafe(f"{cand.tags} {cand.page_url}") or has_rights_risk(cand.tags):
                continue
            try:
                img = Image.open(io.BytesIO(downloader(cand.url)))
                img = ImageOps.exif_transpose(img).convert("RGB")
            except Exception:
                continue
            ok, why = check_image(img)
            if not ok:
                continue
            img.thumbnail((2400, 2400))
            img.save(img_path, "JPEG", quality=92)
            rec = PhotoRecord(term, str(img_path), cand.source, cand.author, cand.page_url,
                              cand.license, query, date.today().isoformat())
            meta_path.write_text(json.dumps(asdict(rec), indent=2))
            return rec
    print(f"[photos] no suitable photo found for '{term}'")
    return None


def credits_text(records: Iterable[PhotoRecord]) -> str:
    """Photo credits. Put these in the VIDEO DESCRIPTION only, never on screen."""
    lines = ["Photo credits:"]
    for r in records:
        who = r.author or "unknown"
        lines.append(f"- {r.term}: {who} ({r.source}, {r.license}) {r.page_url}".rstrip())
    return "\n".join(lines)


# ------------------------------------------------------------------ card ----
_FONTS = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
          "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
          "/Library/Fonts/Arial Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"]


def _font(size: int) -> ImageFont.ImageFont:
    for p in _FONTS:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)


def make_card(photo_path: str | Path, label: str, out_path: str | Path,
              size: tuple[int, int] = (1080, 1920)) -> Path:
    """9:16 card: the WHOLE photo (never cropped, so it looks exactly as it is) in a white
    frame over a soft blurred copy of itself, with the word underneath for reading practice."""
    W, H = size
    photo = Image.open(photo_path).convert("RGB")
    bg = ImageOps.fit(photo, size, Image.LANCZOS).filter(ImageFilter.GaussianBlur(45))
    bg = Image.blend(bg, Image.new("RGB", size, (255, 255, 255)), 0.30)

    border, margin = 18, 60
    fitted = ImageOps.contain(photo, (W - 2 * margin - 2 * border, int(H * 0.56)))
    fw, fh = fitted.size[0] + 2 * border, fitted.size[1] + 2 * border
    draw = ImageDraw.Draw(bg)
    font = _font(150)
    box = draw.textbbox((0, 0), label, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    pad, gap = 50, 90
    # centre the photo + word block vertically so portrait and landscape photos both look balanced
    fx, fy = (W - fw) // 2, (H - (fh + gap + th + 2 * pad)) // 2
    draw.rounded_rectangle((fx, fy, fx + fw, fy + fh), radius=36, fill=(255, 255, 255))
    bg.paste(fitted, (fx + border, fy + border))
    by = fy + fh + gap
    bx0, bx1 = (W - tw) // 2 - pad, (W + tw) // 2 + pad
    draw.rounded_rectangle((bx0, by, bx1, by + th + 2 * pad), radius=60, fill=(255, 196, 61))
    draw.text(((W - tw) // 2 - box[0], by + pad - box[1]), label, font=font, fill=(60, 40, 20))

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    bg.save(out, "PNG")
    return out


def make_contact_sheet(records: list[PhotoRecord], out_path: str | Path, thumb: int = 260) -> Path:
    """One-image overview so a human can approve a batch of photos in seconds."""
    cols = 5
    rows = (len(records) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb, rows * (thumb + 40)), "white")
    d = ImageDraw.Draw(sheet)
    for i, r in enumerate(records):
        im = ImageOps.fit(Image.open(r.path).convert("RGB"), (thumb - 10, thumb - 10))
        x, y = (i % cols) * thumb, (i // cols) * (thumb + 40)
        sheet.paste(im, (x + 5, y + 5))
        d.text((x + 8, y + thumb + 5), r.term, fill="black", font=_font(22))
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    return Path(out_path)


# ------------------------------------------------------------------ cues ----
@dataclass
class Cue:
    term: str
    label: str
    start: float
    end: float
    image: str = ""


def plan_cues(words: list[dict], lex: Lexicon, hold: float = 2.5, min_hold: float = 1.2,
              repeat_after: float = 20.0) -> list[Cue]:
    """words = [{"word": "duck", "start": 3.2, "end": 3.5}, ...] (karaoke timestamps).

    A photo appears the moment its word is sung and stays ``hold`` seconds. The same photo is
    not repeated within ``repeat_after`` seconds. When words come quickly (a song listing
    "duck, frog, dog") each photo gets at least ``min_hold`` seconds.
    """
    cues: list[Cue] = []
    last_seen: dict[str, float] = {}
    for w in words:
        term = lex.term_for(w["word"])
        if not term:
            continue
        t = float(w["start"])
        if term in last_seen and t - last_seen[term] < repeat_after:
            continue
        last_seen[term] = t
        cues.append(Cue(term, term.capitalize(), t, t + hold))
    for a, b in zip(cues, cues[1:]):
        if b.start < a.start + min_hold:
            b.start = a.start + min_hold
            b.end = max(b.end, b.start + min_hold)
        a.end = min(a.end, b.start)
    return cues


def prepare_cues(cues: list[Cue], lex: Lexicon, providers=None, cache_dir: Path = CACHE_DIR,
                 card_dir: Path = CARD_DIR, size=(1080, 1920), downloader=_download):
    """Fetch photos + render cards for every cue. Cues with no photo are dropped (and reported)."""
    ready, records = [], {}
    for cue in cues:
        if cue.term not in records:
            records[cue.term] = get_photo(cue.term, lex, providers, cache_dir, downloader=downloader)
        rec = records[cue.term]
        if rec is None:
            print(f"[photos] WARNING: lesson mentions '{cue.term}' but no real photo was found")
            continue
        cue.image = str(make_card(rec.path, cue.label, Path(card_dir) / f"{cue.term}.png", size))
        ready.append(cue)
    return ready, [r for r in records.values() if r]


def active_cue(cues: list[Cue], t: float) -> Optional[Cue]:
    for c in cues:
        if c.start <= t < c.end:
            return c
    return None


@lru_cache(maxsize=16)
def _load_card(path: str, size: tuple[int, int]) -> Image.Image:
    return Image.open(path).convert("RGB").resize(size, Image.LANCZOS)


def apply_cue(frame: Image.Image, cue: Optional[Cue], t: float, fade: float = 0.25) -> Image.Image:
    """Cut away from the cartoon frame to the real-photo card (quick fade in/out).
    Use inside the frame loop: frame = apply_cue(render.draw_scene(sc, t), active_cue(cues, t), t)."""
    if cue is None:
        return frame
    a = max(0.0, min(1.0, (t - cue.start) / fade, (cue.end - t) / fade))
    card = _load_card(cue.image, frame.size)
    return Image.blend(frame.convert("RGB"), card, a) if a < 1 else card.copy()


# ------------------------------------------------------------------- CLI ----
def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Real-world photo helper")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan", help="list real-world terms found in a script")
    s.add_argument("text")
    f = sub.add_parser("fetch", help="download + cache photos and render cards")
    f.add_argument("terms", nargs="+")
    f.add_argument("--sheet", default="", help="write a contact sheet PNG for quick review")
    args = ap.parse_args(argv)

    lex = Lexicon.load()
    if args.cmd == "scan":
        print(", ".join(lex.find_terms(args.text)) or "(none)")
        return 0
    recs = []
    for t in args.terms:
        if t not in lex.entries:
            print(f"unknown term '{t}' (add it to config/real_world_terms.json)")
            continue
        rec = get_photo(t, lex)
        if rec:
            make_card(rec.path, t.capitalize(), CARD_DIR / f"{t}.png")
            recs.append(rec)
            print(f"ok  {t}: {rec.source} / {rec.author}")
    if recs and args.sheet:
        make_contact_sheet(recs, args.sheet)
    print(credits_text(recs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
