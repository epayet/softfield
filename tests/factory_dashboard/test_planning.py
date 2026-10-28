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
    write_planning,
)
from tests.layout import DISPLAY, PHONE, layout_problems
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
    proposals = desk(db, PROJECT, NOW)[3].items
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
    assert len(desk(db, PROJECT, NOW)[3].items) == 2


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


def test_a_fixture_reply_with_7_points_shows_each_point(planning, db_path, serve):
    """The card's header, the messages in order, then each point's title, answer and action
    within that point, each with its Comment… box, and the progress line."""
    _write(db_path, lambda conn: _seven_points(conn, planning))
    html = _thread(serve(), "f6")
    assert "The planning room" in _text(html.split('<header id="card"', 1)[1].split("</header>")[0])
    text = _text(html)
    assert (
        text.index("Here's each point")
        < text.index("Earlier in this thread (3)")
        < text.index("Looks good.")
        < text.index("A first go.")
    )
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
    folded = html.split('class="full-reply"', 1)[1].split("</article>", 1)[0]
    assert 'class="deck"' in folded  # its points follow the fold, in the same message
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
    # waiting message: #waiting present, the sent message at the top (F30), showing "Sent"
    assert page.locator("#waiting").is_visible()
    msg = page.locator("#conversation .message").first
    assert msg.is_visible()
    assert "And the phone?" in msg.inner_text() and "Sent" in msg.inner_text()
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
    # F84: behind general's, older, while a ticket job runs
    assert "Next for the lead · 2nd in line" in _text(html)
    assert '<form id="reply"' not in html
    assert "Send" not in _text(html)
    assert "Comment…" not in html


def test_the_latest_exchange_comes_first_and_the_older_messages_fold_newest_first(
    planning, db_path, serve
):
    """F30 D1: the lead's latest message, then Send, then a closed Earlier holding every older
    message, newest first."""
    _write(db_path, lambda conn: _seven_points(conn, planning))

    def replied(conn: sqlite3.Connection) -> None:
        f6 = metrics.planner_thread(conn, planning, "f6", NOW.isoformat())["id"]
        metrics.add_planner_message(conn, f6, "owner", _at(timedelta(minutes=4)), "And the phone?")
        metrics.add_planner_message(conn, f6, "lead", _at(timedelta(minutes=1)), "It passes.")

    _write(db_path, replied)
    html = _thread(serve(), "f6")
    conversation = html.split('<div id="conversation">', 1)[1]
    assert (
        conversation.index("It passes.")
        < conversation.index('<form id="reply"')
        < conversation.index('<details id="earlier">')
    )
    # Earlier closes #conversation; the page's script comes next
    earlier = html.split('<details id="earlier">', 1)[1].split("<script>", 1)[0]
    said = _text(earlier)
    assert said.startswith("Earlier in this thread (5) ")
    order = [
        "And the phone?",
        "Here's each point",
        "Looks good.",
        "Here's the plan.",
        "A first go.",
    ]
    assert [said.index(words) for words in order] == sorted(said.index(w) for w in order)
    assert "It passes." not in said
    assert html.count("It passes.") == 1 and html.count("And the phone?") == 1
    # the points folded away are commented on no more: no Comment…, no "7 points" by Send
    assert "Comment…" not in html and 'id="progress"' not in html


def test_waiting_messages_show_above_the_leads_latest_newest_first(planning, db_path, serve):
    """F30 D1: what waits for the lead comes first: the wait, then the owner's messages, newest
    first and dashed, then the lead's latest message; no Send."""
    _write(db_path, lambda conn: _seven_points(conn, planning))
    for minutes, words in ((6, "And the phone?"), (5, "And the tablet?")):
        value = json.dumps({"text": words, "comments": {}})
        _write(
            db_path,
            lambda conn, value=value, minutes=minutes: metrics.add_request(
                conn, planning, "plan_message", "f6", value, _at(timedelta(minutes=minutes))
            ),
        )
    html = _thread(serve(), "f6")
    conversation = html.split('<div id="conversation">', 1)[1]
    assert (
        conversation.index('<p id="waiting"')
        < conversation.index("And the tablet?")
        < conversation.index("And the phone?")
        < conversation.index("each point with my answer")
        < conversation.index('<details id="earlier">')
    )
    tablet, phone, _ = _said(html)
    assert "border-style: dashed" in tablet and "border-style: dashed" in phone
    assert 'id="reply"' not in html


def test_a_thread_with_one_message_has_no_earlier(planning, db_path, serve):
    """F30 D1: a lone lead message, or the owner's first message still waiting, shows open,
    with nothing folded."""

    def lead_only(conn: sqlite3.Connection) -> None:
        f7 = metrics.planner_thread(conn, planning, "f7", NOW.isoformat())["id"]
        metrics.add_planner_message(conn, f7, "lead", _at(timedelta(minutes=5)), "Hello there.")

    _write(db_path, lead_only)
    client = serve()
    html = _thread(client, "f7")
    assert "Hello there." in _text(html.split('<div id="conversation">', 1)[1])
    assert 'id="earlier"' not in html and "Earlier in this thread" not in html
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn, planning, "plan_message", "general", MESSAGE, _at(timedelta(minutes=5))
        ),
    )
    _write(db_path, lambda conn: conn.execute("DELETE FROM planner_messages"))
    html = _thread(client, "general")
    [waiting] = _said(html)
    assert "Make it calm." in waiting and "border-style: dashed" in waiting
    assert 'id="earlier"' not in html and '<p id="waiting"' in html


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


def test_clicking_comment_on_a_point_opens_its_box_and_focuses_the_textarea(
    page, planning, db_path, serve
):
    """f23-01: tapping a point's "Comment…" opens its box and the focused element is that
    point's textarea.comment; tapping it again closes the box and keeps the typed text."""
    _write(db_path, lambda conn: _seven_points(conn, planning))
    _open(page, serve(), "/planning/f6")
    # Click on the first point's "Comment…" summary
    page.click('li[data-point="1"] summary')
    # The details element is now open
    details = page.locator('li[data-point="1"] details[open]')
    assert details.is_visible()
    # The focused element is this point's textarea.comment, not another point's
    assert page.evaluate(
        "() => document.activeElement.matches('li[data-point=\"1\"] textarea.comment')"
    )
    # Type some text
    page.fill('li[data-point="1"] textarea.comment', "First comment")
    # Click again to close
    page.click('li[data-point="1"] summary')
    # The details element is now closed
    assert page.locator('li[data-point="1"] details:not([open])').is_visible()
    # The text is preserved
    assert page.locator('li[data-point="1"] textarea.comment').input_value() == "First comment"


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
_REVIEW_MOCKUP: dict[str, Any] = {
    "id": "mockup",
    "kind": "mockup",
    "title": "The desk, drawn",
    "path": ".factory/cards/f6-mockup/index.html",
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
    adr = checkout / ".factory" / "adr" / "20-planning-room.md"
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
    "path": ".factory/cards/f9-parallel.md",
    "into": "f7",
    "key_points": [{"n": 1, "title": "Notes", "text": "F9's notes go to F7.", "flag": False}],
}


def test_a_merge_shows_like_the_others_and_its_button_approves_the_threads_plan(
    planning, db_path, db, serve
):
    """f6-12: on the desk and its page, its words say "merge F9 into F7"; approving it is the
    thread's ``approve_plan``, which settles it (D6)."""
    _write(db_path, lambda conn: _review(conn, planning, "f9", _REVIEW_MERGE))
    [item] = [i for i in desk(db, PROJECT, NOW)[3].items if i.link.endswith("/merge-f9")]
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
    [item] = [i for i in desk(db, PROJECT, NOW)[3].items if i.link.endswith("/merge-f9")]
    assert item.on_its_way  # on its way until the runner's next pick, no longer waiting on you


def _merges_on_the_desk(db: sqlite3.Connection) -> list[str]:
    return [
        i.link for i in desk(db, PROJECT, NOW)[3].items if "/merge-" in i.link and not i.on_its_way
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
    docs = checkout / ".factory" / "cards"
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
    assert not [i for i in desk(db, PROJECT, NOW)[3].items if i.link.endswith("/merge-f9")]
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
        (".factory/cards/f6-mockup/index.html", "<p>the desk</p>"),
        (".factory/cards/f6-planning-room.md", "# F6"),
        (".factory/adr/20-planning-room.md", ADR_ON_MAIN.format(status="Proposed")),
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
    assert frame and frame[1] == "/planning/mockups/f6/.factory/cards/f6-mockup/index.html"
    served = client.get(frame[1])
    assert (served.status_code, served.text) == (200, "<p>the desk</p>")
    # Opened on its own, outside the sandboxed frame, it still runs in an origin of its own,
    # so its scripts can't post to /requests as the dashboard (ADR 18 item 3)
    assert served.headers["content-security-policy"] == "sandbox allow-scripts"
    for refused in (
        ".factory/cards/f6-planning-room.md",
        ".factory/adr/20-planning-room.md",
        ".factory/cards/f6-mockup/missing.html",
        ".factory/cards/f6-mockup/",
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
    mockup = checkout / ".factory" / "cards" / "f6-mockup" / "index.html"
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


def test_a_mockup_gone_shows_its_message_and_no_frame(planning, db_path, serve, checkout):
    """A mock-up whose old path ``docs/milestones/f54-mockup/moves.html`` can't be read
    from either path: the page shows the gone message with the stored path and no iframe."""
    git(checkout, "checkout", "-q", "-b", "plan/f54")
    (checkout / ".factory/cards/f54-mockup").mkdir(parents=True, exist_ok=True)
    # the mock-up file was never kept: only a placeholder so the branch exists
    (checkout / ".factory/cards/f54-mockup/.gitkeep").write_text("")
    git(checkout, "add", "-A")
    git(checkout, "commit", "-q", "-m", "drafts")
    git(checkout, "checkout", "-q", "main")
    _gone_mockup = {
        "id": "mockup",
        "kind": "mockup",
        "title": "F54 mock-up",
        "path": "docs/milestones/f54-mockup/moves.html",
        "key_points": [],
    }
    _write(db_path, lambda conn: _review(conn, planning, "f54", _gone_mockup))
    client = serve()
    html = _review_page(client, "/planning/f54/proposals/mockup")
    assert 'id="mockup"' not in html
    gone = re.search(r'<div class="gone">(.*?)</div>', html, re.S)
    assert gone is not None
    assert "isn't in the repo any more" in gone[1]
    assert "docs/milestones/f54-mockup/moves.html" in gone[1]


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
    a, b = ".factory/tasks/ready/f7-01-a.md", ".factory/tasks/ready/f7-02-b.md"
    for rel, text in ((a, "main's a"), (b, "<b>'s text")):
        (checkout / rel).parent.mkdir(parents=True, exist_ok=True)
        (checkout / rel).write_text(text)
    git(checkout, "add", "-A")
    git(checkout, "commit", "-q", "-m", "tickets")
    git(checkout, "checkout", "-q", "-b", "plan/f7")
    (checkout / a).write_text("the replan's a")
    (checkout / ".factory/tasks/ready/f7-03-c.md").write_text("the replan's c")
    (checkout / ".factory/tasks/later").mkdir()
    git(checkout, "mv", b, ".factory/tasks/later/f7-02-b.md")
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
        (".factory/tasks/ready/f7-01-a.md", "changed", "the replan's a"),
        (".factory/tasks/ready/f7-02-b.md", "set aside", "<b>'s text"),
        (".factory/tasks/ready/f7-03-c.md", "added", "the replan's c"),
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
        ".factory/tasks/ready/f7-01-a.md",
        ".factory/tasks/ready/f7-02-b.md",
        ".factory/tasks/ready/f7-03-c.md",
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
    assert html.index('id="reply"') < html.index("Archiving at the runner")  # F22: at the bottom
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


def test_on_a_phone_archive_shows_under_send_at_the_end_of_the_page(page, planning, db_path, serve):
    """F22 D1: Send sticks at the bottom while the thread is read, the Archive row out of
    view; scrolled to the end, the row shows under Send, not behind it."""
    _write(db_path, lambda conn: _seven_points(conn, planning))
    short = {"width": PHONE["width"], "height": 500}
    page.set_viewport_size(short)
    _open(page, serve(), "/planning/f6")
    send, archive = page.locator("#reply"), page.locator("#archive-button")
    box, button = send.bounding_box(), archive.bounding_box()
    assert box and button
    assert box["y"] + box["height"] <= short["height"] + 1 <= button["y"] + 1
    page.evaluate("() => window.scrollTo(0, document.documentElement.scrollHeight)")
    box, button = send.bounding_box(), archive.bounding_box()
    assert box and button
    assert box["y"] + box["height"] <= button["y"] + 1
    assert button["y"] + button["height"] <= short["height"] + 1


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
    [item] = desk(db, PROJECT, NOW)[4].items
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
            "F9 has no card in .factory/cards/: not merged",
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


def test_a_lead_message_with_empty_proposals_keeps_earlier_on_thread_and_review(
    planning, db_path, serve
):
    """A lead message whose proposals are ``'[]'`` leaves the thread's earlier proposals
    open, with their buttons on the thread and on each proposal's review page."""
    _write(db_path, lambda conn: _review(conn, planning, "f9", _REVIEW_MERGE))
    # A later lead reply with no proposals (stored as '[]')
    conn = metrics.open_db(db_path)
    f9 = metrics.planner_thread(conn, planning, "f9", _at(timedelta(hours=5)))["id"]
    conn.close()
    _write(
        db_path,
        lambda conn: metrics.add_planner_message(
            conn, f9, "lead", _at(timedelta(minutes=15)), "No replan.", proposals=[]
        ),
    )
    # The thread should still show the earlier proposal with its approve button
    thread_html = _thread(serve(), "f9")
    text = _text(thread_html)
    assert "Parallel, said twice" in text
    # The link to the proposal's review page is on the thread
    assert 'href="/planning/f9/proposals/merge-f9?' in thread_html
    # The proposal card shows it is still open
    assert '<span class="state">open</span>' in thread_html
    # The review page should show the proposal as open, not "replaced"
    review_html = _review_page(serve(), "/planning/f9/proposals/merge-f9")
    assert "Replaced by a newer reply" not in _text(review_html)
    assert 'id="approve-merge"' in review_html


def test_a_later_lead_message_with_a_different_proposal_still_replaces(planning, db_path, serve):
    """A later lead message with a different proposal still replaces the earlier ones, as
    ``test_a_proposal_from_an_older_reply_is_replaced`` checks."""
    _write(db_path, lambda conn: _review(conn, planning, "f9", _REVIEW_MERGE))
    newer = {**_REVIEW_MERGE, "id": "new-proposal"}
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
        (
            ".factory/tasks/later/f7-01-a.md",
            "---\nid: f7-01-a\nagent: lead\ndifficulty: 6\n---\nx\n",
        ),
        (".factory/tasks/later/f7-02-b.md", "---\nid: f7-02-b\ndifficulty: 2\n---\nx\n"),
        (".factory/cards/f7-x.md", "# Milestone F7: x\n"),
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
        ".factory/cards/f7-x.md": ("--good", ""),
        ".factory/tasks/later/f7-01-a.md": ("--good", "lead · difficulty 6"),
        ".factory/tasks/later/f7-02-b.md": ("--good", "developer · difficulty 2"),
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


# --- a waiting message is edited or cancelled on its thread (f14-03) --------------------------

SENT = "Sent · the runner picks it up at its next pick"
CHANGED = "changed · the runner picks it up at its next pick"
CANCELLING = "cancelling at the runner's next pick"
COMMENTED = json.dumps({"text": "Make it calm.", "comments": {"2": 'Say "how".'}})


def _said(html: str) -> list[str]:
    """The owner's messages on a thread, each one's markup, in the page's order."""
    return [
        m[0]
        for m in re.finditer(r'<article class="message"[^>]*>.*?</article>', html, re.S)
        if "You · " in m[0]
    ]


def _lines(locator) -> list[str]:
    return [line.strip() for line in locator.inner_text().splitlines() if line.strip()]


def test_a_waiting_message_has_edit_and_cancel_it_and_a_stored_one_neither(
    planning, db_path, serve
):
    """The editor waits closed, holding the message's own text; the message the runner took
    ("Looks good.") is on the thread for good."""
    said = _finished(db_path, planning, "plan_message", "f6", MESSAGE, None)
    waiting, stored = _said(_thread(serve(), "f6"))
    assert "Looks good." in stored and "<button" not in stored and "<form" not in stored
    assert _text(waiting).endswith(
        f"Make it calm. {SENT} Your message Make it calm. Edit Save Cancel it"
    )
    assert re.search(
        rf'<form id="editor-{said}" hidden[^>]*>.*?<textarea name="text"[^>]*>Make it calm.</t',
        waiting,
        re.S,
    )
    assert re.search(
        rf'<button type="submit" form="editor-{said}" id="save-{said}" hidden', waiting
    )
    assert f'id="edit-{said}"' in waiting and f'id="cancel-{said}"' in waiting
    assert "on-its-way" not in waiting and "line-through" not in waiting


def test_an_edit_on_its_way_shows_the_new_message_and_no_buttons(planning, db_path, serve):
    """The edit's own words and comments show, its status polling; the other waiting message
    still has its buttons, and the thread still waits for the lead."""
    said = _finished(db_path, planning, "plan_message", "f6", COMMENTED, None)
    other = _finished(db_path, planning, "plan_message", "f6", MESSAGE, None)
    edit = json.dumps({"text": "Make it bright.", "comments": {"3": "Shorter."}})
    change = _finished(db_path, planning, "change", str(said), edit, None)
    html = _thread(serve(), "f6")
    untouched, changed, _ = _said(html)  # newest first (F30)
    assert "border-style: dashed" in changed and "line-through" not in changed
    assert _text(changed).endswith(f"Make it bright. {CHANGED} {ASKED} On 3: Shorter.")
    assert "Make it calm." not in changed and "On 2:" not in changed
    assert f'hx-get="/requests/{change}"' in changed
    assert "<button" not in changed and "<form" not in changed
    assert f'id="edit-{other}"' in untouched and "on-its-way" not in untouched
    assert '<p id="waiting"' in html and 'id="reply"' not in html


def test_an_edit_the_runner_will_refuse_keeps_the_messages_words(planning, db_path, serve):
    said = _finished(db_path, planning, "plan_message", "f6", COMMENTED, None)
    _finished(db_path, planning, "change", str(said), '{"comments": {"x": "?"}}', None)
    changed, _ = _said(_thread(serve(), "f6"))
    assert _text(changed).endswith(f'Make it calm. {CHANGED} {ASKED} On 2: Say "how".')
    assert "<button" not in changed


def test_a_cancel_on_its_way_strikes_the_message_and_the_send_form_comes_back(
    planning, db_path, serve
):
    """A cancelled message waits for no reply: Send is back, until another message waits."""
    said = _finished(db_path, planning, "plan_message", "f6", MESSAGE, None)
    cancel = _finished(db_path, planning, "change", str(said), '{"cancel": true}', None)
    client = serve()
    html = _thread(client, "f6")
    cancelled, _ = _said(html)
    assert re.search(r'<p style="[^"]*text-decoration: line-through">Make it calm.</p>', cancelled)
    assert _text(cancelled).endswith(f"Make it calm. {CANCELLING} {ASKED}")
    assert f'hx-get="/requests/{cancel}"' in cancelled
    assert "<button" not in cancelled and "<form" not in cancelled
    assert 'id="reply"' in html and '<p id="waiting"' not in html
    _finished(db_path, planning, "plan_message", "f6", MESSAGE, None)
    html = _thread(client, "f6")
    assert '<p id="waiting"' in html and 'id="reply"' not in html


def test_a_cancelled_message_no_longer_puts_its_thread_in_coming(planning, db_path, serve):
    """The desk says what the thread says: a message with a cancel on its way waits for no
    reply; an edited one still does, and so does a second message nobody cancelled."""
    said = _finished(db_path, planning, "plan_message", "general", MESSAGE, None)
    waiting = ("/planning/general", "General")
    client = serve()
    assert waiting in _coming_items(_page(client))
    edit = _finished(db_path, planning, "change", str(said), COMMENTED, None)
    assert waiting in _coming_items(_page(client))
    _write(db_path, lambda conn: metrics.finish_request(conn, edit, NOW.isoformat(), "changed"))
    _finished(db_path, planning, "change", str(said), '{"cancel": true}', None)
    assert 'id="desk-coming"' not in _page(client)  # nothing else was coming
    _finished(db_path, planning, "plan_message", "general", MESSAGE, None)
    assert waiting in _coming_items(_page(client))


def test_edit_then_save_posts_a_change_and_the_message_shows_it_at_once(
    page, planning, db_path, serve
):
    """On a phone: Edit opens the text in place with Save; Save posts one change naming the
    message, with the new text and its comments as they were; the message is drawn again
    with no reload, on its way and without its buttons."""
    said = _finished(db_path, planning, "plan_message", "f6", COMMENTED, None)
    page.set_viewport_size(PHONE)
    _open(page, serve(), "/planning/f6")
    assert not page.locator(f"#editor-{said}").is_visible()
    assert not page.locator(f"#save-{said}").is_visible()
    page.click(f"#edit-{said}")
    assert page.input_value(f'#editor-{said} textarea[name="text"]') == "Make it calm."
    assert page.locator(f"#edit-{said}").count() == 0
    for button in (f"#save-{said}", f"#cancel-{said}"):
        assert page.locator(button).is_visible()
        assert page.locator(button).evaluate("e => e.offsetHeight") >= 44
    page.fill(f'#editor-{said} textarea[name="text"]', "Make it bright.")
    page.click(f"#save-{said}")
    page.wait_for_selector("#conversation .on-its-way")
    assert page.url.endswith("/planning/f6")
    message = page.locator("#conversation .message").first
    assert _lines(message)[1:] == ["Make it bright.", CHANGED, ASKED, 'On 2: Say "how".']
    assert page.locator(f"#editor-{said}, #save-{said}, #cancel-{said}").count() == 0
    assert page.locator("#conversation").count() == 1
    assert page.locator("#waiting").is_visible() and page.locator("#reply").count() == 0
    words = {"text": "Make it bright.", "comments": {"2": 'Say "how".'}}
    assert _asked_changes(db_path) == [(str(said), words)]
    assert _values(db_path, "plan_message") == [json.loads(COMMENTED)]  # never edited


def test_cancel_it_strikes_the_message_at_once_and_the_send_form_comes_back(
    page, planning, db_path, serve
):
    said = _finished(db_path, planning, "plan_message", "f6", MESSAGE, None)
    _open(page, serve(), "/planning/f6")
    assert page.locator("#reply").count() == 0
    page.click(f"#cancel-{said}")
    page.wait_for_selector("#conversation .on-its-way")
    message = page.locator("#conversation .message").first
    assert _lines(message)[1:] == ["Make it calm.", CANCELLING, ASKED]
    struck = message.locator("p").first
    assert struck.inner_text() == "Make it calm."
    assert "line-through" in struck.evaluate("e => getComputedStyle(e).textDecorationLine")
    assert page.locator(f"#edit-{said}, #cancel-{said}").count() == 0
    assert page.locator("#reply").is_visible() and page.locator("#waiting").count() == 0
    assert _asked_changes(db_path) == [(str(said), {"cancel": True})]


def test_a_message_change_that_isnt_stored_leaves_the_editor_open(page, planning, db_path, serve):
    """The post is refused: nothing is drawn again, and the editor keeps what was typed."""
    said = _finished(db_path, planning, "plan_message", "f6", MESSAGE, None)
    _open(page, serve(), "/planning/f6")
    page.route("**/requests", lambda route: route.fulfill(status=400, body="Bad request"))
    page.click(f"#edit-{said}")
    page.fill(f'#editor-{said} textarea[name="text"]', "Geese")
    with page.expect_response("**/requests"):
        page.click(f"#save-{said}")
    page.wait_for_timeout(300)  # a re-fetch, if one wrongly followed, would have landed
    assert page.input_value(f'#editor-{said} textarea[name="text"]') == "Geese"
    assert page.locator("#conversation .on-its-way").count() == 0
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


def test_the_leads_answer_appears_on_an_open_thread(page, planning, db_path, serve):
    """With F6's thread open, the lead's new answer shows in the conversation within a poll,
    and its points come back as a deck (deck.js binds the drawn-again conversation)."""
    _write(db_path, lambda conn: _seven_points(conn, planning))
    _open(page, serve(), "/planning/f6")
    _lead_says(db_path, planning, "f6", "A second answer.")
    page.locator("#conversation >> text=A second answer.").wait_for(timeout=LIVE)
    assert page.locator("#conversation").count() == 1
    assert page.locator(".deck").count() == page.locator(".deck[data-up]").count() > 0


def test_an_open_thread_waits_while_the_owner_types(page, planning, db_path, serve):
    """Text in the reply box holds the conversation as it is (the text stays); emptied and
    left, the lead's answer arrives."""
    _write(db_path, lambda conn: _seven_points(conn, planning))
    _open(page, serve(), "/planning/f6")
    page.fill('#reply textarea[name="text"]', "Half a thought")
    _lead_says(db_path, planning, "f6", "A second answer.")
    page.wait_for_timeout(LIVE)
    assert page.locator("#conversation >> text=A second answer.").count() == 0
    assert page.input_value('#reply textarea[name="text"]') == "Half a thought"
    page.fill('#reply textarea[name="text"]', "")
    page.evaluate("() => document.activeElement.blur()")
    page.locator("#conversation >> text=A second answer.").wait_for(timeout=LIVE)


def test_a_comment_folded_away_still_holds_the_refresh(page, planning, db_path, serve):
    """A comment typed on a point, its box then closed, is still sent with the message: the
    page doesn't count as idle while it waits, though the box is hidden."""
    _write(db_path, lambda conn: _seven_points(conn, planning))
    _open(page, serve(), "/planning/f6")
    page.click('li[data-point="2"] summary')
    page.fill('li[data-point="2"] textarea', "Inside, but say how it stops.")
    page.click('li[data-point="2"] summary')
    page.evaluate("() => document.activeElement.blur()")
    assert not page.locator('li[data-point="2"] textarea').is_visible()
    assert page.evaluate("() => window.liveIdle()") is False


# --- merge links (f109-01)-------------------------------------------------------------------


def test_a_merge_whose_card_left_main_shows_both_ways(planning, db_path, serve, checkout):
    """F107 merged into F95: /planning/f107 shows 'Merged into F95, <F95's title>' linking
    to F95, and /planning/f95 shows 'Merged here: F107, <F107's title>' linking to F107. The
    merged card's h2 shows the heading's title, not its bare key."""
    from runner import planner

    docs = checkout / ".factory" / "cards"
    docs.mkdir(parents=True)

    # F95's doc holds F107's merge
    f95_doc = "# Milestone F95: Plans get merged\n\n## Notes\n"
    f95_doc = planner.merged_card(
        f95_doc, "notes", "From F107: When plans get merged (merged by the lead on 2026-10-13)"
    )
    (docs / "f95-plans-get-merged.md").write_text(f95_doc)

    # Seed milestones: only F95 (F107 has no row, and no doc: the merge removed it)
    _write(
        db_path,
        lambda conn: metrics.upsert_milestone(
            conn, planning, "f95-plans-get-merged", title="Plans get merged"
        ),
    )

    # Check /planning/f107
    client = serve()
    html = client.get("/planning/f107").text
    assert response_contains(html, "Merged into F95, Plans get merged")
    assert 'href="/planning/f95?' in html
    # h2 shows the heading's title
    h2 = re.search(r"<h2[^>]*>([^<]+)</h2>", html)
    assert h2 and "When plans get merged" in h2[1]

    # Check /planning/f95
    html = client.get("/planning/f95").text
    assert response_contains(html, "Merged here: F107, When plans get merged")
    assert 'href="/planning/f107?' in html


def test_a_merged_card_with_its_removed_row_says_merged_into(planning, db_path, serve, checkout):
    """A merge leaves the merged card's milestone row, marked removed (`remove_cards`): its
    page still says 'Merged into F95', not 'An earlier F107', and keeps the row's title."""
    from runner import planner

    docs = checkout / ".factory" / "cards"
    docs.mkdir(parents=True)
    f95_doc = planner.merged_card(
        "# Milestone F95: Plans get merged\n\n## Notes\n",
        "notes",
        "From F107: When plans get merged (merged by the lead on 2026-10-13)",
    )
    (docs / "f95-plans-get-merged.md").write_text(f95_doc)

    def seed(conn):
        metrics.upsert_milestone(conn, planning, "f95-plans-get-merged", title="Plans get merged")
        metrics.upsert_milestone(
            conn, planning, "f107-when-plans", title="When plans get merged", state="idea"
        )
        metrics.remove_cards(conn, planning, gone="f107")

    _write(db_path, seed)

    html = serve().get("/planning/f107").text
    assert response_contains(html, "Merged into F95, Plans get merged")
    assert not response_contains(html, "An earlier F107")
    h2 = re.search(r"<h2[^>]*>([^<]+)</h2>", html)
    assert h2 and "When plans get merged" in h2[1]


def response_contains(html: str, text: str) -> bool:
    """Check if text appears in HTML (unescaped)."""
    from html import unescape

    return text in unescape(re.sub(r"<[^>]+>", "", html))


def test_merge_links_function_returns_correct_links(checkout):
    """The _merge_links function returns correct merged_into and merged_here lists."""
    from factory_dashboard.planning import _merge_links
    from runner import planner

    docs = checkout / ".factory" / "cards"
    docs.mkdir(parents=True)

    f95_doc = "# Milestone F95: Plans\n\n## Notes\n"
    f95_doc = planner.merged_card(
        f95_doc, "n", "From F107: Title (merged by the lead on 2026-10-13)"
    )
    (docs / "f95-plans-get-merged.md").write_text(f95_doc)

    merged_into, _merged_here, latest_title = _merge_links(checkout, "f107")
    assert len(merged_into) == 1
    assert merged_into[0]["key"] == "f95"
    assert merged_into[0]["title"] == "Plans"  # the kept card's, not the merged one's
    assert latest_title == "Title"
    assert merged_into[0]["date"] == "2026-10-13"
    assert merged_into[0]["link"] == "/planning/f95"

    _, merged_here2, _ = _merge_links(checkout, "f95")
    assert len(merged_here2) == 1
    assert merged_here2[0]["key"] == "f107"
    assert merged_here2[0]["title"] == "Title"


def test_merged_on_shows_link_to_kept_card(planning, db_path, serve, checkout):
    """F107 merged into F95, no F107 doc on main: /planning/f107 has #merged-on
    with a link to /planning/f95 and F95's title, and no message form."""
    from runner import planner

    docs = checkout / ".factory" / "cards"
    docs.mkdir(parents=True)

    # F95's doc holds F107's merge
    f95_doc = "# Milestone F95: Plans get merged\n\n## Notes\n"
    f95_doc = planner.merged_card(
        f95_doc, "notes", "From F107: When plans get merged (merged by the lead on 2026-10-13)"
    )
    (docs / "f95-plans-get-merged.md").write_text(f95_doc)

    # No F107 doc on main: "no doc on main" means F107's key is not in _known_cards

    # Seed milestones: only F95 (F107 has no row)
    _write(
        db_path,
        lambda conn: metrics.upsert_milestone(
            conn, planning, "f95-plans-get-merged", title="Plans get merged"
        ),
    )

    client = serve()
    html = client.get("/planning/f107").text

    # Has #merged-on with link to F95, its text the card's key and title, not its path
    assert 'id="merged-on"' in html
    block = html.split('id="merged-on"', 1)[1]
    link = re.search(r'<a href="/planning/f95\?[^"]*"[^>]*>([^<]*)</a>', block)
    assert link and link[1].startswith("F95, Plans get merged")
    assert response_contains(html, "Merged into F95, Plans get merged: the conversation")
    assert ">/planning/" not in html

    # No message form (textarea for a message)
    assert 'id="reply"' not in html
    assert "<textarea" not in html


def test_merged_on_lists_open_proposals(planning, db_path, serve, checkout):
    """An open plan on F95's thread is listed in #merged-on by its title,
    linking to its review page; an applied or rejected one is not."""
    from runner import planner

    docs = checkout / ".factory" / "cards"
    docs.mkdir(parents=True)

    # F95's doc holds F107's merge
    f95_doc = "# Milestone F95: Plans get merged\n\n## Notes\n"
    f95_doc = planner.merged_card(
        f95_doc, "notes", "From F107: When plans get merged (merged by the lead on 2026-10-13)"
    )
    (docs / "f95-plans-get-merged.md").write_text(f95_doc)

    # No F107 doc on main
    # Seed milestones: only F95
    _write(
        db_path,
        lambda conn: metrics.upsert_milestone(
            conn, planning, "f95-plans-get-merged", title="Plans get merged"
        ),
    )

    # Create an open plan proposal on F95's thread (not a merge, to avoid _gone_merge filter)
    _open_plan = {
        "id": "plan-f95",
        "kind": "plan",
        "title": "Open plan for F95",
        "path": None,
        "key_points": [{"n": 1, "title": "Point", "text": "A point.", "flag": False}],
    }
    _write(db_path, lambda conn: _review(conn, planning, "f95", _open_plan))

    client = serve()
    html = client.get("/planning/f107").text

    # The open proposal's title appears in #merged-on
    assert "Open plan for F95" in html
    # Link to the proposal's review page
    assert 'href="/planning/f95/proposals/plan-f95' in html

    # Applied proposal should not appear
    _finished(db_path, planning, "approve_plan", "f95", None, "approved")
    html = client.get("/planning/f107").text
    assert "Open plan for F95" not in html


def test_merged_on_leaves_out_a_rejected_plan(planning, db_path, serve, checkout):
    """A plan the owner rejected on F95's thread is not listed on /planning/f107."""
    from runner import planner

    docs = checkout / ".factory" / "cards"
    docs.mkdir(parents=True)
    f95_doc = planner.merged_card(
        "# Milestone F95: Plans get merged\n\n## Notes\n",
        "notes",
        "From F107: When plans get merged (merged by the lead on 2026-10-13)",
    )
    (docs / "f95-plans-get-merged.md").write_text(f95_doc)
    _write(
        db_path,
        lambda conn: metrics.upsert_milestone(
            conn, planning, "f95-plans-get-merged", title="Plans get merged"
        ),
    )
    plan = {
        "id": "plan-f95",
        "kind": "plan",
        "title": "Rejected plan for F95",
        "path": None,
        "key_points": [{"n": 1, "title": "Point", "text": "A point.", "flag": False}],
    }
    _write(db_path, lambda conn: _review(conn, planning, "f95", plan))
    client = serve()
    assert "Rejected plan for F95" in client.get("/planning/f107").text

    _finished(db_path, planning, "reject", "f95/plan-f95", None, "rejected plan-f95")
    assert "Rejected plan for F95" not in client.get("/planning/f107").text


def test_merged_on_shows_ticket_count(planning, db_path, serve, checkout):
    """A kept card with one ready and one done ticket shows
    'Planned: 2 tickets, 1 done' linking to its card page;
    a kept card with no ticket shows no such link."""
    from runner import planner

    docs = checkout / ".factory" / "cards"
    docs.mkdir(parents=True)

    # F95's doc holds F107's merge
    f95_doc = "# Milestone F95: Plans get merged\n\n## Notes\n"
    f95_doc = planner.merged_card(
        f95_doc, "notes", "From F107: When plans get merged (merged by the lead on 2026-10-13)"
    )
    (docs / "f95-plans-get-merged.md").write_text(f95_doc)

    # Seed milestones: only F95
    _write(
        db_path,
        lambda conn: metrics.upsert_milestone(
            conn, planning, "f95-plans-get-merged", title="Plans get merged"
        ),
    )
    # Get the milestone id
    conn = metrics.open_db(db_path)
    f95_milestone = conn.execute(
        "SELECT id FROM milestones WHERE project_id = ? AND key = ?",
        (planning, "f95-plans-get-merged"),
    ).fetchone()["id"]
    conn.close()

    # Add tickets: one ready, one done
    _write(
        db_path,
        lambda conn: metrics.upsert_ticket(
            conn, planning, "F95-1", milestone_id=f95_milestone, state="ready"
        ),
    )
    _write(
        db_path,
        lambda conn: metrics.upsert_ticket(
            conn, planning, "F95-2", milestone_id=f95_milestone, state="done"
        ),
    )

    client = serve()
    html = client.get("/planning/f107").text

    assert "Planned: 2 tickets, 1 done" in html
    assert 'href="/milestones/f95-plans-get-merged' in html


def test_merged_on_counts_done_across_two_milestones(planning, db_path, serve, checkout):
    """A kept card with two milestones, three tickets done in the second and one ready
    in the first, shows 'Planned: 4 tickets, 3 done'."""
    from runner import planner

    docs = checkout / ".factory" / "cards"
    docs.mkdir(parents=True)

    # F95's doc holds F107's merge
    f95_doc = "# Milestone F95: Plans get merged\n\n## Notes\n"
    f95_doc = planner.merged_card(
        f95_doc, "notes", "From F107: When plans get merged (merged by the lead on 2026-10-13)"
    )
    (docs / "f95-plans-get-merged.md").write_text(f95_doc)

    # Seed milestones: F95 (first milestone)
    _write(
        db_path,
        lambda conn: metrics.upsert_milestone(
            conn, planning, "f95-plans-get-merged", title="Plans get merged"
        ),
    )
    # F95-continued (second milestone on same card, a replan)
    _write(
        db_path,
        lambda conn: metrics.upsert_milestone(
            conn, planning, "f95-continued", title="Plans continued"
        ),
    )
    conn = metrics.open_db(db_path)
    f95_m1 = conn.execute(
        "SELECT id FROM milestones WHERE project_id = ? AND key = ?",
        (planning, "f95-plans-get-merged"),
    ).fetchone()["id"]
    f95_m2 = conn.execute(
        "SELECT id FROM milestones WHERE project_id = ? AND key = ?",
        (planning, "f95-continued"),
    ).fetchone()["id"]
    conn.close()

    # First milestone: 1 ready ticket
    _write(
        db_path,
        lambda conn: metrics.upsert_ticket(
            conn, planning, "F95-1", milestone_id=f95_m1, state="ready"
        ),
    )
    # Second milestone: 3 done tickets
    for i in range(1, 4):
        _write(
            db_path,
            lambda conn, n=i: metrics.upsert_ticket(
                conn, planning, f"F95-02-{n}", milestone_id=f95_m2, state="done"
            ),
        )

    client = serve()
    html = client.get("/planning/f107").text

    assert "Planned: 4 tickets, 3 done" in html


def test_merged_on_two_kept_cards(planning, db_path, serve, checkout):
    """A key merged into two cards has two .merged-on-card parts, each with its
    own card's links, and keeps its message form."""
    from runner import planner

    docs = checkout / ".factory" / "cards"
    docs.mkdir(parents=True)

    # F95's doc holds F107's merge
    f95_doc = "# Milestone F95: Plans get merged\n\n## Notes\n"
    f95_doc = planner.merged_card(
        f95_doc, "notes", "From F107: When plans get merged (merged by the lead on 2026-10-13)"
    )
    (docs / "f95-plans-get-merged.md").write_text(f95_doc)

    # F13's doc also holds F107's merge (earlier date)
    f13_doc = "# Milestone f13-x: x\n\n## Notes\n"
    f13_doc = planner.merged_card(
        f13_doc, "notes", "From F107: When plans get merged (merged by the lead on 2026-10-10)"
    )
    (docs / "f13-x.md").write_text(f13_doc)

    # Seed milestones: only F95
    _write(
        db_path,
        lambda conn: metrics.upsert_milestone(
            conn, planning, "f95-plans-get-merged", title="Plans get merged"
        ),
    )

    client = serve()
    html = client.get("/planning/f107").text

    # Two .merged-on-card parts
    assert html.count("merged-on-card") == 2

    # Both links present with href
    assert 'href="/planning/f95?' in html
    assert 'href="/planning/f13?' in html

    # Message form stays
    assert 'id="reply"' in html


def test_merged_on_card_on_main_no_block(planning, db_path, serve, checkout):
    """A key that has a card on main again has no #merged-on and keeps its message form."""
    from runner import planner

    docs = checkout / ".factory" / "cards"
    docs.mkdir(parents=True)

    # F95's doc holds F107's merge
    f95_doc = "# Milestone F95: Plans get merged\n\n## Notes\n"
    f95_doc = planner.merged_card(
        f95_doc, "notes", "From F107: When plans get merged (merged by the lead on 2026-10-13)"
    )
    (docs / "f95-plans-get-merged.md").write_text(f95_doc)

    # F107's doc exists on main (key reused)
    (docs / "f107-when-plans-get-merged-i-need.md").write_text(
        "# Milestone f107-when-plans-get-merged-i-need: When plans get merged I need\n\n## Notes\n"
    )

    # Seed milestones: only F95
    _write(
        db_path,
        lambda conn: metrics.upsert_milestone(
            conn, planning, "f95-plans-get-merged", title="Plans get merged"
        ),
    )

    client = serve()
    html = client.get("/planning/f107").text

    # No #merged-on block
    assert 'id="merged-on"' not in html

    # Message form stays
    assert 'id="reply"' in html


def test_merged_on_never_merged_unchanged(planning, db_path, serve):
    """A card never merged, and the general thread, are unchanged."""
    client = serve()
    html = client.get("/planning/f1").text

    # No #merged-on block
    assert 'id="merged-on"' not in html

    # Message form stays
    assert 'id="reply"' in html


def test_no_merge_no_links(planning, serve):
    """A card with no merge, the general thread, and no checkout show no such links."""
    client = serve()

    # General thread
    html = client.get("/planning/general").text
    assert "merged-into" not in html
    assert "merged-here" not in html

    # A card with no merge docs
    html = client.get("/planning/f6").text
    assert "merged-into" not in html
    assert "merged-here" not in html


def test_two_merges_on_one_kept_card(planning, db_path, serve, checkout):
    """A kept card with two merges lists both."""
    from runner import planner

    docs = checkout / ".factory" / "cards"
    docs.mkdir(parents=True)

    f95_doc = "# Milestone F95: Plans get merged\n\n## Notes\n"
    f95_doc = planner.merged_card(
        f95_doc, "n1", "From F107: Title1 (merged by the lead on 2026-10-13)"
    )
    f95_doc = planner.merged_card(
        f95_doc, "n2", "From F16: Title2 (merged by the owner on 2026-10-14)"
    )
    (docs / "f95-plans-get-merged.md").write_text(f95_doc)

    _write(
        db_path,
        lambda conn: metrics.upsert_milestone(
            conn, planning, "f95-plans-get-merged", title="Plans"
        ),
    )

    client = serve()
    page_html = client.get("/planning/f95").text
    assert page_html.count('class="merged-here"') == 2
    assert response_contains(page_html, "Merged here: F107, Title1 · 2026-10-13")
    assert response_contains(page_html, "Merged here: F16, Title2 · 2026-10-14")


def test_key_merged_into_two_cards(planning, db_path, serve, checkout):
    """A key merged into two cards (F64 into F13 and F42) lists both on its thread."""
    from runner import planner

    docs = checkout / ".factory" / "cards"
    docs.mkdir(parents=True)

    f13_doc = "# Milestone F13: Line\n\n## Notes\n"
    f13_doc = planner.merged_card(
        f13_doc, "n", "From F64: F64 title (merged by the lead on 2026-10-01)"
    )
    (docs / "f13-factory-line.md").write_text(f13_doc)

    f42_doc = "# Milestone F42: Seeds\n\n## Notes\n"
    f42_doc = planner.merged_card(
        f42_doc, "n", "From F64: F64 title (merged by the lead on 2026-10-02)"
    )
    (docs / "f42-seeds.md").write_text(f42_doc)

    _write(
        db_path,
        lambda conn: metrics.upsert_milestone(conn, planning, "f64-parallel", title="Parallel"),
    )

    client = serve()
    html = client.get("/planning/f64").text
    # Both links present, each with its kept card's own title
    assert 'href="/planning/f13?' in html
    assert 'href="/planning/f42?' in html
    assert response_contains(html, "Merged into F13, Line")
    assert response_contains(html, "Merged into F42, Seeds")


def test_chain_f107_to_f10(planning, db_path, serve, checkout):
    """F107's notes moved from F95 into F10: links to F10 and back."""
    from runner import planner

    docs = checkout / ".factory" / "cards"
    docs.mkdir(parents=True)

    # F10's doc has both the original heading (from F95) and the chain heading (from F107)
    f10_doc = "# Milestone F10: Notes\n\n## Notes\n"
    # F95 was merged into F10
    f10_doc = planner.merged_card(
        f10_doc, "n", "From F95: F95 title (merged by the lead on 2026-10-05)"
    )
    # F107's heading moved down one level (### → ####)
    f10_doc += "#### From F107: F107 title (merged by the lead on 2026-10-06)\n"
    (docs / "f10-notes.md").write_text(f10_doc)

    _write(
        db_path, lambda conn: metrics.upsert_milestone(conn, planning, "f10-notes", title="Notes")
    )

    client = serve()

    # F107's thread links to F10
    html = client.get("/planning/f107").text
    assert 'href="/planning/f10?' in html
    assert response_contains(html, "Merged into F10, Notes")

    # F10's thread links to both F95 and F107
    html = client.get("/planning/f10").text
    assert 'href="/planning/f95?' in html
    assert 'href="/planning/f107?' in html
    assert response_contains(html, "Merged here: F95, F95 title")
    assert response_contains(html, "Merged here: F107, F107 title")


def test_key_reused_says_an_earlier(planning, db_path, serve, checkout):
    """A key that has a card again on main says 'An earlier F73 was merged into F43'."""
    from runner import planner

    docs = checkout / ".factory" / "cards"
    docs.mkdir(parents=True)

    f43_doc = "# Milestone f43-review: Review\n\n## Notes\n"
    f43_doc = planner.merged_card(
        f43_doc, "n", "From F73: F73 title (merged by the lead on 2026-10-01)"
    )
    (docs / "f43-review.md").write_text(f43_doc)

    # F73 has a card again on main
    (docs / "f73-new-card.md").write_text("# Milestone f73-new-card: New F73\n\n## Notes\n")

    _write(
        db_path,
        lambda conn: metrics.upsert_milestone(conn, planning, "f73-new-card", title="New F73"),
    )

    client = serve()
    html = client.get("/planning/f73").text
    assert "An earlier F73 was merged into F43" in html
    # The card's own title (not the heading's title)
    h2 = re.search(r"<h2[^>]*>([^<]+)</h2>", html)
    assert h2 and "New F73" in h2[1]


def test_lead_message_path_becomes_link(planning, db_path, serve):
    """A lead message without points whose text holds /planning/f95 shows it as a link."""
    _write(
        db_path,
        lambda conn: metrics.upsert_milestone(
            conn, planning, "f6-planning-room", title="The planning room"
        ),
    )
    conn = metrics.open_db(db_path)
    try:
        f6 = metrics.planner_thread(
            conn=conn, project_id=planning, card="f6", created=_at(timedelta(hours=5))
        )["id"]
        metrics.add_planner_message(
            conn,
            f6,
            "lead",
            _at(timedelta(hours=2)),
            "The conversation goes on on F95's thread: /planning/f95",
        )
    finally:
        conn.close()

    client = serve()
    html = client.get("/planning/f6").text
    assert '<a href="/planning/f95?project=coucou">/planning/f95</a>' in html


def test_lead_message_b_stays_text(planning, db_path, serve):
    """<b> in a lead message still shows as text."""
    _write(
        db_path,
        lambda conn: metrics.upsert_milestone(
            conn, planning, "f6-planning-room", title="The planning room"
        ),
    )
    conn = metrics.open_db(db_path)
    try:
        f6 = metrics.planner_thread(
            conn=conn, project_id=planning, card="f6", created=_at(timedelta(hours=5))
        )["id"]
        metrics.add_planner_message(
            conn, f6, "lead", _at(timedelta(hours=2)), "Check <b>bold</b> stays"
        )
    finally:
        conn.close()

    client = serve()
    html = client.get("/planning/f6").text
    assert "&lt;b&gt;bold&lt;/b&gt;" in html


def test_owner_message_path_no_link(planning, db_path, serve):
    """An owner message holding the path has no link."""
    _write(
        db_path,
        lambda conn: metrics.upsert_milestone(
            conn, planning, "f6-planning-room", title="The planning room"
        ),
    )
    conn = metrics.open_db(db_path)
    try:
        f6 = metrics.planner_thread(
            conn=conn, project_id=planning, card="f6", created=_at(timedelta(hours=5))
        )["id"]
        metrics.add_planner_message(conn, f6, "owner", _at(timedelta(hours=3)), "See /planning/f95")
        metrics.add_planner_message(conn, f6, "lead", _at(timedelta(hours=2)), "Yes")
    finally:
        conn.close()

    client = serve()
    html = client.get("/planning/f6").text
    # The owner's message should not have links
    assert '<a href="/planning/f95' not in html


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


def test_the_runners_look_shows_as_the_runners_and_waits_for_the_lead(planning, db_path, serve):
    """The runner's message on F9's thread, its planner row open: drawn as the runner's, not
    as the owner's words; nowhere under "Didn't go through" or "Your answers wanted"; the
    thread waits for the lead."""

    def look(conn: sqlite3.Connection) -> None:
        thread = metrics.planner_thread(conn, planning, "f9", _at(timedelta(minutes=5)))["id"]
        said = metrics.add_planner_message(conn, thread, "runner", _at(timedelta(minutes=5)), LOOK)
        metrics.queue_job(
            conn, planning, "planner", f"f9#m{said}", "a blocked ticket", _at(timedelta(minutes=5))
        )

    _write(db_path, look)
    client = serve()
    page = _thread(client, "f9")
    [drawn] = re.findall(r'<article class="message[^"]*"[^>]*>(.*?)</article>', page, re.S)
    assert _text(drawn).startswith("The runner · ") and LOOK in _text(drawn)
    assert "You ·" not in _text(drawn) and "Edit" not in _text(drawn)
    assert 'id="waiting"' in page  # the lead's reply is next
    html = _page(client)
    assert not _refused_items(html)
    assert "/planning/f9" not in dict(_items(_groups(html).get("answers", "")))
    assert ("/planning/f9", "Parallel developers") in _coming_items(html)


# --- a card's reserve lever (F172 D6) -----------------------------------------------------


def _reserve_client(board_db: Path, tmp_path: Path) -> TestClient:
    """``board_db``, its checkout marking F23 (planted) and F20 (a seed); F24 and F25 are
    growing and unmarked, F1 is ripe."""
    from factory_dashboard.app import create_app, get_now
    from tests.factory_dashboard.conftest import mark_reserve

    mark_reserve(board_db, tmp_path / "repo", "f23-planted", "f20-duck-pond")
    app = create_app(board_db, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url=ORIGIN)


def _lever(html: str) -> dict[str, Any] | None:
    """The card's lever: aria-checked, its classes, disabled, and what it posts; None: none."""
    bay = re.search(r'<div id="reserve-bay"[^>]*>(.*?)</div>', html, re.S)
    if bay is None:
        assert 'role="switch"' not in html.split('<header id="card"', 1)[1].split("</header>", 1)[0]
        return None
    button = re.search(r"<button[^>]*>", bay[1])
    assert button, "no lever"
    tag = button[0]
    vals = re.search(r"hx-vals='([^']*)'", tag)
    assert vals, tag
    return {
        "checked": re.search(r'aria-checked="([^"]*)"', tag)[1],  # type: ignore[index]
        "classes": re.search(r'class="([^"]*)"', tag)[1].split(),  # type: ignore[index]
        "disabled": " disabled" in tag,
        "posts": json.loads(unescape(vals[1])),
        "words": _text(bay[1]),
    }


def test_a_ready_card_s_lever_is_on_when_marked_and_off_when_not(board_db, tmp_path):
    """F23's doc says ``**Reserve:** yes``: on, posting ``off``; F24's doesn't: off, posting
    ``on``. Each posts the card's short key; the words say it uses both reserves."""
    client = _reserve_client(board_db, tmp_path)
    marked = _lever(_thread(client, "f23"))
    assert marked is not None
    assert (marked["checked"], marked["disabled"]) == ("true", False)
    assert "on-its-way" not in marked["classes"]
    reserve = {"kind": "reserve", "project": PROJECT}
    assert marked["posts"] == {**reserve, "subject": "f23", "value": "off"}
    assert "may use Claude's reserve" in marked["words"]
    assert "the week's reserve and your 25% of the 5-hour window" in marked["words"]
    unmarked = _lever(_thread(client, "f24"))
    assert unmarked is not None
    assert unmarked["checked"] == "false"
    assert unmarked["posts"] == {**reserve, "subject": "f24", "value": "on"}


@pytest.mark.parametrize("thread", ["f20", "f1", "m3", "f25"])
def test_an_idea_ripe_or_done_card_has_no_lever(board_db, tmp_path, thread):
    """F20 is a seed (its doc marked all the same), F1 ripe, M3 signed off, and F25 growing
    with its one ticket done, waiting for its review: nothing left to run (F172 D6)."""
    assert _lever(_thread(_reserve_client(board_db, tmp_path), thread)) is None


def test_a_lever_pulled_shows_on_its_way_until_the_runner_applies_it(board_db, tmp_path):
    """An open ``reserve`` request for F24 (and a done one for F23, and the week's switch,
    which name other subjects): F24's lever is on its way and can't be pulled again; F23's
    isn't. Done, the request leaves F24's lever as its doc says."""
    client = _reserve_client(board_db, tmp_path)

    def asked(conn: sqlite3.Connection) -> None:
        project = metrics.upsert_project(conn, PROJECT)
        metrics.add_request(conn, project, "reserve", "f24", "on", NOW.isoformat())
        metrics.add_request(conn, project, "reserve", "week", "on", NOW.isoformat())
        done = metrics.add_request(conn, project, "reserve", "f23", "off", NOW.isoformat())
        conn.execute("UPDATE owner_requests SET done = ? WHERE id = ?", (NOW.isoformat(), done))
        conn.commit()

    _write(board_db, asked)
    pulled = _lever(_thread(client, "f24"))
    assert pulled is not None
    assert "on-its-way" in pulled["classes"] and pulled["disabled"]
    assert pulled["checked"] == "false"  # the doc isn't marked yet
    still = _lever(_thread(client, "f23"))
    assert still is not None
    assert "on-its-way" not in still["classes"] and not still["disabled"]

    def applied(conn: sqlite3.Connection) -> None:
        conn.execute("UPDATE owner_requests SET done = ? WHERE done IS NULL", (NOW.isoformat(),))
        conn.commit()

    _write(board_db, applied)
    taken = _lever(_thread(client, "f24"))
    assert taken is not None
    assert "on-its-way" not in taken["classes"] and not taken["disabled"]


def test_pulling_the_lever_posts_its_request_and_shows_it_on_its_way(page, board_db, tmp_path):
    """In Chromium: the lever on F24's page posts ``reserve`` for ``f24``, ``on``; at once it
    has the dashed edge and is disabled; the request is stored, open."""
    client = _reserve_client(board_db, tmp_path)
    _open(page, client, "/planning/f24")
    lever = page.locator("#reserve-bay .lever")
    with page.expect_response(lambda r: r.url.endswith("/requests")):
        lever.click()
    assert "on-its-way" in (lever.get_attribute("class") or "")
    assert lever.is_disabled()
    conn = metrics.open_db(board_db)
    try:
        rows = conn.execute(
            "SELECT subject, value, done FROM owner_requests WHERE kind = 'reserve'"
        ).fetchall()
    finally:
        conn.close()
    assert [tuple(r) for r in rows] == [("f24", "on", None)]


def _doc(checkout: Path, key: str, body: str) -> None:
    cards = checkout / ".factory" / "cards"
    cards.mkdir(parents=True, exist_ok=True)
    (cards / f"{key}.md").write_text(f"# Milestone {key}\n\n{body}", encoding="utf-8")


def test_a_seed_shows_its_whole_note_under_a_cut_title(planning, checkout, serve):
    """F90 D2: the title is cut, the doc's Notes shown whole, escaped, in #note."""
    note = "is the planning conversation efficient atm, " + "x" * 60 + " <b>end</b>?"
    assert len(note) > 100
    _doc(checkout, "f9", f"## Notes\n{note}\n\n## Why\nnot this\n")
    html = _thread(serve(), "f9")
    section = html.split('<section id="note"', 1)[1].split("</section>", 1)[0]
    assert "&lt;b&gt;end&lt;/b&gt;?" in section and "not this" not in section
    assert "white-space: pre-line" in section and "<details" not in section
    assert html.index('id="card"') < html.index('id="note"')


def test_a_card_with_a_thread_folds_the_note(planning, checkout, db_path, serve):
    _doc(checkout, "f7", "## Notes\nWhole note.\n")

    def lead_only(conn: sqlite3.Connection) -> None:
        f7 = metrics.planner_thread(conn, planning, "f7", NOW.isoformat())["id"]
        metrics.add_planner_message(conn, f7, "lead", _at(timedelta(minutes=5)), "Hello.")

    _write(db_path, lead_only)
    html = _thread(serve(), "f7")
    assert '<details id="note">' in html and "Your note" in html and "Whole note." in html
    assert '<section id="note"' not in html


def test_a_merged_note_shows_without_the_factorys_marks(planning, checkout, serve):
    """f90-F1: F15's page showed "### From F18: …" and a quoted line's escaping backslash."""
    merged = "When?\n\n### From F18: Arrows (merged by the owner on 2026-10-13)\n\\> as I said"
    _doc(checkout, "f9", f"## Notes\n{merged}\n\n## Why\nx\n")
    html = _thread(serve(), "f9")
    note = unescape(html.split('<section id="note"', 1)[1].split("</section>", 1)[0])
    assert "From F18: Arrows" in note and "\n> as I said" in note
    assert "###" not in note and "\\" not in note


def test_no_notes_none_or_the_general_thread_show_no_note(planning, checkout, serve):
    client = serve()
    _doc(checkout, "f9", "## Why\nNo notes here.\n")
    _doc(checkout, "f6", "## Notes\n(none)\n\n## Why\nx\n")
    _doc(checkout, "general", "## Notes\nNot a card.\n")
    for thread in ("f9", "f6", "general"):
        assert 'id="note"' not in _thread(client, thread)


def test_a_repo_that_is_not_a_folder_shows_no_note(planning, db_path, serve):
    _write(db_path, lambda conn: metrics.upsert_project(conn, PROJECT, repo="https://x/y.git"))
    assert 'id="note"' not in _thread(serve(), "f9")


# --- old-path resolved mockup (f165-01) -------------------------------------------------------


def test_an_old_path_mockup_shows_its_frame_and_serves_its_file(planning, db_path, serve, checkout):
    """A mock-up whose stored path is ``docs/milestones/f67-mockup/review.html`` but the file
    lives at ``.factory/cards/f67-mockup/review.html`` on the plan branch: the frame's ``src``
    ends in the resolved path, there is no gone block, and the file is served."""
    git(checkout, "checkout", "-q", "-b", "plan/f67")
    (checkout / ".factory/cards/f67-mockup").mkdir(parents=True, exist_ok=True)
    (checkout / ".factory/cards/f67-mockup/review.html").write_text("<p>the desk</p>")
    git(checkout, "add", "-A")
    git(checkout, "commit", "-q", "-m", "drafts")
    git(checkout, "checkout", "-q", "main")
    _old_mockup = {
        "id": "mockup",
        "kind": "mockup",
        "title": "F67 mock-up",
        "path": "docs/milestones/f67-mockup/review.html",
        "key_points": [],
    }
    _write(db_path, lambda conn: _review(conn, planning, "f67", _old_mockup))
    client = serve()
    html = _review_page(client, "/planning/f67/proposals/mockup")
    frame = re.search(r'<iframe id="mockup" src="([^"?]+)[^"]*" sandbox="allow-scripts" ', html)
    assert frame and frame[1].endswith(".factory/cards/f67-mockup/review.html")
    assert 'id="mockup"' in html
    gone = re.search(r'<div class="gone">', html)
    assert gone is None
    served = client.get(frame[1])
    assert (served.status_code, served.text) == (200, "<p>the desk</p>")


def test_a_plan_proposal_shows_no_frame_and_no_gone_block(planning, db_path, serve):
    """A ``plan`` proposal: no mockup iframe and no gone block."""
    _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_PLAN))
    html = _review_page(serve(), "/planning/f6/proposals/plan")
    assert 'id="mockup"' not in html
    assert re.search(r'<div class="gone">', html) is None


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
    place; the held one says until when, the other after the reply being written."""
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
        ("f85", f"f85 waiting for the lead · {held}"),
        ("f87", "f87 waiting for the lead · after F84's reply, ~4 min"),
    ]
