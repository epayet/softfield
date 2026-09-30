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
    queued_tests,
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
    path.write_text(path.read_text().replace("### Done when", "### Done whenever"))
    with pytest.raises(TaskError, match="Done when"):
        parse_task(path, 150)


def test_a_ticket_needs_no_pattern_or_steps(tmp_path):
    """ADR 07 item 2: a goal, the context and acceptance criteria are enough."""
    path = write_task(tmp_path, "m1-01-thing")
    text = path.read_text()
    text = text.replace("### Pattern to follow\n`coucou/thing.py`\n\n", "")
    path.write_text(text.replace("### Steps\n1. Implement `thing`.\n\n", ""))
    task = parse_task(path, 150)
    assert "Steps" not in task.sections and "Pattern to follow" not in task.sections


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
    (repo / "coucou" / "other.py").write_text("")
    task.path.write_text(
        task.path.read_text().replace("`coucou/thing.py`\n\n###", "`coucou/other.py`\n\n###")
    )
    task = parse_task(task.path, 150)
    (repo / "coucou" / "other.py").unlink()
    assert "referenced path does not exist: coucou/other.py" in preflight(task, repo)


def test_preflight_allows_new_files_and_unwritten_tests(repo):
    """Files listed in `files:` may be created by the task, and juniors write their own
    tests, so neither has to exist yet (ADR 07 items 2 and 4)."""
    path = write_task(repo / "tasks" / "ready", "m1-01-thing")
    # m4-07: a Context naming its own (unwritten) test file failed pre-flight.
    path.write_text(
        path.read_text().replace(
            "`coucou/thing.py` has", "Test it in `tests/unit/test_thing.py`. `coucou/thing.py` has"
        )
    )
    task = parse_task(path, 150)
    (repo / "coucou" / "thing.py").unlink()
    (repo / "tests" / "unit" / "test_thing.py").unlink()
    assert "referenced path does not exist: coucou/thing.py" not in preflight(task, repo)
    assert not any("test_thing" in p for p in preflight(task, repo))


def test_footer(tmp_path):
    path = write_task(tmp_path, "m1-01-thing")
    append_footer(path, {"result": "done", "attempts": 2})
    assert path.read_text().endswith("# --- runner ---\nresult: done\nattempts: 2\n```\n")


def test_queued_tests_are_the_other_queued_tasks_tests(tmp_path: Path):
    tasks = tmp_path / "tasks"
    write_task(tasks / "ready", "m1-01-current")
    other = write_task(tasks / "ready", "m1-02-other")
    other.write_text(other.read_text().replace("test_thing.py", "test_other.py"))
    escalated = write_task(tasks / "escalated", "m1-03-stuck")
    escalated.write_text(escalated.read_text().replace("test_thing.py", "test_stuck.py"))
    done = write_task(tasks / "done", "m1-00-old")
    done.write_text(done.read_text().replace("test_thing.py", "test_old.py"))
    assert queued_tests(tasks, "m1-01-current") == {
        "tests/unit/test_other.py",
        "tests/unit/test_stuck.py",
    }


def test_a_ticket_says_who_works_it(tmp_path):
    path = write_task(tmp_path, "m1-01-thing")
    assert parse_task(path, 150).agent == "junior"
    path.write_text(path.read_text().replace("milestone: 1\n", "milestone: 1\nagent: lead\n"))
    assert parse_task(path, 150).agent == "lead"
    path.write_text(path.read_text().replace("agent: lead", "agent: owner"))
    with pytest.raises(TaskError, match="agent"):
        parse_task(path, 150)
