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
from tests.browser.conftest import DISPLAY, PHONE, layout_problems
from tests.factory_dashboard.conftest import (
    LOCAL,
    NOW,
    OPUS,
    PROJECT,
    _at,
    write_planning,
)
from tests.runner.conftest import git

ORIGIN = "http://127.0.0.1:8765"
STATIC = Path(__file__).parents[2] / "factory_dashboard" / "static"


@pytest.fixture
def planning(db_path: Path) -> int:
    """``write_planning``'s rows in the fixture database; the project's id."""
    conn = metrics.open_db(db_path)
    try:
        return write_planning(conn)
    finally:
        conn.close()


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
        ("/planning/f6/proposals/adr-20", "ADR 20: the planning room"),
        ("/planning/f6/proposals/plan", "F6 plan: 7 tickets"),
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
        "Your answers wanted",
        "Proposals to review",
        "Finished, to talk through",
        "Seeds, not asked about yet",
    ]
    assert [[i.title for i in g.items] for g in groups] == [
        [],
        [],
        [],
        ["The factory measures itself", "The web app"],
        [],
    ]
    assert desk(db, "nowhere", NOW)[3].items == []


def test_an_idea_card_with_a_thread_is_not_a_seed(planning, db):
    seeds = desk(db, PROJECT, NOW)[4].items
    assert [s.title for s in seeds] == ["Parallel developers"]


@pytest.mark.parametrize(
    ("kind", "subject", "value", "done", "result", "still_open"),
    [
        # worked: the ADR is accepted, the plan isn't about it
        ("accept_adr", "f6", "20", True, "accepted docs/adr/20-planning-room.md", ["plan"]),
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
    proposals = desk(db, PROJECT, NOW)[2].items
    assert [p.link.rsplit("/", 1)[1] for p in proposals if not p.on_its_way] == still_open
    # a pending one stays, dashed and on its way (the owner, 2026-10-08)
    assert [p.link.rsplit("/", 1)[1] for p in proposals if p.on_its_way] == (
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
    assert len(desk(db, PROJECT, NOW)[2].items) == 2


def test_the_factory_tile_names_the_running_ticket(planning, serve):
    """No message pending: the tile names the job, and says planning goes first."""
    tile = _tile(_page(serve()), "factory-now")
    assert f"Running f1-04-live on {LOCAL}, attempt 2, 12 min." in tile
    assert "Your next reply" not in tile
    assert "planning goes first" in tile


def test_a_pending_message_says_when_the_reply_comes(planning, db_path, serve):
    """An open planner row: answered after the running job, which ran past its typical
    10 min; with a planner job running, the lead is writing now."""
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
    assert "Your next reply: the lead is writing its reply now." in tile
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
    page.set_viewport_size(size)
    _open(page, serve())
    assert page.locator("#desk-seeds").is_visible()
    assert page.locator("#desk-refused").is_visible()
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


def test_a_fixture_reply_with_7_points_shows_each_point(planning, db_path, serve):
    """The card's header, the messages in order, then each point's title, answer and action
    within that point, each with its Comment… box, and the progress line."""
    _write(db_path, lambda conn: _seven_points(conn, planning))
    html = _thread(serve(), "f6")
    assert "The planning room" in _text(html.split('<header id="card"', 1)[1].split("</header>")[0])
    text = _text(html)
    assert text.index("A first go.") < text.index("Looks good.") < text.index("Here's each point")
    points = _points(html)
    assert list(points) == [str(p["n"]) for p in _SEVEN_POINTS]
    for p in _SEVEN_POINTS:
        point = points[str(p["n"])]
        assert f"{p['title']} {p['answer']} → {p['action']} Comment…" in point
    assert "7 points · 0 comments" in text


def test_a_reply_with_points_folds_its_text_and_one_without_shows_it(planning, db_path, serve):
    """F41 D2, D3: the points carry everything, so the text waits in a closed "Full reply"
    above them; a reply with no points (its block broken) shows its text open, and one with
    points but no text has neither a fold nor an empty line. The owner's never folds."""
    _write(db_path, lambda conn: _seven_points(conn, planning))

    def later(conn: sqlite3.Connection) -> None:
        f6 = metrics.planner_thread(conn, planning, "f6", NOW.isoformat())["id"]
        metrics.add_planner_message(conn, f6, "owner", _at(timedelta(minutes=20)), "Why so?")
        metrics.add_planner_message(
            conn, f6, "lead", _at(timedelta(minutes=10)), "Sorry.\n\n(no json block.)"
        )
        metrics.add_planner_message(
            conn, f6, "lead", _at(timedelta(minutes=5)), "", points=_SEVEN_POINTS[:1]
        )

    _write(db_path, later)
    html = _thread(serve(), "f6")
    [fold] = re.findall(r'<details class="full-reply"[^>]*>(.*?)</details>', html, re.S)
    assert "open" not in html.split('<details class="full-reply"', 1)[1].split(">", 1)[0]
    assert _text(fold) == "Full reply Here's each point with my answer."
    assert html.index('class="full-reply"') < html.index('class="deck"')
    assert "Sorry." not in fold and "(no json block.)" in _text(html)
    assert "Why so?" not in fold and "Why so?" in _text(html)
    assert html.count('class="full-reply"') == 1  # the owner's, the broken and the textless
    assert '<p style="margin: 0; white-space: pre-line"></p>' not in html


def test_the_proposals_column_shows_each_proposal_open_or_answered(planning, db_path, serve):
    """The latest listing's proposals, each linking to its review page; one the owner approved
    since is answered (D6)."""
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn, planning, "approve_plan", "f6", None, _at(timedelta(minutes=30))
        ),
    )
    html = _thread(serve(), "f6")
    found = re.findall(r'<a href="([^"?]+)[^"]*" class="proposal"[^>]*>(.*?)</a>', html, re.S)
    assert [(link, _text(body)) for link, body in found] == [
        ("/planning/f6/proposals/adr-20", "ADR · open ADR 20: the planning room"),
        ("/planning/f6/proposals/plan", "PLAN · on its way F6 plan: 7 tickets"),
    ]


def test_send_with_comments_posts_one_request(page, planning, db_path, serve):
    """Comments on points 2 and 4 and a free message: one ``plan_message`` request about the
    thread carrying them, the other points agreed by saying nothing."""
    _write(db_path, lambda conn: _seven_points(conn, planning))
    _open(page, serve(), "/planning/f6")
    for n, comment in (("2", "Inside, but say how it stops."), ("4", 'Keep "general" too.')):
        page.click(f'li[data-point="{n}"] summary')
        page.fill(f'li[data-point="{n}"] textarea', comment)
    page.fill('#reply textarea[name="text"]', "And the phone?")
    page.wait_for_selector("#progress >> text=7 points · 2 comments")
    page.click('#reply button[type="submit"]')
    page.wait_for_selector("#conversation >> text=And the phone?")
    page.wait_for_selector("#reply", state="hidden")
    # waiting message: #waiting present, message shows "Sent"
    assert page.locator("#waiting").is_visible()
    msg = page.locator("#conversation .message").last
    assert msg.is_visible()
    assert "Sent" in msg.inner_text()
    conn = metrics.open_db(db_path)
    try:
        rows = conn.execute("SELECT * FROM owner_requests WHERE project_id = ?", (planning,))
        asked = [(r["kind"], r["subject"], json.loads(r["value"])) for r in rows]
    finally:
        conn.close()
    assert asked == [
        (
            "plan_message",
            "f6",
            {
                "text": "And the phone?",
                "comments": {"2": "Inside, but say how it stops.", "4": 'Keep "general" too.'},
            },
        )
    ]


def test_an_open_plan_message_request_shows_sent_with_dashed_border(planning, db_path, serve):
    """An open plan_message request: the owner's message element has the text, \"On N: <comment>\"
    and \"Sent\", a dashed hazard border in its style, `#waiting` is present and `#reply` is
    absent."""
    _write(db_path, lambda conn: _seven_points(conn, planning))
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn,
            planning,
            "plan_message",
            "f6",
            json.dumps(
                {
                    "text": "And the phone?",
                    "comments": {"2": "Inside, but say how it stops.", "4": 'Keep "general" too.'},
                }
            ),
            _at(timedelta(minutes=5)),
        ),
    )
    html = _thread(serve(), "f6")
    # find the owner's waiting message containing "And the phone?"
    msg_html = ""
    msg_style = ""
    for m in re.finditer(r'<article class="message"([^>]*)>(.*?)</article>', html, re.S):
        if "And the phone?" in m[2]:
            msg_html = m[2]
            msg_style = m[1]
            break
    assert msg_html, "no message with 'And the phone?' found"
    # text and comment reference
    assert "And the phone?" in _text(msg_html)
    assert "On 2:" in _text(msg_html) and "Inside, but say how it stops." in _text(msg_html)
    # "Sent" status
    assert "Sent" in _text(msg_html)
    # dashed hazard border (on the article's style attribute)
    assert "border-style: dashed" in msg_style
    assert "border-color: var(--hazard)" in msg_style
    # #waiting present, #reply absent
    assert '<p id="waiting"' in html
    assert 'id="reply"' not in html


def test_a_waiting_messages_comments_show_in_point_order(planning, db_path, serve):
    """By number, as the runner keeps them: point 2's before point 10's."""
    _write(db_path, lambda conn: _seven_points(conn, planning))
    value = json.dumps({"text": "", "comments": {"10": "Ten.", "2": "Two.", "3": "  "}})
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn, planning, "plan_message", "f6", value, _at(timedelta(minutes=5))
        ),
    )
    text = _text(_thread(serve(), "f6"))
    assert text.index("On 2:") < text.index("On 10:")
    assert "On 3:" not in text  # a blank comment says nothing


def test_a_done_plan_message_with_lead_reply_shows_once(planning, db_path, serve):
    """Once the request is done and the lead replies: the text shows once, with no \"Sent\" and
    no dashed border."""
    _write(db_path, lambda conn: _seven_points(conn, planning))
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn,
            planning,
            "plan_message",
            "f6",
            '{"text": "And the phone?"}',
            _at(timedelta(minutes=5)),
        ),
    )
    client = serve()
    # first: the waiting message is there
    html = _thread(client, "f6")
    assert "Sent" in _text(html)
    assert "border-style: dashed" in html

    # now the request is done and the lead has replied
    def done_and_replied(conn: sqlite3.Connection) -> None:
        conn.execute(
            "UPDATE owner_requests SET done = ? WHERE kind = 'plan_message'",
            (_at(timedelta(minutes=4)),),
        )
        thread = metrics.planner_thread(
            conn, project_id=planning, card="f6", created=_at(timedelta(minutes=4))
        )["id"]
        metrics.add_planner_message(
            conn, thread, "owner", _at(timedelta(minutes=4)), "And the phone?"
        )
        metrics.add_planner_message(conn, thread, "lead", _at(timedelta(minutes=1)), "It passes.")

    _write(db_path, done_and_replied)
    html = _thread(client, "f6")
    # text appears once (no "Sent" line, no dashed border)
    assert html.count("And the phone?") == 1
    assert "Sent" not in _text(html)
    assert "border-style: dashed" not in html


def test_a_pending_reply_hides_send_and_shows_the_wait(planning, db_path, serve):
    """An open planner row about this thread: the wait instead of Send and the Comment…
    boxes; one about another thread changes nothing here."""
    _write(db_path, lambda conn: _seven_points(conn, planning))
    _write(
        db_path,
        lambda conn: metrics.queue_job(
            conn, planning, "planner", "general#1", "a message", _at(timedelta(minutes=5))
        ),
    )
    client = serve()
    assert '<form id="reply"' in _thread(client, "f6")
    _write(
        db_path,
        lambda conn: metrics.queue_job(
            conn, planning, "planner", "f6#2", "a message", _at(timedelta(minutes=4))
        ),
    )
    html = _thread(client, "f6")
    assert "Next for the lead · after f1-04-live, any minute now" in _text(html)
    assert '<form id="reply"' not in html
    assert "Send" not in _text(html)
    assert "Comment…" not in html


def test_only_a_seeds_thread_has_remove_seed(planning, serve):
    """f6-17: F9 is an idea card; F6 isn't, and the general thread is no card."""
    client = serve()
    html = _thread(client, "f9")
    assert "Remove seed" in html and "Remove F9? Its notes go too." in _text(html)
    assert html.index('id="reply"') < html.index('id="drop-seed"')
    assert _posts(html, "drop-seed") == {"kind": "drop_seed", "project": PROJECT, "subject": "f9"}
    for other in ("f6", "general"):
        page = _thread(client, other)
        assert "Remove seed" not in page and 'id="drop-seed"' not in page


def test_remove_seed_asks_first_then_posts_drop_seed(page, planning, db_path, serve):
    _open(page, serve(), "/planning/f9")
    assert not page.locator("#drop-seed").is_visible()  # the confirm step hides it
    page.click("#remove-seed summary")
    assert page.locator("#drop-seed").is_visible()
    page.click("#drop-seed")
    page.wait_for_selector("#drop-status >> text=Asked")
    conn = metrics.open_db(db_path)
    try:
        rows = conn.execute("SELECT * FROM owner_requests WHERE project_id = ?", (planning,))
        asked = [(r["kind"], r["subject"], r["value"]) for r in rows]
    finally:
        conn.close()
    assert asked == [("drop_seed", "f9", None)]


# --- proposal review page (f6-08) -----------------------------------------------------------

_REVIEW_ADR: dict[str, Any] = {
    "id": "adr-20",
    "kind": "adr",
    "title": "ADR 20: the planning room",
    "path": "docs/adr/20-planning-room.md",
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
_REVIEW_MOCKUP: dict[str, Any] = {
    "id": "mockup",
    "kind": "mockup",
    "title": "The desk, drawn",
    "path": "docs/milestones/f6-mockup/index.html",
    "key_points": [],
}
_REVIEW_SEED: dict[str, Any] = {
    "id": "seed-1",
    "kind": "seed",
    "title": "Parallel developers",
    "path": None,
    "key_points": [{"n": 1, "title": "Two at once", "text": "Beside each other.", "flag": False}],
}
ADR_ON_MAIN = "# ADR 20: the planning room\n\n- **Status:** {status}\n"


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


def _key_points(html: str) -> list[str]:
    return [
        _text(body) for body in re.findall(r'<div class="key-point"[^>]*>(.*?)<button', html, re.S)
    ]


def _posts(html: str, button: str) -> dict[str, str]:
    """What the button posts to ``/requests``: its ``hx-vals``."""
    found = re.search(rf'<button type="button" id="{button}"[^>]*hx-vals=\'([^\']*)\'', html)
    assert found, button
    vals: dict[str, str] = json.loads(unescape(found[1]))
    return vals


@pytest.fixture
def checkout(tmp_path: Path, db_path: Path, planning: int, monkeypatch) -> Path:
    """The project's repo, a git checkout on main; its ADR 20 not there yet."""
    for name in ("GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE"):  # set when run from a hook
        monkeypatch.delenv(name, raising=False)
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "Test")
    git(repo, "commit", "-q", "--allow-empty", "-m", "init")
    _write(db_path, lambda conn: metrics.upsert_project(conn, PROJECT, repo=str(repo)))
    return repo


def test_an_adr_proposal_shows_its_points_in_order_with_their_flags(planning, db_path, serve):
    """Each point's number, title and text in the proposal's order, a ⚑ only where ``flag`` is
    true; tabs for the card's proposals; Accept ADR posts the number from the path."""
    _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_ADR, _REVIEW_PLAN))
    html = _review_page(serve(), "/planning/f6/proposals/adr-20")
    assert _key_points(html) == [
        "1 ⚑ Planning goes first At the next pick.",
        "2 Inside the runner One process.",
        "3 Opus, in your 25% The whole window.",
    ]
    nav = html.split('<nav id="proposal-tabs"', 1)[1].split("</nav>", 1)[0]
    assert re.findall(r'<a href="([^"?]+)[^"]*"( aria-current="page")?', nav) == [
        ("/planning/f6/proposals/adr-20", ' aria-current="page"'),
        ("/planning/f6/proposals/plan", ""),
    ]
    assert _posts(html, "accept-adr") == {
        "kind": "accept_adr",
        "project": PROJECT,
        "subject": "f6",
        "value": "20",
    }
    assert 'id="approve-plan"' not in html
    assert '<iframe id="mockup"' not in html


def test_a_comment_turns_the_primary_button_into_send_back(page, planning, db_path, serve):
    """Accept ADR until a comment; then Send back alone, posting the comments by point."""
    _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_ADR))
    _open(page, serve(), "/planning/f6/proposals/adr-20")
    assert page.locator("#accept-adr").is_visible()
    assert not page.locator("#send-back").is_visible()
    page.click('.change-btn[data-point="2"]')
    page.fill('textarea.comment[data-point="2"]', "Say how it stops.")
    assert not page.locator("#accept-adr").is_visible()
    assert page.locator("#send-back").inner_text().lower() == "send 1 change back"
    page.click("#send-back")
    page.wait_for_selector("#review-status >> text=Asked")
    conn = metrics.open_db(db_path)
    try:
        rows = conn.execute("SELECT * FROM owner_requests WHERE project_id = ?", (planning,))
        asked = [(r["kind"], r["subject"], json.loads(r["value"])) for r in rows]
    finally:
        conn.close()
    assert asked == [
        ("send_back", "f6/adr-20", {"text": "", "comments": {"2": "Say how it stops."}})
    ]


def test_approve_plan_waits_for_the_cards_adr_on_main(planning, db_path, serve, checkout):
    """Disabled while ADR 20 is missing from main, then while it is Proposed; enabled once
    Accepted. It posts ``approve_plan`` about the card."""
    _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_ADR, _REVIEW_PLAN))
    client = serve()

    def approve() -> str:
        html = _review_page(client, "/planning/f6/proposals/plan")
        found = re.search(r'<button type="button" id="approve-plan"[^>]*>', html)
        assert found
        assert _posts(html, "approve-plan") == {
            "kind": "approve_plan",
            "project": PROJECT,
            "subject": "f6",
        }
        return found[0]

    assert " disabled" in approve()
    adr = checkout / "docs" / "adr" / "20-planning-room.md"
    adr.parent.mkdir(parents=True)
    adr.write_text(ADR_ON_MAIN.format(status="Proposed"))
    assert " disabled" in approve()
    adr.write_text(ADR_ON_MAIN.format(status="Accepted"))
    assert " disabled" not in approve()


def test_a_seeds_button_posts_plant_about_its_general_id(planning, db_path, serve):
    _write(db_path, lambda conn: _review(conn, planning, "general", _REVIEW_SEED))
    html = _review_page(serve(), "/planning/general/proposals/seed-1")
    assert _posts(html, "plant") == {
        "kind": "plant",
        "project": PROJECT,
        "subject": "general/seed-1",
    }
    assert 'id="accept-adr"' not in html
    assert 'id="approve-plan"' not in html


_REVIEW_MERGE: dict[str, Any] = {
    "id": "merge-f9",
    "kind": "merge",
    "title": "Parallel, said twice",
    "path": "docs/milestones/f9-parallel.md",
    "into": "f7",
    "key_points": [{"n": 1, "title": "Notes", "text": "F9's notes go to F7.", "flag": False}],
}


def test_a_merge_shows_like_the_others_and_its_button_approves_the_threads_plan(
    planning, db_path, db, serve
):
    """f6-12: on the desk and its page, its words say "merge F9 into F7"; approving it is the
    thread's ``approve_plan``, which settles it (D6)."""
    _write(db_path, lambda conn: _review(conn, planning, "f9", _REVIEW_MERGE))
    [item] = [i for i in desk(db, PROJECT, NOW)[2].items if i.link.endswith("/merge-f9")]
    assert item.words == "merge F9 into F7 · 1 key points"
    html = _review_page(serve(), "/planning/f9/proposals/merge-f9")
    assert ">Merge F9 into F7</span>" in html and "Approve: merge F9 into F7" in html
    assert _posts(html, "approve-merge") == {
        "kind": "approve_plan",
        "project": PROJECT,
        "subject": "f9",
    }
    assert 'id="approve-plan"' not in html and 'id="accept-adr"' not in html
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn, planning, "approve_plan", "f9", None, NOW.isoformat()
        ),
    )
    [item] = [i for i in desk(db, PROJECT, NOW)[2].items if i.link.endswith("/merge-f9")]
    assert item.on_its_way  # on its way until the runner's next pick, no longer waiting on you


def _merges_on_the_desk(db: sqlite3.Connection) -> list[str]:
    return [
        i.link for i in desk(db, PROJECT, NOW)[2].items if "/merge-" in i.link and not i.on_its_way
    ]


def test_an_approved_merge_leaves_the_desk(planning, db_path, db):
    """2026-10-08: a merge-only approval's result is "approved: merged F9 into F7", which the
    desk didn't count as worked, so every approved merge stayed."""
    _write(db_path, lambda conn: _review(conn, planning, "f9", _REVIEW_MERGE))
    _finished(db_path, planning, "approve_plan", "f9", None, "approved: merged F9 into F7")
    assert _merges_on_the_desk(db) == []


@pytest.mark.parametrize("gone", ["f9", "f7"])
def test_a_merge_whose_card_left_main_asks_nothing(planning, db_path, db, checkout, gone):
    """F9 or F7 was merged elsewhere since the lead proposed it: nothing is left to ask."""
    docs = checkout / "docs" / "milestones"
    docs.mkdir(parents=True)
    for key in {"f9", "f7"} - {gone}:
        (docs / f"{key}-x.md").write_text(f"# Milestone {key.upper()}: x\n")
    _write(db_path, lambda conn: _review(conn, planning, "f9", _REVIEW_MERGE))
    assert _merges_on_the_desk(db) == []
    (docs / f"{gone}-x.md").write_text(f"# Milestone {gone.upper()}: x\n")
    assert _merges_on_the_desk(db) == ["/planning/f9/proposals/merge-f9"]


@pytest.mark.parametrize(
    ("thread", "proposal", "words"),
    [
        ("f6", "plan", "the card's plan branch goes"),
        ("f9", "merge-f9", "only this proposal closes"),
    ],
)
def test_reject_posts_a_reject_and_says_what_it_takes(
    planning, db_path, serve, thread, proposal, words
):
    """F31 D2: Reject… opens, says what goes, and its button posts `reject` on the proposal."""
    if thread == "f9":
        _write(db_path, lambda conn: _review(conn, planning, "f9", _REVIEW_MERGE))
    html = _review_page(serve(), f"/planning/{thread}/proposals/{proposal}")
    fold = html.split('<details id="reject">', 1)[1].split("</details>", 1)[0]
    assert words in _text(fold)
    assert _posts(fold, "reject-button") == {
        "kind": "reject",
        "project": PROJECT,
        "subject": f"{thread}/{proposal}",
    }


def test_a_merge_the_lead_applied_asks_nothing(planning, db_path, db, serve):
    """F49 D1: the runner applied it after the job; no Approve, on the desk or its page."""
    applied = {**_REVIEW_MERGE, "applied": True}
    _write(db_path, lambda conn: _review(conn, planning, "f9", applied))
    assert not [i for i in desk(db, PROJECT, NOW)[2].items if i.link.endswith("/merge-f9")]
    html = _review_page(serve(), "/planning/f9/proposals/merge-f9")
    assert 'id="approve-merge"' not in html and 'id="merged-by-lead"' in html
    assert 'id="reject"' not in html  # nothing left to reject


def test_the_mockup_route_serves_the_plan_branchs_mockup_and_nothing_else(
    planning, db_path, serve, checkout
):
    """The mock-up proposal's page frames its file, sandboxed; the route reads it from
    ``plan/f6`` and refuses any path outside a ``-mockup/`` folder, even a draft beside it."""
    git(checkout, "checkout", "-q", "-b", "plan/f6")
    for rel, text in (
        ("docs/milestones/f6-mockup/index.html", "<p>the desk</p>"),
        ("docs/milestones/f6-planning-room.md", "# F6"),
        ("docs/adr/20-planning-room.md", ADR_ON_MAIN.format(status="Proposed")),
    ):
        (checkout / rel).parent.mkdir(parents=True, exist_ok=True)
        (checkout / rel).write_text(text)
    git(checkout, "add", "-A")
    git(checkout, "commit", "-q", "-m", "drafts")
    git(checkout, "checkout", "-q", "main")
    _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_MOCKUP))
    client = serve()
    html = _review_page(client, "/planning/f6/proposals/mockup")
    frame = re.search(r'<iframe id="mockup" src="([^"?]+)[^"]*" sandbox="allow-scripts" ', html)
    assert frame and frame[1] == "/planning/mockups/f6/docs/milestones/f6-mockup/index.html"
    served = client.get(frame[1])
    assert (served.status_code, served.text) == (200, "<p>the desk</p>")
    # Opened on its own, outside the sandboxed frame, it still runs in an origin of its own,
    # so its scripts can't post to /requests as the dashboard (ADR 18 item 3)
    assert served.headers["content-security-policy"] == "sandbox allow-scripts"
    for refused in (
        "docs/milestones/f6-planning-room.md",
        "docs/adr/20-planning-room.md",
        "docs/milestones/f6-mockup/missing.html",
        "docs/milestones/f6-mockup/",
    ):
        assert client.get(f"/planning/mockups/f6/{refused}").status_code == 404, refused


_MOCKUP_WITH_A_SCRIPT = """<p id="out">dead</p>
<script>
  var seen;
  try { seen = parent.document.title; } catch (e) { seen = "refused"; }
  document.getElementById("out").textContent = "alive " + window.origin + " " + seen;
</script>"""


def test_a_mockups_scripts_run_in_the_review_pages_frame_as_no_one(
    page, planning, db_path, serve, checkout
):
    """F104 D1, D2 (the owner, 2026-10-10: "Mockups act like I can interact with but I can't"):
    the frame lets the mock-up's scripts run and nothing else. Its origin is its own, so it
    can't read the page around it or post as the dashboard. Only the browser says what a
    sandbox allows, so this runs in Chromium."""
    git(checkout, "checkout", "-q", "-b", "plan/f6")
    mockup = checkout / "docs" / "milestones" / "f6-mockup" / "index.html"
    mockup.parent.mkdir(parents=True, exist_ok=True)
    mockup.write_text(_MOCKUP_WITH_A_SCRIPT)
    git(checkout, "add", "-A")
    git(checkout, "commit", "-q", "-m", "drafts")
    git(checkout, "checkout", "-q", "main")
    _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_MOCKUP))
    page.set_viewport_size({"width": 1024, "height": 800})
    _open(page, serve(), "/planning/f6/proposals/mockup")
    out = page.frame_locator("#mockup").locator("#out")
    out.filter(has_text="alive").wait_for(timeout=5000)
    assert out.inner_text() == "alive null refused"
    # exactly this: allow-same-origin would make a mock-up's script the dashboard itself
    assert page.locator("#mockup").get_attribute("sandbox") == "allow-scripts"


_REVIEW_REPLAN: dict[str, Any] = {
    "id": "replan",
    "kind": "replan",
    "title": "F7, redirected",
    "path": None,
    "key_points": [{"n": 1, "title": "Less", "text": "Set b aside.", "flag": False}],
}


def _changes(html: str) -> list[tuple[str, str, str | None]]:
    """Each row of "What approving changes": its path, its word and its text, if shown."""
    section = re.search(r'<section id="plan-changes".*?</section>', html, re.S)
    assert section, "no plan-changes section"
    rows = re.findall(r'<li class="plan-change"[^>]*>(.*?)</li>', section[0], re.S)
    found = []
    for row in rows:
        path = re.search(r'<code class="path"[^>]*>(.*?)</code>', row, re.S)
        word = re.search(r'<b class="word"[^>]*>(.*?)</b>', row, re.S)
        text = re.search(r"<pre[^>]*>(.*?)</pre>", row, re.S)
        assert path and word, row
        found.append((unescape(path[1]), word[1], unescape(text[1]) if text else None))
    return found


def _replanned(checkout: Path) -> None:
    """main holds f7-01-a and f7-02-b; ``plan/f7`` changes a, adds c and sets b aside."""
    a, b = "tasks/ready/f7-01-a.md", "tasks/ready/f7-02-b.md"
    for rel, text in ((a, "main's a"), (b, "<b>'s text")):
        (checkout / rel).parent.mkdir(parents=True, exist_ok=True)
        (checkout / rel).write_text(text)
    git(checkout, "add", "-A")
    git(checkout, "commit", "-q", "-m", "tickets")
    git(checkout, "checkout", "-q", "-b", "plan/f7")
    (checkout / a).write_text("the replan's a")
    (checkout / "tasks/ready/f7-03-c.md").write_text("the replan's c")
    (checkout / "tasks/later").mkdir()
    git(checkout, "mv", b, "tasks/later/f7-02-b.md")
    git(checkout, "add", "-A")
    git(checkout, "commit", "-q", "-m", "replan")
    git(checkout, "checkout", "-q", "main")


def test_a_replan_shows_what_approving_changes_with_each_text(planning, db_path, serve, checkout):
    """f6-24: each ticket it changes, adds or sets aside, its text from the branch, escaped;
    main's copy never; and what approving a replan does at once."""
    _replanned(checkout)
    _write(db_path, lambda conn: _review(conn, planning, "f7", _REVIEW_REPLAN))
    html = _review_page(serve(), "/planning/f7/proposals/replan")
    assert _changes(html) == [
        ("tasks/ready/f7-01-a.md", "changed", "the replan's a"),
        ("tasks/ready/f7-02-b.md", "set aside", "<b>'s text"),
        ("tasks/ready/f7-03-c.md", "added", "the replan's c"),
    ]
    assert "main's a" not in html and "<b>'s text" not in html  # escaped
    colours = re.findall(r'class="word" style="[^"]*color: var\((--[\w-]+)\)', html)
    assert colours == ["--a7", "--muted", "--good"]  # changed, set aside, added (F31 D8)
    assert "<details" in html.split('id="plan-changes"', 1)[1]
    steps = _text(html.split("What happens next", 1)[1].split("</ol>", 1)[0])
    assert "applies the ticket changes at once, even while paused, and resumes the line" in steps


def test_a_plan_without_its_branch_or_on_the_general_thread_shows_no_changes(
    planning, db_path, serve, checkout
):
    _replanned(checkout)
    plan = {**_REVIEW_PLAN, "id": "plan"}
    _write(db_path, lambda conn: _review(conn, planning, "f8", plan))
    _write(db_path, lambda conn: _review(conn, planning, "general", plan))
    client = serve()
    for thread in ("f8", "general"):
        html = _review_page(client, f"/planning/{thread}/proposals/plan")
        assert 'id="plan-changes"' not in html, thread
        assert "resumes the line" not in html, thread


def test_a_plan_with_its_branch_shows_its_changes_too(planning, db_path, serve, checkout):
    _replanned(checkout)
    _write(db_path, lambda conn: _review(conn, planning, "f7", _REVIEW_PLAN))
    html = _review_page(serve(), "/planning/f7/proposals/plan")
    assert [path for path, _, _ in _changes(html)] == [
        "tasks/ready/f7-01-a.md",
        "tasks/ready/f7-02-b.md",
        "tasks/ready/f7-03-c.md",
    ]
    assert "resumes the line" not in html


# --- on a phone (f6-10) -------------------------------------------------------------------------


def _shown(page, points: str) -> list[str | None]:
    """The numbers of the points the browser draws."""
    return [p.get_attribute("data-point") for p in page.locator(points).all() if p.is_visible()]


@pytest.mark.parametrize(
    ("path", "points", "comment", "send"),
    [
        ("/planning/f6", "li.point", "summary", "#reply button[type=submit]"),
        ("/planning/f6/proposals/adr-20", ".key-point", ".change-btn", "#send-back"),
    ],
    ids=["thread", "review"],
)
def test_on_a_phone_one_point_shows_at_a_time(
    page, planning, db_path, serve, path, points, comment, send
):
    """At 390 px one point, ◀ ▶ step through them, a commented point's dot is marked, Send
    stays in view at the bottom, every control is 44 px tall and nothing runs off the
    screen; on a display, every point and no ◀ ▶."""
    if points == "li.point":
        _write(db_path, lambda conn: _seven_points(conn, planning))
    else:
        _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_ADR))
    page.set_viewport_size(PHONE)
    _open(page, serve(), path)
    previous, following = page.locator(".deck-arrows button").all()
    assert _shown(page, points) == ["1"]
    following.click()
    assert _shown(page, points) == ["2"]
    page.locator(f"{points}:visible {comment}").click()
    page.locator(f"{points}:visible textarea.comment").fill("Say how it stops.")
    dots = page.locator(".deck-dots span")
    assert ["commented" in (d.get_attribute("class") or "") for d in dots.all()[:3]] == [
        False,
        True,
        False,
    ]
    previous.click()
    assert _shown(page, points) == ["1"]
    page.evaluate("() => window.scrollTo(0, 0)")
    box = page.locator(send).bounding_box()
    assert box and PHONE["height"] - 120 < box["y"] + box["height"] <= PHONE["height"]
    for control in page.locator(f"{points}:visible button, {points}:visible summary").all():
        assert (control.bounding_box() or {"height": 0})["height"] >= 44
    for control in (previous, following, page.locator(send)):
        assert (control.bounding_box() or {"height": 0})["height"] >= 44
    page.evaluate("() => document.querySelector('nav.tabs').setAttribute('data-layout', 'overlay')")
    assert page.evaluate("() => document.documentElement.scrollWidth") <= PHONE["width"]
    # the dock floats over the points by design: check the page with it back in the flow
    page.evaluate("() => document.querySelector('.dock').style.position = 'static'")
    assert layout_problems(page) == []
    page.set_viewport_size(DISPLAY)
    assert len(_shown(page, points)) == (7 if points == "li.point" else 3)
    assert not previous.is_visible()


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
    assert "after f1-04-live, any minute now" in _coming_text(html)


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


def test_a_threads_button_archives_it_and_an_archived_ones_opens_it_again(planning, db_path, serve):
    """The archive row sits after the reply box, not in the card header."""
    client = serve()
    html = _thread(client, "general")
    assert html.index('id="reply"') < html.index('id="archive-button"')
    header = html.split('<header id="card"', 1)[1].split("</header>", 1)[0]
    assert 'id="archive-button"' not in header
    assert 'id="remove-seed"' not in header
    assert _posts(html, "archive-button") == {
        "kind": "archive",
        "project": PROJECT,
        "subject": "general",
        "value": "on",
    }
    assert ">Archive</button>" in html
    _archive(db_path, planning, "general", timedelta(hours=1))
    html = _thread(client, "general")
    assert _posts(html, "archive-button")["value"] == "off"
    assert ">Unarchive</button>" in html
    assert "Or just reply: a message opens it again." in _text(html)


def test_an_archive_on_its_way_shows_at_once_and_its_button_goes(planning, db_path, serve):
    """What the owner asked shows on its way until the runner's next pick (owner.md)."""
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn, planning, "archive", "general", "on", NOW.isoformat()
        ),
    )
    html = _thread(serve(), "general")
    assert "Archiving at the runner's next pick" in _text(html)
    assert 'id="archive-button"' not in html


def test_the_archive_row_still_shows_when_a_reply_waits(planning, db_path, serve):
    """While a reply waits (``id="waiting"`` instead of the form), the Archive row
    still shows after it."""
    _write(db_path, lambda conn: _seven_points(conn, planning))
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn,
            planning,
            "plan_message",
            "general",
            json.dumps({"text": "Waiting.", "comments": {}}),
            _at(timedelta(minutes=5)),
        ),
    )
    html = _thread(serve(), "general")
    assert '<p id="waiting"' in html
    assert 'id="reply"' not in html
    assert 'id="archive-button"' in html
    assert html.index('id="waiting"') < html.index('id="archive"')


def test_a_card_with_no_thread_has_no_archive_button(planning, serve):
    """F9 is an idea card nobody has talked about yet: nothing to archive."""
    assert 'id="archive-button"' not in _thread(serve(), "f9")


def test_archive_posts_once_and_the_button_goes(page, planning, db_path, serve):
    _open(page, serve(), "/planning/general")
    page.click("#archive-button")
    page.wait_for_selector("#archive-status >> text=Asked")
    assert page.locator("#archive-button").count() == 0
    conn = metrics.open_db(db_path)
    try:
        rows = conn.execute("SELECT * FROM owner_requests WHERE project_id = ?", (planning,))
        asked = [(r["kind"], r["subject"], r["value"]) for r in rows]
    finally:
        conn.close()
    assert asked == [("archive", "general", "on")]


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
    project's: the box stays empty."""
    found: list[int] = [planning]
    if project_of == "elsewhere":
        _write(db_path, lambda conn: found.append(metrics.upsert_project(conn, "elsewhere")))
    asked = _finished(db_path, found[-1], "plan_message", "f6", '{"text": "Hi."}', result)
    thread = serve().get(f"/planning/f6?again={asked}").text
    box = re.search(r'<textarea name="text"[^>]*>(.*?)</textarea>', thread, re.S)
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
        ("plant", None, DUCKS, "planted docs/milestones/f12-rubber-ducks.md, queued for the lead"),
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


# --- a finished card shows its review, and Sign off (F50) ------------------------------------


def _review_section(html: str) -> str:
    found = re.search(r'<section id="review".*?</section>', html, re.S)
    assert found, "no #review"
    return found[0]


def test_a_ripe_cards_page_shows_its_sheet_and_signs_off(planning, db_path, db, serve):
    """F50 D2, D3: m4's review is written and every ticket done: its page opens on What
    changed, links the whole review, and Sign off posts a signoff with its full key."""
    html = _thread(serve(), "m4")
    review = _review_section(html)
    assert _text(review).startswith("The review What changed The web app.")
    assert "Decisions waiting for you" not in review  # no decisions in its sheet
    assert '<a href="/milestones/m4?project=' in review
    assert _posts(review, "signoff-button") == {
        "kind": "signoff",
        "project": PROJECT,
        "subject": "m4",
    }
    assert html.index('id="review"') < html.index('id="conversation"')
    [item] = desk(db, PROJECT, NOW)[3].items
    assert item.words == "reviewed · waits for your sign-off"


def test_a_sign_off_on_its_way_shows_and_the_button_goes(planning, db_path, serve):
    _write(
        db_path,
        lambda conn: metrics.add_request(conn, planning, "signoff", "m4", None, NOW.isoformat()),
    )
    review = _review_section(_thread(serve(), "m4"))
    assert "Signing off at the runner's next pick" in _text(review)
    assert 'id="signoff-button"' not in review


def test_a_card_with_tickets_left_shows_its_sheet_but_no_sign_off(planning, db_path, serve):
    """f1's sheet is stored but it has a ticket left: nothing to sign off yet."""
    review = _review_section(_thread(serve(), "f1"))
    assert "The factory measures itself." in _text(review)
    assert 'id="signoff-button"' not in review


def test_a_card_with_no_review_has_no_review_section(planning, serve):
    assert 'id="review"' not in _thread(serve(), "f6")


def test_a_refused_sign_off_keeps_its_word_under_the_button(planning, db_path, serve):
    """F50 D3: the runner refused (a dirty main): after a reload the button is back, and the
    runner's word stays under it."""
    _finished(db_path, planning, "signoff", "m4", None, "main has uncommitted changes")
    review = _review_section(_thread(serve(), "m4"))
    assert 'id="signoff-button"' in review
    assert "The runner said: main has uncommitted changes" in _text(review)


def test_sign_off_shows_on_its_way_at_once(page, planning, db_path, serve):
    """The owner (2026-10-07): the press shows the dashed "Signing off" at once, as a reload
    would, and the button goes."""
    _open(page, serve(), "/planning/m4")
    page.click("#signoff-button")
    page.wait_for_selector("#signoff-status >> text=Asked")
    assert page.locator("#signing-off").is_visible()
    assert page.locator("#signoff-button").count() == 0
    conn = metrics.open_db(db_path)
    try:
        rows = conn.execute("SELECT * FROM owner_requests WHERE project_id = ?", (planning,))
        asked = [(r["kind"], r["subject"]) for r in rows]
    finally:
        conn.close()
    assert asked == [("signoff", "m4")]


# --- a proposal says where it stands (F31 D3, f31-02) ----------------------------------------


def test_pressing_approve_shows_it_on_its_way_at_once_and_after_a_reload(
    page, planning, db_path, serve
):
    """The owner (F47): after Approve plan and a refresh, the button was back and could be
    pressed again. Now the dock turns into the dashed "on its way" box at once, and a reload
    shows the same box with no button and no Comment…."""
    _write(db_path, lambda conn: _review(conn, planning, "f9", _REVIEW_MERGE))
    client = serve()
    _open(page, client, "/planning/f9/proposals/merge-f9")
    assert page.locator("#approve-merge").is_visible()
    assert page.locator("#reject summary").is_visible()
    page.click("#approve-merge")
    page.wait_for_selector("#review-status >> text=Asked")
    assert page.locator("#actions.on-its-way .way-title").is_visible()
    assert not page.locator("#approve-merge").is_visible()
    page.reload()
    assert page.locator("#actions.on-its-way .way-title").is_visible()
    assert "Asked" in page.locator("#review-status").inner_text()
    assert page.locator("#approve-merge").count() == 0
    assert page.locator(".change-btn").count() == 0


@pytest.mark.parametrize(
    ("result", "words", "buttons"),
    [
        (
            "approved: merged F9 into F7",
            ["Approved", "The runner said: approved: merged F9 into F7"],
            False,
        ),
        ("rejected merge-f9", ["Rejected", "The runner said: rejected merge-f9"], False),
        (
            "F9 has no card in docs/milestones/: not merged",
            ["The runner said: F9 has no card"],
            True,
        ),
    ],
)
def test_a_settled_proposal_shows_its_word_and_the_runners_result(
    planning, db_path, serve, result, words, buttons
):
    """Approved or rejected: the word and the result, no button. A refused approval: its
    reason, and the buttons again."""
    _write(db_path, lambda conn: _review(conn, planning, "f9", _REVIEW_MERGE))
    kind = "reject" if result.startswith("rejected") else "approve_plan"
    subject = "f9/merge-f9" if kind == "reject" else "f9"
    _finished(db_path, planning, kind, subject, None, result)
    dock = _text(
        _review_page(serve(), "/planning/f9/proposals/merge-f9")
        .split('id="actions"', 1)[1]
        .split("</section>", 1)[0]
    )
    for word in words:
        assert word in dock
    html = _review_page(serve(), "/planning/f9/proposals/merge-f9")
    assert ('id="approve-merge"' in html) is buttons
    assert ('class="change-btn"' in html) is buttons


def test_a_sent_back_proposal_says_so_with_no_buttons(planning, db_path, serve):
    """f31-02's Done when: sent back shows its word, with no button, no Reject and no
    Comment…, on its page and on the thread's card."""
    _write(db_path, lambda conn: _review(conn, planning, "f9", _REVIEW_MERGE))
    said = json.dumps({"text": "", "comments": {"1": "Keep both."}})
    _finished(db_path, planning, "send_back", "f9/merge-f9", said, "queued for the lead")
    html = _review_page(serve(), "/planning/f9/proposals/merge-f9")
    dock = _text(html.split('id="actions"', 1)[1].split("</section>", 1)[0])
    assert "Sent back" in dock
    for gone in ('id="approve-merge"', 'id="send-back"', 'id="reject"', 'class="change-btn"'):
        assert gone not in html
    thread = _thread(serve(), "f9")
    assert re.findall(r'<span class="state">([^<]*)</span>', thread) == ["sent back"]


def test_a_proposal_from_an_older_reply_is_replaced(planning, db_path, serve):
    _write(db_path, lambda conn: _review(conn, planning, "f9", _REVIEW_MERGE))
    newer = {**_REVIEW_MERGE, "id": "merge-f9-again"}
    _write(db_path, lambda conn: _review(conn, planning, "f9", newer))
    html = _review_page(serve(), "/planning/f9/proposals/merge-f9")
    assert "Replaced by a newer reply" in _text(html)
    assert 'id="approve-merge"' not in html


def test_the_threads_cards_say_the_same_word(planning, db_path, serve):
    _write(db_path, lambda conn: _review(conn, planning, "f9", _REVIEW_MERGE))
    _finished(db_path, planning, "reject", "f9/merge-f9", None, "rejected merge-f9")
    html = _thread(serve(), "f9")
    assert re.findall(r'<span class="state">([^<]*)</span>', html) == ["rejected"]


def test_a_plans_ticket_rows_say_who_builds_them_and_colour_the_word(
    planning, db_path, serve, checkout
):
    """F31 D8: each ticket's builder (lead, or developer when its frontmatter names none) and
    difficulty beside its word, the word in its colour; another file shows neither."""
    git(checkout, "checkout", "-q", "-b", "plan/f7")
    for rel, text in (
        ("tasks/later/f7-01-a.md", "---\nid: f7-01-a\nagent: lead\ndifficulty: 6\n---\nx\n"),
        ("tasks/later/f7-02-b.md", "---\nid: f7-02-b\ndifficulty: 2\n---\nx\n"),
        ("docs/milestones/f7-x.md", "# Milestone F7: x\n"),
    ):
        (checkout / rel).parent.mkdir(parents=True, exist_ok=True)
        (checkout / rel).write_text(text)
    git(checkout, "add", "-A")
    git(checkout, "commit", "-q", "-m", "plan")
    git(checkout, "checkout", "-q", "main")
    _write(db_path, lambda conn: _review(conn, planning, "f7", _REVIEW_PLAN))
    html = _review_page(serve(), "/planning/f7/proposals/plan")
    section = html.split('id="plan-changes"', 1)[1].split("</section>", 1)[0]
    rows = re.findall(r'<li class="plan-change"[^>]*>(.*?)</li>', section, re.S)
    found = {
        re.search(r'<code class="path"[^>]*>([^<]*)</code>', r)[1]: (  # type: ignore[index]
            re.search(r'class="word" style="[^"]*color: var\((--[\w-]+)\)', r)[1],  # type: ignore[index]
            _text(m[1]) if (m := re.search(r'<span class="who"[^>]*>(.*?)</span>', r)) else "",
        )
        for r in rows
    }
    assert found == {
        "docs/milestones/f7-x.md": ("--good", ""),
        "tasks/later/f7-01-a.md": ("--good", "lead · difficulty 6"),
        "tasks/later/f7-02-b.md": ("--good", "developer · difficulty 2"),
    }


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
    [item] = [i for i in desk(db, PROJECT, NOW)[1].items if i.link == "/planning/general"]
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
    [item] = [i for i in desk(db, PROJECT, NOW)[3].items if i.link == "/planning/m4"]
    assert item.on_its_way and item.words == "signing off at the runner's next pick"


def _trail(html: str) -> dict[str, str]:
    nav = re.search(r'<nav id="desk-trail".*?</nav>', html, re.S)
    assert nav, "no #desk-trail"
    found = dict(re.findall(r'<a id="desk-(previous|next)" href="([^"?]+)', nav[0]))
    found["words"] = _text(nav[0])
    return found


def test_previous_and_next_step_through_what_waits(planning, db_path, serve):
    """F35: from the general thread, Next is F6's ADR; from there Previous is back and Next is
    F6's plan; a page already done with leads to the first one left."""
    client = serve()
    first = _trail(_thread(client, "general"))
    assert first["next"] == "/planning/f6/proposals/adr-20" and "previous" not in first
    assert "1 of " in first["words"] and "waiting for you" in first["words"]
    middle = _trail(_review_page(client, "/planning/f6/proposals/adr-20"))
    assert middle["previous"] == "/planning/general"
    assert middle["next"] == "/planning/f6/proposals/plan"
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn, planning, "archive", "general", "on", NOW.isoformat()
        ),
    )
    done = _trail(_thread(client, "general"))  # archived: no longer waiting
    assert done["next"] == "/planning/f6/proposals/adr-20" and "previous" not in done
