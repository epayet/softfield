"""The Runs list and a single run's detail (ADR 13 item 3, f1 D3).

- ``/runs``: newest first, run dir, command, start, minutes, verdict, jobs.
- ``/runs/{run_dir}``: the same facts, its jobs in order (links to ``/jobs/{n}``)
  and the tickets it touched (links to ``/tickets/{id}``).
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from factory_dashboard.app import Db, Now, Project, render

router = APIRouter()

LIVE = timedelta(minutes=2)  # an older heartbeat means the runner stopped


def _age(at: str | None) -> timedelta | None:
    """How long ago ``at`` was, or ``None`` if ``at`` is empty."""
    return datetime.now().astimezone() - datetime.fromisoformat(at) if at else None


def list_runs(conn: sqlite3.Connection, project: str, *, now: datetime) -> list[dict[str, object]]:
    """All runs for ``project``, newest first, with job count and heartbeat."""
    rows = conn.execute(
        "SELECT r.id, r.run_dir, r.command, r.started, r.ended, r.verdict, r.heartbeat, "
        "COUNT(j.id) AS job_count "
        "FROM runs r "
        "JOIN projects p ON p.id = r.project_id "
        "LEFT JOIN jobs j ON j.run_id = r.id "
        "WHERE p.name = ? "
        "GROUP BY r.id "
        "ORDER BY r.started DESC, r.id DESC",
        (project,),
    ).fetchall()
    found: list[dict[str, object]] = []
    for row in rows:
        minutes: float | None = None
        if row["started"] and row["ended"]:
            start = datetime.fromisoformat(row["started"])
            end = datetime.fromisoformat(row["ended"])
            minutes = (end - start).total_seconds() / 60
        heartbeat_age = _age(row["heartbeat"])
        if row["ended"]:
            status = "done"
        elif heartbeat_age is not None and heartbeat_age < LIVE:
            status = "running"
        else:
            status = "stopped"
        found.append(
            {
                "id": row["id"],
                "run_dir": row["run_dir"],
                "command": row["command"],
                "started": row["started"],
                "minutes": minutes,
                "verdict": row["verdict"],
                "job_count": row["job_count"],
                "status": status,
            }
        )
    return found


@dataclass(frozen=True)
class _JobRef:
    id: int
    role: str
    agent: str
    attempt: int


def get_run(conn: sqlite3.Connection, project: str, run_dir: str) -> dict[str, object] | None:
    """A single run by its ``run_dir``, with jobs and tickets."""
    row = conn.execute(
        "SELECT r.id, r.run_dir, r.command, r.started, r.ended, r.heartbeat, r.verdict, "
        "p.name AS project_name "
        "FROM runs r "
        "JOIN projects p ON p.id = r.project_id "
        "WHERE r.run_dir = ? AND p.name = ?",
        (run_dir, project),
    ).fetchone()
    if row is None:
        return None

    jobs_rows = conn.execute(
        "SELECT j.id, j.role, j.agent, j.attempt, t.ticket "
        "FROM jobs j "
        "LEFT JOIN tickets t ON t.id = j.ticket_id "
        "WHERE j.run_id = ? "
        "ORDER BY j.id ASC",
        (row["id"],),
    ).fetchall()
    jobs: list[_JobRef] = [
        _JobRef(id=r["id"], role=r["role"], agent=r["agent"], attempt=r["attempt"])
        for r in jobs_rows
    ]

    ticket_names: list[str] = []
    for jr in jobs_rows:
        if jr["ticket"] and jr["ticket"] not in ticket_names:
            ticket_names.append(jr["ticket"])

    tickets: list[dict[str, str]] = []
    for name in ticket_names:
        trow = conn.execute(
            "SELECT t.ticket, t.title FROM tickets t WHERE t.ticket = ?",
            (name,),
        ).fetchone()
        if trow:
            tickets.append({"ticket": trow["ticket"], "title": trow["title"] or ""})

    minutes: float | None = None
    if row["started"] and row["ended"]:
        start = datetime.fromisoformat(row["started"])
        end = datetime.fromisoformat(row["ended"])
        minutes = (end - start).total_seconds() / 60

    heartbeat_age = _age(row["heartbeat"])
    if row["ended"]:
        status = "done"
    elif heartbeat_age is not None and heartbeat_age < LIVE:
        status = "running"
    else:
        status = "stopped"

    return {
        "id": row["id"],
        "run_dir": row["run_dir"],
        "command": row["command"],
        "started": row["started"],
        "ended": row["ended"],
        "minutes": minutes,
        "verdict": row["verdict"],
        "status": status,
        "jobs": jobs,
        "tickets": tickets,
    }


@router.get("/runs", response_class=HTMLResponse)
def runs_page(
    request: Request,
    conn: Db,
    project: Project,
    now: Now,
) -> HTMLResponse:
    runs = list_runs(conn, project, now=now)
    return render(request, conn, project, "runs.html", {"active": "/runs", "runs": runs})


@router.get("/runs/{run_dir}", response_class=HTMLResponse)
def run_page(
    run_dir: str,
    request: Request,
    conn: Db,
    project: Project,
) -> HTMLResponse:
    run = get_run(conn, project, run_dir)
    if run is None:
        return HTMLResponse(status_code=404, content="Not found")
    return render(request, conn, project, "run.html", {"active": "/runs", "run": run})
