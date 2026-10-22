import sqlite3
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from factory_dashboard.queries import (
    SEED_DOLLARS_PER_LINE,
    Idle,
    clog,
    connect,
    eligibility,
    milestone_results,
    parse_review_note,
    review_note,
    run_order,
    savings,
    trends,
)
from runner import metrics
from tests.factory_dashboard.conftest import CLAUDE_TOKENS, LOCAL, OPUS, PROJECT, SONNET, _job


def test_run_order_is_pick_next_applied_again_and_again(line_db):
    conn = connect(line_db)
    try:
        order = run_order(conn, PROJECT)
    finally:
        conn.close()
    # f1 runs before f5; f5-04 waits for f5-03, which goes first; f5-05 waits behind an
    # escalated ticket, so the runner never takes it: last, with what it waits for
    assert [(u.ticket, u.waits) for u in order] == [
        ("f1-09-early", ()),
        ("f5-03-next", ()),
        ("f5-04-after", ("f5-03-next",)),
        ("f5-05-stuck", ("f5-06-escalated",)),
    ]
    assert [u.ready_now for u in order] == [True, True, False, False]
    assert (order[2].kind, order[2].milestone, order[2].title) == (
        "lead",
        "f5",
        "Goal of f5-04-after.",
    )


def test_run_order_follows_the_board_not_a_feature_tickets_own_priority(tmp_path):
    """F173: the order the runner picks, read from the rows: a card at 0 before one at 1
    whatever its tickets say, inside a card by what they wait for then id, a bug by its own."""
    db = metrics.open_db(tmp_path / "factory-metrics.sqlite")
    project = metrics.upsert_project(db, PROJECT)
    first = metrics.upsert_milestone(db, project, "f9", priority=0)
    second = metrics.upsert_milestone(db, project, "f2", priority=1)
    bugs = metrics.upsert_milestone(db, project, "bugs")
    rows = [
        ("f9-02-b", first, "---\npriority: 100\n---\n", []),
        ("f9-01-a", first, "---\npriority: 100\n---\n", ["f9-02-b"]),
        ("f9-03-c", first, None, []),
        ("f2-01-a", second, "---\npriority: 0\n---\n", []),
        ("bug-01-x", bugs, "---\npriority: 2\n---\n", []),
        ("bug-02-y", bugs, None, []),
    ]
    for ticket, milestone_id, body, after in rows:
        metrics.upsert_ticket(
            db,
            project,
            ticket,
            milestone_id=milestone_id,
            state="ready",
            body=body,
            depends_on=after,
        )
    try:
        order = run_order(db, PROJECT)
    finally:
        db.close()
    assert [(u.ticket, u.priority) for u in order] == [
        ("f9-02-b", 0),
        ("f9-01-a", 0),
        ("f9-03-c", 0),
        ("f2-01-a", 1),
        ("bug-01-x", 2),
        ("bug-02-y", 50),
    ]


def test_run_order_of_an_empty_queue(db):
    assert run_order(db, PROJECT) == []
    assert run_order(db, "elsewhere") == []


# --- what clogged the line (f3-04) -----------------------------------------------------------

ZONE = timezone(timedelta(hours=2))
MIDNIGHT = datetime(2026, 10, 3, tzinfo=ZONE)
NOON = MIDNIGHT + timedelta(hours=12)
GPT_OSS, NEMOTRON = "ollama-gpt-oss-120b", "ollama-nemotron-3-super"


def _clock(hhmm: str) -> str:
    return f"2026-10-03T{hhmm}:00+02:00"


@pytest.fixture
def clog_db(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    """A day (2026-10-03, +02:00) of one run, 09:00–10:40, with three developer machines:
    - the lead's ``f6-01-lead`` on Opus 09:00–09:10, parked by a limit that resets at 09:40;
    - ``f6-02-dev`` on Qwen: failed 09:40–09:52 and 09:52–10:11, passed 10:11–10:20;
    - GPT-OSS and Nemotron ran nothing today (Nemotron failed a ticket yesterday)."""
    path = tmp_path / "clog.sqlite"
    conn = metrics.open_db(path)
    project = metrics.upsert_project(conn, PROJECT)
    f6 = metrics.upsert_milestone(conn, project, "f6")
    run = metrics.upsert_run(
        conn, project, "20261003-090000", started=_clock("09:00"), ended=_clock("10:40")
    )

    def job(
        ticket: int, role: str, agent: str, n: int, span: tuple[str, str], outcome: str,
        note: str | None = None,
    ) -> None:  # fmt: skip
        start, stop = span
        started = start if "T" in start else _clock(start)
        job_id = metrics.start_job(
            conn, run, ticket_id=ticket, milestone_id=f6, role=role, agent=agent, attempt=n,
            started=started,
        )  # fmt: skip
        ended = stop if "T" in stop else _clock(stop)
        metrics.finish_job(conn, job_id, ended=ended, outcome=outcome, note=note)

    lead = metrics.upsert_ticket(conn, project, "f6-01-lead", milestone_id=f6, kind="lead")
    job(lead, "lead-ticket", OPUS, 1, ("09:00", "09:10"), outcome="failed", note="parked")
    metrics.add_usage_event(
        conn, OPUS, _clock("09:10"), "refusal", window="five_hour", resets_at=_clock("09:40")
    )
    dev = metrics.upsert_ticket(conn, project, "f6-02-dev", milestone_id=f6, kind="developer")
    job(dev, "developer", LOCAL, 1, ("09:40", "09:52"), outcome="failed")
    job(dev, "developer", LOCAL, 2, ("09:52", "10:11"), outcome="failed")
    job(dev, "last-attempt", LOCAL, 3, ("10:11", "10:20"), outcome="passed")
    old = metrics.upsert_ticket(conn, project, "f6-00-old", milestone_id=f6, kind="developer")
    yesterday = ("2026-10-02T15:00:00+02:00", "2026-10-02T15:30:00+02:00")
    job(old, "developer", NEMOTRON, 1, yesterday, outcome="failed")
    conn.close()
    reading = connect(path)
    try:
        yield reading
    finally:
        reading.close()


def _write(conn: sqlite3.Connection) -> sqlite3.Connection:
    """A writable connection on the same database as the read-only ``conn``."""
    [(_, _, file)] = conn.execute("PRAGMA database_list").fetchall()
    return metrics.open_db(Path(file))


def test_clog_counts_the_park_the_failed_attempts_and_the_idle_machines(clog_db):
    found = clog(clog_db, PROJECT, MIDNIGHT, NOON, machines=[LOCAL, GPT_OSS, NEMOTRON])
    assert (found.limit, found.failed, found.failures, found.owner) == (30, 31, 2, 0)
    # The runner lived 100 min; a job ran for 50 of them (09:00–09:10, 09:40–10:20): Qwen sat
    # idle through the lead's 10, the other two through all 50.
    assert found.live == 100
    assert found.idle == (
        Idle(LOCAL, 10, 0.1),
        Idle(GPT_OSS, 50, 0.5),
        Idle(NEMOTRON, 50, 0.5),
    )


def test_clog_finds_the_developer_machines_itself(clog_db):
    found = clog(clog_db, PROJECT, MIDNIGHT, NOON)
    assert [i.agent for i in found.idle] == [LOCAL, NEMOTRON]  # those that ran a developer job


def test_clog_counts_only_what_lies_after_since_and_before_now(clog_db):
    found = clog(clog_db, PROJECT, MIDNIGHT, MIDNIGHT + timedelta(hours=9, minutes=55))
    # at 09:55: the whole park and the first failure; the second attempt hasn't failed yet
    assert (found.limit, found.failed, found.failures, found.live) == (30, 12, 1, 55)
    later = clog(clog_db, PROJECT, MIDNIGHT + timedelta(hours=9, minutes=30), NOON)
    assert (later.limit, later.failed, later.live) == (10, 31, 70)


def test_a_wait_for_claude_counts_once_with_the_limit_and_only_while_the_runner_lives(clog_db):
    writing = _write(clog_db)
    try:
        # the runner waited for the reset, a minute past it: the overlap counts once
        metrics.add_usage_event(
            writing, "runner", _clock("09:10"), "wait", resets_at=_clock("09:41")
        )
        # a hold with no refusal (Claude's reserve), cut short when the run ended at 10:40
        metrics.add_usage_event(
            writing, "runner", _clock("10:30"), "wait", resets_at=_clock("11:30")
        )
        # a passing error isn't a limit; Ollama's refusal isn't Claude's
        metrics.add_usage_event(writing, "runner", _clock("10:20"), "transient")
        metrics.add_usage_event(
            writing, GPT_OSS, _clock("10:00"), "refusal", resets_at=_clock("10:20")
        )
    finally:
        writing.close()
    assert clog(clog_db, PROJECT, MIDNIGHT, NOON).limit == 31 + 10


def test_clog_counts_the_owners_open_items_while_no_job_ran(clog_db):
    writing = _write(clog_db)
    project = writing.execute("SELECT id FROM projects").fetchone()[0]
    try:
        # open 10:15–10:30 (a job ran until 10:20), and from 11:00 on, two items at once
        first = metrics.upsert_owner_item(
            writing, project, "blocked", "f6-03", created=_clock("10:15")
        )
        metrics.resolve_owner_item(writing, first, _clock("10:30"))
        metrics.upsert_owner_item(writing, project, "signoff", "f6", created=_clock("11:00"))
        metrics.upsert_owner_item(writing, project, "escalated", "f6-04", created=_clock("11:30"))
    finally:
        writing.close()
    assert clog(clog_db, PROJECT, MIDNIGHT, NOON).owner == 10 + 60


def test_the_owners_pause_counts_as_stopped_for_you_not_as_a_limit(clog_db):
    """f5-18: the runner held for the owner from their pause to their resume, or to now while
    it still holds."""
    before = clog(clog_db, PROJECT, MIDNIGHT, NOON)
    writing = _write(clog_db)
    try:
        metrics.add_usage_event(
            writing, "runner", _clock("10:25"), "pause", resets_at=_clock("10:35")
        )
        metrics.add_usage_event(writing, "runner", _clock("11:40"), "pause")  # still paused
    finally:
        writing.close()
    found = clog(clog_db, PROJECT, MIDNIGHT, NOON)
    assert (found.owner, found.limit) == (before.owner + 10 + 20, before.limit)


def test_a_day_with_no_runs_gives_zeros(db):
    found = clog(db, PROJECT, MIDNIGHT, NOON, machines=[LOCAL])
    assert (found.limit, found.failed, found.owner, found.live) == (0, 0, 0, 0)
    assert found.idle == (Idle(LOCAL, 0, 0.0),)
    assert clog(db, "elsewhere", MIDNIGHT, NOON).idle == ()


def test_milestone_results_count_what_a_person_would(db):
    r = milestone_results(db, PROJECT, "f1")
    assert r is not None
    assert (r.key, r.title) == ("f1", "The factory measures itself")
    assert (r.tickets, r.merged) == (3, 3)
    # f1-01 passed at once, f1-02 never did; the lead ticket isn't a developer's
    assert (r.first_attempt, r.developer_tickets) == (1, 2)
    assert r.pass_rate == 0.5
    assert r.attempts == 4
    assert (r.escalations, r.directions, r.checkpoints, r.review_rounds) == (1, 1, 1, 1)
    assert r.findings == {"blocking": 1, "should-fix": 2, "nit": 1}


def test_milestone_results_split_local_and_claude_spend(db):
    r = milestone_results(db, PROJECT, "f1")
    assert r is not None
    assert (r.local.jobs, r.local.tokens_in, r.local.tokens_out) == (4, 500_000, 25_000)
    assert r.local.dollars == 0
    assert r.claude.jobs == 5
    assert r.claude.dollars == pytest.approx(7.80)
    assert r.claude.token_equivalents == pytest.approx(150_000)
    by_agent = {a.agent: a for a in r.agents}
    assert set(by_agent) == {LOCAL, OPUS, SONNET}
    assert by_agent[OPUS].jobs == 4 and by_agent[OPUS].dollars == pytest.approx(7.50)
    assert by_agent[SONNET].jobs == 1 and by_agent[SONNET].dollars == pytest.approx(0.30)
    assert (by_agent[LOCAL].jobs, by_agent[LOCAL].dollars) == (4, 0)


def test_a_claude_job_without_its_cost_is_priced_from_its_tokens(db):
    r = milestone_results(db, PROJECT, "m4")
    assert r is not None
    assert r.claude.dollars == pytest.approx(2.00)  # 500k equivalents at $4 per 1M
    assert r.review_rounds == 1  # no count kept: its review jobs


def test_an_unknown_milestone_has_no_results(db):
    assert milestone_results(db, PROJECT, "m9") is None
    assert milestone_results(db, "elsewhere", "f1") is None


def test_savings_follow_d7(db):
    s = savings(db, PROJECT, "f1")
    # doing it itself: f1-01's 100 lines at the lead's d4 rate ($3 for 200 lines);
    # f1-02 was merged by the lead, so its lines don't count
    assert s.lines == 100
    assert s.doing_itself == pytest.approx(1.50)
    # supporting: f1-02's direction and escalation ($3), and 2/3 of the review + checkpoint
    assert s.supporting == pytest.approx(3.00 + 1.80 * 2 / 3)
    assert s.net == pytest.approx(1.50 - 4.20)
    # tokens underneath: the lead ticket's 30k equivalents for 200 lines, and the jobs' own
    assert s.doing_itself_tokens == pytest.approx(100 * 30_000 / 200)
    assert s.supporting_tokens == pytest.approx(60_000 + 60_000 * 2 / 3)
    [agent] = s.agents
    assert (agent.agent, agent.tickets, agent.lines) == (LOCAL, 2, 100)
    assert agent.net == pytest.approx(s.net)


def test_savings_use_m4s_seed_when_no_lead_ticket_has_that_difficulty(db, db_path):
    writer = metrics.open_db(db_path)
    project = metrics.upsert_project(writer, PROJECT)
    metrics.upsert_ticket(writer, project, "f1-01-first", difficulty=3)
    writer.close()
    assert pytest.approx(3.5 * 4 / 1979) == SEED_DOLLARS_PER_LINE
    assert savings(db, PROJECT, "f1").doing_itself == pytest.approx(100 * SEED_DOLLARS_PER_LINE)
    # m4's ticket is d2, and there is no d2 lead ticket anywhere
    assert savings(db, PROJECT, "m4").doing_itself == pytest.approx(80 * SEED_DOLLARS_PER_LINE)


def test_overall_savings_add_up_the_milestones(db):
    f1, m4, overall = savings(db, PROJECT, "f1"), savings(db, PROJECT, "m4"), savings(db, PROJECT)
    assert overall.doing_itself == pytest.approx(f1.doing_itself + m4.doing_itself)
    assert overall.supporting == pytest.approx(f1.supporting + m4.supporting)
    assert m4.supporting == pytest.approx(2.00)
    assert overall.lines == 180
    [agent] = overall.agents
    assert (agent.agent, agent.tickets) == (LOCAL, 3)


def write_sonnet_ticket(db_path) -> None:
    """f1-04-sonnet: a d4 developer ticket Sonnet merged (60 lines) at its one attempt ($0.40),
    and f1-05-removed, attempted once by the local model, then removed."""
    writer = metrics.open_db(db_path)
    project = metrics.upsert_project(writer, PROJECT)
    f1 = metrics.upsert_milestone(writer, project, "f1")
    run = metrics.upsert_run(writer, project, "20260930-100000")
    sonnet = metrics.upsert_ticket(
        writer,
        project,
        "f1-04-sonnet",
        milestone_id=f1,
        kind="developer",
        state="done",
        difficulty=4,
        merged_by=SONNET,
        commit="e" * 40,
        lines_changed=60,
    )
    _job(writer, run, f1, sonnet, "developer", SONNET, 1, "passed", cost_usd=0.4, **CLAUDE_TOKENS)
    removed = metrics.upsert_ticket(
        writer, project, "f1-05-removed", milestone_id=f1, kind="developer", state="removed"
    )
    _job(writer, run, f1, removed, "developer", LOCAL, 1, "failed", tokens_in=1_000)
    writer.close()


def test_a_ticket_sonnet_merged_counts_its_lines_and_its_sonnet_jobs(db, db_path):
    write_sonnet_ticket(db_path)
    s = savings(db, PROJECT, "f1")
    by_agent = {a.agent: a for a in s.agents}
    sonnet = by_agent[SONNET]
    assert (sonnet.tickets, sonnet.lines) == (1, 60)
    # 60 lines at the lead's d4 rate ($3 for 200 lines); its own job, and a fifth of the review
    # and checkpoint (the removed ticket was worked on too)
    assert sonnet.doing_itself == pytest.approx(0.90)
    assert sonnet.supporting == pytest.approx(0.40 + 1.80 / 5)
    assert sonnet.doing_itself_tokens == pytest.approx(60 * 30_000 / 200)
    # the lead's escalation of f1-02 still doesn't credit its lines to anyone
    assert by_agent[LOCAL].lines == 100


def test_removed_tickets_are_out_of_the_milestones_tickets(db, db_path):
    write_sonnet_ticket(db_path)
    r = milestone_results(db, PROJECT, "f1")
    assert r is not None
    assert (r.tickets, r.merged) == (4, 4)
    assert (r.first_attempt, r.developer_tickets) == (2, 3)


def test_trends_run_oldest_first(db):
    points = trends(db, PROJECT)
    assert [p.results.key for p in points] == ["m4", "f1"]
    assert points[0].results.pass_rate == 1.0
    assert points[1].savings.net == pytest.approx(-2.70)


REVIEWER, OTHER_REVIEWER, SHADOW = "copilot-auto", "copilot-gpt", "copilot-shadow"


def _replays(db_path, missed_blocking: int = 0) -> sqlite3.Connection:
    """Review replays of the checkpoint (`runner bench --review`, ADR 16 item 10) on top of
    the fixture: copilot-auto replayed f1 only (its m4 replay was refused); copilot-gpt
    replayed f1 and m4, missing ``missed_blocking`` blocking findings in m4. A shadow job
    alone no longer counts. Both reviewers are rated 8.5 by their latest change, whatever its
    skill."""
    writer = metrics.open_db(db_path)
    project = metrics.upsert_project(writer, PROJECT)
    run = metrics.upsert_run(writer, project, "bench-20261001-100000", command="bench")
    replays = (
        (REVIEWER, "f1", "passed", "bench", 0),
        (REVIEWER, "m4", "refused", "bench", 0),
        (OTHER_REVIEWER, "f1", "passed", "bench", 0),
        (OTHER_REVIEWER, "m4", "passed", "bench", missed_blocking),
        (SHADOW, "f1", "passed", "checkpoint-shadow", 0),
        (SHADOW, "m4", "passed", "checkpoint-shadow", 0),
    )
    for attempt, (agent, milestone, outcome, role, blocking) in enumerate(replays, start=1):
        job = metrics.start_job(
            writer,
            run,
            ticket_id=None,
            milestone_id=metrics.upsert_milestone(writer, project, milestone),
            role=role,
            agent=agent,
            attempt=attempt,  # one run: the jobs' key needs them apart
            started="2026-10-01T10:30:00+02:00",
        )
        note = review_note(2, 1 + blocking, blocking, 0) if outcome == "passed" else "quota"
        metrics.finish_job(
            writer, job, ended="2026-10-01T10:31:00+02:00", outcome=outcome, note=note
        )
    for agent in (REVIEWER, OTHER_REVIEWER, SHADOW):
        metrics.add_rating_change(writer, agent, "reviewing", 6, 9, at="2026-09-30T11:00:00+02:00")
        metrics.add_rating_change(writer, agent, "coding", 6, 8.5, at="2026-09-30T12:00:00+02:00")
    writer.commit()
    return writer


def test_a_review_note_reads_back():
    assert parse_review_note(review_note(1, 2, 1, 3)) == (1, 2, 1, 3)
    assert parse_review_note("would escalate") is None
    assert parse_review_note(None) is None


def test_eligibility_says_no_with_its_reason_for_one_milestone(db, db_path):
    _replays(db_path).close()
    found = {(e.agent, e.role): e for e in eligibility(db, PROJECT)}
    assert set(found) == {(REVIEWER, "checkpoint"), (OTHER_REVIEWER, "checkpoint")}
    one = found[REVIEWER, "checkpoint"]
    assert not one.eligible
    assert one.reason == "replayed checkpoints of 1 milestone, needs 2"


def test_eligibility_says_yes_for_an_agent_meeting_every_bar(db, db_path):
    _replays(db_path).close()
    both = next(e for e in eligibility(db, PROJECT) if e.agent == OTHER_REVIEWER)
    assert both.eligible
    # f1's tickets go up to d5, m4's is d2: rated 8.5 covers them
    assert both.reason == (
        "rated 8.5 over replays of 2 milestones, no missed blocking finding, tickets up to"
        " difficulty 5"
    )


def test_eligibility_names_every_bar_it_misses(db, db_path):
    writer = _replays(db_path, missed_blocking=1)
    project = metrics.upsert_project(writer, PROJECT)
    metrics.add_rating_change(
        writer, OTHER_REVIEWER, "coding", 8.5, 4, at="2026-09-30T13:00:00+02:00"
    )
    metrics.upsert_ticket(writer, project, "f1-01-first", difficulty_corrected=9)
    writer.commit()
    writer.close()
    both = next(e for e in eligibility(db, PROJECT) if e.agent == OTHER_REVIEWER)
    assert not both.eligible
    assert both.reason == (
        "rated 4, needs 8; 1 missed blocking finding; rated 4, below difficulty 9 of a ticket"
        " it reviewed"
    )


def test_eligibility_without_a_rating_says_so(db, db_path):
    writer = _replays(db_path)
    writer.execute("DELETE FROM rating_changes WHERE agent = ?", (OTHER_REVIEWER,))
    writer.commit()
    writer.close()
    both = next(e for e in eligibility(db, PROJECT) if e.agent == OTHER_REVIEWER)
    assert (both.eligible, both.reason) == (False, "no rating yet")


def test_the_connection_is_read_only(db):
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        db.execute("DELETE FROM jobs")


def test_connect_refuses_a_missing_database(tmp_path):
    with pytest.raises(sqlite3.OperationalError):
        connect(tmp_path / "nothing.sqlite")
