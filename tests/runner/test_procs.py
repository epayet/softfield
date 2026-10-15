import os
import signal
import subprocess
import sys
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


def test_a_second_ctrl_c_during_the_grace_still_kills_the_group(tmp_path: Path):
    """f7-04: a command that ignores SIGTERM gets its SIGKILL even when the owner presses
    Ctrl-C again while the runner waits out its grace."""
    pidfile = tmp_path / "child.pid"
    cmd = ["sh", "-c", f"trap '' TERM; sleep 60 & echo $! > {pidfile}; wait"]
    interrupts: list[int] = []

    def interrupt(signum: int, frame: object) -> None:
        interrupts.append(1)
        if len(interrupts) <= 2:
            raise KeyboardInterrupt

    old = signal.signal(signal.SIGALRM, interrupt)
    signal.setitimer(signal.ITIMER_REAL, 0.5, 0.5)
    try:
        with pytest.raises(KeyboardInterrupt):
            run_bounded(cmd, tmp_path, timeout=60)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)
    assert len(interrupts) >= 2
    assert _gone(pidfile)


@pytest.mark.parametrize("signum", [signal.SIGTERM, signal.SIGHUP])
def test_a_signal_to_the_runner_kills_its_gate(tmp_path: Path, signum: int):
    """2026-10-04: a gate's pytest ran on for 16 hours after the runner stopped. A closed
    terminal sends SIGHUP, which killed the runner without unwinding."""
    pidfile = tmp_path / "child.pid"

    def signal_when_started() -> None:
        deadline = time.monotonic() + 5
        while not (pidfile.exists() and pidfile.read_text().strip()):
            if time.monotonic() > deadline:
                return
            time.sleep(0.05)
        os.kill(os.getpid(), signum)

    old = {s: signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGHUP)}
    stop_on_sigterm()
    sender = threading.Thread(target=signal_when_started, daemon=True)
    try:
        sender.start()
        with pytest.raises(SystemExit):
            run_bounded(_sleeper(pidfile), tmp_path, timeout=60)
    finally:
        sender.join(5)
        for s, handler in old.items():
            signal.signal(s, handler)
    assert _gone(pidfile)


def test_a_runner_under_nohup_keeps_ignoring_sighup():
    old_term = signal.getsignal(signal.SIGTERM)
    old = signal.signal(signal.SIGHUP, signal.SIG_IGN)
    try:
        stop_on_sigterm()
        assert signal.getsignal(signal.SIGHUP) is signal.SIG_IGN
    finally:
        signal.signal(signal.SIGHUP, old)
        signal.signal(signal.SIGTERM, old_term)


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


def _leaver(pidfile: Path) -> list[str]:
    """Exits at once, leaving a grandchild running in its group (its output detached)."""
    return ["sh", "-c", f"sleep 60 >/dev/null 2>&1 & echo $! > {pidfile}; exit 0"]


def test_an_agent_that_exits_leaves_no_command_running(tmp_path: Path):
    """2026-10-03: an attempt's `uv run pytest … tests/browser` outlived its OpenCode and spun
    a core for 2½ h in the main checkout, slowing the next gates (f4-21 blocked)."""
    pidfile = tmp_path / "child.pid"
    _, code = run_streaming(_leaver(pidfile), tmp_path, 60, tmp_path / "out.log", every=0.1)
    assert code == 0
    assert _gone(pidfile)


def test_a_command_that_exits_leaves_no_child_running(tmp_path: Path):
    pidfile = tmp_path / "child.pid"
    code, _, _ = run_bounded(_leaver(pidfile), tmp_path, 10)
    assert code == 0
    assert _gone(pidfile)


def _killed_mid_run(tmp_path: Path, call: str) -> Path:
    """Start a process that calls ``call`` on a sleeper, SIGKILL it once the sleeper runs,
    and return the sleeper's pidfile."""
    pidfile = tmp_path / "child.pid"
    script = (
        "import sys; from pathlib import Path; from runner.procs import run_bounded, run_streaming;"
        f"cmd = {_sleeper(pidfile)!r}; tmp = Path({str(tmp_path)!r}); {call}"
    )
    parent = subprocess.Popen([sys.executable, "-c", script], cwd=Path(__file__).parents[2])
    deadline = time.monotonic() + 10
    while not (pidfile.exists() and pidfile.read_text().strip()) and time.monotonic() < deadline:
        time.sleep(0.05)
    parent.kill()
    parent.wait()
    return pidfile


def test_a_killed_check_all_leaves_no_command_running(tmp_path: Path):
    """2026-10-15: OpenCode's shell timeout killed an agent's `softfield check-all`; its
    `uv run pytest`, in a session of its own, ran on at 95% for hours (three at once)."""
    assert _gone(_killed_mid_run(tmp_path, "run_bounded(cmd, tmp, 60)"))


def test_a_killed_runner_leaves_no_agent_running(tmp_path: Path):
    call = "run_streaming(cmd, tmp, 60, tmp / 'out.log')"
    assert _gone(_killed_mid_run(tmp_path, call))


def test_a_command_keeps_its_stdin(tmp_path: Path):
    """Claude jobs are fed their prompt on stdin through `run_streaming`."""
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("hello\n")
    with prompt.open() as stdin:
        _, code = run_streaming(
            ["sh", "-c", "read line; test \"$line\" = hello"],
            tmp_path,
            10,
            tmp_path / "out.log",
            stdin=stdin.fileno(),
        )
    assert code == 0


def test_a_command_killed_by_a_signal_reports_it(tmp_path: Path):
    code, _, _ = run_bounded(["sh", "-c", "kill -TERM $$"], tmp_path, 10)
    assert code == -signal.SIGTERM
