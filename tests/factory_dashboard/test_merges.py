"""Merge links (f109-01): a merged card's links both ways, "merged on", and a message's paths as
links. The helpers shared with the desk and the thread page stay in ``test_planning``."""

import re
from datetime import timedelta

from runner import metrics
from tests.factory_dashboard.conftest import _at
from tests.factory_dashboard.test_planning import _finished, _review, _write


def test_a_merge_whose_card_left_main_shows_both_ways(planning, db_path, serve, checkout):
    """F107 merged into F95: /planning/f107 shows 'Merged into F95, <F95's title>' linking
    to F95, and /planning/f95 shows 'Merged here: F107, <F107's title>' linking to F107. The
    merged card's h2 shows the heading's title, not its bare key."""
    from runner import planner

    docs = checkout / ".softfield" / "cards"
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

    docs = checkout / ".softfield" / "cards"
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
    from factory_dashboard.merges import _merge_links
    from runner import planner

    docs = checkout / ".softfield" / "cards"
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

    docs = checkout / ".softfield" / "cards"
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

    docs = checkout / ".softfield" / "cards"
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

    docs = checkout / ".softfield" / "cards"
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

    docs = checkout / ".softfield" / "cards"
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

    docs = checkout / ".softfield" / "cards"
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

    docs = checkout / ".softfield" / "cards"
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

    docs = checkout / ".softfield" / "cards"
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

    docs = checkout / ".softfield" / "cards"
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

    docs = checkout / ".softfield" / "cards"
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

    docs = checkout / ".softfield" / "cards"
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

    docs = checkout / ".softfield" / "cards"
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
