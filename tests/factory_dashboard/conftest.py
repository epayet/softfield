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

import os
import sqlite3
import time
from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from factory_dashboard import queries
from runner import metrics

# A copy of a machine's ~/.config/softfield/factory.toml: the agents and roles (ADR 30 item 3)
MACHINE = Path(__file__).resolve().parents[1] / "fixtures" / "softfield-machine.toml"


@pytest.fixture(autouse=True)
def _machine_config(monkeypatch):
    """The dashboard reads a project's config over this fixed machine file, never the real one."""
    monkeypatch.setenv("SOFTFIELD_CONFIG", str(MACHINE))


def _set_zone(name: str | None) -> None:
    if name is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = name
    time.tzset()


@pytest.fixture(autouse=True)
def _utc_zone() -> Iterator[None]:
    """Pages print local time (F187), so these tests fix the zone: on a machine in the UK, the
    fixtures' dates before 25 Oct would read an hour later than the tests expect."""
    before = os.environ.get("TZ")
    _set_zone("UTC")
    yield
    _set_zone(before)


@pytest.fixture
def paris(_utc_zone: None) -> Iterator[None]:
    """The machine's zone is Paris, so local is not UTC and a slip shows (F187 D6)."""
    _set_zone("Europe/Paris")
    yield
    _set_zone("UTC")


@pytest.fixture
def london(_utc_zone: None) -> Iterator[None]:
    """The owner's machine in summer time: +01:00 at the fixture night's dates, which its
    "overnight" (20:00 local) is worked out from."""
    _set_zone("Europe/London")
    yield
    _set_zone("UTC")


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
    # Both reviewed (their sheets stored), so ripe once their tickets are done (F50 D1)
    m4 = metrics.upsert_milestone(
        conn,
        project,
        "m4",
        title="The web app",
        started="2026-09-20T09:00:00+02:00",
        signoff={"changed": "The web app."},
    )
    f1 = metrics.upsert_milestone(
        conn,
        project,
        "f1",
        title="The factory measures itself",
        started="2026-09-30T09:00:00+02:00",
        review_rounds=1,
        signoff={"changed": "The factory measures itself."},
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
        title="Running now.",
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
        command="softfield accept 15",
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


def write_queue(conn: sqlite3.Connection, waiting_claude: bool = False) -> None:
    """Tickets with various dependency states for queue tests.

    - ``f1-10-queued`` (ready, no deps, ready now)
    - ``f1-11-waits-done`` (ready, depends on f1-01-first which is done, ready now)
    - ``f1-12-waits-running`` (ready, depends on f1-04-live which is running, not done)
    - ``f1-13-waits-escalated`` (ready, depends on f1-12-escalated which is escalated)
    - ``f1-14-lead`` (lead, no deps, ready now unless waiting_claude)
    - ``f1-04-live`` (running, should NOT appear in queue)
    - ``f1-05-first`` and ``f1-06-second`` (ready, no deps, ready now)
    If ``waiting_claude`` is True, a live run with "waiting for Claude" activity is added.
    """
    project = metrics.upsert_project(conn, PROJECT)
    f1 = metrics.upsert_milestone(conn, project, "f1", verdict="ready")
    metrics.upsert_run(
        conn,
        project,
        "20260930-100000",
        ended=_at(timedelta(hours=1)),
        verdict="3 merged, 0 not",
    )

    # f1-12-escalated: escalated ticket (needed as a dependency target)
    metrics.upsert_ticket(
        conn,
        project,
        "f1-12-escalated",
        milestone_id=f1,
        kind="lead",
        state="escalated",
        difficulty=5,
    )

    # f1-04-live: running ticket with a running job (should NOT appear in queue)
    live = metrics.upsert_ticket(
        conn,
        project,
        "f1-04-live",
        milestone_id=f1,
        kind="developer",
        state="running",
        difficulty=5,
        title="Running now.",
    )
    live_run = metrics.upsert_run(
        conn,
        project,
        "20261002-113500",
        command="milestone f1",
        started=_at(timedelta(minutes=25)),
        heartbeat=_at(timedelta(seconds=10)),
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

    # f1-10-queued: ready, no deps
    metrics.upsert_ticket(
        conn, project, "f1-10-queued", milestone_id=f1, kind="developer", state="ready"
    )
    # f1-11-waits-done: ready, depends on f1-01-first (done)
    metrics.upsert_ticket(
        conn,
        project,
        "f1-11-waits-done",
        milestone_id=f1,
        kind="developer",
        state="ready",
        depends_on=["f1-01-first"],
    )
    # f1-12-waits-running: ready, depends on f1-04-live (running, not done)
    metrics.upsert_ticket(
        conn,
        project,
        "f1-12-waits-running",
        milestone_id=f1,
        kind="developer",
        state="ready",
        depends_on=["f1-04-live"],
    )
    # f1-13-waits-escalated: ready, depends on f1-12-escalated (escalated)
    metrics.upsert_ticket(
        conn,
        project,
        "f1-13-waits-escalated",
        milestone_id=f1,
        kind="developer",
        state="ready",
        depends_on=["f1-12-escalated"],
    )
    # f1-14-lead: lead ticket, no deps
    metrics.upsert_ticket(
        conn,
        project,
        "f1-14-lead",
        milestone_id=f1,
        kind="lead",
        state="ready",
    )
    # f1-05-first and f1-06-second: ready, no deps
    for ticket, goal in (("f1-06-second", "Queued second."), ("f1-05-first", "Queued first.")):
        metrics.upsert_ticket(
            conn, project, ticket, milestone_id=f1, kind="developer", state="ready", title=goal
        )

    # Live run with "waiting for Claude" activity if requested
    if waiting_claude:
        live_run = metrics.upsert_run(
            conn,
            project,
            "20261002-120000",
            command="milestone f1",
            started=_at(timedelta(minutes=5)),
            heartbeat=_at(timedelta(seconds=10)),
        )
        metrics.update_run_activity(
            conn,
            live_run,
            "waiting for Claude · f1-14-lead until 15:00",
            "2026-10-02T15:00:00+00:00",
        )


@pytest.fixture
def queue_client(db_path: Path) -> TestClient:
    """A client over the fixture plus ``write_queue``'s rows (no Claude waiting)."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        write_queue(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


@pytest.fixture
def queue_claude_client(db_path: Path) -> TestClient:
    """A client over the fixture plus ``write_queue`` with waiting for Claude."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        write_queue(conn, waiting_claude=True)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


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
            "- All tickets in `.softfield/tasks/done/`, `check-all` passes on `main`,\n"
            "- `backfill` run twice gives identical row counts."
        ),
        signoff={
            "changed": "- A metrics database that every run writes.\n"
            "- The local dashboard at `127.0.0.1`.",
            "how_to_test": "- Run `softfield milestone f1`.\n"
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
            "- All tickets in `.softfield/tasks/done/`, `check-all` passes on `main`,\n"
            "- `backfill` run twice gives identical row counts."
        ),
        signoff={
            "changed": "- A metrics database that every run writes.\n"
            "- The local dashboard at `127.0.0.1`.",
            "how_to_test": "- Run `softfield milestone f1`.\n"
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
    """On top of ``write_fixture``: two done milestones (f1, m4), two in-progress (f2, f10),
    and two not-started (f5, f3) for ordering tests."""
    project = metrics.upsert_project(conn, PROJECT)
    metrics.upsert_milestone(
        conn,
        project,
        "f1",
        status="done",
        ended="2026-10-01T10:00:00+02:00",
    )
    metrics.upsert_milestone(
        conn,
        project,
        "m4",
        status="done",
        ended="2026-09-25T10:00:00+02:00",
    )
    f2 = metrics.upsert_milestone(
        conn,
        project,
        "f2",
        title="The factory reviews itself",
        status="in progress",
        started=_at(timedelta(days=1)),
    )
    f2_run = metrics.upsert_run(conn, project, "20261002-120000", command="milestone f2")
    f2_ticket = metrics.upsert_ticket(
        conn,
        project,
        "f2-01-test",
        milestone_id=f2,
        kind="developer",
        state="running",
    )
    f2_job = metrics.start_job(
        conn,
        f2_run,
        ticket_id=f2_ticket,
        milestone_id=f2,
        role="developer",
        agent=LOCAL,
        attempt=1,
        started="2026-10-02T12:00:00+02:00",
    )
    metrics.finish_job(
        conn,
        f2_job,
        ended="2026-10-02T12:10:00+02:00",
        outcome="passed",
        tokens_in=10_000,
        tokens_out=1_000,
    )
    f10 = metrics.upsert_milestone(
        conn,
        project,
        "f10",
        title="F10 milestone",
        status="in progress",
        started=_at(timedelta(days=2)),
    )
    f10_run = metrics.upsert_run(conn, project, "20261001-100000", command="milestone f10")
    f10_ticket = metrics.upsert_ticket(
        conn,
        project,
        "f10-01-test",
        milestone_id=f10,
        kind="developer",
        state="running",
    )
    f10_job = metrics.start_job(
        conn,
        f10_run,
        ticket_id=f10_ticket,
        milestone_id=f10,
        role="developer",
        agent=LOCAL,
        attempt=1,
        started="2026-10-01T10:00:00+02:00",
    )
    metrics.finish_job(
        conn,
        f10_job,
        ended="2026-10-01T10:10:00+02:00",
        outcome="passed",
        tokens_in=10_000,
        tokens_out=1_000,
    )
    metrics.upsert_milestone(
        conn,
        project,
        "f5",
        title="F5 milestone",
        state="idea",
        status="ready",
        priority=10,
    )
    metrics.upsert_milestone(
        conn,
        project,
        "f3",
        title="F3 milestone",
        state="idea",
        status="ready",
        priority=2,
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


REVIEWER, OTHER_REVIEWER = "copilot-auto", "copilot-gpt"


def write_review_benches(conn: sqlite3.Connection) -> None:
    """On top of ``write_fixture``, review replays (`runner bench --review`) and no shadow:
    ``OTHER_REVIEWER`` replayed checkpoints of f1 and m4 and is rated 8.5 (eligible, 2
    replays); ``REVIEWER`` replayed f1 only and is rated 6 (not eligible, 1 replay; its refused
    m4 replay doesn't count)."""
    project = metrics.upsert_project(conn, PROJECT)
    run = metrics.upsert_run(conn, project, "bench-20261001-110000", command="bench")
    replays = (
        (OTHER_REVIEWER, "f1", "passed"),
        (OTHER_REVIEWER, "m4", "passed"),
        (REVIEWER, "f1", "passed"),
        (REVIEWER, "m4", "refused"),
    )
    for attempt, (agent, milestone, outcome) in enumerate(replays, start=1):
        _job(
            conn,
            run,
            metrics.upsert_milestone(conn, project, milestone),
            None,
            "bench",
            agent,
            attempt,
            outcome,
            note=queries.review_note(attempt, 1, 0, 1) if outcome == "passed" else "quota",
        )
    metrics.add_rating_change(
        conn, OTHER_REVIEWER, "reviewing", 6, 8.5, at="2026-09-30T11:00:00+02:00"
    )
    metrics.add_rating_change(conn, REVIEWER, "reviewing", 5, 6, at="2026-09-30T11:00:00+02:00")


@pytest.fixture
def review_client(db_path: Path) -> TestClient:
    """A client over the fixture plus ``write_review_benches``'s rows."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        write_review_benches(conn)
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


LINE = "f5"  # the factory line's milestone (f1 D10)


def _timed(
    conn: sqlite3.Connection,
    run: int,
    milestone: int,
    ticket: int | None,
    role: str,
    agent: str,
    attempt: int,
    span: tuple[str, str | None],
    outcome: str = "passed",
    note: str | None = None,
) -> int:
    """A job from ``span[0]`` to ``span[1]`` (HH:MM on 2026-09-30, +02:00, or a full ISO
    time); no end: running."""

    def moment(clock: str) -> str:
        return clock if "T" in clock else f"2026-09-30T{clock}:00+02:00"

    job = metrics.start_job(
        conn,
        run,
        ticket_id=ticket,
        milestone_id=milestone,
        role=role,
        agent=agent,
        attempt=attempt,
        started=moment(span[0]),
    )
    if span[1] is not None:
        metrics.finish_job(conn, job, ended=moment(span[1]), outcome=outcome, note=note)
    return job


def write_line(conn: sqlite3.Connection, repo: str | None) -> None:
    """On top of ``write_fixture``: milestone ``f5`` for the factory line, its project's repo
    at ``repo``. Times are 2026-09-30, +02:00.
    - ``f5-01-retry`` (developer, done): failed 10:00–10:20, a direction 10:21–10:25, passed
      10:30–10:50;
    - ``f5-02-parked`` (lead, done, after f5-01): parked by a Claude limit 10:55–11:00 (the
      refusal at 11:00 resets at 11:30), resumed and passed 11:45–12:05;
    - a checkpoint on Sonnet 12:10–12:20, shadowed by Copilot 12:10–12:25;
    - queued: ``f5-03-next`` (after f5-02, so ready now), ``f5-04-after`` (a lead ticket,
      after f5-03), ``f5-05-stuck`` (after the escalated ``f5-06-escalated``), and
      ``f1-09-early`` in f1, with no dependencies.
    Nothing runs from 11:00 to 11:45: one idle stretch over 40 min.
    """
    project = metrics.upsert_project(conn, PROJECT, repo=repo)
    f5 = metrics.upsert_milestone(
        conn, project, LINE, title="The factory line", started="2026-09-30T09:55:00+02:00"
    )
    run = metrics.upsert_run(conn, project, "20260930-095500", command="milestone f5")

    def ticket(name: str, kind: str, state: str, after: list[str], milestone: int = f5) -> int:
        return metrics.upsert_ticket(
            conn,
            project,
            name,
            milestone_id=milestone,
            kind=kind,
            state=state,
            depends_on=after,
            title=f"Goal of {name}.",
        )

    retry = ticket("f5-01-retry", "developer", "done", [])
    _timed(conn, run, f5, retry, "developer", LOCAL, 1, ("10:00", "10:20"), "failed")
    _timed(conn, run, f5, retry, "direction", OPUS, 1, ("10:21", "10:25"))
    _timed(conn, run, f5, retry, "developer", LOCAL, 2, ("10:30", "10:50"))

    parked = ticket("f5-02-parked", "lead", "done", ["f5-01-retry"])
    _timed(conn, run, f5, parked, "lead-ticket", OPUS, 1, ("10:55", "11:00"), "failed", "parked")
    metrics.add_usage_event(
        conn,
        OPUS,
        "2026-09-30T11:00:00+02:00",
        "refusal",
        window="five_hour",
        resets_at="2026-09-30T11:30:00+02:00",
    )
    _timed(conn, run, f5, parked, "lead-ticket", OPUS, 2, ("11:45", "12:05"))

    _timed(conn, run, f5, None, "checkpoint", SONNET, 1, ("12:10", "12:20"))
    _timed(conn, run, f5, None, "checkpoint-shadow", "copilot-auto", 1, ("12:10", "12:25"))

    ticket("f5-03-next", "developer", "ready", ["f5-02-parked"])
    ticket("f5-04-after", "lead", "ready", ["f5-03-next"])
    ticket("f5-05-stuck", "developer", "ready", ["f5-06-escalated"])
    ticket("f5-06-escalated", "developer", "escalated", [])
    ticket("f1-09-early", "developer", "ready", [], metrics.upsert_milestone(conn, project, "f1"))


LINE_NOW = NOW.astimezone(timezone(timedelta(hours=2)))  # 14:00 on 2026-10-02, +02:00


def write_today(conn: sqlite3.Connection) -> None:
    """On top of ``write_line``, the live line at ``LINE_NOW`` (times +02:00):
    - ``f9`` (in progress): ``f9-01-working`` on Qwen since 13:48 (attempt 1; the run beat
      30 s ago); ``f9-02-overnight`` on Qwen 23:40 yesterday to 00:20, merged; the lead's
      ``f9-03-lead`` 09:00–09:40, merged; ``f9-04-later`` set aside; a checkpoint on Sonnet
      10:00–10:10;
    - Claude refused at 13:30, until 15:00;
    - the milestones: ``f8`` ripe (its one ticket merged yesterday), ``f7`` signed off at 08:00
      (Sonnet did its ticket as a developer, on 2026-09-25), ``m4`` signed off on 2026-09-21;
      ``f1``, ``f5`` and ``f9`` are rows.
    """
    project = metrics.upsert_project(conn, PROJECT)
    run = metrics.upsert_run(
        conn,
        project,
        "20261002-090000",
        command="milestone f9",
        started="2026-10-02T09:00:00+02:00",
        heartbeat=(NOW - timedelta(seconds=30)).isoformat(),
    )

    def milestone(key: str, **values: Any) -> int:
        return metrics.upsert_milestone(conn, project, key, **values)

    def ticket(name: str, kind: str, state: str, m: int) -> int:
        return metrics.upsert_ticket(
            conn, project, name, milestone_id=m, kind=kind, state=state, title=f"Goal of {name}."
        )

    f9 = milestone("f9", title="Today's line", status="in progress")
    working = ticket("f9-01-working", "developer", "running", f9)
    _timed(conn, run, f9, working, "developer", LOCAL, 1, ("2026-10-02T13:48:00+02:00", None))
    overnight = ticket("f9-02-overnight", "developer", "done", f9)
    span = ("2026-10-01T23:40:00+02:00", "2026-10-02T00:20:00+02:00")
    _timed(conn, run, f9, overnight, "developer", LOCAL, 1, span)
    lead = ticket("f9-03-lead", "lead", "done", f9)
    span = ("2026-10-02T09:00:00+02:00", "2026-10-02T09:40:00+02:00")
    _timed(conn, run, f9, lead, "lead-ticket", OPUS, 1, span)
    ticket("f9-04-later", "developer", "later", f9)
    span = ("2026-10-02T10:00:00+02:00", "2026-10-02T10:10:00+02:00")
    _timed(conn, run, f9, None, "checkpoint", SONNET, 1, span)
    metrics.add_usage_event(
        conn,
        SONNET,
        "2026-10-02T13:30:00+02:00",
        "refusal",
        window="five_hour",
        resets_at="2026-10-02T15:00:00+02:00",
    )

    f8 = milestone("f8", title="Ripe one", status="review", signoff={"changed": "Ripe."})
    ripe = ticket("f8-01-ripe", "developer", "done", f8)
    span = ("2026-10-01T15:00:00+02:00", "2026-10-01T15:30:00+02:00")
    _timed(conn, run, f8, ripe, "developer", LOCAL, 1, span)
    f7 = milestone("f7", title="Harvested", status="done", ended="2026-10-02T08:00:00+02:00")
    sonnet = ticket("f7-01-sonnet", "developer", "done", f7)
    span = ("2026-09-25T10:00:00+02:00", "2026-09-25T10:30:00+02:00")
    _timed(conn, run, f7, sonnet, "developer", SONNET, 1, span)
    milestone("m4", status="done", ended="2026-09-21T12:00:00+02:00")


@pytest.fixture
def line_db(db_path: Path, tmp_path: Path) -> Path:
    """The fixture plus ``write_line``'s and ``write_today``'s rows, its repo a copy of this
    repo's project.toml over the machine fixture (``MACHINE``), with the developers the rows
    were written for (Qwen and gpt-oss-120b)."""
    repo = tmp_path / "repo"
    (repo / ".softfield").mkdir(parents=True)
    toml = Path(__file__).resolve().parents[2] / ".softfield" / "project.toml"
    roles = '\n[roles]\ndeveloper = ["local-qwen3.6-35b-a3b", "ollama-gpt-oss-120b"]\n'
    (repo / ".softfield" / "project.toml").write_text(toml.read_text(encoding="utf-8") + roles)
    conn = metrics.open_db(db_path)
    try:
        write_line(conn, str(repo))
        write_today(conn)
    finally:
        conn.close()
    return db_path


@pytest.fixture
def line_client(line_db: Path) -> TestClient:
    """A client over ``line_db``."""
    from factory_dashboard.app import create_app, get_now

    app = create_app(line_db, PROJECT)
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


def write_allowance(conn: sqlite3.Connection) -> None:
    """On top of ``write_fixture``: readings for Claude and Copilot, at ``NOW``.

    Claude: ``five_hour`` at 0.8 (resets in 5 h), ``seven_day`` at 0.2 (resets in 7 d).
    Copilot: ``month`` at 0.02 (resets in 30 d).
    """
    write_fixture(conn)
    # Write sonnet first, then opus so opus's values win (latest per window).
    for agent, window, value, offset in (
        (SONNET, "five_hour", 0.85, timedelta(hours=5)),
        (SONNET, "seven_day", 0.22, timedelta(days=7)),
        ("copilot-auto", "month", 0.02, timedelta(days=30)),
        (OPUS, "five_hour", 0.8, timedelta(hours=5)),
        (OPUS, "seven_day", 0.2, timedelta(days=7)),
    ):
        metrics.add_usage_event(
            conn,
            agent,
            NOW.isoformat(),
            "reading",
            window=window,
            value=value,
            resets_at=(NOW + offset).isoformat(),
        )


@pytest.fixture
def allowance_client(db_path: Path) -> TestClient:
    """A client over the fixture plus ``write_allowance``'s rows."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        write_allowance(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


SONNET_45, SONNET_46 = "claude-sonnet-4-5", "claude-sonnet-4-6"


def write_models(conn: sqlite3.Connection) -> None:
    """On top of ``write_fixture``, f1 checkpoints by ``SONNET`` on two models: one on
    ``SONNET_45`` ($0.50), two on ``SONNET_46`` ($0.40 each), and one whose model is ``''``
    ($0.20), counted with the fixture's checkpoint that has none ($0.30)."""
    project = metrics.upsert_project(conn, PROJECT)
    f1 = metrics.upsert_milestone(conn, project, "f1")
    run = metrics.upsert_run(conn, project, "20261001-090000", command="milestone f1")
    for attempt, model, cost in (
        (1, SONNET_45, 0.5),
        (2, SONNET_46, 0.4),
        (3, SONNET_46, 0.4),
        (4, "", 0.2),
    ):
        _job(
            conn,
            run,
            f1,
            None,
            "checkpoint",
            SONNET,
            attempt,
            "passed",
            model=model,
            cost_usd=cost,
            **CLAUDE_TOKENS,
        )


@pytest.fixture
def models_client(db_path: Path) -> TestClient:
    """A client over the fixture plus ``write_models``'s rows."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        write_models(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


def write_later(conn: sqlite3.Connection) -> None:
    """On top of ``write_fixture``: one ticket with state ``later``
    for the Set aside panel tests."""
    project = metrics.upsert_project(conn, PROJECT)
    f1 = metrics.upsert_milestone(conn, project, "f1")
    metrics.upsert_ticket(
        conn,
        project,
        "f1-99-later",
        milestone_id=f1,
        kind="developer",
        state="later",
        difficulty=3,
        title="A set-aside ticket.",
    )
    metrics.upsert_ticket(
        conn,
        project,
        "f1-97-later",
        milestone_id=f1,
        kind="lead",
        state="later",
        difficulty=2,
        title="A lead set-aside ticket.",
    )


@pytest.fixture
def later_client(db_path: Path) -> TestClient:
    """A client over the fixture plus one later ticket."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        write_later(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


PLANNING_ADR = {
    "id": "adr-20",
    "kind": "adr",
    "title": "ADR 20: the planning room",
    "path": ".softfield/adr/20-planning-room.md",
    "key_points": [{"n": 1, "title": "Planning goes first"}, {"n": 2, "title": "Opus plans"}],
}
PLANNING_PLAN = {"id": "plan", "kind": "plan", "title": "F6 plan: 7 tickets", "path": None}


def write_planning(conn: sqlite3.Connection) -> int:
    """On top of ``write_fixture`` (``m4`` is ripe: its one ticket is done), at ``NOW``:
    - ``general``: the owner wrote 2 h ago, the lead replied 1 h ago (your answers wanted);
    - ``f6`` (The planning room): the lead's reply 2 h ago lists ``PLANNING_ADR`` and
      ``PLANNING_PLAN``; an older reply listed a proposal since dropped; the owner answered 1 h
      ago, so the thread waits for the lead, not for the owner;
    - two idea cards: ``f7`` (Memory drift) has a thread, ``f9`` (Parallel developers) has none.
    Returns the project's id."""
    project = metrics.upsert_project(conn, PROJECT)
    metrics.upsert_milestone(conn, project, "f6-planning-room", title="The planning room")
    for key, title in (("f7-memory-drift", "Memory drift"), ("f9-parallel", "Parallel developers")):
        metrics.upsert_milestone(conn, project, key, title=title, state="idea")

    general = metrics.planner_thread(conn, project, "general", _at(timedelta(hours=3)))["id"]
    metrics.add_planner_message(conn, general, "owner", _at(timedelta(hours=2)), "My goals.")
    metrics.add_planner_message(conn, general, "lead", _at(timedelta(hours=1)), "Here's mine.")

    f6 = metrics.planner_thread(conn, project, "f6", _at(timedelta(hours=5)))["id"]
    dropped = {"id": "old", "kind": "plan", "title": "An older plan", "path": None}
    metrics.add_planner_message(
        conn, f6, "lead", _at(timedelta(hours=4)), "A first go.", proposals=[dropped]
    )
    metrics.add_planner_message(
        conn,
        f6,
        "lead",
        _at(timedelta(hours=2)),
        "Here's the plan.",
        proposals=[PLANNING_ADR, PLANNING_PLAN],
    )
    metrics.add_planner_message(conn, f6, "owner", _at(timedelta(hours=1)), "Looks good.")

    metrics.planner_thread(conn, project, "f7", _at(timedelta(hours=1)))
    return project


def write_signoff_button(conn: sqlite3.Connection) -> None:
    """On top of ``write_fixture``: a ripe milestone with a signoff sheet but no
    signoff request, one with its ticket done and no sheet, and one already signed
    off (a sheet, a done ticket, status ``done`` and an ``ended`` date before ``NOW``)."""
    project = metrics.upsert_project(conn, PROJECT)
    bare = metrics.upsert_milestone(
        conn,
        project,
        "bare1",
        title="Review not written",
        status="review",
        started=_at(timedelta(days=2)),
    )
    metrics.upsert_ticket(
        conn,
        project,
        "bare1-01",
        milestone_id=bare,
        kind="developer",
        state="done",
        merged_by=LOCAL,
        commit="b" * 40,
        lines_changed=10,
    )
    # Ripe milestone: all tickets done, has signoff sheet, status not "done"
    ripe_m = metrics.upsert_milestone(
        conn,
        project,
        "ripe1",
        title="Ripe milestone",
        status="review",
        signoff={"changed": "Ripe milestone."},
        started=_at(timedelta(days=2)),
    )
    metrics.upsert_ticket(
        conn,
        project,
        "ripe1-01",
        milestone_id=ripe_m,
        kind="developer",
        state="done",
        merged_by=LOCAL,
        commit="r" * 40,
        lines_changed=10,
    )
    # Signed off milestone
    signed = metrics.upsert_milestone(
        conn,
        project,
        "signed1",
        title="Already signed off",
        status="done",
        signoff={"changed": "Done."},
        ended="2026-09-21T12:00:00+02:00",
    )
    metrics.upsert_ticket(
        conn,
        project,
        "signed1-01",
        milestone_id=signed,
        kind="developer",
        state="done",
        merged_by=LOCAL,
        commit="s" * 40,
        lines_changed=10,
    )


def mark_reserve(db: Path, repo: Path, *keys: str) -> None:
    """The project's checkout at ``repo``, with a card doc for each full key in ``keys`` whose
    header says ``**Reserve:** yes`` (F172 D1), as the runner writes it."""
    cards = repo / ".softfield" / "cards"
    cards.mkdir(parents=True, exist_ok=True)
    for key in keys:
        (cards / f"{key}.md").write_text(
            f"# Milestone {key}: a card\n\n> **State:** ready · **Area:** factory"
            " · **Reserve:** yes\n\n## Goal\nIt.\n",
            encoding="utf-8",
        )
    conn = metrics.open_db(db)
    try:
        metrics.upsert_project(conn, PROJECT, repo=str(repo))
    finally:
        conn.close()


def write_board(conn: sqlite3.Connection) -> None:
    """On top of ``write_fixture`` (``f1`` and ``m4`` are ripe), at ``NOW``, the board's cards:
    - ``f20-duck-pond`` (an idea, priority 30, area product): no thread, a seed;
    - ``f21-parallel`` (an idea a thread is about) and ``f22-research`` (planning): sprouting;
    - ``f23-planted`` (ready, priority 5): two tickets, both ready;
    - ``f24-growing`` (ready, priority 1): ``f24-01-merged`` done, ``f24-02-working`` on Qwen
      (attempt 2, the run beat 30 s ago), ``f24-03-next`` ready, ``f24-04-later`` set aside,
      ``f24-05-gone`` removed;
    - ``f25-unreviewed`` (no state, priority or area): its one ticket done, no sheet stored;
    - ``f26-gone``: a removed card;
    - ``m3`` signed off on 2026-09-15;
    - the ``bugs`` row and its tickets: ``bug-01-duck-count`` set aside (factory),
      ``bug-02-stale`` ready (product, its own priority 7), ``bug-03-working`` running,
      ``bug-04-stuck`` escalated, ``bug-05-fixed`` done (its last job ended 2026-09-30 10:10)
      and ``bug-06-gone`` removed.
    """
    project = metrics.upsert_project(conn, PROJECT)
    run = metrics.upsert_run(
        conn,
        project,
        "20261002-113500",
        command="run",
        started=_at(timedelta(minutes=25)),
        heartbeat=_at(timedelta(seconds=30)),
    )

    def milestone(key: str, title: str, **values: Any) -> int:
        return metrics.upsert_milestone(conn, project, key, title=title, **values)

    def ticket(name: str, state: str, m: int, **values: Any) -> int:
        values.setdefault("kind", "developer")
        return metrics.upsert_ticket(
            conn, project, name, milestone_id=m, state=state, title=f"Goal of {name}.", **values
        )

    milestone("f20-duck-pond", "The duck pond", state="idea", priority=30, area="product")
    milestone("f21-parallel", "Parallel developers", state="idea", priority=20, area="factory")
    metrics.planner_thread(conn, project, "f21", _at(timedelta(hours=1)))
    milestone("f22-research", "Research", state="planning", priority=10, area="factory")

    planted = milestone("f23-planted", "Planted", state="ready", priority=5, area="factory")
    ticket("f23-01-first", "ready", planted)
    ticket("f23-02-second", "ready", planted)

    growing = milestone("f24-growing", "Growing", state="ready", priority=1, area="factory")
    merged = ticket("f24-01-merged", "done", growing)
    _job(conn, run, growing, merged, "developer", LOCAL, 1, "passed")
    working = ticket("f24-02-working", "running", growing)
    metrics.start_job(
        conn,
        run,
        ticket_id=working,
        milestone_id=growing,
        role="developer",
        agent=LOCAL,
        attempt=2,
        started=_at(timedelta(minutes=12)),
    )
    ticket("f24-03-next", "ready", growing)
    ticket("f24-04-later", "later", growing)
    ticket("f24-05-gone", metrics.REMOVED, growing)

    unreviewed = milestone("f25-unreviewed", "Review not written")
    ticket("f25-01-only", "done", unreviewed)

    milestone("f26-gone", "Left the repo", state=metrics.REMOVED)
    milestone("m3", "Display app", status="done", ended="2026-09-15T12:00:00+02:00")

    bugs = milestone("bugs", "Bugs", state="building")
    ticket("bug-01-duck-count", "later", bugs, area="factory")
    ticket("bug-02-stale", "ready", bugs, area="product", body="---\npriority: 7\n---\n")
    ticket("bug-03-working", "running", bugs, area="factory")
    ticket("bug-04-stuck", "escalated", bugs, area="factory")
    fixed = ticket("bug-05-fixed", "done", bugs, area="product")
    _job(conn, run, bugs, fixed, "developer", LOCAL, 1, "passed")
    ticket("bug-06-gone", metrics.REMOVED, bugs, area="factory")


@pytest.fixture
def board_db(db_path: Path) -> Path:
    """The fixture plus ``write_board``'s rows."""
    conn = metrics.open_db(db_path)
    try:
        write_board(conn)
    finally:
        conn.close()
    return db_path


@pytest.fixture
def signoff_button_client(db_path: Path) -> TestClient:
    """A client over the fixture plus ``write_signoff_button``'s rows."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        write_signoff_button(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


def write_later_priority(conn: sqlite3.Connection) -> None:
    """On top of ``write_fixture``: set-aside tickets with various priorities for priority
    ordering tests.

    - ``f1-99-later`` (developer, f1 milestone, no explicit priority → uses milestone's default 100)
    - ``f1-95-low-priority`` (developer, bugs, explicit ``priority: 5`` in body: only a bug's
      is read, F173)
    - ``f1-97-bug`` (developer, bugs milestone, no explicit priority → bug priority 50)
    - ``f1-98-milestone`` (developer, f2 milestone with priority 10 → uses milestone's priority 10)
    """
    project = metrics.upsert_project(conn, PROJECT)
    f1 = metrics.upsert_milestone(conn, project, "f1")
    # f2 milestone with priority 10
    f2 = metrics.upsert_milestone(conn, project, "f2", title="F2 milestone", priority=10)
    bugs = metrics.upsert_milestone(conn, project, "bugs", state="building")
    # f1-95-low-priority: explicit priority 5 (goes first)
    metrics.upsert_ticket(
        conn,
        project,
        "f1-95-low-priority",
        milestone_id=bugs,
        kind="developer",
        state="later",
        difficulty=2,
        title="Low priority ticket.",
        body="---\npriority: 5\n---\nGoal: Low priority ticket.",
    )
    # f1-98-milestone: no explicit priority, milestone priority is 10
    metrics.upsert_ticket(
        conn,
        project,
        "f1-98-milestone",
        milestone_id=f2,
        kind="developer",
        state="later",
        difficulty=2,
        title="Milestone priority ticket.",
    )
    # f1-97-bug: bug ticket, no explicit priority → 50
    metrics.upsert_ticket(
        conn,
        project,
        "f1-97-bug",
        milestone_id=bugs,
        kind="developer",
        state="later",
        difficulty=1,
        title="A bug ticket.",
    )
    # f1-99-later: no explicit priority, f1 milestone has no priority → 100
    metrics.upsert_ticket(
        conn,
        project,
        "f1-99-later",
        milestone_id=f1,
        kind="developer",
        state="later",
        difficulty=3,
        title="A set-aside ticket.",
    )


@pytest.fixture
def later_priority_client(db_path: Path) -> TestClient:
    """A client over the fixture plus ``write_later_priority``'s rows."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        write_later_priority(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


@pytest.fixture
def planning(db_path: Path) -> int:
    """``write_planning``'s rows in the fixture database; the project's id."""
    conn = metrics.open_db(db_path)
    try:
        return write_planning(conn)
    finally:
        conn.close()


@pytest.fixture
def checkout(tmp_path: Path, db_path: Path, planning: int, monkeypatch) -> Path:
    """The project's repo, a git checkout on main; its ADR 20 not there yet."""
    from tests.runner.conftest import git

    for name in ("GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE"):  # set when run from a hook
        monkeypatch.delenv(name, raising=False)
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "Test")
    git(repo, "commit", "-q", "--allow-empty", "-m", "init")
    conn = metrics.open_db(db_path)
    try:
        metrics.upsert_project(conn, PROJECT, repo=str(repo))
    finally:
        conn.close()
    return repo


def write_lead_tickets(conn: sqlite3.Connection) -> None:
    """On top of ``write_fixture``: one Sonnet lead ticket (d4) and one Opus lead ticket (d5).

    The Sonnet ticket (difficulty 4) is a non-Opus lead ticket; the Opus ticket (difficulty 5)
    is an Opus lead ticket. Both are merged with a passed job.
    """
    project = metrics.upsert_project(conn, PROJECT)
    f1 = metrics.upsert_milestone(conn, project, "f1")
    run = metrics.upsert_run(conn, project, "20261001-100000", command="milestone f1")

    # Sonnet lead ticket (difficulty 4, non-Opus)
    sonnet_ticket = metrics.upsert_ticket(
        conn,
        project,
        "f1-99-sonnet",
        milestone_id=f1,
        kind="lead",
        state="done",
        difficulty=4,
        merged_by=SONNET,
        commit="s" * 40,
    )
    metrics.start_job(
        conn,
        run,
        ticket_id=sonnet_ticket,
        milestone_id=f1,
        role="lead-ticket",
        agent=SONNET,
        attempt=1,
        started="2026-10-01T10:00:00+02:00",
    )
    metrics.finish_job(
        conn,
        metrics.start_job(
            conn,
            run,
            ticket_id=sonnet_ticket,
            milestone_id=f1,
            role="lead-ticket",
            agent=SONNET,
            attempt=1,
            started="2026-10-01T10:00:00+02:00",
        ),
        ended="2026-10-01T10:10:00+02:00",
        outcome="passed",
        cost_usd=0.50,
        tokens_in=10_000,
        tokens_cached=100_000,
        tokens_out=2_000,
    )

    # Opus lead ticket (difficulty 5, Opus)
    opus_ticket = metrics.upsert_ticket(
        conn,
        project,
        "f1-98-opus",
        milestone_id=f1,
        kind="lead",
        state="done",
        difficulty=5,
        merged_by=OPUS,
        commit="o" * 40,
    )
    metrics.start_job(
        conn,
        run,
        ticket_id=opus_ticket,
        milestone_id=f1,
        role="lead-ticket",
        agent=OPUS,
        attempt=1,
        started="2026-10-01T11:00:00+02:00",
    )
    metrics.finish_job(
        conn,
        metrics.start_job(
            conn,
            run,
            ticket_id=opus_ticket,
            milestone_id=f1,
            role="lead-ticket",
            agent=OPUS,
            attempt=1,
            started="2026-10-01T11:00:00+02:00",
        ),
        ended="2026-10-01T11:10:00+02:00",
        outcome="passed",
        cost_usd=2.00,
        tokens_in=10_000,
        tokens_cached=100_000,
        tokens_out=2_000,
    )


@pytest.fixture
def lead_client(db_path: Path) -> TestClient:
    """A client over the fixture plus non-Opus lead tickets (Sonnet d4 + Opus d5)."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        write_lead_tickets(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")
