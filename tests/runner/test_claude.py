import subprocess
from datetime import UTC, datetime, timedelta

import pytest

from runner.claude import (
    STRIPPED_ENV,
    ClaudeJob,
    UsageLimited,
    backoff_seconds,
    claude_env,
    run_claude,
    shell_note,
    usage_limit_reset,
)

NOW = datetime(2026, 9, 27, 14, 0, tzinfo=UTC)


def test_env_never_carries_api_credentials():
    env = {k: "x" for k in STRIPPED_ENV} | {"PATH": "/bin", "HOME": "/home/me"}
    assert claude_env(env) == {"PATH": "/bin", "HOME": "/home/me"}


def test_not_a_limit():
    assert usage_limit_reset("Error: file not found", NOW) == (False, None)


def test_epoch_reset():
    stamp = int((NOW + timedelta(hours=2)).timestamp())
    assert usage_limit_reset(f"Claude AI usage limit reached|{stamp}", NOW) == (
        True,
        NOW + timedelta(hours=2),
    )


def test_clock_reset_later_today_and_tomorrow():
    assert usage_limit_reset("You've hit your limit · resets 5pm", NOW) == (
        True,
        NOW.replace(hour=17),
    )
    assert usage_limit_reset("usage limit reached, resets at 9:30am", NOW) == (
        True,
        (NOW + timedelta(days=1)).replace(hour=9, minute=30),
    )


def test_limit_without_time():
    assert usage_limit_reset("rate limit exceeded", NOW) == (True, None)


def test_backoff_grows_and_caps():
    assert [backoff_seconds(n, 900, 18000) for n in range(6)] == [
        900,
        1800,
        3600,
        7200,
        14400,
        18000,
    ]


def test_path_scoped_write_rules_use_edit(repo, monkeypatch):
    """`Write(<glob>)` grants nothing to claude -p; `Edit(<glob>)` covers Write too."""
    import inspect

    from runner import loop

    source = inspect.getsource(loop)
    assert '"Write(' not in source
    assert '"Edit(var/runs/**)"' in source


def test_a_job_with_bash_is_told_how_to_call_it():
    """f0: headless jobs wrote `cd repo; …`, `git -C` and pipes; the prefix rules denied them
    all, and the escalation concluded it couldn't run checks."""
    note = shell_note(("Read", "Bash(uv run pytest:*)", "Bash(git diff:*)"))
    assert "one command per Bash call" in note
    assert "`uv run pytest`, `git diff`" in note
    assert shell_note(("Read", "Edit")) == ""


def test_run_claude_appends_the_shell_note(tmp_path, monkeypatch):
    seen: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        seen.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout='{"result": "ok"}', stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    job = ClaudeJob(kind="review", prompt="Review.", allowed_tools=("Bash(git log:*)",))
    run_claude(job, tmp_path, 10, tmp_path / "log", NOW)
    prompt = seen[0][seen[0].index("-p") + 1]
    assert prompt.startswith("Review.") and "`git log`" in prompt


def _fake_claude(monkeypatch, stdout: str, returncode: int = 1) -> list[list[str]]:
    seen: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        seen.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    return seen


def test_a_usage_limit_carries_the_session_to_resume(tmp_path, monkeypatch):
    """f1: a lead ticket cut off mid-way resumes its session instead of starting over."""
    out = '{"is_error": true, "result": "You\'ve hit your limit · resets 5pm", "session_id": "s1"}'
    _fake_claude(monkeypatch, out)
    job = ClaudeJob(kind="lead-ticket", prompt="Do it.", allowed_tools=("Read",))
    with pytest.raises(UsageLimited) as limit:
        run_claude(job, tmp_path, 10, tmp_path / "log", NOW)
    assert (limit.value.session_id, limit.value.certain) == ("s1", True)
    assert limit.value.resets_at == NOW.replace(hour=17)


def test_an_unrecognised_limit_is_still_a_pause(tmp_path, monkeypatch):
    """A wording the parser doesn't know shouldn't block a ticket: pause and retry instead."""
    _fake_claude(monkeypatch, '{"is_error": true, "result": "Weekly quota exhausted"}')
    job = ClaudeJob(kind="lead-ticket", prompt="Do it.", allowed_tools=("Read",))
    with pytest.raises(UsageLimited) as limit:
        run_claude(job, tmp_path, 10, tmp_path / "log", NOW)
    assert (limit.value.resets_at, limit.value.certain, limit.value.session_id) == (
        None,
        False,
        None,
    )


def test_an_ordinary_error_is_a_failed_result(tmp_path, monkeypatch):
    _fake_claude(monkeypatch, '{"is_error": true, "result": "Tool failed"}')
    job = ClaudeJob(kind="lead-ticket", prompt="Do it.", allowed_tools=("Read",))
    assert not run_claude(job, tmp_path, 10, tmp_path / "log", NOW).ok


def test_run_claude_can_resume_a_session(tmp_path, monkeypatch):
    seen = _fake_claude(monkeypatch, '{"result": "done", "session_id": "s1"}', returncode=0)
    job = ClaudeJob(kind="lead-ticket", prompt="Carry on.", allowed_tools=("Read",))
    result = run_claude(job, tmp_path, 10, tmp_path / "log", NOW, resume="s1")
    assert seen[0][seen[0].index("--resume") + 1] == "s1"
    assert result.session_id == "s1"
