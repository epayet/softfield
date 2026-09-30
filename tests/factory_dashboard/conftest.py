"""A small metrics database, written with ``runner.metrics`` as the runner writes it.

F1 has three merged tickets:
- ``f1-01-first`` (developer, d4, 100 lines): the local model passed at the first attempt;
- ``f1-02-escalated`` (developer, d5, 50 lines): three local attempts failed (a direction
  before the last), then an escalation fixed and merged it ($1 + $2);
- ``f1-03-lead`` (lead, d4, 200 lines): a lead ticket ($3).
Milestone-wide: a review ($1.50) and a checkpoint on Sonnet ($0.30); four findings.

M4, earlier, has one ticket the local model merged (d2, 80 lines) and a review whose cost
wasn't kept: 500k input tokens.

``write_live`` adds what the Overview shows live, at ``NOW``; the ``client`` fixture serves both.
"""

import sqlite3
from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from runner import metrics

PROJECT, OTHER = "coucou", "other"
NOW = datetime(2026, 10, 2, 12, 0, tzinfo=UTC)
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


def _at(ago: timedelta) -> str:
    return (NOW - ago).isoformat()


def write_live(conn: sqlite3.Connection, heartbeat_age: timedelta) -> None:
    """On top of ``write_fixture``, at ``NOW``:
    - a run whose heartbeat is ``heartbeat_age`` old, with a local attempt at ``f1-04-live``
      running for 12 min (42k tokens in, 17 steps so far);
    - two tickets queued in f1, an open owner item and a resolved one;
    - the last verdicts: f1's run ended "3 merged, 0 not", and f1 is ready for sign-off;
    - the Claude allowance: a refusal after f1's jobs (the 650k token-equivalents of every
      Claude job in the 5 h before it), and 30k used an hour ago, in another project;
    - another project with one queued ticket.
    """
    project = metrics.upsert_project(conn, PROJECT)
    f1 = metrics.upsert_milestone(conn, project, "f1", verdict="ready")
    metrics.upsert_run(
        conn,
        project,
        "20260930-100000",
        ended="2026-09-30T12:00:00+02:00",
        verdict="3 merged, 0 not",
    )
    run = metrics.upsert_run(
        conn,
        project,
        "20261002-113500",
        command="milestone f1",
        started=_at(timedelta(minutes=25)),
        heartbeat=_at(heartbeat_age),
    )
    live = metrics.upsert_ticket(
        conn,
        project,
        "f1-04-live",
        milestone_id=f1,
        kind="developer",
        state="running",
        difficulty=5,
    )
    job = metrics.start_job(
        conn,
        run,
        ticket_id=live,
        milestone_id=f1,
        role="developer",
        agent=LOCAL,
        attempt=2,
        started=_at(timedelta(minutes=12)),
    )
    metrics.update_running_job(conn, job, tokens_in=42_000, steps=17)
    for ticket, goal in (("f1-06-second", "Queued second."), ("f1-05-first", "Queued first.")):
        metrics.upsert_ticket(
            conn, project, ticket, milestone_id=f1, kind="developer", state="ready", title=goal
        )
    metrics.upsert_owner_item(
        conn,
        project,
        "adr",
        "ADR 15",
        text="Should reactions be editable once sent?",
        command="uv run runner accept 15",
        created=_at(timedelta(hours=1)),
    )
    done = metrics.upsert_owner_item(conn, project, "setup", "ollama", text="Sign in to Ollama.")
    metrics.resolve_owner_item(conn, done, _at(timedelta(hours=2)))
    metrics.add_usage_event(conn, OPUS, "2026-09-30T10:30:00+02:00", "refusal")

    other = metrics.upsert_project(conn, OTHER)
    m1 = metrics.upsert_milestone(conn, other, "m1", started=_at(timedelta(days=1)))
    metrics.upsert_ticket(
        conn, other, "m1-01-elsewhere", milestone_id=m1, kind="developer", state="ready"
    )
    other_run = metrics.upsert_run(conn, other, "20261002-100000", ended=_at(timedelta(hours=1)))
    claude = metrics.start_job(
        conn,
        other_run,
        ticket_id=None,
        milestone_id=m1,
        role="review",
        agent=OPUS,
        attempt=1,
        started=_at(timedelta(hours=1)),
    )
    tokens: dict[str, Any] = CLAUDE_TOKENS
    metrics.finish_job(conn, claude, ended=_at(timedelta(minutes=50)), outcome="passed", **tokens)


def write_jobs(conn: sqlite3.Connection) -> None:
    """Jobs with gates, for the jobs page. Not in write_fixture so the overview tests stay
    pinned."""
    project = metrics.upsert_project(conn, PROJECT)
    f1 = metrics.upsert_milestone(conn, project, "f1")
    f1_run = metrics.upsert_run(conn, project, "20260930-100000")
    m4 = metrics.upsert_milestone(conn, project, "m4")
    m4_run = metrics.upsert_run(conn, project, "20260920-100000")

    # A job that passed with gates (all ok)
    t = metrics.upsert_ticket(conn, project, "f1-01-first", milestone_id=f1)
    job = metrics.start_job(
        conn,
        f1_run,
        ticket_id=t,
        milestone_id=f1,
        role="developer",
        agent=LOCAL,
        attempt=1,
        started="2026-09-30T10:00:00+02:00",
    )
    metrics.finish_job(
        conn,
        job,
        ended="2026-09-30T10:10:00+02:00",
        outcome="passed",
        tokens_in=200_000,
        tokens_out=10_000,
        gates=[
            {"name": "lint", "ok": True, "seconds": 2.0, "log": "ok"},
            {"name": "tests", "ok": True, "seconds": 30.0, "log": "ok"},
        ],
    )

    # A job that failed at a gate
    escalated = metrics.upsert_ticket(conn, project, "f1-02-escalated", milestone_id=f1)
    job = metrics.start_job(
        conn,
        f1_run,
        ticket_id=escalated,
        milestone_id=f1,
        role="direction",
        agent=OPUS,
        attempt=1,
        started="2026-09-30T10:05:00+02:00",
    )
    metrics.finish_job(
        conn,
        job,
        ended="2026-09-30T10:12:00+02:00",
        outcome="failed",
        cost_usd=1.0,
        peak_context=166_000,
        context_limit=184_000,
        note="Escalation note",
        gates=[
            {"name": "lint", "ok": True, "seconds": 2.0, "log": "ok"},
            {"name": "tests", "ok": False, "seconds": 30.0, "log": "FAIL"},
        ],
    )

    # A running job (no gates)
    live = metrics.upsert_ticket(conn, project, "f1-04-live", milestone_id=f1)
    metrics.start_job(
        conn,
        f1_run,
        ticket_id=live,
        milestone_id=f1,
        role="developer",
        agent=LOCAL,
        attempt=2,
        started=_at(timedelta(minutes=12)),
    )

    # Old m4 job with gates
    old = metrics.upsert_ticket(conn, project, "m4-01-old", milestone_id=m4)
    job = metrics.start_job(
        conn,
        m4_run,
        ticket_id=old,
        milestone_id=m4,
        role="developer",
        agent=LOCAL,
        attempt=1,
        started="2026-09-20T09:00:00+02:00",
    )
    metrics.finish_job(
        conn,
        job,
        ended="2026-09-20T09:05:00+02:00",
        outcome="passed",
        tokens_in=50_000,
        tokens_out=0,
        gates=[{"name": "lint", "ok": True, "seconds": 1.0, "log": "ok"}],
    )

    # A Claude escalation job with note
    esc = metrics.upsert_ticket(conn, project, "f1-02-escalated", milestone_id=f1)
    esc_job = metrics.start_job(
        conn,
        f1_run,
        ticket_id=esc,
        milestone_id=f1,
        role="escalation",
        agent=OPUS,
        attempt=1,
        started="2026-09-30T10:15:00+02:00",
    )
    metrics.finish_job(
        conn,
        esc_job,
        ended="2026-09-30T10:20:00+02:00",
        outcome="passed",
        cost_usd=1.0,
        note="Escalation note",
        tokens_in=10_000,
        tokens_cached=100_000,
        tokens_out=2_000,
    )


def write_review_job(conn: sqlite3.Connection) -> int:
    """A review job with findings, for the job detail page tests."""
    project = metrics.upsert_project(conn, PROJECT)
    f1 = metrics.upsert_milestone(conn, project, "f1")
    f1_run = metrics.upsert_run(conn, project, "20260930-110000")

    review = metrics.start_job(
        conn,
        f1_run,
        ticket_id=None,
        milestone_id=f1,
        role="review",
        agent=OPUS,
        attempt=1,
        started="2026-09-30T11:00:00+02:00",
    )
    metrics.finish_job(
        conn,
        review,
        ended="2026-09-30T11:15:00+02:00",
        outcome="passed",
        cost_usd=1.50,
        tokens_in=10_000,
        tokens_cached=100_000,
        tokens_out=2_000,
    )
    metrics.add_finding(
        conn, f1, "RV-1", job_id=review, severity="blocking", summary="Missing input validation"
    )
    metrics.add_finding(
        conn,
        f1,
        "RV-2",
        job_id=review,
        severity="should-fix",
        summary="Edge case in error handling",
    )
    return review


def write_more_jobs(conn: sqlite3.Connection, count: int) -> int:
    """Add ``count`` more finished jobs for the overflow test. Returns the last job id."""
    project = metrics.upsert_project(conn, PROJECT)
    f1 = metrics.upsert_milestone(conn, project, "f1")
    run = metrics.upsert_run(conn, project, "20260930-100000")
    last = 0
    for i in range(count):
        ticket = metrics.upsert_ticket(
            conn,
            project,
            f"f1-overflow-{i:04d}",
            milestone_id=f1,
            kind="developer",
            state="done",
            difficulty=3,
        )
        job = metrics.start_job(
            conn,
            run,
            ticket_id=ticket,
            milestone_id=f1,
            role="developer",
            agent=LOCAL,
            attempt=1,
            started="2026-09-30T11:00:00+02:00",
        )
        metrics.finish_job(
            conn,
            job,
            ended="2026-09-30T11:01:00+02:00",
            outcome="passed",
            tokens_in=10_000,
            tokens_out=1_000,
        )
        last = job
    return last


@pytest.fixture
def serve(db_path: Path) -> Callable[..., TestClient]:
    """A client for the dashboard over the fixture, with ``write_live``'s rows unless
    ``live=False``; the app's clock reads ``NOW``."""
    from factory_dashboard.app import create_app, get_now

    def make(*, live: bool = True, heartbeat_age: timedelta = timedelta(seconds=30)) -> TestClient:
        if live:
            conn = metrics.open_db(db_path)
            try:
                write_live(conn, heartbeat_age)
            finally:
                conn.close()
        app = create_app(db_path, PROJECT)
        app.dependency_overrides[get_now] = lambda: NOW
        return TestClient(app, base_url="http://127.0.0.1:8765")

    return make


@pytest.fixture
def client(serve: Callable[..., TestClient]) -> TestClient:
    return serve()


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
