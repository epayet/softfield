from pathlib import Path

import pytest

from runner.tasks import (
    STOPPED,
    TESTS_ONLY,
    Task,
    TaskError,
    append_footer,
    blocked_ids,
    command_arg,
    full_key,
    held_ids,
    load_dir,
    milestone_arg,
    milestone_file,
    milestone_key,
    milestone_order,
    next_milestone_key,
    parse_sections,
    parse_task,
    pick_next,
    preflight,
    queued_tests,
    short_key,
    task_ids,
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


def test_a_milestone_waiting_for_a_sign_off_is_never_picked(tmp_path):
    """ADR 17 item 4: m1's tickets wait for m0's sign-off; other milestones go on."""
    ready = _tasks(tmp_path, {"m1-01-a": "[]", "m1-02-b": "[m1-01-a]"})
    other = write_task(tmp_path, "m2-01-c")
    other.write_text(other.read_text().replace("milestone: 1\n", "milestone: 2\n"))
    ready.append(parse_task(other, 150))
    held = held_ids(ready, {"m1": "m0-start-up"})
    assert held == {"m1-01-a": "m0-start-up", "m1-02-b": "m0-start-up"}
    picked = pick_next(ready, done=set(), paused=set(held))
    assert picked is not None and picked.id == "m2-01-c"
    assert pick_next(ready[:2], done=set(), paused=set(held)) is None


def test_no_wait_changes_nothing(tmp_path):
    ready = _tasks(tmp_path, {"m1-01-a": "[]", "m1-02-c": "[]"})
    assert held_ids(ready, {}) == {}
    picked = pick_next(ready, done=set(), paused=set(held_ids(ready, {})))
    assert picked is not None and picked.id == "m1-01-a"


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
    """Files listed in `files:` may be created by the task, and developers write their own
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


def test_preflight_sends_a_tests_only_ticket_to_the_lead(repo):
    """f4-36: a ticket that changes only tests can't pass tests-fail-on-main, so it escalates
    before any attempt rather than after three and a direction."""
    path = write_task(repo / "tasks" / "ready", "m1-01-thing")
    path.write_text(path.read_text().replace("- coucou/thing.py\n", "- tests/unit/test_thing.py\n"))
    task = parse_task(path, 150)
    assert task.files == ("tests/unit/test_thing.py",)
    assert preflight(task, repo) == [TESTS_ONLY]


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


def test_queued_tests_skip_only_developer_tickets_and_never_the_tickets_own(tmp_path: Path):
    """f1-33: lead tickets write their tests in their own job, so theirs are never skeletons,
    and a file the current ticket lists runs even when a queued developer ticket lists it."""
    tasks = tmp_path / "tasks"
    current = write_task(tasks / "ready", "m1-01-current")
    current.write_text(
        current.read_text().replace(
            "  - tests/unit/test_thing.py", "  - tests/unit/test_thing.py\n  - tests/unit/test_x.py"
        )
    )
    lead = write_task(tasks / "ready", "m1-02-lead")
    lead.write_text(
        lead.read_text()
        .replace("milestone: 1\n", "milestone: 1\nagent: lead\n")
        .replace("test_thing.py", "test_lead.py")
    )
    dev = write_task(tasks / "blocked", "m1-03-dev")
    dev.write_text(
        dev.read_text().replace(
            "  - tests/unit/test_thing.py", "  - tests/unit/test_dev.py\n  - tests/unit/test_x.py"
        )
    )
    assert queued_tests(tasks, "m1-01-current") == {"tests/unit/test_dev.py"}
    # A lead's check-all (no current ticket) still runs every lead ticket's tests.
    assert queued_tests(tasks, "") == {
        "tests/unit/test_thing.py",
        "tests/unit/test_dev.py",
        "tests/unit/test_x.py",
    }


def test_a_ticket_says_who_works_it(tmp_path):
    path = write_task(tmp_path, "m1-01-thing")
    assert parse_task(path, 150).agent == "developer"
    path.write_text(path.read_text().replace("milestone: 1\n", "milestone: 1\nagent: lead\n"))
    assert parse_task(path, 150).agent == "lead"
    path.write_text(path.read_text().replace("agent: lead", "agent: owner"))
    with pytest.raises(TaskError, match="agent"):
        parse_task(path, 150)


@pytest.mark.parametrize("line", ["", "agent: developer\n", "agent: junior\n"])
def test_a_developer_ticket_parses_as_developer_and_junior_is_a_synonym(tmp_path, line):
    """ADR 14 item 1: "junior" became "developer"; old tickets keep parsing."""
    path = write_task(tmp_path, "m1-01-thing")
    path.write_text(path.read_text().replace("milestone: 1\n", "milestone: 1\n" + line))
    assert parse_task(path, 150).agent == "developer"


def test_an_old_junior_tickets_tests_are_skipped_like_a_developers(tmp_path):
    tasks = tmp_path / "tasks"
    write_task(tasks / "ready", "m1-01-current")
    old = write_task(tasks / "ready", "m1-02-old")
    old.write_text(
        old.read_text()
        .replace("milestone: 1\n", "milestone: 1\nagent: junior\n")
        .replace("test_thing.py", "test_old.py")
    )
    assert queued_tests(tasks, "m1-01-current") == {"tests/unit/test_old.py"}


def test_a_lead_ticket_may_name_extra_commands(tmp_path):
    """f1's probes run as a headless lead ticket with a narrow tool list (ADR 14)."""
    path = write_task(tmp_path, "m1-01-thing")
    assert parse_task(path, 150).commands == ()
    lead = path.read_text().replace("milestone: 1\n", "milestone: 1\nagent: lead\n")
    commands = "commands: [ollama list, uv run runner report, uv run runner run --dry-run]\n"
    path.write_text(lead.replace("agent: lead\n", "agent: lead\n" + commands))
    assert parse_task(path, 150).commands == (
        "ollama list",
        "uv run runner report",
        "uv run runner run --dry-run",  # read-only: a replan checks its tickets with it
    )


@pytest.mark.parametrize(
    "commands",
    [
        "[git commit]",
        "[git]",
        "[uv run runner signoff]",
        "[uv run runner milestone f1]",
        "[uv run runner]",
        "[uv run]",
        "['ls;rm']",
        "[1]",
    ],
)
def test_commands_never_reach_git_or_the_owners_commands(tmp_path, commands):
    path = write_task(tmp_path, "m1-01-thing")
    lead = path.read_text().replace("milestone: 1\n", "milestone: 1\nagent: lead\n")
    path.write_text(lead.replace("agent: lead\n", f"agent: lead\ncommands: {commands}\n"))
    with pytest.raises(TaskError, match="commands"):
        parse_task(path, 150)


def test_only_lead_tickets_name_commands(tmp_path):
    path = write_task(tmp_path, "m1-01-thing")
    path.write_text(path.read_text().replace("milestone: 1\n", "milestone: 1\ncommands: [ls]\n"))
    with pytest.raises(TaskError, match="commands"):
        parse_task(path, 150)


def test_a_ticket_may_carry_its_difficulty_and_its_correction(tmp_path):
    """ADR 14 item 5: 1 to 10, set at plan time; the lead may correct it at review."""
    path = write_task(tmp_path, "m1-01-thing")
    task = parse_task(path, 150)
    assert (task.difficulty, task.difficulty_corrected) == (None, None)
    path.write_text(
        path.read_text().replace(
            "milestone: 1\n", "milestone: 1\ndifficulty: 1\ndifficulty_corrected: 10\n"
        )
    )
    task = parse_task(path, 150)
    assert (task.difficulty, task.difficulty_corrected) == (1, 10)


@pytest.mark.parametrize("key", ["difficulty", "difficulty_corrected"])
@pytest.mark.parametrize("value", ["11", "0", '"hard"', "hard", "4.5", "true", "-3", "null"])
def test_a_difficulty_is_an_integer_from_1_to_10(tmp_path, key, value):
    path = write_task(tmp_path, "m1-01-thing")
    path.write_text(path.read_text().replace("milestone: 1\n", f"milestone: 1\n{key}: {value}\n"))
    with pytest.raises(TaskError, match=key):
        parse_task(path, 150)


def test_every_done_m1_to_m4_ticket_has_a_difficulty():
    """f1-17 estimated M1–M4 from each ticket and its result, so ratings can be seeded."""
    repo = Path(__file__).resolve().parents[2]
    paths = sorted((repo / "tasks" / "done").glob("m*.md"))
    assert paths
    missing = [p.stem for p in paths if parse_task(p, 150).difficulty is None]
    assert missing == []


def test_a_milestone_is_a_number_or_a_named_key(tmp_path):
    """A number N is Coucou's milestone mN; a key like f1 is a factory milestone."""
    assert parse_task(write_task(tmp_path, "m1-01-thing"), 150).milestone == "m1"
    path = write_task(tmp_path, "f1-01-metrics")
    path.write_text(path.read_text().replace("milestone: 1\n", "milestone: f1\n"))
    assert parse_task(path, 150).milestone == "f1"
    path.write_text(path.read_text().replace("milestone: f1\n", "milestone: F 1\n"))
    with pytest.raises(TaskError, match="milestone"):
        parse_task(path, 150)


@pytest.mark.parametrize(
    ("given", "key"),
    [(4, "m4"), ("4", "m4"), ("m4", "m4"), ("f1", "f1"), ("f12", "f12"), ("f0", "f0"), (0, "m0")],
)
def test_milestone_key(given, key):
    assert milestone_key(given) == key


@pytest.mark.parametrize("given", ["", "f", "1f", "f-1", "F1", "f01", "04", "٣", True, -1])
def test_milestone_key_refuses_anything_else(given):
    with pytest.raises(TaskError):
        milestone_key(given)


def test_next_milestone_key():
    assert next_milestone_key("m4") == "m5" and next_milestone_key("f9") == "f10"


@pytest.mark.parametrize("given", ["f3-factory-line", "m5-history", "f2-cloud-first", "f3-v2"])
def test_a_named_key_is_accepted(given):
    """ADR 16 item 6: a key may be `<series><n>-<slug>`."""
    assert milestone_key(given) == given


@pytest.mark.parametrize(
    "given",
    [
        "f3-",
        "F3",
        "f-1",
        "F3-factory",
        "f3-Factory",
        "f3--line",
        "f3-line-",
        "f3-01",
        "f3-01-x",
        "-f3",
    ],
)
def test_a_named_key_refuses_a_bad_slug(given):
    """A slug starts with a letter, so a ticket id (`f3-01-x`) is never a milestone key."""
    with pytest.raises(TaskError):
        milestone_key(given)


def test_a_named_key_orders_like_its_short_form():
    assert milestone_order("f3-factory-line") == milestone_order("f3") == ("f", 3)
    assert milestone_order("f3-factory-line") < milestone_order("f10")
    assert short_key("f3-factory-line") == "f3" and short_key("m4") == "m4"
    assert next_milestone_key("f3-factory-line") == "f4"
    assert command_arg("f3-factory-line") == "f3-factory-line" and command_arg("m4") == "4"


def _docs(repo: Path, *names: str) -> None:
    (repo / "docs" / "milestones").mkdir(parents=True, exist_ok=True)
    for name in names:
        (repo / "docs" / "milestones" / f"{name}.md").write_text(f"# {name}\n")


def test_the_full_key_comes_from_the_milestone_doc(tmp_path):
    _docs(tmp_path, "f2", "f3-factory-line", "m4")
    assert full_key(tmp_path, "f3") == "f3-factory-line"
    assert full_key(tmp_path, "f3-factory-line") == "f3-factory-line"
    assert full_key(tmp_path, "f2") == "f2"  # an existing short-key doc
    assert full_key(tmp_path, "f4") == "f4"  # no doc yet
    assert full_key(tmp_path / "nowhere", "f3") == "f3"


def test_a_milestone_file_is_the_full_keys_or_else_the_short_keys(tmp_path):
    _docs(tmp_path, "f2", "f3-factory-line")
    docs = tmp_path / "docs" / "milestones"
    assert milestone_file(tmp_path, "milestones", "f3-factory-line") == docs / "f3-factory-line.md"
    assert milestone_file(tmp_path, "milestones", "f2") == docs / "f2.md"
    assert milestone_file(tmp_path, "milestones", "f2-cloud-first") == docs / "f2.md"
    reviews = tmp_path / "docs" / "reviews"
    assert milestone_file(tmp_path, "reviews", "f3-factory-line") == reviews / "f3-factory-line.md"


def _ticket_of(repo: Path, folder: str, task_id: str, milestone: str) -> Path:
    path = write_task(repo / "tasks" / folder, task_id)
    path.write_text(path.read_text().replace("milestone: 1\n", f"milestone: {milestone}\n"))
    return path


def test_a_tickets_milestone_in_either_form_is_the_full_key_once_its_doc_exists(tmp_path):
    short = _ticket_of(tmp_path, "ready", "f3-01-a", "f3")
    full = _ticket_of(tmp_path, "ready", "f3-02-b", "f3-factory-line")
    assert parse_task(short, 150).milestone == "f3"
    assert parse_task(full, 150).milestone == "f3-factory-line"
    _docs(tmp_path, "f3-factory-line")
    assert parse_task(short, 150).milestone == "f3-factory-line"
    assert parse_task(full, 150).milestone == "f3-factory-line"


def test_the_command_takes_either_form(tmp_path):
    """`runner milestone f3` is f3-factory-line when its tickets say so, even with no doc."""
    _ticket_of(tmp_path, "ready", "f3-01-a", "f3-factory-line")
    _ticket_of(tmp_path, "done", "m4-01-b", "4")
    (tmp_path / "tasks" / "done" / "broken.md").write_text("no frontmatter\n")
    assert milestone_arg(tmp_path, "f3") == "f3-factory-line"
    assert milestone_arg(tmp_path, "f3-factory-line") == "f3-factory-line"
    assert milestone_arg(tmp_path, "4") == "m4" and milestone_arg(tmp_path, "f1") == "f1"
    _docs(tmp_path, "f3-assembly")  # the doc wins over the tickets
    assert milestone_arg(tmp_path, "f3") == "f3-assembly"
    with pytest.raises(TaskError):
        milestone_arg(tmp_path, "F3")


def test_pick_next_orders_milestones_by_number(tmp_path):
    for tid in ("m10-01-late", "m9-01-early"):
        path = write_task(tmp_path, tid)
        path.write_text(
            path.read_text().replace("milestone: 1\n", f"milestone: {tid.split('-')[0][1:]}\n")
        )
    ready = [parse_task(p, 150) for p in sorted(tmp_path.glob("*.md"))]
    first = pick_next(ready, done=set(), paused=set())
    assert first is not None and first.id == "m9-01-early"


def _created_before(task: Task, queued: dict[str, Task]) -> set[str]:
    """The files the tickets ``task`` (transitively) depends on will create."""
    created: set[str] = set()
    seen: set[str] = set()
    todo = list(task.depends_on)
    while todo:
        dep = queued.get(todo.pop())
        if dep is None or dep.id in seen:
            continue
        seen.add(dep.id)
        created.update(dep.files, dep.tests)
        todo.extend(dep.depends_on)
    return created


def test_queued_tickets_name_only_what_exists_or_an_earlier_ticket_creates():
    """The replans' check (f1-07, f1-19): a queued ticket's pre-flight has no problem but a
    path that a ticket it depends on creates. ``runner run --dry-run`` needs a clean main."""
    repo = Path(__file__).resolve().parents[2]
    queued = {
        task.id: task
        for folder in ("ready", *STOPPED)
        for task in load_dir(repo / "tasks" / folder, 150)
    }
    # An escalated ticket never runs as written: the lead rewrites or implements it, and its
    # escalation's check-all runs while it still sits in escalated/ (f1-50).
    escalated = task_ids(repo / "tasks" / "escalated")
    problems = []
    for task in queued.values():
        if task.id in escalated:
            continue
        created = _created_before(task, queued)
        for problem in preflight(task, repo):
            path = problem.removeprefix("referenced path does not exist: ")
            # A tests-only ticket may wait here: pre-flight hands it to the lead when it runs.
            if problem != TESTS_ONLY and path not in created:
                problems.append(f"{task.id}: {problem}")
    assert problems == []
