"""The Agents page's eligibility panel (f1-31): who earned a role by shadowing, and why not."""

from tests.factory_dashboard.conftest import OTHER_SHADOW, SHADOW


def _panel(html: str) -> str:
    start = html.index('id="eligibility"')
    return html[start : html.index("</section>", start)]


def _row(panel: str, agent: str) -> str:
    start = panel.index(agent)
    return panel[start : panel.index("</tr>", start)]


def test_an_agent_meeting_every_bar_is_eligible(shadow_client):
    page = shadow_client.get("/agents")
    assert page.status_code == 200
    row = _row(_panel(page.text), OTHER_SHADOW)
    assert "checkpoint" in row
    assert "eligible" in row
    assert "shadowed" not in row


def test_an_agent_missing_bars_shows_the_reasons_and_its_shadow_jobs(shadow_client):
    row = _row(_panel(shadow_client.get("/agents").text), SHADOW)
    assert "rated 6, needs 8" in row
    assert "shadowed 1 milestone, needs 2" in row
    assert ">1<" in row


def test_the_eligible_agent_counts_its_shadow_jobs(shadow_client):
    row = _row(_panel(shadow_client.get("/agents").text), OTHER_SHADOW)
    assert ">2<" in row


def test_an_agent_that_never_shadowed_is_not_listed(shadow_client):
    panel = _panel(shadow_client.get("/agents").text)
    assert "local-qwen3.6-35b-a3b" not in panel


def test_without_shadows_the_panel_says_so(client):
    assert "No agent has shadowed a role yet." in _panel(client.get("/agents").text)
