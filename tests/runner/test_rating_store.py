"""The ratings in the metrics database (`runner/rating_store.py`): what routing reads, and the
ADR 24 recompute. A ticket's, a review's and a bench's games are in `test_ratings.py`."""

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from runner import metrics, rating_store, ratings, session
from tests.runner.test_loop import (  # noqa: F401 - _new_command and _no_probe are fixtures
    AGENTS,
    _config,
    _new_command,
    _no_probe,
    _proven,
)


def test_an_agent_routes_at_the_floor_until_its_third_game(repo, fake_clock):
    """ADR 24 item 3: with 2 games it routes as 1, with 3 as its rating."""
    _proven(repo, claude_sonnet=7)
    s = session.open_session(_config(repo))
    assert rating_store.current_ratings(s)["claude-sonnet"] == 7
    conn = metrics.open_db(_config(repo).metrics_db)
    conn.execute("DELETE FROM rating_changes WHERE id = (SELECT min(id) FROM rating_changes)")
    conn.commit()
    conn.close()
    assert rating_store.current_ratings(s)["claude-sonnet"] == 1
    assert rating_store.current_ratings(s)["claude-opus"] == 1  # an estimate of 9, never played


# --- the ADR 24 recompute (item 4; f7-02) ----------------------------------------------------

REPLAY_START = {"local": 3.0, "claude-sonnet": 7.0, "new-model": 6.0}


def _collapsed(tmp_path: Path) -> tuple[sqlite3.Connection, int]:
    """Local merges three difficulty-3 tickets first time, Sonnet two; then one review, under
    the old rules, charges local a point for each of its eight confirmed findings on two
    tickets (1.0, the floor); a bench before ADR 24 had a new model pass one first time, never
    rated."""
    conn = metrics.open_db(tmp_path / "metrics.sqlite")
    project = metrics.upsert_project(conn, "coucou")
    milestone = metrics.upsert_milestone(conn, project, "f3")
    run = metrics.upsert_run(conn, project, "run-1")
    for n, agent in enumerate(["local"] * 3 + ["claude-sonnet"] * 2):
        ticket_id = metrics.upsert_ticket(
            conn, project, f"f3-0{n}", milestone_id=milestone, difficulty=3, merged_by=agent
        )
        at = datetime(2026, 10, 1, 10 + n, tzinfo=UTC)
        job = metrics.start_job(
            conn,
            run,
            ticket_id=ticket_id,
            milestone_id=milestone,
            role="developer",
            agent=agent,
            attempt=1,
            started=at.isoformat(),
        )
        metrics.finish_job(conn, job, ended=at.isoformat(), outcome="passed")
        rating_store.rate_ticket(
            conn, project, f"f3-0{n}", REPLAY_START, at + timedelta(minutes=30)
        )
    current, _ = rating_store.standing(conn, REPLAY_START)
    for k in range(8):
        ticket_id = metrics.upsert_ticket(conn, project, f"f3-0{k // 4}")
        review = f"2026-10-02T18:57:0{k}+00:00"
        sonnet, local = current["claude-sonnet"], current["local"]
        current["claude-sonnet"], current["local"] = sonnet + 0.1, max(1.0, local - 1.0)
        for agent, skill, before, label in (
            ("claude-sonnet", ratings.REVIEWING, sonnet, f"confirmed F{k}"),
            ("local", ratings.CODING, local, f"finding F{k}"),
        ):
            metrics.add_rating_change(
                conn,
                agent,
                skill,
                before,
                current[agent],
                at=review,
                ticket_id=ticket_id,
                result=label,
            )
    bench = metrics.upsert_run(conn, project, "bench-1", command="bench")
    job = metrics.start_job(
        conn,
        bench,
        ticket_id=metrics.upsert_ticket(conn, project, "f3-02"),
        milestone_id=milestone,
        role="bench",
        agent="new-model",
        attempt=1,
        started="2026-10-03T09:00:00+00:00",
    )
    metrics.finish_job(conn, job, ended="2026-10-03T09:30:00+00:00", outcome="passed")
    return conn, project


def test_the_recompute_replays_a_collapsed_rating_to_its_game_level(tmp_path):
    conn, project = _collapsed(tmp_path)
    before, _ = rating_store.standing(conn, REPLAY_START)
    assert before["local"] == 1.0
    history = conn.execute("SELECT * FROM rating_changes ORDER BY id").fetchall()

    replayed = rating_store.replay_ratings(
        conn, project, REPLAY_START, datetime(2026, 10, 1, tzinfo=UTC)
    )

    def won(agent: str, ticket: str, skill: str = ratings.CODING, by: float = 1.0) -> ratings.Game:
        return ratings.Game(agent, skill, ticket, 3, by, "")

    # findings on f3-00 and f3-01 re-play their games a quarter lower, then (ADR 24 item 1)
    games = [won("local", f"f3-0{n}", by=0.75 if n < 2 else 1.0) for n in range(3)]
    games += [won("claude-sonnet", f"f3-0{n}") for n in (3, 4)]
    games += [won("claude-sonnet", f"f3-0{k // 4}", ratings.REVIEWING) for k in range(8)]
    games.append(won("new-model", "f3-02"))
    expected = {c.agent: c.after for c in ratings.rate(REPLAY_START, {}, games)}
    current, _ = rating_store.standing(conn, REPLAY_START)
    assert current == pytest.approx(expected)
    assert current["local"] > 3  # three wins at par, two of them a quarter lower
    assert [(r.agent, r.before, r.games, r.written) for r in replayed] == [
        ("local", 1.0, 3, True),
        ("claude-sonnet", before["claude-sonnet"], 2, True),
        ("new-model", 6.0, 1, True),
    ]
    rows = conn.execute("SELECT * FROM rating_changes ORDER BY id").fetchall()
    assert [tuple(r) for r in rows[: len(history)]] == [tuple(r) for r in history]  # kept
    new = rows[len(history) :]
    assert all(r["result"].startswith("replay ADR 24") for r in new)
    assert min(r["at"] for r in new) > max(r["at"] for r in history)  # after, though `at` is not
    assert [r["result"] for r in new if r["agent"] == "local"] == [
        "replay ADR 24: from 3",
        f"replay ADR 24: {ratings.MERGED_FIRST}, finding F0",
        f"replay ADR 24: {ratings.MERGED_FIRST}, finding F4",
        f"replay ADR 24: {ratings.MERGED_FIRST}",
    ]
    # the recompute's rows restart the count: Sonnet's two games don't become four
    routed = rating_store.routing_ratings(conn, REPLAY_START)
    assert routed == {"local": current["local"], "claude-sonnet": 1.0, "new-model": 1.0}

    again = rating_store.replay_ratings(
        conn, project, REPLAY_START, datetime(2026, 10, 5, tzinfo=UTC)
    )
    assert conn.execute("SELECT count(*) FROM rating_changes").fetchone()[0] == len(rows)
    assert [(r.agent, r.after, r.written) for r in again] == [
        (r.agent, r.after, False) for r in replayed
    ]
    conn.close()


def test_the_recompute_leaves_an_unplayed_agent_at_its_estimate(tmp_path):
    conn = metrics.open_db(tmp_path / "metrics.sqlite")
    project = metrics.upsert_project(conn, "coucou")
    replayed = rating_store.replay_ratings(
        conn, project, REPLAY_START, datetime(2026, 10, 5, tzinfo=UTC)
    )
    assert [(r.agent, r.after, r.written) for r in replayed] == [
        (agent, rating, False) for agent, rating in REPLAY_START.items()
    ]
    assert conn.execute("SELECT count(*) FROM rating_changes").fetchone()[0] == 0
    conn.close()


VOID_START = {"local-m": 5.0, "claude-sonnet": 7.0}
CUT_OFF = datetime.fromisoformat("2026-10-05T00:59:54+01:00")  # f7-06's fix (a91d5b5)


def test_benches_before_the_cut_off_void_only_opencodes_ticket_replays(tmp_path):
    """f7-07: OpenCode benched in the main checkout until f7-06's fix, so its replays before
    then are void; Claude's, a review bench's (no ticket) and later ones are kept."""
    conn = metrics.open_db(tmp_path / "metrics.sqlite")
    project = metrics.upsert_project(conn, "coucou")
    milestone = metrics.upsert_milestone(conn, project, "f3")
    ticket = metrics.upsert_ticket(conn, project, "f3-01", milestone_id=milestone, difficulty=3)
    jobs: dict[str, int] = {}
    for name, agent, ticket_id, started, outcome in (
        # 23:00Z is before the cut-off; 00:30Z is after it, though earlier as text
        ("leaked", "local-m", ticket, "2026-10-04T23:00:00+00:00", "failed"),
        ("leaked-again", "local-m", ticket, "2026-10-04T23:30:00+00:00", "failed"),
        ("already", "local-m", ticket, "2026-10-04T22:00:00+00:00", "void"),
        ("clean", "local-m", ticket, "2026-10-05T00:30:00+00:00", "passed"),
        ("claude", "claude-sonnet", ticket, "2026-10-04T23:00:00+00:00", "failed"),
        ("review", "local-m", None, "2026-10-04T23:00:00+00:00", "passed"),
    ):
        run = metrics.upsert_run(conn, project, f"bench-{name}", command="bench")
        jobs[name] = metrics.start_job(
            conn,
            run,
            ticket_id=ticket_id,
            milestone_id=milestone,
            role="bench",
            agent=agent,
            attempt=1,
            started=started,
        )
        metrics.finish_job(conn, jobs[name], ended=started, outcome=outcome)
    agents = {a.id: a for a in AGENTS}

    voided = rating_store.void_benches_before(conn, project, agents, CUT_OFF)

    assert voided == {"local-m": 2}
    outcomes = {
        name: conn.execute("SELECT outcome FROM jobs WHERE id = ?", (job,)).fetchone()[0]
        for name, job in jobs.items()
    }
    assert outcomes == {
        "leaked": "void",
        "leaked-again": "void",
        "already": "void",
        "clean": "passed",
        "claude": "failed",
        "review": "passed",
    }
    assert rating_store.void_benches_before(conn, project, agents, CUT_OFF) == {}  # nothing left

    rating_store.replay_ratings(conn, project, VOID_START, CUT_OFF)
    games = [
        ratings.bench_game("claude-sonnet", "f3-01", 3, None),
        ratings.bench_game("local-m", "f3-01", 3, 1),  # its only game: the clean pass
    ]
    expected = {c.agent: c.after for c in ratings.rate(VOID_START, {}, games)}
    current, _ = rating_store.standing(conn, VOID_START)
    assert current == pytest.approx(expected)
    assert current["local-m"] > VOID_START["local-m"]  # the leaked losses no longer count
    conn.close()
