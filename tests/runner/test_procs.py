import os
import time
from pathlib import Path

from runner.procs import run_bounded, run_streaming


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def test_a_command_returns_its_code_and_output(tmp_path: Path):
    code, out, err = run_bounded(["sh", "-c", "echo hi; echo oops >&2; exit 3"], tmp_path, 10)
    assert (code, out, err) == (3, "hi\n", "oops\n")


def test_a_timeout_kills_the_grandchildren_too(tmp_path: Path):
    """2026-10-01: an e2e pytest under `uv run` kept a core at 100% for 23 h after its
    timeout killed only `uv`."""
    pidfile = tmp_path / "child.pid"
    code, _, _ = run_bounded(
        ["sh", "-c", f"sleep 60 & echo $! > {pidfile}; wait"], tmp_path, timeout=0.5
    )
    assert code is None
    child = int(pidfile.read_text())
    deadline = time.monotonic() + 3
    while _alive(child) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not _alive(child)


def test_a_tick_that_asks_to_stop_kills_the_group_like_a_timeout(tmp_path: Path):
    """f2-05: a stuck attempt is stopped at a tick, not left to its timeout."""
    pidfile = tmp_path / "child.pid"
    ticks: list[int] = []

    def tick() -> bool:
        ticks.append(1)
        return len(ticks) == 2

    started = time.monotonic()
    cmd = ["sh", "-c", f"sleep 60 & echo $! > {pidfile}; wait"]
    _, code = run_streaming(cmd, tmp_path, 60, tmp_path / "out.log", tick, every=0.1)
    assert code is None and len(ticks) == 2 and time.monotonic() - started < 10
    child = int(pidfile.read_text())
    deadline = time.monotonic() + 3
    while _alive(child) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not _alive(child)


def test_a_tick_that_returns_nothing_lets_the_command_run(tmp_path: Path):
    ticks: list[int] = []
    cmd = ["sh", "-c", "sleep 0.5; exit 4"]
    out = tmp_path / "out.log"
    _, code = run_streaming(cmd, tmp_path, 10, out, lambda: ticks.append(1), every=0.1)
    assert code == 4 and ticks
