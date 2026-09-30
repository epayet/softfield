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
class ClaudeResult:
    ok: bool
    text: str
    duration_s: float
    usage: dict[str, int] = field(default_factory=dict)
    num_turns: int = 0
    session_id: str | None = None
    cost_usd: float | None = None  # Claude Code's API-equivalent price (f1 D7)


class UsageLimited(Exception):
    """A job stopped by a usage limit. ``session_id`` lets the caller resume it after the
    reset; ``certain`` is False when the error only looks like a limit (a wording
    ``usage_limit_reset`` doesn't know), so the caller retries a bounded number of times."""

    def __init__(
        self, resets_at: datetime | None, session_id: str | None = None, certain: bool = True
    ) -> None:
        super().__init__(f"Claude usage limit reached; resets at {resets_at}")
        self.resets_at = resets_at
        self.session_id = session_id
        self.certain = certain


def claude_env(environ: Mapping[str, str]) -> dict[str, str]:
    return {k: v for k, v in environ.items() if k not in STRIPPED_ENV}


# Words that suggest a limit in an error the precise patterns below don't recognise.
_MAYBE_LIMIT_RE = re.compile(r"\b(limit|quota|capacity)\b", re.IGNORECASE)
_LIMIT_RE = re.compile(r"(usage limit|hit your limit|limit reached|rate limit)", re.IGNORECASE)
_EPOCH_RE = re.compile(r"\|(\d{10})\b")
_CLOCK_RE = re.compile(r"resets?\s+(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", re.IGNORECASE)


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
        reset = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if reset <= now:
            reset += timedelta(days=1)
        return True, reset
    return True, None


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
        "json",
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
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = {"is_error": True, "result": proc.stdout + proc.stderr}
    text = str(data.get("result", ""))
    is_error = bool(data.get("is_error")) or proc.returncode != 0
    session_id = str(data["session_id"]) if data.get("session_id") else None
    if is_error:
        limited, resets_at = usage_limit_reset(text + proc.stderr, now)
        if limited:
            raise UsageLimited(resets_at, session_id)
        if _MAYBE_LIMIT_RE.search(text + proc.stderr):
            raise UsageLimited(None, session_id, certain=False)
    return ClaudeResult(
        ok=not is_error,
        text=text,
        duration_s=duration,
        usage=_usage(data),
        num_turns=int(data.get("num_turns") or 0),
        session_id=session_id,
        cost_usd=float(cost) if (cost := data.get("total_cost_usd")) is not None else None,
    )
