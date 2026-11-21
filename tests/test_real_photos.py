"""Offline tests: no network, no API keys. Run with: python -m pytest -q"""
import io
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import real_photos as rp  # noqa: E402


@pytest.fixture(autouse=True)
def no_cloudinary_env(monkeypatch):
    for k in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET", "ALLOW_CC_BY"):
        monkeypatch.delenv(k, raising=False)


@pytest.fixture(scope="module")
def lex():
    return rp.Lexicon.load()


def sharp_jpeg(size=(1600, 1200)) -> bytes:
    rng = np.random.default_rng(0)
    arr = rng.integers(0, 255, (size[1], size[0], 3), dtype=np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, "JPEG")
    return buf.getvalue()


def blurry_jpeg(size=(1600, 1200)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (120, 160, 90)).save(buf, "JPEG")
    return buf.getvalue()


class FakeProvider:
    name = "fake"

    def __init__(self, cands):
        self.cands = cands

    def search(self, query):
        return self.cands


def test_finds_plurals_and_babies(lex):
    text = "Five ducks and three ducklings met a frog and two mice near the leaves."
    assert lex.find_terms(text) == ["duck", "duckling", "frog", "mouse", "leaf"]


def test_ambiguous_words_need_a_tag(lex):
    assert lex.find_terms("The sky is orange.") == []
    assert lex.find_terms("I eat an [[orange]] today") == ["orange"]
    assert rp.strip_tags("an [[orange]]") == "an orange"


def test_banned_words_never_in_lexicon_or_queries(lex):
    assert "pig" not in lex.entries
    with pytest.raises(ValueError):
        rp.get_photo("duck", rp.Lexicon({"duck": {"query": "pig farm"}}, {"duck": "duck"}),
                     providers=[], cache_dir=Path("/tmp/none"))


def test_quality_gate():
    ok, _ = rp.check_image(Image.open(io.BytesIO(sharp_jpeg())))
    assert ok
    bad, why = rp.check_image(Image.open(io.BytesIO(blurry_jpeg())))
    assert not bad and "blurry" in why
    small, why = rp.check_image(Image.new("RGB", (300, 300)))
    assert not small and "small" in why


def test_get_photo_skips_unsafe_and_blurry_then_caches(lex, tmp_path):
    cands = [
        rp.Candidate("u-unsafe", "fake", tags="duck hunting"),
        rp.Candidate("u-blurry", "fake", tags="duck"),
        rp.Candidate("u-good", "fake", author="A. Photographer", tags="duck pond"),
    ]
    data = {"u-unsafe": sharp_jpeg(), "u-blurry": blurry_jpeg(), "u-good": sharp_jpeg()}
    calls = []

    def dl(url):
        calls.append(url)
        return data[url]

    rec = rp.get_photo("duck", lex, [FakeProvider(cands)], tmp_path, downloader=dl)
    assert rec and rec.author == "A. Photographer"
    assert "u-unsafe" not in calls          # filtered by tags before download
    assert Path(rec.path).exists()
    # second call is served from the cache: no provider, no download
    again = rp.get_photo("duck", lex, [], tmp_path, downloader=lambda u: 1 / 0)
    assert again.path == rec.path


def test_card_is_vertical_and_keeps_whole_photo(tmp_path):
    p = tmp_path / "wide.jpg"
    Image.fromarray(np.random.default_rng(1).integers(0, 255, (600, 1800, 3), dtype=np.uint8)).save(p)
    out = rp.make_card(p, "Duck", tmp_path / "card.png")
    assert Image.open(out).size == (1080, 1920)


def test_cue_planning(lex):
    words = [{"word": "duck", "start": 1.0}, {"word": "frog", "start": 1.3},
             {"word": "dog", "start": 1.5}, {"word": "duck", "start": 5.0},
             {"word": "ducks", "start": 40.0}, {"word": "the", "start": 41.0}]
    cues = rp.plan_cues(words, lex, hold=2.5, min_hold=1.2, repeat_after=20)
    assert [c.term for c in cues] == ["duck", "frog", "dog", "duck"]   # 2nd duck within 20s skipped
    assert all(c.end > c.start for c in cues)
    assert all(a.end <= b.start + 1e-9 for a, b in zip(cues, cues[1:]))
    assert cues[1].start - cues[0].start >= 1.2


def test_prepare_cues_drops_missing_photos(lex, tmp_path):
    cues = [rp.Cue("duck", "Duck", 0, 2), rp.Cue("frog", "Frog", 2, 4)]
    prov = FakeProvider([rp.Candidate("u", "fake", tags="x")])
    # make 'frog' fail by returning nothing for it
    class P:
        name = "p"
        def search(self, q):
            return prov.cands if "duck" in q else []
    ready, recs = rp.prepare_cues(cues, lex, [P()], tmp_path / "c", tmp_path / "cards",
                                  downloader=lambda u: sharp_jpeg())
    assert [c.term for c in ready] == ["duck"] and len(recs) == 1
    assert Path(ready[0].image).exists()


def test_license_policy(monkeypatch):
    monkeypatch.delenv("ALLOW_CC_BY", raising=False)
    assert rp.license_allowed("CC0 1.0") and rp.license_allowed("Public domain")
    assert not rp.license_allowed("CC BY 4.0")                     # off by default
    assert rp.license_allowed("CC BY 4.0", allow_cc_by=True)
    for bad in ("CC BY-SA 4.0", "CC BY-NC 2.0", "CC BY-ND 2.0", "All rights reserved", ""):
        assert not rp.license_allowed(bad, allow_cc_by=True)


def test_rights_risk_tags_are_skipped(lex, tmp_path):
    cands = [rp.Candidate("u1", "fake", tags="dog girl park"),
             rp.Candidate("u2", "fake", tags="dog logo mascot"),
             rp.Candidate("u3", "fake", tags="dog grass")]
    got = []
    rec = rp.get_photo("dog", lex, [FakeProvider(cands)], tmp_path,
                       downloader=lambda u: got.append(u) or sharp_jpeg())
    assert got == ["u3"] and rec.retrieved


def test_credits_text_is_description_only_text(lex):
    r = rp.PhotoRecord("duck", "x.jpg", "pixabay", "A. Person", "https://p/1", "Pixabay Content License", "duck")
    out = rp.credits_text([r])
    assert out.startswith("Photo credits:") and "A. Person" in out


def test_pig_prefix_is_banned(lex):
    assert rp.is_banned("a piglet") and rp.is_banned("pigs") and not rp.is_banned("duck")


def test_apply_cue_shows_panel_in_upper_half_only(tmp_path):
    size = (360, 640)
    panel = rp.make_panel(_photo(tmp_path), "Duck", tmp_path / "c.png", size)
    cue = rp.Cue("duck", "Duck", 1.0, 3.0, str(panel))
    red = (255, 0, 0)
    frame = Image.new("RGB", size, red)
    assert rp.apply_cue(frame, None, 0.5) is frame
    x, y, pw, ph = rp.panel_box(size)
    assert y + ph < size[1] * 0.5                                    # panel stays in the upper half
    shown = rp.apply_cue(frame, cue, 2.0)
    assert shown.getpixel((size[0] // 2, y + ph // 2)) != red        # photo area is covered
    assert shown.getpixel((size[0] // 2, int(size[1] * 0.75))) == red  # lower half untouched
    assert shown.getpixel((2, 2)) == red                             # outside the panel untouched
    fading = rp.apply_cue(frame, cue, 1.1).getpixel((size[0] // 2, y + 8))
    assert fading not in (red, shown.getpixel((size[0] // 2, y + 8)))   # fade = a blend
    assert rp.active_cue([cue], 0.5) is None and rp.active_cue([cue], 1.5) is cue


def _photo(tmp_path):
    p = tmp_path / "p.jpg"
    Image.fromarray(np.random.default_rng(2).integers(0, 255, (400, 600, 3), dtype=np.uint8)).save(p)
    return p


class FakeResp:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


def test_openverse_keeps_only_cc0_and_pdm(monkeypatch):
    payload = {"results": [
        {"url": "u1", "license": "cc0", "creator": "A", "foreign_landing_url": "p1",
         "tags": [{"name": "duck"}], "title": "Pond"},
        {"url": "u2", "license": "pdm", "creator": "B", "tags": [], "title": "x"},
        {"url": "u3", "license": "by", "creator": "C", "tags": [], "title": "x"},
        {"url": "u4", "license": "by-sa", "creator": "D", "tags": [], "title": "x"}]}
    monkeypatch.setattr(rp, "_get", lambda *a, **k: FakeResp(payload))
    got = rp.OpenverseProvider().search("duck")
    assert [c.url for c in got] == ["u1", "u2"]
    assert got[0].license == "CC0 1.0" and "duck" in got[0].tags


def test_default_providers_work_without_any_keys(monkeypatch):
    for k in ("PIXABAY_API_KEY", "PEXELS_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    names = [p.name for p in rp.default_providers()]
    assert names[:2] == ["openverse", "wikimedia"]
    assert rp.PixabayProvider().search("duck") == [] and rp.PexelsProvider().search("duck") == []


def test_cloudinary_signature_matches_buffer_post_method():
    import hashlib
    params = {"public_id": "a/b", "timestamp": "1", "overwrite": "true"}
    expect = hashlib.sha1(b"overwrite=true&public_id=a/b&timestamp=1SECRET").hexdigest()
    assert rp.cloudinary_signature(params, "SECRET") == expect


class FakeStore:
    def __init__(self, have=None):
        self.have, self.saved = have, []

    def load(self, term, cache_dir):
        return self.have

    def save(self, rec):
        self.saved.append(rec.term)


def test_library_hit_skips_downloads_and_new_photo_is_saved(lex, tmp_path):
    img = tmp_path / "duck.jpg"
    img.write_bytes(sharp_jpeg())
    hit = rp.PhotoRecord("duck", str(img), "openverse", "A", "p", "CC0 1.0", "q")
    assert rp.get_photo("duck", lex, [], tmp_path / "c1", store=FakeStore(hit),
                        downloader=lambda u: 1 / 0) is hit
    store = FakeStore()
    rec = rp.get_photo("frog", lex, [FakeProvider([rp.Candidate("u", "fake", tags="frog")])],
                       tmp_path / "c2", store=store, downloader=lambda u: sharp_jpeg())
    assert rec and store.saved == ["frog"]


def test_store_load_reads_public_links(tmp_path, monkeypatch):
    meta = {"term": "duck", "path": "/old/runner/path.jpg", "source": "openverse", "author": "A",
            "page_url": "p", "license": "CC0 1.0", "query": "q", "retrieved": "2026-11-21", "extra": 1}

    class R:
        def __init__(self, c, j=None):
            self.content, self._j = c, j

        def json(self):
            return self._j

    def fake_get(url, **kw):
        if url.endswith("duck.json"):
            return R(b"", meta)
        if url.endswith("duck.jpg"):
            return R(sharp_jpeg())
        raise RuntimeError("404")

    monkeypatch.setattr(rp, "_get", fake_get)
    store = rp.CloudinaryStore("mycloud")
    rec = store.load("duck", tmp_path)
    assert rec and Path(rec.path).exists() and rec.path.startswith(str(tmp_path))
    assert store.load("zebra", tmp_path) is None


def test_word_times_and_scene_cues(lex):
    w = rp.estimate_word_times("One duck swims", 10.0, 3.0)
    assert w[0]["start"] == 10.0 and abs(w[-1]["end"] - 13.0) < 1e-6
    scenes = [{"line": "One little duck swims.", "_tagged": "One little duck swims."},
              {"line": "An orange for the frog.", "_tagged": "An [[orange]] for the frog."}]
    cues = rp.cues_for_scenes(scenes, [3.0, 3.0], lex)
    assert [c.term for c in cues] == ["duck", "orange", "frog"]
    assert cues[0].start < 3.0 <= cues[1].start            # 2nd scene starts after the first
    assert cues[1].start < cues[2].start


def test_credits_go_into_description_only(tmp_path):
    import json
    meta = tmp_path / "meta.json"
    meta.write_text(json.dumps({"title": "T", "description": "Hello"}))
    r = rp.PhotoRecord("duck", "x.jpg", "openverse", "A. Person", "https://p/1", "CC0 1.0", "duck")
    rp.add_credits_to_meta(meta, [r])
    data = json.loads(meta.read_text())
    assert data["description"].startswith("Hello") and "Photo credits:" in data["description"]
    assert data["title"] == "T"
    rp.add_credits_to_meta(meta, [])                         # nothing to add: unchanged
    assert json.loads(meta.read_text()) == data
