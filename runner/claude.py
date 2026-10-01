"""Headless Claude (``claude -p``) on the owner's Pro login.

The subprocess environment never carries API keys or base URLs, so a run can
never fall back to API billing or to LM Studio. Usage limits pause the runner
until the reset instead of retrying in a loop.
"""

import json
import os
import re
import subprocess
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

STRIPPED_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN")

# Tools per job kind: the least each job needs. The runner commits; Claude never runs git.
# A path-scoped file rule is `Edit(<glob>)`, which covers the Write tool too; `Write(<glob>)`
# grants nothing (probed with claude -p, 2026-09-30).
READ_TOOLS = ("Read", "Glob", "Grep")
EDIT_TOOLS = (*READ_TOOLS, "Edit", "Write")
CHECK_TOOLS = (
    "Bash(uv run pytest:*)",
    "Bash(uv run ruff:*)",
    "Bash(uv run mypy:*)",
    "Bash(uv run runner check-all:*)",  # never the owner's commands (signoff, accept)
)
GIT_READ_TOOLS = ("Bash(git diff:*)", "Bash(git log:*)", "Bash(git show:*)")


@dataclass(frozen=True)
class ClaudeJob:
    kind: str  # "escalation" | "direction" | "checkpoint" | "lead-ticket" | "review" | …
    prompt: str
    allowed_tools: tuple[str, ...]
    permission_mode: str = "dontAsk"  # anything not in allowed_tools is denied, no prompts
    model: str = ""  # empty: Claude Code's default


@dataclass(frozen=True)
class Reading:
    """One of Claude's allowance windows, from a stream's ``rate_limit_event`` (ADR 15 item 3)."""

    window: str  # "five_hour" | "seven_day"
    utilization: float  # the share used, 0–1
    resets_at: datetime


@dataclass(frozen=True)
class ClaudeResult:
    ok: bool
    text: str
    duration_s: float
    usage: dict[str, int] = field(default_factory=dict)
    num_turns: int = 0
    session_id: str | None = None
    cost_usd: float | None = None  # Claude Code's API-equivalent price (f1 D7)
    readings: tuple[Reading, ...] = ()  # every window of every rate_limit_event, in order


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


def claude_env(environ: Mapping[str, str]) -> dict[str, str]:
    return {k: v for k, v in environ.items() if k not in STRIPPED_ENV}


# Words that suggest a limit in an error the precise patterns below don't recognise.
_MAYBE_LIMIT_RE = re.compile(r"\b(limit|quota|capacity)\b", re.IGNORECASE)
_LIMIT_RE = re.compile(
    r"(usage limit|hit your (?:\w+ )?limit|(?:session|weekly) limit|limit reached|rate limit)",
    re.IGNORECASE,
)
_EPOCH_RE = re.compile(r"\|(\d{10})\b")
_CLOCK_RE = re.compile(r"resets?\s+(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", re.IGNORECASE)
_ZONE_RE = re.compile(r"\(([A-Za-z_]+/[A-Za-z_/]+)\)")  # "resets 6:50pm (Europe/London)"


def _zone(text: str, now: datetime) -> datetime:
    """``now`` in the time zone the message names, if it names one we know."""
    if match := _ZONE_RE.search(text):
        try:
            return now.astimezone(ZoneInfo(match.group(1)))
        except (ZoneInfoNotFoundError, ValueError):
            pass
    return now


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
        return True, reset
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
        " Use Read, Grep and Glob for everything else."
    )


def run_claude(
    job: ClaudeJob,
    repo: Path,
    timeout: int,
    log_path: Path,
    now: datetime,
    resume: str | None = None,
) -> ClaudeResult:
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
        "--allowedTools",
        *job.allowed_tools,
    ]
    started = time.monotonic()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            cmd,
            cwd=repo,
            env=claude_env(os.environ),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        log_path.write_text("--- timed out ---\n", encoding="utf-8")
        return ClaudeResult(ok=False, text="timed out", duration_s=time.monotonic() - started)
    log_path.write_text(proc.stdout + "\n--- stderr ---\n" + proc.stderr, encoding="utf-8")
    duration = time.monotonic() - started
    stream = _parse_stream(proc.stdout, now)
    data = stream.result or {"is_error": True, "result": stream.other + proc.stderr}
    text = str(data.get("result", ""))
    is_error = bool(data.get("is_error")) or proc.returncode != 0
    session_id = str(data["session_id"]) if data.get("session_id") else None
    readings = stream.readings
    if is_error:
        limited, resets_at = usage_limit_reset(text + proc.stderr, now)
        # The status is structured, so it outlasts a change of wording; the text only says when.
        if limited or data.get("api_error_status") == 429:
            window = stream.rejected.get("rateLimitType")
            raise UsageLimited(
                resets_at or _epoch(stream.rejected.get("resetsAt"), now),
                session_id,
                window=str(window) if window else None,
                readings=readings,
            )
        if _MAYBE_LIMIT_RE.search(text + proc.stderr):
            raise UsageLimited(None, session_id, certain=False, readings=readings)
        if _transient(data, stream):
            raise TransientError(text.strip()[:200], session_id, readings)
    return ClaudeResult(
        ok=not is_error,
        text=text,
        duration_s=duration,
        usage=_usage(data),
        num_turns=int(data.get("num_turns") or 0),
        session_id=session_id,
        cost_usd=float(cost) if (cost := data.get("total_cost_usd")) is not None else None,
        readings=readings,
    )
