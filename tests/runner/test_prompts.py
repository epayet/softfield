"""The developer's prompt (ADR 12 item 1): one finish line, last before any retry text."""

import json
import re
from pathlib import Path

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
