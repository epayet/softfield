"""A project's app, from the Projects page (ADR 46 items 6 and 8, F239 D5): Run and Stop, at
once, without waiting for the runner.

- The dashboard's only writes besides a request row: ``docker compose up -d`` and ``stop``,
  each a fixed command in ``runner/stacks.py``, on a project taken from the registry. Nothing
  from the request reaches the command but the project's name, looked up.
- The guard is ``/requests``'s (ADR 18 item 3), checked before anything else: without it, 403,
  and Docker never runs.
- A name not in the registry, a project without ``[run]`` and Softfield itself answer 404.
- The answer is ``_partials/app_row.html``, re-drawn from ``state``; the Projects page draws
  the same partial from the same ``row_of`` (f239-05).
"""

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from factory_dashboard.app import Db, render, templates
from factory_dashboard.requests import from_the_dashboard
from runner import metrics, stacks
from runner.config import ConfigError
from runner.gitops import Git, GitError

router = APIRouter()

FIX_LOG_LINES = 30  # of the app's logs, in the plant that asks for a fix (D7)
# What a project without a stack can plant (D7)
STACK_PLANT = (
    "Give {name} a Docker Compose stack the Projects page can run "
    "(ADR 46; what it needs: runner/instructions/run-stack.md)"
)

# The state's word on the page, beside its colour (D6)
STATE_WORDS = {
    stacks.RUNNING: "Running",
    stacks.STARTING: "Starting",
    stacks.STOPPED: "Stopped",
    stacks.CRASHED: "Crashed",
    stacks.UPDATE_FAILED: "Update failed",
    stacks.NO_DOCKER: "Docker isn't available",
}
# The states whose app is up: they offer Stop; the others, a crashed app too, offer Run
# (`up -d` brings a crashed app back; a failed update left the old containers running)
UP = (stacks.RUNNING, stacks.STARTING, stacks.UPDATE_FAILED)
# The states that offer a card to fix them (D7)
BROKEN = (stacks.CRASHED, stacks.UPDATE_FAILED)


def plant_value(text: str) -> str:
    """A ``plant`` request's value, in the Plant box's shape: planted, not asked."""
    return json.dumps({"text": text, "ask": False})


@dataclass(frozen=True)
class AppRow:
    """What ``_partials/app_row.html`` draws for one project's app."""

    name: str
    app: stacks.StackState
    path: str  # the app's URL path, from ``[run]``: Open is the page's host, ``url_port`` and it
    commit: str = ""  # main's commit the app is on (an update failed: the one it failed on)
    fix: str = ""  # the "Plant a card to fix it" value, for a crashed app or a failed update
    error: str = ""  # why a press failed

    @property
    def word(self) -> str:
        return STATE_WORDS.get(self.app.word, self.app.word)

    @property
    def up(self) -> bool:
        return self.app.word in UP

    @property
    def running(self) -> bool:
        return self.app.word == stacks.RUNNING

    @property
    def summary(self) -> str:
        """The detail's last line: a failed update's is the end of its build's output."""
        lines = self.app.detail.strip().splitlines()
        return lines[-1] if lines else ""


def _checkout_commit(stack: stacks.Stack) -> str:
    try:
        return Git(stack.checkout).head() if stack.checkout.is_dir() else ""
    except (GitError, OSError):
        return ""


def fix_text(name: str, stack: stacks.Stack, app: stacks.StackState, commit: str) -> str:
    """D7: what happened, ``state``'s detail and the last log lines, for a planner that can't
    run Docker."""
    what = "crashed" if app.word == stacks.CRASHED else "didn't update"
    head = f"{name}'s app {what}"
    if app.since:
        head += f" at {app.since}"
    if commit:
        head += f" on main {commit}"
    lines = stacks.logs(stack, lines=FIX_LOG_LINES).rstrip("\n")
    return f"{head}: find out why and fix it\n\n{app.detail}\n\n```\n{lines}\n```"


def row_of(name: str, stack: stacks.Stack, error: str = "") -> AppRow:
    """The project's app row, from its state now."""
    app = stacks.state(stack)
    commit = app.commit or (_checkout_commit(stack) if app.word in BROKEN else "")
    fix = plant_value(fix_text(name, stack, app, commit)) if app.word in BROKEN else ""
    return AppRow(name, app, stack.path, commit, fix, error)


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
    return templates.TemplateResponse(
        request, "_partials/app_row.html", {"row": row_of(name, stack, error)}
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


@router.get("/projects/{name}/logs")
def logs_page(name: str, request: Request, conn: Db, service: str | None = None) -> HTMLResponse:
    """The app's logs page: state on top, last 200 lines, service chooser, refreshed every 5 s."""
    stack = stack_of(conn, name)
    if stack is None:
        raise HTTPException(404, "no project with an app the dashboard can run")
    if service is not None and service not in stacks.services(stack):
        raise HTTPException(404, "service not in stack")
    svc = service if service else None
    app_state = stacks.state(stack)
    all_services = stacks.services(stack)
    return render(
        request,
        conn,
        name,
        "app_logs.html",
        {
            "name": name,
            "app": app_state,
            "word": STATE_WORDS.get(app_state.word, app_state.word),
            "logs": stacks.logs(stack, service=svc),
            "service": service,
            "services": all_services,
            "since": app_state.since,
        },
    )
