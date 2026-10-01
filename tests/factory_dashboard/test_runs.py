"""Tests for the runs list and run detail pages (f1-14, f1-40)."""

import re
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from runner import metrics
from runner.metrics import open_db
from tests.factory_dashboard.conftest import (
    NOW,
    PROJECT,
    write_fixture,
    write_runs,
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


@pytest.fixture
def runs_client(db_path: Path) -> TestClient:
    """A client over the fixture plus ``write_runs``'s rows."""
    from factory_dashboard.app import create_app, get_now

    conn = open_db(db_path)
    try:
        write_fixture(conn)
        write_runs(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


@pytest.fixture
def stopped_client(db_path: Path) -> TestClient:
    """A client with a run whose heartbeat is 3 min old (shows "stopped")."""
    from factory_dashboard.app import create_app, get_now

    conn = open_db(db_path)
    try:
        write_fixture(conn)
        # Stopped run with old heartbeat
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_run(
            conn,
            project,
            "20260920-stopped",
            command="backfill",
            heartbeat=(NOW - timedelta(minutes=3)).isoformat(),
        )
        write_runs(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


def test_runs_list_shows_newest_first_with_verdicts(runs_client):
    html = runs_client.get("/runs").text
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    tbody_rows = [r for r in rows if "<td" in r and "<th" not in r]
    # First row: running run (newest)
    first_row = tbody_rows[0]
    assert "20261002-113500" in first_row
    assert "–" in first_row  # no minutes for running run
    assert "running" in first_row  # status column
    # Second row: completed run
    second_row = tbody_rows[1]
    assert "20260930-100000" in second_row
    assert "3 merged, 0 not" in second_row
    assert "done" in second_row  # status column
    # Third row: stopped run
    third_row = tbody_rows[2]
    assert "20260920-100000" in third_row
    assert "–" in third_row  # no minutes
    assert "stopped" in third_row  # status column


def test_run_page_shows_jobs_and_tickets(runs_client):
    html = runs_client.get("/runs/20261002-113500").text
    info = section(html, "info")
    assert "milestone f1" in info
    assert "running" in info
    assert "stopped" not in info

    jobs_raw = section_raw(html, "jobs")
    job_links = re.findall(r'href="/jobs/(\d+)', jobs_raw)
    assert len(job_links) == 1

    tickets = section(html, "tickets")
    assert "f1-04-live" in tickets
    tickets_raw = section_raw(html, "tickets")
    ticket_links = re.findall(r'href="/tickets/([^"?]+)', tickets_raw)
    assert "f1-04-live" in ticket_links


def test_unknown_run_is_404(runs_client):
    resp = runs_client.get("/runs/f999-unknown")
    assert resp.status_code == 404


def test_a_run_with_fresh_heartbeat_shows_running(runs_client):
    html = runs_client.get("/runs/20261002-113500").text
    info = section(html, "info")
    assert "running" in info
    assert "stopped" not in info


def test_a_run_with_3_min_old_heartbeat_shows_stopped(stopped_client):
    html = stopped_client.get("/runs/20260920-stopped").text
    info = section(html, "info")
    assert "stopped" in info
    assert "running" not in info


def test_runs_list_checks_every_row(runs_client):
    html = runs_client.get("/runs").text
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    tbody_rows = [r for r in rows if "<td" in r and "<th" not in r]
    assert len(tbody_rows) >= 3
    # Check each row has run dir, minutes or dash, and verdict/status
    for i, row in enumerate(tbody_rows):
        assert "2026" in row, f"row {i} missing run dir"
        has_minutes = re.search(r'<td class="num">[\d.]+</td>', row)
        has_dash = "–" in row
        assert has_minutes or has_dash, f"row {i} missing minutes or dash"
        has_verdict = "merged" in row or "backfill" in row
        has_status = "running" in row or "stopped" in row or "done" in row
        assert has_verdict or has_status, f"row {i} missing verdict or status"
