"""The owner's requests from the dashboard (ADR 18 item 2, f5 D2): applied as the console
commands would, each finished once with its result."""

import json
import os
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from runner import cli, dispatch, loop, metrics, milestone, planner, requests
from runner.gitops import Git, GitError
from runner.state import State, load_state, save_state
from runner.tasks import append_footer, load_dir, parse_task
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
        write_task(repo / ".softfield" / "tasks" / "later", task_id)
    git(repo, "add", ".softfield/tasks")
    git(repo, "commit", "-q", "-m", "set aside")


def test_a_signoff_request_signs_off_as_the_command_does(repo):
    _milestone(repo)
    asked = _ask(repo, "signoff", "m1")
    assert _apply(repo) == ["signoff m1: signed off m1"]
    assert git(repo, "tag").split() == ["m1-done"]
    assert git(repo, "log", "-1", "--format=%s").strip() == "M1 signed off by the owner"
    assert "Status: done." in (repo / ".softfield" / "cards" / "m1.md").read_text()
    assert _request(repo, asked) == (NOW.isoformat(), "signed off m1")
    assert _apply(repo) == []  # finished once


def test_apply_requests_clears_items_of_a_signed_off_milestone(repo):
    """F186 D3: F142's sign-off item was reopened by a late verdict and nothing closed it."""
    _milestone(repo)
    _ask(repo, "signoff", "m1")
    _apply(repo)
    _item(repo, "signoff", "m1")  # reopened after the sign-off
    _item(repo, "review-stop", "m2")  # a milestone not signed off
    _apply(repo)
    assert [(k, s, open_) for k, s, _, open_ in _items(repo)] == [
        ("signoff", "m1", False),
        ("review-stop", "m2", True),
    ]
    conn = metrics.open_db(_db(repo))
    try:
        status = conn.execute("SELECT status FROM milestones WHERE key = 'm1'").fetchone()[0]
    finally:
        conn.close()
    assert status == "done"


def test_a_signoff_request_with_work_left_is_finished_with_the_commands_error(repo):
    _milestone(repo)
    write_task(repo / ".softfield" / "tasks" / "escalated", "m1-02-photos")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "escalated")
    head = git(repo, "rev-parse", "HEAD")
    doc = (repo / ".softfield" / "cards" / "m1.md").read_text()
    asked = _ask(repo, "signoff", "m1")
    error = "work is left: m1-02-photos (escalated). Finish it, or sign off with --force."
    assert _apply(repo) == [f"signoff m1: {error}"]
    assert _request(repo, asked) == (NOW.isoformat(), error)
    # Nothing changed: no commit, no tag, the doc as it was, a clean tree.
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "tag") == "" and git(repo, "status", "--porcelain") == ""
    assert (repo / ".softfield" / "cards" / "m1.md").read_text() == doc
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
    assert (repo / ".softfield" / "tasks" / "ready" / "m4-12-send-recovers.md").is_file()
    assert not (repo / ".softfield" / "tasks" / "later" / "m4-12-send-recovers.md").exists()
    assert (
        repo / ".softfield" / "tasks" / "later" / "f3-01-other.md"
    ).is_file()  # only the one asked for
    assert git(repo, "log", "-1", "--format=%s").strip() == (
        "queue m4-12-send-recovers (by the owner)"
    )
    changed = git(repo, "show", "--name-only", "--no-renames", "--format=", "HEAD").split()
    assert sorted(changed) == [
        ".softfield/tasks/later/m4-12-send-recovers.md",
        ".softfield/tasks/ready/m4-12-send-recovers.md",
    ]
    assert git(repo, "status", "--porcelain") == ""
    assert _request(repo, asked) == (NOW.isoformat(), "queued m4-12-send-recovers")


def test_a_queue_request_for_a_missing_ticket_is_finished_with_the_error(repo):
    _later(repo, "m4-12-a")
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "queue", "m9-01-nothing")
    [line] = _apply(repo)
    error = "m9-01-nothing matches no ticket in .softfield/tasks/later/. Choices: m4-12-a"
    assert line == f"queue m9-01-nothing: {error}"
    assert _request(repo, asked)[1] == line.split(": ", 1)[1]
    assert git(repo, "rev-parse", "HEAD") == head
    assert _apply(repo) == []


# --- a blocked ticket brought back: tried again, or set aside (F106 D3) -----------------------


def _blocked(repo: Path, task_id: str, work: str | None = None) -> None:
    """A ticket the runner blocked: in blocked/ with its footer, its item open, and its work on
    ``task/<id>`` when ``work`` is given."""
    if work is not None:
        git(repo, "checkout", "-q", "-b", f"task/{task_id}")
        (repo / "work.txt").write_text(work)
        git(repo, "add", "work.txt")
        git(repo, "commit", "-q", "-m", f"wip {task_id}")
        git(repo, "checkout", "-q", "main")
    path = write_task(repo / ".softfield" / "tasks" / "blocked", task_id)
    append_footer(path, {"result": "blocked", "reason": "check-all failed"})
    git(repo, "add", ".softfield/tasks")
    git(repo, "commit", "-q", "-m", f"runner: {task_id} blocked")
    _item(repo, "blocked", task_id)


def _moved_alone(repo: Path, task_id: str, src: str, dst: str) -> None:
    changed = git(repo, "show", "--name-only", "--no-renames", "--format=", "HEAD").split()
    assert sorted(changed) == sorted(
        [f".softfield/tasks/{src}/{task_id}.md", f".softfield/tasks/{dst}/{task_id}.md"]
    )
    assert git(repo, "status", "--porcelain") == ""
    moved = (repo / ".softfield" / "tasks" / dst / f"{task_id}.md").read_text()
    assert "result: blocked" in moved and "reason: check-all failed" in moved  # footers kept


def test_a_queue_request_tries_a_blocked_ticket_again_keeping_its_failed_work(repo):
    _blocked(repo, "f9-01-lead", work="first try")
    held = git(repo, "rev-parse", "task/f9-01-lead").strip()
    asked = _ask(repo, "queue", "f9-01-lead")
    assert _apply(repo) == ["queue f9-01-lead: queued f9-01-lead"]
    assert (repo / ".softfield" / "tasks" / "ready" / "f9-01-lead.md").is_file()
    assert not (repo / ".softfield" / "tasks" / "blocked" / "f9-01-lead.md").exists()
    assert git(repo, "log", "-1", "--format=%s").strip() == "queue f9-01-lead (by the owner)"
    _moved_alone(repo, "f9-01-lead", "blocked", "ready")
    assert git(repo, "rev-parse", "blocked/f9-01-lead").strip() == held
    assert _items(repo) == [("blocked", "f9-01-lead", "x", False)]
    assert _request(repo, asked) == (NOW.isoformat(), "queued f9-01-lead")


def test_a_second_try_replaces_the_older_copy_of_the_failed_work(repo):
    _blocked(repo, "f9-01-lead", work="first try")
    git(repo, "branch", "blocked/f9-01-lead", "main")  # an older copy, from an earlier try
    held = git(repo, "rev-parse", "task/f9-01-lead").strip()
    _ask(repo, "queue", "f9-01-lead")
    assert _apply(repo) == ["queue f9-01-lead: queued f9-01-lead"]
    assert git(repo, "rev-parse", "blocked/f9-01-lead").strip() == held


def test_a_blocked_ticket_with_no_branch_is_tried_again_and_makes_none(repo):
    _blocked(repo, "f9-01-lead")
    _ask(repo, "queue", "f9-01-lead")
    assert _apply(repo) == ["queue f9-01-lead: queued f9-01-lead"]
    assert git(repo, "branch", "--list", "blocked/*") == ""


def test_a_queue_request_takes_later_first(repo):
    _later(repo, "f9-01-lead")
    _blocked(repo, "f9-01-lead-again")
    _ask(repo, "queue", "f9-01-lead")
    assert _apply(repo) == ["queue f9-01-lead: queued f9-01-lead"]
    assert (repo / ".softfield" / "tasks" / "blocked" / "f9-01-lead-again.md").is_file()
    assert _items(repo) == [("blocked", "f9-01-lead-again", "x", True)]


def test_a_set_aside_request_moves_a_blocked_ticket_to_later_alone(repo):
    _blocked(repo, "f9-01-lead", work="first try")
    _blocked(repo, "f9-02-other")
    held = git(repo, "rev-parse", "task/f9-01-lead").strip()
    asked = _ask(repo, "set_aside", "f9-01-lead")
    assert _apply(repo) == ["set_aside f9-01-lead: set aside f9-01-lead"]
    assert (repo / ".softfield" / "tasks" / "later" / "f9-01-lead.md").is_file()
    assert not (repo / ".softfield" / "tasks" / "blocked" / "f9-01-lead.md").exists()
    assert git(repo, "log", "-1", "--format=%s").strip() == "set aside f9-01-lead (by the owner)"
    _moved_alone(repo, "f9-01-lead", "blocked", "later")
    assert _items(repo) == [
        ("blocked", "f9-01-lead", "x", False),
        ("blocked", "f9-02-other", "x", True),
    ]
    assert "task/f9-01-lead" in git(repo, "branch")  # the work stays where it was
    # and is copied, for a queue from later/ that starts the lead ticket again from main
    assert git(repo, "rev-parse", "blocked/f9-01-lead").strip() == held
    assert _request(repo, asked) == (NOW.isoformat(), "set aside f9-01-lead")


@pytest.mark.parametrize(
    ("folder", "subject", "said"),
    [
        ("ready", "f9-03-ticket", "isn't in .softfield/tasks/blocked/"),
        ("done", "f9-03-ticket", "isn't in .softfield/tasks/blocked/"),
        (None, "f9-09-nothing", "matches no ticket in .softfield/tasks/blocked/"),
        (None, "", "a set_aside request names its ticket"),
        (None, None, "a set_aside request names its ticket"),
    ],
)
def test_a_set_aside_request_for_a_ticket_not_blocked_is_refused_and_moves_nothing(
    repo, folder, subject, said
):
    _blocked(repo, "f9-01-lead")
    if folder is not None:
        write_task(repo / ".softfield" / "tasks" / folder, "f9-03-ticket")
        git(repo, "add", ".softfield/tasks")
        git(repo, "commit", "-q", "-m", folder)
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "set_aside", subject)
    [line] = _apply(repo)
    assert said in line
    assert _request(repo, asked)[1] == line.split(": ", 1)[1]
    assert git(repo, "rev-parse", "HEAD") == head and git(repo, "status", "--porcelain") == ""
    assert (repo / ".softfield" / "tasks" / "blocked" / "f9-01-lead.md").is_file()
    assert _items(repo) == [("blocked", "f9-01-lead", "x", True)]


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
        (
            "reserve",
            "month",
            "on",
            "a reserve request names week, five_hour or a card, not 'month'",
        ),
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
    assert _items(repo) == [("reserve", "week", "softfield reserve week on", True)]
    _apply(repo, state)
    assert len(_items(repo)) == 1  # raised once
    _ask(repo, "reserve", "week", "on")
    _apply(repo, state)
    assert _items(repo) == [("reserve", "week", "softfield reserve week on", False)]


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
    parked = State(parked={"m1-01-lead": {"kind": "reserve"}, "m1-02-lead": {"kind": "five-hour"}})
    _ask(repo, "reserve", switch, "on")
    _apply(repo, parked)
    resolved = {(kind, subject) for kind, subject, _, open_ in _items(repo) if not open_}
    assert resolved == answered


def test_a_tickets_wait_item_goes_once_the_ticket_is_no_longer_parked(repo):
    """A ticket's reserve item stayed in Needs you a day after the ticket merged (f8-03,
    2026-10-06): an item about a ticket that no longer waits for it is answered."""
    for kind, subject in (
        ("reserve", "m1-01-lead"),
        ("five-hour", "m1-02-lead"),
        ("reserve", "m1-03-lead"),
        ("reserve", "week"),
    ):
        _item(repo, kind, subject)
    _apply(repo, State(parked={"m1-03-lead": {"kind": "reserve"}}))
    still = {(kind, subject) for kind, subject, _, open_ in _items(repo) if open_}
    assert still == {("reserve", "m1-03-lead"), ("reserve", "week")}


def test_another_projects_requests_are_left_alone(repo):
    _later(repo, "m4-12-a")
    conn = metrics.open_db(_db(repo))
    other = metrics.upsert_project(conn, "elsewhere")
    theirs = metrics.add_request(conn, other, "queue", "m4-12-a", None, NOW.isoformat())
    conn.close()
    assert _apply(repo) == []
    assert _request(repo, theirs) == (None, None)
    assert (repo / ".softfield" / "tasks" / "later" / "m4-12-a.md").is_file()


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


# --- `reserve` on a card: it may use Claude's reserve (F172 D2, D4) ----------------------------

MARKED = "f142-reserve"
MARKED_CARD = (
    "# Milestone F142: reserve\n\n> **State:** ready · **Priority:** 1 · **Area:** factory\n"
    "> Planted by the owner on 2026-10-22.\n\n## Notes\nSoon.\n"
)


def _marked_doc(repo: Path) -> str:
    return (repo / ".softfield" / "cards" / f"{MARKED}.md").read_text()


def _reserve_card(repo: Path, card: str = MARKED_CARD) -> str:
    """F142's card on main with two ready tickets, F9's with one; main's head."""
    docs = repo / ".softfield" / "cards"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / f"{MARKED}.md").write_text(card)
    (docs / "f9-other.md").write_text(card.replace("F142", "F9"))
    ready = repo / ".softfield" / "tasks" / "ready"
    ready.mkdir(parents=True, exist_ok=True)
    for task_id, key in (("f142-01-a", MARKED), ("f142-02-b", MARKED), ("f9-01-c", "f9-other")):
        text = _ticket(task_id).replace("milestone: f7", f"milestone: {key}")
        (ready / f"{task_id}.md").write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "cards")
    return git(repo, "rev-parse", "HEAD")


def test_a_reserve_request_on_a_card_marks_its_header_and_commits_it(repo):
    head = _reserve_card(repo)
    asked = _ask(repo, "reserve", "f142", "on")
    assert _apply(repo) == ["reserve f142: F142 in the fast lane"]
    assert _request(repo, asked) == (NOW.isoformat(), "F142 in the fast lane")
    doc = _marked_doc(repo)
    assert doc == MARKED_CARD.replace("**Area:** factory", "**Area:** factory · **Fast lane:** yes")
    assert milestone.card(MARKED, doc).reserve
    assert git(repo, "rev-parse", "HEAD~1") == head
    assert git(repo, "log", "-1", "--format=%s").strip() == ("F142 in the fast lane, by the owner")
    assert git(repo, "show", "--name-only", "--format=", "HEAD").split() == [
        f".softfield/cards/{MARKED}.md"
    ]
    assert git(repo, "status", "--porcelain") == ""
    _ask(repo, "reserve", "f142", "off")
    assert _apply(repo) == ["reserve f142: F142 out of the fast lane"]
    assert _marked_doc(repo) == MARKED_CARD
    assert git(repo, "log", "-1", "--format=%s").strip() == (
        "F142 out of the fast lane, by the owner"
    )


def test_taking_a_card_out_of_the_lane_removes_the_old_mark_too(repo):
    old = MARKED_CARD.replace("**Area:** factory", "**Area:** factory · **Reserve:** yes")
    _reserve_card(repo, old)
    _ask(repo, "reserve", "f142", "off")
    assert _apply(repo) == ["reserve f142: F142 out of the fast lane"]
    assert _marked_doc(repo) == MARKED_CARD


@pytest.mark.parametrize("value", ["on", "off"])
def test_a_reserve_request_on_a_card_already_so_commits_nothing(repo, value):
    card = MARKED_CARD
    if value == "on":
        card = card.replace("**Area:** factory", "**Area:** factory · **Fast lane:** yes")
    head = _reserve_card(repo, card)
    _ask(repo, "reserve", "f142", value)
    said = "is in the fast lane" if value == "on" else "is not in the fast lane"
    assert _apply(repo) == [f"reserve f142: F142 {said} already"]
    assert git(repo, "rev-parse", "HEAD") == head
    assert _marked_doc(repo) == card


def test_a_card_without_an_area_is_marked_after_its_priority(repo):
    card = MARKED_CARD.replace(" · **Area:** factory", "")
    _reserve_card(repo, card)
    _ask(repo, "reserve", "f142", "on")
    _apply(repo)
    assert _marked_doc(repo) == card.replace(
        "**Priority:** 1", "**Priority:** 1 · **Fast lane:** yes"
    )


@pytest.mark.parametrize(
    ("card", "subject", "value", "error"),
    [
        (MARKED_CARD, "f143", "on", "F143 has no card in .softfield/cards/: not marked"),
        (
            MARKED_CARD.replace("ready", "idea"),
            "f142",
            "on",
            "F142 is idea: only a planted card goes in the fast lane",
        ),
        (
            MARKED_CARD.replace("ready", "done"),
            "f142",
            "on",
            "F142 is done: only a planted card goes in the fast lane",
        ),
        (MARKED_CARD, "f142", "yes", "a card's reserve is turned on or off, not 'yes'"),
        (
            MARKED_CARD,
            "../f142",
            "on",
            "a reserve request names week, five_hour or a card, not '../f142'",
        ),
        (MARKED_CARD, None, "on", "a reserve request names week, five_hour or a card, not None"),
    ],
)
def test_a_reserve_request_the_runner_cant_apply_to_a_card_is_refused(
    repo, card, subject, value, error
):
    head = _reserve_card(repo, card)
    asked = _ask(repo, "reserve", subject, value)
    _apply(repo)
    assert _request(repo, asked) == (NOW.isoformat(), error)
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "status", "--porcelain", "--untracked-files=all") == ""


def test_marking_a_card_frees_its_tickets_parked_at_either_reserve(repo):
    """F172 D4: as a switch turned on does, for the card's tickets alone."""
    _reserve_card(repo)
    for kind, subject in (
        ("reserve", "f142-01-a"),
        ("five-hour", "f142-02-b"),
        ("reserve", "f9-01-c"),
        ("reserve", "week"),
    ):
        _item(repo, kind, subject)
    state = State(
        parked={
            "f142-01-a": {"kind": "reserve"},
            "f142-02-b": {"kind": "five-hour", "five_hour": True},
            "f9-01-c": {"kind": "reserve"},
        }
    )
    _ask(repo, "reserve", "f142", "on")
    _apply(repo, state)
    assert state.parked == {
        "f142-01-a": {"kind": "reserve", "retry": True},
        "f142-02-b": {"kind": "five-hour", "five_hour": True, "retry": True},
        "f9-01-c": {"kind": "reserve"},
    }
    resolved = {(kind, subject) for kind, subject, _, open_ in _items(repo) if not open_}
    assert resolved == {("reserve", "f142-01-a"), ("five-hour", "f142-02-b")}
    assert state.switches == {}


def test_a_card_reserve_waits_for_main_and_isnt_taken_by_a_wait(repo):
    _reserve_card(repo)
    asked = _ask(repo, "reserve", "f142", "on")
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.find_project(conn, repo.name)
        assert project is not None
        assert requests.take_switches(conn, project, State(), NOW) == []  # it commits
    finally:
        conn.close()
    git(repo, "checkout", "-q", "-b", "elsewhere")
    assert _apply(repo) == ["reserve f142: waits for the repo to be on main"]
    assert _request(repo, asked) == (None, None)


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


def _archived(repo: Path, card: str) -> bool:
    conn = metrics.open_db(_db(repo))
    try:
        row = conn.execute(
            "SELECT archived FROM planner_threads WHERE card = ?", (card,)
        ).fetchone()
        return row is not None and row["archived"] is not None
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
        ("general", _message(""), "a message has words or comments"),
    ],
)
def test_a_message_the_runner_cant_read_is_finished_with_why_and_queues_nothing(
    repo, subject, value, error
):
    asked = _ask(repo, "plan_message", subject, value)
    _apply(repo)
    assert _request(repo, asked) == (NOW.isoformat(), error)
    assert _queued(repo) == []


def test_an_empty_first_message_on_a_card_asks_the_lead_to_plan_it(repo):
    """The owner, 2026-10-15: the box says the lead reads the card too, so an empty Send on a
    card's new thread was meant as "plan it", not refused. Later, empty is refused again."""
    first = _ask(repo, "plan_message", "f7", _message("  "))
    assert _apply(repo) == ["plan_message f7: queued for the lead"]
    assert _queued(repo) == [("planner", f"f7#{first}", "your message on F7", None)]
    assert [(m["author"], m["text"]) for m in _thread(repo, "f7")] == [("owner", "Plan this card.")]
    conn = metrics.open_db(_db(repo))  # the planner job reads the same words
    try:
        assert (
            json.loads(
                conn.execute("SELECT value FROM owner_requests WHERE id = ?", (first,)).fetchone()[
                    "value"
                ]
            )["text"]
            == "Plan this card."
        )
    finally:
        conn.close()
    again = _ask(repo, "plan_message", "f7", _message(""))
    _apply(repo)
    assert _request(repo, again) == (NOW.isoformat(), "a message has words or comments")


# --- `approve_plan`, `accept_adr`, `send_back`: the owner approves (ADR 20 items 6–7) -------

CARD = "# Milestone F7: one queue\n\n> **State:** planning · **Priority:** 3\n\n## Outcome\n"
TICKET = """\
---
id: {id}
milestone: f7
depends_on: []
files:
  - coucou/thing.py
tests:
  - tests/unit/test_thing.py
---

### Goal
Make the thing work.

### Context
{context}

### Done when
Tests pass.
"""
ADR = "# ADR 23: Parallel planners\n\n- **Status:** Proposed\n- **Date:** 2026-10-06\n"


def _card(repo: Path) -> None:
    """F7's card on main, and a ticket set aside for another milestone."""
    (repo / ".softfield" / "cards").mkdir(parents=True)
    (repo / ".softfield" / "cards" / "f7-one-queue.md").write_text(CARD)
    git(repo, "add", ".softfield")
    _later(repo, "f3-09-old")


def _ticket(task_id: str, context: str = "`coucou/thing.py` has `def thing() -> int`.") -> str:
    return TICKET.format(id=task_id, context=context)


def _plan(repo: Path, files: dict[str, str], card: str = "f7", gone: tuple[str, ...] = ()) -> None:
    """The planner's drafts, committed on the card's plan branch (``gone`` removed); back on
    main."""
    git(repo, "checkout", "-q", "-b", f"plan/{card}", "main")
    for rel in gone:
        git(repo, "rm", "-q", "--", rel)
    for rel, text in files.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "drafts")
    git(repo, "checkout", "-q", "main")


def _main_unchanged(repo: Path, head: str) -> None:
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "branch", "--show-current").strip() == "main"
    assert git(repo, "status", "--porcelain", "--untracked-files=all") == ""
    assert sorted(p.name for p in (repo / ".softfield" / "tasks" / "ready").glob("*.md")) == []


def test_approving_a_plan_merges_its_drafts_queues_its_tickets_and_readies_the_card(repo):
    _card(repo)
    _plan(
        repo,
        {
            ".softfield/tasks/later/f7-01-a.md": _ticket("f7-01-a"),
            ".softfield/tasks/later/f7-02-b.md": _ticket("f7-02-b"),
            ".softfield/cards/f7-one-queue.md": CARD + "- The plan, drafted.\n",
            ".softfield/cards/f7-mockup/index.html": "<p>queue</p>\n",
        },
    )
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "approve_plan", "f7-one-queue")
    result = "approved plan/f7: queued f7-01-a, f7-02-b"
    assert _apply(repo) == [f"approve_plan f7-one-queue: {result}"]
    assert _request(repo, asked) == (NOW.isoformat(), result)
    ready = sorted(p.name for p in (repo / ".softfield" / "tasks" / "ready").glob("*.md"))
    assert ready == ["f7-01-a.md", "f7-02-b.md"]
    later = sorted(p.name for p in (repo / ".softfield" / "tasks" / "later").glob("*.md"))
    assert later == ["f3-09-old.md"]  # set aside by the owner: not this plan's to queue
    doc = (repo / ".softfield" / "cards" / "f7-one-queue.md").read_text()
    assert milestone.card("f7-one-queue", doc).state == "ready"
    assert "- The plan, drafted." in doc and "**Priority:** 3" in doc
    assert (repo / ".softfield" / "cards" / "f7-mockup" / "index.html").is_file()
    # one commit on main, by the owner's request; the branch is gone, its drafts merged
    assert git(repo, "rev-parse", "HEAD~1") == head
    assert git(repo, "log", "-1", "--format=%s").strip() == "F7 plan approved by the owner"
    assert git(repo, "status", "--porcelain") == ""
    assert git(repo, "branch", "--list", "plan/f7") == ""
    assert _apply(repo) == []  # finished once


@pytest.mark.parametrize(
    "stray", ["runner/loop.py", ".softfield/tasks/done/f7-09-sneak.md", "AGENTS.md"]
)
def test_a_plan_touching_anything_but_drafts_is_refused_and_main_is_unchanged(repo, stray):
    _card(repo)
    _plan(repo, {".softfield/tasks/later/f7-01-a.md": _ticket("f7-01-a"), stray: "x = 1\n"})
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "approve_plan", "f7")
    [line] = _apply(repo)
    _, result = _request(repo, asked)
    assert line == f"approve_plan f7: {result}"
    assert result == (
        f"plan/f7 changes {stray}, outside docs/, .softfield/cards/, .softfield/adr/"
        " and .softfield/tasks/later/: not approved"
    )
    _main_unchanged(repo, head)
    assert not (repo / ".softfield" / "tasks" / "later" / "f7-01-a.md").exists()
    assert git(repo, "branch", "--list", "plan/f7").strip() == "plan/f7"  # kept, to fix


ACCEPTED = ADR.replace("Proposed", "Accepted (by the owner, 2026-10-06)")


@pytest.mark.parametrize(
    ("on_main", "drafted", "gone"),
    [
        ({}, {".softfield/adr/23-parallel-planners.md": ACCEPTED}, ()),  # a new ADR, accepted
        (
            {".softfield/adr/23-parallel-planners.md": ADR},
            {".softfield/adr/23-parallel-planners.md": ACCEPTED},
            (),
        ),  # a Proposed one accepted
        (
            {".softfield/adr/23-parallel-planners.md": ACCEPTED},
            {".softfield/adr/23-parallel-planners.md": ACCEPTED.replace("Accepted", "Superseded")},
            (),
        ),
        (
            {".softfield/adr/23-parallel-planners.md": ACCEPTED},
            {},
            (".softfield/adr/23-parallel-planners.md",),
        ),
        (
            {},
            {
                ".softfield/cards/f7-one-queue.md": CARD.replace(
                    "> **State:** planning", "> **State:** done"
                )
            },
            (),
        ),  # signed off
    ],
)
def test_a_plan_setting_what_only_the_owner_sets_is_refused(
    repo: Path, on_main: dict[str, str], drafted: dict[str, str], gone: tuple[str, ...]
) -> None:
    """An ADR's status changes only at accept_adr, and a card is done only at its sign-off."""
    _card(repo)
    for rel, text in on_main.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "--allow-empty", "-m", "on main")
    _plan(repo, {".softfield/tasks/later/f7-01-a.md": _ticket("f7-01-a"), **drafted}, gone=gone)
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    [path] = [*drafted, *gone]
    assert _request(repo, asked)[1] == (
        f"plan/f7 changes {path}, which only the owner sets (accept_adr, signoff): not approved"
    )
    _main_unchanged(repo, head)
    assert git(repo, "branch", "--list", "plan/f7").strip() == "plan/f7"


def test_a_plan_editing_an_adr_but_not_its_status_is_approved(repo):
    _card(repo)
    (repo / ".softfield" / "adr").mkdir()
    (repo / ".softfield" / "adr" / "23-parallel-planners.md").write_text(ACCEPTED)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "adr")
    _plan(repo, {".softfield/adr/23-parallel-planners.md": ACCEPTED + "\nAs built: one planner.\n"})
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert _request(repo, asked)[1] == "approved plan/f7: queued nothing"


def test_a_plan_of_docs_alone_leaves_a_card_with_no_ticket_as_it_was(repo):
    _card(repo)
    _plan(repo, {".softfield/cards/f7-mockup/index.html": "<p>queue</p>\n"})
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert _request(repo, asked)[1] == "approved plan/f7: queued nothing"
    assert (repo / ".softfield" / "cards" / "f7-mockup" / "index.html").is_file()
    assert "**State:** planning" in (repo / ".softfield" / "cards" / "f7-one-queue.md").read_text()


def test_a_plan_of_docs_alone_readies_a_card_that_already_has_a_ticket(repo):
    _card(repo)
    _later(repo, "f7-01-a")
    _plan(repo, {".softfield/cards/f7-mockup/index.html": "<p>queue</p>\n"})
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert _request(repo, asked)[1] == "approved plan/f7: queued nothing"
    assert "**State:** ready" in (repo / ".softfield" / "cards" / "f7-one-queue.md").read_text()


def test_a_plan_with_a_symlink_is_refused(repo):
    """A link in docs/ would let a later edit reach outside the drafts."""
    _card(repo)
    git(repo, "checkout", "-q", "-b", "plan/f7", "main")
    (repo / "docs").mkdir(exist_ok=True)
    (repo / "docs" / "link.md").symlink_to("../runner/loop.py")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "drafts")
    git(repo, "checkout", "-q", "main")
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert (
        _request(repo, asked)[1] == "plan/f7 changes docs/link.md, not a plain file: not approved"
    )
    _main_unchanged(repo, head)


def test_a_plan_that_clashes_with_main_is_refused_and_main_is_unchanged(repo):
    _card(repo)
    _plan(
        repo,
        {
            ".softfield/tasks/later/f7-01-a.md": _ticket("f7-01-a"),
            ".softfield/cards/f7-one-queue.md": CARD.replace("one queue", "two queues"),
        },
    )
    (repo / ".softfield" / "cards" / "f7-one-queue.md").write_text(CARD.replace("one", "a"))
    git(repo, "commit", "-q", "-am", "the owner's edit")
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert _request(repo, asked)[1] == CLASHES
    _main_unchanged(repo, head)
    assert not (repo / ".softfield" / "tasks" / "later" / "f7-01-a.md").exists()
    assert not Path(repo, git(repo, "rev-parse", "--git-path", "SQUASH_MSG").strip()).exists()


CLASHES = "plan/f7 clashes with main: press Refresh against main on its page"
F139_MOVE = "F139: this branch's folder moves to .softfield"
DRAFTED_CARD = CARD + "- The plan, drafted.\n"


def _move(repo: Path, moves: dict[str, str], subject: str) -> None:
    for old, new in moves.items():
        (repo / new).parent.mkdir(parents=True, exist_ok=True)
        git(repo, "mv", old, new)
    git(repo, "commit", "-q", "-m", subject)


def clashing_plan(repo: Path, *, replayable: bool = True) -> None:
    """F7's plan branch as plan/f133 was on 2026-11-03: a draft commit under .factory/, then
    F139's move as one commit, while main moved the folder too, finished a ticket the branch's
    move put in ready/, and changed the card (``replayable``) or removed it. Back on main."""
    old = {
        ".factory/cards/f7-one-queue.md": CARD,
        ".factory/tasks/ready/f5-01-x.md": _ticket("f5-01-x"),
        ".factory/tasks/later/f3-09-old.md": _ticket("f3-09-old"),
    }
    for rel, text in old.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "the factory's folder, before F139")
    moved = {rel: rel.replace(".factory/", ".softfield/") for rel in old}
    git(repo, "checkout", "-q", "-b", "plan/f7")
    (repo / ".factory" / "cards" / "f7-one-queue.md").write_text(DRAFTED_CARD)
    (repo / ".factory" / "tasks" / "later" / "f7-01-a.md").write_text(_ticket("f7-01-a"))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "planner f7#1: drafts (by Claude)")
    _move(
        repo,
        {**moved, ".factory/tasks/later/f7-01-a.md": ".softfield/tasks/later/f7-01-a.md"},
        F139_MOVE,
    )
    git(repo, "checkout", "-q", "main")
    _move(repo, moved, "F139: the factory's folder moves to .softfield")
    ready = ".softfield/tasks/ready/f5-01-x.md"
    _move(repo, {ready: ready.replace("/ready/", "/done/")}, "f5-01-x done")
    card = repo / ".softfield" / "cards" / "f7-one-queue.md"
    if replayable:
        card.write_text(CARD.replace("one queue", "one queue, kept"))
        git(repo, "commit", "-q", "-am", "the owner's edit")
    else:
        git(repo, "rm", "-q", "--", str(card.relative_to(repo)))
        git(repo, "commit", "-q", "-m", "F7's card goes")


def _planner_job_starts(repo: Path) -> list[str]:
    """``loop._plan_branch``, as a planner job on F7 starts; its session report's notes."""
    report = SimpleNamespace(notes=[])
    loop._plan_branch(cast(loop.Session, SimpleNamespace(git=Git(repo), report=report)), "plan/f7")
    git(repo, "checkout", "-q", "main")
    return list(report.notes)


def test_a_clashing_plan_is_refused_before_its_files_are_listed(repo):
    """Its diff falls back to everything since it left main: thousands of files on F133."""
    clashing_plan(repo)
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert _request(repo, asked)[1] == CLASHES
    assert git(repo, "rev-parse", "HEAD") == head
    assert requests.plan_clash(repo, "f7") == CLASHES


def test_a_clashing_plan_its_planner_job_rebuilt_is_approved(repo):
    clashing_plan(repo)
    assert "rebuilt" in " ".join(_planner_job_starts(repo))
    assert requests.plan_clash(repo, "f7") is None
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert _request(repo, asked)[1] == "approved plan/f7: queued f7-01-a"
    assert (repo / ".softfield" / "tasks" / "ready" / "f7-01-a.md").is_file()
    card = (repo / ".softfield" / "cards" / "f7-one-queue.md").read_text()
    assert "one queue, kept" in card and "- The plan, drafted." in card
    assert git(repo, "ls-files", ".factory") == ""  # nothing at the old folder's paths


def test_a_note_main_merged_into_the_card_while_its_plan_was_drafted_is_kept_and_approved(repo):
    """2026-11-09: F237's note was merged into F235's card on main while F235's plan added its
    sections at the same place, the doc's end, and every Approve was refused as a clash (F210,
    F211 and F231 too). Both are kept, main's note first, and the plan is approved."""
    _card(repo)
    doc = repo / ".softfield" / "cards" / "f7-one-queue.md"
    _plan(
        repo,
        {
            ".softfield/tasks/later/f7-01-a.md": _ticket("f7-01-a"),
            ".softfield/cards/f7-one-queue.md": CARD + "\n## Decisions\n- D1 one queue.\n",
        },
    )
    doc.write_text(CARD + "\n### From F9: two queues (merged by the lead)\nWhy two?\n")
    git(repo, "commit", "-q", "-am", "F9 merged into F7 by the lead")
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert _request(repo, asked)[1] == "approved plan/f7: queued f7-01-a"
    text = doc.read_text()
    assert "<<<<<<<" not in text and "|||||||" not in text and ">>>>>>>" not in text
    assert text.index("Why two?") < text.index("- D1 one queue.")
    assert milestone.card("f7-one-queue", text).state == "ready"
    assert git(repo, "branch", "--show-current").strip() == "main"
    assert git(repo, "status", "--porcelain") == ""
    assert git(repo, "branch", "--list", "plan/f7") == ""


def test_a_card_line_both_sides_changed_still_clashes_and_leaves_the_branch_as_it_was(repo):
    _card(repo)
    doc = repo / ".softfield" / "cards" / "f7-one-queue.md"
    _plan(repo, {".softfield/cards/f7-one-queue.md": CARD.replace("one queue", "two queues")})
    tip = git(repo, "rev-parse", "plan/f7")
    doc.write_text(CARD.replace("one queue", "a queue") + "\nA note.\n")
    git(repo, "commit", "-q", "-am", "the owner's edit")
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert _request(repo, asked)[1] == CLASHES
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "rev-parse", "plan/f7") == tip
    assert git(repo, "branch", "--show-current").strip() == "main"
    assert git(repo, "status", "--porcelain") == ""


def test_a_ticket_with_a_bare_path_refuses_the_approval_with_the_problem_named(repo):
    _card(repo)
    _plan(
        repo,
        {
            ".softfield/tasks/later/f7-01-a.md": _ticket("f7-01-a", "Fix `conftest.py`."),
            ".softfield/tasks/later/f7-02-b.md": _ticket("f7-02-b"),
            ".softfield/tasks/later/f7-03-c.md": "no frontmatter\n",
        },
    )
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert _request(repo, asked)[1] == (
        "not approved: f7-01-a: referenced path does not exist: conftest.py;"
        " f7-03-c: task file must start with YAML frontmatter (---)"
    )
    _main_unchanged(repo, head)
    assert not (repo / ".softfield" / "tasks" / "later" / "f7-02-b.md").exists()  # nothing merged
    assert git(repo, "branch", "--list", "plan/f7").strip() == "plan/f7"


def test_accept_adr_merges_the_draft_and_the_plan_waits_for_it(repo):
    _card(repo)
    relies = "Build on `.softfield/adr/23-parallel-planners.md`."
    _plan(
        repo,
        {
            ".softfield/adr/23-parallel-planners.md": ADR,
            ".softfield/tasks/later/f7-01-a.md": _ticket("f7-01-a", relies),
        },
    )
    head = git(repo, "rev-parse", "HEAD")
    first = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert _request(repo, first)[1] == (
        "not approved: f7-01-a: relies on ADR 23, still Proposed: accept it first"
    )
    _main_unchanged(repo, head)

    accepted = _ask(repo, "accept_adr", "f7", "23")
    assert _apply(repo) == ["accept_adr f7: accepted .softfield/adr/23-parallel-planners.md"]
    assert _request(repo, accepted)[1] == "accepted .softfield/adr/23-parallel-planners.md"
    adr = repo / ".softfield" / "adr" / "23-parallel-planners.md"
    assert "- **Status:** Accepted (by the owner, 2026-10-01)\n" in adr.read_text()
    assert git(repo, "log", "-1", "--format=%s").strip() == "ADR 23 accepted by the owner"
    assert git(repo, "rev-parse", "HEAD~1") == head
    assert not (repo / ".softfield" / "tasks" / "later" / "f7-01-a.md").exists()  # the ADR alone
    assert git(repo, "branch", "--show-current").strip() == "main"
    assert git(repo, "status", "--porcelain") == ""

    second = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert _request(repo, second)[1] == "approved plan/f7: queued f7-01-a"
    assert (repo / ".softfield" / "tasks" / "ready" / "f7-01-a.md").is_file()
    assert "Accepted (by the owner, 2026-10-01)" in adr.read_text()


def test_a_plan_whose_adr_is_still_proposed_is_refused_and_main_is_unchanged(repo):
    _card(repo)
    _plan(repo, {".softfield/adr/23-parallel-planners.md": ADR})
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert (
        _request(repo, asked)[1]
        == "not approved: relies on ADR 23, still Proposed: accept it first"
    )
    _main_unchanged(repo, head)
    assert git(repo, "branch", "--list", "plan/f7").strip() == "plan/f7"


def test_a_plan_may_edit_an_adr_main_already_holds_as_proposed(repo):
    """F51 D3 holds for an ADR the branch drafted, not one on main the owner reviews later."""
    _card(repo)
    adr = repo / ".softfield" / "adr" / "23-parallel-planners.md"
    adr.parent.mkdir(parents=True)
    adr.write_text(ADR)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "ADR 23, for later")
    _plan(repo, {str(adr.relative_to(repo)): ADR + "\nA note from F7's plan.\n"})
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert _request(repo, asked)[1] == "approved plan/f7: queued nothing"
    assert "A note from F7's plan." in adr.read_text()


def test_accept_then_approve_in_one_pick_accepts_the_adr_and_merges_the_plan(repo):
    _card(repo)
    relies = "Build on `.softfield/adr/23-parallel-planners.md`."
    _plan(
        repo,
        {
            ".softfield/adr/23-parallel-planners.md": ADR,
            ".softfield/tasks/later/f7-01-a.md": _ticket("f7-01-a", relies),
        },
    )
    accepted = _ask(repo, "accept_adr", "f7", "23")
    approved = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert _request(repo, accepted)[1] == "accepted .softfield/adr/23-parallel-planners.md"
    assert _request(repo, approved)[1] == "approved plan/f7: queued f7-01-a"
    adr = repo / ".softfield" / "adr" / "23-parallel-planners.md"
    assert "Accepted (by the owner, 2026-10-01)" in adr.read_text()
    assert (repo / ".softfield" / "tasks" / "ready" / "f7-01-a.md").is_file()


def test_accept_adr_resolves_the_owner_items_that_ask_about_it(repo):
    _card(repo)
    _plan(repo, {".softfield/adr/23-parallel-planners.md": ADR})
    _item(repo, "adr", ".softfield/adr/23-parallel-planners.md")
    _ask(repo, "accept_adr", "f7", "23")
    _apply(repo)
    assert _items(repo)[0][3] is False


def _main_adr(repo, name: str, text: str = ADR) -> None:
    (repo / ".softfield" / "adr").mkdir(exist_ok=True)
    (repo / ".softfield" / "adr" / name).write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", name)


def test_accept_adr_takes_the_branchs_own_draft_when_main_has_that_number(repo):
    """2026-11-02: F85's Accept of its ADR 39 marked another ADR 39, first in name order."""
    _card(repo)
    _plan(
        repo,
        {
            ".softfield/adr/23-parallel-planners.md": ADR,
            ".softfield/tasks/later/f7-01-a.md": _ticket("f7-01-a", "Builds on ADR 23."),
        },
    )
    _main_adr(repo, "23-another.md")
    asked = _ask(repo, "accept_adr", "f7", "23")
    _apply(repo)
    result = _request(repo, asked)[1]
    assert result == (
        "accepted .softfield/adr/24-parallel-planners.md (number 23 was taken, so it is ADR 24)"
    )
    adr = repo / ".softfield" / "adr"
    assert "Proposed" in (adr / "23-another.md").read_text()
    assert not (adr / "23-parallel-planners.md").exists()
    moved = (adr / "24-parallel-planners.md").read_text()
    assert moved.startswith("# ADR 24:") and "Accepted (by the owner" in moved

    git(repo, "checkout", "-q", "plan/f7")
    assert "ADR 24" in (repo / ".softfield" / "tasks" / "later" / "f7-01-a.md").read_text()
    assert not (adr / "23-parallel-planners.md").exists()
    git(repo, "checkout", "-q", "main")
    second = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert _request(repo, second)[1] == "approved plan/f7: queued f7-01-a"


def test_accepting_an_adr_on_a_card_with_no_tickets_asks_its_lead_for_the_plan(repo):
    _card(repo)
    _plan(repo, {".softfield/adr/23-parallel-planners.md": ADR})
    _ask(repo, "accept_adr", "f7", "23")
    _apply(repo)
    conn = metrics.open_db(_db(repo))
    try:
        thread = conn.execute("SELECT id FROM planner_threads WHERE card = 'f7'").fetchone()
        said = [m["text"] for m in metrics.planner_messages(conn, thread["id"])]
        queued = conn.execute(
            "SELECT COUNT(*) FROM work_queue WHERE kind = 'planner' AND subject LIKE 'f7%'"
        ).fetchone()[0]
    finally:
        conn.close()
    assert any("ADR 23 is accepted" in text and "no tickets" in text for text in said)
    assert queued == 1


def test_accepting_an_adr_on_a_card_with_tickets_asks_nothing(repo):
    _card(repo)
    _plan(
        repo,
        {
            ".softfield/adr/23-parallel-planners.md": ADR,
            ".softfield/tasks/later/f7-01-a.md": _ticket("f7-01-a"),
        },
    )
    _ask(repo, "accept_adr", "f7", "23")
    _apply(repo)
    conn = metrics.open_db(_db(repo))
    try:
        found = conn.execute("SELECT id FROM planner_threads WHERE card = 'f7'").fetchone()
    finally:
        conn.close()
    assert found is None


def test_accept_adr_of_an_adr_already_on_main_accepts_it(repo):
    _card(repo)
    (repo / ".softfield" / "adr").mkdir()
    (repo / ".softfield" / "adr" / "23-parallel-planners.md").write_text(ADR)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "adr")
    asked = _ask(repo, "accept_adr", "f7", "23")
    _apply(repo)
    assert _request(repo, asked)[1] == "accepted .softfield/adr/23-parallel-planners.md"


@pytest.mark.parametrize(
    ("kind", "subject", "value", "error"),
    [
        ("approve_plan", "general", None, "the general thread has no plan to approve"),
        ("approve_plan", "f9", None, "there is no plan/f9 to approve"),
        ("approve_plan", "../x", None, "a thread is a card's key or general, not '../x'"),
        ("accept_adr", "f7", "x", "an ADR is named by its number, not 'x'"),
        ("accept_adr", "f7", "99", "ADR 99 not found in .softfield/adr/"),
        ("send_back", "f7/nothing", _message("Hi."), "F7 has no proposal nothing"),
        ("send_back", "f7", _message("Hi."), "a proposal is <thread>/<id>, not 'f7'"),
    ],
)
def test_an_approval_the_runner_cant_apply_is_finished_with_why(repo, kind, subject, value, error):
    _card(repo)
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, kind, subject, value)
    _apply(repo)
    assert _request(repo, asked) == (NOW.isoformat(), error)
    _main_unchanged(repo, head)


@pytest.mark.parametrize("kind", ["approve_plan", "accept_adr"])
def test_an_approval_waits_for_a_clean_main(repo, kind):
    _card(repo)
    _plan(repo, {".softfield/adr/23-parallel-planners.md": ADR})
    asked = _ask(repo, kind, "f7", "23")
    (repo / "coucou" / "thing.py").write_text("# the owner's edit\n")
    assert _apply(repo) == [f"{kind} f7: waits for a clean main: an approval commits on it"]
    git(repo, "checkout", "-q", "--", "coucou/thing.py")
    git(repo, "checkout", "-q", "plan/f7")
    assert _apply(repo) == [f"{kind} f7: waits for the repo to be on main"]
    assert _request(repo, asked) == (None, None)


def _proposed(repo: Path) -> None:
    """The lead's reply on F7, with its ADR proposal."""
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        thread = metrics.planner_thread(conn, project, "f7", NOW.isoformat())
        proposal = {
            "id": "adr-23",
            "kind": "adr",
            "title": "Parallel planners",
            "path": ".softfield/adr/23-parallel-planners.md",
            "key_points": [
                {"n": 1, "title": "Two at once", "text": "Beside developers.", "flag": False},
                {"n": 2, "title": "One branch", "text": "Each card's own.", "flag": False},
            ],
        }
        metrics.add_planner_message(
            conn, thread["id"], "lead", NOW.isoformat(), "My plan.", proposals=[proposal]
        )
    finally:
        conn.close()


def test_sending_a_proposal_back_becomes_a_message_to_the_lead(repo):
    _proposed(repo)
    asked = _ask(repo, "send_back", "f7/adr-23", _message("Nearly.", p2="Why not one?"))
    assert _apply(repo) == ["send_back f7/adr-23: queued for the lead"]
    assert _request(repo, asked) == (NOW.isoformat(), "queued for the lead")
    [(kind, subject, reason, done)] = _queued(repo)
    assert (kind, reason, done) == ("planner", "your message on F7", None)
    thread, request_id = planner.request_of(str(subject))
    assert thread == "f7"
    conn = metrics.open_db(_db(repo))
    try:
        message = metrics.find_request(conn, request_id)
    finally:
        conn.close()
    assert message is not None and message["kind"] == "plan_message"
    text, comments = planner.message(message["value"])
    assert comments == {}  # on the proposal's key points, not the reply's
    assert text == (
        "I sent back your proposal “Parallel planners” (adr-23).\n"
        "- On its key point 2 (One branch): Why not one?\n\nNearly."
    )
    [(_, owners)] = [
        (m["author"], m["text"]) for m in _thread(repo, "f7") if m["author"] == "owner"
    ]
    assert owners == text


# --- a `merge`: one card repeats another, closed once the owner approves (f6-12) --------------

KEPT = "# Milestone F10: one queue\n\n> **State:** idea\n\n## Notes\nOne queue for all.\n"
KEPT_PLANNED = "# Milestone F10: one queue\n\n> **State:** planning\n\n## Outcome\n- One.\n"
DUPLICATE = (
    "# Milestone F12: queue once\n\n> **State:** idea\n\n## Notes\nA single line.\n"
    "> **Status: done.**\n"
)
MERGE = {
    "id": "merge-f12",
    "kind": "merge",
    "title": "One queue, said twice",
    "path": ".softfield/cards/f12-queue-once.md",
    "into": "f10",
    "key_points": [{"n": 1, "title": "Notes", "text": "F12's notes go to F10.", "flag": False}],
}


def _duplicates(repo: Path, kept: str = KEPT, thread: str = "f12") -> str:
    """F10 and F12 on main, the lead's reply on ``thread`` proposing the merge, and F12's
    Needs-you item for that reply; main's head."""
    docs = repo / ".softfield" / "cards"
    docs.mkdir(parents=True)
    (docs / "f10-one-queue.md").write_text(kept)
    (docs / "f12-queue-once.md").write_text(DUPLICATE)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "cards")
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        found = metrics.planner_thread(conn, project, thread, NOW.isoformat())
        metrics.add_planner_message(
            conn, found["id"], "lead", NOW.isoformat(), "Same idea.", proposals=[MERGE]
        )
        metrics.upsert_owner_item(
            conn, project, planner.PLANNING, thread, text="answers", created=NOW.isoformat()
        )
    finally:
        conn.close()
    return git(repo, "rev-parse", "HEAD")


def test_a_merge_proposal_changes_nothing_before_the_owner_approves(repo):
    head = _duplicates(repo)
    assert _apply(repo) == []
    assert git(repo, "rev-parse", "HEAD") == head
    assert (repo / ".softfield" / "cards" / "f12-queue-once.md").read_text() == DUPLICATE
    assert [m["text"] for m in _thread(repo, "f12")] == ["Same idea."]


@pytest.mark.parametrize("kept", [KEPT, KEPT_PLANNED])
def test_approving_a_merge_moves_the_notes_removes_the_duplicate_and_points_its_thread(repo, kept):
    head = _duplicates(repo, kept)
    asked = _ask(repo, "approve_plan", "f12")
    result = "approved: merged F12 into F10"
    assert _apply(repo) == [f"approve_plan f12: {result}"]
    assert _request(repo, asked) == (NOW.isoformat(), result)
    # the notes, under F10's Notes with where they came from; a quoted line can't sign it off
    doc = (repo / ".softfield" / "cards" / "f10-one-queue.md").read_text()
    moved = (
        "### From F12: queue once (merged by the owner on 2026-10-01)\n"
        "A single line.\n\\> **Status: done.**\n"
    )
    assert doc.startswith(kept.rstrip("\n")) and doc.endswith(moved)
    assert "\n## Notes\n" in doc and doc.count("## Notes") == 1
    assert milestone.card("f10-one-queue", doc).state == milestone.card("f10", kept).state
    assert not (repo / ".softfield" / "cards" / "f12-queue-once.md").exists()
    # one commit by the runner: the duplicate removed, the kept card changed, F12's thread kept
    assert git(repo, "rev-parse", "HEAD~1") == head
    assert git(repo, "log", "-1", "--format=%s").strip() == "F12 merged into F10 by the owner"
    changed = git(repo, "show", "--name-status", "--no-renames", "--format=", "HEAD").split("\n")
    assert sorted(filter(None, changed)) == [
        "A\t.softfield/planning/f12-queue-once.md",
        "D\t.softfield/cards/f12-queue-once.md",
        "M\t.softfield/cards/f10-one-queue.md",
    ]
    assert git(repo, "status", "--porcelain") == ""
    # F12's thread points to F10's, and its Needs-you item is answered
    pointer = _thread(repo, "f12")[-1]
    assert pointer["author"] == "lead" and "F10" in str(pointer["text"])
    assert "/planning/f10" in str(pointer["text"])
    assert _items(repo) == [(planner.PLANNING, "f12", None, False)]
    assert _archived(repo, "f12")  # its card is gone: the pointer asks for no answer
    assert _apply(repo) == []  # finished once


def test_a_merge_proposed_on_the_kept_cards_thread_with_its_plan_goes_in_one_commit(repo):
    head = _duplicates(repo, KEPT_PLANNED, thread="f10")
    _plan(repo, {".softfield/tasks/later/f10-01-a.md": _ticket("f10-01-a")}, card="f10")
    asked = _ask(repo, "approve_plan", "f10")
    _apply(repo)
    assert _request(repo, asked)[1] == "approved plan/f10: queued f10-01-a; merged F12 into F10"
    assert git(repo, "rev-parse", "HEAD~1") == head
    assert (repo / ".softfield" / "tasks" / "ready" / "f10-01-a.md").is_file()
    doc = (repo / ".softfield" / "cards" / "f10-one-queue.md").read_text()
    assert milestone.card("f10-one-queue", doc).state == "ready" and "From F12" in doc
    assert not (repo / ".softfield" / "cards" / "f12-queue-once.md").exists()
    assert "/planning/f10" in str(_thread(repo, "f12")[-1]["text"])  # a thread made for it
    # F31 D1: its plan and its merge, all the reply proposed, are settled: the thread closes
    assert _items(repo) == [(planner.PLANNING, "f10", None, False)]
    assert _archived(repo, "f10")
    line = _thread(repo, "f10")[-1]["text"]
    assert line == f"Approved by the owner on 2026-10-01: {_request(repo, asked)[1]}"


def test_a_merge_proposed_on_the_general_thread_is_approved_there(repo):
    _duplicates(repo, thread="general")
    asked = _ask(repo, "approve_plan", "general")
    _apply(repo)
    assert _request(repo, asked)[1] == "approved: merged F12 into F10"
    assert not (repo / ".softfield" / "cards" / "f12-queue-once.md").exists()
    # F12 had no thread: nothing to export; the kept thread's line names it by its title
    assert not (repo / ".softfield" / "planning").exists()
    assert "Merged F12 here: queue once" in [m["text"] for m in _thread(repo, "f10")]


def _merged_with_summary(repo: Path) -> None:
    """F12's thread says more, then the lead's merge carries its summary (F49 D3) and is
    applied as the planner job's would be."""
    _duplicates(repo)
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        found = metrics.planner_thread(conn, project, "f12", NOW.isoformat())
        metrics.add_planner_message(conn, found["id"], "owner", NOW.isoformat(), "Is it F10?")
        summary = {**MERGE, "summary": "Asked if it was F10. Open: nothing."}
        assert requests.auto_merge(repo, conn, project, NOW, summary, "f12") is None
    finally:
        conn.close()


def test_a_merge_keeps_the_duplicates_words_then_the_leads_summary_of_its_thread(repo):
    """F49 D3, D4: F12's notes as they were, then what was said on its thread; its whole
    thread in .softfield/planning/, in the merge's commit; a line on F10's thread."""
    _merged_with_summary(repo)
    doc = (repo / ".softfield" / "cards" / "f10-one-queue.md").read_text()
    assert doc.endswith(
        "### From F12: queue once (merged by the lead on 2026-10-01)\n"
        "A single line.\n\\> **Status: done.**\n\n"
        "What was said on F12's thread:\nAsked if it was F10. Open: nothing.\n"
    )
    assert git(repo, "log", "-1", "--format=%s").strip() == "F12 merged into F10 by the lead"
    changed = git(repo, "show", "--name-only", "--format=", "HEAD").split()
    assert ".softfield/planning/f12-queue-once.md" in changed
    assert git(repo, "status", "--porcelain", "--untracked-files=all") == ""
    export = (repo / ".softfield" / "planning" / "f12-queue-once.md").read_text()
    assert export.startswith("# F12: queue once\n")
    assert "merged into F10" in export
    assert export.index("> Same idea.") < export.index("> Is it F10?")
    said = [m["text"] for m in _thread(repo, "f10") if m["author"] == "lead"]
    assert said[0] == "Merged F12 here: Asked if it was F10. Open: nothing."


def test_a_merge_whose_commit_fails_leaves_no_export(repo, monkeypatch):
    _duplicates(repo)
    head = git(repo, "rev-parse", "HEAD")

    def fails(*_: object, **__: object) -> None:
        raise GitError("no commit")

    monkeypatch.setattr(Git, "commit_all", fails)
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        with pytest.raises(GitError):
            requests.auto_merge(repo, conn, project, NOW, MERGE, "f12")
    finally:
        conn.close()
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "status", "--porcelain", "--untracked-files=all") == ""


def _with(repo: Path, rel: str, text: str) -> None:
    (repo / rel).parent.mkdir(parents=True, exist_ok=True)
    (repo / rel).write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", rel)


def _kept_gone(repo: Path) -> None:
    git(repo, "rm", "-q", ".softfield/cards/f10-one-queue.md")
    git(repo, "commit", "-q", "-m", "gone")


@pytest.mark.parametrize(
    ("before", "error"),
    [
        (
            lambda repo: _with(repo, ".softfield/tasks/later/f12-01-a.md", _ticket("f12-01-a")),
            "F12 has tickets (.softfield/tasks/later/f12-01-a.md): it can't be merged away",
        ),
        (_kept_gone, "F10 has no card in .softfield/cards/: not merged"),
        (
            lambda repo: _plan(repo, {".softfield/cards/f12-queue-once.md": KEPT}, card="f12"),
            "plan/f12 has drafts for F12, which merges into F10: send it back",
        ),
    ],
)
def test_a_merge_the_runner_cant_apply_is_refused_and_main_is_unchanged(repo, before, error):
    _duplicates(repo)
    before(repo)
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "approve_plan", "f12")
    _apply(repo)
    assert _request(repo, asked) == (NOW.isoformat(), error)
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "status", "--porcelain", "--untracked-files=all") == ""
    assert [m["text"] for m in _thread(repo, "f12")] == ["Same idea."]
    assert _items(repo)[0][3] is True


def test_approving_a_merge_whose_duplicate_is_gone_already_settles_it(repo):
    """F24, F45 and F47 (2026-10-08): merged once, their threads' Approve was refused as "has
    no card" at every press, and they stayed on Needs you."""
    _duplicates(repo)
    git(repo, "rm", "-q", ".softfield/cards/f12-queue-once.md")
    git(repo, "commit", "-q", "-m", "F12 merged into F10 by the owner")
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "approve_plan", "f12")
    _apply(repo)
    assert _request(repo, asked) == (NOW.isoformat(), "approved: F12 merged already")
    assert git(repo, "rev-parse", "HEAD") == head
    assert _items(repo) == [(planner.PLANNING, "f12", None, False)]


def _card_state(repo: Path, key: str) -> object:
    conn = metrics.open_db(_db(repo))
    try:
        row = conn.execute("SELECT state FROM milestones WHERE key = ?", (key,)).fetchone()
        return None if row is None else row["state"]
    finally:
        conn.close()


def test_a_merge_takes_the_duplicate_off_the_board_at_once(repo):
    """f6-17: the desk had F12 as a seed until the next session's sync."""
    _duplicates(repo)
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        metrics.upsert_milestone(conn, project, "f12-queue-once", state="idea")
    finally:
        conn.close()
    _ask(repo, "approve_plan", "f12")
    _apply(repo)
    assert _card_state(repo, "f12-queue-once") == "removed"


# --- `drop_seed`: the owner removes a seed they no longer want (f6-17) ------------------------

SEED_CARD = (
    "# Milestone F11: a test\n\n> **State:** idea · **Area:** factory\n\n## Notes\nA test.\n"
)


def _seeded(repo: Path, card: str = SEED_CARD) -> str:
    """F11's card on main and on the board, a thread with a pending message and a reply the
    owner hasn't answered; main's head."""
    docs = repo / ".softfield" / "cards"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "f11-test.md").write_text(card)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "a seed")
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        metrics.upsert_milestone(conn, project, "f11-test", title="a test", state="idea")
        found = metrics.planner_thread(conn, project, "f11", NOW.isoformat())
        metrics.add_planner_message(conn, found["id"], "lead", NOW.isoformat(), "Noted.")
        for thread in ("f11", "f7"):
            metrics.queue_job(conn, project, "planner", f"{thread}#1", "a message", NOW.isoformat())
            metrics.upsert_owner_item(
                conn, project, planner.PLANNING, thread, text="answers", created=NOW.isoformat()
            )
    finally:
        conn.close()
    return git(repo, "rev-parse", "HEAD")


def _seeded_with_a_ticket(repo: Path) -> None:
    _seeded(repo)
    _later(repo, "f11-01-a")


def test_dropping_a_seed_removes_its_card_in_one_commit_and_closes_its_thread(repo):
    head = _seeded(repo)
    asked = _ask(repo, "drop_seed", "f11")
    assert _apply(repo) == ["drop_seed f11: removed .softfield/cards/f11-test.md"]
    assert _request(repo, asked) == (NOW.isoformat(), "removed .softfield/cards/f11-test.md")
    assert not (repo / ".softfield" / "cards" / "f11-test.md").exists()
    assert git(repo, "rev-parse", "HEAD~1") == head
    assert git(repo, "log", "-1", "--format=%s").strip() == "F11 removed by the owner"
    changed = git(repo, "show", "--name-status", "--format=", "HEAD").split("\n")
    assert list(filter(None, changed)) == ["D\t.softfield/cards/f11-test.md"]
    assert git(repo, "status", "--porcelain") == ""
    assert [(m["author"], m["text"]) for m in _thread(repo, "f11")][-1] == (
        "lead",
        "Removed by the owner on 2026-10-01.",
    )
    # its planner row closes and its Needs-you item is answered; F7's stay open
    assert [(subject, done is None) for _, subject, _, done in _queued(repo)] == [
        ("f11#1", False),
        ("f7#1", True),
    ]
    assert [(subject, open_) for _, subject, _, open_ in _items(repo)] == [
        ("f11", False),
        ("f7", True),
    ]
    assert _card_state(repo, "f11-test") == "removed"
    assert _apply(repo) == []  # finished once


def test_dropping_a_seed_with_no_thread_makes_none(repo):
    (repo / ".softfield" / "cards").mkdir(parents=True)
    (repo / ".softfield" / "cards" / "f11-test.md").write_text(SEED_CARD)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "a seed")
    asked = _ask(repo, "drop_seed", "f11-test")
    _apply(repo)
    assert _request(repo, asked)[1] == "removed .softfield/cards/f11-test.md"
    conn = metrics.open_db(_db(repo))
    try:
        assert conn.execute("SELECT count(*) FROM planner_threads").fetchone()[0] == 0
    finally:
        conn.close()


@pytest.mark.parametrize(
    ("before", "subject", "error"),
    [
        (
            lambda repo: _seeded(repo, SEED_CARD.replace("idea", "building")),
            "f11",
            "F11 is building, not an idea: not removed",
        ),
        (
            _seeded_with_a_ticket,
            "f11",
            "F11 has tickets (.softfield/tasks/later/f11-01-a.md): not removed",
        ),
        (_seeded, "f13", "F13 has no card in .softfield/cards/: not removed"),
        (_seeded, "general", "the general thread is not a seed: not removed"),
        (_seeded, "../x", "a thread is a card's key or general, not '../x'"),
    ],
)
def test_a_drop_the_runner_cant_apply_is_refused_and_main_is_unchanged(
    repo, before, subject, error
):
    before(repo)
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "drop_seed", subject)
    _apply(repo)
    assert _request(repo, asked) == (NOW.isoformat(), error)
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "status", "--porcelain", "--untracked-files=all") == ""
    assert (repo / ".softfield" / "cards" / "f11-test.md").is_file()
    assert [m["text"] for m in _thread(repo, "f11")] == ["Noted."]
    assert all(done is None for *_, done in _queued(repo))
    assert _card_state(repo, "f11-test") == "idea"


def test_a_drop_waits_for_main(repo):
    _seeded(repo)
    git(repo, "checkout", "-q", "-b", "elsewhere")
    asked = _ask(repo, "drop_seed", "f11")
    assert _apply(repo) == ["drop_seed f11: waits for the repo to be on main"]
    assert _request(repo, asked) == (None, None)


def test_sending_a_merge_back_works_as_for_any_proposal(repo):
    head = _duplicates(repo)
    asked = _ask(repo, "send_back", "f12/merge-f12", _message("Keep F12.", p1="Not the same."))
    assert _apply(repo) == ["send_back f12/merge-f12: queued for the lead"]
    assert _request(repo, asked)[1] == "queued for the lead"
    owners = [m["text"] for m in _thread(repo, "f12") if m["author"] == "owner"]
    assert owners == [
        "I sent back your proposal “One queue, said twice” (merge-f12).\n"
        "- On its key point 1 (Notes): Not the same.\n\nKeep F12."
    ]
    assert git(repo, "rev-parse", "HEAD") == head
    assert (repo / ".softfield" / "cards" / "f12-queue-once.md").is_file()


# --- `priority`: the owner reorders the work from the dashboard (f6-18) ------------------------


def _two_ready(repo: Path) -> str:
    """m1-01-a and m1-02-b ready, both at the default priority, each with its row; main's
    head."""
    for task_id in ("m1-01-a", "m1-02-b"):
        write_task(repo / ".softfield" / "tasks" / "ready", task_id)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "two ready")
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        for task_id in ("m1-01-a", "m1-02-b"):
            text = (repo / ".softfield" / "tasks" / "ready" / f"{task_id}.md").read_text()
            metrics.upsert_ticket(conn, project, task_id, state="ready", body=text)
    finally:
        conn.close()
    return git(repo, "rev-parse", "HEAD")


def _pick_order(repo: Path) -> list[str]:
    """The ready tickets in the order `dispatch.plan` runs them, as the run builds them."""
    ready = load_dir(repo / ".softfield" / "tasks" / "ready", 400)
    tickets = loop._dispatch_tickets(repo, ready, set(), set(), {}, NOW)
    return [line.pick.subject for line in dispatch.plan([], tickets, dispatch.Windows(), NOW)]


def _body(repo: Path, task_id: str) -> object:
    conn = metrics.open_db(_db(repo))
    try:
        row = conn.execute("SELECT body FROM tickets WHERE ticket = ?", (task_id,)).fetchone()
        return row["body"]
    finally:
        conn.close()


BUG_A, BUG_B = "bug-01-a", "bug-02-b"


def _two_bugs(repo: Path) -> str:
    """bug-01-a and bug-02-b ready, both at a bug's default priority, each with its row;
    main's head."""
    ready = repo / ".softfield" / "tasks" / "ready"
    for task_id in (BUG_A, BUG_B):
        path = write_task(ready, task_id)
        path.write_text(
            path.read_text().replace("milestone: 1\n", "milestone: bugs\narea: factory\n")
        )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "two bugs")
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        for task_id in (BUG_A, BUG_B):
            text = (ready / f"{task_id}.md").read_text()
            metrics.upsert_ticket(conn, project, task_id, state="ready", body=text)
    finally:
        conn.close()
    return git(repo, "rev-parse", "HEAD")


def test_a_priority_request_sets_a_ready_bugs_priority_in_one_commit_and_the_pick_follows(
    repo,
):
    head = _two_bugs(repo)
    assert _pick_order(repo) == [BUG_A, BUG_B]
    asked = _ask(repo, "priority", BUG_B, "4")
    assert _apply(repo) == [f"priority {BUG_B}: priority of {BUG_B} set to 4"]
    assert _request(repo, asked) == (NOW.isoformat(), f"priority of {BUG_B} set to 4")
    path = repo / ".softfield" / "tasks" / "ready" / f"{BUG_B}.md"
    assert parse_task(path, 400).priority == 4
    assert path.read_text().count("priority:") == 1
    assert _pick_order(repo) == [BUG_B, BUG_A]
    # one commit of that one file, by the owner's request; a clean tree
    assert git(repo, "rev-parse", "HEAD~1") == head
    assert git(repo, "log", "-1", "--format=%s").strip() == (
        f"{BUG_B}: priority 50 → 4, by the owner"
    )
    changed = git(repo, "show", "--name-only", "--format=", "HEAD").split()
    assert changed == [f".softfield/tasks/ready/{BUG_B}.md"]
    assert git(repo, "status", "--porcelain") == ""
    # the dashboard's row has the new text at once; the other ticket's is as it was
    assert "priority: 4" in str(_body(repo, BUG_B))
    assert "priority:" not in str(_body(repo, BUG_A))
    assert _apply(repo) == []  # finished once


def test_a_priority_request_replaces_a_set_aside_bugs_own_priority(repo):
    (repo / ".softfield" / "tasks" / "later").mkdir(parents=True)
    text = TICKET.format(id=BUG_A, context="x").replace(
        "milestone: f7\n", "milestone: bugs\narea: factory\npriority: 7\n"
    )
    assert "priority: 7" in text
    (repo / ".softfield" / "tasks" / "later" / f"{BUG_A}.md").write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "set aside")
    _ask(repo, "priority", BUG_A, "2")
    assert _apply(repo) == [f"priority {BUG_A}: priority of {BUG_A} set to 2"]
    after = (repo / ".softfield" / "tasks" / "later" / f"{BUG_A}.md").read_text()
    assert after == text.replace("priority: 7", "priority: 2")
    assert git(repo, "log", "-1", "--format=%s").strip() == f"{BUG_A}: priority 7 → 2, by the owner"


def test_a_priority_request_on_a_feature_ticket_is_refused_for_its_cards_place(repo):
    """F173 D3: a feature ticket runs in its card's place; main is unchanged."""
    head = _two_ready(repo)
    asked = _ask(repo, "priority", "m1-02-b", "4")
    assert _apply(repo) == [f"priority m1-02-b: {requests.CARD_PLACE}"]
    assert _request(repo, asked) == (
        NOW.isoformat(),
        "a ticket runs in its card's place: move the card on the board",
    )
    assert git(repo, "rev-parse", "HEAD") == head
    assert "priority:" not in (repo / ".softfield" / "tasks" / "ready" / "m1-02-b.md").read_text()


def _priority_of(repo: Path, key: str) -> object:
    conn = metrics.open_db(_db(repo))
    try:
        row = conn.execute("SELECT priority FROM milestones WHERE key = ?", (key,)).fetchone()
        return None if row is None else row["priority"]
    finally:
        conn.close()


def test_a_priority_request_on_a_card_sets_its_headers_priority(repo):
    _card(repo)
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "priority", "f7", "1")
    assert _apply(repo) == ["priority f7: priority of F7 set to 1"]
    assert _request(repo, asked)[1] == "priority of F7 set to 1"
    doc = (repo / ".softfield" / "cards" / "f7-one-queue.md").read_text()
    assert doc == CARD.replace("**Priority:** 3", "**Priority:** 1")
    assert milestone.card("f7-one-queue", doc) == milestone.Card("planning", 1, "factory")
    assert git(repo, "rev-parse", "HEAD~1") == head
    assert git(repo, "log", "-1", "--format=%s").strip() == "F7: priority 3 → 1, by the owner"
    changed = git(repo, "show", "--name-only", "--format=", "HEAD").split()
    assert changed == [".softfield/cards/f7-one-queue.md"]
    assert git(repo, "status", "--porcelain") == ""
    assert _priority_of(repo, "f7-one-queue") == 1  # the board's row, at once


@pytest.mark.parametrize(
    ("card", "header"),
    [
        (SEED_CARD, "> **State:** idea · **Priority:** 0 · **Area:** factory\n"),
        (SEED_CARD.replace(" · **Area:** factory", ""), "> **State:** idea · **Priority:** 0\n"),
        ("# Milestone F11: a test\n\n## Notes\nA test.\n", "> **Priority:** 0\n"),
    ],
)
def test_a_card_without_a_priority_gets_one_in_its_header(repo, card, header):
    _seeded(repo, card)
    _ask(repo, "priority", "f11-test", "0")
    assert _apply(repo) == ["priority f11-test: priority of F11 set to 0"]
    doc = (repo / ".softfield" / "cards" / "f11-test.md").read_text()
    assert header in doc and doc.endswith("## Notes\nA test.\n")
    assert milestone.card("f11-test", doc).priority == 0
    assert git(repo, "log", "-1", "--format=%s").strip() == "F11: priority 100 → 0, by the owner"


def _done_ticket(repo: Path) -> None:
    _two_ready(repo)
    write_task(repo / ".softfield" / "tasks" / "done", "m1-00-old")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "done")


def _done_card(repo: Path) -> None:
    _two_ready(repo)
    _seeded(repo, SEED_CARD.replace("idea", "done"))


@pytest.mark.parametrize(
    ("before", "subject", "value", "error"),
    [
        (
            _done_ticket,
            "m1-00-old",
            "1",
            "m1-00-old is in .softfield/tasks/done/: its priority stays",
        ),
        (_two_ready, "m1-01-a", "1", "m1-01-a is running: its priority stays"),
        (_done_card, "f11", "1", "F11 is done: its priority stays"),
        (_two_ready, "m1-02-b", "-1", "a priority is a whole number from 0, not '-1'"),
        (_two_ready, "m1-02-b", "1.5", "a priority is a whole number from 0, not '1.5'"),
        (_two_ready, "m1-02-b", "x", "a priority is a whole number from 0, not 'x'"),
        (_two_ready, "m1-02-b", None, "a priority is a whole number from 0, not None"),
        (
            _two_ready,
            "m1-02-b",
            "1",
            "a ticket runs in its card's place: move the card on the board",
        ),
        (
            _two_ready,
            "m1-02",
            "1",
            "m1-02 is no ticket in .softfield/tasks/ready/ or .softfield/tasks/later/",
        ),
        (_two_ready, "f13", "1", "F13 has no card in .softfield/cards/: its priority stays"),
        (_two_ready, "general", "1", "the general thread has no priority"),
        (_two_ready, "../x", "1", "a thread is a card's key or general, not '../x'"),
        (_two_ready, None, "1", "a priority request names a ticket or a card"),
    ],
)
def test_a_priority_the_runner_cant_apply_is_refused_and_main_is_unchanged(
    repo, before, subject, value, error
):
    before(repo)
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "priority", subject, value)
    _apply(repo, State(in_flight={"ticket": "m1-01-a"}))
    assert _request(repo, asked) == (NOW.isoformat(), error)
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "status", "--porcelain", "--untracked-files=all") == ""


def test_a_priority_already_set_changes_nothing(repo):
    head = _two_bugs(repo)
    _ask(repo, "priority", BUG_B, "50")
    assert _apply(repo) == [f"priority {BUG_B}: priority of {BUG_B} is 50 already"]
    assert git(repo, "rev-parse", "HEAD") == head


def test_a_priority_waits_for_main(repo):
    _two_ready(repo)
    git(repo, "checkout", "-q", "-b", "elsewhere")
    asked = _ask(repo, "priority", "m1-02-b", "4")
    assert _apply(repo) == ["priority m1-02-b: waits for the repo to be on main"]
    assert _request(repo, asked) == (None, None)


# --- `reorder`: the board's whole order, sent once (F15 D3, D5, D10) ---------------------------

BUG = "bug-07-queue-order"


def _board(repo: Path, cards: dict[str, object], bug: bool = False) -> str:
    """Each card on main with its priority and one ready ticket (or its state alone, for one
    not open), with a ready bug ticket when asked; main's head."""
    docs = repo / ".softfield" / "cards"
    docs.mkdir(parents=True, exist_ok=True)
    ready = repo / ".softfield" / "tasks" / "ready"
    ready.mkdir(parents=True, exist_ok=True)
    for key, priority in cards.items():
        header = f"**State:** ready · **Priority:** {priority}"
        if isinstance(priority, str):
            header = f"**State:** {priority}"
        else:
            ticket = _ticket(f"{key}-01-a").replace("milestone: f7", f"milestone: {key}")
            (ready / f"{key}-01-a.md").write_text(ticket)
        (docs / f"{key}-card.md").write_text(
            f"# Milestone {key.upper()}: a card\n\n> {header}\n\n## Outcome\n"
        )
    if bug:
        text = _ticket(BUG).replace("milestone: f7", "milestone: bugs\narea: factory")
        (ready / f"{BUG}.md").write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "the board")
    return git(repo, "rev-parse", "HEAD")


def _card_priorities(repo: Path) -> dict[str, int]:
    docs = sorted((repo / ".softfield" / "cards").glob("*-card.md"))
    return {p.stem.split("-")[0]: milestone.card(p.stem, p.read_text()).priority for p in docs}


def _changed(repo: Path) -> list[str]:
    return sorted(git(repo, "show", "--name-only", "--format=", "HEAD").split())


def test_a_reorder_sets_the_cards_priorities_in_one_commit_and_the_pick_follows(repo):
    head = _board(repo, {"f7": 100, "f8": 100, "f9": 2})
    assert _pick_order(repo) == ["f9-01-a", "f7-01-a", "f8-01-a"]
    asked = _ask(repo, "reorder", None, '["f8", "f9", "f7"]')
    assert _apply(repo) == ["reorder: reordered: 1 card changed"]
    assert _request(repo, asked) == (NOW.isoformat(), "reordered: 1 card changed")
    assert _pick_order(repo) == ["f8-01-a", "f9-01-a", "f7-01-a"]
    # one commit by the runner, of the one card whose number had to change; a clean tree
    assert git(repo, "rev-parse", "HEAD~1") == head
    assert git(repo, "log", "-1", "--format=%s").strip() == "the board's order, by the owner"
    assert git(repo, "log", "-1", "--format=%an").strip() == "Softfield runner"
    assert _changed(repo) == [".softfield/cards/f8-card.md"]
    assert _card_priorities(repo) == {"f7": 100, "f8": 0, "f9": 2}
    assert git(repo, "status", "--porcelain") == ""
    assert _priority_of(repo, "f8-card") == 0  # the board's row, at once
    assert _apply(repo) == []  # finished once


def test_a_reorder_to_the_order_the_cards_have_changes_nothing(repo):
    head = _board(repo, {"f7": 100, "f8": 100, "f9": 2}, bug=True)
    asked = _ask(repo, "reorder", None, json.dumps(["f9", BUG, "f7", "f8"]))
    assert _apply(repo) == ["reorder: reordered: 0 cards changed"]
    assert _request(repo, asked)[1] == "reordered: 0 cards changed"
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "status", "--porcelain") == ""


def test_a_reorder_sets_a_bug_tickets_priority_and_a_cards_tickets_follow_the_card(repo):
    """F173: a feature ticket's own number, left from before, doesn't beat its card's place."""
    _board(repo, {"f7": 3, "f8": 5}, bug=True)
    own = repo / ".softfield" / "tasks" / "ready" / "f8-01-a.md"
    own.write_text(own.read_text().replace("depends_on", "priority: 1\ndepends_on"))
    git(repo, "commit", "-q", "-am", "its own priority")
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        text = (repo / ".softfield" / "tasks" / "ready" / f"{BUG}.md").read_text()
        metrics.upsert_ticket(conn, project, BUG, state="ready", body=text)
    finally:
        conn.close()
    assert _pick_order(repo) == ["f7-01-a", "f8-01-a", BUG]
    _ask(repo, "reorder", None, json.dumps([BUG, "f7", "f8"]))
    assert _apply(repo) == ["reorder: reordered: 1 card changed"]
    assert _changed(repo) == [f".softfield/tasks/ready/{BUG}.md"]
    assert parse_task(repo / ".softfield" / "tasks" / "ready" / f"{BUG}.md", 400).priority == 0
    assert "priority: 0" in str(_body(repo, BUG))  # the dashboard's row, at once
    # the ticket's file is not touched; its card's place orders it
    assert parse_task(own, 400).priority == 1
    assert _pick_order(repo) == [BUG, "f7-01-a", "f8-01-a"]


def test_a_reorder_puts_an_unlisted_card_last_and_names_what_it_skipped(repo):
    _board(repo, {"f7": 100, "f8": 100, "f9": 2, "f11": "done"})
    done = (repo / ".softfield" / "cards" / "f11-card.md").read_text()
    value = json.dumps(["f8", "f11", "general", "f13", "../x", "f7"])
    _ask(repo, "reorder", None, value)
    result = "reordered: 2 cards changed, skipped F11, general, F13, ../x"
    assert _apply(repo) == [f"reorder: {result}"]
    assert _pick_order(repo) == ["f8-01-a", "f7-01-a", "f9-01-a"]
    assert (repo / ".softfield" / "cards" / "f11-card.md").read_text() == done
    assert len(_changed(repo)) == 2
    assert git(repo, "status", "--porcelain") == ""


def test_a_reorder_renumbers_when_there_is_no_room(repo):
    _board(repo, {"f7": 0, "f8": 0, "f9": 1})
    _ask(repo, "reorder", None, '["f9", "f8", "f7"]')
    assert _apply(repo) == ["reorder: reordered: 2 cards changed"]
    assert _pick_order(repo) == ["f9-01-a", "f8-01-a", "f7-01-a"]


def test_a_reorder_skips_the_running_bug_ticket(repo):
    head = _board(repo, {"f7": 3}, bug=True)
    _ask(repo, "reorder", None, json.dumps([BUG, "f7"]))
    lines = _apply(repo, State(in_flight={"ticket": BUG}))
    assert lines == [f"reorder: reordered: 0 cards changed, skipped {BUG}"]
    assert git(repo, "rev-parse", "HEAD") == head


def test_a_later_reorder_replaces_an_earlier_one_still_open(repo):
    head = _board(repo, {"f7": 100, "f8": 100, "f9": 2})
    first = _ask(repo, "reorder", None, '["f7", "f8", "f9"]')
    second = _ask(repo, "reorder", None, '["f8", "f9", "f7"]')
    assert _apply(repo) == [
        "reorder: replaced by a later order",
        "reorder: reordered: 1 card changed",
    ]
    assert _request(repo, first) == (NOW.isoformat(), "replaced by a later order")
    assert _request(repo, second)[1] == "reordered: 1 card changed"
    assert _pick_order(repo) == ["f8-01-a", "f9-01-a", "f7-01-a"]
    assert git(repo, "rev-parse", "HEAD~1") == head  # one commit, the later order's


_REORDER_VALUE = "a reorder is a JSON list of card keys and bug ticket ids, first in line first"


@pytest.mark.parametrize(
    ("value", "error"),
    [
        (None, _REORDER_VALUE),
        ("f8, f9", _REORDER_VALUE),
        ('{"f8": 1}', _REORDER_VALUE),
        ('"f8"', _REORDER_VALUE),
        ('["f8", 9]', _REORDER_VALUE),
        ('["f8", ["f9"]]', _REORDER_VALUE),
        ('["f8", "f9", "f8"]', "a reorder names each card once: f8 is there twice"),
    ],
)
def test_a_reorder_the_runner_cant_read_is_refused_and_main_is_unchanged(repo, value, error):
    head = _board(repo, {"f7": 100, "f8": 100, "f9": 2})
    asked = _ask(repo, "reorder", None, value)
    assert _apply(repo) == [f"reorder: {error}"]
    assert _request(repo, asked) == (NOW.isoformat(), error)
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "status", "--porcelain", "--untracked-files=all") == ""
    assert _card_priorities(repo) == {"f7": 100, "f8": 100, "f9": 2}


def test_a_reorder_waits_for_main(repo):
    _board(repo, {"f7": 100, "f8": 100, "f9": 2})
    git(repo, "checkout", "-q", "-b", "elsewhere")
    asked = _ask(repo, "reorder", None, '["f8", "f9", "f7"]')
    assert _apply(repo) == ["reorder: waits for the repo to be on main"]
    assert _request(repo, asked) == (None, None)
    assert _card_priorities(repo) == {"f7": 100, "f8": 100, "f9": 2}


# --- pause and resume (ADR 22 item 5, f5-18) --------------------------------------------------


def _pauses(repo: Path) -> list[tuple[object, object]]:
    """The runner's pause usage events: since, and until (None while it holds)."""
    conn = metrics.open_db(_db(repo))
    try:
        rows = conn.execute("SELECT * FROM usage_events WHERE kind = 'pause' ORDER BY id")
        return [(r["at"], r["resets_at"]) for r in rows]
    finally:
        conn.close()


def test_a_pause_stored_in_utc_answers_in_local_time(repo, paris):
    state = State()
    _ask(repo, "pause")
    _apply(repo, state, datetime(2026, 10, 29, 8, 0, tzinfo=UTC))
    _ask(repo, "pause")
    again = datetime(2026, 10, 29, 8, 5, tzinfo=UTC)
    assert _apply(repo, state, again) == ["pause: already paused, since 09:00"]
    assert state.owner_pause == "2026-10-29T08:00:00+00:00"


def test_a_pause_request_holds_the_runner_until_a_resume_request(repo):
    state = State()
    paused = _ask(repo, "pause")
    assert _apply(repo, state) == ["pause: paused: the runner finishes its job, then holds"]
    assert state.owner_pause == NOW.isoformat() and state.paused_until is None
    assert _request(repo, paused) == (
        NOW.isoformat(),
        "paused: the runner finishes its job, then holds",
    )
    # Paused again: still since the first, which is when the line stopped.
    _ask(repo, "pause")
    later = NOW + timedelta(minutes=5)
    assert _apply(repo, state, later) == ["pause: already paused, since 12:00"]
    assert state.owner_pause == NOW.isoformat()
    assert _pauses(repo) == [(NOW.isoformat(), None)]  # open: "Stopped for you" while it holds
    resumed = _ask(repo, "resume")
    end = NOW + timedelta(minutes=20)
    assert _apply(repo, state, end) == ["resume: resumed"]
    assert state.owner_pause is None
    assert _request(repo, resumed) == (end.isoformat(), "resumed")
    assert _pauses(repo) == [(NOW.isoformat(), end.isoformat())]
    _ask(repo, "resume")
    assert _apply(repo, state, end) == ["resume: not paused"]
    assert _pauses(repo) == [(NOW.isoformat(), end.isoformat())]


def test_a_pause_outlives_the_state_files_reload(repo):
    """A restart reads state.json again: the pause is in it, so the runner stays paused."""
    path = repo / ".softfield" / "var" / "runs" / "state.json"
    state = load_state(path)
    _ask(repo, "pause")
    _apply(repo, state)
    save_state(state, path)
    assert load_state(path).owner_pause == NOW.isoformat()


def test_the_pause_and_resume_requests_are_taken_during_a_wait(repo):
    """`take_switches`: a wait applies a resume as it does a switch; the rest waits for the
    pick, which may commit."""
    state = State(owner_pause=NOW.isoformat())
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        metrics.add_request(conn, project, "queue", "m4-12", None, NOW.isoformat())
        metrics.add_request(conn, project, "resume", None, None, NOW.isoformat())
        assert requests.take_switches(conn, project, state, NOW) == ["resume: resumed"]
        assert state.owner_pause is None
        assert [r["kind"] for r in metrics.open_requests(conn, project)] == ["queue"]
    finally:
        conn.close()


# --- the owner's words a request refused, until they dismiss them (F31 D9) -------------------

BAD_AREA = json.dumps({"title": "Ducks", "thoughts": "Rubber ones.", "area": "garden"})


def _row(repo: Path, request_id: int) -> sqlite3.Row:
    conn = metrics.open_db(_db(repo))
    try:
        row = metrics.find_request(conn, request_id)
        assert row is not None
        return row
    finally:
        conn.close()


def test_a_refused_plant_is_dismissed_once_and_keeps_its_words(repo):
    planted = _ask(repo, "plant", None, BAD_AREA)
    _apply(repo)
    row = _row(repo, planted)
    assert requests.refused(row)
    assert requests.owners_words(row) == requests.Words("Ducks", "Rubber ones.")
    later = NOW + timedelta(minutes=5)
    dismissed = _ask(repo, "dismiss", str(planted))
    assert _apply(repo, at=later) == [f"dismiss {planted}: dismissed request {planted}"]
    assert _request(repo, dismissed) == (later.isoformat(), f"dismissed request {planted}")
    row = _row(repo, planted)
    assert row["dismissed"] == later.isoformat()
    assert row["value"] == BAD_AREA and not requests.refused(row)  # its words stay
    _ask(repo, "dismiss", str(planted))
    assert _apply(repo) == [f"dismiss {planted}: request {planted} is dismissed already"]


@pytest.mark.parametrize(
    ("kind", "subject", "value", "result", "error"),
    [
        # worked: nothing to dismiss
        ("plan_message", "f7", _message("Go."), "queued for the lead", "wasn't refused"),
        ("plant", None, BAD_AREA, "planted .softfield/cards/f12-ducks.md", "wasn't refused"),
        # not done yet
        ("plant", None, BAD_AREA, None, "wasn't refused"),
        # refused, but no words of the owner's: they show elsewhere
        ("approve_plan", "f7", None, "there is no plan/f7 to approve", "carries no words"),
        ("pause", None, None, "already paused, since 12:00", "carries no words"),
        ("plant", "general/seed-1", None, "the general thread has no proposal", "no words"),
    ],
)
def test_dismiss_refuses_a_request_not_refused_or_without_words(
    repo, kind, subject, value, result, error
):
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        target = metrics.add_request(conn, project, kind, subject, value, NOW.isoformat())
        if result is not None:
            metrics.finish_request(conn, target, NOW.isoformat(), result)
    finally:
        conn.close()
    if result is None:  # off main, the plant waits: the dismiss alone is applied
        git(repo, "checkout", "-q", "-b", "elsewhere")
    asked = _ask(repo, "dismiss", str(target))
    _apply(repo)
    done, said = _request(repo, asked)
    assert done == NOW.isoformat() and error in str(said)
    assert _row(repo, target)["dismissed"] is None


@pytest.mark.parametrize("subject", [None, "", "x", "12a", "99", "1" * 40])
def test_dismiss_names_a_request_by_its_id(repo, subject):
    asked = _ask(repo, "dismiss", subject)
    _apply(repo)
    done, said = _request(repo, asked)
    assert done == NOW.isoformat() and "request" in str(said)
    assert not str(said).startswith("dismissed")


def test_another_projects_refused_request_isnt_dismissed(repo):
    conn = metrics.open_db(_db(repo))
    try:
        other = metrics.upsert_project(conn, "elsewhere")
        target = metrics.add_request(conn, other, "plant", None, BAD_AREA, NOW.isoformat())
        metrics.finish_request(conn, target, NOW.isoformat(), "an idea's area is …")
    finally:
        conn.close()
    asked = _ask(repo, "dismiss", str(target))
    _apply(repo)
    assert _request(repo, asked)[1] == f"there is no request {target}"
    assert _row(repo, target)["dismissed"] is None


@pytest.mark.parametrize(
    ("kind", "subject", "value", "words"),
    [
        ("plant", None, BAD_AREA, ("Ducks", "Rubber ones.")),
        ("plant", None, '{"title": "  Ducks  "}', ("Ducks", "")),
        # read leniently: words the runner couldn't read are still the owner's
        ("plant", None, "Ducks, rubber ones", ("", "Ducks, rubber ones")),
        ("plant", None, '{"title": ["Ducks"]}', ("", '{"title": ["Ducks"]}')),
        ("plan_message", "f7", _message("Go.", p2="Shorter."), ("", "Go.\n\nOn point 2: Shorter.")),
        ("send_back", "f7/adr-23", _message("", p1="No."), ("", "On point 1: No.")),
        ("plan_message", "f7", "not json", ("", "not json")),
        # no words
        ("plant", "general/seed-1", None, None),
        ("plant", None, '{"title": " ", "thoughts": ""}', None),
        ("plan_message", "f7", None, None),
        ("approve_plan", "f7", None, None),
    ],
)
def test_the_owners_words_a_request_carries(kind, subject, value, words):
    row = {"kind": kind, "subject": subject, "value": value}
    found = requests.owners_words(row)
    assert (None if found is None else (found.title, found.text)) == words


@pytest.mark.parametrize(
    ("kind", "done", "result", "dismissed", "refused"),
    [
        ("plant", True, "an idea's area is factory or product, not 'garden'", None, True),
        ("plant", True, "planted .softfield/cards/f12-ducks.md", None, False),
        ("plant", True, "planted .softfield/cards/f12-ducks.md, queued for the lead", None, False),
        ("plant", None, None, None, False),
        ("plant", True, "ducks is a card already: f3-ducks", NOW.isoformat(), False),
        ("plant", True, "cancelled by you", None, False),  # F14: their own cancel, no refusal
        ("plan_message", True, "cancelled by you", None, False),
        ("plan_message", True, "queued for the lead", None, False),
        ("plan_message", True, "a thread is a card's key or general, not 'x'", None, True),
        ("send_back", True, "F7 has no proposal adr-23", None, True),
        ("send_back", True, "queued for the lead", None, False),
        ("approve_plan", True, "there is no plan/f7 to approve", None, False),
    ],
)
def test_refused_means_done_without_its_kinds_worked_result(kind, done, result, dismissed, refused):
    row = {
        "kind": kind,
        "subject": "f7/adr-23" if kind == "send_back" else None,
        "value": BAD_AREA if kind == "plant" else _message("Go."),
        "done": done and NOW.isoformat(),
        "result": result,
        "dismissed": dismissed,
    }
    assert requests.refused(row) is refused


# --- a taken name never refuses a note (F48 D1), and `again` is the desk's alone (D2) --------

DUCKS_CARD = (
    "# Milestone F3: Rubber ducks\n\n> **State:** ready · **Priority:** 2 · **Area:** factory\n\n"
    "## Notes\nYellow ones.\nFor Mum.\n\\> not a sign-off\n\n## Outcome\n- A duck on the key.\n"
)
SAME_DUCKS = "Yellow  ones.\n\nFor Mum.\n> not a sign-off"  # as the owner typed them again


def _ducks(repo: Path) -> str:
    """F3's card on main, planned since its note was planted; main's head."""
    (repo / ".softfield" / "cards").mkdir(parents=True)
    (repo / ".softfield" / "cards" / "f3-rubber-ducks.md").write_text(DUCKS_CARD)
    toml = repo / ".softfield" / "project.toml"  # a factory project: its notes take `f` keys
    toml.write_text('[project]\narea = "factory"\n\n' + toml.read_text())
    git(repo, "add", ".softfield")
    git(repo, "commit", "-q", "-m", "f3")
    return git(repo, "rev-parse", "HEAD")


def _idea(title: str, thoughts: str = "", **more: object) -> str:
    return json.dumps({"title": title, "thoughts": thoughts, **more})


@pytest.mark.parametrize(
    ("project", "value", "stem"),
    [
        ("", {"text": "Blue ducks"}, "m1-blue-ducks"),
        ('[project]\narea = "factory"\n', {"text": "Blue ducks"}, "f1-blue-ducks"),
        ('[project]\narea = "garden"\n', {"text": "Blue ducks"}, "m1-blue-ducks"),
        (
            '[project]\narea = "factory"\n',
            {"text": "Blue ducks", "area": "product"},
            "m1-blue-ducks",
        ),
        ("", {"text": "Blue ducks", "area": "factory"}, "f1-blue-ducks"),
    ],
)
def test_a_note_without_an_area_takes_its_projects_area(repo, project, value, stem):
    toml = repo / ".softfield" / "project.toml"
    toml.write_text(project + "\n" + toml.read_text())
    _ask(repo, "plant", None, json.dumps(value))
    assert _apply(repo) == [f"plant: planted .softfield/cards/{stem}.md"]


def test_a_note_whose_slug_a_card_has_with_other_words_plants_a_second_card(repo):
    """Two notes that only start alike: each its own card, `-2` then `-3`, asked about too."""
    _ducks(repo)
    second = _ask(repo, "plant", None, _idea("Rubber ducks", "Blue ones this time."))
    third = _ask(repo, "plant", None, _idea("Rubber ducks", "And a red one?", ask=True))
    _apply(repo)
    assert _request(repo, second)[1] == "planted .softfield/cards/f4-rubber-ducks-2.md"
    assert _request(repo, third)[1] == (
        "planted .softfield/cards/f5-rubber-ducks-3.md, queued for the lead"
    )
    assert not requests.refused(_row(repo, second)) and not requests.refused(_row(repo, third))
    milestones = repo / ".softfield" / "cards"
    assert (milestones / "f3-rubber-ducks.md").read_text() == DUCKS_CARD  # the taken card stays
    assert (
        (milestones / "f4-rubber-ducks-2.md")
        .read_text()
        .endswith("## Notes\nBlue ones this time.\n")
    )
    assert (milestones / "f5-rubber-ducks-3.md").read_text().endswith("## Notes\nAnd a red one?\n")
    assert [m["text"] for m in _thread(repo, "f5")] == ["Rubber ducks\n\nAnd a red one?"]
    assert git(repo, "status", "--porcelain", "--untracked-files=all") == ""


@pytest.mark.parametrize(
    ("value", "stem"),
    [
        (_idea("Rubber ducks", SAME_DUCKS, ask=True), "f3-rubber-ducks"),
        (_idea("Rubber ducks"), "f3-rubber-ducks"),  # a title alone, and the card holds it
        (_idea("Rubber ducks", "Blue ones this time."), "f4-rubber-ducks-2"),  # the second card's
    ],
)
def test_the_same_words_again_are_planted_already_and_write_nothing(repo, value, stem):
    """A retried note that was planted in the meantime: its card is named, nothing is written,
    no message is sent, and the result is a worked one, so it never lands on the desk."""
    _ducks(repo)
    _ask(repo, "plant", None, _idea("Rubber ducks", "Blue ones this time."))
    _apply(repo)
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "plant", None, value)
    assert _apply(repo) == [f"plant: planted already: .softfield/cards/{stem}.md"]
    assert _request(repo, asked) == (
        NOW.isoformat(),
        f"planted already: .softfield/cards/{stem}.md",
    )
    assert not requests.refused(_row(repo, asked))
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "status", "--porcelain", "--untracked-files=all") == ""
    assert sorted(p.name for p in (repo / ".softfield" / "cards").glob("*.md")) == [
        "f3-rubber-ducks.md",
        "f4-rubber-ducks-2.md",
    ]
    assert _queued(repo) == []


def test_a_one_box_note_cut_for_its_heading_is_planted_already_under_another_title(repo):
    """F31 D7: the lead names the card, so the cut heading is gone from it; the note's words
    under Notes still say it is the same note."""
    note = "The didnt go through cards try again " + "and again " * 8 + "until they are dismissed."
    _ducks(repo)
    _ask(repo, "plant", None, json.dumps({"text": note}))
    [line] = _apply(repo)
    rel = line.removeprefix("plant: planted ")
    doc = (repo / rel).read_text()
    title = doc.splitlines()[0]
    assert title.endswith("…")
    (repo / rel).write_text(doc.replace(title, "# Milestone F4: Try again plants a note, once"))
    git(repo, "commit", "-q", "-am", "the lead names the card")
    asked = _ask(repo, "plant", None, json.dumps({"text": note, "again": "1"}))
    _apply(repo)
    assert _request(repo, asked)[1] == f"planted already: {rel}"


def test_the_runner_reads_nothing_from_again(repo):
    """F48 D2: the retried request's id rides in the value for the desk; a plant and a message
    carrying it are applied as any other."""
    _ducks(repo)
    planted = _ask(repo, "plant", None, _idea("Parallel planners", again="7"))
    said = _ask(repo, "plan_message", "f3", json.dumps({"text": "Go.", "again": "8"}))
    _apply(repo)
    assert _request(repo, planted)[1] == "planted .softfield/cards/f4-parallel-planners.md"
    assert _request(repo, said)[1] == "queued for the lead"
    assert [m["text"] for m in _thread(repo, "f3")] == ["Go."]


# --- a `replan` edits its running milestone's ready tickets (f6-13) ----------------------------

BUILDING = CARD.replace("planning", "building")
REPLAN = {
    "id": "replan-1",
    "kind": "replan",
    "title": "Redirect F7",
    "path": None,
    "key_points": [{"n": 1, "title": "Less", "text": "f7-01-a does less.", "flag": False}],
}
LESS = _ticket("f7-01-a").replace("Make the thing work.", "Make less of the thing work.")
LATER_ON = NOW + timedelta(minutes=30)


def _running(repo: Path, kind: str = "replan") -> str:
    """F7 building on main with f7-01-a and f7-02-b ready, and f5-01-x of another milestone;
    the lead's reply on F7 proposing a ``kind``; main's head."""
    docs = repo / ".softfield" / "cards"
    docs.mkdir(parents=True)
    (docs / "f7-one-queue.md").write_text(BUILDING)
    (repo / ".softfield" / "tasks" / "ready").mkdir(parents=True, exist_ok=True)
    for task_id in ("f7-01-a", "f7-02-b", "f5-01-x"):
        (repo / ".softfield" / "tasks" / "ready" / f"{task_id}.md").write_text(_ticket(task_id))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "F7 running")
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        thread = metrics.planner_thread(conn, project, "f7", NOW.isoformat())
        proposal = {**REPLAN, "kind": kind}
        metrics.add_planner_message(
            conn, thread["id"], "lead", NOW.isoformat(), "Redirect it.", proposals=[proposal]
        )
    finally:
        conn.close()
    return git(repo, "rev-parse", "HEAD")


def _paused(repo: Path) -> State:
    state = State()
    _ask(repo, "pause")
    _apply(repo, state)
    return state


def _ready(repo: Path) -> dict[str, str]:
    return {
        p.stem: p.read_text()
        for p in sorted((repo / ".softfield" / "tasks" / "ready").glob("*.md"))
    }


def test_approving_a_replan_changes_its_ready_tickets_on_main_and_lifts_the_pause(repo):
    head = _running(repo)
    _plan(
        repo,
        {
            ".softfield/tasks/ready/f7-01-a.md": LESS,
            ".softfield/tasks/ready/f7-04-d.md": _ticket("f7-04-d"),
            ".softfield/tasks/later/f7-03-c.md": _ticket("f7-03-c"),
        },
    )
    state = _paused(repo)
    asked = _ask(repo, "approve_plan", "f7")
    result = "approved plan/f7: queued f7-03-c, f7-04-d; changed f7-01-a; resumed"
    assert _apply(repo, state, LATER_ON) == [f"approve_plan f7: {result}"]
    assert _request(repo, asked) == (LATER_ON.isoformat(), result)
    ready = _ready(repo)
    assert sorted(ready) == ["f5-01-x", "f7-01-a", "f7-02-b", "f7-03-c", "f7-04-d"]
    assert ready["f7-01-a"] == LESS
    # the card keeps building: a replan redirects it, it doesn't start it again
    doc = (repo / ".softfield" / "cards" / "f7-one-queue.md").read_text()
    assert milestone.card("f7-one-queue", doc).state == "building"
    assert git(repo, "rev-parse", "HEAD~1") == head
    assert git(repo, "log", "-1", "--format=%s").strip() == "F7 plan approved by the owner"
    assert git(repo, "status", "--porcelain") == ""
    assert git(repo, "branch", "--list", "plan/f7") == ""
    # the owner's pause is lifted, its hold ended at the approval
    assert state.owner_pause is None
    assert _pauses(repo) == [(NOW.isoformat(), LATER_ON.isoformat())]


def test_a_replan_approved_without_a_pause_still_applies(repo):
    _running(repo)
    _plan(repo, {".softfield/tasks/ready/f7-01-a.md": LESS})
    state = State()
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo, state)
    assert _request(repo, asked)[1] == "approved plan/f7: queued nothing; changed f7-01-a"
    assert _ready(repo)["f7-01-a"] == LESS
    assert state.owner_pause is None and _pauses(repo) == []


def test_a_plan_behind_a_change_main_also_made_is_approved(repo):
    """F139's folder move, on main and on a plan branch that hadn't caught up: it isn't the plan's,
    so it isn't refused as outside the drafts, and the approval changes only the plan's files."""
    _running(repo)
    (repo / "runner.py").write_text("in old/\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "code")
    _plan(repo, {".softfield/tasks/ready/f7-01-a.md": LESS})
    for branch in ("plan/f7", "main"):
        git(repo, "checkout", "-q", branch)
        (repo / "runner.py").write_text("in new/\n")
        git(repo, "commit", "-q", "-am", "the move")
    head = git(repo, "rev-parse", "HEAD").strip()
    state = State()
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo, state)
    assert _request(repo, asked)[1] == "approved plan/f7: queued nothing; changed f7-01-a"
    assert _ready(repo)["f7-01-a"] == LESS
    assert git(repo, "diff", "--name-only", head, "HEAD", "--", "runner.py") == ""


def test_a_plan_on_a_file_main_renamed_is_approved_at_the_new_name(repo):
    """The merge carries the plan's edit over to the new name, which the branch doesn't have."""
    _running(repo)
    lines = "".join(f"line {n}\n" for n in range(40))
    (repo / "docs").mkdir(exist_ok=True)
    (repo / "docs" / "old.md").write_text(lines)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "a doc")
    _plan(repo, {"docs/old.md": f"{lines}the plan's line\n"})
    git(repo, "mv", "docs/old.md", "docs/new.md")
    git(repo, "commit", "-q", "-m", "main renames it")
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo, State())
    assert _request(repo, asked)[1] == "approved plan/f7: queued nothing"
    assert (repo / "docs" / "new.md").read_text().endswith("the plan's line\n")


def test_a_replan_sets_a_ready_ticket_aside_in_later(repo):
    _running(repo)
    _plan(
        repo,
        {".softfield/tasks/later/f7-02-b.md": _ticket("f7-02-b")},
        gone=(".softfield/tasks/ready/f7-02-b.md",),
    )
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert _request(repo, asked)[1] == "approved plan/f7: queued nothing; set aside f7-02-b"
    assert sorted(_ready(repo)) == ["f5-01-x", "f7-01-a"]
    assert (repo / ".softfield" / "tasks" / "later" / "f7-02-b.md").is_file()


def _replan_refused(repo: Path, head: str, state: State, asked: int) -> str:
    """Main as it was, the ready tickets untouched, the pause still held; the result."""
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "branch", "--show-current").strip() == "main"
    assert git(repo, "status", "--porcelain", "--untracked-files=all") == ""
    assert _ready(repo) == {t: _ticket(t) for t in ("f5-01-x", "f7-01-a", "f7-02-b")}
    assert state.owner_pause == NOW.isoformat()
    assert git(repo, "branch", "--list", "plan/f7").strip() == "plan/f7"  # kept, to fix
    return str(_request(repo, asked)[1])


@pytest.mark.parametrize(
    ("files", "gone", "kind", "error"),
    [
        (
            {".softfield/tasks/ready/f5-01-x.md": LESS},
            (),
            "replan",
            "plan/f7 changes .softfield/tasks/ready/f5-01-x.md, another milestone's ticket:"
            " not approved",
        ),
        (
            {".softfield/tasks/ready/f7-01-a.md": LESS},
            (),
            "replan",
            "plan/f7 changes .softfield/tasks/ready/f7-01-a.md, the running ticket: not approved",
        ),
        (
            {".softfield/tasks/later/f7-01-a.md": _ticket("f7-01-a")},
            (".softfield/tasks/ready/f7-01-a.md",),
            "replan",
            "plan/f7 changes .softfield/tasks/ready/f7-01-a.md, the running ticket: not approved",
        ),
        (
            {},
            (".softfield/tasks/ready/f7-02-b.md",),
            "replan",
            "plan/f7 changes .softfield/tasks/ready/f7-02-b.md,"
            " a ready ticket removed, not set aside in .softfield/tasks/later/: not approved",
        ),
        (
            {".softfield/tasks/ready/f7-02-b.md": LESS},
            (),
            "plan",
            "plan/f7 changes .softfield/tasks/ready/f7-02-b.md,"
            " a ready ticket only a replan changes: not approved",
        ),
        (
            {".softfield/tasks/done/f7-00-z.md": LESS},
            (),
            "replan",
            "plan/f7 changes .softfield/tasks/done/f7-00-z.md, outside docs/, .softfield/cards/,"
            " .softfield/adr/ and .softfield/tasks/later/: not approved",
        ),
    ],
)
def test_a_replan_reaching_past_its_milestones_waiting_tickets_is_refused(
    repo, files, gone, kind, error
):
    head = _running(repo, kind)
    _plan(repo, files, gone=gone)
    state = _paused(repo)
    state.in_flight = {"kind": "local", "ticket": "f7-01-a", "branch": "task/f7-01-a"}
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo, state, LATER_ON)
    assert _replan_refused(repo, head, state, asked) == error


def test_a_changed_ticket_failing_pre_flight_refuses_the_replan(repo):
    head = _running(repo)
    _plan(
        repo,
        {
            ".softfield/tasks/ready/f7-01-a.md": _ticket("f7-01-a", "Fix `conftest.py`."),
            ".softfield/tasks/later/f7-03-c.md": _ticket("f7-03-c"),
        },
    )
    state = _paused(repo)
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo, state, LATER_ON)
    assert _replan_refused(repo, head, state, asked) == (
        "not approved: f7-01-a: referenced path does not exist: conftest.py"
    )
    assert not (repo / ".softfield" / "tasks" / "later" / "f7-03-c.md").exists()


# --- a replan brings back its card's blocked tickets (ADR 29 item 3, f106-05) ----------------

BLOCKED_C = ".softfield/tasks/blocked/f7-03-c.md"
REWORKED = _ticket("f7-03-c").replace("Make the thing work.", "Make the thing work, smaller.")


def _blocked_too(repo: Path, kind: str = "replan") -> str:
    """F7 running (``_running``, the lead proposing a ``kind``), with f7-03-c and f5-02-y
    blocked, their items open; main's head."""
    _running(repo, kind)
    for task_id in ("f7-03-c", "f5-02-y"):
        path = repo / ".softfield" / "tasks" / "blocked" / f"{task_id}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_ticket(task_id))
        append_footer(path, {"result": "blocked", "reason": "check-all failed"})
        _item(repo, "blocked", task_id)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "runner: blocked")
    return git(repo, "rev-parse", "HEAD")


@pytest.mark.parametrize("gone", [(), (BLOCKED_C,)])
def test_approving_a_replan_brings_a_reworked_blocked_ticket_back_to_ready(repo, gone):
    """The planner writes the reworked ticket in ready/; the approval removes the blocked copy
    (or applies the branch's removal), keeping its footers on the ticket."""
    _blocked_too(repo)
    _plan(repo, {".softfield/tasks/ready/f7-03-c.md": REWORKED}, gone=gone)
    state = _paused(repo)
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo, state, LATER_ON)
    assert _request(repo, asked)[1] == "approved plan/f7: queued f7-03-c; resumed"
    back = _ready(repo)["f7-03-c"]
    assert back.startswith(REWORKED.rstrip("\n"))
    assert "result: blocked" in back and "reason: check-all failed" in back  # its old footers
    assert not (repo / BLOCKED_C).exists()
    assert (repo / ".softfield" / "tasks" / "blocked" / "f5-02-y.md").is_file()
    assert git(repo, "status", "--porcelain", "--untracked-files=all") == ""
    assert _items(repo) == [
        ("blocked", "f7-03-c", "x", False),
        ("blocked", "f5-02-y", "x", True),
    ]
    assert state.owner_pause is None


def _tried_again(repo: Path) -> None:
    """The owner's Try again on f7-03-c, after the replan's branch was drafted: its blocked copy
    moved to ready/ on main."""
    ready = repo / ".softfield" / "tasks" / "ready" / "f7-03-c.md"
    git(repo, "mv", BLOCKED_C, str(ready.relative_to(repo)))
    git(repo, "commit", "-q", "-m", "Try again f7-03-c")


@pytest.mark.parametrize("place", ["ready", "later"])
def test_a_replan_replaces_the_ticket_try_again_put_back(repo, place):
    _blocked_too(repo)
    _plan(repo, {f".softfield/tasks/{place}/f7-03-c.md": REWORKED})
    _tried_again(repo)
    state = _paused(repo)
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo, state, LATER_ON)
    result = _request(repo, asked)[1]
    assert str(result).startswith("approved plan/f7")
    assert "f7-03-c: the lead's fix replaced the ticket Try again put back" in str(result)
    later = repo / ".softfield" / "tasks" / "later" / "f7-03-c.md"
    text = _ready(repo).get("f7-03-c") if place == "ready" else later.read_text()
    assert text is not None and text.startswith(REWORKED.rstrip("\n"))
    assert text.count("result: blocked") == 1
    assert (place == "later") == ("f7-03-c" not in _ready(repo))
    assert later.exists() == (place == "later")
    assert git(repo, "status", "--porcelain", "--untracked-files=all") == ""


def test_a_replan_cannot_replace_the_running_ticket_try_again_put_back(repo):
    _blocked_too(repo)
    _plan(repo, {".softfield/tasks/ready/f7-03-c.md": REWORKED})
    _tried_again(repo)
    head = git(repo, "rev-parse", "HEAD")
    state = _paused(repo)
    state.in_flight = {"ticket": "f7-03-c"}
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo, state, LATER_ON)
    assert _request(repo, asked)[1] == CLASHES  # a clash `_settle_clash` won't take
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "status", "--porcelain", "--untracked-files=all") == ""


def test_a_blocked_ticket_brought_back_keeps_its_failed_work(repo):
    """Its ``task/<id>`` copied to ``blocked/<id>``, as a Try again does: the reworked lead
    ticket starts again from main."""
    _blocked_too(repo)
    git(repo, "checkout", "-q", "-b", "task/f7-03-c")
    (repo / "work.txt").write_text("first try")
    git(repo, "add", "work.txt")
    git(repo, "commit", "-q", "-m", "wip f7-03-c")
    git(repo, "checkout", "-q", "main")
    held = git(repo, "rev-parse", "task/f7-03-c").strip()
    _plan(repo, {".softfield/tasks/ready/f7-03-c.md": REWORKED})
    state = _paused(repo)
    _ask(repo, "approve_plan", "f7")
    _apply(repo, state, LATER_ON)
    assert "f7-03-c" in _ready(repo)
    assert git(repo, "rev-parse", "blocked/f7-03-c").strip() == held


def test_approving_a_replan_sets_a_blocked_ticket_aside_in_later(repo):
    _blocked_too(repo)
    _plan(repo, {".softfield/tasks/later/f7-03-c.md": REWORKED})
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert _request(repo, asked)[1] == "approved plan/f7: queued nothing; set aside f7-03-c"
    aside = (repo / ".softfield" / "tasks" / "later" / "f7-03-c.md").read_text()
    assert aside.startswith(REWORKED.rstrip("\n")) and "result: blocked" in aside
    assert "f7-03-c" not in _ready(repo)
    assert not (repo / BLOCKED_C).exists()
    assert _items(repo)[0] == ("blocked", "f7-03-c", "x", False)


def _blocked_kept(repo: Path, head: str, state: State, asked: int) -> str:
    """``_replan_refused``, the blocked tickets and their items as they were too."""
    for task_id in ("f7-03-c", "f5-02-y"):
        assert (repo / ".softfield" / "tasks" / "blocked" / f"{task_id}.md").is_file()
    assert _items(repo) == [("blocked", "f7-03-c", "x", True), ("blocked", "f5-02-y", "x", True)]
    return _replan_refused(repo, head, state, asked)


@pytest.mark.parametrize(
    ("files", "gone", "kind", "error"),
    [
        (
            {".softfield/tasks/later/f5-02-y.md": _ticket("f5-02-y")},
            (".softfield/tasks/blocked/f5-02-y.md",),
            "replan",
            "plan/f7 changes .softfield/tasks/blocked/f5-02-y.md, another card's blocked ticket:"
            " not approved",
        ),
        (
            {},
            (BLOCKED_C,),
            "replan",
            f"plan/f7 changes {BLOCKED_C}, a blocked ticket removed and put nowhere: not approved",
        ),
        (
            {BLOCKED_C: REWORKED},
            (),
            "replan",
            f"plan/f7 changes {BLOCKED_C}, a blocked ticket edited but left in"
            " .softfield/tasks/blocked/: not approved",
        ),
        (
            {".softfield/tasks/later/f7-03-c.md": REWORKED},
            (BLOCKED_C,),
            "plan",
            f"plan/f7 changes {BLOCKED_C}, a blocked ticket only a replan brings back:"
            " not approved",
        ),
    ],
)
def test_a_replan_reaching_past_its_cards_blocked_tickets_is_refused(
    repo, files, gone, kind, error
):
    head = _blocked_too(repo, kind)
    _plan(repo, files, gone=gone)
    state = _paused(repo)
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo, state, LATER_ON)
    assert _blocked_kept(repo, head, state, asked) == error


def test_a_reworked_blocked_ticket_failing_pre_flight_refuses_the_replan(repo):
    head = _blocked_too(repo)
    _plan(repo, {".softfield/tasks/ready/f7-03-c.md": _ticket("f7-03-c", "Fix `conftest.py`.")})
    state = _paused(repo)
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo, state, LATER_ON)
    assert _blocked_kept(repo, head, state, asked) == (
        "not approved: f7-03-c: referenced path does not exist: conftest.py"
    )


# --- `runner reserve` and `runner run --use-reserve` (ADR 22 item 4, f8 D4) ------------------


@pytest.fixture
def at_now(monkeypatch):
    monkeypatch.setattr(loop, "now", lambda: NOW)


def _switches(repo: Path) -> dict[str, str]:
    return load_state(repo / ".softfield" / "var" / "runs" / "state.json").switches


def test_runner_reserve_records_the_same_as_the_request(in_repo, at_now, capsys):  # noqa: F811
    _ask(in_repo, "reserve", "week", "on")
    assert cli.main(["accept", "99"]) == 1  # any command applies the dashboard's request
    by_request = _switches(in_repo)
    (in_repo / ".softfield" / "var" / "runs" / "state.json").unlink()
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
    assert cli.main(["run", "--here", *flag]) == 0
    assert seen == [expected]
    assert set(_switches(in_repo)) == expected
    assert all(on == NOW.isoformat() for on in _switches(in_repo).values())


def test_a_restart_doesnt_turn_the_switches_on_again(in_repo, at_now, monkeypatch):  # noqa: F811
    """A restart runs the same arguments: `--use-reserve` keeps its first 24 hours."""
    state_path = in_repo / ".softfield" / "var" / "runs" / "state.json"
    save_state(State(switches={"week": (NOW - timedelta(hours=10)).isoformat()}), state_path)
    monkeypatch.setattr(cli, "run_session", lambda cfg, **kw: None)
    monkeypatch.setenv(cli.RESTARTED_ENV, "1")
    assert cli.main(["run", "--here", "--use-reserve"]) == 0
    assert load_state(state_path).switches == {"week": (NOW - timedelta(hours=10)).isoformat()}
    assert cli.RESTARTED_ENV not in os.environ


# --- at the start of every command (f5 D2) --------------------------------------------------


def test_a_request_made_while_nothing_runs_is_applied_by_the_next_command(in_repo, capsys):  # noqa: F811
    _later(in_repo, "m4-12-a", "m4-13-b")
    asked = _ask(in_repo, "queue", "m4-12-a")
    assert cli.main(["queue", "m4-13"]) == 0
    assert (in_repo / ".softfield" / "tasks" / "ready" / "m4-12-a.md").is_file()
    assert (in_repo / ".softfield" / "tasks" / "ready" / "m4-13-b.md").is_file()
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
    assert (in_repo / ".softfield" / "tasks" / "later" / "m4-12-a.md").is_file()


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
    assert (in_repo / ".softfield" / "tasks" / "ready" / "m4-12-a.md").is_file()
    assert _request(in_repo, asked)[1] == "queued m4-12-a"


def test_the_checks_never_apply_requests(in_repo):  # noqa: F811
    """check-all runs inside jobs and as the pre-commit hook: a commit there would land on a
    task branch, or in the middle of the owner's own."""
    _later(in_repo, "m4-12-a")
    asked = _ask(in_repo, "queue", "m4-12-a")
    cli.main(["check-layout"])
    assert _request(in_repo, asked) == (None, None)


# --- reject: "won't do" (F31 D2) ---------------------------------------------------------------

ADR_30: dict[str, Any] = {
    "id": "adr-30",
    "kind": "adr",
    "title": "One queue",
    "path": ".softfield/adr/30-one-queue.md",
}
PLAN_F7: dict[str, Any] = {"id": "plan-f7", "kind": "plan", "title": "F7 plan", "path": None}
REPLAN_F7: dict[str, Any] = {
    "id": "replan-f7",
    "kind": "replan",
    "title": "F7 redirected",
    "path": None,
}


def _reply(repo: Path, thread: str, *proposals: dict[str, Any]) -> None:
    """The lead's reply on ``thread`` listing ``proposals``, waiting for the owner's answers."""
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        found = metrics.planner_thread(conn, project, thread, NOW.isoformat())
        metrics.add_planner_message(
            conn, found["id"], "lead", NOW.isoformat(), "Here.", proposals=list(proposals)
        )
        metrics.upsert_owner_item(
            conn, project, planner.PLANNING, thread, text="answers", created=NOW.isoformat()
        )
    finally:
        conn.close()


def _why(repo: Path, card: str) -> object:
    conn = metrics.open_db(_db(repo))
    try:
        row = conn.execute(
            "SELECT archived_why FROM planner_threads WHERE card = ?", (card,)
        ).fetchone()
        return None if row is None else row["archived_why"]
    finally:
        conn.close()


def test_rejecting_a_plan_drops_its_drafts_and_an_unbuilt_card(repo):
    """F7 is planning with no ticket: its branch goes (the ADR drafted on it with the plan),
    its doc is removed in a commit of its own, and the thread closes as rejected."""
    _card(repo)
    _plan(
        repo,
        {
            ".softfield/adr/30-one-queue.md": "# ADR 30\n",
            ".softfield/tasks/later/f7-01-a.md": _ticket("f7-01-a"),
        },
    )
    _reply(repo, "f7", ADR_30, PLAN_F7)
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "reject", "f7/plan-f7")
    _apply(repo)
    result = _request(repo, asked)[1]
    assert result == "rejected the drafts on plan/f7 (adr-30, plan-f7); F7 removed"
    assert git(repo, "branch", "--list", "plan/f7") == ""
    assert not (repo / ".softfield" / "cards" / "f7-one-queue.md").exists()
    assert git(repo, "rev-parse", "HEAD~1") == head
    assert git(repo, "log", "-1", "--format=%s").strip() == "F7 rejected by the owner"
    assert git(repo, "status", "--porcelain") == ""
    assert _archived(repo, "f7") and _why(repo, "f7") == "rejected"
    assert _thread(repo, "f7")[-1]["text"] == "Rejected by the owner on 2026-10-01: won't do"
    assert _items(repo) == [(planner.PLANNING, "f7", None, False)]


def test_rejecting_a_replan_keeps_a_building_card_and_its_tickets(repo):
    _card(repo)
    doc = repo / ".softfield" / "cards" / "f7-one-queue.md"
    doc.write_text(CARD.replace("planning", "building"))
    write_task(repo / ".softfield" / "tasks" / "ready", "f7-01-a")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "building")
    _plan(repo, {".softfield/tasks/ready/f7-01-a.md": "changed\n"})
    _reply(repo, "f7", REPLAN_F7)
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "reject", "f7/replan-f7")
    _apply(repo)
    assert _request(repo, asked)[1] == "rejected the drafts on plan/f7 (replan-f7)"
    assert git(repo, "branch", "--list", "plan/f7") == ""
    assert git(repo, "rev-parse", "HEAD") == head  # nothing committed
    assert doc.is_file() and (repo / ".softfield" / "tasks" / "ready" / "f7-01-a.md").is_file()
    assert _why(repo, "f7") == "rejected"


def test_rejecting_a_merge_commits_nothing_and_settles_it(repo):
    head = _duplicates(repo)
    asked = _ask(repo, "reject", "f12/merge-f12")
    _apply(repo)
    assert _request(repo, asked)[1] == "rejected merge-f12"
    assert git(repo, "rev-parse", "HEAD") == head
    assert (repo / ".softfield" / "cards" / "f12-queue-once.md").read_text() == DUPLICATE
    assert _why(repo, "f12") == "rejected"


@pytest.mark.parametrize(
    ("subject", "result"),
    [
        ("f12/nope", "F12's latest reply has no proposal nope: not rejected"),
        ("f12", "a reject names <thread>/<proposal id>, not 'f12'"),
        ("f12/merge-f12", "merge-f12 is settled already: not rejected"),
    ],
)
def test_a_reject_the_runner_cant_apply_changes_nothing(repo, subject, result):
    head = _duplicates(repo)
    if subject == "f12/merge-f12":  # rejected once already
        _ask(repo, "reject", "f12/merge-f12")
        _apply(repo)
        conn = metrics.open_db(_db(repo))
        try:  # open again, so only the reject's settling is left to refuse it
            conn.execute("UPDATE planner_threads SET archived = NULL WHERE card = 'f12'")
        finally:
            conn.close()
    asked = _ask(repo, "reject", subject)
    _apply(repo)
    assert _request(repo, asked)[1] == result
    assert git(repo, "rev-parse", "HEAD") == head


def test_one_proposal_approved_and_one_rejected_closes_as_approved(repo):
    """The general thread lists a merge and a seed: approving the merge leaves the seed open;
    rejecting the seed closes the thread, as approved since something was."""
    _duplicates(repo, thread="general")
    seed: dict[str, Any] = {
        "id": "seed-1",
        "kind": "seed",
        "title": "Ducks",
        "path": None,
        "key_points": [],
    }
    _reply(repo, "general", MERGE, seed)
    _ask(repo, "approve_plan", "general")
    _apply(repo)
    assert not _archived(repo, "general")
    asked = _ask(repo, "reject", "general/seed-1")
    _apply(repo)
    assert _request(repo, asked)[1] == "rejected seed-1"
    assert _archived(repo, "general") and _why(repo, "general") == "approved"
    # the closing line doesn't call the reject an approval
    assert _thread(repo, "general")[-1]["text"] == (
        "Settled by the owner on 2026-10-01: rejected seed-1"
    )


def test_approving_a_plan_leaves_a_rejected_merge_alone(repo):
    """Won't do (F31 D2) holds: a later Approve plan on the thread doesn't merge the cards
    the owner rejected the merge of. F12 keeps its card."""
    head = _duplicates(repo)
    _ask(repo, "reject", "f12/merge-f12")
    _apply(repo)
    asked = _ask(repo, "approve_plan", "f12")
    _apply(repo)
    assert _request(repo, asked)[1] == "there is no plan/f12 to approve"
    assert git(repo, "rev-parse", "HEAD") == head
    assert (repo / ".softfield" / "cards" / "f12-queue-once.md").read_text() == DUPLICATE


def test_approving_a_plan_still_applies_the_merges_not_rejected(repo):
    """The general thread lists two merges: the rejected one stays, the other is applied."""
    _duplicates(repo, thread="general")
    docs = repo / ".softfield" / "cards"
    (docs / "f13-queue-twice.md").write_text(DUPLICATE.replace("F12: queue once", "F13: twice"))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "f13")
    other = {**MERGE, "id": "merge-f13", "path": ".softfield/cards/f13-queue-twice.md"}
    _reply(repo, "general", MERGE, other)
    _ask(repo, "reject", "general/merge-f12")
    asked = _ask(repo, "approve_plan", "general")
    _apply(repo)
    assert _request(repo, asked)[1] == "approved: merged F13 into F10"
    assert (docs / "f12-queue-once.md").read_text() == DUPLICATE
    assert not (docs / "f13-queue-twice.md").exists()


def _say(repo: Path, thread: str, text: str) -> int:
    return _ask(repo, "plan_message", thread, json.dumps({"text": text, "comments": {}}))


def _owner_said(repo: Path, card: str) -> list[str]:
    return [str(m["text"]) for m in _thread(repo, card) if m["author"] == "owner"]


def test_after_a_merge_the_lead_carries_on_on_the_kept_card(repo):
    """f49-03 (the owner, 2026-10-13, after F107): the duplicate's note is the kept thread's
    next message from the owner and a planner job is queued there, so the answer and the plan
    come on the kept card with no "go" to write on another page."""
    _duplicates(repo)
    _ask(repo, "approve_plan", "f12")
    _apply(repo)
    [said] = _owner_said(repo, "f10")
    assert said.startswith("From F12, merged here:") and "A single line." in said
    [(kind, subject, reason, done)] = _queued(repo)
    assert (kind, reason, done) == ("planner", "your message on F10", None)
    assert str(subject).startswith("f10#")
    assert not _archived(repo, "f10")
    assert _owner_said(repo, "f12") == []  # the duplicate's thread only points on


def test_a_merge_proposed_on_the_kept_cards_thread_queues_nothing_more(repo):
    """f49-03: the lead is already on the kept card, with the plan the owner approved."""
    _duplicates(repo, KEPT_PLANNED, thread="f10")
    _plan(repo, {".softfield/tasks/later/f10-01-a.md": _ticket("f10-01-a")}, card="f10")
    _ask(repo, "approve_plan", "f10")
    _apply(repo)
    assert _queued(repo) == [] and _owner_said(repo, "f10") == []


def _merged_away(repo: Path) -> None:
    """F12 merged into F10 and the lead's job on F10 done: nothing queued."""
    _duplicates(repo)
    _ask(repo, "approve_plan", "f12")
    _apply(repo)
    conn = metrics.open_db(_db(repo))
    try:
        conn.execute("UPDATE work_queue SET done = ?", (NOW.isoformat(),))
        conn.commit()
    finally:
        conn.close()


def test_a_message_on_a_merged_away_thread_goes_to_the_kept_card(repo):
    """The owner wrote "Go" on F107, whose card was merged away, and the lead could only
    answer "F107 has no card" (2026-10-13): the message is the kept thread's, and the old
    thread says where it went."""
    _merged_away(repo)
    asked = _say(repo, "f12", "Go.")
    _apply(repo)
    assert _request(repo, asked)[1] == "queued for the lead on F10, where F12 was merged"
    assert _owner_said(repo, "f10")[-1] == "Go."
    assert _owner_said(repo, "f12") == []
    pointer = _thread(repo, "f12")[-1]
    assert pointer["author"] == "lead" and "/planning/f10" in str(pointer["text"])
    assert "Your message went to F10" in str(pointer["text"])
    assert _archived(repo, "f12") and not _archived(repo, "f10")
    [subject] = [s for kind, s, _, done in _queued(repo) if kind == "planner" and done is None]
    assert str(subject).startswith("f10#")


def test_a_message_on_a_key_merged_into_two_cards_or_planted_again_stays_there(repo):
    """Before f109-02 a key was reused (F64, F73, F107): with two kept cards the runner can't
    tell which the owner means, and a key with a card again is that card's thread."""
    _merged_away(repo)
    docs = repo / ".softfield" / "cards"
    other = planner.merged_card(
        KEPT.replace("F10", "F11"), "x", "From F12: y (merged by the lead on 2026-10-02)"
    )
    (docs / "f11-other.md").write_text(other)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "a second merge of F12")
    asked = _say(repo, "f12", "Which one?")
    _apply(repo)
    assert _request(repo, asked)[1] == "queued for the lead"
    assert _owner_said(repo, "f12") == ["Which one?"]
    (docs / "f11-other.md").unlink()
    (docs / "f12-again.md").write_text(DUPLICATE)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "F12 planted again")
    asked = _say(repo, "f12", "And now?")
    _apply(repo)
    assert _request(repo, asked)[1] == "queued for the lead"
    assert _owner_said(repo, "f12")[-1] == "And now?"


def test_the_merges_a_card_holds_are_read_from_the_headings_merged_card_writes():
    doc = planner.merged_card(KEPT, "a", "From F12: queue once (merged by the lead on 2026-10-01)")
    doc = planner.merged_card(doc, "b", "From F64: again (merged by the owner on 2026-10-02)")
    moved = planner.merged_card(
        KEPT, planner.card_notes(doc), "From F10: one (merged by the lead on 2026-10-03)"
    )
    assert planner.merged_keys(doc) == ["f12", "f64"]
    assert planner.merged_keys(moved) == ["f10", "f12", "f64"]  # a chain: headings moved down
    assert planner.merged_keys(KEPT) == []
    assert (
        planner.merged_keys(
            "## Notes\nFrom F12: said in a line (merged by the lead on 2026-10-01)\n"
        )
        == []
    )


# --- change: a waiting plant or message edited or cancelled before the pick (F14 D1 to D4) ----

CANCEL = json.dumps({"cancel": True})


def _cards(repo: Path) -> list[str]:
    return sorted(p.name for p in (repo / ".softfield" / "cards").glob("*.md"))


def test_cancelling_a_waiting_plant_makes_no_card_no_commit_and_no_planner_row(repo):
    """D2: the change was asked after the plant and still goes first."""
    head = _ducks(repo)
    plant = _ask(repo, "plant", None, _idea("Blue ducks", "For the bath.", ask=True))
    change = _ask(repo, "change", str(plant), CANCEL)
    assert _apply(repo) == [f"change {plant}: cancelled"]
    assert _request(repo, plant) == (NOW.isoformat(), "cancelled by you")
    assert _request(repo, change) == (NOW.isoformat(), "cancelled")
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "status", "--porcelain", "--untracked-files=all") == ""
    assert _cards(repo) == ["f3-rubber-ducks.md"]
    assert _queued(repo) == []
    assert not requests.refused(_row(repo, plant))  # their own cancel: not on the desk
    assert _apply(repo) == []


@pytest.mark.parametrize(
    ("before", "after", "stem", "said"),
    [
        (
            _idea("Blue ducks", "For the bath.", area="factory", ask=True),
            {"title": "Red ducks", "thoughts": "For the key."},
            "f4-red-ducks",
            "Red ducks\n\nFor the key.",
        ),
        # a one-box note (F31 D7) edited as one box, and as a title with its thoughts
        (
            json.dumps({"text": "Blue ducks: for the bath.", "ask": True}),
            {"text": "Red ducks: for the key."},
            "f4-red-ducks-for-the-key",
            "Red ducks: for the key.",
        ),
        (
            json.dumps({"text": "Blue ducks: for the bath.", "ask": True}),
            {"title": "Red ducks", "thoughts": "For the key."},
            "f4-red-ducks",
            "Red ducks\n\nFor the key.",
        ),
    ],
)
def test_an_edited_plant_is_planted_with_the_new_words_in_the_same_pick(
    repo, before, after, stem, said
):
    """The words are replaced; what else the plant said (its area, "ask the lead") stays."""
    _ducks(repo)
    plant = _ask(repo, "plant", None, before)
    change = _ask(repo, "change", str(plant), json.dumps(after))
    planted = f"planted .softfield/cards/{stem}.md, queued for the lead"
    assert _apply(repo) == [f"change {plant}: changed", f"plant: {planted}"]
    assert _request(repo, change) == (NOW.isoformat(), "changed")
    assert _request(repo, plant) == (NOW.isoformat(), planted)
    assert _cards(repo) == ["f3-rubber-ducks.md", f"{stem}.md"]
    doc = (repo / ".softfield" / "cards" / f"{stem}.md").read_text()
    assert "Blue" not in doc and "bath" not in doc
    assert [m["text"] for m in _thread(repo, "f4")] == [said]
    assert json.loads(_row(repo, plant)["value"])["ask"] is True


def test_an_edited_message_is_sent_with_the_new_words_in_the_same_pick(repo):
    message = _ask(repo, "plan_message", "f7", _message("Why one queue?", p1="Old."))
    _ask(repo, "change", str(message), _message("Why two queues?", p2="New."))
    assert _apply(repo) == [
        f"change {message}: changed",
        "plan_message f7: queued for the lead",
    ]
    [said] = _thread(repo, "f7")
    assert said["text"] == "Why two queues?"
    assert json.loads(str(said["points"])) == [{"n": 2, "comment": "New."}]
    assert _queued(repo) == [("planner", f"f7#{message}", "your message on F7", None)]


def test_cancelling_a_waiting_message_adds_no_thread_message_and_no_planner_row(repo):
    message = _ask(repo, "plan_message", "f7", _message("Why one queue?"))
    change = _ask(repo, "change", str(message), CANCEL)
    assert _apply(repo) == [f"change {message}: cancelled"]
    assert _request(repo, message) == (NOW.isoformat(), "cancelled by you")
    assert _request(repo, change) == (NOW.isoformat(), "cancelled")
    assert _queued(repo) == []
    conn = metrics.open_db(_db(repo))
    try:
        assert conn.execute("SELECT count(*) FROM planner_messages").fetchone()[0] == 0
    finally:
        conn.close()
    assert not requests.refused(_row(repo, message))


@pytest.mark.parametrize(
    ("kind", "subject", "value", "change", "result"),
    [
        ("plant", None, _idea("Blue ducks"), CANCEL, "too late: already planted"),
        ("plant", None, _idea("Blue ducks"), _idea("Red ducks"), "too late: already planted"),
        ("plan_message", "f7", _message("Go."), CANCEL, "too late: already sent"),
        ("plan_message", "f7", _message("Go."), _message("No."), "too late: already sent"),
    ],
)
def test_a_change_that_comes_after_the_pick_is_too_late_and_changes_nothing(
    repo, kind, subject, value, change, result
):
    _ducks(repo)
    target = _ask(repo, kind, subject, value)
    _apply(repo)
    before = tuple(_row(repo, target))
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "change", str(target), change)
    later = NOW + timedelta(minutes=5)
    assert _apply(repo, at=later) == [f"change {target}: {result}"]
    assert _request(repo, asked) == (later.isoformat(), result)
    assert tuple(_row(repo, target)) == before
    assert git(repo, "rev-parse", "HEAD") == head


@pytest.mark.parametrize("subject", [None, "", "x", "12a", "99", "1" * 40])
def test_a_change_names_a_request_by_its_id(repo, subject):
    asked = _ask(repo, "change", subject, _idea("Red ducks"))
    [line] = _apply(repo)
    done, said = _request(repo, asked)
    assert done == NOW.isoformat() and "request" in str(said)
    assert "Red ducks" not in line  # the owner's words stay off the console


@pytest.mark.parametrize(
    ("kind", "subject", "value", "why"),
    [
        ("signoff", "f9-nothing", None, "is a signoff"),
        ("pause", None, None, "is a pause"),
        ("send_back", "f7/adr-23", _message("No."), "is a send_back"),
    ],
)
def test_a_change_on_another_kind_of_request_changes_nothing(repo, kind, subject, value, why):
    """D3: plants and messages only; the request is applied as it was asked."""
    target = _ask(repo, kind, subject, value)
    asked = _ask(repo, "change", str(target), CANCEL)
    _apply(repo)
    assert why in str(_request(repo, asked)[1])
    done, result = _request(repo, target)
    assert done == NOW.isoformat() and result != "cancelled by you"
    assert _row(repo, target)["value"] == value


def test_a_change_on_another_projects_request_changes_nothing(repo):
    conn = metrics.open_db(_db(repo))
    try:
        other = metrics.upsert_project(conn, "elsewhere")
        target = metrics.add_request(conn, other, "plant", None, BAD_AREA, NOW.isoformat())
    finally:
        conn.close()
    asked = _ask(repo, "change", str(target), CANCEL)
    _apply(repo)
    assert _request(repo, asked)[1] == f"there is no request {target}"
    assert _request(repo, target) == (None, None)


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "not json",
        "[]",
        "{}",
        '{"cancel": false}',
        '{"cancel": "yes"}',
        '{"cancel": true, "title": "Red ducks"}',  # which of the two?
        '{"area": "product"}',  # no words
        '{"title": ""}',
        '{"title": "Red\\nducks"}',
        '{"title": ["Red ducks"]}',
        '{"text": " "}',
        '{"title": "Red ducks", "area": "garden"}',
    ],
)
def test_a_change_with_a_bad_value_says_why_and_the_plant_goes_as_it_was(repo, value):
    _ducks(repo)
    words = _idea("Blue ducks", "For the bath.")
    plant = _ask(repo, "plant", None, words)
    asked = _ask(repo, "change", str(plant), value)
    lines = _apply(repo)
    done, said = _request(repo, asked)
    assert done == NOW.isoformat() and said not in (None, "", "changed", "cancelled")
    assert lines == [f"change {plant}: {said}", "plant: planted .softfield/cards/f4-blue-ducks.md"]
    assert _row(repo, plant)["value"] == words


@pytest.mark.parametrize(
    "value", ["not json", "{}", '{"text": 3}', '{"text": " "}', '{"text": "x", "comments": []}']
)
def test_a_change_with_a_bad_value_leaves_the_message_as_it_was(repo, value):
    words = _message("Why one queue?")
    message = _ask(repo, "plan_message", "f7", words)
    asked = _ask(repo, "change", str(message), value)
    _apply(repo)
    assert _request(repo, asked)[1] not in (None, "", "changed", "cancelled")
    assert _row(repo, message)["value"] == words
    assert [m["text"] for m in _thread(repo, "f7")] == ["Why one queue?"]


def test_two_edits_apply_oldest_first_and_the_last_wins(repo):
    _ducks(repo)
    plant = _ask(repo, "plant", None, _idea("Blue ducks"))
    _ask(repo, "change", str(plant), _idea("Red ducks"))
    _ask(repo, "change", str(plant), _idea("Green ducks"))
    assert _apply(repo) == [
        f"change {plant}: changed",
        f"change {plant}: changed",
        "plant: planted .softfield/cards/f4-green-ducks.md",
    ]
    assert _cards(repo) == ["f3-rubber-ducks.md", "f4-green-ducks.md"]


def test_an_edit_after_a_cancel_is_too_late(repo):
    _ducks(repo)
    plant = _ask(repo, "plant", None, _idea("Blue ducks"))
    _ask(repo, "change", str(plant), CANCEL)
    _ask(repo, "change", str(plant), _idea("Red ducks"))
    assert _apply(repo) == [
        f"change {plant}: cancelled",
        f"change {plant}: too late: already cancelled",
    ]
    assert _row(repo, plant)["value"] == _idea("Blue ducks")
    assert _cards(repo) == ["f3-rubber-ducks.md"]


def test_a_plant_waiting_for_main_is_cancelled_on_another_branch(repo):
    """A change commits nothing, so it never waits for main."""
    _ducks(repo)
    git(repo, "checkout", "-q", "-b", "task/x")
    plant = _ask(repo, "plant", None, _idea("Blue ducks"))
    assert _apply(repo) == ["plant: waits for the repo to be on main"]
    _ask(repo, "change", str(plant), CANCEL)
    assert _apply(repo) == [f"change {plant}: cancelled"]
    assert _request(repo, plant) == (NOW.isoformat(), "cancelled by you")
    git(repo, "checkout", "-q", "main")
    assert _apply(repo) == [] and _cards(repo) == ["f3-rubber-ducks.md"]


def test_an_approved_seeds_plant_is_cancelled_but_not_edited(repo):
    """Its words are the lead's proposal's: there are none of the owner's to replace."""
    seed = _ask(repo, "plant", "general/seed-1", None)
    edit = _ask(repo, "change", str(seed), _idea("Red ducks"))
    cancel = _ask(repo, "change", str(seed), CANCEL)
    _apply(repo)
    assert "only be cancelled" in str(_request(repo, edit)[1])
    assert _request(repo, cancel)[1] == "cancelled"
    assert _row(repo, seed)["value"] is None
    assert _request(repo, seed)[1] == "cancelled by you"


def test_a_wait_leaves_a_change_for_the_pick(repo):
    plant = _ask(repo, "plant", None, _idea("Blue ducks"))
    change = _ask(repo, "change", str(plant), CANCEL)
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.find_project(conn, repo.name)
        assert project is not None
        assert requests.take_switches(conn, project, State(), NOW) == []
    finally:
        conn.close()
    assert _request(repo, change) == (None, None) and _request(repo, plant) == (None, None)


def test_a_requests_value_is_changed_only_while_it_is_open(repo):
    plant = _ask(repo, "plant", None, _idea("Blue ducks"))
    conn = metrics.open_db(_db(repo))
    try:
        assert metrics.change_request(conn, plant, _idea("Red ducks"))
        assert metrics.finish_request(conn, plant, NOW.isoformat(), "planted x")
        assert not metrics.change_request(conn, plant, _idea("Green ducks"))
    finally:
        conn.close()
    assert _row(repo, plant)["value"] == _idea("Red ducks")


# --- an edit that didn't go through waits on the desk until dismissed (f14-04) ---------------


@pytest.mark.parametrize(
    ("value", "words"),
    [
        (_idea("Red ducks", "For the key."), ("Red ducks", "For the key.")),
        ('{"title": "  Red ducks  "}', ("Red ducks", "")),
        ('{"text": "Red ducks: for the key."}', ("", "Red ducks: for the key.")),
        (_message("No.", p2="Shorter."), ("", "No.\n\nOn point 2: Shorter.")),
        # read leniently: words the runner couldn't read are still the owner's
        ("not json", ("", "not json")),
        ('{"title": ["Red ducks"]}', ("", '{"title": ["Red ducks"]}')),
        ('{"text": "x", "comments": 3}', ("", '{"text": "x", "comments": 3}')),
        ('{"cancel": true, "title": "Red ducks"}', ("Red ducks", "")),
        # a cancel, or a value with no words
        (CANCEL, None),
        ('{"cancel": false}', None),
        ('{"area": "product"}', None),
        ('{"text": " "}', None),
        ("{}", None),
        (None, None),
    ],
)
def test_an_edits_words_are_its_values_and_a_cancel_carries_none(value, words):
    row = {"kind": "change", "subject": "3", "value": value}
    found = requests.owners_words(row)
    assert (None if found is None else (found.title, found.text)) == words


@pytest.mark.parametrize(
    ("value", "done", "result", "dismissed", "refused"),
    [
        (_idea("Red ducks"), True, "too late: already planted", None, True),
        (_message("No."), True, "too late: already sent", None, True),
        (_idea("Red ducks"), True, "too late: already cancelled", None, True),
        (_idea("Red\nducks"), True, "an idea has a title, on one line", None, True),
        (_idea("Red ducks"), True, "there is no request 3", None, True),
        (_idea("Red ducks"), True, "changed", None, False),
        (_idea("Red ducks"), None, None, None, False),
        (_idea("Red ducks"), True, "too late: already planted", NOW.isoformat(), False),
        # a cancel is never shown there, whatever its result
        (CANCEL, True, "cancelled", None, False),
        (CANCEL, True, "too late: already planted", None, False),
        (CANCEL, True, "too late: already sent", None, False),
        (CANCEL, True, "there is no request 3", None, False),
    ],
)
def test_an_edit_is_refused_when_done_without_changed_and_a_cancel_never(
    value, done, result, dismissed, refused
):
    row = {
        "kind": "change",
        "subject": "3",
        "value": value,
        "done": done and NOW.isoformat(),
        "result": result,
        "dismissed": dismissed,
    }
    assert requests.refused(row) is refused


@pytest.mark.parametrize(
    ("kind", "subject", "value", "edit", "result"),
    [
        ("plant", None, _idea("Blue ducks"), _idea("Red ducks"), "too late: already planted"),
        ("plan_message", "f7", _message("Go."), _message("No."), "too late: already sent"),
    ],
)
def test_an_edit_that_came_too_late_is_dismissed_once_and_keeps_its_words(
    repo, kind, subject, value, edit, result
):
    _ducks(repo)
    target = _ask(repo, kind, subject, value)
    _apply(repo)
    change = _ask(repo, "change", str(target), edit)
    _apply(repo)
    row = _row(repo, change)
    assert row["result"] == result and requests.refused(row)
    later = NOW + timedelta(minutes=5)
    dismissed = _ask(repo, "dismiss", str(change))
    assert _apply(repo, at=later) == [f"dismiss {change}: dismissed request {change}"]
    assert _request(repo, dismissed) == (later.isoformat(), f"dismissed request {change}")
    row = _row(repo, change)
    assert row["dismissed"] == later.isoformat()
    assert row["value"] == edit and not requests.refused(row)  # its words stay
    assert _row(repo, target)["dismissed"] is None  # the plant or message it named is as it was
    _ask(repo, "dismiss", str(change))
    assert _apply(repo) == [f"dismiss {change}: request {change} is dismissed already"]


def test_an_edit_the_runner_refused_for_its_words_is_dismissed(repo):
    _ducks(repo)
    plant = _ask(repo, "plant", None, _idea("Blue ducks"))
    change = _ask(repo, "change", str(plant), _idea("Red\nducks"))
    _apply(repo)
    row = _row(repo, change)
    assert row["result"] not in ("changed", "cancelled") and requests.refused(row)
    assert requests.owners_words(row) == requests.Words("Red\nducks", "")
    _ask(repo, "dismiss", str(change))
    assert _apply(repo) == [f"dismiss {change}: dismissed request {change}"]


@pytest.mark.parametrize(
    ("change", "taken", "error"),
    [
        (_idea("Red ducks"), False, "wasn't refused"),  # it worked: "changed"
        (CANCEL, False, "carries no words"),  # "cancelled"
        (CANCEL, True, "carries no words"),  # "too late: already planted"
    ],
)
def test_dismiss_refuses_an_edit_that_worked_and_any_cancel(repo, change, taken, error):
    _ducks(repo)
    plant = _ask(repo, "plant", None, _idea("Blue ducks"))
    if taken:
        _apply(repo)
    asked = _ask(repo, "change", str(plant), change)
    _apply(repo)
    dismiss = _ask(repo, "dismiss", str(asked))
    _apply(repo)
    assert error in str(_request(repo, dismiss)[1])
    assert _row(repo, asked)["dismissed"] is None


def test_the_projects_page_order_is_applied_at_the_next_pick_without_a_commit(repo):
    """ADR 30 item 6: the Projects page sends the whole order; the runner works in it from its
    next pick. It touches no file, so a dirty tree or another branch doesn't hold it."""
    conn = metrics.open_db(_db(repo))
    try:
        metrics.upsert_project(conn, "coucou", repo="/r/coucou")
    finally:
        conn.close()
    git(repo, "checkout", "-q", "-b", "elsewhere")
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "project_order", value=json.dumps(["coucou", repo.name, "nope"]))
    bad = _ask(repo, "project_order", value="coucou first")
    assert _apply(repo) == [
        f"project_order: the projects' order: coucou, {repo.name} (no project nope)",
        "project_order: a projects' order is a JSON list of project names, first first",
    ]
    assert _request(repo, asked)[1] == f"the projects' order: coucou, {repo.name} (no project nope)"
    assert _request(repo, bad)[0] is not None
    assert git(repo, "rev-parse", "HEAD") == head
