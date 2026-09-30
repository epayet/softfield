"""The milestone review loop (docs/workflow.md) and milestone metrics."""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from runner import prompts
from runner.claude import CHECK_TOOLS, EDIT_TOOLS, GIT_READ_TOOLS, ClaudeJob
from runner.config import Config
from runner.gates import GateResult
from runner.gitops import Git, GitError, with_trailers
from runner.loop import (
    CLAUDE_HEADLESS_AGENT,
    MAIN,
    RunnerError,
    Session,
    call_claude,
    close_session,
    open_session,
    run_e2e,
    runner_commit,
    work_queue,
)
from runner.review import (
    ReviewFileError,
    parse_review,
    recurring_for_claude,
    stop_reason,
    update_seen,
)
from runner.state import save_state
from runner.tasks import next_milestone_key
from runner.usage import claude_tokens, transcripts_dir, work_summary

_FOOTER_RE = re.compile(r"# --- runner ---\n(.*?)```", re.DOTALL)
_TOKENS_RE = re.compile(r"^tokens: (\d+)\b", re.MULTILINE)


@dataclass(frozen=True)
class MilestoneMetrics:
    done: int
    escalated: int  # tasks escalated at least once, merged since or not
    attempts: list[int]  # per task, over every run of it
    tasks: list[str] = field(default_factory=list)  # short names of the merged tasks
    local_tokens: int = 0
    total: int = 0  # tasks in done/ and escalated/

    @property
    def escalation_rate(self) -> float:
        return self.escalated / self.total if self.total else 0.0


def all_footers(text: str) -> list[dict[str, str]]:
    """Every runner footer of a task file, oldest first (a requeued task has several)."""
    footers = []
    for match in _FOOTER_RE.findall(text):
        fields = {}
        for line in match.splitlines():
            key, sep, value = line.partition(":")
            if sep:
                fields[key.strip()] = value.strip()
        footers.append(fields)
    return footers


def footer_fields(text: str) -> dict[str, str]:
    """The last runner footer of a task file as a dict."""
    footers = all_footers(text)
    return footers[-1] if footers else {}


def footer_tokens(text: str) -> int:
    """Local-model tokens over every runner footer (a requeued task has several)."""
    return sum(int(n) for n in _TOKENS_RE.findall(text))


def milestone_metrics(repo: Path, milestone: str) -> MilestoneMetrics:
    done = escalated = tokens = total = 0
    attempts: list[int] = []
    tasks: list[str] = []
    for folder in ("done", "escalated"):
        for path in sorted((repo / "tasks" / folder).glob(f"{milestone}-*.md")):
            text = path.read_text(encoding="utf-8")
            footers = all_footers(text)
            tokens += footer_tokens(text)
            counts = [int(f["attempts"]) for f in footers if f.get("attempts", "").isdigit()]
            if counts:
                attempts.append(sum(counts))
            if folder == "escalated" or any(f.get("result") == "escalated" for f in footers):
                escalated += 1
            if folder == "done":
                done += 1
                tasks.append(re.sub(r"^[a-z]+\d+-\d+-", "", path.stem))
            total += 1
    return MilestoneMetrics(done, escalated, attempts, tasks, tokens, total)


def _commit_time(repo: Path, ref: str) -> datetime | None:
    try:
        return datetime.fromisoformat(Git(repo).run("log", "-1", "--format=%cI", ref).strip())
    except GitError:
        return None


def milestone_summary(repo: Path, milestone: str, base: str | None = None) -> str:
    """The "who did the work" paragraph: local tokens from the task footers, Claude's from
    its transcripts from the milestone's base commit (default: the ``<key>-start`` tag) to the
    next milestone's start tag, if there is one."""
    m = milestone_metrics(repo, milestone)
    ref = base or f"{milestone}-start"
    label = milestone.upper()
    started = _commit_time(repo, ref)
    if started is None:
        return f"**Who did the work in {label}.** Unknown: there's no `{ref}` yet."
    claude = claude_tokens(
        transcripts_dir(repo), started, _commit_time(repo, f"{next_milestone_key(milestone)}-start")
    )
    return work_summary(label, m.tasks, m.local_tokens, claude)


def _write_metrics(s: Session, milestone: str, base: str, rounds: list[int], stop: str) -> None:
    m = milestone_metrics(s.repo, milestone)
    path = s.repo / "docs" / "reviews" / f"{milestone}-metrics.md"
    avg = sum(m.attempts) / len(m.attempts) if m.attempts else 0
    path.write_text(
        "\n".join(
            [
                f"# Milestone {milestone.upper()}: runner metrics",
                "",
                f"- Tasks merged: {m.done}; escalated at least once: {m.escalated}"
                f" (escalation rate {m.escalation_rate:.0%})",
                f"- Attempts per task: {m.attempts or '-'} (average {avg:.1f})",
                f"- Review rounds: {len(rounds)}; actionable findings per round: {rounds or '-'}",
                f"- Headless Claude runs: {s.state.runs_used(milestone)}",
                f"- Loop stopped because: {stop}",
                "",
                milestone_summary(s.repo, milestone, base),
                "",
            ]
        ),
        encoding="utf-8",
    )


RESTART = "restart"


def run_milestone(cfg: Config, milestone: str, base: str) -> str:
    """ADR 12 item 12: the queue, then the review loop with its fix tickets. Returns the
    review's stop reason, or RESTART when an escalation changed the runner."""
    s = open_session(cfg)
    restart = work_queue(s, milestone=milestone)
    close_session(s)
    if restart:
        return RESTART
    return review_milestone(cfg, milestone, base)


def review_milestone(cfg: Config, milestone: str, base: str) -> str:
    """Run review rounds until a stop rule fires. Returns the stop reason."""
    s = open_session(cfg)
    rounds = s.state.review_counts.setdefault(milestone, [])
    seen = s.state.finding_seen
    since = base
    stop = "not started"
    for round_no in range(len(rounds) + 1, cfg.review_rounds + 1):
        e2e: GateResult = run_e2e(cfg.repo, cfg.gate_timeout)
        if not e2e.ok:
            stop = "end-to-end tests fail on staging"
            (s.run_dir / "e2e.txt").write_text(e2e.output, encoding="utf-8")
            break
        out = s.run_dir / f"review-{milestone}-r{round_no}.json"
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
        call_claude(s, job, milestone, f"{milestone}-review-r{round_no}")
        try:
            round_ = parse_review(out)
        except ReviewFileError as exc:
            stop = f"review output unusable: {exc}"
            break
        s.git.commit_all(
            with_trailers(
                f"review {milestone} round {round_no} (by Claude)", agent=CLAUDE_HEADLESS_AGENT
            )
        )
        seen.update(update_seen(seen, round_))
        count = sum(f.actionable for f in round_.findings)
        previous = rounds[-1] if rounds else None
        rounds.append(count)
        save_state(s.state, s.state_path)
        reason = stop_reason(round_no, round_, previous, seen, cfg.review_rounds)
        if work_queue(s, milestone=milestone):
            stop = RESTART
            break
        if reason:
            stop = reason
            break
    if stop == "not started":  # no rounds left: a rerun after the owner decided something
        stop = s.state.review_stop.get(milestone, "review rounds used up")
    s.state.review_stop[milestone] = stop
    save_state(s.state, s.state_path)
    _write_metrics(s, milestone, base, rounds, stop)
    close_session(s)
    runner_commit(s, f"runner: {milestone} review metrics")
    if s.git.current_branch() != MAIN:
        raise RunnerError("review loop ended off main")
    return stop
