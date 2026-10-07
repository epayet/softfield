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


def test_desk_returns_the_four_groups_in_order_empty_ones_too(db_path, db):
    """Without a thread or an idea card, the groups are still there, in order, empty but the
    ripe one: without ``write_live``'s running and ready tickets, f1 is ripe too."""
    groups = desk(db, PROJECT, NOW)
    assert [g.name for g in groups] == [
        "Your answers wanted",
        "Proposals to review",
        "Finished, to talk through",
        "Seeds, not asked about yet",
    ]
    assert [[i.title for i in g.items] for g in groups] == [
        [],
        [],
        ["The factory measures itself", "The web app"],
        [],
    ]
    assert desk(db, "nowhere", NOW)[2].items == []


def test_an_idea_card_with_a_thread_is_not_a_seed(planning, db):
    seeds = desk(db, PROJECT, NOW)[3].items
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
    proposals = desk(db, PROJECT, NOW)[1].items
    assert [p.link.rsplit("/", 1)[1] for p in proposals] == still_open


def test_a_request_older_than_the_reply_settles_nothing(planning, db_path, db):
    """The owner approved before the lead's latest reply: its proposals are new, so open."""
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn, planning, "approve_plan", "f6", None, _at(timedelta(hours=3))
        ),
    )
    assert len(desk(db, PROJECT, NOW)[1].items) == 2


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


def test_the_plant_form_posts_a_plant_request(page, planning, db_path, serve):
    """Planting asks the runner: a ``plant`` request, no subject, the title and the thoughts."""
    _open(page, serve())
    page.fill('#plant input[name="title"]', 'Memory "drift" on the frame')
    page.fill('#plant textarea[name="thoughts"]', "It forgets.\nOn every reload.")
    page.click('#plant button[type="submit"]')
    page.wait_for_selector("#plant-status >> text=Asked")
    conn = metrics.open_db(db_path)
    try:
        rows = conn.execute("SELECT * FROM owner_requests WHERE project_id = ?", (planning,))
        asked = [(r["kind"], r["subject"], json.loads(r["value"])) for r in rows]
    finally:
        conn.close()
    assert asked == [
        (
            "plant",
            None,
            {"title": 'Memory "drift" on the frame', "thoughts": "It forgets.\nOn every reload."},
        )
    ]


@pytest.mark.parametrize("size", [PHONE, DISPLAY], ids=["phone", "display"])
def test_the_desk_page_lays_out_at_phone_and_display_sizes(page, planning, db_path, serve, size):
    """Every group full, a message pending: nothing overlaps or runs off the screen."""
    _write(
        db_path,
        lambda conn: metrics.queue_job(
            conn, planning, "planner", "general#1", "a message", _at(timedelta(minutes=5))
        ),
    )
    page.set_viewport_size(size)
    _open(page, serve())
    assert page.locator("#desk-seeds").is_visible()
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
        ("/planning/f6/proposals/plan", "PLAN · answered F6 plan: 7 tickets"),
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
    page.wait_for_selector("#reply-status >> text=Asked")
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
    [item] = [i for i in desk(db, PROJECT, NOW)[1].items if i.link.endswith("/merge-f9")]
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
    assert not [i for i in desk(db, PROJECT, NOW)[1].items if i.link.endswith("/merge-f9")]


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
    frame = re.search(r'<iframe id="mockup" src="([^"?]+)[^"]*" sandbox ', html)
    assert frame and frame[1] == "/planning/mockups/f6/docs/milestones/f6-mockup/index.html"
    served = client.get(frame[1])
    assert (served.status_code, served.text) == (200, "<p>the desk</p>")
    for refused in (
        "docs/milestones/f6-planning-room.md",
        "docs/adr/20-planning-room.md",
        "docs/milestones/f6-mockup/missing.html",
        "docs/milestones/f6-mockup/",
    ):
        assert client.get(f"/planning/mockups/f6/{refused}").status_code == 404, refused


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
