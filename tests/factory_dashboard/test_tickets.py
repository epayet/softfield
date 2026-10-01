"""Tests for the tickets list and ticket detail pages (f1-10, f1-36)."""

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


def section_raw(html: str, name: str) -> str:
    """The raw HTML of the page's ``<section id="name">``."""
    match = re.search(rf'<section[^>]*\bid="{name}"[^>]*>(.*?)</section>', html, re.S)
    assert match, f"no section {name}"
    return match.group(1)


def breadcrumbs(html: str) -> str:
    """The text of the nav.crumbs element, tags stripped."""
    match = re.search(r'<nav[^>]*class="crumbs"[^>]*>(.*?)</nav>', html, re.S)
    assert match, "no nav.crumbs"
    return " ".join(re.sub(r"<[^>]+>", " ", match.group(1)).split())


@pytest.fixture
def tickets_client(db_path: Path) -> TestClient:
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


def test_list_shows_tickets_newest_first(tickets_client):
    html = tickets_client.get("/tickets").text
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    tbody_rows = [r for r in rows if "<td" in r and "<th" not in r]
    links = [
        m.group(1) for r in tbody_rows for m in [re.search(r'href="/tickets/([^"?]+)', r)] if m
    ]
    f1_tickets = [t for t in links if t.startswith("f1-")]
    m4_tickets = [t for t in links if t.startswith("m4-")]
    assert len(f1_tickets) == 9
    assert len(m4_tickets) == 2
    # f1 milestone (started 2026-09-30) > m4 (started 2026-09-20), so f1 first.
    # Within each milestone, ordered by database id DESC.
    assert f1_tickets[0] == "f1-04-live"
    assert f1_tickets[1] == "f1-05-first"
    assert f1_tickets[2] == "f1-06-second"
    assert f1_tickets[3] == "f1-12-escalated"
    assert f1_tickets[4] == "f1-11-ticket-b"
    assert f1_tickets[5] == "f1-10-ticket-a"
    assert f1_tickets[6] == "f1-03-lead"
    assert f1_tickets[7] == "f1-02-escalated"
    assert f1_tickets[8] == "f1-01-first"
    assert m4_tickets[0] == "m4-02-ticket-c"
    assert m4_tickets[1] == "m4-01-old"


def test_filter_by_state_shows_only_matching(tickets_client):
    resp = tickets_client.get("/tickets?state=escalated")
    html = resp.text
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    tbody_rows = [r for r in rows if "<td" in r and "<th" not in r]
    assert len(tbody_rows) == 1
    row = tbody_rows[0]
    assert "f1-12-escalated" in row
    assert "escalated" in row


def test_ticket_detail_shows_goal_and_done_when(tickets_client):
    html = tickets_client.get("/tickets/f1-10-ticket-a").text
    goal = section(html, "goal")
    assert "Goal: A ticket." in goal
    assert "Done when: it passes." in goal


def test_ticket_detail_shows_depends_on_as_links(tickets_client):
    html = tickets_client.get("/tickets/f1-11-ticket-b").text
    depends = section(html, "depends")
    assert "f1-10-ticket-a" in depends
    assert 'href="/tickets/f1-10-ticket-a' in html


def test_ticket_detail_shows_result(tickets_client):
    html = tickets_client.get("/tickets/f1-11-ticket-b").text
    result = section(html, "result")
    assert "done" in result
    assert "claude-opus" in result
    assert "ffffffffffffffffffffffffffffffffffffffff" in result
    assert "50" in result


def test_ticket_detail_shows_all_jobs_in_order(tickets_client):
    html = tickets_client.get("/tickets/f1-11-ticket-b").text
    jobs = section(html, "jobs")
    assert "attempt 1" in jobs
    assert "attempt 2" in jobs
    assert "attempt 3" in jobs
    assert "escalation" in jobs
    jobs_raw = section_raw(html, "jobs")
    job_links = re.findall(r'href="/jobs/(\d+)', jobs_raw)
    assert len(job_links) == 3


def test_findings_with_ticket_id_shows_only_on_that_ticket(tickets_client):
    html = tickets_client.get("/tickets/m4-02-ticket-c").text
    findings = section(html, "findings")
    assert "M4-F1" in findings
    assert "M4-F2" in findings
    assert "blocking" in findings
    assert "nit" in findings


def test_ticket_specific_finding_shows_only_on_that_ticket(tickets_client):
    html_b = tickets_client.get("/tickets/f1-11-ticket-b").text
    findings_b = section(html_b, "findings")
    assert "TICKET-F1" in findings_b
    assert "ticket specific" in findings_b

    html_a = tickets_client.get("/tickets/f1-10-ticket-a").text
    assert re.search(r'<section[^>]*\bid="findings"', html_a, re.S) is None


def test_milestone_wide_finding_absent_from_ticket_pages(tickets_client):
    html_a = tickets_client.get("/tickets/f1-10-ticket-a").text
    html_b = tickets_client.get("/tickets/f1-11-ticket-b").text
    html_c = tickets_client.get("/tickets/m4-02-ticket-c").text
    assert "MILESTONE-WIDE" not in html_a
    assert "MILESTONE-WIDE" not in html_b
    assert "MILESTONE-WIDE" not in html_c


def test_unknown_ticket_is_404(tickets_client):
    resp = tickets_client.get("/tickets/f999-unknown")
    assert resp.status_code == 404


def test_list_keeps_filter_values(tickets_client):
    resp = tickets_client.get("/tickets?state=done")
    html = resp.text
    assert 'name="state"' in html
    assert 'value="done"' in html
    assert 'name="milestone"' in html


def test_ticket_detail_shows_files(tickets_client):
    html = tickets_client.get("/tickets/f1-11-ticket-b").text
    files = section(html, "files")
    assert "b.py" in files
    assert "c.py" in files


def test_filter_by_milestone_shows_only_matching(tickets_client):
    resp = tickets_client.get("/tickets?milestone=f1")
    html = resp.text
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    tbody_rows = [r for r in rows if "<td" in r and "<th" not in r]
    ticket_ids = []
    for r in tbody_rows:
        m = re.search(r'href="/tickets/([^"?]+)', r)
        if m:
            ticket_ids.append(m.group(1))
    assert len(ticket_ids) == 9
    for tid in ticket_ids:
        assert tid.startswith("f1-")
    assert "m4" not in html


def test_ticket_breadcrumbs(tickets_client):
    html = tickets_client.get("/tickets/f1-11-ticket-b").text
    crumbs = breadcrumbs(html)
    assert "coucou" in crumbs
    assert "f1" in crumbs
    assert "f1-11-ticket-b" in crumbs


def test_ticket_agent_work_shows_two_agents(tickets_client):
    html = tickets_client.get("/tickets/f1-11-ticket-b").text
    section = section_raw(html, "agent-work")
    assert "claude-opus" in section
    assert "local-qwen3.6-35b-a3b" in section
    assert "merged" in section
    assert "1" in section
    assert "2" in section
    assert "10000" in section
    assert "200000" in section
    assert "2.00" in section


def test_ticket_agent_work_order_merger_first_then_minutes(
    tickets_client,
):
    html = tickets_client.get("/tickets/f1-11-ticket-b").text
    section = section_raw(html, "agent-work")
    merged_pos = section.find("merged")
    claude_pos = section.find("claude-opus")
    local_pos = section.find("local-qwen3.6-35b-a3b")
    assert claude_pos < merged_pos < local_pos


def test_ticket_agent_work_absent_when_no_jobs(tickets_client):
    html = tickets_client.get("/tickets/f1-12-escalated").text
    assert re.search(r'<section[^>]*\bid="agent-work"', html, re.S) is None
