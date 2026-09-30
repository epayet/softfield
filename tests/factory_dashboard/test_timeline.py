"""Tests for the Timeline page (f1-11)."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from factory_dashboard.app import create_app, get_now
from runner.metrics import open_db
from tests.factory_dashboard.conftest import LOCAL, NOW, OPUS, PROJECT, SONNET, write_m1_jobs


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


def test_json_block_has_one_lane_per_agent_and_one_bar_per_job(client):
    html = client.get("/timeline").text
    data = charts(html)
    assert "timeline" in data
    lanes = data["timeline"]["lanes"]
    # 3 agents with jobs in f1
    assert len(lanes) == 3
    agents = {lane["agent"] for lane in lanes}
    assert agents == {LOCAL, OPUS, SONNET}
    # Total bars = 10 (9 from write_fixture + 1 running from write_live)
    total_bars = sum(len(lane["bars"]) for lane in lanes)
    assert total_bars == 10
    # Each bar has the required fields
    for lane in lanes:
        for bar in lane["bars"]:
            assert "ticket" in bar
            assert "role" in bar
            assert "outcome" in bar
            assert "start" in bar
            assert "end" in bar


def test_running_job_bar_ends_at_render_time(client):
    html = client.get("/timeline").text
    data = charts(html)
    # Find the running job
    for lane in data["timeline"]["lanes"]:
        for bar in lane["bars"]:
            if bar["outcome"] == "running":
                end = datetime.fromisoformat(bar["end"])
                assert end == NOW


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


def test_timeline_has_filter_form_and_jobs_table(client):
    html = client.get("/timeline").text
    assert "Filters" in section(html, "filters")
    assert "Jobs" in section(html, "jobs")


@pytest.fixture
def client_with_m1(db_path: Path) -> TestClient:
    """A client over the fixture plus an m1 milestone with jobs."""
    conn = open_db(db_path)
    try:
        write_m1_jobs(conn)
    finally:
        conn.close()

    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")
