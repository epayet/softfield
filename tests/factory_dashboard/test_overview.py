import json
import re
import sqlite3
from datetime import UTC, datetime, timedelta
from html import unescape
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

from factory_dashboard.overview import queue, queued_jobs
from runner import metrics
from tests.factory_dashboard.conftest import LOCAL, NOW, OPUS, OTHER, PROJECT, SONNET
from tests.layout import layout_problems

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
        "needs-you", "now", "queue", "allowance", "line-live", "away", "savings",
        "spend",
    ]  # fmt: skip
    replay_html = re.search(r'<div class="panel replay" id="replay">', html)
    assert replay_html, "no #replay div"
    # #replay sits right after #line-live, outside it (htmx refreshes #line-live every 5 s).
    line_pos = html.index('id="line-live"')
    replay_pos = replay_html.start()
    away_pos = html.index('id="away"')
    assert line_pos < replay_pos < away_pos
    between = html[line_pos:replay_pos].rstrip()
    assert between.endswith("</section>"), "replay should be right after line-live's closing tag"
    assert "Next in line" not in section(html, "now")
    # The old #running section id is no longer present.
    assert 'id="running"' not in html
    live = client.get("/live").text
    # Queue section has its own id; the old #running id is gone.
    assert 'id="queue"' in live
    assert 'id="running"' not in live


def test_needs_you_lists_open_owner_items_with_their_command(client):
    needs = section(client.get("/").text, "needs-you")
    assert "Should reactions be editable once sent?" in needs
    assert "softfield accept 15" in needs
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
    assert "softfield run" in needs  # the standing command (ADR 17), not one milestone
    # with the runner gone, the queue waits on nobody
    assert "2 tickets waiting and the runner is idle" in needs


def test_a_project_the_runner_never_ran_shows_an_empty_queue(client):
    """f8 review: the queued jobs looked up the project's row, and a 500 replaced the page."""
    assert client.get("/?project=nosuch").status_code == 200
    live = client.get("/live?project=nosuch")
    assert live.status_code == 200
    assert "The queue is empty." in section(live.text, "queue")


def test_live_poller_has_no_hx_swap_oob(client):
    """f19-03: the stray hx-swap-oob on the poller is gone."""
    html = client.get("/").text
    poll = re.search(r'<div id="live-needs-you"[^>]*>', html)
    assert poll, "no #live-needs-you"
    assert "hx-swap-oob" not in poll[0], "poller must not carry hx-swap-oob"


def test_the_live_partial_answers_on_its_own_for_htmx(client):
    response = client.get("/live?project=coucou")
    assert response.status_code == 200
    html = response.text
    assert "<html" not in html
    assert "Should reactions be editable" in section(html, "needs-you")
    assert "f1-04-live" in section(html, "now")
    assert 'id="queue"' in html
    # The partial is bare: no hx-get wrapper inside it.
    assert "hx-get" not in html
    # /running returns 404 (the endpoint was removed).
    assert client.get("/running").status_code == 404
    # f19-02: one single poller on the Overview instead of four separate ones.
    page_html = client.get("/?project=coucou").text.split("<main>")[
        1
    ]  # not base.html's notify poll
    assert page_html.count('hx-get="/live?project=coucou"') == 1


def test_the_queue_item_goes_from_live_once_a_run_is_live(serve):
    stopped = serve(heartbeat_age=timedelta(minutes=3)).get("/live").text
    assert "runner is idle" in section(stopped, "needs-you")
    running = serve().get("/live").text
    assert "runner is idle" not in section(running, "needs-you")


def sign_off_all(db_path: Path) -> None:
    """Every milestone signed off, so none waits on the desk as ripe (f6-09)."""
    conn = metrics.open_db(db_path)
    try:
        conn.execute("UPDATE milestones SET status = 'done'")
    finally:
        conn.close()


def test_needs_you_is_absent_when_nothing_needs_the_owner(serve_between, db_path):
    client = serve_between(activity="check-all on main")
    sign_off_all(db_path)
    for html in (client.get("/").text, client.get("/live").text):
        assert "Needs you" not in html and "Nothing needs you" not in html
        assert 'id="needs-you"' not in html


def test_a_live_run_between_jobs_shows_its_activity(serve_between):
    running = section(serve_between(activity="check-all on main").get("/live").text, "now")
    assert "Running: check-all on main" in running
    assert "Nothing is running" not in running


def test_a_live_run_with_idle_activity_shows_idle_as_is(serve_between):
    """Idle activity is shown as-is in Now, without "Running: Idle" (F101 idle reads idle)."""
    running = section(
        serve_between(
            activity="Idle: 2 tickets wait for Claude's reserve · the week resets Mon 16:00"
        )
        .get("/live")
        .text,
        "now",
    )
    assert "Idle: 2 tickets wait for Claude's reserve · the week resets Mon 16:00" in running
    assert "Running: Idle" not in running


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


def test_a_run_on_the_reserve_has_the_pill(serve_between):
    html = serve_between(activity="gates · f1-21", reserve=True).get("/live").text
    assert "on Claude's reserve" in section(html, "now")


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
    running = section(client.get("/").text, "now")
    # 36k uncached + 970k cached: neither part alone renders as 1.0M.
    assert "read 1.0M tokens · 18 turns" in running


def test_now_leaves_out_a_bench(client, db_path):
    """Now is for the real runs (owner, 2026-10-04): a bench's replays run beside them."""
    from runner import metrics

    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1", verdict="ready")
        run = metrics.upsert_run(
            conn,
            project,
            "bench-20261002-120000",
            command="bench",
            started="2026-10-02T12:00:00+00:00",
            heartbeat="2026-10-02T12:00:30+00:00",
        )
        metrics.update_run_activity(conn, run, "bench f1-97-benched attempt 1/3", None)
        ticket = metrics.upsert_ticket(conn, project, "f1-97-benched", milestone_id=f1)
        metrics.start_job(
            conn,
            run,
            ticket_id=ticket,
            milestone_id=f1,
            role="bench",
            agent=OPUS,
            attempt=1,
            started="2026-10-02T12:00:00+00:00",
        )
    finally:
        conn.close()
    running = section(client.get("/").text, "now")
    assert "f1-04-live" in running  # the fixture's real run is still there
    assert "f1-97-benched" not in running and "bench-20261002" not in running


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
    html = client.get("/").text
    now = section(html, "now")
    assert "f1-04-live" in now and "attempt 2" in now and "Running now." in now
    queue_section = section(html, "queue")
    _unused, next_in_line = queue_section.split("Next in line", 1)
    assert re.search(r"\b1 f1-05-first Queued first\. · a developer\b", next_in_line)
    assert next_in_line.index("1 f1-05-first") < next_in_line.index("2 f1-06-second")
    # The command to drain the queue is in the queue section, not in now.
    assert "softfield run" in queue_section
    assert "softfield run" not in now
    assert "f1-01-first" not in next_in_line  # merged


def allowance_rows(html: str) -> dict[str, str]:
    """The allowance panel's rows by their id (``claude-five_hour``…), each row's own text."""
    panel = re.search(r'<section[^>]*\bid="allowance"[^>]*>(.*?)</section>', html, re.S)
    assert panel, "no allowance section"
    # Strip SVG elements so their text doesn't leak into row text, the reserve switches,
    # which `switch_row` reads, and the legend details block.
    text = re.sub(r"<svg[^>]*>.*?</svg>", "", panel.group(1), flags=re.S)
    text = re.sub(r'<button[^>]*class="lever[^"]*"[^>]*>.*?</button>', "", text, flags=re.S)
    text = re.sub(r'<details class="legend">.*?</details>', "", text, flags=re.S)
    parts = re.split(r'<div id="allow-([a-z_-]+)">', text)[1:]
    return {
        key: " ".join(re.sub(r"<[^>]+>", " ", text_part).split())
        for key, text_part in zip(parts[::2], parts[1::2], strict=True)
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
    assert len(rows) == 3
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


def allowance_client_with(db_path: Path, tmp_path: Path, switches: dict[str, str]):
    """``allowance_client`` with the project's repo in ``tmp_path``: this repo's runner.toml
    and a state.json holding ``switches``."""
    from fastapi.testclient import TestClient

    from factory_dashboard.app import create_app, get_now
    from tests.factory_dashboard.conftest import write_allowance

    repo = tmp_path / "repo"
    (repo / ".factory").mkdir(parents=True)
    toml = Path(__file__).resolve().parents[2] / ".factory" / "project.toml"
    (repo / ".factory" / "project.toml").write_text(toml.read_text(encoding="utf-8"))
    (repo / ".factory" / "var" / "runs").mkdir(parents=True)
    (repo / ".factory" / "var" / "runs" / "state.json").write_text(
        json.dumps({"switches": switches})
    )
    conn = metrics.open_db(db_path)
    try:
        write_allowance(conn)
        metrics.upsert_project(conn, PROJECT, repo=str(repo))
    finally:
        conn.close()
    app = create_app(db_path, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url="http://127.0.0.1:8765")


def switch_row(html: str, row: str) -> tuple[str, str | None, str | None, dict[str, str] | None]:
    """A meter row's reserve switch: aria-label, aria-checked, status text ("on until ..."/"asked"),
    and what its button posts (None: no button)."""
    found = re.search(rf'<div id="allow-{row}">(.*?)(?=<div id="allow-|</section>)', html, re.S)
    assert found, row
    button = re.search(r'<button[^>]*role="switch"[^>]*>(.*?)</button>', found[1], re.S)
    if button is None:
        return "", None, None, None
    aria_label = re.search(r'aria-label="([^"]*)"', button.group(0))
    aria_checked = re.search(r'aria-checked="([^"]*)"', button.group(0))
    status = None
    on_match = re.search(r'<small[^>]*class="until"[^>]*>on until (.*?)</small>', found[1], re.S)
    if on_match:
        status = "on until " + unescape(re.sub(r"<[^>]+>", " ", on_match[1])).strip()
    else:
        title_match = re.search(r'title="asked: (on|off)"', button.group(0))
        if title_match:
            status = "asked: " + title_match[1]
    vals = re.search(r"hx-vals='([^']*)'", button.group(0))
    return (
        unescape(aria_label[1]) if aria_label else "",
        aria_checked[1] if aria_checked else None,
        status,
        json.loads(unescape(vals[1])) if vals else None,
    )


def test_each_claude_meter_has_its_switch_showing_the_stored_state(db_path, tmp_path):
    """f8-06: the week's switch on (turned on 2.5 h ago, so until tomorrow 09:30) posts "off";
    the 5-hour switch, absent from state.json, is off and posts "on"."""
    client = allowance_client_with(db_path, tmp_path, {"week": "2026-10-02T09:30:00+00:00"})
    html = client.get("/").text
    label, checked, status, posts = switch_row(html, "claude-seven_day")
    assert label == "Let the factory use the week's reserve"
    assert checked == "true"
    assert status == "on until Sat 09:30"
    assert posts == {"kind": "reserve", "project": PROJECT, "subject": "week", "value": "off"}
    label, checked, status, posts = switch_row(html, "claude-five_hour")
    assert label == "Let the factory use your 25% of the 5-hour window"
    assert checked == "false"
    assert status is None
    assert posts == {"kind": "reserve", "project": PROJECT, "subject": "five_hour", "value": "on"}


def test_a_switch_on_for_more_than_24_hours_shows_off(db_path, tmp_path):
    client = allowance_client_with(db_path, tmp_path, {"five_hour": "2026-10-01T11:00:00+00:00"})
    label, checked, status, posts = switch_row(client.get("/").text, "claude-five_hour")
    assert label == "Let the factory use your 25% of the 5-hour window"
    assert checked == "false"
    assert status is None
    assert posts and posts["value"] == "on"


def test_without_a_config_both_switches_are_off(allowance_client):
    html = allowance_client.get("/").text
    for row, subject in (("claude-five_hour", "five_hour"), ("claude-seven_day", "week")):
        label, checked, status, posts = switch_row(html, row)
        assert label.startswith("Let the factory")
        assert checked == "false"
        assert status is None
        assert posts == {"kind": "reserve", "project": PROJECT, "subject": subject, "value": "on"}


def test_a_meter_of_another_agent_has_no_switch(allowance_client):
    html = allowance_client.get("/").text
    label, checked, status, posts = switch_row(html, "copilot-month")
    assert label == ""
    assert checked is None
    assert status is None
    assert posts is None
    # No switch div left in the page.
    assert 'class="switch"' not in html


def test_a_switch_asked_for_shows_on_its_way_with_no_button(db_path, tmp_path):
    """The owner's request shows at once (owner, 2026-10-07), until the runner takes it."""
    client = allowance_client_with(db_path, tmp_path, {})
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.add_request(conn, project, "reserve", "week", "on", NOW.isoformat())
        conn.commit()
    finally:
        conn.close()
    html = client.get("/").text
    # The asked switch button has on-its-way class, "asked: on" in its title, and is disabled.
    label, _checked, status, posts = switch_row(html, "claude-seven_day")
    assert label == "Let the factory use the week's reserve"
    assert status == "asked: on"
    assert posts == {"kind": "reserve", "project": PROJECT, "subject": "week", "value": "on"}
    row = re.search(
        r'<div id="allow-claude-seven_day">(.*?)(?=<div id="allow-|</section>)', html, re.S
    )
    assert row
    assert "disabled" in row[1]
    btn = re.search(r'<button[^>]*class="lever on-its-way"[^>]*>', row[1])
    assert btn, "asked switch should have on-its-way class"
    assert 'title="asked: on"' in btn.group(0), "asked switch should have 'asked: on' title"
    assert switch_row(html, "claude-five_hour")[3] is not None


def test_live_returns_the_allowance_panel_after_running(allowance_client):
    html = allowance_client.get("/live").text
    ids = re.findall(r'<section[^>]*\bid="([a-z-]+)"', html)
    assert "allowance" in ids and ids.index("allowance") > ids.index("now")
    assert allowance_rows(html)["claude-five_hour"].startswith("Claude 5-hour window: 80%")


def test_a_mark_has_a_title_equal_to_its_label(allowance_client):
    html = allowance_client.get("/live").text
    marks = re.findall(
        r'<div id="allow-([a-z_-]+)">.*?<span class="mark"[^>]*title="([^"]*)"', html, re.S
    )
    assert marks == [
        ("claude-five_hour", "kept for you from here"),
        ("claude-seven_day", "reserve kept for the lead from here"),
    ]


def test_savings_are_for_the_current_milestone(client):
    savings = section(client.get("/").text, "savings")
    assert "F1" in savings
    # f1-04-live now has a job too, so the review and checkpoint ($1.80) split four ways:
    # supporting is $3 + 3 × $0.45; doing it itself is f1-01's 100 lines at $1.50
    assert "$1.50" in savings and "$4.35" in savings and "-$2.85" in savings
    assert "15k" in savings  # token-equivalents underneath


def test_savings_heading_says_so_far_on_milestone(client):
    """The overview savings heading reads "so far on F6" for a milestone."""
    savings = section(client.get("/").text, "savings")
    assert "so far" in savings.lower()


def test_floor_heading_has_no_refreshes(client):
    """The floor's heading has no "refreshes"."""
    html = client.get("/").text
    line_live = re.search(r'<section[^>]*\bid="line-live"[^>]*>(.*?)</section>', html, re.S)
    assert line_live is not None
    text = unescape(re.sub(r"<[^>]+>", " ", line_live.group(1)))
    assert "refreshes" not in text.lower()


def test_the_spend_chart_holds_each_milestones_claude_dollars(serve):
    html = serve(live=False).get("/").text
    assert charts(html) == {"spend": {"labels": ["M4", "F1"], "dollars": [2.0, 7.8]}}
    # charts.js draws each kind with a function of that name
    assert re.search(r"^\s+spend\(", CHARTS_JS.read_text(), re.M)


def test_another_project_shows_only_its_own(client):
    html = client.get(f"/?project={OTHER}").text
    queue_section = section(html, "queue")
    assert "m1-01-elsewhere" in queue_section
    assert "softfield run" in queue_section
    assert "Next in line" in queue_section
    page = html.split("<main>", 1)[1]  # the top bar says what the whole factory does (ADR 30)
    for mine in ("f1-05-first", "f1-04-live", "ADR 15", "3 merged, 0 not"):
        assert mine not in page
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


# Each reason on its own ticket and on no other: the whole queue, not one key.
WAITS = {
    "f1-10-queued": None,
    "f1-11-waits-done": None,
    "f1-12-waits-running": "waits for f1-04-live",
    "f1-13-waits-escalated": "waits for f1-12-escalated's escalation",
    "f1-14-lead": None,
    "f1-05-first": None,
    "f1-06-second": None,
}


def test_a_ticket_whose_dependency_is_ready_waits_for_that_id(queue_client, db_path):
    # f1-12-waits-running depends on f1-04-live (running, not done)
    assert waits(db_path) == WAITS


def test_a_ticket_whose_dependency_is_escalated_waits_for_escalation(queue_client, db_path):
    assert waits(db_path) == WAITS


def test_a_lead_ticket_waits_for_claude(queue_claude_client, db_path):
    assert waits(db_path) == WAITS | {"f1-14-lead": "waits for Claude"}


def test_ready_now_comes_before_waiting(queue_client, db_path):
    order = list(waits(db_path))
    ready = [order.index(t) for t in ("f1-10-queued", "f1-05-first")]
    waiting = [order.index(t) for t in ("f1-12-waits-running", "f1-13-waits-escalated")]
    assert max(ready) < min(waiting)


def test_next_in_line_names_a_due_review_first(client, db_path):
    """f4-20: the review `runner run` takes next, as a batch, with no ticket page."""
    conn = metrics.open_db(db_path)
    try:
        project = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()
        metrics.upsert_milestone(conn, project["id"], "f1", status=metrics.REVIEW_DUE)
    finally:
        conn.close()
    html = client.get("/").text
    rows = section(html, "queue").split("Next in line", 1)[1]
    assert re.search(r"\b1 review F1 · a batch\b", rows)
    assert "/tickets/None" not in html and 'href="/tickets/"' not in html
    assert "2 f1-05-first" in rows


def test_next_in_line_says_what_a_parked_review_waits_for(client, db_path):
    """f53-02: parked until Claude's reset, it comes behind the tickets that can run."""
    until = NOW + timedelta(hours=1)
    conn = metrics.open_db(db_path)
    try:
        project = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()
        metrics.upsert_milestone(conn, project["id"], "f1", status=metrics.REVIEW_DUE)
        metrics.queue_job(
            conn,
            project["id"],
            "review",
            "f1",
            "F1's tickets are all done",
            (NOW - timedelta(hours=1)).isoformat(),
            until.isoformat(),
        )
    finally:
        conn.close()
    rows = section(client.get("/").text, "queue").split("Next in line", 1)[1]
    assert rows.index("1 f1-05-first") < rows.index("2 f1-06-second") < rows.index("3 review F1")
    reset = f"Claude's reset at {until.astimezone():%H:%M}"
    assert rows.endswith(f"3 review F1 · a batch · waits for {reset}")


def test_next_in_line_is_the_first_three_of_the_run_order(queue_client, db_path):
    now = section(queue_client.get("/").text, "queue")
    rows = now.split("Next in line", 1)[1]
    numbers = re.findall(r"\b(\d) (f1-\d\d-[a-z-]+)", rows)
    ids = [t for _, t in numbers]
    assert ids == list(waits(db_path))[:3]
    assert "f1-04-live" not in ids
    assert [n for n, _ in numbers] == ["1", "2", "3"]  # more than three wait: only three rows
    assert "4 f1-" not in rows


def _moves(html: str) -> list[tuple[str, str, dict[str, object]]]:
    """Next in line's ↑ and ↓ buttons: each one's arrow, label and the request it posts."""
    rows = html.split("Next in line", 1)[1].split("</section>", 1)[0]
    button = r"<button[^>]*?hx-vals='([^']*)'[^>]*aria-label=\"([^\"]*)\"[^>]*>(.)</"
    found = re.findall(button, rows)
    return [(arrow, label, json.loads(vals)) for vals, label, arrow in found]


def _post(ticket: str, value: str) -> dict[str, object]:
    return {"kind": "priority", "project": PROJECT, "subject": ticket, "value": value}


def test_next_in_line_shows_each_priority_with_buttons_that_move_it(queue_client, db_path):
    """f6-18: ↑ asks for one less than the ticket above's (0 at least), ↓ one more than the
    one below's; the first's ↑ is by one from its own. All at the default 100 here."""
    html = queue_client.get("/").text
    rows = section(html, "queue").split("Next in line", 1)[1]
    for ticket in ("f1-05-first", "f1-06-second", "f1-10-queued"):
        assert re.search(rf"\b{ticket}\b[^·]*· [^·]+ · priority 100 ↑ ↓", rows), ticket
    assert all(h == "/requests" for h in re.findall(r'hx-post="([^"]*)"', html.split("Next in")[1]))
    assert _moves(html) == [
        ("↑", "Move f1-05-first up: priority 99", _post("f1-05-first", "99")),
        ("↓", "Move f1-05-first down: priority 101", _post("f1-05-first", "101")),
        ("↑", "Move f1-06-second up: priority 99", _post("f1-06-second", "99")),
        ("↓", "Move f1-06-second down: priority 101", _post("f1-06-second", "101")),
        ("↑", "Move f1-10-queued up: priority 99", _post("f1-10-queued", "99")),
        ("↓", "Move f1-10-queued down: priority 101", _post("f1-10-queued", "101")),
    ]


def _prioritise(db_path: Path, ticket: str, own: int, card: int) -> None:
    """``ticket``'s own ``priority:`` in its file, and its milestone card's priority."""
    conn = metrics.open_db(db_path)
    try:
        project = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()[0]
        body = f"---\nid: {ticket}\nmilestone: f1\npriority: {own}\n---\n\n### Goal\nFirst now.\n"
        metrics.upsert_ticket(conn, project, ticket, body=body)
        metrics.upsert_milestone(conn, project, "f1", priority=card)
    finally:
        conn.close()


def test_next_in_line_follows_the_priorities_the_runner_reads(queue_client, db_path):
    """A ticket's own priority, else its card's: lower first, as `pick_next` takes them."""
    _prioritise(db_path, "f1-10-queued", own=5, card=50)
    html = queue_client.get("/").text
    rows = section(html, "queue").split("Next in line", 1)[1]
    assert [t for _, t in re.findall(r"\b(\d) (f1-\d\d-[a-z-]+)", rows)] == [
        "f1-10-queued",
        "f1-05-first",
        "f1-06-second",
    ]
    assert "priority 5 ↑ ↓" in rows and "priority 50 ↑ ↓" in rows
    assert [(arrow, post["subject"], post["value"]) for arrow, _, post in _moves(html)] == [
        ("↑", "f1-10-queued", "4"),
        ("↓", "f1-10-queued", "51"),
        ("↑", "f1-05-first", "4"),
        ("↓", "f1-05-first", "51"),
        ("↑", "f1-06-second", "49"),
        ("↓", "f1-06-second", "51"),  # one more than f1-11-waits-done's, below it
    ]
    assert list(waits(db_path))[:3] == ["f1-10-queued", "f1-05-first", "f1-06-second"]


def test_a_priority_at_0_has_no_up_button(queue_client, db_path):
    _prioritise(db_path, "f1-10-queued", own=0, card=100)
    moves = [(arrow, post["subject"]) for arrow, _, post in _moves(queue_client.get("/").text)]
    assert moves[:2] == [("↓", "f1-10-queued"), ("↑", "f1-05-first")]


def test_empty_queue_shows_message_once(serve):
    """An empty queue shows "The queue is empty." once, not twice."""
    client = serve(live=False)
    html = client.get("/").text
    queue_section = section(html, "queue")
    assert "Next in line" in queue_section
    count = queue_section.count("The queue is empty.")
    assert count == 1, f"expected 1, got {count}"


def test_queue_with_queued_jobs_says_how_many(queue_client, db_path):
    """f9-20: when there are no tickets but queued jobs exist,
    the queue's first line names the jobs waiting by count, never says "0 tickets"
    and never shows None."""
    # Remove all tickets from the queue so queue is empty
    conn = metrics.open_db(db_path)
    conn.execute("UPDATE tickets SET state = 'done' WHERE state = 'ready'")
    conn.commit()
    conn.close()
    # Insert a queued checkpoint job
    conn = metrics.open_db(db_path)
    try:
        proj = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()["id"]
        metrics.queue_job(conn, proj, "checkpoint", "f1", "A checkpoint", NOW.isoformat())
        conn.commit()
    finally:
        conn.close()
    html = queue_client.get("/live").text
    queue_section = section(html, "queue")
    assert "The queue is empty." not in queue_section
    assert "Checkpoint:" in queue_section
    # The first <p> in the queue section: count jobs, not tickets
    p_match = re.search(r"<p[^>]*>(.*?)</p>", html.split('id="queue"')[1].split("</section>")[0])
    assert p_match, "no <p> in queue section"
    p_text = unescape(re.sub(r"<[^>]+>", " ", p_match.group(1)))
    p_text = " ".join(p_text.split())
    assert "1 job waiting" in p_text, f"expected '1 job waiting' in '{p_text}'"
    assert "None" not in p_text
    assert "0 ticket" not in p_text


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
        elif path in ("/", "/live", "/away"):
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
    client = serve_between(activity="check-all on main")
    sign_off_all(db_path)
    open_overview(page, client)
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


# --- f19-03: every part refreshes on poll -------------------------------------------------------


def test_overview_poll_refreshes_every_part(page, serve_between, db_path):
    """f19-03: a single /live poll refreshes Needs you, Now, Queue, the allowance
    and the top bar."""
    client = serve_between(activity="check-all on main")
    sign_off_all(db_path)

    # Track /live requests.
    live_count = [0]

    def route(r) -> None:
        url = r.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        elif path == "/live":
            live_count[0] += 1
            body = client.get(url).text
            r.fulfill(body=body, content_type="text/html; charset=utf-8")
        elif path == "/" or path == "/away":
            body = client.get(url).text
            r.fulfill(body=body, content_type="text/html; charset=utf-8")
        else:
            r.fulfill(status=404, body="")

    page.route(f"{ORIGIN}/**", route)
    page.goto(ORIGIN + "/")

    # Wait for initial render.
    page.wait_for_selector("#live-facts", state="attached", timeout=REFRESH)

    # Record top bar status before any change.
    status_before = page.locator("#factory-status [role=status]").inner_text()

    # 1. Now: start a job and wait for its title.
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        ticket = metrics.upsert_ticket(
            conn,
            project,
            "f1-99-now",
            milestone_id=f1,
            kind="developer",
            state="running",
            title="Polling job.",
        )
        run_id = metrics.upsert_run(
            conn,
            project,
            "20261002-120000",
            heartbeat=(NOW - timedelta(seconds=10)).isoformat(),
        )
        metrics.start_job(
            conn,
            run_id,
            ticket_id=ticket,
            milestone_id=f1,
            role="developer",
            agent=LOCAL,
            attempt=1,
            started=NOW.isoformat(),
        )
    finally:
        conn.close()
    page.locator("#now").get_by_text("Polling job.").wait_for(timeout=REFRESH)

    # 2. Queue: add a ready ticket and wait for the count.
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        metrics.upsert_ticket(
            conn,
            project,
            "f1-99-queue",
            milestone_id=f1,
            kind="developer",
            state="ready",
            title="Queue item.",
        )
    finally:
        conn.close()
    page.locator("#queue").get_by_text("1 ticket waiting").wait_for(timeout=REFRESH)

    # 3. Allowance: add a reading and wait for 80%.
    conn = metrics.open_db(db_path)
    try:
        metrics.add_usage_event(
            conn,
            OPUS,
            NOW.isoformat(),
            "reading",
            window="five_hour",
            value=0.8,
            resets_at=(NOW + timedelta(hours=5)).isoformat(),
        )
    finally:
        conn.close()
    page.locator("#allowance").get_by_text("80%").wait_for(timeout=REFRESH)

    # 4. Needs you: add an owner item and wait for its text.
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_owner_item(
            conn,
            project,
            "poll",
            "Poll question.",
            text="Something to do.",
            created=NOW.isoformat(),
        )
    finally:
        conn.close()
    page.locator("#needs-you").get_by_text("Something to do.").wait_for(timeout=REFRESH)

    # 5. Top bar: status changed.
    status_after = page.locator("#factory-status [role=status]").inner_text()
    assert status_after != status_before, "top bar status did not change after poll"

    # 6. The poller fires at most once per 5 s interval: at least one poll must have occurred.
    assert live_count[0] >= 1, f"expected at least 1 /live poll, got {live_count[0]}"


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


def test_away_counts_failures_and_claude_as_the_rest_of_the_dashboard(tmp_path):
    """f3 review (f3-F4): an attempt stopped short (Ctrl-C, a park) isn't a failure, as in the
    clog; a Claude job whose cost wasn't kept costs its tokens priced, as everywhere else."""
    from factory_dashboard import queries

    path = tmp_path / "away.sqlite"
    conn = metrics.open_db(path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        run = metrics.upsert_run(conn, project, "20261002-080000")
        t = metrics.upsert_ticket(conn, project, "away-x", state="ready")
        for attempt, role, agent, note, tokens in (
            (1, "developer", LOCAL, "interrupted", None),
            (2, "developer", LOCAL, None, None),
            (1, "direction", OPUS, None, 1_000_000),
        ):
            job = metrics.start_job(
                conn, run, ticket_id=t, milestone_id=None, role=role, agent=agent,
                attempt=attempt, started="2026-10-02T09:00:00+00:00",
            )  # fmt: skip
            metrics.finish_job(
                conn, job, ended="2026-10-02T09:30:00+00:00", outcome="failed", note=note,
                tokens_in=tokens,
            )  # fmt: skip
    finally:
        conn.close()
    conn = queries.connect(path)
    try:
        away = queries.away(conn, PROJECT, SINCE, NOW)
    finally:
        conn.close()
    assert away.failed == 1
    assert round(away.claude_usd, 2) == 4.0  # 1M token-equivalents at $4 per 1M


def test_away_ticket_shows_agent_label_and_attempts(tmp_path):
    """A merged ticket by local-qwen3.6-35b-a3b after two developer jobs shows a
    "qwen3.6-35b-a3b" label and "2 attempts"; one by claude-opus after a failed
    developer job, "Opus" and "finished after 1 developer attempt"."""
    from factory_dashboard import queries

    path = tmp_path / "away-label.sqlite"
    conn = metrics.open_db(path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        m = metrics.upsert_milestone(conn, project, "f1")
        run = metrics.upsert_run(
            conn, project, "20261002-040000", started="2026-10-02T04:00:00+00:00"
        )

        def ticket(
            name: str, state: str, merged_by: str | None = None, kind: str = "developer"
        ) -> int:
            return metrics.upsert_ticket(
                conn,
                project,
                name,
                milestone_id=m,
                title=f"Title of {name}.",
                state=state,
                merged_by=merged_by,
                kind=kind,
            )

        def job(
            ticket_id: int,
            role: str,
            agent: str,
            attempt: int,
            started: str,
            ended: str,
            outcome: str,
        ) -> None:
            jid = metrics.start_job(
                conn,
                run,
                ticket_id=ticket_id,
                milestone_id=m,
                role=role,
                agent=agent,
                attempt=attempt,
                started=f"2026-10-02T{started}",
            )
            metrics.finish_job(conn, jid, ended=f"2026-10-02T{ended}", outcome=outcome)

        qwen_ticket = ticket("away-qwen", "done", LOCAL)
        opus_ticket = ticket("away-opus", "done", OPUS)
        opus_lead = ticket("away-lead", "done", OPUS, kind="lead")
        metrics.upsert_ticket(
            conn,
            project,
            "away-none",
            milestone_id=m,
            state="done",
            title="No merge title.",
        )

        # qwen: 2 developer jobs
        job(qwen_ticket, "developer", LOCAL, 1, "08:00:00", "08:10:00", "failed")
        job(qwen_ticket, "developer", LOCAL, 2, "08:10:00", "08:20:00", "passed")

        # opus: 1 developer job
        job(opus_ticket, "developer", LOCAL, 1, "09:00:00", "09:10:00", "failed")
        job(opus_ticket, "escalation", OPUS, 1, "09:30:00", "09:40:00", "passed")

        # opus lead ticket: no developer jobs
        job(opus_lead, "lead-ticket", OPUS, 1, "10:00:00", "10:10:00", "passed")

        # away-none has no merged_by, so no label
    finally:
        conn.close()
    conn = queries.connect(path)
    try:
        away = queries.away(conn, PROJECT, SINCE, NOW)
    finally:
        conn.close()

    merged_map = {t.ticket: t for t in away.merged}

    qwen = merged_map["away-qwen"]
    assert qwen.display_name == "qwen3.6-35b-a3b"
    assert qwen.attempts == 2
    assert qwen.kind == "developer"
    assert qwen.label == "2 attempts"

    opus = merged_map["away-opus"]
    assert opus.display_name == "Opus"
    assert opus.attempts == 1
    assert opus.kind == "developer"
    assert opus.label == "finished after 1 developer attempt"

    lead = merged_map["away-lead"]
    assert lead.display_name == "Opus"
    assert lead.attempts == 0
    assert lead.kind == "lead"
    assert lead.label == "lead ticket"


def test_away_blocked_ids_links_in_summary(tmp_path):
    """With one blocked ticket, the summary line links it by id."""
    from factory_dashboard import queries

    path = tmp_path / "away-blocked.sqlite"
    conn = metrics.open_db(path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        m = metrics.upsert_milestone(conn, project, "f1")
        run = metrics.upsert_run(
            conn, project, "20261002-040000", started="2026-10-02T04:00:00+00:00"
        )

        ticket_id = metrics.upsert_ticket(
            conn,
            project,
            "away-x",
            milestone_id=m,
            state="done",
            merged_by=LOCAL,
        )
        job_id = metrics.start_job(
            conn,
            run,
            ticket_id=ticket_id,
            milestone_id=m,
            role="developer",
            agent=LOCAL,
            attempt=1,
            started="2026-10-02T08:00:00+00:00",
        )
        metrics.finish_job(conn, job_id, ended="2026-10-02T08:10:00+00:00", outcome="passed")

        # Add a blocked ticket
        metrics.upsert_ticket(
            conn,
            project,
            "f9-15-away-who-did-it",
            milestone_id=m,
            state="blocked",
        )
    finally:
        conn.close()
    conn = queries.connect(path)
    try:
        away = queries.away(conn, PROJECT, SINCE, NOW)
    finally:
        conn.close()

    assert away.blocked == 1
    assert away.blocked_ids == ("f9-15-away-who-did-it",)


def test_away_no_merged_by_shows_no_label(client, db_path):
    """A ticket with no merged_by shows no label in the HTML."""
    conn = metrics.open_db(db_path)
    try:
        write_away(conn)
    finally:
        conn.close()
    since = datetime(2026, 10, 2, 8, 0, tzinfo=UTC)
    html = client.get("/?" + urlencode({"since": since.isoformat()})).text
    away_text = section(html, "away")
    # away-a has merged_by=LOCAL so it should show a label
    assert "qwen3.6-35b-a3b" in away_text
    # But no ticket with no merged_by should have an .agent span or label text
    from factory_dashboard import queries

    conn = queries.connect(db_path)
    try:
        aw = queries.away(conn, PROJECT, since, NOW)
    finally:
        conn.close()
    merged_names = {t.ticket for t in aw.merged}
    assert "away-none" not in merged_names


def test_away_developer_ticket_merged_by_opus_after_3_jobs(client, db_path):
    """A developer ticket merged by claude-opus after 3 developer jobs has the label
    'finished after 3 developer attempts', and 'Opus' appears once in its row on the page."""
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        run = metrics.upsert_run(
            conn, project, "20261002-050000", started="2026-10-02T05:00:00+00:00"
        )
        t = metrics.upsert_ticket(
            conn,
            project,
            "away-opus-3",
            milestone_id=f1,
            state="done",
            merged_by=OPUS,
            kind="developer",
            title="Opus merged after 3.",
        )
        for n in range(1, 4):
            jid = metrics.start_job(
                conn,
                run,
                ticket_id=t,
                milestone_id=f1,
                role="developer",
                agent=LOCAL,
                attempt=n,
                started=f"2026-10-02T09:{n:02d}:00+00:00",
            )
            metrics.finish_job(
                conn, jid, ended=f"2026-10-02T09:{n + 10:02d}:00+00:00", outcome="failed"
            )
        esc = metrics.start_job(
            conn,
            run,
            ticket_id=t,
            milestone_id=f1,
            role="escalation",
            agent=OPUS,
            attempt=1,
            started="2026-10-02T10:00:00+00:00",
        )
        metrics.finish_job(conn, esc, ended="2026-10-02T10:10:00+00:00", outcome="passed")
    finally:
        conn.close()
    since = datetime(2026, 10, 2, 8, 0, tzinfo=UTC)
    html = client.get("/?" + urlencode({"since": since.isoformat()})).text
    away_text = section(html, "away")
    assert "finished after 3 developer attempts" in away_text
    assert "Opus" in away_text
    # The label no longer contains the name; "Opus · " should not appear.
    assert "Opus · " not in away_text


def test_away_lead_ticket_shows_lead_ticket(client, db_path):
    """A lead ticket merged by claude-opus reads 'lead ticket' in the label,
    and 'Opus' appears once in the row."""
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        run = metrics.upsert_run(
            conn, project, "20261002-060000", started="2026-10-02T06:00:00+00:00"
        )
        t = metrics.upsert_ticket(
            conn,
            project,
            "away-lead-opus",
            milestone_id=f1,
            state="done",
            merged_by=OPUS,
            kind="lead",
            title="Lead ticket.",
        )
        jid = metrics.start_job(
            conn,
            run,
            ticket_id=t,
            milestone_id=f1,
            role="lead-ticket",
            agent=OPUS,
            attempt=1,
            started="2026-10-02T10:00:00+00:00",
        )
        metrics.finish_job(conn, jid, ended="2026-10-02T10:10:00+00:00", outcome="passed")
    finally:
        conn.close()
    since = datetime(2026, 10, 2, 8, 0, tzinfo=UTC)
    html = client.get("/?" + urlencode({"since": since.isoformat()})).text
    away_text = section(html, "away")
    assert "lead ticket" in away_text
    assert "Opus" in away_text
    # The label no longer contains the name; "Opus · " should not appear.
    assert "Opus · " not in away_text


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


def test_choosing_another_span_keeps_when_you_last_looked(client):
    """f3 review (f3-F3): each span chosen reloads the page, which set the cookie to now, so
    "since you last looked" lost the night after one choice."""
    looked = NOW.astimezone() - timedelta(hours=9)
    client.cookies.set("line_seen", looked.isoformat(timespec="seconds"))
    hour = client.get("/?" + urlencode({"since": (NOW - timedelta(hours=1)).isoformat()}))
    assert "line_seen" not in hour.cookies
    assert f">since you last looked ({looked:%H:%M})</option>" in hour.text
    assert "line_seen" in client.get("/").cookies  # opening the page plainly is looking


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
    assert "The away-b title." in away
    assert "finished after 1 developer attempt" in away
    assert "away-a" not in away and "away-early" not in away  # merged before 10:00
    assert "Nothing happened" not in away


def test_each_away_ticket_takes_the_panels_width(page, serve, db_path):
    """f3 review (f3-F7, f3-22's screenshots): each item sat in the 110 px "when" column of
    `.steps`, so one night's tickets made the Overview about 10,600 px tall."""
    conn = metrics.open_db(db_path)
    try:
        write_away(conn)
    finally:
        conn.close()
    page.set_viewport_size({"width": 1440, "height": 900})
    open_overview(page, serve())
    widths = page.eval_on_selector(
        "#away",
        """panel => {
            const inner = panel.clientWidth - parseFloat(getComputedStyle(panel).paddingLeft)
                - parseFloat(getComputedStyle(panel).paddingRight);
            return [...panel.querySelectorAll("li .what")].map(w => w.offsetWidth / inner);
        }""",
    )
    assert len(widths) == 3  # since 20:00 yesterday: away-early too
    assert all(share >= 0.8 for share in widths), widths


def test_the_away_panel_says_when_nothing_happened(client):
    since = NOW - timedelta(seconds=1)
    html = client.get("/?" + urlencode({"since": since.isoformat()})).text
    assert section(html, "away").endswith(f"Nothing happened since {since.astimezone():%H:%M}.")


def test_away_ticket_has_finished_and_took(tmp_path):
    """A developer ticket merged by claude-opus after 3 developer jobs has
    finished and took on the AwayTicket."""
    from factory_dashboard import queries

    path = tmp_path / "away-ft.sqlite"
    conn = metrics.open_db(path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        m = metrics.upsert_milestone(conn, project, "f1")
        run = metrics.upsert_run(
            conn, project, "20261002-040000", started="2026-10-02T04:00:00+00:00"
        )
        t = metrics.upsert_ticket(
            conn,
            project,
            "away-ft",
            milestone_id=m,
            state="done",
            merged_by=OPUS,
            kind="developer",
            title="Finished and took.",
        )
        for n in range(1, 4):
            jid = metrics.start_job(
                conn,
                run,
                ticket_id=t,
                milestone_id=m,
                role="developer",
                agent=LOCAL,
                attempt=n,
                started=f"2026-10-02T08:{(n - 1) * 10:02d}:00+00:00",
            )
            metrics.finish_job(
                conn,
                jid,
                ended=f"2026-10-02T08:{(n - 1) * 10 + 10:02d}:00+00:00",
                outcome="failed",
            )
        esc = metrics.start_job(
            conn,
            run,
            ticket_id=t,
            milestone_id=m,
            role="escalation",
            agent=OPUS,
            attempt=1,
            started="2026-10-02T08:30:00+00:00",
        )
        metrics.finish_job(conn, esc, ended="2026-10-02T08:30:00+00:00", outcome="passed")
    finally:
        conn.close()
    conn = queries.connect(path)
    try:
        away = queries.away(conn, PROJECT, SINCE, NOW)
    finally:
        conn.close()
    tkt = away.merged[0]
    assert tkt.ticket == "away-ft"
    assert tkt.finished is not None
    assert tkt.took is not None
    assert tkt.took == timedelta(minutes=30)


def test_finished_shows_time_when_same_day(client, db_path):
    """A ticket whose first job started at 08:00 and whose last job ended at 08:20
    the same day as now shows 'finished 08:20' and 'took 20 min'."""
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        run = metrics.upsert_run(
            conn, project, "20261002-040000", started="2026-10-02T04:00:00+00:00"
        )
        t = metrics.upsert_ticket(
            conn,
            project,
            "away-today",
            milestone_id=f1,
            state="done",
            merged_by=OPUS,
            kind="developer",
            title="Today finish.",
        )
        metrics.start_job(
            conn,
            run,
            ticket_id=t,
            milestone_id=f1,
            role="developer",
            agent=LOCAL,
            attempt=1,
            started="2026-10-02T08:00:00+00:00",
        )
        esc = metrics.start_job(
            conn,
            run,
            ticket_id=t,
            milestone_id=f1,
            role="escalation",
            agent=OPUS,
            attempt=1,
            started="2026-10-02T08:20:00+00:00",
        )
        metrics.finish_job(conn, esc, ended="2026-10-02T08:20:00+00:00", outcome="passed")
    finally:
        conn.close()
    since = datetime(2026, 10, 2, 8, 0, tzinfo=UTC)
    html = client.get("/?" + urlencode({"since": since.isoformat()})).text
    away = section(html, "away")
    finished_local = datetime(2026, 10, 2, 8, 20, tzinfo=UTC).astimezone()
    assert f"finished {finished_local.strftime('%H:%M')}" in away
    assert "took 20 min" in away


def test_finished_shows_day_when_different_day(client, db_path):
    """A ticket finished the day before now shows the day and month before the time."""
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        run = metrics.upsert_run(
            conn, project, "20261001-040000", started="2026-10-01T04:00:00+00:00"
        )
        t = metrics.upsert_ticket(
            conn,
            project,
            "away-yesterday",
            milestone_id=f1,
            state="done",
            merged_by=OPUS,
            kind="developer",
            title="Yesterday finish.",
        )
        metrics.start_job(
            conn,
            run,
            ticket_id=t,
            milestone_id=f1,
            role="developer",
            agent=LOCAL,
            attempt=1,
            started="2026-10-01T23:00:00+00:00",
        )
        esc = metrics.start_job(
            conn,
            run,
            ticket_id=t,
            milestone_id=f1,
            role="escalation",
            agent=OPUS,
            attempt=1,
            started="2026-10-01T12:00:00+00:00",
        )
        metrics.finish_job(conn, esc, ended="2026-10-01T12:00:00+00:00", outcome="passed")
    finally:
        conn.close()
    since = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
    html = client.get("/?" + urlencode({"since": since.isoformat()})).text
    away = section(html, "away")
    finished_local = datetime(2026, 10, 1, 12, 0, tzinfo=UTC).astimezone()
    assert f"finished {finished_local.strftime('%-d %b %H:%M')}" in away


def test_no_merged_by_shows_no_name_no_label_but_finished_and_took(client, db_path):
    """A ticket with no merged_by shows no name and no label, but its finished and took."""
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        run = metrics.upsert_run(
            conn, project, "20261002-040000", started="2026-10-02T04:00:00+00:00"
        )
        t = metrics.upsert_ticket(
            conn,
            project,
            "away-nomerge",
            milestone_id=f1,
            state="done",
            merged_by=None,
            kind="developer",
            title="No merge title.",
        )
        metrics.start_job(
            conn,
            run,
            ticket_id=t,
            milestone_id=f1,
            role="developer",
            agent=LOCAL,
            attempt=1,
            started="2026-10-02T08:00:00+00:00",
        )
        metrics.finish_job(
            conn,
            list(conn.execute("SELECT id FROM jobs WHERE ticket_id IS NOT NULL").fetchall())[-1][
                "id"
            ],
            ended="2026-10-02T08:10:00+00:00",
            outcome="passed",
        )
    finally:
        conn.close()
    # Re-fetch the job id properly
    conn = metrics.open_db(db_path)
    try:
        job = conn.execute(
            "SELECT id FROM jobs WHERE ticket_id IS NOT NULL ORDER BY id DESC LIMIT 1"
        ).fetchone()
        metrics.finish_job(conn, job["id"], ended="2026-10-02T08:10:00+00:00", outcome="passed")
    finally:
        conn.close()
    since = datetime(2026, 10, 2, 8, 0, tzinfo=UTC)
    html = client.get("/?" + urlencode({"since": since.isoformat()})).text
    away = section(html, "away")
    assert "finished" in away
    assert "took" in away


def test_how_comes_before_title_in_away_rows(client, db_path):
    """In the page, each row's class='how' element comes before its class='title' element."""
    conn = metrics.open_db(db_path)
    try:
        write_away(conn)
    finally:
        conn.close()
    since = datetime(2026, 10, 2, 8, 0, tzinfo=UTC)
    html = client.get("/?" + urlencode({"since": since.isoformat()})).text
    # Find each <li> in #away and verify .how comes before .title
    items = re.findall(r"<li>(.*?)</li>", html.split('id="away"')[1].split("</section>")[0], re.S)
    for item in items:
        how_idx = item.find('class="how"')
        title_idx = item.find('class="title"')
        assert how_idx != -1, "no class='how' in row"
        assert title_idx != -1, "no class='title' in row"
        assert how_idx < title_idx, f"how ({how_idx}) should come before title ({title_idx})"


def test_title_text_inside_title_only(client, db_path):
    """The title's text is inside class='title' only."""
    conn = metrics.open_db(db_path)
    try:
        write_away(conn)
    finally:
        conn.close()
    since = datetime(2026, 10, 2, 8, 0, tzinfo=UTC)
    html = client.get("/?" + urlencode({"since": since.isoformat()})).text
    # Find each <li> in #away and verify the title text is inside .title
    items = re.findall(r"<li>(.*?)</li>", html.split('id="away"')[1].split("</section>")[0], re.S)
    for item in items:
        title_match = re.search(r'<span class="title">([^<]*)</span>', item)
        assert title_match, "no .title span found"
        title_text = title_match.group(1)
        assert title_text, "title span should contain text"


def test_choosing_a_span_updates_away_in_place(page, serve, client, db_path):
    """f9-14: choosing 'the last hour' changes #away's 'since' time, keeps a value set on
    window before the change, and puts since in the address bar."""
    conn = metrics.open_db(db_path)
    try:
        write_away(conn)
    finally:
        conn.close()
    open_overview(page, serve())
    # Capture the original since time.
    original_away = page.locator("#away").inner_text()
    original_since_match = re.search(r"since (\d{2}:\d{2})", original_away, re.I)
    assert original_since_match, f"no since time in '{original_away}'"
    original_since = original_since_match.group(1)
    # Set a value on window before the change.
    page.evaluate("window._kept = 'preserved'")
    # Choose 'the last hour' without navigation.
    page.select_option("#replay-span", label="the last hour")
    page.wait_for_timeout(1000)
    # The address bar has since=.
    qs = parse_qs(urlsplit(page.url).query)
    assert "since" in qs
    assert datetime.fromisoformat(qs["since"][0]) == NOW - timedelta(hours=1)
    # Exactly one #away element (no nesting).
    assert page.locator("#away").count() == 1, (
        f"expected 1 #away element, got {page.locator('#away').count()}"
    )
    # #away's since time changed to the new time.
    away_section = page.locator("#away")
    away_text = away_section.inner_text()
    new_since_match = re.search(r"since (\d{2}:\d{2})", away_text, re.I)
    assert new_since_match, f"no since time in '{away_text}'"
    new_since = new_since_match.group(1)
    assert new_since != original_since, (
        f"since time should have changed from {original_since} to something else, got {new_since}"
    )
    # A value set on window before the change is kept.
    kept = page.evaluate("window._kept")
    assert kept == "preserved"


def test_replay_asks_new_since_after_span_change(page, serve, client, db_path):
    """f9-14: after choosing a span, the replay bar's data-replay has the new since,
    and clicking Replay requests /line/replay with that new since."""
    conn = metrics.open_db(db_path)
    try:
        write_away(conn)
    finally:
        conn.close()
    open_overview(page, serve())
    # Capture the original since from the page.
    original_page = page.evaluate("document.querySelector('.page[data-since]').dataset.since")
    # Choose 'the last hour'.
    page.select_option("#replay-span", label="the last hour")
    page.wait_for_timeout(1000)
    # The page's data-replay has the new since.
    new_since = page.evaluate("document.querySelector('.page[data-since]').dataset.replay")
    assert "since=" in new_since
    qs = parse_qs(urlsplit(new_since).query)
    assert datetime.fromisoformat(qs["since"][0]) == NOW - timedelta(hours=1)
    # The page's data-since also updated.
    page_since = page.evaluate("document.querySelector('.page[data-since]').dataset.since")
    assert page_since != original_page
    # Click Replay and capture the fetch URL.
    replay_url = [None]

    def handle_route(route):
        url = route.request.url
        if "/line/replay" in url:
            replay_url[0] = url
        route.fulfill(
            status=200,
            body='{"since":"2026-10-02T00:00:00+00:00","until":"2026-10-02T12:00:00+00:00","line":{},"events":[]}',
        )

    page.route("**/line/replay**", handle_route)
    page.click("#replay-start")
    page.wait_for_timeout(500)
    assert replay_url[0] is not None, "Replay button did not trigger /line/replay"
    replay_qs = parse_qs(urlsplit(replay_url[0]).query)
    assert "since" in replay_qs
    assert datetime.fromisoformat(replay_qs["since"][0]) == NOW - timedelta(hours=1)


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


def test_live_queue_matches_root(client):
    """The Queue rows in /live contain the same ticket IDs as on the main page,
    in the same order, read from the queue section (not split on "Next in line")."""
    root_html = client.get("/").text
    live_html = client.get("/live").text
    root_queue = section(root_html, "queue")
    live_queue = section(live_html, "queue")
    assert root_queue, "queue section should not be empty"
    assert live_queue, "live queue section should not be empty"
    root_ids = [t for _, t in re.findall(r"\b(\d) (f1-\d\d-[a-z-]+)", root_queue)]
    live_ids = [t for _, t in re.findall(r"\b(\d) (f1-\d\d-[a-z-]+)", live_queue)]
    assert root_ids == live_ids
    assert "f1-05-first" in root_ids
    assert "f1-06-second" in root_ids
    assert root_ids.index("f1-05-first") < root_ids.index("f1-06-second")


def test_next_in_line_says_why(queue_claude_client, db_path):
    """f4-39: each Next in line row whose ticket waits says what it waits for."""
    from runner import metrics

    conn = metrics.open_db(db_path)
    try:
        f1 = conn.execute(
            "SELECT id FROM milestones WHERE key = 'f1'",
        ).fetchone()["id"]
        proj = conn.execute(
            "SELECT id FROM projects WHERE name = ?",
            (PROJECT,),
        ).fetchone()["id"]
        for tid in ("f1-05-first", "f1-06-second", "f1-10-queued", "f1-11-waits-done"):
            metrics.upsert_ticket(conn, proj, tid, milestone_id=f1, state="done")
    finally:
        conn.close()

    html = queue_claude_client.get("/live").text
    queue_section = section(html, "queue")
    next_section = queue_section.split("Next in line", 1)[1]
    # f1-14-lead: lead ticket, waiting for Claude
    assert "f1-14-lead" in next_section
    assert "waits for Claude" in next_section
    # f1-12-waits-running: depends on f1-04-live (running)
    assert "f1-12-waits-running" in next_section
    assert "waits for f1-04-live" in next_section
    # f1-13-waits-escalated: depends on f1-12-escalated (escalated)
    assert "f1-13-waits-escalated" in next_section
    assert "waits for f1-12-escalated's escalation" in next_section
    # No row carries another ticket's reason
    for ticket, reason in [
        ("f1-14-lead", "waits for Claude"),
        ("f1-12-waits-running", "waits for f1-04-live"),
        ("f1-13-waits-escalated", "waits for f1-12-escalated's escalation"),
    ]:
        rows = next_section.split("next-row")
        for row in rows:
            if ticket in row:
                assert reason in row, f"{ticket} row should show '{reason}'"


def test_next_in_line_no_waits_without_claude(queue_client, db_path):
    """f4-39: with queue_client (no Claude waiting), no Next in line row says 'waits for'."""
    html = queue_client.get("/live").text
    queue_section = section(html, "queue")
    next_section = queue_section.split("Next in line", 1)[1]
    assert "waits for" not in next_section


def test_live_queue_updates_between_polls(queue_client, db_path):
    """A ticket added to the database appears in the Queue on the next /live poll."""
    client = queue_client
    # Capture the queue count from the queue section before insertion.
    before_html = client.get("/live").text
    before_queue = section(before_html, "queue")
    before_match = re.search(r"(\d+) ticket", before_queue)
    assert before_match, "Queue count not found"
    before_count = int(before_match.group(1))
    # Insert a new queued ticket.
    conn = metrics.open_db(db_path)
    try:
        proj = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()["id"]
        f1 = conn.execute("SELECT id FROM milestones WHERE key = 'f1'").fetchone()["id"]
        metrics.upsert_ticket(
            conn,
            proj,
            "f1-99-new",
            milestone_id=f1,
            kind="developer",
            state="ready",
            title="New queued",
        )
    finally:
        conn.close()
    # Capture after insertion.
    after_html = client.get("/live").text
    after_queue = section(after_html, "queue")
    after_match = re.search(r"(\d+) ticket", after_queue)
    assert after_match, "Queue count not found after insertion"
    after_count = int(after_match.group(1))
    assert after_count == before_count + 1, (
        f"expected queue count to increase from {before_count} to {before_count + 1}, "
        f"got {after_count}"
    )
    # Verify the new ticket is in the queue (more items may exist than "Next in line" shows).
    conn = metrics.open_db(db_path)
    try:
        queue_items = list(queue(conn, PROJECT, NOW))
        tickets = [q.ticket for q in queue_items]
        assert "f1-99-new" in tickets, "f1-99-new not in queue"
    finally:
        conn.close()


def test_running_and_queue_share_a_row_on_root(client):
    """On the root page the Running and Queue sections are inside the same .row container."""
    html = client.get("/").text
    # Find the .row that contains id="now" and verify id="queue" is inside it.
    now_idx = html.index('id="now"')
    row_start = html.rfind('<div class="row">', 0, now_idx)
    assert row_start != -1, "no .row before now"
    depth = 1
    pos = row_start
    while depth > 0:
        next_close = html.find("</div>", pos + 1)
        if next_close == -1:
            break
        next_open = html.find("<div", pos + 1, next_close)
        if next_open != -1 and next_open < next_close:
            depth += 1
            pos = next_open
        else:
            depth -= 1
            pos = next_close
    row_content = html[row_start : pos + 7]
    assert 'id="queue"' in row_content, "Queue not in same .row as Running"


# --- allowance bars on phone (f9-17) -----------------------------------------------------------


def test_allowance_bars_one_row_per_window_at_phone(page, allowance_client):
    """f9-17: at 390 px each window is one row with its name, its bar and its reset text,
    and no ``.dial`` is in the page."""
    ORIGIN = "http://127.0.0.1:8765"

    def serve(route) -> None:
        url = route.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            route.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        elif path in ("/", "/live"):
            body = allowance_client.get(url).text
            route.fulfill(body=body, content_type="text/html; charset=utf-8")
        else:
            route.fulfill(status=404, body="")

    page.route(f"{ORIGIN}/**", serve)
    page.set_viewport_size({"width": 390, "height": 1200})
    page.goto(ORIGIN + "/")
    page.wait_for_selector("#allowance .allow > div")

    # No dial SVG should exist
    assert page.locator("#allowance .dial").count() == 0

    # Each window is one row: name + bar + reset text
    rows = page.locator("#allowance .allow > div").all()
    assert len(rows) >= 2
    for row in rows:
        assert row.locator(".agent").count() == 1
        assert row.locator(".meter").count() == 1
        assert row.locator(".line small").count() >= 1

    # Layout check passes at 390 px
    assert layout_problems(page) == []


def test_allowance_bar_colours_match_at_phone_and_desktop(page, allowance_client, db_path):
    """f9-17: at 390 px a window under its mark, one past it and one above 95% have three
    different bar colours, each the same as that window's bar at 1440 px."""
    # Guarantee a nearly-out reading so three colours are present.
    conn = metrics.open_db(db_path)
    try:
        conn.execute(
            "DELETE FROM usage_events WHERE kind = 'reading' AND agent = 'copilot-auto'",
        )
        metrics.add_usage_event(
            conn,
            "copilot-auto",
            NOW.isoformat(),
            "reading",
            window="month",
            value=0.97,
            resets_at=(NOW + timedelta(days=30)).isoformat(),
        )
    finally:
        conn.close()

    ORIGIN = "http://127.0.0.1:8765"

    def serve(route) -> None:
        url = route.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            route.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        elif path in ("/", "/live"):
            body = allowance_client.get(url).text
            route.fulfill(body=body, content_type="text/html; charset=utf-8")
        else:
            route.fulfill(status=404, body="")

    page.route(f"{ORIGIN}/**", serve)

    # Desktop: capture bar colours at 1440 px
    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto(ORIGIN + "/")
    page.wait_for_selector("#allowance .meter > span")

    desktop_colors = page.eval_on_selector_all(
        "#allowance .meter > span",
        "els => els.map(e => getComputedStyle(e).backgroundColor)",
    )

    # Phone: capture bar colours at 390 px
    page.set_viewport_size({"width": 390, "height": 1200})
    page.goto(ORIGIN + "/")
    page.wait_for_selector("#allowance .meter > span")

    phone_colors = page.eval_on_selector_all(
        "#allowance .meter > span",
        "els => els.map(e => getComputedStyle(e).backgroundColor)",
    )

    assert len(desktop_colors) >= 3
    assert len(phone_colors) >= 3

    # Three different colours among the bars
    assert len(set(desktop_colors)) >= 3, (
        f"expected at least 3 different colours at desktop, got {desktop_colors}"
    )
    assert len(set(phone_colors)) >= 3, (
        f"expected at least 3 different colours at phone, got {phone_colors}"
    )

    # Same colours at both sizes (same order)
    for i, (d, p) in enumerate(zip(desktop_colors, phone_colors, strict=True)):
        assert d == p, f"row {i} colour differs: desktop={d}, phone={p}"

    # Each phone bar with usage is visible (non-zero width)
    desktop_widths = page.eval_on_selector_all(
        "#allowance .meter > span",
        "els => els.map(e => e.offsetWidth)",
    )
    widths = page.eval_on_selector_all(
        "#allowance .meter > span",
        "els => els.map(e => e.offsetWidth)",
    )
    for dw, w in zip(desktop_widths, widths, strict=True):
        if dw > 0:
            assert w > 0, f"bar with usage has width {w} at 390 px (desktop width {dw})"


def test_replay_bar_is_just_below_the_floor_on_phone(page, serve, db_path):
    """f9-26: at 390 px the replay bar's top is within 40 px of the floor's bottom."""
    conn = metrics.open_db(db_path)
    try:
        write_away(conn)
    finally:
        conn.close()

    ORIGIN = "http://127.0.0.1:8765"

    def serve_route(route) -> None:
        url = route.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            route.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        elif path in ("/", "/live"):
            body = serve().get(url).text
            route.fulfill(body=body, content_type="text/html; charset=utf-8")
        else:
            route.fulfill(status=404, body="")

    page.route(f"{ORIGIN}/**", serve_route)
    page.set_viewport_size({"width": 390, "height": 1200})
    page.goto(ORIGIN + "/")
    page.wait_for_selector("#replay")

    floor_box = page.locator("#floor-phone").bounding_box()
    replay_box = page.locator("#replay").bounding_box()
    assert floor_box and replay_box
    gap = replay_box["y"] - (floor_box["y"] + floor_box["height"])
    floor_bottom = floor_box["y"] + floor_box["height"]
    assert gap < 40, (
        f"replay top ({replay_box['y']}) should be "
        f"within 40 px of floor bottom ({floor_bottom}), gap is {gap}"
    )


def test_allowance_legend_names_bar_mark(allowance_client):
    """f9-17: the legend explains the mark's meaning, not a ring."""
    panel = re.search(
        r'<section[^>]*\bid="allowance"[^>]*>(.*?)</section>',
        allowance_client.get("/").text,
        re.S,
    )
    assert panel
    legend_text = " ".join(re.sub(r"<[^>]+>", " ", panel.group(1)).split())
    assert "ring" not in legend_text.lower()
    # Must mention the mark and something meaningful about it (factory / owner / stops).
    assert "mark" in legend_text.lower()
    assert (
        "factory" in legend_text.lower()
        or "owner" in legend_text.lower()
        or "stop" in legend_text.lower()
    )


def test_allowance_legend_has_use_reserve_line(allowance_client):
    """f8-14: the legend includes the "use reserve" explanation."""
    panel = re.search(
        r'<section[^>]*\bid="allowance"[^>]*>(.*?)</section>',
        allowance_client.get("/").text,
        re.S,
    )
    assert panel
    legend_text = " ".join(re.sub(r"<[^>]+>", " ", panel.group(1)).split())
    assert "use reserve" in legend_text.lower()
    assert "24 hours" in legend_text


def test_no_data_yet_has_empty_bar(page, serve, db_path):
    """'no data yet' shows an empty bar (width 0)."""
    conn = metrics.open_db(db_path)
    try:
        conn.execute("DELETE FROM usage_events WHERE kind = 'reading'")
        conn.commit()
    finally:
        conn.close()

    ORIGIN = "http://127.0.0.1:8765"

    def serve_route(route) -> None:
        url = route.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            route.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        elif path in ("/", "/live"):
            body = serve().get(url).text
            route.fulfill(body=body, content_type="text/html; charset=utf-8")
        else:
            route.fulfill(status=404, body="")

    page.route(f"{ORIGIN}/**", serve_route)
    page.set_viewport_size({"width": 390, "height": 1200})
    page.goto(ORIGIN + "/")
    page.wait_for_selector("#allowance .allow > div")

    # Check that at least one bar has width 0
    bars = page.locator("#allowance .meter > span").all()
    assert len(bars) >= 2
    found_empty = False
    for bar in bars:
        width = bar.evaluate("el => el.offsetWidth")
        if width == 0:
            found_empty = True
            break
    assert found_empty, "no bar with width 0 found"


def test_queued_checkpoint_comes_before_tickets_and_shows_reason(client, db_path):
    """A queued checkpoint row comes first, before every ticket, with its reason."""
    from factory_dashboard.overview import queued_jobs

    conn = metrics.open_db(db_path)
    try:
        project = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()[
            "id"
        ]
        now_iso = NOW.isoformat()
        metrics.queue_job(conn, project, "checkpoint", "f1", "Checkpoint reason", now_iso)
    finally:
        conn.close()

    html = client.get("/live").text
    queue_section = section(html, "queue")
    next_section = queue_section.split("Next in line", 1)[1]
    assert "Checkpoint:" in next_section
    assert "Checkpoint reason" in next_section
    # The checkpoint row comes before any ticket row in the rendered HTML
    ticket_rows = [m for m in re.findall(r"\b\d (f1-\d\d-[a-z-]+)", next_section)]
    assert len(ticket_rows) >= 2
    # Find the checkpoint row and verify it precedes all ticket rows
    checkpoint_idx = next_section.find("Checkpoint:")
    ticket_indices = [next_section.find(t) for t in ticket_rows]
    for idx in ticket_indices:
        assert checkpoint_idx < idx, (
            f"Checkpoint row at {checkpoint_idx} should come before ticket row at {idx}"
        )
    # queued_jobs returns them in dispatch order: checkpoint before tickets
    conn = metrics.open_db(db_path)
    try:
        jobs = queued_jobs(conn, PROJECT, NOW)
    finally:
        conn.close()
    assert len(jobs) >= 1


def test_queued_checkpoint_with_running_started_job_is_not_in_queue(client, db_path):
    """f8-13: a queued job whose started_job is still running is left out of the queue."""
    from runner import metrics

    conn = metrics.open_db(db_path)
    try:
        # Get a running job id from the fixture's database.
        running_job = conn.execute(
            "SELECT j.id FROM jobs j "
            "JOIN runs r ON r.id = j.run_id "
            "JOIN projects p ON p.id = r.project_id "
            "WHERE p.name = ? AND j.outcome = 'running' "
            "LIMIT 1",
            (PROJECT,),
        ).fetchone()
        assert running_job, "no running job in fixture"
        running_job_id = running_job["id"]
        # Queue a checkpoint and set its started_job to the running job.
        project = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()[
            "id"
        ]
        now_iso = NOW.isoformat()
        metrics.queue_job(conn, project, "checkpoint", "f1", "Should not show", now_iso)
        row = conn.execute(
            "SELECT id FROM work_queue "
            "WHERE kind = 'checkpoint' AND subject = 'f1' "
            "AND done IS NULL"
        ).fetchone()
        conn.execute(
            "UPDATE work_queue SET started_job = ? WHERE id = ?",
            (running_job_id, row["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    html = client.get("/live").text
    queue_section = section(html, "queue")
    next_section = queue_section.split("Next in line", 1)[1]
    # The checkpoint should NOT appear in the queue.
    assert "Should not show" not in next_section
    assert "Checkpoint:" not in next_section

    # queued_jobs also excludes it.
    conn = metrics.open_db(db_path)
    try:
        jobs = queued_jobs(conn, PROJECT, NOW)
    finally:
        conn.close()
    kinds = [j.kind for j in jobs]
    assert "Checkpoint" not in kinds


def test_queued_checkpoint_with_finished_started_job_is_in_queue(client, db_path):
    """f8-13: a queued job whose started_job is finished is listed with its reason."""
    from runner import metrics

    conn = metrics.open_db(db_path)
    try:
        # Get a passed (finished) job id from the fixture's database.
        finished_job = conn.execute(
            "SELECT j.id FROM jobs j "
            "JOIN runs r ON r.id = j.run_id "
            "JOIN projects p ON p.id = r.project_id "
            "WHERE p.name = ? AND j.outcome = 'passed' "
            "LIMIT 1",
            (PROJECT,),
        ).fetchone()
        assert finished_job, "no passed job in fixture"
        finished_job_id = finished_job["id"]
        # Queue a checkpoint and set its started_job to the finished job.
        project = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()[
            "id"
        ]
        now_iso = NOW.isoformat()
        metrics.queue_job(conn, project, "checkpoint", "f1", "Should show", now_iso)
        row = conn.execute(
            "SELECT id FROM work_queue "
            "WHERE kind = 'checkpoint' AND subject = 'f1' "
            "AND done IS NULL"
        ).fetchone()
        conn.execute(
            "UPDATE work_queue SET started_job = ? WHERE id = ?",
            (finished_job_id, row["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    html = client.get("/live").text
    queue_section = section(html, "queue")
    next_section = queue_section.split("Next in line", 1)[1]
    # The checkpoint SHOULD appear in the queue with its reason.
    assert "Should show" in next_section
    assert "Checkpoint:" in next_section

    # queued_jobs includes it.
    conn = metrics.open_db(db_path)
    try:
        jobs = queued_jobs(conn, PROJECT, NOW)
    finally:
        conn.close()
    kinds = [j.kind for j in jobs]
    assert "Checkpoint" in kinds


def test_escalation_comes_before_checkpoint(client, db_path):
    """A queued escalation comes before an older queued checkpoint."""
    from factory_dashboard.overview import queued_jobs

    conn = metrics.open_db(db_path)
    try:
        project = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()[
            "id"
        ]
        # Escalation created first (older)
        metrics.queue_job(
            conn, project, "escalation", "f1", "Escalation reason", "2026-10-01T10:00:00+00:00"
        )
        # Checkpoint created later (newer)
        metrics.queue_job(
            conn, project, "checkpoint", "f1", "Checkpoint reason", "2026-10-02T10:00:00+00:00"
        )
    finally:
        conn.close()

    conn = metrics.open_db(db_path)
    try:
        jobs = queued_jobs(conn, PROJECT, NOW)
    finally:
        conn.close()
    kinds = [j.kind for j in jobs]
    # Escalation should come before checkpoint in dispatch order
    esc_idx = kinds.index("Escalation")
    cp_idx = kinds.index("Checkpoint")
    assert esc_idx < cp_idx, f"Escalation ({esc_idx}) should come before Checkpoint ({cp_idx})"


def test_future_not_before_says_waits_until(client, db_path):
    """A row with not_before in the future says "waits until" and that time."""
    conn = metrics.open_db(db_path)
    try:
        project = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()[
            "id"
        ]
        # not_before is after NOW (2026-10-02 12:00 UTC)
        metrics.queue_job(
            conn,
            project,
            "checkpoint",
            "f1",
            "A checkpoint",
            "2026-10-02T10:00:00+00:00",
            not_before="2026-10-05T17:00:00+00:00",
        )
    finally:
        conn.close()

    html = client.get("/live").text
    queue_section = section(html, "queue")
    next_section = queue_section.split("Next in line", 1)[1]
    assert "waits until" in next_section
    # The displayed time matches the not_before value (Mon 5 Oct 17:00)
    assert "Mon 5 Oct 17:00" in next_section


def test_done_row_isnt_shown(client, db_path):
    """A done queued job row isn't shown."""
    from factory_dashboard.overview import queued_jobs

    conn = metrics.open_db(db_path)
    try:
        project = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()[
            "id"
        ]
        now_iso = NOW.isoformat()
        metrics.queue_job(conn, project, "checkpoint", "f1", "A checkpoint", now_iso)
        # Mark it done
        conn.execute(
            "UPDATE work_queue SET done = ? WHERE kind = 'checkpoint' AND subject = 'f1'"
            " AND done IS NULL",
            (now_iso,),
        )
        conn.commit()
    finally:
        conn.close()

    conn = metrics.open_db(db_path)
    try:
        jobs = queued_jobs(conn, PROJECT, NOW)
    finally:
        conn.close()
    assert len(jobs) == 0
    # The done row is absent from rendered HTML, not just the helper result
    html = client.get("/live").text
    queue_section = section(html, "queue")
    assert "A checkpoint" not in queue_section


def lead_replies(db_path: Path, *cards: str) -> None:
    """A thread per card whose last message is the lead's, each raising its ``planning`` owner
    item as the runner does (f6-09)."""
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        for card in cards:
            thread = metrics.planner_thread(conn, project, card, NOW.isoformat())
            metrics.add_planner_message(conn, thread["id"], "lead", NOW.isoformat(), "A reply.")
            text = f"The lead answered your message on {card.upper()}."
            metrics.upsert_owner_item(conn, project, "planning", card, text=text)
    finally:
        conn.close()


def planning_tab(html: str) -> str:
    match = re.search(r'<a [^>]*id="planning-tab"[^>]*>(.*?)</a>', html, re.S)
    assert match, "no Planning tab"
    return " ".join(match.group(1).split())


def test_three_desk_items_show_their_count_links_and_tab(serve_between, db_path):
    client = serve_between()
    sign_off_all(db_path)
    lead_replies(db_path, "f7", "f8", "f9")
    for html in (client.get("/").text, client.get("/live").text):
        needs = section(html, "needs-you")
        assert "3 things wait for you on your desk" in needs
        assert "Open your desk ›" in needs
        entry = html.split('id="desk-entry"')[1].split("</li>")[0]
        links = re.findall(r'href="/planning/(f\d)\?', entry)
        assert links == ["f7", "f8", "f9"]
        assert planning_tab(html) == "Planning · 3"


def test_a_lead_reply_shows_once_in_the_desk_entry(serve_between, db_path):
    client = serve_between()
    sign_off_all(db_path)
    lead_replies(db_path, "f7")
    html = client.get("/live").text
    needs = section(html, "needs-you")
    assert "1 thing waits for you on your desk" in needs
    assert "The lead answered" not in needs and "planning" not in needs  # the entry stands for it
    assert "The lead answered" in html.split('id="live-facts"')[1]  # notify.js still tells it


def test_a_signoff_on_a_ripe_milestone_shows_once_in_the_desk_entry(serve_between, db_path):
    """f95-01: a sign-off for a milestone on the desk's "Finished, to talk through" shows
    through the desk's entry only, never as a separate row."""
    client = serve_between()
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_owner_item(
            conn, project, "signoff", "f1", text="softfield signoff f1", created=NOW.isoformat()
        )
    finally:
        conn.close()
    html = client.get("/live").text
    needs = section(html, "needs-you")
    assert "signoff" not in needs.lower()  # no separate signoff row
    assert "softfield signoff f1" not in needs
    # the sign-off item still carries in data-needs for notify.js
    facts = html.split('id="live-facts"')[1]
    assert "signoff" in facts.lower()


def test_a_signoff_on_a_milestone_off_the_desk_shows_no_row(client, db_path):
    """f95-01: a stored sign-off for a milestone not on the desk (it got a ready ticket since
    its verdict) shows no row: the desk is the one place a sign-off shows."""
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        m = metrics.upsert_milestone(
            conn,
            project,
            "f95-test",
            title="Test milestone",
            status="in progress",
            started=(NOW - timedelta(days=1)).isoformat(),
        )
        metrics.upsert_ticket(
            conn,
            project,
            "f95-test-01",
            milestone_id=m,
            kind="developer",
            state="ready",
            title="A ready ticket.",
        )
        metrics.upsert_owner_item(
            conn,
            project,
            "signoff",
            "f95-test",
            text="softfield signoff f95-test",
            created=NOW.isoformat(),
        )
    finally:
        conn.close()
    html = client.get("/live").text
    needs = section(html, "needs-you")
    assert "softfield signoff f95-test" not in needs


def test_other_kinds_still_show_with_their_command(client, db_path):
    """Items of other kinds (adr, reserve) still show; blocked does not (the desk counts it)."""
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_owner_item(
            conn,
            project,
            "adr",
            "ADR 42",
            text="An ADR question.",
            command="softfield adr 42",
            created=NOW.isoformat(),
        )
        metrics.upsert_owner_item(
            conn,
            project,
            "blocked",
            "f95-02",
            text="Blocked on external.",
            command="softfield unblock f95-02",
            created=NOW.isoformat(),
        )
        metrics.upsert_owner_item(
            conn,
            project,
            "reserve",
            "f-reserve",
            text="A reserve item.",
            command="softfield reserve f-reserve",
            created=NOW.isoformat(),
        )
    finally:
        conn.close()
    html = client.get("/live").text
    needs = section(html, "needs-you")
    assert "softfield adr 42" in needs
    assert "softfield unblock f95-02" not in needs
    assert "softfield reserve f-reserve" in needs


def test_data_needs_carries_signoff_item_for_notify(client, db_path):
    """data-needs on #live-facts still carries the signoff item so notify.js can compare."""
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_owner_item(
            conn,
            project,
            "signoff",
            "f1",
            text="softfield signoff f1",
            created=NOW.isoformat(),
        )
    finally:
        conn.close()
    html = client.get("/live").text
    # The signoff item is in data-needs even though filtered from needs-you
    facts = html.split('id="live-facts"')[1]
    match = re.search(r"data-needs='([^']*)'", facts)
    assert match, "no data-needs attribute"
    needs_data = json.loads(match[1])
    assert "softfield signoff f1" in needs_data.values()


def test_an_empty_desk_has_no_entry_and_a_plain_tab(serve_between, db_path):
    client = serve_between()
    sign_off_all(db_path)
    for html in (client.get("/").text, client.get("/live").text):
        assert 'id="desk-entry"' not in html
        assert planning_tab(html) == "Planning"


def test_planning_row_shows_first_60_chars_and_title(client, db_path):
    """A planner row for a 100-character message: first 60 chars + …, title holds all 100,
    link is /planning/f11."""
    from runner import metrics

    conn = metrics.open_db(db_path)
    try:
        project = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()[
            "id"
        ]
        # Insert an owner_requests row with a 100-char message
        long_text = "a" * 100
        conn.execute(
            "INSERT INTO owner_requests (project_id, kind, subject, value, created)"
            " VALUES (?, 'plan_message', ?, ?, ?)",
            (project, "f11#1", json.dumps({"text": long_text, "comments": {}}), NOW.isoformat()),
        )
        conn.commit()
        # Queue a planner job referencing that request
        metrics.queue_job(conn, project, "planner", "f11#1", "A message", NOW.isoformat())
    finally:
        conn.close()

    html = client.get("/live").text
    queue_section = section(html, "queue")
    next_section = queue_section.split("Next in line", 1)[1]
    # The row should contain Planning:
    assert "Planning:" in next_section
    # Find the planning row in raw HTML (href/title can't be found in stripped text)
    planning_row = html.split("Planning:")[1].split("</div>")[0]
    assert 'href="/planning/f11"' in planning_row
    # Title attribute is on the <div>, find it from the full row
    next_html = html.split("Next in line", 1)[1]
    title_match = re.search(r'<div class="next-row" title="([^"]*)"[^>]*>.*?Planning:', next_html)
    assert title_match
    assert title_match.group(1) == long_text
    # Visible text: first 60 chars + …
    row_text = " ".join(unescape(re.sub(r"<[^>]+>", " ", planning_row)).split())
    expected_preview = "a" * 60 + "…"
    assert expected_preview in row_text


def test_planning_row_with_empty_text_shows_first_comment(client, db_path):
    """A planner row with no text shows its first comment."""
    from runner import metrics

    conn = metrics.open_db(db_path)
    try:
        project = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()[
            "id"
        ]
        # Insert an owner_requests row with empty text but a comment
        conn.execute(
            "INSERT INTO owner_requests (project_id, kind, subject, value, created)"
            " VALUES (?, 'plan_message', ?, ?, ?)",
            (
                project,
                "f11#1",
                json.dumps({"text": "", "comments": {"2": "First comment."}}),
                NOW.isoformat(),
            ),
        )
        conn.commit()
        metrics.queue_job(conn, project, "planner", "f11#1", "A message", NOW.isoformat())
    finally:
        conn.close()

    html = client.get("/live").text
    queue_section = section(html, "queue")
    next_section = queue_section.split("Next in line", 1)[1]
    assert "First comment." in next_section
    # Title attribute is on the <div>, find it from the full row
    next_html = html.split("Next in line", 1)[1]
    title_match = re.search(r'<div class="next-row" title="([^"]*)"[^>]*>.*?Planning:', next_html)
    assert title_match
    assert title_match.group(1) == "First comment."


def test_open_plant_shows_plant_row(client, db_path):
    """An open plant request shows a Plant: <title> row."""
    from runner import metrics

    conn = metrics.open_db(db_path)
    try:
        project = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()[
            "id"
        ]
        conn.execute(
            "INSERT INTO owner_requests (project_id, kind, value, created)"
            " VALUES (?, 'plant', ?, ?)",
            (
                project,
                json.dumps({"title": "A new plant", "thoughts": "Thoughts here."}),
                NOW.isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    html = client.get("/live").text
    queue_section = section(html, "queue")
    next_section = queue_section.split("Next in line", 1)[1]
    assert "Plant:" in next_section
    assert "A new plant" in next_section
    plant_row = html.split("A new plant")[1].split("</div>")[0]
    row_text = " ".join(unescape(re.sub(r"<[^>]+>", " ", plant_row)).split())
    assert "at the runner's next pick" in row_text


def test_done_plant_shows_no_row(client, db_path):
    """A done plant request shows no row."""
    from runner import metrics

    conn = metrics.open_db(db_path)
    try:
        project = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()[
            "id"
        ]
        conn.execute(
            "INSERT INTO owner_requests (project_id, kind, value, created, done)"
            " VALUES (?, 'plant', ?, ?, ?)",
            (
                project,
                json.dumps({"title": "Done plant", "thoughts": "Done thoughts."}),
                NOW.isoformat(),
                NOW.isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    html = client.get("/live").text
    queue_section = section(html, "queue")
    next_section = queue_section.split("Next in line", 1)[1]
    assert "Done plant" not in next_section


def _next_in_line(client) -> str:
    html: str = client.get("/live").text
    return html.split("Next in line", 1)[1].split("</section>", 1)[0]


def _plants(db_path: Path, *changes: tuple[int, str]) -> None:
    """Two open plants, and a ``change`` on the first (0) or the second (1) for each given."""
    conn = metrics.open_db(db_path)
    try:
        project = conn.execute("SELECT id FROM projects WHERE name = ?", (PROJECT,)).fetchone()[0]
        ids = [
            metrics.add_request(conn, project, "plant", None, value, NOW.isoformat())
            for value in (
                json.dumps({"text": "Calm colours", "ask": True}),
                json.dumps({"title": "Rubber ducks", "thoughts": "Yellow ones."}),
            )
        ]
        for which, value in changes:
            metrics.add_request(conn, project, "change", str(ids[which]), value, NOW.isoformat())
    finally:
        conn.close()


def _plant_rows(markup: str) -> list[str]:
    rows = re.findall(r'<div class="next-row">(.*?)</div>', markup, re.S)
    return [" ".join(unescape(re.sub(r"<[^>]+>", " ", r)).split()) for r in rows if "Plant:" in r]


def test_an_edited_plant_shows_its_new_title_in_next_in_line(client, db_path):
    """F14: the Now page shows the change as the desk does; the other plant is as it was."""
    _plants(db_path, (0, json.dumps({"text": "Calmer colours"})))
    markup = _next_in_line(client)
    assert _plant_rows(markup) == [
        "Plant: Calmer colours · changed · at the runner's next pick",
        "Plant: Rubber ducks · at the runner's next pick",
    ]
    assert "<s>" not in markup


def test_a_cancelled_plant_is_struck_through_in_next_in_line(client, db_path):
    _plants(db_path, (1, '{"cancel": true}'))
    markup = _next_in_line(client)
    assert _plant_rows(markup) == [
        "Plant: Calm colours · at the runner's next pick",
        "Plant: Rubber ducks · cancelling at the runner's next pick",
    ]
    assert re.findall(r"<s>(.*?)</s>", markup) == ["Rubber ducks"]
