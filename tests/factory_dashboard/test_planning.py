"""The planning room's desk (f6-06, F6 D6): ``/planning``'s two tiles, the desk's four groups
and "Plant an idea". The rows come from ``write_planning`` in the conftest."""

import json
import re
import sqlite3
from collections.abc import Callable
from datetime import timedelta
from html import unescape
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from factory_dashboard.planning import desk
from runner import metrics
from tests.factory_dashboard.conftest import (
    LOCAL,
    NOW,
    OPUS,
    PROJECT,
    _at,
)
from tests.layout import DISPLAY, PHONE, layout_problems

ORIGIN = "http://127.0.0.1:8765"
STATIC = Path(__file__).parents[2] / "factory_dashboard" / "static"


def _write(db_path: Path, write: Callable[..., object]) -> None:
    conn = metrics.open_db(db_path)
    try:
        write(conn)
    finally:
        conn.close()


def _page(client: TestClient) -> str:
    response = client.get("/planning")
    assert response.status_code == 200
    return str(response.text)


def _groups(html: str) -> dict[str, str]:
    """Each desk group's markup by its key, in the page's order."""
    return dict(re.findall(r'<div id="desk-([a-z]+)"(.*?)</div>', html, re.S))


def _items(group: str) -> list[tuple[str, str]]:
    """A group's items: (link without the query, title)."""
    return [
        (link, unescape(title))
        for link, title in re.findall(
            r'<a href="([^"?]+)[^"]*"[^>]*>\s*<span[^>]*>([^<]*)</span>', group
        )
    ]


def _tile(html: str, tile_id: str) -> str:
    found = re.search(rf'<div id="{tile_id}"(.*?)</div>\s*(?=<div id=|</section>)', html, re.S)
    assert found, tile_id
    return unescape(re.sub(r"<[^>]+>", "", found[1]))


def test_each_group_shows_its_items_in_order(planning, serve):
    """A reply unanswered, the open proposals and a ripe card, each in its group, and the
    groups in D6's order; the thread the owner answered last is not among the answers."""
    groups = _groups(_page(serve()))
    assert list(groups) == ["answers", "proposals", "ripe", "seeds"]
    assert _items(groups["answers"]) == [("/planning/general", "General")]
    assert "the lead replied 60 min ago" in groups["answers"]
    assert _items(groups["proposals"]) == [
        ("/planning/f6/proposals/adr-20", "F6 plan: 7 tickets"),
    ]
    assert "2 key points" in groups["proposals"]
    assert _items(groups["ripe"]) == [("/planning/m4", "The web app")]
    assert _items(groups["seeds"]) == [("/planning/f9", "Parallel developers")]


def test_desk_returns_the_five_groups_in_order_empty_ones_too(db_path, db):
    """Without a thread or an idea card, the groups are still there, in order, empty but the
    ripe one: without ``write_live``'s running and ready tickets, f1 is ripe too."""
    groups = desk(db, PROJECT, NOW)
    assert [g.name for g in groups] == [
        "Didn't go through",
        "Blocked tickets",
        "Your answers wanted",
        "Proposals to review",
        "Finished, to talk through",
        "Seeds, not asked about yet",
    ]
    assert [[i.title for i in g.items] for g in groups] == [
        [],
        [],
        [],
        [],
        ["The factory measures itself", "The web app"],
        [],
    ]
    assert desk(db, "nowhere", NOW)[4].items == []


def test_an_idea_card_with_a_thread_is_not_a_seed(planning, db):
    seeds = desk(db, PROJECT, NOW)[5].items
    assert [s.title for s in seeds] == ["Parallel developers"]


@pytest.mark.parametrize(
    ("kind", "subject", "value", "done", "result", "still_open"),
    [
        # worked: the ADR is accepted, the plan isn't about it
        ("accept_adr", "f6", "20", True, "accepted .factory/adr/20-planning-room.md", ["plan"]),
        # an ADR request with another number is about another proposal
        ("accept_adr", "f6", "21", None, None, ["adr-20", "plan"]),
        # pending: the runner hasn't done it yet
        ("approve_plan", "f6", None, None, None, ["adr-20"]),
        # refused: the proposal stays open
        ("approve_plan", "f6", None, True, "plan/f6 has no draft", ["adr-20", "plan"]),
        ("send_back", "f6/adr-20", '{"text": "Shorter."}', True, "queued for the lead", ["plan"]),
        # another thread's request
        ("approve_plan", "f7", None, None, None, ["adr-20", "plan"]),
    ],
)
def test_a_proposal_the_owner_settled_is_not_among_the_proposals(
    planning, db_path, db, kind, subject, value, done, result, still_open
):
    """Open unless a request about it came after the reply and is pending or worked (D6)."""
    _write(
        db_path,
        lambda conn: conn.execute(
            "INSERT INTO owner_requests (project_id, kind, subject, value, created, done, result)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                planning,
                kind,
                subject,
                value,
                _at(timedelta(minutes=30)),
                done and NOW.isoformat(),
                result,
            ),
        ),
    )
    (item,) = desk(db, PROJECT, NOW)[3].items  # the card's parts are one item (F51 D1)
    names = {"adr-20": "ADR 20", "plan": "plan"}
    assert [name for name, way in item.parts if not way] == [names[p] for p in still_open]
    # a pending one stays, dashed and on its way (the owner, 2026-10-08)
    assert [name for name, way in item.parts if way] == (
        ["plan"] if kind == "approve_plan" and subject == "f6" and done is None else []
    )


def test_a_request_older_than_the_reply_settles_nothing(planning, db_path, db):
    """The owner approved before the lead's latest reply: its proposals are new, so open."""
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn, planning, "approve_plan", "f6", None, _at(timedelta(hours=3))
        ),
    )
    (item,) = desk(db, PROJECT, NOW)[3].items  # F51 D1: the card's two proposals are one item
    assert item.parts == (("ADR 20", False), ("plan", False))


def test_the_factory_tile_names_the_running_ticket(planning, serve):
    """No message pending: the tile names the job, and says planning goes first."""
    tile = _tile(_page(serve()), "factory-now")
    assert f"Running f1-04-live on {LOCAL}, attempt 2, 12 min." in tile
    assert "Your next reply" not in tile
    assert "planning goes first" in tile


def test_a_pending_message_says_when_the_reply_comes(planning, db_path, serve):
    """An open planner row: answered after the running job, which ran past its typical
    10 min; after a planner job whose row isn't this thread's, and nothing says "writing" (F84:
    every thread said the lead was writing its reply)."""
    _write(
        db_path,
        lambda conn: metrics.queue_job(
            conn, planning, "planner", "general#1", "a message", _at(timedelta(minutes=5))
        ),
    )
    client = serve()
    assert "Your next reply: after f1-04-live, any minute now." in _tile(
        _page(client), "factory-now"
    )

    def planner_job(conn) -> None:
        run = conn.execute("SELECT id FROM runs WHERE run_dir = '20261002-113500'").fetchone()
        metrics.start_job(
            conn,
            run["id"],
            ticket_id=None,
            milestone_id=None,
            role="planner",
            agent=OPUS,
            attempt=1,
            started=_at(timedelta(minutes=1)),
        )

    _write(db_path, planner_job)
    tile = _tile(_page(client), "factory-now")
    assert "Your next reply: after the lead's reply." in tile
    assert "writing" not in tile.lower()
    assert "Running f1-04-live" in tile


def test_the_lead_window_shows_the_75_line(planning, db_path, serve):
    _write(
        db_path,
        lambda conn: metrics.add_usage_event(
            conn,
            OPUS,
            NOW.isoformat(),
            "reading",
            window="five_hour",
            value=0.8,
            resets_at=(NOW + timedelta(hours=2)).isoformat(),
        ),
    )
    html = _page(serve())
    assert "5-hour window 80% · planning may go past the 75% line" in _tile(html, "lead-window")
    assert re.search(r'class="past-mark" style="width: 80%"', html)
    assert re.search(r'class="mark"[^>]*style="left: 75%"', html)


def test_the_lead_window_shows_the_week_row(planning, db_path, serve):
    _write(
        db_path,
        lambda conn: metrics.add_usage_event(
            conn,
            OPUS,
            NOW.isoformat(),
            "reading",
            window="seven_day",
            value=0.6,
            resets_at=(NOW + timedelta(days=2)).isoformat(),
        ),
    )
    html = _page(serve())
    tile = _tile(html, "lead-window")
    assert "week 60%" in tile
    assert re.search(r'class="under-mark" style="width: 60%"', html)


def test_the_top_bar_has_a_planning_tab(client):
    html = client.get("/").text
    # the fixture's ripe milestone waits on the desk (f6-09)
    assert re.search(
        r'<a href="/planning\?project=coucou" id="planning-tab">Planning · 1</a>', html
    )
    # the Planning page keeps its count too (the owner, 2026-10-07, f6-16)
    planning = client.get("/planning").text
    assert re.search(
        r'<a href="/planning\?project=coucou" aria-current="page" id="planning-tab">'
        r"Planning · 1</a>",
        planning,
    )


def _open(page, client: TestClient, path: str = "/planning") -> None:
    """``path`` in Chromium, each request answered by ``client``, the POST too."""

    def serve(route) -> None:
        request = route.request
        path = request.url.removeprefix(ORIGIN).split("?", 1)[0]
        if path.startswith("/static/"):
            route.fulfill(path=str(STATIC / path.removeprefix("/static/")))
            return
        headers = request.all_headers()
        if request.method == "POST":
            response = client.post(
                request.url.removeprefix(ORIGIN),
                content=request.post_data or "",
                headers={
                    k: headers[k] for k in ("hx-request", "origin", "content-type") if k in headers
                },
            )
        else:
            response = client.get(request.url.removeprefix(ORIGIN))
        route.fulfill(
            status=response.status_code, body=response.text, content_type="text/html; charset=utf-8"
        )

    page.route(f"{ORIGIN}/**", serve)
    page.goto(f"{ORIGIN}{path}")


@pytest.mark.parametrize(("button", "ask"), [("#plant-only", False), ("#plant-ask", True)])
def test_the_plant_form_posts_a_plant_request(page, planning, db_path, serve, button, ask):
    """Planting asks the runner: a ``plant`` request, no subject, the note's one box (F31 D7);
    "Plant and ask the lead" also sends it to the lead, "Plant" doesn't (the owner, 2026-10-08)."""
    _open(page, serve())
    # the box, the hidden ask, and the hidden again: empty, so the value doesn't carry it
    assert page.locator("#plant input, #plant textarea").count() == 3
    page.fill('#plant textarea[name="text"]', 'Memory "drift" on the frame\nIt forgets.')
    page.click(button)
    page.wait_for_selector("#desk-coming")
    conn = metrics.open_db(db_path)
    try:
        rows = conn.execute("SELECT * FROM owner_requests WHERE project_id = ?", (planning,))
        asked = [(r["kind"], r["subject"], json.loads(r["value"])) for r in rows]
    finally:
        conn.close()
    words = {"text": 'Memory "drift" on the frame\nIt forgets.'}
    assert asked == [("plant", None, {**words, "ask": ask})]


def test_a_plant_shows_the_idea_in_coming_at_once(page, planning, db_path, serve):
    """With nothing in Coming (#desk-coming absent), typing a note and pressing Plant shows
    #desk-coming holding that note as its title and "planting at the runner's next pick",
    without a reload; the textarea is empty afterwards."""
    _open(page, serve())
    assert page.locator("#desk-coming").count() == 0
    page.fill('#plant textarea[name="text"]', "A note about the frame")
    page.click("#plant-only")
    page.wait_for_selector("#desk-coming")
    pick = "planting at the runner's next pick"
    assert _coming_lines(page) == ["COMING · 1", "A note about the frame", pick]
    assert page.input_value('#plant textarea[name="text"]') == ""
    assert page.locator("#plant-row").count() == 1
    assert page.locator("#plant").count() == 1
    assert page.locator("#desk-coming").count() == 1


def _coming_lines(page) -> list[str]:
    """Coming as the browser shows it, line by line (its heading is drawn in capitals)."""
    return [line for line in page.inner_text("#desk-coming").splitlines() if line.strip()]


def test_a_second_plant_adds_a_second_row(page, planning, db_path, serve):
    """Two plants from the same page, no reload: the form drawn again after the first still
    posts, and Coming holds the two notes in order under "Coming · 2", once each."""
    _open(page, serve())
    page.fill('#plant textarea[name="text"]', "First note")
    page.click("#plant-only")
    page.wait_for_selector("#desk-coming >> text=First note")
    page.fill('#plant textarea[name="text"]', "Second note")
    page.click("#plant-ask")
    page.wait_for_selector("#desk-coming >> text=Second note")
    pick = "planting at the runner's next pick"
    assert _coming_lines(page) == ["COMING · 2", "First note", pick, "Second note", pick]
    assert page.url.endswith("/planning")  # still the same page: no form went out as a GET
    assert _values(db_path, "plant") == [
        {"text": "First note", "ask": False},
        {"text": "Second note", "ask": True},
    ]
    assert page.locator("#plant-row").count() == 1
    assert page.locator("#plant").count() == 1
    assert page.locator("#desk-coming").count() == 1


def test_a_failed_post_leaves_textarea_and_coming_as_they_were(page, planning, db_path, serve):
    """Start with one idea already planted, so "as it was" is one row; type a note, press Plant;
    the request is refused: the test waits for the refused answer, then the textarea is as typed
    and Coming is as it was."""
    _write(
        db_path,
        lambda conn: conn.execute(
            "INSERT INTO owner_requests (project_id, kind, value, created)"
            " VALUES (?, 'plant', ?, ?)",
            (
                planning,
                json.dumps({"title": "Existing note", "thoughts": "Before."}),
                _at(timedelta(minutes=10)),
            ),
        ),
    )
    _open(page, serve())
    before = _coming_lines(page)
    assert before == ["COMING · 1", "Existing note", "planting at the runner's next pick"]
    fetched: list[str] = []

    def refuse(route) -> None:
        route.fulfill(status=400, body="Bad request")

    page.route("**/requests", refuse)
    page.on("request", lambda request: fetched.append(request.url))
    page.fill('#plant textarea[name="text"]', "The new note")

    with page.expect_response("**/requests") as response_info:
        page.click("#plant-only")
    response = response_info.value
    assert response.status == 400
    page.wait_for_timeout(300)  # a re-fetch, if one wrongly followed, would have landed

    assert not [url for url in fetched if "/planning" in url]
    assert page.input_value('#plant textarea[name="text"]') == "The new note"
    assert _coming_lines(page) == before


def test_a_stored_plant_empties_the_box_even_when_the_new_form_never_comes(
    page, planning, db_path, serve
):
    """The post is stored and the re-fetch of the page fails (the Wi-Fi dropped): the box is
    empty all the same, so a second press can't plant the same note twice."""
    _open(page, serve())
    page.route("**/planning", lambda route: route.abort())
    page.fill('#plant textarea[name="text"]', "Stored once")
    page.click("#plant-only")
    page.wait_for_selector("#plant-status >> text=Asked")
    page.wait_for_timeout(300)  # the re-fetch has failed by now
    assert page.input_value('#plant textarea[name="text"]') == ""
    assert page.locator("#desk-coming").count() == 0
    page.click("#plant-only")  # the empty box is required: nothing is sent
    page.wait_for_timeout(300)
    assert _values(db_path, "plant") == [{"text": "Stored once", "ask": False}]


@pytest.mark.parametrize("size", [PHONE, DISPLAY], ids=["phone", "display"])
def test_the_desk_page_lays_out_at_phone_and_display_sizes(page, planning, db_path, serve, size):
    """Every group full, a message pending: nothing overlaps or runs off the screen."""
    _write(
        db_path,
        lambda conn: metrics.queue_job(
            conn, planning, "planner", "general#1", "a message", _at(timedelta(minutes=5))
        ),
    )
    _finished(db_path, planning, "plant", None, DUCKS, TAKEN)
    _two_blocked(db_path)
    page.set_viewport_size(size)
    _open(page, serve())
    assert page.locator("#desk-seeds").is_visible()
    assert page.locator("#desk-refused").is_visible()
    assert page.locator(f"#set-aside-{SECOND}").is_visible()
    # On a phone the tabs scroll sideways by design, Planning centred, Overview cut off (f3-30:
    # test_phone_top_bar_is_compact_and_tabs_scroll in test_app.py checks them)
    page.evaluate("() => document.querySelector('nav.tabs').setAttribute('data-layout', 'overlay')")
    assert layout_problems(page) == []


# --- thread page fixtures --------------------------------------------------------------------

_SEVEN_POINTS = [
    {
        "n": 1,
        "title": "Planning goes first",
        "answer": "A planner job is the lead's highest priority.",
        "action": "ADR 20 item 1",
    },
    {
        "n": 2,
        "title": "It runs inside the runner",
        "answer": "One process, as you asked.",
        "action": "ADR 20 item 2",
    },
    {
        "n": 3,
        "title": "Opus plans, inside your 25%",
        "answer": "Planning may use the whole 5-hour window.",
        "action": "ADR 20 item 3",
    },
    {
        "n": 4,
        "title": "One thread per card",
        "answer": "Each card keeps its own conversation.",
        "action": "ADR 20 item 4",
    },
    {
        "n": 5,
        "title": "Answers come as numbered points",
        "answer": "Every lead reply lists points.",
        "action": "A planner prompt",
    },
    {
        "n": 6,
        "title": "The lead only proposes",
        "answer": "ADRs, mock-ups, milestones and tickets are drafts.",
        "action": "ADR 20 item 5",
    },
    {
        "n": 7,
        "title": "Notifications",
        "answer": "A browser notification when a reply is ready.",
        "action": "F5's notifications",
    },
]


def _seven_points(conn: sqlite3.Connection, project_id: int) -> None:
    """On f6's thread, the lead's reply 30 min ago lists ``_SEVEN_POINTS``."""
    f6 = metrics.planner_thread(conn, project_id, "f6", _at(timedelta(hours=5)))["id"]
    metrics.add_planner_message(
        conn,
        f6,
        "lead",
        _at(timedelta(minutes=30)),
        "Here's each point with my answer.",
        points=_SEVEN_POINTS,
    )


def _thread(client: TestClient, thread: str) -> str:
    response = client.get(f"/planning/{thread}")
    assert response.status_code == 200
    return str(response.text)


def _text(markup: str) -> str:
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", markup)).split())


def _points(html: str) -> dict[str, str]:
    """Each point's text by its number."""
    return {
        n: _text(body)
        for n, body in re.findall(
            r'<li class="point" data-point="(\d+)"[^>]*>(.*?)</li>', html, re.S
        )
    }


# --- proposal review page (f6-08) -----------------------------------------------------------

_REVIEW_ADR: dict[str, Any] = {
    "id": "adr-20",
    "kind": "adr",
    "title": "ADR 20: the planning room",
    "path": ".factory/adr/20-planning-room.md",
    "key_points": [
        {"n": 1, "title": "Planning goes first", "text": "At the next pick.", "flag": True},
        {"n": 2, "title": "Inside the runner", "text": "One process.", "flag": False},
        {"n": 3, "title": "Opus, in your 25%", "text": "The whole window.", "flag": None},
    ],
}
_REVIEW_PLAN: dict[str, Any] = {
    "id": "plan",
    "kind": "plan",
    "title": "F6 plan: 7 tickets",
    "path": None,
    "key_points": [{"n": 1, "title": "Desk first", "text": "Then threads.", "flag": False}],
}


def _review(conn: sqlite3.Connection, project_id: int, thread: str, *proposals: object) -> None:
    """On ``thread``, the lead's reply 30 min ago lists ``proposals``."""
    found = metrics.planner_thread(conn, project_id, thread, _at(timedelta(hours=5)))["id"]
    metrics.add_planner_message(
        conn, found, "lead", _at(timedelta(minutes=30)), "Here.", proposals=list(proposals)
    )


def _review_page(client: TestClient, path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200
    return str(response.text)


def _posts(html: str, button: str) -> dict[str, str]:
    """What the button posts to ``/requests``: its ``hx-vals``."""
    found = re.search(rf'<button type="button" id="{button}"[^>]*hx-vals=\'([^\']*)\'', html)
    assert found, button
    vals: dict[str, str] = json.loads(unescape(found[1]))
    return vals


_REVIEW_MERGE: dict[str, Any] = {
    "id": "merge-f9",
    "kind": "merge",
    "title": "Parallel, said twice",
    "path": ".factory/cards/f9-parallel.md",
    "into": "f7",
    "key_points": [{"n": 1, "title": "Notes", "text": "F9's notes go to F7.", "flag": False}],
}


# --- Coming group (f6-20) --------------------------------------------------------------------


def _coming(html: str) -> str:
    """The Coming section's markup, from the page's HTML."""
    found = re.search(r'<section id="desk-coming"(.*?)</section>', html, re.S)
    assert found, "no Coming section"
    return found[1]


def _coming_items(html: str) -> list[tuple[str, str]]:
    """Coming's items: (link, title) from the section."""
    section = _coming(html)
    items: list[tuple[str, str]] = []
    seen: set[str] = set()
    # Extract links and their titles
    for link, title in re.findall(
        r'<a href="([^"?]+)[^"]*"[^>]*>\s*<span[^>]*>([^<]*)</span>', section
    ):
        if title not in seen:
            items.append((link, unescape(title)))
            seen.add(title)
    # Extract non-link items (plant requests use <div> wrapping a <span>)
    for title in re.findall(r"<div[^>]*>\s*<span[^>]*>([^<]*)</span>", section):
        if title not in seen:
            items.append(("", unescape(title)))
            seen.add(title)
    return items


def _coming_text(html: str) -> str:
    """Coming's text: tags stripped and entities unescaped."""
    section = _coming(html)
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", section)).split())


def _needs_you_count(html: str) -> int:
    """The number of items in the Overview's Needs you section."""
    found = re.search(r'<section id="needs-you"[^>]*>(.*?)</section>', html, re.S)
    assert found, "no Needs you section"
    return len(re.findall(r"<li[^>]*>", found[1]))


def test_an_open_plant_request_shows_in_coming_with_its_title(planning, db_path, serve):
    """A pending plant: its title and the words "planting at the runner's next pick", no link."""
    _write(
        db_path,
        lambda conn: conn.execute(
            "INSERT INTO owner_requests (project_id, kind, value, created)"
            " VALUES (?, 'plant', ?, ?)",
            (
                planning,
                json.dumps({"title": "Memory drift on the frame", "thoughts": "It forgets."}),
                _at(timedelta(minutes=5)),
            ),
        ),
    )
    client = serve()
    html = _page(client)
    assert "desk-coming" in html
    assert _coming_items(html) == [("", "Memory drift on the frame")]
    assert "planting at the runner's next pick" in _coming_text(html)


def test_a_done_plant_does_not_show_in_coming(planning, db_path, serve):
    """Once the plant is done, the Coming section disappears."""
    _write(
        db_path,
        lambda conn: conn.execute(
            "INSERT INTO owner_requests (project_id, kind, value, created, done, result)"
            " VALUES (?, 'plant', ?, ?, ?, ?)",
            (
                planning,
                json.dumps({"title": "Done plant"}),
                _at(timedelta(minutes=5)),
                NOW.isoformat(),
                "planted ",
            ),
        ),
    )
    client = serve()
    html = _page(client)
    assert "desk-coming" not in html


@pytest.mark.parametrize("value", ["not JSON", '["a list"]'])
def test_a_plant_the_runner_will_refuse_still_shows(planning, db_path, serve, value):
    """``POST /requests`` stores any value: until the runner refuses it, the plant shows on
    its way on the desk and Next in line, and neither page fails (f6-planning-room-F2)."""
    _write(
        db_path,
        lambda conn: metrics.add_request(conn, planning, "plant", None, value, NOW.isoformat()),
    )
    client = serve()
    assert _coming_items(_page(client)) == [("", "Your idea")]
    response = client.get("/")
    assert response.status_code == 200
    assert "Plant: Your idea" in _text(response.text)


def test_a_thread_with_open_plan_message_request_shows_in_coming(planning, db_path, serve):
    """A thread whose last stored message is the lead's: an open plan_message request puts it in
    Coming with its link and "waiting for the lead"."""
    _write(
        db_path,
        lambda conn: conn.execute(
            "INSERT INTO owner_requests (project_id, kind, subject, created)"
            " VALUES (?, 'plan_message', ?, ?)",
            (
                planning,
                "general",
                _at(timedelta(minutes=5)),
            ),
        ),
    )
    client = serve()
    html = _page(client)
    assert "desk-coming" in html
    assert ("/planning/general", "General") in _coming_items(html)
    assert "waiting for the lead" in _coming_text(html)


def test_a_thread_with_open_planner_row_shows_in_coming(planning, db_path, serve):
    """F6's last message is the owner's; an open planner row about F6 puts it in Coming."""
    _write(
        db_path,
        lambda conn: metrics.queue_job(
            conn, planning, "planner", "f6#2", "a message", _at(timedelta(minutes=5))
        ),
    )
    client = serve()
    html = _page(client)
    assert "desk-coming" in html
    assert ("/planning/f6", "The planning room") in _coming_items(html)
    assert "next, after f1-04-live · any minute now" in _coming_text(html)


@pytest.mark.parametrize(
    ("ahead", "which"), [(timedelta(days=2), "weekly"), (timedelta(hours=2), "5-hour")]
)
def test_a_reply_parked_for_a_limit_says_which_and_until_when(
    planning, db_path, serve, ahead, which
):
    """The owner (2026-10-08): with Claude's week used up, the thread said "at the factory's
    next pick" while its planner job was parked until the reset. A wait past 5 hours is the
    week's."""
    until = NOW + ahead
    _write(
        db_path,
        lambda conn: metrics.queue_job(
            conn,
            planning,
            "planner",
            "f6#2",
            "a message",
            _at(timedelta(minutes=5)),
            until.isoformat(),
        ),
    )
    words = f"waits for Claude's {which} limit, until {until.astimezone():%a %H:%M}"
    client = serve()
    assert f"waiting for the lead · {words}" in _coming_text(_page(client))
    assert f"Next for the lead · {words}" in _text(_thread(client, "f6"))
    assert f"Your next reply: {words}." in _text(_page(client))


def test_coming_skips_a_job_whose_run_has_stopped_beating(planning, db_path, serve):
    """A run that died leaves its job ``running``: Coming says what the tile says, the next
    pick, not "after" a job nothing runs (f6-planning-room-F1)."""
    _write(
        db_path,
        lambda conn: metrics.queue_job(
            conn, planning, "planner", "f6#2", "a message", _at(timedelta(minutes=5))
        ),
    )
    html = _page(serve(heartbeat_age=timedelta(hours=2)))
    assert "Your next reply: at the factory's next pick." in _tile(html, "factory-now")
    assert "waiting for the lead · at the factory's next pick" in _coming_text(html)


def test_a_thread_with_both_open_request_and_planner_row_shows_once(planning, db_path, serve):
    """A thread with both an open request and an open planner row shows once in Coming."""
    _write(
        db_path,
        lambda conn: conn.execute(
            "INSERT INTO owner_requests (project_id, kind, subject, created)"
            " VALUES (?, 'plan_message', ?, ?)",
            (
                planning,
                "general",
                _at(timedelta(minutes=5)),
            ),
        ),
    )
    _write(
        db_path,
        lambda conn: metrics.queue_job(
            conn, planning, "planner", "general#1", "a message", _at(timedelta(minutes=4))
        ),
    )
    client = serve()
    html = _page(client)
    assert "desk-coming" in html
    items = _coming_items(html)
    general_items = [i for i in items if i[0] == "/planning/general"]
    assert len(general_items) == 1


def test_after_the_request_is_done_and_the_lead_replies_the_thread_leaves_coming(
    planning, db_path, serve
):
    """The general thread's last stored message is the lead's: the owner's open message puts it
    in Coming; once the runner has stored it and the lead's reply, it leaves."""
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn, planning, "plan_message", "general", "{}", _at(timedelta(minutes=5))
        ),
    )
    client = serve()
    assert ("/planning/general", "General") in _coming_items(_page(client))

    def answered(conn: sqlite3.Connection) -> None:
        conn.execute(
            "UPDATE owner_requests SET done = ? WHERE kind = 'plan_message'",
            (_at(timedelta(minutes=4)),),
        )
        thread = metrics.planner_thread(conn, planning, "general", _at(timedelta(minutes=4)))["id"]
        metrics.add_planner_message(conn, thread, "owner", _at(timedelta(minutes=4)), "And test 1?")
        metrics.add_planner_message(conn, thread, "lead", _at(timedelta(minutes=1)), "It passes.")

    _write(db_path, answered)
    assert "desk-coming" not in _page(client)


def test_a_first_message_on_a_card_with_no_thread_shows_in_coming(planning, db_path, serve):
    """F9 is an idea card nobody has talked about: the runner makes its thread at its next pick,
    but the owner's message shows in Coming at once."""
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn, planning, "plan_message", "f9", "{}", _at(timedelta(minutes=5))
        ),
    )
    html = _page(serve())
    assert _coming_items(html) == [("/planning/f9", "Parallel developers")]
    assert "waiting for the lead" in _coming_text(html)


def test_after_the_leads_reply_the_thread_moves_to_answers_wanted(planning, db_path, serve):
    """Once the lead's reply is stored, the thread moves to "Your answers wanted"."""
    # First verify the thread is in Coming with an open planner row
    _write(
        db_path,
        lambda conn: metrics.queue_job(
            conn, planning, "planner", "f6#2", "a message", _at(timedelta(minutes=5))
        ),
    )
    client = serve()
    html = _page(client)
    assert "desk-coming" in html
    assert ("/planning/f6", "The planning room") in _coming_items(html)

    # Now the lead replies: add a lead message to f6
    _write(db_path, lambda conn: _seven_points(conn, planning))

    # The Coming section should no longer have f6
    html = _page(client)
    assert "desk-coming" not in html

    # The thread should now be in "Your answers wanted"
    groups = _groups(html)
    assert ("/planning/f6", "The planning room") in _items(groups["answers"])


def test_the_planning_tab_count_and_overview_needs_you_dont_change_with_coming(
    planning, db_path, serve
):
    """Coming has items: the Planning tab's count and the Overview's Needs you stay the same."""
    # First check the count without Coming
    client = serve()
    html = _page(client)
    planning_tab = re.search(
        r'<a href="/planning\?project=coucou"[^>]*id="planning-tab">Planning · (\d+)</a>', html
    )
    base_count = int(planning_tab[1]) if planning_tab else 0
    # The Overview's "Needs you" is on the home page, not /planning
    overview = client.get("/").text
    base_needs = _needs_you_count(overview)

    # Now add Coming items
    _write(
        db_path,
        lambda conn: metrics.queue_job(
            conn, planning, "planner", "f6#2", "a message", _at(timedelta(minutes=5))
        ),
    )
    html = _page(client)
    # The desk groups are still the same four (Coming is separate)
    groups = _groups(html)
    assert list(groups) == ["answers", "proposals", "ripe", "seeds"]
    # The Planning tab count is unchanged
    planning_tab = re.search(
        r'<a href="/planning\?project=coucou"[^>]*id="planning-tab">Planning · (\d+)</a>', html
    )
    assert planning_tab and planning_tab[1] == str(base_count)
    # The Overview's Needs you count is unchanged
    assert _needs_you_count(client.get("/").text) == base_needs


def test_coming_heading_shows_the_item_count(planning, db_path, serve):
    """With two Coming items, the heading reads "Coming · 2"."""
    _write(
        db_path,
        lambda conn: conn.execute(
            "INSERT INTO owner_requests (project_id, kind, value, created)"
            " VALUES (?, 'plant', ?, ?)",
            (
                planning,
                json.dumps({"title": "First idea", "thoughts": "One."}),
                _at(timedelta(minutes=10)),
            ),
        ),
    )
    _write(
        db_path,
        lambda conn: metrics.queue_job(
            conn, planning, "planner", "f6#2", "a message", _at(timedelta(minutes=5))
        ),
    )
    html = _page(serve())
    assert "Coming · 2" in _coming(html)


def test_desk_heading_shows_the_planning_count(planning, db_path, serve):
    """With items in several desk groups, the desk heading reads "Your desk · N" where N
    equals the Planning tab's count on the same page."""
    client = serve()
    html = _page(client)
    # The fixture has items in answers, proposals, ripe and seeds groups
    planning_tab = re.search(
        r'<a href="/planning\?project=coucou"[^>]*id="planning-tab">Planning · (\d+)</a>', html
    )
    count = int(planning_tab[1]) if planning_tab else 0
    assert count > 0
    assert f"Your desk · {count}" in html


def test_empty_desk_heading_has_no_number_and_nothing_waits(tmp_path: Path, db_path):
    """With an empty desk, the heading reads "Your desk" with no number and "Nothing waits
    for you." still shows."""
    from factory_dashboard.app import create_app, get_now

    # Create a fresh database with only the project row (no desk items)
    fresh_db = tmp_path / "empty.sqlite"
    conn = metrics.open_db(fresh_db)
    try:
        metrics.upsert_project(conn, PROJECT)
    finally:
        conn.close()

    app = create_app(fresh_db, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    client = TestClient(app, base_url="http://127.0.0.1:8765")

    response = client.get("/planning")
    assert response.status_code == 200
    html = response.text

    # Desk heading without number
    desk_section = re.search(r'<section id="desk"(.*?)</section>', html, re.S)
    assert desk_section is not None
    heading = re.search(r"<h2[^>]*>(.*?)</h2>", desk_section[1], re.S)
    assert heading is not None
    heading_text = unescape(re.sub(r"<[^>]+>", "", heading[1]))
    # Should be "Your desk" with no " · " (no number)
    assert heading_text == "Your desk"
    # "Nothing waits for you." should still appear
    assert "Nothing waits for you." in html


def test_group_headings_get_no_number(planning, serve):
    """The groups' own headings ("Your answers wanted", …) get no number."""
    html = _page(serve())
    groups = _groups(html)
    for key in groups:
        # Group headings should not contain " · " pattern like "Your desk · N"
        group_div = groups[key]
        h3_match = re.search(r"<h3[^>]*>(.*?)</h3>", group_div, re.S)
        assert h3_match is not None
        h3_text = unescape(re.sub(r"<[^>]+>", "", h3_match[1]))
        assert " · " not in h3_text, f"group {key} heading has a number: {h3_text}"


def test_desk_heading_leaves_out_what_is_on_its_way(planning, db_path, serve):
    """D2: the heading counts what still waits for the owner, as the tab does. An item on its
    way stays listed, dashed, and is counted no more."""

    def heading_and_tab(html: str) -> tuple[str, str]:
        heading = re.search(r'<section id="desk"[^>]*>\s*<h2[^>]*>(.*?)</h2>', html, re.S)
        tab = re.search(r'id="planning-tab">(.*?)</a>', html, re.S)
        assert heading and tab
        return unescape(heading[1]), unescape(tab[1])

    html = _page(serve())
    cards = sum(len(re.findall(r"<a href=", group)) for group in _groups(html).values())
    assert cards > 1
    assert heading_and_tab(html) == (f"Your desk · {cards}", f"Planning · {cards}")
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn, planning, "archive", "general", "on", NOW.isoformat()
        ),
    )
    html = _page(serve(live=False))
    assert sum(len(re.findall(r"<a href=", g)) for g in _groups(html).values()) == cards
    assert heading_and_tab(html) == (f"Your desk · {cards - 1}", f"Planning · {cards - 1}")


# --- archiving a thread (the owner, 2026-10-07) ---------------------------------------------


def _archive(db_path: Path, project_id: int, card: str, ago: timedelta) -> None:
    def write(conn: sqlite3.Connection) -> None:
        found = metrics.find_thread(conn, project_id, card)
        assert found is not None, card
        metrics.set_thread_archived(conn, found["id"], _at(ago))

    _write(db_path, write)


def _archived(html: str) -> list[tuple[str, str]]:
    found = re.search(r'<details id="archived"(.*?)</details>', html, re.S)
    return [] if found is None else _items(found[1])


def test_an_archived_thread_leaves_the_desk(planning, db_path, serve):
    """The general thread's unanswered reply and F6's open proposals leave the desk once
    archived; the Planning count drops with them."""
    client = serve()
    before = _groups(_page(client))
    assert _items(before["answers"]) and _items(before["proposals"])
    _archive(db_path, planning, "general", timedelta(hours=2))
    _archive(db_path, planning, "f6", timedelta(hours=1))
    after = _groups(_page(client))
    assert "answers" not in after and "proposals" not in after
    assert _items(after["seeds"]) == [("/planning/f9", "Parallel developers")]  # not a thread


def test_the_archived_list_shows_the_most_recently_archived_first(planning, db_path, serve):
    client = serve()
    assert 'id="archived"' not in _page(client)  # none archived: no list
    _archive(db_path, planning, "general", timedelta(hours=2))
    _archive(db_path, planning, "f6", timedelta(minutes=30))
    html = _page(client)
    assert [link for link, _ in _archived(html)] == ["/planning/f6", "/planning/general"]
    found = re.search(r'<details id="archived"(.*?)</details>', html, re.S)
    assert found is not None
    assert "Archived · 2" in _text(found[1])
    assert "archived 30 min ago" in found[1] and "archived 2 h ago" in found[1]


# --- "Didn't go through": the owner's words a request refused (F31 D9) -----------------------

DUCKS = json.dumps({"title": "Rubber ducks", "thoughts": "Yellow ones.\nFor Mum.", "ask": True})
TAKEN = "rubber-ducks is a card already: f3-rubber-ducks"


def _finished(
    db_path: Path,
    project_id: int,
    kind: str,
    subject: str | None,
    value: str | None,
    result: str | None,
) -> int:
    """A request the runner finished with ``result`` (None: not yet); its id."""
    found: list[int] = []

    def write(conn: sqlite3.Connection) -> None:
        request_id = metrics.add_request(
            conn, project_id, kind, subject, value, _at(timedelta(minutes=20))
        )
        if result is not None:
            metrics.finish_request(conn, request_id, _at(timedelta(minutes=10)), result)
        found.append(request_id)

    _write(db_path, write)
    return found[0]


def _refused_items(html: str) -> dict[str, str]:
    """Each refused item's text by its request id."""
    return {
        n: _text(body)
        for n, body in re.findall(
            r'<article class="refused" id="refused-(\d+)"[^>]*>(.*?)</article>', html, re.S
        )
    }


def _count(html: str) -> int:
    tab = re.search(r'id="planning-tab">Planning · (\d+)</a>', html)
    assert tab, "no Planning tab"
    return int(tab[1])


def _waits_on_the_desk(html: str) -> int:
    said = re.search(r"(\d+) things? waits? for you on your desk", html)
    return int(said[1]) if said else 0


def test_a_refused_plant_waits_first_on_the_desk_with_its_words_and_counts(
    planning, db_path, db, serve
):
    client = serve()
    before = _count(_page(client)), _waits_on_the_desk(client.get("/").text)
    asked = _finished(db_path, planning, "plant", None, DUCKS, TAKEN)
    html = _page(client)
    assert next(iter(_groups(html))) == "refused"
    assert "Didn't go through" in _text(html.split('id="desk-refused"', 1)[1])
    item = _refused_items(html)[str(asked)]
    for words in ("Rubber ducks", "Yellow ones. For Mum.", TAKEN, "Try again", "Dismiss"):
        assert words in item
    assert _count(html) == before[0] + 1
    assert _waits_on_the_desk(client.get("/").text) == before[1] + 1
    [refused, *_] = desk(db, PROJECT, NOW)
    assert (refused.key, refused.name, refused.color) == (
        "refused",
        "Didn't go through",
        "--hazard",
    )
    assert [i.title for i in refused.items] == ["Rubber ducks"]


def test_a_refused_message_shows_and_try_again_opens_its_thread_with_it(planning, db_path, serve):
    message = json.dumps({"text": "Make it <calm>.", "comments": {"2": "Shorter."}})
    asked = _finished(db_path, planning, "plan_message", "f6", message, "the thread is gone")
    client = serve()
    html = _page(client)
    item = _refused_items(html)[str(asked)]
    assert "Your message on The planning room" in item
    assert "Make it <calm>. On point 2: Shorter." in item and "the thread is gone" in item
    again = re.search(rf'<a id="again-{asked}" href="([^"]+)"', html)
    assert again and unescape(again[1]) == f"/planning/f6?project={PROJECT}&again={asked}#reply"
    thread = client.get(unescape(again[1]).split("#")[0]).text
    box = re.search(r'<textarea name="text"[^>]*>(.*?)</textarea>', thread, re.S)
    assert box and unescape(box[1]) == "Make it <calm>.\n\nOn point 2: Shorter."
    # nothing is posted until the owner presses Send
    rows = sqlite3.connect(db_path).execute("SELECT count(*) FROM owner_requests").fetchone()
    assert rows[0] == 1


@pytest.mark.parametrize(
    ("project_of", "result"),
    [("ours", "queued for the lead"), ("ours", None), ("elsewhere", "refused")],
)
def test_try_again_fills_the_box_only_with_a_refused_message_of_ours(
    planning, db_path, serve, project_of, result
):
    """A message that worked, one on its way (the box waits for the lead's reply), or another
    project's: the box stays empty. The reply's box: a waiting message has its own (F14)."""
    found: list[int] = [planning]
    if project_of == "elsewhere":
        _write(db_path, lambda conn: found.append(metrics.upsert_project(conn, "elsewhere")))
    asked = _finished(db_path, found[-1], "plan_message", "f6", '{"text": "Hi."}', result)
    thread = serve().get(f"/planning/f6?again={asked}").text
    reply = re.search(r'<form id="reply".*?</form>', thread, re.S)
    box = reply and re.search(r'<textarea name="text"[^>]*>(.*?)</textarea>', reply[0], re.S)
    assert (reply is None) == (result is None)
    assert box is None if result is None else box and box[1] == ""


def test_a_refused_send_back_tries_again_on_its_thread(planning, db_path, serve):
    asked = _finished(
        db_path, planning, "send_back", "f6/plan", '{"text": "", "comments": {"1": "No."}}', "x"
    )
    html = _page(serve())
    assert "On point 1: No." in _refused_items(html)[str(asked)]
    again = re.search(rf'<a id="again-{asked}" href="([^"]+)"', html)
    assert again and unescape(again[1]).startswith("/planning/f6?")


@pytest.mark.parametrize(
    ("kind", "subject", "value", "result"),
    [
        ("plant", None, DUCKS, "planted .factory/cards/f12-rubber-ducks.md, queued for the lead"),
        ("plant", None, DUCKS, None),
        ("approve_plan", "f6", None, "there is no plan/f6 to approve"),
        ("pause", None, None, "already paused, since 12:00"),
        ("plant", "general/seed-1", None, "the general thread has no proposal seed-1"),
        ("plan_message", "f6", '{"text": "Go."}', "queued for the lead"),
    ],
)
def test_a_worked_or_wordless_request_never_shows_and_the_group_isnt_drawn(
    planning, db_path, db, serve, kind, subject, value, result
):
    _finished(db_path, planning, kind, subject, value, result)
    assert desk(db, PROJECT, NOW)[0].items == []
    html = _page(serve())
    assert "desk-refused" not in html and "Didn't go through" not in html


def test_a_dismissed_or_dismissing_request_leaves_the_desk(planning, db_path, db, serve):
    """Dismissed by the runner, or a dismiss on its way: gone, a reload doesn't bring it back."""
    gone = _finished(db_path, planning, "plant", None, DUCKS, TAKEN)
    going = _finished(db_path, planning, "plant", None, DUCKS, TAKEN)
    kept = _finished(db_path, planning, "plant", None, DUCKS, TAKEN)
    _write(db_path, lambda conn: metrics.dismiss_request(conn, gone, NOW.isoformat()))
    _finished(db_path, planning, "dismiss", str(going), None, None)
    # a dismiss the runner refused leaves its item
    _finished(db_path, planning, "dismiss", str(kept), None, "there is no request")
    assert list(_refused_items(_page(serve()))) == [str(kept)]
    assert len(desk(db, PROJECT, NOW)[0].items) == 1


def test_try_again_on_a_plant_fills_the_plant_form_and_posts_nothing(
    page, planning, db_path, serve
):
    asked = _finished(db_path, planning, "plant", None, DUCKS, TAKEN)
    _open(page, serve())
    page.click(f"#again-{asked}")
    assert (
        page.input_value('#plant textarea[name="text"]') == "Rubber ducks\n\nYellow ones.\nFor Mum."
    )
    rows = sqlite3.connect(db_path).execute("SELECT count(*) FROM owner_requests").fetchone()
    assert rows[0] == 1


def test_dismiss_takes_the_item_off_at_once_and_a_reload_keeps_it_off(
    page, planning, db_path, serve
):
    asked = _finished(db_path, planning, "plant", None, DUCKS, TAKEN)
    client = serve()
    _open(page, client)
    page.click(f"#dismiss-{asked}")
    page.wait_for_selector(f"#refused-{asked}.dismissing >> text=Asked")
    assert not page.locator(f"#refused-{asked} .refused-body").is_visible()
    conn = metrics.open_db(db_path)
    try:
        rows = conn.execute("SELECT * FROM owner_requests WHERE kind = 'dismiss'").fetchall()
        assert [(r["subject"], r["value"]) for r in rows] == [(str(asked), None)]
    finally:
        conn.close()
    page.reload()
    assert page.locator(f"#refused-{asked}").count() == 0


# --- Try again carries what it retries: one card per note (F48 D2) ---------------------------


def _retry(value: str, again: object) -> str:
    return json.dumps({**json.loads(value), "again": again})


MESSAGE = json.dumps({"text": "Make it calm.", "comments": {}})


@pytest.mark.parametrize(
    ("kind", "subject", "value", "why", "retried_as"),
    [
        ("plant", None, DUCKS, TAKEN, "plant"),
        ("plan_message", "f6", MESSAGE, "the thread is gone", "plan_message"),
        ("send_back", "f6/plan", MESSAGE, "F6 has no proposal plan", "plan_message"),
        ("send_back", "f6/plan", MESSAGE, "F6 has no proposal plan", "send_back"),
    ],
)
@pytest.mark.parametrize("again", [str, int], ids=["as the form sends it", "a number"])
def test_a_retried_request_leaves_the_desk_and_a_retry_refused_shows_alone(
    planning, db_path, serve, kind, subject, value, why, retried_as, again
):
    """Pending, the retry stands for the refused request it names; refused too, it shows as
    the one card for the note; worked, neither shows."""
    other = _finished(db_path, planning, "plant", None, DUCKS, "an idea has a title, on one line")
    asked = _finished(db_path, planning, kind, subject, value, why)
    assert list(_refused_items(_page(serve()))) == [str(other), str(asked)]
    to = subject if retried_as == "send_back" else subject and "f6"
    retry = _finished(db_path, planning, retried_as, to, _retry(value, again(asked)), None)
    assert list(_refused_items(_page(serve()))) == [str(other)]
    _write(db_path, lambda conn: metrics.finish_request(conn, retry, NOW.isoformat(), why))
    assert list(_refused_items(_page(serve()))) == [str(other), str(retry)]
    # the retry dismissed: the note it stood for stays off the desk
    _write(db_path, lambda conn: metrics.dismiss_request(conn, retry, NOW.isoformat()))
    assert list(_refused_items(_page(serve()))) == [str(other)]


@pytest.mark.parametrize(
    ("kind", "value"),
    [
        ("plant", lambda asked: _retry(DUCKS, asked + 1)),  # another request's retry
        ("plant", lambda asked: _retry(DUCKS, f"{asked} ")),
        ("plant", lambda asked: _retry(DUCKS, [asked])),
        ("plant", lambda asked: _retry(DUCKS, True)),
        ("plant", lambda asked: f"again {asked}"),
        ("plant", lambda asked: json.dumps([{"again": asked}])),
        ("dismiss", lambda asked: json.dumps({"again": asked})),  # not a kind with words
    ],
)
def test_only_a_request_naming_it_as_again_takes_a_refused_one_off(
    planning, db_path, serve, kind, value
):
    asked = _finished(db_path, planning, "plant", None, DUCKS, TAKEN)
    _finished(db_path, planning, kind, None, value(asked), "x" if kind == "dismiss" else None)
    assert str(asked) in _refused_items(_page(serve()))


def test_an_earlier_or_another_projects_request_takes_nothing_off(planning, db_path, serve):
    """``again`` names a request made before it, in its own project: a value can't hide a
    refusal that comes later, or another project's."""
    found: list[int] = []
    _write(db_path, lambda conn: found.append(metrics.upsert_project(conn, "elsewhere")))
    early = _finished(db_path, planning, "plant", None, _retry(DUCKS, "3"), None)
    theirs = _finished(db_path, found[0], "plant", None, _retry(DUCKS, "3"), None)
    asked = _finished(db_path, planning, "plant", None, DUCKS, TAKEN)
    assert (early, theirs, asked) == (1, 2, 3)
    assert list(_refused_items(_page(serve()))) == [str(asked)]


def _reply_box(html: str) -> tuple[str, str]:
    """The reply form's hidden ``again`` and the words waiting in its box."""
    form = html.split('<form id="reply"', 1)[1].split("</form>", 1)[0]
    again = re.search(r'<input type="hidden" name="again" value="([^"]*)">', form)
    box = re.search(r'<textarea name="text"[^>]*>(.*?)</textarea>', form, re.S)
    assert again and box
    return again[1], unescape(box[1])


def test_the_reply_form_carries_the_refused_message_it_retries_until_it_is_retried(
    planning, db_path, serve
):
    asked = _finished(db_path, planning, "plan_message", "f6", MESSAGE, "the thread is gone")
    client = serve()
    assert _reply_box(_thread(client, "f6")) == ("", "")
    assert _reply_box(_thread(client, f"f6?again={asked}")) == (str(asked), "Make it calm.")
    # one that isn't a refused message of this thread's names nothing
    assert _reply_box(_thread(client, f"f6?again={asked + 5}")) == ("", "")
    assert _reply_box(_thread(client, f"general?again={asked}")) == ("", "")
    # retried, and that retry refused: the old link's words are no longer waiting
    _finished(db_path, planning, "plan_message", "f6", _retry(MESSAGE, str(asked)), "still gone")
    assert _reply_box(_thread(client, f"f6?again={asked}")) == ("", "")


def _values(db_path: Path, kind: str) -> list[dict[str, Any]]:
    conn = metrics.open_db(db_path)
    try:
        rows = conn.execute("SELECT value FROM owner_requests WHERE kind = ? ORDER BY id", (kind,))
        return [json.loads(r["value"]) for r in rows]
    finally:
        conn.close()


def test_try_again_then_plant_sends_one_retry_and_its_card_leaves_at_once(
    page, planning, db_path, serve
):
    """The retry names the request it retries; its card goes with the send, the other stays;
    the next plant from the same form is a note of its own."""
    asked = _finished(db_path, planning, "plant", None, DUCKS, TAKEN)
    kept = _finished(db_path, planning, "plant", None, DUCKS, "an idea has a title, on one line")
    _open(page, serve())
    page.click(f"#again-{asked}")
    assert page.input_value('#plant input[name="again"]') == str(asked)
    page.click("#plant-only")
    page.wait_for_selector("#desk-coming")
    page.wait_for_selector(f"#refused-{asked}", state="detached")
    assert page.locator(f"#refused-{kept}").is_visible()
    assert page.input_value('#plant input[name="again"]') == ""
    words = {"text": "Rubber ducks\n\nYellow ones.\nFor Mum.", "ask": False}
    assert _values(db_path, "plant")[2:] == [{**words, "again": str(asked)}]
    page.fill('#plant textarea[name="text"]', "Another thought")
    page.click("#plant-only")
    for _ in range(50):  # until the second plant is written
        if len(_values(db_path, "plant")) == 4:
            break
        page.wait_for_timeout(100)
    assert _values(db_path, "plant")[3:] == [{"text": "Another thought", "ask": False}]
    page.reload()
    assert page.locator(f"#refused-{asked}").count() == 0
    assert page.locator(f"#refused-{kept}").is_visible()


def test_the_last_retried_card_takes_its_group_with_it(page, planning, db_path, serve):
    asked = _finished(db_path, planning, "plant", None, DUCKS, TAKEN)
    _open(page, serve())
    page.click(f"#again-{asked}")
    page.click("#plant-ask")
    page.wait_for_selector("#desk-refused", state="detached")
    page.wait_for_selector("#desk-coming")
    assert page.locator("#desk-seeds").is_visible()


def test_a_message_retried_from_its_reply_box_names_what_it_retries(page, planning, db_path, serve):
    asked = _finished(db_path, planning, "plan_message", "f6", MESSAGE, "the thread is gone")
    client = serve()
    _open(page, client, f"/planning/f6?again={asked}")
    assert page.input_value('#reply textarea[name="text"]') == "Make it calm."
    page.click('#reply button[type="submit"]')
    page.wait_for_selector("#reply", state="hidden")
    assert _values(db_path, "plan_message")[1:] == [
        {"text": "Make it calm.", "comments": {}, "again": str(asked)}
    ]
    assert _refused_items(_page(client)) == {}


# --- what the owner acted on shows on its way; Previous and Next (F35) -----------------------


def test_an_archive_on_its_way_shows_dashed_and_counts_no_more(planning, db_path, db, serve):
    """The owner (2026-10-08): after Archive, the thread still looked like it needed them.
    Until the runner's next pick it is on its way, dashed, and out of the count."""
    from factory_dashboard.app import top_bar

    before = top_bar(db, PROJECT, NOW)["planning_count"]
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn, planning, "archive", "general", "on", NOW.isoformat()
        ),
    )
    [item] = [i for i in desk(db, PROJECT, NOW)[2].items if i.link == "/planning/general"]
    assert item.on_its_way and item.words == "archiving at the runner's next pick"
    assert top_bar(db, PROJECT, NOW)["planning_count"] == before - 1
    html = _page(serve())
    found = re.search(
        r'<a href="/planning/general[^"]*" class="on-its-way-item"'
        r' style="[^"]*dashed var\(--hazard\)',
        html,
    )
    assert found, "no dashed item"


def test_a_sign_off_on_its_way_shows_on_the_desk(planning, db_path, db):
    _write(
        db_path,
        lambda conn: metrics.add_request(conn, planning, "signoff", "m4", None, NOW.isoformat()),
    )
    [item] = [i for i in desk(db, PROJECT, NOW)[4].items if i.link == "/planning/m4"]
    assert item.on_its_way and item.words == "signing off at the runner's next pick"


def _trail(html: str) -> dict[str, str]:
    nav = re.search(r'<nav id="desk-trail".*?</nav>', html, re.S)
    assert nav, "no #desk-trail"
    found = dict(re.findall(r'<a id="desk-(previous|next)" href="([^"?]+)', nav[0]))
    found["words"] = _text(nav[0])
    return found


def test_previous_and_next_step_through_what_waits(planning, db_path, serve):
    """F35: from the general thread, Next is F6's ADR; from there Previous is back and Next is
    the next item (F6's ADR and plan are one item, F51 D1); a page already done with leads to
    the first one left."""
    client = serve()
    first = _trail(_thread(client, "general"))
    assert first["next"] == "/planning/f6/proposals/adr-20" and "previous" not in first
    assert "1 of " in first["words"] and "waiting for you" in first["words"]
    middle = _trail(_review_page(client, "/planning/f6/proposals/adr-20"))
    assert middle["previous"] == "/planning/general"
    assert middle["next"] == "/planning/m4"  # past F6's plan: it is the ADR's item
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn, planning, "archive", "general", "on", NOW.isoformat()
        ),
    )
    done = _trail(_thread(client, "general"))  # archived: no longer waiting
    assert done["next"] == "/planning/f6/proposals/adr-20" and "previous" not in done


# --- a waiting plant is edited or cancelled from Coming (F14) --------------------------------

NOTE = json.dumps({"text": "Calm colours", "ask": True})
PICK = "planting at the runner's next pick"
ASKED = "Asked: the runner will do it."


def _waiting(html: str, request_id: int) -> tuple[str, str]:
    """A plant's row in Coming: its tag (``details`` while it opens, ``div`` once a change is
    on its way) and its markup."""
    found = re.search(
        rf'<(details|div) class="[^"]*" id="waiting-{request_id}".*?</\1>', _coming(html), re.S
    )
    assert found, f"no row for request {request_id}"
    return found[1], found[0]


def _asked_changes(db_path: Path) -> list[tuple[str | None, dict[str, Any]]]:
    conn = metrics.open_db(db_path)
    try:
        rows = conn.execute("SELECT * FROM owner_requests WHERE kind = 'change' ORDER BY id")
        return [(r["subject"], json.loads(r["value"])) for r in rows]
    finally:
        conn.close()


def test_a_waiting_plant_opens_with_its_words_save_and_cancel_it(planning, db_path, serve):
    """A one-box note opens as its one text, an older plant as its title and thoughts; each
    row holds its own words only."""
    note = _finished(db_path, planning, "plant", None, NOTE, None)
    ducks = _finished(db_path, planning, "plant", None, DUCKS, None)
    html = _page(serve())
    tag, row = _waiting(html, note)
    assert tag == "details" and "on-its-way-item" not in row
    assert re.search(r'<textarea name="text"[^>]*>Calm colours</textarea>', row)
    assert 'name="title"' not in row and "Rubber ducks" not in row
    assert f'id="save-{note}"' in row and f'id="cancel-{note}"' in row
    tag, row = _waiting(html, ducks)
    assert tag == "details"
    assert re.search(r'<input name="title" required value="Rubber ducks"', row)
    assert re.search(r'<textarea name="thoughts"[^>]*>Yellow ones.\nFor Mum.</textarea>', row)
    assert 'name="text"' not in row and "Calm colours" not in row


def test_an_edit_on_its_way_shows_the_new_title_and_the_row_opens_no_more(planning, db_path, serve):
    """The plant with an open change shows it, dashed, its status polling; the other plant's
    row is as it was: it still opens, with its own title."""
    note = _finished(db_path, planning, "plant", None, NOTE, None)
    ducks = _finished(db_path, planning, "plant", None, DUCKS, None)
    edit = json.dumps({"text": "Calmer colours\nNothing bright."})
    change = _finished(db_path, planning, "change", str(note), edit, None)
    html = _page(serve())
    tag, row = _waiting(html, note)
    assert tag == "div" and "on-its-way-item" in row and "1px dashed var(--hazard)" in row
    assert _text(row) == f"Calmer colours Nothing bright. changed · {PICK} {ASKED}"
    assert f'hx-get="/requests/{change}"' in row
    assert "<details" not in row and "<form" not in row and "<button" not in row
    tag, row = _waiting(html, ducks)
    assert tag == "details" and _text(row).startswith(f"Rubber ducks {PICK} ")
    assert _coming_items(html) == [("", "Calmer colours Nothing bright."), ("", "Rubber ducks")]


def test_a_cancel_on_its_way_strikes_the_plant_through(planning, db_path, serve):
    """A cancel wins over an edit made before or after it, as the runner applies them."""
    ducks = _finished(db_path, planning, "plant", None, DUCKS, None)
    _finished(db_path, planning, "change", str(ducks), json.dumps({"title": "Geese"}), None)
    cancel = _finished(db_path, planning, "change", str(ducks), '{"cancel": true}', None)
    _finished(db_path, planning, "change", str(ducks), json.dumps({"title": "Swans"}), None)
    tag, row = _waiting(_page(serve()), ducks)
    assert tag == "div" and "1px dashed var(--hazard)" in row
    assert re.search(r'<span style="[^"]*text-decoration: line-through">Rubber ducks</span>', row)
    assert _text(row) == f"Rubber ducks cancelling at the runner's next pick {ASKED}"
    assert f'hx-get="/requests/{cancel}"' in row and "<button" not in row


def test_a_change_the_runner_finished_shows_no_more(planning, db_path, serve):
    """Only an open change counts: once the runner has applied or refused it, the plant
    (still waiting, say the change was refused) opens again."""
    ducks = _finished(db_path, planning, "plant", None, DUCKS, None)
    _finished(db_path, planning, "change", str(ducks), '{"cancel": true}', "a change is JSON")
    tag, row = _waiting(_page(serve()), ducks)
    assert tag == "details" and "line-through" not in row


def test_a_seeds_plant_offers_cancel_it_only(planning, db_path, serve):
    """The runner refuses an edit of a seed's words (they are the lead's)."""
    seed = _finished(db_path, planning, "plant", "general/seed-1", None, None)
    tag, row = _waiting(_page(serve()), seed)
    assert tag == "details" and f'id="cancel-{seed}"' in row
    assert "<form" not in row and f'id="save-{seed}"' not in row


def test_a_change_that_came_too_late_keeps_a_row_for_the_runners_word(planning, db_path, serve):
    """The page was drawn before the runner took the plant, and the owner saved from it: the
    plant has left Coming, and the change's row stays with its status, where "too late:
    already planted" shows. A change on a message isn't the desk's."""
    ducks = _finished(db_path, planning, "plant", None, DUCKS, "planted f9-rubber-ducks")
    said = _finished(db_path, planning, "plan_message", "general", MESSAGE, "sent")
    change = _finished(db_path, planning, "change", str(ducks), '{"cancel": true}', None)
    _finished(db_path, planning, "change", str(said), '{"cancel": true}', None)
    _finished(db_path, planning, "change", "no such request", '{"cancel": true}', None)
    client = serve()
    html = _page(client)
    assert "Coming · 1" in _coming(html)
    tag, row = _waiting(html, ducks)
    assert tag == "div" and "line-through" not in row and "<button" not in row
    assert _text(row) == f"Rubber ducks your change came too late: the runner had taken it {ASKED}"
    assert f'hx-get="/requests/{change}"' in row
    _write(
        db_path,
        lambda conn: metrics.finish_request(
            conn, change, NOW.isoformat(), "too late: already planted"
        ),
    )
    assert _text(client.get(f"/requests/{change}").text) == "too late: already planted"


def test_save_posts_a_change_and_the_row_shows_it_at_once(page, planning, db_path, serve):
    """On a phone: the row opens in place, Save and Cancel it 44 px high; Save posts one
    change naming the plant, with the new words; Coming alone is drawn again, so the other
    plant still opens and a note half typed in the Plant box stays."""
    note = _finished(db_path, planning, "plant", None, NOTE, None)
    ducks = _finished(db_path, planning, "plant", None, DUCKS, None)
    page.set_viewport_size(PHONE)
    _open(page, serve())
    assert _coming_lines(page) == ["COMING · 2", "Calm colours", PICK, "Rubber ducks", PICK]
    assert not page.locator(f"#save-{note}").is_visible()
    page.click(f"#waiting-{note} summary")
    assert page.url.endswith("/planning")
    assert page.input_value(f'#edit-{note} textarea[name="text"]') == "Calm colours"
    for button in (f"#save-{note}", f"#cancel-{note}"):
        assert page.locator(button).is_visible()
        assert page.locator(button).evaluate("e => e.offsetHeight") >= 44
    page.fill('#plant textarea[name="text"]', "Half a new note")
    page.fill(f'#edit-{note} textarea[name="text"]', "Calmer colours")
    page.click(f"#save-{note}")
    page.wait_for_selector(f"div#waiting-{note}")
    changed = ["Calmer colours", f"changed · {PICK}", ASKED]
    assert _coming_lines(page) == ["COMING · 2", *changed, "Rubber ducks", PICK]
    assert page.locator(f"#waiting-{note} summary, #save-{note}, #cancel-{note}").count() == 0
    assert page.locator(f"details#waiting-{ducks}").count() == 1
    assert page.input_value('#plant textarea[name="text"]') == "Half a new note"
    assert _asked_changes(db_path) == [(str(note), {"text": "Calmer colours"})]
    assert _values(db_path, "plant") == [json.loads(NOTE), json.loads(DUCKS)]  # never edited
    page.reload()
    assert _coming_lines(page) == ["COMING · 2", *changed, "Rubber ducks", PICK]


def test_save_on_an_older_plant_posts_its_title_and_thoughts(page, planning, db_path, serve):
    ducks = _finished(db_path, planning, "plant", None, DUCKS, None)
    _open(page, serve())
    page.click(f"#waiting-{ducks} summary")
    assert page.input_value(f'#edit-{ducks} input[name="title"]') == "Rubber ducks"
    thoughts = "Yellow ones.\nFor Mum."
    assert page.input_value(f'#edit-{ducks} textarea[name="thoughts"]') == thoughts
    page.fill(f'#edit-{ducks} input[name="title"]', 'Rubber "duck" keys')
    page.click(f"#save-{ducks}")
    page.wait_for_selector(f"div#waiting-{ducks}")
    assert _coming_lines(page) == ["COMING · 1", 'Rubber "duck" keys', f"changed · {PICK}", ASKED]
    words = {"title": 'Rubber "duck" keys', "thoughts": thoughts}
    assert _asked_changes(db_path) == [(str(ducks), words)]


def test_cancel_it_posts_a_cancel_and_the_row_is_struck_through_at_once(
    page, planning, db_path, serve
):
    ducks = _finished(db_path, planning, "plant", None, DUCKS, None)
    _open(page, serve())
    page.click(f"#waiting-{ducks} summary")
    page.click(f"#cancel-{ducks}")
    page.wait_for_selector(f"div#waiting-{ducks}")
    cancelling = "cancelling at the runner's next pick"
    assert _coming_lines(page) == ["COMING · 1", "Rubber ducks", cancelling, ASKED]
    struck = page.locator(f"#waiting-{ducks} span").first
    assert struck.inner_text() == "Rubber ducks"
    assert "line-through" in struck.evaluate("e => getComputedStyle(e).textDecorationLine")
    assert page.locator(f"#waiting-{ducks} summary, #cancel-{ducks}").count() == 0
    assert _asked_changes(db_path) == [(str(ducks), {"cancel": True})]


def test_a_change_that_isnt_stored_leaves_the_row_open(page, planning, db_path, serve):
    """The post is refused: nothing is drawn again, and the editor keeps what was typed."""
    ducks = _finished(db_path, planning, "plant", None, DUCKS, None)
    _open(page, serve())
    page.route("**/requests", lambda route: route.fulfill(status=400, body="Bad request"))
    page.click(f"#waiting-{ducks} summary")
    page.fill(f'#edit-{ducks} input[name="title"]', "Geese")
    with page.expect_response("**/requests"):
        page.click(f"#save-{ducks}")
    page.wait_for_timeout(300)  # a re-fetch, if one wrongly followed, would have landed
    assert page.input_value(f'#edit-{ducks} input[name="title"]') == "Geese"
    assert page.locator(f"details#waiting-{ducks}[open]").count() == 1
    assert _asked_changes(db_path) == []


# --- an edit that didn't go through shows under "Didn't go through" (f14-04) ------------------

GEESE = json.dumps({"title": "Rubber geese", "thoughts": "Grey ones."})
BRIGHT = json.dumps({"text": "Make it <bright>.", "comments": {"2": "Shorter."}})
LATE_PLANT = "too late: already planted"
LATE_MESSAGE = "too late: already sent"


def test_a_plants_edit_that_came_too_late_shows_with_its_new_words_and_dismiss_only(
    planning, db_path, db, serve
):
    ducks = _finished(db_path, planning, "plant", None, DUCKS, "planted f9-rubber-ducks")
    change = _finished(db_path, planning, "change", str(ducks), GEESE, LATE_PLANT)
    client = serve()
    html = _page(client)
    assert "Didn't go through" in _text(html.split('id="desk-refused"', 1)[1])
    assert _refused_items(html) == {
        str(change): "Your edit of Rubber ducks Rubber geese Grey ones."
        f" The runner said: {LATE_PLANT} Dismiss"
        " Dismissed Your edit of Rubber ducks:"
    }
    # planting the words again would make a second card: no Try again
    assert f'id="again-{change}"' not in html
    assert f'"subject": "{change}"' in unescape(html.split(f'id="dismiss-{change}"', 1)[1])
    assert [i.title for i in desk(db, PROJECT, NOW)[0].items] == ["Your edit of Rubber ducks"]


def test_a_one_box_notes_edit_shows_its_text_once(planning, db_path, serve):
    note = _finished(db_path, planning, "plant", None, NOTE, "planted f9-calm-colours")
    edit = json.dumps({"text": "Calmer colours\nNothing bright."})
    change = _finished(db_path, planning, "change", str(note), edit, LATE_PLANT)
    assert _refused_items(_page(serve()))[str(change)].startswith(
        "Your edit of Calm colours Calmer colours Nothing bright. The runner said:"
    )


def test_a_messages_edit_that_came_too_late_shows_and_try_again_opens_its_thread_with_it(
    planning, db_path, serve
):
    said = _finished(db_path, planning, "plan_message", "f6", MESSAGE, "queued for the lead")
    change = _finished(db_path, planning, "change", str(said), BRIGHT, LATE_MESSAGE)
    client = serve()
    html = _page(client)
    item = _refused_items(html)[str(change)]
    assert item.startswith(
        "Your edit on The planning room Make it <bright>. On point 2: Shorter."
        f" The runner said: {LATE_MESSAGE} Try again Dismiss"
    )
    again = re.search(rf'<a id="again-{change}" href="([^"]+)"', html)
    assert again and unescape(again[1]) == f"/planning/f6?project={PROJECT}&again={change}#reply"
    thread = _thread(client, f"f6?again={change}")
    assert _reply_box(thread) == (str(change), "Make it <bright>.\n\nOn point 2: Shorter.")
    # another thread's reply box doesn't take it
    assert _reply_box(_thread(client, f"general?again={change}")) == ("", "")
    # sent again from the reply box, that retry stands for it: one card per note (F48 D2)
    retry = _retry(BRIGHT, str(change))
    _finished(db_path, planning, "plan_message", "f6", retry, "queued for the lead")
    assert _refused_items(_page(client)) == {}
    assert _reply_box(_thread(client, f"f6?again={change}")) == ("", "")


@pytest.mark.parametrize(
    ("kind", "subject", "value", "edit", "shown"),
    [
        ("plant", None, DUCKS, json.dumps({"title": "Rubber\ngeese"}), "Rubber geese"),
        ("plant", None, DUCKS, "not json", "not json"),
        (
            "plan_message",
            "f6",
            MESSAGE,
            '{"text": "x", "comments": 3}',
            '{"text": "x", "comments": 3}',
        ),
    ],
)
def test_an_edit_refused_for_its_words_shows_them_with_the_runners_reason(
    planning, db_path, serve, kind, subject, value, edit, shown
):
    """The plant or message still waits, as it was; the words that didn't replace its own are
    on the desk."""
    target = _finished(db_path, planning, kind, subject, value, None)
    change = _finished(db_path, planning, "change", str(target), edit, "a change is JSON")
    item = _refused_items(_page(serve()))[str(change)]
    assert f"{shown} The runner said: a change is JSON" in item
    assert ("Try again" in item) == (kind == "plan_message")


@pytest.mark.parametrize(
    ("value", "result"),
    [
        ('{"cancel": true}', "cancelled"),
        ('{"cancel": true}', LATE_PLANT),
        ('{"cancel": true}', "there is no request 99"),
        (GEESE, "changed"),
        (GEESE, None),  # on its way: Coming shows it
    ],
)
def test_a_cancel_or_an_edit_that_worked_never_shows_there(
    planning, db_path, db, serve, value, result
):
    ducks = _finished(db_path, planning, "plant", None, DUCKS, "planted f9-rubber-ducks")
    _finished(db_path, planning, "change", str(ducks), value, result)
    assert desk(db, PROJECT, NOW)[0].items == []
    html = _page(serve())
    assert "desk-refused" not in html and "Didn't go through" not in html


def test_an_edit_naming_no_plant_or_message_of_ours_still_shows_its_words(planning, db_path, serve):
    """Whatever it named (nothing, another kind of request, another project's): the words are
    the owner's, with Dismiss; nothing of the other project's is read."""
    found: list[int] = []
    _write(db_path, lambda conn: found.append(metrics.upsert_project(conn, "elsewhere")))
    theirs = _finished(db_path, found[0], "plan_message", "f6", '{"text": "Secret."}', "sent")
    back = _finished(db_path, planning, "send_back", "f6/plan", MESSAGE, "queued for the lead")
    client = serve()
    for subject in ("99", "x", str(back), str(theirs)):
        change = _finished(db_path, planning, "change", subject, GEESE, "there is no request")
        html = _page(client)
        item = _refused_items(html)[str(change)]
        assert item.startswith("Your edit Rubber geese Grey ones. The runner said:")
        assert "Try again" not in item and "Secret" not in html
        assert _reply_box(_thread(client, f"f6?again={change}")) == ("", "")
        _write(db_path, lambda conn, c=change: metrics.dismiss_request(conn, c, NOW.isoformat()))


def test_a_dismissed_or_dismissing_edit_leaves_the_desk(planning, db_path, serve):
    ducks = _finished(db_path, planning, "plant", None, DUCKS, "planted f9-rubber-ducks")
    gone = _finished(db_path, planning, "change", str(ducks), GEESE, LATE_PLANT)
    going = _finished(db_path, planning, "change", str(ducks), GEESE, LATE_PLANT)
    kept = _finished(db_path, planning, "change", str(ducks), GEESE, LATE_PLANT)
    _write(db_path, lambda conn: metrics.dismiss_request(conn, gone, NOW.isoformat()))
    _finished(db_path, planning, "dismiss", str(going), None, None)
    assert list(_refused_items(_page(serve()))) == [str(kept)]


def test_dismiss_on_an_edit_posts_a_dismiss_naming_the_change(page, planning, db_path, serve):
    said = _finished(db_path, planning, "plan_message", "f6", MESSAGE, "queued for the lead")
    change = _finished(db_path, planning, "change", str(said), BRIGHT, LATE_MESSAGE)
    _open(page, serve())
    assert page.locator(f"#refused-{change} .refused-body").is_visible()
    page.click(f"#dismiss-{change}")
    page.wait_for_selector(f"#refused-{change}.dismissing >> text=Asked")
    assert not page.locator(f"#refused-{change} .refused-body").is_visible()
    conn = metrics.open_db(db_path)
    try:
        rows = conn.execute("SELECT * FROM owner_requests WHERE kind = 'dismiss'").fetchall()
        assert [(r["subject"], r["value"]) for r in rows] == [(str(change), None)]
    finally:
        conn.close()
    page.reload()
    assert page.locator(f"#refused-{change}").count() == 0


# --- liveIdle with a waiting plant (f19-01) ----------------------------


def test_liveIdle_is_true_when_page_loads_with_a_waiting_plant(page, planning, db_path, serve):
    """With one waiting plant in Coming, liveIdle is true on page load: the editor's own
    text doesn't count as user-typed."""
    _finished(db_path, planning, "plant", None, NOTE, None)
    _open(page, serve())
    page.wait_for_selector("#desk-coming")
    assert page.evaluate("() => window.liveIdle()") is True


def test_liveIdle_is_false_once_text_is_typed_in_the_plant_box(page, planning, db_path, serve):
    """With one waiting plant in Coming, liveIdle becomes false once text is typed in the
    Plant box."""
    _finished(db_path, planning, "plant", None, NOTE, None)
    _open(page, serve())
    page.wait_for_selector("#desk-coming")
    assert page.evaluate("() => window.liveIdle()") is True
    page.fill('#plant textarea[name="text"]', "A new note")
    assert page.evaluate("() => window.liveIdle()") is False


def test_liveIdle_is_true_again_once_plant_box_is_emptied_and_focus_left(
    page, planning, db_path, serve
):
    """With one waiting plant in Coming, liveIdle is true again once the Plant box is
    emptied and focus has left it."""
    _finished(db_path, planning, "plant", None, NOTE, None)
    _open(page, serve())
    page.wait_for_selector("#desk-coming")
    page.fill('#plant textarea[name="text"]', "A new note")
    assert page.evaluate("() => window.liveIdle()") is False
    page.fill('#plant textarea[name="text"]', "")
    page.evaluate("() => document.querySelector('#plant textarea[name=text]').blur()")
    assert page.evaluate("() => window.liveIdle()") is True


def test_liveIdle_is_false_while_waiting_plant_is_open(page, planning, db_path, serve):
    """With one waiting plant in Coming, liveIdle is false while the waiting plant is
    open (details is open with input/textarea)."""
    note = _finished(db_path, planning, "plant", None, NOTE, None)
    _open(page, serve())
    page.wait_for_selector("#desk-coming")
    assert page.evaluate("() => window.liveIdle()") is True
    page.click(f"#waiting-{note} summary")
    assert page.evaluate("() => window.liveIdle()") is False


def test_liveIdle_is_true_again_when_waiting_plant_is_closed(page, planning, db_path, serve):
    """With one waiting plant in Coming, liveIdle is true again once the waiting plant
    is closed (details is no longer open)."""
    note = _finished(db_path, planning, "plant", None, NOTE, None)
    _open(page, serve())
    page.wait_for_selector("#desk-coming")
    page.click(f"#waiting-{note} summary")
    assert page.evaluate("() => window.liveIdle()") is False
    page.click(f"#waiting-{note} summary")
    assert page.evaluate("() => window.liveIdle()") is True


def test_desk_has_a_poll_wrapper_with_correct_attributes(planning, serve):
    """The desk has a poll wrapper with hx-get="/planning?project=coucou",
    hx-trigger="every 5s [window.liveIdle()]" and hx-select="#desk"."""
    html = _page(serve())
    assert 'hx-get="/planning' in html
    assert 'hx-trigger="every 5s [window.liveIdle()]"' in html
    assert 'hx-select="#desk"' in html


def test_desk_coming_poll_wrapper_when_items_exist(planning, db_path, serve):
    """With a waiting plant, the HTML has a poll around #desk-coming."""
    _finished(db_path, planning, "plant", None, NOTE, None)
    html = _page(serve())
    assert "desk-coming" in html
    assert 'hx-select="#desk-coming"' in html


def test_desk_coming_poll_wrapper_absent_when_no_items(planning, serve):
    """With no waiting plant, the string desk-coming is nowhere in the page."""
    html = _page(serve())
    assert "desk-coming" not in html


# --- the desk and an open thread refresh by themselves (F19 review) ---------------------------

LIVE = 9000  # one 5 s poll, and room to draw it


def _lead_says(db_path: Path, project_id: int, card: str, text: str) -> None:
    def write(conn: sqlite3.Connection) -> None:
        thread = metrics.planner_thread(conn, project_id, card, _at(timedelta(hours=5)))["id"]
        metrics.add_planner_message(conn, thread, "lead", _at(timedelta(minutes=1)), text)

    _write(db_path, write)


def test_the_desk_poll_moves_an_answered_seed_to_the_answers(page, planning, db_path, serve):
    """F9 is a seed when the desk opens; the lead answers on its thread: within a poll F9 sits
    under "Your answers wanted" and no longer under the seeds, without a reload."""
    _open(page, serve())
    assert page.locator('#desk-seeds a[href^="/planning/f9"]').count() == 1
    _lead_says(db_path, planning, "f9", "Here is what I think.")
    page.locator('#desk-answers a[href^="/planning/f9"]').wait_for(timeout=LIVE)
    assert page.locator('#desk-seeds a[href^="/planning/f9"]').count() == 0


def test_two_blocked_tickets_appear_second_on_the_desk_with_their_ids_and_reasons(
    planning, db_path, db, serve
):
    """Two open blocked rows: the desk's second group is "Blocked tickets" with two items,
    oldest first, each titled with its own ticket's id and worded with its own reason, each
    linking to its ticket's page."""
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_owner_item(
            conn,
            project,
            "blocked",
            "f1-01",
            text="f1-01 blocked: waiting on f12-03",
            created=_at(timedelta(hours=4)),
        )
        metrics.upsert_owner_item(
            conn,
            project,
            "blocked",
            "f1-02",
            text="f1-02 blocked: waiting on f95-01",
            created=_at(timedelta(hours=2)),
        )
    finally:
        conn.close()
    html = _page(serve())
    groups = _groups(html)
    assert "blocked" in groups
    blocked_markup = groups["blocked"]
    assert "Blocked tickets" in blocked_markup
    items = _items(blocked_markup)
    assert len(items) == 2
    assert items[0] == ("/tickets/f1-01", "f1-01")
    assert items[1] == ("/tickets/f1-02", "f1-02")
    [_, blocked_group, *_] = desk(db, PROJECT, NOW)
    assert (blocked_group.key, blocked_group.name, blocked_group.color) == (
        "blocked",
        "Blocked tickets",
        "--hazard",
    )
    assert [i.title for i in blocked_group.items] == ["f1-01", "f1-02"]
    assert [i.words for i in blocked_group.items] == [
        "waiting on f12-03",
        "waiting on f95-01",
    ]
    assert [i.link for i in blocked_group.items] == ["/tickets/f1-01", "/tickets/f1-02"]


def test_a_resolved_blocked_ticket_does_not_show_on_the_desk(planning, db_path, db, serve):
    """A resolved blocked row is not on the desk."""
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        item_id = metrics.upsert_owner_item(
            conn,
            project,
            "blocked",
            "f1-03",
            text="f1-03 blocked: was waiting on something",
            created=_at(timedelta(hours=-4)),
        )
        metrics.resolve_owner_item(conn, item_id, NOW.isoformat())
    finally:
        conn.close()
    html = _page(serve())
    groups = _groups(html)
    blocked_markup = groups.get("blocked", "")
    assert "f1-03" not in blocked_markup
    [_, blocked_group, *_] = desk(db, PROJECT, NOW)
    assert blocked_group.items == []


def test_no_open_blocked_tickets_means_empty_group_and_no_heading(planning, db_path, db, serve):
    """With no open blocked rows, the group is empty and /planning doesn't show its heading."""
    html = _page(serve())
    groups = _groups(html)
    blocked_markup = groups.get("blocked", "")
    assert "Blocked tickets" not in blocked_markup
    [_, blocked_group, *_] = desk(db, PROJECT, NOW)
    assert blocked_group.items == []


# --- Try again or Set aside a blocked ticket (F106 D3) --------------------------------------

FIRST, SECOND = "f1-01-first", "f1-02-second"
ON_ITS_WAY = {
    "queue": "Trying again at the runner's next pick",
    "set_aside": "Set aside at the runner's next pick",
}


def _two_blocked(db_path: Path) -> None:
    def write(conn: sqlite3.Connection) -> None:
        project = metrics.upsert_project(conn, PROJECT)
        for hours, ticket in ((4, FIRST), (2, SECOND)):
            metrics.upsert_owner_item(
                conn,
                project,
                "blocked",
                ticket,
                text=f"{ticket} blocked: waiting on f12-03",
                created=_at(timedelta(hours=hours)),
            )

    _write(db_path, write)


def _blocked_item(html: str, ticket: str) -> str:
    found = re.search(
        rf'<article class="blocked-ticket" id="blocked-{ticket}".*?</article>', html, re.S
    )
    assert found, ticket
    return found[0]


def _desk_count(html: str) -> int:
    found = re.search(r"Your desk(?: · (\d+))?</h2>", html)
    assert found
    return int(found[1] or 0)


@pytest.mark.parametrize(("button", "kind"), [("try-again", "queue"), ("set-aside", "set_aside")])
def test_a_blocked_tickets_button_asks_for_it_by_its_id_and_shows_it_on_its_way(
    page, planning, db_path, serve, button, kind
):
    """Pressed on the second of two blocked tickets: one request of its kind naming that
    ticket; the item shows on its way at once, without buttons; the first keeps both."""
    _two_blocked(db_path)
    _open(page, serve())
    page.click(f"#{button}-{SECOND}")
    item = page.locator(f"#blocked-{SECOND}")
    item.locator(f"text={ON_ITS_WAY[kind]}").wait_for()
    assert "dashed" in item.locator("a").get_attribute("style")
    assert not page.locator(f"#try-again-{SECOND}").is_visible()
    assert not page.locator(f"#set-aside-{SECOND}").is_visible()
    page.wait_for_selector(f"#blocked-status-{SECOND} >> text=Asked")
    assert page.locator(f"#try-again-{FIRST}").is_visible()
    assert page.locator(f"#set-aside-{FIRST}").is_visible()
    conn = metrics.open_db(db_path)
    try:
        rows = conn.execute(
            "SELECT kind, subject FROM owner_requests WHERE kind IN ('queue', 'set_aside')"
        ).fetchall()
        assert [(r["kind"], r["subject"]) for r in rows] == [(kind, SECOND)]
    finally:
        conn.close()


@pytest.mark.parametrize("kind", ["queue", "set_aside"])
def test_a_blocked_ticket_asked_for_is_on_its_way_and_leaves_the_count(
    planning, db_path, db, serve, kind
):
    """An open request for the second ticket: dashed, its words, no button, one fewer in the
    desk's heading; the first ticket keeps its buttons. A finished request changes nothing."""
    _two_blocked(db_path)
    client = serve()
    before = _desk_count(_page(client))
    _finished(db_path, planning, kind, FIRST, None, "done")  # done: the first still waits
    _write(
        db_path,
        lambda conn: metrics.add_request(conn, planning, kind, SECOND, None, NOW.isoformat()),
    )
    html = _page(client)
    assert _desk_count(html) == before - 1
    blocked = _groups(html)["blocked"]
    assert _items(blocked)[1] == (f"/tickets/{SECOND}", SECOND)
    assert f'id="blocked-{SECOND}"' not in html
    second = blocked.split(f'href="/tickets/{SECOND}', 1)[1].split("</a>", 1)[0]
    assert "on-its-way-item" in second and "dashed var(--hazard)" in second
    assert ON_ITS_WAY[kind] in unescape(second)
    assert f"try-again-{SECOND}" not in html and f"set-aside-{SECOND}" not in html
    first = _blocked_item(html, FIRST)
    assert f'id="try-again-{FIRST}"' in first and f'id="set-aside-{FIRST}"' in first
    [_, group, *_] = desk(db, PROJECT, NOW)
    assert [(i.title, i.on_its_way, i.words) for i in group.items] == [
        (FIRST, False, "waiting on f12-03"),
        (SECOND, True, ON_ITS_WAY[kind]),
    ]


# --- the lead looks at a blocked ticket (ADR 29 items 1 and 4, f106-04) ----------------------


LOOK = "f9-01-board blocked: check-all failed. Its work is on task/f9-01-board."


def _blocked_words(db, project_id):
    """Return the blocked group's items' words."""
    [_, blocked_group, *_] = desk(db, PROJECT, NOW)
    return [i.words for i in blocked_group.items]


def test_runner_message_only_says_lead_is_looking(planning, db_path, db):
    """Runner message on F9's thread without a lead follow-up: the words add
    " · the lead is looking at it"."""
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_owner_item(
            conn,
            project,
            "blocked",
            "f9-01-board",
            text="f9-01-board blocked: check-all failed; the work is on task/f9-01-board",
            created=_at(timedelta(hours=4)),
        )
        thread = metrics.planner_thread(conn, project, "f9", _at(timedelta(minutes=5)))["id"]
        metrics.add_planner_message(conn, thread, "runner", _at(timedelta(minutes=5)), LOOK)
    finally:
        conn.close()
    assert _blocked_words(db, project) == [
        "check-all failed; the work is on task/f9-01-board · the lead is looking at it"
    ]


def test_runner_message_then_lead_says_waits_on_thread(planning, db_path, db):
    """Runner message followed by a lead message on F9's thread: the words add
    " · the lead's fix waits on F9's thread"."""
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_owner_item(
            conn,
            project,
            "blocked",
            "f9-01-board",
            text="f9-01-board blocked: check-all failed; the work is on task/f9-01-board",
            created=_at(timedelta(hours=4)),
        )
        thread = metrics.planner_thread(conn, project, "f9", _at(timedelta(minutes=5)))["id"]
        metrics.add_planner_message(conn, thread, "runner", _at(timedelta(minutes=5)), LOOK)
        metrics.add_planner_message(
            conn, thread, "lead", _at(timedelta(minutes=1)), "I'll take a look."
        )
    finally:
        conn.close()
    assert _blocked_words(db, project) == [
        "check-all failed; the work is on task/f9-01-board · the lead's fix waits on F9's thread"
    ]


def test_no_runner_message_words_unchanged(planning, db_path, db):
    """No runner message on the card: words stay as the reason alone."""
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_owner_item(
            conn,
            project,
            "blocked",
            "f1-01",
            text="f1-01 blocked: waiting on f12-03",
            created=_at(timedelta(hours=4)),
        )
    finally:
        conn.close()
    assert _blocked_words(db, project) == ["waiting on f12-03"]


def test_another_tickets_runner_message_does_not_count(planning, db_path, db):
    """A runner message about another ticket on the same thread doesn't count for this one."""
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.upsert_owner_item(
            conn,
            project,
            "blocked",
            "f9-02-other",
            text="f9-02-other blocked: waiting on f95-01",
            created=_at(timedelta(hours=4)),
        )
        thread = metrics.planner_thread(conn, project, "f9", _at(timedelta(minutes=5)))["id"]
        metrics.add_planner_message(
            conn,
            thread,
            "runner",
            _at(timedelta(minutes=5)),
            "f9-01-board blocked: check-all failed. Its work is on task/f9-01-board.",
        )
    finally:
        conn.close()
    assert _blocked_words(db, project) == ["waiting on f95-01"]


# --- text boxes grow with what is typed (f82-01) ------------------------------------------------


def test_the_plant_box_grows_as_you_type_and_has_no_scrollbar_until_60_vh(page, planning, serve):
    """Typing ten lines makes the Plant box taller than at load, with no scrollbar inside
    (scrollHeight equals clientHeight)."""
    _open(page, serve())
    initial_height = page.locator('#plant textarea[name="text"]').evaluate("el => el.offsetHeight")
    # Type ten lines
    for i in range(10):
        page.type('#plant textarea[name="text"]', f"Line {i + 1}\n")
    page.wait_for_timeout(100)
    textarea = page.locator('#plant textarea[name="text"]')
    assert textarea.evaluate("el => el.offsetHeight") > initial_height
    # scrollHeight may be 1-2px larger than clientHeight due to border calculations;
    # what matters is that there is no scrollbar (scrollHeight ≈ clientHeight)
    assert (
        abs(textarea.evaluate("el => el.scrollHeight") - textarea.evaluate("el => el.clientHeight"))
        <= 2
    )


def test_the_plant_box_stops_at_60_vh_and_scrolls_inside(page, planning, serve):
    """Typing far past 60% of the window's height stops the box at about that height,
    and it scrolls inside (scrollHeight greater than clientHeight)."""
    page.set_viewport_size({"width": 1024, "height": 800})
    _open(page, serve())
    # Type enough lines to exceed 60vh
    for i in range(100):
        page.type('#plant textarea[name="text"]', f"Line {i + 1}\n")
    page.wait_for_timeout(100)
    textarea = page.locator('#plant textarea[name="text"]')
    max_height = page.evaluate("() => window.innerHeight * 0.6")
    actual_height = textarea.evaluate("el => el.offsetHeight")
    assert abs(actual_height - max_height) < 10
    assert textarea.evaluate("el => el.scrollHeight") > textarea.evaluate("el => el.clientHeight")


def test_emptying_the_plant_box_brings_it_back_to_four_row_height(page, planning, serve):
    """Emptying the box brings it back to its four-row height, never below."""
    _open(page, serve())
    textarea = page.locator('#plant textarea[name="text"]')
    # Measure the initial height right after page opens
    initial_height = textarea.evaluate("el => el.offsetHeight")
    # Type some text to grow it
    for i in range(10):
        page.type('#plant textarea[name="text"]', f"Line {i + 1}\n")
    page.wait_for_timeout(100)
    grown_height = textarea.evaluate("el => el.offsetHeight")
    # Empty the box
    page.fill('#plant textarea[name="text"]', "")
    page.wait_for_timeout(100)
    empty_height = textarea.evaluate("el => el.offsetHeight")
    assert empty_height < grown_height
    # The box returns to its initial height, never below
    assert abs(empty_height - initial_height) <= 1


def test_after_a_plant_is_sent_the_fresh_box_is_at_four_row_height(page, planning, serve):
    """After a plant is sent, the fresh Plant box is back at its four-row height."""
    _open(page, serve())
    textarea = page.locator('#plant textarea[name="text"]')
    # Measure the initial height right after page opens
    initial_height = textarea.evaluate("el => el.offsetHeight")
    # Type several lines to grow the box (page.type fires input events)
    for i in range(10):
        page.type('#plant textarea[name="text"]', f"Line {i + 1}\n")
    page.wait_for_timeout(100)
    page.click("#plant-only")
    page.wait_for_selector("#desk-coming")
    page.wait_for_selector("#plant textarea")
    assert page.input_value('#plant textarea[name="text"]') == ""
    fresh_height = textarea.evaluate("el => el.offsetHeight")
    assert abs(fresh_height - initial_height) <= 1


def test_a_box_filled_by_a_script_fits_when_focused(page, planning, serve):
    """A value set by a script fires no input event (Try again on a refused note): the box
    fits its text when it is focused, without a script error (f82 review)."""
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    _open(page, serve())
    textarea = page.locator('#plant textarea[name="text"]')
    initial_height = textarea.evaluate("el => el.offsetHeight")
    textarea.evaluate(
        "el => { el.value = Array.from({length: 10}, (_, i) => 'Line ' + i).join('\\n'); }"
    )
    assert textarea.evaluate("el => el.offsetHeight") == initial_height
    textarea.focus()
    assert textarea.evaluate("el => el.offsetHeight") > initial_height
    assert textarea.evaluate("el => el.scrollHeight - el.clientHeight") <= 2
    assert errors == []


def test_a_key_point_comment_box_grows_the_same_way(page, planning, db_path, serve):
    """A key point's comment box on a card's thread grows the same way (the rule is
    page-wide, not the Plant box's)."""
    _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_ADR))
    _open(page, serve(), "/planning/f6/proposals/adr-20")
    # Open the first point's comment box
    page.click('.key-point[data-point="1"] .change-btn')
    page.wait_for_timeout(100)
    textarea = page.locator('.key-point[data-point="1"] textarea.comment')
    initial = textarea.evaluate("el => el.offsetHeight")
    # Type to grow it
    for i in range(10):
        page.type('.key-point[data-point="1"] textarea.comment', f"Comment line {i + 1}\n")
    page.wait_for_timeout(100)
    grown = textarea.evaluate("el => el.offsetHeight")
    assert grown > initial
    # scrollHeight may be 1-2px larger than clientHeight due to border calculations
    assert (
        abs(textarea.evaluate("el => el.scrollHeight") - textarea.evaluate("el => el.clientHeight"))
        <= 2
    )


# --- Coming says which reply the lead is writing (F84) ----------------------------------------


def _line(
    serve: Callable[..., TestClient],
    db_path: Path,
    project_id: int,
    *,
    writing: bool = True,
    reason: str = "your message on F84",
) -> TestClient:
    """The live run (``serve``), a planner reply that took 6 min, then the owner's messages on
    f84, f85 and f86, each with its planner row, oldest first. With ``writing``, a planner job
    2 min in whose row is f84's, as the runner marks it (``runner/loop.py``: ``started_job``);
    else only the ticket job ``f1-04-live`` runs, past its typical length."""
    client = serve()

    def write(conn: sqlite3.Connection) -> None:
        run = conn.execute("SELECT id FROM runs WHERE run_dir = '20261002-113500'").fetchone()
        planner: dict[str, Any] = {
            "ticket_id": None,
            "milestone_id": None,
            "role": "planner",
            "agent": OPUS,
        }
        # one row per run, ticket, role and attempt (``start_job``): the earlier reply is attempt 1
        done = metrics.start_job(
            conn, run["id"], attempt=1, started=_at(timedelta(hours=3)), **planner
        )
        metrics.finish_job(
            conn, done, ended=_at(timedelta(hours=3) - timedelta(minutes=6)), outcome="done"
        )
        rows = {}
        for i, card in enumerate(["f84", "f85", "f86"]):
            asked = _at(timedelta(minutes=40 - i))
            metrics.add_request(conn, project_id, "plan_message", card, '{"text": "When?"}', asked)
            rows[card] = metrics.queue_job(
                conn,
                project_id,
                "planner",
                f"{card}#{i + 1}",
                reason if card == "f84" else "your message",
                _at(timedelta(minutes=30 - i)),
            )
        if writing:
            job = metrics.start_job(
                conn, run["id"], attempt=2, started=_at(timedelta(minutes=2)), **planner
            )
            conn.execute("UPDATE work_queue SET started_job = ? WHERE id = ?", (job, rows["f84"]))

    _write(db_path, write)
    return client


def _boxes(html: str) -> list[tuple[str, str, bool]]:
    """Coming's thread boxes, in order: (thread, text, drawn as the one being written)."""
    return [
        (thread, _text(body), "writing" in attrs)
        for thread, attrs, body in re.findall(
            r'<a href="/planning/([^"?]+)"([^>]*)>(.*?)</a>', _coming(html), re.S
        )
    ]


def test_coming_puts_the_reply_being_written_first_and_the_others_in_line(planning, db_path, serve):
    """F84 D3, D4: only f84's box, whose row the running planner job started, says "writing";
    f85 and f86 say their place and about when, from the 6 min a reply takes (4 min left)."""
    client = _line(serve, db_path, planning)
    writing = (
        "Writing now f84 the lead is writing this reply · 2 min in, about 4 min left"
        " 2 min of about 6 min (a reply's usual length)"
    )
    assert _boxes(_page(client)) == [
        ("f84", writing, True),
        ("f85", "f85 next, after F84's reply · about 4 min", False),
        ("f86", "f86 3rd in line · about 10 min", False),
    ]


def test_a_row_not_started_never_says_writing(planning, db_path, serve):
    """The planner job runs but no row names it: no box nor thread page says "writing"."""
    client = _line(serve, db_path, planning)
    _write(db_path, lambda conn: conn.execute("UPDATE work_queue SET started_job = NULL"))
    boxes = _boxes(_page(client))
    assert [b[0] for b in boxes] == ["f84", "f85", "f86"]
    assert not any(writing or "writing" in text for _, text, writing in boxes)
    assert boxes[0][1] == "f84 next, after the lead's reply · about 4 min"
    for thread in ("f84", "f85", "f86"):
        assert "writing" not in _text(_thread(client, thread))


def test_a_look_at_a_blocked_ticket_says_so(planning, db_path, serve):
    client = _line(serve, db_path, planning, reason="a ticket blocked on F84")
    first = _boxes(_page(client))[0][1]
    assert first.startswith("Writing now f84 the lead is looking at the blocked ticket · 2 min in")
    assert "writing this reply" not in first


def test_with_a_ticket_job_running_the_first_reply_comes_after_it(planning, db_path, serve):
    """No planner job: the first thread waits for f1-04-live (past its typical: any minute),
    the next one a reply's 6 min more."""
    client = _line(serve, db_path, planning, writing=False)
    assert _boxes(_page(client)) == [
        ("f84", "f84 next, after f1-04-live · any minute now", False),
        ("f85", "f85 2nd in line · about 6 min", False),
        ("f86", "f86 3rd in line · about 12 min", False),
    ]


def test_each_thread_page_says_its_place_or_that_it_is_being_written(planning, db_path, serve):
    client = _line(serve, db_path, planning)
    f86 = _thread(client, "f86")
    assert "Next for the lead · 3rd in line · about 10 min" in _text(f86)
    assert '<p id="waiting" class="writing"' not in f86
    f84 = _thread(client, "f84")
    writing = "Next for the lead · the lead is writing this reply · 2 min in, about 4 min left"
    assert writing in _text(f84)
    assert '<p id="waiting" class="writing"' in f84
    # the words in Opus's ink, darkened in the light theme to read on a pale bay
    assert "color: var(--opus-ink)" in f84
    assert "color: var(--opus-ink)" not in f86


def test_the_tile_names_the_reply_being_written_and_the_line_after_it(planning, db_path, serve):
    """F84 D6: the ticket job stays above; f86's reply is written in about 10 + 6 min."""
    html = _page(_line(serve, db_path, planning))
    tile = _tile(html, "factory-now")
    assert "Running f1-04-live" in tile
    assert "Writing now: F84, f84 · 2 min in" in tile
    assert "Then 2 replies in line, about 16 min for all." in tile
    assert "Your next reply" not in tile
    assert '<a class="key" href="/planning/f84">F84</a>' in html


def test_a_held_reply_and_a_message_with_no_row_read_as_today(planning, db_path, serve):
    """f85's row is parked for a Claude limit, and f87's message has no row yet: neither has a
    place; the held one says until when and comes last (D4), the other after the reply being
    written."""
    client = _line(serve, db_path, planning)
    until = NOW + timedelta(hours=2)

    def hold_and_ask(conn: sqlite3.Connection) -> None:
        conn.execute(
            "UPDATE work_queue SET not_before = ? WHERE subject = 'f85#2'", (until.isoformat(),)
        )
        value = '{"text": "And?"}'
        metrics.add_request(conn, planning, "plan_message", "f87", value, NOW.isoformat())

    _write(db_path, hold_and_ask)
    held = f"waits for Claude's 5-hour limit, until {until.astimezone():%a %H:%M}"
    assert [b[:2] for b in _boxes(_page(client))][1:] == [
        ("f86", "f86 next, after F84's reply · about 4 min"),
        ("f87", "f87 waiting for the lead · after F84's reply, ~4 min"),
        ("f85", f"f85 waiting for the lead · {held}"),
    ]


# --- one button set (f81-03) --------------------------------------------------------------------


def test_plant_only_has_btn_go(planning, serve, db_path):
    """D5: #plant-only carries class 'btn go'."""
    client = _line(serve, db_path, planning)
    html = _page(client)
    btn = re.search(r'<button[^>]*id="plant-only"[^>]*class="([^"]*)"', html)
    assert btn
    classes = btn[1].split()
    assert "btn" in classes
    assert "go" in classes


def test_plant_ask_has_btn_plain(planning, serve, db_path):
    """D5: #plant-ask carries class 'btn plain'."""
    client = _line(serve, db_path, planning)
    html = _page(client)
    btn = re.search(r'<button[^>]*id="plant-ask"[^>]*class="([^"]*)"', html)
    assert btn
    classes = btn[1].split()
    assert "btn" in classes
    assert "plain" in classes


def test_no_button_in_planning_has_inline_style(planning, serve, db_path):
    """D5: no <button> tag in planning templates has style=."""
    client = _line(serve, db_path, planning)
    html = _page(client)
    buttons = re.findall(r"<button[^>]*>", html)
    for b in buttons:
        assert "style=" not in b.lower(), f"Button has inline style: {b[:100]}"
