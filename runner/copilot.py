"""GitHub Copilot's CLI, read-only (ADR 14): the ``copilot`` harness's adapter.

Every command this module builds denies Copilot's shell, write and URL tools and its
built-in GitHub MCP server. Deny rules take precedence over any allow in the CLI, so a
review can read the repo and nothing else, whatever its job spec says; a spec asking for
edits is refused before it runs. ``runner copilot-review`` and ``runner github-get`` are
f1's probes; the adapter reads the month's quota after each job through the same GET.
"""

import json
import re
import subprocess
import time
from datetime import UTC, date, datetime
from pathlib import Path

from runner.agents import Agent, JobResult, JobSpec, Reading, Refusal
from runner.claude import usage_limit_reset
from runner.local_model import TRANSIENT_RE

DENIED_TOOLS = ("shell", "write", "url")
PROBE_REVIEWS_PER_DAY = 3  # f1's probe; Copilot Free has 200 credits a month (f1-18)
# Without --no-custom-instructions Copilot loads AGENTS.md; nobody answers a question.
QUIET_FLAGS = ("--no-custom-instructions", "--no-ask-user", "--no-auto-update")
QUOTA_PATH = "/copilot_internal/user"  # undocumented, answers on Free, may lag (f1-18)
_MODEL_RE = re.compile(r"\w[\w.:-]*")  # never a leading dash: it would read as a flag
_API_PATH_RE = re.compile(r"/[\w{}.-]+(/[\w{}.-]+)*")
# A refused model name fails at once, like a missing one: a config failure, not a limit.
_NOT_AVAILABLE_RE = re.compile(r"from --model flag is not available")


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
        *QUIET_FLAGS,
    ]


def github_get_command(path: str) -> list[str]:
    """A GET on GitHub's API: a plain path, no flags, no query string."""
    if not _API_PATH_RE.fullmatch(path) or ".." in path:
        raise CopilotError(f"not a plain API path: {path!r}")
    return ["gh", "api", "--method", "GET", path]


def probe_review(repo: Path, prompt: str, model: str | None, today: date) -> str:
    """One read-only review, counted against a daily cap kept in .softfield/var/."""
    cmd = review_command(prompt, model)
    counts_path = repo / ".softfield" / "var" / "copilot-probe-reviews.json"
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


def quota_reading(repo: Path) -> Reading | None:
    """The month's chat credits used, from ``/copilot_internal/user``; None if it doesn't
    answer as probed. Its ``percent_remaining`` is of the month's entitlement."""
    cmd = github_get_command(QUOTA_PATH)
    try:
        proc = subprocess.run(
            cmd, cwd=repo, capture_output=True, text=True, timeout=30, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode:
        return None
    try:
        data = json.loads(proc.stdout)
        remaining = data["quota_snapshots"]["chat"]["percent_remaining"]
        reset_day = date.fromisoformat(data["quota_reset_date"])
        resets_at = datetime(reset_day.year, reset_day.month, reset_day.day, tzinfo=UTC)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None
    if not isinstance(remaining, int | float) or isinstance(remaining, bool):
        return None
    return Reading("month", 1 - float(remaining) / 100, resets_at)


def classify(text: str, now: datetime) -> tuple[Refusal | None, bool]:
    """A failed run's class (ADR 15 item 12): (a refusal, or None; whether it's transient).

    An unavailable model is a failure. No Copilot refusal has been seen (f1-18), so an error
    that names a limit is one, a passing one is transient, and any other is a possible limit
    with no reset, which the allowance cools down rather than counting as a failed attempt.
    """
    if _NOT_AVAILABLE_RE.search(text):
        return None, False
    limited, resets_at = usage_limit_reset(text, now)
    if limited:
        return Refusal(None, resets_at), False
    if TRANSIENT_RE.search(text):
        return None, True
    return Refusal(None, None, certain=False), False


class CopilotAdapter:
    """A read-only `JobSpec` as one ``copilot --prompt`` on the agent's model. Its
    commands aren't granted (the shell is always denied); one prompt is one request."""

    def run(
        self, agent: Agent, spec: JobSpec, repo: Path, log_path: Path, now: datetime
    ) -> JobResult:
        if not spec.read_only:
            raise CopilotError(f"Copilot jobs are read-only; {spec.role} asks to edit")
        cmd = review_command(spec.whole_prompt, agent.model)
        started = time.monotonic()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            proc = subprocess.run(
                cmd,
                cwd=repo,
                capture_output=True,
                text=True,
                timeout=spec.timeout,
                check=False,
                stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired:
            proc = None
        duration = time.monotonic() - started
        reading = quota_reading(repo)
        readings = (reading,) if reading else ()
        model = agent.model  # `--silent` output never names the model (f2-04)
        if proc is None:
            log_path.write_text("--- timed out ---\n", encoding="utf-8")
            return JobResult(
                False, "timed out", duration, timed_out=True, readings=readings, model=model
            )
        log_path.write_text(proc.stdout + "\n--- stderr ---\n" + proc.stderr, encoding="utf-8")
        if proc.returncode == 0:
            text = proc.stdout.strip()
            return JobResult(
                True, text, duration, requests=1.0, num_turns=1, readings=readings, model=model
            )
        error = (proc.stderr.strip() or proc.stdout.strip())[:500]
        refusal, transient = classify(proc.stderr + proc.stdout, now)
        return JobResult(
            ok=False,
            text=error,
            duration_s=duration,
            refusal=refusal,
            transient=transient,
            readings=readings,
            model=model,
        )


ADAPTER = CopilotAdapter()
