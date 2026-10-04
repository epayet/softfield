"""The owner's requests from the dashboard (ADR 18 item 2, f5 D1 and D2).

The dashboard only writes a request row. The runner applies it, with the code of its console
command: at each pick, while the 5-hour question waits (`take_five_hour`), and at the start of
every ``runner`` command while no run is live. Each request is finished once, with its result
or its error, and never retried. Git and tasks/ keep one writer.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from runner import loop, metrics, owner
from runner.gitops import Git
from runner.tasks import TaskError, milestone_arg

SIGNOFF = "signoff"  # subject: the milestone key
FIVE_HOUR = "five_hour"  # value: yes or no
QUEUE = "queue"  # subject: the ticket id
_ANSWERS = ("yes", "no")


def _what(row: sqlite3.Row) -> str:
    """A request in a console line: ``signoff f4-always-on``, ``five_hour yes``."""
    return " ".join(str(part) for part in (row["kind"], row["subject"] or row["value"]) if part)


def _bad_answer(value: object) -> str:
    return f"a 5-hour answer is yes or no, not {value!r}"


def _five_hour(value: object) -> str:
    """The 5-hour answer with no question waiting: it holds for the command, as a typed one."""
    if value not in _ANSWERS:
        return _bad_answer(value)
    yes = value == "yes"
    loop.FIVE_HOUR.yes, loop.FIVE_HOUR.no = yes, not yes
    if yes:
        return "Claude's 5-hour window is used for the rest of this run"
    return "Claude's 5-hour window stays kept for you"


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


def _apply(repo: Path, db: Path, now: datetime, row: sqlite3.Row) -> str:
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
        if kind == FIVE_HOUR:
            return _five_hour(value)
    except (owner.OwnerError, loop.RunnerError, TaskError) as exc:
        return str(exc)
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"
    return f"unknown request: {kind}"


def apply_requests(repo: Path, db: Path, now: datetime) -> list[str]:
    """Apply the project's open requests, oldest first: one line per request done, or left to
    wait. Nothing to do without the database or the project in it, and neither is made."""
    if not db.is_file():
        return []
    conn = metrics.open_db(db)
    try:
        project = metrics.find_project(conn, repo.name)
        if project is None:
            return []
        lines = []
        for row in metrics.open_requests(conn, project):
            if (why := _waits(repo, row["kind"])) is not None:
                lines.append(f"{_what(row)}: {why}")
                continue
            result = _apply(repo, db, now, row)
            if metrics.finish_request(conn, row["id"], now.isoformat(), result):
                lines.append(f"{_what(row)}: {result}")
        return lines
    finally:
        conn.close()


def take_five_hour(conn: sqlite3.Connection, project_id: int, now: datetime) -> str | None:
    """The first open answer to the 5-hour question, ``yes`` or ``no``, finished as taken by
    the question that waits for it; None without one. Other requests wait for the pick."""
    for row in metrics.open_requests(conn, project_id):
        if row["kind"] != FIVE_HOUR:
            continue
        value = row["value"]
        if value not in _ANSWERS:
            metrics.finish_request(conn, row["id"], now.isoformat(), _bad_answer(value))
            continue
        if metrics.finish_request(
            conn, row["id"], now.isoformat(), f"answered {value} to the 5-hour question"
        ):
            return str(value)
    return None
