"""The daily record: no double posts, backup run catches up, tokens stay safe."""
import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import buffer_post  # noqa: E402
import state  # noqa: E402


@pytest.fixture
def day(tmp_path, monkeypatch):
    monkeypatch.setenv("STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("DAY", "2026-11-12")
    monkeypatch.setenv("LESSON_FILE", str(tmp_path / "lesson.json"))
    for k in ("BUFFER_API_KEY", "BUFFER_YOUTUBE_CHANNEL_ID", "BUFFER_TIKTOK_CHANNEL_ID"):
        monkeypatch.delenv(k, raising=False)
    (tmp_path / "lesson.json").write_text(json.dumps({"title": "Add!", "topic": "addition"}))
    return tmp_path


def _connect(monkeypatch, platform):
    monkeypatch.setenv("BUFFER_API_KEY", "k")
    monkeypatch.setenv(f"BUFFER_{platform.upper()}_CHANNEL_ID", "chan-" + platform)


def _result(tmp_path, name):
    p = tmp_path / name
    p.write_text(json.dumps({"id": "abc"}))
    return str(p)


def test_nothing_connected_is_a_practice_run(day):
    s = state.status()
    assert s["pending"] == "true" and s["youtube"] == "off" and s["tiktok"] == "off"
    assert state.missing() == []  # nothing connected, nothing missing


def test_first_run_posts_everything_then_backup_run_does_nothing(day, monkeypatch):
    _connect(monkeypatch, "youtube")
    _connect(monkeypatch, "tiktok")
    assert state.status()["pending"] == "true"
    assert state.missing() == ["youtube", "tiktok"]
    state.record("youtube", _result(day, "yt.json"))
    state.record("tiktok", _result(day, "tt.json"))
    assert state.missing() == []
    s = state.status()  # the backup run
    assert s["pending"] == "false" and s["youtube"] == "done" and s["tiktok"] == "done"


def test_partial_failure_only_retries_the_missing_platform(day, monkeypatch):
    _connect(monkeypatch, "youtube")
    _connect(monkeypatch, "tiktok")
    state.status()
    state.record("youtube", _result(day, "yt.json"))  # TikTok failed
    assert state.main(["verify"]) == 1
    s = state.status()
    assert s["youtube"] == "done" and s["tiktok"] == "todo" and s["pending"] == "true"


def test_force_posts_again(day, monkeypatch):
    _connect(monkeypatch, "youtube")
    state.record("youtube", _result(day, "yt.json"))
    assert state.status()["youtube"] == "done"
    assert state.status(force=True)["youtube"] == "todo"


def test_a_failed_upload_records_nothing(day, monkeypatch):
    _connect(monkeypatch, "youtube")
    state.record("youtube", str(day / "does_not_exist.json"))
    assert state.missing() == ["youtube"]


def test_record_keeps_the_lesson_title_and_old_days_are_pruned(day, monkeypatch):
    _connect(monkeypatch, "youtube")
    state.save({"2020-01-01": {"youtube": {}}, "2026-11-10": {"youtube": {}}})
    state.record("youtube", _result(day, "yt.json"))
    data = state.load()
    assert "2020-01-01" not in data and "2026-11-10" in data
    assert data["2026-11-12"]["title"] == "Add!" and data["2026-11-12"]["topic"] == "addition"


def test_status_leaves_a_heartbeat_so_github_keeps_the_schedule_on(day, monkeypatch):
    _connect(monkeypatch, "youtube")
    state.status()
    assert state.load()["_last_run"] == "2026-11-12"


META = {"title": "Count to 10!", "description": "Sing along", "caption": "Count! #kids", "is_aigc": True}


def test_youtube_post_is_made_for_kids_private_and_labelled_ai(monkeypatch):
    env = {"BUFFER_YOUTUBE_CHANNEL_ID": "c1"}
    body = buffer_post.build_input("youtube", META, "https://x/v.mp4", env)
    yt = body["metadata"]["youtube"]
    assert yt["madeForKids"] is True and yt["privacy"] == "private" and yt["isAiGenerated"] is True
    assert yt["categoryId"] == "27" and body["channelId"] == "c1"
    assert body["assets"] == [{"video": {"url": "https://x/v.mp4"}}]
    assert buffer_post.build_input("youtube", META, "u", {**env, "PRIVACY": "public"})["metadata"]["youtube"]["privacy"] == "public"


def test_tiktok_waits_as_a_draft_until_you_switch_it_on():
    env = {"BUFFER_TIKTOK_CHANNEL_ID": "c2"}
    body = buffer_post.build_input("tiktok", META, "u", env)
    assert body["saveToDraft"] is True and body["metadata"]["tiktok"]["isAiGenerated"] is True
    assert "saveToDraft" not in buffer_post.build_input("tiktok", META, "u", {**env, "TIKTOK_MODE": "post"})


def test_buffer_errors_are_not_mistaken_for_success(monkeypatch):
    monkeypatch.setenv("BUFFER_API_KEY", "k")

    class Reply:
        def __init__(self, data):
            self.data = data

        def raise_for_status(self):
            pass

        def json(self):
            return self.data

    monkeypatch.setattr(buffer_post.requests, "post",
                        lambda *a, **k: Reply({"data": {"createPost": {"message": "No video"}}}))
    with pytest.raises(SystemExit):
        buffer_post.create_post({})
    monkeypatch.setattr(buffer_post.requests, "post",
                        lambda *a, **k: Reply({"data": {"createPost": {"post": {"id": "p9"}}}}))
    assert buffer_post.create_post({}) == "p9"


def test_workflow_has_backup_run_and_safety_settings():
    wf = yaml.safe_load((ROOT / ".github/workflows/daily.yml").read_text())
    crons = [c["cron"] for c in wf[True]["schedule"]]  # PyYAML reads the key `on` as True
    assert len(crons) == 2
    assert all(not c.startswith("0 ") for c in crons), "avoid the busy top of the hour"
    assert wf["concurrency"]["cancel-in-progress"] is False
    assert wf["permissions"] == {"contents": "write", "issues": "write"}


def test_merge_keeps_what_both_runs_posted(day, monkeypatch):
    other = day / "other.json"
    other.write_text(json.dumps({"_last_run": "2026-11-12", "2026-11-12": {"tiktok": {"publish_id": "T1"}}}))
    state.save({"_last_run": "2026-11-11", "2026-11-12": {"youtube": {"id": "Y1"}, "title": "Add!"}})
    state.merge(str(other))
    merged = state.load()
    assert merged["2026-11-12"]["youtube"] == {"id": "Y1"}
    assert merged["2026-11-12"]["tiktok"] == {"publish_id": "T1"}
    assert merged["2026-11-12"]["title"] == "Add!"
    assert merged["_last_run"] == "2026-11-12"


def test_two_runs_finishing_together_both_get_saved(tmp_path, monkeypatch):
    """Real git, real push_state.sh: the main run posts YouTube, the backup run posts
    TikTok, and they push at the same moment. Neither record may be lost."""
    import shutil
    import subprocess
    if not shutil.which("git"):
        pytest.skip("git not available")
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]

    def run(cmd, cwd, **kw):
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, **kw)
        assert r.returncode == 0, f"{cmd}\n{r.stdout}\n{r.stderr}"
        return r

    remote = tmp_path / "remote.git"
    run(["git", "init", "-q", "--bare", str(remote)], tmp_path)
    seed = tmp_path / "seed"
    run(["git", "clone", "-q", str(remote), str(seed)], tmp_path)
    run(git + ["checkout", "-q", "-b", "state"], seed)
    (seed / "posted.json").write_text("{}\n")
    run(["git", "add", "-A"], seed)
    run(git + ["commit", "-q", "-m", "init"], seed)
    run(["git", "push", "-q", "origin", "state"], seed)

    env = {**__import__("os").environ, "DAY": "2026-11-12", "BUFFER_API_KEY": "k", "BUFFER_YOUTUBE_CHANNEL_ID": "a",
           "BUFFER_TIKTOK_CHANNEL_ID": "b", "LESSON_FILE": str(tmp_path / "none.json")}
    runs = {}
    for name, platform in (("main", "youtube"), ("backup", "tiktok")):
        work = tmp_path / name
        (work / "out").mkdir(parents=True)
        (work / "src").symlink_to(ROOT / "src")  # the script runs python3 src/state.py
        run(["git", "clone", "-q", "-b", "state", str(remote), str(work / "state")], tmp_path)
        (work / "out" / f"result_{platform}.json").write_text(json.dumps({"id": platform}))
        run([sys.executable, str(ROOT / "src/state.py"), "record", platform,
             f"out/result_{platform}.json"], work, env=env)
        runs[name] = work
    for name in ("main", "backup"):  # both have local changes; the second push collides
        run(["bash", str(ROOT / "tools/push_state.sh")], runs[name], env=env)

    final = json.loads(run(["git", "--git-dir", str(remote), "show", "state:posted.json"], tmp_path).stdout)
    assert set(final["2026-11-12"]) >= {"youtube", "tiktok"}


def test_channels_are_found_from_the_api_key_alone(monkeypatch):
    import buffer_channels
    answers = {"organizations": {"account": {"organizations": [{"id": "o1", "name": "me"}]}},
               "channels": {"channels": [{"id": "c-yt", "name": "Kids", "service": "youtube"},
                                         {"id": "c-tt", "name": "Kids", "service": "tiktok"},
                                         {"id": "c-x", "name": "Other", "service": "instagram"}]}}
    ask = lambda q: answers["organizations" if "organizations" in q else "channels"]  # noqa: E731
    assert buffer_channels.channel_ids({"BUFFER_API_KEY": "k"}, ask) == {"youtube": "c-yt", "tiktok": "c-tt"}
    pinned = {"BUFFER_API_KEY": "k", "BUFFER_YOUTUBE_CHANNEL_ID": "mine"}
    assert buffer_channels.channel_ids(pinned, ask) == {"youtube": "mine", "tiktok": "c-tt"}
    assert buffer_channels.channel_ids({}, ask) == {}  # no key, nothing connected


def test_a_failed_channel_lookup_means_nothing_is_posted_not_a_crash(monkeypatch):
    import buffer_channels

    def broken(query):
        raise RuntimeError("down")
    assert buffer_channels.channel_ids({"BUFFER_API_KEY": "k"}, broken) == {}
