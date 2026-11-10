"""Headless Claude (``claude -p``) on the owner's Pro login: the ``claude`` harness's adapter.

The subprocess environment never carries API keys or base URLs, so a run can
never fall back to API billing or to LM Studio. A usage limit comes back as a
refusal with its reset, and the loop waits or parks instead of retrying in a loop.
"""

import json
import os
import re
import subprocess
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from runner import config
from runner.agents import ANY, Agent, JobResult, JobSpec, Reading, Refusal
from runner.procs import run_streaming

STRIPPED_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN")

# Every job may read. A path-scoped file rule is `Edit(<glob>)`, which covers the Write tool
# too; `Write(<glob>)` grants nothing (probed with claude -p, 2026-09-30).
READ_TOOLS = ("Read", "Glob", "Grep")
EDIT_ANYWHERE = ("Edit", "Write")


WEB_TOOLS = ("WebSearch", "WebFetch")


def web_reads(folders: Iterable[Path]) -> tuple[str, ...]:
    """Reads scoped to folders, for a job with the web (ADR 33 item 2).

    Claude Code's documented form for an absolute path is `Tool(//abs/path/**)`, and the
    Read rule covers Glob and Grep too. NOT PROBED with claude -p (2026-11-10): the session
    that wrote this could not run it. Probe it (a read in the repo works, `~/.ssh` is
    refused) and amend this comment with the result."""
    return tuple(
        f"{tool}(/{folder.resolve().as_posix()}/**)" for folder in folders for tool in READ_TOOLS
    )


def allowed_tools(spec: JobSpec, repo: Path | None = None) -> tuple[str, ...]:
    """A spec's tools as `--allowedTools`: reads, its edit globs, its command prefixes. With
    ``spec.web``: the web tools, and reads only in ``repo`` (the job's folder) and the live docs."""
    edits = EDIT_ANYWHERE if ANY in spec.edit else tuple(f"Edit({glob})" for glob in spec.edit)
    commands = tuple(f"Bash({command}:*)" for command in spec.commands)
    if not spec.web:
        return (*READ_TOOLS, *edits, *commands)
    folders = [repo or Path.cwd(), config.HOME / "docs"]
    return (*WEB_TOOLS, *web_reads(folders), *edits, *commands)


@dataclass(frozen=True)
class Progress:
    """A running job's tokens and turns so far, from its stream (f1 D3, amended)."""

    tokens_in: int
    tokens_cached: int
    tokens_out: int
    turns: int


@dataclass(frozen=True)
class ClaudeJob:
    kind: str  # "escalation" | "direction" | "checkpoint" | "lead-ticket" | "review" | …
    prompt: str
    allowed_tools: tuple[str, ...]
    permission_mode: str = "dontAsk"  # anything not in allowed_tools is denied, no prompts
    model: str = ""  # empty: Claude Code's default
    system: str = ""  # the factory's context, appended to the system prompt (ADR 41 item 2)
    # Gets the job's progress every LIVE_EVERY seconds while it runs; called from the thread
    # that runs the job.
    on_progress: Callable[[Progress], None] | None = field(default=None, compare=False)


class UsageLimited(Exception):
    """A job stopped by a usage limit. ``session_id`` lets the caller resume it after the
    reset; ``certain`` is False when the error only looks like a limit (a wording
    ``usage_limit_reset`` doesn't know), so the caller retries a bounded number of times.
    ``window`` is the one a rejected ``rate_limit_event`` named, if any."""

    def __init__(
        self,
        resets_at: datetime | None,
        session_id: str | None = None,
        certain: bool = True,
        *,
        window: str | None = None,
        readings: tuple[Reading, ...] = (),
    ) -> None:
        super().__init__(f"Claude usage limit reached; resets at {resets_at}")
        self.resets_at = resets_at
        self.session_id = session_id
        self.certain = certain
        self.window = window
        self.readings = readings


class TransientError(Exception):
    """A job cut off by something passing: a lost connection, an overload, a server error.
    The caller resumes ``session_id`` after a short wait instead of failing the job."""

    def __init__(
        self, detail: str, session_id: str | None = None, readings: tuple[Reading, ...] = ()
    ) -> None:
        super().__init__(detail)
        self.session_id = session_id
        self.readings = readings


class LoginExpired(Exception):
    """A job stopped because Claude's login has expired: it answers in under a second, and only
    the owner logging in again ends it, so the caller holds the job instead of retrying."""

    def __init__(
        self, detail: str, session_id: str | None = None, readings: tuple[Reading, ...] = ()
    ) -> None:
        super().__init__(detail)
        self.session_id = session_id
        self.readings = readings


def claude_env(environ: Mapping[str, str]) -> dict[str, str]:
    return {k: v for k, v in environ.items() if k not in STRIPPED_ENV}


# Words that suggest a limit in an error the precise patterns below don't recognise.
_MAYBE_LIMIT_RE = re.compile(r"\b(limit|quota|capacity)\b", re.IGNORECASE)
# Its status is null and its reason "api_error", as a lost connection's: only the words tell.
_LOGIN_RE = re.compile(r"Failed to authenticate", re.IGNORECASE)
_LIMIT_RE = re.compile(
    r"(usage limit|hit your (?:\w+ )?limit|(?:session|weekly) limit|limit reached|rate limit)",
    re.IGNORECASE,
)
_EPOCH_RE = re.compile(r"\|(\d{10})\b")
_CLOCK_RE = re.compile(r"resets?\s+(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", re.IGNORECASE)
_ZONE_RE = re.compile(r"\(([A-Za-z_]+/[A-Za-z_/]+)\)")  # "resets 6:50pm (Europe/London)"


def _zone(text: str, now: datetime) -> datetime:
    """``now`` in the time zone the message names, if it names one we know; else on the
    machine's clock, which is what a bare "resets 5pm" means, ``now`` being UTC (F187)."""
    if match := _ZONE_RE.search(text):
        try:
            return now.astimezone(ZoneInfo(match.group(1)))
        except (ZoneInfoNotFoundError, ValueError):
            pass
    return now.astimezone()


def usage_limit_reset(text: str, now: datetime) -> tuple[bool, datetime | None]:
    """Whether ``text`` reports a usage limit, and when it resets if we can tell."""
    if not _LIMIT_RE.search(text):
        return False, None
    if match := _EPOCH_RE.search(text):
        return True, datetime.fromtimestamp(int(match.group(1)), tz=now.tzinfo)
    if match := _CLOCK_RE.search(text):
        hour, minute, meridiem = int(match.group(1)), int(match.group(2) or 0), match.group(3)
        if meridiem:
            hour = hour % 12 + (12 if meridiem.lower() == "pm" else 0)
        if hour > 23 or minute > 59:
            return True, None
        now = _zone(text, now)
        reset = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if reset <= now:
            reset += timedelta(days=1)
        return True, reset.astimezone(UTC)  # the caller stores it (F187 D1)
    return True, None


@dataclass(frozen=True)
class _Stream:
    """What ``--output-format stream-json --verbose`` printed, as far as the runner cares."""

    result: dict[str, Any] | None  # the last line's `result` event: today's JSON output
    readings: tuple[Reading, ...]
    rejected: dict[str, Any]  # the last rate_limit_info whose status is "rejected", else {}
    other: str  # lines that aren't JSON events (an error printed before the stream)


def _epoch(value: object, now: datetime) -> datetime | None:
    if isinstance(value, int | float) and not isinstance(value, bool):
        return datetime.fromtimestamp(value, tz=now.tzinfo)
    return None


def _readings(info: dict[str, Any], now: datetime) -> list[Reading]:
    windows = info.get("unifiedWindows")
    found = []
    for name, window in (windows if isinstance(windows, dict) else {}).items():
        if not isinstance(window, dict):
            continue
        used, resets_at = window.get("utilization"), _epoch(window.get("resetsAt"), now)
        if isinstance(used, int | float) and resets_at is not None:
            found.append(Reading(str(name), float(used), resets_at))
    return found


def _parse_stream(stdout: str, now: datetime) -> _Stream:
    result: dict[str, Any] | None = None
    readings: list[Reading] = []
    rejected: dict[str, Any] = {}
    other: list[str] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            event = None
        if not isinstance(event, dict):
            other.append(line)
        elif event.get("type") == "result":
            result = event
        elif event.get("type") == "rate_limit_event":
            info = event.get("rate_limit_info")
            if isinstance(info, dict):
                readings += _readings(info, now)
                if info.get("status") == "rejected":
                    rejected = info
    return _Stream(result, tuple(readings), rejected, "\n".join(other))


def _costliest(usage: object) -> str | None:
    if not isinstance(usage, dict) or not usage:
        return None

    def cost(name: str) -> float:
        value = usage[name].get("costUSD") if isinstance(usage[name], dict) else None
        return float(value) if isinstance(value, int | float) else 0.0

    return str(max(usage, key=cost))


def stream_model(lines: Iterable[str]) -> str | None:
    """The model a job ran on, as its stream names it (f2-04): the `init` event's, else the
    main thread's first message's (a subagent's carry a ``parent_tool_use_id``), else the
    costliest in the result's ``modelUsage`` (all f1's `--output-format json` logs hold)."""
    usage: object = None
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        message = event.get("message")
        if event.get("type") == "system" and event.get("subtype") == "init":
            found = event.get("model")
        elif event.get("type") == "assistant" and isinstance(message, dict):
            found = None if event.get("parent_tool_use_id") else message.get("model")
        else:
            usage = event.get("modelUsage", usage)
            continue
        if isinstance(found, str) and found:
            return found
    return _costliest(usage)


def stream_session(lines: Iterable[str]) -> str | None:
    """The session a stream ran in, from its `init` event: what a job cut off at its limit,
    which never printed a result, resumes."""
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict) or event.get("type") != "system":
            continue
        if isinstance(found := event.get("session_id"), str) and found:
            return found
    return None


def progress(lines: Iterable[str]) -> Progress:
    """The tokens and turns of the stream so far. A message's content blocks come as separate
    `assistant` events with the same id; each message counts once, with its latest usage."""
    usages: dict[str, dict[str, Any]] = {}
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict) or event.get("type") != "assistant":
            continue
        message = event.get("message")
        if not isinstance(message, dict):
            continue
        usage = message.get("usage")
        usages[str(message.get("id") or len(usages))] = usage if isinstance(usage, dict) else {}
    total = {
        key: sum(int(u.get(key) or 0) for u in usages.values())
        for key in ("input_tokens", "cache_read_input_tokens", "output_tokens")
    }
    return Progress(
        total["input_tokens"], total["cache_read_input_tokens"], total["output_tokens"], len(usages)
    )


def _transient(data: dict[str, Any], stream: _Stream) -> bool:
    """An API error other than a limit (overload, server error, lost connection), or no
    result event at all: Claude Code never got to answer."""
    return data.get("terminal_reason") == "api_error" or stream.result is None


def backoff_seconds(attempt: int, minimum: int, maximum: int) -> int:
    return int(min(maximum, minimum * (2**attempt)))


def _usage(data: dict[str, Any]) -> dict[str, int]:
    usage = data.get("usage") or {}
    keys = (
        "input_tokens",
        "output_tokens",
        "cache_read_input_tokens",
        "cache_creation_input_tokens",
    )
    return {k: int(usage.get(k) or 0) for k in keys}


_BASH_RULE_RE = re.compile(r"^Bash\((.+?):\*\)$")


def shell_note(allowed_tools: tuple[str, ...]) -> str:
    """How a job may call Bash: the rules match a command's prefix, so `cd …;`, `git -C`,
    pipes and chains are denied (every Bash denial in the f0 rehearsal was one of those)."""
    prefixes = [m.group(1) for t in allowed_tools if (m := _BASH_RULE_RE.match(t))]
    if not prefixes:
        return ""
    allowed = ", ".join(f"`{p}`" for p in prefixes)
    return (
        "\n\nShell: you are already at the repo root. Run one command per Bash call, starting"
        f" with one of {allowed}; no `cd`, `git -C`, pipes, `;` or `&&`, or it is denied."
        " Use Read, Grep and Glob for everything else. Run every check in the foreground and"
        " wait for its result: nothing started in the background can be watched from here."
    )


def run_claude(
    job: ClaudeJob,
    repo: Path,
    timeout: int,
    log_path: Path,
    now: datetime,
    resume: str | None = None,
) -> JobResult:
    cmd = [
        "claude",
        "-p",
        job.prompt + shell_note(job.allowed_tools),
        "--output-format",
        "stream-json",  # its rate_limit_events are Claude's allowance (ADR 15 item 3)
        "--verbose",  # stream-json needs it with -p
        "--permission-mode",
        job.permission_mode,
        *(("--model", job.model) if job.model else ()),
        *(("--resume", resume) if resume else ()),
        *(("--append-system-prompt", job.system) if job.system else ()),  # ADR 41 item 2
        "--add-dir",
        str(config.INSTRUCTIONS),
        *(("--add-dir", str(docs)) if (docs := config.HOME / "docs").is_dir() else ()),
        *(("--allowedTools", *job.allowed_tools) if job.allowed_tools else ()),
    ]
    started = time.monotonic()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    def read() -> str:
        return log_path.read_text(encoding="utf-8", errors="replace")

    def tick() -> None:
        if job.on_progress is not None:
            job.on_progress(progress(read().splitlines()))

    # Read as it comes, like OpenCode's (f1 D3): the stream goes into the log line by line.
    stderr, returncode = run_streaming(
        cmd, repo, timeout, log_path, tick, env=claude_env(os.environ), stdin=subprocess.DEVNULL
    )
    stdout = read()
    if returncode is None:
        with log_path.open("a", encoding="utf-8") as log:
            log.write("\n--- timed out ---\n")
        return JobResult(
            ok=False,
            text="timed out",
            duration_s=time.monotonic() - started,
            session_id=stream_session(stdout.splitlines()),
            timed_out=True,
        )
    with log_path.open("a", encoding="utf-8") as log:
        log.write("\n--- stderr ---\n" + stderr)
    duration = time.monotonic() - started
    stream = _parse_stream(stdout, now)
    data = stream.result or {"is_error": True, "result": stream.other + stderr}
    text = str(data.get("result", ""))
    is_error = bool(data.get("is_error")) or returncode != 0
    session_id = str(data["session_id"]) if data.get("session_id") else None
    readings = stream.readings
    if is_error:
        if _LOGIN_RE.search(text + stderr):
            raise LoginExpired(text.strip()[:200], session_id, readings)
        limited, resets_at = usage_limit_reset(text + stderr, now)
        # The status is structured, so it outlasts a change of wording; the text only says when.
        if limited or data.get("api_error_status") == 429:
            window = stream.rejected.get("rateLimitType")
            raise UsageLimited(
                resets_at or _epoch(stream.rejected.get("resetsAt"), now),
                session_id,
                window=str(window) if window else None,
                readings=readings,
            )
        if _MAYBE_LIMIT_RE.search(text + stderr):
            raise UsageLimited(None, session_id, certain=False, readings=readings)
        if _transient(data, stream):
            raise TransientError(text.strip()[:200], session_id, readings)
    return JobResult(
        ok=not is_error,
        text=text,
        duration_s=duration,
        usage=_usage(data),
        num_turns=int(data.get("num_turns") or 0),
        session_id=session_id,
        cost_usd=float(cost) if (cost := data.get("total_cost_usd")) is not None else None,
        readings=readings,
        model=stream_model(stdout.splitlines()) or "",
    )


# A fresh reading of Claude's windows (f4-07): the cheapest call whose stream carries a
# `rate_limit_event`. One real Haiku "ok" cost $0.018 API-equivalent, ~21k tokens, mostly
# Claude Code's own cached prompt (tests/runner/fixtures/probes/claude-stream.jsonl).
PROBE_JOB = ClaudeJob("probe", "Reply with the single word: ok", (), model="haiku")
PROBE_TIMEOUT = 120  # seconds


def probe(repo: Path, log_path: Path, now: datetime) -> JobResult:
    """One `PROBE_JOB`. It never raises: a limit, an expired login or a passing error is a
    failed result, with whatever its stream read."""
    try:
        return run_claude(PROBE_JOB, repo, PROBE_TIMEOUT, log_path, now)
    except (UsageLimited, LoginExpired, TransientError) as exc:
        return JobResult(ok=False, text=str(exc), duration_s=0.0, readings=exc.readings)


class ClaudeAdapter:
    """A `JobSpec` as a `claude -p` job on the agent's model; a limit or a passing error
    comes back as a result (ADR 15 item 12), with the session to resume. ``on_progress`` gets
    the tokens and turns so far every ``LIVE_EVERY`` seconds (f1 D3, amended)."""

    def run(
        self,
        agent: Agent,
        spec: JobSpec,
        repo: Path,
        log_path: Path,
        now: datetime,
        on_progress: Callable[[Progress], None] | None = None,
    ) -> JobResult:
        job = ClaudeJob(
            spec.role,
            spec.prompt,
            allowed_tools(spec, repo),
            model=agent.model,
            system=spec.system,
            on_progress=on_progress,
        )
        try:
            return run_claude(job, repo, spec.timeout, log_path, now, resume=spec.resume)
        except UsageLimited as limit:
            return JobResult(
                ok=False,
                text=str(limit),
                duration_s=0.0,
                refusal=Refusal(limit.window, limit.resets_at, limit.certain),
                session_id=limit.session_id,
                readings=limit.readings,
            )
        except LoginExpired as expired:
            return JobResult(
                ok=False,
                text=str(expired),
                duration_s=0.0,
                login_expired=True,
                session_id=expired.session_id,
                readings=expired.readings,
            )
        except TransientError as blip:
            return JobResult(
                ok=False,
                text=str(blip),
                duration_s=0.0,
                transient=True,
                session_id=blip.session_id,
                readings=blip.readings,
            )


ADAPTER = ClaudeAdapter()
