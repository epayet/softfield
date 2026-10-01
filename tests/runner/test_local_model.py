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
    StreamFacts,
    TokenTotals,
    empty_cause,
    is_local,
    parse_events,
    session_reasoning,
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

    _fake_opencode(tmp_path, monkeypatch, "\n".join([_step(100, 1), _step(200, 2), _tool("edit")]))
    ticks = itertools.count(0, 40)  # every read of the clock is 40 s later
    seen: list[TokenTotals] = []
    log = tmp_path / "logs" / "opencode-1.jsonl"
    run = run_opencode(
        tmp_path, "m", "t", "p", 10**9, log, on_progress=seen.append, clock=lambda: next(ticks)
    )
    assert seen and all(t.input <= 300 for t in seen)
    assert seen[-1].steps >= 1
    assert (run.tokens.input, run.tokens.steps, run.facts.edits) == (300, 2, 1)
    assert log.read_text().startswith(_step(100, 1) + "\n")
    assert run.exit_code == 0


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


def test_the_ollama_agents_are_opencode_json_tags_in_no_role_yet():
    """D6: `ollama-<tag>` without `-cloud` or `:cloud`, `:` as `-`, model `ollama/<tag>`;
    each tag is in opencode.json's `ollama` provider. Local stays the developer."""
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
    assert not {a.id for a in ollama} & {i for ids in cfg.roles.values() for i in ids}
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
