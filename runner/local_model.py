"""Headless OpenCode runs, the ``opencode`` harness's adapter, and LM Studio's warm-up.

The agent's model picks the provider in opencode.json: ``lmstudio/…`` is the local model,
``ollama/<tag>`` an Ollama Cloud model through the local daemon (f1-18's probe). Both stream
the same events, so tokens and facts are read alike; only the local model is warmed up.
"""

import json
import os
import re
import sqlite3
import time
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from runner.agents import Agent, JobResult, JobSpec, Refusal
from runner.claude import usage_limit_reset

# Shared with Claude's adapter since f1-51; loop and the tests still find them here.
from runner.procs import LIVE_EVERY as LIVE_EVERY
from runner.procs import run_streaming as run_streaming

LOCAL_PROVIDER = "lmstudio"
# f4-05: OpenCode killed a shell call at 120 s, check-all included; 15 min is under [timeouts] gate
SHELL_TIMEOUT_ENV = {"OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS": "900000"}


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
    stderr: str = ""
    errors: str = ""  # the stream's error events, if any
    stopped: str = ""  # why it was stopped early, one of STOP_REASONS (f2-05)

    @property
    def timed_out(self) -> bool:
        return self.exit_code is None and not self.stopped


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


def stream_errors(lines: Iterable[str]) -> str:
    """The stream's error events, one per line (their shape for a cloud refusal is unknown)."""
    errors = (event for event in _events(lines) if event.get("type") == "error")
    return "\n".join(json.dumps(event.get("error") or event) for event in errors)


def empty_cause(refused: int, timed_out: bool) -> str:
    """Why an attempt changed nothing: it ran out of time, its commands were refused, or it
    stopped early (it thinks it's done, or asked something nobody answers)."""
    if timed_out:
        return "timeout"
    if refused:
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


# f2-05: in f1, 6 of 24 failed local attempts made no edit in 25-30 minutes, some thinking
# one phrase over and over; at each tick an attempt stuck like this is stopped.
NO_EDIT_AFTER = 10 * 60.0
REPEAT_WINDOW = 4000  # the characters of reasoning, last first, that must all repeat
MAX_PHRASE = 200  # how long the repeated phrase may be
STOP_NO_EDIT = "stopped: no edit after 10 min"
STOP_REPEATING = "stopped: repeating itself"
STOP_REASONS = (STOP_NO_EDIT, STOP_REPEATING)


def repeating(reasoning: str) -> bool:
    """Whether the last ``REPEAT_WINDOW`` characters of reasoning, its spacing ignored, are
    one phrase of at most ``MAX_PHRASE`` characters repeated."""
    tail = " ".join(reasoning.split())[-REPEAT_WINDOW:]
    if len(tail) < REPEAT_WINDOW:
        return False
    return any(tail[n:] == tail[:-n] for n in range(1, MAX_PHRASE + 1))


def stuck(lines: list[str], reasoning: str, elapsed: float) -> str:
    """Why an attempt so far should be stopped (one of ``STOP_REASONS``), or ''."""
    if elapsed >= NO_EDIT_AFTER and not stream_facts(lines).edits:
        return STOP_NO_EDIT
    return STOP_REPEATING if repeating(reasoning) else ""


def stop_reason(result: JobResult) -> str | None:
    """Why an OpenCode attempt was stopped early, or None if it wasn't."""
    return result.text if not result.ok and result.text in STOP_REASONS else None


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
    seconds ``on_progress`` gets the tokens so far (f1 D3), and an attempt found ``stuck``
    is stopped (f2-05). Its reasoning isn't in the stream: OpenCode's database has it."""
    cmd = ["opencode", "run", "--format", "json", "-m", model, "--title", title, prompt]
    started = time.monotonic()
    begun = clock()
    stopped = ""
    log_path.parent.mkdir(parents=True, exist_ok=True)

    def read() -> list[str]:
        return log_path.read_text(encoding="utf-8", errors="replace").splitlines()

    def tick() -> bool:
        nonlocal stopped
        lines = read()
        if on_progress is not None:
            on_progress(parse_events(lines))
        reasoning = session_reasoning(OPENCODE_DB, stream_facts(lines).session_id)
        stopped = stuck(lines, reasoning, clock() - begun)
        return bool(stopped)

    env = {**os.environ, **SHELL_TIMEOUT_ENV}
    stderr, exit_code = run_streaming(cmd, repo, timeout, log_path, tick, clock=clock, env=env)
    lines = read()
    if stopped:
        marker = f"\n--- {stopped} ---\n"
    elif exit_code is None:
        marker = "\n--- timed out ---\n"
    else:
        marker = "\n--- stderr ---\n" + stderr
    with log_path.open("a", encoding="utf-8") as log:
        log.write(marker)
    return OpencodeRun(
        exit_code=exit_code,
        duration_s=time.monotonic() - started,
        tokens=parse_events(lines),
        facts=stream_facts(lines),
        stderr=stderr,
        errors=stream_errors(lines),
        stopped=stopped,
    )


def is_local(agent: Agent) -> bool:
    """Whether the agent's model is LM Studio's (``lmstudio/…``) rather than a cloud one."""
    return agent.model.split("/", 1)[0] == LOCAL_PROVIDER


# Errors that pass: the daemon down or restarting, an overload, a server error.
TRANSIENT_RE = re.compile(
    r"(ECONNREFUSED|ECONNRESET|connection (?:refused|reset)|socket hang up|overloaded"
    r"|\b50[234]\b|service unavailable|bad gateway|gateway time-?out)",
    re.IGNORECASE,
)


def classify(run: OpencodeRun, local: bool, now: datetime) -> tuple[Refusal | None, bool]:
    """An errored run's class (ADR 15 item 12): (a refusal, or None; whether it's transient).

    The local model never refuses: its errors are failures, and the gates judge its work as
    before. No Ollama refusal has been seen (f1-18), so a cloud error that names a limit is
    one, a passing one is transient, and any other is a possible limit with no reset, which
    the allowance cools down (ADR 15 item 2) rather than counting as a failed attempt.
    A timeout, or an attempt stopped stuck, is a failure everywhere.
    """
    text = "\n".join(t for t in (run.errors, run.stderr.strip()) if t)
    if local or run.exit_code is None or (run.exit_code == 0 and not run.errors):
        return None, False
    limited, resets_at = usage_limit_reset(text, now)
    if limited:
        return Refusal(None, resets_at), False
    if TRANSIENT_RE.search(text):
        return None, True
    return Refusal(None, None, certain=False), False


class OpencodeAdapter:
    """A `JobSpec` as an ``opencode run`` on the agent's model. Its permissions are
    opencode.json's: edits anywhere in the repo and the check commands, the developer's.
    ``on_progress`` gets the tokens so far every ``LIVE_EVERY`` seconds (f1 D3)."""

    def run(
        self,
        agent: Agent,
        spec: JobSpec,
        repo: Path,
        log_path: Path,
        now: datetime,
        on_progress: Callable[[TokenTotals], None] | None = None,
    ) -> JobResult:
        title = spec.title or spec.role
        run = run_opencode(
            repo, agent.model, title, spec.prompt, spec.timeout, log_path, on_progress=on_progress
        )
        refusal, transient = classify(run, is_local(agent), now)
        tokens, facts = run.tokens, run.facts
        failed = run.exit_code != 0 or bool(run.errors)
        if run.stopped:
            text = run.stopped
        elif run.timed_out:
            text = "timed out"
        else:
            text = (run.errors or run.stderr.strip())[:500]
        return JobResult(
            ok=not failed,
            text=text,
            duration_s=run.duration_s,
            usage={
                "input_tokens": tokens.input,
                "output_tokens": tokens.output,
                "reasoning_tokens": tokens.reasoning,
            },
            refusal=refusal,
            transient=transient,
            num_turns=tokens.steps,
            session_id=facts.session_id or None,
            peak_context=tokens.peak,
            edit_streak=facts.edit_streak,
            refused_commands=facts.refused,
            edits=facts.edits,
            timed_out=run.timed_out,
            model=agent.model,  # OpenCode's stream doesn't name it; the agent's is exact
        )


ADAPTER = OpencodeAdapter()
