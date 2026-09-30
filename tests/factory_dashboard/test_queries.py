import sqlite3

import pytest

from factory_dashboard.queries import (
    SEED_DOLLARS_PER_LINE,
    connect,
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


def test_the_connection_is_read_only(db):
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        db.execute("DELETE FROM jobs")


def test_connect_refuses_a_missing_database(tmp_path):
    with pytest.raises(sqlite3.OperationalError):
        connect(tmp_path / "nothing.sqlite")
