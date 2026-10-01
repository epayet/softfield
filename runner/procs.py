"""Commands with a time limit that dies with them."""

import contextlib
import os
import signal
import subprocess
from collections.abc import Mapping
from pathlib import Path


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
