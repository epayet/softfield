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
    assert doc["at"] == LINE_NOW.isoformat()


def test_the_document_says_what_clogged_the_line_today(line_db):
    # The run lived 09:00–14:00; jobs ran 09:00–09:40 (the lead), 10:00–10:10 (a checkpoint)
    # and 13:48 on (Qwen); Claude was refused at 13:30. Nothing failed, nothing for the owner.
    assert document(line_db)["clog"] == {
        "limit": 30,
        "failed": 0,
        "failures": 0,
        "idle": [
            {"agent": LOCAL, "name": "qwen3.6-35b-a3b", "minutes": 50, "share": 0.17},
            {"agent": GPT_OSS, "name": "gpt-oss-120b", "minutes": 62, "share": 0.21},
        ],
        "owner": 0,
        "live": 300,
    }


def test_the_clog_at_a_past_moment_counts_up_to_it(line_db):
    conn = connect(line_db)
    try:
        doc = live_line(conn, PROJECT, LINE_NOW, at=LINE_NOW - timedelta(hours=4))
    finally:
        conn.close()
    # at 10:00: the run had lived an hour, the lead's 40 min of it; no limit yet
    assert doc["clog"]["live"] == 60 and doc["clog"]["limit"] == 0
    assert [i["minutes"] for i in doc["clog"]["idle"]] == [40, 40]


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
    html = line_client.get("/").text
    assert block(html) == json.loads(json.dumps(document(line_db, NOW.astimezone())))
    assert re.search(r'<a href="/\?project=coucou" aria-current="page">Overview</a>', html)
    assert 'hx-get="/line/live?project=coucou" hx-trigger="every 5s [window.liveIdle()]"' in html
    live = line_client.get("/line/live")
    assert live.status_code == 200 and "<html" not in live.text
    assert block(live.text) == block(html)


def test_the_old_milestone_line_is_gone(line_client):
    assert line_client.get("/milestones/f5/line").status_code == 404


def test_line_redirects_to_overview_keeping_query(line_client):
    resp = line_client.get("/line?project=coucou", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "/?project=coucou"


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
    first = client.get("/line", follow_redirects=False)
    assert first.status_code == 307
    # the redirect target sets the line_seen cookie
    overview = client.get("/")
    assert overview.status_code == 200
    seen = overview.cookies["line_seen"].strip('"')
    assert datetime.fromisoformat(seen) == UNTIL
    # the page offers overnight from 20:00 yesterday the first time, then from the last visit
    match = re.search(r'data-replay="([^"]+)"', overview.text)
    assert match is not None
    since = parse_qs(urlsplit(unescape(match.group(1))).query)["since"][0]
    assert datetime.fromisoformat(since) == overnight(UNTIL.astimezone(), None)
    # and the last 24 h, from the server's own clock
    day = re.search(r'data-replay-day="([^"]+)"', overview.text)
    assert day is not None
    since = parse_qs(urlsplit(unescape(day.group(1))).query)["since"][0]
    assert since == (UNTIL.astimezone() - timedelta(days=1)).isoformat()
    client.cookies.set("line_seen", night("23:10").isoformat())
    again = re.search(r'data-replay="([^"]+)"', client.get("/").text)
    assert again is not None
    since = parse_qs(urlsplit(unescape(again.group(1))).query)["since"][0]
    assert datetime.fromisoformat(since) == night("23:10")
    # without a since, the route takes the cookie's
    found = client.get("/line/replay").json()
    assert datetime.fromisoformat(found["since"]) == night("23:10")


# --- in a browser ---------------------------------------------------------------------------

ORIGIN = "http://127.0.0.1:8765"


@pytest.fixture
def page(page):
    """pytest-playwright's page, failing on any error the page throws. In f3-11 a syntax error
    stopped factory.js whole; every browser test timed out and the error was never shown."""
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    yield page
    assert errors == [], f"factory.js threw: {errors}"


def open_line(page, client: TestClient, size: dict[str, int] | None = None) -> dict[str, Any]:
    """``/`` as the dashboard renders it, opened in Chromium with ``/static/`` from disk and
    ``/line/replay`` from ``client``. Returns its document."""
    html = client.get("/").text

    def serve(route) -> None:
        url = route.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            route.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        elif path == "/":
            route.fulfill(body=html, content_type="text/html; charset=utf-8")
        elif path == "/line/replay":
            found = client.get(url)
            route.fulfill(
                status=found.status_code, body=found.text, content_type="application/json"
            )
        else:
            route.fulfill(status=404, body="")

    page.set_default_timeout(5000)
    page.set_viewport_size(size or {"width": 1360, "height": 900})
    page.route(f"{ORIGIN}/**", serve)
    page.goto(ORIGIN + "/")
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


def test_the_phone_floor_is_drawn_in_the_floors_colours_not_black(page, line_client):
    """2026-10-03: on the owner's phone the portrait floor was black boxes with black text:
    its svg lacked the `floor` class that every colour rule is scoped to."""
    open_line(page, line_client, {"width": 390, "height": 1200})
    for selector in ("svg#floor-phone .unit", "svg#floor-phone text"):
        fills = page.eval_on_selector_all(selector, "els => els.map(e => getComputedStyle(e).fill)")
        assert fills, selector
        assert "rgb(0, 0, 0)" not in fills, selector
    box = page.locator("svg#floor-phone").bounding_box()
    assert box is not None and box["width"] <= 390


PHONE = {"width": 390, "height": 1200}


def phone_drawn(page, selector: str, key: str) -> list[str]:
    found: list[str] = page.eval_on_selector_all(
        f"svg#floor-phone {selector}", f"els => els.map(e => e.dataset.{key})"
    )
    return found


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_a_phone_draws_every_station_with_its_crates_and_belts(page, line_client, scheme):
    """2026-10-03, at 390 px: the portrait floor was outlines only: no planting and no rows,
    an empty queue and stash, few belts."""
    page.emulate_media(color_scheme=scheme)
    doc = open_line(page, line_client, PHONE)
    assert phone_drawn(page, "[data-station]", "station") == [s["id"] for s in doc["stations"]]
    planting = page.locator('svg#floor-phone [data-station="planting"] text').all_text_contents()
    assert planting[0] == "PLANTING"
    assert phone_drawn(page, "[data-row]", "row") == [r["key"] for r in doc["field"]["rows"]]
    assert phone_drawn(page, "[data-queue-crate]", "queueCrate") == [
        c["ticket"] for c in doc["queue"]
    ]
    assert phone_drawn(page, "[data-machine]", "machine") == [m["id"] for m in doc["machines"]]
    working = page.locator(f'svg#floor-phone [data-machine="{LOCAL}"] [data-crate]')
    assert working.get_attribute("data-crate") == "f9-01-working"
    assert phone_drawn(page, "[data-merged]", "merged") == [c["ticket"] for c in doc["merged"]]
    assert phone_drawn(page, "[data-ripe]", "ripe") == ["f8"]
    assert phone_drawn(page, "[data-stash]", "stash") == ["f7", "m4"]
    assert phone_drawn(page, "[data-belt]", "belt") == [b["id"] for b in doc["belts"]]
    assert phone_drawn(page, "[data-belt].carrying", "belt") == ["queue→developers"]
    merged = belts(doc)["checks→merged"]["today"]
    counted = page.locator('svg#floor-phone [data-belt="checks→merged"] text').text_content()
    assert counted == f"merged · {merged}"


def test_a_phones_queue_holds_its_first_six_crates_in_run_order(page, line_client):
    doc = open_line(page, line_client, PHONE)
    crates = [dict(doc["queue"][0], ticket=f"f6-{n:02}-crate", number=n) for n in range(1, 10)]
    page.evaluate(
        """queue => {
            const block = document.getElementById("factory-line");
            block.textContent = JSON.stringify({ ...JSON.parse(block.textContent), queue });
            document.dispatchEvent(new CustomEvent("htmx:load", { detail: { elt: document } }));
        }""",
        crates,
    )
    assert phone_drawn(page, "[data-queue-crate]", "queueCrate") == [
        c["ticket"] for c in crates[:6]
    ]
    head = page.locator('svg#floor-phone [data-station="queue"] text').first.text_content()
    assert head == "QUEUE · 9"


# Every text on the phone floor: its words, its box, the box of its machine's or station's own
# shapes (null when the station has none of its own), and every machine's shapes, one by one.
LABELS = """svg => {
    const owner = (e) => e.closest("[data-machine], [data-station]");
    const box = (e) => {
        const r = e.getBoundingClientRect();
        return [r.left, r.top, r.right, r.bottom];
    };
    const union = (boxes) => boxes.length ? [
        Math.min(...boxes.map(b => b[0])), Math.min(...boxes.map(b => b[1])),
        Math.max(...boxes.map(b => b[2])), Math.max(...boxes.map(b => b[3])),
    ] : null;
    const shapes = [...svg.querySelectorAll("rect, path, ellipse, circle")]
        .filter(s => !s.closest("[data-belt], defs"));
    const frame = (g) => g ? union(shapes.filter(s => owner(s) === g).map(box)) : null;
    const labels = [...svg.querySelectorAll("text")].filter(t => t.textContent.trim()).map(t => ({
        words: t.textContent,
        box: box(t),
        frame: frame(owner(t)),
        machine: t.closest("[data-machine]")?.dataset.machine ?? null,
    }));
    const machines = shapes.filter(s => s.closest("[data-machine]"))
        .map(s => ({ machine: s.closest("[data-machine]").dataset.machine, box: box(s) }));
    return { floor: box(svg), labels, machines };
}"""


def overlaps(a: list[float], b: list[float], slack: float = 0.5) -> bool:
    return min(a[2], b[2]) - max(a[0], b[0]) > slack and min(a[3], b[3]) - max(a[1], b[1]) > slack


def inside(a: list[float], b: list[float], slack: float = 0.5) -> bool:
    return (
        a[0] >= b[0] - slack
        and a[1] >= b[1] - slack
        and a[2] <= b[2] + slack
        and a[3] <= b[3] + slack
    )


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_no_phone_label_overlaps_another_or_leaves_its_station(page, line_client, scheme):
    """2026-10-03, at 390 px: "SONNET" and "COPIL…" squeezed into 70 px boxes, "DEVELOPER BAY"
    under a chimney, the ripe icon over "RIPE". Measured still: rising smoke fades over words."""
    page.emulate_media(color_scheme=scheme, reduced_motion="reduce")
    open_line(page, line_client, PHONE)
    found = page.eval_on_selector("svg#floor-phone", LABELS)
    labels = found["labels"]
    assert len(labels) > 40
    for n, label in enumerate(labels):
        assert inside(label["box"], found["floor"]), label
        if label["frame"] is not None:
            assert inside(label["box"], label["frame"]), label
        for other in labels[n + 1 :]:
            assert not overlaps(label["box"], other["box"]), (label, other)
        for shape in found["machines"]:
            if shape["machine"] != label["machine"]:
                assert not overlaps(label["box"], shape["box"]), (label, shape)


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


def test_phone_floor_belt_and_smoke_get_their_animation_classes(page, line_client):
    """f4-always-on-C228-2: the phone floor uses .floor-phone, so its belt and smoke
    must carry the same animation classes as the desktop floor."""
    open_line(page, line_client, PHONE)
    phone_carrying = page.eval_on_selector_all(
        "svg#floor-phone [data-belt].carrying.moving", "els => els.map(e => e.dataset.belt)"
    )
    assert phone_carrying == ["queue→developers"]
    phone_on = page.eval_on_selector_all(
        "svg#floor-phone [data-machine].on", "els => els.map(e => e.dataset.machine)"
    )
    assert LOCAL in phone_on


def test_css_motion_query_targets_floor_phone_for_belt_and_smoke_animations():
    """f4-always-on-C228-2: the phone floor uses .floor-phone, so its belt and smoke
    must carry the same animation classes as the desktop floor."""
    css = (STATIC / "dashboard.css").read_text()
    # The motion query (prefers-reduced-motion: no-preference) must include .floor-phone
    # alongside .floor so animations apply on the phone diagram.
    # Before the fix, selectors only targeted .floor and missed the phone floor entirely.
    in_motion = False
    for line in css.splitlines():
        if "prefers-reduced-motion: no-preference" in line:
            in_motion = True
        if in_motion:
            if "}" in line and "{" not in line:
                in_motion = False
            if ".floor-phone" in line:
                break
    else:
        pytest.fail(".floor-phone not found in prefers-reduced-motion: no-preference block")


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


PAUSED = """() => {
    const event = new CustomEvent("htmx:beforeRequest", { bubbles: true, cancelable: true });
    document.getElementById("line-live").dispatchEvent(event);
    return event.defaultPrevented;
}"""


def merged_on_floor(page) -> list[str]:
    found: list[str] = page.eval_on_selector_all(
        "svg#floor [data-merged]", "els => els.map(e => e.dataset.merged)"
    )
    return found


def test_replay_draws_the_floor_at_since_and_back_to_live_draws_it_again(page, night_db):
    client = night_client(night_db)
    open_line(page, client)
    url = page.locator(".page").get_attribute("data-replay")
    assert url is not None
    expected = client.get(url).json()  # the server's zone: +01:00 here, 27 events since 20:00
    assert merged_on_floor(page) == ["n1-03-parked"]
    assert not page.locator("#replay-play").is_visible()
    assert page.evaluate(PAUSED) is False

    page.click("#replay-start")
    page.wait_for_selector("#replay-live", state="visible")
    assert merged_on_floor(page) == ["n0-01-early"]
    count = len(expected["events"])
    assert page.locator("#replay-readout").text_content() == (
        f"{count} events since {expected['since'][11:16]}"
    )
    assert page.evaluate(PAUSED) is True  # the 5 s refresh is cancelled

    page.click("#replay-live")
    assert not page.locator("#replay-live").is_visible()
    assert page.locator("#replay-start").is_visible()
    assert merged_on_floor(page) == ["n1-03-parked"]
    assert page.evaluate(PAUSED) is False


def test_on_a_phone_the_replay_bar_sticks_to_the_bottom_with_44_px_controls(page, night_db):
    size = {"width": 390, "height": 844}
    open_line(page, night_client(night_db), size)
    page.click("#replay-start")
    page.wait_for_selector("#replay-live", state="visible")
    bar = page.locator("#replay")
    assert bar.evaluate("e => getComputedStyle(e).position") == "sticky"
    box = bar.bounding_box()
    assert box is not None and abs(box["y"] + box["height"] - size["height"]) <= 1
    controls = page.locator("#replay button, #replay select")
    assert controls.count() == 7  # Replay, its stretch, Play, ◀, ▶, the speed, Back to live
    for n in range(controls.count()):
        found = controls.nth(n).bounding_box()
        assert found is not None and found["width"] >= 44 and found["height"] >= 44, n


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


# --- replay steps (f3-11) --------------------------------------------------------------------


def start_replay(page, night_db) -> list[dict[str, Any]]:
    """The fixture night's line opened and its overnight replay loaded; returns its events,
    from the route, in the server's zone."""
    client = night_client(night_db)
    open_line(page, client)
    url = page.locator(".page").get_attribute("data-replay")
    assert url is not None
    events: list[dict[str, Any]] = client.get(url).json()["events"]
    page.click("#replay-start")
    page.wait_for_selector("#replay-live", state="visible")
    return events


def readout(page) -> str:
    return page.locator("#replay-readout").text_content() or ""


def about(event: dict[str, Any]) -> str:
    """What the readout must name for ``event``: its crate, machine, agent or card."""
    key = {"trip": "crate", "check": "crate", "machine": "machine", "limit": "agent"}
    return str(event.get(key.get(event["kind"], "card"), f"{event.get('minutes')} min"))


def test_replay_steps_through_the_events_by_hand_and_on_play(page, night_db):
    events = start_replay(page, night_db)
    assert len(events) > 3
    for event in events:
        page.click("#replay-next")
        assert readout(page).startswith(event["at"][11:16] + " "), (readout(page), event)
        assert about(event) in readout(page), (readout(page), event)
    page.click("#replay-next")  # past the last event: nothing moves
    assert about(events[-1]) in readout(page)
    page.click("#replay-prev")
    assert readout(page).startswith(events[-2]["at"][11:16])
    assert about(events[-2]) in readout(page)

    for _ in events:
        page.click("#replay-prev")
    first = readout(page)
    assert first.startswith(f"{len(events)} events since ")  # back at the start
    page.select_option("#replay-speed", "1500")
    page.click("#replay-play")
    assert page.locator("#replay-play").text_content() == "Pause"
    page.wait_for_function(
        "first => document.getElementById('replay-readout').textContent !== first", arg=first
    )
    assert readout(page).startswith(events[0]["at"][11:16])
    page.click("#replay-next")  # stops playing
    assert page.locator("#replay-play").text_content() == "Play"

    page.click("#replay-live")
    assert not page.locator("#replay-live").is_visible()
    assert merged_on_floor(page) == ["n1-03-parked"]


def test_a_replayed_machine_works_on_its_crate_and_a_failed_check_flashes_red(page, night_db):
    events = start_replay(page, night_db)
    working = next(
        n for n, e in enumerate(events) if e["kind"] == "machine" and e["state"] == "working"
    )
    failed = next(n for n, e in enumerate(events) if e["kind"] == "check" and not e["passed"])
    assert (events[failed]["crate"], events[failed]["gate"]) == ("n1-02-retry", "ruff")
    assert working < failed

    for _ in range(working + 1):
        page.click("#replay-next")
    machine = page.locator(f'svg#floor [data-machine="{events[working]["machine"]}"]')
    assert "on" in (machine.get_attribute("class") or "").split()
    assert machine.locator("[data-crate]").get_attribute("data-crate") == events[working]["ticket"]

    for _ in range(failed - working - 1):
        page.click("#replay-next")
    assert page.locator("svg#floor .light.flash-red").count() == 0
    page.click("#replay-next")
    assert readout(page).endswith("n1-02-retry failed checks: ruff")
    assert page.locator("svg#floor .light.flash-red").count() == 1
