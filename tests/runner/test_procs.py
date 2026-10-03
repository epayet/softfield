import os
import signal
import threading
import time
from pathlib import Path

import pytest

from runner.procs import run_bounded, run_streaming, stop_all, stop_on_sigterm


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


def _sleeper(pidfile: Path) -> list[str]:
    return ["sh", "-c", f"sleep 60 & echo $! > {pidfile}; wait"]


def _gone(pidfile: Path) -> bool:
    child = int(pidfile.read_text())
    deadline = time.monotonic() + 8
    while _alive(child) and time.monotonic() < deadline:
        time.sleep(0.05)
    return not _alive(child)


def test_ctrl_c_during_run_streaming_kills_the_agent(tmp_path: Path):
    """f3-13: after a Ctrl-C, the runner's `opencode run` edited the tree for 15 more minutes."""
    pidfile = tmp_path / "child.pid"

    def tick() -> None:
        if pidfile.exists() and pidfile.read_text().strip():
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        run_streaming(_sleeper(pidfile), tmp_path, 60, tmp_path / "out.log", tick, every=0.1)
    assert _gone(pidfile)


def test_ctrl_c_during_run_bounded_kills_the_command(tmp_path: Path):
    pidfile = tmp_path / "child.pid"

    def interrupt(signum: int, frame: object) -> None:
        raise KeyboardInterrupt

    old = signal.signal(signal.SIGALRM, interrupt)
    signal.setitimer(signal.ITIMER_REAL, 0.5)
    try:
        with pytest.raises(KeyboardInterrupt):
            run_bounded(_sleeper(pidfile), tmp_path, timeout=60)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)
    assert _gone(pidfile)


def test_sigterm_to_the_runner_kills_the_agent(tmp_path: Path):
    pidfile = tmp_path / "child.pid"

    def tick() -> None:
        if pidfile.exists() and pidfile.read_text().strip():
            os.kill(os.getpid(), signal.SIGTERM)

    old = signal.getsignal(signal.SIGTERM)
    stop_on_sigterm()
    try:
        with pytest.raises(SystemExit):
            run_streaming(_sleeper(pidfile), tmp_path, 60, tmp_path / "out.log", tick, every=0.1)
    finally:
        signal.signal(signal.SIGTERM, old)
    assert _gone(pidfile)


def test_stop_all_kills_an_agent_running_in_a_worker_thread(tmp_path: Path):
    """Claude jobs and gates run in `with_progress`'s thread: a Ctrl-C reaches the main
    thread only, so the exit hook stops what the threads started."""
    pidfile = tmp_path / "child.pid"
    worker = threading.Thread(
        target=run_streaming,
        args=(_sleeper(pidfile), tmp_path, 60, tmp_path / "out.log"),
        daemon=True,
    )
    worker.start()
    deadline = time.monotonic() + 5
    while not (pidfile.exists() and pidfile.read_text().strip()) and time.monotonic() < deadline:
        time.sleep(0.05)
    stop_all()
    assert _gone(pidfile)
    worker.join(5)
    assert not worker.is_alive()


def test_a_tick_that_returns_nothing_lets_the_command_run(tmp_path: Path):
    ticks: list[int] = []
    cmd = ["sh", "-c", "sleep 0.5; exit 4"]
    out = tmp_path / "out.log"
    _, code = run_streaming(cmd, tmp_path, 10, out, lambda: ticks.append(1), every=0.1)
    assert code == 4 and ticks
