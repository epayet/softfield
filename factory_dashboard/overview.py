"""The Overview (ADR 13 item 3.1, f1 D3, D4, D7, D8), and the worked example for a page: an
``APIRouter``, its own SQL in plain functions that return data, a template extending
``base.html``, and a chart's data for ``static/charts.js`` (D5).

Top to bottom: Needs you, Running now (an htmx partial at ``/running``), the queue, the last
verdict, the Claude allowance, savings for the current milestone and the Claude spend chart.
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from factory_dashboard import queries
from factory_dashboard.app import Db, Now, Project, ago, render
from runner.tasks import milestone_order

router = APIRouter()

LIVE = timedelta(minutes=2)  # D3: an older heartbeat means the runner stopped
WINDOW = timedelta(hours=5)  # Claude Pro's usage window


def _age(now: datetime, at: str | None) -> timedelta | None:
    return now - datetime.fromisoformat(at) if at else None


def _drain(key: str) -> str:
    return f"uv run runner milestone {key}"


# --- Running now and the runner's heartbeat (D3) ------------------------------------------


@dataclass(frozen=True)
class Running:
    job: int
    role: str
    agent: str
    attempt: int
    ticket: str | None
    difficulty: int | None
    milestone: str | None
    run_dir: str
    elapsed: timedelta
    heartbeat: timedelta | None  # how long ago the run last beat
    tokens_in: int | None
    steps: int | None

    @property
    def live(self) -> bool:
        return self.heartbeat is not None and self.heartbeat < LIVE


def running_jobs(conn: sqlite3.Connection, project: str, now: datetime) -> list[Running]:
    """Every job still ``running``, oldest first, live or not."""
    rows = conn.execute(
        "SELECT j.id, j.role, j.agent, j.attempt, j.started, j.tokens_in, j.steps,"
        " t.ticket, t.difficulty, m.key AS milestone, r.run_dir, r.heartbeat"
        " FROM jobs j JOIN runs r ON r.id = j.run_id JOIN projects p ON p.id = r.project_id"
        " LEFT JOIN tickets t ON t.id = j.ticket_id"
        " LEFT JOIN milestones m ON m.id = j.milestone_id"
        " WHERE p.name = ? AND j.outcome = 'running' ORDER BY j.started, j.id",
        (project,),
    ).fetchall()
    return [
        Running(
            job=row["id"],
            role=row["role"],
            agent=row["agent"],
            attempt=row["attempt"],
            ticket=row["ticket"],
            difficulty=row["difficulty"],
            milestone=row["milestone"],
            run_dir=row["run_dir"],
            elapsed=_age(now, row["started"]) or timedelta(0),
            heartbeat=_age(now, row["heartbeat"]),
            tokens_in=row["tokens_in"],
            steps=row["steps"],
        )
        for row in rows
    ]


def runner_live(conn: sqlite3.Connection, project: str, now: datetime) -> bool:
    """A run that hasn't ended and beat less than ``LIVE`` ago."""
    rows = conn.execute(
        "SELECT r.heartbeat FROM runs r JOIN projects p ON p.id = r.project_id"
        " WHERE p.name = ? AND r.ended IS NULL AND r.heartbeat IS NOT NULL",
        (project,),
    ).fetchall()
    return any((_age(now, row["heartbeat"]) or LIVE) < LIVE for row in rows)


# --- the queue (D4) -----------------------------------------------------------------------


@dataclass(frozen=True)
class Queued:
    ticket: str
    title: str | None
    kind: str | None
    difficulty: int | None
    milestone: str | None


def queue(conn: sqlite3.Connection, project: str) -> list[Queued]:
    """The tickets waiting in ``tasks/ready/``, in the order milestones run."""
    rows = conn.execute(
        "SELECT t.ticket, t.title, t.kind, t.difficulty, m.key AS milestone FROM tickets t"
        " JOIN projects p ON p.id = t.project_id LEFT JOIN milestones m ON m.id = t.milestone_id"
        " WHERE p.name = ? AND t.state = 'ready'",
        (project,),
    ).fetchall()
    found = [
        Queued(r["ticket"], r["title"], r["kind"], r["difficulty"], r["milestone"]) for r in rows
    ]
    return sorted(found, key=lambda q: (milestone_order(q.milestone or "m0"), q.ticket))


# --- Needs you (D8) -----------------------------------------------------------------------


@dataclass(frozen=True)
class Need:
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
        "SELECT o.kind, o.subject, o.text, o.command FROM owner_items o"
        " JOIN projects p ON p.id = o.project_id WHERE p.name = ? AND o.resolved IS NULL"
        " ORDER BY o.created DESC, o.id DESC",
        (project,),
    ).fetchall()
    found = [Need(i["kind"], i["text"] or i["subject"], i["command"]) for i in items]
    stopped: dict[str, Running] = {}
    for job in jobs:
        if not job.live:
            stopped.setdefault(job.run_dir, job)
    for job in stopped.values():
        when = f" {ago(job.heartbeat)} ago" if job.heartbeat else ""
        found.append(
            Need(
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
        found.append(Need("queue", text, _drain(waiting[0].milestone or "")))
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
class Allowance:
    used: float  # token-equivalents in the window
    limit: float | None  # what the window held at the last refusal, if any
    jobs: int

    @property
    def share(self) -> float | None:
        return min(1.0, self.used / self.limit) if self.limit else None


def _claude_equivalents(conn: sqlite3.Connection, since: datetime, until: datetime) -> list[float]:
    rows = conn.execute(
        "SELECT started, tokens_in, tokens_cached, tokens_out FROM jobs"
        " WHERE agent LIKE ? AND started IS NOT NULL",
        (queries.LEAD_PREFIX + "%",),
    ).fetchall()
    return [
        queries.Spend(
            tokens_in=r["tokens_in"] or 0,
            tokens_cached=r["tokens_cached"] or 0,
            tokens_out=r["tokens_out"] or 0,
        ).token_equivalents
        for r in rows
        if since <= datetime.fromisoformat(r["started"]) <= until
    ]


def claude_allowance(conn: sqlite3.Connection, now: datetime) -> Allowance:
    """Claude's use in the last ``WINDOW``, across every project (the allowance is the
    account's), against what the window held when Claude last refused."""
    used = _claude_equivalents(conn, now - WINDOW, now)
    refusal = conn.execute(
        "SELECT at FROM usage_events WHERE kind = 'refusal' AND agent LIKE ?"
        " ORDER BY at DESC LIMIT 1",
        (queries.LEAD_PREFIX + "%",),
    ).fetchone()
    limit = None
    if refusal:
        at = datetime.fromisoformat(refusal["at"])
        limit = sum(_claude_equivalents(conn, at - WINDOW, at)) or None
    return Allowance(used=sum(used), limit=limit, jobs=len(used))


def spend_chart(conn: sqlite3.Connection, project: str) -> dict[str, list[str] | list[float]]:
    """Claude's dollars per milestone, oldest first: the data of ``charts.js``'s ``spend``."""
    points = queries.trends(conn, project)
    return {
        "labels": [p.results.key.upper() for p in points],
        "dollars": [round(p.results.claude.dollars, 2) for p in points],
    }


# --- the routes ---------------------------------------------------------------------------


@router.get("/", response_class=HTMLResponse)
def overview(request: Request, conn: Db, project: Project, now: Now) -> HTMLResponse:
    jobs = running_jobs(conn, project, now)
    waiting = queue(conn, project)
    milestone = current_milestone(conn, project)
    return render(
        request,
        conn,
        project,
        "overview.html",
        {
            "active": "/",
            "needs": needs_you(conn, project, now, jobs, waiting),
            "running": [job for job in jobs if job.live],
            "queue": waiting,
            "drain": _drain(waiting[0].milestone or "") if waiting else None,
            "verdict": last_verdict(conn, project),
            "allowance": claude_allowance(conn, now),
            "milestone": milestone,
            "savings": queries.savings(conn, project, milestone["key"]) if milestone else None,
            "spend": spend_chart(conn, project),
        },
    )


@router.get("/running", response_class=HTMLResponse)
def running_now(request: Request, conn: Db, project: Project, now: Now) -> HTMLResponse:
    """Running now on its own, for htmx to swap in every 5 s."""
    running = [job for job in running_jobs(conn, project, now) if job.live]
    return render(request, conn, project, "_partials/running.html", {"running": running})
