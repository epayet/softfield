"""The Project page (f1-29, D8).

Shows a project's name, description, repo path, milestones (newest first) with status,
and last runs.
"""

import sqlite3
from dataclasses import dataclass

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from factory_dashboard.app import Db, Project, render

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
    """Every milestone of the project, newest first."""
    rows = conn.execute(
        "SELECT m.key, m.title, m.status FROM milestones m"
        " JOIN projects p ON p.id = m.project_id"
        " WHERE p.name = ?"
        " ORDER BY m.status IS 'done', m.started DESC, m.id DESC",
        (project,),
    ).fetchall()
    return [MilestoneSummary(r["key"], r["title"], r["status"]) for r in rows]


def run_summaries(conn: sqlite3.Connection, project: str) -> list[RunSummary]:
    """The project's runs, newest first."""
    rows = conn.execute(
        "SELECT r.run_dir, r.ended FROM runs r"
        " JOIN projects p ON p.id = r.project_id"
        " WHERE p.name = ?"
        " ORDER BY r.ended DESC, r.id DESC",
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
            "project": meta,
            "milestones": milestones,
            "runs": runs,
        },
    )
