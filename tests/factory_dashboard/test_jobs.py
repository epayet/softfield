"""Tests for the jobs page (f1-08) and the job detail page (f1-09)."""

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from runner.metrics import open_db
from tests.factory_dashboard.conftest import (
    NOW,
    PROJECT,
    write_jobs,
    write_more_jobs,
    write_review_job,
)


def section(html: str, name: str) -> str:
    """The text of the page's ``<section id="name">``, tags stripped."""
    match = re.search(rf'<section[^>]*\bid="{name}"[^>]*>(.*?)</section>', html, re.S)
    assert match, f"no section {name}"
    return " ".join(re.sub(r"<[^>]+>", " ", match.group(1)).split())


@pytest.fixture
def client_with_jobs(db_path: Path):
    """A client over the fixture plus jobs with gates.
    Returns (client, failed_job_id, escalation_job_id)."""
    from factory_dashboard.app import create_app, get_now
    from runner.metrics import open_db

    conn = open_db(db_path)
    try:
        write_jobs(conn)
        # The direction/failed job is the one with role="direction" and outcome="failed"
        failed_row = conn.execute(
            "SELECT id FROM jobs WHERE role = 'direction' AND outcome = 'failed' LIMIT 1"
        ).fetchone()
        failed_id = failed_row["id"] if failed_row else 0
        # The escalation job is the one with role="escalation" and outcome="passed"
        esc_row = conn.execute(
            "SELECT id FROM jobs WHERE role = 'escalation' AND outcome = 'passed' LIMIT 1"
        ).fetchone()
        esc_id = esc_row["id"] if esc_row else 0
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    client = TestClient(app, base_url="http://127.0.0.1:8765")
    return client, failed_id, esc_id


def test_no_filter_shows_all_jobs_newest_first(client_with_jobs):
    client, _, _ = client_with_jobs
    html = client.get("/jobs").text
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    tbody_rows = [r for r in rows if "<td" in r]
    assert len(tbody_rows) == 12
    expected_order = [12, 6, 4, 11, 9, 8, 7, 5, 3, 2, 1, 10]
    for i, job_id in enumerate(expected_order):
        row = tbody_rows[i]
        link_match = re.search(r'href="/jobs/(\d+)"', row)
        assert link_match, f"row {i} has no job link"
        assert int(link_match.group(1)) == job_id


def test_filter_by_agent_and_role_shows_only_matching(client_with_jobs):
    client, _, _ = client_with_jobs
    resp = client.get("/jobs?agent=claude-opus&role=escalation")
    html = resp.text
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    tbody_rows = [r for r in rows if "<td" in r]
    assert len(tbody_rows) == 1
    row = tbody_rows[0]
    assert "escalation" in row
    assert "claude-opus" in row
    assert "/jobs/6" in row
    for job_id in (1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12):
        assert f"/jobs/{job_id}" not in row


def test_unknown_filter_value_shows_no_jobs_and_keeps_form(client_with_jobs):
    client, _, _ = client_with_jobs
    resp = client.get("/jobs?agent=nonexistent-agent&role=nonexistent-role")
    html = resp.text
    jobs_section = section(html, "jobs")
    assert "No jobs match" in jobs_section
    # The form keeps the values
    assert "nonexistent-agent" in html
    assert "nonexistent-role" in html


def test_failed_attempt_shows_failed_gate_name(client_with_jobs):
    client, _, _ = client_with_jobs
    html = client.get("/jobs").text
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    tbody_rows = [r for r in rows if "thead" not in r.lower()]
    for row in tbody_rows:
        link_match = re.search(r'href="/jobs/(\d+)"', row)
        if link_match:
            job_id = int(link_match.group(1))
            if job_id == 4:
                cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
                text = " ".join(re.sub(r"<[^>]+>", " ", c).strip() for c in cells)
                assert "tests" in text
            else:
                cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
                text = " ".join(re.sub(r"<[^>]+>", " ", c).strip() for c in cells)
                assert text.strip().endswith("–")


def test_running_job_shows_running_outcome(client_with_jobs):
    client, _, _ = client_with_jobs
    html = client.get("/jobs").text
    jobs_section = section(html, "jobs")
    assert "running" in jobs_section


@pytest.fixture
def client_with_overflow(db_path: Path) -> TestClient:
    """A client over the fixture plus 205 extra jobs."""
    from factory_dashboard.app import create_app, get_now

    conn = open_db(db_path)
    try:
        write_jobs(conn)
        write_more_jobs(conn, 205)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


def test_more_than_200_jobs_shows_200_and_count(client_with_overflow):
    html = client_with_overflow.get("/jobs").text
    assert "200 of 217" in html
    assert "17 more" in html


@pytest.fixture
def client_with_review(db_path: Path):
    """A client over the fixture plus a review job with findings.
    Returns (client, review_job_id)."""
    from factory_dashboard.app import create_app, get_now

    conn = open_db(db_path)
    try:
        review_id = write_review_job(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    client = TestClient(app, base_url="http://127.0.0.1:8765")
    return client, review_id


def test_failed_attempt_shows_gates_and_peak_context(client_with_jobs):
    client, failed_id, _ = client_with_jobs
    html = client.get(f"/jobs/{failed_id}").text
    gates = section(html, "gates")
    assert "lint" in gates
    assert "tests" in gates
    assert "pass" in gates
    assert "fail" in gates
    context = section(html, "time")
    assert "166k of 184k" in context


def test_claude_escalation_shows_dollars_and_note(client_with_jobs):
    client, _, esc_id = client_with_jobs
    html = client.get(f"/jobs/{esc_id}").text
    time_section = section(html, "time")
    assert "$1.00" in time_section
    note_section = section(html, "note")
    assert "Escalation note" in note_section


def test_review_job_lists_findings_with_severity(client_with_review):
    client, review_id = client_with_review
    html = client.get(f"/jobs/{review_id}").text
    findings = section(html, "findings")
    assert "RV-1" in findings
    assert "RV-2" in findings
    assert "blocking" in findings
    assert "should-fix" in findings


def test_unknown_job_id_returns_404(client_with_jobs):
    client, _, _ = client_with_jobs
    resp = client.get("/jobs/999999")
    assert resp.status_code == 404
