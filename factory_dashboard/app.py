"""The factory dashboard's service (ADR 13 item 2, f1 D1): a FastAPI app over the metrics
database, served at 127.0.0.1 by ``uv run runner dashboard``.

- One read-only connection per request (``Db``): the dashboard never writes.
- Every page takes ``?project=`` (``Project``) and keeps it in its links (``q`` in templates).
- A page is a module with an ``APIRouter``, included in ``create_app``; it renders a template
  extending ``templates/base.html`` with ``render``. ``overview.py`` is the worked example.
"""

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


def ago(delta: timedelta) -> str:
    """``30 s``, ``3 min``, ``2 h``: how long, to a glance."""
    seconds = max(0, int(delta.total_seconds()))
    if seconds < 90:
        return f"{seconds} s"
    if seconds < 90 * 60:
        return f"{round(seconds / 60)} min"
    return f"{seconds / 3600:.1f} h".replace(".0 h", " h")


templates.env.filters.update(usd=usd, tokens=short, ago=ago)


def create_app(db: Path, project: str) -> FastAPI:
    """The dashboard over the database at ``db``, showing ``project`` unless asked otherwise."""
    from factory_dashboard import jobs, milestones, overview, timeline

    app = FastAPI(title="software-factory", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.db, app.state.project = db, project
    # Only loopback names: a page elsewhere that rebinds its own name to 127.0.0.1 is refused.
    hosts = [HOST, "localhost"]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
    app.include_router(overview.router)
    app.include_router(milestones.router)
    app.include_router(jobs.router)
    app.include_router(timeline.router)
    return app


def serve(db: Path, project: str, port: int = PORT) -> None:
    uvicorn.run(create_app(db, project), host=HOST, port=port, log_level="warning")


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
            **context,
        },
    )
