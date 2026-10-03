"""Commands with a time limit that dies with them, and with the runner."""

import atexit
import contextlib
import os
import signal
import subprocess
import tempfile
import threading
import time
from collections.abc import Callable, Iterator, Mapping
from pathlib import Path
from types import FrameType

LIVE_EVERY = 30.0  # seconds between live updates while a job runs (f1 D3)
GRACE = 5.0  # seconds a stopped group gets between SIGTERM and SIGKILL

_live: set[subprocess.Popen[str]] = set()
_live_lock = threading.Lock()


def _stop(proc: subprocess.Popen[str]) -> None:
    """SIGTERM the whole group, give it ``GRACE`` seconds, then SIGKILL what's left."""
    with contextlib.suppress(ProcessLookupError):
        os.killpg(proc.pid, signal.SIGTERM)
    with contextlib.suppress(subprocess.TimeoutExpired):
        proc.wait(timeout=GRACE)
    with contextlib.suppress(ProcessLookupError):
        os.killpg(proc.pid, signal.SIGKILL)
    proc.wait()


@contextlib.contextmanager
def _owned(proc: subprocess.Popen[str]) -> Iterator[None]:
    """The child dies with whatever leaves the wait: Ctrl-C, SIGTERM, a crash. It runs in its
    own session, so Ctrl-C never reaches it: after one, the runner's `opencode run` kept
    editing the working tree for 15 minutes (f3-13)."""
    with _live_lock:
        _live.add(proc)
    try:
        yield
    except BaseException:
        _stop(proc)
        raise
    else:
        # A child that exits can leave its own commands running in the group: an attempt's
        # pytest outlived its OpenCode for 2½ h (2026-10-03). Nothing in the group may outlive it.
        with contextlib.suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGKILL)
    finally:
        with _live_lock:
            _live.discard(proc)


def stop_all() -> None:
    """Stop every group still running. At exit: Claude jobs and gates wait in a worker thread
    (`loop.with_progress`), which a Ctrl-C in the main thread never interrupts."""
    with _live_lock:
        procs = list(_live)
    for proc in procs:
        _stop(proc)


atexit.register(stop_all)


def _exit_on_sigterm(signum: int, frame: FrameType | None) -> None:
    raise SystemExit(128 + signum)


def stop_on_sigterm() -> None:
    """Make SIGTERM to the runner unwind like Ctrl-C, so its children are stopped too."""
    signal.signal(signal.SIGTERM, _exit_on_sigterm)


def run_bounded(
    args: list[str], cwd: Path, timeout: float, env: Mapping[str, str] | None = None
) -> tuple[int | None, str, str]:
    """Run ``args`` in its own process group: (exit code, stdout, stderr), the code None on
    timeout. A timeout kills the whole group: ``subprocess.run`` kills only the direct child,
    so `uv run pytest` left pytest running for a day (2026-10-01)."""
    proc = subprocess.Popen(
        args,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        text=True,
        start_new_session=True,
    )
    with _owned(proc):
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(proc.pid, signal.SIGKILL)
            out, err = proc.communicate()
            return None, out, err
    return proc.returncode, out, err


def run_streaming(
    cmd: list[str],
    cwd: Path,
    timeout: float,
    out_path: Path,
    on_tick: Callable[[], bool | None] | None = None,
    every: float = LIVE_EVERY,
    clock: Callable[[], float] = time.monotonic,
    *,
    env: Mapping[str, str] | None = None,
    stdin: int | None = None,
) -> tuple[str, int | None]:
    """Run ``cmd`` in its own process group, its stdout written straight into ``out_path``
    as it comes, calling ``on_tick`` every ``every`` seconds; on timeout, or when ``on_tick``
    returns True (a stuck attempt, f2-05), kill the whole group.

    OpenCode and Claude Code start shell commands of their own (pytest, ruff…). Killing only
    the harness would leave a hung child running after the job. Returns (stderr, exit code or
    None).
    """
    with out_path.open("w", encoding="utf-8") as out, tempfile.TemporaryFile("w+") as err:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdin=stdin,
            stdout=out,
            stderr=err,
            text=True,
            start_new_session=True,
        )
        deadline = clock() + timeout
        next_tick = clock() + every
        code: int | None = None
        with _owned(proc):
            while True:
                try:
                    code = proc.wait(timeout=max(0.05, min(next_tick, deadline) - clock()))
                    break
                except subprocess.TimeoutExpired:
                    pass
                stop = clock() >= deadline
                if not stop and on_tick is not None and clock() >= next_tick:
                    stop = bool(on_tick())
                    next_tick = clock() + every
                if stop:
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
                    break
        err.seek(0)
        return err.read(), code
