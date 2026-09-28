from datetime import UTC, datetime, timedelta

from runner.report import ClaudeRunRecord, SessionReport, TaskRecord, observations, render
from runner.usage import ClaudeUsage

T0 = datetime(2026, 9, 27, 14, 0, tzinfo=UTC)


def _report() -> SessionReport:
    report = SessionReport(started=T0, ended=T0 + timedelta(minutes=30))
    report.tasks = [
        TaskRecord(
            "m1-01-a",
            1,
            "done",
            attempts=1,
            model_s=300,
            tokens_in=1_000_000,
            tokens_out=100_000,
            steps=40,
            warmup_s=35,
        ),
        TaskRecord("m1-02-b", 1, "escalated", attempts=3, gate_failures=["mypy", "mypy", "ruff"]),
    ]
    report.claude_runs = [ClaudeRunRecord("escalation", "m1-02-b", 120, 5000, 800, 20000, True)]
    return report


def test_local_and_claude_tokens_are_compared():
    usage = ClaudeUsage(input=0, cache_write=100_000, cache_read=9_000_000, output=40_000, steps=30)
    text = render(_report(), usage)
    assert "processed **1.1M tokens** (1,000,000 in, 100,000 out) on 2 task(s)" in text
    # 125k writes + 900k reads + 200k output = 1.2M; reads are 73% of it
    assert "Claude spent **≈1.2M token-equivalents** over 30 steps (≈41k a step; 73%" in text
    assert "| `m1-02-b` | escalated | 3 |" in text
    assert "| `m1-01-a` | done | 1 | 35 s | 5.0 min |" in text  # warm-up, then model time
    assert "## Headless Claude runs" in text


def test_observations():
    obs = observations(_report())
    assert "First-attempt pass rate: 1/2." in obs
    assert "Most frequent gate failure: `mypy` (2x)." in obs
    assert any("25,000 tokens" in o for o in obs)
    assert any("cold for 1 task" in o for o in obs)


def test_empty_session():
    assert observations(SessionReport(started=T0)) == ["No tasks ran."]
