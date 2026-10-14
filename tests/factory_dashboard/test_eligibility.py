"""The Agents page's eligibility panel (f1-31, f2-11): who earned a role from review replays
(`runner bench --review`), and why not."""

from tests.factory_dashboard.conftest import OTHER_REVIEWER, REVIEWER


def _panel(html: str) -> str:
    start = html.index('id="eligibility"')
    return html[start : html.index("</section>", start)]


def _row(panel: str, agent: str) -> str:
    start = panel.index(agent)
    return panel[start : panel.index("</tr>", start)]


def test_an_agent_is_eligible_from_review_replays_alone(review_client):
    page = review_client.get("/agents")
    assert page.status_code == 200
    panel = _panel(page.text)
    assert "Review replays" in panel and "Shadow" not in panel
    row = _row(panel, OTHER_REVIEWER)
    assert "checkpoint" in row
    assert "eligible" in row
    assert "replayed" not in row


def test_an_agent_missing_bars_shows_the_reasons_and_its_replays(review_client):
    row = _row(_panel(review_client.get("/agents").text), REVIEWER)
    assert "rated 6, needs 8" in row
    assert "replayed checkpoints of 1 milestone, needs 2" in row
    assert ">1<" in row  # its refused replay doesn't count


def test_the_eligible_agent_counts_its_replays(review_client):
    row = _row(_panel(review_client.get("/agents").text), OTHER_REVIEWER)
    assert ">2<" in row


def test_an_agent_that_never_replayed_a_checkpoint_is_not_listed(review_client):
    panel = _panel(review_client.get("/agents").text)
    assert "local-qwen3.6-35b-a3b" not in panel


def test_without_review_replays_the_panel_says_so(client):
    panel = _panel(client.get("/agents").text)
    assert "No agent has replayed a checkpoint yet" in panel
    assert "softfield bench --review" in panel
