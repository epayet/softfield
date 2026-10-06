"""The Timeline page (f1-11): runs and jobs over time, one lane per agent, coloured by outcome."""

import sqlite3
from dataclasses import dataclass
from datetime import datetime

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from factory_dashboard.app import Db, Now, Project, render
from factory_dashboard.overview import current_milestone

router = APIRouter()


@dataclass(frozen=True)
class Bar:
    ticket: str | None
    role: str
    outcome: str
    start: str
    end: str | None
    minutes: float | None
    job_id: int


@dataclass(frozen=True)
class Marker:
    agent: str
    at: str


def timeline_data(
    conn: sqlite3.Connection,
    project: str,
    *,
    milestone: str | None = None,
    run: str | None = None,
    now: datetime,
) -> dict[str, object]:
    """The timeline chart data: lanes per agent, bars per job, refusal markers."""
    conditions = ["p.name = ?"]
    params: list[object] = [project]

    if milestone:
        conditions.append("m.key = ?")
        params.append(milestone)
    if run:
        conditions.append("r.run_dir = ?")
        params.append(run)

    where = " AND ".join(conditions)

    rows = conn.execute(
        "SELECT j.id, j.started, j.ended, j.role, j.agent, j.outcome, "
        "t.ticket "
        "FROM jobs j "
        "JOIN runs r ON r.id = j.run_id "
        "JOIN projects p ON p.id = r.project_id "
        "LEFT JOIN tickets t ON t.id = j.ticket_id "
        "LEFT JOIN milestones m ON m.id = j.milestone_id "
        "WHERE " + where + " "
        "ORDER BY j.started, j.id",
        params,
    ).fetchall()

    # Group by agent
    agent_bars: dict[str, list[Bar]] = {}
    for row in rows:
        agent = row["agent"]
        if agent not in agent_bars:
            agent_bars[agent] = []

        minutes: float | None = None
        if row["started"] and row["ended"]:
            start = datetime.fromisoformat(row["started"])
            end = datetime.fromisoformat(row["ended"])
            minutes = (end - start).total_seconds() / 60

        end_str = row["ended"] if row["ended"] else now.isoformat()

        agent_bars[agent].append(
            Bar(
                ticket=row["ticket"],
                role=row["role"],
                outcome=row["outcome"],
                start=row["started"],
                end=end_str,
                minutes=round(minutes) if minutes is not None else None,
                job_id=row["id"],
            )
        )

    # Get refusal markers
    refusal_rows = conn.execute(
        "SELECT agent, at FROM usage_events WHERE kind = 'refusal' ORDER BY at"
    ).fetchall()
    markers_by_agent: dict[str, list[Marker]] = {}
    for row in refusal_rows:
        agent = row["agent"]
        if agent not in markers_by_agent:
            markers_by_agent[agent] = []
        markers_by_agent[agent].append(Marker(agent=agent, at=row["at"]))

    # Build lanes in order
    lanes: list[dict[str, object]] = []
    for agent in sorted(agent_bars.keys()):
        lanes.append(
            {
                "agent": agent,
                "bars": [
                    {
                        "ticket": b.ticket,
                        "role": b.role,
                        "outcome": b.outcome,
                        "start": b.start,
                        "end": b.end,
                        "minutes": b.minutes,
                        "job_id": b.job_id,
                    }
                    for b in agent_bars[agent]
                ],
                "markers": [
                    {"agent": m.agent, "at": m.at} for m in markers_by_agent.get(agent, [])
                ],
            }
        )

    return {"lanes": lanes}


@router.get("/timeline", response_class=HTMLResponse)
def timeline_page(
    request: Request,
    conn: Db,
    project: Project,
    *,
    milestone: str | None = Query(default=None),
    run: str | None = Query(default=None),
    now: Now,
) -> HTMLResponse:
    # Get default milestone
    default_milestone: str | None = None
    current = current_milestone(conn, project)
    if current:
        default_milestone = current["key"]

    filter_milestone = milestone if milestone is not None else default_milestone

    data = timeline_data(conn, project, milestone=filter_milestone, run=run, now=now)

    milestones = conn.execute(
        "SELECT m.key, m.title FROM milestones m "
        "JOIN projects p ON p.id = m.project_id "
        "WHERE p.name = ? ORDER BY m.started DESC",
        (project,),
    ).fetchall()

    runs = conn.execute(
        "SELECT r.run_dir FROM runs r "
        "JOIN projects p ON p.id = r.project_id "
        "WHERE p.name = ? ORDER BY r.started DESC",
        (project,),
    ).fetchall()

    return render(
        request,
        conn,
        project,
        "timeline.html",
        {
            "active": "/timeline",
            "data": data,
            "milestones": milestones,
            "runs": runs,
            "filter_milestone": filter_milestone,
            "run_filter": run,
        },
    )
