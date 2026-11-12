"""A project's app, from the Projects page (ADR 46 items 6 and 8, F239 D5): Run and Stop, at
once, without waiting for the runner.

- The dashboard's only writes besides a request row: ``docker compose up -d`` and ``stop``,
  each a fixed command in ``runner/stacks.py``, on a project taken from the registry. Nothing
  from the request reaches the command but the project's name, looked up.
- The guard is ``/requests``'s (ADR 18 item 3), checked before anything else: without it, 403,
  and Docker never runs.
- A name not in the registry, a project without ``[run]`` and Softfield itself answer 404.
- The answer is ``_partials/app_row.html``, re-drawn from ``state``.
"""

import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from factory_dashboard.app import Db, templates
from factory_dashboard.requests import from_the_dashboard
from runner import metrics, stacks
from runner.config import ConfigError

router = APIRouter()

# The state's word on the page, beside its colour (D6)
STATE_WORDS = {
    stacks.RUNNING: "Running",
    stacks.STARTING: "Starting",
    stacks.STOPPED: "Stopped",
    stacks.CRASHED: "Crashed",
    stacks.UPDATE_FAILED: "Update failed",
    stacks.NO_DOCKER: "Docker isn't available",
}
# The states whose app has containers up: they offer Stop; the others offer Run
UP = (stacks.RUNNING, stacks.STARTING, stacks.CRASHED, stacks.UPDATE_FAILED)


def stack_of(conn: sqlite3.Connection, name: str) -> stacks.Stack | None:
    """The app of a registered project with ``[run]``; None for any other name, for a project
    whose ``project.toml`` can't be read, and for Softfield itself (ADR 46 item 8)."""
    row = next((p for p in metrics.projects_in_order(conn) if p.name == name), None)
    if row is None or not row.repo:
        return None
    try:
        return stacks.stack_for(Path(row.repo))
    except (ConfigError, OSError):
        return None


def app_row(request: Request, name: str, stack: stacks.Stack, error: str = "") -> HTMLResponse:
    """The project's app row, from its state now; ``error`` says why a press failed."""
    app = stacks.state(stack)
    return templates.TemplateResponse(
        request,
        "_partials/app_row.html",
        {
            "name": name,
            "app": app,
            "word": STATE_WORDS.get(app.word, app.word),
            "up": app.word in UP,
            "error": error,
        },
    )


def _guarded_stack(request: Request, conn: sqlite3.Connection, name: str) -> stacks.Stack:
    if not from_the_dashboard(request):
        raise HTTPException(403, "only the dashboard's own page may run or stop an app")
    stack = stack_of(conn, name)
    if stack is None:
        raise HTTPException(404, "no project with an app the dashboard can run")
    return stack


@router.post("/projects/{name}/run", response_class=HTMLResponse)
def run_app(name: str, request: Request, conn: Db) -> HTMLResponse:
    """``docker compose up -d`` on the project's checkout of main, then its row re-drawn."""
    stack = _guarded_stack(request, conn, name)
    try:
        stacks.start(stack)
    except stacks.StackError as exc:
        return app_row(request, name, stack, str(exc))
    return app_row(request, name, stack)


@router.post("/projects/{name}/stop", response_class=HTMLResponse)
def stop_app(name: str, request: Request, conn: Db) -> HTMLResponse:
    """``docker compose stop``, then the project's row re-drawn."""
    stack = _guarded_stack(request, conn, name)
    try:
        stacks.stop(stack)
    except stacks.StackError as exc:
        return app_row(request, name, stack, str(exc))
    return app_row(request, name, stack)
