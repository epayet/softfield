"""The queue (F279 D6): the whole factory's line, from the plan the runner stored at its last
pick (`metrics.latest_queue_plan`). The page orders nothing itself: it groups the plan's lines
(fast lane, jobs, can go, waits) and folds the waiting ones by the first ticket they wait for.
Factory-wide (F132 D2): ``?project=`` changes the top bar only, each row links with its own.
"""

import sqlite3
from dataclasses import dataclass, field
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from factory_dashboard.app import Db, Project, render
from runner import metrics

router = APIRouter()

NO_PLAN = "The runner hasn't worked out a plan yet: it does at its next pick."
TICKET = "ticket"
WAITING_ON = "waiting on "  # `loop._tickets`'s words for a ticket whose dependencies aren't done
SHOWN = 8  # the rows that can go drawn open; the rest fold into one group
BELT = 6  # crates on the belt
# The owner's requests that change the order (D6), as the page names them
ORDER_KINDS = {
    "approve_plan": "Approve plan",
    "reorder": "The board's new order",
    "project_order": "The projects' new order",
    "queue": "Queue",
    "set_aside": "Set aside",
    "pause": "Pause",
    "resume": "Resume",
    "reserve": "Reserve",
}


@dataclass(frozen=True)
class Row:
    """One line of the plan, numbered in the runner's order."""

    n: int
    project: str
    kind: str
    subject: str
    title: str
    who: str | None
    group: str
    waits: str | None
    reason: str
    card: str | None
    early_for: str | None
    preflight: tuple[str, ...]

    @property
    def is_ticket(self) -> bool:
        return self.kind == TICKET

    @property
    def css(self) -> str:
        return self.who if self.is_ticket and self.who else "job"

    @property
    def who_words(self) -> str:
        return {"lead": "the lead", "developer": "a developer"}.get(self.who or "", "a job")


@dataclass(frozen=True)
class Fold:
    """The waiting rows that wait for one ticket (or for one reason)."""

    key: str  # the ticket they wait for, or the reason itself
    is_ticket: bool
    n: int | None  # that ticket's row, when it is in the list
    project: str
    rows: list[Row] = field(default_factory=list)


@dataclass(frozen=True)
class Pending:
    project: str
    words: str
    subject: str | None


@dataclass(frozen=True)
class Queue:
    sentence: str
    facts: list[str]
    at: str
    lane: list[Row]
    jobs: list[Row]
    go: list[Row]
    waits: list[Fold]
    tickets: int
    job_count: int
    can_go: int
    waiting: int
    by_project: list[tuple[str, int]]
    belt: list[Row]

    @property
    def go_shown(self) -> list[Row]:
        return self.go[:SHOWN]

    @property
    def go_folded(self) -> list[Row]:
        return self.go[SHOWN:]


def _waited_for(waits: str | None) -> tuple[str, bool]:
    """The first ticket a waiting row waits for, or its reason when it waits for no ticket."""
    if waits and waits.startswith(WAITING_ON):
        return waits[len(WAITING_ON) :].split(",")[0].strip(), True
    return waits or "", False


def build(plan: dict[str, Any]) -> Queue:
    """The page's groups from a stored plan, its rows numbered in its order."""
    rows = [
        Row(
            n=i,
            project=line["project"],
            kind=line["kind"],
            subject=line["subject"],
            title=line["title"],
            who=line["who"],
            group=line["group"],
            waits=line["waits"],
            reason=line["reason"],
            card=line["card"],
            early_for=line.get("early_for"),
            preflight=tuple(line.get("preflight") or ()),
        )
        for i, line in enumerate(plan["lines"], start=1)
    ]
    numbers = {(r.project, r.subject): r.n for r in rows if r.is_ticket}
    folds: dict[tuple[str, str], Fold] = {}
    for row in (r for r in rows if r.group == "waits"):
        key, is_ticket = _waited_for(row.waits)
        fold = folds.get((row.project, key))
        if fold is None:
            n = numbers.get((row.project, key)) if is_ticket else None
            fold = folds[(row.project, key)] = Fold(key, is_ticket, n, row.project)
        fold.rows.append(row)
    tickets = [r for r in rows if r.is_ticket]
    per_project: dict[str, int] = {}
    for row in tickets:
        per_project[row.project] = per_project.get(row.project, 0) + 1
    go = [r for r in rows if r.group == "go"]
    lane = [r for r in rows if r.group == "lane"]
    return Queue(
        sentence=plan["sentence"],
        facts=list(plan["facts"]),
        at=plan["at"],
        lane=lane,
        jobs=[r for r in rows if r.group == "jobs"],
        go=go,
        waits=sorted(folds.values(), key=lambda f: -len(f.rows)),
        tickets=len(tickets),
        job_count=len(rows) - len(tickets),
        can_go=len([r for r in go + lane if r.is_ticket]),
        waiting=len([r for r in rows if r.group == "waits"]),
        by_project=list(per_project.items()),
        belt=[r for r in rows if r.group != "waits"][:BELT],
    )


def pending(conn: sqlite3.Connection) -> list[Pending]:
    """The owner's requests that change the order and the runner hasn't applied yet."""
    rows = conn.execute(
        "SELECT r.kind, r.subject, p.name FROM owner_requests r"
        " JOIN projects p ON p.id = r.project_id"
        " WHERE r.done IS NULL AND r.dismissed IS NULL ORDER BY r.id"
    ).fetchall()
    return [
        Pending(row["name"], ORDER_KINDS[row["kind"]], row["subject"])
        for row in rows
        if row["kind"] in ORDER_KINDS
    ]


@router.get("/queue", response_class=HTMLResponse)
def queue(request: Request, conn: Db, project: Project) -> HTMLResponse:
    plan = metrics.latest_queue_plan(conn)
    return render(
        request,
        conn,
        project,
        "queue.html",
        {
            "active": "/queue",
            "plan": None if plan is None else build(plan),
            "no_plan": NO_PLAN,
            "pending": pending(conn),
        },
        is_factory_wide=True,
    )
