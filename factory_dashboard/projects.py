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

from factory_dashboard import queries
from factory_dashboard.app import Db, Now, Project, render
from factory_dashboard.overview import running_jobs
from factory_dashboard.stacks_routes import STACK_PLANT, AppRow, plant_value, row_of, stack_of
from runner import config, metrics, stacks
from runner.requests import FORGET_PROJECT, NEW_PROJECT, PROJECT_ORDER, home_path

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
    savings = queries.savings(conn, name)
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
            "savings": savings,
        },
    )


# --- the Projects page (ADR 30 item 6, after .softfield/cards/projects-page-mockup/) ---


@dataclass(frozen=True)
class ProjectCard:
    """One project on the Projects page, in the owner's order."""

    name: str
    description: str | None
    place: int
    ready: int  # tickets in its .softfield/tasks/ready/, read from its repo
    building: int
    ideas: int
    done: int
    for_you: int  # its Planning desk's items waiting for the owner
    paused: str | None = None  # `metrics.SETTING_UP` while `softfield init`'s setup runs
    paused_by_you: str | None = None  # ISO time the owner paused it, None otherwise
    paused_on_its_way: str | None = None  # "pause_project" or "resume_project" while waiting
    archive_on_its_way: str | None = None  # "archive_project" or "unarchive_project" while waiting
    app: AppRow | None = None  # its app (F239 D6); None without `[run]`, and for Softfield
    softfield: bool = False  # Softfield's own repo: it runs from `live`, with no app row
    stack_plant: str = ""  # the "Plant a card for a stack" value, for a project without one
    setup_job: bool = False  # an open `setup` job: "Set up by the lead" is lit (F122 D6)
    archived: bool = False  # `metrics.is_archived` says the project is archived
    forget_on_its_way: bool = False  # a `forget_project` waits for the runner (F273 D5)
    folder: str = ""  # its repo as `home_path` writes it, for the Forget question (F273 D5)


# A setting-up project's line (F122 D6, .softfield/cards/f122-mockup/projects-new.html)
STATIONS = ("Asked", "Set up by the lead", "ADR 00 for you", "In the factory")


@dataclass(frozen=True)
class NewProject:
    """A `new_project` request the runner hasn't taken yet, drawn from its own value (F122 D6)."""

    name: str
    idea: str


@dataclass(frozen=True)
class NowJob:
    project: str
    ticket: str | None
    title: str | None
    role: str
    agent: str
    minutes: int
    card: dict[str, str] | None = None


def _ready(repo: str | None) -> int:
    folder = Path(repo) / ".softfield" / "tasks" / "ready" if repo else None
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
        stack = stack_of(conn, row.name)
        # `stack_for` is None for Softfield as for a project without `[run]`: ask the repo
        softfield = stack is None and row.repo is not None and stacks._is_softfield(Path(row.repo))
        project_id = metrics.find_project(conn, row.name)
        paused_by_you = metrics.paused_by_you(row.paused)
        paused_its_way = paused_on_its_way(conn, project_id) if project_id else None
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
                paused=row.paused,
                paused_by_you=paused_by_you,
                paused_on_its_way=paused_its_way,
                archive_on_its_way=archive_on_its_way(conn, project_id) if project_id else None,
                app=row_of(row.name, stack) if stack else None,
                softfield=softfield,
                stack_plant=""
                if stack or softfield or not row.repo
                else plant_value(STACK_PLANT.format(name=row.name)),
                setup_job=row.paused == metrics.SETTING_UP and _setup_job(conn, row.name),
                archived=metrics.is_archived(row),
                forget_on_its_way=project_id is not None and forget_on_its_way(conn, project_id),
                folder=home_path(Path(row.repo)) if row.repo else "",
            )
        )
    return cards


def paused_on_its_way(conn: sqlite3.Connection, project_id: int) -> str | None:
    """The latest pause_project or resume_project the runner hasn't taken for ``project_id``."""
    row = conn.execute(
        "SELECT kind FROM owner_requests WHERE project_id = ?"
        " AND kind IN ('pause_project', 'resume_project') AND done IS NULL"
        " ORDER BY id DESC LIMIT 1",
        (project_id,),
    ).fetchone()
    return row["kind"] if row else None


def archive_on_its_way(conn: sqlite3.Connection, project_id: int) -> str | None:
    """The latest archive_project or unarchive_project the runner hasn't taken (F262 D5)."""
    row = conn.execute(
        "SELECT kind FROM owner_requests WHERE project_id = ?"
        " AND kind IN ('archive_project', 'unarchive_project') AND done IS NULL"
        " ORDER BY id DESC LIMIT 1",
        (project_id,),
    ).fetchone()
    return row["kind"] if row else None


def forget_on_its_way(conn: sqlite3.Connection, project_id: int) -> bool:
    """Whether a forget_project for ``project_id`` waits for the runner (F273 D5)."""
    row = conn.execute(
        "SELECT 1 FROM owner_requests WHERE project_id = ? AND kind = ? AND done IS NULL",
        (project_id, FORGET_PROJECT),
    ).fetchone()
    return row is not None


def _setup_job(conn: sqlite3.Connection, name: str) -> bool:
    """Whether the project has a `setup` job waiting or running (`metrics.open_jobs`)."""
    from runner import dispatch

    project_id = metrics.find_project(conn, name)
    if project_id is None:
        return False
    return any(job["kind"] == dispatch.SETUP for job in metrics.open_jobs(conn, project_id))


@dataclass(frozen=True)
class SetupStrip:
    """bug-67: the setup's line at the top of a setting-up project's pages, as on its plate."""

    here: int  # the lit station, by its index in STATIONS
    next: str  # what happens next, in a line
    stations: tuple[str, ...] = STATIONS


_SETUP_NEXT = (
    "The lead's setup is next in line. Its answer comes on M1.",
    "The lead is setting it up. Its answer comes on M1: wait for it there.",
    "Next: read ADR 00 on M1 and approve it. Then the lead plans M1 for your yes,"
    " and the project is in the factory.",
)


def setup_strip(conn: sqlite3.Connection, project: str, now: datetime) -> SetupStrip | None:
    """The strip while ``project`` is being set up from the Projects page (ADR 48); None after.
    The station lit is the plate's (F122 D6): the lead's job while it waits or runs, then ADR 00
    on the desk."""
    from factory_dashboard.planning import desk, waiting_for_you  # planning imports app

    state = metrics.project_state(conn, project)
    if state is None or state[1] != metrics.SETTING_UP:
        return None
    lead = _setup_job(conn, project)
    here = 1 if lead else (2 if waiting_for_you(desk(conn, project, now)) else 0)
    return SetupStrip(here, _SETUP_NEXT[here])


def projects_on_their_way(conn: sqlite3.Connection) -> list[NewProject]:
    """The `new_project` requests the runner hasn't taken yet, oldest first; a value that isn't
    the form's JSON is the idea itself, as the runner reads it."""
    rows = conn.execute(
        "SELECT value FROM owner_requests WHERE kind = ? AND done IS NULL ORDER BY id",
        (NEW_PROJECT,),
    ).fetchall()
    found = []
    for row in rows:
        raw = row["value"] or ""
        try:
            value = json.loads(raw)
        except ValueError:
            value = None
        if isinstance(value, dict):
            found.append(NewProject(str(value.get("name") or ""), str(value.get("idea") or "")))
        else:
            found.append(NewProject("", raw))
    return found


def taken_names(conn: sqlite3.Connection, root: Path) -> list[str]:
    """The folder names Start it can't use (bug-68): every entry in the projects root, every
    live project's name and every name a project on its way asked for. Start it makes new
    projects only; an existing folder joins from the command line (the owner, 2026-11-19)."""
    from runner.setup import _slug  # the runner's own folder name for the form's

    names = {p.name for p in metrics.projects_in_order(conn)}
    names |= {_slug(p.name) for p in projects_on_their_way(conn) if p.name}
    if root.is_dir():
        names |= {entry.name for entry in root.iterdir() if not entry.name.startswith(".")}
    return sorted(n for n in names if n)


def running_now(conn: sqlite3.Connection, now: datetime) -> list[NowJob]:
    """The jobs running now in every project, from a live run (``Running.live``)."""
    from factory_dashboard.overview import job_card

    found = []
    for row in metrics.projects_in_order(conn):
        for job in running_jobs(conn, row.name, now):
            if job.live:
                minutes = int(job.elapsed.total_seconds() // 60)
                card = None
                if not job.ticket:
                    card = job_card(job.role, job.milestone, job.m_title)
                found.append(
                    NowJob(row.name, job.ticket, job.title, job.role, job.agent, minutes, card)
                )
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
    # a broken app first, then the desks; a card with both has both lines
    broken = [c for c in cards if c.app and c.app.needs_you]
    for_you = [c for c in cards if c.for_you]
    needs_you = broken + [c for c in for_you if c not in broken]
    needs_you_count = len(broken) + sum(c.for_you for c in for_you)
    # split: listed cards (not archived) and archived cards for the bay
    listed = [c for c in cards if not c.archived]
    archived = [c for c in cards if c.archived]
    root = config.projects_root(request.app.state.db)
    return render(
        request,
        conn,
        project,
        "projects.html",
        {
            "active": "/projects",
            "cards": listed,
            "archived": archived,
            "now_jobs": running_now(conn, now),
            "for_you": for_you,
            "needs_you": needs_you,
            "needs_you_count": needs_you_count,
            "asked": asked is not None,
            "starting": projects_on_their_way(conn),
            "stations": STATIONS,
            "root": home_path(root),  # as the mock-up
            "taken": taken_names(conn, root),
        },
        is_factory_wide=True,
    )
