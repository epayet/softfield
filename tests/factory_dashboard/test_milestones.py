import html
import json
import re

import pytest
from fastapi.testclient import TestClient

from runner import metrics
from tests.factory_dashboard.conftest import (
    LOCAL,
    NOW,
    OPUS,
    PROJECT,
    SONNET,
    _job,
    write_signoff_button,
)
from tests.factory_dashboard.test_planning import _open as open_page
from tests.layout import DISPLAY, PHONE, layout_problems


def section(html_content: str, name: str) -> str:
    """The text of the page's ``<section id="name">``, or its fold (``<details>``, F216 D8),
    tags stripped and unescaped."""
    match = re.search(rf'<(section|details)[^>]*\bid="{name}"[^>]*>(.*?)</\1>', html_content, re.S)
    assert match, f"no section {name}"
    return html.unescape(" ".join(re.sub(r"<[^>]+>", " ", match.group(2)).split()))


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


def test_not_started_follow_the_list_not_their_key(milestones_client, db_path):
    """F9 review: the not started went by key, and F3 before F5 held by chance. F9, first on
    the queue's list, goes before F3 and F5."""
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_milestone(
            conn, project, "f9", title="F9 milestone", state="idea", status="ready"
        )
        metrics.set_board_order(conn, project, ["f9", "f3", "f5"])
    finally:
        conn.close()
    page = milestones_client.get("/milestones").text
    keys = [
        re.sub(r"<[^>]+>", " ", cells[0]).strip()
        for row in re.findall(r"<tr>(.*?)</tr>", page, re.S)
        if (cells := re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row, re.S))
    ]
    assert keys.index("F9") < keys.index("F3") < keys.index("F5")


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
    """F2 building, F10 an idea, F1 done; M4 has no card."""
    from runner import metrics
    from tests.factory_dashboard.conftest import PROJECT

    conn = metrics.open_db(db_path)
    try:
        project = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()[0]
        cards = (("f2", "building"), ("f10", "idea"), ("f1", "done"))
        for key, state in cards:
            metrics.upsert_milestone(conn, project, key, state=state)
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


def test_the_list_has_no_priority_column_and_no_arrows(milestones_client, db_path):
    """F15 D8: the board is the one place to reorder; F222 D6: no Priority column either."""
    _cards(db_path)
    html = milestones_client.get("/milestones").text
    assert "Priority" not in html and '"priority"' not in html
    assert "move-button" not in html
    for key in ("F2", "F10", "F1", "M4"):
        cells, row = _row_cells(html, key)
        assert cells[-1].startswith("$") or cells[-1].startswith("-$"), key  # Net $ ends it
        assert "<button" not in row and "hx-post" not in row, key
    # the other columns are as they were
    assert _row_cells(html, "F1")[0][:4] == ["F1", "The factory measures itself", "done", "3"]
    words = " ".join(re.sub(r"<[^>]+>", " ", html).split())
    assert "priority" not in words.lower() and not re.search(r"\bP\d+\b", words)


def test_cards_not_started_follow_the_queue_s_list(milestones_client, db_path):
    """F222 D5: not started, in the list's order, whatever their keys say."""
    _cards(db_path)
    conn = metrics.open_db(db_path)
    try:
        project = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()[0]
        metrics.upsert_milestone(conn, project, "f11", state="idea")
        metrics.upsert_milestone(conn, project, "f12", state="idea")
    finally:
        conn.close()

    def shown() -> list[str]:
        html = milestones_client.get("/milestones").text
        keys = re.findall(r'<td class="id"><a href="/milestones/([a-z0-9-]+)', html)
        return [k for k in keys if k in ("f11", "f12")]

    assert shown() == ["f11", "f12"]  # unlisted: by key
    _list(db_path, ["f12", "f11"])
    assert shown() == ["f12", "f11"]


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
    ids = re.findall(r'<(?:section|details)[^>]*\bid="([a-z-]+)"', html)
    # F216 D8: Needs your answer under the head, the reading part, What next, then the folds
    expected = [
        "decisions",
        "about",
        "what-changed",
        "how-to-test",
        "what-next",
        "behind",
        "later",
        "findings",
        "lessons",
        "clogged",
        "results",
        "grew",
        "tickets",
        "runs",
    ]
    # Check that all expected sections appear in order.
    last_pos = -1
    for eid in expected:
        pos = ids.index(eid)
        assert pos > last_pos, f"{eid} not after previous section"
        last_pos = pos


def test_milestone_detail_shows_savings_with_parts_and_net(milestone_detail_client):
    html = milestone_detail_client.get("/milestones/f1").text
    savings = section(html, "results")  # What it cost holds them (F216 D10)
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
        ("how-to-test", "Run softfield milestone f1"),
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
    ids = ["decisions", "what-changed", "how-to-test", "what-next", "later", "lessons", "clogged"]
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
    match = re.search(r'<(section|details)[^>]*\bid="grew"[^>]*>(.*?)</\1>', page, re.S)
    assert match, "no How it grew"
    found = []
    for attrs, inner in re.findall(r"<li([^>]*)>(.*?)</li>", match.group(2), re.S):
        name, _, rest = _words(inner).partition(" ")
        classes = re.search(r'class="([^"]*)"', attrs)
        later = "not-yet" in (classes.group(1).split() if classes else [])
        found.append((name, 'aria-current="step"' in attrs, later, rest))
    return found


def _ticket_rows(page: str) -> list[list[str]]:
    """The Tickets section's rows: each one's cells, as words."""
    match = re.search(r'<(section|details)[^>]*\bid="tickets"[^>]*>(.*?)</\1>', page, re.S)
    assert match, "no Tickets"
    rows = re.findall(r"<tr>(.*?)</tr>", match.group(2), re.S)
    cells = [[_words(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)] for r in rows]
    return [c for c in cells if c]


def _list(db_path, keys: list[str]) -> None:
    """The queue's list, as the runner copies it to ``board_order`` (F222 D5)."""
    conn = metrics.open_db(db_path)
    try:
        metrics.set_board_order(conn, metrics.upsert_project(conn, PROJECT), keys)
    finally:
        conn.close()


def test_the_header_shows_the_card_s_stage_place_and_area(card_client, board_db):
    """F222 D6: the place the board gives it in its stage, from the list, never a priority."""
    _list(board_db, ["bug-02-stale", "f23", "f24", "f20"])
    head = _card_head(card_client.get("/milestones/f24-growing").text)
    assert head.startswith("F24 · f24-growing Growing")  # its keys, then its title
    # a ticket started (F154 D1): Planted, growing, and no ``started`` stored to date it
    assert "Stage Planted: in line for the factory · growing Place" in head
    assert "Place #3 in Planted" in head
    assert "Area" not in head
    assert "Tickets 1 of 5 done · 1 set aside" in head

    planted = _card_head(card_client.get("/milestones/f23-planted").text)
    assert "Stage Planted: in line for the factory Place #2 in Planted" in planted

    seed = _card_head(card_client.get("/milestones/f20-duck-pond").text)
    assert "Stage Seed: an idea, or a ticket set aside" in seed
    assert "Place #1 in Seed" in seed
    assert "Area" not in seed
    assert "Tickets none yet" in seed

    sprouting = _card_head(card_client.get("/milestones/f22-research").text)
    assert re.search(r"Place #\d in Sprouting", sprouting)


def test_a_ripe_or_harvested_card_has_no_place(card_client):
    for key in ("f1", "m3"):
        head = _card_head(card_client.get(f"/milestones/{key}").text)
        assert "Place" not in head, key


def test_a_card_s_place_follows_a_drag_and_no_number_shows(card_client, board_db):
    """F222 D6: worked out from the list as the page opens; no priority anywhere."""
    _list(board_db, ["f23", "f24"])
    assert "Place #2 in Planted" in _card_head(card_client.get("/milestones/f24-growing").text)
    _list(board_db, ["f24", "f23"])
    page = card_client.get("/milestones/f24-growing").text
    assert "Place #1 in Planted" in _card_head(page)
    words = _words(page)
    assert "priority" not in words.lower()
    assert not re.search(r"\bP\d+\b", words)


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
    """A card whose doc has Outcome shows it in #about, before #grew, and its note folded:
    with its review's sheet stored, in Behind it's "Your note and how it grew" (F216 D8)."""
    html = card_doc_client.get("/milestones/f1").text
    about = section(html, "about")
    assert "What it will do" in about
    assert "The page shows this outcome" in about
    assert "And the folded note" in about
    assert "This is the owner" not in about
    grew = section(html, "grew")
    assert grew.startswith("Your note and how it grew")
    assert "This is the owner" in grew
    assert "It has two lines" in grew
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
                ("2026-10-01T10:00:00+00:00", "planted .softfield/cards/f170-second.md", last[0]),
            )
            conn.commit()
    finally:
        conn.close()
    ideas = review_ideas(metrics.open_db(db_path), PROJECT, "f164")
    assert len(ideas) == 2
    assert ideas[0].state == "planted"
    assert ideas[0].card == "f164"
    assert ideas[1].state == "planted"
    assert ideas[1].card == "f170"


def test_idea_with_empty_text_matches_no_request(db_path, tmp_path):
    """An idea whose text is empty once normalised (just a full stop) matches no request."""
    from factory_dashboard.milestones import _same_text, review_ideas
    from runner import metrics

    assert not _same_text(" . ", "Anything at all")
    assert _same_text("First idea.", "First   idea for the factory.")

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
            "f164",
            title="Milestone f164",
            status="in progress",
            signoff={"what_next": "- **Factory:**\n  > .\n"},
        )
        factory_pid = metrics.find_project(conn, "factory")
        assert factory_pid is not None
        metrics.add_request(
            conn, factory_pid, "plant", "", json.dumps({"text": "Anything."}), NOW.isoformat()
        )
        conn.commit()
    finally:
        conn.close()
    ideas = review_ideas(metrics.open_db(db_path), PROJECT, "f164")
    assert len(ideas) == 1
    assert ideas[0].state == "plant"


def test_a_press_of_another_idea_never_counts_for_one_its_text_starts_with(db_path):
    """Idea 2's press, "Add X to Y. From F28's review.", starts with idea 1's text "Add X":
    it is idea 2's alone, and idea 1 keeps its buttons."""
    from factory_dashboard.milestones import review_ideas

    _make_milestone_with_what_next(
        db_path, PROJECT, "f28", "- **Factory:**\n  > Add X.\n  > Add X to Y.\n"
    )
    _make_plant_request(
        db_path, PROJECT, {"text": "Add X to Y. From F28's review.", "from": "f28/2"}
    )
    ideas = review_ideas(metrics.open_db(db_path), PROJECT, "f28")
    assert [(i.id, i.state) for i in ideas] == [("f28/1", "plant"), ("f28/2", "on its way")]


def test_a_quoted_line_takes_its_area_from_its_own_section_only(db_path):
    """What next ends under Product; a quoted line in What clogged with no bullet above it in
    its own section is a factory idea, not product (D2: "in its section")."""
    from factory_dashboard.milestones import review_ideas

    conn = metrics.open_db(db_path)
    try:
        pid = metrics.find_project(conn, PROJECT)
        assert pid is not None
        metrics.upsert_milestone(
            conn,
            pid,
            "f28",
            title="Milestone f28",
            status="in progress",
            signoff={
                "what_next": "- **Product:**\n  > A product idea.\n",
                "clogged": "> Log why the runner skipped each ready ticket.\n",
            },
        )
    finally:
        conn.close()
    ideas = review_ideas(metrics.open_db(db_path), PROJECT, "f28")
    assert [(i.id, i.area) for i in ideas] == [("f28/1", "product"), ("f28/2", "factory")]


def test_a_sheet_with_ideas_outside_what_next_still_gives_them(db_path):
    """D2: any section's quoted lines are ideas, even with no What next at all."""
    from factory_dashboard.milestones import review_ideas

    conn = metrics.open_db(db_path)
    try:
        pid = metrics.find_project(conn, PROJECT)
        assert pid is not None
        metrics.upsert_milestone(
            conn,
            pid,
            "f28",
            title="Milestone f28",
            status="in progress",
            signoff={"clogged": "- Twelve idle hours.\n  > Say why a ready ticket waits.\n"},
        )
    finally:
        conn.close()
    ideas = review_ideas(metrics.open_db(db_path), PROJECT, "f28")
    assert [i.text for i in ideas] == ["Say why a ready ticket waits."]


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


def test_get_milestones_calls_trends_once(milestones_client, monkeypatch):
    """One GET /milestones calls queries.trends exactly once."""
    call_count = 0

    from factory_dashboard.queries import trends as real_trends

    def counting_trends(conn, project):
        nonlocal call_count
        call_count += 1
        return real_trends(conn, project)

    monkeypatch.setattr(
        "factory_dashboard.milestones.queries.trends",
        counting_trends,
    )
    milestones_client.get("/milestones")
    assert call_count == 1


def test_milestones_savings_includes_lead_ticket_without_jobs_in_jobs_in_rate(tmp_path):
    """A lead ticket with no jobs still contributes its lines to the rate denominator,
    lowering the per-line rate and thus the savings calculation."""

    from factory_dashboard.queries import savings
    from runner import metrics

    db = tmp_path / "factory-metrics.sqlite"
    conn = metrics.open_db(db)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1", started="2026-10-01T09:00:00+02:00")
        run = metrics.upsert_run(conn, project, "20261001-100000")

        # Lead ticket 1: d3, 100 lines, with a $1.70 job
        t1 = metrics.upsert_ticket(
            conn,
            project,
            "f1-01-lead",
            milestone_id=f1,
            kind="lead",
            state="done",
            difficulty=3,
            merged_by="claude-opus",
            commit="a" * 40,
            lines_changed=100,
        )
        j1 = metrics.start_job(
            conn,
            run,
            ticket_id=t1,
            milestone_id=f1,
            role="lead-ticket",
            agent="claude-opus",
            attempt=1,
            started="2026-10-01T10:00:00+02:00",
        )
        metrics.finish_job(
            conn,
            j1,
            ended="2026-10-01T10:10:00+02:00",
            outcome="passed",
            cost_usd=1.70,
            tokens_in=10_000,
            tokens_cached=100_000,
            tokens_out=2_000,
        )

        # Lead ticket 2: d3, 50 lines, NO jobs at all
        metrics.upsert_ticket(
            conn,
            project,
            "f1-02-lead",
            milestone_id=f1,
            kind="lead",
            state="done",
            difficulty=3,
            merged_by="claude-opus",
            commit="b" * 40,
            lines_changed=50,
        )

        # Developer ticket: d3, 100 lines, merged by local
        dev = metrics.upsert_ticket(
            conn,
            project,
            "f1-03-dev",
            milestone_id=f1,
            kind="developer",
            state="done",
            difficulty=3,
            merged_by="local-qwen3.6-35b-a3b",
            commit="c" * 40,
            lines_changed=100,
        )
        jdev = metrics.start_job(
            conn,
            run,
            ticket_id=dev,
            milestone_id=f1,
            role="developer",
            agent="local-qwen3.6-35b-a3b",
            attempt=1,
            started="2026-10-01T10:00:00+02:00",
        )
        metrics.finish_job(
            conn,
            jdev,
            ended="2026-10-01T10:05:00+02:00",
            outcome="passed",
            tokens_in=200_000,
            tokens_out=10_000,
        )
    finally:
        conn.close()

    # With the fix: rate = $1.70 / (100 + 50) lines
    # Without the fix: rate = $1.70 / 100 lines (ticket 2 dropped)
    s = savings(metrics.open_db(db), PROJECT, "f1")
    # doing_itself: developer's 100 lines * rate
    # The rate should be 1.70/150 per line (both lead tickets counted)
    expected_rate = 1.70 / 150
    expected_doing_itself = 100 * expected_rate
    assert s.doing_itself == pytest.approx(expected_doing_itself)


# --- a review's ideas are plates in place on the milestone page (f164-03) ---------------------


def test_the_milestone_page_draws_each_quoted_line_as_a_plate_where_it_stood(db_path, serve):
    what_next = "- **Factory:** first\n> Idea one text.\n- between the two\n> Idea two text.\n"
    _make_milestone_with_what_next(db_path, PROJECT, "f28", what_next)
    page = serve().get("/milestones/f28").text
    assert "&gt;" not in page
    assert page.count('class="idea factory"') == 2
    assert (
        page.index("Idea one text.") < page.index("between the two") < page.index("Idea two text.")
    )
    assert f"for {PROJECT}" in page
    assert page.count("Plant and ask the lead") == 2


def test_a_planted_idea_on_the_milestone_page_links_to_its_card(db_path, serve):
    _make_milestone_with_what_next(db_path, PROJECT, "f28", "- **Factory:**\n> Idea one text.\n")
    _make_plant_request(
        db_path,
        PROJECT,
        {"text": "Idea one text. From F28's review.", "from": "f28/1"},
        done="x",
        result="planted .softfield/cards/f166-plans.md",
    )
    page = serve().get("/milestones/f28").text
    assert 'href="/planning/f166?project=' in page
    assert "Plant and ask the lead" not in page


# --- f216-02: caught, spend, and _to_html -----------------------------------------------


def test_caught_lists_findings_with_outcomes_ordered_by_severity(db_path):
    """The card's ``caught`` lists findings with "fixed", "left", "ticket" or "for you"
    as D11 says, blocking first, should-fix second, nit third, then by key."""
    from factory_dashboard.milestones import _caught

    conn = metrics.open_db(db_path)
    try:
        pid = metrics.find_project(conn, PROJECT)
        assert pid is not None
        m_id = metrics.upsert_milestone(conn, pid, "f216-test")
        # Add findings with different severities and routes
        metrics.add_finding(
            conn,
            m_id,
            "F1",
            severity="blocking",
            route="local",
            summary="A blocking bug",
        )
        metrics.add_finding(
            conn,
            m_id,
            "F2",
            severity="blocking",
            route="report",
            summary="A blocking issue",
        )
        metrics.add_finding(
            conn,
            m_id,
            "F3",
            severity="should-fix",
            route="later",
            summary="Should fix this",
        )
        metrics.add_finding(
            conn,
            m_id,
            "F4",
            severity="nit",
            route="adr",
            summary="A nit",
        )
        metrics.add_finding(
            conn,
            m_id,
            "F5",
            severity="should-fix",
            route="backlog",
            summary="Old backlog",
        )
        # A resolved finding
        metrics.add_finding(
            conn,
            m_id,
            "F6",
            severity="blocking",
            route="local",
            summary="Was fixed",
            resolved=True,
        )
        conn.commit()
    finally:
        conn.close()
    caught = _caught(metrics.open_db(db_path), m_id)
    # Blocking first, then should-fix, then nit; within same severity by key
    assert len(caught) == 6
    assert caught[0].severity == "blocking"
    assert caught[0].outcome == "ticket"  # F1, route "local"
    assert caught[1].severity == "blocking"
    assert caught[1].outcome == "left"  # F2, route "report"
    assert caught[2].severity == "blocking"
    assert caught[2].outcome == "fixed"  # F6, resolved
    assert caught[3].severity == "should-fix"
    assert caught[3].outcome == "ticket"  # F3, route "later"
    assert caught[4].severity == "should-fix"
    assert caught[4].outcome == "ticket"  # F5, route "backlog"
    assert caught[5].severity == "nit"
    assert caught[5].outcome == "for you"  # F4, route "adr"


def test_caught_handles_backlog_route_as_ticket(db_path):
    """The old route ``backlog`` reads "ticket" (D11)."""
    from factory_dashboard.milestones import _caught

    conn = metrics.open_db(db_path)
    try:
        pid = metrics.find_project(conn, PROJECT)
        assert pid is not None
        m_id = metrics.upsert_milestone(conn, pid, "f216-bl")
        metrics.add_finding(
            conn,
            m_id,
            "F1",
            severity="should-fix",
            route="backlog",
            summary="Old finding",
        )
        conn.commit()
    finally:
        conn.close()
    caught = _caught(metrics.open_db(db_path), m_id)
    assert len(caught) == 1
    assert caught[0].outcome == "ticket"


def test_spend_gives_dollars_by_role_largest_first_with_share(db_path):
    """The card's ``spend`` gives dollars by role with plain labels, largest first,
    and share to scale."""
    from factory_dashboard.milestones import _milestone_spend

    conn = metrics.open_db(db_path)
    try:
        pid = metrics.find_project(conn, PROJECT)
        assert pid is not None
        m_id = metrics.upsert_milestone(conn, pid, "f216-spend")
        run = metrics.upsert_run(conn, pid, "20261001-100000")
        # Different roles with different costs
        _job(conn, run, m_id, None, "review", OPUS, 1, "passed", cost_usd=3.0)
        _job(conn, run, m_id, None, "escalation", OPUS, 1, "passed", cost_usd=1.5)
        _job(conn, run, m_id, None, "checkpoint", SONNET, 1, "passed", cost_usd=0.5)
        _job(conn, run, m_id, None, "planner", OPUS, 1, "passed", cost_usd=2.0)
        conn.commit()
    finally:
        conn.close()
    spend = _milestone_spend(metrics.open_db(db_path), m_id)
    assert len(spend) == 4
    # Largest first
    assert spend[0].label == "The review"
    assert spend[0].usd == 3.0
    assert spend[0].share == 1.0
    assert spend[1].label == "Planning"
    assert spend[1].usd == 2.0
    assert spend[1].share == pytest.approx(0.67)
    assert spend[2].label == "The lead finishing a developer's ticket"
    assert spend[2].usd == 1.5
    assert spend[2].share == pytest.approx(0.5)
    assert spend[3].label == "Checkpoints"
    assert spend[3].usd == 0.5
    assert spend[3].share == pytest.approx(0.17)


def test_spend_labels_role_names_per_d10(db_path):
    """D10's plain labels: review, escalation, planner, lead-ticket, direction, checkpoint."""
    from factory_dashboard.milestones import _milestone_spend

    conn = metrics.open_db(db_path)
    try:
        pid = metrics.find_project(conn, PROJECT)
        assert pid is not None
        m_id = metrics.upsert_milestone(conn, pid, "f216-labels")
        run = metrics.upsert_run(conn, pid, "20261001-110000")
        _job(conn, run, m_id, None, "lead-ticket", OPUS, 1, "passed", cost_usd=1.0)
        _job(conn, run, m_id, None, "direction", OPUS, 1, "passed", cost_usd=1.0)
        conn.commit()
    finally:
        conn.close()
    spend = _milestone_spend(metrics.open_db(db_path), m_id)
    labels = [s.label for s in spend]
    assert "The lead's tickets" in labels
    assert "Directions for developers" in labels


def test_spend_developer_with_jobs_no_dollars(db_path):
    """A developer role with jobs and no dollars is "Developers, on your GPU" at $0."""
    from factory_dashboard.milestones import _milestone_spend

    conn = metrics.open_db(db_path)
    try:
        pid = metrics.find_project(conn, PROJECT)
        assert pid is not None
        m_id = metrics.upsert_milestone(conn, pid, "f216-dev")
        run = metrics.upsert_run(conn, pid, "20261001-120000")
        ticket = metrics.upsert_ticket(
            conn,
            pid,
            "f216-01",
            milestone_id=m_id,
            kind="developer",
            state="done",
        )
        _job(conn, run, m_id, ticket, "developer", LOCAL, 1, "passed", tokens_in=10_000)
        _job(conn, run, m_id, None, "review", OPUS, 1, "passed", cost_usd=2.0)
        conn.commit()
    finally:
        conn.close()
    spend = _milestone_spend(metrics.open_db(db_path), m_id)
    labels = [s.label for s in spend]
    assert "Developers, on your GPU" in labels
    dev_row = next(s for s in spend if s.label == "Developers, on your GPU")
    assert dev_row.usd == 0.0
    assert dev_row.share == 0.0


def test_to_html_numbered_becomes_ol():
    """``1. x`` lines become ``<ol><li>x</li>``."""
    from factory_dashboard.milestones import _to_html

    result = _to_html("1. First step\n2. Second step\n3. Third step")
    assert "<ol>" in result
    assert "<li>First step</li>" in result
    assert "<li>Second step</li>" in result
    assert "<li>Third step</li>" in result
    assert "</ol>" in result


def test_to_html_nested_bullet_becomes_nested_ul():
    """An indented ``- x`` under a bullet becomes a nested ``<ul>`` inside the parent's ``<li>``."""
    from factory_dashboard.milestones import _to_html

    result = _to_html("- Top level\n  - Nested item\n- Another top")
    assert "<ul>" in result
    # Should have two <ul> tags (outer and nested)
    assert result.count("<ul>") == 2
    # Nested <ul> sits inside the parent's <li>, not between </li> and <ul>
    assert "<li>Top level<ul>" in result
    assert "<li>Nested item</li>" in result
    assert "<li>Another top</li>" in result


def test_to_html_bold_works_everywhere():
    """`` **x** `` becomes ``<strong>x</strong>`` in paragraphs and list items."""
    from factory_dashboard.milestones import _to_html

    # In a paragraph
    result = _to_html("This is **bold** text.")
    assert "<strong>bold</strong>" in result

    # In a list item
    result2 = _to_html("- Item with **bold**")
    assert "<strong>bold</strong>" in result2


def test_to_html_inline_code():
    """`` `x` `` becomes ``<code>x</code>``."""
    from factory_dashboard.milestones import _to_html

    result = _to_html("Use `run_order` for the list.")
    assert "<code>run_order</code>" in result


def test_to_html_http_link_becomes_anchor():
    """``[text](https://x)`` becomes a link."""
    from factory_dashboard.milestones import _to_html

    result = _to_html("See [ADR 1](https://example.com/adr1).")
    assert '<a href="https://example.com/adr1">ADR 1</a>' in result


def test_to_html_non_http_link_becomes_text():
    """``[text](../sessions/x.md)`` and ``[text](javascript:x)`` become text alone."""
    from factory_dashboard.milestones import _to_html

    result1 = _to_html("See [session](../sessions/1.md).")
    assert "session" in result1
    assert "href=" not in result1

    result2 = _to_html("Run [this](javascript:alert(1)).")
    assert "this" in result2
    assert "href=" not in result2


def test_to_html_script_stays_escaped():
    """``<script>`` in the sheet's text still comes out escaped, inside ``code`` too."""
    from factory_dashboard.milestones import _to_html

    result = _to_html("Run <script>alert(1)</script>.")
    assert "&lt;script&gt;" in result
    assert "<script>" not in result

    result2 = _to_html("Use ``<script>`` in code.")
    assert "&lt;script&gt;" in result2


def test_to_html_ideas_still_work():
    """With ``ideas``, quoted lines become idea plates in place."""
    from factory_dashboard.milestones import Idea, _to_html

    ideas = iter(
        [
            Idea(
                id="f1/1",
                text="Idea one",
                area="factory",
                project="coucou",
                state="plant",
                card=None,
                said=None,
            )
        ]
    )
    result = _to_html("- Before\n> Idea text\n- After", ideas=ideas)
    assert "Idea one" in result
    assert "&gt;" not in result


def test_to_html_mixed_numbered_and_bullets():
    """A bullet between numbered items closes the <ol>, creates a <ul>, then reopens <ol>.
    Output has balanced, well-formed tags checked on the full string."""
    from factory_dashboard.milestones import _to_html

    result = _to_html("1. First\n- Bullet\n2. Second")
    # Bullet closes <ol>, creates <ul>, then <ol> reopens
    first_ol_close = result.rindex("</ol>", 0, result.index("<ul>"))
    ul_open = result.index("<ul>")
    second_ol_open = result.index("<ol>", ul_open)
    assert first_ol_close < ul_open < second_ol_open, (
        f"<ul> must be between two </ol> and <ol>; got: {result}"
    )
    assert result.count("<ol>") == 2
    assert result.count("</ol>") == 2
    assert result.count("<ul>") == 1
    assert result.count("</ul>") == 1
    assert "<li>First</li>" in result
    assert "<li>Bullet</li>" in result
    assert "<li>Second</li>" in result


def test_to_html_inline_code_and_bold_together():
    """`` `code` `` and `` **bold** `` work together in one line."""
    from factory_dashboard.milestones import _to_html

    result = _to_html("Use **`run_order`** for the list.")
    assert "<strong>" in result
    assert "<code>run_order</code>" in result


def test_to_html_link_with_bold_and_code():
    """Links work alongside bold and code."""
    from factory_dashboard.milestones import _to_html

    result = _to_html("See **`ADR 1`** at [link](https://example.com).")
    assert "<strong>" in result
    assert "<code>ADR 1</code>" in result
    assert '<a href="https://example.com">link</a>' in result


def test_to_html_consecutive_indented_bullets_nest_in_one_ul():
    """Two or more consecutive indented bullets under a bullet all sit in one nested
    <ul>, which is inside the parent's <li>."""
    from factory_dashboard.milestones import _to_html

    result = _to_html("- Top\n  - Nested 1\n  - Nested 2\n- Another top")
    # Nested <ul> must be inside the first <li> (opens before, closes after).
    first_li_end = result.index("</li>")
    ul_open = result.index("<ul>")
    ul_close = result.index("</ul>")
    assert ul_open < first_li_end, f"nested <ul> must open inside parent <li>; got: {result}"
    assert ul_close > first_li_end, f"nested </ul> must close after parent </li>; got: {result}"
    # Both nested items are inside the nested <ul>
    nested_1_start = result.index("Nested 1")
    nested_2_start = result.index("Nested 2")
    assert ul_open < nested_1_start < ul_close
    assert ul_open < nested_2_start < ul_close
    # Exactly one nested <ul>
    assert result.count("<ul>") == 2
    assert result.count("</ul>") == 2
    # Second top-level item is after </ul>
    after_nested = result[ul_close + len("</ul>") :]
    assert "<li>Another top</li>" in after_nested


def test_to_html_three_consecutive_indented_bullets_in_one_ul():
    """Three consecutive indented bullets under a bullet all sit in one nested <ul>."""
    from factory_dashboard.milestones import _to_html

    result = _to_html("- Top\n  - A\n  - B\n  - C\n- Bottom")
    assert result.count("<ul>") == 2
    assert result.count("</ul>") == 2
    # All three nested items are inside the single nested <ul>
    ul_open = result.index("<ul>")
    ul_close = result.index("</ul>")  # first </ul> closes the nested <ul>
    for item in ("A", "B", "C"):
        pos = result.index(item)
        assert ul_open < pos < ul_close, f"{item} not inside nested <ul>: {result}"
    # Bottom is after the nested </ul> but before the outer </ul>
    after_nested = result[ul_close + len("</ul>") :]
    assert "<li>Bottom</li>" in after_nested


def test_to_html_url_with_quote_does_not_break_href():
    """A url containing \\\" never produces an attribute other than href; it is encoded."""
    from factory_dashboard.milestones import _to_html

    result = _to_html('See [link](https://a\\"onmouseover="y).')
    # The href must only contain the url with encoded quotes (backslash preserved)
    assert 'href="https://a\\%22onmouseover=%22y"' in result
    # onmouseover= is inside the URL string, not a separate attribute
    href_match = re.search(r'href="([^"]*)"', result)
    assert href_match
    url = href_match.group(1)
    # The URL should not have an unencoded quote that breaks the attribute
    assert url.count("%22") == 2, f"Expected 2 encoded quotes in URL, got: {url}"


def test_to_html_code_is_protected_from_bold_and_links():
    """Text inside `` `code` `` isn't turned into bold or links."""
    from factory_dashboard.milestones import _to_html

    # Bold inside code should not be applied
    result = _to_html("Use **`bold inside code`** here.")
    assert "<code>bold inside code</code>" in result
    # The word "bold" inside code should not be wrapped in <strong>
    code_start = result.index("<code>")
    code_end = result.index("</code>") + len("</code>")
    code_content = result[code_start:code_end]
    assert "<strong>" not in code_content, f"bold should not be applied inside code: {code_content}"

    # Link inside code should not be applied
    result2 = _to_html("See [`link`](https://example.com) here.")
    assert "<code>link</code>" in result2
    code_start2 = result2.index("<code>")
    code_end2 = result2.index("</code>") + len("</code>")
    code_content2 = result2[code_start2:code_end2]
    assert "href=" not in code_content2, f"link should not be applied inside code: {code_content2}"


def test_to_html_nested_list_inside_parent_li():
    """A nested ``<ul>`` sits inside its parent's ``<li>``, not between ``</li>`` and ``<ul>``."""
    from factory_dashboard.milestones import _to_html

    result = _to_html("- Top\n  - A\n  - B\n- Bottom")
    assert result == "<ul><li>Top<ul><li>A</li><li>B</li></ul></li><li>Bottom</li></ul>"


def test_to_html_nested_list_ends_text():
    """A nested list that ends the text closes ``</ul></li>`` before the outer ``</ul>``."""
    from factory_dashboard.milestones import _to_html

    result = _to_html("- Top\n  - A\n  - B")
    assert result == "<ul><li>Top<ul><li>A</li><li>B</li></ul></li></ul>"


def test_to_html_nested_list_followed_by_plain_line():
    """A nested list followed by a plain line closes ``</ul></li>`` before the outer ``</ul>``."""
    from factory_dashboard.milestones import _to_html

    result = _to_html("- Top\n  - A\n  - B\nplain text")
    assert result == "<ul><li>Top<ul><li>A</li><li>B</li></ul></li></ul><p>plain text</p>"


def test_to_html_plain_line_after_simple_bullet():
    """``- a\nplain`` gives ``<ul><li>a</li></ul><p>plain</p>``."""
    from factory_dashboard.milestones import _to_html

    result = _to_html("- a\nplain")
    assert result == "<ul><li>a</li></ul><p>plain</p>"


def test_to_html_plain_line_after_numbered_list():
    """``1. a\nplain`` gives ``<ol><li>a</li></ol><p>plain</p>``."""
    from factory_dashboard.milestones import _to_html

    result = _to_html("1. a\nplain")
    assert result == "<ol><li>a</li></ol><p>plain</p>"


def test_to_html_blank_line_closes_list():
    """A blank line after a list still closes it."""
    from factory_dashboard.milestones import _to_html

    result = _to_html("- a\n\nplain")
    assert result == "<ul><li>a</li></ul><p>plain</p>"


def test_to_html_numbered_and_bullet_whole_string():
    """``1. a``, ``- b``, ``2. c`` produces balanced tags on the full string."""
    from factory_dashboard.milestones import _to_html

    result = _to_html("1. a\n- b\n2. c")
    assert result == "<ol><li>a</li></ol><ul><li>b</li></ul><ol><li>c</li></ol>"


def test_to_html_url_with_quote():
    """A URL with a ``\\\"`` is encoded and the whole string is correct."""
    from factory_dashboard.milestones import _to_html

    result = _to_html('See [link](https://a\\"onmouseover="y).')
    assert result == '<p>See <a href="https://a\\%22onmouseover=%22y">link</a>.</p>'


def test_to_html_nested_bullet_then_numbered():
    """A nested bullet followed by a numbered item closes the nested list before the
    numbered one starts, checked on the full string."""
    from factory_dashboard.milestones import _to_html

    result = _to_html("- Top\n  - A\n1. n")
    assert result == "<ul><li>Top<ul><li>A</li></ul></li></ul><ol><li>n</li></ol>"


def test_to_html_a_bullet_under_a_step_sits_inside_the_step():
    """F216 review: a bullet indented under a numbered step nests in the step's ``<li>``,
    and the steps stay one ``<ol>``, so the next one isn't numbered 1 again."""
    from factory_dashboard.milestones import _to_html

    result = _to_html("1. Open it\n   - a detail\n2. Then this")
    assert result == "<ol><li>Open it<ul><li>a detail</li></ul></li><li>Then this</li></ol>"


def test_to_html_a_wrapped_step_stays_one_step():
    """F216 review: m12's How to test, as stored, wraps a step on indented lines; they are
    the step's text, and the steps after it stay in the same list."""
    from factory_dashboard.milestones import _to_html

    text = (
        "1. On your phone, open Me.\n"
        "2. Tap **COASTER RANKER**: the train runs under the letters\n"
        "   (each one jumps), loops and leaves.\n"
        "3. Tap the title again."
    )
    assert _to_html(text) == (
        "<ol><li>On your phone, open Me.</li><li>Tap <strong>COASTER RANKER</strong>: the"
        " train runs under the letters (each one jumps), loops and leaves.</li>"
        "<li>Tap the title again.</li></ol>"
    )


def test_to_html_uneven_indents_still_nest_inside_an_li():
    """F216 review: a dedent to an indent no list has opens a list in the open item, never
    a stray ``</li>``."""
    from factory_dashboard.milestones import _to_html

    assert _to_html("- a\n    - deep\n  - mid\n- c") == (
        "<ul><li>a<ul><li>deep</li></ul><ul><li>mid</li></ul></li><li>c</li></ul>"
    )


def test_to_html_a_link_keeps_brackets_in_its_url():
    """F216 review: ``(…)`` inside a url stays in the href."""
    from factory_dashboard.milestones import _to_html

    assert _to_html("[x](https://e.com/a_(b)) here") == (
        '<p><a href="https://e.com/a_(b)">x</a> here</p>'
    )


# --- f216-03: the page once its review is written: plates, Sign off, then folds -------------

_F187_SHEET = {
    "changed": (
        "- **Nothing should look different.** Every page shows the same clock times.\n"
        "- **The factory now writes every new time in UTC.**"
    ),
    "how_to_test": (
        "1. Open the Overview on your phone.\n2. Open the Timeline, Runs and Jobs pages."
    ),
    "done_check": (
        "- **Not yet:** the stored times at 0 not in UTC.\n"
        "- **Met:** with the zone set to Paris, `08:00+00:00` shows as 09:00."
    ),
    "decisions": "None. ADR 31 was already accepted.",
    "along_the_way": (
        "- **Also changed how a limit's reset time is read.** It returns UTC. *The review.*\n"
        "- **The dashboard's tests now run in UTC.** *The lead, on f187-02.*"
    ),
    "what_next": "- **Factory:** make the suite fit a review's 10-minute limit.",
    "later": "- A conversion that keeps failing writes a copy.\n- The old JSON state lapses.",
    "lessons": (
        "- **UK winter hides this whole class of bug.**\n"
        "- **A clock's readers change too.**\n"
        "- **A sweep by column name misses renamed values.**"
    ),
    "clogged": "- **The local model's three attempts: 34 minutes.** Fixed: a worked example.",
}

_F175_ASKS = (
    "**ADR 39: bound the run logs.** The job logs take about 800 MB. I recommend compressing"
    " logs older than 90 days."
)

_FOLDS = ["later", "findings", "lessons", "clogged", "results", "grew", "tickets", "runs"]


def _ripe_card(db_path, key: str, sheet: dict[str, str], *, costs: bool = True) -> None:
    """A ripe card ``key`` (its one ticket done, its sheet stored), with a review and the lead's
    ticket's jobs in one run, and three findings: two fixed, one left (F187's shape)."""
    conn = metrics.open_db(db_path)
    try:
        pid = metrics.upsert_project(conn, PROJECT)
        m = metrics.upsert_milestone(
            conn,
            pid,
            key,
            title=f"Card {key}",
            status="review",
            review_score=7,
            review_rounds=1,
            outcome="Every time the factory stores is UTC.",
            done_when="- the plan's own Done when line",
            signoff=sheet,
            started="2026-09-29T09:00:00+02:00",
        )
        ticket = metrics.upsert_ticket(
            conn,
            pid,
            f"{key}-01-clocks",
            milestone_id=m,
            kind="lead",
            state="done",
            merged_by=OPUS,
            commit="e" * 40,
            lines_changed=40,
        )
        if costs:
            run = metrics.upsert_run(conn, pid, "20260930-110000")
            _job(conn, run, m, ticket, "lead-ticket", OPUS, 1, "passed", cost_usd=1.3)
            review = _job(conn, run, m, None, "review", OPUS, 1, "passed", cost_usd=2.85)
            for n, (severity, route, resolved) in enumerate(
                (
                    ("should-fix", "local", True),
                    ("nit", "report", None),
                    ("blocking", "local", True),
                ),
                start=1,
            ):
                metrics.add_finding(
                    conn,
                    m,
                    f"F{n}",
                    job_id=review,
                    severity=severity,
                    route=route,
                    resolved=resolved,
                    summary=f"Finding {n}",
                )
    finally:
        conn.close()


def test_to_html_single_stars_are_emphasis_as_d2_ends_a_choice():
    from factory_dashboard.milestones import _to_html

    assert _to_html("- **Kept it.** Why. *The review.*") == (
        "<ul><li><strong>Kept it.</strong> Why. <em>The review.</em></li></ul>"
    )
    # a lone star, or stars inside a word or a sum, stay as they are
    assert _to_html("2 * 3 * 4, a*b*c") == "<p>2 * 3 * 4, a*b*c</p>"


def test_inline_html_code_becomes_code_tag():
    from factory_dashboard.milestones import inline_html

    result = inline_html("`git show x`")
    assert "<code>git show x</code>" in str(result)


def test_inline_html_bold_becomes_strong():
    from factory_dashboard.milestones import inline_html

    result = inline_html("**x**")
    assert "<strong>x</strong>" in str(result)


def test_inline_html_http_link_becomes_anchor():
    from factory_dashboard.milestones import inline_html

    result = inline_html("[a](https://x)")
    assert '<a href="https://x">a</a>' in str(result)


def test_inline_html_non_http_link_becomes_text():
    from factory_dashboard.milestones import inline_html

    result1 = inline_html("[a](javascript:x)")
    assert "a" in str(result1)
    assert "href=" not in str(result1)

    result2 = inline_html("[a](../x.md)")
    assert "a" in str(result2)
    assert "href=" not in str(result2)


def test_inline_html_script_is_escaped():
    from factory_dashboard.milestones import inline_html

    result = inline_html("<script>")
    assert "&lt;script&gt;" in str(result)
    assert "<script>" not in str(result)


def test_inline_html_code_inside_backticks_is_escaped():
    from factory_dashboard.milestones import inline_html

    result = inline_html("`<b>`")
    assert "<code>&lt;b&gt;</code>" in str(result)


def test_inline_html_stars_inside_backticks_stay_as_typed():
    from factory_dashboard.milestones import inline_html

    result = inline_html("`**not from the code**`")
    assert "<code>" in str(result)
    code_match = re.search(r"<code>(.*?)</code>", str(result), re.S)
    assert code_match
    assert "**" in code_match.group(1)


def _part(page: str, name: str) -> str:
    """The raw HTML of the page's ``<section>`` or ``<details>`` with ``id="name"``."""
    match = re.search(rf'<(section|details)[^>]*\bid="{name}"[^>]*>(.*?)</\1>', page, re.S)
    assert match, f"no part {name}"
    return match.group(2)


def _gist(page: str, name: str) -> str:
    """A fold's summary line, as words."""
    match = re.search(r"<summary>(.*?)</summary>", _part(page, name), re.S)
    assert match, f"{name} has no summary"
    return _words(match.group(1))


def test_a_sheet_page_comes_in_d8_order_with_sign_off_before_what_next(db_path, serve):
    _ripe_card(db_path, "f187-utc", {**_F187_SHEET, "decisions": _F175_ASKS})
    page = serve().get("/milestones/f187-utc").text
    order = [
        'id="card-head"',
        'id="decisions"',
        'id="about"',
        'id="what-changed"',
        'id="how-to-test"',
        'id="along-the-way"',
        'id="review"',
        'id="what-next"',
        'id="behind"',
        *(f'id="{f}"' for f in _FOLDS),
    ]
    places = [page.index(mark) for mark in order]
    assert places == sorted(places), order
    assert 'id="signoff-button"' in _part(page, "review")
    assert "Needs your answer" in _words(_part(page, "decisions"))
    assert "ADR 39: bound the run logs." in _words(_part(page, "decisions"))
    # every part is the one plate, and nothing is styled in place
    for part in ("decisions", "about", "what-changed", "how-to-test", "along-the-way", "what-next"):
        # "about" keeps its own class beside the plate's, for its fold of the note
        assert re.search(rf'<section class="card-plate[^"]*" id="{part}"', page), part
    assert "style=" not in _part(page, "review")


def test_the_eight_folds_are_closed_with_their_gists(db_path, serve):
    _ripe_card(db_path, "f187-utc", _F187_SHEET)
    page = serve().get("/milestones/f187-utc").text
    behind = re.search(r'<section[^>]*id="behind"[^>]*>(.*?)</section>', page, re.S)
    assert behind and "Behind it" in behind.group(1)
    folds = re.findall(r'<details([^>]*)\bid="([a-z-]+)"', behind.group(1))
    assert [name for _, name in folds] == _FOLDS
    assert all("open" not in attrs for attrs, _ in folds)
    assert _gist(page, "later") == "Left for later 2 points"
    assert _gist(page, "findings") == "What the review caught 3: 2 fixed, 1 left as it is"
    assert _gist(page, "lessons") == "Lessons 3"
    assert _gist(page, "clogged") == "What clogged the line 1, with its fix"
    assert _gist(page, "results") == "What it cost $4.15, of which the review $2.85"
    assert _gist(page, "tickets") == "Tickets 1 of 1 done"
    assert _gist(page, "runs") == "Runs 1"
    assert _gist(page, "grew").startswith("Your note and how it grew Ripe")
    words = _words(page)
    for empty in ("Not written yet", "No runs.", "No savings data.", "No results yet."):
        assert empty not in words


def test_a_fold_with_nothing_in_it_is_not_drawn(db_path, serve):
    sheet = {k: v for k, v in _F187_SHEET.items() if k not in ("later", "lessons", "clogged")}
    _ripe_card(db_path, "f188-bare", sheet, costs=False)
    page = serve().get("/milestones/f188-bare").text
    for gone in ("later", "lessons", "clogged", "findings", "runs"):
        assert f'id="{gone}"' not in page, gone
    assert 'id="grew"' in page and 'id="tickets"' in page
    assert "Not written yet" not in _words(page)


def test_a_fold_whose_text_is_not_in_bullets_shows_its_name_alone(db_path, serve):
    _ripe_card(db_path, "f189-prose", {**_F187_SHEET, "later": "Nothing much, all in one line."})
    page = serve().get("/milestones/f189-prose").text
    assert _gist(page, "later") == "Left for later"


def test_done_when_as_of_now_replaces_the_plan_s_and_falls_back_to_it(db_path, serve):
    _ripe_card(db_path, "f187-utc", _F187_SHEET)
    _ripe_card(db_path, "f190-old", {k: v for k, v in _F187_SHEET.items() if k != "done_check"})
    about = _words(_part(serve().get("/milestones/f187-utc").text, "about"))
    assert "Done when, as of now" in about
    assert "Not yet: the stored times at 0 not in UTC." in about
    assert "the plan's own Done when line" not in about
    old = _words(_part(serve().get("/milestones/f190-old").text, "about"))
    assert "as of now" not in old
    assert "the plan's own Done when line" in old


def test_a_decisions_starting_none_shows_no_plate(db_path, serve):
    """F187's "None. …" draws nothing, whatever its case; F175's question shows."""
    _ripe_card(db_path, "f187-utc", _F187_SHEET)
    _ripe_card(db_path, "f191-lower", {**_F187_SHEET, "decisions": "none waiting."})
    client = serve()
    for key in ("f187-utc", "f191-lower"):
        page = client.get(f"/milestones/{key}").text
        assert 'id="decisions"' not in page, key
        assert "Needs your answer" not in page, key


def test_what_the_review_caught_and_what_it_cost_draw_the_database_rows(db_path, serve):
    _ripe_card(db_path, "f187-utc", _F187_SHEET)
    page = serve().get("/milestones/f187-utc").text
    caught = re.findall(r"<tr>(.*?)</tr>", _part(page, "findings"), re.S)
    rows = [[_words(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)] for r in caught]
    assert rows == [
        ["blocking", "Finding 3", "fixed"],
        ["should-fix", "Finding 1", "fixed"],
        ["nit", "Finding 2", "left"],
    ]
    cost = _words(_part(page, "results"))
    assert "The review $2.85" in cost and "The lead's tickets $1.30" in cost
    assert "Review score 7.0/10" in cost and "Review rounds 1" in cost
    # no developer lines: no savings; no separate Findings, Results or Savings parts
    assert 'id="savings"' not in page
    assert "Findings by severity" not in page
    assert page.count('id="results"') == 1 and page.count('id="findings"') == 1


def test_savings_show_in_what_it_cost_only_with_developer_lines(milestone_detail_client):
    """f1's developer merged 100 lines: its savings are in What it cost."""
    page = milestone_detail_client.get("/milestones/f1").text
    cost = _part(page, "results")
    assert 'id="savings"' in cost
    assert "$1.50" in _words(cost) and "-$2.70" in _words(cost)
    assert "Developers, first time 1 of 2" in _words(cost)


def test_a_card_with_no_sheet_draws_as_before(milestone_detail_client):
    page = milestone_detail_client.get("/milestones/f10").text
    ids = re.findall(r'<section[^>]*\bid="([a-z-]+)"', page)
    assert ids == [
        "about",
        "grew",
        "review-wait",
        "results",
        "savings",
        "tickets",
        "runs",
        "findings",
    ]
    assert "<details" not in page.split('id="grew"')[1]


def test_the_sheet_page_has_no_sideways_scroll_on_a_phone_and_folds_open_without_script(
    page, db_path, serve
):
    _ripe_card(db_path, "f187-utc", {**_F187_SHEET, "decisions": _F175_ASKS})
    page.set_viewport_size(PHONE)
    client = serve()
    # tapping a fold needs no script: plain <details>, nothing listening on them
    behind = _part(client.get("/milestones/f187-utc").text, "behind")
    assert "<script" not in behind and "hx-" not in behind
    assert not re.search(r"\son[a-z]+=", behind)
    open_page(page, client, "/milestones/f187-utc")
    page.evaluate("() => document.fonts.ready")
    page.evaluate("() => document.querySelector('nav.tabs').setAttribute('data-layout', 'overlay')")
    problems = layout_problems(page)
    assert problems == [], "\n".join(problems)
    fold = page.locator("#findings")
    assert fold.get_attribute("open") is None
    fold.locator("summary").click()
    assert fold.get_attribute("open") == ""
    assert page.locator("#findings table").is_visible()
    assert page.evaluate("() => document.documentElement.scrollWidth") <= PHONE["width"]
