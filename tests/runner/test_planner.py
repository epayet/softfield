"""The planning room's threads and replies (ADR 20 items 3 and 4, f6 D1–D3)."""

import json
from pathlib import Path

import pytest

from runner import claude, loop, metrics, milestone, planner
from runner.state import State
from runner.tasks import milestone_key
from tests.runner.conftest import git, write_task
from tests.runner.test_requests import NOW, _apply, _ask, _db, _request

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


# --- a `merge`: one card repeats another (f6-12, D2) ----------------------------------------------

MERGE = {
    "id": "merge-f12",
    "kind": "merge",
    "title": "One queue, said twice",
    "path": "docs/milestones/f12-queue-once.md",
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
        ({"path": "docs/milestones/f99-gone.md"}, "f99 is no card"),
        ({"path": "docs/adr/23-x.md"}, "a card's doc"),
        ({"path": "docs/milestones/../adr/f12-x.md"}, "a card's doc"),
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


def test_the_cards_are_the_milestone_docs_short_keys(tmp_path):
    docs = tmp_path / "docs" / "milestones"
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


def test_the_prompt_names_the_other_threads_to_check_for_duplicates():
    prompt = planner.prompt("f12", "Go on.", {}, threads=["general", "f10", "f12"])
    assert "Other threads: F10, the general thread." in prompt
    assert "Other threads: none." in planner.prompt("general", "Hi.", {})


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


# --- reading a card's draft from git, for the dashboard (f6 D4) --------------------------------

ADR = "docs/adr/21-room.md"
MOCKUP = "docs/milestones/f7-mockup/index.html"


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
        ("f7", "docs/adr"),  # a folder, not a file
        ("f7", "docs/adr/22-none.md"),
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
    docs = tmp_path / "docs" / "milestones"
    docs.mkdir(parents=True)
    for name in ("f2", "f6-planning-room", "m4", "bugs", "README"):
        (docs / f"{name}.md").write_text("# x\n")
    write_task(tmp_path / "tasks" / "later", "m9-01-later")
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
        json.dumps({"title": "x" * 121}),
        json.dumps({"title": "x", "thoughts": "y" * 20_001}),
    ],
)
def test_a_plant_request_without_a_one_line_title_or_a_known_area_is_refused(value):
    with pytest.raises(planner.PlannerError):
        planner.planting(value)


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
    (repo / "docs" / "milestones").mkdir(parents=True)
    (repo / "docs" / "milestones" / "f6-planning-room.md").write_text(F6_DOC)
    (repo / "docs" / "milestones" / "m4.md").write_text("# Milestone M4: product\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "f6")


def _board(repo: Path) -> dict[str, tuple[object, object, object, object]]:
    conn = metrics.open_db(_db(repo))
    try:
        rows = conn.execute("SELECT * FROM milestones").fetchall()
        return {r["key"]: (r["title"], r["state"], r["priority"], r["area"]) for r in rows}
    finally:
        conn.close()


def _no_claude(*args, **kwargs):
    raise AssertionError("planting needs no Claude")


def _plant(title: str, thoughts: str = "", area: str | None = None) -> str:
    return json.dumps({"title": title, "thoughts": thoughts, "area": area})


def test_a_plant_request_writes_and_commits_an_idea_card_with_the_owners_words(repo, monkeypatch):
    """Done when: f7-<slug> after F6, the owner's words in it, an idea card on the board, and
    no Claude needed, so it goes on while Claude is parked at a limit."""
    _f6(repo)
    monkeypatch.setattr(claude, "run_claude", _no_claude)
    monkeypatch.setattr(loop, "call_claude", _no_claude)
    parked = State(parked={"f6-05-replan": {"kind": "lead", "resets_at": "2026-10-01T17:00:00"}})
    (repo / "coucou" / "thing.py").write_text("# the owner's edit, left alone\n")
    head = git(repo, "rev-parse", "HEAD").strip()
    asked = _ask(repo, "plant", None, _plant("Parallel planners", "Two at once?\nMaybe."))
    result = "planted docs/milestones/f7-parallel-planners.md"
    assert _apply(repo, parked) == [f"plant: {result}"]
    assert _request(repo, asked) == (NOW.isoformat(), result)
    doc = (repo / "docs" / "milestones" / "f7-parallel-planners.md").read_text()
    assert "## Notes\nTwo at once?\nMaybe.\n" in doc
    assert milestone.card("f7-parallel-planners", doc) == milestone.Card("idea", 100, "factory")
    # one commit by the runner, of the card alone
    assert git(repo, "rev-parse", "HEAD~1").strip() == head
    assert git(repo, "log", "-1", "--format=%s").strip() == "F7 planted by the owner"
    assert git(repo, "log", "-1", "--format=%an").strip() == "Coucou runner"
    changed = git(repo, "show", "--name-only", "--format=", "HEAD").split()
    assert changed == ["docs/milestones/f7-parallel-planners.md"]
    assert git(repo, "status", "--porcelain").strip() == "M coucou/thing.py"
    assert _board(repo)["f7-parallel-planners"] == ("Parallel planners", "idea", 100, "factory")
    assert _apply(repo) == []  # finished once


def test_a_product_idea_takes_the_next_product_key(repo):
    _f6(repo)
    _ask(repo, "plant", None, _plant("Rubber ducks", area="product"))
    _apply(repo)
    doc = (repo / "docs" / "milestones" / "m5-rubber-ducks.md").read_text()
    assert milestone.card("m5-rubber-ducks", doc).area == "product"


def test_two_ideas_planted_at_one_pick_take_two_keys(repo):
    _f6(repo)
    _ask(repo, "plant", None, _plant("One"))
    _ask(repo, "plant", None, _plant("Two"))
    _apply(repo)
    found = sorted(p.name for p in (repo / "docs" / "milestones").glob("f*.md"))
    assert found == ["f6-planning-room.md", "f7-one.md", "f8-two.md"]


@pytest.mark.parametrize(
    ("subject", "value", "error"),
    [
        (None, "an idea", "a plant request is JSON with a title, its thoughts and an area"),
        (None, _plant("x", area="garden"), "an idea's area is factory or product, not 'garden'"),
        (None, _plant("Planning room"), "planning-room is a card already: f6-planning-room"),
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
    assert not (repo / "docs" / "milestones" / "f7-one.md").exists()


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
    result = "planted docs/milestones/f7-parallel-planners.md"
    assert _apply(repo) == [f"plant general/seed-1: {result}"]
    assert _request(repo, asked) == (NOW.isoformat(), result)
    doc = (repo / "docs" / "milestones" / "f7-parallel-planners.md").read_text()
    assert "## Notes\n1. Two at once: Beside developers.\n" in doc
    assert "the general thread's seed-1" in doc
    assert milestone.card("f7-parallel-planners", doc).state == "idea"
    assert git(repo, "log", "-1", "--format=%s").strip() == "F7 planted by the owner"
    again = _ask(repo, "plant", "general/seed-1")
    _apply(repo)
    assert _request(repo, again)[1] == ("parallel-planners is a card already: f7-parallel-planners")
