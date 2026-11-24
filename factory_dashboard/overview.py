"""The Overview (ADR 13 item 3.1, f1 D3, D4, D7, D8), and the worked example for a page: an
``APIRouter``, its own SQL in plain functions that return data, a template extending
``base.html``, and a chart's data for ``static/charts.js`` (D5).

Top to bottom: Needs you and Now (one htmx partial at ``/live``), the Claude
allowance, and the line on the floor.
"""

import json
import sqlite3
from collections.abc import Collection, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, TypedDict
from urllib.parse import quote

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from factory_dashboard import queries
from factory_dashboard.app import (
    Db,
    Now,
    Project,
    ago,
    factory_status,
    factory_wide_status,
    render,
)
from runner import allowance, loop, metrics
from runner.requests import CHANGE, PLANT, RESERVE, owners_words
from runner.state import State, load_state
from runner.tasks import milestone_order, short_key

if TYPE_CHECKING:
    from factory_dashboard.board import Board  # board.py imports from here
    from factory_dashboard.coming import DeskItem  # coming.py imports from here
    from runner.config import Config

router = APIRouter()

LIVE = timedelta(minutes=2)  # D3: an older heartbeat means the runner stopped
# Now is for the real runs (owner, 2026-10-04): a bench's runs (command 'bench') are left out.
# [claude] in the machine's factory.toml: reserve for the lead starts at 70% of the week.
WEEK_MARK = 0.70
# [claude] in the machine's factory.toml: reserve for you starts at 75% of the 5-hour window.
FIVE_HOUR_MARK = 0.75
FIVE_HOUR = timedelta(hours=5)
WEEK = timedelta(days=7)


def _age(now: datetime, at: str | None) -> timedelta | None:
    return now - datetime.fromisoformat(at) if at else None


def _drain(key: str) -> str:
    """The command that works through the queue: `runner run`, the standing command (ADR 17),
    whichever milestone ``key`` the work is in."""
    return "softfield run"


def every_project(conn: sqlite3.Connection, project: str) -> list[str]:
    """F132 D4: the projects a factory-wide view shows, in the owner's order: those
    ``metrics.projects_in_order`` gives (a forgotten one left out), or ``[project]`` when it
    gives none. Nothing else decides which projects count."""
    return [p.name for p in metrics.projects_in_order(conn)] or [project]


# --- Running now and the runner's heartbeat (D3) ------------------------------------------


@dataclass(frozen=True)
class Running:
    job: int
    role: str
    agent: str
    attempt: int
    ticket: str | None
    title: str | None
    difficulty: int | None
    milestone: str | None
    m_title: str | None
    run_dir: str
    elapsed: timedelta
    heartbeat: timedelta | None  # how long ago the run last beat
    tokens_in: int | None
    tokens_cached: int | None
    steps: int | None
    waiting_until: str | None = None  # ISO time while the run pauses for a limit
    reserve: bool = False  # the owner said yes to Claude's reserve for this command
    project: str = ""  # whose job it is: its plate and its links (F132 D2)

    @property
    def job_card(self) -> dict[str, str] | None:
        """The card a ticketless job works on (F62 D1), from ``job_card``."""
        if self.ticket:
            return None
        return job_card(self.role, self.milestone, self.m_title)

    @property
    def live(self) -> bool:
        return self.heartbeat is not None and self.heartbeat < LIVE

    @property
    def waiting_clock(self) -> str | None:
        return _clock(self.waiting_until)


def _clock(at: str | None) -> str | None:
    return queries.local(at).strftime("%H:%M") if at else None


def attempt_words(job: Running, max_attempts: int | None) -> str | None:
    """The attempt line for the bar or the Now panel, or None when the role doesn't carry
    an attempt meaning a try (planner, review, checkpoint, direction, setup…)."""
    if job.role not in ("developer", "last-attempt", "lead-ticket"):
        return None
    if job.role == "lead-ticket":
        return f"attempt {job.attempt}"
    if max_attempts is None:
        return f"attempt {job.attempt}"
    if job.role == "last-attempt":
        return f"attempt {job.attempt} of {max_attempts}, the last"
    return f"attempt {job.attempt} of {max_attempts}"


@dataclass(frozen=True)
class LiveRun:
    """A live run, for what it does between jobs (f1 D3, amended)."""

    run_dir: str
    activity: str | None
    waiting_until: str | None
    reserve: bool
    title: str | None = None
    project: str = ""

    @property
    def waiting_clock(self) -> str | None:
        return _clock(self.waiting_until)


def live_runs(conn: sqlite3.Connection, project: str, now: datetime) -> list[LiveRun]:
    """Runs that haven't ended and beat less than ``LIVE`` ago, oldest first."""
    rows = conn.execute(
        "SELECT r.run_dir, r.heartbeat, r.activity, r.waiting_until, r.reserve,"
        " p.name AS project_name FROM runs r"
        " JOIN projects p ON p.id = r.project_id"
        " WHERE p.name = ? AND r.ended IS NULL AND r.heartbeat IS NOT NULL"
        " AND coalesce(r.command, '') != 'bench' ORDER BY r.id",
        (project,),
    ).fetchall()
    found: list[LiveRun] = []
    for r in rows:
        age = _age(now, r["heartbeat"])
        if age is None or age >= LIVE:
            continue
        activity = r["activity"]
        title: str | None = None
        if activity and " · " in activity:
            # "waiting for Claude · f2-06-overview-allowances until 01:40"
            parts = activity.split(" · ")
            if len(parts) >= 2:
                ticket_word = parts[1].split()[0]
                trow = conn.execute(
                    "SELECT title FROM tickets WHERE ticket = ? AND project_id = "
                    "(SELECT id FROM projects WHERE name = ?)",
                    (ticket_word, project),
                ).fetchone()
                if trow and trow["title"]:
                    title = trow["title"]
        found.append(
            LiveRun(
                r["run_dir"], r["activity"], r["waiting_until"], bool(r["reserve"]), title, project
            )
        )
    return found


# What a ticketless job does, in one line, by its role (F62 D2); another role has no line.
ROLE_LINES = {
    "review": "The lead reads what {key} built, before it's yours to sign off",
    "planner": "The lead answers you on {key}'s thread",
    "checkpoint": "Claude re-checks {key}'s merged tickets",
    "pre-review": "Copilot reads {key} before the lead's review",
}


def job_card(role: str, milestone: str | None, title: str | None) -> dict[str, str] | None:
    """F62 D1: the card a ticketless job works on, as its upper-case short key, its title
    (``milestones.title``, else empty) and the role's line; None with no card or another role.
    Every place that names a ticketless job's card calls this."""
    line = ROLE_LINES.get(role)
    if not milestone or line is None:
        return None
    key = short_key(milestone).upper()
    return {"key": key, "title": title or "", "line": line.format(key=key)}


def running_jobs(conn: sqlite3.Connection, project: str, now: datetime) -> list[Running]:
    """Every job still ``running``, oldest first, live or not."""
    rows = conn.execute(
        "SELECT j.id, j.role, j.agent, j.attempt, j.started, j.tokens_in, j.tokens_cached, j.steps,"
        " t.ticket, t.title, t.difficulty, m.key AS milestone, m.title AS m_title,"
        " r.run_dir, r.heartbeat, r.waiting_until, r.reserve"
        " FROM jobs j JOIN runs r ON r.id = j.run_id JOIN projects p ON p.id = r.project_id"
        " LEFT JOIN tickets t ON t.id = j.ticket_id"
        " LEFT JOIN milestones m ON m.id = j.milestone_id"
        " WHERE p.name = ? AND j.outcome = 'running' AND coalesce(r.command, '') != 'bench'"
        " ORDER BY j.started, j.id",
        (project,),
    ).fetchall()
    return [
        Running(
            job=row["id"],
            role=row["role"],
            agent=row["agent"],
            attempt=row["attempt"],
            ticket=row["ticket"],
            title=row["title"],
            difficulty=row["difficulty"],
            milestone=row["milestone"],
            m_title=row["m_title"],
            run_dir=row["run_dir"],
            elapsed=_age(now, row["started"]) or timedelta(0),
            heartbeat=_age(now, row["heartbeat"]),
            tokens_in=row["tokens_in"],
            tokens_cached=row["tokens_cached"],
            steps=row["steps"],
            waiting_until=row["waiting_until"],
            reserve=bool(row["reserve"]),
            project=project,
        )
        for row in rows
    ]


def pause_words(conn: sqlite3.Connection, project: str, now: datetime) -> str | None:
    """The owner's pause for Now, in the top bar's own words (f28-02): held, asked, or a
    resume asked; None otherwise. The top bar holds the one Pause/Resume button."""
    status = factory_status(conn, project, now)
    return status.words if status.button == "resume" or status.words == "Resuming…" else None


def runner_live(conn: sqlite3.Connection, project: str, now: datetime) -> bool:
    """A run that hasn't ended and beat less than ``LIVE`` ago."""
    return bool(live_runs(conn, project, now))


# --- the queue (D4) -----------------------------------------------------------------------


@dataclass(frozen=True)
class Queued:
    ticket: str
    title: str | None
    kind: str | None
    difficulty: int | None
    milestone: str | None
    waits_for: str | None = None
    project: str = ""


def queue(
    conn: sqlite3.Connection,
    project: str,
    now: datetime,
) -> list[Queued]:
    """Tickets whose dependencies are all done first, then the waiting ones, in
    the order ``pick_next`` would take them (the queue's place first, F222 D5).  Tickets with
    a running job are excluded."""
    rows = conn.execute(
        "SELECT t.ticket, t.title, t.kind, t.difficulty, t.depends_on, m.key AS milestone"
        " FROM tickets t"
        " JOIN projects p ON p.id = t.project_id"
        " LEFT JOIN milestones m ON m.id = t.milestone_id"
        " WHERE p.name = ? AND t.state = 'ready'",
        (project,),
    ).fetchall()
    # Tickets with a running job are excluded.
    running = {
        row["ticket"]
        for row in conn.execute(
            "SELECT t.ticket FROM jobs j"
            " JOIN runs r ON r.id = j.run_id"
            " JOIN projects p ON p.id = r.project_id"
            " JOIN tickets t ON t.id = j.ticket_id"
            " WHERE p.name = ? AND j.outcome = 'running'",
            (project,),
        ).fetchall()
    }
    # Live runs whose activity starts with "waiting for Claude".
    live = live_runs(conn, project, now)
    waiting_claude = any(
        act and act.startswith("waiting for Claude") for act in (r.activity for r in live)
    )
    # All ticket states keyed by ticket id for depends_on lookups.
    all_states = {
        row["ticket"]: row["state"]
        for row in conn.execute(
            "SELECT t.ticket, t.state FROM tickets t"
            " JOIN projects p ON p.id = t.project_id"
            " WHERE p.name = ?",
            (project,),
        ).fetchall()
    }
    done = {tid for tid, st in all_states.items() if st == "done"}
    places = queries.board_places(conn, project)
    found: list[Queued] = []
    for r in rows:
        if r["ticket"] in running:
            continue
        waits: str | None = None
        if r["kind"] == "lead" and waiting_claude:
            waits = "waits for Claude"
        elif r["depends_on"]:
            deps = json.loads(r["depends_on"])
            for dep in deps:
                if dep not in done:
                    dep_state = all_states.get(dep, "unknown")
                    if dep_state == "escalated":
                        waits = f"waits for {dep}'s escalation"
                    else:
                        waits = f"waits for {dep}"
                    break
        found.append(
            Queued(
                ticket=r["ticket"],
                title=r["title"],
                kind=r["kind"],
                difficulty=r["difficulty"],
                milestone=r["milestone"],
                waits_for=waits,
                project=project,
            )
        )
    ready_now = [q for q in found if q.waits_for is None]
    waiting = [q for q in found if q.waits_for is not None]

    def order(q: Queued) -> tuple[int, tuple[str, int], str]:
        own = queries.place(places, queries.place_key(q.milestone, q.ticket))
        return own, milestone_order(q.milestone or "m0"), q.ticket

    return sorted(ready_now, key=order) + sorted(waiting, key=order)


# --- queued support jobs ------------------------------------------------------------------


@dataclass(frozen=True)
class QueuedJob:
    kind: str  # plain words: "Checkpoint", "Review", etc.
    subject: str
    reason: str
    waits: str | None = None
    message: str | None = None  # truncated message preview for Planning rows
    title: str | None = None  # plant title for Plant rows
    cancelled: bool = False  # a plant the owner cancelled, the runner yet to take it (F14)
    lane: bool = False  # a direction or escalation of a fast lane ticket: in its bay (F172 D9)
    project: str = ""


CANCELLING = "cancelling at the runner's next pick"


@dataclass(frozen=True)
class Change:
    """An open ``change`` on a waiting request (F14 D1), as its row shows it at once."""

    id: int  # the change's own request: its status polls
    cancel: bool
    title: str  # an edit's new title; "" for a cancel, or for words that give none


def open_changes(conn: sqlite3.Connection, project_id: int) -> dict[str, Change]:
    """The open changes by the id of the request each names. The runner applies them in
    order (F14 D2): a cancel wins, then the latest edit."""
    rows = conn.execute(
        "SELECT id, subject, value FROM owner_requests"
        " WHERE project_id = ? AND kind = ? AND done IS NULL ORDER BY id",
        (project_id, CHANGE),
    ).fetchall()
    found: dict[str, Change] = {}
    for r in rows:
        subject = str(r["subject"] or "")
        if subject in found and found[subject].cancel:
            continue
        try:
            cancel = json.loads(r["value"] or "") == {"cancel": True}
        except json.JSONDecodeError:
            cancel = False
        # an edit carries a plant's words: read as leniently as the plant's own
        words = owners_words({"kind": PLANT, "subject": None, "value": r["value"]})
        found[subject] = Change(r["id"], cancel, words.title if words and not cancel else "")
    return found


def queued_jobs(
    conn: sqlite3.Connection,
    project: str,
    now: datetime,
    *,
    first: Collection[str] = frozenset(),
    card_keys: Collection[str] = frozenset(),
) -> list[QueuedJob]:
    """The project's open ``work_queue`` rows, minus those whose ``started_job`` is still
    running, each with the order and wait from ``dispatch.plan``, a direction or escalation of
    ``first``'s tickets (the fast lane's) on top. Also includes open plant requests from
    ``owner_requests``. Escalations, directions and reviews whose subject starts with a
    ``card_keys`` short key (F191 D3, F242 D4) are treated as fast-lane rows even when the lane
    has no ready ticket."""
    from runner import dispatch

    found_project = conn.execute("SELECT id FROM projects WHERE name = ?", (project,)).fetchone()
    # a project the runner never ran yet has no row, and nothing queued (f8 review)
    rows = metrics.open_jobs(conn, found_project["id"]) if found_project else []
    # Leave out a row whose started_job is a job still running.
    running_jobs = {
        row["id"]
        for row in conn.execute(
            "SELECT j.id FROM jobs j"
            " JOIN runs r ON r.id = j.run_id"
            " JOIN projects p ON p.id = r.project_id"
            " WHERE p.name = ? AND j.outcome = 'running'",
            (project,),
        ).fetchall()
    }
    open_queues = [
        row for row in rows if row["started_job"] is None or row["started_job"] not in running_jobs
    ]
    queued = [dispatch.Queued.from_row(row) for row in open_queues]
    # Escalations, directions and reviews for a fast-lane card whose ticket has left ready/
    # (F191 D3, F242 D4).
    if card_keys:
        lane_subjects: set[str] = set()
        for q in queued:
            if (
                q.kind in dispatch.LANE_KINDS
                and q.subject not in first
                and any(q.subject.upper().startswith(k + "-") for k in card_keys)
            ):
                lane_subjects.add(q.subject)
        first = set(first) | lane_subjects
    plan = dispatch.plan(queued, [], dispatch.Windows(), now, first=first)
    found: list[QueuedJob] = []
    for line in plan:
        pick = line.pick
        kind_map = {
            dispatch.CHECKPOINT: "Checkpoint",
            dispatch.REVIEW: "Review",
            dispatch.DIRECTION: "Direction",
            dispatch.ESCALATION: "Escalation",
            dispatch.PLANNER: "Planning",
        }
        plain = kind_map.get(pick.kind, pick.kind)
        # For Planning rows, look up the message from owner_requests.
        message: str | None = None
        if plain == "Planning" and pick.subject and "#" in pick.subject:
            request_id_str = pick.subject.rpartition("#")[2]
            if request_id_str.isdigit():
                req = conn.execute(
                    "SELECT value FROM owner_requests WHERE id = ?",
                    (int(request_id_str),),
                ).fetchone()
                if req and req["value"]:
                    data = (
                        json.loads(req["value"]) if isinstance(req["value"], str) else req["value"]
                    )
                    if isinstance(data, dict):
                        text = data.get("text", "")
                        if not text:
                            comments = data.get("comments", {})
                            if comments:
                                text = next(iter(comments.values()), "")
                        if text:
                            message = text
        lane = pick.kind in dispatch.LANE_KINDS and pick.subject in first
        found.append(
            QueuedJob(
                plain, pick.subject, pick.reason, line.waits, message, lane=lane, project=project
            )
        )
    # Open plant requests from owner_requests.
    plant_rows = conn.execute(
        "SELECT owner_requests.id, kind, subject, value FROM owner_requests"
        " JOIN projects p ON p.id = owner_requests.project_id"
        " WHERE p.name = ? AND kind = 'plant' AND done IS NULL"
        " ORDER BY owner_requests.id",
        (project,),
    ).fetchall()
    changes = open_changes(conn, found_project["id"]) if found_project else {}
    for pr in plant_rows:
        words = owners_words(pr)  # leniently: the dashboard stores any value
        title = (words.title if words else "") or "Your idea"
        change = changes.get(str(pr["id"]))
        if change is not None and change.cancel:
            found.append(
                QueuedJob("Plant", title, CANCELLING, title=title, cancelled=True, project=project)
            )
            continue
        reason = "at the runner's next pick"
        if change is not None:
            title, reason = change.title or title, f"changed · {reason}"
        found.append(QueuedJob("Plant", title, reason, title=title, project=project))
    return found


# --- Needs you (D8) -----------------------------------------------------------------------


REVIEW_STOP = "review-stop"  # the runner's owner item when a review stopped


@dataclass(frozen=True)
class Need:
    id: str  # stable while the need is open, so notify.js tells a new one (f5-12)
    kind: str
    text: str
    command: str | None = None
    ticket: str | None = None
    subject: str | None = None
    project: str = ""
    on_its_way: bool = False  # the owner answered it; the runner takes it at its next pick


def needs_you(
    conn: sqlite3.Connection,
    project: str,
    now: datetime,
    jobs: list[Running],
    waiting: list[Queued],
) -> list[Need]:
    """Open owner items, newest first; then what the dashboard sees itself: a runner whose
    heartbeat stopped mid-job (a dead runner can't write that), and a queue left waiting."""
    items = conn.execute(
        "SELECT o.id, o.kind, o.subject, o.text, o.command FROM owner_items o"
        " JOIN projects p ON p.id = o.project_id WHERE p.name = ? AND o.resolved IS NULL"
        " ORDER BY o.created DESC, o.id DESC",
        (project,),
    ).fetchall()
    asked = {
        r["subject"]
        for r in conn.execute(
            "SELECT r.subject FROM owner_requests r JOIN projects p ON p.id = r.project_id"
            " WHERE p.name = ? AND r.kind = 'review_again' AND r.done IS NULL",
            (project,),
        )
    }
    found = [
        Need(
            f"{project}/owner-{i['id']}",
            i["kind"],
            i["text"] or i["subject"],
            # a stopped review is started again with its button, never a command (F97)
            None if i["kind"] == REVIEW_STOP else i["command"],
            None,
            i["subject"],
            project,
            on_its_way=i["kind"] == REVIEW_STOP and i["subject"] in asked,
        )
        for i in items
    ]
    stopped: dict[str, Running] = {}
    for job in jobs:
        if not job.live:
            stopped.setdefault(job.run_dir, job)
    for job in stopped.values():
        when = f" {ago(job.heartbeat)} ago" if job.heartbeat else ""
        found.append(
            Need(
                f"{project}/runner-{job.run_dir}",
                "runner",
                f"The runner's heartbeat stopped{when} mid-job: a crash or a closed terminal."
                " Rerun it; it picks up where it stopped.",
                _drain(job.milestone) if job.milestone else None,
                ticket=job.ticket,
                project=project,
            )
        )
    # one runner serves every project (ADR 30): it is idle only with no project's run live
    if waiting and not any(runner_live(conn, p, now) for p in every_project(conn, project)):
        n = len(waiting)
        text = f"{n} ticket{'s' if n != 1 else ''} waiting and the runner is idle."
        command = _drain(waiting[0].milestone or "")
        found.append(Need(f"{project}/queue", "queue", text, command, project=project))
    return found


# --- notices (D1: f114-01) ---------------------------------------------------


class Notices(TypedDict):
    title: str
    body: str
    link: str


def notices(
    open_needs: list[Need],
    card_titles: dict[str, str],
    project: str,
    proposals: Sequence["DeskItem"],
) -> dict[str, Notices]:
    """For every open need, its title, body and link, worded from the item's kind and its card.

    The card's title comes from ``card_titles``; a card with no title in the database shows its
    key.  The general thread is titled "General".
    """

    found: dict[str, Notices] = {}
    for need in open_needs:
        if need.kind == "planning":
            card = need.subject or need.id
            title = card_titles.get(card, card)
            if card == "general":
                title = "General"
            if need.text and need.text.startswith("The lead couldn't answer"):
                found[need.id] = {
                    "title": f"The lead couldn't answer: {title}",
                    "body": "Send your message again",
                    "link": f"/planning/{card}?project={quote(project)}",
                }
                continue
            # Count open proposals for this card (not on their way).
            count = sum(
                sum(1 for part in p.parts if not part.on_its_way) or 1  # one item a card (F51)
                for p in proposals
                if p.link.startswith(f"/planning/{card}/proposals/") and not p.on_its_way
            )
            if count == 0:
                body = "Your answer is wanted"
            elif count == 1:
                body = "1 proposal to review"
            else:
                body = f"{count} proposals to review"
            found[need.id] = {
                "title": f"The lead replied: {title}",
                "body": body,
                "link": f"/planning/{card}?project={quote(project)}",
            }
        elif need.kind == "signoff":
            key = short_key(need.subject or need.id)
            title = card_titles.get(key, key)
            found[need.id] = {
                "title": f"Ready for your sign-off: {title}",
                "body": "Reviewed, waits for you",
                "link": f"/planning/{key}?project={quote(project)}",
            }
        elif need.kind == REVIEW_STOP:
            key = short_key(need.subject or need.id)
            title = card_titles.get(key, key)
            found[need.id] = {
                "title": f"The review stopped: {title}",
                "body": need.text,
                "link": f"/planning/{key}?project={quote(project)}",
            }
        else:  # a kind not named here still notifies (F114 review F1)
            found[need.id] = {
                "title": _OVERVIEW_TITLES.get(need.kind, NEEDS_YOU),
                "body": need.text,
                "link": f"/?project={quote(project)}",
            }
    return found


NEEDS_YOU = "Something needs you"
# The items that open the Overview, by kind (D1); all the work done is notify.js's own
_OVERVIEW_TITLES = {
    "adr": "A decision for you",
    "push": "A push to GitHub waits",
    "blocked": "A ticket is blocked",
    "escalated": "A ticket is blocked",
    "reserve": "Claude's allowance: your choice",
    "five-hour": "Claude's allowance: your choice",
    loop.MAIN_RED_KIND: "A check fails on main",
    "runner": "The runner stopped",
    "queue": "The runner is idle",
}


# --- the allowance ---------------------------------------------


@dataclass(frozen=True)
class WindowAllowance:
    """One window's allowance for one agent group."""

    label: str  # e.g. "Claude", "Copilot"
    window: str  # e.g. "five_hour", "seven_day", "month"
    display: str  # e.g. "5-hour window", "week", "month"
    value: float | None  # 0..1 from reading, or None
    resets_at: str | None  # ISO time
    percent: str | None  # e.g. "80%"
    mark: float | None  # threshold mark (0..1) or None
    mark_label: str | None  # explanation of the mark
    reset_label: str | None  # e.g. "resets at 17:00" or "resets on Oct 9"
    read_label: str | None  # e.g. "read at 03:59" or "read on Oct 26 22:10"
    status: str | None  # e.g. "reset since, no new reading" or "no data yet"
    read_at: str | None = None  # ISO time of the reading (the row's `at`)
    rate: str | None = None  # F61 D1: "at this rate: out Thu 13:38, 3 days 3 h before the reset"
    rate_out: bool = False  # the window runs out before its reset: the warn ink
    ahead: float | None = None  # F61 D4: projected use at the reset (0..1), the ghost's end


NO_DATA = "no data yet"
RESET_SINCE = "reset since, no new reading"


def _reset_label(resets: datetime, now: datetime) -> str:
    """A reading's reset: "resets at 17:00" later today, "resets on Oct 9 12:00" later on."""
    if resets.date() == now.astimezone().date():
        return f"resets at {resets:%H:%M}"
    return f"resets on {resets:%b} {resets.day} {resets:%H:%M}"


def forecast(
    value: float, read_at: datetime, resets_at: datetime, length: timedelta, now: datetime
) -> tuple[datetime | None, float] | None:
    """F61 D2, D3: when the window runs out at this rate, and its use at the reset.

    The rate is the reading over the time from the window's start (``resets_at`` minus
    ``length``) to the reading. Returns ``(out_time, use_at_reset)``, ``out_time`` none when
    the window lasts to its reset and ``use_at_reset`` capped at 1; or none when less than 10%
    of the window had passed at the reading, or the reading is 0. ``now`` isn't used: the
    reading's own time is.
    """
    elapsed = (read_at - (resets_at - length)).total_seconds()
    if elapsed < length.total_seconds() * 0.1 or value <= 0:
        return None
    rate = value / elapsed
    out_time = read_at + timedelta(seconds=max(1.0 - value, 0.0) / rate)
    use_at_reset = min(value + rate * (resets_at - read_at).total_seconds(), 1.0)
    return (out_time if out_time < resets_at else None, use_at_reset)


def _gap(span: timedelta) -> str:
    """F61 D1: "3 days 3 h", "1 day", "5 h", or "40 min" under an hour."""
    if span < timedelta(minutes=59, seconds=30):
        return f"{max(round(span.total_seconds() / 60), 1)} min"
    days, hours = divmod(round(span.total_seconds() / 3600), 24)
    words = [f"{days} day{'s' if days != 1 else ''}"] if days else []
    return " ".join(words + ([f"{hours} h"] if hours else []))


def _rate_line(
    value: float, read_at: datetime, resets: datetime, length: timedelta, now: datetime
) -> tuple[str, bool, float] | None:
    """F61 D1: one Claude meter's "at this rate" words, whether it runs out before the reset,
    and the ghost's end; none when it is too early to tell."""
    projected = forecast(value, read_at, resets, length, now)
    if projected is None:
        return None
    out, use_at_reset = projected
    if out is None:
        return (
            f"at this rate: lasts to the reset, about {use_at_reset:.0%} by then",
            False,
            use_at_reset,
        )
    if out <= now:
        return "at this rate: out any time now", True, use_at_reset
    when = f"{out:%H:%M}" if out - now < timedelta(hours=24) else f"{out:%a %H:%M}"
    return f"at this rate: out {when}, {_gap(resets - out)} before the reset", True, use_at_reset


def _read_label(at: datetime, now: datetime) -> str:
    """A reading's time: "read at 03:59" today, "read on Oct 26 22:10" otherwise."""
    if at.date() == now.astimezone().date():
        return f"read at {at:%H:%M}"
    return f"read on {at:%b} {at.day} {at:%H:%M}"


def _agent_allowances(
    conn: sqlite3.Connection,
    agent_prefix: str,
    agent_label: str,
    windows: list[tuple[str, str, float | None, str | None]],
    now: datetime,
) -> list[WindowAllowance]:
    """One agent group's rows (Claude, Copilot), from its latest reading per window.

    ``windows`` is a list of (window_key, display_label, mark_or_None, mark_label_or_None).
    """
    readings = metrics.latest_readings(conn, agent_prefix)
    rows: list[WindowAllowance] = []
    for wkey, wdisplay, mark, mlabel in windows:
        row = readings.get(wkey)
        value = None if row is None else row["value"]
        resets_at = None if row is None else row["resets_at"]
        at = None if row is None else row["at"]
        resets = queries.local(resets_at) if resets_at else None
        read_at = queries.local(at) if at else None
        if value is None:
            status: str | None = NO_DATA
        elif resets is not None and resets <= now:
            status, value = RESET_SINCE, None  # the reading is stale: no percentage
        else:
            status = None
        # F61 D5: Claude's two windows only, and only on a fresh reading (D3)
        rate = None
        if agent_label == "Claude" and status is None and value and read_at and resets:
            rate = _rate_line(
                value, read_at, resets, FIVE_HOUR if wkey == "five_hour" else WEEK, now
            )
        rows.append(
            WindowAllowance(
                label=agent_label,
                window=wkey,
                display=wdisplay,
                value=value,
                resets_at=resets_at,
                percent=None if value is None else f"{value:.0%}",
                mark=mark,
                mark_label=mlabel,
                reset_label=_reset_label(resets, now) if resets and status is None else None,
                read_label=_read_label(read_at, now) if read_at else None,
                status=status,
                read_at=at,
                rate=rate[0] if rate else None,
                rate_out=bool(rate and rate[1]),
                ahead=rate[2] if rate else None,
            )
        )
    return rows


def agent_allowances(conn: sqlite3.Connection, now: datetime) -> list[WindowAllowance]:
    """Every agent group's allowance, one row per window."""
    claude = _agent_allowances(
        conn,
        queries.LEAD_PREFIX,
        "Claude",
        [
            ("five_hour", "5-hour window", FIVE_HOUR_MARK, "lead tickets go last from here"),
            ("seven_day", "week", WEEK_MARK, "lead tickets go last from here"),
        ],
        now,
    )
    copilot = _agent_allowances(
        conn,
        "copilot-",
        "Copilot",
        [
            ("month", "month", None, None),
        ],
        now,
    )
    return claude + copilot


# Claude's windows each have the owner's reserve switch (f8 D4): allowance window -> switch
SWITCH_OF = {"five_hour": loop.FIVE_HOUR, "seven_day": loop.WEEK}


@dataclass
class Switch:
    """One reserve switch beside its Claude meter."""

    name: str  # "week" or "five_hour": the reserve request's subject
    label: str  # the runner's words for it (`loop.SWITCHES`)
    until: str | None  # "Mon 21:40" while it is on, as `set_switch` words it; None when off
    asked: str | None  # "on" or "off": the owner's latest request the runner hasn't taken


def _runner_state(conn: sqlite3.Connection, project: str) -> tuple["Config | None", State | None]:
    """The project's config and the runner's state.json (in the config's ``runs_dir``, found as
    ``line._config`` finds the config): None for each that can't be read."""
    from factory_dashboard.line import _config  # line.py imports LIVE from here

    config = _config(conn, project)
    try:
        state = load_state(config.runs_dir / "state.json") if config else None
    except (OSError, ValueError):  # unreadable: shown off, as the runner's own would be lost
        state = None
    return config, state


def reserve_switches(conn: sqlite3.Connection, project: str, now: datetime) -> dict[str, Switch]:
    """Each Claude window's switch, by allowance window, from the runner's state.json: no config
    or no file and both are off. A switch asked for shows at once (owner, 2026-10-07)."""
    _, state = _runner_state(conn, project)
    asked = {
        row["subject"]: row["value"]
        for row in conn.execute(
            "SELECT r.subject, r.value FROM owner_requests r"
            " JOIN projects p ON p.id = r.project_id"
            " WHERE p.name = ? AND r.done IS NULL AND r.kind = ? ORDER BY r.id",
            (project, RESERVE),
        )
    }
    switches = {}
    for window, name in SWITCH_OF.items():
        until = None
        if state is not None and loop.switch_on(state, name, now):
            ends = queries.local(state.switches[name])
            until = f"{ends + timedelta(hours=loop.USE_RESERVE_HOURS):%a %H:%M}"
        switches[window] = Switch(name, loop.SWITCHES[name], until, asked.get(name))
    return switches


@dataclass(frozen=True)
class WeekPace:
    """What the week meter says about the pace that holds lead tickets back (F9, f9-29)."""

    state: str  # "on" pace, "over" it, or "last" hours (the last 10% of the week)
    post: float | None  # today's pace line, 0..1: the post; None in the last hours
    used: float  # 0..1: the stretch past ``post`` is hazard-striped
    pace: str  # "33%"
    until: str | None  # "Sun 8 Nov 04:00": when lead tickets go on again, or the reset
    full: bool = False  # in the last hours with the week all used
    limit: bool = False  # at Claude's real limit (100% or a rest)


@dataclass(frozen=True)
class ClaudePace:
    """The week's pace, and the words a held lead ticket's row carries."""

    week: WeekPace | None
    row: str | None  # "goes when nothing else can", "waits for Claude until about Mon 16:00"


def _day_time(at: datetime) -> str:
    at = at.astimezone()
    return f"{at:%a} {at.day} {at:%b %H:%M}"


def claude_pace(conn: sqlite3.Connection, project: str, now: datetime) -> ClaudePace:
    """Claude's week pace as the runner decides it: the windows from the latest readings and
    refusals with their reserves (the config's, else the marks above), the owner's levers from
    state.json, and ``allowance.lead_hold``, ``pace_line`` and ``lead_goes_at`` for every
    answer, so the page can't disagree with the pick."""
    config, state = _runner_state(conn, project)
    kept = {
        "seven_day": config.claude_reserve if config else 1 - WEEK_MARK,
        "five_hour": config.five_hour_reserve if config else 1 - FIVE_HOUR_MARK,
    }
    refusals = metrics.refusals(conn, queries.LEAD_PREFIX)
    windows = [
        loop._rested(replace(w, reserve=kept.get(w.name, 0.0)), refusals, now)
        for w in loop._windows_from(metrics.latest_readings(conn, queries.LEAD_PREFIX), now)
    ]
    reserves = {
        name
        for name, switch in (("seven_day", loop.WEEK), ("five_hour", loop.FIVE_HOUR))
        if state is not None and loop.switch_on(state, switch, now)
    }
    cost = loop.LEAD_COST
    week = next((w for w in windows if w.name == "seven_day"), None)
    pace: WeekPace | None = None
    if week is not None and week.name not in reserves and not allowance.resting(week, now):
        line = allowance.pace_line(week, now)
        capacity = week.capacity or 1.0
        used = week.used / capacity
        at_limit = week.used >= week.capacity - allowance.EPS if week.capacity else False
        if allowance.in_sweep(week, now):
            ends = week.resets_at
            pace = WeekPace(
                "last",
                None,
                used,
                "",
                _day_time(ends) if ends else None,
                full=week.used >= capacity - allowance.EPS,
            )
        elif line is not None:
            held = allowance.lead_hold(loop.CLAUDE, [week], cost, now) is not None
            goes = allowance.lead_goes_at(week, cost, now) if held else None
            pace = WeekPace(
                "over" if held else "on",
                min(line / capacity, 1.0),
                used,
                f"{line / capacity:.0%}",
                _day_time(goes) if goes else None,
                limit=at_limit,
            )
    # The pick's own two questions (ADR 50 items 2, 3 and 7): the real limit holds, the pace
    # line and the marks only order.
    row = None
    if loop._held_at_the_limit(dispatch_windows(windows, reserves), now) is not None:
        full = [
            w
            for w in windows
            if allowance.lead_hold(loop.CLAUDE, [w], loop.FULL, now, reserves=loop.AT_THE_LIMIT)
        ]
        known = [e for w in full if (e := allowance.lead_goes_at(w, loop.FULL, now)) is not None]
        until = f" until about {max(known).astimezone():%a %H:%M}" if known else ""
        row = f"waits for Claude{until}"
    elif allowance.lead_hold(loop.CLAUDE, windows, cost, now, reserves=reserves) is not None:
        row = "goes when nothing else can"
    return ClaudePace(pace, row)


def dispatch_windows(windows: list[allowance.Window], reserves: Collection[str]) -> Any:
    """The runner's `Windows` for what `loop._held_at_the_limit` reads."""
    from runner import dispatch

    return dispatch.Windows(windows, None, reserves)


def fast_lane(
    rows: Sequence[dict[str, Any]], keys: Collection[str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """The run order's ticket rows split into the fast lane's and the rest (F172 D9), each kept
    in order: a ticket of a card in ``keys`` (short keys in capitals), and every ticket a lane
    ticket still waits for, whatever its card, as the runner's ``loop.reserve_cards`` does."""
    by_id = {str(r["ticket"]): r for r in rows if r.get("ticket")}
    todo = [t for t, r in by_id.items() if short_key(str(r["milestone"])).upper() in keys]
    found: set[str] = set()
    while todo:
        ticket = todo.pop()
        if ticket in by_id and ticket not in found:
            found.add(ticket)
            todo.extend(by_id[ticket].get("waits") or [])
    lane = [r for r in rows if r.get("ticket") in found]
    return lane, [r for r in rows if r.get("ticket") not in found]


# --- the routes ---------------------------------------------------------------------------


def _live_context(
    conn: sqlite3.Connection,
    project: str,
    now: datetime,
    *,
    line: dict[str, Any] | None = None,
    cards: "Board | None" = None,
) -> dict[str, object]:
    """What the ``/live`` partial draws: Needs you, then Now (what works and the next three in
    the run order), for the whole factory (F132 D2): every project's, the same whichever
    project is picked. ``line`` and ``cards`` are the picked project's, when handed in."""
    from factory_dashboard.coming import _card_titles  # coming.py imports from overview
    from factory_dashboard.line import _config
    from factory_dashboard.planning import _open_proposals  # planning.py imports from overview
    from runner import metrics

    names = every_project(conn, project)
    found = {
        name: _project_live(
            conn,
            name,
            now,
            line=line if name == project else None,
            cards=cards if name == project else None,
        )
        for name in names
    }
    # the picked project's own: the Planning tab's count, its notices, the reserve's cards
    own = found.get(project) or _project_live(conn, project, now, line=line, cards=cards)
    every = [found[name] for name in names]
    pace = claude_pace(conn, project, now)

    # Now (F132): every project's live job; with none, one line for the runner, the run the
    # top bar names
    jobs = sorted(
        (job for p in every for job in p.jobs if job.live), key=lambda j: j.elapsed, reverse=True
    )
    # F272 D2: each job's attempt pill, the bar's words; a project's config read only for a try
    job_pills: dict[int, str | None] = {}
    for job in jobs:
        tries = job.role in ("developer", "last-attempt") and job.project
        config = _config(conn, job.project) if tries else None
        job_pills[job.job] = attempt_words(job, config.max_attempts if config else None)
    status = factory_wide_status(conn, project, now)
    leading = status.project or project
    runs = [] if jobs else live_runs(conn, leading, now)[:1]

    # Next in line, in the runner's order (D5): every project's lane, its queued jobs, then the
    # tickets that can run project by project, then the waiting ones
    lane = [r for p in every for r in p.lane][:3]
    # each project's own run order kept (live_line's): up to its last row that can run, the rest
    ends = {
        p.name: max(
            (n for n, r in enumerate(p.rest, start=1) if not _held(r, p.waits, pace.row)),
            default=0,
        )
        for p in every
    }
    free = [r for p in every for r in p.rest[: ends[p.name]]]
    held = [r for p in every for r in p.rest[ends[p.name] :]]
    upcoming = [{**r, "number": n} for n, r in enumerate([*lane, *free, *held][:3], start=1)]
    passed = []
    if free:  # a project ahead of the first that can run is passed over, with why
        for p in every:
            if ends[p.name]:
                break
            first = next((r for r in p.rest if r.get("ticket")), None)
            if first is not None:
                why = _held(first, p.waits, pace.row)
                passed.append({"project": p.name, "ticket": first["ticket"], "waits": why})
    # F124-03: paused projects don't contribute tickets to Next in line
    paused = []
    paused_names: set[str] = set()
    for p in every:
        if p.paused:
            paused_names.add(p.name)
            paused.append({"project": p.name, "paused_since": p.paused})
    tickets = [q for p in every for q in p.queued if p.name not in paused_names]
    counts = [(p.name, len(p.queued)) for p in every if p.queued and p.name not in paused_names]

    # Needs you (D6, F97 D2): one desk plate a project with something on it (its count, no
    # titles), then every project's other items
    desks = [{"project": p.name, "count": len(p.items)} for p in every if p.items]
    # F97 D3: what stops the line shows in Now, not in Needs you
    stops = ("runner", "queue", loop.MAIN_RED_KIND)
    line_stops = [n for p in every for n in p.needs if n.kind in stops]
    needs = [n for p in every for n in p.needs if n.kind not in stops]

    # D1: word each notice from the item's kind and its card
    project_id = metrics.find_project(conn, project)
    card_titles: dict[str, str] = {}
    proposals: Sequence[DeskItem] = []
    if project_id is not None:
        card_titles = _card_titles(conn, project_id)
        proposals = _open_proposals(conn, project_id, now)
    notice_data = notices(own.open_needs, card_titles, project, proposals)
    # Cross-project notices: every other project's open items, prefixed with project name
    for name in names:
        if name == project:
            continue
        other_id = metrics.find_project(conn, name)
        if other_id is None:
            continue
        other_items = metrics.open_owner_items(conn, other_id)
        if not other_items:
            continue
        other_needs: list[Need] = []
        for i in other_items:
            other_needs.append(
                Need(
                    f"owner-{i['id']}",
                    i["kind"],
                    i["text"] or i["subject"],
                    i["command"],
                    None,
                    i["subject"],
                )
            )
        other_notices = notices(
            other_needs,
            _card_titles(conn, other_id),
            name,
            _open_proposals(conn, other_id, now),
        )
        for oid, notice in other_notices.items():
            key = f"{name}/{oid}"
            notice["title"] = f"{name}: {notice['title']}"
            notice_data[key] = notice
    return {
        "needs": needs,
        "line_stops": line_stops,
        "desks": desks,
        "planning_count": len(own.items),  # the Planning tab's count, refreshed by /live
        "notices": notice_data,
        "all_done": not any(p.queued or p.jobs_queued or p.jobs for p in every),
        "running": jobs,
        "job_pills": job_pills,
        "runs": runs,
        # the owner's pause on Now (f5-18), as the top bar words it (f28-02)
        "pause_words": pause_words(conn, leading, now),
        "queue": tickets,
        "queue_counts": counts,  # each project's share of the count (D5)
        "lane": upcoming[: len(lane)],
        "next": upcoming[len(lane) :],
        "passed": passed,
        "paused": paused,
        "queued_jobs": [j for p in every for j in p.jobs_queued],
        # Claude's allowance and its reserve switches, below Now (f8-06)
        "allowance": agent_allowances(conn, now),
        "switches": reserve_switches(conn, project, now),
        "reserve_cards": own.reserve_cards,  # named under them (F172 D6)
        "pace": pace.week,  # the week meter's post and plate (f9-29)
        "lead_holds": pace.row,  # what a held lead ticket's row says
    }


@dataclass(frozen=True)
class _ProjectLive:
    """One project's share of the live part (F132): its jobs, its tickets and queued jobs, its
    Next in line rows (the lane's and the rest, each with its project and why it waits), its
    open needs and its desk."""

    name: str
    jobs: list[Running]
    queued: list[Queued]
    waits: dict[str, str]  # ticket -> what it waits for, as `queue` words it
    jobs_queued: list[QueuedJob]
    lane: list[dict[str, Any]]
    rest: list[dict[str, Any]]
    open_needs: list[Need]
    needs: list[Need]  # what Needs you lists: the desk's line stands for the rest
    items: list["DeskItem"]  # the desk's items waiting for the owner
    reserve_cards: list[Any]
    paused: str | None = None  # ISO time paused by you, None otherwise


def _project_live(
    conn: sqlite3.Connection,
    project: str,
    now: datetime,
    *,
    line: dict[str, Any] | None = None,
    cards: "Board | None" = None,
) -> _ProjectLive:
    """``project``'s share of the live part, its board and floor built once (F228) unless
    handed in."""
    from factory_dashboard.board import board, reserve_marked  # board.py imports from here
    from factory_dashboard.line import live_line  # line.py imports LIVE from here
    from factory_dashboard.planning import desk, waiting_for_you  # planning imports overview

    jobs = running_jobs(conn, project, now)
    all_queued = queue(conn, project, now)
    # Mapping from ticket id to its ``waits_for`` reason, for tickets whose dependency isn't done.
    waits: dict[str, str] = {q.ticket: q.waits_for for q in all_queued if q.waits_for is not None}
    if cards is None:
        cards = board(conn, project, now)
    if line is None:
        line = live_line(conn, project, now.astimezone(), cards=cards)
    # the fast lane's tickets, and their directions and escalations, go first (F172 D9)
    reserve_cards = reserve_marked(conn, project, now, found=cards)
    # as the runner will once it applies the requests: a card asked out has left (F192 D4)
    lane_keys = {c.key for c in reserve_cards if c.lane_asked != "off"}
    lane, rest = fast_lane(line["queue"], lane_keys)
    lane_ids = {str(r["ticket"]) for r in lane}
    # "on its way" only on a row of the card asked in, not on a ticket it waits for elsewhere
    asked_in = {c.key for c in reserve_cards if c.lane_asked in ("on", "first")}
    # an escalated lane ticket's row goes by the same cards as its ticket rows (F191 D3)
    qjobs = queued_jobs(conn, project, now, first=lane_ids, card_keys=lane_keys)

    def mine(r: dict[str, Any]) -> dict[str, Any]:
        return {**r, "project": project, "waits_for": waits.get(str(r.get("ticket")))}

    lane = [
        {
            **mine(r),
            "card": r.get("card") or short_key(str(r["milestone"])).upper(),
            "on_its_way": short_key(str(r["milestone"])).upper() in asked_in,
        }
        for r in lane[:3]
    ]
    open_needs = needs_you(conn, project, now, jobs, all_queued)
    # the desk's entry stands for its answers wanted, its sign-offs and its blocked tickets, so no
    # lead reply (f6-09), no stored sign-off row (f95-01) and no blocked row shows on its own
    needs = [n for n in open_needs if n.kind not in ("planning", "signoff", "blocked")]
    items = waiting_for_you(desk(conn, project, now, line=line))  # acted on waits on no one
    # F124-03: whether the project is paused by you
    paused_row = conn.execute("SELECT paused FROM projects WHERE name = ?", (project,)).fetchone()
    paused = metrics.paused_by_you(paused_row["paused"]) if paused_row else None
    return _ProjectLive(
        project,
        jobs,
        all_queued,
        waits,
        qjobs,
        lane,
        [mine(r) for r in rest],
        open_needs,
        needs,
        items,
        reserve_cards,
        paused,
    )


def _held(row: dict[str, Any], waits: dict[str, str], lead_holds: str | None) -> str | None:
    """What keeps a Next in line row from running now, in its row's words, or None when it can
    run: a ticket it waits for, Claude (the run waits for it, or the lead's tickets wait at
    Claude's limit), or a parked review's reset."""
    if row.get("ticket") and row["ticket"] in waits:
        return waits[row["ticket"]]
    if row.get("waits"):
        return "waits for " + ", ".join(row["waits"])
    if row.get("kind") == "lead" and lead_holds and lead_holds.startswith("waits for Claude"):
        return lead_holds
    return None


@router.get("/", response_class=HTMLResponse)
def overview(request: Request, conn: Db, project: Project, now: Now) -> HTMLResponse:
    from factory_dashboard.board import board  # board.py imports from here
    from factory_dashboard.line import SEEN, live_line, overnight

    local = now.astimezone()
    cards = board(conn, project, now)
    line = live_line(conn, project, local, cards=cards)

    def url(path: str, since: datetime) -> str:
        from urllib.parse import urlencode

        return path + "?" + urlencode({"project": project, "since": since.isoformat()})

    # f3-21: the span the panel and the replay show, from ?since= (an option chosen), else
    # since the owner last looked (the cookie, read before it is set again below)
    looked = overnight(local, request.cookies.get(SEEN))
    try:
        since = datetime.fromisoformat(request.query_params["since"]).astimezone(local.tzinfo)
    except (KeyError, ValueError):
        since = looked
    if since >= local:
        since = looked
    spans = [
        (f"since you last looked ({looked:%H:%M})", looked),
        ("the last hour", local - timedelta(hours=1)),
        ("today", local.replace(hour=0, minute=0, second=0, microsecond=0)),
        ("the last 24 h", local - timedelta(days=1)),
    ]
    if since not in [start for _, start in spans]:
        spans.append((f"since {since:%H:%M}", since))  # an option chosen on an earlier load
    choices = [
        {"label": label, "url": url("/", start), "selected": start == since}
        for label, start in spans
    ]

    response = render(
        request,
        conn,
        project,
        "overview.html",
        {
            "active": "/",
            "line": line,
            "replay": url("/line/replay", since),
            "replay_day": url("/line/replay", local - timedelta(days=1)),
            "away": queries.away_every(conn, every_project(conn, project), since, local),
            "since": since,
            "choices": choices,
            "now": local,
            **_live_context(conn, project, now, line=line, cards=cards),
        },
        is_factory_wide=True,
    )
    if "since" not in request.query_params:  # choosing a span isn't looking again (f3-F3)
        response.set_cookie(
            SEEN,
            local.isoformat(timespec="seconds"),
            max_age=400 * 24 * 3600,
            httponly=True,
            samesite="lax",
        )
    return response


@router.get("/live", response_class=HTMLResponse)
def live(request: Request, conn: Db, project: Project, now: Now) -> HTMLResponse:
    """Needs you and Running now together, for htmx to swap in every 5 s."""
    return render(
        request,
        conn,
        project,
        "_partials/live.html",
        _live_context(conn, project, now),
        is_factory_wide=True,
    )


@router.get("/away", response_class=HTMLResponse)
def away_partial(request: Request, conn: Db, project: Project, now: Now) -> HTMLResponse:
    """The 'While you were away' section for a chosen ``since``, for in-place swap (f9-14)."""
    from factory_dashboard.line import SEEN, overnight

    local = now.astimezone()
    try:
        since = datetime.fromisoformat(request.query_params["since"]).astimezone(local.tzinfo)
    except (KeyError, ValueError):
        looked = overnight(local, request.cookies.get(SEEN))
        since = looked
    if since >= local:
        since = looked
    return render(
        request,
        conn,
        project,
        "_partials/away.html",
        {
            "since": since,
            "away": queries.away_every(conn, every_project(conn, project), since, local),
            "now": local,
        },
        is_factory_wide=True,
    )
