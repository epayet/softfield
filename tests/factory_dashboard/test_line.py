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
from itertools import pairwise
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit

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
    assert (found[OPUS]["name"], found[OPUS]["rating"]) == ("Opus", "9")


def test_rating_rounds_to_one_decimal_and_displays_cleanly(line_db):
    """The document's rating is rounded to one decimal: 3.4770 → 3.5, 10 → 10."""
    conn = metrics.open_db(line_db)
    try:
        metrics.add_rating_change(
            conn,
            LOCAL,
            "coding",
            3.0,
            3.4770,
            at="2026-09-30T11:00:00+02:00",
        )
        metrics.add_rating_change(
            conn,
            SONNET,
            "reviewing",
            5.0,
            10.0,
            at="2026-09-30T12:00:00+02:00",
        )
    finally:
        conn.close()
    doc = document(line_db)
    m = machines(doc)
    assert m[LOCAL]["rating"] == "3.5"
    assert m[SONNET]["rating"] == "10"


def test_claude_waits_for_its_limit_until_the_reset(line_db):
    found = machines(document(line_db))
    assert (found[OPUS]["state"], found[OPUS]["reset"]) == ("waiting", "15:00")
    assert (found[SONNET]["state"], found[SONNET]["reset"]) == ("waiting", "15:00")
    assert found[COPILOT]["state"] == "idle"
    later = machines(document(line_db, datetime.fromisoformat("2026-10-02T15:30:00+02:00")))
    assert (later[OPUS]["state"], later[OPUS]["reset"]) == ("idle", None)


def test_machines_say_how_many_trips_they_merged_today(line_db):
    """Each idle machine gains merged_today: the number of today's trips (since local midnight,
    up to at) that end at merged and whose job ran on that machine's agent."""
    doc = document(line_db)
    m = machines(doc)
    # LOCAL (Qwen) merged f9-02-overnight at 00:20 today
    assert m[LOCAL]["merged_today"] == 1
    # OPUS merged f9-03-lead at 09:40 today
    assert m[OPUS]["merged_today"] == 1
    # GPT_OSS has no merges today
    assert m[GPT_OSS]["merged_today"] == 0


def test_idle_lead_says_which_lead_ticket_it_takes_next(line_db):
    """The idle lead shows next: <ticket> for the first crate of the queue that is a lead ticket."""
    doc = document(line_db)
    # f5-04-after is a lead ticket in the queue
    queue_tickets = [c["ticket"] for c in doc["queue"]]
    assert "f5-04-after" in queue_tickets
    # Find the first lead ticket in the queue
    lead_ticket = None
    for c in doc["queue"]:
        if c["kind"] == "lead":
            lead_ticket = c["ticket"]
            break
    assert lead_ticket == "f5-04-after"


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
    assert field["later"] == [{"ticket": "f9-04-later", "title": "Goal of f9-04-later."}]
    counts = {s["id"]: s["count"] for s in doc["stations"]}
    assert (counts["seeds"], counts["planting"], counts["rows"]) == (1, 0, 3)
    assert (counts["ripe"], counts["stash"], counts["merged"], counts["queue"]) == (1, 2, 2, 4)


def planning_cards(db: Path, cards: list[tuple[str, str | None, bool, str | None]]) -> None:
    """Each card as (key, state, a thread about it, a ticket of its own in that state)."""
    conn = metrics.open_db(db)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        for key, state, thread, ticket in cards:
            card = metrics.upsert_milestone(conn, project, key, title=key, state=state)
            if thread:
                metrics.planner_thread(conn, project, key.split("-")[0], NOW.isoformat())
            if ticket:
                name = f"{key.split('-')[0]}-01-own"
                metrics.upsert_ticket(
                    conn, project, name, milestone_id=card, state=ticket, title=f"Goal of {name}."
                )
    finally:
        conn.close()


def test_planting_counts_the_cards_being_planned_once_each(line_db):
    """The owner, 2026-10-06: Planting said "0 in talks" whatever was being planned; the count
    was a placeholder. A card building with a ticket of its own is past planting, thread or
    not."""
    planning_cards(
        line_db,
        [
            ("f20-first-idea", "idea", False, None),
            ("f21-second-idea", "idea", False, None),
            ("f22-in-talks", "planning", True, None),  # its state and its thread: counted once
            ("f23-building", "building", True, "done"),
        ],
    )
    doc = document(line_db)
    assert doc["field"]["planting"] == 3
    assert {s["id"]: s["count"] for s in doc["stations"]}["planting"] == 3


def test_a_thread_about_a_card_with_no_ticket_yet_is_planting(line_db):
    """A thread is enough, whatever the card's state, until the card has a ticket; the general
    thread is about no card, and an archived thread is no longer a talk."""
    planning_cards(line_db, [("f24-asked-about", None, True, None)])
    conn = metrics.open_db(line_db)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.planner_thread(conn, project, "general", NOW.isoformat())
        metrics.planner_thread(conn, project, "f9", NOW.isoformat())  # f9 has tickets
    finally:
        conn.close()
    assert document(line_db)["field"]["planting"] == 1
    conn = metrics.open_db(line_db)
    try:
        thread = metrics.find_thread(conn, metrics.upsert_project(conn, PROJECT), "f24")
        assert thread is not None
        metrics.set_thread_archived(conn, thread["id"], NOW.isoformat())
        conn.commit()
    finally:
        conn.close()
    assert document(line_db)["field"]["planting"] == 0


def test_later_lists_the_set_aside_tickets_by_id_and_seeds_counts_them(line_db):
    planning_cards(line_db, [("f23-building", "building", False, "later")])
    conn = metrics.open_db(line_db)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f1 = metrics.upsert_milestone(conn, project, "f1")
        metrics.upsert_ticket(conn, project, "f1-90-untitled", milestone_id=f1, state="later")
    finally:
        conn.close()
    field = document(line_db)["field"]
    assert field["later"] == [
        {"ticket": "f1-90-untitled", "title": None},
        {"ticket": "f9-04-later", "title": "Goal of f9-04-later."},
        {"ticket": "f23-01-own", "title": "Goal of f23-01-own."},
    ]
    assert field["seeds"] == 3


def test_a_card_ripens_only_once_its_review_is_written(line_db):
    """F50 D1: F20's tickets were done but its review wasn't: the desk asked for a sign-off
    with nothing to read. Without its sheet, f8 stays in the rows, all done."""
    conn = metrics.open_db(line_db)
    try:
        conn.execute("UPDATE milestones SET signoff = NULL WHERE key = 'f8'")
    finally:
        conn.close()
    field = document(line_db)["field"]
    assert [m["key"] for m in field["ripe"]] == []
    [row] = [r for r in field["rows"] if r["key"] == "f8"]
    assert (row["ready"], row["running"], row["done"], row["total"]) == (0, 0, 1, 1)
    assert [m["key"] for m in field["stash"]] == ["f7", "m4"]  # done ones, sheet or not


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


def test_a_due_review_heads_the_queue_as_a_batch_crate(line_db):
    """f4-20 (the owner, 2026-10-03: "a task scheduled like the others"): `runner run` takes
    a due review before the next ticket."""
    conn = metrics.open_db(line_db)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_milestone(conn, project, "f8", status=metrics.REVIEW_DUE)
    finally:
        conn.close()
    doc = document(line_db)
    review: dict[str, Any] = {
        "ticket": None,
        "role": "review",
        "title": "review F8",
        "kind": "batch",
        "milestone": "f8",
        "number": 1,
        "waits": [],
    }
    assert doc["queue"][0] == review
    assert [c["number"] for c in doc["queue"]] == [1, 2, 3, 4, 5]
    assert doc["now"]["next"][0] == review
    assert {s["id"]: s["count"] for s in doc["stations"]}["queue"] == 5


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


def test_the_floor_keeps_its_section_and_fetches_only_its_document(line_client):
    """f3-17: swapping the section whole every 5 s restarted every animation (the flicker)."""
    html = line_client.get("/").text
    assert 'hx-swap="none"' in html
    assert """hx-headers='{"Accept": "application/json"}'""" in html
    live = line_client.get("/line/live", headers={"Accept": "application/json"})
    assert live.status_code == 200
    assert live.headers["content-type"] == "application/json"
    assert live.json() == block(html)


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
        conn, project, "n0", title="Ripe", status="done", signoff={"changed": "Ripe."},
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


def open_line(
    page,
    client: TestClient,
    size: dict[str, int] | None = None,
    live: list[dict[str, Any]] | None = None,
    query: str = "",
) -> dict[str, Any]:
    """``/`` as the dashboard renders it, opened in Chromium with ``/static/`` from disk and
    ``/line/replay`` and ``/line/live`` from ``client``; or ``/line/live`` answers ``live``'s
    documents in turn, the last one again. Returns its document.``query`` is appended to the
    initial ``page.goto`` so that ``window.location.search`` contains it when factory.js runs."""
    html = client.get(f"/?{query}").text

    def serve(route) -> None:
        url = route.request.url.removeprefix(ORIGIN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            route.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        elif path == "/":
            route.fulfill(body=html, content_type="text/html; charset=utf-8")
        elif path == "/line/live" and live:
            body = json.dumps(live.pop(0) if len(live) > 1 else live[0])
            route.fulfill(body=body, content_type="application/json")
        elif path in ("/line/replay", "/line/live"):
            found = client.get(url, headers={"Accept": route.request.headers.get("accept", "")})
            route.fulfill(
                status=found.status_code,
                body=found.text,
                content_type=found.headers["content-type"],
            )
        else:
            route.fulfill(status=404, body="")

    page.set_default_timeout(5000)
    page.set_viewport_size(size or {"width": 1360, "height": 900})
    page.route(f"{ORIGIN}/**", serve)
    page.goto(ORIGIN + "/" + ("?" + query if query else ""))
    page.evaluate(
        """() => {
            window.refreshes = 0;
            document.addEventListener("htmx:afterRequest", (event) => {
                if (event.target.id === "line-live") window.refreshes += 1;
            });
        }"""
    )
    return block(html)


def refresh(page) -> None:
    """The floor's 5 s refresh, once, on the page's clock (``page.clock.install()`` before
    ``open_line``), and drawn."""
    before = page.evaluate("() => window.refreshes")
    page.clock.run_for(5100)
    page.wait_for_function("n => window.refreshes > n", arg=before)


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
        f"merged · {merged} today"
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
    assert counted == f"merged · {merged} today"


def test_phone_belts_with_say_show_their_word_and_count(page, line_client):
    """On the phone, queue→developers reads "developer · N today", lead→checks reads
    "lead's work · N today" and checks→lead reads "back to the lead · N today";
    only seeds→planting reads "N today" (short)."""
    open_line(page, line_client, PHONE)
    doc = block(line_client.get("/").text)
    for belt in doc["belts"]:
        if belt["id"] == "queue→developers":
            belt["today"] = 7
        elif belt["id"] == "lead→checks":
            belt["today"] = 3
        elif belt["id"] == "checks→lead":
            belt["today"] = 5
    page.evaluate(
        "(doc) => { "
        "  const el = document.getElementById('factory-line'); "
        "  el.textContent = JSON.stringify(doc); "
        "  document.dispatchEvent(new CustomEvent('htmx:load', { detail: { elt: document } })); "
        "}",
        doc,
    )
    assert (
        page.locator('svg#floor-phone [data-belt="queue→developers"] text').text_content()
        == "developer · 7 today"
    )
    assert (
        page.locator('svg#floor-phone [data-belt="lead→checks"] text').text_content()
        == "lead's work · 3 today"
    )
    assert (
        page.locator('svg#floor-phone [data-belt="checks→lead"] text').text_content()
        == "back to the lead · 5 today"
    )
    seeds_planting = page.locator(
        'svg#floor-phone [data-belt="seeds→planting"] text'
    ).text_content()
    assert " · " not in seeds_planting


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


def test_planting_says_ideas_with_lead_and_N_in_talks(page, line_client):
    """Planting reads "ideas you're planning", "with the lead" and "N in talks" (N from the
    document's planting count, not a fixed number)."""
    doc = open_line(page, line_client, PHONE)
    planting = page.locator('svg#floor-phone [data-station="planting"] text').all_text_contents()
    assert "ideas you're planning" in planting
    assert "with the lead" in planting
    n = doc["field"]["planting"]
    assert f"{n} in talks" in planting


def test_legend_says_faded_dashed_and_replay_counts(page, line_client):
    """The legend contains "faded, dashed: waits for another ticket" and "a replay counts its
    own day"."""
    open_line(page, line_client)
    legend = re.search(
        r'<div class="legend">(.*?)</div>', page.locator("#line-live").inner_html(), re.S
    )
    assert legend is not None
    text = unescape(re.sub(r"<[^>]+>", " ", legend.group(1)))
    assert "faded, dashed: waits for another ticket" in text
    assert "a replay counts its own day" in text


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_developer_crate_fill_differs_from_lead_and_checks(page, line_client, scheme):
    """A developer crate's computed fill differs from the lead crate's and from the checks
    light's, in both themes."""
    page.emulate_media(color_scheme=scheme)
    open_line(page, line_client)
    dev_fill = page.locator("svg#floor .crate.developer").first.evaluate(
        "e => getComputedStyle(e).fill"
    )
    lead_fill = page.locator("svg#floor .crate.lead").first.evaluate(
        "e => getComputedStyle(e).fill"
    )
    light_fill = page.locator("svg#floor .light").first.evaluate("e => getComputedStyle(e).fill")
    assert dev_fill != lead_fill
    assert dev_fill != light_fill


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


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_planted_row_bar_and_words_pass_3_to_1_contrast_in_light_and_dark(
    page, line_client, scheme
):
    """The bar fill and its dim words each differ from what is behind them by at least 3:1.

    Light mode: the bar fill gets a darker yellow and the rows' words a stronger ink.
    Dark mode: today's colours stay unchanged.
    """
    page.emulate_media(color_scheme=scheme)
    open_line(page, line_client)

    ratio = """(bg, fg) => {
        function lum(c) {  // WCAG relative luminance, channel by channel
            const [r, g, b] = c.map(v => v / 255)
                .map(v => v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4));
            return 0.2126 * r + 0.7152 * g + 0.0722 * b;
        }
        const l1 = lum(bg), l2 = lum(fg);
        return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    }"""

    bg_rgb = page.locator("svg#floor .bar-bg").nth(0).evaluate("e => getComputedStyle(e).fill")
    fg_rgb = page.locator("svg#floor .bar-fill").nth(0).evaluate("e => getComputedStyle(e).fill")
    bar_fill = page.evaluate(
        f"""({ratio})("""
        f"""('{bg_rgb}'.match(/\\d+/g).map(Number)), """
        f"""('{fg_rgb}'.match(/\\d+/g).map(Number)))"""
    )
    assert bar_fill >= 3.0, f"bar fill contrast is {bar_fill:.2f}:1, need 3:1"

    if scheme == "dark":
        assert fg_rgb == "rgb(242, 177, 10)", f"dark mode bar fill changed: {fg_rgb}"

    dim = page.locator("svg#floor text.dim").first
    assert dim.count() > 0, "no dim text found"
    dim_fg = dim.evaluate("e => getComputedStyle(e).fill")
    # the rows' words sit on the field's plot
    plot = page.locator("svg#floor .field-plot").first.evaluate("e => getComputedStyle(e).fill")
    dim_ratio = page.evaluate(
        f"""({ratio})('{plot}'.match(/\\d+/g).map(Number), '{dim_fg}'.match(/\\d+/g).map(Number))"""
    )
    assert dim_ratio >= 3.0, f"dim text contrast is {dim_ratio:.2f}:1, need 3:1"


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


def test_idle_machine_has_idle_class_and_working_does_not(page, line_client):
    """An idle machine's group has the class idle; a working one does not."""
    open_line(page, line_client)
    doc = open_line(page, line_client)
    machines = {m["id"]: m for m in doc["machines"]}
    for mid, m in machines.items():
        cls = page.locator(f'svg#floor [data-machine="{mid}"]').get_attribute("class")
        assert cls is not None
        classes = cls.split()
        if m["state"] == "idle":
            assert "idle" in classes, f"{mid} is idle but has no idle class"
        else:
            assert "idle" not in classes, f"{mid} is {m['state']} but has idle class"


def test_idle_machine_with_merges_says_merged_today(page, line_client):
    """An idle machine with merges today shows "idle" with "N merged today" underneath."""
    page.clock.install()
    open_line(page, line_client)
    doc = block(line_client.get("/").text)
    # Find an idle non-stand-in machine and give it merges today
    idle_machine = None
    for m in doc["machines"]:
        if m["state"] == "idle" and not m.get("stand_in"):
            idle_machine = m
            break
    assert idle_machine is not None
    idle_machine["merged_today"] = 3
    page.evaluate(
        "(doc) => { "
        "  const el = document.getElementById('factory-line'); "
        "  el.textContent = JSON.stringify(doc); "
        "  document.dispatchEvent(new CustomEvent('htmx:load', { detail: { elt: document } })); "
        "}",
        doc,
    )
    text_content = page.locator(
        f'svg#floor [data-machine="{idle_machine["id"]}"] text'
    ).all_text_contents()
    assert any("idle" in t for t in text_content), (
        f"idle machine must show idle label, got: {text_content}"
    )
    assert any("merged today" in t for t in text_content), (
        f"idle machine with merges must show count, got: {text_content}"
    )


def test_idle_lead_says_next_ticket(page, line_client):
    """The idle lead shows next: <ticket> for the first lead ticket in the queue."""
    page.clock.install()
    open_line(page, line_client)
    doc = block(line_client.get("/").text)
    # Find the lead machine and give it a next_ticket
    lead_machine = None
    for m in doc["machines"]:
        if m["station"] == "lead":
            lead_machine = m
            break
    assert lead_machine is not None
    lead_machine["state"] = "idle"
    lead_machine["next_ticket"] = "fX-01-next"
    page.evaluate(
        "(doc) => { "
        "  const el = document.getElementById('factory-line'); "
        "  el.textContent = JSON.stringify(doc); "
        "  document.dispatchEvent(new CustomEvent('htmx:load', { detail: { elt: document } })); "
        "}",
        doc,
    )
    text_content = page.locator(
        f'svg#floor [data-machine="{lead_machine["id"]}"] text'
    ).all_text_contents()
    assert any("fX-01" in t for t in text_content)
    link = page.locator(f'svg#floor [data-machine="{lead_machine["id"]}"] a')
    assert link.count() == 1
    href = link.get_attribute("href")
    assert href is not None
    assert "/tickets/fX-01-next" in href


def test_idle_lead_with_merges_shows_next_ticket_and_merge_count(page, line_client):
    """The idle lead shows next ticket on the first line and merge count underneath."""
    page.clock.install()
    open_line(page, line_client)
    doc = block(line_client.get("/").text)
    # Find the lead machine and make it idle with a next ticket
    lead_machine = None
    for m in doc["machines"]:
        if m["station"] == "lead":
            lead_machine = m
            break
    assert lead_machine is not None
    lead_machine["state"] = "idle"
    lead_machine["next_ticket"] = "fX-01-next"
    lead_machine["merged_today"] = 5
    page.evaluate(
        "(doc) => { "
        "  const el = document.getElementById('factory-line'); "
        "  el.textContent = JSON.stringify(doc); "
        "  document.dispatchEvent(new CustomEvent('htmx:load', { detail: { elt: document } })); "
        "}",
        doc,
    )
    text_content = page.locator(
        f'svg#floor [data-machine="{lead_machine["id"]}"] text'
    ).all_text_contents()
    assert any("fX-01" in t for t in text_content), "lead must show next ticket"
    assert any("5 merged today" in t for t in text_content), "lead must show merge count"
    link = page.locator(f'svg#floor [data-machine="{lead_machine["id"]}"] a')
    assert link.count() == 1
    href = link.get_attribute("href")
    assert href is not None
    assert "/tickets/fX-01-next" in href


def test_idle_lead_next_ticket_text_lies_inside_lead_machine_rect(page, line_client):
    """The next-ticket link text is drawn inside the lead machine's box.

    Not at absolute (0, 16) like the bug had it.
    """
    page.clock.install()
    open_line(page, line_client)
    doc = block(line_client.get("/").text)
    lead_machine = next(m for m in doc["machines"] if m["station"] == "lead")
    lead_machine["state"] = "idle"
    lead_machine["next_ticket"] = "fX-01-next"
    lead_machine["merged_today"] = 3
    page.evaluate(
        "(doc) => { "
        "  const el = document.getElementById('factory-line'); "
        "  el.textContent = JSON.stringify(doc); "
        "  document.dispatchEvent(new CustomEvent('htmx:load', { detail: { elt: document } })); "
        "}",
        doc,
    )
    # Verify the text is inside the lead machine's rect by computing expected bounds
    # from AREAS and comparing screen coordinates converted to SVG space.
    result = page.eval_on_selector(
        "svg#floor",
        """svg => {
            const vb = svg.viewBox.baseVal;
            const svgBox = svg.getBoundingClientRect();
            const scaleX = svgBox.width / vb.width;
            const scaleY = svgBox.height / vb.height;
            const areas = {"lead": {"x": 560, "y": 120, "width": 230, "height": 170}};
            const area = areas.lead;
            const rectBox = [area.x, area.y, area.x + area.width, area.y + area.height];
            // text at (left, line) where left = x + 10, line = y + 88
            const textSvg = [area.x + 10, area.y + 88, area.x + 10 + 60, area.y + 88 + 14];
            // Convert rect to screen coords
            const rectScreen = [
                svgBox.left + rectBox[0] * scaleX,
                svgBox.top + rectBox[1] * scaleY,
                svgBox.left + rectBox[2] * scaleX,
                svgBox.top + rectBox[3] * scaleY,
            ];
            // Convert text to screen coords
            const textScreen = [
                svgBox.left + textSvg[0] * scaleX,
                svgBox.top + textSvg[1] * scaleY,
                svgBox.left + textSvg[2] * scaleX,
                svgBox.top + textSvg[3] * scaleY,
            ];
            // Get actual text box
            const textEl = svg.querySelector('[data-machine] text');
            const actualBox = textEl.getBoundingClientRect();
            const actualScreen = [actualBox.left, actualBox.top, actualBox.right, actualBox.bottom];
            const inside = (a, b) =>
                a[0] >= b[0] - 0.5 && a[1] >= b[1] - 0.5 &&
                a[2] <= b[2] + 0.5 && a[3] <= b[3] + 0.5;
            return {
                expected: inside(textScreen, rectScreen),
                actual: inside(actualScreen, rectScreen),
                expectedBox: rectScreen,
                actualBox: actualScreen,
            };
        }""",
    )
    assert result["expected"], "Expected text position should be inside lead rect"
    assert result["actual"], (
        f"Actual text box {result['actualBox']} not inside expected rect {result['expectedBox']}"
    )


def test_merged_today_sits_right_under_next_ticket(page, line_client):
    """The 'merged today' line sits directly below the next-ticket text."""
    page.clock.install()
    open_line(page, line_client)
    doc = block(line_client.get("/").text)
    lead_machine = next(m for m in doc["machines"] if m["station"] == "lead")
    lead_machine["state"] = "idle"
    lead_machine["next_ticket"] = "fX-01-next"
    lead_machine["merged_today"] = 3
    page.evaluate(
        "(doc) => { "
        "  const el = document.getElementById('factory-line'); "
        "  el.textContent = JSON.stringify(doc); "
        "  document.dispatchEvent(new CustomEvent('htmx:load', { detail: { elt: document } })); "
        "}",
        doc,
    )
    text_content = page.locator(
        f'svg#floor [data-machine="{lead_machine["id"]}"] text'
    ).all_text_contents()
    ticket_text = next(t for t in text_content if "next:" in t)
    merge_text = next(t for t in text_content if "merged today" in t)
    ticket_box = (
        page.locator(f'svg#floor [data-machine="{lead_machine["id"]}"] text')
        .filter(has_text=ticket_text)
        .first.evaluate(
            "e => { "
            "const r = e.getBoundingClientRect(); "
            "return [r.left, r.top, r.right, r.bottom]; }"
        )
    )
    merge_box = (
        page.locator(f'svg#floor [data-machine="{lead_machine["id"]}"] text')
        .filter(has_text=merge_text)
        .first.evaluate(
            "e => { "
            "const r = e.getBoundingClientRect(); "
            "return [r.left, r.top, r.right, r.bottom]; }"
        )
    )
    assert merge_box[1] > ticket_box[1], "merged today should be below the ticket text"
    assert abs(merge_box[0] - ticket_box[0]) < 2, "merged today should align with the ticket text"


# --- machines and belts (f3-20) ----------------------------------------------------------------


# Playwright can't send back live objects (getAnimations, getComputedStyle): ask in the page.
PLAYING = "els => els.map(e => e.getAnimations().map(a => a.playState).join(' '))"
LOOKS = "e => ((s) => [s.stroke, s.strokeDasharray, s.opacity])(getComputedStyle(e))"
STYLE = "els => els.map(e => getComputedStyle(e)[{!r}])"
ROLLER = "rgb(242, 177, 10)"  # the mock-up's #f2b10a


def test_local_and_cloud_machine_plates_differ(page, line_client):
    """Owner, 2026-10-03: "The cloud vs local label was clear, ... the rating of the model was
    clear." A solid LOCAL plate, an outlined CLOUD one, each with its rating."""
    doc = open_line(page, line_client)
    shop = [m for m in doc["machines"] if m["station"] in ("developers", "reviewers")]
    local = next(m for m in shop if m["where"] == "local GPU")
    cloud = next(m for m in shop if m["where"] != "local GPU")
    for m, kind in ((local, "local"), (cloud, "cloud")):
        plate = page.locator(f'svg#floor [data-machine="{m["id"]}"] rect.plate')
        assert plate.get_attribute("class") == f"plate {kind}"
        words = page.locator(f'svg#floor [data-machine="{m["id"]}"] text.ptext').text_content()
        rated = "not rated yet" if m["rating"] == "" else m["rating"]
        assert words == f"{m['where'].upper()} · {rated}"
    looks = [
        page.locator(f'svg#floor [data-machine="{m["id"]}"] rect.plate').evaluate(
            "e => getComputedStyle(e).fill"
        )
        for m in (local, cloud)
    ]
    assert looks[0] != looks[1]


def test_a_planted_row_with_null_title_says_its_key_alone(page, line_client):
    """A row whose title is null (the live runner never writes it) shows just its key,
    without " · "."""
    page.clock.install()
    doc = open_line(page, line_client)
    doc["field"]["rows"][0]["title"] = None
    page.evaluate(
        "(d) => { "
        "  const el = document.getElementById('factory-line'); "
        "  const cur = JSON.parse(el.textContent); "
        "  cur.field = { ...cur.field, rows: d.field.rows }; "
        "  el.textContent = JSON.stringify(cur); "
        "  document.dispatchEvent(new CustomEvent('htmx:load', { detail: { elt: document } })); "
        "}",
        doc,
    )
    first_row = page.locator('svg#floor [data-row="f1"]')
    name = first_row.locator("text").first.text_content()
    assert name is not None
    assert name.startswith("F1")
    assert " · " not in name


def test_a_working_machine_blinks_three_lights_and_an_idle_one_none(page, line_client):
    doc = open_line(page, line_client)
    working = next(m for m in doc["machines"] if m["state"] == "working")
    idle = next(m for m in doc["machines"] if m["state"] == "idle")
    lights = f'svg#floor [data-machine="{working["id"]}"] .led'
    assert page.eval_on_selector_all(lights, PLAYING) == ["running"] * 3
    delays = page.eval_on_selector_all(lights, STYLE.format("animationDelay"))
    assert delays == ["0s", "0.15s", "0.3s"]
    assert page.locator(f'svg#floor [data-machine="{idle["id"]}"] .led').count() == 0


def test_under_reduced_motion_the_lights_stay_lit_and_still(page, line_client):
    page.emulate_media(reduced_motion="reduce")
    open_line(page, line_client)
    assert page.eval_on_selector_all("svg#floor .led", PLAYING) == [""] * 3
    assert page.eval_on_selector_all("svg#floor .led", STYLE.format("opacity")) == ["1"] * 3


def test_belts_roll_yellow_where_work_went_today(page, line_client):
    """Owner, 2026-10-03: "I like the yellow dotted lines." Still and dimmer where work went
    today, marching where it goes now, grey where nothing went."""
    doc = open_line(page, line_client)
    found = {b["id"]: b for b in doc["belts"]}
    went = next(i for i, b in found.items() if b["today"] and not b["carrying"])
    quiet = next(i for i, b in found.items() if not b["today"] and not b["carrying"])

    def rollers(belt: str) -> str:
        return f'svg#floor [data-belt="{belt}"] .rollers'

    stroke, dashes, opacity = page.locator(rollers(went)).evaluate(LOOKS)
    assert (stroke, dashes) == (ROLLER, "2px, 7px") and float(opacity) < 1
    assert page.eval_on_selector_all(rollers(went), PLAYING) == [""]
    assert page.locator(rollers("queue→developers")).evaluate(LOOKS)[::2] == [ROLLER, "1"]
    assert page.eval_on_selector_all(rollers("queue→developers"), PLAYING) == ["running"]
    assert page.locator(rollers(quiet)).evaluate(LOOKS)[0] != ROLLER


# --- refreshing in place (f3-17) -------------------------------------------------------------

MARK = """() => {
    const floor = document.getElementById("floor");
    const nodes = [floor, ...floor.querySelectorAll("*")];
    nodes.forEach((node) => { node.marked = true; });
    return nodes.length;
}"""
MARKED = """() => {
    const floor = document.getElementById("floor");
    return [floor, ...floor.querySelectorAll("*")].filter((node) => !node.marked).length;
}"""
ROLLERS = 'svg#floor [data-belt="queue→developers"] .rollers'


def later(client: TestClient, merged: int) -> dict[str, Any]:
    """The page's document with ``merged`` more crates through the checks today."""
    doc = block(client.get("/").text)
    for b in doc["belts"]:
        if b["id"] == "checks→merged":
            b["today"] += merged
    return doc


def test_an_unchanged_document_leaves_every_node_of_the_floor_in_place(page, line_client):
    """2026-10-03, the owner: "the factory on the homepage refreshes every 5 seconds and gets
    flicky every 5 seconds". Two refreshes later, every node is still the one first drawn."""
    page.clock.install()
    open_line(page, line_client)
    assert page.evaluate(MARK) > 100
    refresh(page)
    refresh(page)
    assert page.evaluate(MARKED) == 0
    assert page.locator("section#line-live").count() == 1


def test_a_carrying_belt_keeps_rolling_across_a_refresh(page, line_client):
    """2026-10-03, the owner: "factory lines currently don't move": every refresh drew new
    rollers, so their animation started over every 5 s."""
    page.clock.install()
    doc = open_line(page, line_client, live=[later(line_client, merged=1)])
    rollers = page.locator(ROLLERS)
    rollers.evaluate("e => { window.rolling = e.getAnimations()[0]; }")
    assert page.evaluate("() => window.rolling.playState") == "running"
    refresh(page)
    counted = belts(doc)["checks→merged"]["today"] + 1
    assert page.locator('svg#floor [data-belt="checks→merged"] text').text_content() == (
        f"merged · {counted} today"
    )  # drawn again, in place
    assert rollers.evaluate(
        """e => {
            const now = e.getAnimations();
            return now.length === 1 && now[0] === window.rolling && now[0].playState === "running";
        }"""
    )


def test_opening_the_page_doesnt_flash_the_checks_light_a_later_merge_does(page, line_client):
    """f4-21's finding: the first draw took today's checks count for a new result."""
    page.clock.install()
    page.add_init_script(FLASHES)
    doc = open_line(page, line_client, live=[later(line_client, merged=0), later(line_client, 1)])
    assert belts(doc)["checks→merged"]["today"] > 0
    assert page.evaluate("() => window.flashes") == []
    refresh(page)  # the same counts
    assert page.evaluate("() => window.flashes") == []
    refresh(page)
    assert set(page.evaluate("() => window.flashes")) == {"light flash-green"}


# The class of a checks light that flashes, from the page's first script on (once per record).
FLASHES = """
window.flashes = [];
new MutationObserver((changes) => {
    for (const change of changes) {
        const nodes = change.type === "attributes" ? [change.target] : [...change.addedNodes];
        for (const node of nodes.filter((n) => n instanceof Element)) {
            for (const light of [node, ...node.querySelectorAll(".light")]) {
                const cls = light.getAttribute("class") || "";
                if (light.matches(".light") && cls.includes("flash")) window.flashes.push(cls);
            }
        }
    }
}).observe(document, { subtree: true, childList: true, attributeFilter: ["class"] });
"""


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


def test_on_a_phone_the_replay_bar_sits_on_screen_with_44_px_controls(page, night_db):
    size = {"width": 390, "height": 844}
    open_line(page, night_client(night_db), size)
    bar = page.locator("#replay")
    page.click("#replay-start")
    page.wait_for_selector("#replay-live", state="visible")
    # while replaying at 390 × 844, the whole bar is on screen
    bar.scroll_into_view_if_needed()
    box = bar.bounding_box()
    assert box is not None
    assert box["y"] + box["height"] <= size["height"] + 1
    controls = page.locator("#replay button, #replay select")
    assert controls.count() == 7  # Replay, its stretch, Play, ◀, ▶, the speed, Back to live
    for n in range(controls.count()):
        found = controls.nth(n).bounding_box()
        assert found is not None and found["width"] >= 44 and found["height"] >= 44, n
    page.click("#replay-live")
    page.wait_for_selector("#replay-controls", state="hidden")


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


def start_replay(page, night_db, size: dict[str, int] | None = None) -> list[dict[str, Any]]:
    """The fixture night's line opened and its overnight replay loaded; returns its events,
    from the route, in the server's zone."""
    client = night_client(night_db)
    open_line(page, client, size)
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


def test_a_failed_check_flashes_the_phone_floors_light(page, night_db):
    events = start_replay(page, night_db, PHONE)
    failed = next(n for n, e in enumerate(events) if e["kind"] == "check" and not e["passed"])

    for _ in range(failed + 1):
        page.click("#replay-next")
    assert page.locator("svg#floor-phone .light.flash-red").count() == 1
    assert page.locator("svg#floor .light.flash-red").count() == 0


# --- crate card (f3-19) --------------------------------------------------------------------


def test_clicking_a_queued_crate_shows_the_card_with_ticket_id_and_title(page, line_client):
    """A click on a queued crate opens the card showing its ticket id linking to /tickets/<id>
    and its title; Escape hides it."""
    page.clock.install()
    open_line(page, line_client)
    page.wait_for_selector("svg#floor [data-queue-crate]")
    queue_crates = page.eval_on_selector_all(
        "svg#floor [data-queue-crate]", "els => els.map(e => e.dataset.queueCrate)"
    )
    first = queue_crates[0]
    page.click(f'svg#floor [data-queue-crate="{first}"]')
    card = page.locator("#crate-card")
    assert not card.is_hidden()
    card_href = card.locator("a").get_attribute("href")
    assert card_href is not None
    assert card_href.startswith("/tickets/")
    assert first in card_href
    assert first in card.text_content() or first in (card.locator("a").text_content() or "")
    page.keyboard.press("Escape")
    assert card.is_hidden()


def test_tapping_a_crate_on_the_phone_floor_shows_the_card(page, line_client):
    """At 390 px wide, tapping a crate on the phone floor shows the card."""
    page.clock.install()
    open_line(page, line_client, PHONE)
    page.wait_for_selector("svg#floor-phone [data-queue-crate]")
    phone_crates = page.eval_on_selector_all(
        "svg#floor-phone [data-queue-crate]", "els => els.map(e => e.dataset.queueCrate)"
    )
    first = phone_crates[0]
    page.dispatch_event(f'svg#floor-phone [data-queue-crate="{first}"]', "click")
    card = page.locator("#crate-card")
    assert not card.is_hidden()
    card_href = card.locator("a").get_attribute("href")
    assert card_href is not None
    assert card_href.startswith("/tickets/")
    assert first in card_href


def test_at_390_the_card_is_a_bottom_sheet_without_scrolling(page, line_client):
    """At 390 px, tapping a working crate shows the card inside the viewport without scrolling,
    the ticket link is visible, the Close button hides it, and a tap outside also hides it."""
    page.clock.install()
    open_line(page, line_client, {"width": 390, "height": 1200})
    page.wait_for_selector("svg#floor-phone [data-queue-crate]")
    crate = page.locator("svg#floor-phone [data-queue-crate]").first
    crate.click()
    card = page.locator("#crate-card")
    assert not card.is_hidden()
    box = card.bounding_box()
    assert box is not None
    assert box["x"] >= 0
    assert box["x"] + box["width"] <= 390 + 1
    assert box["y"] + box["height"] <= 1200 + 1
    assert card.locator("a").count() >= 1
    assert card.locator("button.card-close").count() == 1
    page.click("button.card-close")
    assert card.is_hidden()
    # Tap outside also hides it
    page.locator("svg#floor-phone [data-queue-crate]").first.click()
    assert not card.is_hidden()
    page.mouse.click(0, 0)
    assert card.is_hidden()


def test_at_1440_the_card_is_under_the_floor(page, line_client):
    """At 1440 px the card is under the floor, as before, with no Close button."""
    page.clock.install()
    open_line(page, line_client, {"width": 1440, "height": 900})
    page.wait_for_selector("svg#floor [data-merged]")
    merged_crates = page.eval_on_selector_all(
        "svg#floor [data-merged]", "els => els.map(e => e.dataset.merged)"
    )
    page.click(f'svg#floor [data-merged="{merged_crates[0]}"]')
    card = page.locator("#crate-card")
    assert not card.is_hidden()
    floor_box = page.locator("svg#floor").bounding_box()
    card_box = card.bounding_box()
    assert floor_box is not None and card_box is not None
    assert card_box["y"] > floor_box["y"] + floor_box["height"]
    assert card.locator("button.card-close").count() == 0


def test_the_card_stays_open_across_a_live_refresh(page, line_client):
    """A refresh that redraws the floor leaves an open card open."""
    page.clock.install()
    doc = block(line_client.get("/").text)
    open_line(page, line_client, live=[doc])
    page.wait_for_selector("svg#floor [data-queue-crate]")
    queue_crates = page.eval_on_selector_all(
        "svg#floor [data-queue-crate]", "els => els.map(e => e.dataset.queueCrate)"
    )
    first = queue_crates[0]
    page.click(f'svg#floor [data-queue-crate="{first}"]')
    card = page.locator("#crate-card")
    assert not card.is_hidden()
    page.evaluate("() => { window.liveIdle = () => true; }")
    refresh(page)
    assert not card.is_hidden()
    card_href = card.locator("a").get_attribute("href")
    assert card_href is not None
    assert first in card_href


def test_the_card_shows_the_title_as_text_with_html_characters(page, line_client):
    """f3-19: a title such as `Fix <b>x</b> & y` is rendered as markup, not shown as written."""
    page.clock.install()
    open_line(page, line_client)
    doc = block(line_client.get("/").text)
    doc["queue"].append(
        {
            "ticket": "fX-00-escape",
            "title": "Fix <b>x</b> & y",
            "kind": "developer",
            "number": 99,
            "waits": [],
        }
    )
    page.evaluate(
        "(doc) => { "
        "  const el = document.getElementById('factory-line'); "
        "  const cur = JSON.parse(el.textContent); "
        "  const newQueue = [...cur.queue]; "
        "  newQueue.push(doc.queue[doc.queue.length - 1]); "
        "  el.textContent = JSON.stringify({ ...cur, queue: newQueue }); "
        "  document.dispatchEvent(new CustomEvent('htmx:load', { detail: { elt: document } })); "
        "}",
        doc,
    )
    page.wait_for_selector("svg#floor [data-queue-crate='fX-00-escape']")
    page.click("svg#floor [data-queue-crate='fX-00-escape']")
    card = page.locator("#crate-card")
    assert not card.is_hidden()
    title_text = card.locator(".card-title").text_content()
    assert "<b>x</b> & y" in title_text
    assert "Fix " in title_text
    page.keyboard.press("Escape")


def test_a_queued_crate_that_waits_shows_what_it_waits_for(page, line_client):
    """A queued crate that waits shows what it waits for in the card."""
    page.clock.install()
    open_line(page, line_client)
    page.wait_for_selector("svg#floor [data-queue-crate]")
    crate = page.locator("svg#floor [data-queue-crate='f5-04-after']")
    crate.click()
    card = page.locator("#crate-card")
    assert not card.is_hidden()
    waits = card.locator(".card-waits").text_content()
    assert waits is not None and "f5-03-next" in waits


def test_a_crate_on_a_machine_shows_agent_attempt_and_minutes(page, line_client):
    """A crate on a machine shows its agent, attempt and minutes."""
    page.clock.install()
    open_line(page, line_client)
    doc = block(line_client.get("/").text)
    # Find the working machine and modify its crate
    for m in doc["machines"]:
        if m["state"] == "working" and m.get("crate"):
            m["crate"]["ticket"] = "fM-01-mine"
            m["crate"]["title"] = "Machine crate."
            m["crate"]["kind"] = "developer"
            m["crate"]["role"] = "developer"
            m["crate"]["attempt"] = 3
            m["crate"]["minutes"] = 42
            m["name"] = "Opus"
            break
    page.evaluate(
        "(doc) => { "
        "  const el = document.getElementById('factory-line'); "
        "  el.textContent = JSON.stringify(doc); "
        "  document.dispatchEvent(new CustomEvent('htmx:load', { detail: { elt: document } })); "
        "}",
        doc,
    )
    page.wait_for_selector('svg#floor [data-crate="fM-01-mine"]')
    page.click('svg#floor [data-crate="fM-01-mine"]')
    card = page.locator("#crate-card")
    assert not card.is_hidden()
    card_text = card.text_content() or ""
    assert "Opus" in card_text
    assert "3" in card_text
    assert "42" in card_text
    page.keyboard.press("Escape")


def test_a_batch_crate_shows_its_role_and_has_no_link(page, line_client):
    """A batch crate shows its role and has no link."""
    page.clock.install()
    open_line(page, line_client)
    doc = block(line_client.get("/").text)
    # Set the machine's crate to have no ticket (batch)
    for m in doc["machines"]:
        if m["state"] == "working" and m.get("crate"):
            m["crate"]["ticket"] = None
            m["crate"]["role"] = "reviewer"
            m["crate"]["title"] = "Batch review."
            m["crate"]["kind"] = "checkpoint"
            break
    page.evaluate(
        "(doc) => { "
        "  const el = document.getElementById('factory-line'); "
        "  el.textContent = JSON.stringify(doc); "
        "  document.dispatchEvent(new CustomEvent('htmx:load', { detail: { elt: document } })); "
        "}",
        doc,
    )
    # When ticket is null, data-crate is set to role
    page.wait_for_selector('svg#floor [data-crate="reviewer"]')
    page.click('svg#floor [data-crate="reviewer"]')
    card = page.locator("#crate-card")
    assert not card.is_hidden()
    assert card.locator("a").count() == 0
    card_text = card.text_content() or ""
    assert "reviewer" in card_text
    page.keyboard.press("Escape")


def test_a_queued_review_is_a_batch_crate_with_its_milestone(page, line_client):
    """f4-20: a due review waits in the queue like a ticket, as a batch crate."""
    page.clock.install()
    open_line(page, line_client)
    doc = block(line_client.get("/").text)
    review: dict[str, Any] = {
        "ticket": None,
        "role": "review",
        "title": "review F8",
        "kind": "batch",
        "milestone": "f8",
        "waits": [],
    }
    doc["queue"] = [review, *doc["queue"]]
    for n, crate in enumerate(doc["queue"], start=1):
        crate["number"] = n
    page.evaluate(
        "(doc) => { "
        "  const el = document.getElementById('factory-line'); "
        "  el.textContent = JSON.stringify(doc); "
        "  document.dispatchEvent(new CustomEvent('htmx:load', { detail: { elt: document } })); "
        "}",
        doc,
    )
    crate = page.locator('svg#floor [data-queue-crate="review"]')
    crate.wait_for()
    assert crate.locator("rect").get_attribute("class") == "crate batch"
    assert crate.locator("title").text_content() == "1 review F8"
    crate.click()
    card = page.locator("#crate-card")
    assert not card.is_hidden()
    assert card.locator("a").count() == 0
    assert "review F8" in (card.text_content() or "")


def test_enter_opens_the_card_and_click_outside_closes_it(page, line_client):
    """Enter on a focused crate opens the card, and a click outside the crates closes it."""
    page.clock.install()
    open_line(page, line_client)
    page.wait_for_selector("svg#floor [data-queue-crate]")
    crate = page.locator("svg#floor [data-queue-crate]").first
    crate.focus()
    crate.press("Enter")
    card = page.locator("#crate-card")
    assert not card.is_hidden()
    assert card.locator("a").count() >= 1
    page.mouse.click(0, 0)
    assert card.is_hidden()


def test_the_cards_link_keeps_markup_in_the_project_as_text(page, line_client):
    """f3 review (f3-F1): the card's link took ``?project=`` from the address as HTML, so a link
    such as ``/?project="><img onerror=…>`` ran script in the dashboard."""
    page.clock.install()
    open_line(page, line_client)
    hostile = '"><img src=x onerror="window.pwned=1">'
    page.goto(f"{ORIGIN}/?{urlencode({'project': hostile})}")
    crate = page.locator("svg#floor [data-queue-crate]").first
    first = crate.get_attribute("data-queue-crate")
    crate.click()
    card = page.locator("#crate-card")
    assert card.locator("img").count() == 0
    assert page.evaluate("() => window.pwned") is None
    href = card.locator("a").get_attribute("href")
    assert href == f"/tickets/{first}?{urlencode({'project': hostile})}"
    assert card.locator("a").text_content() == first


def test_the_card_reads_the_document_the_floor_drew_last(page, line_client):
    """f3 review (f3-F2): the card kept the document of the first crate opened, so a crate
    queued by a later refresh opened nothing, and an open card never moved on."""
    page.clock.install()
    first = block(line_client.get("/").text)
    later_doc = json.loads(json.dumps(first))
    later_doc["queue"].append(
        {"ticket": "f9-09-new", "title": "Queued later.", "kind": "lead", "number": 99, "waits": []}
    )
    for m in later_doc["machines"]:
        if m["crate"]:
            m["crate"]["minutes"] += 5
    working = next(m for m in first["machines"] if m["crate"])
    open_line(page, line_client, live=[first, later_doc])
    page.click(f'svg#floor [data-crate="{working["crate"]["ticket"]}"]')
    card = page.locator("#crate-card")
    assert f"{working['crate']['minutes']} min" in (card.text_content() or "")
    page.evaluate("() => { window.liveIdle = () => true; }")
    refresh(page)
    refresh(page)
    assert f"{working['crate']['minutes'] + 5} min" in (card.text_content() or "")
    page.keyboard.press("Escape")
    page.click('svg#floor [data-queue-crate="f9-09-new"]')
    assert card.locator(".card-title").text_content() == "Queued later."


def set_aside(page, later: list[dict[str, Any]]) -> None:
    """Redraw the floor with ``later`` as the field's set-aside tickets."""
    page.evaluate(
        "(later) => { "
        "  const el = document.getElementById('factory-line'); "
        "  const cur = JSON.parse(el.textContent); "
        "  const field = { ...cur.field, later, seeds: later.length }; "
        "  el.textContent = JSON.stringify({ ...cur, field }); "
        "  document.dispatchEvent(new CustomEvent('htmx:load', { detail: { elt: document } })); "
        "}",
        later,
    )


def test_tapping_the_seeds_on_a_phone_lists_the_set_aside_tickets_in_the_sheet(page, line_client):
    """The owner, 2026-10-06: "the seeds set aside are not really navigable on mobile": the tap
    left the floor for the whole tickets page. Now it opens the sheet, one link per ticket."""
    page.clock.install()
    open_line(page, line_client, PHONE, query="project=coucou")
    later: list[dict[str, Any]] = [
        {"ticket": "f9-04-later", "title": "Goal of f9-04-later."},
        {"ticket": "f9-05-markup", "title": "Fix <b>x</b> & y"},
        {"ticket": "f9-06-untitled", "title": None},
    ]
    set_aside(page, later)
    page.locator('svg#floor-phone [data-station="seeds"]').click()
    assert page.url == f"{ORIGIN}/?project=coucou"  # still on the floor
    card = page.locator("#crate-card")
    assert not card.is_hidden()
    links = card.locator("a")
    assert [links.nth(n).get_attribute("href") for n in range(links.count())] == [
        "/tickets/f9-04-later?project=coucou",
        "/tickets/f9-05-markup?project=coucou",
        "/tickets/f9-06-untitled?project=coucou",
        "/tickets?project=coucou#later",
    ]
    assert links.all_text_contents() == [
        "f9-04-later",
        "f9-05-markup",
        "f9-06-untitled",
        "All set-aside tickets",
    ]
    assert card.locator("li .card-title").all_text_contents() == [
        "Goal of f9-04-later.",
        "Fix <b>x</b> & y",  # as written: text, never markup (f3-F1)
    ]
    assert card.locator("b").count() == 0
    box = card.bounding_box()
    assert box is not None and box["y"] >= 0 and box["y"] + box["height"] <= PHONE["height"] + 1
    # The sheet covers the floor, so the page's layout check can't run with it open: each
    # link is on screen, on its own line, clear of the Close button.
    close = page.locator("button.card-close").bounding_box()
    boxes = [links.nth(n).bounding_box() for n in range(links.count())]
    assert close is not None and all(b is not None for b in boxes)
    for above, below in pairwise(boxes):
        assert above["y"] + above["height"] <= below["y"] + 0.5
    for b in boxes:
        assert b["x"] >= 0 and b["x"] + b["width"] <= PHONE["width"] and b["height"] >= 24
        assert b["y"] >= close["y"] + close["height"] or b["x"] + b["width"] <= close["x"]
    # A refresh that changes the list changes the open sheet, and Close shuts it
    set_aside(page, later[:1])
    assert card.locator("li").count() == 1
    page.click("button.card-close")
    assert card.is_hidden()
    set_aside(page, later)
    assert card.is_hidden()


def test_a_long_list_of_seeds_scrolls_inside_the_sheet(page, line_client):
    page.clock.install()
    open_line(page, line_client, {"width": 390, "height": 700})
    set_aside(page, [{"ticket": f"f9-{n}-later", "title": f"Goal {n}."} for n in range(40, 100)])
    page.locator('svg#floor-phone [data-station="seeds"]').click()
    card = page.locator("#crate-card")
    box = card.bounding_box()
    assert box is not None and box["y"] >= 0 and box["y"] + box["height"] <= 701
    last = card.locator("a", has_text="All set-aside tickets")
    last.scroll_into_view_if_needed()
    assert last.is_visible()
    end = last.bounding_box()
    assert end is not None and box["y"] <= end["y"] and end["y"] + end["height"] <= 701


def test_the_seeds_card_keeps_markup_in_the_project_as_text(page, line_client):
    """As the crate card's link (f3-F1): ``?project=`` is the address's, so it could hold markup."""
    page.clock.install()
    hostile = '"><img src=x onerror="window.pwned=1">'
    open_line(page, line_client, query=urlencode({"project": hostile}))
    set_aside(page, [{"ticket": "f9-04-later", "title": "Goal."}])
    page.click('svg#floor [data-station="seeds"]')
    card = page.locator("#crate-card")
    assert card.locator("img").count() == 0
    assert page.evaluate("() => window.pwned") is None
    links = card.locator("a")
    assert [links.nth(n).get_attribute("href") for n in range(links.count())] == [
        f"/tickets/f9-04-later?{urlencode({'project': hostile})}",
        f"/tickets?{urlencode({'project': hostile})}#later",
    ]


def test_planted_row_links_to_milestone_and_seeds_to_set_aside_tickets(page, line_client):
    """Tapping a planted row opens its milestone's page. The seeds open the card under the floor
    (Enter too, and a click outside closes it), whose last link opens the Set aside tickets. Both
    keep the page's ``?project=`` query, as the crate card's link does."""
    page.clock.install()
    open_line(page, line_client, query="project=coucou")
    page.wait_for_selector("svg#floor [data-row]")
    row_group = page.locator("svg#floor [data-row]").first
    first_row_key = row_group.get_attribute("data-row")
    assert first_row_key is not None
    # Click the row and check navigation to the milestone page
    with page.expect_navigation():
        page.click(f'svg#floor [data-row="{first_row_key}"]')
    assert page.url.endswith(f"/milestones/{first_row_key}?project=coucou")
    # Re-open the line page and click the seeds
    open_line(page, line_client, query="project=coucou")
    page.wait_for_selector("svg#floor [data-station='seeds']")
    seeds = page.locator("svg#floor [data-station='seeds']")
    card = page.locator("#crate-card")
    seeds.focus()
    seeds.press("Enter")
    assert not card.is_hidden()
    page.mouse.click(0, 0)
    assert card.is_hidden()
    seeds.click()
    floor_box = page.locator("svg#floor").bounding_box()
    card_box = card.bounding_box()
    assert floor_box is not None and card_box is not None
    assert card_box["y"] > floor_box["y"] + floor_box["height"]
    assert card.locator("button.card-close").count() == 0
    assert card.locator("li a").all_text_contents() == ["f9-04-later"]
    assert card.locator("li a").get_attribute("href") == "/tickets/f9-04-later?project=coucou"
    with page.expect_navigation():
        card.locator("a", has_text="All set-aside tickets").click()
    assert page.url == "http://127.0.0.1:8765/tickets?project=coucou#later"


def test_stash_tiles_show_short_key_and_link_to_milestone(page, line_client):
    """Each stash tile shows only its short key (before the first dash), fits inside 52 px,
    links to its milestone with ?project=, and its <title> holds the full key."""
    page.clock.install()
    open_line(page, line_client, query="project=coucou")
    page.wait_for_selector("svg#floor [data-stash]")
    stash_tiles = page.eval_on_selector_all(
        "svg#floor [data-stash]", "els => els.map(e => e.dataset.stash)"
    )
    assert len(stash_tiles) >= 2
    for full_key in stash_tiles:
        tile = page.locator(f'svg#floor [data-stash="{full_key}"]')
        tile_box = tile.bounding_box()
        assert tile_box is not None
        assert tile_box["width"] <= 52
        text_el = tile.locator("text")
        text_content = text_el.first.text_content()
        assert text_content is not None
        assert text_content == full_key.split("-")[0].upper()
        title_el = tile.locator("title")
        title_content = title_el.first.text_content()
        assert title_content == full_key.upper()
        link = tile.locator("a")
        assert link.count() == 1
        href = link.get_attribute("href")
        assert href is not None
        assert f"/milestones/{full_key}?project=coucou" in href


def test_ripe_lines_link_to_milestone(page, line_client):
    """Each ripe line links to its milestone with ?project= kept."""
    page.clock.install()
    open_line(page, line_client, query="project=coucou")
    page.wait_for_selector("svg#floor [data-ripe]")
    ripe_keys = page.eval_on_selector_all(
        "svg#floor [data-ripe]", "els => els.map(e => e.dataset.ripe)"
    )
    for key in ripe_keys:
        ripe_line = page.locator(f'svg#floor [data-ripe="{key}"]')
        link = ripe_line.locator("a")
        assert link.count() == 1
        href = link.get_attribute("href")
        assert href is not None
        assert f"/milestones/{key}?project=coucou" in href


def test_planting_links_to_planning(page, line_client):
    """Tapping the planting station opens the planning page with ?project= kept."""
    page.clock.install()
    open_line(page, line_client, query="project=coucou")
    page.wait_for_selector("svg#floor [data-station='planting']")
    planting_station = page.locator('svg#floor [data-station="planting"]')
    link = planting_station.locator("a")
    assert link.count() == 1
    href = link.get_attribute("href")
    assert href is not None
    assert "/planning?project=coucou" in href


def test_merged_crate_opens_card_with_ticket_link(page, line_client):
    """Tapping a merged crate opens the crate card with its ticket's link."""
    page.clock.install()
    open_line(page, line_client)
    page.wait_for_selector("svg#floor [data-merged]")
    merged_crates = page.eval_on_selector_all(
        "svg#floor [data-merged]", "els => els.map(e => e.dataset.merged)"
    )
    assert len(merged_crates) >= 1
    first_merged = merged_crates[0]
    page.click(f'svg#floor [data-merged="{first_merged}"]')
    card = page.locator("#crate-card")
    assert not card.is_hidden()
    card_href = card.locator("a").get_attribute("href")
    assert card_href is not None
    assert "/tickets/" in card_href
    assert first_merged in card_href
    page.keyboard.press("Escape")


def test_floor_links_layout_at_phone_and_display(page, line_client):
    """Every link on the floor passes the layout check at 390 px and 1440 px."""
    from tests.browser.conftest import layout_problems

    # Phone size
    open_line(page, line_client, {"width": 390, "height": 1200})
    assert layout_problems(page) == []
    # Display size
    open_line(page, line_client, {"width": 1440, "height": 900})
    assert layout_problems(page) == []


def test_sprout_path_is_the_original_d_attribute(page, line_client):
    """The sprout path must be exactly what it was before f9-03; a test would fail if it changes."""
    page.clock.install()
    open_line(page, line_client)
    d = page.locator("svg#floor .sprout").first.get_attribute("d")
    assert d is not None
    # Check the curve commands (the relative part that defines the leaf shape)
    assert "c-8 0-11-4-11-9 8 0 11 4 11 9" in d
    assert "c0-7 3-10 10-10 0 7-3 10-10 10" in d


def test_each_row_sits_inside_the_rows_station(page, line_client):
    """Each [data-row] sits inside g[data-station="rows"] again: a link inside the station,
    around the row group."""
    page.clock.install()
    open_line(page, line_client)
    page.wait_for_selector("svg#floor [data-row]")
    inside = page.evaluate("""() => {
        const rows = document.querySelectorAll('svg#floor [data-row]');
        return Array.from(rows).every((row) => {
            const link = row.closest('a');
            if (!link) return false;
            const station = link.closest('[data-station="rows"]');
            return station !== null;
        });
    }""")
    assert inside


# --- allowance rows layout (f4-34)---------------------------------------------------------------


def test_allowance_rows_side_by_side_at_desktop_and_stacked_at_phone(page, allowance_client):
    """f9-17: on desktop the bars are side by side;
    on phone each window is one row stacked vertically."""
    ORIGIN = "http://127.0.0.1:8765"
    ROWS = "#allowance .allow > div"

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

    # Desktop: rows side by side (bars layout).
    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto(ORIGIN + "/")
    page.wait_for_selector(ROWS)
    boxes = page.eval_on_selector_all(ROWS, "els => els.map(e => e.getBoundingClientRect())")
    assert len(boxes) >= 2
    for i in range(len(boxes) - 1):
        assert abs(boxes[i]["y"] - boxes[i + 1]["y"]) < 4

    # Phone: rows stacked vertically (different y).
    page.set_viewport_size({"width": 390, "height": 1200})
    page.reload()
    page.wait_for_selector(ROWS)
    boxes = page.eval_on_selector_all(ROWS, "els => els.map(e => e.getBoundingClientRect())")
    assert len(boxes) >= 2
    # At least some rows have different y (stacked)
    ys = [b["y"] for b in boxes]
    assert len(set(ys)) > 1, "rows should be stacked vertically on phone"

    # Labels and percentages visible at both sizes.
    for row in page.locator(ROWS).all():
        assert row.is_visible()
        text = row.text_content()
        assert text is not None and len(text) > 0
