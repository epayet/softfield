"""The board's cards (f5 D4, ADR 19 item 4): ``board.board`` over ``write_board``'s rows, then
its page, ``/board`` (f5-16)."""

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
from tests.factory_dashboard.test_planning import ORIGIN
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
    totals = re.search(r'<section id="totals"(.*?)</section>', html, re.S)
    assert totals
    assert re.search(r"<b>6</b>\s*<span>Harvested</span>", totals[1])


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
    assert words.startswith("P30 F20 product The duck pond")


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


def test_the_totals_count_each_stage(board_client):
    html = _page(board_client)
    totals = re.search(r'<section id="totals"(.*?)</section>', html, re.S)
    assert totals
    found = dict(
        (unescape(label), int(count))
        for count, label in re.findall(r"<b>(\d+)</b>\s*<span>([^<]*)</span>", totals[1])
    )
    assert found == {
        "Seeds: 1 idea, 1 bug": 2,
        "Sprouting: being planned": 2,
        "Planted: tickets ready": 2,
        "Growing: in the factory": 4,
        "Ripe: needs your sign-off": 2,
        "Harvested": 2,
        "Tickets set aside": 1,
    }


def test_the_page_is_read_only_and_links_to_the_factory_floor(board_client):
    html = _page(board_client)
    main = html.split("<main>", 1)[1]
    assert "<script" not in main
    assert "hx-post" not in main
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
    each card's ↑ and ↓ and the trends, so it still answers and the board links to it."""
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
    assert page.locator("#stage-growing").is_visible()
    # the tabs scroll sideways on a phone by design, as test_planning.py's layout test has it
    page.evaluate("() => document.querySelector('nav.tabs').setAttribute('data-layout', 'overlay')")
    assert layout_problems(page) == []
    tops = page.evaluate(
        "() => Object.fromEntries([...document.querySelectorAll('.stage')].map((el) =>"
        " [el.id.replace('stage-', ''), el.getBoundingClientRect().top]))"
    )
    lefts = page.evaluate(
        "() => [...document.querySelectorAll('.stage')]"
        ".map((el) => el.getBoundingClientRect().left)"
    )
    if size is PHONE:
        # what needs the owner and what runs come first (the owner, 2026-10-03)
        order = sorted(tops, key=lambda stage: tops[stage])
        assert order == ["ripe", "growing", "planted", "sprouting", "seed", "harvested"]
        small = page.evaluate(
            """() => [...document.querySelectorAll(
                    '.board a, .board button, .board input:not([type=hidden])')]
                .filter((el) => el.getBoundingClientRect().height < 44)
                .map((el) => el.textContent.trim() || el.name)"""
        )
        assert small == [], f"tap targets under 44 px: {small}"
    else:
        assert len(set(tops.values())) == 1, "the columns sit side by side"
        assert lefts == sorted(lefts)
        scroller = page.locator("#field .scroll")
        assert scroller.evaluate("el => el.scrollWidth <= el.clientWidth + 1")


@pytest.mark.parametrize("size", [PHONE, DISPLAY], ids=["phone", "display"])
def test_ripe_card_words_fit_inside_the_card(page, board_client, size):
    page.set_viewport_size(size)
    open_page(page, board_client, "/board")
    page.evaluate("() => document.fonts.ready")
    cards = page.query_selector_all("#stage-ripe .card")
    for card in cards:
        assert card.is_visible()
        text = card.inner_text()
        assert "Read the review and sign off" in text


def test_the_columns_scroll_sideways_on_a_narrow_desktop(page, board_client):
    page.set_viewport_size({"width": 1000, "height": 800})
    open_page(page, board_client, "/board")
    scroller = page.locator("#field .scroll")
    assert scroller.evaluate("el => el.scrollWidth > el.clientWidth")
    assert page.evaluate(
        "() => document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )


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
