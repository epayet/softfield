"""The planning room's threads and replies (ADR 20 items 3 and 4, f6 D1–D3)."""

import json

import pytest

from runner import metrics, planner

POINTS = [
    {"n": 1, "title": "The switch", "answer": "Keep one per window.", "action": "Nothing"},
    {"n": 2, "title": "The queue", "answer": "Planner jobs go first.", "action": "A ticket"},
]
PROPOSAL = {
    "id": "adr-23",
    "kind": "adr",
    "title": "Parallel planners",
    "path": "docs/adr/23-parallel-planners.md",
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
        ("Build on `docs/adr/23-parallel-planners.md` items 2-3.", {23}),
        ("As ADR 7 item 2 and ADR 20 say.", {7, 20}),
        ("Read docs/adr/README.md and the address 23-a.", set()),
    ],
)
def test_the_adrs_a_ticket_relies_on_are_the_ones_it_names(text, adrs):
    assert planner.named_adrs(text) == adrs


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


def test_a_cards_prompt_names_its_branch_and_the_general_one_none():
    card = planner.prompt("f7", "Draft it.", {})
    assert "plan/f7 only, never main" in card and "docs/milestones/f7-mockup/" in card
    assert "{" not in card.split("```json")[0]  # every field filled
    general = planner.prompt("general", "An idea.", {})
    assert "plan/" not in general and "change nothing" in general
    assert (planner.plan_branch("f7"), planner.plan_branch("general")) == ("plan/f7", None)


@pytest.mark.parametrize(
    ("path", "draft"),
    [
        ("docs/adr/21-room.md", True),
        ("docs/milestones/f7-mockup/index.html", True),
        ("tasks/later/f7-01-x.md", True),
        ("tasks/ready/f7-01-x.md", False),
        ("runner/loop.py", False),
        ("docs/../runner/loop.py", False),
        ("documents/x.md", False),
    ],
)
def test_a_draft_is_in_docs_or_the_later_tickets(path, draft):
    assert planner.is_draft(path) is draft


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
