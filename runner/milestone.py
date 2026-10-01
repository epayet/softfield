"""The milestone review loop (docs/workflow.md) and milestone metrics."""

import re
from dataclasses import dataclass, field
from datetime import datetime
from functools import partial
from pathlib import Path

from runner import console, metrics, prompts
from runner.claude import CHECK_TOOLS, EDIT_TOOLS, GIT_READ_TOOLS, ClaudeJob
from runner.config import Config
from runner.gates import GateResult
from runner.gitops import Git, GitError, with_trailers
from runner.loop import (
    CLAUDE_HEADLESS_AGENT,
    MAIN,
    RUNNER_AGENT,
    RunnerError,
    Session,
    _record,
    call_claude,
    claude_agent,
    clock,
    close_session,
    open_session,
    run_e2e,
    runner_commit,
    with_progress,
    work_queue,
)
from runner.review import (
    ReviewFileError,
    ReviewRound,
    parse_review,
    recurring_for_claude,
    stop_reason,
    update_seen,
)
from runner.state import save_state
from runner.tasks import load_dir, next_milestone_key
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


# --- the milestone's row in the metrics database (f1 D2) ----------------------------------

_TITLE_RE = re.compile(r"^# (?:Milestone \w+: )?(.+?)\s*$", re.MULTILINE)
_SUBHEADING_RE = re.compile(r"^### (?:\d+\. )?(.+?)[ \t]*\n(.*?)(?=^#{1,3} |\Z)", re.M | re.S)
# The sign-off sheet's sections (lead.md, "Sign-off sheet"; f1 D8) and their keys.
SIGNOFF_SECTIONS = {
    "What changed": "changed",
    "How to test it yourself": "how_to_test",
    "What next": "what_next",
    "Left for later": "later",
    "How the work went": "lessons",
}


def _section(text: str, name: str) -> str | None:
    match = re.search(rf"^## {re.escape(name)}[ \t]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match.group(1).strip() if match else None


def milestone_doc(text: str) -> dict[str, str]:
    """A milestone doc's title, ``Outcome`` and ``Done when``; a part it lacks is left out."""
    title = _TITLE_RE.search(text)
    parts = {
        "title": title.group(1) if title else None,
        "outcome": _section(text, "Outcome"),
        "done_when": _section(text, "Done when"),
    }
    return {key: value for key, value in parts.items() if value}


def signoff_sections(text: str) -> dict[str, str]:
    """The sign-off sheet of a review report by key; a heading missing leaves its key out."""
    found = {}
    for match in _SUBHEADING_RE.finditer(text):
        key = SIGNOFF_SECTIONS.get(match.group(1))
        if key and key not in found:
            found[key] = match.group(2).strip()
    return found


def _record_milestone_doc(s: Session, milestone: str) -> None:
    if s.project_id is None:
        return
    path = s.repo / "docs" / "milestones" / f"{milestone}.md"
    doc = milestone_doc(path.read_text(encoding="utf-8")) if path.is_file() else {}
    started = _commit_time(s.repo, f"{milestone}-start")
    _record(
        s,
        metrics.upsert_milestone,
        s.project_id,
        milestone,
        title=doc.get("title"),
        outcome=doc.get("outcome"),
        done_when=doc.get("done_when"),
        status="in progress",
        started=started.isoformat() if started else None,
    )


def _record_findings(s: Session, milestone: str, round_: ReviewRound, agent: str) -> None:
    """A review round's findings, on its review job, keyed by their ids."""
    if s.project_id is None:
        return
    milestone_id = _record(s, metrics.upsert_milestone, s.project_id, milestone)
    if milestone_id is None:
        return
    for finding in round_.findings:
        _record(
            s,
            metrics.add_finding,
            milestone_id,
            finding.id,
            job_id=s.last_job_id,
            severity=finding.severity,
            route=finding.route,
            summary=finding.summary,
            resolved=finding.resolved,
            agent=agent,
        )


def _record_review(s: Session, milestone: str, rounds: int) -> None:
    if s.project_id is None:
        return
    review = s.repo / "docs" / "reviews" / f"{milestone}.md"
    sheet = signoff_sections(review.read_text(encoding="utf-8")) if review.is_file() else {}
    _record(
        s,
        metrics.upsert_milestone,
        s.project_id,
        milestone,
        status="review",
        review_rounds=rounds,
        signoff=sheet or None,
    )


def _e2e(s: Session) -> GateResult:
    """The end-to-end run, with its start, progress and end on the console (f1-42)."""
    s.log(console.start(RUNNER_AGENT, "e2e tests"))
    started = clock()
    result: GateResult = with_progress(
        partial(run_e2e, s.repo, s.cfg.gate_timeout),
        lambda elapsed: s.log(console.running(RUNNER_AGENT, "e2e tests", elapsed)),
    )
    outcome = "passed" if result.ok else "failed"
    s.log(f"■ [{RUNNER_AGENT}] e2e tests {outcome} · {console.duration(clock() - started)}")
    return result


RESTART = "restart"
PAUSED = "tickets paused behind a blocked or escalated one: "


def run_milestone(cfg: Config, milestone: str, base: str) -> str:
    """ADR 12 item 12: the queue, then the review loop with its fix tickets. Returns the
    review's stop reason, or RESTART when an escalation changed the runner."""
    s = open_session(cfg, f"milestone {milestone}")
    _record_milestone_doc(s, milestone)
    restart = work_queue(s, milestone=milestone)
    close_session(s)
    if restart:
        return RESTART
    # Tickets still in ready/ after the queue ran are waiting on a stopped one: the milestone
    # isn't built, so the verdict asks the owner instead of reviewing half of it (f1-16).
    waiting = sorted(
        t.id
        for t in load_dir(s.tasks_dir("ready"), cfg.default_max_diff)
        if t.milestone == milestone
    )
    if waiting:
        return PAUSED + ", ".join(waiting)
    return review_milestone(cfg, milestone, base)


def review_milestone(cfg: Config, milestone: str, base: str) -> str:
    """Run review rounds until a stop rule fires. Returns the stop reason."""
    s = open_session(cfg, f"review {milestone}")
    rounds = s.state.review_counts.setdefault(milestone, [])
    seen = s.state.finding_seen
    since = base
    stop = "not started"
    for round_no in range(len(rounds) + 1, cfg.review_rounds + 1):
        s.log("")
        s.log(
            console.ticket_header(
                f"{milestone} review", f"round {round_no}/{cfg.review_rounds}", None
            )
        )
        s.log("The whole milestone diff." if round_no == 1 else "The fixes since the last round.")
        e2e = _e2e(s)
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
        _record_findings(s, milestone, round_, claude_agent(s, job))
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
    _record_review(s, milestone, len(rounds))
    close_session(s)
    runner_commit(s, f"runner: {milestone} review metrics")
    if s.git.current_branch() != MAIN:
        raise RunnerError("review loop ended off main")
    return stop
