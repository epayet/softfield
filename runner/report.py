"""Session reports in docs/sessions/: what happened, what it cost, what to improve. And
``runner report <key>``: a milestone review's numbers from the metrics database."""

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from factory_dashboard.queries import (
    MilestoneResults,
    Savings,
    connect,
    is_claude,
    milestone_results,
    savings,
    trends,
)
from runner.usage import ClaudeUsage, claude_line, short

# Where `uv run runner dashboard` serves by default (factory_dashboard.app's HOST and PORT).
DASHBOARD_URL = "http://127.0.0.1:8765"


@dataclass
class TaskRecord:
    id: str
    milestone: str
    result: str = "running"  # done | escalated | blocked | preflight
    attempts: int = 0
    warmup_s: float = 0.0
    model_s: float = 0.0
    gates_s: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    steps: int = 0
    edit_streak: int = 0  # the longest run of edits without running a command (ADR 12 item 7)
    timeouts: int = 0
    sessions: list[str] = field(default_factory=list)  # OpenCode session per attempt
    directed: bool = False
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
    restart: bool = False  # Claude changed runner/: the command carries on in a new process
    review: str | None = None  # the milestone `runner run` stopped its queue to review (f4-20)
    idle: bool = False  # an idle run ended its session to report the day: it goes on (F101 D3)


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
    streaks = [t for t in tasks if t.edit_streak >= 8]
    if streaks:
        obs.append(
            "Long runs of edits without running a command: "
            + ", ".join(f"{t.id} ({t.edit_streak})" for t in streaks)
            + "."
        )
    directed = [t.id for t in tasks if t.directed]
    if directed:
        obs.append("The lead gave direction before the last attempt: " + ", ".join(directed) + ".")
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


def _tasks_line(tasks: list[TaskRecord]) -> str:
    done = [f"`{t.id}`" for t in tasks if t.result == "done"]
    others = [f"`{t.id}`: {t.result}" for t in tasks if t.result != "done"]
    line = f"{len(tasks)} attempted: {len(done)} merged"
    line += f" ({', '.join(done)})" if done else ""
    line += f", {len(others)} not ({', '.join(others)})" if others else ""
    return line


def run_url(report: SessionReport) -> str:
    """The run's page on the dashboard. The runner names a run's folder after its start
    (``runner.loop.open_session``)."""
    return f"{DASHBOARD_URL}/runs/{report.started:%Y%m%d-%H%M%S}"


def render(report: SessionReport, claude: ClaudeUsage | None = None) -> str:
    """A summary; every task, job and gate is on the run's dashboard page (f1-06)."""
    ended = report.ended or report.started
    tasks = report.tasks
    local_in = sum(t.tokens_in for t in tasks)
    local_out = sum(t.tokens_out for t in tasks)
    lines = [
        f"# Session {report.started:%Y-%m-%d %H:%M}",
        "",
        f"- **Duration:** {_minutes((ended - report.started).total_seconds())}",
        f"- **Tasks:** {_tasks_line(tasks)}",
        f"- **Headless Claude runs:** {len(report.claude_runs)}",
        f"- **Details:** every task, job and gate at {run_url(report)} (`uv run runner dashboard`)",
    ]
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


# --- `runner report <key>` (f1-05, ADR 14 item 16) -----------------------------------------

REPORT_START, REPORT_END = "<!-- runner report -->", "<!-- /runner report -->"


class ReportError(Exception):
    pass


def _usd(dollars: float) -> str:
    return f"-${-dollars:,.2f}" if dollars < -0.005 else f"${abs(dollars):,.2f}"


def _pass_rate(first: int, tried: int) -> str:
    return f"{first}/{tried} ({first / tried:.0%})" if tried else "-"


def _savings_row(label: str, s: Savings) -> str:
    return (
        f"| {label} | {s.tickets} | {s.lines:,} | {_usd(s.doing_itself)} | {_usd(s.supporting)}"
        f" | **{_usd(s.net)}** |"
    )


def _results_lines(r: MilestoneResults) -> list[str]:
    findings = ", ".join(f"{n} {severity}" for severity, n in r.findings.items()) or "none"
    return [
        f"| Result | {r.key.upper()} |",
        "|---|---|",
        f"| Tickets merged | {r.merged} of {r.tickets} |",
        f"| First-attempt pass rate | {_pass_rate(r.first_attempt, r.developer_tickets)} |",
        f"| Local attempts | {r.attempts} |",
        f"| Escalations, directions, checkpoints | {r.escalations}, {r.directions},"
        f" {r.checkpoints} |",
        f"| Review rounds | {r.review_rounds} |",
        f"| Findings | {findings} |",
        f"| Local model | {short(r.local.tokens)} tokens ({r.local.tokens_in:,} in,"
        f" {r.local.tokens_out:,} out) |",
        f"| Claude | {_usd(r.claude.dollars)} ({short(r.claude.token_equivalents)}"
        " token-equivalents) |",
    ]


def milestone_report(conn: sqlite3.Connection, project: str, key: str) -> str:
    """The numbers section of ``docs/reviews/<key>.md``, between its markers."""
    r = milestone_results(conn, project, key)
    if r is None:
        raise ReportError(f"no milestone {key} in the metrics database")
    s = savings(conn, project, key)
    lines = [
        REPORT_START,
        "## Numbers",
        "",
        f"_Written by `uv run runner report {key}` from the metrics database, which isn't in"
        " git: a snapshot. Run it again to refresh; edit outside these markers._",
        "",
        *_results_lines(r),
        "",
        "### Savings from delegating",
        "",
        "What Claude would have spent writing the lines the developers merged, against what it"
        " spent supporting them: tickets, directions, escalations, and a share of the reviews and"
        " checkpoints (f1 D7). API-equivalent dollars.",
        "",
        "| Developer | Tickets | Lines | Doing it itself | Supporting | Net |",
        "|---|---|---|---|---|---|",
        _savings_row("**All**", s),
        *(_savings_row(a.agent or "?", a) for a in s.agents),
        "",
        f"Tokens underneath: doing it itself ≈{short(s.doing_itself_tokens)} token-equivalents,"
        f" supporting ≈{short(s.supporting_tokens)}.",
        "",
        "### By agent",
        "",
        "| Agent | Jobs | Tokens (Claude: token-equivalents) | Dollars |",
        "|---|---|---|---|",
    ]
    for a in r.agents:
        tokens = a.token_equivalents if is_claude(a.agent) else a.tokens
        lines.append(f"| {a.agent} | {a.jobs} | {short(tokens)} | {_usd(a.dollars)} |")
    lines += [
        "",
        "### Trends",
        "",
        "| Milestone | Merged | First-attempt | Attempts | Claude | Net savings |",
        "|---|---|---|---|---|---|",
    ]
    points = trends(conn, project)
    for p in points:
        t = p.results
        lines.append(
            f"| {t.key} | {t.merged} | {_pass_rate(t.first_attempt, t.developer_tickets)}"
            f" | {t.attempts} | {_usd(t.claude.dollars)} | {_usd(p.savings.net)} |"
        )
    every = [p.results for p in points]
    first = sum(t.first_attempt for t in every)
    tried = sum(t.developer_tickets for t in every)
    lines.append(
        f"| **All** | {sum(t.merged for t in every)} | {_pass_rate(first, tried)}"
        f" | {sum(t.attempts for t in every)} | {_usd(sum(t.claude.dollars for t in every))}"
        f" | {_usd(savings(conn, project).net)} |"
    )
    return "\n".join([*lines, REPORT_END]) + "\n"


def with_report(text: str, block: str) -> str:
    """``text`` with ``block`` in place of what's between the markers, or at the end."""
    start = text.find(REPORT_START)
    end = text.find(REPORT_END, start) if start >= 0 else -1
    if end >= 0:
        after = text[end + len(REPORT_END) :]
        return text[:start] + block + after.removeprefix("\n")
    if not text or text.endswith("\n\n"):
        return text + block
    return text + ("\n" if text.endswith("\n") else "\n\n") + block


def write_milestone_report(repo: Path, db: Path, key: str) -> Path:
    """Write ``runner report <key>`` into ``docs/reviews/<key>.md``; returns the file."""
    if not db.is_file():
        raise ReportError(f"no metrics database at {db}; `uv run runner backfill` makes one")
    conn = connect(db)
    try:
        block = milestone_report(conn, repo.name, key)
    finally:
        conn.close()
    path = repo / "docs" / "reviews" / f"{key}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    path.write_text(with_report(text, block), encoding="utf-8")
    return path
