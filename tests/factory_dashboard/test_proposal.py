"""The proposal review page and the mock-up route (f6-08, f165-01):
``/planning/{thread}/proposals/{id}`` and ``/planning/mockups/...``. The helpers shared with the
desk and the thread page stay in ``test_planning``."""

import json
import re
import sqlite3
from datetime import timedelta
from html import unescape
from pathlib import Path
from typing import Any

import pytest

from factory_dashboard.planning import desk, waiting_for_you
from runner import metrics
from tests.factory_dashboard.conftest import (
    NOW,
    PROJECT,
)
from tests.factory_dashboard.test_planning import (
    _REVIEW_ADR,
    _REVIEW_MERGE,
    _REVIEW_PLAN,
    _finished,
    _group,
    _lead_says,
    _open,
    _posts,
    _review,
    _review_page,
    _text,
    _write,
)
from tests.layout import PHONE
from tests.runner.conftest import git

ORIGIN = "http://127.0.0.1:8765"
STATIC = Path(__file__).parents[2] / "factory_dashboard" / "static"

_REVIEW_MOCKUP: dict[str, Any] = {
    "id": "mockup",
    "kind": "mockup",
    "title": "The desk, drawn",
    "path": ".softfield/cards/f6-mockup/index.html",
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
REFRESH = (
    "Check this against main as it is now: renumber what is taken, drop what is done or gone,"
    " and update the tickets."
)


def _key_points(html: str) -> list[str]:
    return [
        _text(body) for body in re.findall(r'<div class="key-point"[^>]*>(.*?)<button', html, re.S)
    ]


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
    adr = checkout / ".softfield" / "adr" / "20-planning-room.md"
    adr.parent.mkdir(parents=True)
    adr.write_text(ADR_ON_MAIN.format(status="Proposed"))
    assert " disabled" in approve()
    adr.write_text(ADR_ON_MAIN.format(status="Accepted"))
    assert " disabled" not in approve()


def test_an_open_accept_adr_enables_approve_plan_and_says_so(planning, db_path, serve, checkout):
    """An open accept_adr for the card's ADR counts as accepted: the runner applies it first."""
    _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_ADR, _REVIEW_PLAN))
    adr = checkout / ".softfield" / "adr" / "20-planning-room.md"
    adr.parent.mkdir(parents=True)
    adr.write_text(ADR_ON_MAIN.format(status="Proposed"))
    client = serve()
    waiting = _review_page(client, "/planning/f6/proposals/plan")
    assert " disabled" in re.search(r'<button type="button" id="approve-plan"[^>]*>', waiting)[0]  # type: ignore[index]
    assert "acceptance is on its way" not in waiting
    _write(
        db_path,
        lambda conn: metrics.add_request(
            conn, planning, "accept_adr", "f6", "20", "2026-10-28T10:00:00+00:00"
        ),
    )
    html = _review_page(client, "/planning/f6/proposals/plan")
    assert " disabled" not in re.search(r'<button type="button" id="approve-plan"[^>]*>', html)[0]  # type: ignore[index]
    assert "ADR 20's acceptance is on its way: the runner applies it first." in html


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


def test_a_merge_shows_like_the_others_and_its_button_approves_the_threads_plan(
    planning, db_path, db, serve
):
    """f6-12: on the desk and its page, its words say "merge F9 into F7"; approving it is the
    thread's ``approve_plan``, which settles it (D6)."""
    _write(db_path, lambda conn: _review(conn, planning, "f9", _REVIEW_MERGE))
    [item] = [i for i in _group(db, "proposals") if i.link.endswith("/merge-f9")]
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
    [item] = [i for i in _group(db, "proposals") if i.link.endswith("/merge-f9")]
    assert item.on_its_way  # on its way until the runner's next pick, no longer waiting on you


def _merges_on_the_desk(db: sqlite3.Connection) -> list[str]:
    return [i.link for i in _group(db, "proposals") if "/merge-" in i.link and not i.on_its_way]


def test_an_approved_merge_leaves_the_desk(planning, db_path, db):
    """2026-10-08: a merge-only approval's result is "approved: merged F9 into F7", which the
    desk didn't count as worked, so every approved merge stayed."""
    _write(db_path, lambda conn: _review(conn, planning, "f9", _REVIEW_MERGE))
    _finished(db_path, planning, "approve_plan", "f9", None, "approved: merged F9 into F7")
    assert _merges_on_the_desk(db) == []


@pytest.mark.parametrize("gone", ["f9", "f7"])
def test_a_merge_whose_card_left_main_asks_nothing(planning, db_path, db, checkout, gone):
    """F9 or F7 was merged elsewhere since the lead proposed it: nothing is left to ask."""
    docs = checkout / ".softfield" / "cards"
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


def _f6_adr_plan_merge(db_path: Path, planning: int, checkout: Path) -> None:
    """F6's thread lists an ADR (Proposed on main), a plan and a merge into it."""
    adr = checkout / ".softfield" / "adr" / "20-planning-room.md"
    adr.parent.mkdir(parents=True)
    adr.write_text(ADR_ON_MAIN.format(status="Proposed"))
    for key in ("f6", "f9"):  # a merge whose cards left main asks nothing
        (checkout / ".softfield" / "cards").mkdir(exist_ok=True)
        (checkout / ".softfield" / "cards" / f"{key}-x.md").write_text(f"# Milestone {key}: x\n")
    merge = {**_REVIEW_MERGE, "into": "f6"}
    _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_PLAN, merge, _REVIEW_ADR))


def _f6_mockup_review(db_path: Path, planning: int, checkout: Path) -> None:
    """F6's thread lists a mock-up proposal whose file is on ``plan/f6``."""
    git(checkout, "checkout", "-q", "-b", "plan/f6")
    for rel, text in (
        (".softfield/cards/f6-mockup/index.html", "<p>the desk</p>"),
        (".softfield/adr/20-planning-room.md", ADR_ON_MAIN.format(status="Proposed")),
    ):
        (checkout / rel).parent.mkdir(parents=True, exist_ok=True)
        (checkout / rel).write_text(text)
    git(checkout, "add", "-A")
    git(checkout, "commit", "-q", "-m", "drafts")
    git(checkout, "checkout", "-q", "main")
    _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_MOCKUP))


def _proposals(db: sqlite3.Connection) -> list[Any]:
    return _group(db, "proposals")


def _counted(db: sqlite3.Connection) -> int:
    """How many of the proposals the desk counts as waiting for the owner."""
    return len([i for i in waiting_for_you(desk(db, PROJECT, NOW)) if i.group == "proposals"])


def test_a_cards_proposals_are_one_desk_item_counted_while_a_part_waits(
    planning, db_path, db, checkout
):
    """F51 D1: ADR first, then plan and merge; the item links to the first part still to do,
    and counts until every part is on its way."""
    _f6_adr_plan_merge(db_path, planning, checkout)
    (item,) = _proposals(db)
    assert item.title == "F6 plan: 7 tickets"  # the plan's title names its card already
    assert item.parts == (("ADR 20", False), ("plan", False), ("merge F9", False))
    assert item.words == "5 key points · accept the ADR first"
    assert item.link == "/planning/f6/proposals/adr-20"
    assert not item.on_its_way
    assert _counted(db) == 1

    _finished(db_path, planning, "accept_adr", "f6", "20", None)
    (item,) = _proposals(db)
    assert item.parts[0] == ("ADR 20", True)
    assert item.words == "5 key points"
    assert item.link == "/planning/f6/proposals/plan"
    assert not item.on_its_way
    assert _counted(db) == 1

    _finished(db_path, planning, "approve_plan", "f6", None, None)
    (item,) = _proposals(db)
    assert item.on_its_way
    assert all(way for _, way in item.parts)
    assert _counted(db) == 0


def test_a_plan_and_its_mockup_are_one_item_and_the_general_seeds_stay_two(planning, db_path, db):
    seeds = [{**_REVIEW_SEED, "id": "seed-1"}, {**_REVIEW_SEED, "id": "seed-2"}]
    _write(db_path, lambda conn: _review(conn, planning, "f7", _REVIEW_PLAN, _REVIEW_MOCKUP))
    _write(db_path, lambda conn: _review(conn, planning, "general", *seeds))
    items = _proposals(db)
    assert [(i.title, i.parts) for i in items if i.link.startswith("/planning/f7/")] == [
        ("F7: F6 plan: 7 tickets", (("plan", False), ("mock-up", False)))  # F7's, named so
    ]
    assert len([i for i in items if i.link.startswith("/planning/general/")]) == 2


def test_a_thread_with_an_open_plan_message_is_not_an_answer_wanted(planning, db_path, db):
    """F51 D4, F74: the owner answered; the lead's reply is on its way, so the thread's one box
    is dashed and no longer waits for them."""
    _lead_says(db_path, planning, "f7", "Which one?")

    def f7() -> list[tuple[str, bool]]:
        return [(i.link, i.on_its_way) for i in _group(db, "answers") if i.link == "/planning/f7"]

    assert f7() == [("/planning/f7", False)]
    _finished(db_path, planning, "plan_message", "f7", "The first.", None)
    assert f7() == [("/planning/f7", True)]


def test_answers_wanted_lists_the_leads_newest_reply_first(planning, db_path, db):
    """F185 D3: by the lead's latest reply, newest first, not by when a thread began; a thread
    the lead still owes a reply comes after every answered one (F84 D4)."""
    _lead_says(db_path, planning, "f7", "Which one?")
    _lead_says(db_path, planning, "f9", "Two developers?")
    _lead_says(db_path, planning, "f7", "Or the second?")
    _finished(db_path, planning, "plan_message", "f1", "And this one?", None)
    links = [i.link for i in _group(db, "answers")]
    shown = ("/planning/f7", "/planning/f9", "/planning/general", "/planning/f1")
    # general's reply is the fixture's, written before the test's
    assert [link for link in links if link in shown] == list(shown)


def test_a_merge_the_lead_applied_asks_nothing(planning, db_path, db, serve):
    """F49 D1: the runner applied it after the job; no Approve, on the desk or its page."""
    applied = {**_REVIEW_MERGE, "applied": True}
    _write(db_path, lambda conn: _review(conn, planning, "f9", applied))
    assert not [i for i in _group(db, "proposals") if i.link.endswith("/merge-f9")]
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
        (".softfield/cards/f6-mockup/index.html", "<p>the desk</p>"),
        (".softfield/cards/f6-planning-room.md", "# F6"),
        (".softfield/adr/20-planning-room.md", ADR_ON_MAIN.format(status="Proposed")),
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
    assert frame and frame[1] == "/planning/mockups/f6/.softfield/cards/f6-mockup/index.html"
    served = client.get(frame[1])
    assert (served.status_code, served.text) == (200, "<p>the desk</p>")
    # Opened on its own, outside the sandboxed frame, it still runs in an origin of its own,
    # so its scripts can't post to /requests as the dashboard (ADR 18 item 3)
    assert served.headers["content-security-policy"] == "sandbox allow-scripts"
    for refused in (
        ".softfield/cards/f6-planning-room.md",
        ".softfield/adr/20-planning-room.md",
        ".softfield/cards/f6-mockup/missing.html",
        ".softfield/cards/f6-mockup/",
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
    mockup = checkout / ".softfield" / "cards" / "f6-mockup" / "index.html"
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
    (checkout / ".softfield/cards/f54-mockup").mkdir(parents=True, exist_ok=True)
    # the mock-up file was never kept: only a placeholder so the branch exists
    (checkout / ".softfield/cards/f54-mockup/.gitkeep").write_text("")
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
    a, b = ".softfield/tasks/ready/f7-01-a.md", ".softfield/tasks/ready/f7-02-b.md"
    for rel, text in ((a, "main's a"), (b, "<b>'s text")):
        (checkout / rel).parent.mkdir(parents=True, exist_ok=True)
        (checkout / rel).write_text(text)
    git(checkout, "add", "-A")
    git(checkout, "commit", "-q", "-m", "tickets")
    git(checkout, "checkout", "-q", "-b", "plan/f7")
    (checkout / a).write_text("the replan's a")
    (checkout / ".softfield/tasks/ready/f7-03-c.md").write_text("the replan's c")
    (checkout / ".softfield/tasks/later").mkdir()
    git(checkout, "mv", b, ".softfield/tasks/later/f7-02-b.md")
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
        (".softfield/tasks/ready/f7-01-a.md", "changed", "the replan's a"),
        (".softfield/tasks/ready/f7-02-b.md", "set aside", "<b>'s text"),
        (".softfield/tasks/ready/f7-03-c.md", "added", "the replan's c"),
    ]
    assert "main's a" not in html and "<b>'s text" not in html  # escaped
    colours = re.findall(r'class="word"[^>]*style="[^"]*--c:\s*var\((--[\w-]+)\)', html)
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
        ".softfield/tasks/ready/f7-01-a.md",
        ".softfield/tasks/ready/f7-02-b.md",
        ".softfield/tasks/ready/f7-03-c.md",
    ]
    assert "resumes the line" not in html


def test_a_plan_that_clashes_with_main_says_what_to_press_instead_of_its_files(
    planning, db_path, serve, checkout
):
    """F139-F1: a clashing branch's diff is everything since it left main (2,137 files)."""
    _replanned(checkout)
    (checkout / ".softfield/tasks/ready/f7-01-a.md").write_text("main's a, changed again")
    git(checkout, "commit", "-q", "-am", "main moves on")
    _write(db_path, lambda conn: _review(conn, planning, "f7", _REVIEW_PLAN))
    html = _review_page(serve(), "/planning/f7/proposals/plan")
    section = html.split('id="plan-changes"', 1)[1].split("</section>", 1)[0]
    assert "plan/f7 clashes with main: press Refresh against main on its page" in _text(section)
    assert 'class="plan-change"' not in section and "softfield " not in section


# --- old-path resolved mockup (f165-01) -------------------------------------------------------


def test_an_old_path_mockup_shows_its_frame_and_serves_its_file(planning, db_path, serve, checkout):
    """A mock-up whose stored path is ``docs/milestones/f67-mockup/review.html`` but the file
    lives at ``.softfield/cards/f67-mockup/review.html`` on the plan branch: the frame's ``src``
    ends in the resolved path, there is no gone block, and the file is served."""
    git(checkout, "checkout", "-q", "-b", "plan/f67")
    (checkout / ".softfield/cards/f67-mockup").mkdir(parents=True, exist_ok=True)
    (checkout / ".softfield/cards/f67-mockup/review.html").write_text("<p>the desk</p>")
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
    assert frame and frame[1].endswith(".softfield/cards/f67-mockup/review.html")
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


def test_a_mockup_link_is_visible_on_a_phone(page, planning, db_path, serve, checkout):
    """At 390 px a mock-up review shows no iframe and an "Open the mock-up" link, at least
    44 px tall, whose href is the mock-up's route and which opens a new tab."""
    _f6_mockup_review(db_path, planning, checkout)
    page.set_viewport_size(PHONE)
    _open(page, serve(), "/planning/f6/proposals/mockup")
    link = page.locator(".mockup-link")
    assert link.is_visible()
    assert link.evaluate("e => e.offsetHeight") >= 44
    href = link.get_attribute("href")
    assert href and "/planning/mockups/f6/.softfield/cards/f6-mockup/index.html" in href
    assert link.get_attribute("target") == "_blank"
    assert link.get_attribute("rel") == "noopener"


# --- Set aside, Refresh and the stale note (F73 D2, D4, D6) ----------------------------------


def _asked(db_path: Path, planning: int) -> list[tuple[str, str, str]]:
    conn = metrics.open_db(db_path)
    try:
        rows = conn.execute("SELECT * FROM owner_requests WHERE project_id = ?", (planning,))
        return [(r["kind"], r["subject"], r["value"]) for r in rows]
    finally:
        conn.close()


def test_an_open_plan_has_set_aside_and_refresh_posting_their_requests(planning, db_path, serve):
    """Set aside posts the thread's ``archive`` (the whole conversation, D2); Refresh posts
    Send back on the proposal with the fixed words and no comments (D6)."""
    _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_ADR, _REVIEW_PLAN))
    html = _review_page(serve(), "/planning/f6/proposals/plan")
    assert _posts(html, "set-aside-button") == {
        "kind": "archive",
        "project": PROJECT,
        "subject": "f6",
        "value": "on",
    }
    refresh = _posts(html, "refresh-button")
    assert {k: v for k, v in refresh.items() if k != "value"} == {
        "kind": "send_back",
        "project": PROJECT,
        "subject": "f6/plan",
    }
    assert json.loads(refresh["value"]) == {"text": REFRESH, "comments": {}}
    assert "It leaves your desk with its drafts kept." in _text(html)


def test_an_adr_has_set_aside_but_no_refresh_and_a_merge_neither_refresh(planning, db_path, serve):
    _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_ADR, _REVIEW_PLAN))
    _write(db_path, lambda conn: _review(conn, planning, "f9", _REVIEW_MERGE))
    client = serve()
    adr = _review_page(client, "/planning/f6/proposals/adr-20")
    assert 'id="set-aside-button"' in adr and 'id="refresh-button"' not in adr
    merge = _review_page(client, "/planning/f9/proposals/merge-f9")
    assert 'id="refresh-button"' not in merge


def test_an_approved_plan_and_an_archived_thread_have_no_set_aside(planning, db_path, serve):
    _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_ADR, _REVIEW_PLAN))
    client = serve()
    assert 'id="set-aside-button"' in _review_page(client, "/planning/f6/proposals/plan")
    _finished(db_path, planning, "approve_plan", "f6", None, "approved: 2 tickets queued")
    approved = _review_page(client, "/planning/f6/proposals/plan")
    assert 'id="settled"' in approved  # the plan's own state, not a page that failed to show
    assert 'id="set-aside-button"' not in approved

    _write(db_path, lambda conn: _review(conn, planning, "f9", _REVIEW_MERGE))
    assert 'id="set-aside-button"' in _review_page(client, "/planning/f9/proposals/merge-f9")

    def archive(conn: sqlite3.Connection) -> None:
        found = metrics.planner_thread(conn, planning, "f9", NOW.isoformat())["id"]
        metrics.set_thread_archived(conn, found, NOW.isoformat(), "by you")

    _write(db_path, archive)
    archived = _review_page(client, "/planning/f9/proposals/merge-f9")
    assert 'id="approve-merge"' in archived  # still open: only the Set aside button goes
    assert 'id="set-aside-button"' not in archived


def test_a_set_aside_on_its_way_shows_after_a_reload(planning, db_path, serve):
    """Pressed, then the page opened again before the runner's pick: on its way, no buttons."""
    _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_ADR, _REVIEW_PLAN))
    client = serve()
    assert 'id="setting-aside"' not in _review_page(client, "/planning/f6/proposals/plan")
    _write(
        db_path,
        lambda conn: metrics.add_request(conn, planning, "archive", "f6", "on", NOW.isoformat()),
    )
    html = _review_page(client, "/planning/f6/proposals/plan")
    assert "Setting aside at the runner's next pick" in _text(html)
    assert 'id="set-aside-button"' not in html and 'id="refresh-button"' not in html


def _drafted(db_path: Path, days: int) -> None:
    """The lead's last message on F6, ``days`` days before ``NOW``."""

    def write(conn: sqlite3.Connection) -> None:
        conn.execute(
            "UPDATE planner_messages SET at = ? WHERE id = (SELECT MAX(id) FROM planner_messages"
            " WHERE author = 'lead')",
            ((NOW - timedelta(days=days)).isoformat(),),
        )

    _write(db_path, write)


def test_a_plan_drafted_five_days_ago_says_so_and_one_from_today_doesnt(planning, db_path, serve):
    _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_ADR, _REVIEW_PLAN))
    client = serve()
    stale = "Refresh it before approving."
    assert stale not in _review_page(client, "/planning/f6/proposals/plan")
    _drafted(db_path, 2)
    assert stale not in _review_page(client, "/planning/f6/proposals/plan")
    _drafted(db_path, 5)
    html = _review_page(client, "/planning/f6/proposals/plan")
    assert "Drafted 5 days ago: the code may have moved. Refresh it before approving." in _text(
        html
    )


def test_set_aside_posts_one_archive_and_cant_be_pressed_again(page, planning, db_path, serve):
    _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_ADR, _REVIEW_PLAN))
    _open(page, serve(), "/planning/f6/proposals/plan")
    page.click("#set-aside-button")
    page.wait_for_selector("#review-status >> text=Asked")
    assert "on-its-way" in (page.locator("#actions").get_attribute("class") or "")
    button = page.locator("#set-aside-button")
    assert button.is_disabled() and not button.is_visible()
    assert _asked(db_path, planning) == [("archive", "f6", "on")]


def test_refresh_posts_one_send_back_with_the_fixed_words(page, planning, db_path, serve):
    _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_ADR, _REVIEW_PLAN))
    _open(page, serve(), "/planning/f6/proposals/plan")
    page.click("#refresh-button")
    page.wait_for_selector("#review-status >> text=Asked")
    assert not page.locator("#refresh-button").is_visible()
    [(kind, subject, value)] = _asked(db_path, planning)
    assert (kind, subject, json.loads(value)) == (
        "send_back",
        "f6/plan",
        {"text": REFRESH, "comments": {}},
    )


def test_on_a_phone_set_aside_is_a_thumbs_target_inside_the_page(page, planning, db_path, serve):
    _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_ADR, _REVIEW_PLAN))
    page.set_viewport_size(PHONE)
    _open(page, serve(), "/planning/f6/proposals/plan")
    for button in ("#set-aside-button", "#refresh-button"):
        box = page.locator(button).bounding_box()
        assert box, button
        assert box["height"] >= 44, button
        assert box["x"] >= 0 and box["x"] + box["width"] <= PHONE["width"], button


def test_the_mockup_iframe_shows_at_display(page, planning, db_path, serve, checkout):
    """At 1024 px the iframe shows, at least 480 px tall, with the same link."""
    _f6_mockup_review(db_path, planning, checkout)
    page.set_viewport_size({"width": 1024, "height": 768})
    _open(page, serve(), "/planning/f6/proposals/mockup")
    iframe = page.locator("#mockup")
    assert iframe.is_visible()
    height = iframe.evaluate("e => e.offsetHeight")
    assert height >= 480
    link = page.locator(".mockup-link")
    assert link.is_visible()


# --- old ADR paths (f196-01) --------------------------------------------------------------------


def test_old_path_adr_shows_accept_adr_when_file_exists_on_main(planning, db_path, serve, checkout):
    """A proposal whose stored path is ``docs/adr/27-the-lead-acts-when-asked.md`` and that file
    exists on main: Accept ADR posts its number."""
    adr = checkout / "docs" / "adr" / "27-the-lead-acts-when-asked.md"
    adr.parent.mkdir(parents=True)
    adr.write_text(ADR_ON_MAIN.format(status="Proposed"))
    old_adr = {
        "id": "adr-27",
        "kind": "adr",
        "title": "ADR 27: the lead acts when asked",
        "path": "docs/adr/27-the-lead-acts-when-asked.md",
        "key_points": [],
    }
    _write(db_path, lambda conn: _review(conn, planning, "f58", old_adr))
    html = _review_page(serve(), "/planning/f58/proposals/adr-27")
    assert _posts(html, "accept-adr") == {
        "kind": "accept_adr",
        "project": PROJECT,
        "subject": "f58",
        "value": "27",
    }


def test_old_path_adr_shows_no_accept_adr_when_file_missing_on_main(
    planning, db_path, serve, checkout
):
    """A proposal whose stored path is ``docs/adr/27-planning-beside-the-line.md`` but that file
    does not exist on main: no Accept ADR; Send back and Reject stay."""
    # Another ADR of number 27 exists on main, but not the one named in the proposal
    other = checkout / "docs" / "adr" / "27-another-adr.md"
    other.parent.mkdir(parents=True)
    other.write_text(ADR_ON_MAIN.format(status="Accepted"))
    old_adr = {
        "id": "adr-27",
        "kind": "adr",
        "title": "ADR 27: planning beside the line",
        "path": "docs/adr/27-planning-beside-the-line.md",
        "key_points": [],
    }
    _write(db_path, lambda conn: _review(conn, planning, "f27", old_adr))
    client = serve()
    html = _review_page(client, "/planning/f27/proposals/adr-27")
    assert 'id="accept-adr"' not in html
    assert 'id="send-back"' in html
    assert 'id="reject"' in html


# --- "In short" plate on the proposal page (F207) ----------------------------------------------


_TLDR = "Approving queues seven tickets: the desk first, then the threads."


def test_a_proposal_with_tldr_shows_the_plate_under_the_header(planning, db_path, serve):
    """F207 D5: a proposal with a ``tldr`` shows it in the In short plate right under the
    page's header, before the key points; the other proposal, without one, has no plate."""
    plan = {**_REVIEW_PLAN, "tldr": _TLDR}
    _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_ADR, plan))
    client = serve()
    html = _review_page(client, "/planning/f6/proposals/plan")
    [plate] = re.findall(r'<div class="in-short">(.*?)</div>', html, re.S)
    assert _text(plate) == f"In short {_TLDR}"
    after_header = html.split('<header class="card-head"', 1)[1].split("</header>", 1)[1]
    assert after_header.lstrip().startswith('<div class="in-short">')
    assert after_header.index("in-short") < after_header.index("Desk first")
    assert "in-short" not in _review_page(client, "/planning/f6/proposals/adr-20")


def test_a_mockups_plate_sits_above_its_frame(planning, db_path, serve, checkout):
    """F207 D5: on a mock-up's review the plate comes before the frame and its link."""
    _f6_mockup_review(db_path, planning, checkout)
    mockup = {**_REVIEW_MOCKUP, "tldr": "The desk, with the threads under it."}
    _write(db_path, lambda conn: _review(conn, planning, "f6", mockup))
    html = _review_page(serve(), "/planning/f6/proposals/mockup")
    assert 'id="mockup"' in html
    plate = html.index('<div class="in-short">')
    assert plate < html.index('class="mockup-link"') < html.index('<iframe id="mockup"')
    assert "The desk, with the threads under it." in html[plate : html.index('<iframe id="')]


def test_the_proposal_plate_stays_in_place_on_a_phone(page, planning, db_path, serve):
    """F207: on a phone (390 px) the plate stays in place while ▶ steps through the key
    points."""
    adr = {**_REVIEW_ADR, "tldr": _TLDR}
    _write(db_path, lambda conn: _review(conn, planning, "f6", adr))
    page.set_viewport_size(PHONE)
    _open(page, serve(), "/planning/f6/proposals/adr-20")
    plate = page.locator(".in-short")
    assert plate.inner_text().split() == f"IN SHORT {_TLDR}".split()
    before = plate.bounding_box()
    assert before and before["x"] >= 0 and before["x"] + before["width"] <= PHONE["width"]
    shown = page.locator(".key-point:visible")
    first = shown.inner_text()
    page.locator(".deck-arrows button").all()[1].click()
    assert shown.count() == 1 and shown.inner_text() != first
    assert plate.is_visible() and plate.bounding_box() == before
