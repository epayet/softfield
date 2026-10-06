"""A benched agent may write only in its copy and the caches its tools need (Landlock).

Every earlier fix kept OpenCode in its copy by pointing it there (f2-12, f4-19, f7-06's
``PWD``) and checked afterwards that the main checkout hadn't changed. That check also caught
the owner, the runner and the lead working beside the bench, and voided the replay
(2026-10-06). Landlock makes a write outside the allowed folders fail instead, so the bench
can run beside anything. Reads stay open everywhere: the agent reads its tools and caches.

Landlock is the kernel's unprivileged sandbox (Linux 5.13+). bubblewrap would need user
namespaces, which Ubuntu 24.04's AppArmor denies to an unprivileged user.

``python runner/sandbox.py --write DIR [--write DIR …] -- CMD …`` restricts itself, then
execs ``CMD``: the rules hold for it and every process it starts. A launcher rather than a
``preexec_fn``, which isn't safe in the runner's threaded process.
"""

import ctypes
import os
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

_SYS_CREATE_RULESET, _SYS_ADD_RULE, _SYS_RESTRICT_SELF = 444, 445, 446  # x86_64 and arm64
_CREATE_RULESET_VERSION = 1
_RULE_PATH_BENEATH = 1
_PR_SET_NO_NEW_PRIVS = 38

# LANDLOCK_ACCESS_FS_*: every right that changes the filesystem. Execute, read file and read
# dir are left unhandled, so they stay allowed everywhere.
_WRITE_FILE, _REMOVE_DIR, _REMOVE_FILE = 1 << 1, 1 << 4, 1 << 5
_MAKE = sum(1 << n for n in range(6, 13))  # char, dir, reg, sock, fifo, block, sym
_REFER, _TRUNCATE = 1 << 13, 1 << 14  # ABI 2, ABI 3
_FILE_RIGHTS = _WRITE_FILE | _TRUNCATE  # what a rule on a file (not a folder) may carry
MIN_ABI = 3  # truncation is handled from 3: without it, `open(…, "w")` could empty any file

HOME = Path.home()
# What OpenCode, uv, pytest and Playwright write besides the copy.
TOOL_DIRS = (
    Path("/tmp"),  # noqa: S108 - pytest's and Playwright's temp files, not ours
    Path("/dev"),  # /dev/null, /dev/shm (Chromium), /dev/tty
    HOME / ".cache",
    HOME / ".local" / "share" / "opencode",
    HOME / ".local" / "state",
    HOME / ".local" / "share" / "uv",  # uv's Pythons and tools
    HOME / ".config" / "opencode",
    HOME / ".opencode",
)


class SandboxError(RuntimeError):
    pass


class _RulesetAttr(ctypes.Structure):
    _fields_ = [("handled_access_fs", ctypes.c_uint64)]


class _PathBeneathAttr(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int32)]


_libc = ctypes.CDLL(None, use_errno=True)


def abi() -> int:
    """The kernel's Landlock ABI version; 0 when Landlock is off."""
    version = _libc.syscall(_SYS_CREATE_RULESET, None, ctypes.c_size_t(0), _CREATE_RULESET_VERSION)
    return max(int(version), 0)


def available() -> bool:
    return abi() >= MIN_ABI


def _fail(what: str) -> SandboxError:
    errno = ctypes.get_errno()
    return SandboxError(f"Landlock {what} failed: {os.strerror(errno)}")


def restrict(writable: Iterable[Path]) -> None:
    """From now on this process and its children write only under ``writable``."""
    if not available():
        raise SandboxError(f"Landlock ABI {MIN_ABI}+ is needed; this kernel has {abi()}")
    handled = _WRITE_FILE | _REMOVE_DIR | _REMOVE_FILE | _MAKE | _REFER | _TRUNCATE
    attr = _RulesetAttr(handled)
    ruleset = _libc.syscall(
        _SYS_CREATE_RULESET, ctypes.byref(attr), ctypes.c_size_t(ctypes.sizeof(attr)), 0
    )
    if ruleset < 0:
        raise _fail("create_ruleset")
    try:
        for path in writable:
            if not path.exists():
                continue
            fd = os.open(path, os.O_PATH | os.O_CLOEXEC)
            try:
                rights = handled if path.is_dir() else _FILE_RIGHTS
                rule = _PathBeneathAttr(rights, fd)
                if _libc.syscall(_SYS_ADD_RULE, ruleset, _RULE_PATH_BENEATH, ctypes.byref(rule), 0):
                    raise _fail(f"add_rule on {path}")
            finally:
                os.close(fd)
        if _libc.prctl(_PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0):
            raise _fail("no_new_privs")
        if _libc.syscall(_SYS_RESTRICT_SELF, ruleset, 0):
            raise _fail("restrict_self")
    finally:
        os.close(ruleset)


def wrap(cmd: Sequence[str], writable: Iterable[Path]) -> list[str]:
    """``cmd`` run under the sandbox, writing only under ``writable`` and ``TOOL_DIRS``."""
    dirs = [*writable, *TOOL_DIRS]
    flags = [arg for path in dirs for arg in ("--write", str(path))]
    # By path, not `-m runner.sandbox`: started in a copy, `-m` would import the copy's runner
    return [sys.executable, str(Path(__file__).resolve()), *flags, "--", *cmd]


def main(argv: Sequence[str]) -> None:
    args = list(argv)
    split = args.index("--")
    flags, cmd = args[:split], args[split + 1 :]
    writable = [Path(flags[i + 1]) for i, flag in enumerate(flags) if flag == "--write"]
    restrict(writable)
    os.execvp(cmd[0], cmd)  # noqa: S606 - the bench's own command


if __name__ == "__main__":
    main(sys.argv[1:])
