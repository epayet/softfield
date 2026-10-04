"""The milestone review loop (docs/workflow.md) and milestone metrics."""

import re
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from functools import partial
from pathlib import Path

import yaml

from runner import console, metrics, prompts
from runner.agents import ANY, CHECK_COMMANDS, GIT_READ_COMMANDS, JobSpec
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
    clock,
    close_session,
    now,
    open_session,
    rate_verdicts,
    record_findings,
    run_e2e,
    runner_commit,
    starting_ratings,
    wait_for_room,
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
from runner.state import State, save_state
from runner.tasks import (
    BUGS,
    STOPPED,
    TaskError,
    full_key,
    held_ids,
    load_dir,
    milestone_file,
    milestone_key,
    milestone_order,
    named_keys,
    next_milestone_key,
    short_key,
    split_frontmatter,
)
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
        for path in sorted((repo / "tasks" / folder).glob(f"{short_key(milestone)}-*.md")):
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
    following = full_key(repo, next_milestone_key(milestone))
    claude = claude_tokens(transcripts_dir(repo), started, _commit_time(repo, f"{following}-start"))
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
    "Decisions waiting for you": "decisions",
    "How the work went": "lessons",
    "What clogged the factory line": "clogged",
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


# ADR 17 item 4: `> **After:** f3-factory-line signed off`, in the header or under the title.
_AFTER_RE = re.compile(
    r"\bAfter:(?:\*\*)?\s*`?([a-z]+\d+(?:-[a-z][a-z0-9]*(?:-[a-z0-9]+)*)?)`?\s+signed off"
)
# `> **Status: done.** …`, what `runner signoff` writes (backfill reads it the same way).
_STATUS_RE = re.compile(r"^>\s*\*\*Status:\s*(.+?)\.?\*\*", re.MULTILINE)


def _header(text: str) -> str:
    """A milestone doc's header: the text above its first ``## `` section."""
    return re.split(r"^## ", text, maxsplit=1, flags=re.M)[0]


def milestone_after(text: str) -> str | None:
    """The milestone a milestone doc waits for (``After: <key> signed off``), if any. Only
    its header counts."""
    match = _AFTER_RE.search(_header(text))
    return match.group(1) if match else None


# f5 D4 (ADR 19 items 1 and 2b): `> **State:** building · **Priority:** 2 · **Area:** factory`.
CARD_STATES = ("idea", "planning", "ready", "building", "needs sign-off", "done")
DEFAULT_PRIORITY = 100
_CARD_STATE_RE = re.compile(r"\*\*State:\*\*[ \t]*([^·*\n]+)")
_CARD_PRIORITY_RE = re.compile(r"\*\*Priority:\*\*[ \t]*(\d+)\b")
_CARD_AREA_RE = re.compile(r"\*\*Area:\*\*[ \t]*(factory|product)\b")


@dataclass(frozen=True)
class Card:
    state: str
    priority: int
    area: str


def card(key: str, text: str) -> Card:
    """A milestone doc's card, from its header. A missing (or unknown) state is derived: done
    once its doc says "Status: done", else building. A missing priority is 100; a missing area
    is the key's series: ``f`` factory, ``m`` product."""
    header = _header(text)
    state = _CARD_STATE_RE.search(header)
    priority = _CARD_PRIORITY_RE.search(header)
    area = _CARD_AREA_RE.search(header)
    named = state.group(1).strip() if state else ""
    if named not in CARD_STATES:
        status = _STATUS_RE.search(text)
        named = "done" if status and status.group(1).strip() == "done" else "building"
    return Card(
        state=named,
        priority=int(priority.group(1)) if priority else DEFAULT_PRIORITY,
        area=area.group(1) if area else ("factory" if key.startswith("f") else "product"),
    )


def signed_off(repo: Path, key: str) -> bool:
    """Whether the owner signed ``key`` off: its doc says "Status: done", or failing that a
    ``<key>-done`` tag exists (either form of the key)."""
    key = full_key(repo, key)
    doc = milestone_file(repo, "milestones", key)
    status = _STATUS_RE.search(doc.read_text(encoding="utf-8")) if doc.is_file() else None
    if status and status.group(1).strip() == "done":
        return True
    try:
        return bool(Git(repo).run("tag", "--list", f"{key}-done", f"{short_key(key)}-done").strip())
    except GitError:
        return False


def waits_for(repo: Path, milestones: Iterable[str]) -> dict[str, str]:
    """Short key -> the milestone it waits for, for each of ``milestones`` whose doc says
    ``After: <key> signed off`` and whose ``<key>`` isn't signed off yet."""
    waits = {}
    for key in set(milestones):
        doc = milestone_file(repo, "milestones", key)
        after = milestone_after(doc.read_text(encoding="utf-8")) if doc.is_file() else None
        if after and not signed_off(repo, after):
            waits[short_key(key)] = after
    return waits


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
    path = milestone_file(s.repo, "milestones", milestone)
    doc = milestone_doc(path.read_text(encoding="utf-8")) if path.is_file() else {}
    # A sheet written outside the runner (an interactive review) reaches the dashboard too
    review = milestone_file(s.repo, "reviews", milestone)
    sheet = signoff_sections(review.read_text(encoding="utf-8")) if review.is_file() else {}
    started = _commit_time(s.repo, f"{milestone}-start")
    _record(
        s,
        metrics.upsert_milestone,
        s.project_id,
        milestone,
        title=doc.get("title"),
        outcome=doc.get("outcome"),
        done_when=doc.get("done_when"),
        signoff=sheet or None,
        status="in progress",
        started=started.isoformat() if started else None,
    )


def _milestone_findings(
    conn: sqlite3.Connection, project_id: int, milestone: str
) -> list[sqlite3.Row]:
    """Every finding of the milestone so far, with the role of the job that found it."""
    return conn.execute(
        "SELECT f.key, f.severity, f.file, f.line, f.summary, j.role FROM findings f"
        " JOIN milestones m ON m.id = f.milestone_id LEFT JOIN jobs j ON j.id = f.job_id"
        " WHERE m.project_id = ? AND m.key = ? ORDER BY f.id",
        (project_id, milestone),
    ).fetchall()


def _findings_so_far(s: Session, milestone: str) -> list[sqlite3.Row]:
    if s.project_id is None:
        return []
    return _record(s, _milestone_findings, s.project_id, milestone) or []


def _checkpoint_list(s: Session, milestone: str) -> str:
    """The checkpoints' findings for the review to judge, one line each."""
    lines = []
    for row in _findings_so_far(s, milestone):
        if row["role"] != "checkpoint":
            continue
        where = row["file"] + (f":{row['line']}" if row["line"] else "") if row["file"] else ""
        about = ", ".join(part for part in (row["severity"], where) if part)
        lines.append(f"- {row['key']} ({about}): {row['summary']}")
    return "\n".join(lines) or "none"


def _record_judging(s: Session, milestone: str, round_: ReviewRound) -> None:
    """A round's verdicts on the findings it names, and its score on the milestone; a key
    with no finding is left out. A later round's replace an earlier one's."""
    if s.project_id is None:
        return
    known = {row["key"] for row in _findings_so_far(s, milestone)}
    milestone_id = _record(
        s, metrics.upsert_milestone, s.project_id, milestone, review_score=round_.score
    )
    if milestone_id is None:
        return
    for key, verdict in round_.checkpoint_verdicts.items():
        if key in known:
            _record(s, metrics.add_finding, milestone_id, key, verdict=verdict)


def _rate_verdicts(s: Session, milestone: str) -> None:
    """The final review's verdicts, as they stand when its loop stops, move the reviewers'
    and authors' ratings (ADR 15 item 9); a missed finding is the checkpoint's."""
    if s.project_id is None:
        return
    checkpoint = next(iter(s.cfg.roles.get("checkpoint", ())), None)
    start = starting_ratings(s.cfg)
    _record(s, rate_verdicts, s.project_id, milestone, start, checkpoint, now())


def _record_review(s: Session, milestone: str, rounds: int) -> None:
    if s.project_id is None:
        return
    review = milestone_file(s.repo, "reviews", milestone)
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
WAITS = "waits for "


def run_milestone(cfg: Config, milestone: str, base: str) -> str:
    """ADR 12 item 12: the queue, then the review loop with its fix tickets. Returns the
    review's stop reason, or RESTART when an escalation changed the runner."""
    s = open_session(cfg, f"milestone {milestone}")
    # The review diffs from `<key>-start`: the first run tags the plan's commit if the plan
    # session didn't (f2 review); a rerun keeps it.
    if base == f"{milestone}-start" and not s.git.run("tag", "--list", base).strip():
        s.git.run("tag", base)
    _record_milestone_doc(s, milestone)
    restart = work_queue(s, milestone=milestone)
    close_session(s)
    if restart:
        return RESTART
    # Tickets still in ready/ after the queue ran are waiting on a stopped one: the milestone
    # isn't built, so the verdict asks the owner instead of reviewing half of it (f1-16).
    ready = [
        t
        for t in load_dir(s.tasks_dir("ready"), cfg.default_max_diff)
        if short_key(t.milestone) == short_key(milestone)
    ]
    # Waiting for another milestone's sign-off (ADR 17 item 4) is all of its tickets' reason.
    held = held_ids(ready, waits_for(s.repo, [milestone]))
    if held:
        return f"{WAITS}{next(iter(held.values()))}'s sign-off: " + ", ".join(sorted(held))
    waiting = sorted(t.id for t in ready)
    if waiting:
        return PAUSED + ", ".join(waiting)
    return review_milestone(cfg, milestone, base)


# --- the reviews `runner run` starts (f4-20) -----------------------------------------------

# A ticket in one of these isn't built yet; one set aside in later/ isn't part of the build.
_BUILDING = ("ready", *STOPPED)


def _ticket_milestones(repo: Path, folder: str) -> set[str]:
    """The short keys of the milestones with a ticket in ``tasks/<folder>``; ``bugs``, and a
    ticket that doesn't parse, are left out."""
    found = set()
    for path in (repo / "tasks" / folder).glob("*.md"):
        try:
            meta, _ = split_frontmatter(path.read_text(encoding="utf-8"))
            if meta.get("milestone") != BUGS:
                found.add(short_key(milestone_key(meta.get("milestone"))))
        except (TaskError, yaml.YAMLError, UnicodeDecodeError):
            continue
    return found


def _reviewed(repo: Path, state: State, key: str) -> bool:
    """Whether ``key`` has its review: the loop recorded its stop (a restart's carries on), or
    a report was written outside the runner, with no rounds of its own in state.json."""
    stop = state.review_stop.get(key)
    if stop is not None:
        return stop != RESTART
    return key not in state.review_counts and milestone_file(repo, "reviews", key).is_file()


def due_reviews(repo: Path, state: State) -> list[str]:
    """The milestones whose review `runner run` starts, in milestone order, by full key: every
    ticket in done/, not signed off, and no review yet."""
    names = named_keys(repo)
    building = set().union(*(_ticket_milestones(repo, folder) for folder in _BUILDING))
    due = []
    for short in sorted(_ticket_milestones(repo, "done") - building, key=milestone_order):
        key = names.get(short, short)
        if not _reviewed(repo, state, key) and not signed_off(repo, key):
            due.append(key)
    return due


def _done_tickets(repo: Path, milestone: str) -> list[str]:
    """The ids of the milestone's tickets in done/."""
    found = []
    for path in (repo / "tasks" / "done").glob("*.md"):
        try:
            meta, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        except (TaskError, yaml.YAMLError, UnicodeDecodeError):
            continue
        if short_key(milestone_key(meta.get("milestone"))) == short_key(milestone):
            found.append(path.stem)
    return found


def _plan_commit(git: Git, repo: Path, milestone: str) -> str:
    """Where the milestone's work starts: the parent of its first ticket's merge (a `Task:`
    trailer), else the commit that added its doc, else HEAD (where `run_milestone` tags). A
    replanned milestone's doc can be far older than its work: F3's dated from F1, and its
    review read all of F2 and F4 (f3-F5)."""
    tickets = _done_tickets(repo, milestone)
    if tickets:
        trailer = "^Task: (" + "|".join(re.escape(t) for t in tickets) + ")$"
        merges = git.run("log", "-E", f"--grep={trailer}", "--format=%H").split()
        if merges and git.run("rev-list", "--parents", "-n", "1", merges[-1]).split()[1:]:
            return f"{merges[-1]}^"
    doc = milestone_file(repo, "milestones", milestone)
    if not doc.is_file():
        return "HEAD"
    path = doc.relative_to(repo).as_posix()
    added = git.run("log", "--follow", "--diff-filter=A", "--format=%H", "--", path).split()
    return added[-1] if added else "HEAD"


def run_due_review(cfg: Config, milestone: str) -> str:
    """A review `runner run` found due, as `run_milestone` runs it after its queue, from
    ``<key>-start``. No plan session tagged it (F3, F4): the plan's commit is tagged."""
    base = f"{milestone}-start"
    git = Git(cfg.repo)
    if not git.run("tag", "--list", base).strip():
        git.run("tag", base, _plan_commit(git, cfg.repo, milestone))
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
        job = JobSpec(
            role="review",
            prompt=prompts.REVIEW.format(
                milestone=milestone,
                round=round_no,
                max_rounds=cfg.review_rounds,
                scope=scope,
                recurring=", ".join(recurring_for_claude(seen)) or "none",
                checkpoints=_checkpoint_list(s, milestone),
                out=out.relative_to(cfg.repo).as_posix(),
            ),
            timeout=cfg.claude_timeout,
            edit=(ANY,),
            commands=(*CHECK_COMMANDS, *GIT_READ_COMMANDS),
        )
        since = s.git.head()
        wait_for_room(s, "the review")  # nothing else runs: it waits rather than parks
        if s.project_id is not None:  # under way: off the line's queue (f4-20)
            _record(s, metrics.upsert_milestone, s.project_id, milestone, status="review")
        call_claude(s, job, milestone, f"{milestone}-review-r{round_no}")
        try:
            round_ = parse_review(out)
        except ReviewFileError as exc:
            stop = f"review output unusable: {exc}"
            break
        record_findings(s, milestone, round_.findings, cfg.agent_for(job.role).id)
        _record_judging(s, milestone, round_)
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
    if stop != RESTART:  # a restarted review goes on judging
        _rate_verdicts(s, milestone)
    _write_metrics(s, milestone, base, rounds, stop)
    _record_review(s, milestone, len(rounds))
    close_session(s)
    runner_commit(s, f"runner: {milestone} review metrics")
    if s.git.current_branch() != MAIN:
        raise RunnerError("review loop ended off main")
    return stop
