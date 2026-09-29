"""Session reports in docs/sessions/: what happened, what it cost, what to improve."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from runner.usage import ClaudeUsage, claude_line, short


@dataclass
class TaskRecord:
    id: str
    milestone: int
    result: str = "running"  # done | escalated | blocked | preflight
    attempts: int = 0
    warmup_s: float = 0.0
    model_s: float = 0.0
    gates_s: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    steps: int = 0
    gate_failures: list[str] = field(default_factory=list)
    blocked: str | None = None
    note: str = ""
    logs: Path | None = None
    commit: str = ""  # the squash-merge sha on main, when the task merged
    # For the milestone review to read first (ADR 07 items 4 and 9):
    outside_files: list[str] = field(default_factory=list)  # changed, not in `files:`
    changed_tests: list[str] = field(default_factory=list)  # existing test files it edited


@dataclass
class ClaudeRunRecord:
    kind: str
    subject: str
    duration_s: float
    tokens_in: int
    tokens_out: int
    cache_read: int
    ok: bool


@dataclass
class SessionReport:
    started: datetime
    ended: datetime | None = None
    tasks: list[TaskRecord] = field(default_factory=list)
    claude_runs: list[ClaudeRunRecord] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    narrative: str = ""


def _minutes(seconds: float) -> str:
    return f"{seconds / 60:.1f} min" if seconds >= 60 else f"{seconds:.0f} s"


def observations(report: SessionReport) -> list[str]:
    """Deterministic, cheap observations; the narrative adds judgement on top."""
    obs: list[str] = []
    tasks = report.tasks
    if not tasks:
        return ["No tasks ran."]
    first_try = sum(t.result == "done" and t.attempts == 1 for t in tasks)
    obs.append(f"First-attempt pass rate: {first_try}/{len(tasks)}.")
    failures: dict[str, int] = {}
    for t in tasks:
        for name in t.gate_failures:
            failures[name] = failures.get(name, 0) + 1
    if failures:
        top = max(failures.items(), key=lambda kv: kv[1])
        obs.append(f"Most frequent gate failure: `{top[0]}` ({top[1]}x).")
    steps = sum(t.steps for t in tasks)
    if steps:
        per_step = sum(t.tokens_in for t in tasks) / steps
        obs.append(
            f"Average local input per model step: {per_step:,.0f} tokens"
            " (the whole conversation is re-sent each step; high values mean context bloat)."
        )
    cold = [t for t in tasks if t.warmup_s > 20]
    if cold:
        obs.append(
            f"Model was cold for {len(cold)} task(s);"
            f" JIT load cost {_minutes(sum(t.warmup_s for t in cold))}."
        )
    blocked = [t for t in tasks if t.blocked]
    if blocked:
        obs.append("BLOCKED: " + ", ".join(f"{t.id} ({t.blocked})" for t in blocked) + ".")
    for t in tasks:
        if t.outside_files:
            obs.append(f"`{t.id}` changed files outside `files:`: {', '.join(t.outside_files)}.")
        if t.changed_tests:
            obs.append(
                f"`{t.id}` edited existing tests (review these): {', '.join(t.changed_tests)}."
            )
    return obs


def render(report: SessionReport, claude: ClaudeUsage | None = None) -> str:
    ended = report.ended or report.started
    tasks = report.tasks
    done = [t for t in tasks if t.result == "done"]
    local_in = sum(t.tokens_in for t in tasks)
    local_out = sum(t.tokens_out for t in tasks)
    lines = [
        f"# Session {report.started:%Y-%m-%d %H:%M}",
        "",
        f"- **Duration:** {_minutes((ended - report.started).total_seconds())}",
        f"- **Tasks:** {len(tasks)} attempted, {len(done)} merged, "
        f"{sum(t.result != 'done' for t in tasks)} escalated or blocked",
        f"- **Headless Claude runs:** {len(report.claude_runs)}",
        "",
        "## Tasks",
        "",
        "| Task | Result | Attempts | Warm-up | Model time | Gates time | Local tokens in / out"
        " | Gate failures | Commit |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for t in tasks:
        lines.append(
            f"| `{t.id}` | {t.result} | {t.attempts} | {_minutes(t.warmup_s)} | "
            f"{_minutes(t.model_s)} | "
            f"{_minutes(t.gates_s)} | {t.tokens_in:,} / {t.tokens_out:,} | "
            f"{', '.join(t.gate_failures) or '-'} | "
            f"{f'`{t.commit[:9]}`' if t.commit else '-'} |"
        )
    lines += ["", "## Local model vs Claude", ""]
    lines.append(
        f"The local model processed **{short(local_in + local_out)} tokens**"
        f" ({local_in:,} in, {local_out:,} out) on {len(tasks)} task(s), on your own GPU."
    )
    if claude is not None:
        lines += [
            "",
            claude_line(claude) + " (This session, interactive and headless, from Claude"
            " Code's transcripts; weighted by price.)",
        ]
    if report.claude_runs:
        lines += [
            "",
            "## Headless Claude runs",
            "",
            "| Kind | Subject | Time | Input | Output | Cache read | OK |",
            "|---|---|---|---|---|---|---|",
        ]
        for r in report.claude_runs:
            lines.append(
                f"| {r.kind} | {r.subject} | {_minutes(r.duration_s)} | {r.tokens_in:,} | "
                f"{r.tokens_out:,} | {r.cache_read:,} | {'yes' if r.ok else 'no'} |"
            )
    lines += ["", "## Observations", ""]
    lines += [f"- {o}" for o in observations(report) + report.notes]
    lines += ["", "## Narrative", ""]
    lines.append(
        report.narrative
        or "_Not written by the runner. Claude adds one at calibration, reviews and escalations._"
    )
    return "\n".join(lines) + "\n"


def write(repo: Path, report: SessionReport, claude: ClaudeUsage | None = None) -> Path:
    path = repo / "docs" / "sessions" / f"{report.started:%Y-%m-%d-%H%M}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(report, claude), encoding="utf-8")
    return path
