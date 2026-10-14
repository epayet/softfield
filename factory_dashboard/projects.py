"""The Project page (f1-29, D8), and the Projects page above every project (ADR 30 item 6).

The Project page shows a project's name, description, repo path, milestones (newest first)
with status, and last runs. The Projects page shows what runs now in any project, what waits
for the owner in each, and the projects in the owner's order, which it changes.
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from factory_dashboard.app import Db, Now, Project, render
from factory_dashboard.overview import running_jobs
from runner import metrics
from runner.requests import PROJECT_ORDER

router = APIRouter()


@dataclass(frozen=True)
class ProjectMeta:
    name: str
    description: str | None
    repo: str | None


@dataclass(frozen=True)
class MilestoneSummary:
    key: str
    title: str | None
    status: str | None


@dataclass(frozen=True)
class RunSummary:
    run_dir: str
    ended: str | None


def get_project(conn: sqlite3.Connection, name: str) -> ProjectMeta | None:
    """Look up the project by name."""
    row = conn.execute(
        "SELECT name, description, repo FROM projects WHERE name = ? LIMIT 1",
        (name,),
    ).fetchone()
    if row is None:
        return None
    return ProjectMeta(name=row["name"], description=row["description"], repo=row["repo"])


def milestone_summaries(conn: sqlite3.Connection, project: str) -> list[MilestoneSummary]:
    """Every milestone of the project, newest first by ``started``."""
    rows = conn.execute(
        "SELECT m.key, m.title, m.status FROM milestones m"
        " JOIN projects p ON p.id = m.project_id"
        " WHERE p.name = ?"
        " ORDER BY m.started DESC, m.id DESC",
        (project,),
    ).fetchall()
    return [MilestoneSummary(r["key"], r["title"], r["status"]) for r in rows]


def run_summaries(conn: sqlite3.Connection, project: str) -> list[RunSummary]:
    """The last 10 runs of the project, newest first."""
    rows = conn.execute(
        "SELECT r.run_dir, r.ended FROM runs r"
        " JOIN projects p ON p.id = r.project_id"
        " WHERE p.name = ?"
        " ORDER BY r.ended DESC, r.id DESC"
        " LIMIT 10",
        (project,),
    ).fetchall()
    return [RunSummary(r["run_dir"], r["ended"]) for r in rows]


@router.get("/projects/{name}", response_class=HTMLResponse)
def project_page(
    name: str,
    request: Request,
    conn: Db,
    project: Project,
) -> HTMLResponse:
    meta = get_project(conn, name)
    if meta is None:
        return HTMLResponse(status_code=404, content="Not found")
    milestones = milestone_summaries(conn, name)
    runs = run_summaries(conn, name)
    return render(
        request,
        conn,
        name,
        "project.html",
        {
            "active": "/projects",
            "meta": meta,
            "milestones": milestones,
            "runs": runs,
        },
    )


# --- the Projects page (ADR 30 item 6, after .factory/cards/f120-many-projects-mockup/) ---


@dataclass(frozen=True)
class ProjectCard:
    """One project on the Projects page, in the owner's order."""

    name: str
    description: str | None
    place: int
    ready: int  # tickets in its .factory/tasks/ready/, read from its repo
    building: int
    ideas: int
    done: int
    for_you: int  # its Planning desk's items waiting for the owner


@dataclass(frozen=True)
class NowJob:
    project: str
    ticket: str | None
    title: str | None
    role: str
    agent: str
    minutes: int


def _ready(repo: str | None) -> int:
    folder = Path(repo) / ".factory" / "tasks" / "ready" if repo else None
    return len(list(folder.glob("*.md"))) if folder and folder.is_dir() else 0


def project_cards(conn: sqlite3.Connection, now: datetime) -> list[ProjectCard]:
    """Every project in the owner's order, with what waits in it and what waits for the owner."""
    from factory_dashboard.planning import desk, waiting_for_you  # planning imports app

    cards = []
    for place, row in enumerate(metrics.projects_in_order(conn), start=1):
        states = dict(
            conn.execute(
                "SELECT m.state, count(*) FROM milestones m JOIN projects p ON p.id = m.project_id"
                " WHERE p.name = ? GROUP BY m.state",
                (row.name,),
            ).fetchall()
        )
        cards.append(
            ProjectCard(
                name=row.name,
                description=row.description,
                place=place,
                ready=_ready(row.repo),
                building=states.get("building", 0),
                ideas=states.get("idea", 0),
                done=states.get("done", 0),
                for_you=len(waiting_for_you(desk(conn, row.name, now))),
            )
        )
    return cards


def running_now(conn: sqlite3.Connection, now: datetime) -> list[NowJob]:
    """The jobs running now in every project, from a live run (``Running.live``)."""
    found = []
    for row in metrics.projects_in_order(conn):
        for job in running_jobs(conn, row.name, now):
            if job.live:
                minutes = int(job.elapsed.total_seconds() // 60)
                found.append(NowJob(row.name, job.ticket, job.title, job.role, job.agent, minutes))
    return found


def order_on_its_way(conn: sqlite3.Connection) -> list[str] | None:
    """The latest projects' order the runner hasn't taken yet, as sent; None when none waits."""
    row = conn.execute(
        "SELECT value FROM owner_requests WHERE kind = ? AND done IS NULL ORDER BY id DESC LIMIT 1",
        (PROJECT_ORDER,),
    ).fetchone()
    if row is None:
        return None
    try:
        names = json.loads(row["value"] or "")
    except ValueError:
        return None
    return [str(n) for n in names] if isinstance(names, list) else None


@router.get("/projects", response_class=HTMLResponse)
def projects_page(request: Request, conn: Db, project: Project, now: Now) -> HTMLResponse:
    cards = project_cards(conn, now)
    asked = order_on_its_way(conn)
    if asked is not None:  # shown as sent, on its way (owner, 2026-10-07)
        cards.sort(key=lambda c: asked.index(c.name) if c.name in asked else len(asked))
    return render(
        request,
        conn,
        project,
        "projects.html",
        {
            "active": "/projects",
            "cards": cards,
            "now_jobs": running_now(conn, now),
            "for_you": [c for c in cards if c.for_you],
            "asked": asked is not None,
        },
    )
