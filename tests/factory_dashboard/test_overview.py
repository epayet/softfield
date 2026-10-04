import json
import re
import sqlite3
from datetime import UTC, datetime, timedelta
from html import unescape
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

from factory_dashboard.overview import queue
from runner import metrics
from tests.factory_dashboard.conftest import LOCAL, NOW, OPUS, OTHER, PROJECT, SONNET

CHARTS_JS = Path(__file__).parents[2] / "factory_dashboard" / "static" / "charts.js"


def section(html: str, name: str) -> str:
    """The text of the page's ``<section id="name">``, tags stripped."""
    match = re.search(rf'<section[^>]*\bid="{name}"[^>]*>(.*?)</section>', html, re.S)
    assert match, f"no section {name}"
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", match.group(1))).split())


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
    assert ids == [
        "needs-you", "now", "allowance", "line-live", "clog", "verdict", "away", "savings",
        "spend",
    ]  # fmt: skip
    assert "Next in line" in section(html, "now")
    assert 'id="running"' not in html and 'id="queue"' not in html
    live = client.get("/live").text
    assert 'id="running"' not in live and 'id="queue"' not in live


def test_needs_you_lists_open_owner_items_with_their_command(client):
    needs = section(client.get("/").text, "needs-you")
    assert "Should reactions be editable once sent?" in needs
    assert "uv run runner accept 15" in needs
    assert "Sign in to Ollama." not in needs  # resolved


def test_a_job_with_a_fresh_heartbeat_is_running_now(client):
    html = client.get("/").text
    now = section(html, "now")
    assert "f1-04-live" in now
    assert "attempt 2" in now and LOCAL in now and "developer" in now
    assert "12 min" in now  # elapsed
    assert "read 42k tokens · 17 turns" in now
    assert "30 s ago" in now  # the heartbeat
    assert "Running now." in now  # the ticket's title
    needs = section(html, "needs-you")
    assert "heartbeat" not in needs
    assert "idle" not in needs  # the runner is live, so the queue isn't waiting on it


def test_a_stale_heartbeat_is_a_needs_you_item_instead(serve):
    html = serve(heartbeat_age=timedelta(minutes=3)).get("/").text
    assert "f1-04-live" not in section(html, "now")
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
    assert "f1-04-live" in section(html, "now")
    # the bare sections: the page's two wrappers fetch it every 5 s, keeping the project (f3-16)
    assert "hx-get" not in html
    page = client.get("/?project=coucou").text
    assert page.count('hx-get="/live?project=coucou"') == 2
    assert page.count('hx-swap="innerHTML"') == 2
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
    running = section(serve_between(activity="check-all on main").get("/live").text, "now")
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
    now = section(html, "now")
    assert "Running: waiting for Claude · f2-06-overview-allowances until 01:40" in now
    assert "Overview allowances." in now


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
    now = section(html, "now")
    assert "checkpoint" in now
    assert "Nothing is running" not in now
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
    now = section(html, "now")
    assert "Running: waiting for Claude · f9-99-missing-ticket until 02:00" in now
    assert "Nothing is running" not in now
    assert "running-title" not in html


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
    running = section(client.get("/live").text, "now")
    assert "Nothing is running" in running
    assert "on Claude's reserve" not in running


def test_cached_only_shown_when_input_null(client, db_path):
    """Claude job with only cached tokens (input null) should show cached count."""
    from runner import metrics

    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1", verdict="ready")
        run = metrics.upsert_run(
            conn,
            project,
            "20261002-123457",
            command="milestone f1",
            started="2026-10-02T13:00:00+00:00",
            heartbeat="2026-10-02T13:00:30+00:00",
        )
        ticket = metrics.upsert_ticket(
            conn, project, "f1-98-claude", milestone_id=f1, kind="developer", state="running"
        )
        job = metrics.start_job(
            conn,
            run,
            ticket_id=ticket,
            milestone_id=f1,
            role="developer",
            agent=OPUS,
            attempt=1,
            started="2026-10-02T13:00:00+00:00",
        )
        metrics.update_running_job(conn, job, tokens_in=None, tokens_cached=500_000, steps=10)
    finally:
        conn.close()
    running = section(client.get("/").text, "now")
    assert "read 500k tokens · 10 turns" in running


def test_now_holds_what_works_then_next_in_line_and_the_command_that_drains_it(client):
    now = section(client.get("/").text, "now")
    working, next_in_line = now.split("Next in line", 1)
    assert "f1-04-live" in working and "attempt 2" in working and "Running now." in working
    assert re.search(r"\b1 f1-05-first Queued first\. · a developer\b", next_in_line)
    assert next_in_line.index("1 f1-05-first") < next_in_line.index("2 f1-06-second")
    assert "uv run runner run" in next_in_line
    assert "f1-01-first" not in next_in_line  # merged


def test_the_last_verdict_is_the_milestones_and_the_last_runs(client):
    html = client.get("/").text
    verdict = section(html, "verdict")
    assert "F1" in verdict and "ready" in verdict
    assert "3 merged, 0 not" in verdict
    assert 'href="/runs/20260930-100000?project=coucou"' in html


def with_clog(monkeypatch, clog: dict[str, object] | None) -> None:
    """The line's ``clog`` set to ``clog``, the rest of the document as it is."""
    from factory_dashboard import line

    real = line.live_line

    def live_line(*args, **kwargs):
        doc = real(*args, **kwargs)
        doc["clog"] = clog
        return doc

    monkeypatch.setattr(line, "live_line", live_line)


def clog(**numbers: object) -> dict[str, object]:
    idle = [
        {"agent": LOCAL, "name": "qwen", "minutes": 0, "share": 0.0},
        {"agent": "gpt-oss", "name": "gpt-oss", "minutes": 25, "share": 0.1},
        {"agent": "devstral", "name": "devstral", "minutes": 25, "share": 0.1},
    ]
    zero = {"limit": 0, "failed": 0, "failures": 0, "idle": idle, "owner": 0, "live": 240}
    return zero | numbers


def test_what_clogged_the_line_shows_the_four_numbers_and_the_biggest(client, monkeypatch):
    with_clog(monkeypatch, clog(limit=12, failed=31, failures=2, owner=5))
    panel = section(client.get("/").text, "clog")
    assert "What clogged the line today" in panel
    assert "Waiting for Claude's limit 12 min" in panel
    assert "Failed attempts 2 · 31 min" in panel
    assert "Machines idle while one job runs 2 of 3" in panel
    assert "Stopped for you 5 min" in panel
    assert "Biggest clog: Failed attempts, 31 min." in panel
    assert "240" not in panel  # the runner's live time isn't one of the four


def test_the_biggest_clog_names_the_most_idle_machine_and_a_tie_goes_first(client, monkeypatch):
    with_clog(monkeypatch, clog(limit=25))
    panel = section(client.get("/").text, "clog")
    assert "Biggest clog: Waiting for Claude's limit, 25 min." in panel
    with_clog(monkeypatch, clog(limit=10, owner=20))
    panel = section(client.get("/").text, "clog")
    assert "Biggest clog: Idle: gpt-oss, 25 min." in panel


def test_a_day_without_clogs_says_so(client, monkeypatch):
    with_clog(monkeypatch, clog(idle=[]))
    panel = section(client.get("/").text, "clog")
    assert "Machines idle while one job runs 0 of 0" in panel
    assert "Nothing clogged the line today." in panel and "Biggest" not in panel


def test_without_a_clog_document_there_is_no_clog_panel(client, monkeypatch):
    with_clog(monkeypatch, None)
    html = client.get("/").text
    assert 'id="clog"' not in html and "What clogged the line today" not in html


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
    assert "m1-01-elsewhere" in section(html, "now")
    assert "uv run runner run" in section(html, "now")
    for mine in ("f1-05-first", "f1-04-live", "ADR 15", "3 merged, 0 not"):
        assert mine not in html
    assert "m1-01-elsewhere" not in client.get("/").text


def waits(db_path: Path) -> dict[str, str | None]:
    """``queue``'s tickets on the fixture database, in its order, each with its ``waits_for``."""
    conn = metrics.open_db(db_path)
    try:
        return {q.ticket: q.waits_for for q in queue(conn, PROJECT, NOW)}
    finally:
        conn.close()


def test_a_ticket_with_a_running_job_isnt_in_the_queue(queue_client, db_path):
    assert "f1-04-live" not in waits(db_path)


def test_a_ticket_whose_dependency_is_ready_waits_for_that_id(queue_client, db_path):
    # f1-12-waits-running depends on f1-04-live (running, not done)
    assert waits(db_path)["f1-12-waits-running"] == "waits for f1-04-live"


def test_a_ticket_whose_dependency_is_escalated_waits_for_escalation(queue_client, db_path):
    assert waits(db_path)["f1-13-waits-escalated"] == "waits for f1-12-escalated's escalation"


def test_a_lead_ticket_waits_for_claude(queue_claude_client, db_path):
    assert waits(db_path)["f1-14-lead"] == "waits for Claude"


def test_ready_now_comes_before_waiting(queue_client, db_path):
    order = list(waits(db_path))
    ready = [order.index(t) for t in ("f1-10-queued", "f1-05-first")]
    waiting = [order.index(t) for t in ("f1-12-waits-running", "f1-13-waits-escalated")]
    assert max(ready) < min(waiting)


def test_next_in_line_is_the_first_three_of_the_run_order(queue_client, db_path):
    now = section(queue_client.get("/").text, "now")
    rows = now.split("Next in line", 1)[1]
    numbers = re.findall(r"\b(\d) (f1-\d\d-[a-z-]+)", rows)
    ids = [t for _, t in numbers]
    assert ids == list(waits(db_path))[:3]
    assert "f1-04-live" not in ids
    assert [n for n, _ in numbers] == ["1", "2", "3"]  # more than three wait: only three rows
    assert "4 f1-" not in rows


def test_the_live_part_pauses_while_the_owner_scrolls_or_selects(client):
    """2026-10-03: the queue jumped back to the top every 5 s while the owner scrolled it,
    and a selection was lost (f4-14)."""
    html = client.get("/").text
    assert 'hx-trigger="every 5s [window.liveIdle()]"' in html
    assert "window.liveIdle" in html.split('<div id="live-')[0]  # defined once, outside the swap


# --- in a browser: the 5 s refresh (f3-16) -----------------------------------------------

ORIGIN = "http://127.0.0.1:8765"
STATIC = Path(__file__).parents[2] / "factory_dashboard" / "static"
REFRESH = 12_000  # ms: up to two 5 s polls


def open_overview(page, client) -> None:
    """``/`` in Chromium, with ``/`` and ``/live`` rendered by ``client`` on every request, so
    what the database holds at each poll is what the page gets."""

    def serve(route) -> None:
        url = route.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            route.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        elif path in ("/", "/live"):
            body = client.get(url).text
            route.fulfill(body=body, content_type="text/html; charset=utf-8")
        else:
            route.fulfill(status=404, body="")

    page.route(f"{ORIGIN}/**", serve)
    page.goto(ORIGIN + "/")


def test_needs_you_comes_back_when_a_need_appears_after_the_page_loaded(
    page, serve_between, db_path
):
    """In f3-14 the empty Needs you swapped its wrapper away, so a later need never showed."""
    open_overview(page, serve_between(activity="check-all on main"))
    assert page.locator("#needs-you").count() == 0
    page.wait_for_timeout(6_000)  # one refresh with nothing to show
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_owner_item(
            conn,
            project,
            "adr",
            "ADR 30",
            text="A question that came later.",
            created=NOW.isoformat(),
        )
    finally:
        conn.close()
    page.wait_for_selector("#needs-you", timeout=REFRESH)
    assert "A question that came later." in page.locator("#needs-you").inner_text()


def test_now_keeps_refreshing_after_the_first_refresh(page, serve_between, db_path):
    """In f3-14 the first refresh replaced #live-now with a bare section that didn't poll."""
    client = serve_between(activity="check-all on main")

    def running(title: str) -> None:
        conn = metrics.open_db(db_path)
        try:
            project = metrics.upsert_project(conn, PROJECT)
            f1 = metrics.upsert_milestone(conn, project, "f1")
            ticket = metrics.upsert_ticket(
                conn,
                project,
                "f1-30-now",
                milestone_id=f1,
                kind="developer",
                state="running",
                title=title,
            )
            metrics.start_job(
                conn,
                metrics.upsert_run(conn, project, "20261002-115000"),
                ticket_id=ticket,
                milestone_id=f1,
                role="developer",
                agent=LOCAL,
                attempt=1,
                started=NOW.isoformat(),
            )
        finally:
            conn.close()

    open_overview(page, client)
    now = page.locator("#now")
    for title in ("The first title.", "The second title."):
        running(title)
        now.get_by_text(title).wait_for(timeout=REFRESH)
    assert "The first title." not in now.inner_text()


# --- away (f3-21) --------------------------------------------------------------------------------


SINCE = datetime(2026, 10, 2, 8, 0, tzinfo=UTC)


def write_away(conn: sqlite3.Connection) -> None:
    """Between ``SINCE`` and ``NOW`` (08:00 to 12:00 UTC): ``away-b`` merged at 10:30 (by Opus,
    after an escalation), ``away-a`` at 09:20 (after one failed attempt); ``away-c`` blocked
    after a last attempt failed at 11:10 (written at +02:00); a Sonnet checkpoint ($0.50) and
    an owner item. Before it: ``away-early`` merged at 07:30, a failed attempt at 05:10, a
    direction ($4) and an owner item; after it, a failed attempt at 12:30."""
    project = metrics.upsert_project(conn, PROJECT)
    m = metrics.upsert_milestone(conn, project, "f1")
    run = metrics.upsert_run(conn, project, "20261002-040000", started="2026-10-02T04:00:00+00:00")

    def ticket(name: str, state: str, merged_by: str | None = None) -> int:
        title = f"The {name} title."
        return metrics.upsert_ticket(
            conn, project, name, milestone_id=m, title=title, state=state, merged_by=merged_by
        )

    def job(
        ticket_id: int | None, role: str, agent: str, attempt: int, started: str, ended: str,
        outcome: str, cost: float | None = None,
    ) -> None:  # fmt: skip
        found = metrics.start_job(
            conn, run, ticket_id=ticket_id, milestone_id=m, role=role, agent=agent,
            attempt=attempt, started=f"2026-10-02T{started}",
        )  # fmt: skip
        metrics.finish_job(conn, found, ended=f"2026-10-02T{ended}", outcome=outcome, cost_usd=cost)

    early, a = ticket("away-early", "done", LOCAL), ticket("away-a", "done", LOCAL)
    b, c = ticket("away-b", "done", OPUS), ticket("away-c", "blocked")
    job(early, "developer", LOCAL, 1, "07:00:00+00:00", "07:30:00+00:00", "passed")
    job(a, "developer", LOCAL, 1, "08:30:00+00:00", "09:10:00+00:00", "failed")
    job(a, "developer", LOCAL, 2, "09:10:00+00:00", "09:20:00+00:00", "passed")
    job(b, "developer", LOCAL, 1, "05:00:00+00:00", "05:10:00+00:00", "failed")
    job(b, "escalation", OPUS, 1, "10:00:00+00:00", "10:30:00+00:00", "passed", 1.5)
    job(c, "direction", OPUS, 1, "07:00:00+00:00", "07:10:00+00:00", "passed", 4.0)
    job(c, "last-attempt", LOCAL, 1, "12:40:00+02:00", "13:10:00+02:00", "failed")
    job(c, "developer", LOCAL, 2, "12:10:00+00:00", "12:30:00+00:00", "failed")
    job(None, "checkpoint", SONNET, 1, "11:00:00+00:00", "11:05:00+00:00", "passed", 0.5)
    metrics.upsert_owner_item(
        conn, project, "escalation", "away-c", created="2026-10-02T11:15:00+00:00"
    )
    metrics.upsert_owner_item(conn, project, "adr", "old", created="2026-10-02T06:00:00+00:00")


def test_away_counts_what_happened_in_the_span_only(tmp_path):
    from factory_dashboard import queries

    path = tmp_path / "away.sqlite"
    conn = metrics.open_db(path)
    try:
        write_away(conn)
    finally:
        conn.close()
    conn = queries.connect(path)
    try:
        away = queries.away(conn, PROJECT, SINCE, NOW)
    finally:
        conn.close()
    assert [(t.ticket, t.title, t.merged_by) for t in away.merged] == [
        ("away-b", "The away-b title.", OPUS),
        ("away-a", "The away-a title.", LOCAL),
    ]  # latest first; away-early merged before the span
    assert away.failed == 2  # away-a's first attempt and away-c's last, not 05:10 or 12:30
    assert away.escalations == 1
    assert away.blocked == 1
    assert away.needs_you == 1
    assert away.claude_usd == 2.0  # the escalation and the checkpoint, not the 07:00 direction


def replay_since(html: str) -> datetime:
    """The ``since`` of the page's replay URL."""
    match = re.search(r'data-replay="([^"]+)"', html)
    assert match
    return datetime.fromisoformat(parse_qs(urlsplit(unescape(match.group(1))).query)["since"][0])


def chosen(html: str) -> str:
    """The replay bar's selected option."""
    bar = re.search(r'<select id="replay-span".*?</select>', html, re.S)
    assert bar
    match = re.search(r"<option [^>]*selected>([^<]+)</option>", bar.group(0))
    assert match
    return match.group(1)


def test_the_overview_offers_since_you_last_looked_with_its_time(client):
    local = NOW.astimezone()
    evening = (local - timedelta(days=1)).replace(hour=20, minute=0, second=0, microsecond=0)
    html = client.get("/").text
    assert chosen(html) == "since you last looked (20:00)"  # no cookie yet: 20:00 yesterday
    assert replay_since(html) == evening
    assert "overnight" not in html.lower()
    for other in ("the last hour", "today", "the last 24 h"):
        assert f">{other}</option>" in html
    looked = local - timedelta(hours=2, minutes=15)
    client.cookies.set("line_seen", looked.isoformat(timespec="seconds"))
    html = client.get("/").text
    assert chosen(html) == f"since you last looked ({looked:%H:%M})"
    assert replay_since(html) == looked.replace(microsecond=0)
    assert "since " + f"{looked:%H:%M}" in section(html, "away")


def test_the_away_panel_follows_since_and_links_each_merged_ticket(serve, db_path):
    conn = metrics.open_db(db_path)
    try:
        write_away(conn)
    finally:
        conn.close()
    since = datetime(2026, 10, 2, 10, 0, tzinfo=UTC)
    html = serve().get("/?" + urlencode({"since": since.isoformat()})).text
    assert replay_since(html) == since  # Replay plays the chosen span
    assert chosen(html) == f"since {since.astimezone():%H:%M}"
    assert re.search(r'href="/tickets/away-b\?project=[^"]+">away-b</a>', html)
    away = section(html, "away")
    assert "The away-b title. (merged by claude-opus)" in away
    assert "away-a" not in away and "away-early" not in away  # merged before 10:00
    assert "Nothing happened" not in away


def test_the_away_panel_says_when_nothing_happened(client):
    since = NOW - timedelta(seconds=1)
    html = client.get("/?" + urlencode({"since": since.isoformat()})).text
    assert section(html, "away").endswith(f"Nothing happened since {since.astimezone():%H:%M}.")


def test_choosing_a_span_reloads_the_overview_for_it(page, client):
    open_overview(page, client)
    with page.expect_navigation():
        page.select_option("#replay-span", label="the last hour")
    since = parse_qs(urlsplit(page.url).query)["since"][0]
    assert datetime.fromisoformat(since) == NOW - timedelta(hours=1)


def test_the_legend_sits_collapsed_after_the_floor_svg(client):
    """f4-34: the floor's legend is inside a <details> without open,
    placed after the floor's svgs, and not anywhere before them."""
    html = client.get("/").text
    line_section = re.search(r'<section[^>]*\bid="line-live"[^>]*>(.*?)</section>', html, re.S)
    assert line_section, "no line-live section"
    details = re.search(r"<details[^>]*>(.*?)</details>", line_section.group(1), re.S)
    assert details, "no legend details"
    assert "open" not in details.group(0).lower()
    assert "How to read the floor" in details.group(0)
    entries = [
        "lead ticket",
        "developer ticket",
        "belt carrying now",
        "numbers on belts: how many went that way today",
    ]
    for entry in entries:
        assert entry in details.group(1)
    for svg_match in re.finditer(r"<svg[^>]*>", line_section.group(1)):
        assert details.start() > svg_match.end(), "details must come after all SVGs"
