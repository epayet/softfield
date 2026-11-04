"""The console's lines (f1-42): each names its agent in brackets and stays short."""

from datetime import UTC, datetime, timedelta

from runner import console


def test_a_ticket_header_names_the_ticket_its_role_and_difficulty():
    assert console.ticket_header("f1-15-agents-page", "developer", 6) == (
        "── f1-15-agents-page · developer · d6 ──"
    )
    assert console.ticket_header("f1-01-x", "lead", None) == "── f1-01-x · lead ──"


def test_a_job_starts_with_its_agent():
    assert console.start("local-qwen3.6-35b-a3b", "attempt 1/3") == (
        "▶ [local-qwen3.6-35b-a3b] attempt 1/3"
    )
    assert console.start("claude-opus", "direction") == "▶ [claude-opus] direction"


def test_a_local_end_line_has_outcome_minutes_tokens_and_steps():
    line = console.local_end("local-m", "attempt 2/3", "failed gate ruff", 14 * 60, 45_230, 31)
    assert line == "■ [local-m] attempt 2/3 failed gate ruff · 14 min · 45.2k tokens · 31 steps"


def test_a_claude_end_line_has_outcome_minutes_and_dollars():
    assert console.claude_end("claude-opus", "direction", True, 190, 0.754) == (
        "■ [claude-opus] direction done · 3 min · $0.75"
    )
    assert console.claude_end("claude-sonnet", "checkpoint", False, 60, None) == (
        "■ [claude-sonnet] checkpoint failed · 1 min"
    )
    assert console.claude_end("claude-opus", "escalation", False, 2700, None, timed_out=True) == (
        "■ [claude-opus] escalation cut off at its time limit · 45 min"
    )


def test_a_summary_is_the_first_real_line_cut_to_about_100_characters():
    assert console.summary("claude-opus", "\n# Requeued\nmore") == "  ↳ [claude-opus] Requeued"
    # f1-51: the owner read cut lines; the whole first line prints.
    assert console.summary("claude-opus", "x" * 300 + "\nmore") == "  ↳ [claude-opus] " + "x" * 300
    assert console.summary("claude-opus", " \n") is None


def test_progress_lines():
    assert console.local_progress("local-m", "attempt 1/3", 600, 12_000, 40, 3) == (
        "… [local-m] attempt 1/3 · 10 min · 12.0k tokens · 40 steps · edit streak 3"
    )
    assert console.running("claude-opus", "review", 1200) == (
        "… [claude-opus] review still running · 20 min"
    )


def test_long_durations_read_in_hours():
    assert console.duration(3 * 3600 + 5 * 60) == "3 h 05"
    assert console.duration(59 * 60) == "59 min"


def test_a_merge_names_the_merger_attempts_lines_and_duration():
    assert console.merged("local-m", "f1-15-x", 1, 42, 16 * 60) == (
        "✔ [local-m] f1-15-x merged · 1 attempt · 42 lines · 16 min"
    )
    assert console.merged("claude-opus", "f1-01-x", 2, None, 60) == (
        "✔ [claude-opus] f1-01-x merged · 2 attempts · 1 min"
    )


def test_a_stop_says_why_where_and_how_many_wait():
    line = console.stopped("f1-01-x", "blocked", "check-all failed", "work on task/f1-01-x", 2)
    assert line == (
        "⚠ [runner] f1-01-x blocked: check-all failed · work on task/f1-01-x"
        " · 2 tickets wait behind it"
    )
    assert console.stopped("f1-01-x", "escalated", "r", "logs in x", 1).endswith(
        "1 ticket waits behind it"
    )
    assert console.stopped("f1-01-x", "escalated", "r", "logs in x", 0).endswith("nothing waits")


def test_a_pause_gives_the_exact_resume_time():
    now = datetime(2026, 10, 1, 18, 39)
    line = console.paused("claude-opus", "Claude usage limit", now + timedelta(minutes=12), now)
    assert line == "⏸ [claude-opus] Claude usage limit · resumes 18:51 (in 12 min)"
    tomorrow = console.paused("claude-opus", "limit", now + timedelta(hours=15), now)
    assert "resumes Fri 09:39 (in 15 h 00)" in tomorrow
    assert console.resumed("claude-opus", "direction") == "▶ [claude-opus] direction resumed"


def test_a_resume_time_and_its_day_are_on_the_machines_clock(paris):
    """F187: 22:30 UTC is 23:30 in Paris, so an hour on is tomorrow there, and today in UTC."""
    now = datetime(2026, 10, 29, 22, 30, tzinfo=UTC)
    soon = console.paused("claude-opus", "limit", now + timedelta(minutes=12), now)
    assert "resumes 23:42 (in 12 min)" in soon
    tomorrow = console.paused("claude-opus", "limit", now + timedelta(hours=1), now)
    assert "resumes Fri 00:30" in tomorrow
