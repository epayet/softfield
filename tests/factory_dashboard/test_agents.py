"""Tests for the Agents page (/agents): efficiency, roles table, ratings."""

import json
import re
from pathlib import Path

from tests.factory_dashboard.conftest import LOCAL, OPUS, SONNET

CHARTS_JS = Path(__file__).parents[2] / "factory_dashboard" / "static" / "charts.js"


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


def test_efficiency_numbers_for_fixture_local_agent(serve):
    html = serve(live=False).get("/agents").text
    eff = section(html, "efficiency")
    assert LOCAL in eff
    assert "5" in eff  # jobs
    assert "2" in eff  # merged
    assert "3" in eff  # attempt tickets
    assert "67%" in eff  # first attempt pass rate
    assert "2.5" in eff  # attempts per merge
    assert "25.0" in eff  # minutes per merge
    assert "287500" in eff  # tokens per merge
    assert "192" in eff  # tokens per second
    assert "33%" in eff  # escalation rate
    assert "$0" in eff  # dollars
    assert "\u2013" in eff  # no failed gate


def test_agents_roles_table_has_cell_per_pair(client):
    html = client.get("/agents").text
    roles = section(html, "roles")
    assert LOCAL in roles
    assert OPUS in roles
    assert SONNET in roles
    assert "developer" in roles
    assert "checkpoint" in roles
    assert "review" in roles


def test_empty_state_when_no_ratings(serve):
    html = serve(live=False).get("/agents").text
    ratings = section(html, "ratings")
    assert "Ratings start after f1-24" in ratings
    assert "data-chart" not in ratings


def test_rating_chart_json_with_two_changes(rating_client):
    html = rating_client.get("/agents").text
    c = charts(html)
    assert "rating" in c
    data = c["rating"]
    assert len(data["labels"]) == 2  # type: ignore[index]
    assert len(data["agents"]) == 2  # type: ignore[index]
    assert len(data["skills"]) == 2  # type: ignore[index]
    assert len(data["scores"]) == 2  # type: ignore[index]
    assert data["agents"][0] == LOCAL  # type: ignore[index]
    assert data["skills"][0] == "coding"  # type: ignore[index]
    assert data["scores"][0] == 4.5  # type: ignore[index]


def test_claude_sonnet_shows_dashes_for_per_merge(serve):
    html = serve(live=False).get("/agents").text
    eff = section(html, "efficiency")
    assert SONNET in eff
    assert "1" in eff  # 1 job
    assert "\u2013" in eff  # per-merge dashes (merged=0)
