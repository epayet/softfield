"""The factory dashboard's service (ADR 13 item 2, f1 D1): a FastAPI app over the metrics
database, served at 127.0.0.1 by ``softfield dashboard`` (or at ``--host``, a LAN address).

- It restarts itself when its code changes, and each page polls ``/version`` to offer a refresh.
- One read-only connection per request (``Db``). The one write is ``POST /requests``
  (``requests.py``, ADR 18 item 2): a request row for the runner, on its own connection
  (``writable``), opened in that route only.
- Every page takes ``?project=`` (``Project``) and keeps it in its links (``q`` in templates).
- A page is a module with an ``APIRouter``, included in ``create_app``; it renders a template
  extending ``templates/base.html`` with ``render``. ``overview.py`` is the worked example.
"""

import hashlib
import os
import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import urlencode

import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.trustedhost import TrustedHostMiddleware

from runner.usage import short

HOST, PORT = "127.0.0.1", 8765
HERE = Path(__file__).parent
templates = Jinja2Templates(directory=HERE / "templates")


def usd(dollars: float) -> str:
    return f"-${-dollars:,.2f}" if dollars < -0.005 else f"${abs(dollars):,.2f}"


def pct(value: float) -> str:
    return f"{round(value)}%"


def ago(delta: timedelta) -> str:
    """``30 s``, ``3 min``, ``2 h``, ``5.9 days``: how long, to a glance."""
    seconds = max(0, int(delta.total_seconds()))
    if seconds < 90:
        return f"{seconds} s"
    if seconds < 90 * 60:
        return f"{round(seconds / 60)} min"
    if seconds >= 48 * 3600:
        days = seconds / 3600 / 24
        return f"{days:.1f} days".replace(".0 days", " days")
    return f"{seconds / 3600:.1f} h".replace(".0 h", " h")


templates.env.filters.update(usd=usd, pct=pct, tokens=short, ago=ago)

# Cache by path -> (mtime, first 10 hex chars of sha256).
_static_cache: dict[str, tuple[float, str]] = {}


def static(path: str) -> str:
    """Return ``/static/<path>?v=<first 10 hex of the file's sha256>``.

    The hash is cached keyed by (path, mtime) so a merge that only changes
    CSS still gives a new version (the server reloads its Python itself).
    A path that isn't a file under ``factory_dashboard/static/`` raises at
    render time, catching typos in templates.
    """
    full = HERE / "static" / path
    mtime = full.stat().st_mtime
    if path in _static_cache:
        prev_mtime, prev_hash = _static_cache[path]
        if prev_mtime == mtime:
            return f"/static/{path}?v={prev_hash}"
    h = hashlib.sha256(full.read_bytes()).hexdigest()[:10]
    _static_cache[path] = (mtime, h)
    return f"/static/{path}?v={h}"


templates.env.globals["static"] = static


def create_app(db: Path, project: str, host: str = HOST) -> FastAPI:
    """The dashboard over the database at ``db``, showing ``project`` unless asked otherwise,
    answering to loopback names and to ``host``, the address it listens on."""
    from factory_dashboard import (
        agents,
        bench,
        board,
        jobs,
        line,
        milestones,
        overview,
        planning,
        projects,
        requests,
        runs,
        tickets,
        timeline,
    )

    app = FastAPI(title="softfield", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.db, app.state.project = db, project
    # Only loopback names and the address it listens on: a page elsewhere that rebinds its own
    # name to one of them is refused.
    hosts = list(dict.fromkeys([HOST, "localhost", host]))
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
    app.include_router(overview.router)
    app.include_router(milestones.router)
    app.include_router(line.router)
    app.include_router(tickets.router)
    app.include_router(jobs.router)
    app.include_router(timeline.router)
    app.include_router(projects.router)
    app.include_router(runs.router)
    app.include_router(agents.router)
    app.include_router(bench.router)
    app.include_router(requests.router)
    app.include_router(planning.router)
    app.include_router(board.router)

    @app.get("/version", response_class=HTMLResponse)
    def version(seen: str = "") -> str:
        """The page's poller: itself again while ``seen`` is current, else a bar to refresh."""
        if seen == code_version():
            return VERSION_POLL.format(version=seen)
        return NEW_VERSION

    return app


# A page's poller (base.html): asks every 10 s whether the dashboard's code is still ``version``.
VERSION_POLL = (
    '<span hx-get="/version?seen={version}" hx-trigger="every 10s" hx-swap="outerHTML"></span>'
)
NEW_VERSION = (
    '<p class="new-version" role="status">New version of the dashboard: <a href="">refresh</a></p>'
)


def code_version() -> str:
    """A short hash of the dashboard's files and when they changed: a new one means a new
    version (the server reloads its Python itself; templates and static files are read fresh)."""
    digest = hashlib.sha256()
    for path in sorted(HERE.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            digest.update(f"{path.relative_to(HERE)}:{path.stat().st_mtime_ns}\n".encode())
    return digest.hexdigest()[:12]


def from_env() -> FastAPI:
    """``create_app`` from what ``serve`` left in the environment: uvicorn's reloader imports
    the app by name in a fresh process."""
    env = os.environ
    return create_app(
        Path(env["FACTORY_DASHBOARD_DB"]),
        env["FACTORY_DASHBOARD_PROJECT"],
        env["FACTORY_DASHBOARD_HOST"] or HOST,
    )


def serve(db: Path, project: str, port: int = PORT, host: str = HOST) -> None:
    os.environ.update(
        FACTORY_DASHBOARD_DB=str(db), FACTORY_DASHBOARD_PROJECT=project, FACTORY_DASHBOARD_HOST=host
    )
    uvicorn.run(
        f"{__name__}:from_env",
        factory=True,
        reload=True,
        reload_dirs=[str(HERE), str(HERE.parent / "runner")],
        host=host,
        port=port,
        log_level="warning",
    )


def get_db(request: Request) -> Iterator[sqlite3.Connection]:
    """The database, read-only (``mode=ro``), for one request. FastAPI may open and use it on
    different threads, one after the other, hence ``check_same_thread=False``."""
    path: Path = request.app.state.db
    conn = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def writable(request: Request) -> sqlite3.Connection:
    """The database for writing (``mode=rw``: it makes no file), in autocommit as the runner
    opens it. Only ``POST /requests`` opens it, after its guard, and closes it."""
    path: Path = request.app.state.db
    return sqlite3.connect(
        f"{path.resolve().as_uri()}?mode=rw", uri=True, isolation_level=None, timeout=10
    )


def get_project(request: Request, project: str | None = None) -> str:
    return project or str(request.app.state.project)


def get_now() -> datetime:
    """The clock; tests override it."""
    return datetime.now(UTC)


Db = Annotated[sqlite3.Connection, Depends(get_db)]
Project = Annotated[str, Depends(get_project)]
Now = Annotated[datetime, Depends(get_now)]


@dataclass(frozen=True)
class Status:
    """What the factory does, in the top bar (f6-16): its words; ``tone`` (``asked`` while the
    owner's request is on its way); the request its sign posts (``pause``, ``resume``, none);
    and its dot (f17): ``lead`` or ``developer`` while that one's job runs, ``waiting`` for
    Claude, ``stopped`` with no live run, else ``idle``."""

    words: str
    tone: str
    button: str | None
    project: str | None = None  # whose run it is: the button's request goes there (ADR 30)
    dot: str = "idle"


PICKING = "picking the next ticket"  # runner/loop.py's PICKING: between jobs
IDLE = "Idle: "  # runner writes its idle activity starting with this prefix (F101)


def _clock(at: str) -> str:
    return datetime.fromisoformat(at).strftime("%H:%M")


def _asked(conn: sqlite3.Connection, project: str) -> str | None:
    """The owner's latest pause or resume the runner hasn't taken yet, if any."""
    row = conn.execute(
        "SELECT r.kind FROM owner_requests r JOIN projects p ON p.id = r.project_id"
        " WHERE p.name = ? AND r.done IS NULL AND r.kind IN ('pause', 'resume')"
        " ORDER BY r.id DESC LIMIT 1",
        (project,),
    ).fetchone()
    return None if row is None else str(row["kind"])


def factory_wide_status(conn: sqlite3.Connection, project: str, now: datetime) -> Status:
    """The top bar's status for the whole factory, whichever project the page shows (the
    owner, 2026-10-14: picking a project is for planning and the board, not for what the
    factory does). Of every project's status: a pause first (it holds every project), then a
    running job (its dot is the lead's or a developer's, F132), a wait for Claude, a project
    between jobs, Idle, and Stopped last; it names its project
    when there is more than one, and its button posts there."""
    from runner import metrics

    names = [p.name for p in metrics.projects_in_order(conn)] or [project]
    found = [(name, factory_status(conn, name, now)) for name in names]

    def rank(status: Status) -> int:
        if status.button == "resume" or "asked" in status.tone:
            return 0
        if status.dot in ("lead", "developer"):
            return 1
        if status.words.startswith("Waiting for Claude"):
            return 2
        if status.words.startswith("Running: "):
            return 3
        if status.words.startswith("Idle: "):
            return 4
        return 5 if status.words == "Stopped" else 4

    name, status = min(found, key=lambda pair: rank(pair[1]))
    if len(names) == 1 or status.words == "Stopped":
        return replace(status, project=name)
    words = status.words
    if words.startswith("Running: "):
        words = f"Running: {name} · {words.removeprefix('Running: ')}"
    else:
        words = f"{words} · {name}"
    return replace(status, words=words, project=name)


def factory_status(conn: sqlite3.Connection, project: str, now: datetime) -> Status:
    """Stopped with no live run; else the owner's pause (held, asked, or a resume asked), a
    wait for Claude, the job running, what the run does between jobs, or idle with no work."""
    from factory_dashboard import overview, queries  # overview imports this module
    from factory_dashboard.line import DEVELOPER_ROLES  # line imports this module

    runs = overview.live_runs(conn, project, now)
    if not runs:
        return Status("Stopped", "", None, dot="stopped")
    paused, asked = queries.paused_since(conn), _asked(conn, project)
    if paused and asked == "resume":
        return Status("Resuming…", "asked", None)
    if paused:  # only the planner runs while paused
        words = f"Paused by you since {_clock(paused)}"
        jobs = overview.running_jobs(conn, project, now)
        if any(j.live and j.role == "planner" for j in jobs):
            return Status(f"{words} · the lead is answering you", "warn", "resume", dot="lead")
        return Status(words, "warn", "resume")
    # the dot is about the job the words name: the first live one
    jobs = overview.running_jobs(conn, project, now)
    job = next((j for j in jobs if j.live), None)
    dot = "idle" if job is None else "developer" if job.role in DEVELOPER_ROLES else "lead"
    if asked == "pause":  # which job, still (the owner, 2026-10-08: the bar lost it)
        doing = f"{job.ticket or f'{job.role}, job {job.job}'}" if job else "this job"
        return Status(f"Pausing after {doing}", "warn asked", "resume", dot=dot)
    waiting = next((r.waiting_until for r in runs if r.waiting_until), None)
    if waiting:
        words = f"Waiting for Claude until {_clock(waiting)}"
        return Status(words, "serious", "pause", dot="waiting")
    if job:
        words = f"Running: {job.ticket or f'{job.role}, job {job.job}'}"
        return Status(words, "good", "pause", dot=dot)
    activity = next((r.activity for r in runs if r.activity), None) or PICKING
    if activity == PICKING and not (
        jobs or overview.queue(conn, project, now) or overview.queued_jobs(conn, project, now)
    ):
        return Status("Idle: nothing to do", "", "pause")
    if activity.startswith(IDLE):
        return Status(activity, "", "pause")
    return Status(f"Running: {activity}", "good", "pause")


def top_bar(conn: sqlite3.Connection, project: str, now: datetime) -> dict[str, Any]:
    """The top bar's live facts on every page (f6-16): the factory's status and the Planning
    tab's count. ``render`` adds them to each page's first paint; ``/live`` refreshes them."""
    from factory_dashboard.planning import desk, waiting_for_you  # planning imports this module

    return {
        "bar_status": factory_wide_status(conn, project, now),
        "planning_count": len(waiting_for_you(desk(conn, project, now))),
    }


def render(
    request: Request,
    conn: sqlite3.Connection,
    project: str,
    template: str,
    context: dict[str, Any],
) -> HTMLResponse:
    """A page: ``template`` with the top bar's projects and live facts, and ``q`` to keep
    ``?project=``."""
    names = [  # a forgotten project is in no list (`softfield forget`)
        row["name"]
        for row in conn.execute(
            "SELECT name FROM projects WHERE coalesce(paused, '') != 'forgotten' ORDER BY name"
        )
    ]
    # the clock a test pinned, as the routes' ``Now`` reads it
    now = request.app.dependency_overrides.get(get_now, get_now)()
    return templates.TemplateResponse(
        request,
        template,
        {
            "project": project,
            "projects": names if project in names else [*names, project],
            "q": "?" + urlencode({"project": project}),
            "version_poll": VERSION_POLL.format(version=code_version()),
            **top_bar(conn, project, now),
            **context,
        },
    )
