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
READ_TOOLS = ("Read", "Glob", "Grep")
EDIT_TOOLS = (*READ_TOOLS, "Edit", "Write")
CHECK_TOOLS = ("Bash(uv run pytest:*)", "Bash(uv run ruff:*)", "Bash(uv run mypy:*)")
GIT_READ_TOOLS = ("Bash(git diff:*)", "Bash(git log:*)", "Bash(git show:*)")


@dataclass(frozen=True)
class ClaudeJob:
    kind: str  # "escalation" | "review" | "narrative"
    prompt: str
    allowed_tools: tuple[str, ...]
    permission_mode: str = "dontAsk"  # anything not in allowed_tools is denied, no prompts


@dataclass(frozen=True)
class ClaudeResult:
    ok: bool
    text: str
    duration_s: float
    usage: dict[str, int] = field(default_factory=dict)
    num_turns: int = 0


class UsageLimited(Exception):
    def __init__(self, resets_at: datetime | None) -> None:
        super().__init__(f"Claude usage limit reached; resets at {resets_at}")
        self.resets_at = resets_at


def claude_env(environ: Mapping[str, str]) -> dict[str, str]:
    return {k: v for k, v in environ.items() if k not in STRIPPED_ENV}


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


def run_claude(
    job: ClaudeJob, repo: Path, timeout: int, log_path: Path, now: datetime
) -> ClaudeResult:
    cmd = [
        "claude",
        "-p",
        job.prompt,
        "--output-format",
        "json",
        "--permission-mode",
        job.permission_mode,
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
    if is_error:
        limited, resets_at = usage_limit_reset(text + proc.stderr, now)
        if limited:
            raise UsageLimited(resets_at)
    return ClaudeResult(
        ok=not is_error,
        text=text,
        duration_s=duration,
        usage=_usage(data),
        num_turns=int(data.get("num_turns") or 0),
    )
