"""The milestone review loop (docs/workflow.md) and milestone metrics."""

import re
from dataclasses import dataclass
from pathlib import Path

from runner import prompts
from runner.claude import CHECK_TOOLS, EDIT_TOOLS, GIT_READ_TOOLS, ClaudeJob
from runner.config import Config
from runner.gates import GateResult
from runner.gitops import with_trailers
from runner.loop import (
    CLAUDE_HEADLESS_AGENT,
    MAIN,
    RunnerError,
    Session,
    call_claude,
    close_session,
    open_session,
    run_e2e,
    run_task,
    runner_commit,
)
from runner.review import (
    ReviewFileError,
    parse_review,
    recurring_for_claude,
    stop_reason,
    update_seen,
)
from runner.state import save_state
from runner.tasks import blocked_ids, load_dir, pick_next, task_ids

_FOOTER_RE = re.compile(r"# --- runner ---\n(.*?)```", re.DOTALL)


@dataclass(frozen=True)
class MilestoneMetrics:
    done: int
    escalated: int
    attempts: list[int]

    @property
    def escalation_rate(self) -> float:
        total = self.done + self.escalated
        return self.escalated / total if total else 0.0


def footer_fields(text: str) -> dict[str, str]:
    """The last runner footer of a task file as a dict."""
    matches = _FOOTER_RE.findall(text)
    if not matches:
        return {}
    fields = {}
    for line in matches[-1].splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    return fields


def milestone_metrics(repo: Path, milestone: int) -> MilestoneMetrics:
    done = escalated = 0
    attempts: list[int] = []
    for folder in ("done", "escalated"):
        for path in sorted((repo / "tasks" / folder).glob(f"m{milestone}-*.md")):
            fields = footer_fields(path.read_text(encoding="utf-8"))
            if fields.get("attempts", "").isdigit():
                attempts.append(int(fields["attempts"]))
            if folder == "done":
                done += 1
            else:
                escalated += 1
    return MilestoneMetrics(done=done, escalated=escalated, attempts=attempts)


def _run_ready_tasks(s: Session, milestone: int) -> None:
    while True:
        ready = [t for t in load_dir(s.tasks_dir("ready"), s.cfg.default_max_diff)]
        paused = blocked_ids(ready, task_ids(s.tasks_dir("escalated")))
        task = pick_next(
            [t for t in ready if t.milestone == milestone], task_ids(s.tasks_dir("done")), paused
        )
        if task is None:
            return
        s.report.tasks.append(run_task(s, task))


def _write_metrics(s: Session, milestone: int, rounds: list[int], stop: str) -> None:
    m = milestone_metrics(s.repo, milestone)
    path = s.repo / "docs" / "reviews" / f"m{milestone}-metrics.md"
    avg = sum(m.attempts) / len(m.attempts) if m.attempts else 0
    path.write_text(
        "\n".join(
            [
                f"# Milestone {milestone}: runner metrics",
                "",
                f"- Tasks merged: {m.done}; escalated: {m.escalated}"
                f" (escalation rate {m.escalation_rate:.0%})",
                f"- Attempts per task: {m.attempts or '-'} (average {avg:.1f})",
                f"- Review rounds: {len(rounds)}; actionable findings per round: {rounds or '-'}",
                f"- Headless Claude runs used: {s.state.runs_used(milestone)}"
                f" of {s.cfg.headless_runs_per_milestone}",
                f"- Loop stopped because: {stop}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def review_milestone(cfg: Config, milestone: int, base: str) -> str:
    """Run review rounds until a stop rule fires. Returns the stop reason."""
    s = open_session(cfg)
    rounds = s.state.review_counts.setdefault(str(milestone), [])
    seen = s.state.finding_seen
    since = base
    stop = "not started"
    for round_no in range(len(rounds) + 1, cfg.review_rounds + 1):
        e2e: GateResult = run_e2e(cfg.repo, cfg.gate_timeout)
        if not e2e.ok:
            stop = "end-to-end tests fail on staging"
            (s.run_dir / "e2e.txt").write_text(e2e.output, encoding="utf-8")
            break
        out = s.run_dir / f"review-m{milestone}-r{round_no}.json"
        scope = (
            f"Review the whole milestone diff: `git diff {base}..{MAIN}`."
            if round_no == 1
            else f"Re-review only the fix diffs `git diff {since}..{MAIN}` and whether each"
            " earlier finding is resolved. New should-fix points about untouched code go to"
            " the backlog."
        )
        job = ClaudeJob(
            kind="review",
            prompt=prompts.REVIEW.format(
                milestone=milestone,
                round=round_no,
                max_rounds=cfg.review_rounds,
                scope=scope,
                recurring=", ".join(recurring_for_claude(seen)) or "none",
                out=out.relative_to(cfg.repo).as_posix(),
            ),
            allowed_tools=(*EDIT_TOOLS, *CHECK_TOOLS, *GIT_READ_TOOLS),
        )
        since = s.git.head()
        result = call_claude(s, job, milestone, f"m{milestone}-review-r{round_no}")
        if result is None:
            stop = "headless Claude cap reached"
            break
        try:
            round_ = parse_review(out)
        except ReviewFileError as exc:
            stop = f"review output unusable: {exc}"
            break
        s.git.commit_all(
            with_trailers(
                f"review m{milestone} round {round_no} (by Claude)", agent=CLAUDE_HEADLESS_AGENT
            )
        )
        seen.update(update_seen(seen, round_))
        count = sum(f.actionable for f in round_.findings)
        previous = rounds[-1] if rounds else None
        rounds.append(count)
        save_state(s.state, s.state_path)
        reason = stop_reason(round_no, round_, previous, seen, cfg.review_rounds)
        _run_ready_tasks(s, milestone)
        if reason:
            stop = reason
            break
    _write_metrics(s, milestone, rounds, stop)
    close_session(s)
    runner_commit(s, f"runner: m{milestone} review metrics")
    if s.git.current_branch() != MAIN:
        raise RunnerError("review loop ended off main")
    return stop
