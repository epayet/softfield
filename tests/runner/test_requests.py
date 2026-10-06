"""The owner's requests from the dashboard (ADR 18 item 2, f5 D2): applied as the console
commands would, each finished once with its result."""

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from runner import cli, loop, metrics, requests
from runner.state import State, load_state, save_state
from tests.runner.conftest import git, write_task
from tests.runner.test_cli import in_repo  # noqa: F401 - a fixture
from tests.runner.test_owner import _milestone

NOW = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)


def _db(repo: Path) -> Path:
    return repo / "var" / "factory-metrics.sqlite"


def _ask(repo: Path, kind: str, subject: str | None = None, value: str | None = None) -> int:
    """The dashboard's write: one request row for this repo's project."""
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        return metrics.add_request(conn, project, kind, subject, value, NOW.isoformat())
    finally:
        conn.close()


def _request(repo: Path, request_id: int) -> tuple[object, object]:
    conn = metrics.open_db(_db(repo))
    try:
        row = conn.execute(
            "SELECT done, result FROM owner_requests WHERE id = ?", (request_id,)
        ).fetchone()
        return row["done"], row["result"]
    finally:
        conn.close()


def _apply(repo: Path, state: State | None = None, at: datetime = NOW) -> list[str]:
    return requests.apply_requests(repo, _db(repo), at, State() if state is None else state)


def _items(repo: Path) -> list[tuple[object, object, object, object]]:
    """The owner items: kind, subject, command, and whether they are still open."""
    conn = metrics.open_db(_db(repo))
    try:
        rows = conn.execute("SELECT * FROM owner_items ORDER BY id").fetchall()
        return [(r["kind"], r["subject"], r["command"], r["resolved"] is None) for r in rows]
    finally:
        conn.close()


def _item(repo: Path, kind: str, subject: str) -> None:
    """A Needs-you item a parked ticket raised (`at_reserve`, `at_five_hour`)."""
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        metrics.upsert_owner_item(
            conn, project, kind, subject, text="waits", command="x", created=NOW.isoformat()
        )
    finally:
        conn.close()


def _later(repo: Path, *ids: str) -> None:
    for task_id in ids:
        write_task(repo / "tasks" / "later", task_id)
    git(repo, "add", "tasks")
    git(repo, "commit", "-q", "-m", "set aside")


def test_a_signoff_request_signs_off_as_the_command_does(repo):
    _milestone(repo)
    asked = _ask(repo, "signoff", "m1")
    assert _apply(repo) == ["signoff m1: signed off m1"]
    assert git(repo, "tag").split() == ["m1-done"]
    assert git(repo, "log", "-1", "--format=%s").strip() == "M1 signed off by the owner"
    assert "Status: done." in (repo / "docs" / "milestones" / "m1.md").read_text()
    assert _request(repo, asked) == (NOW.isoformat(), "signed off m1")
    assert _apply(repo) == []  # finished once


def test_a_signoff_request_with_work_left_is_finished_with_the_commands_error(repo):
    _milestone(repo)
    write_task(repo / "tasks" / "escalated", "m1-02-photos")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "escalated")
    head = git(repo, "rev-parse", "HEAD")
    doc = (repo / "docs" / "milestones" / "m1.md").read_text()
    asked = _ask(repo, "signoff", "m1")
    error = "work is left: m1-02-photos (escalated). Finish it, or sign off with --force."
    assert _apply(repo) == [f"signoff m1: {error}"]
    assert _request(repo, asked) == (NOW.isoformat(), error)
    # Nothing changed: no commit, no tag, the doc as it was, a clean tree.
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "tag") == "" and git(repo, "status", "--porcelain") == ""
    assert (repo / "docs" / "milestones" / "m1.md").read_text() == doc
    assert _apply(repo) == []  # never retried


def test_a_signoff_request_for_a_bad_key_is_refused_before_any_file_is_read(repo):
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "signoff", "../../etc/passwd")
    [line] = _apply(repo)
    assert "must be a number or a key like f1" in line
    assert _request(repo, asked)[1] == line.split(": ", 1)[1]
    assert git(repo, "rev-parse", "HEAD") == head and git(repo, "tag") == ""


def test_a_queue_request_moves_the_ticket_and_commits_as_the_command_does(repo):
    _later(repo, "m4-12-send-recovers", "f3-01-other")
    asked = _ask(repo, "queue", "m4-12-send-recovers")
    assert _apply(repo) == ["queue m4-12-send-recovers: queued m4-12-send-recovers"]
    assert (repo / "tasks" / "ready" / "m4-12-send-recovers.md").is_file()
    assert not (repo / "tasks" / "later" / "m4-12-send-recovers.md").exists()
    assert (repo / "tasks" / "later" / "f3-01-other.md").is_file()  # only the one asked for
    assert git(repo, "log", "-1", "--format=%s").strip() == (
        "queue m4-12-send-recovers (by the owner)"
    )
    changed = git(repo, "show", "--name-only", "--no-renames", "--format=", "HEAD").split()
    assert sorted(changed) == [
        "tasks/later/m4-12-send-recovers.md",
        "tasks/ready/m4-12-send-recovers.md",
    ]
    assert git(repo, "status", "--porcelain") == ""
    assert _request(repo, asked) == (NOW.isoformat(), "queued m4-12-send-recovers")


def test_a_queue_request_for_a_missing_ticket_is_finished_with_the_error(repo):
    _later(repo, "m4-12-a")
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "queue", "m9-01-nothing")
    [line] = _apply(repo)
    error = "m9-01-nothing matches no ticket in tasks/later/. Choices: m4-12-a"
    assert line == f"queue m9-01-nothing: {error}"
    assert _request(repo, asked)[1] == line.split(": ", 1)[1]
    assert git(repo, "rev-parse", "HEAD") == head
    assert _apply(repo) == []


@pytest.mark.parametrize("switch", ["week", "five_hour"])
def test_a_reserve_request_turns_its_switch_on_for_24_hours_and_off(repo, switch):
    """ADR 22 item 4, f8 D4: the switch is kept in state.json, with the time it went on."""
    state = State()
    asked = _ask(repo, "reserve", switch, "on")
    [line] = _apply(repo, state)
    assert line.startswith(f"reserve {switch}: ") and "on until Fri 12:00" in line
    assert state.switches == {switch: NOW.isoformat()}
    assert _request(repo, asked) == (NOW.isoformat(), line.split(": ", 1)[1])
    assert loop.switch_on(state, switch, NOW + timedelta(hours=23, minutes=59))
    assert not loop.switch_on(state, switch, NOW + timedelta(hours=24))
    other = {"week": "five_hour", "five_hour": "week"}[switch]
    assert not loop.switch_on(state, other, NOW)  # one switch per window
    _ask(repo, "reserve", switch, "off")
    [line] = _apply(repo, state)
    assert line.endswith("is off") and state.switches == {}


def test_turning_a_switch_on_again_starts_its_24_hours_again(repo):
    state = State(switches={"week": (NOW - timedelta(hours=20)).isoformat()})
    _ask(repo, "reserve", "week", "on")
    _apply(repo, state)
    assert state.switches == {"week": NOW.isoformat()}


def test_an_old_5_hour_answer_is_an_unknown_request_and_sets_no_switch(repo):
    """f8-10: the reserve switches replace f5-10's Yes and No; one still open is finished."""
    asked = _ask(repo, "five_hour", value="yes")
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.find_project(conn, repo.name)
        assert project is not None
        assert requests.take_switches(conn, project, State(), NOW) == []  # not a switch now
    finally:
        conn.close()
    state = State()
    assert _apply(repo, state) == ["five_hour yes: unknown request: five_hour"]
    assert _request(repo, asked) == (NOW.isoformat(), "unknown request: five_hour")
    assert state.switches == {}


@pytest.mark.parametrize(
    ("kind", "subject", "value", "error"),
    [
        ("reserve", "month", "on", "a reserve switch is week or five_hour, not 'month'"),
        ("reserve", "week", "yes", "a reserve switch is turned on or off, not 'yes'"),
        ("reboot", "now", None, "unknown request: reboot"),
    ],
)
def test_a_request_the_runner_cant_read_is_finished_with_why(repo, kind, subject, value, error):
    asked = _ask(repo, kind, subject, value)
    state = State()
    _apply(repo, state)
    assert _request(repo, asked) == (NOW.isoformat(), error)
    assert state.switches == {}


def test_a_switch_on_for_24_hours_reads_off_and_asks_to_be_turned_on_again(repo):
    """The owner, 2026-10-04: on lasts 24 hours, then a Needs-you item asks again."""
    _ask(repo, "queue", "m4-12-none")  # the project, and a request that isn't a switch
    state = State(
        switches={"week": (NOW - timedelta(hours=24)).isoformat(), "five_hour": NOW.isoformat()}
    )
    assert not loop.switch_on(state, "week", NOW)
    lines = _apply(repo, state)
    assert "Claude's reserve: the week's switch went off after 24 hours" in lines[0]
    assert state.switches == {"five_hour": NOW.isoformat()}  # the other one stays on
    assert _items(repo) == [("reserve", "week", "uv run runner reserve week on", True)]
    _apply(repo, state)
    assert len(_items(repo)) == 1  # raised once
    _ask(repo, "reserve", "week", "on")
    _apply(repo, state)
    assert _items(repo) == [("reserve", "week", "uv run runner reserve week on", False)]


@pytest.mark.parametrize(
    ("switch", "answered"),
    [
        ("week", {("reserve", "m1-01-lead"), ("reserve", "week")}),
        ("five_hour", {("five-hour", "m1-02-lead"), ("reserve", "five_hour")}),
    ],
)
def test_turning_a_switch_on_answers_the_items_that_wait_for_it(repo, switch, answered):
    """ADR 22 item 4: each ticket's item names the switch that lets it run."""
    for kind, subject in (
        ("reserve", "m1-01-lead"),
        ("reserve", "week"),
        ("five-hour", "m1-02-lead"),
        ("reserve", "five_hour"),
    ):
        _item(repo, kind, subject)
    _ask(repo, "reserve", switch, "on")
    _apply(repo)
    resolved = {(kind, subject) for kind, subject, _, open_ in _items(repo) if not open_}
    assert resolved == answered


def test_another_projects_requests_are_left_alone(repo):
    _later(repo, "m4-12-a")
    conn = metrics.open_db(_db(repo))
    other = metrics.upsert_project(conn, "elsewhere")
    theirs = metrics.add_request(conn, other, "queue", "m4-12-a", None, NOW.isoformat())
    conn.close()
    assert _apply(repo) == []
    assert _request(repo, theirs) == (None, None)
    assert (repo / "tasks" / "later" / "m4-12-a.md").is_file()


def test_without_a_database_there_is_nothing_to_apply_and_none_is_made(repo):
    assert _apply(repo) == []
    assert not _db(repo).exists()


def test_a_wait_takes_only_the_switches_and_leaves_the_rest_for_the_pick(repo):
    """While the run sleeps for the owner's 25% it takes the switches alone: a queue or a
    sign-off commits, and waits for the pick."""
    asked = _ask(repo, "reserve", "five_hour", "on")
    _ask(repo, "queue", "m4-12-a")
    conn = metrics.open_db(_db(repo))
    project = metrics.find_project(conn, repo.name)
    assert project is not None
    state = State()
    try:
        [line] = requests.take_switches(conn, project, state, NOW)
        assert requests.take_switches(conn, project, state, NOW) == []
        assert [r["kind"] for r in metrics.open_requests(conn, project)] == ["queue"]
    finally:
        conn.close()
    assert _request(repo, asked) == (NOW.isoformat(), line.split(": ", 1)[1])
    assert loop.switch_on(state, "five_hour", NOW)


# --- `plan_message`: the owner's message to the lead (ADR 20 items 3 and 9, f6 D1) ------------


def _message(text: str, **comments: str) -> str:
    return json.dumps({"text": text, "comments": {n.lstrip("p"): c for n, c in comments.items()}})


def _queued(repo: Path) -> list[tuple[object, object, object, object]]:
    conn = metrics.open_db(_db(repo))
    try:
        rows = conn.execute("SELECT * FROM work_queue ORDER BY id").fetchall()
        return [(r["kind"], r["subject"], r["reason"], r["done"]) for r in rows]
    finally:
        conn.close()


def _thread(repo: Path, card: str) -> list[dict[str, object]]:
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.find_project(conn, repo.name)
        assert project is not None
        thread = metrics.planner_thread(conn, project, card, NOW.isoformat())
        return [dict(row) for row in metrics.planner_messages(conn, thread["id"])]
    finally:
        conn.close()


def test_two_messages_on_one_thread_make_two_planner_rows_each_with_its_reason(repo):
    """ADR 22 item 1: one open row per kind and subject, so each message has its own."""
    first = _ask(repo, "plan_message", "f7", _message("Why one queue?"))
    second = _ask(repo, "plan_message", "f7-one-queue", _message("And the switches?"))
    general = _ask(repo, "plan_message", "general", _message("An idea."))
    assert _apply(repo) == [
        "plan_message f7: queued for the lead",
        "plan_message f7-one-queue: queued for the lead",
        "plan_message general: queued for the lead",
    ]
    assert _queued(repo) == [
        ("planner", f"f7#{first}", "your message on F7", None),
        ("planner", f"f7#{second}", "your message on F7", None),
        ("planner", f"general#{general}", "your message on the general thread", None),
    ]
    assert _request(repo, first) == (NOW.isoformat(), "queued for the lead")
    assert [(m["author"], m["text"]) for m in _thread(repo, "f7")] == [
        ("owner", "Why one queue?"),
        ("owner", "And the switches?"),
    ]
    assert _apply(repo) == []  # finished once: no second row


def test_a_messages_comments_are_kept_with_it_by_point(repo):
    _ask(repo, "plan_message", "f7", _message("Agreed otherwise.", p2="Why first?"))
    _apply(repo)
    [message] = _thread(repo, "f7")
    assert json.loads(str(message["points"])) == [{"n": 2, "comment": "Why first?"}]


def test_sending_answers_on_a_thread_resolves_its_planning_item(repo):
    """ADR 20 item 9: the lead's reply waits for the owner until they answer on that thread."""
    _item(repo, "planning", "f7")
    _item(repo, "planning", "f8")
    _ask(repo, "plan_message", "f7", _message("Thanks."))
    _apply(repo)
    assert {(kind, subject, open_) for kind, subject, _, open_ in _items(repo)} == {
        ("planning", "f7", False),
        ("planning", "f8", True),
    }


@pytest.mark.parametrize(
    ("subject", "value", "error"),
    [
        ("../x", _message("Hi."), "a thread is a card's key or general, not '../x'"),
        (None, _message("Hi."), "a thread is a card's key or general, not None"),
        ("f7", "Hi.", "a message is JSON with its text and comments"),
        ("f7", _message(""), "a message has words or comments"),
    ],
)
def test_a_message_the_runner_cant_read_is_finished_with_why_and_queues_nothing(
    repo, subject, value, error
):
    asked = _ask(repo, "plan_message", subject, value)
    _apply(repo)
    assert _request(repo, asked) == (NOW.isoformat(), error)
    assert _queued(repo) == []


# --- `runner reserve` and `runner run --use-reserve` (ADR 22 item 4, f8 D4) ------------------


@pytest.fixture
def at_now(monkeypatch):
    monkeypatch.setattr(loop, "now", lambda: NOW)


def _switches(repo: Path) -> dict[str, str]:
    return load_state(repo / "var" / "runs" / "state.json").switches


def test_runner_reserve_records_the_same_as_the_request(in_repo, at_now, capsys):  # noqa: F811
    _ask(in_repo, "reserve", "week", "on")
    assert cli.main(["accept", "99"]) == 1  # any command applies the dashboard's request
    by_request = _switches(in_repo)
    (in_repo / "var" / "runs" / "state.json").unlink()
    assert cli.main(["reserve", "week", "on"]) == 0
    assert _switches(in_repo) == by_request == {"week": NOW.isoformat()}
    assert "on until Fri 12:00" in capsys.readouterr().out
    assert cli.main(["reserve", "five-hour", "on"]) == 0
    assert cli.main(["reserve", "week", "off"]) == 0
    assert _switches(in_repo) == {"five_hour": NOW.isoformat()}


def test_runner_reserve_during_a_live_run_leaves_it_to_the_run(in_repo, at_now, capsys):  # noqa: F811
    """The run is state.json's writer while it lives: it takes the switch at its next pick."""
    conn = metrics.open_db(_db(in_repo))
    project = metrics.upsert_project(conn, in_repo.name)
    beat = (NOW - timedelta(seconds=30)).isoformat()
    metrics.upsert_run(conn, project, "20261001-115900", started=beat, heartbeat=beat)
    conn.close()
    assert cli.main(["reserve", "five-hour", "on"]) == 0
    assert _switches(in_repo) == {}
    conn = metrics.open_db(_db(in_repo))
    [row] = metrics.open_requests(conn, project)
    conn.close()
    assert (row["kind"], row["subject"], row["value"]) == ("reserve", "five_hour", "on")
    assert "the run turns it on at its next pick" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("flag", "expected"),
    [
        (["--use-reserve"], {"week", "five_hour"}),
        (["--use-reserve", "week"], {"week"}),
        (["--use-reserve", "five-hour"], {"five_hour"}),
        ([], set()),
    ],
)
def test_use_reserve_turns_the_switches_on_for_24_hours(
    in_repo,  # noqa: F811
    at_now,
    monkeypatch,
    flag,
    expected,
):
    seen: list[set[str]] = []

    def run_session(cfg, *, once, dry_run, escalate):
        state = load_state(cfg.runs_dir / "state.json")
        seen.append({s for s in ("week", "five_hour") if loop.switch_on(state, s, NOW)})
        return None

    monkeypatch.setattr(cli, "run_session", run_session)
    assert cli.main(["run", *flag]) == 0
    assert seen == [expected]
    assert set(_switches(in_repo)) == expected
    assert all(on == NOW.isoformat() for on in _switches(in_repo).values())


def test_a_restart_doesnt_turn_the_switches_on_again(in_repo, at_now, monkeypatch):  # noqa: F811
    """A restart runs the same arguments: `--use-reserve` keeps its first 24 hours."""
    state_path = in_repo / "var" / "runs" / "state.json"
    save_state(State(switches={"week": (NOW - timedelta(hours=10)).isoformat()}), state_path)
    monkeypatch.setattr(cli, "run_session", lambda cfg, **kw: None)
    monkeypatch.setenv(cli.RESTARTED_ENV, "1")
    assert cli.main(["run", "--use-reserve"]) == 0
    assert load_state(state_path).switches == {"week": (NOW - timedelta(hours=10)).isoformat()}
    assert cli.RESTARTED_ENV not in os.environ


# --- at the start of every command (f5 D2) --------------------------------------------------


def test_a_request_made_while_nothing_runs_is_applied_by_the_next_command(in_repo, capsys):  # noqa: F811
    _later(in_repo, "m4-12-a", "m4-13-b")
    asked = _ask(in_repo, "queue", "m4-12-a")
    assert cli.main(["queue", "m4-13"]) == 0
    assert (in_repo / "tasks" / "ready" / "m4-12-a.md").is_file()
    assert (in_repo / "tasks" / "ready" / "m4-13-b.md").is_file()
    subjects = git(in_repo, "log", "-2", "--format=%s").splitlines()
    assert subjects == ["queue m4-13-b (by the owner)", "queue m4-12-a (by the owner)"]
    assert _request(in_repo, asked)[1] == "queued m4-12-a"
    assert "queued m4-12-a" in capsys.readouterr().out


def test_a_live_run_applies_its_own_requests_not_another_command(in_repo):  # noqa: F811
    _later(in_repo, "m4-12-a")
    asked = _ask(in_repo, "queue", "m4-12-a")
    conn = metrics.open_db(_db(in_repo))
    project = metrics.upsert_project(conn, in_repo.name)
    beat = (datetime.now(UTC) - timedelta(seconds=30)).isoformat()
    metrics.upsert_run(conn, project, "20261003-120000", started=beat, heartbeat=beat)
    conn.close()
    assert cli.main(["accept", "99"]) == 1  # any command; this one changes nothing
    assert _request(in_repo, asked) == (None, None)
    assert (in_repo / "tasks" / "later" / "m4-12-a.md").is_file()


def test_a_live_bench_doesnt_hold_the_requests_back(in_repo):  # noqa: F811
    """A bench runs beside the runner (2026-10-04) and never applies requests."""
    _later(in_repo, "m4-12-a")
    asked = _ask(in_repo, "queue", "m4-12-a")
    conn = metrics.open_db(_db(in_repo))
    project = metrics.upsert_project(conn, in_repo.name)
    beat = (datetime.now(UTC) - timedelta(seconds=30)).isoformat()
    metrics.upsert_run(
        conn, project, "bench-20261003-120000", command="bench", started=beat, heartbeat=beat
    )
    conn.close()
    cli.main(["accept", "99"])
    assert (in_repo / "tasks" / "ready" / "m4-12-a.md").is_file()
    assert _request(in_repo, asked)[1] == "queued m4-12-a"


def test_the_checks_never_apply_requests(in_repo):  # noqa: F811
    """check-all runs inside jobs and as the pre-commit hook: a commit there would land on a
    task branch, or in the middle of the owner's own."""
    _later(in_repo, "m4-12-a")
    asked = _ask(in_repo, "queue", "m4-12-a")
    cli.main(["check-layout"])
    assert _request(in_repo, asked) == (None, None)
