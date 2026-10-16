import itertools
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from runner import local_model
from runner.agents import FAILURE, LIMIT, TRANSIENT, Agent, JobSpec, adapter_for
from runner.config import load_config
from runner.local_model import (
    STOP_NO_EDIT,
    STOP_REPEATING,
    StreamFacts,
    TokenTotals,
    empty_cause,
    is_local,
    parse_events,
    repeating,
    session_reasoning,
    stop_reason,
    stream_facts,
)

REPO = Path(__file__).parents[2]
PROBE = Path(__file__).parent / "fixtures" / "probes" / "opencode-ollama.jsonl"
LOCAL = Agent("local-m", "opencode", "lmstudio/m", 5)
CLOUD = Agent("ollama-gpt-oss-120b", "opencode", "ollama/gpt-oss:120b-cloud", 6)
NOW = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)


def _step(inp: int, out: int, reasoning: int = 0) -> str:
    return json.dumps(
        {
            "type": "step_finish",
            "part": {"tokens": {"input": inp, "output": out, "reasoning": reasoning}},
        }
    )


def test_parse_events_sums_steps_and_ignores_noise():
    lines = [
        json.dumps({"type": "step_start"}),
        _step(6417, 4, 12),
        "not json",
        '{"broken',
        _step(8000, 200),
    ]
    assert parse_events(lines) == TokenTotals(
        input=14417, output=204, reasoning=12, steps=2, peak=8000
    )


def test_the_peak_context_counts_cached_input():
    cached = {"input": 100, "output": 5, "cache": {"read": 9000, "write": 400}}
    step = json.dumps({"type": "step_finish", "part": {"tokens": cached}})
    assert parse_events([_step(8000, 1), step]).peak == 9500


def test_an_ollama_cloud_run_has_the_same_shape_as_lm_studios():
    # f1-18's probe: `opencode run --format json -m ollama/gpt-oss:120b-cloud`
    fixture = Path(__file__).parent / "fixtures" / "probes" / "opencode-ollama.jsonl"
    lines = fixture.read_text(encoding="utf-8").splitlines()
    assert parse_events(lines) == TokenTotals(
        input=6536 + 1259, output=86 + 6, reasoning=0, steps=2, peak=1259 + 6608
    )
    assert stream_facts(lines).session_id == "ses_f07dc81a4ffe9DHBuzY59NV28i"


def test_a_timeout_kills_the_whole_process_group(tmp_path):
    """A hung grandchild (e.g. a pytest OpenCode started) must not outlive the attempt."""
    import os
    import time

    from runner.local_model import run_streaming

    pidfile = tmp_path / "child.pid"
    script = f"sleep 60 & echo $! > {pidfile}; wait"
    started = time.monotonic()
    _, code = run_streaming(["sh", "-c", script], tmp_path, 1, tmp_path / "out.log")
    assert code is None and time.monotonic() - started < 10
    child = int(pidfile.read_text())
    time.sleep(0.2)
    try:
        os.kill(child, 0)
        alive = True
    except ProcessLookupError:
        alive = False
    assert not alive, "the grandchild survived"


def test_a_normal_run_streams_its_output_to_the_log(tmp_path):
    from runner.local_model import run_streaming

    out = tmp_path / "out.log"
    cmd = ["sh", "-c", "echo hi; echo oops >&2; exit 3"]
    assert run_streaming(cmd, tmp_path, 5, out) == ("oops\n", 3)
    assert out.read_text() == "hi\n"


def _fake_opencode(tmp_path, monkeypatch, body: str) -> None:
    """An `opencode` on PATH that prints ``body``'s lines, a short pause between them."""
    import os

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "opencode"
    lines = "".join(f"echo '{line}'\nsleep 0.2\n" for line in body.splitlines())
    script.write_text("#!/bin/sh\n" + lines)
    script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")


def test_opencode_reports_progress_as_it_runs(tmp_path, monkeypatch):
    """f1 D3: the stream is read as it comes, and every interval the caller sees the tokens
    so far. The clock is a parameter, so the test doesn't wait 30 s."""
    from runner.local_model import run_opencode

    # The edit first: this clock passes NO_EDIT_AFTER in a few ticks, and stops an attempt with none
    _fake_opencode(tmp_path, monkeypatch, "\n".join([_tool("edit"), _step(100, 1), _step(200, 2)]))
    monkeypatch.setattr(local_model, "session_reasoning", lambda db, session: "")
    ticks = itertools.count(0, 40)  # every read of the clock is 40 s later
    seen: list[TokenTotals] = []
    log = tmp_path / "logs" / "opencode-1.jsonl"
    run = run_opencode(
        tmp_path, "m", "t", "p", 10**9, log, on_progress=seen.append, clock=lambda: next(ticks)
    )
    assert seen and all(t.input <= 300 for t in seen)
    assert seen[-1].steps >= 1
    assert (run.tokens.input, run.tokens.steps, run.facts.edits) == (300, 2, 1)
    assert log.read_text().startswith(_tool("edit") + "\n")
    assert run.exit_code == 0


def test_opencode_gets_a_20_minute_shell_timeout_and_the_rest_of_the_environment(
    tmp_path, monkeypatch
):
    """f4-05: OpenCode killed shell calls at 120 s, check-all included; the runner raises
    its default and keeps the environment it was given."""
    from runner.local_model import run_opencode

    _fake_opencode(tmp_path, monkeypatch, _tool("edit"))
    script = tmp_path / "bin" / "opencode"
    script.write_text(
        '#!/bin/sh\necho "$OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS $COUCOU_KEPT"\n'
    )
    monkeypatch.setenv("COUCOU_KEPT", "kept")
    monkeypatch.setenv("OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS", "120000")
    monkeypatch.setattr(local_model, "session_reasoning", lambda db, session: "")
    log = tmp_path / "logs" / "opencode-1.jsonl"
    run = run_opencode(tmp_path, "m", "t", "p", 60, log)
    assert run.exit_code == 0
    assert log.read_text().startswith("1200000 kept\n")


def _tool(tool: str, status: str = "completed") -> str:
    return json.dumps(
        {
            "type": "tool_use",
            "sessionID": "ses_1",
            "part": {"tool": tool, "state": {"status": status}},
        }
    )


def test_stream_facts_find_the_session_edit_streaks_and_refused_commands():
    lines = [
        _tool("read"),
        _tool("edit"),
        _tool("edit"),
        _tool("bash"),
        _tool("edit"),
        _tool("write"),
        _tool("edit"),
        _tool("bash", "error"),
        _tool("edit"),
    ]
    facts = stream_facts(lines)
    assert facts == StreamFacts(session_id="ses_1", edit_streak=3, refused=1, edits=6)


def test_an_empty_attempt_is_triaged_by_cause():
    assert empty_cause(0, timed_out=True) == "timeout"
    assert empty_cause(2, timed_out=False) == "refused"
    assert empty_cause(0, timed_out=False) == "stopped"


# --- the `opencode` harness's adapter (f1-21) ----------------------------------------------


def _fake_stream(monkeypatch, lines: list[str], stderr: str = "", code: int | None = 0):
    """`run_streaming` faked: the stream is ``lines``; returns the commands it was given."""
    commands: list[list[str]] = []

    def run_streaming(cmd, cwd, timeout, out_path, on_tick=None, **kwargs):
        commands.append(cmd)
        out_path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
        return stderr, code

    monkeypatch.setattr(local_model, "run_streaming", run_streaming)
    return commands


def _spec() -> JobSpec:
    return JobSpec("developer", "Do it.", timeout=60, title="m1-01-thing attempt 1")


def _run(agent: Agent, tmp_path: Path):
    return local_model.ADAPTER.run(agent, _spec(), tmp_path, tmp_path / "logs" / "oc.jsonl", NOW)


def test_the_opencode_harness_names_its_adapter():
    assert adapter_for("opencode") is local_model.ADAPTER


def test_the_agents_model_picks_the_provider():
    assert is_local(LOCAL)
    assert not is_local(CLOUD)


def test_an_ollama_agent_runs_opencode_with_its_model_and_the_probe_gives_its_tokens(
    tmp_path, monkeypatch
):
    commands = _fake_stream(monkeypatch, PROBE.read_text(encoding="utf-8").splitlines())
    result = _run(CLOUD, tmp_path)
    assert commands == [
        [
            "opencode",
            "run",
            "--format",
            "json",
            "-m",
            "ollama/gpt-oss:120b-cloud",
            "--title",
            "m1-01-thing attempt 1",
            "Do it.",
        ]
    ]
    assert result.ok and result.error is None
    # f1-18's probe: OpenCode's `cost` is 0, so the usage is our own token count (ADR 15 item 3)
    assert result.usage == {"input_tokens": 7795, "output_tokens": 92, "reasoning_tokens": 0}
    assert (result.num_turns, result.peak_context) == (2, 7867)
    assert result.session_id == "ses_f07dc81a4ffe9DHBuzY59NV28i"
    assert result.cost_usd is None
    assert result.model == "ollama/gpt-oss:120b-cloud"  # f2-04: the agent's model


def test_a_local_job_records_its_agents_model(tmp_path, monkeypatch):
    _fake_stream(monkeypatch, [_step(100, 1)], stderr="boom", code=1)
    assert _run(LOCAL, tmp_path).model == LOCAL.model


def test_the_stream_facts_come_back_in_the_result(tmp_path, monkeypatch):
    lines = [_tool("edit"), _tool("edit"), _tool("bash", "error"), _step(100, 1)]
    _fake_stream(monkeypatch, lines)
    result = _run(LOCAL, tmp_path)
    assert (result.edit_streak, result.refused_commands, result.edits) == (2, 1, 2)
    assert result.session_id == "ses_1" and not result.timed_out


UNRECOGNISED = "Error: something nobody has seen before"


def test_an_unrecognised_error_from_a_cloud_tag_is_a_possible_limit(tmp_path, monkeypatch):
    """No Ollama refusal has been seen (f1-18): until one is, an unknown error from a cloud
    tag is a limit with no reset, so the allowance's cooldown applies (ADR 15 item 2)."""
    _fake_stream(monkeypatch, [_step(100, 1)], stderr=UNRECOGNISED, code=1)
    result = _run(CLOUD, tmp_path)
    assert result.error == LIMIT
    assert result.refusal is not None
    assert (result.refusal.certain, result.refusal.resets_at, result.refusal.window) == (
        False,
        None,
        None,
    )
    assert result.usage["input_tokens"] == 100  # what it spent still counts


def test_a_harness_that_never_started_is_a_failure_not_a_limit(tmp_path, monkeypatch):
    """No stream at all: OpenCode never ran, so the model refused nothing. The bench's
    sandbox launcher once failed to start, and gemma was recorded as refusing (2026-10-06)."""
    missing = "python3: can't open file '/repo/runner/sandbox.py': [Errno 2] No such file"
    _fake_stream(monkeypatch, [], stderr=missing, code=2)
    result = _run(CLOUD, tmp_path)
    assert (result.error, result.refusal) == (FAILURE, None)


def test_the_same_error_on_the_local_model_is_a_failure(tmp_path, monkeypatch):
    _fake_stream(monkeypatch, [_step(100, 1)], stderr=UNRECOGNISED, code=1)
    result = _run(LOCAL, tmp_path)
    assert result.error == FAILURE and result.refusal is None


def test_an_error_event_in_the_stream_counts_as_an_error(tmp_path, monkeypatch):
    event = json.dumps({"type": "error", "error": {"name": "APIError", "data": {"message": "?"}}})
    _fake_stream(monkeypatch, [event], code=0)
    assert _run(CLOUD, tmp_path).error == LIMIT
    assert _run(LOCAL, tmp_path).error == FAILURE


def test_a_cloud_limit_that_says_when_it_resets_is_certain(tmp_path, monkeypatch):
    _fake_stream(monkeypatch, [], stderr="Error: weekly usage limit reached|1791216000", code=1)
    refusal = _run(CLOUD, tmp_path).refusal
    assert refusal is not None and refusal.certain
    assert refusal.resets_at == datetime.fromtimestamp(1791216000, tz=UTC)


@pytest.mark.parametrize(
    "stderr",
    [
        "Error: connect ECONNREFUSED 127.0.0.1:11434",
        "Error: 503 Service Unavailable",
        "Error: the server is overloaded, try again",
    ],
)
def test_a_passing_error_from_a_cloud_tag_is_transient(tmp_path, monkeypatch, stderr):
    _fake_stream(monkeypatch, [], stderr=stderr, code=1)
    assert _run(CLOUD, tmp_path).error == TRANSIENT


def test_a_timeout_is_a_failure_even_on_a_cloud_tag(tmp_path, monkeypatch):
    _fake_stream(monkeypatch, [_step(100, 1)], code=None)
    result = _run(CLOUD, tmp_path)
    assert result.timed_out and result.error == FAILURE


def test_the_ollama_agents_are_opencode_json_tags_and_none_develops_for_now(machine):
    """D6: `ollama-<tag>` without `-cloud` or `:cloud`, `:` as `-`, model `ollama/<tag>`;
    each tag is in opencode.json's `ollama` provider. None is a developer until a clean bench
    (owner, 2026-10-04: the 2026-10-04 bench leaked into the main checkout, f7-06), and none
    has another role."""
    cfg = load_config(REPO)
    ollama = [a for a in cfg.agents.values() if a.model.startswith("ollama/")]
    config = json.loads((REPO / "opencode.json").read_text(encoding="utf-8"))
    tags = set(config["provider"]["ollama"]["models"])
    assert {a.model.removeprefix("ollama/") for a in ollama} == tags and len(tags) == 6
    for agent in ollama:
        tag = agent.model.removeprefix("ollama/")
        name = tag.removesuffix("-cloud").removesuffix(":cloud").replace(":", "-")
        assert agent.id == f"ollama-{name}"
        assert agent.harness == "opencode" and not is_local(agent)
        assert 1 <= agent.rating <= 10
    ids = {a.id for a in ollama}
    assert not ids & set(cfg.roles["developer"])
    others = {i for role, names in cfg.roles.items() if role != "developer" for i in names}
    assert not ids & others
    assert is_local(cfg.agent_for("developer"))
    assert cfg.agent_for("developer").model.removeprefix("lmstudio/") in set(
        config["provider"]["lmstudio"]["models"]
    )


def test_the_developers_thinking_is_read_from_opencodes_database(tmp_path):
    db = tmp_path / "opencode.db"
    con = sqlite3.connect(db)
    con.execute("create table part (id text, session_id text, time_created int, data text)")
    rows = [
        ("p2", "ses_1", 2, {"type": "reasoning", "text": "Then the CSP blocks it."}),
        ("p1", "ses_1", 1, {"type": "reasoning", "text": "First, read compose.js."}),
        ("p3", "ses_1", 3, {"type": "text", "text": "not thinking"}),
        ("p4", "ses_2", 1, {"type": "reasoning", "text": "another session"}),
    ]
    con.executemany(
        "insert into part values (?, ?, ?, ?)", [(i, s, t, json.dumps(d)) for i, s, t, d in rows]
    )
    con.commit()
    con.close()
    assert session_reasoning(db, "ses_1") == "First, read compose.js.\n\nThen the CSP blocks it."
    assert session_reasoning(tmp_path / "missing.db", "ses_1") == ""


# --- stuck attempts (f2-05) -----------------------------------------------------------------

# f1-13's first attempt ended in thousands of lines of this (thinking-1.md, 205 KB).
LOOPING = "I'll read the views first, then the templates.\n\n" + (
    "Building out the template structure... Building the template structure...\n" * 120
)
VARIED = "\n".join(
    f"Step {i}: read file {i * 7 % 13}, then check gate {i % 5} against test {i * 3}."
    for i in range(80)
)


def test_reasoning_made_of_one_short_phrase_repeated_is_repeating():
    assert repeating(LOOPING)
    assert repeating("OK, let me write the code now. " * 200)


def test_varied_or_short_reasoning_is_not_repeating():
    assert len(VARIED) > 4000 and not repeating(VARIED)
    assert not repeating("Building the template structure... " * 20)  # under ~4,000 characters
    assert not repeating("")


def _ticking(monkeypatch, frames: list[tuple[float, list[str]]]):
    """`run_streaming` faked: at each (minute, new lines) frame the stream grows by its lines
    and a tick comes; it ends after the last frame unless a tick stops it. Returns the clock
    and the minutes of the ticks that came."""
    minute = [0.0]
    ticked: list[float] = []

    def run_streaming(cmd, cwd, timeout, out_path, on_tick=None, **kwargs):
        lines: list[str] = []
        for at, new in frames:
            minute[0] = at
            lines += new
            out_path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
            ticked.append(at)
            if on_tick is not None and on_tick():
                return "", None
        return "", 0

    monkeypatch.setattr(local_model, "run_streaming", run_streaming)
    return (lambda: minute[0] * 60), ticked


def _thinking(monkeypatch, text: str) -> None:
    monkeypatch.setattr(local_model, "session_reasoning", lambda db, session: text)


def _attempt(tmp_path: Path, clock):
    log = tmp_path / "logs" / "opencode-1.jsonl"
    return local_model.run_opencode(tmp_path, "m", "t", "p", 45 * 60, log, clock=clock)


def test_a_stream_with_no_edit_for_20_minutes_is_stopped(tmp_path, monkeypatch):
    """f1: 6 of 24 failed local attempts made no edit in 25-30 minutes; F93: 10 was too soon."""
    frames = [(m / 2, [_tool("read"), _step(100, 1)]) for m in range(1, 61)]
    clock, ticked = _ticking(monkeypatch, frames)
    _thinking(monkeypatch, VARIED)
    run = _attempt(tmp_path, clock)
    assert run.stopped == STOP_NO_EDIT == "stopped: no edit after 20 min"
    assert ticked[-1] == 20 and 19.5 in ticked and run.exit_code is None
    assert not run.timed_out  # stopped, not out of time
    assert f"--- {STOP_NO_EDIT} ---" in (tmp_path / "logs" / "opencode-1.jsonl").read_text()


def test_a_stream_whose_reasoning_repeats_one_phrase_is_stopped_within_one_tick(
    tmp_path, monkeypatch
):
    clock, ticked = _ticking(monkeypatch, [(m / 2, [_step(100, 1)]) for m in range(1, 10)])
    _thinking(monkeypatch, LOOPING)
    run = _attempt(tmp_path, clock)
    assert run.stopped == STOP_REPEATING == "stopped: repeating itself"
    assert ticked == [0.5]


def test_a_stream_that_edits_at_minute_19_runs_on(tmp_path, monkeypatch):
    frames = [(m / 2, [_tool("edit")] if m == 38 else [_step(100, 1)]) for m in range(1, 61)]
    clock, ticked = _ticking(monkeypatch, frames)
    _thinking(monkeypatch, VARIED)
    run = _attempt(tmp_path, clock)
    assert (run.stopped, run.exit_code, ticked[-1]) == ("", 0, 30)


def test_a_stopped_attempt_fails_with_its_reason(tmp_path, monkeypatch):
    _ticking(monkeypatch, [(0.5, [_step(100, 1)])])
    _thinking(monkeypatch, LOOPING)
    result = _run(CLOUD, tmp_path)  # a cloud agent's stop isn't a refusal either
    assert result.error == FAILURE and result.refusal is None and not result.transient
    assert result.text == STOP_REPEATING and not result.timed_out
    assert stop_reason(result) == STOP_REPEATING
    assert stop_reason(_run(LOCAL, tmp_path)) is not None
    _fake_stream(monkeypatch, [_step(100, 1)], code=None)
    assert stop_reason(_run(LOCAL, tmp_path)) is None  # a plain timeout
