"""The Jobs list (ADR 13 item 2, f1 D2)."""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from factory_dashboard.app import Db, Project, render

router = APIRouter()


@dataclass(frozen=True)
class JobRow:
    id: int
    started: str
    ticket: str | None
    role: str
    agent: str
    attempt: int
    outcome: str
    minutes: float | None
    tokens_in: int | None
    tokens_out: int | None
    failed_gate: str | None


@dataclass(frozen=True)
class FindingRow:
    key: str
    severity: str
    summary: str


@dataclass(frozen=True)
class JobDetail:
    id: int
    started: str
    ended: str | None
    role: str
    agent: str
    attempt: int
    outcome: str
    routing_reason: str | None
    minutes: float | None
    tokens_in: int | None
    tokens_cached: int | None
    tokens_out: int | None
    requests: int | None
    cost_usd: float | None
    steps: int | None
    peak_context: int | None
    context_limit: int | None
    edit_streak: int | None
    refused_commands: int | None
    note: str | None
    session_id: str | None
    log_path: str | None
    gates: list[dict[str, object]] | None
    findings: list[FindingRow]
    ticket: str | None
    milestone_key: str | None


def _parse_gates(gates_json: str | None) -> list[dict[str, object]] | None:
    if not gates_json:
        return None
    return json.loads(gates_json)  # type: ignore[no-any-return]


def _failed_gate(gates_json: str | None) -> str | None:
    gates = _parse_gates(gates_json)
    if gates:
        for gate in gates:
            if gate.get("ok") is False:
                name: object | None = gate.get("name")
                return str(name) if name is not None else None
    return None


def get_job_detail(conn: sqlite3.Connection, job_id: int) -> JobDetail | None:
    """A single job by ``job_id``, with its gates, findings, and metadata."""
    row = conn.execute(
        "SELECT j.id, j.started, j.ended, j.role, j.agent, j.attempt, "
        "j.outcome, j.routing_reason, j.tokens_in, j.tokens_cached, "
        "j.tokens_out, j.requests, j.cost_usd, j.steps, "
        "j.peak_context, j.context_limit, j.edit_streak, j.refused_commands, "
        "j.gates, j.note, j.session_id, j.log_path, "
        "t.ticket, m.key AS milestone_key "
        "FROM jobs j "
        "JOIN runs r ON r.id = j.run_id "
        "JOIN projects p ON p.id = r.project_id "
        "LEFT JOIN tickets t ON t.id = j.ticket_id "
        "LEFT JOIN milestones m ON m.id = j.milestone_id "
        "WHERE j.id = ?",
        (job_id,),
    ).fetchone()
    if row is None:
        return None

    minutes: float | None = None
    if row["started"] and row["ended"]:
        start = datetime.fromisoformat(row["started"])
        end = datetime.fromisoformat(row["ended"])
        minutes = (end - start).total_seconds() / 60

    gates = _parse_gates(row["gates"])

    findings_rows = conn.execute(
        "SELECT key, severity, summary FROM findings WHERE job_id = ? ORDER BY id",
        (job_id,),
    ).fetchall()
    findings = [
        FindingRow(key=f["key"], severity=f["severity"], summary=f["summary"] or "")
        for f in findings_rows
    ]

    return JobDetail(
        id=row["id"],
        started=row["started"],
        ended=row["ended"],
        role=row["role"],
        agent=row["agent"],
        attempt=row["attempt"],
        outcome=row["outcome"],
        routing_reason=row["routing_reason"],
        minutes=minutes,
        tokens_in=row["tokens_in"],
        tokens_cached=row["tokens_cached"],
        tokens_out=row["tokens_out"],
        requests=row["requests"],
        cost_usd=row["cost_usd"],
        steps=row["steps"],
        peak_context=row["peak_context"],
        context_limit=row["context_limit"],
        edit_streak=row["edit_streak"],
        refused_commands=row["refused_commands"],
        note=row["note"],
        session_id=row["session_id"],
        log_path=row["log_path"],
        gates=gates,
        findings=findings,
        ticket=row["ticket"],
        milestone_key=row["milestone_key"],
    )


def list_jobs(
    conn: sqlite3.Connection,
    project: str,
    *,
    milestone: str | None = None,
    ticket: str | None = None,
    agent: str | None = None,
    role: str | None = None,
    outcome: str | None = None,
) -> tuple[list[JobRow], int]:
    """All jobs for ``project``, newest first. Returns (rows, total_count)."""
    conditions = ["p.name = ?"]
    params: list[object] = [project]

    if milestone:
        conditions.append("m.key = ?")
        params.append(milestone)
    if ticket:
        conditions.append("t.ticket = ?")
        params.append(ticket)
    if agent:
        conditions.append("j.agent = ?")
        params.append(agent)
    if role:
        conditions.append("j.role = ?")
        params.append(role)
    if outcome:
        conditions.append("j.outcome = ?")
        params.append(outcome)

    where = " AND ".join(conditions)

    count_sql = (
        f"SELECT COUNT(*) AS n FROM jobs j "  # noqa: S608
        f"JOIN runs r ON r.id = j.run_id "
        f"JOIN projects p ON p.id = r.project_id "
        f"LEFT JOIN tickets t ON t.id = j.ticket_id "
        f"LEFT JOIN milestones m ON m.id = j.milestone_id "
        f"WHERE {where}"
    )
    total = conn.execute(count_sql, params).fetchone()["n"]

    query_sql = (
        f"SELECT j.id, j.started, j.ended, j.role, j.agent, j.attempt, "  # noqa: S608
        f"j.outcome, j.tokens_in, j.tokens_out, j.gates, "
        f"t.ticket "
        f"FROM jobs j "
        f"JOIN runs r ON r.id = j.run_id "
        f"JOIN projects p ON p.id = r.project_id "
        f"LEFT JOIN tickets t ON t.id = j.ticket_id "
        f"LEFT JOIN milestones m ON m.id = j.milestone_id "
        f"WHERE {where} "
        f"ORDER BY j.started DESC, j.id DESC "
        f"LIMIT 201"
    )
    rows = conn.execute(query_sql, params).fetchall()

    jobs: list[JobRow] = []
    for row in rows:
        minutes: float | None = None
        if row["started"] and row["ended"]:
            start = datetime.fromisoformat(row["started"])
            end = datetime.fromisoformat(row["ended"])
            minutes = (end - start).total_seconds() / 60

        jobs.append(
            JobRow(
                id=row["id"],
                started=row["started"],
                ticket=row["ticket"],
                role=row["role"],
                agent=row["agent"],
                attempt=row["attempt"],
                outcome=row["outcome"],
                minutes=minutes,
                tokens_in=row["tokens_in"],
                tokens_out=row["tokens_out"],
                failed_gate=_failed_gate(row["gates"]),
            )
        )

    return jobs, total


@router.get("/jobs", response_class=HTMLResponse)
def jobs_page(
    request: Request,
    conn: Db,
    project: Project,
    *,
    milestone: Annotated[str | None, Query()] = None,
    ticket: Annotated[str | None, Query()] = None,
    agent: Annotated[str | None, Query()] = None,
    role: Annotated[str | None, Query()] = None,
    outcome: Annotated[str | None, Query()] = None,
) -> HTMLResponse:
    jobs, total = list_jobs(
        conn, project, milestone=milestone, ticket=ticket, agent=agent, role=role, outcome=outcome
    )
    more = max(0, total - 200)

    return render(
        request,
        conn,
        project,
        "jobs.html",
        {
            "active": "/jobs",
            "jobs": jobs,
            "total": total,
            "more": more,
            "milestone_filter": milestone,
            "ticket_filter": ticket,
            "agent_filter": agent,
            "role_filter": role,
            "outcome_filter": outcome,
        },
    )


@router.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_page(job_id: int, request: Request, conn: Db, project: Project) -> HTMLResponse:
    detail = get_job_detail(conn, job_id)
    if detail is None:
        return HTMLResponse(status_code=404, content="Not found")
    return render(
        request,
        conn,
        project,
        "job.html",
        {
            "active": "/jobs",
            "job": detail,
            "ticket": detail.ticket,
            "milestone_key": detail.milestone_key,
        },
    )
