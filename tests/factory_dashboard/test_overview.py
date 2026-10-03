import json
import re
from datetime import timedelta
from pathlib import Path

from tests.factory_dashboard.conftest import LOCAL, NOW, OPUS, OTHER, PROJECT

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
    assert "read 42k tokens · 17 turns" in running
    assert "30 s ago" in running  # the heartbeat
    assert "Running now." in running  # the ticket's title
    needs = section(html, "needs-you")
    assert "heartbeat" not in needs
    assert "idle" not in needs  # the runner is live, so the queue isn't waiting on it


def test_a_stale_heartbeat_is_a_needs_you_item_instead(serve):
    html = serve(heartbeat_age=timedelta(minutes=3)).get("/").text
    assert "f1-04-live" not in section(html, "running")
    needs = section(html, "needs-you")
    assert "heartbeat stopped 3 min ago" in needs and "f1-04-live" in needs
    assert "uv run runner run" in needs  # the standing command (ADR 17), not one milestone
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
    assert 'hx-trigger="every 5s [window.liveIdle()]"' in html
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


def test_a_waiting_run_names_its_ticket_and_until_when(serve_between, db_path):
    """f2-03: "waiting for Claude" between jobs named no ticket."""
    from runner import metrics

    conn = metrics.open_db(db_path)
    try:
        proj = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()["id"]
        m = metrics.upsert_milestone(conn, proj, "f2")
        metrics.upsert_ticket(
            conn,
            proj,
            "f2-06-overview-allowances",
            milestone_id=m,
            kind="lead",
            state="ready",
            title="Overview allowances.",
        )
    finally:
        conn.close()
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
    assert "Overview allowances." in running


def test_a_checkpoint_job_shows_no_goal_line(client, db_path):
    """A checkpoint job (no ticket) shows no goal line."""
    from runner import metrics

    conn = metrics.open_db(db_path)
    try:
        run = conn.execute("SELECT id FROM runs WHERE run_dir = '20261002-113500'").fetchone()[0]
        f1 = conn.execute("SELECT id FROM milestones WHERE key = 'f1'").fetchone()["id"]
        job_id = metrics.start_job(
            conn,
            run,
            ticket_id=None,
            milestone_id=f1,
            role="checkpoint",
            agent=OPUS,
            attempt=1,
            started=NOW.isoformat(),
        )
        metrics.update_running_job(conn, job_id, tokens_in=10_000, steps=5)
    finally:
        conn.close()
    html = client.get("/").text
    running = section(html, "running")
    assert "checkpoint" in running
    assert "Nothing is running" not in running
    # The checkpoint card (job 14) has no title div.
    # Find "job 14" in the HTML and check the surrounding context for running-title.
    idx = html.index("job 14")
    # The card content extends from "job 14" to the next "</div>" at the card level.
    # Grab a chunk and verify no running-title appears.
    chunk = html[idx : idx + 500]
    assert "running-title" not in chunk


def test_a_waiting_run_with_unknown_ticket_shows_no_title(serve_between):
    """A waiting run referencing an unknown ticket shows no title line."""
    html = (
        serve_between(
            activity="waiting for Claude · f9-99-missing-ticket until 02:00",
            waiting_until="2026-10-02T02:00:00+00:00",
        )
        .get("/live")
        .text
    )
    running = section(html, "running")
    assert "Running: waiting for Claude · f9-99-missing-ticket until 02:00" in running
    assert "Nothing is running" not in running


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

    def test_claude_job_shows_cached_and_turns(client, db_path):
        """Claude job with cached input should show summed tokens and turns."""
        from runner import metrics

        conn = metrics.open_db(db_path)
        try:
            project = metrics.upsert_project(conn, PROJECT)
            f1 = metrics.upsert_milestone(conn, project, "f1", verdict="ready")
            run = metrics.upsert_run(
                conn,
                project,
                "20261002-123456",
                command="milestone f1",
                started="2026-10-02T12:00:00+00:00",
                heartbeat="2026-10-02T12:00:30+00:00",
            )
            ticket = metrics.upsert_ticket(
                conn, project, "f1-99-claude", milestone_id=f1, kind="developer", state="running"
            )
            job = metrics.start_job(
                conn,
                run,
                ticket_id=ticket,
                milestone_id=f1,
                role="developer",
                agent=OPUS,
                attempt=1,
                started="2026-10-02T12:00:00+00:00",
            )
            metrics.update_running_job(conn, job, tokens_in=36_000, tokens_cached=970_000, steps=18)
        finally:
            conn.close()
        running = section(client.get("/").text, "running")
        assert "read 970k tokens · 18 turns" in running


def test_the_queue_has_its_tickets_and_the_command_that_drains_it(client):
    queue = section(client.get("/").text, "queue")
    assert queue.index("f1-05-first") < queue.index("f1-06-second")
    assert "Queued first." in queue
    assert "uv run runner run" in queue
    assert "f1-01-first" not in queue  # merged


def test_the_last_verdict_is_the_milestones_and_the_last_runs(client):
    html = client.get("/").text
    verdict = section(html, "verdict")
    assert "F1" in verdict and "ready" in verdict
    assert "3 merged, 0 not" in verdict
    assert 'href="/runs/20260930-100000?project=coucou"' in html


def allowance_rows(html: str) -> dict[str, str]:
    """The allowance panel's rows by their id (``claude-five_hour``…), each row's own text."""
    panel = re.search(r'<section[^>]*\bid="allowance"[^>]*>(.*?)</section>', html, re.S)
    assert panel, "no allowance section"
    parts = re.split(r'<div id="allow-([a-z_-]+)">', panel.group(1))[1:]
    return {
        key: " ".join(re.sub(r"<[^>]+>", " ", text).split())
        for key, text in zip(parts[::2], parts[1::2], strict=True)
    }


def test_each_allowance_row_shows_its_own_reading_and_reset(allowance_client):
    """f2-13: the latest reading per window (Opus's, written after Sonnet's), each in its row;
    a later day's reset gives its date."""
    rows = allowance_client.get("/").text
    assert allowance_rows(rows) == {
        "claude-five_hour": "Claude 5-hour window: 80% resets at 17:00 kept for you from here",
        "claude-seven_day": "Claude week: 20% resets on Oct 9 12:00"
        " reserve kept for the lead from here",
        "copilot-month": "Copilot month: 2% resets on Nov 1 12:00",
        "ollama-ollama": "Ollama allowance no data yet",
    }


def test_the_local_model_has_no_allowance_row(allowance_client):
    assert LOCAL not in section(allowance_client.get("/").text, "allowance")


def test_without_readings_every_row_says_no_data_yet(serve, db_path):
    from runner import metrics

    client = serve()
    conn = metrics.open_db(db_path)
    try:
        conn.execute("DELETE FROM usage_events WHERE kind = 'reading'")
        conn.commit()
    finally:
        conn.close()
    rows = allowance_rows(client.get("/").text)
    assert len(rows) == 4
    assert all("no data yet" in row and "%" not in row for row in rows.values())


def test_a_reading_past_its_reset_says_reset_since_with_no_percentage(serve, db_path):
    from runner import metrics

    client = serve()
    conn = metrics.open_db(db_path)
    try:
        conn.execute(
            "DELETE FROM usage_events WHERE kind = 'reading' AND agent LIKE 'claude-%'"
            " AND \"window\" = 'five_hour'",
        )
        metrics.add_usage_event(
            conn,
            OPUS,
            "2026-10-01T10:00:00+00:00",
            "reading",
            window="five_hour",
            value=0.5,
            resets_at="2026-10-01T15:00:00+00:00",
        )
    finally:
        conn.close()
    row = allowance_rows(client.get("/").text)["claude-five_hour"]
    assert row == "Claude 5-hour window reset since, no new reading kept for you from here"


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
    assert "uv run runner run" in section(html, "queue")
    for mine in ("f1-05-first", "f1-04-live", "ADR 15", "3 merged, 0 not"):
        assert mine not in html
    assert "m1-01-elsewhere" not in client.get("/").text


def queue_rows(html: str) -> dict[str, str]:
    """Queue table rows by ticket id, each row's text (tags stripped)."""
    # The queue section text has all tags stripped. Each row appears as:
    # ticket_id goal difficulty ready_now waits_for
    # We split on the id column which is always the first token
    rows: dict[str, str] = {}
    for m in re.finditer(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        raw = m.group(1)
        # Extract the ticket id from the href
        id_m = re.search(r'href="/tickets/([^"?]+)', raw)
        if id_m:
            tid = id_m.group(1)
            # Strip tags from the row content
            cell_text = " ".join(re.sub(r"<[^>]+>", " ", raw).split())
            rows[tid] = cell_text
    return rows


def test_a_ticket_with_a_running_job_isnt_in_the_queue(queue_client):
    html = queue_client.get("/").text
    q = section(html, "queue")
    # f1-04-live should not appear as a ticket row (in the Ticket column)
    # It may appear in the "Waits for" column of another row
    import html as html_module

    q_decoded = html_module.unescape(q)
    # Check that f1-04-live doesn't appear as a standalone ticket id (followed by space or end)
    assert re.search(r"\bf1-04-live\b", q_decoded) is None or "waits for f1-04-live" in q_decoded


def test_a_ticket_whose_dependency_is_ready_waits_for_that_id(queue_client):
    html = queue_client.get("/").text
    q = section(html, "queue")
    # f1-12-waits-running depends on f1-04-live (running, not done)
    import html as html_module

    q_decoded = html_module.unescape(q)
    assert "waits for f1-04-live" in q_decoded


def test_a_ticket_whose_dependency_is_escalated_waits_for_escalation(queue_client, db_path):
    html = queue_client.get("/").text
    q = section(html, "queue")
    # Verify the database state directly
    from runner import metrics

    conn = metrics.open_db(db_path)
    try:
        proj = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()["id"]
        f1 = conn.execute(
            "SELECT id FROM milestones WHERE key = 'f1' AND project_id = ?", (proj,)
        ).fetchone()["id"]
        esc = conn.execute(
            "SELECT state FROM tickets WHERE ticket = 'f1-12-escalated' AND milestone_id = ?",
            (f1,),
        ).fetchone()
        # f1-12-escalated should have state 'escalated'
        assert esc is not None, "f1-12-escalated should exist"
        assert esc["state"] == "escalated", (
            f"f1-12-escalated state should be 'escalated', got {esc['state']!r}"
        )
    finally:
        conn.close()
    import html as html_module

    q_decoded = html_module.unescape(q)
    assert "waits for f1-12-escalated's escalation" in q_decoded


def test_a_lead_ticket_waits_for_claude(queue_claude_client):
    html = queue_claude_client.get("/").text
    q = section(html, "queue")
    assert "waits for Claude" in q


def test_ready_now_comes_before_waiting(queue_client):
    html = queue_client.get("/").text
    q = section(html, "queue")
    # Ready-now tickets should appear before waiting ones in the HTML
    # f1-10-queued and f1-05-first are ready now
    # f1-12-waits-running and f1-13-waits-escalated are waiting
    ready_pos = []
    waiting_pos = []
    for tid in ("f1-10-queued", "f1-05-first"):
        pos = q.find(tid)
        if pos >= 0:
            ready_pos.append(pos)
    for tid in ("f1-12-waits-running", "f1-13-waits-escalated"):
        pos = q.find(tid)
        if pos >= 0:
            waiting_pos.append(pos)
    if ready_pos and waiting_pos:
        assert max(ready_pos) < min(waiting_pos), "ready-now rows should come before waiting rows"


def test_the_live_part_pauses_while_the_owner_scrolls_or_selects(client):
    """2026-10-03: the queue jumped back to the top every 5 s while the owner scrolled it,
    and a selection was lost (f4-14)."""
    html = client.get("/").text
    assert 'hx-trigger="every 5s [window.liveIdle()]"' in html
    assert "window.liveIdle" in html.split('<div id="live"')[0]  # defined once, outside the swap
