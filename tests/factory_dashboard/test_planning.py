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

from factory_dashboard.planning import desk, waiting_for_you
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


def _group(db: sqlite3.Connection, key: str) -> list[Any]:
    """A desk group's items by its key."""
    for g in desk(db, PROJECT, NOW):
        if g.key == key:
            return g.items
    return []


def _tile(html: str, tile_id: str) -> str:
    found = re.search(rf'<div id="{tile_id}"(.*?)</div>\s*(?=<div id=|</section>)', html, re.S)
    assert found, tile_id
    return unescape(re.sub(r"<[^>]+>", "", found[1]))


def test_each_group_shows_its_items_in_order(planning, serve):
    """A reply unanswered, the open proposals and a ripe card, each in its group, and the
    groups in D6's order; the thread the owner answered last is not among the answers."""
    groups = _groups(_page(serve()))
    assert list(groups) == ["ripe", "proposals", "answers", "seeds"]
    assert _items(groups["answers"]) == [("/planning/general", "General")]
    assert "the lead replied 60 min ago" in groups["answers"]
    assert _items(groups["proposals"]) == [
        ("/planning/f6/proposals/adr-20", "F6 plan: 7 tickets"),
    ]
    assert "2 key points" in groups["proposals"]
    assert _items(groups["ripe"]) == [("/planning/m4", "The web app")]
    assert _items(groups["seeds"]) == [("/planning/f9", "Parallel developers")]


def test_desk_returns_the_six_groups_in_order_empty_ones_too(db_path, db):
    """Without a thread or an idea card, the groups are still there, in order, empty but the
    ripe one: without ``write_live``'s running and ready tickets, f1 is ripe too."""
    groups = desk(db, PROJECT, NOW)
    assert [g.name for g in groups] == [
        "Didn't go through",
        "Blocked tickets",
        "To sign off",
        "Proposals to review",
        "Your answers wanted",
        "Seeds, not asked about yet",
    ]
    assert [[i.title for i in g.items] for g in groups] == [
        [],
        [],
        ["The factory measures itself", "The web app"],
        [],
        [],
        [],
    ]
    assert _group(db, "blocked") == []
    assert [g.items for g in desk(db, "nowhere", NOW)] == [[], [], [], [], [], []]


def test_an_idea_card_with_a_thread_is_not_a_seed(planning, db):
    seeds = _group(db, "seeds")
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
    (item,) = _group(db, "proposals")  # the card's parts are one item (F51 D1)
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
    (item,) = _group(db, "proposals")  # F51 D1: the card's two proposals are one item
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


def _headings(html: str) -> dict[str, str]:
    """Each desk group's heading text by its key."""
    found = {}
    for key, markup in _groups(html).items():
        h3 = re.search(r"<h3[^>]*>(.*?)</h3>", markup, re.S)
        assert h3 is not None, f"group {key} has no heading"
        found[key] = unescape(h3[1])
    return found


def _waiting_by_group(db_path: Path) -> dict[str, tuple[str, int]]:
    """Each shown group's name and its items not on their way, from the desk itself."""
    conn = metrics.open_db(db_path)
    try:
        return {
            g.key: (g.name, sum(not item.on_its_way for item in g.items))
            for g in desk(conn, PROJECT, NOW)
            if g.items
        }
    finally:
        conn.close()


def _desk_number(html: str) -> int:
    heading = re.search(r'<section id="desk"[^>]*>\s*<h2[^>]*>Your desk · (\d+)</h2>', html)
    assert heading, "the desk heading has no number"
    return int(heading[1])


def test_group_headings_count_what_waits_and_add_up_to_the_desk(planning, db_path, serve):
    """F26: each group's heading reads its name, " · " and its items still waiting, and the
    numbers add up to "Your desk · N" and the Planning tab on the same page."""
    html = _page(serve())
    headings = _headings(html)
    waiting = _waiting_by_group(db_path)
    assert set(headings) == set(waiting)
    assert len(headings) > 1
    for key, (name, n) in waiting.items():
        assert n > 0
        assert headings[key] == f"{name} · {n}"
    # the fixture's card with open proposals: one item since F51 D1
    assert headings["proposals"] == "Proposals to review · 1"
    total = sum(n for _, n in waiting.values())
    assert _desk_number(html) == total
    assert f'id="planning-tab">Planning · {total}</a>' in html


def test_a_group_heading_leaves_out_what_is_on_its_way(planning, db_path, serve):
    """F26: after an archive request, the thread's card stays listed in its group, and that
    group's number is one less, or its name alone when nothing in it waits any more."""
    html = _page(serve())
    before = _headings(html)
    holder = _group_holding(html, "/planning/general")
    name, n = _waiting_by_group(db_path)[holder]
    assert before[holder] == f"{name} · {n}"
    _ask_archive(db_path, planning, "general")
    html = _page(serve(live=False))
    after = _headings(html)
    assert "/planning/general" in dict(_items(_groups(html)[holder]))
    assert after[holder] == (f"{name} · {n - 1}" if n > 1 else name)
    assert {k: v for k, v in after.items() if k != holder} == {
        k: v for k, v in before.items() if k != holder
    }
    assert sum(n for _, n in _waiting_by_group(db_path).values()) == _desk_number(html)


def _group_holding(html: str, link: str) -> str:
    """The key of the desk group that lists ``link``."""
    return next(k for k, markup in _groups(html).items() if link in dict(_items(markup)))


def _ask_archive(db_path: Path, project_id: int, card: str) -> None:
    """An archive request on ``card``'s thread, not yet done by the runner."""
    _write(
        db_path,
        lambda conn: metrics.add_request(conn, project_id, "archive", card, "on", NOW.isoformat()),
    )


def test_a_group_whose_items_are_all_on_their_way_reads_its_name_alone(planning, db_path, serve):
    """F26: with every thread of a group archived but not yet done, each stays listed and the
    heading reads the group's name alone, with no " · "."""
    html = _page(serve())
    holder = _group_holding(html, "/planning/general")
    links = [link for link, _ in _items(_groups(html)[holder])]
    for link in links:
        _ask_archive(db_path, planning, link.removeprefix("/planning/"))
    html = _page(serve(live=False))
    name, n = _waiting_by_group(db_path)[holder]
    assert n == 0
    assert [link for link, _ in _items(_groups(html)[holder])] == links
    assert _headings(html)[holder] == name


def test_the_refused_group_counts_its_notes(planning, db_path, serve):
    """F26: a refused note on the desk makes "Didn't go through · 1"."""
    _finished(db_path, planning, "plant", None, DUCKS, TAKEN)
    html = _page(serve())
    assert _headings(html)["refused"] == "Didn't go through · 1"


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


MESSAGE = json.dumps({"text": "Make it calm.", "comments": {}})


def _values(db_path: Path, kind: str) -> list[dict[str, Any]]:
    conn = metrics.open_db(db_path)
    try:
        rows = conn.execute("SELECT value FROM owner_requests WHERE kind = ? ORDER BY id", (kind,))
        return [json.loads(r["value"]) for r in rows]
    finally:
        conn.close()


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
    [item] = [i for i in _group(db, "answers") if i.link == "/planning/general"]
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
    [item] = [i for i in _group(db, "ripe") if i.link == "/planning/m4"]
    assert item.on_its_way and item.words == "signing off at the runner's next pick"


def _trail(html: str) -> dict[str, str]:
    nav = re.search(r'<nav id="desk-trail".*?</nav>', html, re.S)
    assert nav, "no #desk-trail"
    found = dict(re.findall(r'<a id="desk-(previous|next)" href="([^"?]+)', nav[0]))
    found["words"] = _text(nav[0])
    return found


def test_previous_and_next_step_through_what_waits(planning, db_path, serve):
    """F35: from the general thread, Next is F9 (seeds come after answers); from there Previous is
    back and Next is the ripe card; a page already done with leads to the first one left."""
    client = serve()
    first = _trail(_thread(client, "general"))
    assert first["next"] == "/planning/f9" and first["previous"] == "/planning/f6/proposals/adr-20"
    assert "3 of " in first["words"] and "waiting for you" in first["words"]
    middle = _trail(_review_page(client, "/planning/f6/proposals/adr-20"))
    assert middle["previous"] == "/planning/m4"
    assert middle["next"] == "/planning/general"
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn, planning, "archive", "general", "on", NOW.isoformat()
        ),
    )
    done = _trail(_thread(client, "general"))  # archived: no longer waiting
    assert done["next"] == "/planning/m4" and "previous" not in done


# --- a waiting plant is edited or cancelled from Coming (F14) --------------------------------

NOTE = json.dumps({"text": "Calm colours", "ask": True})
PICK = "planting at the runner's next pick"
ASKED = "Asked: the runner will do it."


def _asked_changes(db_path: Path) -> list[tuple[str | None, dict[str, Any]]]:
    conn = metrics.open_db(db_path)
    try:
        rows = conn.execute("SELECT * FROM owner_requests WHERE kind = 'change' ORDER BY id")
        return [(r["subject"], json.loads(r["value"])) for r in rows]
    finally:
        conn.close()


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
    """With no waiting plant, the #desk-coming section is not rendered
    (only the poll wrapper exists)."""
    html = _page(serve())
    assert '<section id="desk-coming"' not in html


def test_coming_then_plant_then_the_desk_then_archived(planning, db_path, serve):
    """F63 D1, D2: what the owner just did first, then the box, the desk, and Archived last."""
    _finished(db_path, planning, "plant", None, NOTE, None)
    _archive(db_path, planning, "general", timedelta(hours=1))
    html = _page(serve())
    marks = ['<section id="desk-coming"', 'id="plant"', 'id="desk"', 'id="archived"']
    places = [html.index(mark) for mark in marks]
    assert places == sorted(places)


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


def test_two_blocked_tickets_appear_second_on_the_desk_with_their_ids_and_reason(
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
    blocked_group_items = _group(db, "blocked")
    assert len(blocked_group_items) == 2
    blocked_group = next(g for g in desk(db, PROJECT, NOW) if g.key == "blocked")
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
    blocked_group = next(g for g in desk(db, PROJECT, NOW) if g.key == "blocked")
    assert blocked_group.items == []


def test_no_open_blocked_tickets_means_empty_group_and_no_heading(planning, db_path, db, serve):
    """With no open blocked rows, the group is empty and /planning doesn't show its heading."""
    html = _page(serve())
    groups = _groups(html)
    blocked_markup = groups.get("blocked", "")
    assert "Blocked tickets" not in blocked_markup
    blocked_group = next(g for g in desk(db, PROJECT, NOW) if g.key == "blocked")
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
    group = next(g for g in desk(db, PROJECT, NOW) if g.key == "blocked")
    assert [(i.title, i.on_its_way, i.words) for i in group.items] == [
        (FIRST, False, "waiting on f12-03"),
        (SECOND, True, ON_ITS_WAY[kind]),
    ]


# --- the lead looks at a blocked ticket (ADR 29 items 1 and 4, f106-04) ----------------------


LOOK = "f9-01-board blocked: check-all failed. Its work is on task/f9-01-board."


def _blocked_words(db, project_id):
    """Return the blocked group's items' words."""
    blocked_group = next(g for g in desk(db, PROJECT, NOW) if g.key == "blocked")
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
    """The thread boxes waiting for the lead, in order, from "Your answers wanted": (thread,
    text, drawn as the one being written)."""
    return [
        (thread, _text(body), "writing" in attrs)
        for thread, attrs, body in re.findall(
            r'<a href="/planning/([^"?]+)[^"]*"( class="on-its-way-item[^>]*)>(.*?)</a>',
            _groups(html)["answers"],
            re.S,
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
    # the words in Opus's ink, darkened in the light theme to read on a pale bay (f81-05: the
    # stylesheet colours .writing)
    css = (STATIC / "dashboard.css").read_text()
    assert ".thread-page #waiting.writing { color: var(--opus-ink); }" in css


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


# --- proposals being revised while the owner's message waits (F100) -----------------------------

_MOCKUP: dict[str, Any] = {**_REVIEW_PLAN, "id": "mock", "kind": "mockup", "title": "A mock-up"}


def _revising(
    db_path: Path, planning: int, *, stored: bool = False, proposals: tuple[Any, ...] = ()
) -> None:
    """f85's lead reply lists a plan and a mock-up; then the owner's message waits for the lead:
    an open request, or (``stored``) the message in the thread and a planner job about it."""

    def write(conn: sqlite3.Connection) -> None:
        _review(conn, planning, "f85", *(proposals or (_REVIEW_PLAN, _MOCKUP)))
        if not stored:
            value = '{"text": "Why?"}'
            metrics.add_request(
                conn, planning, "plan_message", "f85", value, _at(timedelta(minutes=5))
            )
            return
        found = metrics.planner_thread(conn, planning, "f85", _at(timedelta(hours=5)))["id"]
        metrics.add_planner_message(conn, found, "owner", _at(timedelta(minutes=5)), "Why?")
        metrics.queue_job(
            conn, planning, "planner", "f85#1", "your message", _at(timedelta(minutes=4))
        )

    _write(db_path, write)


def _proposal_items(db_path: Path) -> list[Any]:
    conn = metrics.open_db(db_path)
    try:
        return [i for i in _group(conn, "proposals") if i.link.startswith("/planning/f85/")]
    finally:
        conn.close()


def _waiting_proposals(db_path: Path) -> list[Any]:
    conn = metrics.open_db(db_path)
    try:
        return [i for i in waiting_for_you(desk(conn, PROJECT, NOW)) if "/f85/" in i.link]
    finally:
        conn.close()


@pytest.mark.parametrize("stored", [False, True])
def test_proposals_wait_for_the_lead_while_the_owners_message_does(
    planning, db_path, serve, stored
):
    """An open request, or the stored message with a planner job open: the thread's proposals
    are dashed, "being revised · …", and don't wait for the owner."""
    client = serve()
    _revising(db_path, planning, stored=stored)
    (item,) = _proposal_items(db_path)
    assert item.on_its_way and item.words.startswith("being revised · ")
    group = _groups(_page(client))["proposals"]
    assert 'class="on-its-way-item' in group
    assert "being revised · " in _text(group)
    assert not _waiting_proposals(db_path)


def test_the_general_threads_proposals_are_revised_each_on_its_own(planning, db_path, db):
    """The general thread's proposals are one desk item each (F51 D1): a message on it dashes
    each, and a message on another thread none."""

    def write(conn: sqlite3.Connection) -> None:
        _review(conn, planning, "general", _REVIEW_PLAN, _MOCKUP)
        value = '{"text": "Why?"}'
        metrics.add_request(conn, planning, "plan_message", "f85", value, _at(timedelta(minutes=6)))

    _write(db_path, write)
    general = [i for i in _group(db, "proposals") if i.link.startswith("/planning/general/")]
    assert len(general) == 2 and not any(i.on_its_way for i in general)
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn, planning, "plan_message", "general", '{"text": "Why?"}', NOW.isoformat()
        ),
    )
    general = [i for i in _group(db, "proposals") if i.link.startswith("/planning/general/")]
    assert len(general) == 2
    assert all(i.on_its_way and i.words.startswith("being revised · ") for i in general)


def test_a_lead_reply_without_proposals_makes_them_solid_again(planning, db_path, serve):
    serve()
    _revising(db_path, planning, stored=True)
    _write(db_path, lambda conn: conn.execute("UPDATE work_queue SET done = ?", (NOW.isoformat(),)))
    _lead_says(db_path, planning, "f85", "Unchanged.")
    # the reply had no proposals, so the earlier set is still the latest listing: solid
    (item,) = _proposal_items(db_path)
    assert not item.on_its_way and "being revised" not in item.words
    assert _waiting_proposals(db_path)


def test_a_cancelled_message_leaves_the_proposals_solid(planning, db_path, serve):
    serve()
    _revising(db_path, planning)

    def cancel(conn: sqlite3.Connection) -> None:
        asked = conn.execute("SELECT id FROM owner_requests WHERE kind = 'plan_message'").fetchone()
        value = '{"cancel": true}'
        metrics.add_request(conn, planning, "change", str(asked["id"]), value, NOW.isoformat())

    _write(db_path, cancel)
    (item,) = _proposal_items(db_path)
    assert not item.on_its_way


def test_an_approve_on_its_way_keeps_its_own_words(planning, db_path, serve):
    serve()
    _revising(db_path, planning, proposals=(_REVIEW_PLAN,))
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn, planning, "reject", "f85/plan", None, _at(timedelta(minutes=2))
        ),
    )
    (item,) = _proposal_items(db_path)
    assert item.words == "on its way · the runner applies it at its next pick"


def test_the_thread_and_proposal_pages_say_being_revised(planning, db_path, serve):
    client = serve()
    _revising(db_path, planning)
    thread = _thread(client, "f85")
    assert _text(thread).count("being revised") >= 2
    assert thread.count('class="proposal revising"') == 2
    page = _review_page(client, "/planning/f85/proposals/plan")
    assert "Being revised" in page
    assert "Approve" in page and "Reject" in page
