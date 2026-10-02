"""The Agents page (ADR 13 item 3.1, f1 D5, D6): efficiency, who did what, ratings."""

import json
import sqlite3
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from factory_dashboard.app import Db, Project, render
from factory_dashboard.eligibility import eligibility_rows
from factory_dashboard.queries import dollars

router = APIRouter()

ROLES: tuple[str, ...] = (
    "developer",
    "last-attempt",
    "direction",
    "escalation",
    "checkpoint",
    "review",
)


@dataclass(frozen=True)
class Efficiency:
    agent: str
    jobs: int
    merged: int
    attempt_tickets: int
    first_attempt_pass: float | None
    attempts_per_merge: float | None
    minutes_per_merge: float | None
    tokens_per_merge: float | None
    tokens_per_second: float | None
    escalation_rate: float | None
    most_failed_gate: str
    dollars: float
    # Set on the rows under an agent's that split its jobs by model.
    model: str | None = None


# Jobs whose model is NULL or '' (before f2-04, or a harness that didn't say).
NOT_RECORDED = "not recorded"


def efficiency(
    conn: sqlite3.Connection,
    project: str,
    milestone: str | None = None,
) -> list[Efficiency]:
    base_cond = "p.name = ?"
    base_params: list[str] = [project]
    if milestone:
        base_cond += " AND m.key = ?"
        base_params.append(milestone)
    where_clause = " WHERE " + base_cond
    agents = conn.execute(
        "SELECT DISTINCT j.agent FROM jobs j"  # noqa: S608
        " JOIN runs r ON r.id = j.run_id"
        " JOIN projects p ON p.id = r.project_id"
        " LEFT JOIN milestones m ON m.id = j.milestone_id" + where_clause,
        base_params,
    ).fetchall()

    found = []
    for ag in agents:
        agent = ag["agent"]
        agent_cond = base_cond + " AND j.agent = ?"
        agent_params = [*base_params, agent]
        rows = conn.execute(
            "SELECT j.*, t.merged_by FROM jobs j"  # noqa: S608
            " JOIN runs r ON r.id = j.run_id"
            " JOIN projects p ON p.id = r.project_id"
            " LEFT JOIN milestones m ON m.id = j.milestone_id"
            " LEFT JOIN tickets t ON t.id = j.ticket_id" + " WHERE " + agent_cond,
            agent_params,
        ).fetchall()
        found.append(_efficiency(conn, agent, rows))

        # One row per model, under the agent's, when its jobs ran on more than one (f2-07).
        by_model: dict[str, list[sqlite3.Row]] = defaultdict(list)
        for r in rows:
            by_model[r["model"] or NOT_RECORDED].append(r)
        if len(by_model) > 1:
            found.extend(_efficiency(conn, agent, jobs, m) for m, jobs in by_model.items())
    return found


def _efficiency(
    conn: sqlite3.Connection,
    agent: str,
    rows: Sequence[sqlite3.Row],
    model: str | None = None,
) -> Efficiency:
    """One row of the efficiency table, over ``rows``: an agent's jobs, or one model's."""
    total_jobs = len(rows)
    # Tickets, not jobs: three attempts at one merged ticket are one merge.
    merged = len({r["ticket_id"] for r in rows if r["ticket_id"] and r["merged_by"] == agent})

    attempt_rows = [r for r in rows if r["role"] in ("developer", "last-attempt")]
    attempt_ticket_ids = {r["ticket_id"] for r in attempt_rows if r["ticket_id"]}
    attempt_tickets = len(attempt_ticket_ids)

    first_pass = None
    if attempt_tickets:
        first = sum(
            1
            for tid in attempt_ticket_ids
            if len([r for r in attempt_rows if r["ticket_id"] == tid]) == 1
            and any(r["outcome"] == "passed" for r in attempt_rows if r["ticket_id"] == tid)
        )
        first_pass = round(first / attempt_tickets * 100)

    attempts_per_m = round(len(attempt_rows) / merged, 1) if merged else None

    total_seconds = sum(_secs(r["started"], r["ended"]) for r in attempt_rows)
    minutes_per_m = round(total_seconds / 60 / merged, 1) if merged else None

    total_tokens = sum(
        (r["tokens_in"] or 0) + (r["tokens_cached"] or 0) + (r["tokens_out"] or 0) for r in rows
    )
    tokens_per_m = round(total_tokens / merged) if merged else None

    tps = round(total_tokens / total_seconds) if total_seconds and merged else None

    esc_rate = None
    if attempt_tickets and attempt_ticket_ids:
        placeholders = ",".join(["?"] * len(attempt_ticket_ids))
        esc_count = conn.execute(
            "SELECT count(DISTINCT ticket_id) FROM jobs"  # noqa: S608
            " WHERE ticket_id IN (" + placeholders + ")"
            " AND role = 'escalation'",
            list(attempt_ticket_ids),
        ).fetchone()[0]
        esc_rate = round(esc_count / attempt_tickets * 100)

    gate_fails: dict[str, int] = defaultdict(int)
    for r in rows:
        gates = r["gates"]
        if isinstance(gates, str):
            gates = json.loads(gates)
        if isinstance(gates, list):
            for g in gates:
                if g.get("ok") is False:
                    gate_fails[g["name"]] += 1
    most_failed = max(gate_fails, key=lambda k: gate_fails[k]) if gate_fails else ""

    return Efficiency(
        agent=agent,
        jobs=total_jobs,
        merged=merged,
        attempt_tickets=attempt_tickets,
        first_attempt_pass=first_pass,
        attempts_per_merge=attempts_per_m,
        minutes_per_merge=minutes_per_m,
        tokens_per_merge=tokens_per_m,
        tokens_per_second=tps,
        escalation_rate=esc_rate,
        most_failed_gate=most_failed or "\u2013",
        dollars=sum(dollars(r) for r in rows),
        model=model,
    )


def _secs(started: str | None, ended: str | None) -> int:
    if not started or not ended:
        return 0
    s = datetime.fromisoformat(started)
    e = datetime.fromisoformat(ended)
    return max(0, int((e - s).total_seconds()))


def agents_roles(
    conn: sqlite3.Connection,
    project: str,
    milestone: str | None = None,
) -> tuple[list[str], tuple[str, ...], dict[str, dict[str, int]]]:
    base_cond = "p.name = ?"
    base_params: list[str] = [project]
    if milestone:
        base_cond += " AND m.key = ?"
        base_params.append(milestone)
    where_clause = " WHERE " + base_cond
    agents = conn.execute(
        "SELECT DISTINCT j.agent FROM jobs j"  # noqa: S608
        " JOIN runs r ON r.id = j.run_id"
        " JOIN projects p ON p.id = r.project_id"
        " LEFT JOIN milestones m ON m.id = j.milestone_id" + where_clause,
        base_params,
    ).fetchall()
    agent_names = [a["agent"] for a in agents]
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in conn.execute(
        "SELECT j.agent, j.role FROM jobs j"  # noqa: S608
        " JOIN runs r ON r.id = j.run_id"
        " JOIN projects p ON p.id = r.project_id"
        " LEFT JOIN milestones m ON m.id = j.milestone_id" + where_clause,
        base_params,
    ).fetchall():
        counts[row["agent"]][row["role"]] += 1
    return agent_names, ROLES, dict(counts)


def rating_data(
    conn: sqlite3.Connection,
    project: str,
    milestone: str | None = None,
) -> dict[str, Sequence[str] | Sequence[float]]:
    base_cond = "p.name = ?"
    base_params: list[str] = [project]
    if milestone:
        base_cond += " AND m.key = ?"
        base_params.append(milestone)
    where_clause = " WHERE " + base_cond
    changes = conn.execute(
        (
            "SELECT agent, skill, at, after FROM rating_changes"  # noqa: S608
            " JOIN tickets t ON t.id = rating_changes.ticket_id"
            " JOIN projects p ON p.id = t.project_id"
            " LEFT JOIN milestones m ON m.id = t.milestone_id" + where_clause + " ORDER BY at"
        ),
        base_params,
    ).fetchall()
    return {
        "labels": [c["at"] for c in changes],
        "agents": [c["agent"] for c in changes],
        "skills": [c["skill"] for c in changes],
        "scores": [c["after"] for c in changes],
    }


@router.get("/agents", response_class=HTMLResponse)
def agents_page(
    request: Request,
    conn: Db,
    project: Project,
    milestone: str | None = None,
) -> HTMLResponse:
    eff = efficiency(conn, project, milestone)
    agent_names, roles, counts = agents_roles(conn, project, milestone)
    ratings = rating_data(conn, project, milestone)
    return render(
        request,
        conn,
        project,
        "agents.html",
        {
            "active": "/agents",
            "efficiency": eff,
            "agent_names": agent_names,
            "roles": roles,
            "counts": counts,
            "ratings": ratings,
            "eligible": eligibility_rows(conn, project),
            "milestone": milestone,
        },
    )
