from pathlib import Path

import pytest

from runner.tasks import (
    AREA_MISSING,
    DEFAULT_PRIORITY,
    FEATURE_PRIORITY,
    FIX_OF_FIX,
    STOPPED,
    TESTS_ONLY,
    TESTS_ONLY_CODE,
    Task,
    TaskError,
    append_footer,
    blocked_ids,
    command_arg,
    early_for,
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
    pulls,
    short_key,
    task_ids,
    task_priority,
    ticket_prefix,
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


def test_sections_read_level_two_headings():
    """f23-01's plan was refused for "## Goal" (2026-10-08): a heading's form isn't a reason."""
    assert parse_sections("## Goal\none\n### Context\ntwo\n") == {"Goal": "one", "Context": "two"}


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
    task = parse_task(write_task(repo / ".factory" / "tasks" / "ready", "m1-01-thing"), 150)
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


def _with_context(repo: Path, context: str):
    path = write_task(repo / ".factory" / "tasks" / "ready", "m1-01-thing")
    text = path.read_text().replace("`coucou/thing.py` has `def thing() -> int`.", context)
    path.write_text(text)
    return parse_task(path, 150)


def test_preflight_reads_prose_class_as_no_symbol(repo):
    """f42-02 was refused for "symbol not found: to", from "adds a class to" (2026-10-08)."""
    task = _with_context(repo, "A scroll down adds a class to `header.bar` that moves it up.")
    assert preflight(task, repo) == []
    task = _with_context(repo, "```python\ndef missing(x):\n```")
    assert preflight(task, repo) == ["symbol not found in the task's files: missing"]


def test_preflight_takes_a_listed_files_bare_name(repo):
    """f33-01 said `overview.py` after naming its listed path (2026-10-08)."""
    task = _with_context(repo, "Read `coucou/thing.py`; `thing.py` gains a function.")
    assert preflight(task, repo) == []
    task = _with_context(repo, "`other.py` gains a function.")
    assert preflight(task, repo) == ["referenced path does not exist: other.py"]


def test_preflight_allows_new_files_and_unwritten_tests(repo):
    """Files listed in `files:` may be created by the task, and developers write their own
    tests, so neither has to exist yet (ADR 07 items 2 and 4)."""
    path = write_task(repo / ".factory" / "tasks" / "ready", "m1-01-thing")
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
    path = write_task(repo / ".factory" / "tasks" / "ready", "m1-01-thing")
    path.write_text(path.read_text().replace("- coucou/thing.py\n", "- tests/unit/test_thing.py\n"))
    task = parse_task(path, 150)
    assert task.files == ("tests/unit/test_thing.py",)
    assert preflight(task, repo) == [TESTS_ONLY]


def _tests_only(repo: Path, files: str) -> Task:
    path = write_task(repo / ".factory" / "tasks" / "ready", "m1-01-thing")
    text = path.read_text().replace("- coucou/thing.py\n", files)
    path.write_text(text.replace("milestone: 1\n", "milestone: 1\ntests_only: true\n"))
    return parse_task(path, 150)


def test_a_test_only_ticket_passes_preflight_for_a_developer(repo):
    """f8-09: a stand-in's weak-test finding is a developer's test-only ticket, not a lead job
    (f9-06 … f9-12 each waited for Claude over one assertion)."""
    task = _tests_only(repo, "- tests/unit/test_thing.py\n")
    assert task.tests_only and task.agent == "developer"
    assert preflight(task, repo) == []
    assert not parse_task(
        write_task(repo / ".factory" / "tasks" / "done", "m1-02-other"), 150
    ).tests_only


def test_a_test_only_ticket_lists_only_tests(repo):
    task = _tests_only(repo, "- tests/unit/test_thing.py\n  - coucou/thing.py\n")
    assert preflight(task, repo) == [TESTS_ONLY_CODE]


def test_tests_only_is_true_or_false(repo):
    path = _tests_only(repo, "- tests/unit/test_thing.py\n").path
    path.write_text(path.read_text().replace("tests_only: true", "tests_only: yes please"))
    with pytest.raises(TaskError, match="tests_only"):
        parse_task(path, 150)


def test_footer(tmp_path):
    path = write_task(tmp_path, "m1-01-thing")
    append_footer(path, {"result": "done", "attempts": 2})
    assert path.read_text().endswith("# --- runner ---\nresult: done\nattempts: 2\n```\n")


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


def test_a_lead_ticket_may_name_extra_commands(tmp_path):
    """f1's probes run as a headless lead ticket with a narrow tool list (ADR 14)."""
    path = write_task(tmp_path, "m1-01-thing")
    assert parse_task(path, 150).commands == ()
    lead = path.read_text().replace("milestone: 1\n", "milestone: 1\nagent: lead\n")
    commands = "commands: [ollama list, softfield report, softfield run --dry-run]\n"
    path.write_text(lead.replace("agent: lead\n", "agent: lead\n" + commands))
    assert parse_task(path, 150).commands == (
        "ollama list",
        "softfield report",
        "softfield run --dry-run",  # read-only: a replan checks its tickets with it
    )


@pytest.mark.parametrize(
    "commands",
    [
        "[git commit]",
        "[git]",
        "[softfield signoff]",
        "[softfield milestone f1]",
        "[softfield]",
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
    (repo / ".factory" / "cards").mkdir(parents=True, exist_ok=True)
    for name in names:
        (repo / ".factory" / "cards" / f"{name}.md").write_text(f"# {name}\n")


def test_the_full_key_comes_from_the_milestone_doc(tmp_path):
    _docs(tmp_path, "f2", "f3-factory-line", "m4")
    assert full_key(tmp_path, "f3") == "f3-factory-line"
    assert full_key(tmp_path, "f3-factory-line") == "f3-factory-line"
    assert full_key(tmp_path, "f2") == "f2"  # an existing short-key doc
    assert full_key(tmp_path, "f4") == "f4"  # no doc yet
    assert full_key(tmp_path / "nowhere", "f3") == "f3"


def test_a_milestone_file_is_the_full_keys_or_else_the_short_keys(tmp_path):
    _docs(tmp_path, "f2", "f3-factory-line")
    docs = tmp_path / ".factory" / "cards"
    assert milestone_file(tmp_path, "cards", "f3-factory-line") == docs / "f3-factory-line.md"
    assert milestone_file(tmp_path, "cards", "f2") == docs / "f2.md"
    assert milestone_file(tmp_path, "cards", "f2-cloud-first") == docs / "f2.md"
    reviews = tmp_path / ".factory" / "reviews"
    assert milestone_file(tmp_path, "reviews", "f3-factory-line") == reviews / "f3-factory-line.md"


def _ticket_of(repo: Path, folder: str, task_id: str, milestone: str) -> Path:
    path = write_task(repo / ".factory" / "tasks" / folder, task_id)
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
    (tmp_path / ".factory" / "tasks" / "done" / "broken.md").write_text("no frontmatter\n")
    assert milestone_arg(tmp_path, "f3") == "f3-factory-line"
    assert milestone_arg(tmp_path, "f3-factory-line") == "f3-factory-line"
    assert milestone_arg(tmp_path, "4") == "m4" and milestone_arg(tmp_path, "f1") == "f1"
    _docs(tmp_path, "f3-assembly")  # the doc wins over the tickets
    assert milestone_arg(tmp_path, "f3") == "f3-assembly"
    with pytest.raises(TaskError):
        milestone_arg(tmp_path, "F3")


def _bug(directory: Path, task_id: str = "bug-01-x", extra: str = "area: factory\n") -> Path:
    path = write_task(directory, task_id)
    path.write_text(path.read_text().replace("milestone: 1\n", f"milestone: bugs\n{extra}"))
    return path


def test_a_bug_ticket_belongs_to_the_standing_bugs_key(repo):
    """ADR 19 item 2: `bug-<nn>-<slug>`, `milestone: bugs`, with its area and priority 50."""
    task = parse_task(_bug(repo / ".factory" / "tasks" / "ready"), 150)
    assert (task.id, task.milestone, task.priority, task.area) == (
        "bug-01-x",
        "bugs",
        50,
        "factory",
    )
    assert preflight(task, repo) == []


def test_bugs_is_a_key_of_its_own(tmp_path):
    assert milestone_key("bugs") == "bugs" and short_key("bugs") == "bugs"
    assert full_key(tmp_path, "bugs") == "bugs"
    assert milestone_order("bugs") < milestone_order("f1")  # at equal priorities, a bug first
    assert ticket_prefix("bugs") == "bug" and ticket_prefix("f3-factory-line") == "f3"


@pytest.mark.parametrize("given", ["bug", "Bugs", "bugs-x", "BUGS"])
def test_only_bugs_itself_is_the_bugs_key(given):
    with pytest.raises(TaskError):
        milestone_key(given)


def test_no_milestone_command_takes_bugs(tmp_path):
    """Bugs are never planned, reviewed or signed off: `runner milestone|review|signoff bugs`."""
    with pytest.raises(TaskError, match="bugs is no milestone: its tickets run under `runner run`"):
        milestone_arg(tmp_path, "bugs")


@pytest.mark.parametrize(
    ("task_id", "milestone"),
    [("bug-01-x", "1"), ("m1-01-x", "bugs"), ("bug-1-x", "bugs"), ("bug-01", "bugs")],
)
def test_a_bug_id_and_the_bugs_key_go_together(tmp_path, task_id, milestone):
    path = write_task(tmp_path, task_id)
    path.write_text(
        path.read_text().replace("milestone: 1\n", f"milestone: {milestone}\narea: product\n")
    )
    with pytest.raises(TaskError, match="bug-<nn>-<slug>"):
        parse_task(path, 150)


def test_a_bug_without_an_area_fails_preflight(repo):
    task = parse_task(_bug(repo / ".factory" / "tasks" / "ready", extra=""), 150)
    assert task.area is None
    assert preflight(task, repo) == [AREA_MISSING]


@pytest.mark.parametrize("value", ["both", "Factory", "1", "null"])
def test_an_area_is_factory_or_product(tmp_path, value):
    with pytest.raises(TaskError, match="'area' must be factory or product"):
        parse_task(_bug(tmp_path, extra=f"area: {value}\n"), 150)


def test_any_ticket_may_carry_a_priority_and_only_a_bug_has_a_default(tmp_path):
    """ADR 19 item 3: lower first. A milestone ticket without one takes its card's (f5 D6)."""
    path = write_task(tmp_path, "m1-01-thing")
    task = parse_task(path, 150)
    assert (task.priority, task.area) == (None, None)
    path.write_text(path.read_text().replace("milestone: 1\n", "milestone: 1\npriority: 3\n"))
    assert parse_task(path, 150).priority == 3
    assert parse_task(_bug(tmp_path, extra="area: product\npriority: 0\n"), 150).priority == 0


@pytest.mark.parametrize("value", ["-1", "high", "2.5", "true", "null", '"3"'])
def test_a_priority_is_a_whole_number_from_0(tmp_path, value):
    path = write_task(tmp_path, "m1-01-thing")
    path.write_text(
        path.read_text().replace("milestone: 1\n", f"milestone: 1\npriority: {value}\n")
    )
    with pytest.raises(TaskError, match="'priority' must be a whole number from 0"):
        parse_task(path, 150)


def test_pick_next_orders_milestones_by_number(tmp_path):
    for tid in ("m10-01-late", "m9-01-early"):
        path = write_task(tmp_path, tid)
        path.write_text(
            path.read_text().replace("milestone: 1\n", f"milestone: {tid.split('-')[0][1:]}\n")
        )
    ready = [parse_task(p, 150) for p in sorted(tmp_path.glob("*.md"))]
    first = pick_next(ready, done=set(), paused=set())
    assert first is not None and first.id == "m9-01-early"


def _in(directory: Path, task_id: str, milestone: str, extra: str = "", deps: str = "[]") -> Task:
    path = write_task(directory, task_id, deps)
    path.write_text(path.read_text().replace("milestone: 1\n", f"milestone: {milestone}\n{extra}"))
    return parse_task(path, 150)


def test_pick_next_goes_by_the_milestone_card_priority_first(tmp_path):
    """f5 D6: a ticket in a priority-1 milestone goes before one in an earlier milestone at 5."""
    ready = [_in(tmp_path, "f1-01-early", "f1"), _in(tmp_path, "f2-01-late", "f2")]
    picked = pick_next(ready, done=set(), paused=set(), cards={"f1": 5, "f2": 1})
    assert picked is not None and picked.id == "f2-01-late"
    assert [task_priority(t, {"f1": 5, "f2": 1}) for t in ready] == [5, 1]


def test_a_bug_at_priority_1_goes_before_milestone_tickets_at_2(tmp_path):
    ready = [
        _in(tmp_path, "f1-01-a", "f1"),
        _in(tmp_path, "m1-01-b", "1"),
        _in(tmp_path, "bug-01-x", "bugs", "area: factory\npriority: 1\n"),
    ]
    picked = pick_next(ready, done=set(), paused=set(), cards={"f1": 2, "m1": 2})
    assert picked is not None and picked.id == "bug-01-x"


def test_a_feature_ticket_runs_in_its_cards_place_and_no_card_is_100(tmp_path):
    """F173 D1: the card's place wins over a feature ticket's own number; a bug keeps its own."""
    ticket = _in(tmp_path, "f1-01-a", "f1", "priority: 7\n")
    assert task_priority(ticket, {"f1": 3}) == 3
    assert task_priority(_in(tmp_path, "f1-02-b", "f1"), {}) == DEFAULT_PRIORITY == 100
    assert task_priority(_in(tmp_path, "bug-01-x", "bugs", "area: factory\n"), {}) == 50
    assert task_priority(_in(tmp_path, "bug-02-y", "bugs", "area: factory\npriority: 4\n"), {}) == 4


def test_a_card_at_0_goes_before_one_at_1_whatever_its_tickets_say(tmp_path):
    """F173: F153's card was dragged first, but its tickets' `priority: 100` sent them last."""
    first = _in(tmp_path, "f9-01-first", "f9", "priority: 100\n")
    second = _in(tmp_path, "f2-01-second", "f2", "priority: 2\n")
    picked = pick_next([second, first], done=set(), paused=set(), cards={"f9": 0, "f2": 1})
    assert picked is not None and picked.id == "f9-01-first"


def test_inside_a_card_tickets_go_by_what_they_wait_for_then_id(tmp_path):
    later = _in(tmp_path, "f1-01-a", "f1", deps="[f1-02-b]")
    sooner = _in(tmp_path, "f1-02-b", "f1")
    third = _in(tmp_path, "f1-03-c", "f1", "priority: 0\n")
    picked = pick_next([later, sooner, third], done=set(), paused=set(), cards={"f1": 0})
    assert picked is not None and picked.id == "f1-02-b"
    picked = pick_next([later, third], done={"f1-02-b"}, paused=set(), cards={"f1": 0})
    assert picked is not None and picked.id == "f1-01-a"


def test_preflight_refuses_a_feature_tickets_priority_and_passes_a_bugs(repo):
    """F173 D2: the board orders the work."""
    ready = repo / ".factory" / "tasks" / "ready"
    assert preflight(_in(ready, "m1-01-a", "1", "priority: 3\n"), repo) == [FEATURE_PRIORITY]
    assert "the board orders the work" in FEATURE_PRIORITY
    assert preflight(_in(ready, "m1-02-b", "1"), repo) == []
    assert preflight(_in(ready, "bug-01-x", "bugs", "area: factory\npriority: 3\n"), repo) == []


def test_preflight_sends_a_fix_of_a_fix_to_the_lead(repo):
    """f68-08: F68's fifth developer fix ticket on one test; the check holds the F114 rule."""
    tasks = repo / ".factory" / "tasks"
    _in(tasks / "done", "f1-01-fixed", "f1", "finding: f1-C1-1\n")
    _in(tasks / "done", "f1-02-plain", "f1")

    def fix(task_id: str, at_fault: str, extra: str) -> Task:
        _in(tasks / "ready", task_id, "f1", extra)
        path = tasks / "ready" / f"{task_id}.md"
        path.write_text(
            path.read_text().replace(
                "### Context\n",
                f"### Context\nOn the merge of `.factory/tasks/done/{at_fault}.md`.\n",
            )
        )
        return parse_task(path, 150)

    assert preflight(fix("f1-03-a", "f1-01-fixed", "finding: f1-C2-1\n"), repo) == [FIX_OF_FIX]
    lead = fix("f1-04-b", "f1-01-fixed", "finding: f1-C2-2\nagent: lead\n")
    assert preflight(lead, repo) == []
    assert preflight(fix("f1-05-c", "f1-02-plain", "finding: f1-C2-3\n"), repo) == []
    assert preflight(fix("f1-06-d", "f1-01-fixed", ""), repo) == []


def test_equal_priorities_keep_milestone_then_id_order(tmp_path):
    ready = [_in(tmp_path, "f2-01-a", "f2"), _in(tmp_path, "f1-02-c", "f1")]
    ready.append(_in(tmp_path, "f1-01-b", "f1"))
    picked = pick_next(ready, done=set(), paused=set(), cards={"f1": 3, "f2": 3})
    assert picked is not None and picked.id == "f1-01-b"


def test_dependencies_and_pauses_still_come_before_priority(tmp_path):
    first = _in(tmp_path, "f2-01-a", "f2")
    waiting = _in(tmp_path, "f2-02-b", "f2", deps="[f2-01-a]")
    other = _in(tmp_path, "f1-01-c", "f1")
    cards = {"f1": 9, "f2": 1}
    picked = pick_next([waiting, other], done=set(), paused=set(), cards=cards)
    assert picked is not None and picked.id == "f1-01-c"
    picked = pick_next([first, other], done=set(), paused={"f2-01-a"}, cards=cards)
    assert picked is not None and picked.id == "f1-01-c"


CASE_CARDS = {"f15": 4, "f132": 5, "f73": 6, "f42": 6, "f26": 7, "f63": 14}


def _case(directory: Path) -> list[Task]:
    """F173 D6, the line on 2026-10-26: F15 (at 4) waits on a chain of F73, F42, F26 and F63
    tickets, while F132's (at 5) are free to run."""
    return [
        _in(directory, "f15-06-card-actions", "f15", deps="[f73-02-set-aside-button]"),
        _in(
            directory,
            "f73-02-set-aside-button",
            "f73",
            deps="[f73-01-set-aside-list, f42-01-review-page-room]",
        ),
        _in(directory, "f73-01-set-aside-list", "f73", deps="[f26-02-group-counts]"),
        _in(directory, "f42-01-review-page-room", "f42"),
        _in(directory, "f26-02-group-counts", "f26", deps="[f63-01-desk-order]"),
        _in(directory, "f63-01-desk-order", "f63"),
        _in(directory, "f132-01-one", "f132"),
        _in(directory, "f132-02-two", "f132"),
    ]


def _picks(ready: list[Task], cards: dict[str, int]) -> list[str]:
    """``pick_next`` again and again, each pick counted as merged."""
    left, done, order = list(ready), set[str](), []
    while (task := pick_next(left, done, set(), cards, pulls(ready, cards))) is not None:
        order.append(task.id)
        left.remove(task)
        done.add(task.id)
    return order


def test_what_a_higher_ticket_waits_for_runs_in_its_place(tmp_path):
    """F173 D6: F15's chain runs before F132's, the top card's ticket as soon as it can."""
    assert _picks(_case(tmp_path), CASE_CARDS) == [
        "f42-01-review-page-room",
        "f63-01-desk-order",
        "f26-02-group-counts",
        "f73-01-set-aside-list",
        "f73-02-set-aside-button",
        "f15-06-card-actions",
        "f132-01-one",
        "f132-02-two",
    ]


def test_pulls_name_the_first_waiter_and_early_for_only_when_it_is_ahead(tmp_path):
    ready = _case(tmp_path)
    by_id = {t.id: t for t in ready}
    pulled = pulls(ready, CASE_CARDS)
    assert pulled["f63-01-desk-order"] == (4, ("f", 15), "f15-06-card-actions")
    assert "f15-06-card-actions" not in pulled and "f132-01-one" not in pulled
    assert early_for(by_id["f63-01-desk-order"], CASE_CARDS, pulled) == "f15-06-card-actions"
    assert early_for(by_id["f132-01-one"], CASE_CARDS, pulled) is None
    behind = {**CASE_CARDS, "f15": 20}  # F15 behind: F73 pulls its chain, f42-01 keeps its own
    assert (
        early_for(by_id["f63-01-desk-order"], behind, pulls(ready, behind))
        == "f73-01-set-aside-list"
    )
    assert early_for(by_id["f42-01-review-page-room"], behind, pulls(ready, behind)) is None
    assert _picks(ready, behind)[:2] == ["f132-01-one", "f132-02-two"]


def test_a_ticket_nothing_ready_waits_for_keeps_its_cards_place(tmp_path):
    """A done or set-aside waiter isn't in the ready list, so it pulls nothing."""
    ready = [t for t in _case(tmp_path) if t.id != "f15-06-card-actions"]
    ready = [t for t in ready if not t.id.startswith("f73-")]
    assert pulls(ready, CASE_CARDS) == {"f63-01-desk-order": (7, ("f", 26), "f26-02-group-counts")}
    assert _picks(ready, CASE_CARDS)[:3] == [
        "f132-01-one",
        "f132-02-two",
        "f42-01-review-page-room",
    ]


def test_a_cycle_in_depends_on_doesnt_hang(tmp_path):
    ready = [
        _in(tmp_path, "f1-01-a", "f1", deps="[f1-02-b]"),
        _in(tmp_path, "f1-02-b", "f1", deps="[f1-01-a]"),
        _in(tmp_path, "f2-01-c", "f2"),
    ]
    assert set(pulls(ready, {"f1": 0, "f2": 1})) == {"f1-01-a", "f1-02-b"}
    assert _picks(ready, {"f1": 0, "f2": 1}) == ["f2-01-c"]


def test_a_pulled_chain_goes_before_another_card_at_its_waiters_place(tmp_path):
    """Ties: the waiter's key (priority, milestone order, id), then the ticket's own id."""
    ready = [
        _in(tmp_path, "f15-06-card-actions", "f15", deps="[f73-01-a]"),
        _in(tmp_path, "f73-01-a", "f73"),
        _in(tmp_path, "f171-01-b", "f171"),
    ]
    cards = {"f15": 4, "f171": 4, "f73": 6}
    assert _picks(ready, cards) == ["f73-01-a", "f15-06-card-actions", "f171-01-b"]


def test_pick_next_reads_the_pulls_it_is_given_for_a_subset(tmp_path):
    """`_next_task`'s developer pick: a lead ticket out of the subset still pulls."""
    ready = _case(tmp_path)
    subset = [t for t in ready if t.id in {"f63-01-desk-order", "f132-01-one"}]
    alone = pick_next(subset, set(), set(), CASE_CARDS)
    assert alone is not None and alone.id == "f132-01-one"
    picked = pick_next(subset, set(), set(), CASE_CARDS, pulls(ready, CASE_CARDS))
    assert picked is not None and picked.id == "f63-01-desk-order"


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
        for task in load_dir(repo / ".factory" / "tasks" / folder, 150)
    }
    # An escalated ticket never runs as written: the lead rewrites or implements it, and its
    # escalation's check-all runs while it still sits in escalated/ (f1-50).
    escalated = task_ids(repo / ".factory" / "tasks" / "escalated")
    problems = []
    for task in queued.values():
        if task.id in escalated:
            continue
        created = _created_before(task, queued)
        for problem in preflight(task, repo):
            path = problem.removeprefix("referenced path does not exist: ")
            # A tests-only ticket without `tests_only: true` fails here too: pre-flight would
            # spend an escalation on it before any attempt (f9-30).
            if path not in created:
                problems.append(f"{task.id}: {problem}")
    assert problems == []
