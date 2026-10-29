"""A thread's page (f6-07, f143-03): ``/planning/{thread}``, its messages and points, Send, the
archive row, Sign off, the proposals' standing, a waiting message's edit and cancel, no fast
lane lever and a seed's note. The helpers shared with the desk stay in ``test_planning``."""

import json
import re
import sqlite3
from datetime import timedelta
from html import unescape
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from runner import metrics
from tests.factory_dashboard.conftest import (
    NOW,
    PROJECT,
    _at,
)
from tests.factory_dashboard.test_planning import (
    _REVIEW_ADR,
    _REVIEW_MERGE,
    _REVIEW_PLAN,
    _SEVEN_POINTS,
    ASKED,
    LOOK,
    MESSAGE,
    ORIGIN,
    _archive,
    _asked_changes,
    _finished,
    _group,
    _groups,
    _lead_says,
    _open,
    _page,
    _points,
    _posts,
    _refused_items,
    _review,
    _review_page,
    _seven_points,
    _text,
    _thread,
    _values,
    _write,
)
from tests.factory_dashboard.test_proposal import (
    _f6_mockup_review,
)
from tests.layout import DISPLAY, PHONE, layout_problems
from tests.runner.conftest import git

LIVE = 9000  # one 5 s poll, and room to draw it


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
    assert '<p class="said"></p>' not in html


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
    # it waits: drawn dashed, in hazard, from the stylesheet (f81-05)
    border = msg.evaluate(
        "e => [getComputedStyle(e).borderTopStyle, getComputedStyle(e).borderTopColor]"
    )
    hazard = page.evaluate(
        "() => { const p = document.createElement('p'); p.style.color = 'var(--hazard)';"
        " document.body.append(p); const c = getComputedStyle(p).color; p.remove(); return c; }"
    )
    assert border == ["dashed", hazard]
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
    # dashed hazard border (on the article via data-waiting attribute)
    assert "data-waiting" in msg_style
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
    assert "data-waiting" in html

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
    # text appears once (no "Sent" line, no data-waiting)
    assert html.count("And the phone?") == 1
    assert "Sent" not in _text(html)
    assert "data-waiting" not in html


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
    assert "data-waiting" in tablet and "data-waiting" in phone
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
    assert "Make it calm." in waiting and "data-waiting" in waiting
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
    [item] = _group(db, "ripe")
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
    found = re.search(r'class="[^"]*change-btn[^"]*"', html) is not None
    assert found is buttons


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
            re.search(r'class="word"[^>]*style="[^"]*--c:\s*var\((--[\w-]+)\)', r)[1],  # type: ignore[index]
            _text(m[1]) if (m := re.search(r'<span class="who"[^>]*>(.*?)</span>', r)) else "",
        )
        for r in rows
    }
    assert found == {
        ".factory/cards/f7-x.md": ("--good", ""),
        ".factory/tasks/later/f7-01-a.md": ("--good", "lead · difficulty 6"),
        ".factory/tasks/later/f7-02-b.md": ("--good", "developer · difficulty 2"),
    }


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
        rf'<button[^>]*type="submit"[^>]*form="editor-{said}"[^>]*id="save-{said}"[^>]*hidden',
        waiting,
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
    assert "data-waiting" in changed and "line-through" not in changed
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
    assert '<p class="said struck">Make it calm.</p>' in cancelled
    assert _text(cancelled).endswith(f"Make it calm. {CANCELLING} {ASKED}")
    assert f'hx-get="/requests/{cancel}"' in cancelled
    assert "<button" not in cancelled and "<form" not in cancelled
    assert 'id="reply"' in html and '<p id="waiting"' not in html
    _finished(db_path, planning, "plan_message", "f6", MESSAGE, None)
    html = _thread(client, "f6")
    assert '<p id="waiting"' in html and 'id="reply"' not in html


def _dashed_links(html: str) -> list[str]:
    """The links of the dashed (on its way) boxes in "Your answers wanted"."""
    return re.findall(
        r'<a href="([^"?]+)[^"]*" class="on-its-way-item', _groups(html).get("answers", "")
    )


def test_a_cancelled_message_no_longer_puts_its_thread_in_answers_wanted(planning, db_path, serve):
    """The desk says what the thread says: a message with a cancel on its way waits for no
    reply; an edited one still does, and so does a second message nobody cancelled."""
    said = _finished(db_path, planning, "plan_message", "general", MESSAGE, None)
    client = serve()
    assert _dashed_links(_page(client)) == ["/planning/general"]
    edit = _finished(db_path, planning, "change", str(said), COMMENTED, None)
    assert _dashed_links(_page(client)) == ["/planning/general"]
    _write(db_path, lambda conn: metrics.finish_request(conn, edit, NOW.isoformat(), "changed"))
    _finished(db_path, planning, "change", str(said), '{"cancel": true}', None)
    assert _dashed_links(_page(client)) == []  # nothing else was coming
    _finished(db_path, planning, "plan_message", "general", MESSAGE, None)
    assert _dashed_links(_page(client)) == ["/planning/general"]


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
    assert _dashed_links(html) == ["/planning/f9"]  # one dashed box, nothing asks for the owner
    assert 'id="desk-coming"' not in html.replace('id="live-desk-coming"', "")


# --- a card's fast lane lever is on its page under the board (F172 D8) --------------------


def _reserve_client(board_db: Path, tmp_path: Path) -> TestClient:
    """``board_db``, its checkout marking F23 (planted) and F20 (a seed); F24 and F25 are
    growing and unmarked, F1 is ripe."""
    from factory_dashboard.app import create_app, get_now
    from tests.factory_dashboard.conftest import mark_reserve

    mark_reserve(board_db, tmp_path / "repo", "f23-planted", "f20-duck-pond")
    app = create_app(board_db, PROJECT)
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app, base_url=ORIGIN)


@pytest.mark.parametrize("thread", ["f23", "f24"])
def test_a_planted_card_s_thread_has_no_lever(board_db, tmp_path, thread):
    """F172 D8: the lever lives on the card's page under the board, not on its thread, even
    for F23 (marked) and F24 (unmarked), which have one there."""
    page = _thread(_reserve_client(board_db, tmp_path), thread)
    head = page.split('<header id="card"', 1)[1].split("</header>", 1)[0]
    assert 'role="switch"' not in head and "fast lane" not in head.lower()
    assert "reserve-bay" not in page and 'id="fast-lane"' not in page
    assert "Claude's reserve" not in page


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
    assert '<p class="said">' in section and "<details" not in section  # pre-line, in the CSS
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


def test_the_dock_is_compact_on_a_phone(page, planning, db_path, serve, checkout):
    """At 390 × 844 the dock is at most 72 px tall and still holds the count, the button and
    the closed Reject… fold on one row, the button in view; opened, the fold may grow the
    dock."""
    _f6_mockup_review(db_path, planning, checkout)
    page.set_viewport_size(PHONE)
    _open(page, serve(), "/planning/f6/proposals/mockup")
    dock = page.locator(".proposal-page .dock")
    height = dock.evaluate("e => e.offsetHeight")
    assert height <= 72, height
    assert not page.locator(".dock > h2").is_visible()
    assert not page.locator("#review-status").is_visible()
    row = ("#review-count", "#approve-plan", "#reject > summary")
    boxes = [page.locator(s).bounding_box() for s in row]
    dock_box = dock.bounding_box()
    assert dock_box
    for box in boxes:
        assert box and dock_box["y"] <= box["y"]
        assert box["y"] + box["height"] <= dock_box["y"] + height
    # this page is shorter than the screen, so the dock sits in the flow: Send at the bottom on a
    # long page is test_on_a_phone_one_point_shows_at_a_time's check
    box = boxes[1]
    assert box and box["y"] + box["height"] <= PHONE["height"]
    page.locator("#reject > summary").click()
    assert page.locator("#reject-button").is_visible()


def test_the_review_status_shows_after_sending_on_a_phone(page, planning, db_path, serve, checkout):
    """After sending, the request's answer shows in the dock at 390 px."""
    _f6_mockup_review(db_path, planning, checkout)
    page.set_viewport_size(PHONE)
    _open(page, serve(), "/planning/f6/proposals/mockup")
    page.click("#approve-plan")
    page.wait_for_selector("#review-status >> text=Asked")
    status = page.locator("#review-status")
    assert status.is_visible()
    assert "Asked" in status.inner_text()
