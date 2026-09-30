"""The junior's prompt (ADR 12 item 1): one finish line, last before any retry text."""

from pathlib import Path

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
