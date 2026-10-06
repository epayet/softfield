"""The owner's requests from the dashboard (ADR 18 item 2, f5 D1 and D2).

The dashboard only writes a request row. The runner applies it, with the code of its console
command: at each pick, while a wait for the owner's 25% sleeps (`take_switches`), and at the
start of every ``runner`` command while no run is live. Each request is finished once, with
its result or its error, and never retried. Git and tasks/ keep one writer, and the run
state.json, whose reserve switches (ADR 22 item 4) the requests set.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from runner import loop, metrics, owner
from runner.gitops import Git
from runner.state import State
from runner.tasks import TaskError, milestone_arg

SIGNOFF = "signoff"  # subject: the milestone key
RESERVE = "reserve"  # subject: week or five_hour; value: on or off (f8 D4)
FIVE_HOUR = "five_hour"  # value: yes or no; the 5-hour switch, until f8-06's switches
QUEUE = "queue"  # subject: the ticket id
_ANSWERS = {"yes": "on", "no": "off"}
_SWITCHED = ("on", "off")


def _what(row: sqlite3.Row) -> str:
    """A request in a console line: ``signoff f4-always-on``, ``five_hour yes``."""
    return " ".join(str(part) for part in (row["kind"], row["subject"] or row["value"]) if part)


def _switch(
    conn: sqlite3.Connection,
    project_id: int,
    state: State,
    now: datetime,
    switch: object,
    value: object,
) -> str:
    """A reserve switch turned on (for 24 hours) or off; the items the owner acted on are
    answered: the switch's own lapse item and, when on, the tickets parked for it."""
    if switch not in loop.SWITCHES:
        return f"a reserve switch is {' or '.join(loop.SWITCHES)}, not {switch!r}"
    if value not in _SWITCHED:
        return f"a reserve switch is turned on or off, not {value!r}"
    name, on = str(switch), value == "on"
    parked = loop.FIVE_HOUR_KIND if name == loop.FIVE_HOUR else loop.RESERVE_KIND
    for row in metrics.open_owner_items(conn, project_id):
        kind, subject = row["kind"], row["subject"]
        lapsed = kind == loop.RESERVE_KIND and subject == name
        waiting = on and kind == parked and subject not in loop.SWITCHES
        if lapsed or waiting:
            metrics.resolve_owner_item(conn, row["id"], now.isoformat())
    return f"Claude's reserve: {loop.set_switch(state, name, on, now)}"


def _five_hour(
    conn: sqlite3.Connection, project_id: int, state: State, now: datetime, value: object
) -> str:
    """The dashboard's Yes or No to the 5-hour window: the 5-hour switch on or off."""
    if value not in _ANSWERS:
        return f"a 5-hour answer is yes or no, not {value!r}"
    return _switch(conn, project_id, state, now, loop.FIVE_HOUR, _ANSWERS[str(value)])


def _waits(repo: Path, kind: str) -> str | None:
    """Why a request that commits must wait, if it must: a queue commits on the branch it is
    on, and a sign-off commits the whole tree, so neither goes anywhere but a main that is
    as clean as it needs to be. It stays open for a later command or pick."""
    if kind not in (SIGNOFF, QUEUE):
        return None
    git = Git(repo)
    if git.current_branch() != loop.MAIN:
        return f"waits for the repo to be on {loop.MAIN}"
    if kind == SIGNOFF and not git.is_clean():
        return f"waits for a clean {loop.MAIN}: a sign-off commits the whole tree"
    return None


def _apply(
    repo: Path,
    db: Path,
    conn: sqlite3.Connection,
    project_id: int,
    state: State,
    now: datetime,
    row: sqlite3.Row,
) -> str:
    """One request, as its console command; its result, or the error that command prints."""
    kind, subject, value = row["kind"], row["subject"], row["value"]
    try:
        if kind == SIGNOFF:
            key = milestone_arg(repo, subject)
            owner.signoff(repo, key, now.date(), db=db)
            return f"signed off {key}"
        if kind == QUEUE:
            if not subject:  # "" would match every ticket in later/
                return "a queue request names its ticket"
            return f"queued {loop.move_to_ready(repo, str(subject))}"
        if kind == RESERVE:
            return _switch(conn, project_id, state, now, subject, value)
        if kind == FIVE_HOUR:
            return _five_hour(conn, project_id, state, now, value)
    except (owner.OwnerError, loop.RunnerError, TaskError) as exc:
        return str(exc)
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"
    return f"unknown request: {kind}"


def _lapse(conn: sqlite3.Connection, project_id: int, state: State, now: datetime) -> list[str]:
    """The switches on for 24 hours turned off, each with a Needs-you item that asks to turn
    it on again (the owner, 2026-10-04)."""
    lines = []
    for switch in loop.lapse_switches(state, now):
        which = "the week's switch" if switch == loop.WEEK else "the 5-hour switch"
        text = (
            f"Claude's reserve: {which} went off after 24 hours."
            f" Turn “{loop.SWITCHES[switch]}” on again for 24 h?"
        )
        metrics.upsert_owner_item(
            conn,
            project_id,
            loop.RESERVE_KIND,
            switch,
            text=text,
            command=loop.switch_command(switch),
            created=now.isoformat(),
        )
        lines.append(text)
    return lines


def apply_requests(repo: Path, db: Path, now: datetime, state: State) -> list[str]:
    """Apply the project's open requests, oldest first, after turning off the switches whose
    24 hours are over: one line per request done or left to wait, and per switch turned off.
    The switches are set on ``state``, for the caller to save. Nothing to do without the
    database or the project in it, and neither is made."""
    if not db.is_file():
        return []
    conn = metrics.open_db(db)
    try:
        project = metrics.find_project(conn, repo.name)
        if project is None:
            return []
        lines = _lapse(conn, project, state, now)
        for row in metrics.open_requests(conn, project):
            if (why := _waits(repo, row["kind"])) is not None:
                lines.append(f"{_what(row)}: {why}")
                continue
            result = _apply(repo, db, conn, project, state, now, row)
            if metrics.finish_request(conn, row["id"], now.isoformat(), result):
                lines.append(f"{_what(row)}: {result}")
        return lines
    finally:
        conn.close()


def take_switches(
    conn: sqlite3.Connection, project_id: int, state: State, now: datetime
) -> list[str]:
    """The open switch requests (``reserve``, the dashboard's 5-hour answer) applied to
    ``state`` and finished, for a wait that sleeps for the owner's 25%; the others wait for
    the pick, which may commit."""
    lines = []
    for row in metrics.open_requests(conn, project_id):
        if row["kind"] == RESERVE:
            result = _switch(conn, project_id, state, now, row["subject"], row["value"])
        elif row["kind"] == FIVE_HOUR:
            result = _five_hour(conn, project_id, state, now, row["value"])
        else:
            continue
        if metrics.finish_request(conn, row["id"], now.isoformat(), result):
            lines.append(f"{_what(row)}: {result}")
    return lines
