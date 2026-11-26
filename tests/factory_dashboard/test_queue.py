"""The queue page (F279 D6, f279-03): the whole factory's line from the runner's stored plan."""

import re
from collections.abc import Callable
from datetime import UTC, datetime
from html import unescape
from pathlib import Path

from fastapi.testclient import TestClient

from factory_dashboard.queries import local
from runner import metrics
from runner.dispatch import FactoryPlan, PlanLine
from tests.factory_dashboard.conftest import OTHER, PROJECT

AT = datetime(2026, 10, 2, 11, 40, tzinfo=UTC)
SENTENCE = "Over pace: developers first, the lead when nothing else can."
FACTS = ("Claude's week 82% used, today's pace 42%", "2 developer tickets can go now, about 35 min")

LINES = (
    PlanLine(
        PROJECT,
        "checkpoint",
        "f265",
        "Claude re-checks f265-04",
        None,
        "jobs",
        None,
        "Claude re-checks f265-04",
        "f265",
    ),
    PlanLine(
        OTHER,
        "ticket",
        "m8-08-trip-by-hand",
        "The owner adds a trip by hand.",
        "developer",
        "go",
        None,
        "place 1, developer ticket",
        "m8",
    ),
    PlanLine(
        PROJECT,
        "ticket",
        "f132-02-overview-live",
        "The Overview's live part.",
        "lead",
        "go",
        "goes when nothing else can (Claude's week over its pace)",
        "early for f199-01-the-map, lead ticket",
        "f132",
        "f199-01-the-map",
        ("files: factory_dashboard/gone.py doesn't exist",),
    ),
    PlanLine(
        PROJECT,
        "ticket",
        "f132-05-floor",
        "The floor is the whole factory's.",
        "lead",
        "waits",
        "waiting on f132-02-overview-live",
        "place 2, lead ticket",
        "f132",
    ),
    PlanLine(
        PROJECT,
        "ticket",
        "f199-01-the-map",
        "A map of the factory.",
        "lead",
        "waits",
        "waiting on f132-02-overview-live, f132-05-floor",
        "place 3, lead ticket",
        "f199",
    ),
    PlanLine(
        PROJECT,
        "ticket",
        "f9-01-held",
        "Something held.",
        "developer",
        "waits",
        "waits for f8's sign-off",
        "place 4, developer ticket",
        "f9",
    ),
)


def store(db_path: Path, lines: tuple[PlanLine, ...] = LINES) -> None:
    conn = metrics.open_db(db_path)
    try:
        metrics.store_queue_plan(conn, FactoryPlan(AT, 0, SENTENCE, FACTS, lines))
    finally:
        conn.close()


def text(html: str) -> str:
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", html)).split())


def row(html: str, n: int) -> str:
    """Row ``n``'s whole list item, its details included."""
    found = re.search(rf'<li class="[a-z]+" id="row-{n}">(.*?)</details></li>', html, re.S)
    assert found, f"no row {n}"
    return found.group(1)


def section(html: str, id: str) -> str:
    found = re.search(rf'<ol class="rows" id="{id}">(.*?)\n</ol>\n</div>', html, re.S)
    assert found, f"no {id}"
    return found.group(1)


def test_the_page_shows_the_plans_sentence_facts_and_time(
    db_path: Path, serve: Callable[..., TestClient]
) -> None:
    store(db_path)
    html = serve().get("/queue").text
    mode = re.search(r'<div class="mode" id="q-mode">(.*?)</ul>', html, re.S)
    assert mode
    assert text(mode.group(1)) == f"What drives the order now {SENTENCE} {FACTS[0]} {FACTS[1]}"
    assert f"worked out at {local(AT).strftime('%H:%M')}, the runner's last pick" in html


def test_the_rows_are_numbered_in_the_plans_order_with_plate_who_card_and_why(
    db_path: Path, serve: Callable[..., TestClient]
) -> None:
    store(db_path)
    html = serve().get("/queue").text
    first = text(row(html, 1)).split(" Why here")[0]
    assert first.startswith(f"1 {PROJECT} checkpoint · f265")
    trip = row(html, 2)
    assert text(trip).startswith(
        f"2 {OTHER} m8-08-trip-by-hand The owner adds a trip by hand. a developer · M8 · place 1"
    )
    assert re.search(r'<li class="developer" id="row-2">', html)
    lead = text(row(html, 3))
    assert lead.startswith(f"3 {PROJECT} f132-02-overview-live The Overview's live part. the lead")
    # the order: jobs before what can go, in the plan's numbering
    go = text(section(html, "q-go"))
    assert go.index("m8-08-trip-by-hand") < go.index("f132-02-overview-live")
    assert "f132-05-floor" not in go


def test_the_belts_key_is_text_under_the_picture_so_a_phone_never_clips_it(
    db_path: Path, serve: Callable[..., TestClient]
) -> None:
    """Review: inside the 360-wide picture the key was cut at "the lea"."""
    store(db_path)
    html = serve().get("/queue").text
    svg = re.search(r'<svg class="conveyor".*?</svg>', html, re.S)
    assert svg and "orange: the lead" not in svg.group(0)
    key = re.search(r'</svg>\s*<p class="belt-key" id="q-belt-key">(.*?)</p>', html, re.S)
    assert key
    assert text(key.group(1)) == (
        "dashed: a job · blue: a developer · orange: the lead · tap a crate for its row"
    )


def test_a_ticket_row_opens_its_goal_waits_reason_and_preflight_with_its_projects_links(
    db_path: Path, serve: Callable[..., TestClient]
) -> None:
    store(db_path)
    html = serve(live=False).get("/queue").text
    lead = row(html, 3)
    details = text(lead.split('<div class="more-row">')[1])
    assert "Goal The Overview's live part." in details
    why = "early for f199-01-the-map, lead ticket; it goes early because f199-01-the-map waits"
    assert f"Why here {why} for it" in details
    assert "Waits for goes when nothing else can (Claude's week over its pace)" in details
    assert "Pre-flight files: factory_dashboard/gone.py doesn't exist" in details
    assert f'href="/tickets/f132-02-overview-live?project={PROJECT}"' in lead
    assert f'href="/planning/f132?project={PROJECT}"' in lead
    trip = row(html, 2)
    assert "Pre-flight no problem" in text(trip)
    assert f'href="/tickets/m8-08-trip-by-hand?project={OTHER}"' in trip
    assert f'href="/planning/m8?project={OTHER}"' in trip
    assert f"?project={PROJECT}" not in trip


def test_waiting_tickets_fold_by_the_first_ticket_they_wait_for_with_counts(
    db_path: Path, serve: Callable[..., TestClient]
) -> None:
    store(db_path)
    html = serve().get("/queue").text
    waits = section(html, "q-waits")
    fold = r'<li class="group"><details id="[^"]*"><summary>(.*?)</summary>'
    folds = re.findall(fold, waits, re.S)
    assert [text(f) for f in folds] == [
        f"for f132-02-overview-live (3) {PROJECT} 2",
        f"waits for f8's sign-off {PROJECT} 1",
    ]
    first = waits.split('<li class="group">')[1]
    assert "f132-05-floor" in first and "f199-01-the-map" in first and "f9-01-held" not in first
    # closed by default
    assert "<details open" not in waits


def test_a_pending_approve_plan_shows_on_its_way_and_goes_once_done(
    db_path: Path, serve: Callable[..., TestClient]
) -> None:
    store(db_path)
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        asked = metrics.add_request(conn, project, "approve_plan", "f279", None, AT.isoformat())
    finally:
        conn.close()
    html = serve().get("/queue").text
    ways = [text(w) for w in re.findall(r'<div class="way">(.*?)</div>', html, re.S)]
    assert f"On its way · {PROJECT} Approve plan: f279 · applied at the next pick" in ways
    conn = metrics.open_db(db_path)
    try:
        metrics.finish_request(conn, asked, AT.isoformat(), "approved")
    finally:
        conn.close()
    html = serve().get("/queue").text
    ways = [text(w) for w in re.findall(r'<div class="way">(.*?)</div>', html, re.S)]
    assert not any("Approve plan: f279" in w for w in ways)


def test_with_no_plan_stored_the_page_says_so(serve: Callable[..., TestClient]) -> None:
    response = serve().get("/queue")
    assert response.status_code == 200
    found = re.search(r'<p id="no-plan" class="sub">(.*?)</p>', response.text)
    assert found
    words = "The runner hasn&#39;t worked out a plan yet: it does at its next pick."
    assert found.group(1) == words
    assert 'id="q-go"' not in response.text


def test_the_page_reads_the_same_whichever_project_is_picked(
    db_path: Path, serve: Callable[..., TestClient]
) -> None:
    store(db_path)
    client = serve()
    mine = client.get(f"/queue?project={PROJECT}").text
    theirs = client.get(f"/queue?project={OTHER}").text
    for n in range(1, len(LINES) + 1):
        assert row(mine, n) == row(theirs, n)
    assert section(mine, "q-waits") == section(theirs, "q-waits")


def test_the_page_refreshes_every_30_s_held_by_live_idle(
    db_path: Path, serve: Callable[..., TestClient]
) -> None:
    store(db_path)
    html = serve().get("/queue").text
    live = re.search(r'<div id="queue-live"([^>]*)>', html)
    assert live
    assert 'hx-trigger="every 30s [window.liveIdle()]"' in live.group(1)
    assert 'hx-select="#queue-live"' in live.group(1)
