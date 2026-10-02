"""Tests for the Agents page (/agents): efficiency, roles table, ratings."""

import json
import re
from pathlib import Path

from tests.factory_dashboard.conftest import LOCAL, OPUS, SONNET, SONNET_45, SONNET_46

CHARTS_JS = Path(__file__).parents[2] / "factory_dashboard" / "static" / "charts.js"


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
    # Read the local agent's row cell by cell (raw HTML)
    eff_raw = section_raw(html, "efficiency")
    local_row_match = re.search(rf"<tr>.*?{re.escape(LOCAL)}.*?</tr>", eff_raw, re.S)
    assert local_row_match, f"no row for {LOCAL}"
    local_row = local_row_match.group(0)
    # jobs=5
    assert '<td class="num">5</td>' in local_row
    # merged=2
    assert '<td class="num">2</td>' in local_row
    # attempt_tickets=3
    assert '<td class="num">3</td>' in local_row
    # first_attempt_pass=67%
    assert "67%" in local_row
    # attempts_per_merge=2.5
    assert '<td class="num">2.5</td>' in local_row
    # minutes_per_merge=25.0
    assert '<td class="num">25.0</td>' in local_row
    # tokens_per_merge=287500
    assert '<td class="num">287500</td>' in local_row
    # tokens_per_second=192
    assert '<td class="num">192</td>' in local_row
    # escalation_rate=33%
    assert "33%" in local_row
    # dollars=$0.00
    assert "$0.00" in local_row
    # most_failed_gate=–
    assert "\u2013" in local_row


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
    # Find the row containing SONNET (raw HTML)
    eff_raw = section_raw(html, "efficiency")
    sonnet_row_match = re.search(rf"<tr>.*?{re.escape(SONNET)}.*?</tr>", eff_raw, re.S)
    assert sonnet_row_match, f"no row for {SONNET}"
    sonnet_row = sonnet_row_match.group(0)
    # jobs=1
    assert '<td class="num">1</td>' in sonnet_row
    # merged=0, so per-merge values are dashes
    assert "\u2013" in sonnet_row


def test_milestone_filter_filters_every_query(serve):
    """``/agents?milestone=f1`` answers 200; m4-01-old drops from the local row."""
    resp = serve(live=False).get("/agents?milestone=f1")
    assert resp.status_code == 200
    html = resp.text
    eff = section(html, "efficiency")
    assert LOCAL in eff
    # Find the local agent's row (raw HTML)
    eff_raw = section_raw(html, "efficiency")
    local_row_match = re.search(rf"<tr>.*?{re.escape(LOCAL)}.*?</tr>", eff_raw, re.S)
    assert local_row_match, f"no row for {LOCAL}"
    local_row = local_row_match.group(0)
    # m4-01-old job drops out: jobs=4 (was 5), merged=1 (was 2)
    assert '<td class="num">4</td>' in local_row
    assert '<td class="num">1</td>' in local_row


def efficiency_rows(html: str) -> list[list[str]]:
    """The efficiency table's rows, each a list of its cells' text."""
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", section_raw(html, "efficiency"), re.S)
    cells = [re.findall(r"<td[^>]*>(.*?)</td>", row, re.S) for row in rows]
    return [[" ".join(re.sub(r"<[^>]+>|&nbsp;|↳", " ", c).split()) for c in r] for r in cells if r]


def test_a_ticket_merged_after_three_attempts_is_one_merge(serve, db_path):
    """f2 review: `merged` counted the jobs on merged tickets, so three attempts at one ticket
    read as three merges and 1.0 attempts per merge."""
    from runner import metrics
    from tests.factory_dashboard.conftest import PROJECT, _job

    client = serve(live=False)
    agent = "ollama-gpt-oss-120b"
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f2 = metrics.upsert_milestone(conn, project, "f2")
        run = metrics.upsert_run(conn, project, "20261002-120000", command="milestone f2")
        ticket = metrics.upsert_ticket(
            conn, project, "f2-06-x", milestone_id=f2, kind="developer", merged_by=agent
        )
        for attempt, outcome in ((1, "failed"), (2, "failed"), (3, "passed")):
            _job(conn, run, f2, ticket, "developer", agent, attempt, outcome)
    finally:
        conn.close()
    [row] = [r for r in efficiency_rows(client.get("/agents").text) if r[0] == agent]
    # jobs, merged, tickets attempted, first-attempt pass, attempts per merge
    assert row[1:6] == ["3", "1", "1", "0%", "3.0"]


def test_agent_on_two_models_gets_a_row_per_model(models_client):
    """f2-07: claude-sonnet's own row totals its 5 jobs, then one row per model; NULL and ''
    are one "not recorded" group."""
    rows = efficiency_rows(models_client.get("/agents").text)
    names = [r[0] for r in rows]
    at = names.index(SONNET)
    sonnet = {r[0]: (r[1], r[-1]) for r in rows[at : at + 4]}
    assert sonnet == {
        SONNET: ("5", "$1.80"),
        "not recorded": ("2", "$0.50"),
        SONNET_45: ("1", "$0.50"),
        SONNET_46: ("2", "$0.80"),
    }


def test_agent_on_one_model_gets_no_model_rows(models_client):
    """Only claude-sonnet's three model rows appear, none for the local agent or Opus."""
    eff = section_raw(models_client.get("/agents").text, "efficiency")
    assert eff.count('<tr class="model">') == 3


def test_default_fixture_has_no_model_rows(serve):
    eff = section_raw(serve(live=False).get("/agents").text, "efficiency")
    assert '<tr class="model">' not in eff


def test_rating_chart_has_one_series_per_agent(rating_client):
    """The rating chart has one series per agent, named by the agent."""
    html = rating_client.get("/agents").text
    c = charts(html)
    assert "rating" in c
    data = c["rating"]
    # Both points present
    assert len(data["scores"]) == 2  # type: ignore[index]
    # One series per agent (the JS draws one series per unique agent)
    unique_agents = len(set(data["agents"]))  # type: ignore[index]
    assert unique_agents == 1
    assert LOCAL in data["agents"]  # type: ignore[index]
