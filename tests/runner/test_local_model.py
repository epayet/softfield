import json

from runner.local_model import TokenTotals, parse_events


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
