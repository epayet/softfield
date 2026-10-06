"""The Overview (ADR 13 item 3.1, f1 D3, D4, D7, D8), and the worked example for a page: an
``APIRouter``, its own SQL in plain functions that return data, a template extending
``base.html``, and a chart's data for ``static/charts.js`` (D5).

Top to bottom: Needs you and Now (one htmx partial at ``/live``), the last verdict, the Claude
allowance, savings for the current milestone and the Claude spend chart.
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from factory_dashboard import queries
from factory_dashboard.app import Db, Now, Project, ago, render
from runner import metrics
from runner.tasks import milestone_order

router = APIRouter()

LIVE = timedelta(minutes=2)  # D3: an older heartbeat means the runner stopped
# Now is for the real runs (owner, 2026-10-04): a bench's runs (command 'bench') are left out.
# [claude] in workflow/runner.toml: reserve for the lead starts at 70% of the week.
WEEK_MARK = 0.70
# [claude] in workflow/runner.toml: reserve for you starts at 75% of the 5-hour window.
FIVE_HOUR_MARK = 0.75


def _age(now: datetime, at: str | None) -> timedelta | None:
    return now - datetime.fromisoformat(at) if at else None


def _drain(key: str) -> str:
    """The command that works through the queue: `runner run`, the standing command (ADR 17),
    whichever milestone ``key`` the work is in."""
    return "uv run runner run"


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
    the order ``pick_next`` would take them.  Tickets with a running job are excluded."""
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
    ready_now.sort(key=lambda q: (milestone_order(q.milestone or "m0"), q.ticket))
    waiting.sort(key=lambda q: (milestone_order(q.milestone or "m0"), q.ticket))
    return ready_now + waiting


# --- queued support jobs ------------------------------------------------------------------


@dataclass(frozen=True)
class QueuedJob:
    kind: str  # plain words: "Checkpoint", "Review", etc.
    subject: str
    reason: str
    waits: str | None = None


def queued_jobs(
    conn: sqlite3.Connection,
    project: str,
    now: datetime,
) -> list[QueuedJob]:
    """The project's open ``work_queue`` rows, minus those whose ``started_job`` is still
    running, each with the order and wait from ``dispatch.plan``."""
    from runner import dispatch

    project_id = conn.execute("SELECT id FROM projects WHERE name = ?", (project,)).fetchone()["id"]
    rows = metrics.open_jobs(conn, project_id)
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
        found.append(QueuedJob(plain, pick.subject, pick.reason, line.waits))
    return found


# --- Needs you (D8) -----------------------------------------------------------------------


@dataclass(frozen=True)
class Need:
    id: str  # stable while the need is open, so notify.js tells a new one (f5-12)
    kind: str
    text: str
    command: str | None = None
    ticket: str | None = None


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
        Need(f"owner-{i['id']}", i["kind"], i["text"] or i["subject"], i["command"]) for i in items
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


# --- the last verdict, the allowance, savings ---------------------------------------------


@dataclass(frozen=True)
class Verdict:
    milestone: str | None
    milestone_verdict: str | None
    run_dir: str | None
    run_verdict: str | None
    run_ended: str | None


def current_milestone(conn: sqlite3.Connection, project: str) -> sqlite3.Row | None:
    """The newest milestone not done yet, or the newest one."""
    row: sqlite3.Row | None = conn.execute(
        "SELECT m.key, m.title, m.status, m.verdict FROM milestones m"
        " JOIN projects p ON p.id = m.project_id WHERE p.name = ?"
        " ORDER BY m.status IS 'done', m.started DESC, m.id DESC LIMIT 1",
        (project,),
    ).fetchone()
    return row


def last_verdict(conn: sqlite3.Connection, project: str) -> Verdict:
    m = current_milestone(conn, project)
    run = conn.execute(
        "SELECT r.run_dir, r.verdict, r.ended FROM runs r JOIN projects p ON p.id = r.project_id"
        " WHERE p.name = ? AND r.verdict IS NOT NULL ORDER BY r.ended DESC, r.id DESC LIMIT 1",
        (project,),
    ).fetchone()
    return Verdict(
        milestone=m["key"] if m else None,
        milestone_verdict=m["verdict"] if m else None,
        run_dir=run["run_dir"] if run else None,
        run_verdict=run["verdict"] if run else None,
        run_ended=run["ended"] if run else None,
    )


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
    # Ollama reports no reading (ADR 15 item 2: used until refused), so its row says so.
    ollama = _agent_allowances(
        conn,
        "ollama-",
        "Ollama",
        [
            ("ollama", "allowance", None, None),
        ],
        now,
    )
    return claude + copilot + ollama


def biggest_clog(clog: dict[str, Any]) -> str:
    """The line under "What clogged the line today" (f3 D11): the highest of the limit, the
    failed minutes, the most idle machine's minutes and the owner's, a tie to the first."""
    idle = max(clog["idle"], key=lambda i: i["minutes"], default=None)
    minutes, label = max(
        [
            (clog["limit"], "Waiting for Claude's limit"),
            (clog["failed"], "Failed attempts"),
            (idle["minutes"] if idle else 0, f"Idle: {idle['name'] if idle else ''}"),
            (clog["owner"], "Stopped for you"),
        ],
        key=lambda c: c[0],
    )
    if not minutes:
        return "Nothing clogged the line today."
    return f"Biggest clog: {label}, {minutes} min."


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
    from factory_dashboard.line import live_line  # line.py imports LIVE from here

    jobs = running_jobs(conn, project, now)
    all_queued = queue(conn, project, now)
    # Mapping from ticket id to its ``waits_for`` reason, for tickets whose dependency isn't done.
    waits: dict[str, str] = {q.ticket: q.waits_for for q in all_queued if q.waits_for is not None}
    qjobs = queued_jobs(conn, project, now)
    needs = needs_you(conn, project, now, jobs, all_queued)
    return {
        "needs": needs,
        # what notify.js compares after each poll (f5-12): a job stopped mid-way isn't done
        "notify": {need.id: need.text for need in needs},
        "all_done": not (all_queued or qjobs or jobs),
        "running": [job for job in jobs if job.live],
        "runs": live_runs(conn, project, now),
        "queue": all_queued,
        "next": live_line(conn, project, now.astimezone())["now"]["next"],
        "drain": _drain(all_queued[0].milestone or "") if all_queued else None,
        "waits": waits,
        "queued_jobs": qjobs,
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
            "clog_biggest": biggest_clog(line["clog"]) if line["clog"] else None,
            "replay": url("/line/replay", since),
            "replay_day": url("/line/replay", local - timedelta(days=1)),
            "away": queries.away(conn, project, since, local),
            "since": since,
            "choices": choices,
            **_live_context(conn, project, now),
            "verdict": last_verdict(conn, project),
            "allowance": agent_allowances(conn, now),
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
