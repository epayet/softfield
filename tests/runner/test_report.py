from datetime import UTC, datetime, timedelta

from runner.config import Price
from runner.report import ClaudeRunRecord, SessionReport, TaskRecord, observations, render

T0 = datetime(2026, 9, 27, 14, 0, tzinfo=UTC)
PRICES = {"Claude Sonnet 5": Price(input=2.0, output=10.0)}


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


def test_savings_are_priced_from_local_tokens():
    text = render(_report(), PRICES)
    # 1M in * $2 + 0.1M out * $10 = $3.00
    assert "- Claude Sonnet 5: **$3.00**" in text
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
