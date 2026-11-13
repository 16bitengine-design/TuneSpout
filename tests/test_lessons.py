"""Checks lessons are kid-safe, the math is right, and every scene draws.
Run: python -m pytest tests"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import metadata  # noqa: E402
import music  # noqa: E402
import render  # noqa: E402
from generators import GENERATORS, generate  # noqa: E402
from safety import BLOCKLIST, check_lesson  # noqa: E402


def _check_equation(eq):
    left, right = eq.split("=")
    a, op, b = left.split()
    a, b = int(a), int(b)
    result = {"+": a + b, "-": a - b, "×": a * b, "÷": a // b}[op]
    assert result == int(right), eq
    if op == "÷":
        assert a % b == 0, eq


def test_curated_lessons_pass_safety():
    for f in (ROOT / "lessons").rglob("*.json"):
        check_lesson(json.loads(f.read_text()))


def test_generated_lessons_are_safe_and_correct():
    for topic in GENERATORS:
        for seed in range(40):
            lesson = generate(topic, seed)
            check_lesson(lesson)
            for key in ("title", "description", "tags", "tune"):
                assert lesson.get(key), (topic, key)
            for sc in lesson["scenes"]:
                assert len(sc.get("kids", [])) <= 2
                items = sc.get("items")
                if items:
                    assert items["count"] <= 20
                    if items.get("split"):
                        assert sum(items["split"]) == items["count"]
                if "=" in sc.get("equation", ""):
                    _check_equation(sc["equation"])


def test_every_scene_renders():
    for topic in GENERATORS:
        lesson = json.loads(json.dumps(generate(topic, 7)))  # as read from a file
        for sc in lesson["scenes"]:
            for t in (0.0, 1.0):
                img = render.draw_scene(sc, t, size=(320, 180))
                assert img.size == (320, 180)


def test_automatic_metadata():
    for topic in GENERATORS:
        lesson = generate(topic, 3)
        yt, tt = metadata.youtube(lesson), metadata.tiktok(lesson)
        assert 0 < len(yt["title"]) <= 100
        assert yt["description"].count("#") <= 15  # YouTube ignores hashtags past 15
        assert len(tt["caption"]) <= 2200
        assert 3 <= tt["caption"].count("#") <= 5
        assert tt["is_aigc"] is True
        # generated text must avoid unsafe words (the fixed parent note is allowed
        # to say "no scary content", so it is skipped)
        text = " ".join([yt["title"], tt["caption"]] + [
            ln for ln in yt["description"].splitlines() if not ln.startswith("For parents")])
        assert not BLOCKLIST.intersection(re.findall(r"[a-zA-Z']+", text.lower()))


def test_every_object_draws_and_unknown_words_get_one():
    import random
    from PIL import Image, ImageDraw
    from characters import library
    from characters.items import draw_item
    img = Image.new("RGB", (200, 200)); d = ImageDraw.Draw(img)
    legacy = ["apple", "star", "ball", "flower"]
    rng = random.Random(1)
    words = ["".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randint(3, 9)))
             for _ in range(300)]
    for name in list(library.LIBRARY) + legacy + words:
        for ghost in (False, True):
            draw_item(d, name, 100, 100, 40, group=2, ghost=ghost, t=0.4, phase=1.0)
    # the same word always gives the same invented object
    assert library.invent_recipe("rocket") == library.invent_recipe("rocket")
    # across many words, invented objects are not all the same design
    assert len({str(library.invent_recipe(w)) for w in words}) > 100
    from generators.common import ITEMS
    for name in ITEMS:
        assert name in library.LIBRARY or name in legacy, f"{name} has no drawing recipe"


def test_invented_creatures_are_deterministic_and_safe():
    import random
    from PIL import Image, ImageDraw
    from characters import creatures
    img = Image.new("RGB", (300, 300)); d = ImageDraw.Draw(img)
    for seed in range(300):
        assert creatures.genome(seed) == creatures.genome(seed)
        name = creatures.make_name(random.Random(seed))
        assert name and not any(b in name.lower() for b in creatures.BANNED_PIECES), name
        creatures.draw_creature(d, 150, 280, 2.0, 0.3, 0.0, creatures.genome(seed))
    # the whole set of invented looks is varied, not one design repeated
    looks = {tuple(sorted((k, str(v)) for k, v in creatures.genome(s).items())) for s in range(50)}
    assert len(looks) > 40


def test_lessons_with_pals_keep_kids_as_stars():
    for topic in GENERATORS:
        for seed in range(40):
            lesson = generate(topic, seed)
            for sc in lesson["scenes"]:
                assert len(sc.get("pals", [])) <= 2
                if sc.get("pals"):
                    assert len(sc["kids"]) >= 1  # a pal never appears without a kid


def test_brand_images_and_thumbnails(tmp_path):
    import branding
    for topic in GENERATORS:
        for seed in (1, 2, 3):
            lesson = json.loads(json.dumps(generate(topic, seed)))
            img = branding.thumbnail(lesson)
            assert img.size == (1280, 720)
            path = tmp_path / f"{topic}{seed}.png"
            img.save(path, optimize=True)
            assert path.stat().st_size < 2_000_000, "YouTube thumbnails must be under 2 MB"
    assert branding.avatar(800).size == (800, 800)
    wm = branding.watermark(150)
    assert wm.size == (150, 150) and wm.mode == "RGBA" and wm.getpixel((0, 0))[3] == 0  # transparent corner
    assert branding.banner(1280, 720).size == (1280, 720)
    assert branding.tiktok_cover(540, 960).size == (540, 960)


def test_tunes_have_right_length():
    for name in music.TUNES:
        assert len(music.tune_track(name, 3.0)) == 3 * music.SR


def test_long_lessons_split_into_parts_of_at_most_three_minutes():
    import random

    import episodes
    assert episodes.split([10.0] * 18) == [(0, 18)]                  # exactly 180 s: one video
    assert episodes.split([10.0] * 19) == [(0, 10), (10, 19)]        # 190 s: two even parts
    assert episodes.split([10.0] * 60) == [(i * 15, i * 15 + 15) for i in range(4)]  # 600 s: 4 x 150 s
    rng = random.Random(5)
    for _ in range(200):                                             # any mix of scene lengths
        durs = [rng.uniform(2, 25) for _ in range(rng.randint(20, 90))]
        ranges = episodes.split(durs)
        assert ranges[0][0] == 0 and ranges[-1][1] == len(durs)
        assert all(a[1] == b[0] for a, b in zip(ranges, ranges[1:])), "no scene lost or repeated"
        assert all(sum(durs[a:b]) <= 180 for a, b in ranges), "a part ran over three minutes"
    assert episodes.episode_title("Add!", 2, 3) == "Add! (Part 2 of 3)"
    assert episodes.episode_title("Add!", 1, 1) == "Add!"


def test_later_episodes_are_scheduled_in_order_not_all_at_once():
    import buffer_post
    env = {"BUFFER_YOUTUBE_CHANNEL_ID": "c"}
    meta = {"title": "T", "description": "d"}
    first = buffer_post.build_input("youtube", meta, "u", env, episode=0)
    second = buffer_post.build_input("youtube", meta, "u", env, episode=1)
    assert first["mode"] == "shareNow" and "dueAt" not in first
    assert second["mode"] == "customScheduled" and second["dueAt"].endswith("Z")


def test_cast_is_the_same_every_video_and_extras_change():
    from characters.cast import CAST_ANIMALS, CAST_KIDS, check_cast
    from generators import GENERATORS, generate
    assert check_cast()
    cast_names = {k["name"] for k in CAST_KIDS}
    looks = {k["name"]: k for k in CAST_KIDS}
    extras_seen = set()
    for topic in GENERATORS:
        for seed in (1, 2, 3):
            lesson = generate(topic, seed)
            for sc in lesson["scenes"]:
                for kid in sc.get("kids", []):
                    assert kid["name"] in cast_names and kid == looks[kid["name"]], "a main kid changed looks"
            with_kids = [sc for sc in lesson["scenes"] if "kids" in sc]
            assert with_kids and all([p["cast"] for p in sc["pals"]] == list(CAST_ANIMALS) for sc in with_kids)
            extras_seen.add(str(with_kids[0]["extras"]))
    assert len(extras_seen) > 5, "extras should differ from video to video"


def test_each_topic_picks_its_own_length_inside_its_range():
    from generators import MAX_MINUTES, MIN_MINUTES, TOPIC_MINUTES, TOPICS, target_minutes
    assert set(TOPIC_MINUTES) == set(TOPICS)
    for topic, (low, high) in TOPIC_MINUTES.items():
        assert MIN_MINUTES <= low <= high <= MAX_MINUTES
        picks = {target_minutes(topic, seed) for seed in range(60)}
        assert all(low <= m <= high for m in picks)
    assert target_minutes("division", 5) == target_minutes("division", 5)  # repeatable


def test_long_lessons_are_safe_long_enough_and_fit_in_parts():
    import episodes
    from generators import estimate_seconds, generate_long
    from safety import check_lesson
    for topic in ("addition", "plurals", "sports"):
        lesson = generate_long(topic, 7, 8)
        check_lesson(lesson)
        secs = estimate_seconds(lesson["scenes"])
        assert secs >= 8 * 60
        assert lesson["scenes"][-1]["line"] != lesson["scenes"][-2]["line"]
        durs = [len(sc["line"].split()) / 2.2 + 0.6 for sc in lesson["scenes"]]
        parts = episodes.split(durs)
        assert len(parts) >= 3 and all(sum(durs[a:b]) <= 180 for a, b in parts)


def test_animal_lessons_teach_the_right_facts_and_every_animal_is_drawn():
    from PIL import Image, ImageDraw

    from characters.animals import ANIMALS
    from characters.library import draw_named
    facts = {"dog": ("woof", "puppy"), "cat": ("meow", "kitten"), "cow": ("moo", "calf"),
             "sheep": ("baa", "lamb"), "pig": ("oink", "piglet"), "frog": ("ribbit", "tadpole")}
    for name, (sound, baby) in facts.items():
        assert ANIMALS[name] == {"sound": sound, "baby": baby}
    for animal, info in ANIMALS.items():
        for thing in (animal, info["baby"]):
            img = Image.new("RGB", (200, 200), (255, 255, 255))
            draw_named(ImageDraw.Draw(img), thing, 100, 100, 80)
            painted = sum(1 for px in img.getdata() if px != (255, 255, 255))
            assert painted > 300, f"{thing} is barely drawn"
    for seed in range(30):
        sounds = generate("animalsounds", seed)
        for sc in sounds["scenes"]:
            if "items" in sc and sc["items"]["type"] in ANIMALS:
                kind = sc["items"]["type"]
                if "says" in sc["line"]:
                    assert ANIMALS[kind]["sound"] in sc["line"]
        babies = generate("babyanimals", seed)
        for sc in babies["scenes"]:
            if "is called a" in sc["line"]:
                adult, baby = sc["items"]["types"]
                assert sc["line"] == f"A baby {adult} is called a {ANIMALS[adult]['baby']}!" and baby == ANIMALS[adult]["baby"]


def test_phonics_and_spelling_match_picture_letter_and_word():
    from generators.reading_lessons import LETTERS, SPELL_WORDS
    for _, _, thing in LETTERS:
        assert thing in LIBRARY_THINGS()
    for word in SPELL_WORDS:
        assert word in LIBRARY_THINGS()
    for seed in range(20):
        for sc in generate("phonics", seed)["scenes"]:
            if "is for" in sc["line"]:
                letter, _, thing = sc["line"].partition(" is for ")
                assert thing.rstrip("!") == sc["items"]["type"] and sc["items"]["type"][0].upper() == letter
        for sc in generate("spelling", seed)["scenes"]:
            if "We spelled" in sc["line"]:  # the last scene shows every letter of the word
                assert sc["equation"].replace(" ", "").lower() == sc["items"]["type"]
                assert sc["equation"].count(" ") == len(sc["items"]["type"]) - 1


def LIBRARY_THINGS():
    import characters.animals  # noqa: F401
    from characters.items import COLORS as LEGACY
    from characters.library import LIBRARY
    return set(LIBRARY) | set(LEGACY)
