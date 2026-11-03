"""Commands with a time limit that dies with them, and with the runner."""

import atexit
import contextlib
import os
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Iterator, Mapping
from pathlib import Path
from types import FrameType
from typing import IO

LIVE_EVERY = 30.0  # seconds between live updates while a job runs (f1 D3)
GRACE = 5.0  # seconds a stopped group gets between SIGTERM and SIGKILL

# Leads each command's session and kills it all when the process that started it dies, even
# by SIGKILL, which nothing in that process can catch. OpenCode's shell timeout killed an
# agent's `softfield check-all`; its `uv run pytest`, in a session of its own, ran on at 95%
# for hours, three at once (2026-10-15). Linux tells the watcher (PR_SET_PDEATHSIG); the
# check of its parent's pid covers a death before that. A SIGTERM to the group reaches the
# command itself, so the watcher only waits: the command keeps its grace (`_stop`).
_WATCH = """\
import ctypes, os, signal, subprocess, sys
def die(signum, frame):
    os.killpg(0, signal.SIGKILL)
signal.signal(signal.SIGUSR2, die)
signal.signal(signal.SIGTERM, lambda signum, frame: None)
try:
    ctypes.CDLL(None, use_errno=True).prctl(1, signal.SIGUSR2)
except AttributeError:
    pass
if os.getppid() != int(sys.argv[1]):
    die(0, None)
code = subprocess.Popen(sys.argv[2:]).wait()
if code < 0:
    try:
        signal.signal(-code, signal.SIG_DFL)
    except (OSError, ValueError):
        pass
    os.kill(os.getpid(), -code)
sys.exit(code)
"""


def _watched(args: list[str]) -> list[str]:
    return [sys.executable, "-I", "-c", _WATCH, str(os.getpid()), *args]


# Each command gets a temp folder of its own, removed when its group ends (f175 D1): the
# SIGKILL that ends every group leaves nothing in it the time to remove its own (pytest's
# folders, Chromium profiles), and Ubuntu empties /tmp only at boot. Not TMPDIR's: inside a
# job, that is the job's folder.
TMP_BASE = Path("/tmp")  # noqa: S108 - the root is checked as ours before any use


def _tmp_root() -> Path | None:
    """``/tmp/softfield-<uid>``, made private; None when the path there isn't our own folder
    (another user's, or a link planted in the shared ``/tmp``) or can't be made (a full disk)."""
    root = TMP_BASE / f"softfield-{os.getuid()}"
    try:
        with contextlib.suppress(FileExistsError):
            root.mkdir(mode=0o700)
        st = root.lstat()
    except OSError:
        return None
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
        return None
    return root


def _job_tmp(env: dict[str, str]) -> Path | None:
    """A fresh folder ``<runner pid>-<random>`` under the root, set as ``TMPDIR`` in ``env``;
    None, ``env`` unchanged, when it already names one under the root (D2: a nested command
    keeps its job's), the root isn't ours or the disk is full: a folder is housekeeping, and
    never what stops a command."""
    root = _tmp_root()
    if root is None:
        return None
    if root in Path(env.get("TMPDIR", "/")).parents:
        return None
    try:
        folder = Path(tempfile.mkdtemp(prefix=f"{os.getpid()}-", dir=root))
    except OSError:
        return None
    env["TMPDIR"] = str(folder)
    return folder


def _remove(folder: Path | None) -> None:
    if folder is not None:
        shutil.rmtree(folder, ignore_errors=True)


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def sweep_tmp() -> None:
    """Remove the folders runners that died left under the root (D3): a reboot, a crash, a
    SIGKILL. Folders of a live runner, and anything else, stay."""
    root = _tmp_root()
    if root is None:
        return
    for folder in root.iterdir():
        pid, dash, _ = folder.name.partition("-")
        if dash and pid.isdigit() and not _alive(int(pid)):
            _remove(folder)


def _start(
    args: list[str],
    cwd: Path,
    env: Mapping[str, str] | None,
    stdin: int | None,
    stdout: int | IO[str],
    stderr: int | IO[str],
) -> tuple[subprocess.Popen[str], Path | None]:
    """``args`` watched, in a session of its own with a temp folder of its own; the folder is
    removed if the start fails."""
    full_env = dict(os.environ if env is None else env)
    folder = _job_tmp(full_env)
    try:
        proc = subprocess.Popen(
            _watched(args),
            cwd=cwd,
            env=full_env,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            text=True,
            start_new_session=True,
        )
    except BaseException:
        _remove(folder)
        raise
    return proc, folder


_live: dict[subprocess.Popen[str], Path | None] = {}  # each group and its temp folder
_live_lock = threading.Lock()


def _kill(proc: subprocess.Popen[str]) -> None:
    with contextlib.suppress(ProcessLookupError):
        os.killpg(proc.pid, signal.SIGKILL)


def _stop(proc: subprocess.Popen[str]) -> None:
    """SIGTERM the whole group, give it ``GRACE`` seconds, then SIGKILL what's left. A second
    Ctrl-C during the grace cuts it short, not the SIGKILL (f7-04)."""
    try:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGTERM)
        with contextlib.suppress(subprocess.TimeoutExpired):
            proc.wait(timeout=GRACE)
    finally:
        _kill(proc)
    proc.wait()


@contextlib.contextmanager
def _owned(proc: subprocess.Popen[str], folder: Path | None) -> Iterator[None]:
    """The child dies with whatever leaves the wait: Ctrl-C, SIGTERM, a crash. It runs in its
    own session, so Ctrl-C never reaches it: after one, the runner's `opencode run` kept
    editing the working tree for 15 minutes (f3-13). Its temp folder goes with it."""
    with _live_lock:
        _live[proc] = folder
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
            _live.pop(proc, None)
        _remove(folder)


def stop_all() -> None:
    """Stop every group still running, and remove their temp folders. At exit: Claude jobs and
    gates wait in a worker thread (`loop.with_progress`), which a Ctrl-C in the main thread
    never interrupts."""
    with _live_lock:
        procs = dict(_live)
    try:
        for proc in procs:
            _stop(proc)
    finally:
        for proc, folder in procs.items():
            _kill(proc)
            _remove(folder)


atexit.register(stop_all)


def _exit_on_sigterm(signum: int, frame: FrameType | None) -> None:
    raise SystemExit(128 + signum)


def stop_on_sigterm() -> None:
    """Make SIGTERM and SIGHUP to the runner unwind like Ctrl-C, so its children are stopped
    too. SIGHUP's default killed the runner without unwinding: a closed terminal left a gate's
    pytest running for 16 hours (2026-10-04). Under `nohup` it stays ignored."""
    signal.signal(signal.SIGTERM, _exit_on_sigterm)
    if signal.getsignal(signal.SIGHUP) is not signal.SIG_IGN:
        signal.signal(signal.SIGHUP, _exit_on_sigterm)


def run_bounded(
    args: list[str], cwd: Path, timeout: float, env: Mapping[str, str] | None = None
) -> tuple[int | None, str, str]:
    """Run ``args`` in its own process group: (exit code, stdout, stderr), the code None on
    timeout. A timeout kills the whole group: ``subprocess.run`` kills only the direct child,
    so `uv run pytest` left pytest running for a day (2026-10-01)."""
    proc, folder = _start(args, cwd, env, subprocess.DEVNULL, subprocess.PIPE, subprocess.PIPE)
    with _owned(proc, folder):
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            _kill(proc)
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

    ``PWD`` is set to ``cwd``: OpenCode takes its directory from ``PWD`` over its real cwd, so
    a bench copy started from the main checkout edited the main checkout (f7-06's probe).
    """
    env = {**(os.environ if env is None else env), "PWD": str(cwd.absolute())}
    with out_path.open("w", encoding="utf-8") as out, tempfile.TemporaryFile("w+") as err:
        proc, folder = _start(cmd, cwd, env, stdin, out, err)
        deadline = clock() + timeout
        next_tick = clock() + every
        code: int | None = None
        with _owned(proc, folder):
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
