"""The factory line (f3 D11): the trips ``line.trips`` reads from the jobs, the document
``line.live_line`` builds, the page that carries it, and what ``static/factory.js`` draws from
it in a browser.

The browser test is the pattern for the factory's tickets: render the page with the
``TestClient``, then open it in pytest-playwright's ``page`` with ``/static/`` served from disk
(``page.route``), and assert on what is drawn.
"""

import json
import re
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient

from factory_dashboard.line import BELTS, STATIONS, live_line, overnight, replay, trips
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


# --- replay (f3-06) -------------------------------------------------------------------------

TZ = timezone(timedelta(hours=2))
SINCE, UNTIL = datetime(2026, 10, 1, 20, 45, tzinfo=TZ), datetime(2026, 10, 2, 2, 30, tzinfo=TZ)


def night(clock: str) -> datetime:
    """``clock`` on the fixture night: the evening on 2026-10-01, the small hours on 10-02."""
    hour, minute = map(int, clock.split(":"))
    return datetime(2026, 10, 1 if hour >= 12 else 2, hour, minute, tzinfo=TZ)


def write_night(conn: Any) -> None:
    """A night (+02:00) in a project of its own, no repo:
    - ``n0`` is ripe at 20:45 (its one ticket merged at 19:30) and signed off at 23:00;
    - ``n1`` (started 20:30): ``n1-01-merge`` passes on Qwen 21:00–21:30; ``n1-02-retry``
      fails ruff 21:40–22:00 and passes 22:05–22:30; the lead's ``n1-03-parked`` is parked at
      22:40 by a Claude limit (until 23:30), then idles to 01:40 (3 h) and passes 01:40–02:10;
      ``n1-04-next`` waits for it.
    """
    project = metrics.upsert_project(conn, PROJECT)
    run = metrics.upsert_run(conn, project, "20261001-183000", command="milestone n1")

    def job(ticket: int, role: str, agent: str, n: int, span: str, ok: bool = True, **end: Any):
        start, stop = (night(c).isoformat() for c in span.split("–"))
        job = metrics.start_job(
            conn, run, ticket_id=ticket, milestone_id=None, role=role, agent=agent, attempt=n,
            started=start,
        )  # fmt: skip
        metrics.finish_job(conn, job, ended=stop, outcome="passed" if ok else "failed", **end)

    def ticket(name: str, m: int, kind: str = "developer", state: str = "done", **more: Any):
        return metrics.upsert_ticket(
            conn, project, name, milestone_id=m, kind=kind, state=state, title=f"Goal of {name}.",
            **more,
        )  # fmt: skip

    n0 = metrics.upsert_milestone(
        conn, project, "n0", title="Ripe", status="done",
        started=night("18:00").isoformat(), ended=night("23:00").isoformat(),
    )  # fmt: skip
    job(ticket("n0-01-early", n0), "developer", LOCAL, 1, "19:00–19:30")
    n1 = metrics.upsert_milestone(
        conn, project, "n1", title="The night", status="in progress",
        started=night("20:30").isoformat(),
    )  # fmt: skip
    job(ticket("n1-01-merge", n1), "developer", LOCAL, 1, "21:00–21:30")
    retry = ticket("n1-02-retry", n1)
    ruff = [{"name": "tests", "ok": True}, {"name": "ruff", "ok": False}]
    job(retry, "developer", LOCAL, 1, "21:40–22:00", ok=False, gates=ruff)
    job(retry, "developer", LOCAL, 2, "22:05–22:30")
    parked = ticket("n1-03-parked", n1, kind="lead")
    job(parked, "lead-ticket", OPUS, 1, "22:35–22:40", ok=False, note="parked")
    metrics.add_usage_event(
        conn, OPUS, night("22:40").isoformat(), "refusal", window="five_hour",
        resets_at=night("23:30").isoformat(),
    )  # fmt: skip
    job(parked, "lead-ticket", OPUS, 2, "01:40–02:10")
    ticket("n1-04-next", n1, state="ready", depends_on=["n1-03-parked"])


@pytest.fixture
def night_db(tmp_path: Path) -> Path:
    path = tmp_path / "night.sqlite"
    conn = metrics.open_db(path)
    try:
        write_night(conn)
    finally:
        conn.close()
    return path


def replayed(db: Path, since: datetime = SINCE, until: datetime = UNTIL) -> dict[str, Any]:
    conn = connect(db)
    try:
        return replay(conn, PROJECT, since, until)
    finally:
        conn.close()


def brief(event: dict[str, Any]) -> tuple[str, ...]:
    """An event in a line: its clock, its kind, what it's about and what happened."""
    clock, kind = (
        datetime.fromisoformat(event["at"]).astimezone(TZ).strftime("%H:%M"),
        event["kind"],
    )
    if kind == "trip":
        return clock, kind, event["crate"], " ".join(event["belts"]), event["to"] or "off"
    if kind == "check":
        result = "passed" if event["passed"] else f"failed: {event['gate']}"
        return clock, kind, event["crate"], result
    if kind == "machine":
        extra = event["ticket"] or event["reset"]
        return clock, kind, event["machine"], " ".join(s for s in (event["state"], extra) if s)
    if kind == "limit":
        return clock, kind, event["agent"], event["state"]
    if kind == "card":
        return clock, kind, event["card"], event["stage"] or "gone"
    return clock, kind, f"{event['minutes']} min"


def test_a_night_replays_in_order_with_the_idle_stretch_as_one_event(night_db):
    found = replayed(night_db)
    assert (found["since"], found["until"]) == (SINCE.isoformat(), UNTIL.isoformat())
    assert [brief(e) for e in found["events"]] == [
        ("21:00", "trip", "n1-01-merge", "queue→developers", "developers"),
        ("21:00", "machine", LOCAL, "working n1-01-merge"),
        ("21:30", "trip", "n1-01-merge", "developers→checks checks→merged", "merged"),
        ("21:30", "check", "n1-01-merge", "passed"),
        ("21:30", "machine", LOCAL, "idle"),
        ("21:40", "trip", "n1-02-retry", "queue→developers", "developers"),
        ("21:40", "machine", LOCAL, "working n1-02-retry"),
        ("22:00", "trip", "n1-02-retry", "developers→checks", "checks"),
        ("22:00", "check", "n1-02-retry", "failed: ruff"),
        ("22:00", "machine", LOCAL, "idle"),
        ("22:05", "trip", "n1-02-retry", "checks→developers", "developers"),
        ("22:05", "machine", LOCAL, "working n1-02-retry"),
        ("22:30", "trip", "n1-02-retry", "developers→checks checks→merged", "merged"),
        ("22:30", "check", "n1-02-retry", "passed"),
        ("22:30", "machine", LOCAL, "idle"),
        ("22:35", "trip", "n1-03-parked", "queue→lead", "lead"),
        ("22:35", "machine", OPUS, "working n1-03-parked"),
        ("22:40", "trip", "n1-03-parked", "", "queue"),  # parked: simply moved
        ("22:40", "machine", OPUS, "waiting 23:30"),
        ("22:40", "limit", OPUS, "start"),
        ("22:40", "idle", "180 min"),  # the 3 h stretch, one event with its real length
        ("23:00", "card", "n0", "stash"),  # signed off
        ("23:30", "machine", OPUS, "idle"),
        ("23:30", "limit", OPUS, "end"),
        ("01:40", "trip", "n1-03-parked", "queue→lead", "lead"),
        ("01:40", "machine", OPUS, "working n1-03-parked"),
        ("02:10", "trip", "n1-03-parked", "lead→checks checks→merged", "merged"),
        ("02:10", "check", "n1-03-parked", "passed"),
        ("02:10", "machine", OPUS, "idle"),
    ]
    idle = [e for e in found["events"] if e["kind"] == "idle"]
    assert idle[0]["until"] == night("01:40").isoformat()


def test_a_replay_starts_from_the_line_at_since(night_db):
    found = replayed(night_db)
    conn = connect(night_db)
    try:
        assert found["line"] == live_line(conn, PROJECT, UNTIL, at=SINCE)
    finally:
        conn.close()
    assert found["line"]["at"] == SINCE.isoformat()
    assert [c["ticket"] for c in found["line"]["queue"]] == [
        "n1-01-merge", "n1-02-retry", "n1-03-parked", "n1-04-next",
    ]  # fmt: skip
    assert ([r["key"] for r in found["line"]["field"]["rows"]], found["line"]["field"]["ripe"]) == (
        ["n1"],
        [{"key": "n0", "title": "Ripe"}],
    )
    assert {m["id"]: m["state"] for m in found["line"]["machines"]} == {LOCAL: "idle", OPUS: "idle"}


def test_the_line_at_each_event_agrees_with_the_event(night_db):
    conn = connect(night_db)
    try:
        events = replay(conn, PROJECT, SINCE, UNTIL)["events"]
        for event in events:
            doc = live_line(conn, PROJECT, UNTIL, at=datetime.fromisoformat(event["at"]))
            found = machines(doc)
            kind = event["kind"]
            if kind == "trip" and event["to"] == "merged":
                assert event["crate"] in [c["ticket"] for c in doc["merged"]], brief(event)
            elif kind == "trip" and event["to"] == "queue":
                assert event["crate"] in [c["ticket"] for c in doc["queue"]], brief(event)
            elif kind == "trip" and event["to"] in ("developers", "lead"):
                working = [m["crate"]["ticket"] for m in found.values() if m["crate"]]
                assert event["crate"] in working, brief(event)
            elif kind == "machine":
                m = found[event["machine"]]
                assert m["state"] == event["state"], brief(event)
                assert (m["crate"] or {}).get("ticket") == event["ticket"], brief(event)
                assert m["reset"] == event["reset"], brief(event)
            elif kind == "limit":
                waits = found[event["agent"]]["state"] == "waiting"
                assert waits == (event["state"] == "start"), brief(event)
            elif kind == "card":
                field = doc["field"]
                stage = {r["key"]: "rows" for r in field["rows"]}
                stage |= {m["key"]: "ripe" for m in field["ripe"]}
                stage |= {m["key"]: "stash" for m in field["stash"]}
                assert stage.get(event["card"]) == event["stage"], brief(event)
            elif kind == "idle":
                assert doc["now"]["working"] == [], brief(event)
    finally:
        conn.close()


def test_the_line_mid_job_shows_its_machine_working(night_db):
    conn = connect(night_db)
    try:
        doc = live_line(conn, PROJECT, UNTIL, at=night("21:15"))
        later = live_line(conn, PROJECT, UNTIL, at=night("22:50"))
        small_hours = live_line(conn, PROJECT, UNTIL, at=UNTIL)
    finally:
        conn.close()
    qwen = machines(doc)[LOCAL]
    assert (qwen["state"], qwen["crate"]["ticket"], qwen["crate"]["minutes"]) == (
        "working",
        "n1-01-merge",
        15,
    )
    assert [w["ticket"] for w in doc["now"]["working"]] == ["n1-01-merge"]
    assert belts(doc)["queue→developers"]["carrying"] is True
    assert [c["ticket"] for c in doc["queue"]] == ["n1-02-retry", "n1-03-parked", "n1-04-next"]
    assert [c["ticket"] for c in doc["merged"]] == ["n0-01-early"]  # at 19:30
    # parked: back in the queue, the lead waiting for its limit
    assert [(c["ticket"], c["waits"]) for c in later["queue"]] == [
        ("n1-03-parked", []),
        ("n1-04-next", ["n1-03-parked"]),
    ]
    assert (machines(later)[OPUS]["state"], machines(later)[OPUS]["reset"]) == ("waiting", "23:30")
    assert [c["ticket"] for c in later["merged"]] == ["n0-01-early", "n1-01-merge", "n1-02-retry"]
    # after midnight, today's counts start again
    assert [c["ticket"] for c in small_hours["merged"]] == ["n1-03-parked"]
    assert belts(small_hours)["checks→merged"]["today"] == 1
    assert [s["key"] for s in small_hours["field"]["stash"]] == ["n0"]


def test_overnight_starts_when_the_line_was_last_opened_or_at_20_yesterday():
    morning = datetime(2026, 10, 2, 7, 5, tzinfo=TZ)
    assert overnight(morning, None) == datetime(2026, 10, 1, 20, 0, tzinfo=TZ)
    assert overnight(morning, "not a time") == datetime(2026, 10, 1, 20, 0, tzinfo=TZ)
    assert overnight(morning, "2026-10-01T23:10:00+02:00") == night("23:10")
    assert overnight(morning, "2026-10-02T09:00:00+02:00") == night("20:00")  # not yet: ignored


def night_client(db: Path) -> TestClient:
    from factory_dashboard.app import create_app, get_now

    app = create_app(db, PROJECT)
    app.dependency_overrides[get_now] = lambda: UNTIL
    return TestClient(app, base_url="http://127.0.0.1:8765")


def test_the_replay_route_serves_a_stretch_as_json(night_db):
    client = night_client(night_db)
    response = client.get("/line/replay", params={"since": SINCE.isoformat()})
    assert response.status_code == 200
    expected = json.loads(json.dumps(replayed(night_db, SINCE, UNTIL.astimezone())))
    assert response.json() == expected
    assert client.get("/line/replay", params={"since": "yesterday"}).status_code == 400
    late = {"since": UNTIL.isoformat(), "until": SINCE.isoformat()}
    assert client.get("/line/replay", params=late).status_code == 400


def test_the_line_page_remembers_when_it_was_opened_for_overnight(night_db):
    client = night_client(night_db)
    first = client.get("/line")
    assert first.status_code == 200
    seen = first.cookies["line_seen"].strip('"')
    assert datetime.fromisoformat(seen) == UNTIL
    # the page offers overnight from 20:00 yesterday the first time, then from the last visit
    match = re.search(r'data-replay="([^"]+)"', first.text)
    assert match is not None
    since = parse_qs(urlsplit(unescape(match.group(1))).query)["since"][0]
    assert datetime.fromisoformat(since) == overnight(UNTIL.astimezone(), None)
    client.cookies.set("line_seen", night("23:10").isoformat())
    again = re.search(r'data-replay="([^"]+)"', client.get("/line").text)
    assert again is not None
    since = parse_qs(urlsplit(unescape(again.group(1))).query)["since"][0]
    assert datetime.fromisoformat(since) == night("23:10")
    # without a since, the route takes the cookie's
    found = client.get("/line/replay").json()
    assert datetime.fromisoformat(found["since"]) == night("23:10")


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


def test_carrying_belt_has_moving_class(page, line_client):
    open_line(page, line_client)
    carrying = page.eval_on_selector_all(
        "svg#floor [data-belt].carrying.moving", "els => els.map(e => e.dataset.belt)"
    )
    assert carrying == ["queue→developers"]
    quiet = page.eval_on_selector_all(
        "svg#floor [data-belt]:not(.moving)", "els => els.map(e => e.dataset.belt)"
    )
    assert "queue→developers" not in quiet


def test_working_machine_has_smoke_idle_does_not(page, line_client):
    open_line(page, line_client)
    doc = open_line(page, line_client)
    machines = {m["id"]: m for m in doc["machines"]}
    for mid, m in machines.items():
        smoke = page.locator(f'svg#floor [data-machine="{mid}"] circle.smoke')
        has_smoke = smoke.count() > 0
        if m["state"] == "working":
            assert has_smoke, f"{mid} is working but has no smoke"
        else:
            assert not has_smoke, f"{mid} is {m['state']} but has smoke"


def test_reduced_motion_disables_animations(page, line_client):
    page.emulate_media(reduced_motion="reduce")
    open_line(page, line_client)
    running = page.evaluate("""
        () => {
            const els = document.querySelectorAll('svg#floor *');
            const style = getComputedStyle(document.body);
            const media = window.matchMedia('(prefers-reduced-motion: reduce)');
            if (!media.matches) return ['no reduced motion media query'];
            const animated = [];
            for (const el of els) {
                const cs = getComputedStyle(el);
                if (cs.animationName && cs.animationName !== 'none') {
                    animated.push(el.className.baseVal || el.tagName);
                }
            }
            return animated;
        }
    """)
    assert running == [], f"elements still animated: {running}"
