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
OTHER_LOCAL = "local-other"
OPUS, SONNET = "claude-opus", "claude-sonnet"
# Each Claude job in f1: 10k input + 100k cache reads (0.1) + 2k output (5) = 30k equivalents.
CLAUDE_TOKENS: dict[str, int | float | None] = {
    "tokens_in": 10_000,
    "tokens_cached": 100_000,
    "tokens_out": 2_000,
}


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


def write_between_jobs(
    conn: sqlite3.Connection,
    *,
    activity: str | None = None,
    waiting_until: str | None = None,
    reserve: bool = False,
) -> int:
    """On top of ``write_fixture``, at ``NOW``: a live run with no running job, no queue and
    no owner item, doing ``activity``, optionally waiting until a time, optionally on Claude's
    reserve. Returns the run's id."""
    project = metrics.upsert_project(conn, PROJECT)
    run = metrics.upsert_run(
        conn,
        project,
        "20261002-115000",
        command="check-all",
        started=_at(timedelta(minutes=10)),
        heartbeat=_at(timedelta(seconds=10)),
    )
    metrics.update_run_activity(conn, run, activity, waiting_until)
    if reserve:
        metrics.set_run_reserve(conn, run)
    return run


@pytest.fixture
def serve_between(db_path: Path) -> Callable[..., TestClient]:
    """A client over the fixture plus ``write_between_jobs``'s rows (its keyword arguments)."""
    from factory_dashboard.app import create_app, get_now

    def make(**kwargs: Any) -> TestClient:
        conn = metrics.open_db(db_path)
        try:
            write_between_jobs(conn, **kwargs)
        finally:
            conn.close()
        app = create_app(db_path, PROJECT)
        app.dependency_overrides[get_now] = lambda: NOW
        return TestClient(app, base_url="http://127.0.0.1:8765")

    return make


def write_milestone_detail(conn: sqlite3.Connection) -> None:
    """On top of ``write_fixture``: F1 with a sign-off (outcome, done_when,
    signoff sections) for the milestone detail page tests."""
    project = metrics.upsert_project(conn, PROJECT)
    metrics.upsert_milestone(
        conn,
        project,
        "f1",
        status="done",
        outcome="The factory now measures itself end-to-end.",
        done_when=(
            "- All tickets in `tasks/done/`, `check-all` passes on `main`,\n"
            "- `backfill` run twice gives identical row counts."
        ),
        signoff={
            "changed": "- A metrics database that every run writes.\n"
            "- The local dashboard at `127.0.0.1`.",
            "how_to_test": "- Run `uv run runner milestone f1`.\n"
            "- Open `127.0.0.1` and check every page.",
            "what_next": "- Close the factory review.\n- Replan the agents section.",
            "later": "- Full diffs and before/after screenshots.\n- ADRs view on the dashboard.",
            "lessons": "- Run the loop before the replan.",
            "decisions": "- ADR 16, waiting for the owner.",
            "clogged": "- 11 h waiting for Claude's 5-hour window.",
        },
    )
    metrics.upsert_milestone(
        conn,
        project,
        "f10",
        title="F10 milestone",
        status="in progress",
        started=_at(timedelta(days=2)),
    )
    metrics.upsert_milestone(
        conn,
        project,
        "f2",
        title="The factory reviews itself",
        status="in progress",
        started=_at(timedelta(days=1)),
    )


def reset_milestone_scores(conn: sqlite3.Connection, milestone_id: int) -> None:
    """Reset review_score and owner_score to NULL for a milestone."""
    cur = conn.execute(
        "UPDATE milestones SET review_score = NULL, owner_score = NULL WHERE id = ?",
        (milestone_id,),
    )
    cur.close()
    conn.commit()


def write_milestone_with_scores(
    conn: sqlite3.Connection,
    milestone_id: int,
    review_score: float,
    owner_score: float,
) -> None:
    """Set review_score and owner_score on an existing milestone."""
    conn.execute(
        "UPDATE milestones SET review_score = ?, owner_score = ? WHERE id = ?",
        (review_score, owner_score, milestone_id),
    )
    conn.commit()


def write_milestone_detail_with_scores(conn: sqlite3.Connection) -> None:
    """On top of ``write_fixture``: F1 with sign-off and scores, F10 without scores."""
    project = metrics.upsert_project(conn, PROJECT)
    metrics.upsert_milestone(
        conn,
        project,
        "f1",
        status="done",
        review_score=7,
        owner_score=8.5,
        outcome="The factory now measures itself end-to-end.",
        done_when=(
            "- All tickets in `tasks/done/`, `check-all` passes on `main`,\n"
            "- `backfill` run twice gives identical row counts."
        ),
        signoff={
            "changed": "- A metrics database that every run writes.\n"
            "- The local dashboard at `127.0.0.1`.",
            "how_to_test": "- Run `uv run runner milestone f1`.\n"
            "- Open `127.0.0.1` and check every page.",
            "what_next": "- Close the factory review.\n- Replan the agents section.",
            "later": "- Full diffs and before/after screenshots.\n- ADRs view on the dashboard.",
            "lessons": "- Run the loop before the replan.",
            "decisions": "- ADR 16, waiting for the owner.",
            "clogged": "- 11 h waiting for Claude's 5-hour window.",
        },
    )
    metrics.upsert_milestone(
        conn,
        project,
        "f10",
        title="F10 milestone",
        status="in progress",
        started=_at(timedelta(days=2)),
    )


def write_milestones(conn: sqlite3.Connection) -> None:
    """On top of ``write_fixture``: a milestone with no tickets yet (f2),
    F1 with a status, and F10 (earlier than F2) for ordering tests."""
    project = metrics.upsert_project(conn, PROJECT)
    metrics.upsert_milestone(
        conn,
        project,
        "f1",
        status="done",
    )
    metrics.upsert_milestone(
        conn,
        project,
        "f10",
        title="F10 milestone",
        status="in progress",
        started=_at(timedelta(days=2)),
    )
    metrics.upsert_milestone(
        conn,
        project,
        "f2",
        title="The factory reviews itself",
        status="in progress",
        started=_at(timedelta(days=1)),
    )


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


def write_runs(conn: sqlite3.Connection) -> None:
    """Runs for the runs page tests: a running run, a completed run, and a stopped run."""
    project = metrics.upsert_project(conn, PROJECT)
    f1 = metrics.upsert_milestone(conn, project, "f1")

    # Running run (fresh heartbeat)
    running_run = metrics.upsert_run(
        conn,
        project,
        "20261002-113500",
        command="milestone f1",
        started=_at(timedelta(minutes=25)),
        heartbeat=_at(timedelta(seconds=30)),
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
    metrics.start_job(
        conn,
        running_run,
        ticket_id=live,
        milestone_id=f1,
        role="developer",
        agent=LOCAL,
        attempt=2,
        started=_at(timedelta(minutes=12)),
    )

    # Completed run
    completed_run = metrics.upsert_run(
        conn,
        project,
        "20260930-100000",
        command="milestone f1",
        started="2026-09-30T10:00:00+02:00",
        ended=_at(timedelta(hours=1)),
        verdict="3 merged, 0 not",
    )
    for tid, role in [
        ("f1-01-first", "developer"),
        ("f1-02-escalated", "direction"),
        ("f1-03-lead", "lead-ticket"),
    ]:
        t = metrics.upsert_ticket(
            conn, project, tid, milestone_id=f1, kind="developer", state="done", difficulty=4
        )
        metrics.start_job(
            conn,
            completed_run,
            ticket_id=t,
            milestone_id=f1,
            role=role,
            agent=OPUS,
            attempt=1,
            started="2026-09-30T10:00:00+02:00",
        )

    # Stopped run (old heartbeat)
    metrics.upsert_run(
        conn,
        project,
        "20260920-100000",
        command="backfill",
        heartbeat=_at(timedelta(minutes=3)),
    )


def write_m1_jobs(conn: sqlite3.Connection) -> int:
    """An m1 milestone in the coucou project with a job, for the timeline milestone filter test."""
    project = metrics.upsert_project(conn, PROJECT)
    m1 = metrics.upsert_milestone(
        conn, project, "m1", title="Milestone one", started=_at(timedelta(days=10))
    )
    m1_run = metrics.upsert_run(conn, project, "20260922-100000")
    ticket = metrics.upsert_ticket(
        conn, project, "m1-01-test", milestone_id=m1, kind="developer", state="done"
    )
    job = metrics.start_job(
        conn,
        m1_run,
        ticket_id=ticket,
        milestone_id=m1,
        role="developer",
        agent=LOCAL,
        attempt=1,
        started="2026-09-22T10:00:00+02:00",
    )
    metrics.finish_job(
        conn,
        job,
        ended="2026-09-22T10:05:00+02:00",
        outcome="passed",
        tokens_in=10_000,
        tokens_out=1_000,
    )
    return m1


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


def write_tickets(conn: sqlite3.Connection) -> None:
    """On top of ``write_fixture``: tickets for the ticket pages.

    - ``f1-10-ticket-a`` (developer, d3, done) in f1.
    - ``f1-11-ticket-b`` (developer, d4, done) in f1 with depends_on=[f1-10-ticket-a],
      escalated then merged, with 3 jobs (2 failed + 1 passed escalation).
    - ``f1-12-escalated`` (lead, d5, escalated) in f1 for state filtering.
    - ``m4-02-ticket-c`` (developer, d2, done) in m4 for cross-milestone ordering.
    - Findings on m4 milestone for ticket-c.
    """
    project = metrics.upsert_project(conn, PROJECT)
    f1 = metrics.upsert_milestone(conn, project, "f1")
    m4 = metrics.upsert_milestone(conn, project, "m4")
    run = metrics.upsert_run(conn, project, "20260930-100000")
    old_run = metrics.upsert_run(conn, project, "20260920-100000")

    ticket_a = metrics.upsert_ticket(
        conn,
        project,
        "f1-10-ticket-a",
        milestone_id=f1,
        kind="developer",
        state="done",
        difficulty=3,
        merged_by=LOCAL,
        commit="e" * 40,
        lines_changed=30,
        body="Goal: A ticket.\n\nDone when: it passes.",
        depends_on=[],
        files=["a.py"],
    )
    _job(
        conn, run, f1, ticket_a, "developer", LOCAL, 1, "passed", tokens_in=10_000, tokens_out=1_000
    )

    ticket_b = metrics.upsert_ticket(
        conn,
        project,
        "f1-11-ticket-b",
        milestone_id=f1,
        kind="developer",
        state="done",
        difficulty=4,
        merged_by=OPUS,
        commit="f" * 40,
        lines_changed=50,
        body="Goal: B ticket.\n\nDone when: it works.",
        depends_on=["f1-10-ticket-a"],
        files=["b.py", "c.py"],
    )
    _local(conn, run, f1, ticket_b, "developer", 1, ok=False)
    _local(conn, run, f1, ticket_b, "developer", 2, ok=False)
    _job(conn, run, f1, ticket_b, "escalation", OPUS, 3, "passed", cost_usd=2.0, **CLAUDE_TOKENS)

    metrics.upsert_ticket(
        conn,
        project,
        "f1-12-escalated",
        milestone_id=f1,
        kind="lead",
        state="escalated",
        difficulty=5,
    )

    ticket_c = metrics.upsert_ticket(
        conn,
        project,
        "m4-02-ticket-c",
        milestone_id=m4,
        kind="developer",
        state="done",
        difficulty=2,
        merged_by=LOCAL,
        commit="g" * 40,
        lines_changed=20,
    )
    _job(
        conn,
        old_run,
        m4,
        ticket_c,
        "developer",
        LOCAL,
        1,
        "passed",
        tokens_in=5_000,
        tokens_out=500,
    )
    metrics.add_finding(
        conn, m4, "M4-F1", ticket_id=ticket_c, severity="blocking", summary="Blocking issue"
    )
    metrics.add_finding(conn, m4, "M4-F2", ticket_id=ticket_c, severity="nit", summary="Nitpick")
    metrics.add_finding(
        conn, m4, "MILESTONE-WIDE", severity="should-fix", summary="milestone-wide finding"
    )

    # Ticket-specific finding on ticket_b, for f1-36 testing
    if ticket_b:
        metrics.add_finding(
            conn,
            f1,
            "TICKET-F1",
            ticket_id=ticket_b,
            severity="should-fix",
            summary="ticket specific",
        )

    # Live queue tickets (from write_live) so the list has all 9 f1 tickets.
    for ticket, goal in (("f1-06-second", "Queued second."), ("f1-05-first", "Queued first.")):
        metrics.upsert_ticket(
            conn, project, ticket, milestone_id=f1, kind="developer", state="ready", title=goal
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
    live_run = metrics.upsert_run(
        conn,
        project,
        "20261002-113500",
        command="milestone f1",
        started=_at(timedelta(minutes=25)),
        heartbeat=_at(timedelta(seconds=30)),
    )
    job = metrics.start_job(
        conn,
        live_run,
        ticket_id=live,
        milestone_id=f1,
        role="developer",
        agent=LOCAL,
        attempt=2,
        started=_at(timedelta(minutes=12)),
    )
    metrics.update_running_job(conn, job, tokens_in=42_000, steps=17)


def write_f1_run(conn: sqlite3.Connection) -> None:
    """A second run with F1 jobs, for the timeline run filter test."""
    project = metrics.upsert_project(conn, PROJECT)
    f1 = metrics.upsert_milestone(conn, project, "f1")
    new_run = metrics.upsert_run(conn, project, "20261001-100000", command="milestone f1")
    ticket = metrics.upsert_ticket(
        conn, project, "f1-07-test", milestone_id=f1, kind="developer", state="done"
    )
    job1 = metrics.start_job(
        conn,
        new_run,
        ticket_id=ticket,
        milestone_id=f1,
        role="developer",
        agent=LOCAL,
        attempt=1,
        started="2026-10-01T10:00:00+02:00",
    )
    metrics.finish_job(
        conn,
        job1,
        ended="2026-10-01T10:05:00+02:00",
        outcome="failed",
        tokens_in=10_000,
        tokens_out=1_000,
    )
    job2 = metrics.start_job(
        conn,
        new_run,
        ticket_id=ticket,
        milestone_id=f1,
        role="escalation",
        agent=OPUS,
        attempt=1,
        started="2026-10-01T10:06:00+02:00",
    )
    metrics.finish_job(
        conn,
        job2,
        ended="2026-10-01T10:11:00+02:00",
        outcome="passed",
        cost_usd=1.0,
        tokens_in=10_000,
        tokens_cached=100_000,
        tokens_out=2_000,
    )


def write_run_no_jobs_in_milestone(conn: sqlite3.Connection) -> None:
    """A run with jobs in a different milestone (m1), for the timeline run filter test."""
    project = metrics.upsert_project(conn, PROJECT)
    m1 = metrics.upsert_milestone(
        conn, project, "m1", title="Milestone one", started=_at(timedelta(days=10))
    )
    run = metrics.upsert_run(conn, project, "20260922-100000", command="milestone m1")
    ticket = metrics.upsert_ticket(
        conn, project, "m1-01-test", milestone_id=m1, kind="developer", state="done"
    )
    job = metrics.start_job(
        conn,
        run,
        ticket_id=ticket,
        milestone_id=m1,
        role="developer",
        agent=LOCAL,
        attempt=1,
        started="2026-09-22T10:00:00+02:00",
    )
    metrics.finish_job(
        conn,
        job,
        ended="2026-09-22T10:05:00+02:00",
        outcome="passed",
        tokens_in=10_000,
        tokens_out=1_000,
    )


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


def write_bench(conn: sqlite3.Connection) -> None:
    """On top of ``write_fixture``, bench jobs on ``f1-01-first`` (d4) and ``f1-02-escalated``
    (d5), by ``LOCAL`` and ``OTHER_LOCAL``:
    - f1-01 by LOCAL: failed, then passed (attempt 2), 20 min, 300k tokens;
    - f1-01 by OTHER_LOCAL: refused;
    - f1-02 by LOCAL: failed, then would escalate;
    - f1-02 by OTHER_LOCAL: not benched (an empty cell)."""
    project = metrics.upsert_project(conn, PROJECT)
    f1 = metrics.upsert_milestone(conn, project, "f1")
    run = metrics.upsert_run(conn, project, "bench-20261001-100000", command="bench")
    first = metrics.upsert_ticket(conn, project, "f1-01-first", milestone_id=f1)
    escalated = metrics.upsert_ticket(conn, project, "f1-02-escalated", milestone_id=f1)
    for ticket, agent, n, outcome, note in (
        (first, LOCAL, 1, "failed", None),
        (first, LOCAL, 2, "passed", None),
        (first, OTHER_LOCAL, 3, "refused", "it resets Fri 3 Oct 10:00"),
        (escalated, LOCAL, 4, "failed", None),
        (escalated, LOCAL, 5, "failed", "would escalate"),
    ):
        job = metrics.start_job(
            conn,
            run,
            ticket_id=ticket,
            milestone_id=f1,
            role="bench",
            agent=agent,
            attempt=n,
            started="2026-10-01T10:00:00+02:00",
        )
        metrics.finish_job(
            conn,
            job,
            ended="2026-10-01T10:10:00+02:00",
            outcome=outcome,
            note=note,
            tokens_in=100_000,
            tokens_out=50_000,
        )


@pytest.fixture
def bench_client(db_path: Path) -> TestClient:
    """A client over the fixture plus ``write_bench``'s rows."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        write_bench(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


SHADOW, OTHER_SHADOW = "copilot-auto", "copilot-gpt"


def write_shadows(conn: sqlite3.Connection) -> None:
    """On top of ``write_fixture``, checkpoint shadows: ``OTHER_SHADOW`` shadowed f1 and m4 and
    is rated 8.5 (eligible, 2 jobs); ``SHADOW`` shadowed f1 only and is rated 6 (not eligible,
    1 job)."""
    project = metrics.upsert_project(conn, PROJECT)
    run = metrics.upsert_run(conn, project, "shadow-20260930-100000")
    shadows = ((OTHER_SHADOW, "f1"), (OTHER_SHADOW, "m4"), (SHADOW, "f1"))
    for attempt, (agent, milestone) in enumerate(shadows, start=1):
        _job(
            conn,
            run,
            metrics.upsert_milestone(conn, project, milestone),
            None,
            "checkpoint-shadow",
            agent,
            attempt,
            "passed",
        )
    metrics.add_rating_change(
        conn, OTHER_SHADOW, "reviewing", 6, 8.5, at="2026-09-30T11:00:00+02:00"
    )
    metrics.add_rating_change(conn, SHADOW, "reviewing", 5, 6, at="2026-09-30T11:00:00+02:00")


@pytest.fixture
def shadow_client(db_path: Path) -> TestClient:
    """A client over the fixture plus ``write_shadows``'s rows."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        write_shadows(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


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
def milestone_detail_with_scores_client(db_path: Path) -> TestClient:
    """A client over the fixture plus ``write_milestone_detail_with_scores``'s rows."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        write_milestone_detail_with_scores(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


@pytest.fixture
def timeline_run_no_jobs_client(db_path: Path) -> TestClient:
    """Timeline client: fixture + write_live + write_f1_run + a run with jobs in m1."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        write_live(conn, timedelta(seconds=30))
        write_f1_run(conn)
        write_run_no_jobs_in_milestone(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


def write_ratings(conn: sqlite3.Connection) -> None:
    """Two rating changes for the local agent, for the agents page chart test."""
    project = metrics.upsert_project(conn, PROJECT)
    f1 = metrics.upsert_milestone(conn, project, "f1")
    ticket = metrics.upsert_ticket(
        conn, project, "f1-01-first", milestone_id=f1, kind="developer", state="done"
    )
    metrics.add_rating_change(
        conn, LOCAL, "coding", 4.0, 4.5, at="2026-09-30T11:00:00+02:00", ticket_id=ticket
    )
    metrics.add_rating_change(
        conn, LOCAL, "reviewing", 3.5, 4.0, at="2026-09-30T12:00:00+02:00", ticket_id=ticket
    )


@pytest.fixture
def rating_client(db_path: Path) -> TestClient:
    """A client over the fixture plus two rating changes."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        write_ratings(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


def write_project(conn: sqlite3.Connection) -> None:
    """On top of ``write_fixture``: a project with description and repo, milestones, and runs."""
    metrics.upsert_project(
        conn,
        PROJECT,
        repo="https://github.com/example/coucou",
        description="A factory dashboard that measures itself.",
    )
    metrics.upsert_milestone(
        conn,
        metrics.upsert_project(conn, PROJECT),
        "f1",
        title="The factory measures itself",
        status="done",
        started=_at(timedelta(days=2)),
    )
    metrics.upsert_milestone(
        conn,
        metrics.upsert_project(conn, PROJECT),
        "f2",
        title="The factory reviews itself",
        status="in progress",
        started=_at(timedelta(days=1)),
    )
    # In-progress milestone newer than the done one (for ordering tests).
    metrics.upsert_milestone(
        conn,
        metrics.upsert_project(conn, PROJECT),
        "f3",
        title="The factory ships itself",
        status="in progress",
        started=_at(timedelta(hours=12)),
    )
    metrics.upsert_run(
        conn,
        metrics.upsert_project(conn, PROJECT),
        "20261001-100000",
        command="milestone f1",
        ended=_at(timedelta(hours=1)),
    )
    metrics.upsert_run(
        conn,
        metrics.upsert_project(conn, PROJECT),
        "20260930-100000",
        command="milestone f1",
        ended=_at(timedelta(days=1)),
    )


@pytest.fixture
def project_client(db_path: Path) -> TestClient:
    """A client over the fixture plus ``write_project``'s rows."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        write_project(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


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


@pytest.fixture
def milestones_client(db_path: Path) -> TestClient:
    """A client for the dashboard over the fixture with ``write_milestones``'s rows."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        write_milestones(conn)
    finally:
        conn.close()
    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


@pytest.fixture
def tickets_client(db_path: Path) -> TestClient:
    """A client over the fixture plus ``write_tickets``'s rows."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        write_tickets(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


@pytest.fixture
def milestone_detail_client(db_path: Path) -> TestClient:
    """A client over the fixture plus ``write_milestone_detail``'s rows."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        write_milestone_detail(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")
