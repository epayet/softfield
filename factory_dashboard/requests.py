"""``POST /requests``: the dashboard asks the runner for something (ADR 18 items 2 and 3, f5 D3).

- Its only write: one ``owner_requests`` row, which the runner applies as its console command
  would (``runner/requests.py``). It changes nothing else, and never git or ``tasks/``.
- The guard: htmx's ``HX-Request`` header, and an ``Origin`` (else a ``Referer``) whose host is
  the request's own, so a website open in the owner's browser can't post here. Anything else
  is 403, before the database is opened for writing.
- The answer is ``_partials/request.html``: "Asked", polling ``GET /requests/{id}`` every 5 s
  until the runner finishes the request, then its result.

The worked example for a button that asks the runner (``docs/agents/developer.md``).
"""

import sqlite3
from urllib.parse import parse_qs, urlsplit

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from factory_dashboard.app import Db, Now, templates, writable
from runner import metrics
from runner.requests import (
    ACCEPT_ADR,
    APPROVE_PLAN,
    ARCHIVE,
    CHANGE,
    DISMISS,
    DROP_SEED,
    PAUSE,
    PLAN_MESSAGE,
    PLANT,
    PRIORITY,
    QUEUE,
    REJECT,
    REORDER,
    RESERVE,
    RESUME,
    SEND_BACK,
    SIGNOFF,
)

router = APIRouter()

# The planning room's six (f6 D1) too, Now's pause and resume (f5-18), and the ↑ and ↓ of
# Next in line and the Milestones page (f6-18), archiving a thread (2026-10-07), dismissing
# words that didn't go through (F31 D9), rejecting a proposal (F31 D2), and editing or
# cancelling a waiting plant or message (F14 D1), and the board's order sent whole (F15 D3);
# the runner checks each value, as for the first three
KINDS = (
    SIGNOFF,
    RESERVE,
    QUEUE,
    PLAN_MESSAGE,
    PLANT,
    SEND_BACK,
    ACCEPT_ADR,
    APPROVE_PLAN,
    DROP_SEED,
    PAUSE,
    RESUME,
    PRIORITY,
    ARCHIVE,
    DISMISS,
    REJECT,
    CHANGE,
    REORDER,
)


def from_the_dashboard(request: Request) -> bool:
    """An htmx request from a page this server served: its ``Origin``, or without one its
    ``Referer``, names the host it was sent to (``TrustedHostMiddleware`` vouches for that)."""
    if request.headers.get("hx-request") != "true":
        return False
    source = request.headers.get("origin") or request.headers.get("referer")
    host = request.headers.get("host")
    return bool(source and host) and urlsplit(source).netloc == host


def _status(request: Request, row: sqlite3.Row) -> HTMLResponse:
    return templates.TemplateResponse(request, "_partials/request.html", {"asked": row})


@router.post("/requests", response_class=HTMLResponse)
async def ask(request: Request, now: Now) -> HTMLResponse:
    """Write one request row for the runner, from the dashboard's own page only."""
    if not from_the_dashboard(request):
        raise HTTPException(403, "only the dashboard's own page may ask")
    form = {k: v[0] for k, v in parse_qs((await request.body()).decode()).items()}
    kind = form.get("kind")
    if kind not in KINDS:
        raise HTTPException(400, f"not a request the runner takes: {kind!r}")
    conn = writable(request)
    try:
        conn.row_factory = sqlite3.Row
        project = metrics.find_project(conn, form.get("project") or request.app.state.project)
        if project is None:
            raise HTTPException(404, "no such project")
        request_id = metrics.add_request(
            conn, project, kind, form.get("subject"), form.get("value"), now.isoformat()
        )
        row = conn.execute("SELECT * FROM owner_requests WHERE id = ?", (request_id,)).fetchone()
    finally:
        conn.close()
    return _status(request, row)


@router.get("/requests/{request_id}", response_class=HTMLResponse)
def status(request: Request, conn: Db, request_id: int) -> HTMLResponse:
    """The request's status, for its partial to poll: "Asked" until done, then its result."""
    row = conn.execute("SELECT * FROM owner_requests WHERE id = ?", (request_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "no such request")
    return _status(request, row)
