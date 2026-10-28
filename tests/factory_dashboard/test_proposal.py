"""The proposal review page and the mock-up route (f6-08, f165-01):
``/planning/{thread}/proposals/{id}`` and ``/planning/mockups/...``. The helpers shared with the
desk and the thread page stay in ``test_planning``."""

import json
import re
import sqlite3
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
    _lead_says,
    _open,
    _posts,
    _review,
    _review_page,
    _text,
    _write,
)
from tests.runner.conftest import git

ORIGIN = "http://127.0.0.1:8765"
STATIC = Path(__file__).parents[2] / "factory_dashboard" / "static"

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
    adr = checkout / ".factory" / "adr" / "20-planning-room.md"
    adr.parent.mkdir(parents=True)
    adr.write_text(ADR_ON_MAIN.format(status="Proposed"))
    assert " disabled" in approve()
    adr.write_text(ADR_ON_MAIN.format(status="Accepted"))
    assert " disabled" not in approve()


def test_an_open_accept_adr_enables_approve_plan_and_says_so(planning, db_path, serve, checkout):
    """An open accept_adr for the card's ADR counts as accepted: the runner applies it first."""
    _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_ADR, _REVIEW_PLAN))
    adr = checkout / ".factory" / "adr" / "20-planning-room.md"
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


def _f6_adr_plan_merge(db_path: Path, planning: int, checkout: Path) -> None:
    """F6's thread lists an ADR (Proposed on main), a plan and a merge into it."""
    adr = checkout / ".factory" / "adr" / "20-planning-room.md"
    adr.parent.mkdir(parents=True)
    adr.write_text(ADR_ON_MAIN.format(status="Proposed"))
    for key in ("f6", "f9"):  # a merge whose cards left main asks nothing
        (checkout / ".factory" / "cards").mkdir(exist_ok=True)
        (checkout / ".factory" / "cards" / f"{key}-x.md").write_text(f"# Milestone {key}: x\n")
    merge = {**_REVIEW_MERGE, "into": "f6"}
    _write(db_path, lambda conn: _review(conn, planning, "f6", _REVIEW_PLAN, merge, _REVIEW_ADR))


def _proposals(db: sqlite3.Connection) -> list[Any]:
    return desk(db, PROJECT, NOW)[3].items


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
    """F51 D4: the owner answered; the lead's reply is Coming, not on the desk."""
    _lead_says(db_path, planning, "f7", "Which one?")
    assert "/planning/f7" in [i.link for i in desk(db, PROJECT, NOW)[2].items]
    _finished(db_path, planning, "plan_message", "f7", "The first.", None)
    assert "/planning/f7" not in [i.link for i in desk(db, PROJECT, NOW)[2].items]


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
