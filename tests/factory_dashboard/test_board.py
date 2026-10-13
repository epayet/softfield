"""The board's cards (f5 D4, ADR 19 item 4): ``board.board`` over ``write_board``'s rows."""

import sqlite3
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import Any

from factory_dashboard.board import STAGES, Board, Card, board
from factory_dashboard.line import live_line
from factory_dashboard.queries import connect
from runner import metrics
from tests.factory_dashboard.conftest import LOCAL, NOW, PROJECT


def read(db: Path, **filters: Any) -> Board:
    conn = connect(db)
    try:
        return board(conn, PROJECT, NOW, **filters)
    finally:
        conn.close()


def write(db: Path, change: Callable[[sqlite3.Connection, int], object]) -> None:
    conn = metrics.open_db(db)
    try:
        change(conn, metrics.upsert_project(conn, PROJECT))
    finally:
        conn.close()


def keys(found: Board, stage: str) -> list[str]:
    return [card.key for card in found.stages[stage]]


def card(found: Board, key: str) -> Card:
    return next(c for cards in found.stages.values() for c in cards if c.key == key)


def test_the_stages_come_in_growth_order(board_db):
    assert STAGES == ("seed", "sprouting", "planted", "growing", "ripe", "harvested")
    assert tuple(read(board_db).stages) == STAGES


def test_an_idea_is_a_seed_and_sprouting_once_a_thread_is_about_it(board_db):
    found = read(board_db)
    assert card(found, "F20").stage == "seed"
    assert card(found, "F21").stage == "sprouting"  # an idea a thread is about
    assert card(found, "F22").stage == "sprouting"  # state planning

    write(board_db, lambda conn, p: metrics.planner_thread(conn, p, "f20", NOW.isoformat()))
    assert card(read(board_db), "F20").stage == "sprouting"


def test_a_ready_card_with_a_ticket_merged_is_growing_and_shows_what_runs(board_db):
    growing = card(read(board_db), "F24")
    assert growing.stage == "growing"
    assert (growing.done, growing.total, growing.set_aside) == (1, 3, 1)
    assert growing.full_key == "f24-growing"
    assert (growing.title, growing.area, growing.bug, growing.priority) == (
        "Growing",
        "factory",
        False,
        1,
    )
    assert growing.running is not None
    assert (
        growing.running.ticket,
        growing.running.goal,
        growing.running.agent,
        growing.running.attempt,
    ) == ("f24-02-working", "Goal of f24-02-working.", LOCAL, 2)


def test_a_job_whose_run_stopped_beating_is_not_what_runs_now(board_db):
    stale = (NOW - timedelta(minutes=10)).isoformat()
    write(
        board_db,
        lambda conn, p: metrics.upsert_run(conn, p, "20261002-113500", heartbeat=stale),
    )
    growing = card(read(board_db), "F24")
    assert growing.stage == "growing"
    assert growing.running is None


def test_a_planted_card_has_tickets_all_still_ready(board_db):
    planted = card(read(board_db), "F23")
    assert planted.stage == "planted"
    assert (planted.done, planted.total, planted.running) == (0, 2, None)


def test_every_ticket_done_is_growing_until_the_sheet_is_stored_then_ripe_then_harvested(
    board_db,
):
    unreviewed = card(read(board_db), "F25")
    assert unreviewed.stage == "growing"
    # a row the runner made before reading its doc: 100, and its series' area
    assert (unreviewed.priority, unreviewed.area) == (100, "factory")
    assert card(read(board_db), "M4").area == "product"

    write(
        board_db,
        lambda conn, p: metrics.upsert_milestone(
            conn, p, "f25-unreviewed", status="review", signoff={"changed": "It."}
        ),
    )
    assert card(read(board_db), "F25").stage == "ripe"

    write(
        board_db,
        lambda conn, p: metrics.upsert_milestone(
            conn, p, "f25-unreviewed", status="done", ended=NOW.isoformat()
        ),
    )
    assert card(read(board_db), "F25").stage == "harvested"


def test_a_set_aside_ticket_keeps_no_card_from_ripening(board_db):
    def change(conn: sqlite3.Connection, p: int) -> None:
        m = metrics.upsert_milestone(conn, p, "f25-unreviewed", signoff={"changed": "It."})
        metrics.upsert_ticket(conn, p, "f25-02-later", milestone_id=m, state="later")

    write(board_db, change)
    ripe = card(read(board_db), "F25")
    assert (ripe.stage, ripe.done, ripe.total, ripe.set_aside) == ("ripe", 1, 1, 1)


def test_a_removed_card_a_removed_ticket_and_the_bugs_row_make_no_card(board_db):
    found = read(board_db)
    every = [c.key for cards in found.stages.values() for c in cards]
    assert "F26" not in every
    assert "bug-06-gone" not in every
    assert not {"BUGS", "bugs"} & set(every)
    assert card(found, "F24").total == 3  # f24-05-gone isn't counted
    assert len(every) == len(set(every))


def test_a_set_aside_bug_is_a_seed_marked_as_a_bug_and_planted_once_ready(board_db):
    bug = card(read(board_db), "bug-01-duck-count")
    assert (bug.stage, bug.bug, bug.area, bug.kind) == ("seed", True, "factory", "bug")
    assert bug.note == "ticket written, set aside"
    assert (bug.full_key, bug.title, bug.priority) == (
        "bug-01-duck-count",
        "Goal of bug-01-duck-count.",
        50,
    )

    write(
        board_db,
        lambda conn, p: metrics.upsert_ticket(conn, p, "bug-01-duck-count", state="ready"),
    )
    bug = card(read(board_db), "bug-01-duck-count")
    assert (bug.stage, bug.note) == ("planted", "")


def test_a_bug_grows_while_it_runs_or_is_stuck_and_is_harvested_once_done(board_db):
    found = read(board_db)
    assert card(found, "bug-02-stale").stage == "planted"
    assert card(found, "bug-02-stale").priority == 7  # its own `priority:`
    assert card(found, "bug-03-working").stage == "growing"
    assert card(found, "bug-04-stuck").stage == "growing"
    assert card(found, "bug-05-fixed").stage == "harvested"


def test_a_ready_bug_with_a_running_job_is_growing_and_shows_it(board_db):
    def change(conn: sqlite3.Connection, p: int) -> None:
        run = metrics.upsert_run(conn, p, "20261002-113500")
        bugs = metrics.upsert_milestone(conn, p, "bugs")
        bug = metrics.upsert_ticket(conn, p, "bug-02-stale", milestone_id=bugs)
        metrics.start_job(
            conn,
            run,
            ticket_id=bug,
            milestone_id=bugs,
            role="developer",
            agent=LOCAL,
            attempt=1,
            started=NOW.isoformat(),
        )

    write(board_db, change)
    bug = card(read(board_db), "bug-02-stale")
    assert bug.stage == "growing"
    assert bug.running is not None
    assert (bug.running.ticket, bug.running.attempt) == ("bug-02-stale", 1)


def test_cards_within_a_stage_come_in_priority_order_then_by_key(board_db):
    found = read(board_db)
    assert keys(found, "seed") == ["F20", "bug-01-duck-count"]  # 30, 50
    assert keys(found, "sprouting") == ["F22", "F21"]  # 10, 20
    assert keys(found, "planted") == ["F23", "bug-02-stale"]  # 5, 7
    # 1, then the bugs' 50 by key, then 100
    assert keys(found, "growing") == ["F24", "bug-03-working", "bug-04-stuck", "F25"]
    assert keys(found, "ripe") == ["F1", "M4"]  # both 100


def test_q_keeps_the_cards_whose_key_or_title_contains_it(board_db):
    found = read(board_db, q="DUCK")
    every = sorted(c.key for cards in found.stages.values() for c in cards)
    assert every == ["F20", "bug-01-duck-count"]  # a title, a key
    assert keys(read(board_db, q="f24"), "growing") == ["F24"]
    assert read(board_db, q="").stages == read(board_db).stages


def test_kind_keeps_bugs_or_one_area_s_cards(board_db):
    bugs = [c for cards in read(board_db, kind="bug").stages.values() for c in cards]
    assert sorted(c.key for c in bugs) == [
        "bug-01-duck-count",
        "bug-02-stale",
        "bug-03-working",
        "bug-04-stuck",
        "bug-05-fixed",
    ]
    product = [c for cards in read(board_db, kind="product").stages.values() for c in cards]
    assert sorted(c.key for c in product) == ["F20", "M3", "M4"]
    factory = [c for cards in read(board_db, kind="factory").stages.values() for c in cards]
    assert all(c.area == "factory" and not c.bug for c in factory)
    assert "F24" in [c.key for c in factory]


def test_harvested_keeps_the_latest_four_and_says_how_many_more(db_path):
    def change(conn: sqlite3.Connection, p: int) -> None:
        for day, key in enumerate(("m4", "f1", "f30", "f31", "f32", "f33"), start=1):
            metrics.upsert_milestone(
                conn, p, key, status="done", ended=f"2026-09-{day:02d}T12:00:00+02:00"
            )

    write(db_path, change)
    found = read(db_path)
    assert keys(found, "harvested") == ["F33", "F32", "F31", "F30"]  # the latest first
    assert found.more_harvested == 2
    assert read(db_path, q="f3").more_harvested == 0


def test_a_harvested_bug_is_placed_by_its_latest_job_s_end(board_db):
    found = read(board_db)
    # bug-05's job ended 2026-09-30; m3 was signed off on 2026-09-15
    assert keys(found, "harvested") == ["bug-05-fixed", "M3"]
    assert found.more_harvested == 0


def test_the_ripe_cards_are_the_line_s_ripe_ones_and_the_harvested_its_stash(board_db):
    conn = connect(board_db)
    try:
        field = live_line(conn, PROJECT, NOW)["field"]
        found = board(conn, PROJECT, NOW)
    finally:
        conn.close()
    assert [c.full_key for c in found.stages["ripe"]] == [m["key"] for m in field["ripe"]]
    assert field["ripe"]
    harvested = [c.full_key for c in found.stages["harvested"] if not c.bug]
    assert harvested == [m["key"] for m in field["stash"]]
    assert field["stash"]


def test_an_unknown_project_has_an_empty_board(board_db):
    conn = connect(board_db)
    try:
        found = board(conn, "nowhere", NOW)
    finally:
        conn.close()
    assert found.stages == {stage: [] for stage in STAGES}
    assert found.more_harvested == 0
