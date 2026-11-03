"""The milestone review loop (docs/workflow.md) and milestone metrics."""

import re
import sqlite3
import textwrap
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from functools import partial
from pathlib import Path

import yaml

from runner import console, look, metrics, prompts
from runner.agents import ANY, CHECK_COMMANDS, GIT_READ_COMMANDS, JobSpec
from runner.config import Config, project_checks
from runner.gates import GateResult
from runner.gitops import Git, GitError, parse_trailers, with_trailers
from runner.loop import (
    CHECK_TICKETS,
    CLAUDE_HEADLESS_AGENT,
    MAIN,
    NO_E2E,
    REVIEW,
    RUNNER_AGENT,
    RunnerError,
    Session,
    _record,
    call_claude,
    clock,
    close_session,
    enqueue,
    finish_row,
    now,
    open_session,
    park_review,
    rate_verdicts,
    record_findings,
    review_reason,
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
        for path in sorted(
            (repo / ".softfield" / "tasks" / folder).glob(f"{short_key(milestone)}-*.md")
        ):
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
    path = s.repo / ".softfield" / "reviews" / f"{milestone}-metrics.md"
    path.parent.mkdir(parents=True, exist_ok=True)  # a new project's first review
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
# The same sheet as a numbered list, `1. **What changed**`, with a colon or words after the
# title: F26's and F12's reviews wrote it so, as lead.md lays it out, and nothing was stored.
_LIST_ITEM_RE = re.compile(
    r"^\d+\. \*\*(.+?):?\*\*:?[ \t]*(.*?)(?=^\d+\. \*\*|^#{1,3} |\Z)", re.M | re.S
)
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
# F172 D1, D10: the fast lane's mark; the old ``**Reserve:**`` counts as the same
CARD_RESERVE_RE = re.compile(r"\*\*(?:Fast lane|Reserve):\*\*[ \t]*([^·*\n]*)")


@dataclass(frozen=True)
class Card:
    state: str
    priority: int
    area: str
    reserve: bool = False  # the owner's fast lane (ADR 34, ADR 35): may use Claude's reserve


def card(key: str, text: str) -> Card:
    """A milestone doc's card, from its header. A missing (or unknown) state is derived: done
    once its doc says "Status: done", else building. A missing priority is 100; a missing area
    is the key's series: ``f`` factory, ``m`` product. It may use the reserve only when it
    says ``**Fast lane:** yes`` (or the old ``**Reserve:** yes``)."""
    header = _header(text)
    state = _CARD_STATE_RE.search(header)
    priority = _CARD_PRIORITY_RE.search(header)
    area = _CARD_AREA_RE.search(header)
    reserve = CARD_RESERVE_RE.search(header)
    named = state.group(1).strip() if state else ""
    if named not in CARD_STATES:
        status = _STATUS_RE.search(text)
        named = "done" if status and status.group(1).strip() == "done" else "building"
    return Card(
        state=named,
        priority=int(priority.group(1)) if priority else DEFAULT_PRIORITY,
        area=area.group(1) if area else ("factory" if key.startswith("f") else "product"),
        reserve=reserve is not None and reserve.group(1).strip() == "yes",
    )


def signed_off(repo: Path, key: str) -> bool:
    """Whether the owner signed ``key`` off: its doc says "Status: done", or failing that a
    ``<key>-done`` tag exists (either form of the key)."""
    key = full_key(repo, key)
    doc = milestone_file(repo, "cards", key)
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
        doc = milestone_file(repo, "cards", key)
        after = milestone_after(doc.read_text(encoding="utf-8")) if doc.is_file() else None
        if after and not signed_off(repo, after):
            waits[short_key(key)] = after
    return waits


def signoff_sections(text: str) -> dict[str, str]:
    """The sign-off sheet of a review report by key; a heading missing leaves its key out.
    Its sections are `### 1. What changed` headings, or, in a report with none of them, the
    items of a numbered list, `1. **What changed**`."""
    found = {}
    for match in _SUBHEADING_RE.finditer(text):
        key = SIGNOFF_SECTIONS.get(match.group(1))
        if key and key not in found:
            found[key] = match.group(2).strip()
    if found:
        return found
    for match in _LIST_ITEM_RE.finditer(text):  # no heading at all: the list form
        key = SIGNOFF_SECTIONS.get(match.group(1))
        if key and key not in found:
            found[key] = textwrap.dedent(_first_line_in(match.group(2))).strip()
    return found


def _first_line_in(body: str) -> str:
    """A list item's body with the words after its title indented like the lines under it,
    so one dedent brings both to the margin."""
    first, sep, rest = body.partition("\n")
    indent = re.match(r"[ \t]*", rest)
    return f"{indent[0] if indent and rest.strip() else ''}{first}{sep}{rest}"


def _record_milestone_doc(s: Session, milestone: str) -> None:
    if s.project_id is None:
        return
    path = milestone_file(s.repo, "cards", milestone)
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
    if result.output == NO_E2E:
        outcome = f"skipped ({NO_E2E})"
    s.log(f"■ [{RUNNER_AGENT}] e2e tests {outcome} · {console.duration(clock() - started)}")
    return result


RESTART = "restart"
E2E_STOP = "end-to-end tests fail on staging"
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
    """The short keys of the milestones with a ticket in ``.softfield/tasks/<folder>``; ``bugs``,
    and
    a
    ticket that doesn't parse, are left out."""
    found = set()
    for path in (repo / ".softfield" / "tasks" / folder).glob("*.md"):
        try:
            meta, _ = split_frontmatter(path.read_text(encoding="utf-8"))
            if meta.get("milestone") != BUGS:
                found.add(short_key(milestone_key(meta.get("milestone"))))
        except (TaskError, yaml.YAMLError, UnicodeDecodeError):
            continue
    return found


def _reviewed(repo: Path, state: State, key: str) -> bool:
    """Whether ``key`` has its review: the loop recorded its stop (a restart's carries on), or
    a report was written outside the runner, with no rounds of its own in state.json. An
    end-to-end stop in a project that names no end-to-end tests is stale: F28's and F19's
    came from the `tests/e2e` the split removed (F135 D2)."""
    stop = state.review_stop.get(key)
    if stop == E2E_STOP:
        return bool(project_checks(repo).e2e)
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
    for path in (repo / ".softfield" / "tasks" / "done").glob("*.md"):
        try:
            meta, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        except (TaskError, yaml.YAMLError, UnicodeDecodeError):
            continue
        if short_key(milestone_key(meta.get("milestone"))) == short_key(milestone):
            found.append(path.stem)
    return found


_TICKET_ID = re.compile(r"\b(?:f\d+|bug|m\d+)-\d+\b")
_REVIEW_SUBJECT = re.compile(r"review \S+ round \d+ \(by Claude\)")


def _short_id(ticket: str) -> str:
    """``f104-01`` for ``f104-01-mockups``: how a commit subject names a ticket."""
    found = re.match(r"[a-z]+\d*-\d+", ticket)
    return found[0] if found else ticket


def _named_in(subject: str, tickets: list[str]) -> list[str]:
    """The tickets a commit subject names, by id or short id."""
    return [t for t in tickets if re.search(rf"(?<![\w-]){re.escape(_short_id(t))}(?!\d)", subject)]


def _is_runner_commit(subject: str) -> bool:
    return subject.startswith("runner:") or bool(_REVIEW_SUBJECT.fullmatch(subject))


def _commits(git: Git, spec: str, *extra: str) -> list[tuple[str, str, str]]:
    """``(sha, subject, body)`` of the commits in ``spec``, oldest first."""
    log = git.run("log", "--reverse", "--format=%H%x1f%s%x1f%b%x1e", *extra, spec)
    out = []
    for entry in log.split("\x1e"):
        sha, _, rest = entry.strip().partition("\x1f")
        subject, _, body = rest.partition("\x1f")
        if sha:
            out.append((sha, subject, body))
    return out


def _plan_commit(git: Git, repo: Path, milestone: str) -> str:
    """Where the milestone's work starts: the parent of its first ticket's merge (a `Task:`
    trailer), else of the first commit whose subject names one of its tickets (built in a
    terminal session, bug-01), else the commit that added its doc, else HEAD (where
    `run_milestone` tags). A replanned milestone's doc can be far older than its work: F3's
    dated from F1, and its review read all of F2 and F4 (f3-F5)."""
    tickets = _done_tickets(repo, milestone)
    if tickets:
        trailer = "^Task: (" + "|".join(re.escape(t) for t in tickets) + ")$"
        merges = git.run("log", "-E", f"--grep={trailer}", "--format=%H").split()
        if merges and git.run("rev-list", "--parents", "-n", "1", merges[-1]).split()[1:]:
            return f"{merges[-1]}^"
        for sha, subject, _ in _commits(git, "HEAD"):
            if not _is_runner_commit(subject) and _named_in(subject, tickets):
                if git.run("rev-list", "--parents", "-n", "1", sha).split()[1:]:
                    return f"{sha}^"
                break
    doc = milestone_file(repo, "cards", milestone)
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
    return review_milestone(cfg, milestone, base, park=True)


def _last_round(git: Git, milestone: str, rounds: int, base: str) -> str:
    """Where a review that goes on (parked, restarted) left off: the commit before its last
    round's, as a round under way keeps it; ``base`` with no round yet or no such commit."""
    if not rounds:
        return base
    subject = f"review {milestone} round {rounds} (by Claude)"
    found = git.run("log", "-1", "-F", f"--grep={subject}", "--format=%H", MAIN).strip()
    return f"{found}^" if found else base


def _fix_scope(s: Session, milestone: str, since: str) -> str:
    """What a later round re-reads: the fix diffs since the last round. When another
    milestone's ticket merged meanwhile (a review parked between rounds, F53 D1), its own
    milestone's merges by name instead, so it doesn't read the others' as its fixes."""
    log = s.git.run("log", "--reverse", "--format=%H%x1f%B%x1e", f"{since}..{MAIN}")
    merges = []
    for entry in log.split("\x1e"):
        sha, _, body = entry.strip().partition("\x1f")
        if ticket := parse_trailers(body).get("Task"):
            merges.append((ticket, sha))
    mine = set(_done_tickets(s.repo, milestone))
    own = [(ticket, sha) for ticket, sha in merges if ticket in mine]
    if len(own) == len(merges):
        return (
            f"Re-review only the fix diffs `git diff {since}..{MAIN}` and whether each"
            " earlier finding is resolved. New should-fix points about untouched code take the"
            " route `later` or `report`."
        )
    listed = "\n".join(f"- {ticket}: `git show {sha[:9]}`" for ticket, sha in own)
    return (
        "Re-review only this milestone's fix merges since the last round and whether each"
        " earlier finding is resolved. Other milestones' tickets merged meanwhile: leave them"
        " out. New should-fix points about untouched code take the route `later` or `report`."
        " The fix merges:\n" + (listed or "none")
    )


def _first_scope(s: Session, milestone: str, base: str) -> str:
    """What round 1 reads: the whole diff from ``base``, or, when commits of other work sit in
    the range (another milestone's merge, a terminal session's commit), this milestone's own
    commits one by one. The runner's own commits count for neither."""
    mine = _done_tickets(s.repo, milestone)
    own = []
    others = False
    for sha, subject, body in _commits(s.git, f"{base}..{MAIN}"):
        if _is_runner_commit(subject):
            continue
        task = parse_trailers(body).get("Task")
        named = _named_in(subject, mine)
        tickets = [task] if task in mine else named
        if not tickets:
            others = True
            continue
        mixed = any(t not in {_short_id(m) for m in mine} for t in _TICKET_ID.findall(subject))
        own.append((sha, tickets, mixed))
    if not others:
        return f"Review the whole milestone diff: `git diff {base}..{MAIN}`."
    lines = []
    for sha, tickets, mixed in own:
        line = f"- {', '.join(tickets)}: `git show {sha[:9]}`"
        if mixed:
            line += (
                f" (holds other tickets' work too: only {', '.join(tickets)} is this milestone's)"
            )
        lines.append(line)
    found = "\n".join(lines) or (
        "none by ticket id. A terminal session may have named the card instead: find them with"
        f" `git log -i --grep={milestone.split('-')[0]}`, review those, and say so in the report."
    )
    return (
        "Review this milestone's own commits: other work was committed in the same range, so"
        " the range's diff is not the milestone's. Read only these, and leave the other commits"
        " out. The milestone's commits:\n" + found
    )


PARKED = "parked"  # no stop: the review waits in the queue for Claude (F53 D1)


def review_milestone(cfg: Config, milestone: str, base: str, *, park: bool = False) -> str:
    """Run review rounds until a stop rule fires. Returns the stop reason. The review is a
    queued job (ADR 22 item 1): `runner run` queued it, else it is queued here, and its row
    is done with its last round's job once the loop stops (a restart's carries on).

    Claude's room is checked before each round, e2e run included. With ``park`` (`runner
    run`), a round Claude can't take now parks the review's row and returns PARKED: no stop
    is recorded, and it goes on from that round once the queue picks it again (F53 D1).
    Without, there is no queue to go back to: it waits for the reset."""
    s = open_session(cfg, f"review {milestone}")
    s.running_row = row = enqueue(s, REVIEW, milestone, review_reason(milestone))
    rounds = s.state.review_counts.setdefault(milestone, [])
    seen = s.state.finding_seen
    since = _last_round(s.git, milestone, len(rounds), base)
    stop = "not started"
    for round_no in range(len(rounds) + 1, cfg.review_rounds + 1):
        if park and park_review(s, milestone):
            s.running_row = None
            close_session(s)
            return PARKED
        if not park:
            wait_for_room(s, "the review")
        s.log("")
        s.log(
            console.ticket_header(
                f"{milestone} review", f"round {round_no}/{cfg.review_rounds}", None
            )
        )
        s.log("The whole milestone diff." if round_no == 1 else "The fixes since the last round.")
        e2e = _e2e(s)
        if not e2e.ok:
            stop = E2E_STOP
            (s.run_dir / "e2e.txt").write_text(e2e.output, encoding="utf-8")
            break
        out = s.run_dir / f"review-{milestone}-r{round_no}.json"
        scope = (
            _first_scope(s, milestone, base) if round_no == 1 else _fix_scope(s, milestone, since)
        )
        job = JobSpec(
            role="review",
            prompt=prompts.REVIEW.format(
                milestone=milestone,
                round=round_no,
                max_rounds=cfg.review_rounds,
                scope=scope,
                tests=" ".join(project_checks(s.repo).test_dirs),  # the project's own (ADR 30)
                recurring=", ".join(recurring_for_claude(seen)) or "none",
                checkpoints=_checkpoint_list(s, milestone),
                out=out.relative_to(cfg.repo).as_posix(),
            ),
            timeout=cfg.review_timeout,
            edit=(ANY,),
            # ADR 28: its times and counts from the database, read-only
            commands=(*CHECK_COMMANDS, *GIT_READ_COMMANDS, look.COMMAND, CHECK_TICKETS),
        )
        since = s.git.head()
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
    s.running_row = None
    if stop != RESTART:  # a restarted review goes on judging
        _rate_verdicts(s, milestone)
        finish_row(s, row)
    _write_metrics(s, milestone, base, rounds, stop)
    _record_review(s, milestone, len(rounds))
    close_session(s)
    runner_commit(s, f"runner: {milestone} review metrics")
    if s.git.current_branch() != MAIN:
        raise RunnerError("review loop ended off main")
    return stop
