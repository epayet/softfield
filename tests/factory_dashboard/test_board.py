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
from factory_dashboard.board import STAGES, Board, Card, board, milestone_card
from factory_dashboard.line import live_line
from factory_dashboard.queries import connect
from runner import metrics
from tests.factory_dashboard.conftest import LOCAL, NOW, PROJECT
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
    assert STAGES == ("seed", "sprouting", "planted", "growing", "ripe", "harvested")
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
    _, words = _card(html, "/milestones/f21-parallel")
    assert "waits for your answer since 2 Oct" in words
    _, words = _card(html, "/milestones/f23-planted")
    assert "waits for your answer" not in words
    assert "the lead is answering" not in words
    _, words = _card(html, "/milestones/f24-growing")
    assert "waits for your answer" not in words
    assert "the lead is answering" not in words


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
    """F15 D1: #1, #2… in place of a P number, in the stages the owner orders."""
    write(board_db, _planted(("f27-third", 9)))
    found = read(board_db)
    assert _places(found, "planted") == [
        ("F23", 1, False, 0),
        ("bug-02-stale", 2, False, 0),
        ("F27", 3, False, 0),
    ]
    assert [c.place for c in found.stages["seed"]] == [1, 2]
    assert [c.place for c in found.stages["sprouting"]] == [1, 2]
    assert [c.place for c in found.stages["growing"]] == [1, 2, 3, 4]
    assert [c.place for c in found.stages["ripe"] + found.stages["harvested"]] == [0, 0, 0, 0]


def test_an_open_reorder_shows_at_once_with_where_the_moved_card_was(board_db):
    """F15 D4: F9 sent before F7, which the priorities put first: F9 is on its way, F7 is not
    marked (the card moved is the one out of place, not the one it passed)."""
    write(board_db, _planted(("f7-first", 2), ("f9-second", 3)))
    assert keys(read(board_db), "planted") == ["F7", "F9", "F23", "bug-02-stale"]

    write(board_db, _reorder('["f9", "f7"]'))
    found = read(board_db)
    assert _places(found, "planted") == [
        ("F9", 1, True, 2),
        ("F7", 2, False, 0),
        ("F23", 3, False, 0),
        ("bug-02-stale", 4, False, 0),
    ]
    assert not any(c.on_its_way for cards in found.stages.values() for c in cards if c.key != "F9")


def test_a_card_whose_neighbours_moved_past_it_is_not_marked(board_db):
    write(board_db, _planted(("f7-first", 2), ("f9-second", 3)))
    # F7 sent to the end of the planted cards: only F7 is out of place
    write(board_db, _reorder('["f9", "f23", "bug-02-stale", "f7"]'))
    assert _places(read(board_db), "planted") == [
        ("F9", 1, False, 0),
        ("F23", 2, False, 0),
        ("bug-02-stale", 3, False, 0),
        ("F7", 4, True, 1),
    ]


def test_the_latest_open_reorder_is_the_one_shown(board_db):
    write(board_db, _planted(("f7-first", 2), ("f9-second", 3)))
    write(board_db, _reorder('["f9", "f7"]'))
    write(board_db, _reorder('["f23", "f7", "f9"]'))
    assert _places(read(board_db), "planted") == [
        ("F23", 1, True, 3),
        ("F7", 2, False, 0),
        ("F9", 3, False, 0),
        ("bug-02-stale", 4, False, 0),
    ]


def test_a_done_or_refused_reorder_shows_no_mark(board_db):
    write(board_db, _planted(("f7-first", 2), ("f9-second", 3)))
    before = read(board_db)
    write(board_db, _reorder('["f9", "f7"]', NOW.isoformat(), "reordered: 1 card changed"))
    write(board_db, _reorder('["f23", "f9"]', NOW.isoformat(), "a reorder names each card once"))
    write(board_db, _reorder("not a list"))  # the runner will refuse it: nothing to show
    after = read(board_db)
    assert after.stages == before.stages
    assert _places(after, "planted")[0] == ("F7", 1, False, 0)


def test_a_card_the_reorder_doesnt_name_keeps_its_place_after_the_listed_ones(board_db):
    write(board_db, _reorder('["bug-02-stale", "f25", "nowhere"]'))
    found = read(board_db)
    assert _places(found, "planted") == [("bug-02-stale", 1, True, 2), ("F23", 2, False, 0)]
    # F25 is listed first of the growing cards; the others keep their own order after it
    assert keys(found, "growing") == ["F25", "F24", "bug-03-working", "bug-04-stuck"]
    assert card(found, "F25").was == 4
    assert keys(found, "seed") == ["F20", "bug-01-duck-count"]


def test_places_are_counted_before_q_and_kind_narrow_the_cards(board_db):
    assert _places(read(board_db, q="stale"), "planted") == [("bug-02-stale", 2, False, 0)]
    write(board_db, _reorder('["bug-03-working", "bug-04-stuck", "f24"]'))
    bugs = read(board_db, kind="bug")
    assert _places(bugs, "growing") == [
        ("bug-03-working", 1, False, 0),
        ("bug-04-stuck", 2, False, 0),
    ]
    assert _places(read(board_db, q="f24"), "growing") == [("F24", 3, True, 1)]


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


def _card(html: str, link: str) -> tuple[list[str], str]:
    """A card by its link: its classes and its words."""
    found = re.search(
        rf'<a class="card([^"]*)" href="{re.escape(link)}\?[^"]*">(.*?)</a>', html, re.S
    )
    assert found, link
    return found[1].split(), " ".join(unescape(re.sub(r"<[^>]+>", " ", found[2])).split())


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
    assert _links(columns["growing"])[0] == "/milestones/f24-growing"
    # each column's head counts its cards
    assert re.search(r"in the factory · 4\b", columns["growing"])


def test_a_card_s_link_opens_its_page(board_client):
    for link in _links(_page(board_client)):
        assert board_client.get(link).status_code == 200, link


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
    classes, words = _card(html, "/tickets/bug-01-duck-count")
    assert "bug" in classes  # the striped edge
    assert "factory" in classes
    assert "bug · factory" in words
    assert "ticket written, set aside" in words
    classes, words = _card(html, "/milestones/f20-duck-pond")
    assert "bug" not in classes
    assert "product" in classes
    assert "bug" not in words
    assert words.startswith("#1 F20 product The duck pond")


def test_a_card_shows_its_place_and_no_p_number_on_the_page(board_db):
    write(board_db, _planted(("f27-third", 9)))
    html = _page(_client(board_db))
    _, words = _card(html, "/milestones/f27-third")
    assert words.startswith("#3 F27 factory")
    assert not re.search(r"\bP\d", words)
    for link in ("/milestones/f1", "/milestones/m3"):  # ripe, harvested
        _, words = _card(html, link)
        assert "#" not in words
        assert not re.search(r"\bP\d", words)


def test_a_card_on_its_way_has_a_dashed_edge_and_says_where_it_was(board_db):
    write(board_db, _planted(("f7-first", 2), ("f9-second", 3)))
    write(board_db, _reorder('["f9", "f7"]'))
    html = _page(_client(board_db))
    classes, words = _card(html, "/milestones/f9-second")
    assert "on-its-way" in classes
    assert words.startswith("#1 F9")
    assert "on its way · was #2 · at the runner's next pick" in words
    classes, words = _card(html, "/milestones/f7-first")
    assert "on-its-way" not in classes
    assert "on its way" not in words
    assert words.startswith("#2 F7")


def test_a_growing_card_shows_its_tickets_and_what_runs_now(board_client):
    html = _page(board_client)
    _, words = _card(html, "/milestones/f24-growing")
    assert "1 of 3 tickets · 1 set aside" in words
    assert f"Now: f24-02-working · Goal of f24-02-working. · {LOCAL}, attempt 2" in words
    growing = _columns(html)["growing"]
    assert re.search(r'<span class="meter"><span style="width: 33%">', growing)
    # a ripe card carries the sign-off text
    _, ripe = _card(html, "/milestones/f1")
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
        "planted": (2, "Planted", False),
        "growing": (4, "Growing", False),
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
    assert re.findall(r'kind: "(\w+)"', script) == ["reorder"]
    assert script.count('fetch("/requests"') == 1
    assert re.search(
        r'<a href="/\?project=coucou">\s*Growing cards feed the factory floor ›\s*</a>', main
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
    assert len(plots) == 6
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
        assert rows[0] == rows[2] and rows[3] == rows[5]
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
        assert len(set(rows)) == 1, "the six plots sit in one row"
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
    assert page.locator("#stage-ripe .none").is_visible()


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
        assert order == ["ripe", "growing", "planted", "sprouting", "seed", "harvested"]
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
        _, words = _card(html, link)
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


def test_growing_and_harvested_cards_have_no_review_fragment(board_db, board_client):
    html = _page(board_client)
    found = read(board_db)
    for stage in ("growing", "harvested"):
        for c in found.stages[stage]:
            link = f"{'/tickets' if c.bug else '/milestones'}/{c.full_key}"
            _, words = _card(html, link)
            match = re.search(
                rf'<a class="card[^"]*" href="{re.escape(link)}\?[^"]*#review">', html
            )
            assert match is None, f"{stage} card {link} should not have #review"
            if stage == "harvested":
                assert "Read the review and sign off" not in words


# --- moving cards and sending the order (f15-04) ---------------------------------------------


def _three_planted(page, board_db: Path, size: dict[str, int] = PHONE) -> None:
    """The board in Chromium with three planted cards: F23, bug-02-stale, F27."""
    write(board_db, _planted(("f27-third", 9)))
    page.set_viewport_size(size)
    open_page(page, _client(board_db), "/board")
    assert _order(page, "planted") == ["f23", "bug-02-stale", "f27"]


def _order(page, stage: str) -> list[str]:
    order: list[str] = page.evaluate(
        f"() => [...document.querySelectorAll('#stage-{stage} .slot')].map((s) => s.dataset.key)"
    )
    return order


def _drag(page, key: str, onto: str, *, below: bool = False) -> None:
    """Drag ``key``'s card by its grip and drop it over the top (or bottom) fifth of ``onto``,
    the stage in the middle of the screen first, clear of the bar."""
    page.locator(f'.slot[data-key="{key}"]').evaluate(
        "el => el.closest('.cards').scrollIntoView({block: 'center'})"
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
    _drag(page, "f27", "f23")
    assert _order(page, "planted") == ["f27", "f23", "bug-02-stale"]
    moved = page.locator('.slot[data-key="f27"] .card')
    assert "moved" in (moved.get_attribute("class") or "").split()
    assert moved.evaluate("el => getComputedStyle(el).borderTopStyle") == "dashed"
    assert _words(page, "f27").startswith("#1 F27")
    assert "moved · was #3 · not sent yet" in _words(page, "f27")
    # the cards it passed are not moved, but their places change
    assert page.locator(".card.moved").count() == 1
    assert _words(page, "f23").startswith("#2 F23")
    assert _bar(page) == "1 card moved. Nothing is sent yet."
    assert page.get_by_role("button", name="Send new order").is_visible()
    assert page.get_by_role("button", name="Cancel").is_visible()

    _drag(page, "f27", "bug-02-stale", below=True)  # back to third
    assert _order(page, "planted") == ["f23", "bug-02-stale", "f27"]
    assert page.locator(".card.moved").count() == 0
    assert "moved" not in _words(page, "f27")
    assert _words(page, "f27").startswith("#3 F27")
    assert _bar(page) is None


def test_the_menu_does_the_same_moves_by_keyboard_too(page, board_db):
    _three_planted(page, board_db)
    more = page.locator('.slot[data-key="f27"] .more')
    assert more.get_attribute("aria-label") == "Move F27"
    more.focus()
    page.keyboard.press("Enter")
    sheet = page.locator("#order-sheet")
    assert sheet.is_visible()
    page.keyboard.press("Enter")  # Top, the first button, has the focus
    assert not sheet.is_visible()
    assert _order(page, "planted") == ["f27", "f23", "bug-02-stale"]
    assert page.evaluate("() => document.activeElement.closest('.slot').dataset.key") == "f27"
    for move, order in (
        ("Down", ["f23", "f27", "bug-02-stale"]),
        ("Bottom", ["f23", "bug-02-stale", "f27"]),
        ("Up", ["f23", "f27", "bug-02-stale"]),
    ):
        page.keyboard.press("Enter")  # the focus is back on F27's ⋯
        page.get_by_role("button", name=move, exact=True).focus()
        page.keyboard.press("Enter")
        assert _order(page, "planted") == order, move
    assert "moved · was #3 · not sent yet" in _words(page, "f27")
    page.keyboard.press("Enter")
    page.keyboard.press("Escape")
    assert not sheet.is_visible()


def test_cancel_puts_the_order_back(page, board_db):
    _three_planted(page, board_db)
    _drag(page, "f27", "f23")
    _drag(page, "f23", "bug-02-stale", below=True)  # the two ends swapped
    assert _order(page, "planted") == ["f27", "bug-02-stale", "f23"]
    assert page.locator(".card.moved").count() == 2
    assert _bar(page) == "2 cards moved. Nothing is sent yet."
    page.get_by_role("button", name="Cancel").click()
    assert _order(page, "planted") == ["f23", "bug-02-stale", "f27"]
    assert page.locator(".card.moved").count() == 0
    assert _bar(page) is None


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
    assert "on its way · was #3 · at the runner's next pick" in _words(page, "f27")
    assert _words(page, "f27").startswith("#1 F27")
    assert _bar(page) is None
    # the cards stay draggable: a second order is held until it is sent
    _drag(page, "f23", "f27")
    assert _bar(page) == "1 card moved. Nothing is sent yet."
    assert posts == [f"{ORIGIN}/requests"]


def test_a_card_stays_in_its_stage_and_a_ripe_or_harvested_one_has_no_grip(page, board_db):
    _three_planted(page, board_db, DISPLAY)
    growing = _order(page, "growing")
    _drag(page, "f23", "f25")  # over the growing column: it lands in its own
    assert sorted(_order(page, "planted")) == ["bug-02-stale", "f23", "f27"]
    assert _order(page, "growing") == growing
    for stage in ("ripe", "harvested"):
        assert page.locator(f"#stage-{stage} .card").count()
        assert page.locator(f"#stage-{stage} .grip, #stage-{stage} .more").count() == 0
    for stage in ("seed", "sprouting", "planted", "growing"):
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
    _, words = _card(html, "/milestones/f23-planted")
    assert "waits for F22" in words


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
    _, words = _card(html, "/milestones/f23-planted")
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
    _, words = _card(html, "/milestones/f23-planted")
    assert "waits for F22, F63" in words


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
    _, words = _card(html, "/milestones/f23-planted")
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
    _, bug_words = _card(html, "/tickets/bug-02-stale")
    assert "waits for" not in bug_words
    _, ripe_words = _card(html, "/milestones/f1")
    assert "waits for" not in ripe_words


def test_waits_populated_only_for_planted_and_growing_stages(board_db):
    """waits is empty for seed, sprouting, ripe, and harvested cards even when their
    tickets have dependencies, because only planted and growing cards expose waits."""

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
    # growing card F63: waits is populated
    f63 = card(found, "F63")
    assert f63.stage == "growing"
    assert f63.waits == ("F22",)
    # sprouting card F22: waits is empty even though its ticket depends on another card
    f22 = card(found, "F22")
    assert f22.stage == "sprouting"
    assert f22.waits == ()
    # seed card F20: waits is empty even though its tickets may have deps
    f20 = card(found, "F20")
    assert f20.stage == "seed"
    assert f20.waits == ()
    # sprouting card F21: waits is empty
    f21 = card(found, "F21")
    assert f21.stage == "sprouting"
    assert f21.waits == ()
    # ripe card F1: waits is empty
    f1 = card(found, "F1")
    assert f1.stage == "ripe"
    assert f1.waits == ()
    # harvested card M3: waits is empty
    m3 = card(found, "M3")
    assert m3.stage == "harvested"
    assert m3.waits == ()
