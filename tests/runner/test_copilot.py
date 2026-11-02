import json
import subprocess
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from runner import copilot
from runner.agents import FAILURE, LIMIT, TRANSIENT, Agent, JobSpec, adapter_for
from runner.copilot import (
    PROBE_REVIEWS_PER_DAY,
    CopilotError,
    github_get_command,
    probe_review,
    review_command,
)

FIXTURE = Path(__file__).parent / "fixtures" / "probes" / "copilot-review.txt"
NOW = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
AGENT = Agent("copilot-auto", "copilot", "auto", rating=6)
QUOTA = {
    "access_type_sku": "free_limited_copilot",
    "quota_reset_date": "2026-11-01",
    "quota_snapshots": {
        "chat": {"entitlement": 200, "quota_remaining": 199.6, "percent_remaining": 99.8},
        "completions": {"entitlement": 2000, "percent_remaining": 100.0},
    },
}
NOT_AVAILABLE = 'Error: Model "gpt-5-mini" from --model flag is not available.\n'


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


def fake_copilot(monkeypatch, *, code=0, stdout="", stderr="", quota=QUOTA, gh_code=0):
    """Fakes both subprocesses: the Copilot job, then the quota read through ``gh api``."""
    ran: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        ran.append(cmd)
        if cmd[0] == "gh":
            return subprocess.CompletedProcess(cmd, gh_code, stdout=json.dumps(quota), stderr="")
        assert kwargs["stdin"] == subprocess.DEVNULL  # --no-ask-user, and nothing to answer
        if isinstance(code, BaseException):
            raise code
        return subprocess.CompletedProcess(cmd, code, stdout=stdout, stderr=stderr)

    monkeypatch.setattr(subprocess, "run", fake_run)
    return ran


def review(tmp_path, spec=None):
    spec = spec or JobSpec("checkpoint-shadow", "Review the last merges.", timeout=60)
    return adapter_for("copilot").run(AGENT, spec, tmp_path, tmp_path / "log.txt", NOW)


def test_the_copilot_harness_is_this_module():
    assert adapter_for("copilot") is copilot.ADAPTER


def test_a_read_only_spec_runs_with_shell_and_write_denied(tmp_path, monkeypatch):
    ran = fake_copilot(monkeypatch, stdout=FIXTURE.read_text(encoding="utf-8"))
    review(tmp_path)
    cmd = ran[0]
    assert cmd[:2] == ["copilot", "--prompt=Review the last merges."]
    assert cmd[cmd.index("--model") + 1] == "auto"
    for tool in ("shell", "write", "url"):
        assert ["--deny-tool", tool] == cmd[cmd.index(tool) - 1 : cmd.index(tool) + 1]
    assert "--disable-builtin-mcps" in cmd
    for flag in ("--no-custom-instructions", "--no-ask-user", "--no-auto-update"):
        assert flag in cmd
    assert not any(a.startswith(("--allow", "--yolo", "--share", "--add-dir")) for a in cmd)


def test_a_specs_commands_never_lift_the_denials(tmp_path, monkeypatch):
    """Copilot gets no shell whatever the spec says: its commands aren't granted."""
    ran = fake_copilot(monkeypatch, stdout="ok")
    review(tmp_path, JobSpec("review", "Review.", timeout=60, commands=("git diff",)))
    assert ran[0][ran[0].index("shell") - 1 : ran[0].index("shell") + 1] == ["--deny-tool", "shell"]
    assert not any("git diff" in a for a in ran[0][2:])


@pytest.mark.parametrize("edit", [("**",), (".softfield/var/runs/**",)])
def test_a_spec_asking_for_edits_is_refused_before_running(tmp_path, monkeypatch, edit):
    ran = fake_copilot(monkeypatch)
    with pytest.raises(CopilotError, match="read-only"):
        review(tmp_path, JobSpec("checkpoint", "Check.", timeout=60, edit=edit))
    assert ran == []


def test_the_probes_output_is_the_results_text_and_one_request(tmp_path, monkeypatch):
    fake_copilot(monkeypatch, stdout=FIXTURE.read_text(encoding="utf-8"))
    result = review(tmp_path)
    assert result.ok and result.error is None
    assert result.text.startswith("- **`runner/copilot.py:51-55`**")
    assert result.text.endswith("I can’t provide the exact underlying model name.")
    assert result.requests == 1.0
    assert "runner/copilot.py:51-59" in (tmp_path / "log.txt").read_text(encoding="utf-8")


def test_the_quota_after_a_job_is_a_month_reading(tmp_path, monkeypatch):
    ran = fake_copilot(monkeypatch, stdout="ok")
    (reading,) = review(tmp_path).readings
    assert ran[1] == ["gh", "api", "--method", "GET", "/copilot_internal/user"]
    assert reading.window == "month"
    assert reading.utilization == pytest.approx(0.002)
    assert reading.resets_at == datetime(2026, 11, 1, tzinfo=UTC)


@pytest.mark.parametrize(
    ("quota", "gh_code"),
    [
        (QUOTA, 1),  # gh failed: not logged in, offline, a 404
        ({"message": "Not Found"}, 0),
        ({**QUOTA, "quota_reset_date": "soon"}, 0),
        ({**QUOTA, "quota_snapshots": {"chat": {"percent_remaining": "lots"}}}, 0),
    ],
)
def test_a_quota_that_doesnt_answer_gives_no_reading(tmp_path, monkeypatch, quota, gh_code):
    fake_copilot(monkeypatch, stdout="ok", quota=quota, gh_code=gh_code)
    result = review(tmp_path)
    assert result.ok and result.readings == ()


def test_the_quota_read_is_a_plain_get(monkeypatch):
    ran = fake_copilot(monkeypatch)
    assert copilot.quota_reading(Path(".")) is not None
    assert ran == [github_get_command("/copilot_internal/user")]


def test_an_unavailable_model_is_a_failure(tmp_path, monkeypatch):
    """A config mistake, not a refusal: Copilot fails at once, before any credit is spent."""
    fake_copilot(monkeypatch, code=1, stderr=NOT_AVAILABLE)
    result = review(tmp_path)
    assert result.error == FAILURE
    assert "not available" in result.text
    assert result.requests == 0.0


def test_an_unrecognised_error_is_a_limit_with_no_reset(tmp_path, monkeypatch):
    """No Copilot refusal has been seen (f1-18): an unknown error may be one."""
    fake_copilot(monkeypatch, code=1, stderr="Error: something went wrong\n")
    result = review(tmp_path)
    assert result.error == LIMIT
    assert result.refusal is not None
    assert result.refusal.resets_at is None and not result.refusal.certain


def test_an_error_naming_a_limit_is_a_certain_limit(tmp_path, monkeypatch):
    fake_copilot(monkeypatch, code=1, stderr="Error: You've reached your monthly usage limit.\n")
    result = review(tmp_path)
    assert result.error == LIMIT
    assert result.refusal is not None and result.refusal.certain


def test_a_lost_connection_is_transient(tmp_path, monkeypatch):
    fake_copilot(monkeypatch, code=1, stderr="Error: connect ECONNRESET 140.82.112.21:443\n")
    assert review(tmp_path).error == TRANSIENT


def test_a_timeout_is_a_failure(tmp_path, monkeypatch):
    fake_copilot(monkeypatch, code=subprocess.TimeoutExpired("copilot", 60))
    result = review(tmp_path)
    assert result.error == FAILURE and result.timed_out
