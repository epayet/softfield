import itertools
import json
import sqlite3

from runner.local_model import (
    StreamFacts,
    TokenTotals,
    empty_cause,
    parse_events,
    session_reasoning,
    stream_facts,
)


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
    assert empty_cause(StreamFacts(), timed_out=True) == "timeout"
    assert empty_cause(StreamFacts(refused=2), timed_out=False) == "refused"
    assert empty_cause(StreamFacts(), timed_out=False) == "stopped"


def test_the_juniors_thinking_is_read_from_opencodes_database(tmp_path):
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
