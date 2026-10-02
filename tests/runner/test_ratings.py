from datetime import UTC, datetime, timedelta

import pytest

from runner import loop, metrics
from runner.agents import Agent
from runner.ratings import (
    CODING,
    REVIEWING,
    Attempt,
    Game,
    Judged,
    expected,
    judged_games,
    may_review,
    moments,
    rate,
    ticket_games,
)

ESTABLISHED = {"a": ["t1", "t2", "t3", "t4", "t5"]}  # past its provisional tickets
AT = datetime(2026, 10, 2, 12, 0, tzinfo=UTC)


def test_a_two_point_lead_expects_three_quarters():
    assert expected(5, 5) == pytest.approx(0.5)
    assert expected(7, 5) == pytest.approx(0.75)
    assert expected(3, 5) == pytest.approx(0.25)


@pytest.mark.parametrize(
    ("case", "rating", "difficulty", "result", "played", "after"),
    [
        ("an expected result barely moves it", 7, 3, 1.0, ESTABLISHED, 7.1),
        ("beating a hard ticket raises it a lot", 4, 8, 1.0, ESTABLISHED, 4.9),
        ("failing an easy one drops it a lot", 8, 4, 0.0, ESTABLISHED, 7.1),
        ("merged later, at par", 5, 5, 0.5, ESTABLISHED, 5.0),
        ("a provisional agent moves twice as fast", 5, 5, 1.0, {}, 6.0),
        ("established, the same game moves half as much", 5, 5, 1.0, ESTABLISHED, 5.5),
        ("never above 10", 9.8, 10, 1.0, {}, 10.0),
        ("never below 1", 1.2, 1, 0.0, {}, 1.0),
    ],
)
def test_a_coding_game(case, rating, difficulty, result, played, after):
    [change] = rate({"a": rating}, played, [Game("a", CODING, "t9", difficulty, result, "x")])
    assert change.before == rating, case
    assert change.after == pytest.approx(after), case


def test_a_confirmed_finding_lowers_the_tickets_result_by_a_quarter():
    [change] = rate({"a": 6}, ESTABLISHED, [Game("a", CODING, "t9", None, -0.25, "finding F1")])
    assert change.after == pytest.approx(5.75)


@pytest.mark.parametrize(("earlier", "step"), [(0, 1.0), (4, 1.0), (5, 0.5)])
def test_the_provisional_k_lasts_five_tickets(earlier, step):
    played = {"a": [f"t{n}" for n in range(earlier)]}
    [change] = rate({"a": 5}, played, [Game("a", CODING, "t9", 5, 1.0, "x")])
    assert change.after - change.before == pytest.approx(step)


def test_several_games_on_one_ticket_count_it_once():
    games = [Game("a", REVIEWING, "t9", 5, 1.0, f"confirmed F{n}") for n in range(6)]
    last = rate({"a": 5}, {}, games)[-1]
    k = (last.after - last.before) / (1 - expected(last.before, 5))
    assert k == pytest.approx(2)  # still provisional: one ticket played


def test_games_follow_each_other_and_leave_other_agents_alone():
    games = [Game("a", CODING, "t1", 5, 1.0, "x"), Game("a", CODING, "t2", 5, 1.0, "x")]
    first, second = rate({"a": 5, "b": 3}, {}, games)
    assert second.before == first.after
    assert {c.agent for c in (first, second)} == {"a"}


def test_an_agent_with_no_starting_rating_is_left_out():
    assert rate({}, {}, [Game("unknown", CODING, "t1", 5, 1.0, "x")]) == []


# --- tickets ----------------------------------------------------------------------------


def results(games):
    return [(g.agent, g.result, g.label) for g in games]


def test_merged_at_the_first_attempt_wins():
    games = ticket_games("t1", 5, [Attempt("local", merged=True)])
    assert results(games) == [("local", 1.0, "merged at the first attempt")]


def test_merged_later_draws_once_for_its_agent():
    games = ticket_games("t1", 5, [Attempt("local"), Attempt("local", merged=True)])
    assert results(games) == [("local", 0.5, "merged later")]


def test_a_two_agent_ticket_gives_the_merger_its_result_and_the_earlier_developer_a_loss():
    attempts = [Attempt("local"), Attempt("local"), Attempt("claude-sonnet", merged=True)]
    games = ticket_games("t1", 6, attempts)
    assert results(games) == [
        ("local", 0.0, "not merged"),
        ("claude-sonnet", 1.0, "merged at the first attempt"),
    ]
    assert {(g.skill, g.difficulty, g.ticket) for g in games} == {(CODING, 6, "t1")}


def test_a_ticket_never_merged_is_a_loss_for_every_agent_once():
    games = ticket_games("t1", 4, [Attempt("local"), Attempt("local"), Attempt("ollama")])
    assert results(games) == [("local", 0.0, "not merged"), ("ollama", 0.0, "not merged")]


# --- reviews ----------------------------------------------------------------------------


def judged(verdict, reviewer="claude-sonnet", author="local", key="f1-C3-F1"):
    return Judged(key, "t1", 6, verdict, reviewer, author)


def test_a_confirmed_finding_raises_the_reviewer_and_costs_the_author_a_quarter():
    games = judged_games([judged("confirmed")])
    assert [(g.agent, g.skill, g.difficulty, g.result, g.label) for g in games] == [
        ("claude-sonnet", REVIEWING, 6, 1.0, "confirmed f1-C3-F1"),
        ("local", CODING, None, -0.25, "finding f1-C3-F1"),
    ]


def test_a_rejected_finding_lowers_the_reviewer_and_spares_the_author():
    games = judged_games([judged("rejected")])
    assert [(g.agent, g.result, g.label) for g in games] == [
        ("claude-sonnet", 0.0, "rejected f1-C3-F1")
    ]


def test_a_missed_finding_is_a_loss_for_the_reviewer_and_a_finding_on_the_code():
    games = judged_games([judged("missed", key="F2")])
    assert [(g.agent, g.result, g.label) for g in games] == [
        ("claude-sonnet", 0.0, "missed F2"),
        ("local", -0.25, "finding F2"),
    ]


def test_a_finding_with_no_difficulty_or_no_reviewer_moves_no_reviewer():
    no_difficulty = Judged("F1", "t1", None, "confirmed", "claude-sonnet", "local")
    no_reviewer = Judged("F2", "t1", 6, "missed", None, None)
    assert judged_games([no_difficulty, no_reviewer]) == [
        Game("local", CODING, "t1", None, -0.25, "finding F1")
    ]


def test_reviews_move_the_same_rating_as_coding():
    games = [
        Game("claude-sonnet", CODING, "t1", 7, 1.0, "merged at the first attempt"),
        *judged_games([judged("confirmed"), judged("rejected", key="f1-C3-F2")]),
    ]
    coded, confirmed, _penalty, rejected = rate({"claude-sonnet": 7, "local": 5}, {}, games)
    assert confirmed.before == coded.after and confirmed.after > confirmed.before
    assert rejected.before == confirmed.after and rejected.after < rejected.before
    assert (confirmed.skill, rejected.skill) == (REVIEWING, REVIEWING)


# --- who may review whom (ADR 15 item 9) -------------------------------------------------

SONNET = Agent("claude-sonnet", "claude", "sonnet", 7)
OPUS = Agent("claude-opus", "claude", "opus", 9)
COPILOT_OPUS = Agent("copilot-claude-opus", "copilot", "claude-opus-4.5", 8)
COPILOT_AUTO = Agent("copilot-auto", "copilot", "auto", 6)
LOCAL = Agent("local-qwen3.6-35b-a3b", "opencode", "lmstudio/qwen/qwen3.6-35b-a3b", 5)
GPT_OSS = Agent("ollama-gpt-oss-120b", "opencode", "ollama/gpt-oss:120b-cloud", 6)


@pytest.mark.parametrize(
    ("reviewer", "author", "ok"),
    [
        (SONNET, SONNET, False),
        (OPUS, SONNET, True),
        (SONNET, LOCAL, True),
        (COPILOT_OPUS, OPUS, False),  # the model, not the harness
        (COPILOT_OPUS, SONNET, True),
        (GPT_OSS, LOCAL, True),
        (GPT_OSS, Agent("x-gpt-oss", "other", "gpt-oss:120b", 6), False),
        (COPILOT_AUTO, LOCAL, False),  # whatever Copilot picks: it may be the author's model
    ],
)
def test_a_reviewer_is_another_model(reviewer, author, ok):
    assert may_review(reviewer, author) is ok


def test_moments_keep_changes_of_one_moment_apart():
    stamps = moments(AT, 3)
    assert len(set(stamps)) == 3 and stamps == sorted(stamps)
    assert stamps[0] == AT.isoformat()


# --- the runner's side: reading the database and writing the changes -----------------------

START = {"local": 5, "claude-opus": 9, "claude-sonnet": 7}


@pytest.fixture
def db(tmp_path):
    conn = metrics.open_db(tmp_path / "metrics.sqlite")
    yield conn
    conn.close()


def _ticket(conn, ticket, *, milestone="f1", difficulty=5, merged_by=None, state="done", jobs=()):
    project = metrics.upsert_project(conn, "coucou")
    milestone_id = metrics.upsert_milestone(conn, project, milestone)
    run = metrics.upsert_run(conn, project, "run-1")
    ticket_id = metrics.upsert_ticket(
        conn,
        project,
        ticket,
        milestone_id=milestone_id,
        difficulty=difficulty,
        merged_by=merged_by,
        state=state,
    )
    for n, (agent, role, outcome, ended, *note) in enumerate(jobs, start=1):
        job = metrics.start_job(
            conn,
            run,
            ticket_id=ticket_id,
            milestone_id=milestone_id,
            role=role,
            agent=agent,
            attempt=n,
            started=ended,
        )
        metrics.finish_job(conn, job, ended=ended, outcome=outcome, note=note[0] if note else None)
    return project, ticket_id


def _changes(conn):
    return [
        (r["agent"], r["skill"], r["before"], round(r["after"], 3), r["result"])
        for r in conn.execute("SELECT * FROM rating_changes ORDER BY at, id")
    ]


def test_a_merged_ticket_is_rated_once(db):
    project, _ = _ticket(
        db,
        "f1-01",
        merged_by="local",
        jobs=[
            ("local", "developer", "failed", "2026-10-02T10:00:00+00:00"),
            ("ollama", "developer", "failed", "2026-10-02T10:10:00+00:00", "refused"),
            ("local", "developer", "passed", "2026-10-02T10:20:00+00:00"),
        ],
    )
    loop.rate_ticket(db, project, "f1-01", START, AT)
    loop.rate_ticket(db, project, "f1-01", START, AT + timedelta(minutes=1))
    assert _changes(db) == [("local", CODING, 5.0, 5.0, "merged later")]  # a refusal isn't a loss


def test_a_finished_ticket_credits_the_lead_and_costs_the_developer(db):
    jobs = [
        ("local", role, "failed", f"2026-10-02T1{n}:00:00+00:00")
        for n, role in enumerate(("developer", "developer", "last-attempt"))
    ]
    project, _ = _ticket(db, "f1-02", difficulty=6, merged_by="claude-opus", jobs=jobs)
    loop.rate_ticket(db, project, "f1-02", START, AT)
    assert [(a, r) for a, _, _, _, r in _changes(db)] == [
        ("local", "not merged"),
        ("claude-opus", "merged at the first attempt"),
    ]


def test_a_blocked_lead_ticket_is_a_loss_for_the_lead(db):
    jobs = [("claude-opus", "lead-ticket", "passed", "2026-10-02T10:00:00+00:00")]
    project, _ = _ticket(db, "f1-03", difficulty=7, state="blocked", jobs=jobs)
    loop.rate_ticket(db, project, "f1-03", START, AT)
    [(agent, _, before, after, result)] = _changes(db)
    assert (agent, result) == ("claude-opus", "not merged") and after < before


def test_a_ticket_with_no_difficulty_is_not_rated(db):
    jobs = [("local", "developer", "passed", "2026-10-02T10:00:00+00:00")]
    project, _ = _ticket(db, "f1-04", difficulty=None, merged_by="local", jobs=jobs)
    loop.rate_ticket(db, project, "f1-04", START, AT)
    assert _changes(db) == []


def test_ratings_build_on_the_latest_change(db):
    jobs = [("local", "developer", "passed", "2026-10-02T10:00:00+00:00")]
    project, _ = _ticket(db, "f1-05", merged_by="local", jobs=jobs)
    _ticket(db, "f1-06", merged_by="local", jobs=jobs)
    loop.rate_ticket(db, project, "f1-05", START, AT)
    loop.rate_ticket(db, project, "f1-06", START, AT + timedelta(minutes=1))
    first, second = _changes(db)
    assert round(second[2], 3) == first[3]


def test_the_reviews_verdicts_are_rated_once_with_distinct_moments(db):
    jobs = [("local", "developer", "passed", "2026-10-02T10:00:00+00:00")]
    project, ticket_id = _ticket(db, "f1-07", difficulty=6, merged_by="local", jobs=jobs)
    milestone = metrics.upsert_milestone(db, project, "f1")
    for key, verdict, agent in (
        ("f1-C9-F1", "confirmed", "claude-sonnet"),
        ("f1-C9-F2", "rejected", "claude-sonnet"),
        ("F3", "missed", "claude-opus"),
        ("F4", None, "claude-opus"),  # not judged
    ):
        metrics.add_finding(db, milestone, key, ticket_id=ticket_id, verdict=verdict, agent=agent)
    loop.rate_verdicts(db, project, "f1", START, "claude-sonnet", AT)
    loop.rate_verdicts(db, project, "f1", START, "claude-sonnet", AT + timedelta(hours=1))
    assert [(a, s, r) for a, s, _, _, r in _changes(db)] == [
        ("claude-sonnet", REVIEWING, "confirmed f1-C9-F1"),
        ("local", CODING, "finding f1-C9-F1"),
        ("claude-sonnet", REVIEWING, "rejected f1-C9-F2"),
        ("claude-sonnet", REVIEWING, "missed F3"),
        ("local", CODING, "finding F3"),
    ]


def _history(db):
    """M1–M4's tickets as the backfill leaves them, plus an f1 one replay leaves alone."""
    _ticket(
        db,
        "m1-02",
        milestone="m1",
        difficulty=3,
        merged_by="local",
        jobs=[("local", "developer", "passed", "2026-09-02T10:00:00+00:00")],
    )
    _ticket(
        db,
        "m1-01",
        milestone="m1",
        difficulty=4,
        merged_by="local",
        jobs=[
            ("local", "developer", "failed", "2026-09-01T10:00:00+00:00"),
            ("local", "developer", "passed", "2026-09-01T11:00:00+00:00"),
        ],
    )
    _ticket(
        db,
        "m4-06",
        milestone="m4",
        difficulty=7,
        merged_by="claude-opus",
        jobs=[("local", "developer", "failed", "2026-09-20T10:00:00+00:00")],
    )
    return _ticket(
        db,
        "f1-01",
        merged_by="local",
        jobs=[("local", "developer", "passed", "2026-10-01T10:00:00+00:00")],
    )[0]


def test_replay_seeds_the_local_model_from_m1_to_m4_in_merge_order(db):
    project = _history(db)
    loop.replay_ratings(db, project, "local", 5)
    changes = _changes(db)
    assert [(a, r) for a, _, _, _, r in changes] == [
        ("local", "merged later"),  # m1-01, merged first
        ("local", "merged at the first attempt"),  # m1-02
        ("local", "not merged"),  # m4-06: the lead implemented it
    ]
    assert changes[0][2] == 5.0
    assert [round(c[2], 3) for c in changes[1:]] == [c[3] for c in changes[:-1]]


def test_replay_twice_gives_the_same_ratings(db):
    project = _history(db)
    loop.replay_ratings(db, project, "local", 5)
    first = _changes(db)
    loop.replay_ratings(db, project, "local", 5)
    assert _changes(db) == first
