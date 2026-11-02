"""A signed-off milestone goes to its project's remote (ADR 42). Only the owner's sign-off pushes,
and no model decides: at each pick, any ``<key>-done`` tag the remote lacks goes, with main up to
exactly that commit, oldest first. Never a task, plan or superseded branch, and never ``--force``.
A secret check reads what is about to go first, and names a file and line, never the value."""

import json
import os
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from runner.procs import run_bounded

TIMEOUT = 300  # seconds, a push or a fetch
MAIN = "main"
REMOTE = "origin"
STATE = Path(".softfield") / "var" / "push.json"
KEEPS_FAILING = timedelta(hours=6)  # a passing network error says nothing until then

_SECRETS = re.compile(
    r"sk-ant-[A-Za-z0-9_-]{10,}|sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}"
    r"|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}"
    r"|AIza[0-9A-Za-z_-]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY|sk_live_[A-Za-z0-9]+"
)
_RISKY_FILE = re.compile(
    r"(^|/)(\.env(\.(?!example$)[^/]+)?|id_rsa|id_ed25519|[^/]+\.(pem|key|sqlite3?|db))$"
)
_HUNK = re.compile(r"^@@ -\S+ \+(\d+)")

Run = Callable[[list[str], Path, float, Mapping[str, str] | None], tuple[int | None, str, str]]


def secret_problems(diff: str, topic: str | None) -> list[str]:
    """``file:line`` and what it looks like, from ``git log -p -U0``'s added lines. Never the
    value: this reaches the desk."""
    found: list[str] = []
    path, line = "", 0
    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            path = raw[4:].removeprefix("b/")
            if _RISKY_FILE.search(path):
                found.append(f"{path}: a file that shouldn't be public")
        elif hit := _HUNK.match(raw):
            line = int(hit[1])
        elif raw.startswith("+"):
            if _SECRETS.search(raw):
                found.append(f"{path}:{line}: looks like a key or a token")
            elif topic and topic in raw:
                found.append(f"{path}:{line}: this machine's notification topic")
            line += 1
    return list(dict.fromkeys(found))


@dataclass(frozen=True)
class Outcome:
    pushed: tuple[str, ...] = ()
    held: str = ""  # a secret or a diverged remote: the owner's, not a passing error
    failed: str = ""  # a network error or the like: it tries again


def _git(run: Run, repo: Path, *args: str) -> tuple[int | None, str, str]:
    # Nobody is there to type a password, or a key's passphrase
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_SSH_COMMAND": "ssh -o BatchMode=yes"}
    return run(["git", *args], repo, TIMEOUT, env)


def remote_of(repo: Path, run: Run = run_bounded) -> str | None:
    """``origin`` when the repo has one: setting it is how a project opts in (the owner,
    2026-11-02, ADR 42 item 2). Without it nothing is pushed."""
    return REMOTE if _git(run, repo, "remote", "get-url", REMOTE)[0] == 0 else None


def _done_tags(run: Run, repo: Path) -> list[str]:
    _, out, _ = _git(
        run, repo, "for-each-ref", "--sort=creatordate", "--format=%(refname:short)", "refs/tags"
    )
    return [tag for tag in out.split() if tag.endswith("-done")]


def _is_ancestor(run: Run, repo: Path, older: str, newer: str) -> bool:
    return _git(run, repo, "merge-base", "--is-ancestor", older, newer)[0] == 0


def push_signed_off(
    repo: Path, remote: str, topic: str | None = None, run: Run = run_bounded
) -> Outcome:
    """Every ``-done`` tag the remote lacks, oldest first; the first that can't go stops the
    round, and the next pick starts over from what the remote says."""
    code, out, err = _git(run, repo, "ls-remote", remote, f"refs/heads/{MAIN}", "refs/tags/*-done")
    if code != 0:
        return Outcome(failed=err.strip() or "the remote didn't answer")
    theirs = {ref: sha for sha, ref in (line.split() for line in out.splitlines() if line.strip())}
    tip = theirs.get(f"refs/heads/{MAIN}")
    if tip is not None and _git(run, repo, "cat-file", "-e", f"{tip}^{{commit}}")[0] != 0:
        code, _, err = _git(run, repo, "fetch", "-q", remote, MAIN)
        if code != 0:
            return Outcome(failed=err.strip() or "the fetch failed")
    pushed: list[str] = []
    for tag in _done_tags(run, repo):
        if f"refs/tags/{tag}" in theirs:
            continue
        commit = f"{tag}^{{commit}}"
        behind = tip is not None and _is_ancestor(run, repo, commit, tip)
        if tip is not None and not behind and not _is_ancestor(run, repo, tip, commit):
            held = f"{remote}'s main has moved apart from this one, so {tag} stays here."
            return Outcome(tuple(pushed), held=f"{held} Nothing was forced.")
        span = [commit] if tip is None else [f"{tip}..{commit}"]
        _, diff, _ = _git(run, repo, "log", "-p", "-U0", "--no-color", "--format=", *span)
        if problems := secret_problems(diff, topic):
            listed = "; ".join(problems[:10])
            return Outcome(tuple(pushed), held=f"{tag} wasn't pushed: {listed}.")
        refs = (
            [f"refs/tags/{tag}"] if behind else [f"{commit}:refs/heads/{MAIN}", f"refs/tags/{tag}"]
        )
        code, _, err = _git(run, repo, "push", "-q", remote, *refs)
        if code != 0:
            return Outcome(tuple(pushed), failed=err.strip() or "the push failed")
        pushed.append(tag)
        if not behind:
            _, out, _ = _git(run, repo, "rev-parse", commit)
            tip = out.strip()
    return Outcome(tuple(pushed))


@dataclass(frozen=True)
class Memory:
    """What saves asking the remote at every pick, and how long a push has been failing."""

    settled: tuple[str, ...] = ()
    failing_since: str = ""


def read_memory(repo: Path) -> Memory:
    path = repo / STATE
    if not path.is_file():
        return Memory()
    data = json.loads(path.read_text(encoding="utf-8"))
    return Memory(tuple(data.get("settled", ())), str(data.get("failing_since", "")))


def write_memory(repo: Path, memory: Memory) -> None:
    path = repo / STATE
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps({"settled": list(memory.settled), "failing_since": memory.failing_since})
    path.write_text(text, encoding="utf-8")


def keeps_failing(since: str, now: datetime) -> bool:
    return bool(since) and now - datetime.fromisoformat(since) >= KEEPS_FAILING


def done_tags(repo: Path, run: Run = run_bounded) -> tuple[str, ...]:
    return tuple(_done_tags(run, repo))
