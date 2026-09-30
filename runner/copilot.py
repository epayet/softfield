"""GitHub Copilot's CLI, read-only (ADR 14).

Every command this module builds denies Copilot's shell, write and URL tools and its
built-in GitHub MCP server. Deny rules take precedence over any allow in the CLI, so a
review can read the repo and nothing else. f1-22 builds the Copilot adapter on
``review_command``; until then, ``runner copilot-review`` and ``runner github-get`` are
the only way a headless job reaches Copilot or GitHub's API (f1's probes).
"""

import json
import re
import subprocess
from datetime import date
from pathlib import Path

DENIED_TOOLS = ("shell", "write", "url")
PROBE_REVIEWS_PER_DAY = 3  # Copilot Free has 50 requests a month
_MODEL_RE = re.compile(r"\w[\w.:-]*")  # never a leading dash: it would read as a flag
_API_PATH_RE = re.compile(r"/[\w{}.-]+(/[\w{}.-]+)*")


class CopilotError(ValueError):
    pass


def review_command(prompt: str, model: str | None) -> list[str]:
    if model is not None and not _MODEL_RE.fullmatch(model):
        raise CopilotError(f"not a model name: {model!r}")
    return [
        "copilot",
        f"--prompt={prompt}",  # bound to its flag, so a prompt like "--yolo" stays text
        "--silent",
        *(("--model", model) if model else ()),
        *(arg for tool in DENIED_TOOLS for arg in ("--deny-tool", tool)),
        "--disable-builtin-mcps",
        "--disallow-temp-dir",
    ]


def github_get_command(path: str) -> list[str]:
    """A GET on GitHub's API: a plain path, no flags, no query string."""
    if not _API_PATH_RE.fullmatch(path) or ".." in path:
        raise CopilotError(f"not a plain API path: {path!r}")
    return ["gh", "api", "--method", "GET", path]


def probe_review(repo: Path, prompt: str, model: str | None, today: date) -> str:
    """One read-only review, counted against a daily cap kept in var/."""
    cmd = review_command(prompt, model)
    counts_path = repo / "var" / "copilot-probe-reviews.json"
    try:
        counts = json.loads(counts_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        counts = {}
    used = int(counts.get(today.isoformat(), 0))
    if used >= PROBE_REVIEWS_PER_DAY:
        raise CopilotError(f"daily cap of {PROBE_REVIEWS_PER_DAY} Copilot reviews reached")
    counts_path.parent.mkdir(parents=True, exist_ok=True)
    counts_path.write_text(json.dumps({today.isoformat(): used + 1}), encoding="utf-8")
    proc = subprocess.run(
        cmd, cwd=repo, capture_output=True, text=True, check=False, stdin=subprocess.DEVNULL
    )
    return proc.stdout + (
        f"\n--- stderr (exit {proc.returncode}) ---\n{proc.stderr}" if proc.returncode else ""
    )
