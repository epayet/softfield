import json
import re
from datetime import timedelta
from pathlib import Path

from factory_dashboard.overview import claude_allowance
from tests.factory_dashboard.conftest import LOCAL, NOW, OTHER

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


def test_the_overview_shows_every_panel_in_order(client):
    html = client.get("/").text
    ids = re.findall(r'<section[^>]*\bid="([a-z-]+)"', html)
    assert ids == ["needs-you", "running", "queue", "verdict", "allowance", "savings", "spend"]


def test_needs_you_lists_open_owner_items_with_their_command(client):
    needs = section(client.get("/").text, "needs-you")
    assert "Should reactions be editable once sent?" in needs
    assert "uv run runner accept 15" in needs
    assert "Sign in to Ollama." not in needs  # resolved


def test_a_job_with_a_fresh_heartbeat_is_running_now(client):
    html = client.get("/").text
    running = section(html, "running")
    assert "f1-04-live" in running
    assert "attempt 2" in running and LOCAL in running and "developer" in running
    assert "12 min" in running  # elapsed
    assert "42k tokens in · 17 steps" in running
    assert "30 s ago" in running  # the heartbeat
    needs = section(html, "needs-you")
    assert "heartbeat" not in needs
    assert "idle" not in needs  # the runner is live, so the queue isn't waiting on it


def test_a_stale_heartbeat_is_a_needs_you_item_instead(serve):
    html = serve(heartbeat_age=timedelta(minutes=3)).get("/").text
    assert "f1-04-live" not in section(html, "running")
    needs = section(html, "needs-you")
    assert "heartbeat stopped 3 min ago" in needs and "f1-04-live" in needs
    assert "uv run runner milestone f1" in needs
    # with the runner gone, the queue waits on nobody
    assert "2 tickets waiting and the runner is idle" in needs


def test_the_live_partial_answers_on_its_own_for_htmx(client):
    response = client.get("/live?project=coucou")
    assert response.status_code == 200
    html = response.text
    assert "<html" not in html
    assert "Should reactions be editable" in section(html, "needs-you")
    assert "f1-04-live" in section(html, "running")
    # it asks to be fetched again every 5 s, keeping the project
    assert 'hx-get="/live?project=coucou"' in html
    assert 'hx-trigger="every 5s"' in html
    assert 'hx-get="/live?project=coucou"' in client.get("/").text
    assert client.get("/running").status_code == 404


def test_the_queue_item_goes_from_live_once_a_run_is_live(serve):
    stopped = serve(heartbeat_age=timedelta(minutes=3)).get("/live").text
    assert "runner is idle" in section(stopped, "needs-you")
    running = serve().get("/live").text
    assert "runner is idle" not in section(running, "needs-you")


def test_needs_you_is_absent_when_nothing_needs_the_owner(serve_between):
    client = serve_between(activity="check-all on main")
    for html in (client.get("/").text, client.get("/live").text):
        assert "Needs you" not in html and "Nothing needs you" not in html
        assert 'id="needs-you"' not in html


def test_a_live_run_between_jobs_shows_its_activity(serve_between):
    running = section(serve_between(activity="check-all on main").get("/live").text, "running")
    assert "Running: check-all on main" in running
    assert "Nothing is running" not in running


def test_a_waiting_run_names_its_ticket_and_until_when(serve_between):
    """f2-03: "waiting for Claude" between jobs named no ticket."""
    html = (
        serve_between(
            activity="waiting for Claude · f2-06-overview-allowances until 01:40",
            waiting_until="2026-10-02T01:40:00+00:00",
        )
        .get("/live")
        .text
    )
    running = section(html, "running")
    assert "Running: waiting for Claude · f2-06-overview-allowances until 01:40" in running


def test_a_run_ended_by_a_ctrl_c_is_not_running(serve_between, db_path):
    """f2-03: after a Ctrl-C the page said "on Claude's reserve" until the heartbeat went stale."""
    from runner import metrics

    client = serve_between(activity="picking the next ticket", reserve=True)
    conn = metrics.open_db(db_path)
    try:
        run = conn.execute("SELECT id FROM runs WHERE run_dir = '20261002-115000'").fetchone()[0]
        metrics.end_run(conn, run, NOW.isoformat(), "interrupted")
    finally:
        conn.close()
    running = section(client.get("/live").text, "running")
    assert "Nothing is running" in running
    assert "on Claude's reserve" not in running


def test_a_run_on_the_reserve_has_the_pill(serve_between):
    html = serve_between(activity="gates · f1-21", reserve=True).get("/live").text
    assert "on Claude's reserve" in section(html, "running")


def test_a_running_job_shows_waiting_reserve_and_claude_tokens(client, db_path):
    from runner import metrics

    conn = metrics.open_db(db_path)
    try:
        run = conn.execute("SELECT id FROM runs WHERE run_dir = '20261002-113500'").fetchone()[0]
        metrics.update_run_activity(conn, run, "waiting for Claude", "2026-10-02T01:40:00+00:00")
        metrics.set_run_reserve(conn, run)
    finally:
        conn.close()
    running = section(client.get("/live").text, "running")
    assert "f1-04-live" in running
    assert "Waiting for Claude's limit to reset, until 01:40" in running
    assert "on Claude's reserve" in running
    assert "42k tokens in" not in running  # the waiting line replaces the Live line
    assert "elapsed time only" not in running


def test_the_queue_has_its_tickets_and_the_command_that_drains_it(client):
    queue = section(client.get("/").text, "queue")
    assert queue.index("f1-05-first") < queue.index("f1-06-second")
    assert "Queued first." in queue
    assert "uv run runner milestone f1" in queue
    assert "f1-01-first" not in queue  # merged


def test_the_last_verdict_is_the_milestones_and_the_last_runs(client):
    html = client.get("/").text
    verdict = section(html, "verdict")
    assert "F1" in verdict and "ready" in verdict
    assert "3 merged, 0 not" in verdict
    assert 'href="/runs/20260930-100000?project=coucou"' in html


def test_the_allowance_bar_counts_this_windows_claude_tokens(client):
    allowance = section(client.get("/").text, "allowance")
    # 30k in the last 5 h, from any project; the last refusal came at 650k
    assert "30k of ≈650k token-equivalents" in allowance
    assert "5%" in allowance


def test_without_a_refusal_the_allowance_has_no_limit(db):
    a = claude_allowance(db, NOW)
    assert (a.used, a.limit, a.share) == (0, None, None)


def test_savings_are_for_the_current_milestone(client):
    savings = section(client.get("/").text, "savings")
    assert "F1" in savings
    # f1-04-live now has a job too, so the review and checkpoint ($1.80) split four ways:
    # supporting is $3 + 3 × $0.45; doing it itself is f1-01's 100 lines at $1.50
    assert "$1.50" in savings and "$4.35" in savings and "-$2.85" in savings
    assert "15k" in savings  # token-equivalents underneath


def test_the_spend_chart_holds_each_milestones_claude_dollars(serve):
    html = serve(live=False).get("/").text
    assert charts(html) == {"spend": {"labels": ["M4", "F1"], "dollars": [2.0, 7.8]}}
    # charts.js draws each kind with a function of that name
    assert re.search(r"^\s+spend\(", CHARTS_JS.read_text(), re.M)


def test_another_project_shows_only_its_own(client):
    html = client.get(f"/?project={OTHER}").text
    assert "m1-01-elsewhere" in section(html, "queue")
    assert "uv run runner milestone m1" in section(html, "queue")
    for mine in ("f1-05-first", "f1-04-live", "ADR 15", "3 merged, 0 not"):
        assert mine not in html
    assert "m1-01-elsewhere" not in client.get("/").text
