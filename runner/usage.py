"""Claude's token use, read from Claude Code's own transcripts.

Interactive sessions and the runner's headless ``claude -p`` runs both save a transcript
under ``~/.claude/projects/<repo path>/``, so one scan covers both. Rough by design: it
only has to say how the work split between Claude and the local model.

Tokens are weighted by their relative API price, the best public proxy for how much of a
Pro allowance they use: a cache read counts 0.1, a cache write 1.25, output 5. Re-reading
a long conversation at every step is usually most of the cost.
"""

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

CACHE_READ_WEIGHT = 0.1
CACHE_WRITE_WEIGHT = 1.25
OUTPUT_WEIGHT = 5.0
# How many Claude steps a small local-model task would take if Claude did it directly
# (read the spec'd files, edit, run the tests, fix, commit). A guess to calibrate.
STEPS_PER_TASK = 5


@dataclass(frozen=True)
class ClaudeUsage:
    input: int = 0
    cache_write: int = 0
    cache_read: int = 0
    output: int = 0
    steps: int = 0  # API calls

    @property
    def weighted(self) -> float:
        """Input-token equivalents, weighted by price."""
        return (
            self.input
            + CACHE_WRITE_WEIGHT * self.cache_write
            + CACHE_READ_WEIGHT * self.cache_read
            + OUTPUT_WEIGHT * self.output
        )

    @property
    def per_step(self) -> float:
        return self.weighted / self.steps if self.steps else 0.0

    @property
    def rereading_share(self) -> float:
        return CACHE_READ_WEIGHT * self.cache_read / self.weighted if self.weighted else 0.0


def transcripts_dir(repo: Path) -> Path:
    base = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    return base / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(repo.resolve()))


def claude_tokens(folder: Path, since: datetime, until: datetime | None = None) -> ClaudeUsage:
    """Claude's usage in ``[since, until)``.

    Claude Code writes one line per content block and repeats the message's usage on each,
    so every message is counted once, by its id.
    """
    if not folder.is_dir():
        return ClaudeUsage()
    seen: set[str] = set()
    totals = {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0}
    fields = {
        "input": "input_tokens",
        "cache_write": "cache_creation_input_tokens",
        "cache_read": "cache_read_input_tokens",
        "output": "output_tokens",
    }
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
                for name, field in fields.items():
                    totals[name] += int(usage.get(field) or 0)
    return ClaudeUsage(**totals, steps=len(seen))


def short(tokens: float) -> str:
    """``1_400_000`` → ``1.4M``, ``420_000`` → ``420k``."""
    if tokens >= 1_000_000:
        return f"{tokens / 1_000_000:.1f}M"
    if tokens >= 1_000:
        return f"{tokens / 1_000:.0f}k"
    return str(round(tokens))


def claude_line(claude: ClaudeUsage) -> str:
    return (
        f"Claude spent **≈{short(claude.weighted)} token-equivalents** over {claude.steps}"
        f" steps (≈{short(claude.per_step)} a step; {claude.rereading_share:.0%} of it"
        " re-reading the conversation)."
    )


def work_summary(label: str, tasks: list[str], local: int, claude: ClaudeUsage) -> str:
    """One paragraph: what the local model built, what Claude spent, what it saved."""
    if not tasks:
        return f"**Who did the work in {label}.** No local-model tasks yet."
    text = (
        f"**Who did the work in {label}.** The local model built {len(tasks)} task(s)"
        f" ({', '.join(tasks)}) using {short(local)} tokens, free on your GPU. "
        + claude_line(claude)
        + " That includes preparing, reviewing and fixing the local model's work."
    )
    if claude.steps:
        direct = len(tasks) * STEPS_PER_TASK * claude.per_step
        text += (
            f" Doing those {len(tasks)} tasks directly would have cost Claude roughly"
            f" **{short(direct)}** (about {STEPS_PER_TASK} steps each at today's step cost),"
            f" **{direct / claude.weighted:.0%}** of what it spent. Delegating only saves"
            " allowance when preparing a task costs Claude less than that."
        )
    return text
