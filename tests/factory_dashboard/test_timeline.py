"""Tests for the Timeline page (f1-11)."""

import json
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from factory_dashboard.app import create_app, get_now
from factory_dashboard.queries import local
from runner import metrics
from runner.metrics import open_db
from tests.factory_dashboard.conftest import (
    LOCAL,
    NOW,
    OPUS,
    PROJECT,
    SONNET,
    _at,
    write_f1_run,
    write_live,
)


def _add_f2_jobs(conn: sqlite3.Connection) -> None:
    """Add f2 milestone with 2 jobs on top of write_fixture."""
    from runner import metrics as runner_metrics

    project = runner_metrics.upsert_project(conn, PROJECT)
    f2 = runner_metrics.upsert_milestone(
        conn, project, "f2", title="The factory reviews itself", started=NOW.isoformat()
    )
    f2_run = runner_metrics.upsert_run(conn, project, "20261002-120000", command="milestone f2")
    ticket = runner_metrics.upsert_ticket(
        conn, project, "f2-01-test", milestone_id=f2, kind="developer", state="done"
    )
    job1 = runner_metrics.start_job(
        conn,
        f2_run,
        ticket_id=ticket,
        milestone_id=f2,
        role="developer",
        agent=LOCAL,
        attempt=1,
        started="2026-10-02T12:00:00+02:00",
    )
    runner_metrics.finish_job(
        conn,
        job1,
        ended="2026-10-02T12:10:00+02:00",
        outcome="passed",
        tokens_in=10_000,
        tokens_out=1_000,
    )
    ticket2 = runner_metrics.upsert_ticket(
        conn, project, "f2-02-test", milestone_id=f2, kind="developer", state="done"
    )
    job2 = runner_metrics.start_job(
        conn,
        f2_run,
        ticket_id=ticket2,
        milestone_id=f2,
        role="developer",
        agent=SONNET,
        attempt=1,
        started="2026-10-02T12:10:00+02:00",
    )
    runner_metrics.finish_job(
        conn,
        job2,
        ended="2026-10-02T12:15:00+02:00",
        outcome="passed",
        tokens_in=10_000,
        tokens_out=1_000,
    )


def write_recent_m1_jobs(conn: sqlite3.Connection) -> int:
    """An m1 milestone within the last 24 hours with a job, for the timeline milestone filter."""
    project = metrics.upsert_project(conn, PROJECT)
    m1 = metrics.upsert_milestone(
        conn, project, "m1", title="Milestone one", started=_at(timedelta(hours=12))
    )
    m1_run = metrics.upsert_run(conn, project, "20261002-000000")
    ticket = metrics.upsert_ticket(
        conn, project, "m1-01-test", milestone_id=m1, kind="developer", state="done"
    )
    job = metrics.start_job(
        conn,
        m1_run,
        ticket_id=ticket,
        milestone_id=m1,
        role="developer",
        agent=LOCAL,
        attempt=1,
        started=(NOW - timedelta(hours=11)).isoformat(),
    )
    metrics.finish_job(
        conn,
        job,
        ended=(NOW - timedelta(hours=10)).isoformat(),
        outcome="passed",
        tokens_in=10_000,
        tokens_out=1_000,
    )
    return m1


def charts(html: str) -> dict[str, Any]:
    """Each chart's kind and its JSON data block (f1 D5)."""
    found = re.findall(
        r'<div[^>]*data-chart="([a-z-]+)"[^>]*></div>\s*'
        r'<script type="application/json">(.*?)</script>',
        html,
        re.S,
    )
    return {kind: json.loads(data) for kind, data in found}


def section(html: str, name: str) -> str:
    """The text of the page's ``<section id="name">``, tags stripped."""
    match = re.search(rf'<section[^>]*\bid="{name}"[^>]*>(.*?)</section>', html, re.S)
    assert match, f"no section {name}"
    return " ".join(re.sub(r"<[^>]+>", " ", match.group(1)).split())


def test_timeline_page_returns_200(client):
    resp = client.get("/timeline")
    assert resp.status_code == 200


def test_the_jobs_table_prints_local_times(paris, client):
    """F187 D3: the table prints a time as it stands; the chart's own data stays stored UTC."""
    html = client.get("/timeline").text
    bars = [bar for lane in charts(html)["timeline"]["lanes"] for bar in lane["bars"]]
    table = re.search(r'<section id="jobs".*?</section>', html, re.S)
    assert table and bars
    for bar in bars:
        assert f"<td>{local(bar['start']).isoformat()}</td>" in table[0]
        assert f"<td>{local(bar['end']).isoformat()}</td>" in table[0]
    assert "+00:00</td>" not in table[0]


def test_json_block_has_one_lane_per_agent_and_one_bar_per_job(client):
    html = client.get("/timeline").text
    data = charts(html)
    assert "timeline" in data
    lanes = data["timeline"]["lanes"]
    # Only LOCAL and OPUS have jobs within the last 24 hours
    assert len(lanes) == 2
    agents = {lane["agent"] for lane in lanes}
    assert agents == {LOCAL, OPUS}
    # Total bars: 2 from write_f1_run + 1 running from write_live + 1 from other project
    total_bars = sum(len(lane["bars"]) for lane in lanes)
    assert total_bars == 4
    # Each bar has the required fields
    for lane in lanes:
        for bar in lane["bars"]:
            assert "ticket" in bar
            assert "role" in bar
            assert "outcome" in bar
            assert "start" in bar
            assert "end" in bar
            assert "project" in bar


def test_running_job_bar_ends_at_render_time(client):
    html = client.get("/timeline").text
    data = charts(html)
    # Find the running job (only within last 24 hours)
    found = False
    for lane in data["timeline"]["lanes"]:
        for bar in lane["bars"]:
            if bar["outcome"] == "running":
                end = datetime.fromisoformat(bar["end"])
                assert end == NOW
                found = True
    assert found, "No running bar found"


def test_refusal_marker_appears_on_agent_lane(client):
    html = client.get("/timeline").text
    data = charts(html)
    opus_lanes = [lane for lane in data["timeline"]["lanes"] if lane["agent"] == OPUS]
    assert len(opus_lanes) == 1
    markers = opus_lanes[0]["markers"]
    assert len(markers) == 1
    assert markers[0]["at"] == "2026-09-30T10:30:00+02:00"


def test_milestone_filter_shows_only_that_milestones_jobs(client_with_m1):
    html = client_with_m1.get("/timeline?milestone=m1").text
    data = charts(html)
    total_bars = sum(len(lane["bars"]) for lane in data["timeline"]["lanes"])
    assert total_bars == 1
    for lane in data["timeline"]["lanes"]:
        for bar in lane["bars"]:
            assert bar["ticket"] == "m1-01-test"


def test_empty_milestone_returns_all_milestones(client_with_m1):
    """?milestone= (empty) shows jobs from the last 24 hours across all milestones."""
    html = client_with_m1.get("/timeline?milestone=").text
    data = charts(html)
    total_bars = sum(len(lane["bars"]) for lane in data["timeline"]["lanes"])
    assert total_bars == 1
    tickets = {bar["ticket"] for lane in data["timeline"]["lanes"] for bar in lane["bars"]}
    assert "m1-01-test" in tickets


def test_milestone_filter_with_f2(client_with_f2):
    """?milestone=f2 returns only f2's jobs."""
    html = client_with_f2.get("/timeline?milestone=f2").text
    data = charts(html)
    total_bars = sum(len(lane["bars"]) for lane in data["timeline"]["lanes"])
    assert total_bars == 2
    tickets = {bar["ticket"] for lane in data["timeline"]["lanes"] for bar in lane["bars"]}
    assert tickets == {"f2-01-test", "f2-02-test"}


def test_form_preserves_project(client):
    """The milestone filter form keeps the project parameter on submit."""
    html = client.get("/timeline").text
    # Find the milestone filter form by its id=filters section
    section_match = re.search(r'<section[^>]*id="filters"[^>]*>(.*?)</section>', html, re.S)
    assert section_match, "filters section not found"
    section_html = section_match.group(1)
    form_match = re.search(r"<form[^>]*>(.*?)</form>", section_html, re.S)
    assert form_match, "form not found in filters section"
    form_html = form_match.group(1)
    assert 'name="project"' in form_html
    assert PROJECT in form_html


def test_timeline_has_filter_form_and_jobs_table(client):
    html = client.get("/timeline").text
    assert "Filters" in section(html, "filters")
    assert "Jobs" in section(html, "jobs")


def test_timeline_bar_has_job_id(client):
    """Each timeline bar carries a job_id so clicking it opens /jobs/{n}."""
    html = client.get("/timeline").text
    data = charts(html)
    for lane in data["timeline"]["lanes"]:
        for bar in lane["bars"]:
            assert "job_id" in bar
            assert isinstance(bar["job_id"], int)


def test_timeline_milestone_select_shows_filter(client):
    """The milestone select shows 'All milestones' when no filter is applied."""
    html = client.get("/timeline").text
    # Read the select's raw HTML to find the selected option.
    select_match = re.search(r'<select[^>]*name="milestone"[^>]*>(.*?)</select>', html, re.S)
    assert select_match, "milestone select not found"
    select_html = select_match.group(1)
    # Find the option with the 'selected' attribute.
    selected_match = re.search(r"<option[^>]*\bselected\b[^>]*>(.*?)</option>", select_html, re.S)
    assert selected_match, "no selected option in milestone select"
    selected_text = re.sub(r"<[^>]+>", " ", selected_match.group(1)).strip()
    assert selected_text == "All milestones"


def test_timeline_milestone_select_non_default(client_with_m1):
    """The milestone select shows the selected milestone
    when filtering, and 'All milestones' is available."""
    html = client_with_m1.get("/timeline?milestone=m1").text
    select_match = re.search(r'<select[^>]*name="milestone"[^>]*>(.*?)</select>', html, re.S)
    assert select_match, "milestone select not found"
    select_html = select_match.group(1)
    selected_match = re.search(r"<option[^>]*\bselected\b[^>]*>(.*?)</option>", select_html, re.S)
    assert selected_match, "no selected option in milestone select"
    selected_text = re.sub(r"<[^>]+>", " ", selected_match.group(1)).strip()
    assert selected_text == "M1"
    assert "All milestones" in select_html


def test_timeline_run_filter(client):
    """?run= shows only that run's jobs."""
    html = client.get("/timeline?run=20261001-100000").text
    data = charts(html)
    total_bars = sum(len(lane["bars"]) for lane in data["timeline"]["lanes"])
    # The run 20261001-100000 has 2 jobs in F1; only those bars should appear.
    assert total_bars == 2


def test_timeline_run_filter_no_jobs_in_milestone(timeline_run_no_jobs_client):
    """A run filter without the 24 h window shows that run's jobs."""
    html = timeline_run_no_jobs_client.get("/timeline?run=20260922-100000").text
    data = charts(html)
    total_bars = sum(len(lane["bars"]) for lane in data["timeline"]["lanes"])
    assert total_bars == 1


def test_timeline_shows_every_projects_bars(two_project_client):
    """The timeline shows bars from every project, not just the picked one."""
    html = two_project_client.get("/timeline").text
    data = charts(html)
    projects = {bar["project"] for lane in data["timeline"]["lanes"] for bar in lane["bars"]}
    assert PROJECT in projects
    assert "travel-companion" in projects


def test_milestone_filter_shows_only_that_milestones_bars(two_project_with_m1_client):
    """?milestone= of a travel-companion milestone shows its bars only."""
    html = two_project_with_m1_client.get("/timeline?milestone=tc-m1").text
    data = charts(html)
    total_bars = sum(len(lane["bars"]) for lane in data["timeline"]["lanes"])
    assert total_bars == 1
    tickets = {bar["ticket"] for lane in data["timeline"]["lanes"] for bar in lane["bars"]}
    assert tickets == {"m1-01-test"}


def test_each_bars_link_carries_its_project(two_project_client):
    """Each bar's link opens its job with its own project."""
    html = two_project_client.get("/timeline").text
    data = charts(html)["timeline"]
    # Verify each bar in JSON has a project, and the HTML renders the href correctly
    for lane in data["lanes"]:
        for bar in lane["bars"]:
            assert "project" in bar
            assert bar["project"]
            # The href in HTML should contain the job_id and project
            expected = f"/jobs/{bar['job_id']}?project={bar['project']}"
            assert expected in html, f"Expected {expected!r} in HTML but not found"


@pytest.fixture
def two_project_client(db_path: Path) -> TestClient:
    """A client with jobs from both coucou and travel-companion in the last 24 hours."""
    conn = open_db(db_path)
    try:
        write_live(conn, timedelta(seconds=30))
        write_f1_run(conn)
        # Add a project "travel-companion" with a job within 24 hours
        tc_project = metrics.upsert_project(conn, "travel-companion")
        tc_m1 = metrics.upsert_milestone(
            conn,
            tc_project,
            "m1",
            title="Travel companion milestone",
            started=(NOW - timedelta(hours=12)).isoformat(),
        )
        tc_run = metrics.upsert_run(
            conn,
            tc_project,
            (NOW - timedelta(hours=6)).strftime("%Y%m%d-%H%M%S"),
        )
        tc_ticket = metrics.upsert_ticket(
            conn,
            tc_project,
            "tc-01-test",
            milestone_id=tc_m1,
            kind="developer",
            state="done",
        )
        tc_job = metrics.start_job(
            conn,
            tc_run,
            ticket_id=tc_ticket,
            milestone_id=tc_m1,
            role="developer",
            agent=OPUS,
            attempt=1,
            started=(NOW - timedelta(hours=5)).isoformat(),
        )
        metrics.finish_job(
            conn,
            tc_job,
            ended=(NOW - timedelta(hours=4)).isoformat(),
            outcome="passed",
            tokens_in=10_000,
            tokens_out=1_000,
        )
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


@pytest.fixture
def two_project_with_m1_client(db_path: Path) -> TestClient:
    """A client with jobs from both projects plus an m1 milestone in travel-companion."""
    conn = open_db(db_path)
    try:
        write_live(conn, timedelta(seconds=30))
        write_f1_run(conn)
        # travel-companion with an m1 milestone
        tc_project = metrics.upsert_project(conn, "travel-companion")
        tc_m1 = metrics.upsert_milestone(
            conn,
            tc_project,
            "tc-m1",
            title="Travel companion milestone",
            started=(NOW - timedelta(hours=12)).isoformat(),
        )
        tc_run = metrics.upsert_run(
            conn,
            tc_project,
            (NOW - timedelta(hours=6)).strftime("%Y%m%d-%H%M%S"),
        )
        tc_ticket = metrics.upsert_ticket(
            conn,
            tc_project,
            "m1-01-test",
            milestone_id=tc_m1,
            kind="developer",
            state="done",
        )
        tc_job = metrics.start_job(
            conn,
            tc_run,
            ticket_id=tc_ticket,
            milestone_id=tc_m1,
            role="developer",
            agent=OPUS,
            attempt=1,
            started=(NOW - timedelta(hours=5)).isoformat(),
        )
        metrics.finish_job(
            conn,
            tc_job,
            ended=(NOW - timedelta(hours=4)).isoformat(),
            outcome="passed",
            tokens_in=10_000,
            tokens_out=1_000,
        )
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


@pytest.fixture
def client(db_path: Path) -> TestClient:
    """Timeline client: fixture + write_live + write_f1_run (second run with F1 jobs)."""
    from factory_dashboard.app import create_app, get_now

    conn = metrics.open_db(db_path)
    try:
        write_live(conn, timedelta(seconds=30))
        write_f1_run(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


@pytest.fixture
def client_with_m1(db_path: Path) -> TestClient:
    """A client over the fixture plus a recent m1 milestone with jobs."""
    conn = open_db(db_path)
    try:
        write_recent_m1_jobs(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


@pytest.fixture
def client_with_f2(db_path: Path) -> TestClient:
    """A client over the fixture plus f2 milestone with jobs."""
    conn = open_db(db_path)
    try:
        _add_f2_jobs(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")
