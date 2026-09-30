"""A small metrics database, written with ``runner.metrics`` as the runner writes it.

F1 has three merged tickets:
- ``f1-01-first`` (developer, d4, 100 lines): the local model passed at the first attempt;
- ``f1-02-escalated`` (developer, d5, 50 lines): three local attempts failed (a direction
  before the last), then an escalation fixed and merged it ($1 + $2);
- ``f1-03-lead`` (lead, d4, 200 lines): a lead ticket ($3).
Milestone-wide: a review ($1.50) and a checkpoint on Sonnet ($0.30); four findings.

M4, earlier, has one ticket the local model merged (d2, 80 lines) and a review whose cost
wasn't kept: 500k input tokens.
"""

import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from runner import metrics

PROJECT = "coucou"
LOCAL = "local-qwen3.6-35b-a3b"
OPUS, SONNET = "claude-opus", "claude-sonnet"
# Each Claude job in f1: 10k input + 100k cache reads (0.1) + 2k output (5) = 30k equivalents.
CLAUDE_TOKENS = {"tokens_in": 10_000, "tokens_cached": 100_000, "tokens_out": 2_000}


def _job(
    conn: sqlite3.Connection,
    run_id: int,
    milestone_id: int,
    ticket_id: int | None,
    role: str,
    agent: str,
    attempt: int,
    outcome: str,
    **finish: Any,
) -> int:
    job_id = metrics.start_job(
        conn,
        run_id,
        ticket_id=ticket_id,
        milestone_id=milestone_id,
        role=role,
        agent=agent,
        attempt=attempt,
        started="2026-09-30T10:00:00+02:00",
    )
    metrics.finish_job(
        conn,
        job_id,
        ended="2026-09-30T10:10:00+02:00",
        outcome=outcome,
        **finish,
    )
    return job_id


def _local(conn: sqlite3.Connection, run: int, m: int, t: int, role: str, n: int, ok: bool) -> None:
    outcome = "passed" if ok else "failed"
    _job(conn, run, m, t, role, LOCAL, n, outcome, tokens_in=100_000, tokens_out=5_000)


def write_fixture(conn: sqlite3.Connection) -> None:
    project = metrics.upsert_project(conn, PROJECT)
    m4 = metrics.upsert_milestone(
        conn, project, "m4", title="The web app", started="2026-09-20T09:00:00+02:00"
    )
    f1 = metrics.upsert_milestone(
        conn,
        project,
        "f1",
        title="The factory measures itself",
        started="2026-09-30T09:00:00+02:00",
        review_rounds=1,
    )
    run = metrics.upsert_run(conn, project, "20260930-100000", command="milestone f1")
    old_run = metrics.upsert_run(conn, project, "20260920-100000", command="backfill")

    first = metrics.upsert_ticket(
        conn,
        project,
        "f1-01-first",
        milestone_id=f1,
        kind="developer",
        state="done",
        difficulty=4,
        merged_by=LOCAL,
        commit="a" * 40,
        lines_changed=100,
    )
    _job(
        conn, run, f1, first, "developer", LOCAL, 1, "passed", tokens_in=200_000, tokens_out=10_000
    )

    escalated = metrics.upsert_ticket(
        conn,
        project,
        "f1-02-escalated",
        milestone_id=f1,
        kind="developer",
        state="done",
        difficulty=5,
        merged_by=OPUS,
        commit="b" * 40,
        lines_changed=50,
    )
    _local(conn, run, f1, escalated, "developer", 1, ok=False)
    _local(conn, run, f1, escalated, "developer", 2, ok=False)
    _job(conn, run, f1, escalated, "direction", OPUS, 1, "passed", cost_usd=1.0, **CLAUDE_TOKENS)
    _local(conn, run, f1, escalated, "last-attempt", 3, ok=False)
    _job(conn, run, f1, escalated, "escalation", OPUS, 1, "passed", cost_usd=2.0, **CLAUDE_TOKENS)

    lead = metrics.upsert_ticket(
        conn,
        project,
        "f1-03-lead",
        milestone_id=f1,
        kind="lead",
        state="done",
        difficulty=4,
        merged_by=OPUS,
        commit="c" * 40,
        lines_changed=200,
    )
    _job(conn, run, f1, lead, "lead-ticket", OPUS, 1, "passed", cost_usd=3.0, **CLAUDE_TOKENS)

    review = _job(conn, run, f1, None, "review", OPUS, 1, "passed", cost_usd=1.5, **CLAUDE_TOKENS)
    _job(conn, run, f1, None, "checkpoint", SONNET, 1, "passed", cost_usd=0.3, **CLAUDE_TOKENS)
    for n, severity in enumerate(("blocking", "should-fix", "should-fix", "nit"), start=1):
        metrics.add_finding(conn, f1, f"f1-F{n}", job_id=review, severity=severity)

    old = metrics.upsert_ticket(
        conn,
        project,
        "m4-01-old",
        milestone_id=m4,
        kind="developer",
        state="done",
        difficulty=2,
        merged_by=LOCAL,
        commit="d" * 40,
        lines_changed=80,
    )
    _job(conn, old_run, m4, old, "developer", LOCAL, 1, "passed", tokens_in=50_000, tokens_out=0)
    _job(conn, old_run, m4, None, "review", OPUS, 1, "passed", tokens_in=500_000)


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "factory-metrics.sqlite"
    conn = metrics.open_db(path)
    try:
        write_fixture(conn)
    finally:
        conn.close()
    return path


@pytest.fixture
def db(db_path: Path) -> Iterator[sqlite3.Connection]:
    from factory_dashboard.queries import connect

    conn = connect(db_path)
    try:
        yield conn
    finally:
        conn.close()
