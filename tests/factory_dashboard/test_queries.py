import re
import sqlite3
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from factory_dashboard import milestones, overview
from factory_dashboard.queries import (
    SEED_DOLLARS_PER_LINE,
    Idle,
    clog,
    connect,
    eligibility,
    lead_split,
    local,
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


def test_run_order_puts_what_a_higher_ticket_waits_for_in_its_place(tmp_path):
    """F173 D6, D7: f15-06 (F15 at 4) waits on f73-01 (F73 at 6), which waits on f63-01
    (F63 at 14): both go before F132 (at 5), each saying whom it runs early for. A waiter of
    its own card says nothing."""
    db = metrics.open_db(tmp_path / "factory-metrics.sqlite")
    project = metrics.upsert_project(db, PROJECT)
    cards = {
        key: metrics.upsert_milestone(db, project, key, priority=place)
        for key, place in (("f15", 4), ("f132", 5), ("f73", 6), ("f63", 14))
    }
    rows = [
        ("f15-06-card-actions", "f15", ["f73-01-set-aside-list"]),
        ("f73-01-set-aside-list", "f73", ["f63-01-desk-order"]),
        ("f63-01-desk-order", "f63", []),
        ("f132-01-a", "f132", ["f132-02-b"]),
        ("f132-02-b", "f132", []),
    ]
    for ticket, key, after in rows:
        metrics.upsert_ticket(
            db, project, ticket, milestone_id=cards[key], state="ready", depends_on=after
        )
    try:
        order = run_order(db, PROJECT)
    finally:
        db.close()
    assert [(u.ticket, u.early_for) for u in order] == [
        ("f63-01-desk-order", "f15-06-card-actions"),
        ("f73-01-set-aside-list", "f15-06-card-actions"),
        ("f15-06-card-actions", None),
        ("f132-02-b", None),
        ("f132-01-a", None),
    ]
    assert [u.priority for u in order] == [14, 6, 4, 5, 5]  # the board's place is kept


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


def _hour_and_minute(at: datetime) -> tuple[int, int]:
    return at.hour, at.minute


def test_local_gives_the_same_moment_on_the_machines_clock(paris):
    """F187 D3: whatever offset a time was stored with; winter (+01:00) and summer (+02:00)."""
    assert _hour_and_minute(local("2026-10-29T08:00:00+00:00")) == (9, 0)
    assert _hour_and_minute(local("2026-10-24T09:00:00+01:00")) == (10, 0)
    assert local("2026-10-24T09:00:00+01:00").utcoffset() == timedelta(hours=2)
    assert _hour_and_minute(local(datetime(2026, 10, 29, 8, 0, tzinfo=UTC))) == (9, 0)
    assert local(None) is None


def test_local_counts_a_naive_time_as_utc(paris):
    assert _hour_and_minute(local("2026-10-29T08:00:00")) == (9, 0)


def test_the_top_bars_paused_time_is_local(paris, serve, db_path):
    client = serve()
    writer = metrics.open_db(db_path)
    try:
        metrics.add_usage_event(writer, "runner", "2026-10-29T08:00:00+00:00", "pause")
    finally:
        writer.close()
    bar = re.search(r'<span class="words" role="status">([^<]*)</span>', client.get("/live").text)
    assert bar, "the top bar's status"
    assert bar.group(1).startswith("Paused by you since 09:00")


def test_a_cards_date_is_local(paris):
    assert milestones._date("2026-10-29T08:00:00+00:00") == "29 Oct 09:00"


def test_the_allowance_resets_are_local(paris, allowance_client):
    """The fixture's 5-hour window resets at 17:00 UTC on 2 Oct and its week at 12:00 on 9 Oct,
    both in Paris's summer time."""
    html = allowance_client.get("/").text
    assert "resets at 19:00" in html and "resets on Oct 9 14:00" in html
    assert "resets at 17:00" not in html and "resets on Oct 9 12:00" not in html


def test_a_reset_after_midnight_local_is_not_today(paris):
    """22:30 UTC is 00:30 the next day in Paris: not "later today"."""
    now = datetime(2026, 10, 2, 21, 0, tzinfo=UTC)
    resets = local("2026-10-02T22:30:00+00:00")
    assert overview._reset_label(resets, now) == "resets on Oct 3 00:30"


def test_the_runs_and_jobs_pages_print_local_times(paris, serve, db_path):
    writer = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(writer, PROJECT)
        milestone = metrics.upsert_milestone(writer, project, "f187")
        run = metrics.upsert_run(
            writer,
            project,
            "20261029-090000",
            started="2026-10-29T08:00:00+00:00",
            ended="2026-10-29T08:30:00+00:00",
        )
        job = metrics.start_job(
            writer,
            run,
            ticket_id=None,
            milestone_id=milestone,
            role="developer",
            agent=LOCAL,
            attempt=1,
            started="2026-10-29T08:00:00+00:00",
        )
        metrics.finish_job(writer, job, ended="2026-10-29T08:30:00+00:00", outcome="passed")
    finally:
        writer.close()
    client = serve()
    pages = ("/runs", "/runs/20261029-090000", "/jobs", f"/jobs/{job}", f"/projects/{PROJECT}")
    for path in pages:
        html = client.get(path).text
        assert "2026-10-29T09:" in html, path
        assert "2026-10-29T08:" not in html, path


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


# --- lead split (F179 D1, D2, D3) -----------------------------------------------------------


def _make_lead_db(
    tmp_path: Path,
    *,
    opus_d3_1_cost: float = 1.6,
    opus_d3_2_cost: float = 1.8,
    sonnet_d3_cost: float = 0.5,
) -> sqlite3.Connection:
    """A project where Opus merged two difficulty-3 leads and Sonnet merged one."""
    path = tmp_path / "lead.sqlite"
    writer = metrics.open_db(path)
    project = metrics.upsert_project(writer, PROJECT)
    f1 = metrics.upsert_milestone(writer, project, "f1", started="2026-10-01T09:00:00+02:00")
    run = metrics.upsert_run(writer, project, "20261001-100000")

    # Opus lead ticket 1: d3, $1.60
    t1 = metrics.upsert_ticket(
        writer,
        project,
        "f1-01-lead",
        milestone_id=f1,
        kind="lead",
        difficulty=3,
        state="done",
        merged_by=OPUS,
        commit="a" * 40,
    )
    _job(
        writer,
        run,
        f1,
        t1,
        "lead-ticket",
        OPUS,
        1,
        "passed",
        cost_usd=opus_d3_1_cost,
        **CLAUDE_TOKENS,
    )

    # Opus lead ticket 2: d3, $1.80
    t2 = metrics.upsert_ticket(
        writer,
        project,
        "f1-02-lead",
        milestone_id=f1,
        kind="lead",
        difficulty=3,
        state="done",
        merged_by=OPUS,
        commit="b" * 40,
    )
    _job(
        writer,
        run,
        f1,
        t2,
        "lead-ticket",
        OPUS,
        1,
        "passed",
        cost_usd=opus_d3_2_cost,
        **CLAUDE_TOKENS,
    )

    # Sonnet lead ticket: d3, $0.50
    t3 = metrics.upsert_ticket(
        writer,
        project,
        "f1-03-lead",
        milestone_id=f1,
        kind="lead",
        difficulty=3,
        state="done",
        merged_by=SONNET,
        commit="c" * 40,
    )
    _job(
        writer,
        run,
        f1,
        t3,
        "lead-ticket",
        SONNET,
        1,
        "passed",
        cost_usd=sonnet_d3_cost,
        **CLAUDE_TOKENS,
    )

    writer.close()
    return connect(path)


def _lead_db(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    """Generator: yields the read-only connection from a lead-split database."""
    conn = _make_lead_db(tmp_path)
    try:
        yield conn
    finally:
        conn.close()


def test_sonnet_row_says_how_many_tickets_would_have_and_saved(tmp_path):
    """F179 D1, D2: Opus merged two d3 leads ($1.60, $1.80); Sonnet merged one d3 ($0.50).
    Sonnet's 'difficulty 4 or below' row: 1 ticket, 1 first time,
    would-have $1.70, saved $1.20."""
    gen = _lead_db(tmp_path)
    conn = next(gen)
    rows = lead_split(conn, PROJECT)
    assert len(rows) == 2
    sonnet_rows = [r for r in rows if r.agent == SONNET]
    assert len(sonnet_rows) == 1
    s = sonnet_rows[0]
    assert s.band == "difficulty 4 or below"
    assert s.tickets == 1
    assert s.merged == 1
    assert s.first_time == 1
    assert s.step_ups == 0
    assert s.would_have == pytest.approx(1.70)
    assert s.saved == pytest.approx(1.20)
    assert s.reviewed == 0
    assert s.should_fix == 0
    assert s.blocking == 0


def test_parked_first_job_then_passed_counts_first_time(tmp_path):
    """F179 D1: a Sonnet ticket whose first job is parked, then a passed
    Sonnet job, counts first time."""
    path = tmp_path / "parked.sqlite"
    writer = metrics.open_db(path)
    project = metrics.upsert_project(writer, PROJECT)
    f1 = metrics.upsert_milestone(writer, project, "f1", started="2026-10-01T09:00:00+02:00")
    run = metrics.upsert_run(writer, project, "20261001-100000")

    # Opus d3 leads for mean
    t0 = metrics.upsert_ticket(
        writer,
        project,
        "f1-00-lead",
        milestone_id=f1,
        kind="lead",
        difficulty=3,
        state="done",
        merged_by=OPUS,
        commit="0" * 40,
    )
    _job(writer, run, f1, t0, "lead-ticket", OPUS, 1, "passed", cost_usd=1.70, **CLAUDE_TOKENS)

    # Sonnet ticket: first job parked, second passed
    t1 = metrics.upsert_ticket(
        writer,
        project,
        "f1-01-lead",
        milestone_id=f1,
        kind="lead",
        difficulty=3,
        state="done",
        merged_by=SONNET,
        commit="a" * 40,
    )
    _job(writer, run, f1, t1, "lead-ticket", SONNET, 1, "failed", note="parked")
    _job(writer, run, f1, t1, "lead-ticket", SONNET, 2, "passed", cost_usd=0.50, **CLAUDE_TOKENS)

    writer.close()
    reading = connect(path)
    rows = lead_split(reading, PROJECT)
    reading.close()
    sonnet_rows = [r for r in rows if r.agent == SONNET]
    assert len(sonnet_rows) == 1
    s = sonnet_rows[0]
    assert s.first_time == 1
    assert s.step_ups == 0


def test_failed_then_opus_pass_is_step_up_with_opus_dollars(tmp_path):
    """F179 D1: a failed Sonnet attempt then a passed Opus job is Sonnet's,
    not first time, 1 step-up, with Opus dollars in Sonnet's dollars."""
    path = tmp_path / "stepup.sqlite"
    writer = metrics.open_db(path)
    project = metrics.upsert_project(writer, PROJECT)
    f1 = metrics.upsert_milestone(writer, project, "f1", started="2026-10-01T09:00:00+02:00")
    run = metrics.upsert_run(writer, project, "20261001-100000")

    # Opus d3 leads for mean
    t0 = metrics.upsert_ticket(
        writer,
        project,
        "f1-00-lead",
        milestone_id=f1,
        kind="lead",
        difficulty=3,
        state="done",
        merged_by=OPUS,
        commit="0" * 40,
    )
    _job(writer, run, f1, t0, "lead-ticket", OPUS, 1, "passed", cost_usd=1.70, **CLAUDE_TOKENS)

    # Sonnet ticket: failed attempt then Opus step-up
    t1 = metrics.upsert_ticket(
        writer,
        project,
        "f1-01-lead",
        milestone_id=f1,
        kind="lead",
        difficulty=3,
        state="done",
        merged_by=OPUS,
        commit="a" * 40,
    )
    _job(writer, run, f1, t1, "lead-ticket", SONNET, 1, "failed", cost_usd=0.30, **CLAUDE_TOKENS)
    _job(writer, run, f1, t1, "lead-ticket", OPUS, 2, "passed", cost_usd=1.20, **CLAUDE_TOKENS)

    writer.close()
    reading = connect(path)
    rows = lead_split(reading, PROJECT)
    reading.close()
    sonnet_rows = [r for r in rows if r.agent == SONNET]
    assert len(sonnet_rows) == 1
    s = sonnet_rows[0]
    assert s.first_time == 0
    assert s.step_ups == 1
    # Sonnet's dollars include both its own and Opus's step-up
    assert s.dollars == pytest.approx(0.30 + 1.20)


def test_unknown_difficulty_takes_opus_overall_mean(tmp_path):
    """F179 D2: a difficulty Opus never did takes Opus's mean over all its lead tickets."""
    path = tmp_path / "unknown_diff.sqlite"
    writer = metrics.open_db(path)
    project = metrics.upsert_project(writer, PROJECT)
    f1 = metrics.upsert_milestone(writer, project, "f1", started="2026-10-01T09:00:00+02:00")
    run = metrics.upsert_run(writer, project, "20261001-100000")

    # Opus leads: d3 ($1.60), d4 ($2.00) → overall mean = (1.60 + 2.00) / 2 = 1.80
    t0 = metrics.upsert_ticket(
        writer,
        project,
        "f1-00-lead",
        milestone_id=f1,
        kind="lead",
        difficulty=3,
        state="done",
        merged_by=OPUS,
        commit="0" * 40,
    )
    _job(writer, run, f1, t0, "lead-ticket", OPUS, 1, "passed", cost_usd=1.60, **CLAUDE_TOKENS)
    t0b = metrics.upsert_ticket(
        writer,
        project,
        "f1-00b-lead",
        milestone_id=f1,
        kind="lead",
        difficulty=4,
        state="done",
        merged_by=OPUS,
        commit="0b" * 40,
    )
    _job(writer, run, f1, t0b, "lead-ticket", OPUS, 1, "passed", cost_usd=2.00, **CLAUDE_TOKENS)

    # Sonnet ticket: d5 (difficulty Opus never did)
    t1 = metrics.upsert_ticket(
        writer,
        project,
        "f1-01-lead",
        milestone_id=f1,
        kind="lead",
        difficulty=5,
        state="done",
        merged_by=SONNET,
        commit="a" * 40,
    )
    _job(writer, run, f1, t1, "lead-ticket", SONNET, 1, "passed", cost_usd=0.50, **CLAUDE_TOKENS)

    writer.close()
    reading = connect(path)
    rows = lead_split(reading, PROJECT)
    reading.close()
    sonnet_rows = [r for r in rows if r.agent == SONNET]
    assert len(sonnet_rows) == 1
    s = sonnet_rows[0]
    assert s.band == "difficulty 5 and up"
    # Opus's overall mean = (1.60 + 2.00) / 2 = 1.80
    assert s.would_have == pytest.approx(1.80)
    assert s.saved == pytest.approx(1.80 - 0.50)


def test_unknown_difficulty_uses_ticket_mean_not_difficulty_mean(tmp_path):
    """F179 D2: when difficulties have different ticket counts, the fallback
    averages across Opus tickets, not difficulty-level means equally."""
    path = tmp_path / "skew.sqlite"
    writer = metrics.open_db(path)
    project = metrics.upsert_project(writer, PROJECT)
    f1 = metrics.upsert_milestone(writer, project, "f1", started="2026-10-01T09:00:00+02:00")
    run = metrics.upsert_run(writer, project, "20261001-100000")

    # Opus: two d3 tickets ($1.00, $2.00) and one d4 ticket ($6.00)
    # Per-difficulty means: d3=$1.50, d4=$6.00 → equal-weighted mean = $3.75 (wrong)
    # Ticket-level mean: ($1.00+$2.00+$6.00)/3 = $3.00 (correct)
    t0 = metrics.upsert_ticket(
        writer,
        project,
        "f1-00-lead",
        milestone_id=f1,
        kind="lead",
        difficulty=3,
        state="done",
        merged_by=OPUS,
        commit="0" * 40,
    )
    _job(writer, run, f1, t0, "lead-ticket", OPUS, 1, "passed", cost_usd=1.00, **CLAUDE_TOKENS)
    t0b = metrics.upsert_ticket(
        writer,
        project,
        "f1-00b-lead",
        milestone_id=f1,
        kind="lead",
        difficulty=3,
        state="done",
        merged_by=OPUS,
        commit="0b" * 40,
    )
    _job(writer, run, f1, t0b, "lead-ticket", OPUS, 1, "passed", cost_usd=2.00, **CLAUDE_TOKENS)
    t0c = metrics.upsert_ticket(
        writer,
        project,
        "f1-00c-lead",
        milestone_id=f1,
        kind="lead",
        difficulty=4,
        state="done",
        merged_by=OPUS,
        commit="0c" * 40,
    )
    _job(writer, run, f1, t0c, "lead-ticket", OPUS, 1, "passed", cost_usd=6.00, **CLAUDE_TOKENS)

    # Sonnet ticket: d5 (difficulty Opus never did)
    t1 = metrics.upsert_ticket(
        writer,
        project,
        "f1-01-lead",
        milestone_id=f1,
        kind="lead",
        difficulty=5,
        state="done",
        merged_by=SONNET,
        commit="a" * 40,
    )
    _job(writer, run, f1, t1, "lead-ticket", SONNET, 1, "passed", cost_usd=0.50, **CLAUDE_TOKENS)

    writer.close()
    reading = connect(path)
    rows = lead_split(reading, PROJECT)
    reading.close()
    sonnet_rows = [r for r in rows if r.agent == SONNET]
    assert len(sonnet_rows) == 1
    s = sonnet_rows[0]
    # Ticket-level mean: (1.00 + 2.00 + 6.00) / 3 = 3.00, not difficulty-level mean
    assert s.would_have == pytest.approx(3.00)
    assert s.saved == pytest.approx(3.00 - 0.50)


def test_ticket_with_no_difficulty_is_in_no_row(tmp_path):
    """A ticket with no difficulty is in no row."""
    path = tmp_path / "no_diff.sqlite"
    writer = metrics.open_db(path)
    project = metrics.upsert_project(writer, PROJECT)
    f1 = metrics.upsert_milestone(writer, project, "f1", started="2026-10-01T09:00:00+02:00")
    run = metrics.upsert_run(writer, project, "20261001-100000")

    t0 = metrics.upsert_ticket(
        writer,
        project,
        "f1-00-lead",
        milestone_id=f1,
        kind="lead",
        difficulty=3,
        state="done",
        merged_by=OPUS,
        commit="0" * 40,
    )
    _job(writer, run, f1, t0, "lead-ticket", OPUS, 1, "passed", cost_usd=1.70, **CLAUDE_TOKENS)

    # Sonnet ticket with no difficulty
    t1 = metrics.upsert_ticket(
        writer,
        project,
        "f1-01-lead",
        milestone_id=f1,
        kind="lead",
        state="done",
        merged_by=SONNET,
        commit="a" * 40,
    )
    _job(writer, run, f1, t1, "lead-ticket", SONNET, 1, "passed", cost_usd=0.50, **CLAUDE_TOKENS)

    writer.close()
    reading = connect(path)
    rows = lead_split(reading, PROJECT)
    reading.close()
    sonnet_rows = [r for r in rows if r.agent == SONNET]
    assert len(sonnet_rows) == 0


def test_reviewed_counts_passed_review_job_and_findings(tmp_path):
    """Reviewed counts a ticket whose milestone has a passed review job;
    should-fix and blocking count its findings."""
    path = tmp_path / "reviewed.sqlite"
    writer = metrics.open_db(path)
    project = metrics.upsert_project(writer, PROJECT)
    f1 = metrics.upsert_milestone(writer, project, "f1", started="2026-10-01T09:00:00+02:00")
    run = metrics.upsert_run(writer, project, "20261001-100000")

    t0 = metrics.upsert_ticket(
        writer,
        project,
        "f1-00-lead",
        milestone_id=f1,
        kind="lead",
        difficulty=3,
        state="done",
        merged_by=OPUS,
        commit="0" * 40,
    )
    _job(writer, run, f1, t0, "lead-ticket", OPUS, 1, "passed", cost_usd=1.70, **CLAUDE_TOKENS)

    # Sonnet ticket with review findings
    t1 = metrics.upsert_ticket(
        writer,
        project,
        "f1-01-lead",
        milestone_id=f1,
        kind="lead",
        difficulty=3,
        state="done",
        merged_by=SONNET,
        commit="a" * 40,
    )
    _job(writer, run, f1, t1, "lead-ticket", SONNET, 1, "passed", cost_usd=0.50, **CLAUDE_TOKENS)

    # Add a review job and findings on the milestone
    review = _job(writer, run, f1, None, "review", OPUS, 1, "passed", cost_usd=1.0, **CLAUDE_TOKENS)
    metrics.add_finding(writer, f1, "F1", ticket_id=t1, job_id=review, severity="should-fix")
    metrics.add_finding(writer, f1, "F2", ticket_id=t1, job_id=review, severity="blocking")
    metrics.add_finding(writer, f1, "F3", ticket_id=t1, job_id=review, severity="nit")

    writer.close()
    reading = connect(path)
    rows = lead_split(reading, PROJECT)
    reading.close()
    sonnet_rows = [r for r in rows if r.agent == SONNET]
    assert len(sonnet_rows) == 1
    s = sonnet_rows[0]
    assert s.reviewed == 1
    assert s.should_fix == 1
    assert s.blocking == 1


def test_key_keeps_one_milestones_tickets(tmp_path):
    """key keeps one milestone's tickets."""
    path = tmp_path / "key.sqlite"
    writer = metrics.open_db(path)
    project = metrics.upsert_project(writer, PROJECT)
    f1 = metrics.upsert_milestone(writer, project, "f1", started="2026-10-01T09:00:00+02:00")
    f2 = metrics.upsert_milestone(writer, project, "f2", started="2026-10-05T09:00:00+02:00")
    run1 = metrics.upsert_run(writer, project, "20261001-100000")
    run2 = metrics.upsert_run(writer, project, "20261005-100000")

    # f1: Sonnet d3
    t1 = metrics.upsert_ticket(
        writer,
        project,
        "f1-01-lead",
        milestone_id=f1,
        kind="lead",
        difficulty=3,
        state="done",
        merged_by=SONNET,
        commit="a" * 40,
    )
    _job(writer, run1, f1, t1, "lead-ticket", SONNET, 1, "passed", cost_usd=0.50, **CLAUDE_TOKENS)

    # f2: Sonnet d3
    t2 = metrics.upsert_ticket(
        writer,
        project,
        "f2-01-lead",
        milestone_id=f2,
        kind="lead",
        difficulty=3,
        state="done",
        merged_by=SONNET,
        commit="b" * 40,
    )
    _job(writer, run2, f2, t2, "lead-ticket", SONNET, 1, "passed", cost_usd=0.60, **CLAUDE_TOKENS)

    writer.close()
    reading = connect(path)
    # Without key: both milestones
    all_rows = lead_split(reading, PROJECT)
    assert len(all_rows) == 1
    assert all_rows[0].tickets == 2
    # With key: only f1's ticket
    f1_rows = lead_split(reading, PROJECT, key="f1")
    assert len(f1_rows) == 1
    assert f1_rows[0].tickets == 1
    reading.close()


def test_start_and_end_keep_tickets_by_first_job_started(tmp_path):
    """start and end keep tickets whose first job started in them."""
    path = tmp_path / "time.sqlite"
    writer = metrics.open_db(path)
    project = metrics.upsert_project(writer, PROJECT)
    f1 = metrics.upsert_milestone(writer, project, "f1", started="2026-10-01T09:00:00+02:00")
    run = metrics.upsert_run(writer, project, "20261001-100000")

    # Opus d3 lead at 09:00
    t0 = metrics.upsert_ticket(
        writer,
        project,
        "f1-00-lead",
        milestone_id=f1,
        kind="lead",
        difficulty=3,
        state="done",
        merged_by=OPUS,
        commit="0" * 40,
    )
    job0 = metrics.start_job(
        writer,
        run,
        ticket_id=t0,
        milestone_id=f1,
        role="lead-ticket",
        agent=OPUS,
        attempt=1,
        started="2026-10-01T09:00:00+02:00",
    )
    metrics.finish_job(
        writer,
        job0,
        ended="2026-10-01T09:10:00+02:00",
        outcome="passed",
        cost_usd=1.70,
        tokens_in=10_000,
        tokens_cached=100_000,
        tokens_out=2_000,
    )

    # Sonnet d3 lead at 10:00
    t1 = metrics.upsert_ticket(
        writer,
        project,
        "f1-01-lead",
        milestone_id=f1,
        kind="lead",
        difficulty=3,
        state="done",
        merged_by=SONNET,
        commit="a" * 40,
    )
    job1 = metrics.start_job(
        writer,
        run,
        ticket_id=t1,
        milestone_id=f1,
        role="lead-ticket",
        agent=SONNET,
        attempt=1,
        started="2026-10-01T10:00:00+02:00",
    )
    metrics.finish_job(
        writer,
        job1,
        ended="2026-10-01T10:10:00+02:00",
        outcome="passed",
        cost_usd=0.50,
        tokens_in=10_000,
        tokens_cached=100_000,
        tokens_out=2_000,
    )

    writer.close()
    reading = connect(path)
    # Both tickets
    all_rows = lead_split(reading, PROJECT)
    assert len(all_rows) == 2
    # Only Sonnet's ticket (started at 10:00)
    sonnet_rows = lead_split(reading, PROJECT, start="2026-10-01T10:00:00+02:00")
    assert len(sonnet_rows) == 1
    assert sonnet_rows[0].agent == SONNET
    # end: tickets whose first job started <= end
    early_rows = lead_split(reading, PROJECT, end="2026-10-01T09:30:00+02:00")
    assert len(early_rows) == 1
    assert early_rows[0].agent == OPUS
    # end at exactly Sonnet's start includes both
    both_rows = lead_split(reading, PROJECT, end="2026-10-01T10:00:00+02:00")
    assert len(both_rows) == 2
    # end before Opus's start excludes all
    too_early_rows = lead_split(reading, PROJECT, end="2026-10-01T08:59:59+02:00")
    assert len(too_early_rows) == 0
    reading.close()


def test_opus_rows_have_no_would_have_or_saved(tmp_path):
    """Opus's own rows have no would-have and no saving."""
    gen = _lead_db(tmp_path)
    conn = next(gen)
    rows = lead_split(conn, PROJECT)
    opus_rows = [r for r in rows if r.agent == OPUS]
    assert len(opus_rows) == 1
    o = opus_rows[0]
    assert o.would_have == 0.0
    assert o.saved == 0.0


def test_no_lead_ticket_returns_empty_list(tmp_path):
    """A project with no lead ticket returns []."""
    path = tmp_path / "no_lead.sqlite"
    writer = metrics.open_db(path)
    project = metrics.upsert_project(writer, PROJECT)
    f1 = metrics.upsert_milestone(writer, project, "f1", started="2026-10-01T09:00:00+02:00")
    # Only developer tickets, no lead tickets
    t = metrics.upsert_ticket(
        writer, project, "f1-01-dev", milestone_id=f1, kind="developer", difficulty=3, state="done"
    )
    run = metrics.upsert_run(writer, project, "20261001-100000")
    _job(writer, run, f1, t, "developer", SONNET, 1, "passed", cost_usd=0.50, **CLAUDE_TOKENS)
    writer.close()
    reading = connect(path)
    rows = lead_split(reading, PROJECT)
    assert rows == []
    reading.close()


def test_lead_rates_includes_lead_ticket_without_jobs_in_denominator(tmp_path):
    """A lead ticket with no jobs still contributes its lines to the rate denominator."""
    from factory_dashboard.queries import _lead_rates, connect

    writer = metrics.open_db(tmp_path / "factory-metrics.sqlite")
    project_id = metrics.upsert_project(writer, PROJECT)
    f1 = metrics.upsert_milestone(writer, project_id, "f1")
    run = metrics.upsert_run(writer, project_id, "20261001-100000")

    # Lead ticket 1: d3, 100 lines, with a $1.70 job
    t1 = metrics.upsert_ticket(
        writer,
        project_id,
        "f1-01-lead",
        milestone_id=f1,
        kind="lead",
        state="done",
        difficulty=3,
        merged_by=OPUS,
        commit="a" * 40,
        lines_changed=100,
    )
    _job(
        writer,
        run,
        f1,
        t1,
        "lead-ticket",
        OPUS,
        1,
        "passed",
        cost_usd=1.70,
        **CLAUDE_TOKENS,
    )

    # Lead ticket 2: d3, 50 lines, NO jobs at all
    metrics.upsert_ticket(
        writer,
        project_id,
        "f1-02-lead",
        milestone_id=f1,
        kind="lead",
        state="done",
        difficulty=3,
        merged_by=OPUS,
        commit="b" * 40,
        lines_changed=50,
    )

    # Developer ticket: d4, should NOT be included in lead rates
    dev = metrics.upsert_ticket(
        writer,
        project_id,
        "f1-03-dev",
        milestone_id=f1,
        kind="developer",
        state="done",
        difficulty=4,
        merged_by=LOCAL,
        commit="c" * 40,
        lines_changed=200,
    )
    _job(
        writer,
        run,
        f1,
        dev,
        "developer",
        LOCAL,
        1,
        "passed",
        tokens_in=10_000,
        tokens_out=1_000,
    )

    writer.close()
    conn = connect(tmp_path / "factory-metrics.sqlite")
    rates = _lead_rates(conn, project_id)
    conn.close()

    # d3: $1.70 / (100 + 50) lines = $0.01133... per line
    # d4 should not appear (developer ticket)
    assert 3 in rates
    assert rates[3][0] == pytest.approx(1.70 / 150)
    assert 4 not in rates


def test_lead_rates_runs_one_query_with_many_lead_tickets(db, tmp_path):
    """_lead_rates runs one SQL statement regardless of how many lead tickets there are."""
    from factory_dashboard.queries import _lead_rates, connect

    writer = metrics.open_db(tmp_path / "factory-metrics.sqlite")
    project_id = metrics.upsert_project(writer, PROJECT)
    f1 = metrics.upsert_milestone(writer, project_id, "f1")
    run = metrics.upsert_run(writer, project_id, "20261001-100000")
    # Create 10 lead tickets with their jobs
    for i in range(1, 11):
        ticket = metrics.upsert_ticket(
            writer,
            project_id,
            f"f1-lead-{i:02d}",
            milestone_id=f1,
            kind="lead",
            state="done",
            difficulty=4,
            merged_by=OPUS,
            commit="a" * 40,
            lines_changed=100,
        )
        _job(
            writer,
            run,
            f1,
            ticket,
            "lead-ticket",
            OPUS,
            1,
            "passed",
            cost_usd=3.0,
            **CLAUDE_TOKENS,
        )
    writer.close()
    conn = connect(tmp_path / "factory-metrics.sqlite")
    queries_executed: list[str] = []
    conn.set_trace_callback(lambda q: queries_executed.append(q))
    _lead_rates(conn, project_id)
    conn.close()
    assert len(queries_executed) == 1


def test_trends_runs_same_sql_count_with_one_or_ten_leads(db, tmp_path):
    """trends runs the same number of SQL statements with 1 lead ticket as with 10."""
    from factory_dashboard.queries import connect, trends

    # First: count queries with 10 lead tickets
    writer = metrics.open_db(tmp_path / "factory-metrics-10.sqlite")
    project_id = metrics.upsert_project(writer, PROJECT)
    f1 = metrics.upsert_milestone(writer, project_id, "f1")
    run = metrics.upsert_run(writer, project_id, "20261001-100000")
    for i in range(1, 11):
        ticket = metrics.upsert_ticket(
            writer,
            project_id,
            f"f1-lead-{i:02d}",
            milestone_id=f1,
            kind="lead",
            state="done",
            difficulty=4,
            merged_by=OPUS,
            commit="a" * 40,
            lines_changed=100,
        )
        _job(
            writer,
            run,
            f1,
            ticket,
            "lead-ticket",
            OPUS,
            1,
            "passed",
            cost_usd=3.0,
            **CLAUDE_TOKENS,
        )
    writer.close()
    conn = connect(tmp_path / "factory-metrics-10.sqlite")
    queries_executed: list[str] = []
    conn.set_trace_callback(lambda q: queries_executed.append(q))
    trends(conn, PROJECT)
    count_10 = len(queries_executed)
    conn.close()

    # Second: count queries with 1 lead ticket (same milestone structure)
    writer2 = metrics.open_db(tmp_path / "factory-metrics-1.sqlite")
    project_id2 = metrics.upsert_project(writer2, PROJECT)
    f1_2 = metrics.upsert_milestone(writer2, project_id2, "f1")
    run2 = metrics.upsert_run(writer2, project_id2, "20261001-100000")
    ticket2 = metrics.upsert_ticket(
        writer2,
        project_id2,
        "f1-lead-01",
        milestone_id=f1_2,
        kind="lead",
        state="done",
        difficulty=4,
        merged_by=OPUS,
        commit="a" * 40,
        lines_changed=100,
    )
    _job(
        writer2,
        run2,
        f1_2,
        ticket2,
        "lead-ticket",
        OPUS,
        1,
        "passed",
        cost_usd=3.0,
        **CLAUDE_TOKENS,
    )
    writer2.close()
    conn2 = connect(tmp_path / "factory-metrics-1.sqlite")
    queries_executed2: list[str] = []
    conn2.set_trace_callback(lambda q: queries_executed2.append(q))
    trends(conn2, PROJECT)
    count_1 = len(queries_executed2)
    conn2.close()
    assert count_1 == count_10
