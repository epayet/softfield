"""The Bench page (ADR 14 item 8): each replayed ticket against each agent that tried it.

``softfield bench`` records its attempts as jobs of role ``bench``. A cell is a pair's
latest bench (its newest run), whatever came before.
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from factory_dashboard.app import Db, Project, render

router = APIRouter()

COMMAND = "softfield bench <ticket…> --agents <id…>"
WOULD_ESCALATE = "would escalate"


@dataclass(frozen=True)
class Cell:
    result: str  # "passed at attempt 2", "would escalate", "refused", or the outcome
    passed: bool
    minutes: float
    tokens: int
    job: int  # the last bench job


@dataclass(frozen=True)
class Grid:
    agents: list[str]
    tickets: list[tuple[str, int | None]]  # id, difficulty
    cells: dict[tuple[str, str], Cell]


def _minutes(started: str | None, ended: str | None) -> float:
    if not started or not ended:
        return 0.0
    return (datetime.fromisoformat(ended) - datetime.fromisoformat(started)).total_seconds() / 60


def _cell(jobs: list[sqlite3.Row]) -> Cell:
    last = jobs[-1]
    if last["outcome"] == "passed":
        result = f"passed at attempt {len(jobs)}"
    elif last["outcome"] == "refused":
        result = "refused"
    elif last["outcome"] == "running":
        result = "running"
    elif WOULD_ESCALATE in (last["note"] or ""):
        result = WOULD_ESCALATE
    else:
        result = str(last["outcome"])
    return Cell(
        result=result,
        passed=last["outcome"] == "passed",
        minutes=sum(_minutes(j["started"], j["ended"]) for j in jobs),
        tokens=sum((j["tokens_in"] or 0) + (j["tokens_out"] or 0) for j in jobs),
        job=last["id"],
    )


def bench_grid(conn: sqlite3.Connection, project: str) -> Grid:
    rows = conn.execute(
        "SELECT j.id, j.run_id, j.agent, j.outcome, j.note, j.started, j.ended, j.tokens_in,"
        " j.tokens_out, t.ticket, t.difficulty"
        " FROM jobs j JOIN tickets t ON t.id = j.ticket_id JOIN projects p ON p.id = t.project_id"
        " WHERE p.name = ? AND j.role = 'bench' ORDER BY j.id",
        (project,),
    ).fetchall()
    pairs: dict[tuple[str, str], list[sqlite3.Row]] = {}
    for row in rows:
        pairs.setdefault((row["ticket"], row["agent"]), []).append(row)
    cells: dict[tuple[str, str], Cell] = {}
    for key, jobs in pairs.items():
        latest = [j for j in jobs if j["run_id"] == jobs[-1]["run_id"]]
        cells[key] = _cell(latest)
    tickets = {row["ticket"]: row["difficulty"] for row in rows}
    return Grid(
        agents=sorted({row["agent"] for row in rows}),
        tickets=sorted(tickets.items()),
        cells=cells,
    )


@router.get("/bench", response_class=HTMLResponse)
def bench(request: Request, conn: Db, project: Project) -> HTMLResponse:
    return render(
        request,
        conn,
        project,
        "bench.html",
        {"active": "/bench", "grid": bench_grid(conn, project), "command": COMMAND},
    )
