"""A sign-off pushes the milestone (ADR 42), against real bare repos."""

import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from runner import push
from tests.runner.conftest import git

FAKE_KEY = "sk-ant-" + "abcdefghij0123456789"


@pytest.fixture
def remote(tmp_path: Path) -> Path:
    bare = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], check=True)
    return bare


@pytest.fixture
def work(tmp_path: Path, remote: Path) -> Path:
    repo = tmp_path / "work"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "Test")
    git(repo, "remote", "add", "origin", str(remote))
    _commit(repo, "first.txt", "one\n")
    return repo


def _commit(repo: Path, name: str, text: str) -> str:
    (repo / name).write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", name)
    return git(repo, "rev-parse", "HEAD").strip()


def _on_remote(bare: Path, ref: str) -> str | None:
    found = subprocess.run(
        ["git", "rev-parse", "--verify", "-q", ref], cwd=bare, capture_output=True, text=True
    )
    return found.stdout.strip() if found.returncode == 0 else None


def test_a_sign_off_pushes_exactly_that_commit_and_its_tag(work: Path, remote: Path):
    signed = _commit(work, "a.txt", "a\n")
    git(work, "tag", "f1-done")
    _commit(work, "later.txt", "merged after the sign-off\n")
    git(work, "branch", "task/f2-01")
    git(work, "tag", "f2-start")
    assert push.push_signed_off(work, "origin") == push.Outcome(("f1-done",))
    assert _on_remote(remote, "refs/heads/main") == signed  # later work waits for its sign-off
    assert _on_remote(remote, "refs/tags/f1-done") == signed
    assert _on_remote(remote, "refs/heads/task/f2-01") is None
    assert _on_remote(remote, "refs/tags/f2-start") is None


def test_nothing_signed_off_pushes_nothing(work: Path, remote: Path):
    assert push.push_signed_off(work, "origin") == push.Outcome()
    assert _on_remote(remote, "refs/heads/main") is None


def test_several_go_oldest_first_and_a_second_round_changes_nothing(work: Path, remote: Path):
    _commit(work, "a.txt", "a\n")
    git(work, "-c", "user.name=T", "tag", "f1-done")
    last = _commit(work, "b.txt", "b\n")
    git(work, "tag", "f2-done")
    assert set(push.push_signed_off(work, "origin").pushed) == {"f1-done", "f2-done"}
    assert _on_remote(remote, "refs/heads/main") == last
    assert push.push_signed_off(work, "origin") == push.Outcome()


def test_an_older_tag_goes_alone_when_main_is_already_past_it(work: Path, remote: Path):
    older = _commit(work, "a.txt", "a\n")
    newer = _commit(work, "b.txt", "b\n")
    git(work, "tag", "f2-done")
    push.push_signed_off(work, "origin")
    git(work, "tag", "f1-done", older)
    assert push.push_signed_off(work, "origin").pushed == ("f1-done",)
    assert _on_remote(remote, "refs/heads/main") == newer
    assert _on_remote(remote, "refs/tags/f1-done") == older


def test_a_remote_that_moved_apart_stops_it_and_nothing_is_forced(
    work: Path, remote: Path, tmp_path: Path
):
    _commit(work, "a.txt", "a\n")
    git(work, "tag", "f1-done")
    push.push_signed_off(work, "origin")
    other = tmp_path / "other"
    subprocess.run(["git", "clone", "-q", str(remote), str(other)], check=True)
    git(other, "config", "user.email", "o@example.com")
    git(other, "config", "user.name", "Other")
    theirs = _commit(other, "theirs.txt", "theirs\n")
    git(other, "push", "-q", "origin", "main")
    _commit(work, "b.txt", "b\n")
    git(work, "tag", "f2-done")
    outcome = push.push_signed_off(work, "origin")
    assert outcome.pushed == () and "moved apart" in outcome.held and "f2-done" in outcome.held
    assert _on_remote(remote, "refs/heads/main") == theirs
    assert _on_remote(remote, "refs/tags/f2-done") is None


def test_a_key_holds_the_push_and_is_never_named(work: Path, remote: Path):
    _commit(work, "config.py", f'KEY = "{FAKE_KEY}"\n')
    _commit(work, "fine.py", "x = 1\n")  # gone from the tip's change wouldn't matter: history goes
    git(work, "tag", "f1-done")
    outcome = push.push_signed_off(work, "origin")
    assert outcome.pushed == () and "config.py:1" in outcome.held
    assert FAKE_KEY not in outcome.held
    assert _on_remote(remote, "refs/heads/main") is None


def test_a_key_removed_in_a_later_commit_still_holds_it(work: Path):
    _commit(work, "config.py", f'KEY = "{FAKE_KEY}"\n')
    _commit(work, "config.py", "KEY = None\n")
    git(work, "tag", "f1-done")
    assert "config.py:1" in push.push_signed_off(work, "origin").held


def test_the_notification_topic_holds_it_too(work: Path):
    _commit(work, "notes.md", "the topic is abcdef123456\n")
    git(work, "tag", "f1-done")
    outcome = push.push_signed_off(work, "origin", topic="abcdef123456")
    assert "notes.md:1" in outcome.held and "abcdef123456" not in outcome.held


@pytest.mark.parametrize(
    ("name", "bad"),
    [
        (".env", True),
        ("app/.env.local", True),
        (".env.example", False),
        ("db.sqlite3", True),
        ("server.pem", True),
        ("environment.py", False),
        ("tests/fixtures/probes/claude-stream.jsonl", False),
    ],
)
def test_a_risky_file_name_is_named(name: str, bad: bool):
    diff = f"+++ b/{name}\n@@ -0,0 +1 @@\n+x\n"
    assert bool(push.secret_problems(diff, None)) is bad


def test_a_remote_that_doesnt_answer_is_a_failure_to_try_again(work: Path, tmp_path: Path):
    git(work, "remote", "set-url", "origin", str(tmp_path / "gone.git"))
    _commit(work, "a.txt", "a\n")
    git(work, "tag", "f1-done")
    outcome = push.push_signed_off(work, "origin")
    assert outcome.failed and not outcome.held and outcome.pushed == ()
    git(work, "remote", "set-url", "origin", str(tmp_path / "remote.git"))
    assert push.push_signed_off(work, "origin").pushed == ("f1-done",)  # no state to clear


def test_the_project_names_its_remote_or_nothing_is_pushed(tmp_path: Path):
    assert push.remote_of(tmp_path) is None
    (tmp_path / ".softfield").mkdir()
    toml = tmp_path / ".softfield" / "project.toml"
    toml.write_text('[project]\nname = "x"\n')
    assert push.remote_of(tmp_path) is None
    toml.write_text('[project]\nname = "x"\nremote = "origin"\n')
    assert push.remote_of(tmp_path) == "origin"


def test_it_says_keeps_failing_only_after_hours(tmp_path: Path):
    now = datetime(2026, 11, 2, 12, tzinfo=UTC)
    assert not push.keeps_failing("", now)
    assert not push.keeps_failing((now - timedelta(hours=1)).isoformat(), now)
    assert push.keeps_failing((now - timedelta(hours=7)).isoformat(), now)
    push.write_memory(tmp_path, push.Memory(("f1-done",), "x"))
    assert push.read_memory(tmp_path) == push.Memory(("f1-done",), "x")
