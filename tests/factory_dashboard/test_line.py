"""The factory line (f3 D11): the trips ``line.trips`` reads from the jobs, the document
``line.live_line`` builds, the page that carries it, and what ``static/factory.js`` draws from
it in a browser.

The browser test is the pattern for the factory's tickets: render the page with the
``TestClient``, then open it in pytest-playwright's ``page`` with ``/static/`` served from disk
(``page.route``), and assert on what is drawn.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from factory_dashboard.line import BELTS, STATIONS, live_line, trips
from factory_dashboard.queries import connect
from runner import metrics
from tests.factory_dashboard.conftest import LINE_NOW, LOCAL, NOW, OPUS, PROJECT, SONNET

STATIC = Path(__file__).resolve().parents[2] / "factory_dashboard" / "static"
COPILOT, GPT_OSS = "copilot-auto", "ollama-gpt-oss-120b"


def at(clock: str) -> str:
    return f"2026-09-30T{clock}:00+02:00"


def journey(db: Path, crate: str) -> list[tuple[str, list[str], str | None]]:
    conn = connect(db)
    try:
        found = trips(conn, PROJECT)
    finally:
        conn.close()
    return [(t.at.isoformat(), list(t.belts), t.to) for t in found if t.crate == crate]


def document(db: Path, now: datetime = LINE_NOW, project: str = PROJECT) -> dict[str, Any]:
    conn = connect(db)
    try:
        return live_line(conn, project, now)
    finally:
        conn.close()


def machines(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {m["id"]: m for m in doc["machines"]}


def belts(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {b["id"]: b for b in doc["belts"]}


# --- the trips ------------------------------------------------------------------------------


def test_a_developer_ticket_that_fails_once_gets_a_direction_and_passes(line_db):
    assert journey(line_db, "f5-01-retry") == [
        (at("10:00"), ["queue→developers"], "developers"),
        (at("10:20"), ["developers→checks"], "checks"),
        (at("10:21"), ["checks→lead"], "lead"),
        (at("10:25"), [], "developers"),  # a direction: text, simply moved
        (at("10:50"), ["developers→checks", "checks→merged"], "merged"),
    ]


def test_a_lead_ticket_parked_by_a_limit_goes_back_to_the_queue_and_comes_back(line_db):
    assert journey(line_db, "f5-02-parked") == [
        (at("10:55"), ["queue→lead"], "lead"),
        (at("11:00"), [], "queue"),
        (at("11:45"), ["queue→lead"], "lead"),
        (at("12:05"), ["lead→checks", "checks→merged"], "merged"),
    ]


def test_a_checkpoint_is_a_batch_crate_from_merged_to_the_reviewers(line_db):
    conn = connect(line_db)
    try:
        found = trips(conn, PROJECT)
    finally:
        conn.close()
    # f5's checkpoint on Sonnet and its shadow on Copilot
    names = sorted(t.crate for t in found if t.at.isoformat() == at("12:10"))
    assert [n.rsplit("-", 1)[0] for n in names] == ["checkpoint", "checkpoint-shadow"]
    assert [journey(line_db, n) for n in names] == [
        [(at("12:10"), ["merged→reviewers"], "reviewers"), (at("12:20"), [], None)],
        [(at("12:10"), ["merged→reviewers"], "reviewers"), (at("12:25"), [], None)],
    ]


def test_every_trip_is_in_time_order_and_on_a_named_belt(line_db):
    conn = connect(line_db)
    try:
        found = trips(conn, PROJECT)
    finally:
        conn.close()
    assert [t.at for t in found] == sorted(t.at for t in found)
    assert {belt for t in found for belt in t.belts} <= set(BELTS)


# --- the document ---------------------------------------------------------------------------


def test_the_stations_and_belts_are_d11s(line_db):
    doc = document(line_db)
    assert [s["id"] for s in doc["stations"]] == [
        "seeds", "planting", "rows", "queue", "lead", "reviewers", "developers", "checks",
        "merged", "ripe", "stash",
    ]  # fmt: skip
    assert [s["id"] for s in doc["stations"]] == list(STATIONS)
    assert [b["id"] for b in doc["belts"]] == list(BELTS)
    assert doc["clog"] is None  # f3-04's
    assert doc["at"] == LINE_NOW.isoformat()


def test_the_developers_qwen_machine_works_on_its_crate(line_db):
    qwen = machines(document(line_db))[LOCAL]
    assert (qwen["station"], qwen["state"], qwen["local"]) == ("developers", "working", True)
    assert qwen["crate"] == {
        "ticket": "f9-01-working",
        "title": "Goal of f9-01-working.",
        "kind": "developer",
        "role": "developer",
        "attempt": 1,
        "minutes": 12,
    }


def test_belts_count_today_and_roll_while_they_carry(line_db):
    found = belts(document(line_db))
    assert (found["queue→developers"]["today"], found["queue→developers"]["carrying"]) == (1, True)
    assert (found["checks→merged"]["today"], found["checks→merged"]["carrying"]) == (2, False)
    # f9-02 came in before midnight and went to the checks after it
    assert (found["developers→checks"]["today"], found["developers→checks"]["carrying"]) == (
        1,
        False,
    )
    assert (found["queue→lead"]["today"], found["lead→checks"]["today"]) == (1, 1)
    assert found["merged→reviewers"]["today"] == 1  # today's checkpoint
    assert found["ripe→stash"]["today"] == 1  # f7, signed off this morning
    assert [b for b in found if found[b]["carrying"]] == ["queue→developers"]


def test_a_new_day_starts_the_counts_again(line_db):
    found = belts(document(line_db, datetime.fromisoformat("2026-10-03T09:00:00+02:00")))
    assert {b["today"] for b in found.values() if b["today"] is not None} == {0}
    assert not any(b["carrying"] for b in found.values())  # the run's heartbeat is long gone


def test_one_machine_per_agent_a_role_names_on_its_station(line_db):
    found = machines(document(line_db))
    assert {k: m["station"] for k, m in found.items()} == {
        OPUS: "lead",
        SONNET: "reviewers",
        COPILOT: "reviewers",
        LOCAL: "developers",
        GPT_OSS: "developers",
    }
    assert document(line_db)["machines"][0]["id"] == OPUS  # the lead first


def test_sonnet_off_the_developers_is_a_reviewer_and_copilot_a_stand_in(line_db):
    found = machines(document(line_db))
    assert found[SONNET]["station"] == "reviewers"
    assert found[SONNET]["off"] == ["developer"]  # it did developer tickets before
    assert found[SONNET]["stand_in"] is False
    assert (found[COPILOT]["station"], found[COPILOT]["stand_in"]) == ("reviewers", True)
    assert found[GPT_OSS]["state"] == "idle"
    assert (found[OPUS]["name"], found[OPUS]["rating"]) == ("Opus", 9)


def test_claude_waits_for_its_limit_until_the_reset(line_db):
    found = machines(document(line_db))
    assert (found[OPUS]["state"], found[OPUS]["reset"]) == ("waiting", "15:00")
    assert (found[SONNET]["state"], found[SONNET]["reset"]) == ("waiting", "15:00")
    assert found[COPILOT]["state"] == "idle"
    later = machines(document(line_db, datetime.fromisoformat("2026-10-02T15:30:00+02:00")))
    assert (later[OPUS]["state"], later[OPUS]["reset"]) == ("idle", None)


def test_the_field_rows_ripe_and_stash_match_the_milestones(line_db):
    doc = document(line_db)
    field = doc["field"]
    assert [(r["key"], r["ready"], r["running"], r["done"], r["total"]) for r in field["rows"]] == [
        ("f1", 1, 0, 3, 4),
        ("f5", 3, 0, 2, 6),
        ("f9", 0, 1, 2, 4),
    ]
    assert [m["key"] for m in field["ripe"]] == ["f8"]
    assert [m["key"] for m in field["stash"]] == ["f7", "m4"]  # latest first
    assert (field["seeds"], field["planting"]) == (1, 0)  # f9-04, set aside
    counts = {s["id"]: s["count"] for s in doc["stations"]}
    assert (counts["seeds"], counts["planting"], counts["rows"]) == (1, 0, 3)
    assert (counts["ripe"], counts["stash"], counts["merged"], counts["queue"]) == (1, 2, 2, 4)


def test_the_queue_is_in_run_order_and_now_names_the_next_three(line_db):
    doc = document(line_db)
    assert [(c["ticket"], c["number"], c["waits"]) for c in doc["queue"]] == [
        ("f1-09-early", 1, []),
        ("f5-03-next", 2, []),
        ("f5-04-after", 3, ["f5-03-next"]),
        ("f5-05-stuck", 4, ["f5-06-escalated"]),
    ]
    assert [n["ticket"] for n in doc["now"]["next"]] == ["f1-09-early", "f5-03-next", "f5-04-after"]
    assert [w["ticket"] for w in doc["now"]["working"]] == ["f9-01-working"]
    assert [c["ticket"] for c in doc["merged"]] == ["f9-02-overnight", "f9-03-lead"]


def test_a_project_whose_repo_cant_be_read_falls_back_to_its_jobs(line_db):
    conn = metrics.open_db(line_db)
    try:
        metrics.upsert_project(conn, PROJECT, repo="/nowhere/at/all")
    finally:
        conn.close()
    found = machines(document(line_db))
    assert {k: m["station"] for k, m in found.items()} == {
        OPUS: "lead",
        SONNET: "reviewers",
        COPILOT: "reviewers",
        LOCAL: "developers",
    }
    assert found[LOCAL]["state"] == "working" and found[SONNET]["off"] == []


def test_an_empty_project_has_an_empty_line(line_db):
    doc = document(line_db, project="elsewhere")
    assert (doc["machines"], doc["queue"], doc["merged"], doc["field"]["rows"]) == ([], [], [], [])
    assert {b["today"] for b in doc["belts"] if b["today"] is not None} == {0}


# --- the page -------------------------------------------------------------------------------

_BLOCK = re.compile(r'<script type="application/json" id="factory-line">(.*?)</script>', re.S)


def block(html: str) -> dict[str, Any]:
    match = _BLOCK.search(html)
    assert match is not None
    found: dict[str, Any] = json.loads(match.group(1))
    return found


def test_the_page_carries_the_document_and_refreshes_every_5_s(line_db, line_client):
    response = line_client.get("/line")
    assert response.status_code == 200
    assert block(response.text) == json.loads(json.dumps(document(line_db, NOW.astimezone())))
    assert re.search(
        r'<a href="/line\?project=coucou" aria-current="page">Factory line</a>', response.text
    )
    assert 'hx-get="/line/live?project=coucou" hx-trigger="every 5s"' in response.text
    live = line_client.get("/line/live")
    assert live.status_code == 200 and "<html" not in live.text
    assert block(live.text) == block(response.text)


def test_the_old_milestone_line_is_gone(line_client):
    assert line_client.get("/milestones/f5/line").status_code == 404


# --- in a browser ---------------------------------------------------------------------------

ORIGIN = "http://127.0.0.1:8765"


def open_line(page, client: TestClient, size: dict[str, int] | None = None) -> dict[str, Any]:
    """``/line`` as the dashboard renders it, opened in Chromium with ``/static/`` from disk.
    Returns its document."""
    html = client.get("/line").text

    def serve(route) -> None:
        path = route.request.url.removeprefix(ORIGIN).split("?", 1)[0]
        if path.startswith("/static/"):
            route.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        elif path == "/line":
            route.fulfill(body=html, content_type="text/html; charset=utf-8")
        else:
            route.fulfill(status=404, body="")

    page.set_default_timeout(5000)
    page.set_viewport_size(size or {"width": 1360, "height": 900})
    page.route(f"{ORIGIN}/**", serve)
    page.goto(ORIGIN + "/line")
    return block(html)


def test_the_floor_draws_one_machine_per_agent_and_the_queue_in_run_order(page, line_client):
    doc = open_line(page, line_client)
    page.wait_for_selector("svg#floor [data-machine]")
    drawn = page.eval_on_selector_all(
        "svg#floor [data-machine]", "els => els.map(e => e.dataset.machine)"
    )
    assert sorted(drawn) == sorted(m["id"] for m in doc["machines"])
    queued = page.eval_on_selector_all(
        "svg#floor [data-queue-crate]", "els => els.map(e => e.dataset.queueCrate)"
    )
    assert queued == [c["ticket"] for c in doc["queue"]]
    working = page.locator(f'svg#floor [data-machine="{LOCAL}"] [data-crate]')
    assert working.get_attribute("data-crate") == "f9-01-working"
    carrying = page.eval_on_selector_all(
        "svg#floor [data-belt].carrying", "els => els.map(e => e.dataset.belt)"
    )
    assert carrying == ["queue→developers"]
    merged = belts(doc)["checks→merged"]["today"]  # from the server's own midnight
    assert page.locator('svg#floor [data-belt="checks→merged"] text').text_content() == (
        f"merged · {merged}"
    )


def test_a_phone_sees_the_portrait_floor(page, line_client):
    open_line(page, line_client, {"width": 390, "height": 1200})
    assert page.locator("svg#floor-phone").is_visible()
    assert not page.locator("svg#floor").is_visible()
    drawn = page.eval_on_selector_all(
        "svg#floor-phone [data-machine]", "els => els.map(e => e.dataset.machine)"
    )
    doc = open_line(page, line_client)
    assert sorted(drawn) == sorted(m["id"] for m in doc["machines"])


def test_desktop_at_1280_sees_the_desktop_floor(page, line_client):
    open_line(page, line_client, {"width": 1280, "height": 900})
    assert page.locator("svg#floor").is_visible()
    assert not page.locator("svg#floor-phone").is_visible()
    drawn = page.eval_on_selector_all(
        "svg#floor [data-machine]", "els => els.map(e => e.dataset.machine)"
    )
    doc = open_line(page, line_client)
    assert sorted(drawn) == sorted(m["id"] for m in doc["machines"])
