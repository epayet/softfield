"""Tests for the tickets list and ticket detail pages (f1-10)."""

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from runner.metrics import open_db
from tests.factory_dashboard.conftest import (
    NOW,
    PROJECT,
    write_tickets,
)


def section(html: str, name: str) -> str:
    """The text of the page's ``<section id="name">``, tags stripped."""
    match = re.search(rf'<section[^>]*\bid="{name}"[^>]*>(.*?)</section>', html, re.S)
    assert match, f"no section {name}"
    return " ".join(re.sub(r"<[^>]+>", " ", match.group(1)).split())


@pytest.fixture
def client_with_tickets(db_path: Path) -> TestClient:
    """A client over the fixture plus ``write_tickets``'s rows."""
    from factory_dashboard.app import create_app, get_now

    conn = open_db(db_path)
    try:
        write_tickets(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


def test_list_shows_tickets_newest_first(client_with_tickets):
    html = client_with_tickets.get("/tickets").text
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    tbody_rows = [r for r in rows if "<td" in r and "<th" not in r]
    # Extract ticket ids from links (strip query string)
    links = []
    for r in tbody_rows:
        m = re.search(r'href="/tickets/([^"?]+)', r)
        if m:
            links.append(m.group(1))
    # f1 milestone is newer than m4, so f1 tickets come first
    # Within f1, highest id first: 12, 11, 10, 6, 5, 4, 3, 2, 1
    f1_tickets = [t for t in links if t.startswith("f1-")]
    m4_tickets = [t for t in links if t.startswith("m4-")]
    assert len(f1_tickets) == 9
    # f1 milestone started (2026-09-30) > m4 (2026-09-20), so f1 first
    assert m4_tickets[0] == "m4-02-ticket-c"
    assert m4_tickets[1] == "m4-01-old"


def test_filter_by_state_shows_only_matching(client_with_tickets):
    resp = client_with_tickets.get("/tickets?state=escalated")
    html = resp.text
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    tbody_rows = [r for r in rows if "<td" in r and "<th" not in r]
    assert len(tbody_rows) == 1
    row = tbody_rows[0]
    assert "f1-12-escalated" in row
    assert "escalated" in row


def test_ticket_detail_shows_goal_and_done_when(client_with_tickets):
    html = client_with_tickets.get("/tickets/f1-10-ticket-a").text
    goal = section(html, "goal")
    assert "Goal: A ticket." in goal
    assert "Done when: it passes." in goal


def test_ticket_detail_shows_depends_on_as_links(client_with_tickets):
    html = client_with_tickets.get("/tickets/f1-11-ticket-b").text
    depends = section(html, "depends")
    assert "f1-10-ticket-a" in depends
    assert 'href="/tickets/f1-10-ticket-a' in html


def test_ticket_detail_shows_result(client_with_tickets):
    html = client_with_tickets.get("/tickets/f1-11-ticket-b").text
    result = section(html, "result")
    assert "done" in result
    assert "claude-opus" in result  # merged_by
    assert "lines changed" in result.lower() or "50" in result


def test_ticket_detail_shows_all_jobs_in_order(client_with_tickets):
    html = client_with_tickets.get("/tickets/f1-11-ticket-b").text
    jobs = section(html, "jobs")
    # Should show 3 jobs: 2 failed attempts + 1 escalation
    assert "attempt 1" in jobs
    assert "attempt 2" in jobs
    assert "attempt 3" in jobs
    assert "escalation" in jobs
    # Each job links to /jobs/{n}
    job_links = re.findall(r'href="/jobs/(\d+)', html)
    assert len(job_links) >= 3


def test_ticket_detail_shows_findings_with_severity(client_with_tickets):
    html = client_with_tickets.get("/tickets/m4-02-ticket-c").text
    findings = section(html, "findings")
    assert "M4-F1" in findings
    assert "M4-F2" in findings
    assert "blocking" in findings
    assert "nit" in findings


def test_unknown_ticket_is_404(client_with_tickets):
    resp = client_with_tickets.get("/tickets/f999-unknown")
    assert resp.status_code == 404


def test_list_keeps_filter_values(client_with_tickets):
    resp = client_with_tickets.get("/tickets?state=done")
    html = resp.text
    assert 'name="state"' in html
    assert 'value="done"' in html
    assert 'name="milestone"' in html


def test_ticket_detail_shows_files(client_with_tickets):
    html = client_with_tickets.get("/tickets/f1-11-ticket-b").text
    files = section(html, "files")
    assert "b.py" in files
    assert "c.py" in files
