import subprocess
import time
import types
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from runner import session, waits


@pytest.fixture(autouse=True)
def utc_zone(monkeypatch):
    """The runner shows local time; its tests write UTC times and read them back as such, so
    the machine's zone is UTC unless a test sets another (F187 D6)."""
    monkeypatch.setenv("TZ", "UTC")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


@pytest.fixture
def paris(monkeypatch):
    """The machine's zone is Paris, so local is not UTC and a slip shows (F187 D6)."""
    monkeypatch.setenv("TZ", "Europe/Paris")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


TASK = """\
---
id: {id}
milestone: 1
depends_on: {deps}
files:
  - coucou/thing.py
tests:
  - tests/unit/test_thing.py
---

### Goal
Make the thing work.

### Context
`coucou/thing.py` has `def thing() -> int`.

### Pattern to follow
`coucou/thing.py`

### Steps
1. Implement `thing`.

### Done when
Tests pass.
"""


# Coucou's own checks (its .softfield/project.toml), for the gates' tests
CHECKS = """\
[checks]
mypy = ["coucou", "tests", "runner", "factory_dashboard"]
translations = true
dependency_dirs = ["coucou/static/coucou/vendor/", "factory_dashboard/static/vendor/"]
test_dirs = ["tests/unit", "tests/integration", "tests/runner", "tests/browser",
             "tests/factory_dashboard"]

[checks.layouts]
"tests/unit" = ["coucou", ".py"]
"tests/runner" = ["runner", ".py"]
"tests/browser" = ["coucou/static/coucou/js", ".js"]
"tests/factory_dashboard" = ["factory_dashboard", ".py"]
"""


def write_task(directory: Path, task_id: str, deps: str = "[]") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{task_id}.md"
    path.write_text(TASK.format(id=task_id, deps=deps), encoding="utf-8")
    return path


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout


@pytest.fixture(autouse=True)
def _no_machine_config(monkeypatch, tmp_path_factory):
    """A test's config is its repo's ``.softfield/project.toml`` alone, never this machine's
    ``~/.config/softfield/factory.toml`` (ADR 30 item 3)."""
    monkeypatch.setenv("SOFTFIELD_CONFIG", str(tmp_path_factory.getbasetemp() / "no-machine.toml"))


# A copy of a machine's ~/.config/softfield/factory.toml: its agents, roles, Claude's reserves
MACHINE = Path(__file__).resolve().parents[1] / "fixtures" / "softfield-machine.toml"


@pytest.fixture
def machine(monkeypatch):
    """This repo's project.toml over the machine file it was written for (ADR 30 item 3)."""
    monkeypatch.setenv("SOFTFIELD_CONFIG", str(MACHINE))


@pytest.fixture(autouse=True)
def _no_shared_docs(monkeypatch, tmp_path_factory):
    """A test's lead jobs read only its own repo's docs, never the Softfield checkout's
    (ADR 30 item 4); a test that wants shared docs sets ``config.HOME`` itself."""
    monkeypatch.setattr("runner.config.HOME", tmp_path_factory.mktemp("softfield-home"))


@pytest.fixture(autouse=True)
def _fresh_process(monkeypatch):
    """Each test is a process of its own: the runner's code is fingerprinted anew."""
    monkeypatch.setattr("runner.loop._CODE_AT_START", {})


@pytest.fixture(autouse=True)
def _no_outer_git(monkeypatch):
    """Run from a git hook, GIT_INDEX_FILE and friends point at the real repo; the temporary
    repos here must never inherit them."""
    for name in (
        "GIT_INDEX_FILE",
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_PREFIX",
        "GIT_OBJECT_DIRECTORY",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture(autouse=True)
def _idle_run_is_ended(monkeypatch):
    """`runner run` holds when it has nothing to run (F101): here the owner ends it at its
    first idle poll (Ctrl-C), unless a test scripts the polls."""

    def ctrl_c() -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr("runner.loop._idle_wait", ctrl_c)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A tiny git repo shaped like coucou, on main, with one commit."""
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.email", "t@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "coucou").mkdir()
    (tmp_path / "coucou" / "thing.py").write_text(
        "def thing() -> int:\n    raise NotImplementedError\n"
    )
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    (tmp_path / "tests" / "unit" / "test_thing.py").write_text("def test_thing():\n    pass\n")
    (tmp_path / ".softfield").mkdir()
    (tmp_path / ".softfield" / "project.toml").write_text(CHECKS)
    (tmp_path / ".softfield" / "protected-paths.txt").write_text(
        "# comment\ncoucou/secret.py\nrunner/**\n"
    )
    for folder in ("ready", "done", "escalated", "blocked"):
        (tmp_path / ".softfield" / "tasks" / folder).mkdir(parents=True)
        (tmp_path / ".softfield" / "tasks" / folder / ".gitkeep").write_text("")
    (tmp_path / ".gitignore").write_text(".softfield/var/\nvar/\nBLOCKED.md\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "init")
    return tmp_path


THURSDAY = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)


@pytest.fixture
def fake_clock(monkeypatch) -> list[datetime]:
    """``session.now`` reads the clock; a sleep moves it on, so a reset can pass in a test."""
    clock = [THURSDAY]
    slept: list[float] = []

    def sleep(seconds: float) -> None:
        slept.append(seconds)
        clock[0] += timedelta(seconds=seconds)

    real_sleep = time.sleep
    monkeypatch.setattr(session, "now", lambda: clock[0])
    monkeypatch.setattr("time.sleep", sleep)
    monkeypatch.setattr("subprocess.time", types.SimpleNamespace(sleep=real_sleep))
    return clock


class _Terminal:
    """The owner at the keyboard, ready to type y: the runner must never read it."""

    def isatty(self) -> bool:
        return True

    def readline(self, *args: object) -> str:
        pytest.fail("the runner read the console")

    def read(self, *args: object) -> str:
        pytest.fail("the runner read the console")


@pytest.fixture
def at_the_keyboard(monkeypatch) -> None:
    """ADR 22 item 4: no command asks y/N, so nothing reads the console or waits on it."""
    monkeypatch.setattr("sys.stdin", _Terminal())
    monkeypatch.setattr("select.select", lambda *a: pytest.fail("the runner waited on stdin"))


@pytest.fixture(autouse=True)
def _new_command(monkeypatch):
    """Each test is a new command, with the runs its exit ends."""
    monkeypatch.setattr(session, "OPEN_RUNS", [])


@pytest.fixture(autouse=True)
def _no_probe(monkeypatch):
    """No fresh reading of Claude's windows (f4-07), unless a test asks for one: the stored
    readings decide, and no real `claude -p` runs."""
    monkeypatch.setattr(waits, "fresh_reading", lambda s: None)
