"""The desk's Coming side (f6-20, F14, F31 D9): the Plant box, what is on its way, a waiting
plant's edit and cancel, and Didn't go through. Shared helpers stay in ``test_planning``."""

import json
import re
import sqlite3
from datetime import timedelta
from html import unescape

import pytest

from factory_dashboard.planning import desk
from runner import metrics
from tests.factory_dashboard.conftest import (
    NOW,
    PROJECT,
    _at,
)
from tests.factory_dashboard.test_planning import (
    ASKED,
    DUCKS,
    MESSAGE,
    NOTE,
    PICK,
    TAKEN,
    _asked_changes,
    _coming,
    _coming_items,
    _coming_text,
    _finished,
    _groups,
    _items,
    _needs_you_count,
    _open,
    _page,
    _refused_items,
    _seven_points,
    _text,
    _thread,
    _tile,
    _values,
    _write,
)
from tests.layout import PHONE


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
    without a reload and before Coming's 5 s poll; the textarea is empty afterwards."""
    _open(page, serve())
    assert page.locator("#desk-coming").count() == 0
    page.fill('#plant textarea[name="text"]', "A note about the frame")
    page.click("#plant-only")
    page.wait_for_selector("#desk-coming", timeout=2000)  # F63: the poll would take ~5 s
    pick = "planting at the runner's next pick"
    assert _coming_lines(page) == ["COMING SEEDS · 1", "A note about the frame", pick]
    assert page.input_value('#plant textarea[name="text"]') == ""
    assert page.locator("#plant-row").count() == 1
    assert page.locator("#plant").count() == 1
    assert page.locator("#desk-coming").count() == 1


def _coming_lines(page) -> list[str]:
    """Coming as the browser shows it, line by line (its heading is drawn in capitals)."""
    return [line for line in page.inner_text("#desk-coming").splitlines() if line.strip()]


def test_a_second_plant_adds_a_second_row(page, planning, db_path, serve):
    """Two plants from the same page, no reload: the form drawn again after the first still
    posts, and Coming holds the two notes in order under "Coming seeds · 2", once each."""
    _open(page, serve())
    page.fill('#plant textarea[name="text"]', "First note")
    page.click("#plant-only")
    page.wait_for_selector("#desk-coming >> text=First note")
    page.fill('#plant textarea[name="text"]', "Second note")
    page.click("#plant-ask")
    page.wait_for_selector("#desk-coming >> text=Second note")
    pick = "planting at the runner's next pick"
    assert _coming_lines(page) == ["COMING SEEDS · 2", "First note", pick, "Second note", pick]
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
    assert before == ["COMING SEEDS · 1", "Existing note", "planting at the runner's next pick"]
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
    assert '<section id="desk-coming"' not in html


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


def _answers(html: str) -> str:
    """The "Your answers wanted" group's markup."""
    return _groups(html).get("answers", "")


def _dashed(html: str, link: str) -> int:
    """How many dashed (on its way) items in "Your answers wanted" link to ``link``."""
    found = re.findall(r'<a href="([^"?]+)[^"]*" class="on-its-way-item"', _answers(html))
    return found.count(link)


def test_a_thread_with_open_plan_message_request_shows_in_answers_wanted(planning, db_path, serve):
    """A thread whose last stored message is the lead's: an open plan_message request makes its
    one box dashed, "waiting for the lead", and nothing shows in Coming seeds."""
    _write(db_path, lambda conn: _seven_points(conn, planning))
    _write(
        db_path,
        lambda conn: conn.execute(
            "INSERT INTO owner_requests (project_id, kind, subject, created)"
            " VALUES (?, 'plan_message', 'f6', ?)",
            (planning, _at(timedelta(minutes=5))),
        ),
    )
    html = _page(serve())
    assert '<section id="desk-coming"' not in html
    assert [i for i in _items(_answers(html)) if i[0] == "/planning/f6"] == [
        ("/planning/f6", "The planning room")
    ]
    assert _dashed(html, "/planning/f6") == 1
    assert "waiting for the lead" in _text(_answers(html))


def test_a_general_message_request_is_a_dashed_answers_item(planning, db_path, serve):
    """The general thread has no stored message: an open request still makes its dashed box."""
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
    html = _page(serve())
    assert '<section id="desk-coming"' not in html
    assert _dashed(html, "/planning/general") == 1
    assert "waiting for the lead" in _text(_answers(html))


def test_a_thread_with_open_planner_row_shows_in_answers_wanted(planning, db_path, serve):
    """F6's last message is the owner's; an open planner row about F6 keeps its dashed box."""
    _write(
        db_path,
        lambda conn: metrics.queue_job(
            conn, planning, "planner", "f6#2", "a message", _at(timedelta(minutes=5))
        ),
    )
    client = serve()
    html = _page(client)
    assert '<section id="desk-coming"' not in html
    assert _dashed(html, "/planning/f6") == 1
    assert "next, after f1-04-live · any minute now" in _text(_answers(html))


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
    assert f"waiting for the lead · {words}" in _text(_answers(_page(client)))
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
    assert "waiting for the lead · at the factory's next pick" in _text(_answers(html))


def test_a_thread_with_both_open_request_and_planner_row_shows_once(planning, db_path, serve):
    """A thread with both an open request and an open planner row shows once, dashed."""
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
    assert '<section id="desk-coming"' not in html
    assert _dashed(html, "/planning/general") == 1
    assert [i for i in _items(_answers(html)) if i[0] == "/planning/general"] == [
        ("/planning/general", "General")
    ]


def test_after_the_request_is_done_and_the_lead_replies_the_box_goes_solid(
    planning, db_path, serve
):
    """The owner's open message makes the general thread's box dashed; once the runner has
    stored it, an open planner job keeps it dashed; once the lead's reply is stored, it is solid
    and counts."""
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn, planning, "plan_message", "general", "{}", _at(timedelta(minutes=5))
        ),
    )
    client = serve()
    before = _count(_page(client))
    assert _dashed(_page(client), "/planning/general") == 1

    def picked(conn: sqlite3.Connection) -> None:
        conn.execute(
            "UPDATE owner_requests SET done = ? WHERE kind = 'plan_message'",
            (_at(timedelta(minutes=4)),),
        )
        thread = metrics.planner_thread(conn, planning, "general", _at(timedelta(minutes=4)))["id"]
        metrics.add_planner_message(conn, thread, "owner", _at(timedelta(minutes=4)), "And test 1?")
        metrics.queue_job(
            conn, planning, "planner", "general#1", "a message", _at(timedelta(minutes=4))
        )

    _write(db_path, picked)
    html = _page(client)
    assert _dashed(html, "/planning/general") == 1
    assert _count(html) == before

    def replied(conn: sqlite3.Connection) -> None:
        thread = metrics.planner_thread(conn, planning, "general", _at(timedelta(minutes=4)))["id"]
        metrics.add_planner_message(conn, thread, "lead", _at(timedelta(minutes=1)), "It passes.")

    _write(db_path, replied)
    html = _page(client)
    assert '<section id="desk-coming"' not in html
    assert _dashed(html, "/planning/general") == 0
    assert ("/planning/general", "General") in _items(_answers(html))
    assert _count(html) == before + 1


def test_a_first_message_on_a_card_with_no_thread_is_a_dashed_answers_item(
    planning, db_path, serve
):
    """F9 is an idea card nobody has talked about: the runner makes its thread at its next pick,
    but the owner's message shows at once as a dashed box, and F9 leaves the seeds."""
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn, planning, "plan_message", "f9", "{}", _at(timedelta(minutes=5))
        ),
    )
    html = _page(serve())
    assert '<section id="desk-coming"' not in html
    assert _dashed(html, "/planning/f9") == 1
    assert ("/planning/f9", "Parallel developers") in _items(_answers(html))
    assert "waiting for the lead" in _text(_answers(html))
    assert "/planning/f9" not in _groups(html).get("seeds", "")


def test_an_open_plant_request_is_all_coming_seeds_holds(planning, db_path, serve):
    """Coming's heading reads "Coming seeds" and holds the plant, nothing about a thread."""
    _write(
        db_path,
        lambda conn: conn.execute(
            "INSERT INTO owner_requests (project_id, kind, value, created)"
            " VALUES (?, 'plant', ?, ?)",
            (planning, json.dumps({"text": "A new idea"}), _at(timedelta(minutes=10))),
        ),
    )
    _write(
        db_path,
        lambda conn: metrics.queue_job(
            conn, planning, "planner", "f6#2", "a message", _at(timedelta(minutes=5))
        ),
    )
    html = _page(serve())
    assert "Coming seeds · 1" in _coming(html)
    assert "A new idea" in _coming(html)
    assert "/planning/f6" not in _coming(html)


def test_after_the_leads_reply_the_box_goes_solid(planning, db_path, serve):
    """Once the lead's reply is stored, the thread's box in "Your answers wanted" is solid."""
    # First verify the box is dashed with an open planner row
    _write(
        db_path,
        lambda conn: metrics.queue_job(
            conn, planning, "planner", "f6#2", "a message", _at(timedelta(minutes=5))
        ),
    )
    client = serve()
    html = _page(client)
    assert _dashed(html, "/planning/f6") == 1

    # Now the lead replies: add a lead message to f6
    _write(db_path, lambda conn: _seven_points(conn, planning))

    html = _page(client)
    assert '<section id="desk-coming"' not in html
    assert _dashed(html, "/planning/f6") == 0
    assert ("/planning/f6", "The planning room") in _items(_groups(html)["answers"])


def test_a_waiting_message_adds_nothing_to_the_counts_and_takes_its_proposals_off(
    planning, db_path, serve
):
    """A message waits for the lead: its dashed box adds nothing to the Planning tab's count or
    the Overview's Needs you, and its thread's proposals leave the count (F100)."""
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
    # The dashed box is the only new item, and it doesn't count
    groups = _groups(html)
    assert list(groups) == ["ripe", "answers", "proposals", "seeds"]
    assert _dashed(html, "/planning/f6") == 1
    # The Planning tab count drops by f6's plan and ADR only: with the owner's message waiting
    # for the lead they are being revised, not waiting for the owner (F100); the dashed box
    # itself adds nothing
    planning_tab = re.search(
        r'<a href="/planning\?project=coucou"[^>]*id="planning-tab">Planning · (\d+)</a>', html
    )
    assert planning_tab and planning_tab[1] == str(base_count - 1)
    # The Overview's Needs you is unchanged: the desk is one line whatever its count
    assert _needs_you_count(client.get("/").text) == base_needs


def test_coming_heading_shows_the_item_count(planning, db_path, serve):
    """With a plant and a thread on its way, the heading counts the plant only."""
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
    assert "Coming seeds · 1" in _coming(html)


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
        ("plant", None, DUCKS, "planted .softfield/cards/f12-rubber-ducks.md, queued for the lead"),
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


def _waiting(html: str, request_id: int) -> tuple[str, str]:
    """A plant's row in Coming: its tag (``details`` while it opens, ``div`` once a change is
    on its way) and its markup."""
    found = re.search(
        rf'<(details|div) class="[^"]*" id="waiting-{request_id}".*?</\1>', _coming(html), re.S
    )
    assert found, f"no row for request {request_id}"
    return found[1], found[0]


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
    assert "Coming seeds · 1" in _coming(html)
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
    assert _coming_lines(page) == ["COMING SEEDS · 2", "Calm colours", PICK, "Rubber ducks", PICK]
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
    assert _coming_lines(page) == ["COMING SEEDS · 2", *changed, "Rubber ducks", PICK]
    assert page.locator(f"#waiting-{note} summary, #save-{note}, #cancel-{note}").count() == 0
    assert page.locator(f"details#waiting-{ducks}").count() == 1
    assert page.input_value('#plant textarea[name="text"]') == "Half a new note"
    assert _asked_changes(db_path) == [(str(note), {"text": "Calmer colours"})]
    assert _values(db_path, "plant") == [json.loads(NOTE), json.loads(DUCKS)]  # never edited
    page.reload()
    assert _coming_lines(page) == ["COMING SEEDS · 2", *changed, "Rubber ducks", PICK]


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
    assert _coming_lines(page) == [
        "COMING SEEDS · 1",
        'Rubber "duck" keys',
        f"changed · {PICK}",
        ASKED,
    ]
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
    assert _coming_lines(page) == ["COMING SEEDS · 1", "Rubber ducks", cancelling, ASKED]
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
