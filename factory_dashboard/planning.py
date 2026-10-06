"""The planning room's desk (f6-06, F6 D6): ``/planning`` is the owner's desk.

- Two tiles: the factory now, with when the next reply is expected (planner jobs go first, so a
  pending message is answered once the running job is done, D1), and the lead's 5-hour window.
- ``desk(conn, project)``: what waits for the owner, in four groups (D6); the Overview's Needs
  you and the top bar's count reuse its items' words and links (f6-09).
- "Plant an idea": a ``plant`` request through ``POST /requests``, the dashboard's only write.
"""

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from factory_dashboard.app import Db, Now, Project, ago, render
from factory_dashboard.line import live_line
from factory_dashboard.overview import Running, agent_allowances, running_jobs
from runner import metrics
from runner.planner import PLANNER
from runner.requests import (
    ACCEPT_ADR,
    APPROVE_PLAN,
    PLANT,
    QUEUED_FOR_THE_LEAD,
    SEND_BACK,
)
from runner.tasks import short_key

router = APIRouter()

GENERAL = "general"
# A request's result when it worked (D1's table); any other result is a refusal.
WORKED = (QUEUED_FOR_THE_LEAD, "approved ", "accepted ", "planted ")
_ADR_NUMBER = re.compile(r"docs/adr/(\d+)-")
_TYPICAL = 20  # finished jobs of the running one's role and agent that make its typical length


@dataclass(frozen=True)
class DeskItem:
    group: str
    title: str
    words: str
    link: str


@dataclass(frozen=True)
class DeskGroup:
    key: str
    name: str
    color: str  # a token from dashboard.css
    items: list[DeskItem]


def _when(at: str) -> datetime:
    return datetime.fromisoformat(at)


def _card_titles(conn: sqlite3.Connection, project_id: int) -> dict[str, str]:
    """Each card's title by its short key (``f7``), the key of a thread."""
    rows = conn.execute(
        "SELECT key, title FROM milestones WHERE project_id = ? ORDER BY id", (project_id,)
    ).fetchall()
    return {short_key(r["key"]): r["title"] or r["key"] for r in rows}


def _thread_title(card: str, titles: dict[str, str]) -> str:
    return "General" if card == GENERAL else titles.get(card, card)


def _answers_wanted(
    conn: sqlite3.Connection, project_id: int, titles: dict[str, str], now: datetime
) -> list[DeskItem]:
    """Threads whose last message is the lead's: a reply the owner hasn't answered."""
    rows = conn.execute(
        "SELECT t.card, m.at FROM planner_threads t"
        " JOIN planner_messages m ON m.id = ("
        "   SELECT max(id) FROM planner_messages WHERE thread_id = t.id)"
        " WHERE t.project_id = ? AND m.author = 'lead' ORDER BY m.id",
        (project_id,),
    ).fetchall()
    return [
        DeskItem(
            "answers",
            _thread_title(r["card"], titles),
            f"the lead replied {ago(now - _when(r['at']))} ago",
            f"/planning/{r['card']}",
        )
        for r in rows
    ]


def _about(proposal: dict[str, object], card: str) -> list[tuple[str, str, str | None]]:
    """The requests about a proposal (D6): (kind, subject, value or None for any value)."""
    pid, kind = str(proposal.get("id")), proposal.get("kind")
    about: list[tuple[str, str, str | None]] = [(SEND_BACK, f"{card}/{pid}", None)]
    if kind == "adr":
        number = _ADR_NUMBER.match(str(proposal.get("path") or ""))
        if number:
            about.append((ACCEPT_ADR, card, str(int(number[1]))))
    elif kind in ("plan", "mockup", "replan"):
        about.append((APPROVE_PLAN, card, None))
    elif kind == "seed":
        about.append((PLANT, f"{GENERAL}/{pid}", None))
    return about


def _settled(requests: list[sqlite3.Row], about: list[tuple[str, str, str | None]]) -> bool:
    """An owner request about the proposal, pending or worked (a refusal leaves it open)."""
    for r in requests:
        for kind, subject, value in about:
            if r["kind"] != kind or r["subject"] != subject:
                continue
            if value is not None and str(r["value"] or "").strip() != value:
                continue
            if r["done"] is None or str(r["result"] or "").startswith(WORKED):
                return True
    return False


def _open_proposals(conn: sqlite3.Connection, project_id: int) -> list[DeskItem]:
    """The proposals in each thread's latest lead message that lists some, still open."""
    rows = conn.execute(
        "SELECT t.card, m.at, m.proposals FROM planner_threads t"
        " JOIN planner_messages m ON m.id = ("
        "   SELECT max(id) FROM planner_messages WHERE thread_id = t.id AND author = 'lead'"
        "   AND proposals IS NOT NULL AND proposals != '[]')"
        " WHERE t.project_id = ? ORDER BY m.id",
        (project_id,),
    ).fetchall()
    requests = conn.execute(
        "SELECT * FROM owner_requests WHERE project_id = ? ORDER BY id", (project_id,)
    ).fetchall()
    items = []
    for row in rows:
        since = _when(row["at"])
        later = [r for r in requests if _when(r["created"]) > since]
        for proposal in json.loads(row["proposals"]):
            if not isinstance(proposal, dict) or not proposal.get("id"):
                continue
            if _settled(later, _about(proposal, row["card"])):
                continue
            points = proposal.get("key_points")
            words = f"{len(points)} key points" if isinstance(points, list) and points else ""
            items.append(
                DeskItem(
                    "proposals",
                    str(proposal.get("title") or proposal["id"]),
                    words or str(proposal.get("kind") or ""),
                    f"/planning/{row['card']}/proposals/{proposal['id']}",
                )
            )
    return items


def _ripe(conn: sqlite3.Connection, project: str, now: datetime) -> list[DeskItem]:
    """Every ticket done and not signed off, as the line's field has them."""
    return [
        DeskItem(
            "ripe",
            m["title"] or m["key"],
            "every ticket merged · waits for your sign-off",
            f"/planning/{short_key(m['key'])}",
        )
        for m in live_line(conn, project, now)["field"]["ripe"]
    ]


def _seeds(conn: sqlite3.Connection, project_id: int) -> list[DeskItem]:
    """Idea cards no thread is about yet."""
    threads = {
        r["card"]
        for r in conn.execute(
            "SELECT card FROM planner_threads WHERE project_id = ?", (project_id,)
        ).fetchall()
    }
    rows = conn.execute(
        "SELECT key, title FROM milestones WHERE project_id = ? AND state = 'idea' ORDER BY id",
        (project_id,),
    ).fetchall()
    return [
        DeskItem("seeds", r["title"] or r["key"], "an idea, not asked about yet", f"/planning/{k}")
        for r in rows
        if (k := short_key(r["key"])) not in threads
    ]


def desk(conn: sqlite3.Connection, project: str, now: datetime) -> list[DeskGroup]:
    """What waits for the owner (D6), in four groups in this order, empty ones included."""
    project_id = metrics.find_project(conn, project)
    if project_id is None:
        answers: list[DeskItem] = []
        proposals: list[DeskItem] = []
        ripe: list[DeskItem] = []
        seeds: list[DeskItem] = []
    else:
        titles = _card_titles(conn, project_id)
        answers = _answers_wanted(conn, project_id, titles, now)
        proposals = _open_proposals(conn, project_id)
        ripe = _ripe(conn, project, now)
        seeds = _seeds(conn, project_id)
    return [
        DeskGroup("answers", "Your answers wanted", "--hazard", answers),
        DeskGroup("proposals", "Proposals to review", "--opus", proposals),
        DeskGroup("ripe", "Finished, to talk through", "--qwen", ripe),
        DeskGroup("seeds", "Seeds, not asked about yet", "--ink-2", seeds),
    ]


# --- the tiles ----------------------------------------------------------------------------


def _typical(conn: sqlite3.Connection, project: str, job: Running) -> timedelta | None:
    """How long the last finished jobs of the running job's role and agent took, on average."""
    rows = conn.execute(
        "SELECT j.started, j.ended FROM jobs j JOIN runs r ON r.id = j.run_id"
        " JOIN projects p ON p.id = r.project_id"
        " WHERE p.name = ? AND j.role = ? AND j.agent = ? AND j.outcome != 'running'"
        " AND j.started IS NOT NULL AND j.ended IS NOT NULL ORDER BY j.id DESC LIMIT ?",
        (project, job.role, job.agent, _TYPICAL),
    ).fetchall()
    spans = [_when(r["ended"]) - _when(r["started"]) for r in rows]
    return sum(spans, timedelta()) / len(spans) if spans else None


def _what(job: Running) -> str:
    return job.ticket or job.role


def _next_reply(
    conn: sqlite3.Connection, project: str, jobs: list[Running], pending: bool
) -> str | None:
    """When the owner's pending message is answered: after the running job, planning going
    first (D1); ``None`` with nothing pending."""
    if not pending:
        return None
    if any(j.role == PLANNER for j in jobs):
        return "the lead is writing its reply now"
    if not jobs:
        return "at the factory's next pick"
    job = jobs[0]
    typical = _typical(conn, project, job)
    if typical is None:
        return f"after {_what(job)}"
    left = typical - job.elapsed
    if left < timedelta(minutes=1):
        return f"after {_what(job)}, any minute now"
    return f"after {_what(job)}, ~{ago(left)}"


def factory_now(conn: sqlite3.Connection, project: str, now: datetime) -> dict[str, object]:
    """The tile: the running job, and when the next reply is expected."""
    jobs = [j for j in running_jobs(conn, project, now) if j.live]
    project_id = metrics.find_project(conn, project)
    pending = project_id is not None and any(
        r["kind"] == PLANNER for r in metrics.open_jobs(conn, project_id)
    )
    working = [j for j in jobs if j.role != PLANNER]
    return {
        "running": working[0] if working else None,
        "next_reply": _next_reply(conn, project, jobs, pending),
    }


@router.get("/planning", response_class=HTMLResponse)
def planning(request: Request, conn: Db, project: Project, now: Now) -> HTMLResponse:
    """The owner's desk: the two tiles, what waits for the owner, and Plant an idea."""
    window = next(
        (a for a in agent_allowances(conn, now) if a.label == "Claude" and a.window == "five_hour"),
        None,
    )
    return render(
        request,
        conn,
        project,
        "planning.html",
        {
            "active": "/planning",
            "factory": factory_now(conn, project, now),
            "window": window,
            "groups": desk(conn, project, now),
        },
    )
