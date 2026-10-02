"""Commands with a time limit that dies with them."""

import contextlib
import os
import signal
import subprocess
import tempfile
import time
from collections.abc import Callable, Mapping
from pathlib import Path

LIVE_EVERY = 30.0  # seconds between live updates while a job runs (f1 D3)


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
    on_tick: Callable[[], None] | None = None,
    every: float = LIVE_EVERY,
    clock: Callable[[], float] = time.monotonic,
    *,
    env: Mapping[str, str] | None = None,
    stdin: int | None = None,
) -> tuple[str, int | None]:
    """Run ``cmd`` in its own process group, its stdout written straight into ``out_path``
    as it comes, calling ``on_tick`` every ``every`` seconds; on timeout kill the whole group.

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
        while True:
            try:
                code = proc.wait(timeout=max(0.05, min(next_tick, deadline) - clock()))
                break
            except subprocess.TimeoutExpired:
                pass
            if clock() >= deadline:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                break
            if on_tick is not None and clock() >= next_tick:
                on_tick()
                next_tick = clock() + every
        err.seek(0)
        return err.read(), code
