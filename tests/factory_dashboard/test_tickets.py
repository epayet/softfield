"""Tests for the tickets list and ticket detail pages (f1-10, f1-36)."""

import json
import re
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from runner import metrics
from runner.metrics import open_db
from tests.factory_dashboard.conftest import (
    LOCAL,
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


def listed(html: str) -> list[tuple[str, str]]:
    """Each listed ticket and its Last worked cell, in page order."""
    return re.findall(
        r'<tr>\s*<td class="id"><a href="/tickets/([^"?]+).*?'
        r'<td data-col="last-worked">(.*?)</td>',
        html,
        re.S,
    )


def test_list_shows_latest_work_first_whatever_the_milestone(db_path, tickets_client):
    conn = open_db(db_path)
    try:
        old, m4 = conn.execute(
            "SELECT id, milestone_id FROM tickets WHERE ticket = 'm4-01-old'"
        ).fetchone()
        run = conn.execute("SELECT id FROM runs LIMIT 1").fetchone()[0]
        metrics.start_job(
            conn, run, ticket_id=old, milestone_id=m4, role="developer", agent=LOCAL,
            attempt=9, started=(NOW - timedelta(minutes=3)).isoformat(),
        )  # fmt: skip
    finally:
        conn.close()
    html = tickets_client.get("/tickets").text
    assert "latest work first" in html
    rows = listed(html)
    # m4 started before f1, but its ticket was worked 3 min ago, f1-04-live 12 min ago.
    assert rows[:2] == [("m4-01-old", "3 min ago"), ("f1-04-live", "12 min ago")]


def test_list_puts_unworked_tickets_last_newest_row_first(tickets_client):
    rows = listed(tickets_client.get("/tickets").text)
    cells = [cell for _, cell in rows]
    unworked = cells.index("–")
    assert all(cell != "–" for cell in cells[:unworked])
    assert all(cell == "–" for cell in cells[unworked:])
    assert [ticket for ticket, _ in rows[unworked:]] == [
        "f1-05-first",
        "f1-06-second",
        "f1-12-escalated",
    ]


def test_filter_by_state_shows_only_matching(db_path, tickets_client):
    from runner.metrics import open_db

    conn = open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        metrics.upsert_ticket(
            conn,
            project,
            "f1-99-later",
            milestone_id=f1,
            kind="developer",
            state="later",
            difficulty=3,
            title="A set-aside ticket.",
        )
    finally:
        conn.close()

    resp = tickets_client.get("/tickets?state=escalated")
    html = resp.text
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S)
    tbody_rows = [r for r in rows if "<td" in r and "<th" not in r]
    # 1 main ticket + 1 later panel row
    assert len(tbody_rows) == 2
    # The later panel row comes first in the page; the main table row contains the escalated ticket
    main_rows = [r for r in tbody_rows if "f1-12-escalated" in r]
    assert len(main_rows) == 1
    assert "escalated" in main_rows[0]


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


def agent_row(raw: str, agent: str) -> dict[str, str]:
    """The ``data-col`` cells of the ``<tr data-agent="agent">`` row in ``raw``."""
    match = re.search(rf'<tr[^>]*\bdata-agent="{re.escape(agent)}"[^>]*>(.*?)</tr>', raw, re.S)
    assert match, f"no row for {agent}"
    cells = re.findall(r'<td[^>]*\bdata-col="([^"]+)"[^>]*>(.*?)</td>', match.group(1), re.S)
    return {col: text.strip() for col, text in cells}


def test_ticket_agent_work_shows_two_agents(tickets_client):
    html = tickets_client.get("/tickets/f1-11-ticket-b").text
    raw = section_raw(html, "agent-work")
    assert agent_row(raw, "claude-opus") == {
        "agent": "claude-opus",
        "roles": "escalation",
        "jobs": "1",
        "minutes": "10",
        "tokens-in": "10000",
        "cost": "2.00",
        "merged": "merged",
    }
    assert agent_row(raw, "local-qwen3.6-35b-a3b") == {
        "agent": "local-qwen3.6-35b-a3b",
        "roles": "developer ×2",
        "jobs": "2",
        "minutes": "20",
        "tokens-in": "200000",
        "cost": "–",
        "merged": "",
    }


def test_ticket_agent_work_order_merger_first_then_minutes(
    tickets_client,
):
    html = tickets_client.get("/tickets/f1-11-ticket-b").text
    raw = section_raw(html, "agent-work")
    agents = re.findall(r'<tr[^>]*\bdata-agent="([^"]+)"', raw)
    assert agents == ["claude-opus", "local-qwen3.6-35b-a3b"]


def test_ticket_agent_work_absent_when_no_jobs(tickets_client):
    html = tickets_client.get("/tickets/f1-12-escalated").text
    assert re.search(r'<section[^>]*\bid="agent-work"', html, re.S) is None


def later_row(raw: str, ticket: str) -> dict[str, str]:
    """The ``data-col`` cells of the ``<tr data-ticket="ticket">`` row in ``raw``."""
    match = re.search(rf'<tr[^>]*\bdata-ticket="{re.escape(ticket)}"[^>]*>(.*?)</tr>', raw, re.S)
    assert match, f"no row for {ticket}"
    cells = re.findall(r'<td[^>]*\bdata-col="([^"]+)"[^>]*>(.*?)</td>', match.group(1), re.S)
    return {col: text.strip() for col, text in cells}


def test_later_tickets_panel_shows_kind(later_client):
    html = later_client.get("/tickets").text
    later_section = section_raw(html, "later")
    dev_row = later_row(later_section, "f1-99-later")
    id_cell = dev_row["id"]
    assert f'href="/tickets/f1-99-later?project={PROJECT}"' in id_cell
    assert "f1-99-later" in id_cell
    assert dev_row["goal"] == "A set-aside ticket."
    assert dev_row["kind"] == "developer"
    lead_row = later_row(later_section, "f1-97-later")
    assert lead_row["goal"] == "A lead set-aside ticket."
    assert lead_row["kind"] == "lead"
    # No row shows the old queue command text
    assert "softfield queue" not in later_section
    # Queue button's request (hx-vals parsed as JSON) is queue with that ticket's id as subject
    btn = re.search(
        r'<button[^>]*hx-post="/requests"[^>]*>Queue</button>',
        dev_row["queue"],
        re.S,
    )
    assert btn is not None, "Queue button not found"
    vals = re.search(r'hx-vals=[\'"]\{([^}]*)\}[\'"]', btn.group(0), re.S)
    assert vals is not None
    parsed = json.loads("{" + vals.group(1) + "}")
    assert parsed["kind"] == "queue"
    assert parsed["subject"] == "f1-99-later"


def test_each_queue_button_answers_in_its_own_row(db_path, later_client):
    """With two set-aside tickets, each button's answer goes to a place in its own row."""
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        metrics.upsert_ticket(
            conn,
            project,
            "f1-98-later",
            milestone_id=f1,
            kind="developer",
            state="later",
            difficulty=2,
            title="Another set-aside ticket.",
        )
    finally:
        conn.close()

    html = later_client.get("/tickets").text
    later_section = section_raw(html, "later")

    for ticket in ("f1-99-later", "f1-98-later"):
        row = later_row(later_section, ticket)
        btn = re.search(
            r'<button[^>]*hx-post="/requests"[^>]*>Queue</button>',
            row["queue"],
            re.S,
        )
        assert btn is not None, f"Queue button for {ticket} not found"
        vals = re.search(r'hx-vals=[\'"]\{([^}]*)\}[\'"]', btn.group(0), re.S)
        assert vals is not None
        parsed = json.loads("{" + vals.group(1) + "}")
        assert parsed["kind"] == "queue"
        assert parsed["subject"] == ticket
        # the answer's place is in this row's own Queue cell, where the button points
        assert f'hx-target="#answer-{ticket}"' in btn.group(0)
        assert f'id="answer-{ticket}"' in row["queue"], f"answer div for {ticket} not in its row"

    # The answer divs are not shared between rows
    answer_ids = re.findall(r'id="answer-([^"]+)"', later_section)
    assert len(answer_ids) == len(set(answer_ids))


def test_later_tickets_panel_absent_when_no_later_tickets(tickets_client):
    html = tickets_client.get("/tickets").text
    assert re.search(r'<section[^>]*\bid="later"', html, re.S) is None


def test_later_tickets_respects_milestone_filter(db_path, later_client):
    from runner.metrics import open_db

    conn = open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        m4 = metrics.upsert_milestone(conn, project, "m4")
        metrics.upsert_ticket(
            conn,
            project,
            "m4-99-later",
            milestone_id=m4,
            kind="developer",
            state="later",
            difficulty=2,
            title="An m4 set-aside ticket.",
        )
    finally:
        conn.close()

    html = later_client.get("/tickets?milestone=m4").text
    later_section = section_raw(html, "later")
    assert "m4-99-later" in later_section
    assert "f1-99-later" not in later_section


def test_later_tickets_ignore_the_state_filter(later_client):
    html = later_client.get("/tickets?state=done").text
    later_section = section_raw(html, "later")
    assert "f1-99-later" in later_section


def test_non_later_state_filter_does_not_leak_to_later_section(db_path, tickets_client):
    from runner.metrics import open_db

    conn = open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        metrics.upsert_ticket(
            conn,
            project,
            "f1-99-later",
            milestone_id=f1,
            kind="developer",
            state="later",
            difficulty=3,
            title="A set-aside ticket.",
        )
    finally:
        conn.close()

    resp = tickets_client.get("/tickets?state=escalated")
    html = resp.text
    later_section = section_raw(html, "later")
    assert "f1-12-escalated" not in later_section


def later_priority_rows(html: str) -> list[tuple[str, str]]:
    """Each later ticket's id and priority cell, in page order."""
    later_section = section_raw(html, "later")
    tickets = re.findall(r'<tr[^>]*\bdata-ticket="([^"]+)"', later_section)
    return [(ticket, later_row(later_section, ticket)["priority"]) for ticket in tickets]


def test_later_tickets_sorted_by_priority_then_id(later_priority_client):
    html = later_priority_client.get("/tickets").text
    rows = later_priority_rows(html)
    tickets = [r[0] for r in rows]
    priorities = [int(r[1]) for r in rows]
    # f1-95-low-priority has priority 5 (goes first)
    assert tickets[0] == "f1-95-low-priority"
    assert priorities[0] == 5
    # f1-98-milestone has priority 10 (milestone's priority)
    assert tickets[1] == "f1-98-milestone"
    assert priorities[1] == 10
    # f1-97-bug has priority 50 (bug default)
    assert tickets[2] == "f1-97-bug"
    assert priorities[2] == 50
    # f1-99-later has priority 100 (default)
    assert tickets[3] == "f1-99-later"
    assert priorities[3] == 100


def test_ticket_with_priority_5_lists_before_earlier_id_no_priority(later_priority_client):
    html = later_priority_client.get("/tickets").text
    rows = later_priority_rows(html)
    tickets = [r[0] for r in rows]
    # f1-95-low-priority (id 95) has priority 5 and comes before f1-99-later (id 99, no priority)
    assert tickets.index("f1-95-low-priority") < tickets.index("f1-99-later")


def test_bug_ticket_without_priority_shows_50(later_priority_client):
    html = later_priority_client.get("/tickets").text
    assert dict(later_priority_rows(html))["f1-97-bug"] == "50"


def test_milestone_ticket_without_priority_shows_milestone_priority(later_priority_client):
    html = later_priority_client.get("/tickets").text
    assert dict(later_priority_rows(html))["f1-98-milestone"] == "10"


def test_parse_ticket_body_extracts_goal_done_when_context():
    from factory_dashboard.tickets import Paragraph, parse_ticket_body

    body = (
        "---\nid: f1-01\npriority: 50\n---\n\n"
        "### Goal\nA goal paragraph.\n\n"
        "### Context\nThe lead's notes.\n\n"
        "### Done when\n- item one\n- item two\n"
    )
    parsed = parse_ticket_body(body)
    assert parsed.goal == [Paragraph(text="A goal paragraph.")]
    assert parsed.context == [Paragraph(text="The lead's notes.")]
    assert parsed.done_when == ["item one", "item two"]


def test_parse_ticket_body_without_front_matter():
    from factory_dashboard.tickets import Paragraph, parse_ticket_body

    body = "### Goal\nA goal.\n\n### Done when\n- done\n"
    parsed = parse_ticket_body(body)
    assert parsed.goal == [Paragraph(text="A goal.")]
    assert parsed.done_when == ["done"]


def test_parse_ticket_body_without_known_headings():
    from factory_dashboard.tickets import Paragraph, parse_ticket_body

    body = "### Context\nJust context.\n"
    parsed = parse_ticket_body(body)
    assert parsed.goal is None
    assert parsed.done_when is None
    assert parsed.context == [Paragraph(text="Just context.")]


def test_context_with_intro_bullets_and_paragraph_becomes_three_blocks():
    """Context of "Intro line.\n- first\n- second\n\nLast paragraph."
    shows as a paragraph, a list of two items and a paragraph."""
    from factory_dashboard.tickets import ListBlock, Paragraph, parse_ticket_body

    body = (
        "### Goal\nA goal.\n\n"
        "### Context\nIntro line.\n- first\n- second\n\nLast paragraph.\n\n"
        "### Done when\n- done\n"
    )
    parsed = parse_ticket_body(body)
    assert parsed.context == [
        Paragraph(text="Intro line."),
        ListBlock(items=["first", "second"]),
        Paragraph(text="Last paragraph."),
    ]


def test_goal_with_two_paragraphs_shows_as_two_blocks():
    """A Goal of two paragraphs shows as two paragraph blocks."""
    from factory_dashboard.tickets import Paragraph, parse_ticket_body

    body = "### Goal\nFirst paragraph.\n\nSecond paragraph.\n\n### Done when\n- done\n"
    parsed = parse_ticket_body(body)
    assert parsed.goal == [
        Paragraph(text="First paragraph."),
        Paragraph(text="Second paragraph."),
    ]


def test_bullet_wrapped_over_two_lines_is_one_list_item():
    """A bullet wrapped over two lines is one list item holding both lines."""
    from factory_dashboard.tickets import ListBlock, parse_ticket_body

    body = (
        "### Goal\nA goal.\n\n"
        "### Context\n- a bullet that wraps\n  over two lines\n\n"
        "### Done when\n- done\n"
    )
    parsed = parse_ticket_body(body)
    assert parsed.context == [
        ListBlock(items=["a bullet that wraps over two lines"]),
    ]


def test_a_later_ticket_page_shows_set_aside_panel(later_client):
    """D2: a ticket in state `later` starts with a Set aside panel and a Queue it button."""
    html = later_client.get("/tickets/f1-99-later").text
    assert re.search(r'<section[^>]*\bid="aside"', html, re.S)
    assert "This ticket won't run until you queue it." in html
    assert re.search(r'<button[^>]*class="[^"]*go[^"]*"[^>]*>Queue it</button>', html, re.S)


def test_the_queue_it_button_targets_a_place_on_the_page(later_client):
    """htmx sends nothing when hx-target matches no element (review f159 F1)."""
    html = later_client.get("/tickets/f1-99-later").text
    button = re.search(r'<button[^>]*id="queue"[^>]*>', html, re.S)
    assert button
    target = re.search(r'hx-target="#([^"]+)"', button.group(0))
    assert target
    assert f'id="{target.group(1)}"' in html
    assert "classList.add('sent')" in button.group(0)  # on its way at once, as the mock-up


def test_a_later_ticket_page_state_pill_says_set_aside(later_client):
    """`later` reads "set aside" in the Result section's State pill."""
    html = later_client.get("/tickets/f1-99-later").text
    result = section(html, "result")
    assert "set aside" in result


def test_a_set_aside_ticket_page_shows_parsed_body_as_text(db_path, later_client):
    """D3: Goal as a paragraph, Done when as a list, Context folded; no front-matter line."""
    from runner import metrics

    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        metrics.upsert_ticket(
            conn,
            project,
            "f1-96-parsed",
            milestone_id=f1,
            kind="developer",
            state="later",
            difficulty=2,
            title="Parsed body ticket.",
            body=(
                "---\nid: f1-96-parsed\n---\n\n"
                "### Goal\nA parsed goal.\n\n"
                "### Done when\n- item one\n- item two\n"
            ),
        )
    finally:
        conn.close()

    html = later_client.get("/tickets/f1-96-parsed").text
    # Check the goal section exists and has parsed content
    goal_section = section_raw(html, "goal")
    assert "A parsed goal." in goal_section
    assert "item one" in goal_section
    assert "item two" in goal_section
    # No front matter
    assert "id: f1-96-parsed" not in goal_section
    assert "---" not in goal_section
    # Should use readable panel (parsed body), not raw pre
    assert "<ul>" in goal_section
    assert "<li>" in goal_section


def test_done_when_with_wrapped_bullet_shows_full_text_on_page(db_path, later_client):
    """A bullet in "Done when" that wraps over two lines shows the full text on the ticket page."""
    from runner import metrics

    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        metrics.upsert_ticket(
            conn,
            project,
            "f1-93-wrap",
            milestone_id=f1,
            kind="developer",
            state="later",
            difficulty=2,
            title="Wrapped bullet ticket.",
            body=(
                "---\nid: f1-93-wrap\n---\n\n"
                "### Goal\nA goal.\n\n"
                "### Done when\n- a bullet that wraps\n  over two lines\n- second\n"
            ),
        )
    finally:
        conn.close()

    html = later_client.get("/tickets/f1-93-wrap").text
    goal_section = section_raw(html, "goal")
    assert "a bullet that wraps over two lines" in goal_section
    assert "second" in goal_section


def test_a_non_later_ticket_has_no_set_aside_panel(tickets_client):
    """A ticket in any other state has no set-aside panel."""
    html = tickets_client.get("/tickets/f1-10-ticket-a").text
    assert re.search(r'<section[^>]*\bid="aside"', html, re.S) is None


def test_a_ticket_with_parsed_body_folds_context(db_path, later_client):
    """Context shows inside a closed <details> element."""
    from runner import metrics

    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        metrics.upsert_ticket(
            conn,
            project,
            "f1-95-context",
            milestone_id=f1,
            kind="developer",
            state="later",
            difficulty=2,
            title="Context ticket.",
            body=(
                "---\nid: f1-95-context\n---\n\n"
                "### Goal\nA goal.\n\n"
                "### Context\nThe lead's notes for the agent.\n\n"
                "### Done when\n- done\n"
            ),
        )
    finally:
        conn.close()

    html = later_client.get("/tickets/f1-95-context").text
    goal_section = section_raw(html, "goal")
    assert "<details>" in goal_section
    assert "<summary>" in goal_section
    assert "The lead&#39;s notes for the agent." in goal_section


def test_later_ticket_page_on_its_way_message(db_path, later_client):
    """With an open queue request for the ticket, the panel shows on its way and no button."""
    from runner import metrics

    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        metrics.upsert_ticket(
            conn,
            project,
            "f1-94-later",
            milestone_id=f1,
            kind="developer",
            state="later",
            difficulty=2,
            title="On its way ticket.",
        )
        # Add an open queue request for this ticket
        from tests.factory_dashboard.conftest import _at

        metrics.add_request(conn, project, "queue", "f1-94-later", "", _at(timedelta(minutes=5)))
    finally:
        conn.close()

    html = later_client.get("/tickets/f1-94-later").text
    # The panel should be marked as "sent"
    aside_match = re.search(r'<section[^>]*\bid="aside"[^>]*class="([^"]*)"', html, re.S)
    assert aside_match, "no aside section"
    assert "sent" in aside_match.group(1)
    # No Queue it button
    assert re.search(r'<button[^>]*class="go"', html, re.S) is None
    # On its way message
    assert "on its way" in html.lower()
