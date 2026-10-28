"""Week numbers for the reports page (F59 D2, D3).

Plain functions over a read-only connection that return data, never text. A week runs from
Monday 00:00 to the next Monday 00:00 in the machine's local time; a job counts in the week
its ``started`` falls in, a milestone in the week of its ``ended``.
"""

import sqlite3
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, timedelta

from factory_dashboard import queries

MERGING_ROLES = ("developer", "last-attempt", "lead-ticket")  # a `passed` one merged a ticket


@dataclass(frozen=True)
class Week:
    """One week's numbers, by agent or role where named; ``previous`` is the week before,
    with no ``previous`` of its own."""

    monday: date
    milestones_done: int = 0
    merged: dict[str, int] = field(default_factory=dict)  # by agent
    dollars: dict[str, float] = field(default_factory=dict)  # Claude's, by role
    hours: dict[str, float] = field(default_factory=dict)  # by agent
    attempts: dict[str, int] = field(default_factory=dict)  # developer attempts, by agent
    passed: dict[str, int] = field(default_factory=dict)  # of those, passed, by agent
    timeouts: int = 0
    escalations: int = 0
    savings: float = 0.0  # net dollars
    previous: "Week | None" = None

    @property
    def rate(self) -> float | None:
        """The developers' pass rate, or None in a week with no developer attempt."""
        attempts = sum(self.attempts.values())
        return sum(self.passed.values()) / attempts if attempts else None


def _midnight(day: date) -> datetime:
    """Local midnight of ``day``, with that date's own offset (summer time changes)."""
    return datetime(day.year, day.month, day.day).astimezone()


def _monday_of(moment: datetime) -> date:
    day = moment.astimezone().date()
    return day - timedelta(days=day.weekday())


def _rows(conn: sqlite3.Connection, sql: str, projects: Sequence[str]) -> list[sqlite3.Row]:
    """``sql``'s rows for the named projects; ``sql`` ends in ``p.name IN``."""
    if not projects:
        return []
    marks = ",".join("?" * len(projects))
    return conn.execute(f"{sql} ({marks})", list(projects)).fetchall()


def _jobs(conn: sqlite3.Connection, projects: Sequence[str]) -> list[sqlite3.Row]:
    return _rows(
        conn,
        "SELECT j.* FROM jobs j JOIN runs r ON r.id = j.run_id"
        " JOIN projects p ON p.id = r.project_id WHERE j.started IS NOT NULL AND p.name IN",
        projects,
    )


def _numbers(conn: sqlite3.Connection, projects: Sequence[str], monday: date) -> Week:
    start, end = _midnight(monday), _midnight(monday + timedelta(days=7))
    jobs = [j for j in _jobs(conn, projects) if start <= queries._time(j["started"]) < end]
    milestones = [
        m
        for m in _rows(
            conn,
            "SELECT m.key, p.name AS project, m.ended FROM milestones m"
            " JOIN projects p ON p.id = m.project_id WHERE m.ended IS NOT NULL AND p.name IN",
            projects,
        )
        if start <= queries._time(m["ended"]) < end
    ]
    merged: dict[str, int] = defaultdict(int)
    dollars: dict[str, float] = defaultdict(float)
    hours: dict[str, float] = defaultdict(float)
    attempts: dict[str, int] = defaultdict(int)
    passed: dict[str, int] = defaultdict(int)
    for job in jobs:
        agent = job["agent"]
        if job["outcome"] == "passed" and job["role"] in MERGING_ROLES:
            merged[agent] += 1
        if queries.is_claude(agent):
            dollars[job["role"]] += queries.dollars(job)
        if job["ended"]:
            took = queries._time(job["ended"]) - queries._time(job["started"])
            hours[agent] += took.total_seconds() / 3600
        if job["role"] in queries.LOCAL_ROLES:
            attempts[agent] += 1
            passed[agent] += int(job["outcome"] == "passed")
    return Week(
        monday=monday,
        milestones_done=len(milestones),
        merged=dict(merged),
        dollars=dict(dollars),
        hours=dict(hours),
        attempts=dict(attempts),
        passed=dict(passed),
        timeouts=sum(j["outcome"] == "timeout" for j in jobs),
        escalations=sum(j["role"] == "escalation" for j in jobs),
        savings=sum(queries.savings(conn, m["project"], m["key"]).net for m in milestones),
    )


def week(conn: sqlite3.Connection, projects: list[str], monday: date) -> Week:
    """The week starting on ``monday`` for ``projects``, with the week before."""
    previous = _numbers(conn, projects, monday - timedelta(days=7))
    return replace(_numbers(conn, projects, monday), previous=previous)


def weeks(conn: sqlite3.Connection, projects: list[str]) -> list[date]:
    """Every Monday from the first job's week to this one, newest first."""
    started = [queries._time(j["started"]) for j in _jobs(conn, projects)]
    if not started:
        return []
    monday, last = _monday_of(min(started)), _monday_of(datetime.now(UTC))
    found = []
    while monday <= last:
        found.append(monday)
        monday += timedelta(days=7)
    return found[::-1]


def series(conn: sqlite3.Connection, projects: list[str]) -> list[Week]:
    """``weeks``' weeks with their numbers, oldest first."""
    return [week(conn, projects, monday) for monday in reversed(weeks(conn, projects))]
