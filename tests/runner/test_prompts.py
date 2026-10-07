"""The developer's prompt (ADR 12 item 1): one finish line, last before any retry text."""

import json
import re
from pathlib import Path

import pytest

from runner import prompts
from runner.prompts import local_prompt
from runner.tasks import parse_task
from tests.runner.conftest import write_task


def test_the_finish_line_is_one_check_all_command(tmp_path: Path):
    task = parse_task(write_task(tmp_path, "m1-01-thing"), 1000)
    prompt = local_prompt(task)
    assert prompt.rstrip().endswith(
        "Finish by running `uv run runner check-all --fix --task m1-01-thing` and fixing what it"
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
    for folder in ("docs/adr/", "docs/milestones/{card}-mockup/", "tasks/later/"):
        assert folder in text
    assert "self-contained HTML" in text and "don't commit" in text
    # The approval rule (item 7): nothing queued until the owner approves; only a replan's
    # branch touches tasks/ready/ (f6-13)
    assert "Nothing is queued without their approval" in text
    assert "Only a `replan` may touch tasks/ready/" in text
    # Questions first, every point agreed by default, and push back (owner.md)
    assert text.index("questions and comments first") < text.index("then revise")
    assert "counts as agreed" in text and "Challenge them" in text


def test_the_general_thread_has_no_branch_and_proposes_seeds():
    text = prompts.PLANNER_GENERAL
    assert "plan/" not in text and "change nothing" in text and "`seed`" in text
    assert "Nothing is queued without their approval" in text and "```json" in text


@pytest.mark.parametrize("text", [prompts.PLANNER, prompts.PLANNER_GENERAL])
def test_both_planner_prompts_look_for_duplicates_and_propose_a_merge(text):
    """f6-12: before answering, the cards in docs/milestones/ (idea, planning or ready) and the
    other threads; a repeat is a point and a `merge` proposal, applied only once approved."""
    looks = text.index("Before answering")
    assert "docs/milestones/" in text[looks:] and "idea, planning or ready" in text
    assert "{threads}" in text and "repeats another" in text
    assert "`merge`" in text and '"into"' in text.split("```json", 1)[1]
    assert "once the owner approves" in text
    assert text.index("Before answering") < text.index("```json")


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
    assert not (root / "docs/agents/junior.md").exists()
    assert (root / "docs/agents/developer.md").is_file()
    named = [p for p in sorted((root / "runner").rglob("*.py")) if "junior.md" in p.read_text()]
    assert named == []
    instructions = json.loads((root / "opencode.json").read_text())["instructions"]
    assert "docs/agents/developer.md" in instructions
    assert not [i for i in instructions if "junior" in i]
