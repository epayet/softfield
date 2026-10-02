import sqlite3

import pytest

from factory_dashboard.queries import (
    SEED_DOLLARS_PER_LINE,
    connect,
    eligibility,
    milestone_results,
    savings,
    trends,
)
from runner import metrics
from tests.factory_dashboard.conftest import LOCAL, OPUS, PROJECT, SONNET


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


def test_trends_run_oldest_first(db):
    points = trends(db, PROJECT)
    assert [p.results.key for p in points] == ["m4", "f1"]
    assert points[0].results.pass_rate == 1.0
    assert points[1].savings.net == pytest.approx(-2.70)


SHADOW, OTHER_SHADOW = "copilot-auto", "copilot-gpt"


def _shadows(db_path) -> sqlite3.Connection:
    """Two shadows of the checkpoint (ADR 14 item 12) on top of the fixture: copilot-auto
    shadowed f1 only (its m4 shadow was refused); copilot-gpt shadowed f1 and m4. Both are
    rated 8.5 by their latest change, whatever its skill."""
    writer = metrics.open_db(db_path)
    project = metrics.upsert_project(writer, PROJECT)
    run = metrics.upsert_run(writer, project, "20260930-100000")
    shadows = (
        (SHADOW, "f1", "passed"),
        (SHADOW, "m4", "refused"),
        (OTHER_SHADOW, "f1", "passed"),
        (OTHER_SHADOW, "m4", "passed"),
    )
    for attempt, (agent, milestone, outcome) in enumerate(shadows, start=1):
        job = metrics.start_job(
            writer,
            run,
            ticket_id=None,
            milestone_id=metrics.upsert_milestone(writer, project, milestone),
            role="checkpoint-shadow",
            agent=agent,
            attempt=attempt,  # one run: the jobs' key needs them apart
            started="2026-09-30T10:30:00+02:00",
        )
        metrics.finish_job(writer, job, ended="2026-09-30T10:31:00+02:00", outcome=outcome)
    for agent in (SHADOW, OTHER_SHADOW):
        metrics.add_rating_change(writer, agent, "reviewing", 6, 9, at="2026-09-30T11:00:00+02:00")
        metrics.add_rating_change(writer, agent, "coding", 6, 8.5, at="2026-09-30T12:00:00+02:00")
    writer.commit()
    return writer


def test_eligibility_says_no_with_its_reason_for_one_milestone(db, db_path):
    _shadows(db_path).close()
    found = {(e.agent, e.role): e for e in eligibility(db, PROJECT)}
    assert set(found) == {(SHADOW, "checkpoint"), (OTHER_SHADOW, "checkpoint")}
    one = found[SHADOW, "checkpoint"]
    assert not one.eligible
    assert one.reason == "shadowed 1 milestone, needs 2"


def test_eligibility_says_yes_for_an_agent_meeting_every_bar(db, db_path):
    _shadows(db_path).close()
    both = next(e for e in eligibility(db, PROJECT) if e.agent == OTHER_SHADOW)
    assert both.eligible
    # f1's tickets go up to d5, m4's is d2: rated 8.5 covers them
    assert both.reason == (
        "rated 8.5 over 2 milestones, no missed blocking finding, tickets up to difficulty 5"
    )


def test_eligibility_names_every_bar_it_misses(db, db_path):
    writer = _shadows(db_path)
    project = metrics.upsert_project(writer, PROJECT)
    m4 = metrics.upsert_milestone(writer, project, "m4")
    metrics.add_finding(writer, m4, "m4-F9", severity="blocking", verdict="missed")
    metrics.add_rating_change(
        writer, OTHER_SHADOW, "coding", 8.5, 4, at="2026-09-30T13:00:00+02:00"
    )
    metrics.upsert_ticket(writer, project, "f1-01-first", difficulty_corrected=9)
    writer.commit()
    writer.close()
    both = next(e for e in eligibility(db, PROJECT) if e.agent == OTHER_SHADOW)
    assert not both.eligible
    assert both.reason == (
        "rated 4, needs 8; 1 missed blocking finding; rated 4, below difficulty 9 of a ticket"
        " it reviewed"
    )


def test_eligibility_without_a_rating_says_so(db, db_path):
    writer = _shadows(db_path)
    writer.execute("DELETE FROM rating_changes WHERE agent = ?", (OTHER_SHADOW,))
    writer.commit()
    writer.close()
    both = next(e for e in eligibility(db, PROJECT) if e.agent == OTHER_SHADOW)
    assert (both.eligible, both.reason) == (False, "no rating yet")


def test_the_connection_is_read_only(db):
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        db.execute("DELETE FROM jobs")


def test_connect_refuses_a_missing_database(tmp_path):
    with pytest.raises(sqlite3.OperationalError):
        connect(tmp_path / "nothing.sqlite")
