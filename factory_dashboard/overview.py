"""The Overview (ADR 13 item 3.1, f1 D3, D4, D7, D8), and the worked example for a page: an
``APIRouter``, its own SQL in plain functions that return data, a template extending
``base.html``, and a chart's data for ``static/charts.js`` (D5).

Top to bottom: Needs you and Now (one htmx partial at ``/live``), the Claude
allowance, savings for the current milestone and the Claude spend chart.
"""

import json
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, TypedDict
from urllib.parse import quote

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from factory_dashboard import queries
from factory_dashboard.app import Db, Now, Project, ago, factory_status, render
from runner import loop, metrics
from runner.requests import CHANGE, PLANT, RESERVE, owners_words
from runner.state import load_state
from runner.tasks import milestone_order

if TYPE_CHECKING:
    from factory_dashboard.planning import DeskItem  # planning.py imports from here

router = APIRouter()

LIVE = timedelta(minutes=2)  # D3: an older heartbeat means the runner stopped
# Now is for the real runs (owner, 2026-10-04): a bench's runs (command 'bench') are left out.
# [claude] in the machine's factory.toml: reserve for the lead starts at 70% of the week.
WEEK_MARK = 0.70
# [claude] in the machine's factory.toml: reserve for you starts at 75% of the 5-hour window.
FIVE_HOUR_MARK = 0.75


def _age(now: datetime, at: str | None) -> timedelta | None:
    return now - datetime.fromisoformat(at) if at else None


def _drain(key: str) -> str:
    """The command that works through the queue: `runner run`, the standing command (ADR 17),
    whichever milestone ``key`` the work is in."""
    return "softfield run"


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
    run_dir: str
    elapsed: timedelta
    heartbeat: timedelta | None  # how long ago the run last beat
    tokens_in: int | None
    tokens_cached: int | None
    steps: int | None
    waiting_until: str | None = None  # ISO time while the run pauses for a limit
    reserve: bool = False  # the owner said yes to Claude's reserve for this command

    @property
    def live(self) -> bool:
        return self.heartbeat is not None and self.heartbeat < LIVE

    @property
    def waiting_clock(self) -> str | None:
        return _clock(self.waiting_until)


def _clock(at: str | None) -> str | None:
    return datetime.fromisoformat(at).strftime("%H:%M") if at else None


@dataclass(frozen=True)
class LiveRun:
    """A live run, for what it does between jobs (f1 D3, amended)."""

    run_dir: str
    activity: str | None
    waiting_until: str | None
    reserve: bool
    title: str | None = None

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
            LiveRun(r["run_dir"], r["activity"], r["waiting_until"], bool(r["reserve"]), title)
        )
    return found


def running_jobs(conn: sqlite3.Connection, project: str, now: datetime) -> list[Running]:
    """Every job still ``running``, oldest first, live or not."""
    rows = conn.execute(
        "SELECT j.id, j.role, j.agent, j.attempt, j.started, j.tokens_in, j.tokens_cached, j.steps,"
        " t.ticket, t.title, t.difficulty, m.key AS milestone, r.run_dir, r.heartbeat,"
        " r.waiting_until, r.reserve"
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
            run_dir=row["run_dir"],
            elapsed=_age(now, row["started"]) or timedelta(0),
            heartbeat=_age(now, row["heartbeat"]),
            tokens_in=row["tokens_in"],
            tokens_cached=row["tokens_cached"],
            steps=row["steps"],
            waiting_until=row["waiting_until"],
            reserve=bool(row["reserve"]),
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


def queue(
    conn: sqlite3.Connection,
    project: str,
    now: datetime,
) -> list[Queued]:
    """Tickets whose dependencies are all done first, then the waiting ones, in
    the order ``pick_next`` would take them (priority first, f6-18).  Tickets with a running
    job are excluded."""
    rows = conn.execute(
        "SELECT t.ticket, t.title, t.kind, t.difficulty, t.depends_on, t.body,"
        " m.key AS milestone, m.priority AS card"
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
    priority = {
        r["ticket"]: queries.ticket_priority(r["body"], r["milestone"], r["card"]) for r in rows
    }
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
            )
        )
    ready_now = [q for q in found if q.waits_for is None]
    waiting = [q for q in found if q.waits_for is not None]

    def order(q: Queued) -> tuple[int, tuple[str, int], str]:
        return priority[q.ticket], milestone_order(q.milestone or "m0"), q.ticket

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
) -> list[QueuedJob]:
    """The project's open ``work_queue`` rows, minus those whose ``started_job`` is still
    running, each with the order and wait from ``dispatch.plan``. Also includes open plant
    requests from ``owner_requests``."""
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
    plan = dispatch.plan(queued, [], dispatch.Windows(), now)
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
        found.append(QueuedJob(plain, pick.subject, pick.reason, line.waits, message))
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
            found.append(QueuedJob("Plant", title, CANCELLING, title=title, cancelled=True))
            continue
        reason = "at the runner's next pick"
        if change is not None:
            title, reason = change.title or title, f"changed · {reason}"
        found.append(QueuedJob("Plant", title, reason, title=title))
    return found


# --- Needs you (D8) -----------------------------------------------------------------------


@dataclass(frozen=True)
class Need:
    id: str  # stable while the need is open, so notify.js tells a new one (f5-12)
    kind: str
    text: str
    command: str | None = None
    ticket: str | None = None
    subject: str | None = None


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
    found = [
        Need(
            f"owner-{i['id']}",
            i["kind"],
            i["text"] or i["subject"],
            i["command"],
            None,
            i["subject"],
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
                f"runner-{job.run_dir}",
                "runner",
                f"The runner's heartbeat stopped{when} mid-job: a crash or a closed terminal."
                " Rerun it; it picks up where it stopped.",
                _drain(job.milestone) if job.milestone else None,
                ticket=job.ticket,
            )
        )
    if waiting and not runner_live(conn, project, now):
        n = len(waiting)
        text = f"{n} ticket{'s' if n != 1 else ''} waiting and the runner is idle."
        found.append(Need("queue", "queue", text, _drain(waiting[0].milestone or "")))
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
    from runner.tasks import short_key

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
                1
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
        elif need.kind == "review-stop":
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
    "blocked": "A ticket is blocked",
    "escalated": "A ticket is blocked",
    "reserve": "Claude's allowance: your choice",
    "five-hour": "Claude's allowance: your choice",
    loop.MAIN_RED_KIND: "A check fails on main",
    "runner": "The runner stopped",
    "queue": "The runner is idle",
}


# --- the allowance, savings ---------------------------------------------


def current_milestone(conn: sqlite3.Connection, project: str) -> sqlite3.Row | None:
    """The newest milestone not done yet, or the newest one."""
    row: sqlite3.Row | None = conn.execute(
        "SELECT m.key, m.title, m.status, m.verdict FROM milestones m"
        " JOIN projects p ON p.id = m.project_id WHERE p.name = ?"
        " ORDER BY m.status IS 'done', m.started DESC, m.id DESC LIMIT 1",
        (project,),
    ).fetchone()
    return row


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
    status: str | None  # e.g. "reset since, no new reading" or "no data yet"


NO_DATA = "no data yet"
RESET_SINCE = "reset since, no new reading"


def _reset_label(resets: datetime, now: datetime) -> str:
    """A reading's reset: "resets at 17:00" later today, "resets on Oct 9 12:00" later on."""
    if resets.date() == now.date():
        return f"resets at {resets:%H:%M}"
    return f"resets on {resets:%b} {resets.day} {resets:%H:%M}"


def _agent_allowances(
    conn: sqlite3.Connection,
    agent_prefix: str,
    agent_label: str,
    windows: list[tuple[str, str, float | None, str | None]],
    now: datetime,
) -> list[WindowAllowance]:
    """One agent group's rows (Claude, Copilot, Ollama), from its latest reading per window.

    ``windows`` is a list of (window_key, display_label, mark_or_None, mark_label_or_None).
    """
    readings = metrics.latest_readings(conn, agent_prefix)
    rows: list[WindowAllowance] = []
    for wkey, wdisplay, mark, mlabel in windows:
        row = readings.get(wkey)
        value = None if row is None else row["value"]
        resets_at = None if row is None else row["resets_at"]
        resets = datetime.fromisoformat(resets_at) if resets_at else None
        if value is None:
            status: str | None = NO_DATA
        elif resets is not None and resets <= now:
            status, value = RESET_SINCE, None  # the reading is stale: no percentage
        else:
            status = None
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
                status=status,
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
            ("five_hour", "5-hour window", FIVE_HOUR_MARK, "kept for you from here"),
            ("seven_day", "week", WEEK_MARK, "reserve kept for the lead from here"),
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


def reserve_switches(conn: sqlite3.Connection, project: str, now: datetime) -> dict[str, Switch]:
    """Each Claude window's switch, by allowance window, from the runner's state.json (in the
    config's ``runs_dir``, found as ``line._config`` finds the config): no config or no file
    and both are off. A switch asked for shows at once (owner, 2026-10-07)."""
    from factory_dashboard.line import _config  # line.py imports LIVE from here

    config = _config(conn, project)
    try:
        state = load_state(config.runs_dir / "state.json") if config else None
    except (OSError, ValueError):  # unreadable: shown off, as the runner's own would be lost
        state = None
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
            ends = datetime.fromisoformat(state.switches[name])
            until = f"{ends + timedelta(hours=loop.USE_RESERVE_HOURS):%a %H:%M}"
        switches[window] = Switch(name, loop.SWITCHES[name], until, asked.get(name))
    return switches


def spend_chart(conn: sqlite3.Connection, project: str) -> dict[str, list[str] | list[float]]:
    """Claude's dollars per milestone, oldest first: the data of ``charts.js``'s ``spend``."""
    points = queries.trends(conn, project)
    return {
        "labels": [p.results.key.upper() for p in points],
        "dollars": [round(p.results.claude.dollars, 2) for p in points],
    }


# --- the routes ---------------------------------------------------------------------------


def _live_context(conn: sqlite3.Connection, project: str, now: datetime) -> dict[str, object]:
    """What the ``/live`` partial draws: Needs you, then Now (what works and the next three in
    the run order)."""
    from factory_dashboard.board import reserve_marked  # board.py imports from here
    from factory_dashboard.line import live_line  # line.py imports LIVE from here
    from factory_dashboard.planning import (  # planning.py imports from overview at module level
        _card_titles,
        _open_proposals,
        desk,
        waiting_for_you,
    )
    from runner import metrics

    jobs = running_jobs(conn, project, now)
    all_queued = queue(conn, project, now)
    # Mapping from ticket id to its ``waits_for`` reason, for tickets whose dependency isn't done.
    waits: dict[str, str] = {q.ticket: q.waits_for for q in all_queued if q.waits_for is not None}
    qjobs = queued_jobs(conn, project, now)
    open_needs = needs_you(conn, project, now, jobs, all_queued)
    # the desk's entry stands for its answers wanted, its sign-offs and its blocked tickets, so no
    # lead reply (f6-09), no stored sign-off row (f95-01) and no blocked row shows on its own
    needs = [n for n in open_needs if n.kind not in ("planning", "signoff", "blocked")]
    project_id = metrics.find_project(conn, project)
    card_titles: dict[str, str] = {}
    proposals: Sequence[DeskItem] = []
    if project_id is not None:
        card_titles = _card_titles(conn, project_id)
        proposals = _open_proposals(conn, project_id)
    items = waiting_for_you(desk(conn, project, now))  # what the owner acted on waits on no one
    if items:
        n = len(items)
        text = f"{n} thing{'s wait' if n != 1 else ' waits'} for you on your desk"
        needs.insert(0, Need("desk", "desk", text))
    # D1: word each notice from the item's kind and its card
    notice_data = notices(open_needs, card_titles, project, proposals)
    return {
        "needs": needs,
        "desk_items": items[:3],
        "planning_count": len(items),  # the Planning tab's count, refreshed by the live partial
        "notices": notice_data,
        "all_done": not (all_queued or qjobs or jobs),
        "running": [job for job in jobs if job.live],
        "runs": live_runs(conn, project, now),
        # the owner's pause on Now (f5-18), as the top bar words it (f28-02)
        "pause_words": pause_words(conn, project, now),
        "queue": all_queued,
        "next": live_line(conn, project, now.astimezone())["now"]["next"],
        "waits": waits,
        "queued_jobs": qjobs,
        # Claude's allowance and its reserve switches, below Now (f8-06)
        "allowance": agent_allowances(conn, now),
        "switches": reserve_switches(conn, project, now),
        "reserve_cards": reserve_marked(conn, project, now),  # named under them (F172 D6)
    }


@router.get("/", response_class=HTMLResponse)
def overview(request: Request, conn: Db, project: Project, now: Now) -> HTMLResponse:
    from factory_dashboard.line import SEEN, live_line, overnight

    local = now.astimezone()
    line = live_line(conn, project, local)
    milestone = current_milestone(conn, project)

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
            "away": queries.away(conn, project, since, local),
            "since": since,
            "choices": choices,
            "now": local,
            **_live_context(conn, project, now),
            "milestone": milestone,
            "savings": queries.savings(conn, project, milestone["key"]) if milestone else None,
            "spend": spend_chart(conn, project),
        },
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
    return render(request, conn, project, "_partials/live.html", _live_context(conn, project, now))


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
        {"since": since, "away": queries.away(conn, project, since, local), "now": local},
    )
