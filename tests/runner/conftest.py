import subprocess
from pathlib import Path

import pytest

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
    (tmp_path / "workflow").mkdir()
    (tmp_path / "workflow" / "protected-paths.txt").write_text(
        "# comment\ncoucou/secret.py\nrunner/**\n"
    )
    for folder in ("ready", "done", "escalated", "blocked"):
        (tmp_path / "tasks" / folder).mkdir(parents=True)
        (tmp_path / "tasks" / folder / ".gitkeep").write_text("")
    (tmp_path / ".gitignore").write_text("var/\nBLOCKED.md\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "init")
    return tmp_path
