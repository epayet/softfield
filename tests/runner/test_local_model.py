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
    assert parse_events(lines) == TokenTotals(input=14417, output=204, reasoning=12, steps=2)


def test_a_timeout_kills_the_whole_process_group(tmp_path):
    """A hung grandchild (e.g. a pytest OpenCode started) must not outlive the attempt."""
    import os
    import time

    from runner.local_model import run_killing_group

    pidfile = tmp_path / "child.pid"
    script = f"sleep 60 & echo $! > {pidfile}; wait"
    started = time.monotonic()
    *_, code = run_killing_group(["sh", "-c", script], tmp_path, timeout=1)
    assert code is None and time.monotonic() - started < 10
    child = int(pidfile.read_text())
    time.sleep(0.2)
    try:
        os.kill(child, 0)
        alive = True
    except ProcessLookupError:
        alive = False
    assert not alive, "the grandchild survived"


def test_a_normal_run_returns_output_and_exit_code(tmp_path):
    from runner.local_model import run_killing_group

    assert run_killing_group(["sh", "-c", "echo hi; exit 3"], tmp_path, timeout=5) == (
        "hi\n",
        "",
        3,
    )


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
