"""The factory dashboard's service (ADR 13 item 2, f1 D1): a FastAPI app over the metrics
database, served at 127.0.0.1 by ``uv run runner dashboard`` (or at ``--host``, a LAN address).

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
    """``30 s``, ``3 min``, ``2 h``: how long, to a glance."""
    seconds = max(0, int(delta.total_seconds()))
    if seconds < 90:
        return f"{seconds} s"
    if seconds < 90 * 60:
        return f"{round(seconds / 60)} min"
    return f"{seconds / 3600:.1f} h".replace(".0 h", " h")


templates.env.filters.update(usd=usd, pct=pct, tokens=short, ago=ago)


def create_app(db: Path, project: str, host: str = HOST) -> FastAPI:
    """The dashboard over the database at ``db``, showing ``project`` unless asked otherwise,
    answering to loopback names and to ``host``, the address it listens on."""
    from factory_dashboard import (
        agents,
        bench,
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

    app = FastAPI(title="software-factory", docs_url=None, redoc_url=None, openapi_url=None)
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


def render(
    request: Request,
    conn: sqlite3.Connection,
    project: str,
    template: str,
    context: dict[str, Any],
) -> HTMLResponse:
    """A page: ``template`` with the top bar's projects, and ``q`` to keep ``?project=``."""
    names = [row["name"] for row in conn.execute("SELECT name FROM projects ORDER BY name")]
    return templates.TemplateResponse(
        request,
        template,
        {
            "project": project,
            "projects": names if project in names else [*names, project],
            "q": "?" + urlencode({"project": project}),
            "version_poll": VERSION_POLL.format(version=code_version()),
            **context,
        },
    )
