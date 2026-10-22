import html
import json
import re

import pytest
from fastapi.testclient import TestClient

from runner import metrics
from tests.factory_dashboard.conftest import LOCAL, NOW, PROJECT, write_signoff_button
from tests.factory_dashboard.test_planning import _open as open_page
from tests.layout import DISPLAY, PHONE, layout_problems


def section(html: str, name: str) -> str:
    """The text of the page's ``<section id="name">``, tags stripped."""
    match = re.search(rf'<section[^>]*\bid="{name}"[^>]*>(.*?)</section>', html, re.S)
    assert match, f"no section {name}"
    return " ".join(re.sub(r"<[^>]+>", " ", match.group(1)).split())


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
    assert "F99" not in keys


def test_milestone_detail_answers_200(milestone_detail_client):
    resp = milestone_detail_client.get("/milestones/f1")
    assert resp.status_code == 200


def test_milestone_detail_sections_in_d8_order(milestone_detail_client):
    html = milestone_detail_client.get("/milestones/f1").text
    ids = re.findall(r'<section[^>]*\bid="([a-z-]+)"', html)
    expected = [
        "outcome",
        "what-changed",
        "how-to-test",
        "what-next",
        "later",
        "lessons",
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
    outcome = section(html, "outcome")
    assert "The factory now measures itself end-to-end." in outcome
    assert "All tickets in" in outcome


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
    # f10 has no signoff, so all signoff sections should show "Not written yet"
    for section_name in (
        "what-changed",
        "how-to-test",
        "decisions",
        "what-next",
        "later",
        "lessons",
        "clogged",
    ):
        sec_text = section(html, section_name)
        assert "Not written yet" in sec_text, f"{section_name} should show 'Not written yet'"


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
    done_when = section(html, "outcome")
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
    """A client over ``write_board``'s rows, plus on ``f24-growing``: a lead ticket that goes
    first (``priority: 0``) and a developer one that waits for ``f24-03-next``."""
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
    assert "Stage Growing: in the factory" in head
    assert "Priority P1" in head
    assert "Area factory" in head
    assert "Tickets 1 of 5 done · 1 set aside" in head

    seed = _card_head(card_client.get("/milestones/f20-duck-pond").text)
    assert "Stage Seed: idea or set aside" in seed
    assert "Priority P30" in seed
    assert "Area product" in seed
    assert "Tickets none yet" in seed


def test_the_header_s_stage_is_the_board_s_not_the_doc_s_status(card_client, board_db):
    """``f25-unreviewed`` has every ticket done: growing until the review's sheet is stored,
    then ripe, whatever its ``status`` says."""
    assert "Stage Growing" in _card_head(card_client.get("/milestones/f25-unreviewed").text)
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
    assert [name for name, *_ in grew] == [
        "Seed",
        "Sprouting",
        "Planted",
        "Growing",
        "Ripe",
        "Harvested",
    ]
    assert [name for name, current, _, _ in grew if current] == ["Growing"]
    assert [name for name, _, later, _ in grew if later] == ["Ripe", "Harvested"]

    seed = _grew(card_client.get("/milestones/f20-duck-pond").text)
    assert [name for name, current, _, _ in seed if current] == ["Seed"]
    assert [name for name, _, later, _ in seed if later] == [
        "Sprouting",
        "Planted",
        "Growing",
        "Ripe",
        "Harvested",
    ]

    harvested = _grew(card_client.get("/milestones/m3").text)
    assert [name for name, current, _, _ in harvested if current] == ["Harvested"]
    assert not any(later for _, _, later, _ in harvested)


def test_how_it_grew_dates_growing_and_harvested_where_the_database_has_them(card_client, board_db):
    words = {name: rest for name, _, _, rest in _grew(card_client.get("/milestones/m3").text)}
    assert words["Harvested"] == "15 Sep 12:00"  # ``milestones.ended``
    assert words["Growing"] == ""  # no ``started`` stored: no date made up
    assert words["Seed"] == words["Sprouting"] == words["Planted"] == ""

    # f1 started on 2026-09-30 and is ripe: growing has its date, harvested none yet
    words = {name: rest for name, _, _, rest in _grew(card_client.get("/milestones/f1").text)}
    assert words["Growing"] == "30 Sep 09:00"
    assert words["Harvested"] == ""

    conn = metrics.open_db(board_db)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        for key in ("f23-planted", "f24-growing"):
            metrics.upsert_milestone(conn, project, key, started="2026-10-01T08:30:00+02:00")
    finally:
        conn.close()
    growing = _grew(card_client.get("/milestones/f24-growing").text)
    assert [(name, rest) for name, current, _, rest in growing if current] == [
        ("Growing", "since 1 Oct 08:30")
    ]
    # a card not growing yet shows no growing date, even with one stored
    planted = _grew(card_client.get("/milestones/f23-planted").text)
    assert [(name, rest) for name, current, _, rest in planted if current] == [("Planted", "")]
    assert all(rest == "" for *_, rest in planted)


def test_the_tickets_come_in_run_order_with_who_works_on_each(card_client):
    """Done, then what's being worked on, then the ready ones as the runner will take them
    (priority, then id; one that waits after those it can take), then the set-aside ones. A
    removed ticket (``f24-05-gone``) is left out."""
    rows = _ticket_rows(card_client.get("/milestones/f24-growing").text)
    assert rows == [
        ["f24-01-merged", "Goal of f24-01-merged.", LOCAL, "done"],
        ["f24-02-working", "Goal of f24-02-working.", LOCAL, "running"],
        ["f24-06-lead", "Goal of f24-06-lead.", "the lead", "ready"],
        ["f24-03-next", "Goal of f24-03-next.", "a developer", "ready"],
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
