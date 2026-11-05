"""The board's cards (f5 D4, ADR 19 item 4): ``board.board`` over ``write_board``'s rows, then
its page, ``/board`` (f5-16)."""

import json
import re
import sqlite3
from collections.abc import Callable
from datetime import timedelta
from html import unescape
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from factory_dashboard.app import create_app, get_now
from factory_dashboard.board import STAGES, Board, Card, DevWork, _hours, board, milestone_card
from factory_dashboard.line import live_line
from factory_dashboard.queries import connect
from runner import metrics
from tests.factory_dashboard.conftest import LOCAL, NOW, OPUS, PROJECT, mark_reserve
from tests.factory_dashboard.test_planning import ORIGIN, STATIC
from tests.factory_dashboard.test_planning import _open as open_page
from tests.layout import DISPLAY, PHONE, layout_problems


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
    assert STAGES == ("seed", "sprouting", "planted", "ripe", "harvested")
    assert tuple(read(board_db).stages) == STAGES


def test_an_idea_is_a_seed_and_sprouting_once_a_thread_is_about_it(board_db):
    found = read(board_db)
    assert card(found, "F20").stage == "seed"
    assert card(found, "F21").stage == "sprouting"  # an idea a thread is about
    assert card(found, "F22").stage == "sprouting"  # state planning

    write(board_db, lambda conn, p: metrics.planner_thread(conn, p, "f20", NOW.isoformat()))
    assert card(read(board_db), "F20").stage == "sprouting"


def test_archived_threads_are_excluded_from_sprouting(board_db):
    conn = metrics.open_db(board_db)
    try:
        (thread,) = conn.execute(
            "SELECT id FROM planner_threads WHERE card = ?", ("f21",)
        ).fetchone()
        conn.execute(
            "UPDATE planner_threads SET archived = ? WHERE id = ?",
            (NOW.isoformat(), thread),
        )
        conn.commit()
    finally:
        conn.close()
    found = read(board_db)
    assert card(found, "F21").stage == "seed"


def test_a_sprouting_cards_since_date_is_local(paris, board_db):
    """F187: 23:30 UTC on 1 Oct is already 2 Oct in Paris."""
    conn = metrics.open_db(board_db)
    try:
        (thread_id,) = conn.execute(
            "SELECT id FROM planner_threads WHERE card = ?", ("f21",)
        ).fetchone()
        conn.execute(
            "INSERT INTO planner_messages (thread_id, author, at, text)"
            " VALUES (?, 'lead', '2026-10-01T23:30:00+00:00', 'What do you think?')",
            (thread_id,),
        )
        conn.commit()
    finally:
        conn.close()
    assert card(read(board_db), "F21").note == "waits for your answer since 2 Oct"


def test_sprouting_card_shows_note_from_lead_message(board_db):
    conn = metrics.open_db(board_db)
    try:
        (thread_id,) = conn.execute(
            "SELECT id FROM planner_threads WHERE card = ?", ("f21",)
        ).fetchone()
        conn.execute(
            "INSERT INTO planner_messages (thread_id, author, at, text)"
            " VALUES (?, 'lead', ?, 'What do you think?')",
            (thread_id, (NOW - timedelta(hours=1)).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
    found = read(board_db)
    f21 = card(found, "F21")
    assert f21.stage == "sprouting"
    assert f21.note == "waits for your answer since 2 Oct"
    f22 = card(found, "F22")
    assert f22.stage == "sprouting"
    assert f22.note == ""


def test_sprouting_card_with_owner_last_says_lead_is_answering(board_db):
    conn = metrics.open_db(board_db)
    try:
        (thread_id,) = conn.execute(
            "SELECT id FROM planner_threads WHERE card = ?", ("f21",)
        ).fetchone()
        conn.execute(
            "INSERT INTO planner_messages (thread_id, author, at, text)"
            " VALUES (?, 'owner', ?, 'I have an idea.')",
            (thread_id, (NOW - timedelta(hours=1)).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
    found = read(board_db)
    f21 = card(found, "F21")
    assert f21.stage == "sprouting"
    assert f21.note == "the lead is answering"


def test_the_owners_message_on_its_way_shows_at_once(board_db):
    """The owner answered from /planning; the runner hasn't picked it up: the card no longer
    waits for them, and on an archived idea's thread it sprouts again (the owner, 2026-10-07)."""

    def answer(conn: sqlite3.Connection, project: int) -> None:
        thread = metrics.planner_thread(conn, project, "f21", NOW.isoformat())
        metrics.add_planner_message(conn, thread["id"], "lead", NOW.isoformat(), "Which?")
        archived = metrics.planner_thread(conn, project, "f20", NOW.isoformat())
        metrics.set_thread_archived(conn, archived["id"], NOW.isoformat())
        for key in ("f21", "f20"):
            metrics.add_request(conn, project, "plan_message", key, "This one.", NOW.isoformat())

    write(board_db, answer)
    found = read(board_db)
    assert (card(found, "F21").stage, card(found, "F21").note) == (
        "sprouting",
        "the lead is answering",
    )
    assert (card(found, "F20").stage, card(found, "F20").note) == (
        "sprouting",
        "the lead is answering",
    )


def test_page_shows_note_on_sprouting_but_not_other_stages(board_db, board_client):
    conn = metrics.open_db(board_db)
    try:
        (thread_id,) = conn.execute(
            "SELECT id FROM planner_threads WHERE card = ?", ("f21",)
        ).fetchone()
        conn.execute(
            "INSERT INTO planner_messages (thread_id, author, at, text)"
            " VALUES (?, 'lead', ?, 'What do you think?')",
            (thread_id, (NOW - timedelta(hours=1)).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
    html = _page(board_client)
    _, words, _ = _card(html, "/milestones/f21-parallel")
    assert "waits for your answer since 2 Oct" in words
    _, words, _ = _card(html, "/milestones/f23-planted")
    assert "waits for your answer" not in words
    assert "the lead is answering" not in words
    _, words, _ = _card(html, "/milestones/f24-growing")
    assert "waits for your answer" not in words
    assert "the lead is answering" not in words


def test_a_ready_card_with_a_ticket_merged_is_planted_started_and_shows_what_runs(board_db):
    """F154 D1: a ticket started keeps the card in Planted, marked started."""
    growing = card(read(board_db), "F24")
    assert (growing.stage, growing.started) == ("planted", True)
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
    assert (growing.stage, growing.started) == ("planted", True)
    assert growing.running is None


def test_a_planted_card_has_tickets_all_still_ready(board_db):
    planted = card(read(board_db), "F23")
    assert (planted.stage, planted.started) == ("planted", False)
    assert (planted.done, planted.total, planted.running) == (0, 2, None)


def test_every_ticket_done_is_planted_until_the_sheet_is_stored_then_ripe_then_harvested(
    board_db,
):
    unreviewed = card(read(board_db), "F25")
    assert (unreviewed.stage, unreviewed.started) == ("planted", True)
    # a row the runner made before reading its doc: 100, and its series' area
    assert (unreviewed.priority, unreviewed.area) == (100, "factory")
    assert card(read(board_db), "M4").area == "product"
    # every ticket done, no sheet stored: "Review next"
    assert unreviewed.review_step is not None
    assert unreviewed.review_step.label == "Review next"
    assert (
        unreviewed.review_step.text
        == "Claude reviews it before the next ticket · then it's yours to sign off"
    )

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


def test_an_empty_milestone_with_no_state_and_no_tickets_makes_no_card(board_db):
    """D3: a row with neither state nor tickets is no card."""

    def add_empty(conn: sqlite3.Connection, p: int) -> None:
        metrics.upsert_milestone(conn, p, "f99-empty")

    write(board_db, add_empty)
    found = read(board_db)
    every = [c.key for cards in found.stages.values() for c in cards]
    assert "F99" not in every


def test_an_empty_milestone_with_no_state_but_with_status_makes_no_card(board_db):
    """The bug: a state-less milestone with a non-null status still appeared."""

    def add_empty(conn: sqlite3.Connection, p: int) -> None:
        metrics.upsert_milestone(conn, p, "f98-empty", status="in progress")

    write(board_db, add_empty)
    found = read(board_db)
    every = [c.key for cards in found.stages.values() for c in cards]
    assert "F98" not in every


def test_a_set_aside_bug_is_a_seed_marked_as_a_bug_and_planted_once_ready(board_db):
    bug = card(read(board_db), "bug-01-duck-count")
    assert (bug.stage, bug.bug, bug.area, bug.kind) == ("seed", True, "factory", "bug")
    assert bug.note == "Set aside, won't run until you queue it ›"
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
    assert (bug.stage, bug.note, bug.started) == ("planted", "", False)


def test_a_set_aside_bug_card_shows_set_aside_action_on_the_board(board_db, board_client):
    """A set-aside bug card on the board reads
    "Set aside, won't run until you queue it ›" as a card-action."""
    html = _page(board_client)
    # bug-01-duck-count is set aside (seed stage)
    _classes, words, raw = _card(html, "/tickets/bug-01-duck-count")
    assert "Set aside, won't run until you queue it" in words
    assert "card-action" in raw


def test_a_bug_grows_while_it_runs_or_is_stuck_and_is_harvested_once_done(board_db):
    found = read(board_db)
    assert (card(found, "bug-02-stale").stage, card(found, "bug-02-stale").started) == (
        "planted",
        False,
    )
    assert card(found, "bug-02-stale").priority == 7  # its own `priority:`
    for key in ("bug-03-working", "bug-04-stuck"):
        assert (card(found, key).stage, card(found, key).started) == ("planted", True), key
    assert (card(found, "bug-05-fixed").stage, card(found, "bug-05-fixed").started) == (
        "harvested",
        False,
    )


def test_a_ready_bug_with_a_running_job_is_planted_started_and_shows_it(board_db):
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
    assert (bug.stage, bug.started) == ("planted", True)
    assert bug.running is not None
    assert (bug.running.ticket, bug.running.attempt) == ("bug-02-stale", 1)


def test_cards_within_a_stage_come_in_priority_order_then_by_key(board_db):
    found = read(board_db)
    assert keys(found, "seed") == ["F20", "bug-01-duck-count"]  # 30, 50
    assert keys(found, "sprouting") == ["F22", "F21"]  # 10, 20
    # one line, started or not (F154 D1): 1, 5, 7, the bugs' 50 by key, then 100
    assert keys(found, "planted") == [
        "F24",
        "F23",
        "bug-02-stale",
        "bug-03-working",
        "bug-04-stuck",
        "F25",
    ]
    assert keys(found, "ripe") == ["F1", "M4"]  # both 100


def _planted(*cards: tuple[str, int]) -> Callable[[sqlite3.Connection, int], None]:
    """More planted cards, each with its priority."""

    def change(conn: sqlite3.Connection, p: int) -> None:
        for key, priority in cards:
            metrics.upsert_milestone(conn, p, key, title=key, state="ready", priority=priority)

    return change


def _reorder(
    value: str, done: str | None = None, result: str | None = None
) -> Callable[[sqlite3.Connection, int], None]:
    """A ``reorder`` request, open or finished with ``result``."""

    def change(conn: sqlite3.Connection, p: int) -> None:
        asked = metrics.add_request(conn, p, "reorder", None, value, NOW.isoformat())
        if done:
            metrics.finish_request(conn, asked, done, result or "")

    return change


def _places(found: Board, stage: str) -> list[tuple[str, int, bool, int]]:
    return [(c.key, c.place, c.on_its_way, c.was) for c in found.stages[stage]]


def test_a_card_shows_its_place_in_its_stage_but_not_once_ripe_or_harvested(board_db):
    """F15 D1: #1, #2… in place of a P number, in the stages the owner orders; the planted
    cards, started or not, are one line (F154 D1)."""
    write(board_db, _planted(("f27-third", 9)))
    found = read(board_db)
    assert _places(found, "planted") == [
        ("F24", 1, False, 0),
        ("F23", 2, False, 0),
        ("bug-02-stale", 3, False, 0),
        ("F27", 4, False, 0),
        ("bug-03-working", 5, False, 0),
        ("bug-04-stuck", 6, False, 0),
        ("F25", 7, False, 0),
    ]
    assert [c.place for c in found.stages["seed"]] == [1, 2]
    assert [c.place for c in found.stages["sprouting"]] == [1, 2]
    assert [c.place for c in found.stages["ripe"] + found.stages["harvested"]] == [0, 0, 0, 0]


def test_an_open_reorder_shows_at_once_with_where_the_moved_card_was(board_db):
    """F15 D4: F9 sent before F7, which the priorities put first: F9 is on its way, F7 is not
    marked (the card moved is the one out of place, not the one it passed)."""
    write(board_db, _planted(("f7-first", 2), ("f9-second", 3)))
    assert keys(read(board_db), "planted")[:5] == ["F24", "F7", "F9", "F23", "bug-02-stale"]

    write(board_db, _reorder('["f24", "f9", "f7"]'))
    found = read(board_db)
    assert _places(found, "planted")[:5] == [
        ("F24", 1, False, 0),
        ("F9", 2, True, 3),
        ("F7", 3, False, 0),
        ("F23", 4, False, 0),
        ("bug-02-stale", 5, False, 0),
    ]
    assert not any(c.on_its_way for cards in found.stages.values() for c in cards if c.key != "F9")


def test_a_card_whose_neighbours_moved_past_it_is_not_marked(board_db):
    write(board_db, _planted(("f7-first", 2), ("f9-second", 3)))
    # F7 sent below the cards not started: only F7 is out of place
    write(board_db, _reorder('["f24", "f9", "f23", "bug-02-stale", "f7"]'))
    assert _places(read(board_db), "planted") == [
        ("F24", 1, False, 0),
        ("F9", 2, False, 0),
        ("F23", 3, False, 0),
        ("bug-02-stale", 4, False, 0),
        ("F7", 5, True, 2),
        ("bug-03-working", 6, False, 0),
        ("bug-04-stuck", 7, False, 0),
        ("F25", 8, False, 0),
    ]


def test_the_latest_open_reorder_is_the_one_shown(board_db):
    write(board_db, _planted(("f7-first", 2), ("f9-second", 3)))
    write(board_db, _reorder('["f9", "f7"]'))
    write(board_db, _reorder('["f24", "f23", "f7", "f9"]'))
    assert _places(read(board_db), "planted") == [
        ("F24", 1, False, 0),
        ("F23", 2, True, 4),
        ("F7", 3, False, 0),
        ("F9", 4, False, 0),
        ("bug-02-stale", 5, False, 0),
        ("bug-03-working", 6, False, 0),
        ("bug-04-stuck", 7, False, 0),
        ("F25", 8, False, 0),
    ]


def test_a_done_or_refused_reorder_shows_no_mark(board_db):
    write(board_db, _planted(("f7-first", 2), ("f9-second", 3)))
    before = read(board_db)
    write(board_db, _reorder('["f9", "f7"]', NOW.isoformat(), "reordered: 1 card changed"))
    write(board_db, _reorder('["f23", "f9"]', NOW.isoformat(), "a reorder names each card once"))
    write(board_db, _reorder("not a list"))  # the runner will refuse it: nothing to show
    after = read(board_db)
    assert after.stages == before.stages
    assert _places(after, "planted")[:2] == [("F24", 1, False, 0), ("F7", 2, False, 0)]


def test_a_card_the_reorder_doesnt_name_keeps_its_place_after_the_listed_ones(board_db):
    write(board_db, _reorder('["bug-02-stale", "f25", "nowhere"]'))
    found = read(board_db)
    # the two listed come first, started or not (F154 D1); the others keep their own order
    assert _places(found, "planted") == [
        ("bug-02-stale", 1, True, 3),
        ("F25", 2, True, 6),
        ("F24", 3, False, 0),
        ("F23", 4, False, 0),
        ("bug-03-working", 5, False, 0),
        ("bug-04-stuck", 6, False, 0),
    ]
    assert keys(found, "seed") == ["F20", "bug-01-duck-count"]


def test_places_are_counted_before_q_and_kind_narrow_the_cards(board_db):
    assert _places(read(board_db, q="stale"), "planted") == [("bug-02-stale", 3, False, 0)]
    write(
        board_db,
        _reorder('["f23", "bug-02-stale", "bug-03-working", "bug-04-stuck", "f24"]'),
    )
    bugs = read(board_db, kind="bug")
    assert _places(bugs, "planted") == [
        ("bug-02-stale", 2, False, 0),
        ("bug-03-working", 3, False, 0),
        ("bug-04-stuck", 4, False, 0),
    ]
    assert _places(read(board_db, q="f24"), "planted") == [("F24", 5, True, 1)]


def test_the_board_holds_every_open_card_in_the_order_shown_for_a_send(board_db):
    """F15 D10: a send is the whole open line, whatever q and kind keep, each card by the key
    a reorder names it by and with its stage; harvested cards are done and not in it."""
    write(board_db, _reorder('["bug-02-stale"]'))
    whole = read(board_db)
    line = whole.line
    assert line[0] == ("bug-02-stale", "planted")  # the order on its way
    assert read(board_db, q="duck", kind="bug").line == line
    for stage in STAGES:
        assert [key for key, at in line if at == stage] == (
            [] if stage == "harvested" else [c.key.lower() for c in whole.stages[stage]]
        ), stage
    assert len({key for key, _ in line}) == len(line)


def test_q_keeps_the_cards_whose_key_or_title_contains_it(board_db):
    found = read(board_db, q="DUCK")
    every = sorted(c.key for cards in found.stages.values() for c in cards)
    assert every == ["F20", "bug-01-duck-count"]  # a title, a key
    assert keys(read(board_db, q="f24"), "planted") == ["F24"]
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


# --- the developers' line (F146 D1-D4) -------------------------------------------------------


def _tickets(
    *rows: tuple[str, str, str, str, tuple[str, ...]],
) -> Callable[[sqlite3.Connection, int], None]:
    """Planted cards with tickets: (card, ticket, kind, state, depends_on); files from
    ``FILES`` when the ticket id is in it."""

    def change(conn: sqlite3.Connection, p: int) -> None:
        made: dict[str, int] = {}
        for card_key, ticket, kind, state, deps in rows:
            if card_key not in made:
                made[card_key] = metrics.upsert_milestone(
                    conn, p, card_key, title=card_key, state="ready", priority=1
                )
            metrics.upsert_ticket(
                conn,
                p,
                ticket,
                milestone_id=made[card_key],
                kind=kind,
                state=state,
                depends_on=list(deps),
                files=FILES.get(ticket, []),
            )

    return change


FILES: dict[str, list[str]] = {}


def _work(db: Path, key: str, **filters: Any):
    found = read(db, developers=True, **filters)
    return next(
        c for cards in found.stages.values() for c in cards if c.full_key == key.lower()
    ).developers


def test_developer_work_is_none_without_the_view(board_db):
    found = read(board_db)
    assert all(c.developers is None for cards in found.stages.values() for c in cards)
    assert found.developers == (0, 0, None)
    assert read(board_db, developers=True).line == found.line


def test_a_developer_ticket_that_can_start_is_now_and_one_after_it_is_after(db_path):
    write(
        db_path,
        _tickets(
            ("f60-a", "f60-01", "developer", "ready", ()),
            ("f60-a", "f60-02", "developer", "ready", ("f60-01",)),
            ("f60-a", "f60-03", "lead", "ready", ("f60-02",)),
        ),
    )
    work = _work(db_path, "F60-A")
    assert (work.look, work.now, work.after, work.waiting, work.waits_for) == ("can", 1, 1, 0, ())
    assert work.then == "f60-03"


def test_a_card_with_only_developer_tickets_says_review_next(db_path):
    write(db_path, _tickets(("f61-a", "f61-01", "developer", "ready", ())))
    assert _work(db_path, "F61-A").then == "review"


def test_a_developer_ticket_after_a_lead_one_waits_even_through_another_developer(db_path):
    write(
        db_path,
        _tickets(
            ("f62-a", "f62-01", "lead", "ready", ()),
            ("f62-a", "f62-02", "developer", "ready", ("f62-01",)),
            ("f62-a", "f62-03", "developer", "ready", ("f62-02",)),
        ),
    )
    work = _work(db_path, "F62-A")
    assert (work.look, work.now, work.after, work.waiting) == ("waits", 0, 0, 2)
    assert work.waits_for == ("f62-01",)
    assert work.then is None


def test_a_set_aside_or_unknown_dependency_waits_under_its_own_id(db_path):
    write(
        db_path,
        _tickets(
            ("f63-a", "f63-01", "developer", "later", ()),
            ("f63-a", "f63-02", "developer", "ready", ("f63-01", "nowhere-01")),
        ),
    )
    work = _work(db_path, "F63-A")
    assert (work.look, work.waits_for) == ("waits", ("f63-01", "nowhere-01"))


def test_a_card_with_a_ticket_that_can_run_and_one_that_waits_is_can(db_path):
    write(
        db_path,
        _tickets(
            ("f64-a", "f64-01", "lead", "ready", ()),
            ("f64-a", "f64-02", "developer", "ready", ("f64-01",)),
            ("f64-a", "f64-03", "developer", "ready", ()),
        ),
    )
    work = _work(db_path, "F64-A")
    assert (work.look, work.now, work.waiting, work.then) == ("can", 1, 1, "f64-01")


def test_a_lead_only_card_and_the_other_stages_look_none(db_path):
    write(db_path, _tickets(("f65-a", "f65-01", "lead", "ready", ())))
    found = read(db_path, developers=True)
    assert card(found, "F65").developers == DevWork("none")
    assert all(
        c.developers == DevWork("none")
        for stage in ("seed", "sprouting", "ripe", "harvested")
        for c in found.stages[stage]
    )


def test_a_ticket_under_a_protected_path_is_the_lead_s_with_a_checkout(db_path, tmp_path):
    (tmp_path / ".softfield").mkdir()
    (tmp_path / ".softfield" / "protected-paths.txt").write_text("runner/**\n", encoding="utf-8")
    FILES["f66-01"] = ["runner/x.py"]
    try:
        write(db_path, _tickets(("f66-a", "f66-01", "developer", "ready", ())))
        assert _work(db_path, "F66-A").look == "can"  # no checkout: kind alone
        write(db_path, lambda conn, p: metrics.upsert_project(conn, PROJECT, repo=str(tmp_path)))
        assert _work(db_path, "F66-A").look == "none"
    finally:
        FILES.clear()


def test_the_board_counts_the_cards_and_tickets_developers_can_work_on(db_path):
    write(
        db_path,
        _tickets(
            ("f67-a", "f67-01", "developer", "ready", ()),
            ("f67-a", "f67-02", "developer", "ready", ("f67-01",)),
            ("f68-b", "f68-03", "developer", "ready", ("f68-04",)),
            ("f68-b", "f68-04", "lead", "ready", ()),
        ),
    )
    # two tickets times the fixture's one merged ticket, 10 minutes long
    assert read(db_path, developers=True).developers == (1, 2, 20.0)


def test_a_planted_card_with_every_ticket_done_says_review_next(db_path):
    write(db_path, _tickets(("f69-a", "f69-01", "developer", "done", ())))
    assert _work(db_path, "F69-A") == DevWork("none", then="review")
    _, words = _slot(_page(_client(db_path), "?view=developers"), "/milestones/f69-a")
    assert words == "every ticket done · then Claude's review"


# --- the page (f5-16) ------------------------------------------------------------------------


def _client(db: Path) -> TestClient:
    app = create_app(db, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url=ORIGIN)


@pytest.fixture
def board_client(board_db: Path) -> TestClient:
    """A client over ``board_db``."""
    return _client(board_db)


def _page(client: TestClient, query: str = "") -> str:
    response = client.get(f"/board{query}")
    assert response.status_code == 200
    return str(response.text)


def _columns(html: str) -> dict[str, str]:
    """Each stage's column by its stage, in the page's order."""
    return dict(re.findall(r'<section id="stage-([a-z]+)"(.*?)</section>', html, re.S))


def _links(html: str) -> list[str]:
    """The cards' links, without the query."""
    return re.findall(r'<a class="card[^"]*" href="([^"?]+)', html)


def _card(html: str, link: str) -> tuple[list[str], str, str]:
    """A card by its link: its classes, its words, and its raw HTML."""
    found = re.search(
        rf'<a class="card([^"]*)" href="{re.escape(link)}\?[^"]*">(.*?)</a>', html, re.S
    )
    assert found, link
    return found[1].split(), " ".join(unescape(re.sub(r"<[^>]+>", " ", found[2])).split()), found[2]


def _card_note(html: str, link: str) -> str:
    """A card's note by its link, "" when it has none: read inside that card alone, so another
    card's note further down never answers for it."""
    found = re.search(r'<span class="card-note">([^<]*)</span>', _card(html, link)[2])
    return unescape(found[1]) if found else ""


def test_the_page_lists_each_card_in_its_stage_s_column(board_db, board_client):
    columns = _columns(_page(board_client))
    assert tuple(columns) == STAGES
    found = read(board_db)
    for stage in STAGES:
        assert _links(columns[stage]) == [
            f"/tickets/{c.full_key}" if c.bug else f"/milestones/{c.full_key}"
            for c in found.stages[stage]
        ], stage
    assert _links(columns["seed"]) == ["/milestones/f20-duck-pond", "/tickets/bug-01-duck-count"]
    assert _links(columns["planted"])[0] == "/milestones/f24-growing"


def _head(column: str) -> str:
    """A column's head, as words."""
    found = re.search(r'<div class="stage-head">(.*?)</div>\s*<div class="cards">', column, re.S)
    assert found
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", found[1])).split())


def test_each_stage_s_head_says_what_it_means_and_what_comes_next(board_client):
    """F154 D2: its meaning and its count, then what moves a card on; Planted counts its
    started cards too, and Harvested has no next step."""
    columns = _columns(_page(board_client))
    assert {stage: _head(column) for stage, column in columns.items()} == {
        "seed": "Seed an idea, or a ticket set aside · 2"
        " Next a conversation with the lead plans it",
        "sprouting": "Sprouting being planned with the lead · 2 Next you approve the plan",
        "planted": "Planted in line for the factory, #1 first · 6, 4 growing"
        " Next every ticket done, then Claude reviews it",
        "ripe": "Ripe needs your sign-off · 2 Next you sign off",
        "harvested": "Harvested signed off or fixed · 2",
    }
    assert 'class="stage-next"' not in columns["harvested"]


def test_a_started_card_carries_the_growing_tag_and_one_not_started_none(board_client):
    """F154 D3: the class ``started`` (the orange edge) and the "growing" tag."""
    html = _page(board_client)
    for link, started in (
        ("/milestones/f24-growing", True),
        ("/tickets/bug-03-working", True),
        ("/milestones/f23-planted", False),
        ("/tickets/bug-02-stale", False),
    ):
        classes, words, raw = _card(html, link)
        assert ("started" in classes) is started, link
        assert ('class="card-growing"' in raw) is started, link
        assert (" growing " in f"{words} ") is started, link


def test_a_card_s_link_opens_its_page(board_client):
    for link in _links(_page(board_client)):
        assert board_client.get(link).status_code == 200, link


def test_a_marked_card_shows_the_fast_lane_plate_and_an_unmarked_one_doesn_t(
    board_db, board_client, tmp_path
):
    """F172 D6, D8: the "fast lane" plate on a planted card (F23) and a started one (F24) whose
    doc is marked; none on F25, unmarked, nor on F20, a seed whose doc is marked."""
    mark_reserve(board_db, tmp_path / "repo", "f23-planted", "f24-growing", "f20-duck-pond")
    found = read(board_db)
    assert [c.key for cards in found.stages.values() for c in cards if c.reserve] == ["F24", "F23"]
    html = _page(board_client)
    for link, plate in (
        ("/milestones/f23-planted", True),
        ("/milestones/f24-growing", True),
        ("/milestones/f25-unreviewed", False),
        ("/milestones/f20-duck-pond", False),
    ):
        _, words, raw = _card(html, link)
        assert ('class="card-reserve"' in raw) is plate, link
        assert ("fast lane" in words) is plate, link
        assert "uses Claude's reserve" not in words, link


def test_no_card_is_marked_without_a_checkout(board_db):
    assert not any(c.reserve for cards in read(board_db).stages.values() for c in cards)


def test_q_and_kind_narrow_the_page_s_cards_and_stay_in_the_form(board_client):
    html = _page(board_client, "?q=DUCK")
    assert sorted(_links(html)) == ["/milestones/f20-duck-pond", "/tickets/bug-01-duck-count"]
    assert re.search(r'<input type="search" name="q" value="DUCK"', html)

    bugs = _page(board_client, "?kind=bug")
    assert sorted(_links(bugs)) == [
        "/tickets/bug-01-duck-count",
        "/tickets/bug-02-stale",
        "/tickets/bug-03-working",
        "/tickets/bug-04-stuck",
        "/tickets/bug-05-fixed",
    ]
    pressed = re.findall(r'<button name="kind" value="([a-z]*)" aria-pressed="true"', bugs)
    assert pressed == ["bug"]
    # Enter in the search box sends the form's first button: it keeps the kind
    form = re.search(r'<form id="board-filter"(.*?)</form>', bugs, re.S)
    assert form
    assert re.search(r'<form id="board-filter"[^>]*method="get"', bugs)
    assert re.findall(r"<button[^>]*>", form[1])[0] == '<button name="kind" value="bug">'

    both = _page(board_client, "?q=duck&kind=bug")
    assert _links(both) == ["/tickets/bug-01-duck-count"]
    assert _links(_page(board_client, "?kind=nonsense")) == _links(_page(board_client))


def test_the_harvested_column_shows_four_cards_and_how_many_more(db_path):
    def change(conn: sqlite3.Connection, p: int) -> None:
        for day, key in enumerate(("m4", "f1", "f30", "f31", "f32", "f33"), start=1):
            metrics.upsert_milestone(
                conn, p, key, status="done", ended=f"2026-09-{day:02d}T12:00:00+02:00"
            )

    write(db_path, change)
    html = _page(_client(db_path))
    harvested = _columns(html)["harvested"]
    assert _links(harvested) == [f"/milestones/f{n}" for n in (33, 32, 31, 30)]
    assert re.search(r">\s*2 more harvested\b", harvested)
    assert re.search(r"· 6, latest 4\b", harvested)
    assert _plots(html)["harvested"] == (6, "Harvested", False)


def test_no_more_harvested_shows_when_four_or_fewer_are(board_client):
    assert "more harvested" not in _page(board_client)


def test_a_bug_card_says_bug_and_links_to_its_ticket_page(board_client):
    html = _page(board_client)
    classes, words, _ = _card(html, "/tickets/bug-01-duck-count")
    assert "bug" in classes  # the striped edge
    assert "factory" in classes
    assert "bug · factory" in words
    assert "Set aside, won't run until you queue it" in words
    classes, words, _ = _card(html, "/milestones/f20-duck-pond")
    assert "bug" not in classes
    assert "product" in classes
    assert "bug" not in words
    assert words.startswith("#1 F20 product The duck pond")


def test_a_card_shows_its_place_and_no_p_number_on_the_page(board_db):
    write(board_db, _planted(("f27-third", 9)))
    html = _page(_client(board_db))
    _, words, _ = _card(html, "/milestones/f27-third")
    assert words.startswith("#4 F27 factory")
    assert not re.search(r"\bP\d", words)
    for link in ("/milestones/f1", "/milestones/m3"):  # ripe, harvested
        _, words, _ = _card(html, link)
        assert "#" not in words
        assert not re.search(r"\bP\d", words)


def test_a_card_on_its_way_has_a_dashed_edge_and_says_where_it_was(board_db):
    write(board_db, _planted(("f7-first", 2), ("f9-second", 3)))
    write(board_db, _reorder('["f24", "f9", "f7"]'))
    html = _page(_client(board_db))
    classes, words, _ = _card(html, "/milestones/f9-second")
    assert "on-its-way" in classes
    assert words.startswith("#2 F9")
    assert "on its way · was #3 · at the runner's next pick" in words
    classes, words, _ = _card(html, "/milestones/f7-first")
    assert "on-its-way" not in classes
    assert "on its way" not in words
    assert words.startswith("#3 F7")


def test_a_started_card_shows_its_tickets_and_what_runs_now(board_client):
    html = _page(board_client)
    _, words, _ = _card(html, "/milestones/f24-growing")
    assert "1 of 3 tickets · 1 set aside" in words
    assert f"Now: f24-02-working · Goal of f24-02-working. · {LOCAL}, attempt 2" in words
    planted = _columns(html)["planted"]
    assert re.search(r'<span class="meter"><span style="width: 33%">', planted)
    # a ripe card carries the sign-off text
    _, ripe, _ = _card(html, "/milestones/f1")
    assert "Read the review and sign off" in ripe
    assert "softfield signoff" not in ripe


def _plots(html: str) -> dict[str, tuple[int, str, bool]]:
    """Each plot by its stage, in the page's order: its count, its name, and whether its
    count is ripe's yellow."""
    section = re.search(r'<section id="plots"(.*?)</section>', html, re.S)
    assert section
    found = re.findall(
        r'<button type="button" class="plot at-([a-z]+)( ripe)?" data-stage="\1"'
        r' aria-pressed="false">'
        r"\s*<svg[^>]*>.*?</svg>\s*<b>(\d+)</b>\s*<span>([^<]*)</span>\s*</button>",
        section[1],
        re.S,
    )
    return {stage: (int(count), name, bool(ripe)) for stage, ripe, count, name in found}


def test_the_plots_count_each_stage(board_client):
    html = _page(board_client)
    plots = _plots(html)
    assert tuple(plots) == STAGES
    assert plots == {
        "seed": (2, "Seed", False),
        "sprouting": (2, "Sprouting", False),
        "planted": (6, "Planted", False),
        "ripe": (2, "Ripe", True),
        "harvested": (2, "Harvested", False),
    }
    assert 'id="totals"' not in html  # the plots replace the totals row


def test_ripe_s_plot_is_plain_with_no_card(board_client):
    assert _plots(_page(board_client, "?q=duck"))["ripe"] == (0, "Ripe", False)


def test_without_scripts_every_stage_is_in_the_page(board_client):
    html = _page(board_client)
    assert re.findall(r'<section id="stage-([a-z]+)"', html) == list(STAGES)
    assert not re.search(r'<section id="stage-[a-z]+"[^>]*hidden', html)


def test_the_page_posts_only_a_reorder_and_links_to_the_factory_floor(board_client):
    html = _page(board_client)
    main = html.split("<main>", 1)[1]
    # the board's script picks the stage shown on a phone and sends the order (F15 D3), from
    # the line the page holds
    scripts = re.findall(r"<script[^>]*>", main)
    assert len(scripts) == 2
    assert scripts[0] == '<script type="application/json" id="board-line">'
    assert re.fullmatch(r'<script src="/static/board\.js\?v=[0-9a-f]{10}">', scripts[1])
    assert "hx-post" not in main
    assert "Read-only" not in main
    script = (STATIC / "board.js").read_text(encoding="utf-8")
    # the order, and a card's Set aside from its ⋯ (f15-06)
    assert re.findall(r'kind: "(\w+)"', script) == ["archive", "reorder"]
    assert script.count('fetch("/requests"') == 2
    assert re.search(
        r'<a href="/\?project=coucou">\s*Planted cards feed the factory floor ›\s*</a>', main
    )


def test_the_top_bar_has_a_board_tab_right_after_planning(board_client):
    tabs = re.findall(r'<nav class="tabs"[^>]*>(.*?)</nav>', board_client.get("/").text, re.S)[0]
    paths = re.findall(r'href="([^"?]*)\?', tabs)
    assert paths[:4] == ["/projects", "/", "/planning", "/board"]  # Projects first (ADR 30)
    assert re.search(r'<a href="/board\?project=coucou">Board</a>', tabs)
    assert re.search(
        r'<a href="/board\?project=coucou" aria-current="page">Board</a>', _page(board_client)
    )


def test_the_board_replaces_the_milestones_tab_and_links_to_the_list(board_client):
    """The owner, 2026-10-06: the board is how milestones are found (f5-17). The list keeps
    each card's priority and the trends, so it still answers and the board links to it."""
    html = _page(board_client)
    tabs = re.findall(r'<nav class="tabs"[^>]*>(.*?)</nav>', html, re.S)[0]
    assert "/milestones" not in re.findall(r'href="([^"?]*)\?', tabs)
    assert "Milestones" not in tabs
    assert board_client.get("/milestones").status_code == 200
    main = html.split("<main>", 1)[1]
    assert re.search(
        r'<a href="/milestones\?project=coucou">\s*All milestones and their trends ›\s*</a>', main
    )


def test_a_milestone_s_card_is_found_by_its_full_key_however_old(db_path):
    """The board keeps the latest four harvested cards; a milestone's page finds its own."""

    def change(conn: sqlite3.Connection, p: int) -> None:
        for day, key in enumerate(("m4", "f1", "f30", "f31", "f32", "f33"), start=1):
            metrics.upsert_milestone(
                conn, p, key, status="done", ended=f"2026-09-{day:02d}T12:00:00+02:00"
            )
        metrics.upsert_milestone(conn, p, "f26-gone", state=metrics.REMOVED)

    write(db_path, change)
    assert "M4" not in keys(read(db_path), "harvested")
    conn = connect(db_path)
    try:
        oldest = milestone_card(conn, PROJECT, NOW, "m4")
        assert oldest is not None
        assert (oldest.key, oldest.stage, oldest.area) == ("M4", "harvested", "product")
        assert milestone_card(conn, PROJECT, NOW, "f26-gone") is None  # a removed card
        assert milestone_card(conn, PROJECT, NOW, "nowhere") is None
    finally:
        conn.close()


def test_a_bug_s_ticket_id_is_no_milestone_s_card(board_db):
    conn = connect(board_db)
    try:
        assert milestone_card(conn, PROJECT, NOW, "bug-01-duck-count") is None
        assert milestone_card(conn, PROJECT, NOW, "bugs") is None
    finally:
        conn.close()


@pytest.mark.parametrize("size", [PHONE, DISPLAY], ids=["phone", "display"])
def test_the_board_lays_out_at_phone_and_display_sizes(page, board_client, size):
    page.set_viewport_size(size)
    open_page(page, board_client, "/board")
    page.evaluate("() => document.fonts.ready")
    # the tabs scroll sideways on a phone by design, as test_planning.py's layout test has it
    page.evaluate("() => document.querySelector('nav.tabs').setAttribute('data-layout', 'overlay')")
    assert layout_problems(page) == []
    assert page.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth"), (
        "the page scrolls sideways"
    )
    plots = page.evaluate(
        "() => [...document.querySelectorAll('.plot')].map((el) => {"
        " const r = el.getBoundingClientRect();"
        " return {top: Math.round(r.top), left: r.left, right: r.right, height: r.height}; })"
    )
    assert len(plots) == 5
    assert all(p["left"] >= 0 and p["right"] <= size["width"] for p in plots)
    rows = [p["top"] for p in plots]
    tops = page.evaluate(
        "() => [...document.querySelectorAll('.stage')]"
        ".filter((el) => el.getBoundingClientRect().height > 0)"
        ".map((el) => [el.id.replace('stage-', ''), el.getBoundingClientRect().top])"
    )
    lefts = page.evaluate(
        "() => [...document.querySelectorAll('.stage')]"
        ".map((el) => el.getBoundingClientRect().left)"
    )
    if size is PHONE:
        assert rows == sorted(rows) and len(set(rows)) == 2, "three plots to a row"
        assert rows[0] == rows[2] and rows[3] == rows[4]
        assert all(p["height"] >= 44 for p in plots)
        assert [stage for stage, _ in tops] == ["planted"]  # one stage at a time
        assert page.locator(".plot.at-planted").get_attribute("aria-pressed") == "true"
        assert page.locator('.plot[aria-pressed="true"]').count() == 1
        small = page.evaluate(
            """() => [...document.querySelectorAll(
                    '.board a, .board button, .board input:not([type=hidden])')]
                .filter((el) => el.getBoundingClientRect().height > 0)  // shown
                .filter((el) => el.getBoundingClientRect().height < 44)
                .map((el) => el.textContent.trim() || el.name)"""
        )
        assert small == [], f"tap targets under 44 px: {small}"
    else:
        assert len(set(rows)) == 1, "the five plots sit in one row"
        assert [stage for stage, _ in tops] == list(STAGES)
        assert len({top for _, top in tops}) == 1, "the columns sit side by side"
        assert lefts == sorted(lefts)


def _shown(page) -> list[str]:
    """The stages whose column shows."""
    shown: list[str] = page.evaluate(
        "() => [...document.querySelectorAll('.stage')]"
        ".filter((el) => el.getBoundingClientRect().height > 0)"
        ".map((el) => el.id.replace('stage-', ''))"
    )
    return shown


def test_a_tap_on_a_plot_shows_its_stage_alone_on_a_phone(page, board_client):
    page.set_viewport_size(PHONE)
    open_page(page, board_client, "/board")
    seed = page.locator(".plot.at-seed")
    assert seed.get_attribute("aria-pressed") == "false"
    seed.click()
    assert _shown(page) == ["seed"]
    assert seed.get_attribute("aria-pressed") == "true"
    assert page.locator('.plot[aria-pressed="true"]').count() == 1
    # a stage with no card shows too, saying so
    open_page(page, board_client, "/board?q=duck")
    page.locator(".plot.at-ripe").click()
    assert _shown(page) == ["ripe"]
    assert page.locator("#stage-ripe .empty").is_visible()


def test_the_address_names_the_stage_shown_on_a_phone(page, board_client):
    page.set_viewport_size(PHONE)
    open_page(page, board_client, "/board#stage-ripe")
    assert _shown(page) == ["ripe"]
    assert page.locator(".plot.at-ripe").get_attribute("aria-pressed") == "true"
    page.goto(f"{ORIGIN}/board#stage-seed")  # a new hash, the same page
    assert _shown(page) == ["seed"]
    page.goto(f"{ORIGIN}/board?q=#stage-nowhere")  # a stage no plot names
    assert _shown(page) == ["planted"]


def test_without_scripts_a_phone_stacks_every_stage_with_cards(browser, board_client):
    page = browser.new_page(java_script_enabled=False, viewport=PHONE)
    try:
        open_page(page, board_client, "/board")
        tops = page.evaluate(
            "() => Object.fromEntries([...document.querySelectorAll('.stage')]"
            ".filter((el) => el.getBoundingClientRect().height > 0)"
            ".map((el) => [el.id.replace('stage-', ''), el.getBoundingClientRect().top]))"
        )
        # what needs the owner and what runs come first (the owner, 2026-10-03)
        order = sorted(tops, key=lambda stage: tops[stage])
        assert order == ["ripe", "planted", "sprouting", "seed", "harvested"]
        assert page.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth")
    finally:
        page.close()


@pytest.mark.parametrize("size", [PHONE, DISPLAY], ids=["phone", "display"])
def test_ripe_card_words_fit_inside_the_card(page, board_client, size):
    page.set_viewport_size(size)
    open_page(page, board_client, "/board#stage-ripe")
    page.evaluate("() => document.fonts.ready")
    cards = page.query_selector_all("#stage-ripe .card")
    assert cards
    for card in cards:
        assert "Read the review and sign off" in card.inner_text()
        box, words = card.bounding_box(), card.query_selector(".card-action").bounding_box()
        assert box and words
        assert box["x"] <= words["x"] and words["x"] + words["width"] <= box["x"] + box["width"] + 1


@pytest.mark.parametrize("size", [PHONE, DISPLAY], ids=["phone", "display"])
def test_the_on_its_way_line_fits_inside_the_card(page, board_db, size):
    write(board_db, _reorder('["bug-02-stale"]'))
    page.set_viewport_size(size)
    open_page(page, _client(board_db), "/board")
    page.evaluate("() => document.fonts.ready")
    (moved,) = page.query_selector_all(".card.on-its-way")
    stage = moved.evaluate("el => el.closest('.stage').id.replace('stage-', '')")
    page.locator(f".plot.at-{stage}").click()
    box, words = moved.bounding_box(), moved.query_selector(".card-way").bounding_box()
    assert box and words
    assert box["x"] <= words["x"] and words["x"] + words["width"] <= box["x"] + box["width"] + 1
    page.evaluate("() => document.querySelector('nav.tabs').setAttribute('data-layout', 'overlay')")
    assert layout_problems(page) == []


@pytest.mark.parametrize("width", [700, 1000])
def test_nothing_scrolls_sideways_on_a_narrow_desktop(page, board_client, width):
    """Under 900 px one stage shows, from 900 px the six fit: neither scrolls sideways."""
    page.set_viewport_size({"width": width, "height": 800})
    open_page(page, board_client, "/board")
    field = page.locator("#field")
    assert field.evaluate("el => el.scrollWidth <= el.clientWidth + 1")
    assert page.evaluate(
        "() => document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert _shown(page) == (["planted"] if width < 900 else list(STAGES))
    # from 900 px a plot is a count: a press changes nothing shown
    page.locator(".plot.at-seed").click()
    assert _shown(page) == (["seed"] if width < 900 else list(STAGES))


def test_ripe_card_says_read_the_review_and_signs_off(board_db, board_client):
    html = _page(board_client)
    found = read(board_db)
    for c in found.stages["ripe"]:
        link = f"/milestones/{c.full_key}"
        _, words, _ = _card(html, link)
        assert "Read the review and sign off" in words
        assert "softfield signoff" not in words


def test_ripe_card_link_ends_with_review_fragment(board_db, board_client):
    html = _page(board_client)
    found = read(board_db)
    for c in found.stages["ripe"]:
        link = f"/milestones/{c.full_key}"
        _card(html, link)
        match = re.search(rf'<a class="card[^"]*" href="{re.escape(link)}\?[^"]*#review">', html)
        assert match, f"link for {link} should end with #review"


def test_planted_and_harvested_cards_have_no_review_fragment(board_db, board_client):
    html = _page(board_client)
    found = read(board_db)
    for stage in ("planted", "harvested"):
        for c in found.stages[stage]:
            link = f"{'/tickets' if c.bug else '/milestones'}/{c.full_key}"
            _, words, _ = _card(html, link)
            match = re.search(
                rf'<a class="card[^"]*" href="{re.escape(link)}\?[^"]*#review">', html
            )
            assert match is None, f"{stage} card {link} should not have #review"
            if stage == "harvested":
                assert "Read the review and sign off" not in words


# --- moving cards and sending the order (f15-04) ---------------------------------------------


STARTED = ["bug-03-working", "bug-04-stuck", "f25"]  # the planted cards after F27, all started


def _three_planted(page, board_db: Path, size: dict[str, int] = PHONE) -> None:
    """The board in Chromium with three planted cards not started, F23, bug-02-stale, F27,
    after the started F24 and before the ``STARTED`` ones: one line (F154 D1)."""
    write(board_db, _planted(("f27-third", 9)))
    page.set_viewport_size(size)
    open_page(page, _client(board_db), "/board")
    assert _order(page, "planted") == ["f24", "f23", "bug-02-stale", "f27", *STARTED]


def _order(page, stage: str) -> list[str]:
    order: list[str] = page.evaluate(
        f"() => [...document.querySelectorAll('#stage-{stage} .slot')].map((s) => s.dataset.key)"
    )
    return order


def _drag(page, key: str, onto: str, *, below: bool = False) -> None:
    """Drag ``key``'s card by its grip and drop it over the top (or bottom) fifth of ``onto``,
    the two cards in the middle of the screen first, clear of the bar: one Planted column is
    taller than a phone (F154 D1)."""
    page.evaluate(
        """([a, b]) => {
            const box = (k) =>
                document.querySelector(`.slot[data-key="${k}"]`).getBoundingClientRect();
            const top = Math.min(box(a).top, box(b).top);
            const bottom = Math.max(box(a).bottom, box(b).bottom);
            scrollBy(0, (top + bottom) / 2 - innerHeight / 2);
        }""",
        [key, onto],
    )
    grip = page.locator(f'.slot[data-key="{key}"] .grip').bounding_box()
    target = page.locator(f'.slot[data-key="{onto}"]').bounding_box()
    assert grip and target
    page.mouse.move(grip["x"] + grip["width"] / 2, grip["y"] + grip["height"] / 2)
    page.mouse.down()
    y = target["y"] + target["height"] * (0.8 if below else 0.2)
    page.mouse.move(target["x"] + target["width"] / 2, y, steps=8)
    page.mouse.up()


def _words(page, key: str) -> str:
    return " ".join(page.locator(f'.slot[data-key="{key}"] .card').inner_text().split())


def _bar(page) -> str | None:
    """The bar's words, None while it is hidden."""
    bar = page.locator("#order-bar")
    return " ".join(bar.locator("p").inner_text().split()) if bar.is_visible() else None


def test_dragging_a_card_by_its_grip_moves_it_and_back_again(page, board_db):
    _three_planted(page, board_db)
    _drag(page, "f27", "f24")  # a card not started, above a started one (F154 D1)
    assert _order(page, "planted") == ["f27", "f24", "f23", "bug-02-stale", *STARTED]
    moved = page.locator('.slot[data-key="f27"] .card')
    assert "moved" in (moved.get_attribute("class") or "").split()
    assert moved.evaluate("el => getComputedStyle(el).borderTopStyle") == "dashed"
    assert _words(page, "f27").startswith("#1 F27")
    assert "moved · was #4 · not sent yet" in _words(page, "f27")
    # the cards it passed are not moved, but their places change
    assert page.locator(".card.moved").count() == 1
    assert _words(page, "f24").startswith("#2 F24")
    assert _bar(page) == "1 card moved. Nothing is sent yet."
    assert page.get_by_role("button", name="Send new order").is_visible()
    assert page.get_by_role("button", name="Cancel").is_visible()

    _drag(page, "f27", "bug-02-stale", below=True)  # back to fourth
    assert _order(page, "planted") == ["f24", "f23", "bug-02-stale", "f27", *STARTED]
    assert page.locator(".card.moved").count() == 0
    assert "moved" not in _words(page, "f27")
    assert _words(page, "f27").startswith("#4 F27")
    assert _bar(page) is None


def test_the_menu_does_the_same_moves_by_keyboard_too(page, board_db):
    _three_planted(page, board_db)
    more = page.locator('.slot[data-key="f27"] .more')
    assert more.get_attribute("aria-label") == "Actions for F27"
    more.focus()
    page.keyboard.press("Enter")
    sheet = page.locator("#order-sheet")
    assert sheet.is_visible()
    page.keyboard.press("Enter")  # Top, the first button, has the focus
    assert not sheet.is_visible()
    assert _order(page, "planted") == ["f27", "f24", "f23", "bug-02-stale", *STARTED]
    assert page.evaluate("() => document.activeElement.closest('.slot').dataset.key") == "f27"
    for move, order in (
        ("Down", ["f24", "f27", "f23", "bug-02-stale", *STARTED]),
        ("Bottom", ["f24", "f23", "bug-02-stale", *STARTED, "f27"]),
        ("Up", ["f24", "f23", "bug-02-stale", *STARTED[:2], "f27", "f25"]),
    ):
        page.keyboard.press("Enter")  # the focus is back on F27's ⋯
        page.get_by_role("button", name=move, exact=True).focus()
        page.keyboard.press("Enter")
        assert _order(page, "planted") == order, move
    assert "moved · was #4 · not sent yet" in _words(page, "f27")
    page.keyboard.press("Enter")
    page.keyboard.press("Escape")
    assert not sheet.is_visible()


def test_cancel_puts_the_order_back(page, board_db):
    _three_planted(page, board_db)
    _drag(page, "f27", "f23")
    _drag(page, "f23", "bug-02-stale", below=True)  # the two ends swapped
    assert _order(page, "planted") == ["f24", "f27", "bug-02-stale", "f23", *STARTED]
    assert page.locator(".card.moved").count() == 2
    assert _bar(page) == "2 cards moved. Nothing is sent yet."
    page.get_by_role("button", name="Cancel").click()
    assert _order(page, "planted") == ["f24", "f23", "bug-02-stale", "f27", *STARTED]
    assert page.locator(".card.moved").count() == 0
    assert _bar(page) is None


# --- a card's actions in its ⋯ menu (f15-06) ---------------------------------------------------


def _actions(html: str, key: str) -> list[tuple[str, str]] | None:
    """The actions in the slot of the card ``key`` (lower case), each as its words and where it
    goes: a link's ``href``, a Set aside button's ``data-thread`` (``disabled`` after it when
    disabled). None when the slot has no actions."""
    found = re.search(
        rf'<div class="slot[^"]*" data-key="{re.escape(key)}"[^>]*>(.*?)</div>', html, re.S
    )
    assert found, key
    template = re.search(r'<template class="card-actions">(.*?)</template>', found[1], re.S)
    if template is None:
        return None
    actions = []
    for tag, attrs, words in re.findall(r"<(a|button)([^>]*)>(.*?)</\1>", template[1], re.S):
        if tag == "a":
            where = unescape(re.search(r'href="([^"]*)"', attrs)[1])  # type: ignore[index]
        else:
            assert 'class="set-aside"' in attrs and 'type="button"' in attrs
            where = re.search(r'data-thread="([^"]*)"', attrs)[1]  # type: ignore[index]
            where += " disabled" if re.search(r"\sdisabled\b", attrs) else ""
        actions.append((unescape(" ".join(words.split())), where))
    return actions


def test_each_placed_card_s_actions_lead_to_its_conversation_set_aside_and_its_page(
    board_db, board_client
):
    """F21 sprouts on a thread; F22 sprouts from its plan with none; F20 is a seed with none;
    F23 is planted and given a thread here."""
    write(board_db, lambda conn, p: metrics.planner_thread(conn, p, "f23", NOW.isoformat()))
    html = _page(board_client)
    q = "?project=coucou"
    assert _actions(html, "f21") == [
        ("Open its conversation", f"/planning/f21{q}"),
        ("Set aside", "f21"),
        ("Open the card", f"/milestones/f21-parallel{q}"),
    ]
    assert _actions(html, "f22") == [("Open the card", f"/milestones/f22-research{q}")]
    assert _actions(html, "f20") == [("Open the card", f"/milestones/f20-duck-pond{q}")]
    # a planted card keeps its conversation but isn't set aside from the board
    assert _actions(html, "f23") == [
        ("Open its conversation", f"/planning/f23{q}"),
        ("Open the card", f"/milestones/f23-planted{q}"),
    ]
    # a bug has no conversation, seed or planted
    assert _actions(html, "bug-01-duck-count") == [
        ("Open the card", f"/tickets/bug-01-duck-count{q}")
    ]
    assert _actions(html, "bug-02-stale") == [("Open the card", f"/tickets/bug-02-stale{q}")]
    # every placed card's last action is its own card's link; ripe and harvested have none
    columns = _columns(html)
    for stage in STAGES:
        for key in re.findall(r'<div class="slot[^"]*" data-key="([^"]+)"', columns[stage]):
            actions = _actions(html, key)
            if stage in ("ripe", "harvested"):
                assert actions is None, key
                continue
            link = re.search(
                rf'data-key="{re.escape(key)}"[^>]*>\s*<a class="card[^"]*" href="([^"]+)"', html
            )
            assert link and actions and actions[-1] == ("Open the card", unescape(link[1])), key


def test_a_card_set_aside_on_its_way_says_so_and_can_t_be_pressed_again(board_db, board_client):
    def ask(conn: sqlite3.Connection, project: int) -> None:
        metrics.planner_thread(conn, project, "f20", NOW.isoformat())
        metrics.add_request(conn, project, "archive", "f21", "on", NOW.isoformat())
        # another thread's request, one taking it back, and one done: none of them is F20's
        metrics.add_request(conn, project, "archive", "f20", "off", NOW.isoformat())
        done = metrics.add_request(conn, project, "archive", "f22", "on", NOW.isoformat())
        conn.execute("UPDATE owner_requests SET done = ? WHERE id = ?", (NOW.isoformat(), done))
        conn.commit()

    write(board_db, ask)
    found = read(board_db)
    assert (card(found, "F21").thread, card(found, "F21").setting_aside) == ("f21", True)
    assert (card(found, "F20").thread, card(found, "F20").setting_aside) == ("f20", False)
    assert (card(found, "F22").thread, card(found, "F22").setting_aside) == ("", False)
    assert card(found, "bug-01-duck-count").thread == ""
    html = _page(board_client)
    assert ("Set aside · on its way", "f21 disabled") in (_actions(html, "f21") or [])
    assert ("Set aside", "f20") in (_actions(html, "f20") or [])


def test_the_menu_shows_a_card_s_actions_under_its_moves_and_sets_it_aside(page, board_db):
    page.set_viewport_size(PHONE)
    open_page(page, _client(board_db), "/board")
    page.get_by_role("button", name="Sprouting").click()
    posts: list[str] = []
    page.on("request", lambda r: posts.append(r.url) if r.method == "POST" else None)
    page.locator('.slot[data-key="f21"] .more').click()
    sheet = page.locator("#order-sheet")
    assert sheet.is_visible()
    buttons = [" ".join(t.split()) for t in sheet.locator("button, a").all_inner_texts()]
    # upper case in the sheet, as its buttons are drawn
    assert [b.lower() for b in buttons] == [
        "top",
        "up",
        "down",
        "bottom",
        "open its conversation",
        "set aside",
        "open the card",
        "close",
    ]
    for action in sheet.locator(".order-actions > *").all():
        box = action.bounding_box()
        assert box and box["height"] >= 44
    assert sheet.get_by_role("link", name="Open its conversation").get_attribute("href") == (
        "/planning/f21?project=coucou"
    )
    aside = sheet.get_by_role("button", name="Set aside")
    aside.click()
    page.wait_for_function(
        "() => document.querySelector('#order-sheet .set-aside').textContent"
        " === 'Set aside · on its way'"
    )
    assert aside.is_disabled()
    assert posts == [f"{ORIGIN}/requests"]
    conn = connect(board_db)
    try:
        rows = conn.execute("SELECT kind, subject, value, done FROM owner_requests").fetchall()
    finally:
        conn.close()
    assert [tuple(r) for r in rows] == [("archive", "f21", "on", None)]
    # another card's ⋯ shows its own actions, not F21's
    page.keyboard.press("Escape")
    page.get_by_role("button", name="Seed").click()
    page.locator('.slot[data-key="f20"] .more').click()
    assert [
        " ".join(t.split()).lower() for t in sheet.locator(".order-actions > *").all_inner_texts()
    ] == ["open the card"]


def test_send_posts_the_whole_open_order_once_and_the_board_shows_it_on_its_way(page, board_db):
    _three_planted(page, board_db)
    line = [key for key, _ in read(board_db).line]
    posts: list[str] = []
    page.on("request", lambda r: posts.append(r.url) if r.method == "POST" else None)
    _drag(page, "f27", "f23")
    page.get_by_role("button", name="Send new order").click()
    page.locator(".slot[data-key=f27] .card.on-its-way").wait_for()
    assert posts == [f"{ORIGIN}/requests"]
    conn = connect(board_db)
    try:
        rows = conn.execute("SELECT kind, subject, value, done FROM owner_requests").fetchall()
    finally:
        conn.close()
    assert [(r["kind"], r["subject"], r["done"]) for r in rows] == [("reorder", None, None)]
    sent = json.loads(rows[0]["value"])
    line.remove("f27")
    line.insert(line.index("f23"), "f27")
    assert sent == line  # every open card once, F27 just before the card it was dropped above
    assert "on its way · was #4 · at the runner's next pick" in _words(page, "f27")
    assert _words(page, "f27").startswith("#2 F27")
    assert _bar(page) is None
    # the cards stay draggable: a second order is held until it is sent
    _drag(page, "f23", "f27")
    assert _bar(page) == "1 card moved. Nothing is sent yet."
    assert posts == [f"{ORIGIN}/requests"]


def _requests(board_db: Path) -> list[tuple[str, str | None]]:
    conn = connect(board_db)
    try:
        rows = conn.execute("SELECT kind, subject FROM owner_requests").fetchall()
    finally:
        conn.close()
    return [(r["kind"], r["subject"]) for r in rows]


def test_a_refused_send_keeps_the_moves_and_a_second_press_sends_them(page, board_db):
    _three_planted(page, board_db)
    _drag(page, "f27", "f23")
    moved = ["f24", "f27", "f23", "bug-02-stale", *STARTED]
    assert _order(page, "planted") == moved
    page.route("**/requests", lambda route: route.fulfill(status=500))
    send = page.get_by_role("button", name="Send new order")
    send.click()
    refused = "Not sent: the dashboard didn't take it. Your moves are kept; try again."
    page.wait_for_function(
        "(words) => document.querySelector('#order-bar p').textContent === words", arg=refused
    )
    assert _bar(page) == refused
    assert send.is_enabled()
    assert _order(page, "planted") == moved
    assert "moved · was #4 · not sent yet" in _words(page, "f27")
    assert page.locator(".slot[data-key=f27] .card.on-its-way").count() == 0
    assert _requests(board_db) == []
    # the dashboard takes it now: the same moves go at the second press
    page.unroute("**/requests")
    send.click()
    page.locator(".slot[data-key=f27] .card.on-its-way").wait_for()
    assert _requests(board_db) == [("reorder", None)]
    assert "on its way · was #4 · at the runner's next pick" in _words(page, "f27")


def test_a_refused_set_aside_can_be_pressed_again(page, board_db):
    page.set_viewport_size(PHONE)
    open_page(page, _client(board_db), "/board")
    page.get_by_role("button", name="Sprouting").click()
    page.locator('.slot[data-key="f21"] .more').click()
    page.route("**/requests", lambda route: route.fulfill(status=500))
    aside = page.locator("#order-sheet").get_by_role("button", name="Set aside")
    aside.click()
    page.wait_for_function(
        "() => document.querySelector('#order-sheet .set-aside').textContent"
        " === 'Set aside · not sent, try again'"
    )
    assert aside.is_enabled()
    assert _requests(board_db) == []


def test_a_card_stays_in_its_stage_and_a_ripe_or_harvested_one_has_no_grip(page, board_db):
    _three_planted(page, board_db, DISPLAY)
    sprouting = _order(page, "sprouting")
    _drag(page, "f23", "f22")  # over the sprouting column: it lands in its own
    assert sorted(_order(page, "planted")) == sorted(
        ["f24", "f23", "bug-02-stale", "f27", *STARTED]
    )
    assert _order(page, "sprouting") == sprouting
    for stage in ("ripe", "harvested"):
        assert page.locator(f"#stage-{stage} .card").count()
        assert page.locator(f"#stage-{stage} .grip, #stage-{stage} .more").count() == 0
    for stage in ("seed", "sprouting", "planted"):
        assert (
            page.locator(f"#stage-{stage} .grip").count()
            == page.locator(f"#stage-{stage} .card").count()
        )
    assert page.locator(".grip").first.evaluate("el => getComputedStyle(el).touchAction") == "none"


def test_a_drag_near_the_bottom_edge_scrolls_the_page(page, board_db):
    write(board_db, _planted(*((f"f{n}-more", 9) for n in range(40, 56))))
    page.set_viewport_size(PHONE)
    open_page(page, _client(board_db), "/board")
    assert page.evaluate("() => scrollY") == 0
    grip = page.locator(".slot[data-key=f23] .grip").bounding_box()
    assert grip
    page.mouse.move(grip["x"] + 20, grip["y"] + 20)
    page.mouse.down()
    page.mouse.move(grip["x"] + 20, PHONE["height"] - 10, steps=4)
    page.wait_for_function("() => scrollY > 200")
    page.mouse.up()


# --- waits (f15-08) ------------------------------------------------


def test_review_next_running_stopped(board_db):
    """F25: no review job and no stop → "Review next"; live review job
    → "Review running"; another role → "Review next"; unresolved
    review-stop → "Review stopped"; resolved → "Review next"."""
    # default: "Review next"
    f25 = card(read(board_db), "F25")
    assert f25.review_step is not None
    assert f25.review_step.label == "Review next"

    # live review job by claude-opus → "Review running"
    def add_review_job(conn: sqlite3.Connection, p: int) -> None:
        run = metrics.upsert_run(conn, p, "20261002-120000", heartbeat=NOW.isoformat())
        m = conn.execute("SELECT id FROM milestones WHERE key = ?", ("f25-unreviewed",)).fetchone()
        metrics.start_job(
            conn,
            run,
            ticket_id=None,
            milestone_id=m["id"],
            role="review",
            agent=OPUS,
            attempt=1,
            started=NOW.isoformat(),
        )

    write(board_db, add_review_job)
    f25 = card(read(board_db), "F25")
    assert f25.review_step is not None
    assert f25.review_step.label == "Review running"
    assert f25.review_step.text == f"{OPUS} reads the work · then it's yours to sign off"

    # live job of another role → "Review next" (not a review role)
    def change_to_developer(conn: sqlite3.Connection, p: int) -> None:
        sql = (
            "SELECT id FROM jobs WHERE milestone_id = "
            "(SELECT id FROM milestones WHERE key = ?) "
            "AND outcome = 'running'"
        )
        jobs = conn.execute(sql, ("f25-unreviewed",)).fetchall()
        for j in jobs:
            conn.execute("UPDATE jobs SET role = ? WHERE id = ?", ("developer", j["id"]))

    write(board_db, change_to_developer)
    f25 = card(read(board_db), "F25")
    assert f25.review_step is not None
    assert f25.review_step.label == "Review next"

    # unresolved review-stop → "Review stopped"
    def add_review_stop(conn: sqlite3.Connection, p: int) -> None:
        metrics.upsert_owner_item(
            conn,
            p,
            "review-stop",
            "f25-unreviewed",
            text="end-to-end tests fail on staging",
            created=NOW.isoformat(),
        )

    write(board_db, add_review_stop)
    f25 = card(read(board_db), "F25")
    assert f25.review_step is not None
    assert f25.review_step.label == "Review stopped"
    assert f25.review_step.text == "end-to-end tests fail on staging · shown under Needs you"

    # resolved review-stop → "Review next"
    def resolve_review_stop(conn: sqlite3.Connection, p: int) -> None:
        item = conn.execute(
            "SELECT id FROM owner_items WHERE kind = 'review-stop' AND subject = ?",
            ("f25-unreviewed",),
        ).fetchone()
        conn.execute(
            "UPDATE owner_items SET resolved = ? WHERE id = ?", (NOW.isoformat(), item["id"])
        )

    write(board_db, resolve_review_stop)
    f25 = card(read(board_db), "F25")
    assert f25.review_step is not None
    assert f25.review_step.label == "Review next"


def test_no_step_on_cards_not_started_or_not_done(board_db):
    """A started card with a ticket not done, a planted card not started with none left to
    do, a ripe card and a bug have no step (F154: started, not a stage, asks for it)."""
    # F24 is started but has a ticket not done
    f24 = card(read(board_db), "F24")
    assert f24.review_step is None

    # F28: its only ticket set aside, so none counted is left to do, and none started
    def nothing_started(conn: sqlite3.Connection, p: int) -> None:
        m = metrics.upsert_milestone(conn, p, "f28-quiet", title="Quiet", state="ready")
        metrics.upsert_ticket(conn, p, "f28-01-only", milestone_id=m, state="later")

    write(board_db, nothing_started)
    f28 = card(read(board_db), "F28")
    assert (f28.stage, f28.started, f28.review_step) == ("planted", False, None)

    # F1 is ripe
    f1 = card(read(board_db), "F1")
    assert f1.review_step is None

    # a bug
    bug = card(read(board_db), "bug-03-working")
    assert bug.review_step is None


def test_board_page_shows_review_step(board_db, board_client):
    """The board page shows the step inside F25's card."""
    html = _page(board_client)
    _, words, _ = _card(html, "/milestones/f25-unreviewed")
    assert "Review next" in words
    assert "Claude reviews it before the next ticket" in words


def test_set_aside_says_wont_run(board_db, board_client):
    """A card with one set-aside ticket reads
    "1 set aside, won't run" on the board and on its page."""
    # F24 has one set aside ticket (f24-04-later)
    found = read(board_db)
    f24 = card(found, "F24")
    assert f24.set_aside == 1
    html = _page(board_client)
    _, words, _ = _card(html, "/milestones/f24-growing")
    assert "1 set aside, won't run" in words


def test_milestone_page_shows_review_step_on_stage_line(board_client):
    """F25's page shows the step on its Stage line."""
    html = board_client.get("/milestones/f25-unreviewed").text
    match = re.search(r"<dt>Stage</dt><dd[^>]*>(.*?)</dd>", html, re.S)
    assert match, "no Stage dd"
    stage_text = " ".join(re.sub(r"<[^>]+>", " ", match.group(1)).split())
    assert "review next" in stage_text
    assert "Claude reviews it before the next ticket" in stage_text


def test_a_planted_card_says_what_it_waits_for(board_db):
    """A planted card whose only ready ticket depends on F22's unfinished ticket has
    ``waits == ("F22",)`` and its card reads "waits for F22"."""

    def change(conn: sqlite3.Connection, p: int) -> None:
        # create f22's ticket that will be a dependency target
        f22 = metrics.upsert_milestone(
            conn, p, "f22-research", title="Research", state="planning", priority=10, area="factory"
        )
        metrics.upsert_ticket(
            conn, p, "f22-01-unfinished", milestone_id=f22, kind="developer", state="ready"
        )
        # make f23-01-first depend on f22-01-unfinished, and f23-02-second set aside
        conn.execute(
            "UPDATE tickets SET depends_on = ? WHERE ticket = ?",
            (json.dumps(["f22-01-unfinished"]), "f23-01-first"),
        )
        conn.execute(
            "UPDATE tickets SET state = ? WHERE ticket = ?",
            ("later", "f23-02-second"),
        )

    write(board_db, change)
    found = read(board_db)
    f23 = card(found, "F23")
    assert f23.stage == "planted"
    assert f23.waits == ("F22",)
    html = _page(_client(board_db))
    assert _card_note(html, "/milestones/f23-planted") == "waits for F22"


def test_two_ready_tickets_one_free_means_no_waits(board_db):
    """With two ready tickets, one depending on F22's unfinished ticket and one free,
    ``waits`` is empty and the card shows no such line."""

    def change(conn: sqlite3.Connection, p: int) -> None:
        # create f22's ticket
        f22 = metrics.upsert_milestone(
            conn, p, "f22-research", title="Research", state="planning", priority=10, area="factory"
        )
        metrics.upsert_ticket(
            conn, p, "f22-01-unfinished", milestone_id=f22, kind="developer", state="ready"
        )
        # f23-01-first depends on f22-01-unfinished, but f23-02-second is free
        conn.execute(
            "UPDATE tickets SET depends_on = ? WHERE ticket = ?",
            (json.dumps(["f22-01-unfinished"]), "f23-01-first"),
        )

    write(board_db, change)
    found = read(board_db)
    f23 = card(found, "F23")
    assert f23.waits == ()
    html = _page(_client(board_db))
    _, words, _ = _card(html, "/milestones/f23-planted")
    assert "waits for" not in words


def test_ready_tickets_depend_on_two_other_cards(board_db):
    """With ready tickets depending on unfinished tickets of F22 and F63, the line reads
    "waits for F22, F63", each once."""

    def change(conn: sqlite3.Connection, p: int) -> None:
        # create f22 and f63 milestones
        f22 = metrics.upsert_milestone(
            conn, p, "f22-research", title="Research", state="planning", priority=10, area="factory"
        )
        metrics.upsert_ticket(
            conn, p, "f22-01-unfinished", milestone_id=f22, kind="developer", state="ready"
        )
        f63 = metrics.upsert_milestone(
            conn, p, "f63-later", title="Later", state="planning", priority=10, area="product"
        )
        metrics.upsert_ticket(
            conn, p, "f63-01-unfinished", milestone_id=f63, kind="developer", state="ready"
        )
        # f23-01-first depends on f22-01-unfinished, f23-02-second depends on f63-01-unfinished
        conn.execute(
            "UPDATE tickets SET depends_on = ? WHERE ticket = ?",
            (json.dumps(["f22-01-unfinished"]), "f23-01-first"),
        )
        conn.execute(
            "UPDATE tickets SET depends_on = ? WHERE ticket = ?",
            (json.dumps(["f63-01-unfinished"]), "f23-02-second"),
        )

    write(board_db, change)
    found = read(board_db)
    f23 = card(found, "F23")
    assert f23.waits == ("F22", "F63")
    html = _page(_client(board_db))
    assert _card_note(html, "/milestones/f23-planted") == "waits for F22, F63"


def test_a_card_waiting_on_a_bug_names_the_bug(board_db):
    """A bug's card is its ticket: the note names it, not the standing ``bugs`` key."""

    def change(conn: sqlite3.Connection, p: int) -> None:
        conn.execute("UPDATE tickets SET state = 'later' WHERE ticket = 'f23-02-second'")
        conn.execute(
            "UPDATE tickets SET depends_on = ? WHERE ticket = 'f23-01-first'",
            (json.dumps(["bug-02-stale"]),),
        )

    write(board_db, change)
    assert card(read(board_db), "F23").waits == ("bug-02-stale",)
    html = _page(_client(board_db))
    assert _card_note(html, "/milestones/f23-planted") == "waits for bug-02-stale"


def test_done_dependency_and_own_ticket_name_no_card(board_db):
    """A dependency that is done, and one on the card's own earlier ticket, name no card."""

    def change(conn: sqlite3.Connection, p: int) -> None:
        # f24-01-merged is done
        # make f23-01-first depend on f24-01-merged (done) and f23-02-second (own ticket)
        conn.execute(
            "UPDATE tickets SET depends_on = ? WHERE ticket = ?",
            (json.dumps(["f24-01-merged", "f23-02-second"]), "f23-01-first"),
        )

    write(board_db, change)
    found = read(board_db)
    f23 = card(found, "F23")
    assert f23.waits == ()
    html = _page(_client(board_db))
    _, words, _ = _card(html, "/milestones/f23-planted")
    assert "waits for" not in words


def test_bug_and_ripe_card_have_no_waits_line(board_db):
    """A bug card and a ripe card have no such line."""
    found = read(board_db)
    # bug card should have no waits
    bug = card(found, "bug-02-stale")
    assert bug.waits == ()
    # ripe card should have no waits
    ripe = card(found, "F1")
    assert ripe.waits == ()
    html = _page(_client(board_db))
    _, bug_words, _ = _card(html, "/tickets/bug-02-stale")
    assert "waits for" not in bug_words
    _, ripe_words, _ = _card(html, "/milestones/f1")
    assert "waits for" not in ripe_words


def test_waits_populated_only_for_planted_cards(board_db):
    """Only planted cards, started or not, have waits: a sprouting card whose ticket depends
    on another card's has none. (Seed, ripe and harvested cards have no ready ticket to wait;
    `test_bug_and_ripe_card_have_no_waits_line` covers the ripe one.)"""

    def change(conn: sqlite3.Connection, p: int) -> None:
        # create f22 milestone with a ready ticket (to be a dependency target)
        f22 = metrics.upsert_milestone(
            conn, p, "f22-research", title="Research", state="planning", priority=10, area="factory"
        )
        metrics.upsert_ticket(
            conn, p, "f22-01-unfinished", milestone_id=f22, kind="developer", state="ready"
        )
        # create a growing milestone with a ready ticket that depends on f22
        growing = metrics.upsert_milestone(
            conn, p, "f63-growing", title="Growing", state="ready", priority=10, area="factory"
        )
        growing_ticket = metrics.upsert_ticket(
            conn, p, "f63-01-ticket", milestone_id=growing, kind="developer", state="ready"
        )
        # add a job so the milestone is "growing" (not just "planted")
        run = conn.execute(
            "SELECT r.id FROM runs r JOIN projects p ON p.id = r.project_id"
            " WHERE p.name = ? ORDER BY r.id DESC LIMIT 1",
            (PROJECT,),
        ).fetchone()
        metrics.start_job(
            conn,
            run[0],
            ticket_id=growing_ticket,
            milestone_id=growing,
            role="developer",
            agent=LOCAL,
            attempt=1,
            started=NOW.isoformat(),
        )
        # set f23-02-second aside so f23-01-first is the only counting ticket
        conn.execute(
            "UPDATE tickets SET state = ? WHERE ticket = ?",
            ("later", "f23-02-second"),
        )
        # make f23-01-first depend on f22-01-unfinished
        conn.execute(
            "UPDATE tickets SET depends_on = ? WHERE ticket = ?",
            (json.dumps(["f22-01-unfinished"]), "f23-01-first"),
        )
        # make f63-01-ticket depend on f22-01-unfinished
        conn.execute(
            "UPDATE tickets SET depends_on = ? WHERE ticket = ?",
            (json.dumps(["f22-01-unfinished"]), "f63-01-ticket"),
        )
        # make f22-01-unfinished depend on f63-01-ticket so F22 has a nonempty waits on main
        conn.execute(
            "UPDATE tickets SET depends_on = ? WHERE ticket = ?",
            (json.dumps(["f63-01-ticket"]), "f22-01-unfinished"),
        )

    write(board_db, change)
    found = read(board_db)
    # planted card F23: waits is populated
    f23 = card(found, "F23")
    assert f23.stage == "planted"
    assert f23.waits == ("F22",)
    # started card F63: waits is populated
    f63 = card(found, "F63")
    assert (f63.stage, f63.started) == ("planted", True)
    assert f63.waits == ("F22",)
    # sprouting card F22: waits is empty even though its ticket depends on another card
    f22 = card(found, "F22")
    assert f22.stage == "sprouting"
    assert f22.waits == ()


# --- the developer's view (f146-02, after .softfield/cards/f146-mockup/developers-only.html) ------


def _lever(html: str) -> tuple[str, str]:
    """The lever's link and whether it is on."""
    found = re.search(
        r'<a href="([^"]*)" class="lever" role="switch" aria-checked="(true|false)"', html
    )
    assert found
    return unescape(found[1]), found[2]


def _slot(html: str, link: str) -> tuple[list[str], str]:
    """A card's slot by its card's link: the slot's classes, and the card's ``dev-tag`` words."""
    found = re.search(
        rf'<div class="slot([^"]*)"[^>]*>\s*<a class="card[^"]*" href="{re.escape(link)}\?.*?</a>',
        html,
        re.S,
    )
    assert found, link
    tag = re.search(r'<span class="dev-tag">(.*?)</span>\s*</a>', found[0], re.S)
    words = " ".join(unescape(re.sub(r"<[^>]+>", " ", tag[1])).split()) if tag else ""
    return found[1].split(), words


def _three_looks(db: Path) -> None:
    """F70 developers can work on (1 now, 5 after it, then the lead's f70-07), F71 whose two
    developer tickets wait for the lead's f71-01, and F72, lead only."""
    write(
        db,
        _tickets(
            ("f70-a", "f70-01", "developer", "ready", ()),
            *[("f70-a", f"f70-0{n}", "developer", "ready", ("f70-01",)) for n in range(2, 7)],
            ("f70-a", "f70-07", "lead", "ready", ("f70-02",)),
            ("f71-a", "f71-01", "lead", "ready", ()),
            ("f71-a", "f71-02", "developer", "ready", ("f71-01",)),
            ("f71-a", "f71-03", "developer", "ready", ("f71-01",)),
            ("f72-a", "f72-01", "lead", "ready", ()),
        ),
    )


def test_the_lever_comes_after_the_kinds_off_and_links_to_the_view(board_client):
    html = _page(board_client)
    form = re.search(r'<form id="board-filter"(.*?)</form>', html, re.S)
    assert form
    assert form[1].index('class="kinds"') < form[1].index('class="lever"')
    assert _lever(html) == (f"/board?project={PROJECT}&view=developers", "false")
    assert 'name="view"' not in form[1]

    on = _page(board_client, "?view=developers&q=duck&kind=bug")
    assert _lever(on) == (f"/board?project={PROJECT}&q=duck&kind=bug", "true")
    # searching or picking a kind sends the view with them
    form = re.search(r'<form id="board-filter"(.*?)</form>', on, re.S)
    assert form
    assert '<input type="hidden" name="view" value="developers">' in form[1]
    assert _lever(_page(board_client, "?q=duck&kind=bug"))[0] == (
        f"/board?project={PROJECT}&q=duck&kind=bug&view=developers"
    )


def test_each_planted_card_says_what_it_holds_for_developers(db_path):
    _three_looks(db_path)
    html = _page(_client(db_path), "?view=developers")
    assert 'class="field dev-view"' in html
    assert _slot(html, "/milestones/f70-a") == (
        ["dev-can"],
        "developers: 1 now · 5 after it · then the lead's f70-07",
    )
    assert _slot(html, "/milestones/f71-a") == (
        ["dev-waits"],
        "2 developer tickets wait for f71-01",
    )
    assert _slot(html, "/milestones/f72-a") == (["dev-none"], "lead only")


def test_the_planted_head_counts_what_developers_can_work_on_and_how_long(db_path, monkeypatch):
    _three_looks(db_path)
    monkeypatch.setattr("factory_dashboard.board.ticket_minutes", lambda conn, p: [50.5, 40, 60])
    head = _head(_columns(_page(_client(db_path), "?view=developers"))["planted"])
    # one card, its six developer tickets, 6 × the median 50.5 minutes
    assert head.endswith(
        "Developers can work on 1 card, 6 tickets , about 5 h 03 min,"
        " before every developer ticket left waits for the lead"
    )
    assert _hours(45.4) == "45 min"


def test_off_the_lever_gives_the_normal_board_unchanged(db_path):
    _three_looks(db_path)
    client = _client(db_path)
    normal = _page(client)
    for page in (normal, _page(client, "?view=nonsense")):
        assert "dev-" not in page
        assert "Developers can work on" not in page
    assert _columns(_page(client, "?view=nonsense")) == _columns(normal)
    # the view changes looks and words only: the same cards, in the same places
    assert _links(_page(client, "?view=developers")) == _links(normal)


def test_sending_from_the_view_posts_the_same_reorder(page, board_db):
    write(board_db, _planted(("f27-third", 9)))
    page.set_viewport_size(PHONE)
    open_page(page, _client(board_db), "/board?view=developers")
    assert page.locator("#field.dev-view").count() == 1
    line = [key for key, _ in read(board_db).line]
    posts: list[str] = []
    page.on("request", lambda r: posts.append(r.url) if r.method == "POST" else None)
    _drag(page, "f27", "f23")
    page.get_by_role("button", name="Send new order").click()
    page.locator(".slot[data-key=f27] .card.on-its-way").wait_for()
    assert posts == [f"{ORIGIN}/requests"]
    conn = connect(board_db)
    try:
        rows = conn.execute("SELECT kind, value FROM owner_requests").fetchall()
    finally:
        conn.close()
    line.remove("f27")
    line.insert(line.index("f23"), "f27")
    assert [(r["kind"], json.loads(r["value"])) for r in rows] == [("reorder", line)]


# --- a card with an open fast lane request (f192-01) -------------------------------------------


def _reserve(value: str, done: str | None = None) -> Callable[[sqlite3.Connection, int], None]:
    """A ``reserve`` request, open or finished with ``done``."""

    def change(conn: sqlite3.Connection, p: int) -> None:
        asked = metrics.add_request(conn, p, "reserve", "f23", value, NOW.isoformat())
        if done:
            metrics.finish_request(conn, asked, done, "")

    return change


def test_a_planted_card_with_an_open_reserve_on_shows_the_on_its_way_plate(board_db, board_client):
    """F192 D1, D2: a planted card with lane_asked "on" has the on-its-way plate."""
    write(board_db, _reserve("on"))
    found = read(board_db)
    f23 = card(found, "F23")
    assert f23.reserve is False  # F23 is not marked
    assert f23.lane_asked == "on"
    html = _page(board_client)
    _, words, raw = _card(html, "/milestones/f23-planted")
    assert "card-reserve on-its-way" in raw
    assert "fast lane · on its way · at the runner's next pick" in words


def test_a_planted_card_with_an_open_reserve_off_shows_the_leaving_plate(board_db, board_client):
    """F192 D2: a planted card with lane_asked "off" has the leaving plate."""
    write(board_db, _reserve("off"))
    found = read(board_db)
    f23 = card(found, "F23")
    assert f23.lane_asked == "off"
    html = _page(board_client)
    _, words, raw = _card(html, "/milestones/f23-planted")
    assert "card-reserve on-its-way leaving" in raw
    assert "leaving the fast lane · on its way" in words


def test_a_seed_card_keeps_lane_asked_none_even_with_a_request(board_db):
    """F192 D1: a seed card's lane_asked is None even with a reserve request."""
    write(board_db, _reserve("on"))
    found = read(board_db)
    f20 = card(found, "F20")
    assert f20.lane_asked is None


def test_a_card_with_no_open_request_keeps_its_class_unchanged(board_db, board_client, tmp_path):
    """F192 D2: a marked card with no open request keeps exactly class="card-reserve"."""
    mark_reserve(board_db, tmp_path / "repo", "f23-planted")
    found = read(board_db)
    f23 = card(found, "F23")
    assert f23.reserve is True
    assert f23.lane_asked is None
    html = _page(board_client)
    _, words, raw = _card(html, "/milestones/f23-planted")
    assert 'class="card-reserve"' in raw
    assert "on-its-way" not in raw
    assert "fast lane" in words


def test_a_done_reserve_request_shows_no_plate(board_db, board_client):
    """F192: a request the runner has done shows nothing."""
    write(board_db, _reserve("on", NOW.isoformat()))
    found = read(board_db)
    f23 = card(found, "F23")
    assert f23.lane_asked is None
    html = _page(board_client)
    _, _words, raw = _card(html, "/milestones/f23-planted")
    assert "on-its-way" not in raw


def test_pageshow_with_persisted_true_draws_the_field_with_grip_and_menu(page, board_db):
    """D3: a pageshow with persisted true draws the second body's field, with each card's grip
    and ... working."""
    page.set_viewport_size(PHONE)
    open_page(page, _client(board_db), "/board")
    stages = ("seed", "sprouting", "planted")
    before = {stage: _order(page, stage) for stage in stages}
    fetches: list[str] = []
    page.on("request", lambda r: fetches.append(r.url) if "/board" in r.url else None)
    write(board_db, _reserve("on"))  # the second body: the lever pulled on the card's page
    page.evaluate("() => dispatchEvent(new PageTransitionEvent('pageshow', {persisted: true}))")
    plate = page.locator(".slot[data-key=f23] .card-reserve.on-its-way")
    plate.wait_for()  # visible: on a phone the stage shown stays shown
    assert len(fetches) == 1
    # every card still in its own stage, in its place, and nothing marked as moved
    assert {stage: _order(page, stage) for stage in stages} == before
    assert page.locator(".card.moved").count() == 0
    assert page.locator(".slot[data-key=f24] .grip").count() == 1  # one grip, not one per redraw
    page.locator(".slot[data-key=f24] .more").click()
    assert page.locator("#order-sheet").evaluate("(d) => d.open")
    page.locator("#order-sheet [data-move=down]").click()
    assert _order(page, "planted")[:2] == [before["planted"][1], "f24"]


def test_back_without_the_browsers_memory_still_fetches_what_is_true_now(page, board_db):
    """F192 D3: back that doesn't come from the browser's memory (not ``persisted``): the document
    can still be the browser's old copy, so the field is fetched past it, on a phone."""
    client = _client(board_db)
    old_copy = client.get("/board").text
    page.set_viewport_size(PHONE)
    open_page(page, client, "/board")

    def from_the_browsers_cache(route) -> None:
        if route.request.resource_type == "document":
            route.fulfill(body=old_copy, content_type="text/html; charset=utf-8")
        else:
            route.fallback()

    page.route(f"{ORIGIN}/board", from_the_browsers_cache)
    page.goto(f"{ORIGIN}/planning")
    write(board_db, _reserve("on"))
    page.go_back()
    page.locator(".slot[data-key=f23] .card-reserve.on-its-way").wait_for()


def test_pageshow_when_the_fetch_fails_leaves_the_page_as_it_is(page, board_db):
    """F192 D3: an answer that isn't the board, here a 500, changes nothing on the page."""
    page.set_viewport_size(PHONE)
    open_page(page, _client(board_db), "/board")
    before = _order(page, "planted")
    page.route(f"{ORIGIN}/board", lambda route: route.fulfill(status=500, body="no"))
    with page.expect_response(f"{ORIGIN}/board"):
        page.evaluate("() => dispatchEvent(new PageTransitionEvent('pageshow', {persisted: true}))")
    page.wait_for_timeout(100)
    assert _order(page, "planted") == before
    assert page.locator(".slot[data-key=f24]").is_visible()


def test_a_sent_order_whose_refetch_fails_reloads_the_page(page, board_db):
    """f15-04, kept by F192: the order is sent, so the moves can't stay on the page as not sent."""
    _three_planted(page, board_db)
    _drag(page, "f27", "f23")
    page.route(
        f"{ORIGIN}/board",
        lambda route: route.abort() if route.request.resource_type == "fetch" else route.fallback(),
    )
    with page.expect_navigation():
        page.locator('[data-order="send"]').click()
    assert page.locator("#order-bar").is_hidden()


def test_pageshow_with_persisted_false_fetches_nothing(page, board_db):
    """D3: a pageshow with persisted false on a normal load fetches nothing."""
    page.set_viewport_size(PHONE)
    open_page(page, _client(board_db), "/board")
    fetches: list[str] = []
    page.on("request", lambda r: fetches.append(r.url) if "/board" in r.url else None)
    page.evaluate("() => dispatchEvent(new PageTransitionEvent('pageshow', {persisted: false}))")
    page.wait_for_timeout(500)
    board_fetches = [f for f in fetches if "/board" in f]
    assert board_fetches == []


def test_pageshow_with_unsent_moves_keeps_order_and_skips_fetch(page, board_db):
    """D3: with a card moved and not sent, that pageshow makes no board request and the order
    stays."""
    _three_planted(page, board_db)
    _drag(page, "f27", "f23")
    assert _order(page, "planted") == ["f24", "f27", "f23", "bug-02-stale", *STARTED]
    fetches: list[str] = []
    page.on("request", lambda r: fetches.append(r.url) if "/board" in r.url else None)
    page.evaluate("() => dispatchEvent(new PageTransitionEvent('pageshow', {persisted: true}))")
    page.wait_for_timeout(500)
    assert fetches == []
    assert _order(page, "planted") == ["f24", "f27", "f23", "bug-02-stale", *STARTED]


def test_pageshow_with_reorder_draws_the_new_planted_order(page, board_db):
    """F192 D3: an order sent after the page opened (F27 before F23) reaches the redraw: Planted
    is in the new order, the other stages stay the same, and no card has .moved."""
    _three_planted(page, board_db)
    seed_before = _order(page, "seed")
    sprouting_before = _order(page, "sprouting")
    line = [key for key, _ in read(board_db).line]
    line.remove("f27")
    line.insert(line.index("f23"), "f27")
    write(board_db, _reorder(json.dumps(line)))
    page.evaluate("() => dispatchEvent(new PageTransitionEvent('pageshow', {persisted: true}))")
    page.locator(".slot[data-key=f27] .card.on-its-way").wait_for()
    assert _order(page, "planted") == ["f24", "f27", "f23", "bug-02-stale", *STARTED]
    assert _order(page, "seed") == seed_before
    assert _order(page, "sprouting") == sprouting_before
    assert page.locator(".card.moved").count() == 0


def test_pageshow_with_planted_f20_draws_it_in_planted_stage(page, board_db):
    """F192 D3: a seed planted after the page opened is drawn in its new stage: F20 in Planted
    with data-stage "planted" and one grip, and gone from Seed."""
    _three_planted(page, board_db)
    assert _order(page, "seed") == ["f20", "bug-01-duck-count"]
    write(board_db, _planted(("f20-duck-pond", 9)))
    page.evaluate("() => dispatchEvent(new PageTransitionEvent('pageshow', {persisted: true}))")
    page.locator("#stage-planted .slot[data-key=f20]").wait_for(state="attached")
    assert page.locator(".slot[data-key=f20]").get_attribute("data-stage") == "planted"
    assert "f20" in _order(page, "planted")
    assert _order(page, "seed") == ["bug-01-duck-count"]
    assert page.locator(".slot[data-key=f20] .grip").count() == 1


def test_moving_a_card_keeps_the_plate_showing(page, board_db):
    """F192 D2: moving a card on the board leaves the plate showing."""
    write(board_db, _reserve("on"))
    _three_planted(page, board_db)
    page.locator(".slot[data-key=f23] .card .card-reserve").wait_for()
    _drag(page, "f23", "f24")
    slot = page.locator('.slot[data-key="f23"]')
    plate = slot.locator(".card-reserve")
    assert plate.is_visible()
    classes = plate.get_attribute("class") or ""
    assert "on-its-way" in classes
