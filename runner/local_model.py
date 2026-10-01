"""The local executor: LM Studio warm-up and headless OpenCode runs."""

import contextlib
import json
import os
import signal
import sqlite3
import subprocess
import tempfile
import time
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TokenTotals:
    input: int = 0
    output: int = 0
    reasoning: int = 0
    steps: int = 0
    peak: int = 0  # the largest context one step sent, cached input included


@dataclass(frozen=True)
class StreamFacts:
    """What an attempt did, from OpenCode's event stream (ADR 12 items 4, 6 and 7)."""

    session_id: str = ""
    edit_streak: int = 0  # the longest run of edits without running a command
    refused: int = 0  # shell commands refused or failed to start
    edits: int = 0


@dataclass(frozen=True)
class OpencodeRun:
    exit_code: int | None  # None when it timed out
    duration_s: float
    tokens: TokenTotals
    facts: StreamFacts = StreamFacts()

    @property
    def timed_out(self) -> bool:
        return self.exit_code is None


def parse_events(lines: Iterable[str]) -> TokenTotals:
    """Sum token usage over OpenCode's ``--format json`` step_finish events."""
    inp = out = reasoning = steps = peak = 0
    for event in _events(lines):
        if event.get("type") != "step_finish":
            continue
        tokens = (event.get("part") or {}).get("tokens") or {}
        cache = tokens.get("cache") or {}
        step_in = int(tokens.get("input", 0))
        inp += step_in
        out += int(tokens.get("output", 0))
        reasoning += int(tokens.get("reasoning", 0))
        steps += 1
        peak = max(peak, step_in + int(cache.get("read", 0)) + int(cache.get("write", 0)))
    return TokenTotals(input=inp, output=out, reasoning=reasoning, steps=steps, peak=peak)


EDIT_TOOLS = ("edit", "write", "patch", "multiedit")
# OpenCode keeps each session's parts, the developer's reasoning included (read-only here).
OPENCODE_DB = Path.home() / ".local" / "share" / "opencode" / "opencode.db"


def _events(lines: Iterable[str]) -> Iterable[dict[str, Any]]:
    for line in lines:
        line = line.strip()
        if line.startswith("{"):
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def stream_facts(lines: Iterable[str]) -> StreamFacts:
    session, streak, longest, refused, edits = "", 0, 0, 0, 0
    for event in _events(lines):
        session = session or str(event.get("sessionID") or "")
        if event.get("type") != "tool_use":
            continue
        part = event.get("part") or {}
        tool = part.get("tool")
        if tool in EDIT_TOOLS:
            edits += 1
            streak += 1
            longest = max(longest, streak)
        elif tool == "bash":
            streak = 0
            if (part.get("state") or {}).get("status") == "error":
                refused += 1
    return StreamFacts(session_id=session, edit_streak=longest, refused=refused, edits=edits)


def empty_cause(facts: StreamFacts, timed_out: bool) -> str:
    """Why an attempt changed nothing: it ran out of time, its commands were refused, or it
    stopped early (it thinks it's done, or asked something nobody answers)."""
    if timed_out:
        return "timeout"
    if facts.refused:
        return "refused"
    return "stopped"


def session_reasoning(db: Path, session_id: str) -> str:
    """The developer's thinking in one OpenCode session, oldest first; empty if unavailable."""
    if not session_id or not db.is_file():
        return ""
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            rows = con.execute(
                "select data from part where session_id = ? order by time_created, id",
                (session_id,),
            ).fetchall()
        finally:
            con.close()
    except sqlite3.Error:
        return ""
    texts = []
    for (data,) in rows:
        try:
            part = json.loads(data)
        except json.JSONDecodeError:
            continue
        if part.get("type") == "reasoning" and part.get("text"):
            texts.append(str(part["text"]).strip())
    return "\n\n".join(texts)


def warmup(base_url: str, model: str, timeout: int) -> float:
    """One sequential tiny request so LM Studio JIT-loads the model with the owner's settings."""
    body = json.dumps(
        {"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1}
    ).encode()
    request = urllib.request.Request(  # noqa: S310 - base_url is our localhost config
        f"{base_url}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - localhost
        response.read()
    return time.monotonic() - started


def loaded_context_length(base_url: str, model: str) -> int | None:
    try:
        with urllib.request.urlopen(f"{base_url}/api/v0/models/{model}", timeout=10) as r:  # noqa: S310
            data = json.load(r)
    except OSError:
        return None
    value = data.get("loaded_context_length")
    return int(value) if value else None


LIVE_EVERY = 30.0  # seconds between live updates while an attempt runs (f1 D3)


def run_streaming(
    cmd: list[str],
    cwd: Path,
    timeout: float,
    out_path: Path,
    on_tick: Callable[[], None] | None = None,
    every: float = LIVE_EVERY,
    clock: Callable[[], float] = time.monotonic,
) -> tuple[str, int | None]:
    """Run ``cmd`` in its own process group, its stdout written straight into ``out_path``
    as it comes, calling ``on_tick`` every ``every`` seconds; on timeout kill the whole group.

    OpenCode starts shell commands of its own (pytest, ruff…). Killing only OpenCode would
    leave a hung child running after the attempt. Returns (stderr, exit code or None).
    """
    with out_path.open("w", encoding="utf-8") as out, tempfile.TemporaryFile("w+") as err:
        proc = subprocess.Popen(
            cmd, cwd=cwd, stdout=out, stderr=err, text=True, start_new_session=True
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


def run_opencode(
    repo: Path,
    model: str,
    title: str,
    prompt: str,
    timeout: int,
    log_path: Path,
    on_progress: Callable[[TokenTotals], None] | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> OpencodeRun:
    """One attempt. Its stream goes into ``log_path`` line by line; every ``LIVE_EVERY``
    seconds ``on_progress`` gets the tokens so far (f1 D3)."""
    cmd = ["opencode", "run", "--format", "json", "-m", model, "--title", title, prompt]
    started = time.monotonic()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    def read() -> list[str]:
        return log_path.read_text(encoding="utf-8", errors="replace").splitlines()

    def tick() -> None:
        if on_progress is not None:
            on_progress(parse_events(read()))

    stderr, exit_code = run_streaming(cmd, repo, timeout, log_path, tick, clock=clock)
    lines = read()
    marker = "\n--- timed out ---\n" if exit_code is None else "\n--- stderr ---\n" + stderr
    with log_path.open("a", encoding="utf-8") as log:
        log.write(marker)
    return OpencodeRun(
        exit_code=exit_code,
        duration_s=time.monotonic() - started,
        tokens=parse_events(lines),
        facts=stream_facts(lines),
    )
