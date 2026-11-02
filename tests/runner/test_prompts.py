"""The developer's prompt (ADR 12 item 1): one finish line, last before any retry text."""

import inspect
import re
from pathlib import Path

import pytest

from runner import milestone, prompts
from runner.prompts import local_prompt
from runner.tasks import parse_task
from tests.runner.conftest import write_task


def test_the_finish_line_is_one_check_all_command(tmp_path: Path):
    task = parse_task(write_task(tmp_path, "m1-01-thing"), 1000)
    prompt = local_prompt(task)
    assert prompt.rstrip().endswith(
        "Finish by running `softfield check-all --fix --task m1-01-thing` and fixing what it"
        " reports."
    )
    assert "pipes (`|`), redirections\nand unknown flags are refused" in prompt


def test_the_lead_may_reset_the_branch_and_an_escalation_may_finish_first():
    """ADR 15 items 7 and 8: the next attempt builds on the branch unless the lead says reset."""
    assert "reset: true" in prompts.DIRECTION
    assert '"reset": true' in prompts.ESCALATION
    options = prompts.ESCALATION.split("Do exactly one of:", 1)[1]
    assert options.index("finish") < options.index("requeue") < options.index("implemented")
    assert "git checkout task/{id}" in prompts.ESCALATION
    assert "has been reset" not in prompts.RETRY


def test_the_planner_prompt_names_the_block_the_branch_and_the_approval_rule():
    """f6-02: the planner plans as the lead did with the owner (ADR 20 items 4–7, f6 D2, D4)."""
    text = prompts.PLANNER
    # The block (D2): last, with the points and the proposals' key points
    block = text.split("```json", 1)[1]
    for field in ('"points"', '"answer"', '"action"', '"proposals"', '"key_points"', '"flag"'):
        assert field in block
    assert "nothing after it" in text and text.rstrip().endswith("```")
    # The branch (D4): drafts on plan/<card> only, in the drafts' folders, committed by the runner
    assert "plan/{card} only, never main" in text and "`git checkout plan/{card}`" in text
    for folder in (".softfield/adr/", ".softfield/cards/{card}-mockup/", ".softfield/tasks/later/"):
        assert folder in text
    assert "self-contained HTML" in text and "don't commit" in text
    # The frame the owner reads a mock-up in runs its scripts and nothing else (F104 D1)
    for refused in ("no localStorage", "no alert or confirm", "no request to the dashboard"):
        assert refused in text
    # The approval rule (item 7): nothing queued until the owner approves; only a replan's
    # branch touches .softfield/tasks/ready/ (f6-13)
    assert "Nothing is queued without their approval" in text
    assert "Only a `replan` may touch .softfield/tasks/ready/" in text
    # Questions first, every point agreed by default, and push back (owner.md)
    assert text.index("questions and comments first") < text.index("then revise")
    assert "counts as agreed" in text and "Challenge them" in text


def test_the_general_thread_has_no_branch_and_proposes_seeds():
    text = prompts.PLANNER_GENERAL
    assert "plan/" not in text and "change nothing" in text and "`seed`" in text
    assert "Nothing is queued without their approval" in text and "```json" in text


@pytest.mark.parametrize("text", [prompts.PLANNER, prompts.PLANNER_GENERAL])
def test_both_planner_prompts_look_for_duplicates_and_propose_a_merge(text):
    """f6-12: before answering, the cards in .softfield/cards/ (idea, planning or ready) and the
    other threads; a repeat is a point and a `merge` proposal, which the runner applies at
    once (F49 D1), keeping the more advanced card (D2)."""
    looks = text.index("Before answering")
    assert ".softfield/cards/" in text[looks:] and "idea, planning or ready" in text
    assert "{threads}" in text and "repeats another" in text
    assert "`merge`" in text and '"into"' in text.split("```json", 1)[1]
    assert "applies the merge on its own" in text and "once the owner approves" not in text
    assert "ready over planning over idea" in text
    assert text.index("Before answering") < text.index("```json")


ROOT = Path(__file__).resolve().parents[2]
LEAD_PROMPTS = {
    "planner": (prompts.PLANNER, prompts.PLANNER_GENERAL),
    "lead-ticket": (prompts.LEAD_TICKET,),
    "escalation": (prompts.ESCALATION,),
    "direction": (prompts.DIRECTION,),
    "checkpoint": (prompts.CHECKPOINT,),
    "review": (prompts.REVIEW,),
}


def _lead_doc(repo: Path, headings: tuple[str, ...]) -> None:
    (repo / prompts.OWNER_DOC).parent.mkdir(parents=True, exist_ok=True)
    (repo / prompts.OWNER_DOC).write_text("# The owner\n\n- Low ceremony.\n")
    body = "".join(f"## {h}\nWhat {h} says.\n- ### not a section\n\n" for h in headings)
    (repo / prompts.LEAD_DOC).write_text("# The lead\n\nThe model.\n\n" + body)


def test_every_section_a_lead_role_needs_is_a_heading_of_the_real_lead_md():
    """f21 D2: a renamed section fails here, at commit, not in a run."""
    assert set(prompts.SECTIONS) == set(LEAD_PROMPTS)
    headings = set(prompts.sections((ROOT / prompts.LEAD_DOC).read_text(encoding="utf-8")))
    headings |= set(prompts.sections((ROOT / prompts.KNOWN_RANGE_DOC).read_text(encoding="utf-8")))
    for role, names in prompts.SECTIONS.items():
        assert names and set(names) <= headings, role
        text, missing = prompts.brief(ROOT, role)
        assert missing == []
        assert text.startswith((ROOT / prompts.OWNER_DOC).read_text(encoding="utf-8").strip())


def test_the_roles_get_the_sections_f21_d2_lists():
    escalations, review = "Escalations (headless or interactive)", "Review"
    assert {
        "planner": ("Authority", "Plan", "Planning room", "Tickets"),
        "lead-ticket": ("Your own work", "Tickets"),
        "escalation": ("Known range", escalations, "Your own work"),
        "direction": ("Known range", escalations, "Your own work"),
        "checkpoint": (review, "Sign-off sheet", "Reporting"),
        "review": (review, "Sign-off sheet", "Reporting"),
    } == prompts.SECTIONS


def test_a_brief_is_owner_md_then_the_roles_sections_and_no_other(tmp_path: Path):
    _lead_doc(tmp_path, ("Plan", "Tickets", "Review", "Your own work", "Known range"))
    text, missing = prompts.brief(tmp_path, "lead-ticket")
    assert missing == []
    assert text.startswith("# The owner\n\n- Low ceremony.\n")
    # in the map's order, each whole, up to the next `## ` heading
    assert text.index("## Your own work\nWhat Your own work says.\n- ### not a section") < (
        text.index("## Tickets\nWhat Tickets says.")
    )
    assert text.count("\n## ") == 2 and "The model." not in text
    assert text.endswith("\n") and prompts.brief(tmp_path, "lead-ticket") == (text, [])


def test_a_brief_goes_with_what_it_found_and_names_what_is_missing(tmp_path: Path):
    _lead_doc(tmp_path, ("Plan", "Tickets"))
    text, missing = prompts.brief(tmp_path, "planner")
    assert missing == ["Authority", "Planning room"]
    assert "## Plan\n" in text and "## Tickets\n" in text and text.count("\n## ") == 2
    (tmp_path / prompts.OWNER_DOC).unlink()
    text, missing = prompts.brief(tmp_path, "planner")
    assert missing == [prompts.OWNER_DOC, "Authority", "Planning room"]
    assert "## Plan\n" in text


def test_a_role_without_sections_or_a_repo_without_lead_md_gets_no_brief(tmp_path: Path):
    assert prompts.brief(tmp_path, "planner") == ("", [])
    _lead_doc(tmp_path, ("Plan",))
    assert prompts.brief(tmp_path, "narrative") == ("", [])
    assert prompts.brief(tmp_path, "checkpoint-shadow") == ("", [])


@pytest.mark.parametrize("role", sorted(LEAD_PROMPTS))
def test_the_lead_prompts_no_longer_point_at_lead_md_or_owner_md(role):
    """f21 D2: the text is in the prompt."""
    for text in LEAD_PROMPTS[role]:
        assert "lead.md" not in text and "owner.md" not in text
        for name in re.findall(r'"([^"\n]+)"[ \n]+above', text):
            assert any(h == name or h.startswith(name + " (") for h in prompts.SECTIONS[role])


@pytest.mark.parametrize("text", [prompts.PLANNER, prompts.PLANNER_GENERAL])
def test_both_planner_prompts_ask_for_outcomes_short_prose_and_named_cards(text):
    """F31 D4 and D6: each point says what it leads to; two lines of prose at most; a card
    goes by its title; a bare "agreed" gets one point, not a round of answers."""
    block = text.split("```json", 1)[1]
    assert '"outcome"' in block and '"proposal"' in block
    rule = text[text.index("`outcome`") : text.index("```json")]
    for outcome in ("info", "ticket", "adr", "mockup", "roadmap", "merge", "question"):
        assert f"`{outcome}`" in rule
    assert "`proposal`" in rule and "in this block" in rule
    assert "at most two short lines" in text
    assert "F22, Archive at the bottom" in text and "never a bare number" in text
    assert '"agreed" or "go"' in text and "nothing new" in text
    assert "one point" in text and "waits for their Approve" in text
    assert text.index("How to answer") < text.index('"agreed" or "go"') < text.index("```json")


@pytest.mark.parametrize(
    "text", [prompts.PLANNER, prompts.PLANNER_GENERAL], ids=["card", "general"]
)
def test_both_planner_prompts_say_a_new_list_of_proposals_replaces_the_last(text):
    """F31 D3: only the latest list's proposals keep their buttons, and the thread closes
    once they are settled, so the lead lists again what still waits: one it left unchanged,
    and one the owner sent back that it keeps as it is."""
    rule = text[text.index("End your reply") : text.index("```json")]
    assert "replaces your last one" in rule
    assert "still waits for them" in rule and "unchanged" in rule
    assert "sent back" in rule and "list it again" in rule


def test_a_cards_planner_names_a_seed_card_in_its_first_reply_and_the_general_one_doesnt():
    """F31 D7: `title`, top level, on a card still an idea; the runner rewrites the heading."""
    text = prompts.PLANNER
    [rule] = [bullet for bullet in text.split("\n- ") if "`title`" in bullet]
    assert "still an idea" in rule and "first reply" in rule
    assert '"title": "…"' in rule and "beside `points`" in rule
    assert "at most 80 characters" in rule and "one line" in rule
    assert "Don't edit the heading yourself" in rule
    assert text.index("`title`") < text.index("```json")
    assert "`title`" not in prompts.PLANNER_GENERAL


def test_a_card_that_changes_a_page_gets_a_today_proposed_mockup_unasked():
    """f72-01: the mock-up is the default for a card with screen changes (F72 D1–D3)."""
    text = prompts.PLANNER
    start = text.index("- A card that changes what a page shows or how it is laid out")
    paragraph = text[start : text.index("\n- ", start)]
    assert start < text.index("```json")
    # When (D1): without being asked, with the exceptions, and a point when skipped
    assert "without being asked" in paragraph and "wording only" in paragraph
    assert "say why in a point" in paragraph
    # What it shows (D2): one file, a Today / Proposed switch, Today copied, real values
    assert "Today / Proposed" in paragraph and ".softfield/cards/{card}-mockup/" in paragraph
    assert "copied from the live template" in paragraph and "real values" in paragraph
    # The example it names for the switch has one (F72's review: f17's has none)
    example = ".softfield/cards/f94-mockup/away-rows.html"
    assert example in paragraph
    assert 'data-show="today"' in (ROOT / example).read_text(encoding="utf-8")
    # Order (D3): with the plan, and the UI tickets point at it
    assert "in the same reply" in paragraph and "in its Context" in paragraph
    # The general thread drafts nothing, so it asks for none (D4)
    assert "mock-up" not in prompts.PLANNER_GENERAL and "Today" not in prompts.PLANNER_GENERAL


def test_a_factory_mockups_proposed_is_drawn_in_the_factory_theme_leaning_bolder():
    """f88-01: Proposed uses the factory theme from dashboard.css's tokens, a little bolder
    than needed (F88 D1, D4), the factory only (D5); the game is never named (D2)."""
    text = prompts.PLANNER
    start = text.index("- A card that changes what a page shows or how it is laid out")
    paragraph = text[start : text.index("\n- ", start)]
    assert "factory theme" in paragraph and "dashboard.css's tokens" in paragraph
    assert "leaning bolder" in paragraph and "the owner tones it down" in paragraph
    assert "nothing copied from a game" in paragraph
    assert "a factory page" in paragraph
    for template in (prompts.PLANNER, prompts.PLANNER_GENERAL):
        assert "endfield" not in template.lower() and "arknights" not in template.lower()


def test_the_planner_prompts_still_fill_in():
    """The new rules add no stray brace: both prompts format with the same fields."""
    for template in (prompts.PLANNER, prompts.PLANNER_GENERAL):
        text = template.format(thread="F7", card="f7", comments="", text="Hi", threads="none")
        assert '{"points": [{"n": 1' in text and "{card}" not in text


def _prompt_texts() -> list[str]:
    texts: list[str] = []
    for value in vars(prompts).values():
        if isinstance(value, str):
            texts.append(value)
        elif isinstance(value, dict):
            texts += [v for v in value.values() if isinstance(v, str)]
    return texts


def test_no_prompt_says_junior(tmp_path: Path):
    """ADR 14 item 1: "junior" became "developer"."""
    texts = [*_prompt_texts(), local_prompt(parse_task(write_task(tmp_path, "m1-01-x"), 1000))]
    assert len(texts) > 10
    assert not [t for t in texts if re.search("junior", t, re.IGNORECASE)]


def test_nothing_in_the_runner_or_opencode_names_junior_md():
    root = Path(__file__).resolve().parents[2]
    assert not (root / "runner/instructions/junior.md").exists()
    assert (root / ".softfield/developer.md").is_file()
    named = [p for p in sorted((root / "runner").rglob("*.py")) if "junior.md" in p.read_text()]
    assert named == []
    instructions = prompts.developer_instructions(root, root)
    assert str(root / ".softfield/developer.md") in instructions
    assert not [i for i in instructions if "junior" in i]


@pytest.mark.parametrize("text", [prompts.PLANNER, prompts.PLANNER_GENERAL])
def test_on_a_duplicate_the_planner_only_merges_and_never_sends_the_owner_elsewhere(text):
    """f49-03 (the owner, 2026-10-13): F107's replies answered in full on a page with no card,
    then asked for a "go" on F73's and F95's. The runner brings the note to the kept card and
    queues the lead there, so the answer and the plan come on that thread."""
    looks = text[text.index("Before answering") : text.index("How to answer")]
    assert "say only which card it repeats" in looks
    assert "brings their note to the kept card's thread and queues you there" in looks
    assert "Never ask the owner to write" in looks and "on another page" in looks


def test_no_prompt_or_re_review_names_a_backlog():
    """ADR 35: a finding is a set-aside bug ticket or a line in the report, never a backlog."""
    texts = [v for k, v in vars(prompts).items() if k.isupper() and isinstance(v, str)]
    assert texts and not [t for t in texts if "backlog" in t.lower()]
    assert "backlog" not in inspect.getsource(milestone._fix_scope).lower()


def test_the_machines_file_replaces_the_authors(tmp_path: Path, monkeypatch):
    """ADR 41 item 4: the author's opinions ship with the package; a user's replace them."""
    _lead_doc(tmp_path, ("Your own work", "Tickets"))
    monkeypatch.setenv("SOFTFIELD_CONFIG", str(tmp_path / "machine" / "factory.toml"))
    (tmp_path / "machine").mkdir()
    assert "- Low ceremony." in prompts.brief(tmp_path, "lead-ticket")[0]
    (tmp_path / "machine" / "owner.md").write_text("# Me\n\n- Lots of ceremony.\n")
    text = prompts.brief(tmp_path, "lead-ticket")[0]
    assert "- Lots of ceremony." in text and "Low ceremony" not in text


def test_known_range_is_read_from_the_authors_file(tmp_path: Path):
    _lead_doc(tmp_path, ("Authority",))
    known = tmp_path / prompts.KNOWN_RANGE_DOC
    known.write_text("## Known range\nQwen does this.\n")
    assert "Qwen does this." in prompts.brief(tmp_path, "escalation")[0]


def test_a_developer_gets_the_factorys_files_then_the_projects(tmp_path: Path):
    """ADR 41 items 2 and 4: a later file wins, so the project's come last."""
    home, repo = tmp_path / "home", tmp_path / "repo"
    for path in (
        home / "runner/instructions/rules.md",
        home / "runner/instructions/developer.md",
        repo / ".softfield/project.md",
        repo / ".softfield/developer.md",
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x")
    assert prompts.developer_instructions(home, repo) == [
        str(home / "runner/instructions/rules.md"),
        str(home / "runner/instructions/developer.md"),
        str(repo / ".softfield/project.md"),
        str(repo / ".softfield/developer.md"),
    ]


def test_a_terminal_lead_session_holds_everything_a_lead_needs(tmp_path: Path):
    _lead_doc(tmp_path, ("Plan", "Tickets"))
    (tmp_path / prompts.KNOWN_RANGE_DOC).write_text("## Known range\nQwen.\n")
    (tmp_path / prompts.CLAUDE_DOC).write_text("# When the lead is Claude\n")
    rules = tmp_path / "project.md"
    rules.write_text("# This project\n")
    text = prompts.lead_session(tmp_path, rules)
    for said in ("Low ceremony", "## Plan", "Qwen.", "When the lead is Claude", "# This project"):
        assert said in text
