import json
import re

import pytest


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


def test_milestones_shows_newest_first(milestones_client):
    """Milestones ordered by start date, newest first.

    F2 (2026-10-01) > F10 (2026-09-30) > F1 (2026-09-30) > M4 (2026-09-20).
    F10 sorts before F1 because they share the same date and 'f10' < 'f1' in key order.
    """
    html = milestones_client.get("/milestones").text
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    # Find rows by their exact key cell (first <td>).
    key_cells = []
    for row in rows:
        tds = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row, re.S)
        tds = [re.sub(r"<[^>]+>", " ", c).strip() for c in tds]
        if tds:
            key_cells.append(tds[0])
    f2_pos = key_cells.index("F2")
    f1_pos = key_cells.index("F1")
    f10_pos = key_cells.index("F10")
    m4_pos = key_cells.index("M4")
    assert f2_pos < f10_pos < f1_pos < m4_pos


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
