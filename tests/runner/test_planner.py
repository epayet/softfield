"""The planning room's threads and replies (ADR 20 items 3 and 4, f6 D1–D3)."""

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest

from runner import claude, loop, metrics, milestone, planner
from runner.gitops import Git, GitError
from runner.state import State
from runner.tasks import milestone_key
from tests.runner.conftest import git, write_task
from tests.runner.test_requests import (
    NOW,
    _apply,
    _ask,
    _card,
    _db,
    _duplicates,
    _main_unchanged,
    _plan,
    _request,
    _ticket,
)

POINTS = [
    {"n": 1, "title": "The switch", "answer": "Keep one per window.", "action": "Nothing"},
    {"n": 2, "title": "The queue", "answer": "Planner jobs go first.", "action": "A ticket"},
]
PROPOSAL = {
    "id": "adr-23",
    "kind": "adr",
    "title": "Parallel planners",
    "path": ".factory/adr/23-parallel-planners.md",
    "key_points": [{"n": 1, "title": "Two at once", "text": "Beside developers.", "flag": None}],
}


def _reply(block: object, before: str = "Here is my answer.", after: str = "") -> str:
    return f"{before}\n\n```json\n{json.dumps(block)}\n```\n{after}"


def test_a_reply_block_gives_its_points_and_proposals_and_the_text_around_it():
    reply = planner.parse_reply(
        _reply({"points": POINTS, "proposals": [PROPOSAL]}, after="Over to you.")
    )
    assert reply.points == tuple(POINTS)
    assert reply.proposals == (PROPOSAL,)
    assert reply.text == "Here is my answer.\n\nOver to you."
    assert reply.note is None


@pytest.mark.parametrize(
    ("doc", "expected"),
    [
        (
            "# F7\n\n> **State:** planning · **Priority:** 3\n\n## Outcome\n- **State:** idea\n",
            "# F7\n\n> **State:** ready · **Priority:** 3\n\n## Outcome\n- **State:** idea\n",
        ),
        ("# F7\n\n> **State:** idea\n", "# F7\n\n> **State:** ready\n"),
        ("# F7\n\nSome words.\n", "# F7\n\n> **State:** ready\n\nSome words.\n"),
    ],
)
def test_a_cards_state_is_set_to_ready_in_its_header_only(doc, expected):
    assert planner.ready_card(doc) == expected


@pytest.mark.parametrize(
    ("text", "adrs"),
    [
        ("Build on `.factory/adr/23-parallel-planners.md` items 2-3.", {23}),
        ("As ADR 7 item 2 and ADR 20 say.", {7, 20}),
        ("Read .factory/adr/README.md and the address 23-a.", set()),
    ],
)
def test_the_adrs_a_ticket_relies_on_are_the_ones_it_names(text, adrs):
    assert planner.named_adrs(text) == adrs


PAGE = ".factory/cards/f9-mockup/a.html"
PLAN = {**PROPOSAL, "id": "plan-9", "kind": "plan", "path": ".factory/cards/f9-x.md"}


def test_a_mockup_the_reply_did_not_list_is_listed_by_the_runner():
    reply = planner.parse_reply(_reply({"points": POINTS, "proposals": [PLAN]}))
    listed = planner.with_mockups(reply, {PAGE: "<html><title> The  board\n</title></html>"})
    assert listed.proposals[0] == PLAN
    mockup = listed.proposals[1]
    assert (mockup["kind"], mockup["path"], mockup["id"]) == ("mockup", PAGE, "a-mockup")
    assert mockup["title"] == "The board"
    assert mockup["key_points"][0]["title"] == "Listed by the runner"
    assert len(listed.proposals) == 2


def test_a_mockup_without_a_title_is_named_by_its_file_and_a_blockless_reply_gets_it():
    listed = planner.with_mockups(planner.parse_reply("All text."), {PAGE: "<html></html>"})
    assert listed.note is not None
    assert [(p["path"], p["title"]) for p in listed.proposals] == [(PAGE, "a.html")]


def test_a_mockup_a_proposal_names_is_not_listed_twice():
    own = {**PLAN, "kind": "mockup", "path": PAGE}
    reply = planner.parse_reply(_reply({"points": POINTS, "proposals": [own]}))
    assert planner.with_mockups(reply, {PAGE: "<title>T</title>"}).proposals == (own,)


@pytest.mark.parametrize(
    "path",
    [".factory/cards/f9-mockup/a.css", ".factory/cards/f9/a.html", "docs/a.html"],
)
def test_only_mockup_pages_are_listed(path):
    reply = planner.parse_reply(_reply({"points": POINTS}))
    assert planner.with_mockups(reply, {path: "x"}).proposals == ()


def test_a_reply_without_proposals_has_none():
    reply = planner.parse_reply(_reply({"points": POINTS}))
    assert reply.points == tuple(POINTS) and reply.proposals == ()


def test_the_last_json_block_is_the_reply_block():
    """A reply may quote JSON in its text; the block it ends with is the one read."""
    text = 'An example:\n```json\n{"a": 1}\n```\n' + _reply({"points": POINTS}, before="")
    reply = planner.parse_reply(text)
    assert reply.points == tuple(POINTS) and reply.note is None
    assert '{"a": 1}' in reply.text


@pytest.mark.parametrize(
    ("text", "why"),
    [
        ("Just words, no block.", "no json block"),
        ("```json\n{not json}\n```", "not JSON"),
        (_reply([1, 2]), "an object"),
        (_reply({"proposals": []}), "points"),
        (_reply({"points": [{"n": 1, "title": "t", "answer": "a"}]}), "action"),
        (_reply({"points": [{**POINTS[0], "n": "1"}]}), "n"),
        (_reply({"points": [POINTS[0], POINTS[0]]}), "twice"),
        (_reply({"points": POINTS, "proposals": [{**PROPOSAL, "kind": "essay"}]}), "kind"),
        (_reply({"points": POINTS, "proposals": [{**PROPOSAL, "key_points": "x"}]}), "key_points"),
    ],
)
def test_a_broken_block_leaves_the_whole_reply_as_text_with_a_note(text, why):
    reply = planner.parse_reply(text)
    assert reply.points == () and reply.proposals == ()
    assert reply.text == text.strip()
    assert reply.note is not None and why in reply.note


# --- a point's outcome and the card's title (F31 D4, D7) -------------------------------------


def _point(n: int, **more: object) -> dict[str, Any]:
    return {"n": n, "title": f"Point {n}", "answer": "So.", "action": "Nothing", **more}


def test_a_block_whose_points_carry_each_outcome_is_read():
    """D4: every outcome, and a point that leads to a proposal names it by its id."""
    points = [_point(n, outcome=outcome) for n, outcome in enumerate(planner.OUTCOMES, 1)]
    points.append(_point(8, outcome="adr", proposal="adr-23"))
    reply = planner.parse_reply(_reply({"points": points, "proposals": [PROPOSAL]}))
    assert reply.note is None and reply.points == tuple(points)
    assert [p["outcome"] for p in reply.points[:7]] == [
        "info",
        "ticket",
        "adr",
        "mockup",
        "roadmap",
        "merge",
        "question",
    ]
    assert reply.points[7]["proposal"] == "adr-23"


@pytest.mark.parametrize(
    ("more", "why"),
    [
        ({"outcome": "essay"}, "point 1's outcome is one of info, ticket"),
        ({"outcome": ["adr"]}, "point 1's outcome"),
        ({"outcome": ""}, "point 1's outcome"),
        ({"outcome": "adr", "proposal": "adr-99"}, "point 1's proposal is an id in this block"),
        ({"proposal": ["adr-23"]}, "point 1's proposal"),
        ({"proposal": "Parallel planners"}, "point 1's proposal"),  # its title is not its id
    ],
)
def test_an_unknown_outcome_or_a_proposal_not_in_the_block_leaves_it_unread(more, why):
    text = _reply({"points": [_point(1, **more)], "proposals": [PROPOSAL]})
    reply = planner.parse_reply(text)
    assert reply.points == () and reply.proposals == () and reply.title is None
    assert reply.text == text.strip()
    assert reply.note is not None and why in reply.note


def test_a_proposal_named_with_no_proposals_in_the_block_leaves_it_unread():
    reply = planner.parse_reply(_reply({"points": [_point(1, proposal="adr-23")]}))
    assert reply.points == () and reply.note is not None and "adr-23" in reply.note


def test_a_null_outcome_or_proposal_reads_as_a_point_without_one():
    """A point without an outcome shows as today (D4), so a null is no outcome at all."""
    block = {"points": [_point(1, outcome=None, proposal=None), _point(2, outcome="info")]}
    reply = planner.parse_reply(_reply(block))
    assert reply.note is None
    assert reply.points == (_point(1), _point(2, outcome="info"))


def test_a_reply_without_a_title_or_outcomes_reads_as_before():
    reply = planner.parse_reply(_reply({"points": POINTS, "proposals": [PROPOSAL]}))
    assert reply == planner.Reply("Here is my answer.", tuple(POINTS), (PROPOSAL,))
    assert reply.title is None and reply.ignored is None
    assert not [p for p in reply.points if "outcome" in p or "proposal" in p]


@pytest.mark.parametrize("given", ["Archive at the bottom", "  Archive at the bottom \n"])
def test_a_blocks_title_is_the_replys(given):
    reply = planner.parse_reply(_reply({"points": POINTS, "title": given}))
    assert reply.title == "Archive at the bottom" and reply.ignored is None
    assert reply.note is None and reply.points == tuple(POINTS)


@pytest.mark.parametrize(
    ("given", "why"),
    [
        ("x" * 81, "at most 80 characters"),
        ("Archive\nat the bottom", "one line"),
        ("Archive\rat the bottom", "one line"),
        ("Archive\u2028at the bottom", "one line"),
        (7, "not text"),
        (["Archive"], "not text"),
    ],
)
def test_a_title_too_long_or_on_two_lines_is_ignored_with_a_note_and_the_block_is_read(given, why):
    reply = planner.parse_reply(_reply({"points": POINTS, "title": given}))
    assert reply.title is None
    assert reply.ignored is not None and why in reply.ignored
    assert reply.note is None and reply.points == tuple(POINTS)  # the block is still read


@pytest.mark.parametrize("given", [None, "", "  "])
def test_an_empty_title_is_no_title(given):
    reply = planner.parse_reply(_reply({"points": POINTS, "title": given}))
    assert (reply.title, reply.ignored, reply.note) == (None, None, None)


def test_a_title_of_80_characters_is_kept():
    reply = planner.parse_reply(_reply({"points": POINTS, "title": "x" * 80}))
    assert reply.title == "x" * 80


SEED_DOC = (
    "# Milestone F32: when i click on approve plan it looks…\n\n"
    "> **State:** idea · **Priority:** 100 · **Area:** factory\n"
    "> Planted by the owner on 2026-10-08.\n\n"
    "## Notes\n# Milestone F32: not this line\nwhen i click on approve plan\n"
)


def test_naming_a_card_rewrites_its_heading_and_nothing_else():
    """D7: the heading is the only line that changes; the key in it stays."""
    named = planner.named_card(SEED_DOC, "Proposals close the loop")
    assert named is not None
    first, rest = named.split("\n", 1)
    assert first == "# Milestone F32: Proposals close the loop"
    assert rest == SEED_DOC.split("\n", 1)[1]
    # Text a regex would read as a group or an escape is the title as written
    literal = planner.named_card(SEED_DOC, r"A \1 and \g<0>")
    assert literal is not None and literal.startswith("# Milestone F32: A \\1 and \\g<0>\n")


@pytest.mark.parametrize(
    "doc", ["", "Some words.\n# Milestone F32: later\n", "# F32\n", "## Milestone F32: x\n"]
)
def test_a_doc_whose_first_line_is_no_card_heading_is_not_named(doc):
    assert planner.named_card(doc, "A title") is None


# --- a `merge`: one card repeats another (f6-12, D2) ----------------------------------------------

MERGE = {
    "id": "merge-f12",
    "kind": "merge",
    "title": "One queue, said twice",
    "path": ".factory/cards/f12-queue-once.md",
    "into": "f10",
    "key_points": [{"n": 1, "title": "Notes", "text": "F12's notes go to F10.", "flag": False}],
}
CARDS = {"f10", "f12", "m4"}


def test_a_merge_proposal_names_the_duplicates_doc_and_the_card_it_joins():
    reply = planner.parse_reply(_reply({"points": POINTS, "proposals": [MERGE]}), CARDS)
    assert reply.note is None and reply.proposals == (MERGE,)
    assert planner.merge_cards(MERGE) == ("f12", "f10")
    assert planner.merge_words(MERGE) == "merge F12 into F10"


@pytest.mark.parametrize(
    ("change", "why"),
    [
        ({"into": None}, "into"),
        ({"into": "f99"}, "f99 is no card"),
        ({"into": "general"}, "into"),
        ({"into": "f12"}, "into itself"),
        ({"path": ".factory/cards/f99-gone.md"}, "f99 is no card"),
        ({"path": ".factory/adr/23-x.md"}, "a card's doc"),
        ({"path": ".factory/cards/../adr/f12-x.md"}, "a card's doc"),
        ({"path": None}, "a card's doc"),
    ],
)
def test_a_merge_without_into_or_with_an_unknown_card_is_refused(change, why):
    proposal = {key: value for key, value in {**MERGE, **change}.items() if value is not None}
    reply = planner.parse_reply(_reply({"points": POINTS, "proposals": [proposal]}), CARDS)
    assert reply.proposals == ()
    assert reply.note is not None and why in reply.note


def test_without_the_cards_no_merge_is_read():
    """A caller that doesn't say which cards exist gets every merge refused, never guessed."""
    assert planner.parse_reply(_reply({"points": POINTS, "proposals": [MERGE]})).note


@pytest.mark.parametrize("summary", [3, ["Asked why."], {"text": "x"}])
def test_a_merges_summary_that_isnt_text_leaves_the_block_unread(summary):
    """F49 D3: the lead's summary of the duplicate's thread is text, or nothing."""
    proposal = {**MERGE, "summary": summary}
    reply = planner.parse_reply(_reply({"points": POINTS, "proposals": [proposal]}), CARDS)
    assert reply.proposals == () and reply.points == ()
    assert reply.note is not None and "merge-f12's summary is not text" in reply.note


def test_a_merges_summary_is_read_with_it():
    proposal = {**MERGE, "summary": "Asked why. Answered: one queue."}
    reply = planner.parse_reply(_reply({"points": POINTS, "proposals": [proposal]}), CARDS)
    assert reply.note is None and reply.proposals == (proposal,)


KEPT_DOC = "# Milestone F10: one queue\n\n> **State:** idea\n\n## Notes\nOne queue for all.\n"
SOURCE = "From F12: queue once (merged by the lead on 2026-10-01)"


def test_the_kept_card_holds_the_duplicates_notes_then_what_was_said_on_its_thread():
    """F49 D3: the owner's words as they were, then the lead's summary under its heading."""
    doc = planner.merged_card(KEPT_DOC, "A single line.", SOURCE, summary="Asked why.\nOpen: when.")
    assert doc == (
        f"{KEPT_DOC}\n### {SOURCE}\nA single line.\n\n"
        "What was said on F12's thread:\nAsked why.\nOpen: when.\n"
    )
    assert planner.merged_card(KEPT_DOC, "A single line.", SOURCE) == (
        f"{KEPT_DOC}\n### {SOURCE}\nA single line.\n"
    )


def test_a_summary_cant_sign_the_card_off_or_make_a_heading_of_its_own():
    """The lead writes the summary: a quoted line could sign the card off, and a heading could
    pass for another merge's (``merged_keys``) or a section of the card."""
    said = "> **Status: done.**\n## Done when\n### From F99: x (merged by the lead on 2026-10-01)"
    doc = planner.merged_card(KEPT_DOC, "A single line.", SOURCE, summary=said)
    assert doc.endswith(
        "What was said on F12's thread:\n\\> **Status: done.**\n\\## Done when\n"
        "\\### From F99: x (merged by the lead on 2026-10-01)\n"
    )
    assert planner.merged_keys(doc) == ["f12"]
    assert milestone.card("f10-one-queue", doc).state == "idea"


def test_the_cards_are_the_milestone_docs_short_keys(tmp_path):
    docs = tmp_path / ".factory" / "cards"
    (docs / "f6-mockup").mkdir(parents=True)
    for name in ("f6-planning-room", "m4", "bugs", "README"):
        (docs / f"{name}.md").write_text("# x\n")
    assert planner.cards(tmp_path) == {"f6", "m4"}


def test_a_stored_reply_says_when_its_points_couldnt_be_read():
    broken = planner.parse_reply("No block here.")
    assert planner.stored_text(broken).startswith("No block here.\n\n")
    assert broken.note is not None and broken.note in planner.stored_text(broken)
    good = planner.parse_reply(_reply({"points": POINTS}))
    assert planner.stored_text(good) == good.text


@pytest.mark.parametrize(
    ("subject", "thread"),
    [("f7", "f7"), ("f6-planning-room", "f6"), ("general", "general"), ("m4", "m4")],
)
def test_a_thread_is_a_cards_short_key_or_general(subject, thread):
    assert planner.thread_key(subject) == thread


@pytest.mark.parametrize("subject", [None, "", "../etc", "f7/x", "bugs", "F7", "f7#2", "x" * 99])
def test_anything_else_is_no_thread(subject):
    with pytest.raises(planner.PlannerError):
        planner.thread_key(subject)


def test_a_rows_subject_names_its_thread_and_request():
    subject = planner.row_subject("f7", 41)
    assert subject == "f7#41"
    assert planner.request_of(subject) == ("f7", 41)
    assert planner.thread_name("f7") == "F7"
    assert planner.thread_name("general") == "the general thread"


def test_a_message_is_its_text_and_its_comments_by_point():
    value = json.dumps({"text": "Go on.", "comments": {"2": "Why first?"}})
    assert planner.message(value) == ("Go on.", {2: "Why first?"})
    assert planner.message(json.dumps({"text": "Only words."})) == ("Only words.", {})


@pytest.mark.parametrize(
    "value",
    [
        None,
        "not json",
        json.dumps(["Go on."]),
        json.dumps({"text": 3}),
        json.dumps({"text": "", "comments": {}}),
        json.dumps({"text": "x", "comments": {"two": "?"}}),
        json.dumps({"text": "x", "comments": {"2": 5}}),
    ],
)
def test_a_message_without_words_or_with_bad_comments_is_refused(value):
    with pytest.raises(planner.PlannerError):
        planner.message(value)


def test_the_prompt_carries_the_message_and_the_comments_by_point():
    prompt = planner.prompt("f7", "Go on.", {2: "Why first?"})
    assert "Go on." in prompt and "Why first?" in prompt and "F7" in prompt
    assert "```json" in prompt and '"points"' in prompt
    assert "point 2" in prompt


def test_a_job_with_no_session_reads_what_was_said_on_its_thread_before():
    """Lead replies written outside a job (2026-10-07) have no session to resume: the next
    job's prompt carries them, the lead's points with them."""
    said: list[dict[str, Any]] = [
        {"author": "owner", "text": "When is the board?", "points": None},
        {"author": "lead", "text": "After F5's replan.", "points": json.dumps(POINTS)},
        {"author": "owner", "text": "Fine.", "points": json.dumps([{"n": 2, "comment": "Why?"}])},
    ]
    earlier = planner.history(said)
    assert earlier.index("The owner:\nWhen is the board?") < earlier.index("You (the lead):")
    assert "2. The queue: Planner jobs go first. (A ticket)" in earlier
    assert "On point 2: Why?" in earlier
    prompt = planner.prompt("f7", "Go on.", {}, earlier=earlier)
    assert earlier in prompt and prompt.index("When is the board?") < prompt.index("Go on.")
    assert planner.history([]) == ""


def test_a_look_is_the_runners_message_by_its_own_subject():
    """ADR 29 item 1: a look's row names the runner's message (``f7#m12``), never a request,
    and its history and its export say it was the runner's."""
    subject = planner.look_subject("f7", 12)
    assert subject == "f7#m12" and planner.look_of(subject) == ("f7", 12)
    assert planner.look_of(planner.row_subject("f7", 12)) is None  # an owner's message
    with pytest.raises(planner.PlannerError):
        planner.request_of(subject)
    text = planner.look_text("f7-02-x", "check-all failed", "task/f7-02-x", ".factory/var/runs/r")
    assert "f7-02-x blocked: check-all failed." in text and "task/f7-02-x" in text
    assert ".factory/var/runs/r" in text and "replan" in text
    assert "left no branch" in planner.look_text("f7-02-x", "why", None, "logs")
    said = [{"author": "runner", "text": text, "points": None, "proposals": None}]
    assert planner.history(said).startswith(
        "\nWhat was said on this thread before, oldest first:\n\nThe runner:\n"
    )
    assert (
        planner.export("F7", None, [{**said[0], "at": "2026-10-21T10:00:00"}]).count(
            "## The runner, 2026-10-21 10:00"
        )
        == 1
    )


def test_a_looks_prompt_says_what_a_look_is_and_a_message_doesnt():
    looked = planner.prompt("f7", "f7-02-x blocked.", {}, blocked=True)
    assert "the runner's, not the owner's" in looked and "`replan`" in looked
    assert "the runner's, not the owner's" not in planner.prompt("f7", "Go on.", {})


def test_a_planners_prompt_says_a_replan_brings_back_its_cards_blocked_tickets():
    """ADR 29 item 3: written at the new path, the blocked copy left for the runner."""
    said = planner.prompt("f7", "Go on.", {})
    assert ".factory/tasks/blocked/f7-*.md" in said
    assert "removes the blocked copy when the owner approves" in said
    assert planner.drafts("f7") == (*planner.DRAFTS, ".factory/tasks/ready/f7-*")  # not blocked/


def test_a_merged_threads_history_says_whose_it_was():
    """F49 D4: the duplicate's thread, read by the kept thread's next job."""
    said = [{"author": "owner", "text": "Same as F10?", "points": None}]
    earlier = planner.history(said, merged="f12")
    assert earlier == "\nFrom F12's thread, merged here:\n\nThe owner:\nSame as F10?\n"
    assert planner.history([], merged="f12") == ""


def _ready(n: int) -> list[planner.ReadyTicket]:
    return [planner.ReadyTicket(f"f7-{i:02}-t", "f7-one-queue", "developer", 3) for i in range(n)]


def test_the_block_lists_the_ticket_in_flight_then_the_ready_ones_in_the_order_given():
    """F21 D1: the one in flight is named once, with who has it; the others keep their order,
    each with its milestone, who does it, its priority and what it waits for."""
    ready = [
        planner.ReadyTicket("f8-01-x", "f8-the-line", "lead", 1),
        planner.ReadyTicket("f7-01-a", "f7-one-queue", "developer", 3),
        planner.ReadyTicket("f7-02-b", "f7-one-queue", "developer", 3, "waits for f7-01-a"),
    ]
    in_flight = {"kind": "local", "ticket": "f7-01-a", "agent": "local-qwen"}
    lines = planner.where_it_stands(in_flight, ready, [], []).splitlines()
    assert "In flight: f7-01-a (f7-one-queue, developer, priority 3), now with local-qwen." in lines
    assert "1. f8-01-x (f8-the-line, lead, priority 1)" in lines
    assert "2. f7-02-b (f7-one-queue, developer, priority 3): waits for f7-01-a" in lines
    assert not any(line.startswith(("1. f7-01-a", "2. f7-01-a", "3.")) for line in lines)
    assert lines.index("1. f8-01-x (f8-the-line, lead, priority 1)") > lines.index(
        "In flight: f7-01-a (f7-one-queue, developer, priority 3), now with local-qwen."
    )


def test_the_block_says_when_nothing_is_in_flight_or_ready_and_names_another_job():
    idle = planner.where_it_stands(None, [], [], []).splitlines()
    assert "In flight: nothing." in idle and "Ready: no ticket." in idle
    job = {"kind": "checkpoint", "ticket": None, "subject": "f7", "agent": "claude-sonnet"}
    assert "In flight: checkpoint f7, now with claude-sonnet." in planner.where_it_stands(
        job, [], [], []
    )


def test_the_block_shows_every_card_with_its_state_and_priority():
    cards = [("f9", "idea", 100), ("f7", "building", 3), ("f8", "building", 1), ("m4", "done", 100)]
    lines = planner.where_it_stands(None, [], cards, []).splitlines()
    assert "- building: F8 (1), F7 (3)" in lines  # lower goes first
    assert "- idea: F9 (100)" in lines and "- done: M4 (100)" in lines
    assert lines.index("- building: F8 (1), F7 (3)") < lines.index("- idea: F9 (100)")
    assert sum(line.startswith("- ") for line in lines) == 3  # a state with no card has no line


def test_the_block_gives_the_median_duration_in_minutes_or_says_none_merged():
    block = planner.where_it_stands(None, [], [], [10.0, 31.4, 240.0])
    assert "about 31 minutes" in block and "the last 3 merged" in block
    assert "about 20 minutes" in planner.where_it_stands(None, [], [], [10.0, 30.0])
    assert "about 1 minute " in planner.where_it_stands(None, [], [], [0.2])
    none = planner.where_it_stands(None, [], [], [])
    assert "No ticket has merged yet" in none and "minutes" not in none


def test_past_25_ready_tickets_the_rest_are_a_count_and_the_block_stays_short():
    cards = [(f"f{i}", state, i) for i, state in enumerate(["idea", "ready", "done"] * 40)]
    lines = planner.where_it_stands(None, _ready(31), cards, [5.0]).splitlines()
    assert "25. f7-24-t (f7-one-queue, developer, priority 3)" in lines
    assert not any("f7-25-t" in line for line in lines)
    assert "… and 6 more ready tickets." in lines
    assert len(lines) <= 40
    exact = planner.where_it_stands(None, _ready(25), [], []).splitlines()
    assert "25. f7-24-t (f7-one-queue, developer, priority 3)" in exact
    assert not any("more ready ticket" in line for line in exact)
    assert "… and 1 more ready ticket." in planner.where_it_stands(None, _ready(26), [], [])


def test_the_prompt_carries_where_the_work_stands_before_the_message():
    stands = planner.where_it_stands(None, _ready(2), [("f7", "building", 3)], [12.0])
    for thread in ("f7", "general"):
        prompt = planner.prompt(thread, "When is F7 done?", {1: "Why?"}, stands=stands)
        assert stands in prompt and "On your point 1: Why?" in prompt
        assert prompt.index("Where the work stands") < prompt.index("When is F7 done?")
    assert "Where the work stands" not in planner.prompt("f7", "When is F7 done?", {})


def test_the_prompt_names_the_other_threads_to_check_for_duplicates():
    prompt = planner.prompt("f12", "Go on.", {}, threads=["general", "f10", "f12"])
    assert "Other threads: F10, the general thread." in prompt
    assert "Other threads: none." in planner.prompt("general", "Hi.", {})


def test_a_cards_prompt_names_its_branch_and_the_general_one_none():
    card = planner.prompt("f7", "Draft it.", {})
    assert "plan/f7 only, never main" in card and ".factory/cards/f7-mockup/" in card
    assert "{" not in card.split("```json")[0]  # every field filled
    general = planner.prompt("general", "An idea.", {})
    assert "plan/" not in general and "change nothing" in general
    assert (planner.plan_branch("f7"), planner.plan_branch("general")) == ("plan/f7", None)


def test_a_cards_prompt_says_what_a_replan_may_change_and_when_to_suggest_a_pause():
    card = planner.prompt("f7", "Redirect it.", {})
    assert "`replan`" in card and ".factory/tasks/ready/f7-*.md" in card
    assert "move it to .factory/tasks/later/" in card and "never .factory/tasks/done/" in card
    assert "in progress" in card and "suggest the owner pause" in card
    general = planner.prompt("general", "An idea.", {})
    assert ".factory/tasks/ready/f" not in general and "suggest the owner pause" not in general


@pytest.mark.parametrize("thread", ["f7", "general"])
def test_the_prompt_puts_everything_in_the_points_and_no_empty_checks(thread):
    """F41 D1: the text before the block is at most two short lines; answers, risks,
    questions and asks are points; no point reports a check that found nothing (F44)."""
    text = planner.prompt(thread, "Anything?", {})
    assert "at most two short lines" in text and "every answer, risk, question and ask" in text
    assert "Don't write them out in the text too" in text
    assert "No point reports that a check found nothing" in text
    assert "propose a `merge`" in text  # a repeat found still is one
    assert "Reply in plain words, as numbered points" not in text


@pytest.mark.parametrize(
    ("path", "draft"),
    [
        (".factory/adr/21-room.md", True),
        (".factory/cards/f7-mockup/index.html", True),
        (".factory/tasks/later/f7-01-x.md", True),
        (".factory/tasks/ready/f7-01-x.md", False),
        ("runner/loop.py", False),
        ("docs/../runner/loop.py", False),
        ("documents/x.md", False),
    ],
)
def test_a_draft_is_in_docs_or_the_later_tickets(path, draft):
    assert planner.is_draft(path) is draft


@pytest.mark.parametrize(
    ("path", "draft"),
    [
        (".factory/tasks/ready/f7-01-x.md", True),
        (".factory/tasks/later/f7-01-x.md", True),
        (".factory/adr/21-room.md", True),
        (".factory/tasks/ready/f5-01-x.md", False),  # another milestone's
        (".factory/tasks/ready/f70-01-x.md", False),
        (".factory/tasks/ready/f7-notes.md", False),
        (".factory/tasks/ready/f7-01-x.txt", False),
        (".factory/tasks/ready/f7-01/x.md", False),
        (".factory/tasks/ready/f7-01-../x.md", False),
        (".factory/tasks/done/f7-01-x.md", False),
        ("runner/loop.py", False),
    ],
)
def test_a_replans_drafts_take_its_own_cards_ready_tickets_too(path, draft):
    """f6-13: given the card, its tickets in .factory/tasks/ready/ are drafts; never another's or
    done."""
    assert planner.is_draft(path, "f7") is draft


def test_a_cards_planner_job_may_edit_its_own_ready_tickets():
    assert planner.drafts("f7") == (
        "docs/**",
        ".factory/cards/**",
        ".factory/adr/**",
        ".factory/tasks/later/**",
        ".factory/tasks/ready/f7-*",
    )


# --- reading a card's draft from git, for the dashboard (f6 D4) --------------------------------

ADR = ".factory/adr/21-room.md"
MOCKUP = ".factory/cards/f7-mockup/index.html"


def _write(repo: Path, rel: str, text: str) -> None:
    (repo / rel).parent.mkdir(parents=True, exist_ok=True)
    (repo / rel).write_text(text)


@pytest.fixture
def drafted(repo: Path) -> Path:
    """main holds the ADR and a stray ``x``; ``plan/f7`` revises the ADR, adds a mock-up and
    code beside them. The working tree is back on main, with an uncommitted edit."""
    _write(repo, ADR, "main's\n")
    _write(repo, "x", "outside\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "adr")
    git(repo, "checkout", "-q", "-b", "plan/f7")
    _write(repo, ADR, "the plan's\n")
    _write(repo, MOCKUP, "<p>mock</p>\n")
    _write(repo, "runner/x.py", "code\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "drafts")
    git(repo, "checkout", "-q", "main")
    _write(repo, ADR, "the working tree's\n")
    return repo


def test_a_draft_is_read_from_the_plan_branch_while_it_exists(drafted):
    assert planner.draft(drafted, "f7", ADR) == b"the plan's\n"
    assert planner.draft(drafted, "f7", MOCKUP) == b"<p>mock</p>\n"
    assert planner.draft(drafted, "f7-planning-room", MOCKUP) == b"<p>mock</p>\n"  # its long key


def test_without_the_plan_branch_a_draft_is_mains(drafted):
    git(drafted, "branch", "-q", "-D", "plan/f7")
    assert planner.draft(drafted, "f7", ADR) == b"main's\n"  # git's, never the working tree's
    assert planner.draft(drafted, "f7", MOCKUP) is None
    assert planner.draft(drafted, "general", ADR) == b"main's\n"  # it has no plan branch


def test_another_cards_plan_branch_is_not_read(drafted):
    assert planner.draft(drafted, "f8", ADR) == b"main's\n"
    assert planner.draft(drafted, "f8", MOCKUP) is None


@pytest.mark.parametrize(
    ("thread", "path"),
    [
        ("f7", "runner/x.py"),  # on the plan branch, but code
        ("f7", "docs/../x"),
        ("f7", "docs/./adr/21-room.md"),
        ("f7", "docs//adr/21-room.md"),
        ("f7", ".factory/adr"),  # a folder, not a file
        ("f7", ".factory/adr/22-none.md"),
        ("f7", "docs/a\0b"),
        ("../x", ADR),
        ("f7/../main", ADR),
        ("plan/f7", ADR),
        ("", ADR),
        (None, ADR),
    ],
)
def test_nothing_but_a_draft_of_a_thread_is_read(drafted, thread, path):
    assert planner.draft(drafted, thread, path) is None


# --- what approving a plan branch changes (f6-24) ------------------------------------------------

READY_A = ".factory/tasks/ready/f7-01-a.md"
READY_B = ".factory/tasks/ready/f7-02-b.md"
READY_C = ".factory/tasks/ready/f7-03-c.md"
LATER_B = ".factory/tasks/later/f7-02-b.md"
OTHER = ".factory/tasks/ready/f8-01-x.md"
DONE = ".factory/tasks/done/f7-00-z.md"


@pytest.fixture
def replanned(repo: Path) -> Path:
    """main holds f7-01-a, f7-02-b, another card's f8-01-x and a done ticket; ``plan/f7`` changes
    f7-01-a, adds f7-03-c, sets f7-02-b aside in .factory/tasks/later/, drops ADR 21 and edits the
    others it may not. The working tree is back on main."""
    for rel in (READY_A, READY_B, OTHER, DONE, ADR):
        _write(repo, rel, f"main's {rel}\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "tickets")
    git(repo, "checkout", "-q", "-b", "plan/f7")
    _write(repo, READY_A, "the replan's a\n")
    _write(repo, READY_C, "the replan's c\n")
    _write(repo, LATER_B, f"main's {READY_B}\n")
    git(repo, "rm", "-q", READY_B)
    git(repo, "rm", "-q", ADR)
    _write(repo, OTHER, "the replan's x\n")
    _write(repo, DONE, "the replan's z\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "replan")
    git(repo, "checkout", "-q", "main")
    return repo


def test_a_plan_branchs_changes_are_listed_with_their_words(replanned):
    """A ticket set aside shows once, under its .factory/tasks/ready/ path, read from
    .factory/tasks/later/."""
    assert planner.plan_changes(replanned, "f7") == [
        planner.Change(ADR, "removed", None),
        planner.Change(DONE, "changed", DONE),
        planner.Change(READY_A, "changed", READY_A),
        planner.Change(READY_B, "set aside", LATER_B),
        planner.Change(READY_C, "added", READY_C),
        planner.Change(OTHER, "changed", OTHER),
    ]
    assert planner.plan_changes(replanned, "f7-planning-room") == planner.plan_changes(
        replanned, "f7"
    )


def test_a_set_aside_ticket_reads_from_the_branch_not_main(replanned):
    assert planner.draft(replanned, "f7", READY_A) == b"the replan's a\n"
    assert planner.draft(replanned, "f7", READY_C) == b"the replan's c\n"
    assert planner.draft(replanned, "f7", LATER_B) == f"main's {READY_B}\n".encode()
    assert planner.draft(replanned, "f7", READY_B) is None  # gone from .factory/tasks/ready/


def test_no_branch_and_the_general_thread_have_no_changes(replanned):
    assert planner.plan_changes(replanned, "general") == []
    assert planner.plan_changes(replanned, "f8") == []  # no plan/f8
    assert planner.plan_changes(replanned, "../x") == []
    git(replanned, "branch", "-q", "-D", "plan/f7")
    assert planner.plan_changes(replanned, "f7") == []


@pytest.mark.parametrize(
    ("thread", "path"),
    [
        ("f7", OTHER),  # another card's ready ticket, changed on this branch
        ("f8", READY_A),  # this card's ticket, read as another card's
        ("f7", DONE),
        ("f7", ".factory/tasks/ready/f7-01-a.md/../../done/f7-00-z.md"),
        ("f7", ".factory/tasks/ready/f70-01-a.md"),
        ("general", READY_A),
        ("f7", "/etc/passwd"),
        ("f7", "../outside/tasks/ready/f7-01-a.md"),
    ],
)
def test_the_dashboard_reads_no_ready_ticket_but_its_cards(replanned, thread, path):
    """Isolation (f6-24): ``draft`` stays the only way the dashboard reads the branch."""
    assert planner.draft(replanned, thread, path) is None


# --- the tables (f6 D1) ------------------------------------------------------------------------


@pytest.fixture
def db(tmp_path):
    conn = metrics.open_db(tmp_path / "factory-metrics.sqlite")
    yield conn
    conn.close()


T0 = "2026-10-06T10:00:00+00:00"


def test_a_thread_is_made_once_per_card_and_keeps_its_session(db):
    project = metrics.upsert_project(db, "coucou")
    thread = metrics.planner_thread(db, project, "f7", T0)
    assert (thread["card"], thread["session_id"], thread["created"]) == ("f7", None, T0)
    assert metrics.planner_thread(db, project, "f7", "later")["id"] == thread["id"]
    assert metrics.planner_thread(db, project, "general", T0)["id"] != thread["id"]
    metrics.set_thread_session(db, thread["id"], "s1")
    assert metrics.planner_thread(db, project, "f7", T0)["session_id"] == "s1"


def test_a_threads_messages_keep_their_points_and_proposals_as_json(db):
    project = metrics.upsert_project(db, "coucou")
    thread = metrics.planner_thread(db, project, "f7", T0)["id"]
    metrics.add_planner_message(db, thread, "owner", T0, "Go on.")
    metrics.add_planner_message(
        db, thread, "lead", T0, "Answer.", points=POINTS, proposals=[PROPOSAL]
    )
    owner, lead = metrics.planner_messages(db, thread)
    assert (owner["author"], owner["text"], owner["points"], owner["job_id"]) == (
        "owner",
        "Go on.",
        None,
        None,
    )
    assert json.loads(lead["points"]) == POINTS and json.loads(lead["proposals"]) == [PROPOSAL]
    with pytest.raises(ValueError, match="author"):
        metrics.add_planner_message(db, thread, "someone", T0, "x")


# --- planting: a seed card without Claude (ADR 20 item 8, f6 D5) -------------------------------


@pytest.mark.parametrize(
    ("title", "slug"),
    [
        ("Parallel planners", "parallel-planners"),
        ("  Café: the owner's   *best* idea!  ", "cafe-the-owner-s-best-idea"),
        ("One two three four five six seven eight", "one-two-three-four-five-six"),
        ("2FA for the dashboard", "idea-2fa-for-the-dashboard"),
        ("¿¡!?", "idea"),
    ],
)
def test_a_cards_slug_comes_from_its_title(title, slug):
    assert planner.slug(title) == slug
    assert milestone_key(f"f7-{slug}") == f"f7-{slug}"  # always a valid key


def test_the_next_key_is_the_one_after_the_highest_in_the_areas_series(tmp_path):
    docs = tmp_path / ".factory" / "cards"
    docs.mkdir(parents=True)
    for name in ("f2", "f6-planning-room", "m4", "bugs", "README"):
        (docs / f"{name}.md").write_text("# x\n")
    write_task(tmp_path / ".factory" / "tasks" / "later", "m9-01-later")
    assert planner.next_key(tmp_path, "factory") == "f7"
    assert planner.next_key(tmp_path, "product") == "m10"  # a ticket's milestone counts too
    assert planner.next_key(tmp_path / "empty", "factory") == "f1"


@pytest.mark.parametrize(
    ("value", "planted"),
    [
        (
            {"title": " One queue ", "thoughts": " Why two? \n", "area": "product"},
            ("One queue", "Why two?", "product"),
        ),
        ({"title": "One queue"}, ("One queue", "", "factory")),
        ({"title": "One queue", "thoughts": "x", "area": None}, ("One queue", "x", "factory")),
    ],
)
def test_a_plant_request_is_a_title_its_thoughts_and_an_area(value, planted):
    assert planner.planting(json.dumps(value)) == planted


@pytest.mark.parametrize(
    "value",
    [
        None,
        "One queue",
        json.dumps(["One queue"]),
        json.dumps({"title": "  "}),
        json.dumps({"title": "x", "thoughts": 3}),
        json.dumps({"title": "x", "area": "garden"}),
        json.dumps({"title": "a\nb"}),
        json.dumps({"title": "x", "thoughts": "y" * 20_001}),
    ],
)
def test_a_plant_request_without_a_one_line_title_or_a_known_area_is_refused(value):
    with pytest.raises(planner.PlannerError):
        planner.planting(value)


def test_a_long_title_is_cut_at_a_word_and_kept_whole_in_the_thoughts():
    """Never refused for its length (the owner, 2026-10-08: seven notes were lost that way):
    the title is cut at a word with an ellipsis, and the whole of it opens the thoughts."""
    long = "when i accept a proposal from a card what happens to the card? " * 3
    title, thoughts, _ = planner.planting(json.dumps({"title": long, "thoughts": "Sticky?"}))
    assert len(title) <= 120 and title.endswith("…")
    assert long.startswith(title[:-1] + " ")
    assert thoughts == f"{long.strip()}\n\nSticky?"
    assert planner.planting(json.dumps({"title": "x" * 130}))[:2] == ("x" * 119 + "…", "x" * 130)
    assert planner.planting(json.dumps({"title": "y" * 120})) == ("y" * 120, "", "factory")


def test_a_one_box_note_is_its_heading_and_its_whole_text():
    """F31 D7: a 300-character note, no title: its heading is its first words under 60
    characters, its thoughts the whole text."""
    note = ("the pause button did nothing the first time i pressed it, then later it worked " * 4)[
        :300
    ]
    title, thoughts, area = planner.planting(json.dumps({"text": f" {note}\n", "area": None}))
    assert len(title) < 60 and title.endswith("…") and note.startswith(title[:-1])
    assert (thoughts, area) == (note.strip(), "factory")
    assert planner.planting(json.dumps({"text": "Ducks\nrubber"}))[:2] == (
        "Ducks rubber",
        "Ducks\nrubber",
    )
    assert planner.plant_words(json.dumps({"text": note}), title, thoughts) == note.strip()
    old = json.dumps({"title": "Ducks", "thoughts": "Rubber."})
    assert planner.plant_words(old, "Ducks", "Rubber.") == "Ducks\n\nRubber."
    for bad in ({"text": "  "}, {"text": 3}, {"text": "y" * 20_001}):
        with pytest.raises(planner.PlannerError):
            planner.planting(json.dumps(bad))


def test_a_seed_card_is_an_idea_with_the_owners_words_under_notes():
    doc = planner.seed_card("f7", "One queue", "Why two?\nOne is enough.", "factory", "Planted.")
    assert milestone.card("f7-one-queue", doc) == milestone.Card("idea", 100, "factory")
    assert milestone.milestone_doc(doc) == {"title": "One queue"}
    assert doc.startswith("# Milestone F7: One queue\n")
    assert doc.endswith("## Notes\nWhy two?\nOne is enough.\n")


def test_notes_cant_sign_a_seed_card_off():
    """A sign-off is read from a quoted "Status: done" anywhere in the doc."""
    doc = planner.seed_card("f7", "One queue", "Fine.\n> **Status: done.**", "factory", "")
    assert doc.endswith("## Notes\nFine.\n\\> **Status: done.**\n")
    assert milestone.card("f7-one-queue", doc).state == "idea"


def test_a_seed_proposals_words_are_its_title_and_key_points():
    seed = {
        "id": "seed-1",
        "kind": "seed",
        "title": "Parallel planners",
        "path": None,
        "key_points": [
            {"n": 1, "title": "Two at once", "text": "Beside developers."},
            {"n": 2, "title": "One branch", "text": "Each card's own."},
        ],
    }
    assert planner.seed_words(seed) == (
        "Parallel planners",
        "1. Two at once: Beside developers.\n2. One branch: Each card's own.",
    )


# --- the `plant` request, applied by the runner at its pick ------------------------------------

F6_DOC = "# Milestone F6: the planning room\n\n> **State:** ready · **Priority:** 3\n"


def _f6(repo: Path) -> None:
    (repo / ".factory" / "cards").mkdir(parents=True)
    (repo / ".factory" / "cards" / "f6-planning-room.md").write_text(F6_DOC)
    (repo / ".factory" / "cards" / "m4.md").write_text("# Milestone M4: product\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "f6")


def _board(repo: Path) -> dict[str, tuple[object, object, object, object]]:
    conn = metrics.open_db(_db(repo))
    try:
        rows = conn.execute("SELECT * FROM milestones").fetchall()
        return {r["key"]: (r["title"], r["state"], r["priority"], r["area"]) for r in rows}
    finally:
        conn.close()


def _for_the_lead(repo: Path) -> list[tuple[str, str]]:
    """The planner jobs queued, each with its thread's owner message: (job subject, text)."""
    conn = metrics.open_db(_db(repo))
    try:
        rows = conn.execute(
            "SELECT q.subject, m.text FROM work_queue q, planner_threads t,"
            " planner_messages m WHERE q.kind = 'planner' AND q.done IS NULL"
            " AND m.thread_id = t.id AND m.author = 'owner'"
            " AND t.card = substr(q.subject, 1, instr(q.subject, '#') - 1) ORDER BY q.id"
        ).fetchall()
        return [(r["subject"].split("#")[0], r["text"]) for r in rows]
    finally:
        conn.close()


def _no_claude(*args, **kwargs):
    raise AssertionError("planting needs no Claude")


def _plant(title: str, thoughts: str = "", area: str | None = None, ask: bool = False) -> str:
    return json.dumps({"title": title, "thoughts": thoughts, "area": area, "ask": ask})


def test_a_plant_request_writes_and_commits_an_idea_card_with_the_owners_words(repo, monkeypatch):
    """Done when: f7-<slug> after F6, the owner's words in it, an idea card on the board, and
    no Claude needed, so it goes on while Claude is parked at a limit."""
    _f6(repo)
    monkeypatch.setattr(claude, "run_claude", _no_claude)
    monkeypatch.setattr(loop, "call_claude", _no_claude)
    parked = State(parked={"f6-05-replan": {"kind": "lead", "resets_at": "2026-10-01T17:00:00"}})
    (repo / "coucou" / "thing.py").write_text("# the owner's edit, left alone\n")
    head = git(repo, "rev-parse", "HEAD").strip()
    asked = _ask(repo, "plant", None, _plant("Parallel planners", "Two at once?\nMaybe.", ask=True))
    result = "planted .factory/cards/f7-parallel-planners.md, queued for the lead"
    assert _apply(repo, parked) == [f"plant: {result}"]
    assert _request(repo, asked) == (NOW.isoformat(), result)
    doc = (repo / ".factory" / "cards" / "f7-parallel-planners.md").read_text()
    assert "## Notes\nTwo at once?\nMaybe.\n" in doc
    assert milestone.card("f7-parallel-planners", doc) == milestone.Card("idea", 100, "factory")
    # one commit by the runner, of the card alone
    assert git(repo, "rev-parse", "HEAD~1").strip() == head
    assert git(repo, "log", "-1", "--format=%s").strip() == "F7 planted by the owner"
    assert git(repo, "log", "-1", "--format=%an").strip() == "Softfield runner"
    changed = git(repo, "show", "--name-only", "--format=", "HEAD").split()
    assert changed == [".factory/cards/f7-parallel-planners.md"]
    assert git(repo, "status", "--porcelain").strip() == "M coucou/thing.py"
    assert _board(repo)["f7-parallel-planners"] == ("Parallel planners", "idea", 100, "factory")
    # the owner's words are also F7's first message, for the lead to answer (2026-10-07)
    assert _for_the_lead(repo) == [("f7", "Parallel planners\n\nTwo at once?\nMaybe.")]
    assert _apply(repo) == []  # finished once


def test_a_one_box_note_plants_its_text_whole(repo):
    """F31 D7: no title; the heading is the first words, the Notes and the thread's first
    message the whole text, once."""
    _f6(repo)
    note = "Parallel planners: two at once?\nMaybe, if they each get their own branch."
    _ask(repo, "plant", None, json.dumps({"text": note, "ask": True}))
    [line] = _apply(repo)
    stem = "f7-parallel-planners-two-at-once-maybe"
    assert line == f"plant: planted .factory/cards/{stem}.md, queued for the lead"
    doc = (repo / ".factory" / "cards" / f"{stem}.md").read_text()
    assert doc.startswith(
        "# Milestone F7: Parallel planners: two at once? Maybe, if they each get…\n"
    )
    assert doc.endswith(f"## Notes\n{note}\n")
    assert _for_the_lead(repo) == [("f7", note)]


def test_a_plant_not_asked_about_waits_as_a_seed(repo):
    """The owner, 2026-10-08: "plant and later send to the lead manually": Plant alone files
    the card; nothing goes to the lead until the owner writes on its thread."""
    _f6(repo)
    asked = _ask(repo, "plant", None, _plant("Parallel planners", "Two at once?"))
    result = "planted .factory/cards/f7-parallel-planners.md"
    assert _apply(repo) == [f"plant: {result}"]
    assert _request(repo, asked) == (NOW.isoformat(), result)
    assert _for_the_lead(repo) == []
    old = _ask(repo, "plant", None, json.dumps({"title": "Older form"}))  # no ask: a seed
    _apply(repo)
    assert _request(repo, old)[1] == "planted .factory/cards/f8-older-form.md"
    assert _for_the_lead(repo) == []


def test_a_product_idea_takes_the_next_product_key(repo):
    _f6(repo)
    _ask(repo, "plant", None, _plant("Rubber ducks", area="product"))
    _apply(repo)
    doc = (repo / ".factory" / "cards" / "m5-rubber-ducks.md").read_text()
    assert milestone.card("m5-rubber-ducks", doc).area == "product"


def test_two_ideas_planted_at_one_pick_take_two_keys(repo):
    _f6(repo)
    _ask(repo, "plant", None, _plant("One"))
    _ask(repo, "plant", None, _plant("Two"))
    _apply(repo)
    found = sorted(p.name for p in (repo / ".factory" / "cards").glob("f*.md"))
    assert found == ["f6-planning-room.md", "f7-one.md", "f8-two.md"]


@pytest.mark.parametrize(
    ("subject", "value", "error"),
    [
        (None, "an idea", "a plant request is JSON with a title, its thoughts and an area"),
        (None, _plant("x", area="garden"), "an idea's area is factory or product, not 'garden'"),
        (
            None,
            _plant("**State:** done"),
            "an idea's title can't set its card: '**State:** done'",
        ),
        (
            None,
            _plant("After: f1 signed off"),
            "an idea's title can't set its card: 'After: f1 signed off'",
        ),
        ("general/seed-9", None, "the general thread has no proposal seed-9"),
        ("general/adr-23", None, "proposal adr-23 is an adr, not a seed"),
        ("f7/seed-1", None, "only the general thread's seeds are planted, not F7's"),
    ],
)
def test_a_plant_the_runner_cant_apply_is_finished_with_why_and_commits_nothing(
    repo, subject, value, error
):
    _f6(repo)
    _seeded(repo)
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "plant", subject, value)
    _apply(repo)
    assert _request(repo, asked) == (NOW.isoformat(), error)
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "status", "--porcelain", "--untracked-files=all") == ""


def test_a_plant_waits_for_the_repo_to_be_on_main(repo):
    _f6(repo)
    git(repo, "checkout", "-q", "-b", "task/x")
    asked = _ask(repo, "plant", None, _plant("One"))
    assert _apply(repo) == ["plant: waits for the repo to be on main"]
    assert _request(repo, asked) == (None, None)
    assert not (repo / ".factory" / "cards" / "f7-one.md").exists()


def _seeded(repo: Path) -> None:
    """The lead's reply on the general thread, with a seed and an ADR proposal."""
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        thread = metrics.planner_thread(conn, project, "general", NOW.isoformat())
        seed = {
            "id": "seed-1",
            "kind": "seed",
            "title": "Parallel planners",
            "path": None,
            "key_points": [{"n": 1, "title": "Two at once", "text": "Beside developers."}],
        }
        metrics.add_planner_message(
            conn, thread["id"], "lead", NOW.isoformat(), "A seed.", proposals=[seed, PROPOSAL]
        )
    finally:
        conn.close()


def test_approving_a_general_threads_seed_plants_it_the_same_way(repo):
    _f6(repo)
    _seeded(repo)
    asked = _ask(repo, "plant", "general/seed-1", json.dumps({"area": "factory"}))
    result = "planted .factory/cards/f7-parallel-planners.md"
    assert _apply(repo) == [f"plant general/seed-1: {result}"]
    assert _request(repo, asked) == (NOW.isoformat(), result)
    doc = (repo / ".factory" / "cards" / "f7-parallel-planners.md").read_text()
    assert "## Notes\n1. Two at once: Beside developers.\n" in doc
    assert "the general thread's seed-1" in doc
    assert milestone.card("f7-parallel-planners", doc).state == "idea"
    assert git(repo, "log", "-1", "--format=%s").strip() == "F7 planted by the owner"
    assert _for_the_lead(repo) == []  # the lead wrote the seed: nothing to answer
    again = _ask(repo, "plant", "general/seed-1")
    _apply(repo)  # F48 D1: the card holds the seed's words, so nothing is written
    assert _request(repo, again)[1] == "planted already: .factory/cards/f7-parallel-planners.md"
    assert git(repo, "log", "-1", "--format=%s").strip() == "F7 planted by the owner"


# --- archiving a thread (the owner, 2026-10-07) ---------------------------------------------


def _thread_row(repo: Path, card: str) -> dict[str, Any]:
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        found = metrics.find_thread(conn, project, card)
        assert found is not None, card
        items = [dict(i) for i in metrics.open_owner_items(conn, project) if i["subject"] == card]
        return {**dict(found), "items": items}
    finally:
        conn.close()


def _talked_about(repo: Path, card: str) -> None:
    """A thread with the owner's message on it, and the lead's reply waiting for answers."""
    _ask(repo, "plan_message", card, json.dumps({"text": "Hi.", "comments": {}}))
    _apply(repo)
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        metrics.upsert_owner_item(
            conn, project, planner.PLANNING, card, text="answers wanted", created=NOW.isoformat()
        )
    finally:
        conn.close()


def test_archiving_a_thread_stamps_it_and_clears_its_needs_you_item(repo):
    _talked_about(repo, "f7")
    asked = _ask(repo, "archive", "f7", "on")
    assert _apply(repo) == ["archive f7: archived F7"]
    assert _request(repo, asked) == (NOW.isoformat(), "archived F7")
    found = _thread_row(repo, "f7")
    assert found["archived"] == NOW.isoformat() and found["items"] == []
    _ask(repo, "archive", "f7", "on")
    assert _apply(repo) == ["archive f7: F7 is archived already"]


def test_unarchive_and_a_new_message_both_open_a_thread_again(repo):
    _talked_about(repo, "f7")
    _ask(repo, "archive", "f7", "on")
    _apply(repo)
    _ask(repo, "archive", "f7", "off")
    assert _apply(repo) == ["archive f7: F7 is open again"]
    assert _thread_row(repo, "f7")["archived"] is None
    _ask(repo, "archive", "f7", "off")
    assert _apply(repo) == ["archive f7: F7 is not archived"]
    _ask(repo, "archive", "f7", "on")
    _apply(repo)
    _ask(repo, "plan_message", "f7", json.dumps({"text": "One more thing.", "comments": {}}))
    _apply(repo)
    assert _thread_row(repo, "f7")["archived"] is None  # replying opens it again


def test_the_owners_archive_says_by_you_and_opening_clears_it(repo):
    _talked_about(repo, "f7")
    _ask(repo, "archive", "f7", "on")
    _apply(repo)
    assert _thread_row(repo, "f7")["archived_why"] == "by you"
    _ask(repo, "plan_message", "f7", json.dumps({"text": "Again.", "comments": {}}))
    _apply(repo)
    assert _thread_row(repo, "f7")["archived_why"] is None


# --- a thread closes once every proposal is settled (F31 D1) ---------------------------------

SEED_2: dict[str, Any] = {
    "id": "seed-2",
    "kind": "seed",
    "title": "Two",
    "path": None,
    "key_points": [],
}


def test_planting_every_seed_of_the_reply_closes_the_general_thread(repo):
    """F31 D1: one seed planted leaves the thread on the desk; the last one closes it with a
    lead line and resolves its item. An ADR still open keeps it open."""
    _f6(repo)
    _seeded(repo)  # seed-1 and an ADR
    _talked_about(repo, "general")
    _ask(repo, "plant", "general/seed-1", json.dumps({"area": "factory"}))
    _apply(repo)
    assert _thread_row(repo, "general")["archived"] is None  # the ADR is still open
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        thread = metrics.planner_thread(conn, project, "general", NOW.isoformat())["id"]
        seed_3 = {**SEED_2, "id": "seed-3", "title": "Three"}
        metrics.add_planner_message(
            conn, thread, "lead", NOW.isoformat(), "Two seeds.", proposals=[SEED_2, seed_3]
        )
    finally:
        conn.close()
    _ask(repo, "plant", "general/seed-2", None)
    _apply(repo)
    assert _thread_row(repo, "general")["archived"] is None  # seed-3 still open
    refused = _ask(repo, "plant", "general/seed-9", None)
    _apply(repo)
    assert "no proposal" in str(_request(repo, refused)[1])
    assert _thread_row(repo, "general")["archived"] is None  # a refusal settles nothing
    asked = _ask(repo, "plant", "general/seed-3", None)
    _apply(repo)
    found = _thread_row(repo, "general")
    assert found["archived"] == NOW.isoformat() and found["archived_why"] == "approved"
    assert found["items"] == []
    result = _request(repo, asked)[1]
    conn = metrics.open_db(_db(repo))
    try:
        said = metrics.planner_messages(conn, found["id"])
    finally:
        conn.close()
    assert said[-1]["author"] == "lead"
    assert said[-1]["text"] == f"Approved by the owner on 2026-10-01: {result}"


def test_a_thread_with_no_proposals_stays_until_the_owner_archives_it(repo):
    _talked_about(repo, "f7")
    _ask(repo, "approve_plan", "f7", None)
    _apply(repo)
    assert _thread_row(repo, "f7")["archived"] is None


# --- the clear-out, once per database (F55 D3) -----------------------------------------------


def _older_database(repo: Path) -> None:
    """A database from before F55: its clear-out not done yet."""
    conn = metrics.open_db(_db(repo))
    try:
        conn.execute("DELETE FROM once_steps")
    finally:
        conn.close()


def _card_in(repo: Path, key: str, state: str) -> None:
    docs = repo / ".factory" / "cards"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / f"{key}-x.md").write_text(f"# Milestone {key.upper()}: x\n\n> **State:** {state}\n")


def test_the_clear_out_archives_settled_threads_once(repo):
    """F55 D3: a ready card's or a gone card's thread answered by the lead is archived as
    approved; an idea's, the general thread, and one with an open proposal stay; a thread the
    owner opens later is never cleared again."""
    for key, state in (("f7", "ready"), ("f8", "idea"), ("f9", "ready")):
        _card_in(repo, key, state)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "cards")
    for card in ("f7", "f8", "f9", "f10", "general"):
        _talked_about(repo, card)
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        for card in ("f7", "f8", "f10", "general"):
            thread = metrics.planner_thread(conn, project, card, NOW.isoformat())["id"]
            metrics.add_planner_message(conn, thread, "lead", NOW.isoformat(), "Done.")
        thread = metrics.planner_thread(conn, project, "f9", NOW.isoformat())["id"]
        metrics.add_planner_message(  # a replan still open
            conn,
            thread,
            "lead",
            NOW.isoformat(),
            "Redirect?",
            proposals=[{**SEED_2, "kind": "replan"}],
        )
    finally:
        conn.close()
    _older_database(repo)
    assert _apply(repo) == ["archived the settled threads of F7, F10 (F55)"]
    for card, why in (("f7", "approved"), ("f10", "approved")):
        found = _thread_row(repo, card)
        assert found["archived_why"] == why and found["items"] == []
    for card in ("f8", "f9", "general"):
        assert _thread_row(repo, card)["archived"] is None
    _ask(repo, "archive", "f7", "off")
    _apply(repo)
    assert _apply(repo) == []
    assert _thread_row(repo, "f7")["archived"] is None  # opened by the owner: left alone


def test_the_clear_out_reads_the_owners_approvals_of_the_latest_proposals(repo):
    """F55 D3: a plan the owner approved before F31 D1 counts as settled, on a ready or a
    building card; an ADR of the same reply left unanswered keeps its thread open."""
    for key, state in (("f7", "ready"), ("f9", "ready"), ("f11", "building")):
        _card_in(repo, key, state)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "cards")
    plan = {**SEED_2, "id": "plan-1", "kind": "plan"}
    adr = {**SEED_2, "id": "adr-1", "kind": "adr", "path": ".factory/adr/30-x.md"}
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        for card, proposals in (("f7", [plan]), ("f9", [plan, adr]), ("f11", [plan])):
            thread = metrics.planner_thread(conn, project, card, NOW.isoformat())["id"]
            metrics.add_planner_message(
                conn, thread, "lead", NOW.isoformat(), "Plan.", proposals=proposals
            )
            asked = metrics.add_request(conn, project, "approve_plan", card, None, NOW.isoformat())
            metrics.finish_request(conn, asked, NOW.isoformat(), f"approved {card}")
    finally:
        conn.close()
    _older_database(repo)
    assert _apply(repo) == ["archived the settled threads of F7, F11 (F55)"]
    assert _thread_row(repo, "f9")["archived"] is None  # its ADR still waits for the owner


def test_a_new_database_owes_no_clear_out(repo):
    _talked_about(repo, "f10")  # no card: it would be cleared on an older database
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        thread = metrics.planner_thread(conn, project, "f10", NOW.isoformat())["id"]
        metrics.add_planner_message(conn, thread, "lead", NOW.isoformat(), "Done.")
    finally:
        conn.close()
    assert _apply(repo) == []
    assert _thread_row(repo, "f10")["archived"] is None


@pytest.mark.parametrize(
    ("subject", "value", "result"),
    [
        ("f8", "on", "F8 has no thread to archive"),
        ("f7", "yes", "archive is on or off, not 'yes'"),
        ("x y", "on", "a thread is a card's key or general, not 'x y'"),
    ],
)
def test_an_archive_the_runner_cant_apply_says_why(repo, subject, value, result):
    _talked_about(repo, "f7")
    asked = _ask(repo, "archive", subject, value)
    _apply(repo)
    assert _request(repo, asked)[1] == result
    assert _thread_row(repo, "f7")["archived"] is None


# --- the thread committed with its approved plan (f20 D2) ------------------------------------

EXPORT = ".factory/planning/f7-one-queue.md"
MARKDOWN = "# x\n```\nAgreed otherwise, see `.factory/tasks/`.\nA line\n---"
EXPORTED = """\
# F7: one queue

The planning thread behind F7's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-01 12:00

> Why one queue?

## The lead, 2026-10-01 12:05

> Here is my answer.
>
> 1. **The switch**: Keep one per window.
>    Action: Nothing
> 2. **The queue**: Planner jobs go first.
>    Action: A ticket
>
> Proposals:
> - Parallel planners (adr)

## The owner, 2026-10-01 12:10

> # x
> ```
> Agreed otherwise, see `.factory/tasks/`.
> A line
> ---
>
> On point 2: Why first?
"""


def _said(repo: Path, card: str, author: str, minutes: int, text: str, **json_: Any) -> None:
    """A message on ``card``'s thread, ``minutes`` after NOW."""
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        thread = metrics.planner_thread(conn, project, card, NOW.isoformat())
        at = (NOW + timedelta(minutes=minutes)).isoformat()
        metrics.add_planner_message(conn, thread["id"], author, at, text, **json_)
    finally:
        conn.close()


def _talked_through(repo: Path) -> None:
    """F7's thread: the owner asks, the lead answers with points and a proposal, and the
    owner replies in Markdown with a comment on point 2."""
    _said(repo, "f7", "owner", 0, "Why one queue?")
    _said(repo, "f7", "lead", 5, "Here is my answer.", points=POINTS, proposals=[PROPOSAL])
    _said(repo, "f7", "owner", 10, MARKDOWN, points=[{"n": 2, "comment": "Why first?"}])


def _committed(repo: Path) -> list[str]:
    return sorted(filter(None, git(repo, "show", "--name-only", "--format=", "HEAD").split("\n")))


def test_approving_a_plan_commits_its_thread_with_its_drafts(repo):
    _card(repo)
    _plan(repo, {".factory/tasks/later/f7-01-a.md": _ticket("f7-01-a")})
    _talked_through(repo)
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert _request(repo, asked)[1] == "approved plan/f7: queued f7-01-a"
    assert (repo / EXPORT).read_text() == EXPORTED
    assert git(repo, "log", "-1", "--format=%s").strip() == "F7 plan approved by the owner"
    assert _committed(repo) == [
        ".factory/cards/f7-one-queue.md",
        EXPORT,
        ".factory/tasks/ready/f7-01-a.md",
    ]
    assert git(repo, "status", "--porcelain", "--untracked-files=all") == ""


def test_a_messages_markdown_cant_make_a_heading_of_the_export(repo):
    _card(repo)
    _plan(repo, {".factory/tasks/later/f7-01-a.md": _ticket("f7-01-a")})
    _talked_through(repo)
    _ask(repo, "approve_plan", "f7")
    _apply(repo)
    lines = (repo / EXPORT).read_text().splitlines()
    # only the title and each message's heading; everything said sits in a quote
    assert [line for line in lines if not line.startswith(">") and line.strip()] == [
        "# F7: one queue",
        "The planning thread behind F7's plan, oldest first, as it was when the owner approved it.",
        "## The owner, 2026-10-01 12:00",
        "## The lead, 2026-10-01 12:05",
        "## The owner, 2026-10-01 12:10",
    ]


def test_a_second_approval_rewrites_the_export_with_the_whole_thread(repo):
    _card(repo)
    _plan(repo, {".factory/tasks/later/f7-01-a.md": _ticket("f7-01-a")})
    _talked_through(repo)
    _ask(repo, "approve_plan", "f7")
    _apply(repo)
    _said(repo, "f7", "owner", 20, "One more ticket, please.")
    _plan(repo, {".factory/tasks/later/f7-02-b.md": _ticket("f7-02-b")})
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert _request(repo, asked)[1] == "approved plan/f7: queued f7-02-b"
    more = "\n## The owner, 2026-10-01 12:20\n\n> One more ticket, please.\n"
    assert (repo / EXPORT).read_text() == EXPORTED + more
    assert EXPORT in _committed(repo)


def test_a_refused_approval_writes_no_export(repo):
    _card(repo)
    _plan(repo, {".factory/tasks/later/f7-01-a.md": _ticket("f7-01-a", "Fix `conftest.py`.")})
    _talked_through(repo)
    head = git(repo, "rev-parse", "HEAD")
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert str(_request(repo, asked)[1]).startswith("not approved: f7-01-a:")
    _main_unchanged(repo, head)
    assert not (repo / ".factory" / "planning").exists()


def test_a_commit_that_fails_after_the_export_leaves_no_file(repo, monkeypatch):
    _card(repo)
    _plan(repo, {".factory/tasks/later/f7-01-a.md": _ticket("f7-01-a")})
    _talked_through(repo)
    head = git(repo, "rev-parse", "HEAD")

    def commit_all(self, message):
        assert (repo / EXPORT).exists()  # written before the commit, then undone
        raise GitError("disk full")

    monkeypatch.setattr(Git, "commit_all", commit_all)
    asked = _ask(repo, "approve_plan", "f7")
    _apply(repo)
    assert _request(repo, asked)[1] == "GitError: disk full"
    _main_unchanged(repo, head)
    assert not (repo / EXPORT).exists()


def test_the_general_threads_approved_merges_export_nothing(repo):
    _duplicates(repo, thread="general")
    asked = _ask(repo, "approve_plan", "general")
    _apply(repo)
    assert _request(repo, asked)[1] == "approved: merged F12 into F10"
    assert not (repo / ".factory" / "planning").exists()
    assert ".factory/planning" not in git(repo, "show", "--name-only", "--format=", "HEAD")


# --- proposal_state (F31 D3) --------------------------------------------------------------------


def _row(
    kind: str, subject: str, done: bool = True, result: str = "", value: str = ""
) -> dict[str, Any]:
    return {
        "kind": kind,
        "subject": subject,
        "value": value,
        "done": "x" if done else None,
        "result": result,
    }


PLAN_P = {"id": "plan-f7", "kind": "plan"}
ADR_P = {"id": "adr-30", "kind": "adr", "path": ".factory/adr/30-one-queue.md"}
SEED_P = {"id": "seed-1", "kind": "seed"}


@pytest.mark.parametrize(
    ("proposal", "card", "rows", "state"),
    [
        (PLAN_P, "f7", [], "open"),
        (
            PLAN_P,
            "f7",
            [_row("approve_plan", "f7", result="approved plan/f7: queued x")],
            "approved",
        ),
        (PLAN_P, "f7", [_row("approve_plan", "f7", done=False)], "on its way"),
        (
            PLAN_P,
            "f7",
            [_row("approve_plan", "f7", result="plan/f7 clashes with main: not approved")],
            "open",
        ),
        (
            PLAN_P,
            "f7",
            [_row("send_back", "f7/plan-f7", result="queued for the lead")],
            "sent back",
        ),
        (ADR_P, "f7", [_row("accept_adr", "f7", value="30", result="accepted ADR 30")], "approved"),
        (
            PLAN_P,
            "f7",
            [_row("reject", "f7/plan-f7", result="rejected the drafts on plan/f7 (plan-f7)")],
            "rejected",
        ),
        # a reject on the plan takes the branch, so the ADR drafted on it too
        (
            ADR_P,
            "f7",
            [
                _row(
                    "reject",
                    "f7/plan-f7",
                    result="rejected the drafts on plan/f7 (adr-30, plan-f7)",
                )
            ],
            "rejected",
        ),
        (PLAN_P, "f7", [_row("reject", "f7/plan-f7", done=False)], "on its way"),
        (
            PLAN_P,
            "f7",
            [
                _row(
                    "reject",
                    "f7/plan-f7",
                    result="F7's latest reply has no proposal x: not rejected",
                )
            ],
            "open",
        ),
        (
            SEED_P,
            "general",
            [_row("reject", "general/seed-1", result="rejected seed-1")],
            "rejected",
        ),
        (SEED_P, "general", [_row("reject", "general/seed-2", result="rejected seed-2")], "open"),
        ({**PLAN_P, "applied": True}, "f7", [], "approved"),
    ],
)
def test_a_proposals_state_comes_from_the_owners_requests(proposal, card, rows, state):
    assert planner.proposal_state(proposal, card, rows) == state


def test_a_key_that_has_a_thread_is_never_given_again(tmp_path):
    """f109-02: F64 was planted and merged three times, F73 and F107 twice: the merged card's
    doc left main and the next plant took its key, and its thread with it."""
    docs = tmp_path / ".factory" / "cards"
    docs.mkdir(parents=True)
    for name in ("f2", "f8-one-queue", "m4"):
        (docs / f"{name}.md").write_text("# x\n")
    assert planner.next_key(tmp_path, "factory", ["f9"]) == "f10"
    assert planner.next_key(tmp_path, "factory", ["general", "m9", "f3"]) == "f9"
    assert planner.next_key(tmp_path, "product", ["general", "f9"]) == "m5"
    assert planner.next_key(tmp_path, "factory", []) == planner.next_key(tmp_path, "factory")


def test_a_plant_passes_over_the_key_of_a_card_merged_away(repo):
    """f109-02: F7's card is gone from main, its thread is not."""
    _f6(repo)
    conn = metrics.open_db(_db(repo))
    try:
        project = metrics.upsert_project(conn, repo.name, repo=str(repo))
        metrics.planner_thread(conn, project, "f7", NOW.isoformat())
        metrics.planner_thread(conn, project, "general", NOW.isoformat())
    finally:
        conn.close()
    _ask(repo, "plant", None, _plant("One"))
    _ask(repo, "plant", None, _plant("Two"))
    _apply(repo)
    found = sorted(p.name for p in (repo / ".factory" / "cards").glob("f*.md"))
    assert found == ["f6-planning-room.md", "f8-one.md", "f9-two.md"]
