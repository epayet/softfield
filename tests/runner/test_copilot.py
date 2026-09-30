import subprocess
from datetime import date

import pytest

from runner.copilot import (
    PROBE_REVIEWS_PER_DAY,
    CopilotError,
    github_get_command,
    probe_review,
    review_command,
)


def test_a_review_is_always_read_only():
    """Deny rules beat every allow in Copilot's CLI, so these can't be widened by a prompt."""
    cmd = review_command("Review runner/loop.py", model="gpt-5-mini")
    assert cmd[:2] == ["copilot", "--prompt=Review runner/loop.py"]
    for tool in ("shell", "write", "url"):
        assert ["--deny-tool", tool] == cmd[cmd.index(tool) - 1 : cmd.index(tool) + 1]
    assert "--disable-builtin-mcps" in cmd  # the GitHub MCP server can write to GitHub
    assert not any(a.startswith(("--allow", "--yolo", "--share", "--add-dir")) for a in cmd)
    assert cmd[cmd.index("--model") + 1] == "gpt-5-mini"


@pytest.mark.parametrize("model", ["--yolo", "a b", "x;rm", ""])
def test_a_model_that_isnt_a_plain_name_is_refused(model):
    with pytest.raises(CopilotError):
        review_command("hi", model=model)


def test_a_prompt_can_never_become_a_flag():
    assert review_command("--yolo", model=None)[1] == "--prompt=--yolo"


def test_no_model_leaves_copilots_default():
    assert "--model" not in review_command("hi", model=None)


def test_github_reads_are_get_only():
    path = "/users/epayet/settings/billing/usage"
    assert github_get_command(path) == ["gh", "api", "--method", "GET", path]


@pytest.mark.parametrize(
    "path", ["users/x", "/a -X POST", "/a/../b", "--method=POST", "/a;b", "/a?x=1&y=2"]
)
def test_github_reads_refuse_anything_but_a_plain_path(path):
    with pytest.raises(CopilotError):
        github_get_command(path)


def test_probe_reviews_are_capped_per_day(tmp_path, monkeypatch):
    """Copilot Free has 50 requests a month; f1's probe needs 3 at most."""
    ran: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        ran.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    today = date(2026, 10, 1)
    for _ in range(PROBE_REVIEWS_PER_DAY):
        probe_review(tmp_path, "hi", None, today)
    with pytest.raises(CopilotError, match="cap"):
        probe_review(tmp_path, "hi", None, today)
    assert len(ran) == PROBE_REVIEWS_PER_DAY
    probe_review(tmp_path, "hi", None, date(2026, 10, 2))  # a new day
    assert len(ran) == PROBE_REVIEWS_PER_DAY + 1
