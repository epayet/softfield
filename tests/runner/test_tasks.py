from pathlib import Path

import pytest

from runner.tasks import (
    TaskError,
    append_footer,
    blocked_ids,
    parse_sections,
    parse_task,
    pick_next,
    preflight,
)
from tests.runner.conftest import write_task


def test_parse_task(tmp_path):
    task = parse_task(write_task(tmp_path, "m1-01-thing"), default_max_diff=150)
    assert task.id == "m1-01-thing"
    assert task.files == ("coucou/thing.py",)
    assert task.tests == ("tests/unit/test_thing.py",)
    assert task.max_diff == 150
    assert task.goal == "Make the thing work."


def test_id_must_match_file_name(tmp_path):
    path = write_task(tmp_path, "m1-01-thing")
    path.rename(tmp_path / "m1-02-other.md")
    with pytest.raises(TaskError, match="file name"):
        parse_task(tmp_path / "m1-02-other.md", 150)


def test_missing_section_is_rejected(tmp_path):
    path = write_task(tmp_path, "m1-01-thing")
    path.write_text(path.read_text().replace("### Steps", "### Stepz"))
    with pytest.raises(TaskError, match="Steps"):
        parse_task(path, 150)


def test_frontmatter_required(tmp_path):
    path = tmp_path / "m1-01-x.md"
    path.write_text("### Goal\nx\n")
    with pytest.raises(TaskError, match="frontmatter"):
        parse_task(path, 150)


def test_sections():
    assert parse_sections("intro\n### A\none\n### B\ntwo\nthree\n") == {
        "A": "one",
        "B": "two\nthree",
    }


def _tasks(tmp_path: Path, specs: dict[str, str]):
    return [parse_task(write_task(tmp_path, tid, deps), 150) for tid, deps in specs.items()]


def test_pick_next_respects_dependencies_and_order(tmp_path):
    ready = _tasks(tmp_path, {"m1-02-b": "[m1-01-a]", "m1-03-c": "[]", "m2-01-d": "[]"})
    first = pick_next(ready, done=set(), paused=set())
    assert first is not None and first.id == "m1-03-c"
    second = pick_next(ready, done={"m1-01-a"}, paused=set())
    assert second is not None and second.id == "m1-02-b"


def test_dependants_of_escalated_tasks_are_paused(tmp_path):
    ready = _tasks(tmp_path, {"m1-02-b": "[m1-01-a]", "m1-03-c": "[m1-02-b]", "m1-04-d": "[]"})
    assert blocked_ids(ready, escalated={"m1-01-a"}) == {"m1-02-b", "m1-03-c"}


def test_preflight(repo):
    task = parse_task(write_task(repo / "tasks" / "ready", "m1-01-thing"), 150)
    assert preflight(task, repo) == []
    (repo / "coucou" / "thing.py").write_text("x = 1\n")
    assert preflight(task, repo) == ["symbol not found in the task's files: thing"]
    (repo / "coucou" / "thing.py").unlink()
    assert "referenced path does not exist: coucou/thing.py" in preflight(task, repo)


def test_footer(tmp_path):
    path = write_task(tmp_path, "m1-01-thing")
    append_footer(path, {"result": "done", "attempts": 2})
    assert path.read_text().endswith("# --- runner ---\nresult: done\nattempts: 2\n```\n")
