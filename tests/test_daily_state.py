"""The daily record: no double posts, backup run catches up, tokens stay safe."""
import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import secrets_store  # noqa: E402
import state  # noqa: E402


@pytest.fixture
def day(tmp_path, monkeypatch):
    monkeypatch.setenv("STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("DAY", "2026-11-12")
    monkeypatch.setenv("LESSON_FILE", str(tmp_path / "lesson.json"))
    monkeypatch.delenv("YT_REFRESH_TOKEN", raising=False)
    monkeypatch.delenv("TIKTOK_REFRESH_TOKEN", raising=False)
    (tmp_path / "lesson.json").write_text(json.dumps({"title": "Add!", "topic": "addition"}))
    return tmp_path


def _result(tmp_path, name):
    p = tmp_path / name
    p.write_text(json.dumps({"id": "abc"}))
    return str(p)


def test_nothing_connected_is_a_practice_run(day):
    s = state.status()
    assert s["pending"] == "true" and s["youtube"] == "off" and s["tiktok"] == "off"
    assert state.missing() == []  # nothing connected, nothing missing


def test_first_run_posts_everything_then_backup_run_does_nothing(day, monkeypatch):
    monkeypatch.setenv("YT_REFRESH_TOKEN", "x")
    monkeypatch.setenv("TIKTOK_REFRESH_TOKEN", "y")
    assert state.status()["pending"] == "true"
    assert state.missing() == ["youtube", "tiktok"]
    state.record("youtube", _result(day, "yt.json"))
    state.record("tiktok", _result(day, "tt.json"))
    assert state.missing() == []
    s = state.status()  # the backup run
    assert s["pending"] == "false" and s["youtube"] == "done" and s["tiktok"] == "done"


def test_partial_failure_only_retries_the_missing_platform(day, monkeypatch):
    monkeypatch.setenv("YT_REFRESH_TOKEN", "x")
    monkeypatch.setenv("TIKTOK_REFRESH_TOKEN", "y")
    state.status()
    state.record("youtube", _result(day, "yt.json"))  # TikTok failed
    assert state.main(["verify"]) == 1
    s = state.status()
    assert s["youtube"] == "done" and s["tiktok"] == "todo" and s["pending"] == "true"


def test_force_posts_again(day, monkeypatch):
    monkeypatch.setenv("YT_REFRESH_TOKEN", "x")
    state.record("youtube", _result(day, "yt.json"))
    assert state.status()["youtube"] == "done"
    assert state.status(force=True)["youtube"] == "todo"


def test_a_failed_upload_records_nothing(day, monkeypatch):
    monkeypatch.setenv("YT_REFRESH_TOKEN", "x")
    state.record("youtube", str(day / "does_not_exist.json"))
    assert state.missing() == ["youtube"]


def test_record_keeps_the_lesson_title_and_old_days_are_pruned(day, monkeypatch):
    monkeypatch.setenv("YT_REFRESH_TOKEN", "x")
    state.save({"2020-01-01": {"youtube": {}}, "2026-11-10": {"youtube": {}}})
    state.record("youtube", _result(day, "yt.json"))
    data = state.load()
    assert "2020-01-01" not in data and "2026-11-10" in data
    assert data["2026-11-12"]["title"] == "Add!" and data["2026-11-12"]["topic"] == "addition"


def test_status_leaves_a_heartbeat_so_github_keeps_the_schedule_on(day, monkeypatch):
    monkeypatch.setenv("YT_REFRESH_TOKEN", "x")
    state.status()
    assert state.load()["_last_run"] == "2026-11-12"


def test_rotated_tiktok_token_is_encrypted_and_a_new_secret_wins(tmp_path):
    f = tmp_path / "tiktok_token.enc"
    secrets_store.save_token(f, "long random key", "rotated-token-123", "original-secret")
    assert b"rotated-token-123" not in f.read_bytes()  # not readable in a public repo
    assert secrets_store.load_token(f, "long random key", "original-secret") == "rotated-token-123"
    assert secrets_store.load_token(f, "wrong key", "original-secret") is None
    # you paste a fresh token into the secret later: the old saved one must be ignored
    assert secrets_store.load_token(f, "long random key", "brand-new-secret") is None
    assert secrets_store.load_token(tmp_path / "missing.enc", "k", "s") is None


def test_tiktok_token_refresh_saves_rotation(tmp_path, monkeypatch):
    import upload_tiktok
    monkeypatch.setenv("STATE_DIR", str(tmp_path))
    monkeypatch.setenv("STATE_KEY", "long random key")
    monkeypatch.setenv("TIKTOK_REFRESH_TOKEN", "secret-v1")
    monkeypatch.setenv("TIKTOK_CLIENT_KEY", "ck")
    monkeypatch.setenv("TIKTOK_CLIENT_SECRET", "cs")
    sent = []

    class Reply:
        def __init__(self, rt):
            self.rt = rt

        def raise_for_status(self):
            pass

        def json(self):
            return {"access_token": "at", "refresh_token": self.rt}

    replies = iter(["rotated-v2", "rotated-v3"])
    monkeypatch.setattr(upload_tiktok.requests, "post",
                        lambda url, data, timeout: sent.append(data["refresh_token"]) or Reply(next(replies)))
    assert upload_tiktok.get_access_token() == "at"   # day 1 uses the secret
    assert upload_tiktok.get_access_token() == "at"   # day 2 must use the rotated token
    assert sent == ["secret-v1", "rotated-v2"]


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

    env = {**__import__("os").environ, "DAY": "2026-11-12", "YT_REFRESH_TOKEN": "x",
           "TIKTOK_REFRESH_TOKEN": "y", "LESSON_FILE": str(tmp_path / "none.json")}
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
