import html
import json
import re

import pytest

from runner import metrics
from tests.factory_dashboard.conftest import NOW, PROJECT


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


def _posts(row: str) -> list[tuple[str, dict[str, object]]]:
    found = re.findall(r"<button[^>]*?hx-vals='([^']*)'[^>]*>(.)</button>", row)
    return [(arrow, json.loads(vals)) for vals, arrow in found]


def test_each_milestone_not_done_shows_its_priority_with_buttons_that_move_it(
    milestones_client, db_path
):
    """f6-18: ↑ asks for one less than the milestone before it in the run order (0 at least),
    ↓ one more than the one after it; a done milestone, or one with no card, has none."""
    from tests.factory_dashboard.conftest import PROJECT

    _cards(db_path)
    html = milestones_client.get("/milestones").text
    assert "<th>Priority</th>" in html or '<th class="num">Priority</th>' in html

    def post(key: str, value: str) -> dict[str, object]:
        return {"kind": "priority", "project": PROJECT, "subject": key, "value": value}

    cells, row = _row_cells(html, "F2")
    assert cells[-1] == "5 ↑ ↓"
    # Run order includes F3(2), F2(5), F5(10), F10(100); F2's neighbors are F3 and F5
    assert _posts(row) == [("↑", post("f2", "1")), ("↓", post("f2", "11"))]
    cells, row = _row_cells(html, "F10")
    assert cells[-1] == "100 ↑ ↓"
    # F10's neighbor above is F5(10)
    assert _posts(row) == [("↑", post("f10", "9")), ("↓", post("f10", "101"))]
    for key in ("F1", "M4"):
        cells, row = _row_cells(html, key)
        assert cells[-1] == "–" and _posts(row) == []
    # the columns before it are as they were
    assert _row_cells(html, "F1")[0][:4] == ["F1", "The factory measures itself", "done", "3"]


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
        ("how-to-test", "Run `uv run runner milestone f1`"),
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
