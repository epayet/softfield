from datetime import UTC, datetime

import pytest

from runner import agents, claude
from runner.agents import (
    FAILURE,
    LIMIT,
    TRANSIENT,
    Agent,
    JobResult,
    JobSpec,
    Refusal,
    adapter_for,
)

RESETS = datetime(2026, 10, 5, 16, 0, tzinfo=UTC)


def test_a_spec_without_edit_globs_is_read_only():
    assert JobSpec("review", "Review.", timeout=1).read_only
    assert not JobSpec("direction", "Direct.", timeout=1, edit=(".factory/var/runs/**",)).read_only


def test_a_results_error_is_one_of_three_classes():
    """ADR 15 item 12: every adapter's errors come back as a limit, transient or a failure."""
    assert JobResult(ok=True, text="", duration_s=1.0).error is None
    limited = JobResult(ok=False, text="", duration_s=0.0, refusal=Refusal("seven_day", RESETS))
    assert limited.error == LIMIT
    assert JobResult(ok=False, text="", duration_s=0.0, transient=True).error == TRANSIENT
    assert JobResult(ok=False, text="Tool failed", duration_s=1.0).error == FAILURE


def test_a_harness_names_its_adapter():
    assert adapter_for("claude") is claude.ADAPTER
    with pytest.raises(agents.UnknownHarness, match="nope"):
        adapter_for("nope")


def test_an_adapter_runs_an_agent_and_a_spec(tmp_path, monkeypatch):
    """The protocol every harness follows: ``run(agent, spec, repo, log_path, now)``."""
    seen: list[tuple[str, str, int]] = []

    def run_claude(job, repo, timeout, log_path, now, resume=None):
        seen.append((job.kind, job.model, timeout))
        return JobResult(ok=True, text="done", duration_s=1.0)

    monkeypatch.setattr(claude, "run_claude", run_claude)
    agent = Agent("claude-sonnet", "claude", "sonnet", rating=8)
    adapter: agents.Adapter = adapter_for(agent.harness)
    result = adapter.run(
        agent, JobSpec("checkpoint", "Check.", timeout=7), tmp_path, tmp_path, RESETS
    )
    assert result.text == "done"
    assert seen == [("checkpoint", "sonnet", 7)]
