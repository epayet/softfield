"""Week numbers for the reports page (F59 D2, D3), with the owner's time (F86).

Plain functions over a read-only connection that return data, never text. A week runs from
Monday 00:00 to the next Monday 00:00 in the machine's local time; a job counts in the week
its ``started`` falls in, a milestone in the week of its ``ended``.
"""

import re
import sqlite3
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, timedelta
from statistics import median

from factory_dashboard import queries

MERGING_ROLES = ("developer", "last-attempt", "lead-ticket")  # a `passed` one merged a ticket

SITTING_GAP = timedelta(minutes=20)  # F86 D2: a gap this long or longer starts a sitting
FIRST_MINUTES = 5.0  # F86 D2: the reading before a sitting's first press
PLANTING = "Planting"
STEERING = "Steering the line"
_CARD_KEY = re.compile(r"([a-z]+\d+)(?:-|$)")  # `f158-milestones-…` → f158, `m1` → m1


@dataclass(frozen=True)
class CardTime:
    """The owner's minutes on one card of one project, or on Planting or Steering the line
    (``key`` and ``project`` None: those are one entry over every project)."""

    key: str | None
    project: str | None
    title: str
    minutes: float


@dataclass(frozen=True)
class OwnerTime:
    """The owner's time in one week (F86 D1–D5), counted from their presses on the dashboard;
    the ``_before`` numbers are the week before's, None when that week wasn't recorded."""

    hours: float = 0.0
    sittings: int = 0
    days: int = 0
    actions: dict[str, int] = field(default_factory=dict)  # by kind
    by_card: list[CardTime] = field(default_factory=list)  # most minutes first
    waited_hours: float | None = None  # median, over the items resolved in the week
    waited_items: int = 0
    hours_before: float | None = None
    waited_hours_before: float | None = None


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
    owner: "OwnerTime | None" = None  # None before the first owner_requests row's week (F86)

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


@dataclass(frozen=True)
class _Press:
    at: datetime
    project: str
    kind: str
    subject: str | None
    minutes: float
    sitting: int


def _presses(conn: sqlite3.Connection) -> list[_Press]:
    """Every project's actions in time order, as datetimes (offsets differ between rows), each
    with its minutes and its sitting's number (F86 D2)."""
    rows = conn.execute(
        "SELECT o.kind, o.subject, o.created, p.name AS project FROM owner_requests o"
        " JOIN projects p ON p.id = o.project_id"
    ).fetchall()
    timed = sorted(((queries._time(r["created"]), r) for r in rows), key=lambda pair: pair[0])
    found: list[_Press] = []
    last: datetime | None = None
    sitting = 0
    for at, row in timed:
        if last is not None and at - last < SITTING_GAP:
            minutes = (at - last).total_seconds() / 60
        else:
            sitting += 1
            minutes = FIRST_MINUTES
        last = at
        found.append(_Press(at, row["project"], row["kind"], row["subject"], minutes, sitting))
    return found


def _first_recorded(conn: sqlite3.Connection) -> date | None:
    """The Monday of the first ``owner_requests`` row's week; None with none."""
    rows = conn.execute("SELECT created FROM owner_requests").fetchall()
    if not rows:
        return None
    return _monday_of(min(queries._time(r["created"]) for r in rows))


def _card_titles(conn: sqlite3.Connection, projects: Sequence[str]) -> dict[tuple[str, str], str]:
    """Each project's card titles by short key (``f158`` for ``f158-milestones-…``)."""
    titles: dict[tuple[str, str], str] = {}
    for row in _rows(
        conn,
        "SELECT m.key, m.title, p.name AS project FROM milestones m"
        " JOIN projects p ON p.id = m.project_id WHERE m.title IS NOT NULL AND p.name IN",
        projects,
    ):
        matched = _CARD_KEY.match(row["key"])
        if matched:
            titles.setdefault((row["project"], matched.group(1)), row["title"])
    return titles


def _waited(conn: sqlite3.Connection, projects: Sequence[str], monday: date) -> list[float]:
    """Hours each item resolved in the week waited for the owner (F86 D4)."""
    start, end = _midnight(monday), _midnight(monday + timedelta(days=7))
    waited = []
    for row in _rows(
        conn,
        "SELECT i.created, i.resolved FROM owner_items i JOIN projects p ON p.id = i.project_id"
        " WHERE i.created IS NOT NULL AND i.resolved IS NOT NULL AND p.name IN",
        projects,
    ):
        resolved = queries._time(row["resolved"])
        if start <= resolved < end:
            waited.append((resolved - queries._time(row["created"])).total_seconds() / 3600)
    return waited


def _owner_week(
    conn: sqlite3.Connection, projects: Sequence[str], monday: date, presses: list[_Press]
) -> OwnerTime:
    start, end = _midnight(monday), _midnight(monday + timedelta(days=7))
    mine = [p for p in presses if p.project in projects and start <= p.at < end]
    titles = _card_titles(conn, projects)
    actions: dict[str, int] = defaultdict(int)
    cards: dict[tuple[str | None, str | None], float] = defaultdict(float)
    for press in mine:
        actions[press.kind] += 1
        matched = _CARD_KEY.match(press.subject or "")
        if press.kind == "plant":
            cards[(None, PLANTING)] += press.minutes
        elif matched:
            cards[(press.project, matched.group(1))] += press.minutes
        else:
            cards[(None, STEERING)] += press.minutes
    by_card = [
        CardTime(key, project, titles.get((project, key), key), minutes)
        if project is not None and key is not None
        else CardTime(None, None, key or STEERING, minutes)
        for (project, key), minutes in cards.items()
    ]
    waited = _waited(conn, projects, monday)
    return OwnerTime(
        hours=sum(p.minutes for p in mine) / 60,
        sittings=len({p.sitting for p in mine}),
        days=len({p.at.astimezone().date() for p in mine}),
        actions=dict(actions),
        by_card=sorted(by_card, key=lambda c: c.minutes, reverse=True),
        waited_hours=median(waited) if waited else None,
        waited_items=len(waited),
    )


def owner_time(conn: sqlite3.Connection, projects: list[str], monday: date) -> OwnerTime:
    """The owner's time in the week starting on ``monday`` for ``projects`` (F86 D5), with the
    week before's hours and wait. Sittings are found over every project's actions together;
    each action's minutes count for its own project, so a sitting can split between them."""
    presses = _presses(conn)
    now = _owner_week(conn, projects, monday, presses)
    first = _first_recorded(conn)
    before = monday - timedelta(days=7)
    if first is None or before < first:
        return now
    then = _owner_week(conn, projects, before, presses)
    return replace(now, hours_before=then.hours, waited_hours_before=then.waited_hours)


def week(conn: sqlite3.Connection, projects: list[str], monday: date) -> Week:
    """The week starting on ``monday`` for ``projects``, with the week before; ``owner`` is
    None for a week before the owner's actions were first recorded."""
    previous = _numbers(conn, projects, monday - timedelta(days=7))
    first = _first_recorded(conn)
    owner = owner_time(conn, projects, monday) if first is not None and monday >= first else None
    return replace(_numbers(conn, projects, monday), previous=previous, owner=owner)


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
