import json
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from runner import claude
from runner.agents import (
    ANY,
    CHECK_COMMANDS,
    FAILURE,
    GIT_READ_COMMANDS,
    LIMIT,
    TRANSIENT,
    Agent,
    JobResult,
    JobSpec,
    Reading,
    Refusal,
)
from runner.claude import (
    ADAPTER,
    STRIPPED_ENV,
    ClaudeJob,
    Progress,
    TransientError,
    UsageLimited,
    allowed_tools,
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


def test_path_scoped_write_rules_use_edit():
    """`Write(<glob>)` grants nothing to claude -p; `Edit(<glob>)` covers Write too."""
    tools = allowed_tools(
        JobSpec("direction", "Direct.", timeout=1, edit=(".softfield/var/runs/**",))
    )
    assert "Edit(.softfield/var/runs/**)" in tools
    assert not [t for t in tools if t.startswith("Write")]


# Today's jobs' --allowedTools, as they were written out before the neutral spec (f1-20).
_READ = ("Read", "Glob", "Grep")
_EDIT = (*_READ, "Edit", "Write")
_CHECK = (
    "Bash(uv run pytest:*)",
    "Bash(uv run ruff:*)",
    "Bash(uv run mypy:*)",
    "Bash(softfield check-all:*)",
)
_GIT = ("Bash(git diff:*)", "Bash(git log:*)", "Bash(git show:*)")


@pytest.mark.parametrize(
    ("spec", "today"),
    [
        (
            JobSpec(
                "direction", "", 1, edit=(".softfield/var/runs/**",), commands=GIT_READ_COMMANDS
            ),
            (*_READ, *_GIT, "Edit(.softfield/var/runs/**)"),
        ),
        (
            JobSpec(
                "lead-ticket",
                "",
                1,
                edit=(ANY,),
                commands=(*CHECK_COMMANDS, *GIT_READ_COMMANDS, "gh api"),
            ),
            (*_EDIT, *_CHECK, *_GIT, "Bash(gh api:*)"),
        ),
        (
            JobSpec(
                "checkpoint",
                "",
                1,
                edit=(
                    ".softfield/tasks/ready/**",
                    ".softfield/developer.md",
                    ".softfield/var/runs/**",
                ),
                commands=(*GIT_READ_COMMANDS, "uv run pytest"),
            ),
            (
                *_READ,
                *_GIT,
                "Bash(uv run pytest:*)",
                "Edit(.softfield/tasks/ready/**)",
                "Edit(.softfield/developer.md)",
                "Edit(.softfield/var/runs/**)",
            ),
        ),
        (
            JobSpec(
                "escalation",
                "",
                1,
                edit=(ANY,),
                commands=(*CHECK_COMMANDS, *GIT_READ_COMMANDS, "git checkout task/x"),
            ),
            (*_EDIT, *_CHECK, *_GIT, "Bash(git checkout task/x:*)"),
        ),
        (
            JobSpec("review", "", 1, edit=(ANY,), commands=(*CHECK_COMMANDS, *GIT_READ_COMMANDS)),
            (*_EDIT, *_CHECK, *_GIT),
        ),
        (JobSpec("narrative", "", 1, edit=(ANY,)), _EDIT),
        (JobSpec("review", "", 1), _READ),
    ],
)
def test_a_spec_becomes_the_same_allowed_tools_as_todays_jobs(spec, today):
    tools = allowed_tools(spec)
    assert sorted(tools) == sorted(today)
    assert len(set(tools)) == len(tools)


def _adapter_run(tmp_path, spec: JobSpec, model: str = "opus") -> JobResult:
    agent = Agent("claude-opus", "claude", model, rating=9)
    return ADAPTER.run(agent, spec, tmp_path, tmp_path / "log", NOW)


def test_the_adapter_runs_the_agents_model_with_the_specs_tools(tmp_path, monkeypatch):
    seen = _fake_claude(monkeypatch, '{"result": "ok", "session_id": "s1"}', returncode=0)
    spec = JobSpec("review", "Review.", 10, commands=GIT_READ_COMMANDS, resume="s0")
    result = _adapter_run(tmp_path, spec, model="sonnet")
    cmd = seen[0]
    assert cmd[cmd.index("--model") + 1] == "sonnet"
    assert cmd[cmd.index("--resume") + 1] == "s0"
    assert cmd[cmd.index("--allowedTools") + 1 :] == [*_READ, *_GIT]
    assert "`git diff`, `git log`, `git show`" in cmd[cmd.index("-p") + 1]  # the shell note
    assert (result.ok, result.error, result.session_id) == (True, None, "s1")


def test_every_job_may_read_softfields_shared_docs_and_only_read_them(tmp_path, monkeypatch):
    """ADR 30 item 4: a project's lead job reads lead.md, task-format.md and the rest from the
    Softfield checkout it runs from, outside the project; its edits stay the spec's."""
    home = tmp_path / "live"
    (home / "docs").mkdir(parents=True)
    monkeypatch.setattr("runner.config.HOME", home)
    monkeypatch.setattr("runner.config.INSTRUCTIONS", home / "runner" / "instructions")
    seen = _fake_claude(monkeypatch, '{"result": "ok", "session_id": "s1"}', returncode=0)
    _adapter_run(tmp_path, JobSpec("review", "Review.", 10, commands=GIT_READ_COMMANDS))
    cmd = seen[0]
    dirs = [cmd[i + 1] for i, arg in enumerate(cmd) if arg == "--add-dir"]
    assert dirs == [str(home / "runner" / "instructions"), str(home / "docs")]
    assert [t for t in cmd if t.startswith(("Edit", "Write"))] == []


def test_a_usage_limit_message_comes_back_as_a_refusal_with_its_reset(tmp_path, monkeypatch):
    out = '{"is_error": true, "result": "You\'ve hit your limit · resets 5pm", "session_id": "s1"}'
    _fake_claude(monkeypatch, out)
    result = _adapter_run(tmp_path, JobSpec("lead-ticket", "Do it.", 10))
    assert (result.ok, result.error, result.session_id) == (False, LIMIT, "s1")
    assert result.refusal == Refusal(None, NOW.replace(hour=17))


def test_a_refusal_keeps_its_window_and_readings(tmp_path, monkeypatch):
    windows = {"five_hour": {"utilization": 1.0, "resetsAt": 1790883600}}
    stream = "\n".join(
        [
            _event(status="rejected", rateLimitType="five_hour", unifiedWindows=windows),
            '{"type": "result", "is_error": true, "api_error_status": 429, "result": "Slow"}',
        ]
    )
    _fake_stream(monkeypatch, stream, returncode=1)
    result = _adapter_run(tmp_path, JobSpec("lead-ticket", "Do it.", 10))
    assert result.refusal == Refusal("five_hour", None)
    assert [r.window for r in result.readings] == ["five_hour"]


def test_an_unrecognised_limit_is_an_uncertain_refusal(tmp_path, monkeypatch):
    _fake_claude(monkeypatch, '{"is_error": true, "result": "Weekly quota exhausted"}')
    result = _adapter_run(tmp_path, JobSpec("lead-ticket", "Do it.", 10))
    assert result.refusal == Refusal(None, None, certain=False)


def test_a_dropped_connection_is_transient_and_an_ordinary_error_a_failure(tmp_path, monkeypatch):
    _fake_claude(monkeypatch, "Error: getaddrinfo ENOTFOUND api.anthropic.com")
    assert _adapter_run(tmp_path, JobSpec("review", "Review.", 10)).error == TRANSIENT
    _fake_claude(monkeypatch, '{"is_error": true, "result": "Tool failed"}')
    failed = _adapter_run(tmp_path, JobSpec("review", "Review.", 10))
    assert (failed.error, failed.text) == (FAILURE, "Tool failed")


def test_a_job_with_bash_is_told_how_to_call_it():
    """f0: headless jobs wrote `cd repo; …`, `git -C` and pipes; the prefix rules denied them
    all, and the escalation concluded it couldn't run checks."""
    note = shell_note(("Read", "Bash(uv run pytest:*)", "Bash(git diff:*)"))
    assert "one command per Bash call" in note
    assert "`uv run pytest`, `git diff`" in note
    assert shell_note(("Read", "Edit")) == ""
    # f31-03 (2026-10-12): it ran check-all in the background, couldn't watch it (Monitor is
    # denied in a headless job) and ended its turn before the result
    assert "in the foreground" in note
    assert "background" in note


def test_run_claude_appends_the_shell_note(tmp_path, monkeypatch):
    seen = _fake_stream(monkeypatch, '{"type": "result", "result": "ok"}')
    job = ClaudeJob(kind="review", prompt="Review.", allowed_tools=("Bash(git log:*)",))
    run_claude(job, tmp_path, 10, tmp_path / "log", NOW)
    prompt = seen[0][seen[0].index("-p") + 1]
    assert prompt.startswith("Review.") and "`git log`" in prompt


def test_claude_runs_without_api_credentials_or_a_terminal(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-never")
    calls: list[dict[str, object]] = []

    def fake(cmd, cwd, timeout, out_path, on_tick=None, **kwargs):
        calls.append(kwargs)
        out_path.write_text('{"type": "result", "result": "ok"}', encoding="utf-8")
        return "", 0

    monkeypatch.setattr(claude, "run_streaming", fake)
    run_claude(ClaudeJob("review", "Review.", ("Read",)), tmp_path, 10, tmp_path / "log", NOW)
    env = calls[0]["env"]
    assert isinstance(env, dict) and "ANTHROPIC_API_KEY" not in env
    assert calls[0]["stdin"] == subprocess.DEVNULL


def _assistant(message: str, inp: int, cached: int, out: int) -> str:
    usage = {"input_tokens": inp, "cache_read_input_tokens": cached, "output_tokens": out}
    return json.dumps({"type": "assistant", "message": {"id": message, "usage": usage}})


def test_a_running_job_hands_on_its_tokens_and_turns_so_far(tmp_path, monkeypatch):
    """f1-51: Claude jobs showed elapsed time only. A message's content blocks come as
    separate events with the same id; it counts once, with its latest usage."""
    chunks = [
        [_assistant("m1", 2, 100, 5), _assistant("m1", 2, 100, 7)],
        [_assistant("m2", 3, 200, 11)],
        ['{"type": "result", "result": "ok", "num_turns": 2}'],
    ]

    def fake(cmd, cwd, timeout, out_path, on_tick=None, **kwargs):
        with out_path.open("w", encoding="utf-8") as out:
            for chunk in chunks:
                out.write("".join(f"{line}\n" for line in chunk))
                out.flush()
                if on_tick is not None and chunk is not chunks[-1]:
                    on_tick()
        return "", 0

    monkeypatch.setattr(claude, "run_streaming", fake)
    seen: list[Progress] = []
    job = ClaudeJob("lead-ticket", "Do it.", ("Read",), on_progress=seen.append)
    result = run_claude(job, tmp_path, 10, tmp_path / "log", NOW)
    assert seen == [Progress(2, 100, 7, 1), Progress(5, 300, 18, 2)]
    assert (result.ok, result.num_turns) == (True, 2)


def test_a_job_that_times_out_keeps_its_stream_in_the_log(tmp_path, monkeypatch):
    def fake(cmd, cwd, timeout, out_path, on_tick=None, **kwargs):
        out_path.write_text(_assistant("m1", 1, 0, 1) + "\n", encoding="utf-8")
        return "", None

    monkeypatch.setattr(claude, "run_streaming", fake)
    result = run_claude(ClaudeJob("review", "R.", ("Read",)), tmp_path, 10, tmp_path / "log", NOW)
    assert (result.ok, result.text) == (False, "timed out")
    log = (tmp_path / "log").read_text(encoding="utf-8")
    assert log.startswith('{"type": "assistant"') and log.endswith("--- timed out ---\n")
    assert result.timed_out and result.session_id is None  # no init event in this stream


def test_a_job_cut_off_at_its_limit_keeps_its_session_for_the_resume(tmp_path, monkeypatch):
    """f17-01's escalation was cut off at 45 min: its session, from the stream's `init`."""
    init = json.dumps({"type": "system", "subtype": "init", "session_id": "s9"})

    def fake(cmd, cwd, timeout, out_path, on_tick=None, **kwargs):
        out_path.write_text(init + "\n" + _assistant("m1", 1, 0, 1) + "\n", encoding="utf-8")
        return "", None

    monkeypatch.setattr(claude, "run_streaming", fake)
    job = ClaudeJob("escalation", "E.", ("Read",))
    result = run_claude(job, tmp_path, 10, tmp_path / "log", NOW)
    assert (result.ok, result.timed_out, result.session_id) == (False, True, "s9")
    assert claude.stream_session(["not json", "[1]", init]) == "s9"


def _as_result_event(stdout: str) -> str:
    """A JSON object as stream-json's last line, the `result` event; anything else as is."""
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return stdout
    return json.dumps(data | {"type": "result"}) if isinstance(data, dict) else stdout


def _fake_claude(monkeypatch, stdout: str, returncode: int = 1) -> list[list[str]]:
    return _fake_stream(monkeypatch, _as_result_event(stdout), returncode)


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


def test_run_claude_reads_the_jobs_cost(tmp_path, monkeypatch):
    """f1 D7: savings are in dollars, from Claude Code's own `total_cost_usd`."""
    _fake_claude(monkeypatch, '{"result": "ok", "total_cost_usd": 1.25}', returncode=0)
    job = ClaudeJob(kind="review", prompt="Review.", allowed_tools=("Read",))
    assert run_claude(job, tmp_path, 10, tmp_path / "log", NOW).cost_usd == 1.25
    _fake_claude(monkeypatch, '{"result": "ok"}', returncode=0)
    assert run_claude(job, tmp_path, 10, tmp_path / "log", NOW).cost_usd is None


def test_run_claude_can_resume_a_session(tmp_path, monkeypatch):
    seen = _fake_claude(monkeypatch, '{"result": "done", "session_id": "s1"}', returncode=0)
    job = ClaudeJob(kind="lead-ticket", prompt="Carry on.", allowed_tools=("Read",))
    result = run_claude(job, tmp_path, 10, tmp_path / "log", NOW, resume="s1")
    assert seen[0][seen[0].index("--resume") + 1] == "s1"
    assert result.session_id == "s1"


# f1 (2026-09-30): the real message, which the old pattern missed ("hit your session limit"),
# so the runner guessed 15 min and would have failed the job after three guesses.
SESSION_LIMIT = (
    '{"is_error": true, "terminal_reason": "api_error", "api_error_status": 429,'
    ' "result": "You\'ve hit your session limit · resets 6:50pm (Europe/London)",'
    ' "session_id": "s1"}'
)


def test_the_session_limit_message_resets_at_its_time_in_its_zone(tmp_path, monkeypatch):
    _fake_claude(monkeypatch, SESSION_LIMIT)
    job = ClaudeJob(kind="lead-ticket", prompt="Do it.", allowed_tools=("Read",))
    with pytest.raises(UsageLimited) as limit:
        run_claude(job, tmp_path, 10, tmp_path / "log", NOW)
    assert limit.value.certain and limit.value.session_id == "s1"
    assert limit.value.resets_at == datetime(2026, 9, 27, 17, 50, tzinfo=UTC)  # 18:50 BST


def test_a_429_is_a_limit_whatever_it_says(tmp_path, monkeypatch):
    """The status is structured; the wording may change again."""
    out = '{"is_error": true, "api_error_status": 429, "result": "Slow down, friend"}'
    _fake_claude(monkeypatch, out)
    job = ClaudeJob(kind="lead-ticket", prompt="Do it.", allowed_tools=("Read",))
    with pytest.raises(UsageLimited) as limit:
        run_claude(job, tmp_path, 10, tmp_path / "log", NOW)
    assert (limit.value.certain, limit.value.resets_at) == (True, None)


@pytest.mark.parametrize(
    "stdout",
    [
        '{"is_error": true, "terminal_reason": "api_error", "api_error_status": 529,'
        ' "result": "Overloaded", "session_id": "s1"}',
        '{"is_error": true, "terminal_reason": "api_error", "api_error_status": null,'
        ' "result": "Connection error.", "session_id": "s1"}',
        "Error: getaddrinfo ENOTFOUND api.anthropic.com",
    ],
)
def test_a_dropped_connection_or_overload_is_transient(tmp_path, monkeypatch, stdout):
    _fake_claude(monkeypatch, stdout)
    job = ClaudeJob(kind="review", prompt="Review.", allowed_tools=("Read",))
    with pytest.raises(TransientError):
        run_claude(job, tmp_path, 10, tmp_path / "log", NOW)


# --- Claude's allowance, read from the stream (ADR 15 item 3) ------------------------------

PROBE = Path(__file__).parent / "fixtures" / "probes" / "claude-stream.jsonl"


def _fake_stream(monkeypatch, stdout: str, returncode: int = 0) -> list[list[str]]:
    """`claude -p` faked: its stream is ``stdout``, written to the log as it would come."""
    seen: list[list[str]] = []

    def fake(cmd, cwd, timeout, out_path, on_tick=None, **kwargs):
        seen.append(cmd)
        out_path.write_text(stdout, encoding="utf-8")
        return "", returncode

    monkeypatch.setattr(claude, "run_streaming", fake)
    return seen


def _event(**info: object) -> str:
    return json.dumps({"type": "rate_limit_event", "rate_limit_info": info})


def test_the_probes_stream_gives_two_readings_and_the_same_result(tmp_path, monkeypatch):
    stream = PROBE.read_text(encoding="utf-8")
    seen = _fake_stream(monkeypatch, stream)
    job = ClaudeJob(kind="review", prompt="Review.", allowed_tools=("Read",))
    result = run_claude(job, tmp_path, 10, tmp_path / "log", NOW)
    cmd = seen[0]
    assert cmd[cmd.index("--output-format") + 1] == "stream-json" and "--verbose" in cmd
    assert result.readings == (
        Reading("five_hour", 0.07, datetime.fromtimestamp(1790883600, UTC)),
        Reading("seven_day", 0.79, datetime.fromtimestamp(1791216000, UTC)),
    )
    assert (result.ok, result.text, result.num_turns) == (True, "ok", 1)
    assert result.session_id == "0428228a-1618-4c41-b260-c06665913372"
    assert result.cost_usd == pytest.approx(0.0180713)
    assert result.usage == {
        "input_tokens": 10,
        "output_tokens": 48,
        "cache_read_input_tokens": 12413,
        "cache_creation_input_tokens": 8290,
    }
    assert (tmp_path / "log").read_text(encoding="utf-8").startswith(stream)
    assert result.model == "claude-haiku-4-5-20251001"  # its only `modelUsage`


def test_a_probe_is_one_short_haiku_call_with_no_tools_and_reads_the_windows(tmp_path, monkeypatch):
    """f4-07: the cheapest fresh reading. The fixture is a real one: Haiku answering "ok"
    cost $0.018 (API-equivalent) and its stream carried the `rate_limit_event` first."""
    seen = _fake_stream(monkeypatch, PROBE.read_text(encoding="utf-8"))
    result = claude.probe(tmp_path, tmp_path / "log", NOW)
    [cmd] = seen
    assert cmd[cmd.index("--model") + 1] == "haiku"
    # No tool granted, and in dontAsk mode every tool not granted is denied.
    assert "--allowedTools" not in cmd and "Shell:" not in cmd[2]
    assert cmd[cmd.index("--permission-mode") + 1] == "dontAsk"
    assert len(cmd[2]) < 100
    assert [(r.window, r.utilization) for r in result.readings] == [
        ("five_hour", 0.07),
        ("seven_day", 0.79),
    ]
    assert result.ok and result.cost_usd == pytest.approx(0.0180713)


@pytest.mark.parametrize(
    ("stream", "returncode"),
    [
        (
            _event(
                status="rejected",
                rateLimitType="five_hour",
                resetsAt=1790883600,
                unifiedWindows={"five_hour": {"utilization": 1.0, "resetsAt": 1790883600}},
            )
            + '\n{"type": "result", "is_error": true, "api_error_status": 429, "result": "x"}',
            1,
        ),
        ("Error: getaddrinfo ENOTFOUND api.anthropic.com", 1),
    ],
)
def test_a_probe_never_raises_and_keeps_what_it_read(tmp_path, monkeypatch, stream, returncode):
    """A refused probe or a passing error is a failed probe, with whatever its stream read."""
    _fake_stream(monkeypatch, stream, returncode)
    result = claude.probe(tmp_path, tmp_path / "log", NOW)
    assert not result.ok
    assert [r.utilization for r in result.readings] == ([1.0] if "rejected" in stream else [])


def _message_from(model: str, parent: str | None = None) -> str:
    message = {"id": f"msg-{model}", "model": model, "usage": {"output_tokens": 1}}
    return json.dumps({"type": "assistant", "message": message, "parent_tool_use_id": parent})


RESULT = json.dumps(
    {
        "type": "result",
        "result": "ok",
        "modelUsage": {"claude-haiku-4-5": {"costUSD": 0.01}, "claude-opus-5-5": {"costUSD": 2}},
    }
)


def test_a_job_records_the_model_its_stream_names_not_the_alias(tmp_path, monkeypatch):
    """f2-04: run 20261002-055804's lead ticket ran `--model opus` on claude-opus-5-5."""
    init = json.dumps({"type": "system", "subtype": "init", "model": "claude-opus-5-5"})
    stream = "\n".join([init, _message_from("claude-haiku-4-5", parent="toolu_1"), RESULT])
    _fake_stream(monkeypatch, stream)
    result = _adapter_run(tmp_path, JobSpec("lead-ticket", "Do it.", 10), model="opus")
    assert result.model == "claude-opus-5-5"


def test_without_an_init_event_the_main_threads_model_counts_not_a_subagents():
    stream = [_message_from("claude-haiku-4-5", parent="t1"), _message_from("claude-sonnet-5-5")]
    assert claude.stream_model([*stream, RESULT]) == "claude-sonnet-5-5"


def test_a_plain_json_result_names_its_costliest_model():
    """f1's logs (`--output-format json`) hold one result, with `modelUsage` only."""
    assert claude.stream_model([RESULT]) == "claude-opus-5-5"
    assert claude.stream_model(['{"result": "ok"}', "not json", "[1]"]) is None


def test_every_rate_limit_event_is_returned(tmp_path, monkeypatch):
    windows = {"five_hour": {"utilization": 0.5, "resetsAt": 1790883600}}
    later = {"five_hour": {"utilization": 0.6, "resetsAt": 1790883600}}
    stream = "\n".join(
        [
            _event(status="allowed", unifiedWindows=windows),
            '{"type": "assistant", "message": {}}',
            _event(status="allowed", unifiedWindows=later),
            '{"type": "result", "result": "ok", "is_error": false}',
        ]
    )
    _fake_stream(monkeypatch, stream)
    job = ClaudeJob(kind="review", prompt="Review.", allowed_tools=("Read",))
    readings = run_claude(job, tmp_path, 10, tmp_path / "log", NOW).readings
    assert [(r.window, r.utilization) for r in readings] == [("five_hour", 0.5), ("five_hour", 0.6)]


def test_a_429_in_a_stream_is_a_limit_with_its_session_and_window(tmp_path, monkeypatch):
    windows = {"five_hour": {"utilization": 1.0, "resetsAt": 1790883600}}
    stream = "\n".join(
        [
            _event(
                status="rejected",
                rateLimitType="five_hour",
                resetsAt=1790883600,
                unifiedWindows=windows,
            ),
            '{"type": "result", "is_error": true, "api_error_status": 429,'
            ' "result": "Slow down", "session_id": "s1"}',
        ]
    )
    _fake_stream(monkeypatch, stream, returncode=1)
    job = ClaudeJob(kind="lead-ticket", prompt="Do it.", allowed_tools=("Read",))
    with pytest.raises(UsageLimited) as limit:
        run_claude(job, tmp_path, 10, tmp_path / "log", NOW)
    assert (limit.value.session_id, limit.value.certain) == ("s1", True)
    assert limit.value.window == "five_hour"
    assert limit.value.resets_at == datetime.fromtimestamp(1790883600, UTC)
    assert [r.window for r in limit.value.readings] == ["five_hour"]


def test_a_429_without_a_rejected_event_names_no_window(tmp_path, monkeypatch):
    """The probe's warning names the week; that says nothing about which window refused."""
    warning = PROBE.read_text(encoding="utf-8").splitlines()[0]
    _fake_stream(monkeypatch, f"{warning}\n{_as_result_event(SESSION_LIMIT)}", returncode=1)
    job = ClaudeJob(kind="lead-ticket", prompt="Do it.", allowed_tools=("Read",))
    with pytest.raises(UsageLimited) as limit:
        run_claude(job, tmp_path, 10, tmp_path / "log", NOW)
    assert limit.value.window is None
    assert limit.value.resets_at == datetime(2026, 9, 27, 17, 50, tzinfo=UTC)


@pytest.mark.parametrize("returncode", [0, 1])
def test_a_stream_with_no_result_event_is_transient(tmp_path, monkeypatch, returncode):
    _fake_stream(monkeypatch, PROBE.read_text(encoding="utf-8").splitlines()[0], returncode)
    job = ClaudeJob(kind="review", prompt="Review.", allowed_tools=("Read",))
    with pytest.raises(TransientError) as blip:
        run_claude(job, tmp_path, 10, tmp_path / "log", NOW)
    assert blip.value.session_id is None
    assert [r.window for r in blip.value.readings] == ["five_hour", "seven_day"]


def test_the_factorys_context_goes_in_the_system_prompt_not_the_message(tmp_path, monkeypatch):
    """ADR 41 item 2."""
    seen = _fake_claude(monkeypatch, '{"result": "ok", "session_id": "s1"}', returncode=0)
    spec = JobSpec("review", "Review.", 10, system="The factory's rules.")
    _adapter_run(tmp_path, spec)
    cmd = seen[0]
    assert cmd[cmd.index("--append-system-prompt") + 1] == "The factory's rules."
    assert "The factory's rules." not in cmd[cmd.index("-p") + 1]


def test_no_context_no_system_prompt_flag(tmp_path, monkeypatch):
    seen = _fake_claude(monkeypatch, '{"result": "ok", "session_id": "s1"}', returncode=0)
    _adapter_run(tmp_path, JobSpec("review", "Review.", 10))
    assert "--append-system-prompt" not in seen[0]
