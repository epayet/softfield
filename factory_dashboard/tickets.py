"""The Tickets list and a single ticket's story (ADR 13 item 2, f1 D2).

- ``/tickets``: newest first, filterable by ``milestone`` and ``state``.
- ``/tickets/{ticket_id}``: goal, Done when, depends_on, result, every job, findings.
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from factory_dashboard.app import Db, Now, Project, render

router = APIRouter()


@dataclass(frozen=True)
class TicketRow:
    id: int
    ticket: str
    milestone: str | None
    kind: str | None
    difficulty: int | None
    state: str | None
    attempts: int
    merged_by: str | None
    lines_changed: int | None
    last_worked: timedelta | None  # how long ago its latest job started


@dataclass(frozen=True)
class TicketDetail:
    ticket: str
    milestone: str | None
    milestone_title: str | None
    body: str | None
    kind: str | None
    depends_on: list[str]
    files: list[str]
    state: str | None
    merged_by: str | None
    commit: str | None
    lines_changed: int | None


@dataclass(frozen=True)
class JobRow:
    id: int
    attempt: int
    role: str
    agent: str
    outcome: str
    started: str
    ended: str | None
    cost_usd: float | None
    tokens_in: int | None


@dataclass(frozen=True)
class FindingRow:
    key: str
    severity: str
    summary: str


@dataclass(frozen=True)
class TicketAgentWork:
    agent: str
    roles: str
    job_count: int
    minutes: int
    tokens_in: int
    cost_usd: str
    merged: bool = False


def list_later_tickets(
    conn: sqlite3.Connection,
    project: str,
    *,
    milestone: str | None = None,
) -> list[dict[str, str | None]]:
    """Tickets set aside (state ``later``) for ``project``, optionally filtered by
    ``milestone``. The page's state filter doesn't apply: the panel only ever lists these."""
    conditions = ["p.name = ?"]
    params: list[object] = [project]

    if milestone:
        conditions.append("m.key = ?")
        params.append(milestone)

    conditions.append("t.state = 'later'")

    where = " AND ".join(conditions)

    rows = conn.execute(
        f"SELECT t.ticket, t.title, t.kind "  # noqa: S608
        "FROM tickets t "
        "JOIN projects p ON p.id = t.project_id "
        "LEFT JOIN milestones m ON m.id = t.milestone_id "
        f"WHERE {where} "
        f"ORDER BY t.ticket",
        tuple(params),
    ).fetchall()
    return [
        {
            "ticket": row["ticket"],
            "title": row["title"],
            "kind": row["kind"],
        }
        for row in rows
    ]


def list_tickets(
    conn: sqlite3.Connection,
    project: str,
    *,
    milestone: str | None = None,
    state: str | None = None,
    now: datetime,
) -> list[TicketRow]:
    """All tickets for ``project``, latest work first (by their jobs' latest start, then id DESC).

    A ticket with no job yet comes after every worked one.
    """
    conditions = ["p.name = ?"]
    params: list[object] = [project]

    if milestone:
        conditions.append("m.key = ?")
        params.append(milestone)
    if state:
        conditions.append("t.state = ?")
        params.append(state)

    where = " AND ".join(conditions)

    query = (
        f"SELECT t.id, t.ticket, m.key AS milestone, t.kind, t.difficulty, t.state, "  # noqa: S608
        f"(SELECT COUNT(*) FROM jobs j WHERE j.ticket_id = t.id) AS attempts, "
        f"t.merged_by, t.lines_changed, "
        f"(SELECT MAX(j.started) FROM jobs j WHERE j.ticket_id = t.id) AS last_worked "
        f"FROM tickets t "
        f"JOIN projects p ON p.id = t.project_id "
        f"LEFT JOIN milestones m ON m.id = t.milestone_id "
        f"WHERE {where} "
        f"ORDER BY last_worked IS NULL, last_worked DESC, t.id DESC"
    )
    rows = conn.execute(query, params).fetchall()
    return [
        TicketRow(
            id=row["id"],
            ticket=row["ticket"],
            milestone=row["milestone"],
            kind=row["kind"],
            difficulty=row["difficulty"],
            state=row["state"],
            attempts=row["attempts"],
            merged_by=row["merged_by"],
            lines_changed=row["lines_changed"],
            last_worked=now - datetime.fromisoformat(row["last_worked"])
            if row["last_worked"]
            else None,
        )
        for row in rows
    ]


def get_ticket(conn: sqlite3.Connection, project: str, ticket_id: str) -> TicketDetail | None:
    """A single ticket by its text id (like ``f1-01-first``)."""
    row = conn.execute(
        "SELECT t.ticket, m.key AS milestone, m.title AS milestone_title, "
        "t.body, t.kind, t.depends_on, t.files, t.state, "
        't.merged_by, t."commit", t.lines_changed '
        "FROM tickets t "
        "JOIN projects p ON p.id = t.project_id "
        "LEFT JOIN milestones m ON m.id = t.milestone_id "
        "WHERE p.name = ? AND t.ticket = ?",
        (project, ticket_id),
    ).fetchone()
    if row is None:
        return None

    depends_on: list[str] = []
    if row["depends_on"]:
        depends_on = json.loads(row["depends_on"])

    files: list[str] = []
    if row["files"]:
        files = json.loads(row["files"])

    return TicketDetail(
        ticket=row["ticket"],
        milestone=row["milestone"],
        milestone_title=row["milestone_title"],
        body=row["body"],
        kind=row["kind"],
        depends_on=depends_on,
        files=files,
        state=row["state"],
        merged_by=row["merged_by"],
        commit=row["commit"],
        lines_changed=row["lines_changed"],
    )


def ticket_jobs(conn: sqlite3.Connection, ticket_id: int) -> list[JobRow]:
    """All jobs for a ticket, ordered by attempt ascending."""
    rows = conn.execute(
        "SELECT j.id, j.attempt, j.role, j.agent, j.outcome, "
        "       j.started, j.ended, j.cost_usd, j.tokens_in "
        "FROM jobs j "
        "WHERE j.ticket_id = ? "
        "ORDER BY j.attempt ASC, j.id ASC",
        (ticket_id,),
    ).fetchall()
    return [
        JobRow(
            id=row["id"],
            attempt=row["attempt"],
            role=row["role"],
            agent=row["agent"],
            outcome=row["outcome"],
            started=row["started"],
            ended=row["ended"],
            cost_usd=row["cost_usd"],
            tokens_in=row["tokens_in"],
        )
        for row in rows
    ]


def ticket_agent_work(conn: sqlite3.Connection, ticket_id: int) -> list[TicketAgentWork]:
    """Agent work summary for a ticket: roles, counts, minutes, tokens, cost."""
    rows = conn.execute(
        "SELECT j.agent, j.role, "
        "       CAST((julianday(j.ended) - julianday(j.started)) * 24 * 60 AS INTEGER) "
        "          AS minutes, "
        "       j.cost_usd, j.tokens_in "
        "FROM jobs j "
        "WHERE j.ticket_id = ? "
        "ORDER BY j.attempt ASC, j.id ASC",
        (ticket_id,),
    ).fetchall()

    merged_by: str | None = conn.execute(
        "SELECT merged_by FROM tickets WHERE id = ?", (ticket_id,)
    ).fetchone()["merged_by"]

    agent_data: dict[str, Any] = {}
    for row in rows:
        agent = row["agent"]
        if agent not in agent_data:
            agent_data[agent] = {
                "roles": [],
                "job_count": 0,
                "minutes": 0,
                "tokens_in": 0,
                "cost_usd": 0.0,
            }
        ad = agent_data[agent]
        ad["roles"].append(row["role"])
        ad["job_count"] = ad["job_count"] + 1
        ad["minutes"] = ad["minutes"] + (row["minutes"] or 0)
        ad["tokens_in"] = ad["tokens_in"] + (row["tokens_in"] or 0)
        ad["cost_usd"] = ad["cost_usd"] + (row["cost_usd"] or 0.0)

    def fmt_roles(roles: list[str]) -> str:
        counts: dict[str, int] = {}
        for r in roles:
            counts[r] = counts.get(r, 0) + 1
        parts: list[str] = []
        for r, c in counts.items():
            if c > 1:
                parts.append(f"{r} \u00d7{c}")
            else:
                parts.append(r)
        return ", ".join(parts)

    result: list[TicketAgentWork] = []
    if merged_by and merged_by in agent_data:
        ad = agent_data[merged_by]
        cost = ad["cost_usd"]
        result.append(
            TicketAgentWork(
                agent=merged_by,
                roles=fmt_roles(ad["roles"]),
                job_count=ad["job_count"],
                minutes=ad["minutes"],
                tokens_in=ad["tokens_in"],
                cost_usd=f"{cost:.2f}" if cost > 0 else "\u2013",
                merged=True,
            )
        )
        del agent_data[merged_by]
    for agent, ad in sorted(
        agent_data.items(),
        key=lambda x: x[1]["minutes"],
        reverse=True,
    ):
        cost = ad["cost_usd"]
        result.append(
            TicketAgentWork(
                agent=agent,
                roles=fmt_roles(ad["roles"]),
                job_count=ad["job_count"],
                minutes=ad["minutes"],
                tokens_in=ad["tokens_in"],
                cost_usd=f"{cost:.2f}" if cost > 0 else "\u2013",
            )
        )
    return result


def ticket_findings(
    conn: sqlite3.Connection,
    milestone_id: int,
    *,
    ticket_id: int | None = None,
) -> list[FindingRow]:
    """Findings on a milestone, optionally filtered to a specific ticket.

    Findings with ``ticket_id`` set show only on that ticket;
    findings without one show on no ticket page.
    """
    conditions = ["milestone_id = ?"]
    params: list[object] = [milestone_id]

    if ticket_id is not None:
        conditions.append("ticket_id = ?")
        params.append(ticket_id)

    where = " AND ".join(conditions)

    rows = conn.execute(
        f"SELECT key, severity, summary FROM findings WHERE {where} ORDER BY id",  # noqa: S608
        tuple(params),
    ).fetchall()
    return [
        FindingRow(
            key=row["key"],
            severity=row["severity"],
            summary=row["summary"] or "",
        )
        for row in rows
    ]


@router.get("/tickets", response_class=HTMLResponse)
def tickets_page(
    request: Request,
    conn: Db,
    project: Project,
    now: Now,
    *,
    milestone: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query()] = None,
) -> HTMLResponse:
    tickets = list_tickets(conn, project, milestone=milestone, state=state, now=now)
    later_tickets = list_later_tickets(conn, project, milestone=milestone)
    return render(
        request,
        conn,
        project,
        "tickets.html",
        {
            "active": "/tickets",
            "tickets": tickets,
            "later_tickets": later_tickets,
            "milestone_filter": milestone,
            "state_filter": state,
        },
    )


@router.get("/tickets/{ticket_id}", response_class=HTMLResponse)
def ticket_page(
    ticket_id: str,
    request: Request,
    conn: Db,
    project: Project,
) -> HTMLResponse:
    detail = get_ticket(conn, project, ticket_id)
    if detail is None:
        return HTMLResponse(status_code=404, content="Not found")

    ticket_row = conn.execute(
        "SELECT t.id, m.id AS milestone_id FROM tickets t "
        "JOIN projects p ON p.id = t.project_id "
        "LEFT JOIN milestones m ON m.id = t.milestone_id "
        "WHERE p.name = ? AND t.ticket = ?",
        (project, ticket_id),
    ).fetchone()

    jobs: list[JobRow] = []
    findings: list[FindingRow] = []
    if ticket_row:
        jobs = ticket_jobs(conn, ticket_row["id"])
        if ticket_row["milestone_id"]:
            findings = ticket_findings(
                conn,
                ticket_row["milestone_id"],
                ticket_id=ticket_row["id"],
            )

    agent_work: list[TicketAgentWork] = []
    if ticket_row:
        agent_work = ticket_agent_work(conn, ticket_row["id"])

    return render(
        request,
        conn,
        project,
        "ticket.html",
        {
            "active": "/tickets",
            "ticket": detail,
            "jobs": jobs,
            "findings": findings,
            "agent_work": agent_work,
        },
    )
