import html
import json
import re

import pytest
from fastapi.testclient import TestClient

from runner import metrics
from tests.factory_dashboard.conftest import LOCAL, NOW, PROJECT, write_signoff_button
from tests.factory_dashboard.test_planning import _open as open_page
from tests.layout import DISPLAY, PHONE, layout_problems


def section(html_content: str, name: str) -> str:
    """The text of the page's ``<section id="name">``, tags stripped and unescaped."""
    match = re.search(rf'<section[^>]*\bid="{name}"[^>]*>(.*?)</section>', html_content, re.S)
    assert match, f"no section {name}"
    return html.unescape(" ".join(re.sub(r"<[^>]+>", " ", match.group(1)).split()))


def charts(html: str) -> dict[str, object]:
    """Each chart's kind and its JSON data block (f1 D5)."""
    found = re.findall(
        r'<div[^>]*data-chart="([a-z-]+)"[^>]*></div>\s*'
        r'<script type="application/json">(.*?)</script>',
        html,
        re.S,
    )
    return {kind: json.loads(data) for kind, data in found}


def test_milestones_page_answers_200(milestones_client):
    resp = milestones_client.get("/milestones")
    assert resp.status_code == 200


def test_milestones_groups_and_sorts_correctly(milestones_client):
    """In progress first (by latest job), then not started (by priority), then done (by end date).

    In progress: F2 (job 2026-10-02) before F10 (job 2026-10-01).
    Not started: F3 (priority 2) before F5 (priority 10).
    Done: F1 (ended 2026-10-01) before M4 (ended 2026-09-25).
    """
    html = milestones_client.get("/milestones").text
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    key_cells = []
    for row in rows:
        tds = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row, re.S)
        tds = [re.sub(r"<[^>]+>", " ", c).strip() for c in tds]
        if tds:
            key_cells.append(tds[0])
    f2_pos = key_cells.index("F2")
    f10_pos = key_cells.index("F10")
    f3_pos = key_cells.index("F3")
    f5_pos = key_cells.index("F5")
    f1_pos = key_cells.index("F1")
    m4_pos = key_cells.index("M4")
    # In-progress group: F2 (more recent job) before F10.
    assert f2_pos < f10_pos, (
        "In-progress milestones should be ordered by latest job, most recent first"
    )
    # Not-started group: F3 (priority 2) before F5 (priority 10).
    assert f3_pos < f5_pos, "Not-started milestones should be ordered by priority, lower first"
    # Done group: F1 (ended 2026-10-01) before M4 (ended 2026-09-25).
    assert f1_pos < m4_pos, "Done milestones should be ordered by end date, most recent first"
    # Groups are in order: in-progress before not-started before done.
    assert f10_pos < f3_pos, "In-progress milestones should come before not-started"
    assert f5_pos < f1_pos, "Not-started milestones should come before done"


def test_done_milestones_newest_first(milestones_client):
    """Fails if two done milestones come oldest first."""
    html = milestones_client.get("/milestones").text
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    key_cells = []
    for row in rows:
        tds = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row, re.S)
        tds = [re.sub(r"<[^>]+>", " ", c).strip() for c in tds]
        if tds:
            key_cells.append(tds[0])
    f1_pos = key_cells.index("F1")
    m4_pos = key_cells.index("M4")
    assert f1_pos < m4_pos, (
        "Done milestone F1 (ended 2026-10-01) should come before M4 (ended 2026-09-25)"
    )


def test_not_started_ordered_by_priority(milestones_client):
    """Fails if a ready milestone with priority 2 comes after one with priority 5."""
    html = milestones_client.get("/milestones").text
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    key_cells = []
    for row in rows:
        tds = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row, re.S)
        tds = [re.sub(r"<[^>]+>", " ", c).strip() for c in tds]
        if tds:
            key_cells.append(tds[0])
    f3_pos = key_cells.index("F3")
    f5_pos = key_cells.index("F5")
    assert f3_pos < f5_pos, (
        "Not-started milestone F3 (priority 2) should come before F5 (priority 10)"
    )


def test_milestone_with_no_tickets_shows_dashes(milestones_client):
    html = milestones_client.get("/milestones").text
    # Find the F2 row's text
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    f2_row = None
    for row in rows:
        if "F2" in row:
            f2_row = row
            break
    assert f2_row is not None, "F2 row not found"
    assert "–" in f2_row  # dashes for pass rate and other empty fields


def test_milestone_numbers_match_queries(milestones_client):
    html = milestones_client.get("/milestones").text
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    # Find F1 row by exact key cell, not substring.
    f1_row = None
    for row in rows:
        tds = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row, re.S)
        tds = [re.sub(r"<[^>]+>", " ", c).strip() for c in tds]
        if tds and tds[0] == "F1":
            f1_row = row
            break
    assert f1_row is not None
    assert "3" in f1_row  # 3 merged
    assert "50.0%" in f1_row  # pass rate
    assert "1" in f1_row  # 1 escalation


def test_rate_chart_holds_one_point_per_milestone_oldest_first(milestones_client):
    html = milestones_client.get("/milestones").text
    ch = charts(html)
    assert ch["milestone-rate"] == {
        "labels": ["M4", "F1"],
        "rate": [100.0, 50.0],
    }


def test_escalation_chart_holds_one_point_per_milestone_oldest_first(milestones_client):
    html = milestones_client.get("/milestones").text
    ch = charts(html)
    assert ch["milestone-esc"] == {
        "labels": ["M4", "F1"],
        "count": [0, 1],
    }


def test_dollars_chart_holds_one_point_per_milestone_oldest_first(milestones_client):
    html = milestones_client.get("/milestones").text
    ch = charts(html)
    assert ch["milestone-dollars"] == {
        "labels": ["M4", "F1"],
        "dollars": [2.0, 2.6],
    }


def test_savings_chart_holds_one_point_per_milestone_oldest_first(milestones_client):
    html = milestones_client.get("/milestones").text
    ch = charts(html)
    assert ch["milestone-savings"] == {
        "labels": ["M4", "F1"],
        "savings": [pytest.approx(-1.43), pytest.approx(-2.70)],
    }


def test_page_links_to_milestone_detail(milestones_client):
    html = milestones_client.get("/milestones").text
    assert 'href="/milestones/f1?project=' in html
    assert 'href="/milestones/m4?project=' in html


def test_milestone_f1_cells(milestones_client):
    """Each cell of the F1 row, checked individually against fixture data.

    Template columns: Key, Title, Status, Merged, Pass rate, Escalations,
    Review rounds, Claude $, Net $.
    """
    html = milestones_client.get("/milestones").text
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    f1_row = None
    for row in rows:
        tds = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row, re.S)
        tds = [re.sub(r"<[^>]+>", " ", c).strip() for c in tds]
        if tds and tds[0] == "F1":
            f1_row = row
            break
    assert f1_row is not None, "F1 row not found"
    cells = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", f1_row, re.S)
    cells = [re.sub(r"<[^>]+>", " ", c).strip() for c in cells]
    assert cells[0] == "F1"  # key cell
    assert "The factory" in cells[1]  # title
    assert "done" in cells[2]  # status must show done
    assert cells[3] == "3"  # merged = 3 (all tickets have commits)
    assert "50.0%" in cells[4]  # pass rate
    assert cells[5] == "1"  # escalations
    assert cells[6] == "1"  # review rounds
    assert "$7.8" in cells[7]  # claude dollars
    assert "-$2.7" in cells[8]  # net savings


def test_milestone_f2_cells(milestones_client):
    """Each cell of the F2 row, checked individually."""
    html = milestones_client.get("/milestones").text
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    f2_row = None
    for row in rows:
        tds = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row, re.S)
        tds = [re.sub(r"<[^>]+>", " ", c).strip() for c in tds]
        if tds and tds[0] == "F2":
            f2_row = row
            break
    assert f2_row is not None, "F2 row not found"
    cells = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", f2_row, re.S)
    cells = [re.sub(r"<[^>]+>", " ", c).strip() for c in cells]
    assert cells[0] == "F2"  # key cell
    assert "in progress" in cells[2]  # status must show in progress


def _cards(db_path) -> None:
    """F2 building at 5, F10 an idea at the default 100, F1 done at 1; M4 has no card."""
    from runner import metrics
    from tests.factory_dashboard.conftest import PROJECT

    conn = metrics.open_db(db_path)
    try:
        project = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()[0]
        cards = (("f2", "building", 5), ("f10", "idea", 100), ("f1", "done", 1))
        for key, state, priority in cards:
            metrics.upsert_milestone(conn, project, key, state=state, priority=priority)
    finally:
        conn.close()


def _row_cells(html: str, key: str) -> tuple[list[str], str]:
    """A milestone row's cells as text, and its HTML."""
    for row in re.findall(r"<tr>(.*?)</tr>", html, re.S):
        cells = [re.sub(r"<[^>]+>", " ", c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
        cells = [" ".join(c.split()) for c in cells]
        if cells and cells[0] == key:
            return cells, row
    raise AssertionError(f"no row {key}")


def test_each_milestone_not_done_shows_its_priority_and_no_arrows(milestones_client, db_path):
    """F15 D8: the board is the one place to reorder, so the list only shows each card's
    priority; a done milestone, or one with no card, shows –."""
    _cards(db_path)
    html = milestones_client.get("/milestones").text
    assert "<th>Priority</th>" in html or '<th class="num">Priority</th>' in html
    assert "move-button" not in html and '"priority"' not in html
    for key, priority in (("F2", "5"), ("F10", "100"), ("F1", "–"), ("M4", "–")):
        cells, row = _row_cells(html, key)
        assert cells[-1] == priority, key
        assert "<button" not in row and "hx-post" not in row, key
    # the columns before it are as they were
    assert _row_cells(html, "F1")[0][:4] == ["F1", "The factory measures itself", "done", "3"]


def test_an_empty_milestone_with_no_state_and_no_tickets_is_not_in_the_list(db_path):
    """D3: a row with neither state nor tickets is left out of the milestones list."""
    from factory_dashboard.milestones import milestone_rows

    conn = metrics.open_db(db_path)
    try:
        project = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()[0]
        metrics.upsert_milestone(conn, project, "f99-empty")
    finally:
        conn.close()
    rows = milestone_rows(metrics.open_db(db_path), PROJECT)
    keys = {r.key for r in rows}
    assert "f99-empty" not in keys
    assert keys  # the project's other milestones still show


def test_an_empty_milestone_with_no_state_but_with_status_is_not_in_the_list(db_path):
    """The bug: a row with no state, a non-null status, and no tickets still appeared."""
    from factory_dashboard.milestones import milestone_rows

    conn = metrics.open_db(db_path)
    try:
        project = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()[0]
        metrics.upsert_milestone(conn, project, "f98-empty", status="in progress")
    finally:
        conn.close()
    rows = milestone_rows(metrics.open_db(db_path), PROJECT)
    keys = {r.key for r in rows}
    assert "f98-empty" not in keys
    assert keys  # the project's other milestones still show


def test_milestone_detail_answers_200(milestone_detail_client):
    resp = milestone_detail_client.get("/milestones/f1")
    assert resp.status_code == 200


def test_milestone_detail_sections_in_d8_order(milestone_detail_client):
    html = milestone_detail_client.get("/milestones/f1").text
    ids = re.findall(r'<section[^>]*\bid="([a-z-]+)"', html)
    expected = [
        "about",
        "grew",
        "what-changed",
        "how-to-test",
        "decisions",
        "what-next",
        "later",
        "lessons",
        "clogged",
        "results",
        "savings",
        "tickets",
        "runs",
        "findings",
    ]
    # Check that all expected sections appear in order.
    last_pos = -1
    for eid in expected:
        pos = ids.index(eid)
        assert pos > last_pos, f"{eid} not after previous section"
        last_pos = pos


def test_milestone_detail_shows_savings_with_parts_and_net(milestone_detail_client):
    html = milestone_detail_client.get("/milestones/f1").text
    savings = section(html, "savings")
    # Should show doing_itself, supporting, and net
    assert "what Claude would have spent" in savings
    assert "what it spent supporting" in savings
    assert "net" in savings
    # Dollar figures from fixture: doing_itself, supporting, net
    assert "$1.50" in savings
    assert "$4.20" in savings
    assert "-$2.70" in savings


def test_milestone_detail_shows_outcome_and_done_when(milestone_detail_client):
    html = milestone_detail_client.get("/milestones/f1").text
    about = section(html, "about")
    assert "The factory now measures itself end-to-end." in about
    assert "All tickets in" in about


def test_milestone_detail_shows_signoff_parts_by_text(milestone_detail_client):
    html = milestone_detail_client.get("/milestones/f1").text
    for section_name, expected_text in (
        ("what-changed", "A metrics database"),
        ("how-to-test", "Run `softfield milestone f1`"),
        ("what-next", "Close the factory review"),
        ("later", "Full diffs"),
        ("lessons", "Run the loop before the replan"),
        ("decisions", "ADR 16, waiting for the owner"),
        ("clogged", "11 h waiting for Claude"),
    ):
        sec_text = section(html, section_name)
        assert expected_text in sec_text, f"{section_name} missing expected text"


def test_milestone_detail_follows_the_sheets_order(milestone_detail_client):
    html = milestone_detail_client.get("/milestones/f1").text
    ids = ["what-changed", "how-to-test", "decisions", "what-next", "later", "lessons", "clogged"]
    assert [html.index(f'id="{i}"') for i in ids] == sorted(html.index(f'id="{i}"') for i in ids)


def test_milestone_detail_tickets_section_lists_exactly_milestone_tickets(milestone_detail_client):
    html = milestone_detail_client.get("/milestones/f1").text
    tickets_sec = section(html, "tickets")
    # Should list exactly the 3 milestone tickets
    assert "f1-01-first" in tickets_sec
    assert "f1-02-escalated" in tickets_sec
    assert "f1-03-lead" in tickets_sec
    # Count ticket links
    ticket_links = re.findall(r'href="/tickets/([^?]+)', html)
    f1_tickets = [t for t in ticket_links if t.startswith("f1-")]
    assert len(f1_tickets) == 3


def test_milestone_detail_unknown_key_is_404(milestone_detail_client):
    resp = milestone_detail_client.get("/milestones/nonexistent")
    assert resp.status_code == 404


def test_milestone_detail_tickets_link_to_ticket_pages(milestone_detail_client):
    html = milestone_detail_client.get("/milestones/f1").text
    assert 'href="/tickets/f1-01-first?project=' in html
    assert 'href="/tickets/f1-02-escalated?project=' in html
    assert 'href="/tickets/f1-03-lead?project=' in html


def test_milestone_detail_runs_link_to_run_pages(milestone_detail_client):
    html = milestone_detail_client.get("/milestones/f1").text
    assert 'href="/runs/20260930-100000?project=' in html


def test_milestone_detail_without_signoff_shows_not_written_yet(milestone_detail_client):
    """A milestone without a sign-off shows 'Not written yet' for those parts."""
    resp = milestone_detail_client.get("/milestones/f10")
    assert resp.status_code == 200
    html = resp.text
    # f10 has no signoff, so #review-wait replaces the seven signoff sections
    assert 'id="review-wait"' in html
    for section_name in (
        "what-changed",
        "how-to-test",
        "decisions",
        "what-next",
        "later",
        "lessons",
        "clogged",
    ):
        assert f'id="{section_name}"' not in html, f"section {section_name} should not exist"


def test_milestone_scores_detail(milestone_detail_with_scores_client):
    """A milestone with both scores set shows them; one with none shows dashes."""
    resp = milestone_detail_with_scores_client.get("/milestones/f1")
    assert resp.status_code == 200
    html = resp.text
    results = section(html, "results")
    assert "Review score" in results
    assert "7.0/10" in results
    assert "Owner score" in results
    assert "8.5/10" in results
    # Done when items are rendered as <li> inside the section
    done_when = section(html, "about")
    assert "All tickets in" in done_when
    assert "<li>" in html
    # F10 has no scores, so the dash is shown
    resp10 = milestone_detail_with_scores_client.get("/milestones/f10")
    assert resp10.status_code == 200
    html10 = resp10.text
    results10 = section(html10, "results")
    assert "–" in results10


# --- the card's page (f5-17) ---------------------------------------------------------------


@pytest.fixture
def card_client(board_db):
    """A client over ``write_board``'s rows, plus on ``f24-growing``: a lead ticket whose
    ``priority: 0`` its card's place overrides (F173) and a developer one that waits for
    ``f24-03-next``."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(board_db)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        growing = metrics.upsert_milestone(conn, project, "f24-growing")
        metrics.upsert_ticket(
            conn,
            project,
            "f24-06-lead",
            milestone_id=growing,
            kind="lead",
            state="ready",
            title="Goal of f24-06-lead.",
            body="---\npriority: 0\n---\n",
        )
        metrics.upsert_ticket(
            conn,
            project,
            "f24-07-waits",
            milestone_id=growing,
            kind="developer",
            state="ready",
            title="Goal of f24-07-waits.",
            depends_on=["f24-03-next"],
        )
    finally:
        conn.close()
    app = create_app(board_db, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


def _words(markup: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", markup)).split())


def _card_head(page: str) -> str:
    """The words of the card's header."""
    match = re.search(r'<header id="card-head"[^>]*>(.*?)</header>', page, re.S)
    assert match, "no card header"
    return _words(match.group(1))


def _grew(page: str) -> list[tuple[str, bool, bool, str]]:
    """How it grew: each stage's name, whether it's the current one, whether it's dimmed as
    a later one, and its words after the name."""
    match = re.search(r'<section[^>]*\bid="grew"[^>]*>(.*?)</section>', page, re.S)
    assert match, "no How it grew"
    found = []
    for attrs, inner in re.findall(r"<li([^>]*)>(.*?)</li>", match.group(1), re.S):
        name, _, rest = _words(inner).partition(" ")
        classes = re.search(r'class="([^"]*)"', attrs)
        later = "not-yet" in (classes.group(1).split() if classes else [])
        found.append((name, 'aria-current="step"' in attrs, later, rest))
    return found


def _ticket_rows(page: str) -> list[list[str]]:
    """The Tickets section's rows: each one's cells, as words."""
    match = re.search(r'<section[^>]*\bid="tickets"[^>]*>(.*?)</section>', page, re.S)
    assert match, "no Tickets"
    rows = re.findall(r"<tr>(.*?)</tr>", match.group(1), re.S)
    cells = [[_words(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)] for r in rows]
    return [c for c in cells if c]


def test_the_header_shows_the_card_s_stage_priority_and_area(card_client):
    head = _card_head(card_client.get("/milestones/f24-growing").text)
    assert head.startswith("F24 · f24-growing Growing")  # its keys, then its title
    # a ticket started (F154 D1): Planted, growing, and no ``started`` stored to date it
    assert "Stage Planted: in line for the factory · growing Priority" in head
    assert "Priority P1" in head
    assert "Area factory" in head
    assert "Tickets 1 of 5 done · 1 set aside" in head

    planted = _card_head(card_client.get("/milestones/f23-planted").text)
    assert "Stage Planted: in line for the factory Priority" in planted  # none started

    seed = _card_head(card_client.get("/milestones/f20-duck-pond").text)
    assert "Stage Seed: an idea, or a ticket set aside" in seed
    assert "Priority P30" in seed
    assert "Area product" in seed
    assert "Tickets none yet" in seed


def test_the_header_s_stage_is_the_board_s_not_the_doc_s_status(card_client, board_db):
    """``f25-unreviewed`` has every ticket done: planted until the review's sheet is stored,
    then ripe, whatever its ``status`` says."""
    assert "Stage Planted" in _card_head(card_client.get("/milestones/f25-unreviewed").text)
    conn = metrics.open_db(board_db)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_milestone(
            conn, project, "f25-unreviewed", status="in progress", signoff={"changed": "It."}
        )
    finally:
        conn.close()
    head = _card_head(card_client.get("/milestones/f25-unreviewed").text)
    assert "Stage Ripe: needs your sign-off" in head
    assert "in progress" not in head


def test_how_it_grew_marks_the_current_stage_and_dims_the_later_ones(card_client):
    grew = _grew(card_client.get("/milestones/f24-growing").text)
    assert [name for name, *_ in grew] == ["Seed", "Sprouting", "Planted", "Ripe", "Harvested"]
    assert [name for name, current, _, _ in grew if current] == ["Planted"]
    assert [name for name, _, later, _ in grew if later] == ["Ripe", "Harvested"]

    seed = _grew(card_client.get("/milestones/f20-duck-pond").text)
    assert [name for name, current, _, _ in seed if current] == ["Seed"]
    assert [name for name, _, later, _ in seed if later] == [
        "Sprouting",
        "Planted",
        "Ripe",
        "Harvested",
    ]

    harvested = _grew(card_client.get("/milestones/m3").text)
    assert [name for name, current, _, _ in harvested if current] == ["Harvested"]
    assert not any(later for _, _, later, _ in harvested)


def test_how_it_grew_dates_planted_and_harvested_where_the_database_has_them(
    paris, card_client, board_db
):
    words = {name: rest for name, _, _, rest in _grew(card_client.get("/milestones/m3").text)}
    assert words["Harvested"] == "15 Sep 12:00"  # ``milestones.ended``
    assert words["Planted"] == ""  # no ``started`` stored: no date made up
    assert words["Seed"] == words["Sprouting"] == ""

    # f1 started on 2026-09-30 and is ripe: planted has its date, harvested none yet
    words = {name: rest for name, _, _, rest in _grew(card_client.get("/milestones/f1").text)}
    assert words["Planted"] == "30 Sep 09:00"
    assert words["Harvested"] == ""

    conn = metrics.open_db(board_db)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        for key in ("f23-planted", "f24-growing"):
            metrics.upsert_milestone(conn, project, key, started="2026-10-01T08:30:00+02:00")
    finally:
        conn.close()
    page = card_client.get("/milestones/f24-growing").text
    assert [(name, rest) for name, current, _, rest in _grew(page) if current] == [
        ("Planted", "growing since 1 Oct 08:30")
    ]
    # its header says so too (F154 D4)
    assert "Stage Planted: in line for the factory · growing since 1 Oct 08:30" in _card_head(page)
    # a card not started yet shows no growing date, even with one stored
    page = card_client.get("/milestones/f23-planted").text
    planted = _grew(page)
    assert [(name, rest) for name, current, _, rest in planted if current] == [("Planted", "")]
    assert all(rest == "" for *_, rest in planted)
    assert "growing" not in _card_head(page)


def test_the_tickets_come_in_run_order_with_who_works_on_each(card_client):
    """Done, then what's being worked on, then the ready ones as the runner will take them
    (inside the card by id, whatever a ticket's own ``priority:`` says, F173; one that waits
    after those it can take), then the set-aside ones. A removed ticket (``f24-05-gone``) is
    left out."""
    rows = _ticket_rows(card_client.get("/milestones/f24-growing").text)
    assert rows == [
        ["f24-01-merged", "Goal of f24-01-merged.", LOCAL, "done"],
        ["f24-02-working", "Goal of f24-02-working.", LOCAL, "running"],
        ["f24-03-next", "Goal of f24-03-next.", "a developer", "ready"],
        ["f24-06-lead", "Goal of f24-06-lead.", "the lead", "ready"],
        ["f24-07-waits", "Goal of f24-07-waits.", "a developer", "waits for f24-03-next"],
        ["f24-04-later", "Goal of f24-04-later.", "a developer", "set aside"],
    ]


def test_a_ticket_s_who_is_its_last_job_s_agent(milestone_detail_client):
    """``f1-02-escalated`` went from the local model to Opus: its last job's agent shows."""
    from tests.factory_dashboard.conftest import OPUS

    rows = {r[0]: r for r in _ticket_rows(milestone_detail_client.get("/milestones/f1").text)}
    assert rows["f1-01-first"][2:] == [LOCAL, "done"]
    assert rows["f1-02-escalated"][2:] == [OPUS, "done"]


def test_the_page_links_to_the_card_s_planning_thread(card_client):
    page = card_client.get("/milestones/f24-growing").text
    assert re.search(r'<a[^>]*href="/planning/f24\?project=coucou"', page)
    assert card_client.get("/planning/f24").status_code == 200


def test_a_milestone_s_page_lights_the_board_tab_and_leads_back_to_the_board(card_client):
    page = card_client.get("/milestones/f24-growing").text
    tabs = re.findall(r'<nav class="tabs"[^>]*>(.*?)</nav>', page, re.S)[0]
    assert re.findall(r'<a href="([^"?]*)\?[^"]*" aria-current="page"', tabs) == ["/board"]
    crumbs = re.findall(r'<nav class="crumbs"[^>]*>(.*?)</nav>', page, re.S)[0]
    assert re.search(r'<a href="/board\?project=coucou">Board</a>', crumbs)


@pytest.mark.parametrize("size", [PHONE, DISPLAY], ids=["phone", "display"])
def test_the_card_s_page_lays_out_at_phone_and_display_sizes(page, card_client, size):
    page.set_viewport_size(size)
    open_page(page, card_client, "/milestones/f24-growing")
    page.evaluate("() => document.fonts.ready")
    # the tabs scroll sideways on a phone by design, as test_planning.py's layout test has it
    page.evaluate("() => document.querySelector('nav.tabs').setAttribute('data-layout', 'overlay')")
    problems = layout_problems(page)
    assert problems == [], "\n".join(problems)
    if size is PHONE:
        # the header, with the card's stage, is what the phone shows first
        assert page.locator("#card-head .stage-name").bounding_box()["y"] < size["height"]
        link = page.locator("#card-head .card-thread").bounding_box()
        assert link["height"] >= 44


def test_a_removed_card_s_page_still_answers_without_a_stage(card_client):
    """``f26-gone`` left the repo, so the board has no card for it; an old link still opens."""
    response = card_client.get("/milestones/f26-gone")
    assert response.status_code == 200
    assert "Stage" not in _card_head(response.text)
    assert not any(current for _, current, _, _ in _grew(response.text))


def test_a_ripe_milestone_shows_its_signoff_button(signoff_button_client):
    """A ripe milestone's page has the button, and the request it posts (its ``hx-vals``,
    parsed as JSON) is ``signoff`` with the milestone's full key as subject."""
    page = signoff_button_client.get("/milestones/ripe1").text
    match = re.search(r'id="signoff-button"[^>]*hx-vals=\'([^\']*)\'', page)
    assert match, "no Sign off button"
    assert json.loads(html.unescape(match.group(1))) == {
        "kind": "signoff",
        "project": PROJECT,
        "subject": "ripe1",
    }


def test_a_set_aside_ticket_does_not_hide_the_signoff_button(db_path):
    """A milestone whose non-later tickets are all done still shows the button
    even with a later ticket."""
    from fastapi.testclient import TestClient

    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        write_signoff_button(conn)
        rows = conn.execute(
            "SELECT m.id FROM milestones m JOIN projects p ON p.id = m.project_id"
            " WHERE p.name = ? AND m.key = ?",
            (PROJECT, "ripe1"),
        ).fetchall()
        [ripe1] = [r["id"] for r in rows]
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_ticket(conn, project, "ripe1-later", milestone_id=ripe1, state="later")
    finally:
        conn.close()
    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    client = TestClient(app, base_url="http://127.0.0.1:8765")
    page = client.get("/milestones/ripe1").text
    assert 'id="signoff-button"' in page


def test_a_milestone_with_a_ready_ticket_shows_no_button(serve):
    """A milestone with a ready ticket (f1) shows no button."""
    html = serve().get("/milestones/f1").text
    assert 'id="signoff-button"' not in html


def test_a_milestone_with_no_review_shows_no_button(signoff_button_client):
    """Every ticket done but the review's sheet not written (bare1): no button."""
    html = signoff_button_client.get("/milestones/bare1").text
    assert 'id="signoff-button"' not in html


def test_a_signed_off_milestone_shows_no_button(signoff_button_client):
    """A milestone already signed off shows no button."""
    html = signoff_button_client.get("/milestones/signed1").text
    assert 'id="signoff-button"' not in html


def _ask_signoff(db_path, subject: str) -> int:
    """A ``signoff`` request for the milestone, not done yet; its id."""
    conn = metrics.open_db(db_path)
    try:
        project = metrics.find_project(conn, PROJECT)
        assert project is not None
        return metrics.add_request(conn, project, "signoff", subject, None, NOW.isoformat())
    finally:
        conn.close()


def test_a_milestone_with_a_signoff_request_underway_shows_status_line(serve, db_path):
    """With a ``signoff`` request not done yet, the page says
    \"Signing off at the runner's next pick\" and shows no button."""
    _ask_signoff(db_path, "m4")
    html = serve().get("/milestones/m4").text
    assert "Signing off at the runner's next pick" in section(html, "review")
    assert 'id="signoff-button"' not in html


def test_a_refused_sign_off_keeps_its_word_under_the_milestones_button(serve, db_path):
    """A done request on a milestone still ripe was refused: the button is back, with the
    runner's words under it."""
    asked = _ask_signoff(db_path, "m4")
    conn = metrics.open_db(db_path)
    try:
        metrics.finish_request(conn, asked, NOW.isoformat(), "main has uncommitted changes")
    finally:
        conn.close()
    html = serve().get("/milestones/m4").text
    assert 'id="signoff-button"' in html
    assert "The runner said: main has uncommitted changes" in section(html, "review")


# --- the card's page "What it's about" (f158-01) -------------------------------------------------


@pytest.fixture
def card_doc_client(db_path, tmp_path):
    """A project whose repo points to a temp dir with a card doc that has Outcome and Notes."""
    from factory_dashboard.app import create_app, get_now

    cards_dir = tmp_path / ".softfield" / "cards"
    cards_dir.mkdir(parents=True)
    cards_dir.joinpath("f1-test.md").write_text(
        "---\n"
        "id: f1-test\n"
        "milestone: f1\n"
        "agent: developer\n"
        "files: []\n"
        "tests: []\n"
        "priority: 1\n"
        "area: factory\n"
        "---\n"
        "# Milestone F1: Test card\n"
        "\n"
        "> **State:** planted · **Priority:** 1 · **Area:** factory\n"
        "\n"
        "## Outcome\n"
        "- The page shows this outcome\n"
        "- And the folded note\n"
        "\n"
        "## Done when\n"
        "- The outcome shows\n"
        "- The note is folded\n"
        "\n"
        "## Notes\n"
        "This is the owner's note.\n"
        "It has two lines, <b>not bold</b>.\n",
        encoding="utf-8",
    )
    conn = metrics.open_db(db_path)
    try:
        pid = metrics.find_project(conn, PROJECT)
        assert pid is not None
        metrics.upsert_project(conn, PROJECT, repo=str(tmp_path))
        metrics.upsert_milestone(
            conn,
            pid,
            "f1",
            status="done",
            outcome="The factory now measures itself end-to-end.",
            done_when="- All tickets in",
            signoff={"changed": "A metrics database."},
        )
    finally:
        conn.close()
    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


@pytest.fixture
def card_note_only_client(db_path, tmp_path):
    """A project whose repo points to a temp dir with a card doc
    that has only Notes (no Outcome)."""
    from factory_dashboard.app import create_app, get_now

    cards_dir = tmp_path / ".softfield" / "cards"
    cards_dir.mkdir(parents=True)
    note_text = (
        "milestones don't show me their descriptions, "
        "so when i click on a milestone on the board "
        "to see what it's about, i have no idea"
    )
    cards_dir.joinpath("f1-test.md").write_text(
        "---\n"
        "id: f1-test\n"
        "milestone: f1\n"
        "agent: developer\n"
        "files: []\n"
        "tests: []\n"
        "priority: 1\n"
        "area: factory\n"
        "---\n"
        "# Milestone F1: Test card\n"
        "\n"
        "> **State:** planted · **Priority:** 1 · **Area:** factory\n"
        "\n"
        "## Notes\n"
        f"{note_text}\n",
        encoding="utf-8",
    )
    conn = metrics.open_db(db_path)
    try:
        pid = metrics.find_project(conn, PROJECT)
        assert pid is not None
        metrics.upsert_project(conn, PROJECT, repo=str(tmp_path))
        metrics.upsert_milestone(conn, pid, "f1", status="in progress")
    finally:
        conn.close()
    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


@pytest.fixture
def card_nothing_client(db_path, tmp_path):
    """A project whose repo points to a temp dir with a card doc
    that has neither Outcome nor Notes."""
    from factory_dashboard.app import create_app, get_now

    cards_dir = tmp_path / ".softfield" / "cards"
    cards_dir.mkdir(parents=True)
    cards_dir.joinpath("f1-test.md").write_text(
        "---\n"
        "id: f1-test\n"
        "milestone: f1\n"
        "agent: developer\n"
        "files: []\n"
        "tests: []\n"
        "priority: 1\n"
        "area: factory\n"
        "---\n"
        "# Milestone F1: Test card\n"
        "\n"
        "> **State:** planted · **Priority:** 1 · **Area:** factory\n",
        encoding="utf-8",
    )
    conn = metrics.open_db(db_path)
    try:
        pid = metrics.find_project(conn, PROJECT)
        assert pid is not None
        metrics.upsert_project(conn, PROJECT, repo=str(tmp_path))
        metrics.upsert_milestone(conn, pid, "f1", status="in progress")
    finally:
        conn.close()
    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


@pytest.fixture
def no_repo_client(db_path):
    """A project whose repo is a URL (not a local folder):
    should fall back to stored outcome."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        pid = metrics.find_project(conn, PROJECT)
        assert pid is not None
        metrics.upsert_project(conn, PROJECT, repo="https://github.com/example/coucou")
        metrics.upsert_milestone(
            conn,
            pid,
            "f1",
            status="done",
            outcome="The factory now measures itself end-to-end.",
            done_when="- All tickets in `.softfield/tasks/done/`, `check-all` passes on `main`.",
            signoff={"changed": "A metrics database."},
        )
    finally:
        conn.close()
    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


@pytest.fixture
def no_signoff_client(db_path):
    """A milestone without a signoff sheet:
    should show #review-wait."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        pid = metrics.find_project(conn, PROJECT)
        assert pid is not None
        metrics.upsert_milestone(
            conn,
            pid,
            "f10",
            title="F10 milestone",
            status="in progress",
        )
    finally:
        conn.close()
    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


def test_a_card_with_outcome_shows_it_in_about_and_folds_the_note(card_doc_client):
    """A card whose doc has Outcome shows it in #about, before #grew, and its note folded."""
    html = card_doc_client.get("/milestones/f1").text
    about = section(html, "about")
    assert "What it will do" in about
    assert "The page shows this outcome" in about
    assert "And the folded note" in about
    assert "Your note ›" in about
    assert "This is the owner" in about
    assert "It has two lines" in about
    assert "Done when" in about
    assert "The outcome shows" in about
    assert "The note is folded" in about
    # the Outcome is a real list, not its tags as text (section() unescapes, so check the HTML)
    assert "<li>The page shows this outcome</li>" in html
    assert "&lt;li&gt;" not in html
    # the note stays the owner's text, escaped
    assert "&lt;b&gt;not bold&lt;/b&gt;" in html
    # The old #outcome section should not exist
    assert 'id="outcome"' not in html


def test_a_card_with_only_notes_shows_the_note_open(card_note_only_client):
    """A card whose doc has only Notes (no Outcome) shows the note open and the later text."""
    html = card_note_only_client.get("/milestones/f1").text
    about = section(html, "about")
    assert "Your note" in about
    assert "milestones don't show me their descriptions" in about
    assert "The lead writes what it will do when it plans the card." in about


def test_a_card_with_neither_outcome_nor_note_says_nothing_written(card_nothing_client):
    """A card with neither Outcome nor note shows
    'Nothing written about it yet.' and its thread link."""
    html = card_nothing_client.get("/milestones/f1").text
    about = section(html, "about")
    assert "Nothing written about it yet." in about
    assert "Its planning thread" in about
    # The href is inside a tag, so check the raw HTML
    assert 'href="/planning/f1' in html


@pytest.fixture
def card_stored_outcome_client(db_path, tmp_path):
    """A project whose repo points to a temp dir with a card doc
    that has neither Outcome nor Notes, but the milestone has a stored outcome."""
    from factory_dashboard.app import create_app, get_now

    cards_dir = tmp_path / ".softfield" / "cards"
    cards_dir.mkdir(parents=True)
    cards_dir.joinpath("f1-test.md").write_text(
        "---\n"
        "id: f1-test\n"
        "milestone: f1\n"
        "agent: developer\n"
        "files: []\n"
        "tests: []\n"
        "priority: 1\n"
        "area: factory\n"
        "---\n"
        "# Milestone F1: Test card\n"
        "\n"
        "> **State:** planted · **Priority:** 1 · **Area:** factory\n",
        encoding="utf-8",
    )
    conn = metrics.open_db(db_path)
    try:
        pid = metrics.find_project(conn, PROJECT)
        assert pid is not None
        metrics.upsert_project(conn, PROJECT, repo=str(tmp_path))
        metrics.upsert_milestone(
            conn,
            pid,
            "f1",
            status="in progress",
            outcome="The factory now measures itself end-to-end.",
            done_when="- All tickets in `.softfield/tasks/done/`, `check-all` passes on `main`.",
        )
    finally:
        conn.close()
    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


@pytest.fixture
def card_done_when_only_client(db_path, tmp_path):
    """A project whose repo points to a temp dir with a card doc
    that has only Done when (no Outcome, no Notes)."""
    from factory_dashboard.app import create_app, get_now

    cards_dir = tmp_path / ".softfield" / "cards"
    cards_dir.mkdir(parents=True)
    cards_dir.joinpath("f1-test.md").write_text(
        "---\n"
        "id: f1-test\n"
        "milestone: f1\n"
        "agent: developer\n"
        "files: []\n"
        "tests: []\n"
        "priority: 1\n"
        "area: factory\n"
        "---\n"
        "# Milestone F1: Test card\n"
        "\n"
        "> **State:** planted · **Priority:** 1 · **Area:** factory\n"
        "\n"
        "## Done when\n"
        "- The card doc has no Outcome or Notes\n"
        "- But the done when shows\n",
        encoding="utf-8",
    )
    conn = metrics.open_db(db_path)
    try:
        pid = metrics.find_project(conn, PROJECT)
        assert pid is not None
        metrics.upsert_project(conn, PROJECT, repo=str(tmp_path))
        metrics.upsert_milestone(conn, pid, "f1", status="in progress")
    finally:
        conn.close()
    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


def test_a_card_doc_with_neither_outcome_nor_notes_shows_stored_outcome(card_stored_outcome_client):
    """A card doc with neither Outcome nor Notes, and a stored outcome,
    shows the stored outcome in #about."""
    html = card_stored_outcome_client.get("/milestones/f1").text
    about = section(html, "about")
    assert "What it will do" in about
    assert "The factory now measures itself end-to-end." in about
    assert "Done when" in about
    assert "All tickets in" in about
    # the outcome is a real list, not its tags as text (section() unescapes, so check the HTML)
    assert "<p>The factory now measures itself end-to-end.</p>" in html
    assert "&lt;p&gt;" not in html


def test_a_card_doc_with_only_done_when_shows_it(card_done_when_only_client):
    """A card doc with only ## Done when (no Outcome, no Notes)
    shows 'Done when' and its items in #about."""
    html = card_done_when_only_client.get("/milestones/f1").text
    about = section(html, "about")
    assert "Done when" in about
    assert "The card doc has no Outcome or Notes" in about
    assert "But the done when shows" in about
    # the done_when items are real <li>, not escaped
    assert "<li>The card doc has no Outcome or Notes</li>" in html
    assert "&lt;li&gt;" not in html


def test_a_project_with_no_local_repo_shows_stored_outcome(no_repo_client):
    """A project whose repo isn't a local folder shows the stored outcome, and the page renders."""
    resp = no_repo_client.get("/milestones/f1")
    assert resp.status_code == 200
    html = resp.text
    about = section(html, "about")
    assert "The factory now measures itself end-to-end." in about


def test_no_signoff_sheet_shows_review_wait(no_signoff_client):
    """With no sign-off sheet: #review-wait, and none of the individual signoff sections."""
    html = no_signoff_client.get("/milestones/f10").text
    assert 'id="review-wait"' in html
    assert "The review" in section(html, "review-wait")
    for sid in (
        "what-changed",
        "how-to-test",
        "decisions",
        "what-next",
        "later",
        "lessons",
        "clogged",
    ):
        assert f'id="{sid}"' not in html, f"section {sid} should not exist without signoff"


def test_with_signoff_sheet_shows_individual_sections(milestone_detail_client):
    """With a signoff sheet: the individual sections, no #review-wait."""
    html = milestone_detail_client.get("/milestones/f1").text
    for sid in (
        "what-changed",
        "how-to-test",
        "decisions",
        "what-next",
        "later",
        "lessons",
        "clogged",
    ):
        assert f'id="{sid}"' in html, f"section {sid} should exist with signoff"
    assert 'id="review-wait"' not in html


# --- review_ideas (f164-02) -------------------------------------------------------------------


def _make_milestone_with_what_next(db_path, project_name, key, what_next):
    """Create a milestone with a signoff sheet containing a what_next section."""

    conn = metrics.open_db(db_path)
    try:
        pid = metrics.find_project(conn, project_name)
        if pid is None:
            pid = metrics.upsert_project(conn, project_name)
        metrics.upsert_milestone(
            conn,
            pid,
            key,
            title=f"Milestone {key}",
            status="in progress",
            signoff={"what_next": what_next},
        )
    finally:
        conn.close()
    return db_path


def _make_plant_request(db_path, project_name, value, done=None, result=None):
    """Create a plant request in owner_requests."""
    from tests.factory_dashboard.conftest import NOW

    conn = metrics.open_db(db_path)
    try:
        pid = metrics.find_project(conn, project_name)
        assert pid is not None
        metrics.add_request(conn, pid, "plant", "", json.dumps(value), NOW.isoformat())
        if done is not None:
            # Get the last request id
            last = conn.execute(
                "SELECT max(id) FROM owner_requests WHERE project_id = ? AND kind = 'plant'",
                (pid,),
            ).fetchone()
            if last and last[0]:
                conn.execute(
                    "UPDATE owner_requests SET done = ?, result = ? WHERE id = ?",
                    (done, result or "", last[0]),
                )
                conn.commit()
    finally:
        conn.close()


def test_a_sheet_with_what_next_holding_factory_gives_one_factory_idea(db_path):
    """A sheet whose what_next holds \"- **Factory:**\" then an indented \"> Plans: …\" line
    gives one factory idea with id \"f19/1\" and that text, without the \">\"."""
    from factory_dashboard.milestones import review_ideas

    what_next = (
        "- **Product:** on hold, as you asked.\n"
        "- **Factory:**\n"
        "  - A plan check that each Done-when line is named by a ticket's Done when.\n"
        "    This is the third milestone where an outcome fell between tickets.\n"
        "    Worth a planted card:\n"
        "    > Plans: every Done-when line of a card is carried by at least one\n"
        "    ticket's Done when, checked when the plan is approved, so no outcome\n"
        "    falls between tickets.\n"
    )
    _make_milestone_with_what_next(db_path, PROJECT, "f19", what_next)
    ideas = review_ideas(metrics.open_db(db_path), PROJECT, "f19")
    assert len(ideas) == 1
    idea = ideas[0]
    assert idea.id == "f19/1"
    assert "Plans: every Done-when line" in idea.text
    assert idea.area == "factory"
    assert idea.state == "plant"
    assert idea.card is None
    assert idea.said is None


def test_a_quoted_line_under_product_is_a_product_idea(db_path):
    """A quoted line under \"- **Product:**\" is a product idea."""
    from factory_dashboard.milestones import review_ideas

    what_next = (
        "- **Product:**\n  > A new feature for users.\n- **Factory:**\n  > A factory improvement.\n"
    )
    _make_milestone_with_what_next(db_path, PROJECT, "f28", what_next)
    ideas = review_ideas(metrics.open_db(db_path), PROJECT, "f28")
    assert len(ideas) == 2
    assert ideas[0].area == "product"
    assert ideas[1].area == "factory"


def test_a_factory_idea_plants_in_the_factory_s_own_project(db_path):
    """A factory idea from another project's review plants in the project whose folder
    holds the factory's code."""
    from factory_dashboard.milestones import review_ideas

    what_next = "- **Factory:**\n  > A factory idea.\n"
    _make_milestone_with_what_next(db_path, PROJECT, "f28", what_next)
    ideas = review_ideas(metrics.open_db(db_path), PROJECT, "f28")
    assert len(ideas) == 1
    # Since the review's project (coucou) doesn't have the factory code,
    # it should default to the review's own project
    assert ideas[0].project == PROJECT


def test_a_product_idea_plants_in_the_review_s_own_project(db_path):
    """A product idea plants in the review's own project."""
    from factory_dashboard.milestones import review_ideas

    what_next = "- **Product:**\n  > A product idea.\n"
    _make_milestone_with_what_next(db_path, PROJECT, "f28", what_next)
    ideas = review_ideas(metrics.open_db(db_path), PROJECT, "f28")
    assert len(ideas) == 1
    assert ideas[0].project == PROJECT


def test_no_plant_request_gives_plant_state(db_path):
    """No plant request: \"plant\"."""
    from factory_dashboard.milestones import review_ideas

    what_next = "- **Factory:**\n  > A factory idea.\n"
    _make_milestone_with_what_next(db_path, PROJECT, "f28", what_next)
    ideas = review_ideas(metrics.open_db(db_path), PROJECT, "f28")
    assert len(ideas) == 1
    assert ideas[0].state == "plant"


def test_done_with_planted_result_gives_planted_state(db_path):
    """One whose ``from`` is the id and ``done`` is not NULL with \"planted .softfield/cards/…\":
    \"planted\" with card \"f166\"."""
    from factory_dashboard.milestones import review_ideas

    what_next = "- **Factory:**\n  > Plans: every Done-when line of a card.\n"
    _make_milestone_with_what_next(db_path, PROJECT, "f19", what_next)
    _make_plant_request(
        db_path,
        PROJECT,
        {"text": "Plans: every Done-when line of a card.", "from": "f19/1"},
        done="2026-10-01T10:00:00+00:00",
        result="planted .softfield/cards/f166-plans-every-done-when-line-of.md",
    )
    ideas = review_ideas(metrics.open_db(db_path), PROJECT, "f19")
    assert len(ideas) == 1
    assert ideas[0].state == "planted"
    assert ideas[0].card == "f166"
    assert ideas[0].said is None


def test_done_with_other_result_gives_refused_state(db_path):
    """Done with any other result: \"refused\" with that result."""
    from factory_dashboard.milestones import review_ideas

    what_next = "- **Factory:**\n  > A factory idea.\n"
    _make_milestone_with_what_next(db_path, PROJECT, "f28", what_next)
    _make_plant_request(
        db_path,
        PROJECT,
        {"text": "A factory idea.", "from": "f28/1"},
        done="2026-10-01T10:00:00+00:00",
        result="not enough time",
    )
    ideas = review_ideas(metrics.open_db(db_path), PROJECT, "f28")
    assert len(ideas) == 1
    assert ideas[0].state == "refused"
    assert ideas[0].said == "not enough time"


def test_hand_made_plant_counts_as_planted(db_path):
    """A hand-made plant whose text is the idea's without its final full stop counts as planted."""
    from factory_dashboard.milestones import review_ideas

    what_next = "- **Factory:**\n  > Plans: every Done-when line of a card.\n"
    _make_milestone_with_what_next(db_path, PROJECT, "f19", what_next)
    _make_plant_request(
        db_path,
        PROJECT,
        {"text": "Plans: every Done-when line of a card"},  # no final full stop
        done="2026-10-01T10:00:00+00:00",
        result="planted .softfield/cards/f166-plans-every-done-when-line-of.md",
    )
    ideas = review_ideas(metrics.open_db(db_path), PROJECT, "f19")
    assert len(ideas) == 1
    assert ideas[0].state == "planted"
    assert ideas[0].card == "f166"


def test_no_quoted_line_gives_no_ideas(db_path):
    """A sheet with no quoted line gives no ideas."""
    from factory_dashboard.milestones import review_ideas

    what_next = "- **Factory:**\n  - A plain bullet.\n"
    _make_milestone_with_what_next(db_path, PROJECT, "f28", what_next)
    ideas = review_ideas(metrics.open_db(db_path), PROJECT, "f28")
    assert ideas == []


def test_no_sheet_gives_no_ideas(db_path):
    """No sheet gives no ideas."""
    from factory_dashboard.milestones import review_ideas

    conn = metrics.open_db(db_path)
    try:
        pid = metrics.find_project(conn, PROJECT)
        assert pid is not None
        metrics.upsert_milestone(conn, pid, "f99-no-sheet", title="No sheet", status="in progress")
    finally:
        conn.close()
    ideas = review_ideas(metrics.open_db(db_path), PROJECT, "f99-no-sheet")
    assert ideas == []


def test_no_what_next_gives_no_ideas(db_path):
    """A sheet with no what_next gives no ideas."""
    from factory_dashboard.milestones import review_ideas

    what_next = ""
    _make_milestone_with_what_next(db_path, PROJECT, "f28", what_next)
    ideas = review_ideas(metrics.open_db(db_path), PROJECT, "f28")
    assert ideas == []


def test_factory_idea_uses_factory_project_when_it_has_the_code(tmp_path):
    """A factory idea from a review whose project has no factory code uses the
    project whose folder holds the factory's code."""
    from factory_dashboard.milestones import review_ideas
    from runner import metrics

    factory_repo = tmp_path / "factory_repo"
    (factory_repo / "runner").mkdir(parents=True)
    (factory_repo / "factory_dashboard").mkdir(parents=True)
    (factory_repo / "runner" / "loop.py").write_text("# loop", encoding="utf-8")
    (factory_repo / "factory_dashboard" / "app.py").write_text("# app", encoding="utf-8")
    db_path = tmp_path / "factory-metrics.sqlite"
    conn = metrics.open_db(db_path)
    try:
        metrics.upsert_project(conn, "factory", repo=str(factory_repo))
        metrics.upsert_project(conn, "review_proj")
        review_pid = metrics.find_project(conn, "review_proj")
        assert review_pid is not None
        metrics.upsert_milestone(
            conn,
            review_pid,
            "f30",
            title="Milestone f30",
            status="in progress",
            signoff={"what_next": "- **Factory:**\n  > A factory idea.\n"},
        )
    finally:
        conn.close()
    ideas = review_ideas(metrics.open_db(db_path), "review_proj", "f30")
    assert len(ideas) == 1
    assert ideas[0].project == "factory"


def test_factory_idea_state_from_factory_project_requests(db_path, tmp_path):
    """A factory idea whose plant request is stored on the factory's project shows
    its state from the review's page."""
    from factory_dashboard.milestones import review_ideas
    from runner import metrics
    from tests.factory_dashboard.conftest import NOW

    factory_repo = tmp_path / "factory_repo"
    (factory_repo / "runner").mkdir(parents=True)
    (factory_repo / "factory_dashboard").mkdir(parents=True)
    (factory_repo / "runner" / "loop.py").write_text("# loop", encoding="utf-8")
    (factory_repo / "factory_dashboard" / "app.py").write_text("# app", encoding="utf-8")
    conn = metrics.open_db(db_path)
    try:
        metrics.upsert_project(conn, "factory", repo=str(factory_repo))
        review_pid = metrics.find_project(conn, PROJECT)
        assert review_pid is not None
        metrics.upsert_milestone(
            conn,
            review_pid,
            "f31",
            title="Milestone f31",
            status="in progress",
            signoff={"what_next": "- **Factory:**\n  > Plans: every Done-when line of a card.\n"},
        )
        factory_pid = metrics.find_project(conn, "factory")
        assert factory_pid is not None
        metrics.add_request(
            conn,
            factory_pid,
            "plant",
            "",
            json.dumps({"text": "Plans: every Done-when line of a card.", "from": "f31/1"}),
            NOW.isoformat(),
        )
        last = conn.execute(
            "SELECT max(id) FROM owner_requests WHERE project_id = ? AND kind = 'plant'",
            (factory_pid,),
        ).fetchone()
        if last and last[0]:
            conn.execute(
                "UPDATE owner_requests SET done = ?, result = ? WHERE id = ?",
                (
                    "2026-10-01T10:00:00+00:00",
                    "planted .softfield/cards/f166-plans-every-done-when-line-of.md",
                    last[0],
                ),
            )
            conn.commit()
    finally:
        conn.close()
    ideas = review_ideas(metrics.open_db(db_path), PROJECT, "f31")
    assert len(ideas) == 1
    assert ideas[0].state == "planted"
    assert ideas[0].card == "f166"


def test_two_ideas_each_with_own_plant_request(db_path, tmp_path):
    """Two ideas of one review, each with its own plant request in the same project,
    each show their own state."""
    from factory_dashboard.milestones import review_ideas
    from runner import metrics
    from tests.factory_dashboard.conftest import NOW

    factory_repo = tmp_path / "factory_repo"
    (factory_repo / "runner").mkdir(parents=True)
    (factory_repo / "factory_dashboard").mkdir(parents=True)
    (factory_repo / "runner" / "loop.py").write_text("# loop", encoding="utf-8")
    (factory_repo / "factory_dashboard" / "app.py").write_text("# app", encoding="utf-8")
    conn = metrics.open_db(db_path)
    try:
        metrics.upsert_project(conn, "factory", repo=str(factory_repo))
        review_pid = metrics.find_project(conn, PROJECT)
        assert review_pid is not None
        metrics.upsert_milestone(
            conn,
            review_pid,
            "f32",
            title="Milestone f32",
            status="in progress",
            signoff={
                "what_next": ("- **Factory:**\n  > First idea.\n- **Factory:**\n  > Second idea.\n")
            },
        )
        factory_pid = metrics.find_project(conn, "factory")
        assert factory_pid is not None
        metrics.add_request(
            conn,
            factory_pid,
            "plant",
            "",
            json.dumps({"text": "First idea.", "from": "f32/1"}),
            NOW.isoformat(),
        )
        metrics.add_request(
            conn,
            factory_pid,
            "plant",
            "",
            json.dumps({"text": "Second idea.", "from": "f32/2"}),
            NOW.isoformat(),
        )
        req1 = conn.execute(
            "SELECT id FROM owner_requests WHERE project_id = ? AND kind = 'plant'",
            (factory_pid,),
        ).fetchone()
        if req1 and req1[0]:
            conn.execute(
                "UPDATE owner_requests SET done = ?, result = ? WHERE id = ?",
                (
                    "2026-10-01T10:00:00+00:00",
                    "planted .softfield/cards/f166-first.md",
                    req1[0],
                ),
            )
        last = conn.execute(
            "SELECT max(id) FROM owner_requests WHERE project_id = ? AND kind = 'plant'",
            (factory_pid,),
        ).fetchone()
        if last and last[0]:
            conn.execute(
                "UPDATE owner_requests SET done = ?, result = ? WHERE id = ?",
                ("2026-10-01T10:00:00+00:00", "planted .softfield/cards/f167-second.md", last[0]),
            )
            conn.commit()
    finally:
        conn.close()
    ideas = review_ideas(metrics.open_db(db_path), PROJECT, "f32")
    assert len(ideas) == 2
    assert ideas[0].state == "planted"
    assert ideas[0].card == "f166"
    assert ideas[1].state == "planted"
    assert ideas[1].card == "f167"


def test_idea_on_its_way_when_done_is_null(db_path, tmp_path):
    """An idea whose request has ``from`` equal to its id and ``done`` NULL is
    \"on its way\"."""
    from factory_dashboard.milestones import review_ideas
    from runner import metrics
    from tests.factory_dashboard.conftest import NOW

    factory_repo = tmp_path / "factory_repo"
    (factory_repo / "runner").mkdir(parents=True)
    (factory_repo / "factory_dashboard").mkdir(parents=True)
    (factory_repo / "runner" / "loop.py").write_text("# loop", encoding="utf-8")
    (factory_repo / "factory_dashboard" / "app.py").write_text("# app", encoding="utf-8")
    conn = metrics.open_db(db_path)
    try:
        metrics.upsert_project(conn, "factory", repo=str(factory_repo))
        review_pid = metrics.find_project(conn, PROJECT)
        assert review_pid is not None
        metrics.upsert_milestone(
            conn,
            review_pid,
            "f33",
            title="Milestone f33",
            status="in progress",
            signoff={"what_next": "- **Factory:**\n  > A factory idea.\n"},
        )
        factory_pid = metrics.find_project(conn, "factory")
        assert factory_pid is not None
        metrics.add_request(
            conn,
            factory_pid,
            "plant",
            "",
            json.dumps({"text": "A factory idea.", "from": "f33/1"}),
            NOW.isoformat(),
        )
    finally:
        conn.close()
    ideas = review_ideas(metrics.open_db(db_path), PROJECT, "f33")
    assert len(ideas) == 1
    assert ideas[0].state == "on its way"


def test_mixed_product_factory_ideas_match_independently(db_path, tmp_path):
    """Two ideas of one review, each with its own plant request in a different project,
    each show their own state.

    Product requests are stored in the review project; factory requests in the factory project.
    The old code chose one target project for the whole review, so Product requests
    stored in the review project were ignored when a Factory idea existed.
    """
    from factory_dashboard.milestones import review_ideas
    from runner import metrics
    from tests.factory_dashboard.conftest import NOW

    factory_repo = tmp_path / "factory_repo"
    (factory_repo / "runner").mkdir(parents=True)
    (factory_repo / "factory_dashboard").mkdir(parents=True)
    (factory_repo / "runner" / "loop.py").write_text("# loop", encoding="utf-8")
    (factory_repo / "factory_dashboard" / "app.py").write_text("# app", encoding="utf-8")
    conn = metrics.open_db(db_path)
    try:
        metrics.upsert_project(conn, "factory", repo=str(factory_repo))
        review_pid = metrics.find_project(conn, PROJECT)
        assert review_pid is not None
        metrics.upsert_milestone(
            conn,
            review_pid,
            "f34",
            title="Milestone f34",
            status="in progress",
            signoff={
                "what_next": (
                    "- **Product:**\n  > A product idea.\n- **Factory:**\n  > A factory idea.\n"
                )
            },
        )
        # Product idea's plant request is stored in the review project
        metrics.add_request(
            conn,
            review_pid,
            "plant",
            "",
            json.dumps({"text": "A product idea.", "from": "f34/1"}),
            NOW.isoformat(),
        )
        req_prod = conn.execute(
            "SELECT id FROM owner_requests WHERE project_id = ? AND kind = 'plant'",
            (review_pid,),
        ).fetchone()
        if req_prod and req_prod[0]:
            conn.execute(
                "UPDATE owner_requests SET done = ?, result = ? WHERE id = ?",
                (
                    "2026-10-01T10:00:00+00:00",
                    "planted .softfield/cards/f168-product.md",
                    req_prod[0],
                ),
            )
        # Factory idea's plant request is stored in the factory project
        factory_pid = metrics.find_project(conn, "factory")
        assert factory_pid is not None
        metrics.add_request(
            conn,
            factory_pid,
            "plant",
            "",
            json.dumps({"text": "A factory idea.", "from": "f34/2"}),
            NOW.isoformat(),
        )
        req_fact = conn.execute(
            "SELECT id FROM owner_requests WHERE project_id = ? AND kind = 'plant'",
            (factory_pid,),
        ).fetchone()
        if req_fact and req_fact[0]:
            conn.execute(
                "UPDATE owner_requests SET done = ?, result = ? WHERE id = ?",
                (
                    "2026-10-01T10:00:00+00:00",
                    "planted .softfield/cards/f169-factory.md",
                    req_fact[0],
                ),
            )
            conn.commit()
    finally:
        conn.close()
    ideas = review_ideas(metrics.open_db(db_path), PROJECT, "f34")
    assert len(ideas) == 2
    assert ideas[0].state == "planted"
    assert ideas[0].card == "f168"
    assert ideas[1].state == "planted"
    assert ideas[1].card == "f169"


def test_id_less_idea_matches_by_text_not_project_fallback(db_path, tmp_path):
    """An idea without a ``from`` field must match its own request by text similarity,
    not grab the first request for the target project.

    Without the fix, the project-name fallback selects the newest request first,
    which may belong to another idea, causing both ideas to match to the wrong request.
    """
    from factory_dashboard.milestones import review_ideas
    from runner import metrics

    factory_repo = tmp_path / "factory_repo"
    (factory_repo / "runner").mkdir(parents=True)
    (factory_repo / "factory_dashboard").mkdir(parents=True)
    (factory_repo / "runner" / "loop.py").write_text("# loop", encoding="utf-8")
    (factory_repo / "factory_dashboard" / "app.py").write_text("# app", encoding="utf-8")
    conn = metrics.open_db(db_path)
    try:
        metrics.upsert_project(conn, "factory", repo=str(factory_repo))
        review_pid = metrics.find_project(conn, PROJECT)
        assert review_pid is not None
        # Two factory ideas
        metrics.upsert_milestone(
            conn,
            review_pid,
            "f164",
            title="Milestone f164",
            status="in progress",
            signoff={
                "what_next": (
                    "- **Factory:**\n  > First idea for the factory.\n"
                    "- **Factory:**\n  > Second idea for the factory.\n"
                )
            },
        )
        factory_pid = metrics.find_project(conn, "factory")
        assert factory_pid is not None
        # Request 1 (lower ID): text matches idea1, no ``from`` field
        metrics.add_request(
            conn,
            factory_pid,
            "plant",
            "",
            json.dumps({"text": "First idea for the factory."}),
            NOW.isoformat(),
        )
        # Request 2 (higher ID): has ``from`` for idea2, will be returned first
        metrics.add_request(
            conn,
            factory_pid,
            "plant",
            "",
            json.dumps({"text": "Second idea for the factory.", "from": "f164/2"}),
            NOW.isoformat(),
        )
        # Mark request1 as planted (lower ID, so it's older)
        req1 = conn.execute(
            "SELECT id FROM owner_requests WHERE project_id = ? AND kind = 'plant'"
            " ORDER BY id ASC LIMIT 1",
            (factory_pid,),
        ).fetchone()
        if req1 and req1[0]:
            conn.execute(
                "UPDATE owner_requests SET done = ?, result = ? WHERE id = ?",
                ("2026-10-01T10:00:00+00:00", "planted .softfield/cards/f164-first.md", req1[0]),
            )
        # Mark request2 as planted (higher ID, so it's newer)
        last = conn.execute(
            "SELECT max(id) FROM owner_requests WHERE project_id = ? AND kind = 'plant'",
            (factory_pid,),
        ).fetchone()
        if last and last[0]:
            conn.execute(
                "UPDATE owner_requests SET done = ?, result = ? WHERE id = ?",
                ("2026-10-01T10:00:00+00:00", "planted .softfield/cards/f164-second.md", last[0]),
            )
            conn.commit()
    finally:
        conn.close()
    ideas = review_ideas(metrics.open_db(db_path), PROJECT, "f164")
    assert len(ideas) == 2
    assert ideas[0].state == "planted"
    assert ideas[0].card == "f164"
    assert ideas[1].state == "planted"
    assert ideas[1].card == "f164"


# --- the card's fast lane lever (F172 D6, D8) ---------------------------------------------


def _lane_client(board_db) -> TestClient:
    """``board_db``, its checkout marking F23 (planted) and F20 (a seed); F24 and F25 are
    growing and unmarked, F1 is ripe."""
    from factory_dashboard.app import create_app, get_now
    from tests.factory_dashboard.conftest import mark_reserve

    mark_reserve(board_db, board_db.parent / "repo", "f23-planted", "f20-duck-pond")
    app = create_app(board_db, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


def _lever(client: TestClient, key: str) -> dict[str, object] | None:
    """The Fast lane row of ``key``'s header: the lever's aria-checked, classes, disabled,
    what it posts and the row's words; None when the header has no such row."""
    response = client.get(f"/milestones/{key}")
    assert response.status_code == 200
    head = re.search(r'<header id="card-head"[^>]*>(.*?)</header>', response.text, re.S)
    assert head, "no card header"
    row = re.search(r'<dt>Fast lane</dt>\s*<dd id="fast-lane"[^>]*>(.*?)</dd>', head[1], re.S)
    if row is None:
        assert 'role="switch"' not in head[1] and "Fast lane" not in head[1]
        return None
    tag = re.search(r"<button[^>]*>", row[1])
    assert tag, "no lever"
    vals = re.search(r"hx-vals='([^']*)'", tag[0])
    assert vals, tag[0]
    return {
        "checked": re.search(r'aria-checked="([^"]*)"', tag[0])[1],  # type: ignore[index]
        "classes": re.search(r'class="([^"]*)"', tag[0])[1].split(),  # type: ignore[index]
        "disabled": " disabled" in tag[0],
        "posts": json.loads(html.unescape(vals[1])),
        "words": _words(row[1]),
    }


def test_a_planted_card_s_fast_lane_row_is_on_when_marked_and_off_when_not(board_db):
    """F23's doc is marked: on, posting ``off``; F24's isn't: off, posting ``on``. Each posts
    the card's short key; the words say it goes first and uses both reserves."""
    client = _lane_client(board_db)
    marked = _lever(client, "f23-planted")
    assert marked is not None
    assert (marked["checked"], marked["disabled"]) == ("true", False)
    assert "on-its-way" not in marked["classes"]  # type: ignore[operator]
    reserve = {"kind": "reserve", "project": PROJECT}
    assert marked["posts"] == {**reserve, "subject": "f23", "value": "off"}
    assert marked["words"] == (
        "fast lane Goes before everything, planning and reviews too, and uses both of"
        " Claude's reserves. Leaves the lane when its tickets are done."
    )
    unmarked = _lever(client, "f24-growing")
    assert unmarked is not None
    assert unmarked["checked"] == "false"
    assert unmarked["posts"] == {**reserve, "subject": "f24", "value": "on"}
    # after Tickets, the header's last row
    head = _card_head(client.get("/milestones/f24-growing").text)
    assert head.index(" Tickets ") < head.index(" Fast lane fast lane Goes before"), head


@pytest.mark.parametrize("key", ["f20-duck-pond", "f1", "m3", "f25-unreviewed"])
def test_an_idea_ripe_or_done_card_has_no_fast_lane_row(board_db, key):
    """F20 is a seed (its doc marked all the same), F1 ripe, M3 signed off, and F25 growing
    with its one ticket done, waiting for its review: nothing left to run (F172 D6)."""
    assert _lever(_lane_client(board_db), key) is None


def test_a_lever_pulled_shows_on_its_way_until_the_runner_applies_it(board_db):
    """An open ``reserve`` request for F24 (and a done one for F23, and the week's switch,
    which name other subjects): F24's lever is on its way and can't be pulled again; F23's
    isn't. Done, the request leaves F24's lever as its doc says."""
    client = _lane_client(board_db)
    conn = metrics.open_db(board_db)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.add_request(conn, project, "reserve", "f24", "on", NOW.isoformat())
        metrics.add_request(conn, project, "reserve", "week", "on", NOW.isoformat())
        done = metrics.add_request(conn, project, "reserve", "f23", "off", NOW.isoformat())
        conn.execute("UPDATE owner_requests SET done = ? WHERE id = ?", (NOW.isoformat(), done))
        conn.commit()
    finally:
        conn.close()
    pulled = _lever(client, "f24-growing")
    assert pulled is not None
    assert "on-its-way" in pulled["classes"] and pulled["disabled"]  # type: ignore[operator]
    assert pulled["checked"] == "false"  # the doc isn't marked yet
    still = _lever(client, "f23-planted")
    assert still is not None
    assert "on-its-way" not in still["classes"] and not still["disabled"]  # type: ignore[operator]
    conn = metrics.open_db(board_db)
    try:
        conn.execute("UPDATE owner_requests SET done = ? WHERE done IS NULL", (NOW.isoformat(),))
        conn.commit()
    finally:
        conn.close()
    taken = _lever(client, "f24-growing")
    assert taken is not None
    assert "on-its-way" not in taken["classes"] and not taken["disabled"]  # type: ignore[operator]


def test_pulling_the_lever_posts_its_request_and_shows_it_on_its_way(page, board_db):
    """In Chromium: the lever on F24's card page posts ``reserve`` for ``f24``, ``on``; at
    once it has the dashed edge and is disabled; the request is stored, open."""
    client = _lane_client(board_db)
    open_page(page, client, "/milestones/f24-growing")
    lever = page.locator("#fast-lane .lever")
    with page.expect_response(lambda r: r.url.endswith("/requests")):
        lever.click()
    assert "on-its-way" in (lever.get_attribute("class") or "")
    assert lever.is_disabled()
    conn = metrics.open_db(board_db)
    try:
        rows = conn.execute(
            "SELECT subject, value, done FROM owner_requests WHERE kind = 'reserve'"
        ).fetchall()
    finally:
        conn.close()
    assert [tuple(r) for r in rows] == [("f24", "on", None)]
