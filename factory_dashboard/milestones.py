"""The Milestones list page (f1-12, D8), with trends across them.

One row per milestone: key (a link to ``/milestones/{key}``), title, status, dates,
tickets merged, first-attempt pass rate, escalations, review rounds, Claude dollars,
net savings. Trends below: first-attempt rate, escalations, Claude dollars per merged
ticket and savings per milestone, as small charts (D5).
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from factory_dashboard import queries
from factory_dashboard.app import Db, Now, Project, render

router = APIRouter()


@dataclass(frozen=True)
class MilestoneRow:
    key: str
    title: str | None
    status: str | None
    started: str | None
    ended: str | None
    tickets: int
    merged: int
    pass_rate: float | None
    escalations: int
    review_rounds: int
    claude_dollars: float
    net_savings: float


def milestone_rows(conn: sqlite3.Connection, project: str) -> list[MilestoneRow]:
    """Every milestone's summary, newest first. Milestones with no tickets show dashes."""
    # Milestones with data from trends (oldest first).
    with_data: list[MilestoneRow] = []
    for trend in queries.trends(conn, project):
        r = trend.results
        s = trend.savings
        # Skip milestones with no tickets (they show dashes, not zeros).
        if r.merged == 0:
            continue
        with_data.append(
            MilestoneRow(
                key=r.key,
                title=r.title,
                status=None,
                started=None,
                ended=None,
                tickets=r.tickets,
                merged=r.merged,
                pass_rate=r.pass_rate,
                escalations=r.escalations,
                review_rounds=r.review_rounds,
                claude_dollars=r.claude.dollars,
                net_savings=s.net,
            )
        )
    # Milestones without tickets (from the DB).
    no_data = conn.execute(
        "SELECT m.key, m.title, m.status, m.started, m.ended FROM milestones m"
        " JOIN projects p ON p.id = m.project_id WHERE p.name = ?"
        " ORDER BY m.status IS 'done', m.started DESC, m.id DESC",
        (project,),
    ).fetchall()
    seen = {row.key for row in with_data}
    no_data_rows: list[MilestoneRow] = []
    for m in no_data:
        if m["key"] not in seen:
            no_data_rows.append(
                MilestoneRow(
                    key=m["key"],
                    title=m["title"],
                    status=m["status"],
                    started=m["started"],
                    ended=m["ended"],
                    tickets=0,
                    merged=0,
                    pass_rate=None,
                    escalations=0,
                    review_rounds=0,
                    claude_dollars=0.0,
                    net_savings=0.0,
                )
            )
    # Merge and sort newest first by started date.
    all_rows: list[MilestoneRow] = [*with_data, *no_data_rows]

    def _sort_key(r: MilestoneRow) -> tuple[int, float, str]:
        started = r.started
        ts = datetime.fromisoformat(started).timestamp() if started else 0.0
        return (0 if started else 1, -ts, r.key)

    return sorted(all_rows, key=_sort_key)


def _rate_chart(conn: sqlite3.Connection, project: str) -> dict[str, Any]:
    points = [p for p in queries.trends(conn, project) if p.results.merged > 0]
    return {
        "labels": [p.results.key.upper() for p in points],
        "rate": [
            round(p.results.pass_rate * 100, 1) if p.results.pass_rate is not None else None
            for p in points
        ],
    }


def _esc_chart(conn: sqlite3.Connection, project: str) -> dict[str, Any]:
    points = [p for p in queries.trends(conn, project) if p.results.merged > 0]
    return {
        "labels": [p.results.key.upper() for p in points],
        "count": [p.results.escalations for p in points],
    }


def _dollars_chart(conn: sqlite3.Connection, project: str) -> dict[str, Any]:
    points = [p for p in queries.trends(conn, project) if p.results.merged > 0]
    return {
        "labels": [p.results.key.upper() for p in points],
        "dollars": [
            round(p.results.claude.dollars / p.results.merged, 2) if p.results.merged else None
            for p in points
        ],
    }


def _savings_chart(conn: sqlite3.Connection, project: str) -> dict[str, Any]:
    points = [p for p in queries.trends(conn, project) if p.results.merged > 0]
    return {
        "labels": [p.results.key.upper() for p in points],
        "savings": [round(p.savings.net, 2) for p in points],
    }


@router.get("/milestones", response_class=HTMLResponse)
def milestones_list(request: Request, conn: Db, project: Project, now: Now) -> HTMLResponse:
    rows = milestone_rows(conn, project)
    return render(
        request,
        conn,
        project,
        "milestones.html",
        {
            "active": "/milestones",
            "milestones": rows,
            "rate": _rate_chart(conn, project),
            "esc": _esc_chart(conn, project),
            "dollars": _dollars_chart(conn, project),
            "savings": _savings_chart(conn, project),
        },
    )
