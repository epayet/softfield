"""Claude's token use, read from Claude Code's own transcripts.

Interactive sessions and the runner's headless ``claude -p`` runs both save a transcript
under ``~/.claude/projects/<repo path>/``, so one scan covers both. Rough by design: it
only has to say how the work split between Claude and the local model.
"""

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# A guess, to calibrate by having Claude do one local-model task itself: Claude caches the
# conversation it re-sends each step, so a task costs it about half the local model's
# (uncached) token count in new tokens.
CLAUDE_NEW_PER_LOCAL_TOKEN = 0.5


@dataclass(frozen=True)
class ClaudeUsage:
    new: int = 0  # input, cache writes and output
    cached: int = 0  # re-read from the prompt cache, about a tenth of the price


def transcripts_dir(repo: Path) -> Path:
    base = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    return base / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(repo.resolve()))


def claude_tokens(folder: Path, since: datetime, until: datetime | None = None) -> ClaudeUsage:
    """Tokens Claude used in ``[since, until)``: new ones, and those re-read from its cache.

    Claude Code writes one line per content block and repeats the message's usage on each,
    so every message is counted once, by its id.
    """
    if not folder.is_dir():
        return ClaudeUsage()
    seen: set[str] = set()
    new = cached = 0
    for path in sorted(folder.rglob("*.jsonl")):
        with path.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(entry, dict) or entry.get("type") != "assistant":
                    continue
                message = entry.get("message") or {}
                usage = message.get("usage") or {}
                key = message.get("id") or entry.get("uuid")
                if not usage or not key or key in seen:
                    continue
                try:
                    at = datetime.fromisoformat(entry["timestamp"])
                except (KeyError, TypeError, ValueError):
                    continue
                if at < since or (until is not None and at >= until):
                    continue
                seen.add(key)
                new += sum(
                    int(usage.get(name) or 0)
                    for name in ("input_tokens", "cache_creation_input_tokens", "output_tokens")
                )
                cached += int(usage.get("cache_read_input_tokens") or 0)
    return ClaudeUsage(new=new, cached=cached)


def short(tokens: int) -> str:
    """``1_400_000`` → ``1.4M``, ``420_000`` → ``420k``."""
    if tokens >= 1_000_000:
        return f"{tokens / 1_000_000:.1f}M"
    if tokens >= 1_000:
        return f"{tokens / 1_000:.0f}k"
    return str(tokens)


def work_summary(label: str, tasks: list[str], local: int, claude: ClaudeUsage) -> str:
    """One paragraph: what the local model built, what Claude spent, what Claude saved."""
    if not tasks:
        return f"**Who did the work in {label}.** No local-model tasks yet."
    text = (
        f"**Who did the work in {label}.** The local model built {len(tasks)} task(s)"
        f" ({', '.join(tasks)}) using **{short(local)} tokens**, on your own GPU."
        f" Claude used **{short(claude.new)} new tokens** (plus {short(claude.cached)}"
        " re-read from its cache, at about a tenth of the price) on everything else:"
        " planning, writing the tests, its own protected work and the reviews."
    )
    saved = round(local * CLAUDE_NEW_PER_LOCAL_TOKEN)
    if saved and claude.new:
        text += (
            f" Building those tasks itself would have cost Claude roughly"
            f" **{short(saved)} more** new tokens, about **{saved / claude.new:.0%}** on top"
            " of what it spent (a rough guess: half the local model's count, since Claude"
            " caches what it re-reads)."
        )
    return text
