"""``runner backfill``: past milestones into the metrics database from what's left of their
logs (f1-04; ADR 13 item 1, f1 D2 and D6).

It reads ``var/runs/<run>/`` (OpenCode logs, gates files, ``claude-*.log``, ``review-*.json``,
``state.json``), the task files and their footers, ``docs/milestones/`` and ``docs/reviews/``,
and git's ``Agent:``/``Task:`` trailers. Every write goes through ``runner.metrics``, so a
second run updates the same rows. A run the runner recorded itself is left alone. Whatever
is missing or unreadable is listed as a gap, never raised.
"""

import json
import re
import sqlite3
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from runner import metrics
from runner.gates import parse_blocked
from runner.gitops import LOCAL_MODEL_AGENT, Git, GitError, parse_trailers
from runner.local_model import parse_events, stream_facts
from runner.loop import CLAUDE_HEADLESS_AGENT, TICKET_FOLDERS
from runner.milestone import _commit_time, all_footers, milestone_doc, signoff_sections
from runner.review import ReviewFileError, parse_review
from runner.state import load_state
from runner.tasks import (
    difficulty,
    milestone_key,
    milestone_order,
    parse_sections,
    split_frontmatter,
)

BACKFILL = "backfill"  # the command of a run backfilled: its real one isn't in the logs
UNKNOWN = "backfill-unknown"  # D6: a role or agent the logs don't say
ROLES = frozenset(
    {
        "developer",
        "last-attempt",
        "direction",
        "checkpoint",
        "checkpoint-shadow",
        "escalation",
        "lead-ticket",
        "review",
        "narrative",
        "bench",
    }
)
TICKET_KINDS = ("lead-ticket", "escalation", "direction")  # Claude jobs about one ticket
CLAUDE_OPUS, CLAUDE_SONNET = "claude-opus", "claude-sonnet"  # D6

_KEY_RE = re.compile(r"[a-z]+\d+")
_TICKET_RE = re.compile(r"^([a-z]+\d+)-\d+-")
_RUN_DIR_RE = re.compile(r"^\d{8}-\d{6}$")
_TASK_DIR_RE = re.compile(r"^(.+?)(?:-run(\d+))?$")
_OPENCODE_RE = re.compile(r"^opencode-(\d+)\.jsonl$")
_REVIEW_JSON_RE = re.compile(r"^review-([a-z]+\d+)-r(\d+)\.json$")
_ROUND_RE = re.compile(r"-r(\d+)$")
_CLAUDE_LOG_RE = re.compile(
    r"^claude-(?P<kind>lead-ticket|[a-z]+)-(?P<subject>.+?)"
    r"(?:-(?P<number>\d+))?(?:-retry(?P<retry>\d+))?\.log$"
)
_GATE_RE = re.compile(r"^## (.+?): (ok|FAIL)$", re.MULTILINE)
_STDERR = "\n--- stderr ---\n"
_TIMED_OUT = "--- timed out ---"


# --- the parsers ---------------------------------------------------------------------------


def parse_gates(text: str, log: str) -> list[dict[str, object]] | None:
    """A ``gates-N.txt`` as the jobs table's ``gates`` (their seconds weren't kept); None if
    it holds no gate."""
    gates: list[dict[str, object]] = [
        {"name": m[1], "ok": m[2] == "ok", "seconds": None, "log": log}
        for m in _GATE_RE.finditer(text)
    ]
    return gates or None


@dataclass(frozen=True)
class ClaudeLog:
    ok: bool
    timed_out: bool = False
    tokens_in: int = 0
    tokens_cached: int = 0
    tokens_out: int = 0
    cost_usd: float | None = None
    session_id: str | None = None
    duration_s: float = 0.0


def parse_claude_log(text: str) -> ClaudeLog | None:
    """A ``claude-*.log`` (``claude -p``'s JSON, then its stderr); None if unreadable."""
    if text.startswith(_TIMED_OUT):
        return ClaudeLog(ok=False, timed_out=True)
    try:
        data = json.loads(text.split(_STDERR, 1)[0].strip())
        if not isinstance(data, dict):
            return None
        usage = data.get("usage") or {}
        cost = data.get("total_cost_usd")
        return ClaudeLog(
            ok=not data.get("is_error"),
            tokens_in=int(usage.get("input_tokens") or 0),
            tokens_cached=int(usage.get("cache_read_input_tokens") or 0),
            tokens_out=int(usage.get("output_tokens") or 0),
            cost_usd=float(cost) if cost is not None else None,
            session_id=str(data["session_id"]) if data.get("session_id") else None,
            duration_s=int(data.get("duration_ms") or 0) / 1000,
        )
    except (ValueError, TypeError, AttributeError):
        return None


@dataclass(frozen=True)
class LogName:
    kind: str
    subject: str
    number: int | None  # the job's number in its session, when there was more than one
    retry: int  # a usage-limit retry of the same job; 0 for the first run


def claude_log_name(name: str) -> LogName | None:
    """``claude-<kind>-<subject>[-N][-retryK].log``, as ``runner.loop.call_claude`` names it."""
    match = _CLAUDE_LOG_RE.match(name)
    if match is None:
        return None
    number, retry = match["number"], match["retry"]
    return LogName(
        match["kind"], match["subject"], int(number) if number else None, int(retry or 0)
    )


def _event_times(lines: Iterable[str]) -> list[int]:
    times = []
    for line in lines:
        if line.startswith("{"):
            try:
                at = json.loads(line).get("timestamp")
            except (json.JSONDecodeError, AttributeError):
                continue
            if isinstance(at, int):
                times.append(at)
    return times


def _iso_ms(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=UTC).astimezone().isoformat()


def _iso_mtime(path: Path, minus_s: float = 0.0) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime - minus_s, tz=UTC).astimezone().isoformat()


def _key_of(ticket: str) -> str | None:
    match = _TICKET_RE.match(ticket)
    return match[1] if match else None


# --- the backfill --------------------------------------------------------------------------


@dataclass(frozen=True)
class Counts:
    runs: int = 0
    tickets: int = 0
    jobs: int = 0
    findings: int = 0
    merges: int = 0


@dataclass
class Summary:
    written: dict[str, Counts]  # per milestone key
    gaps: list[str]


@dataclass
class _Backfill:
    conn: sqlite3.Connection
    repo: Path
    runs_dir: Path
    local_agent: str
    project_id: int
    gaps: list[str] = field(default_factory=list)
    seen: dict[str, dict[str, set[object]]] = field(default_factory=dict)
    milestones: dict[str, int] = field(default_factory=dict)
    tickets: dict[str, int] = field(default_factory=dict)
    local_logs: Counter[str] = field(default_factory=Counter)  # ticket -> attempts with a log

    def rel(self, path: Path) -> str:
        return path.relative_to(self.repo).as_posix()

    def gap(self, path: Path, why: str) -> None:
        self.gaps.append(f"{self.rel(path)}: {why}")

    def count(self, key: str | None, what: str, item: object) -> None:
        if key is not None:
            self.seen.setdefault(key, {}).setdefault(what, set()).add(item)

    def milestone(self, key: str) -> int:
        if key not in self.milestones:
            self.milestones[key] = metrics.upsert_milestone(self.conn, self.project_id, key)
        return self.milestones[key]

    def ticket(self, ticket: str) -> int:
        if ticket not in self.tickets:
            key = _key_of(ticket)
            self.tickets[ticket] = metrics.upsert_ticket(
                self.conn,
                self.project_id,
                ticket,
                milestone_id=self.milestone(key) if key else None,
            )
        self.count(_key_of(ticket), "tickets", ticket)
        return self.tickets[ticket]

    def summary(self) -> Summary:
        written = {
            key: Counts(**{what: len(items) for what, items in found.items()})
            for key, found in self.seen.items()
        }
        return Summary(written=written, gaps=self.gaps)


def backfill(conn: sqlite3.Connection, repo: Path, runs_dir: Path, *, local_agent: str) -> Summary:
    """Load every past milestone into ``conn``; ``local_agent`` is D6's id for the OpenCode
    jobs (the logs don't name the model)."""
    b = _Backfill(
        conn, repo, runs_dir, local_agent, metrics.upsert_project(conn, repo.name, repo=str(repo))
    )
    footers = _tickets(b)
    if runs_dir.is_dir():
        for entry in sorted(runs_dir.iterdir()):
            if entry.is_dir() and _RUN_DIR_RE.match(entry.name):
                _run(b, entry)
            elif entry.name != "state.json":
                b.gap(entry, "not a run folder; nothing recovered from it")
    _merges(b)
    _milestones(b)
    for ticket, (attempts, tokens) in sorted(footers.items()):
        found = b.local_logs[ticket]
        if attempts > found:
            b.gaps.append(
                f"{ticket}: its footers count {attempts} attempt(s) and {tokens:,} tokens, the"
                f" logs hold {found}; only the ticket-level facts were recorded"
            )
    return b.summary()


def _tickets(b: _Backfill) -> dict[str, tuple[int, int]]:
    """Every ticket in tasks/ with its text and folder; returns the local attempts and tokens
    its footers count, per ticket."""
    footers: dict[str, tuple[int, int]] = {}
    for folder in TICKET_FOLDERS:
        for path in sorted((b.repo / "tasks" / folder).glob("*.md")):
            try:
                text = path.read_text(encoding="utf-8")
                meta, body = split_frontmatter(text)
                key = milestone_key(meta.get("milestone"))
                estimate = difficulty(meta, "difficulty")
                corrected = difficulty(meta, "difficulty_corrected")
            except Exception as exc:
                b.gap(path, f"unreadable ticket ({exc})")
                continue
            goal = parse_sections(body).get("Goal", "").strip()
            depends_on, files = meta.get("depends_on") or [], meta.get("files") or []
            b.tickets[path.stem] = metrics.upsert_ticket(
                b.conn,
                b.project_id,
                path.stem,
                milestone_id=b.milestone(key),
                title=goal.splitlines()[0] if goal else None,
                body=text,
                kind="lead" if meta.get("agent") == "lead" else "developer",
                depends_on=[str(d) for d in depends_on] if isinstance(depends_on, list) else None,
                files=[str(f) for f in files] if isinstance(files, list) else None,
                state=folder,
                difficulty=estimate,
                difficulty_corrected=corrected,
            )
            b.count(key, "tickets", path.stem)
            local = [f for f in all_footers(text) if f.get("agent") != "lead"]
            attempts = sum(int(f["attempts"]) for f in local if f.get("attempts", "").isdigit())
            tokens = sum(int(f["tokens"]) for f in local if f.get("tokens", "").isdigit())
            if attempts:
                footers[path.stem] = (attempts, tokens)
    return footers


def _task_dirs(run: Path) -> list[tuple[str, Path]]:
    """(ticket, folder) per task folder of a run, a requeued task's `-runN` in order."""
    found = []
    for sub in run.iterdir():
        match = _TASK_DIR_RE.match(sub.name)
        if sub.is_dir() and match and _key_of(match[1]):
            found.append((match[1], int(match[2] or 1), sub))
    return [(ticket, sub) for ticket, _, sub in sorted(found)]


def _opencode_logs(folder: Path) -> list[tuple[int, Path]]:
    logs = [(int(m[1]), p) for p in folder.iterdir() if (m := _OPENCODE_RE.match(p.name))]
    return sorted(logs)


def _run(b: _Backfill, run: Path) -> None:
    task_dirs = _task_dirs(run)
    for ticket, folder in task_dirs:
        b.local_logs[ticket] += len(_opencode_logs(folder))
    row = b.conn.execute(
        "SELECT command FROM runs WHERE project_id = ? AND run_dir = ?", (b.project_id, run.name)
    ).fetchone()
    if row is not None and row["command"] not in (None, BACKFILL):
        return  # the runner recorded this run as it happened
    started = datetime.strptime(run.name, "%Y%m%d-%H%M%S").astimezone().isoformat()
    run_id = metrics.upsert_run(b.conn, b.project_id, run.name, command=BACKFILL, started=started)
    ends: list[str] = []
    attempts: Counter[str] = Counter()
    for ticket, folder in task_dirs:
        logs = _opencode_logs(folder)
        for n, log in logs:
            attempts[ticket] += 1
            last = n == logs[-1][0] and (folder / "direction.md").is_file()
            ends.append(_local_job(b, run_id, ticket, attempts[ticket], folder, n, log, last))
    keys = Counter(_key_of(ticket) for ticket, _ in task_dirs)
    run_key = keys.most_common(1)[0][0] if keys else None
    reviews = _claude_jobs(b, run, run_id, run_key, ends)
    _review_findings(b, run, reviews)
    if ends:
        metrics.upsert_run(b.conn, b.project_id, run.name, ended=max(ends))


def _local_job(
    b: _Backfill,
    run_id: int,
    ticket: str,
    attempt: int,
    folder: Path,
    n: int,
    log: Path,
    directed: bool,
) -> str:
    """One OpenCode attempt as a job; returns when it ended."""
    text = log.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    tokens, facts, times = parse_events(lines), stream_facts(lines), _event_times(lines)
    timed_out = _TIMED_OUT in text
    started = _iso_ms(times[0]) if times else _iso_mtime(log)
    ended = _iso_ms(times[-1]) if times else started
    gates: list[dict[str, object]] | None = None
    note = None
    blocked, gates_file = folder / f"BLOCKED-{n}.md", folder / f"gates-{n}.txt"
    if blocked.is_file():
        outcome = "failed"
        note = f"BLOCKED: {parse_blocked(blocked.read_text(encoding='utf-8')) or 'invalid'}"
    else:
        if gates_file.is_file():
            gates = parse_gates(gates_file.read_text(encoding="utf-8"), b.rel(gates_file))
            if gates is None:
                b.gap(gates_file, "no gate results in it; the attempt's outcome is a guess")
        else:
            b.gap(gates_file, "missing; the attempt's outcome is a guess")
        if gates and all(g["ok"] for g in gates):
            outcome = "passed"
        else:
            outcome = "timeout" if timed_out else "failed"
    key = _key_of(ticket)
    job_id = metrics.start_job(
        b.conn,
        run_id,
        ticket_id=b.ticket(ticket),
        milestone_id=b.milestone(key) if key else None,
        role="last-attempt" if directed else "developer",
        agent=b.local_agent,
        attempt=attempt,
        started=started,
        log_path=b.rel(log),
    )
    metrics.finish_job(
        b.conn,
        job_id,
        ended=ended,
        outcome=outcome,
        tokens_in=tokens.input,
        tokens_out=tokens.output + tokens.reasoning,
        steps=tokens.steps,
        peak_context=tokens.peak,
        edit_streak=facts.edit_streak,
        refused_commands=facts.refused,
        gates=gates,
        note=note,
        session_id=facts.session_id or None,
    )
    b.count(key, "jobs", job_id)
    b.count(key, "runs", run_id)
    return ended


def _claude_jobs(
    b: _Backfill, run: Path, run_id: int, run_key: str | None, ends: list[str]
) -> dict[tuple[str, int], int]:
    """The run's Claude jobs, a limit's retries folded into their job; returns the review
    jobs' ids by (milestone, round)."""
    groups: dict[tuple[str, str, int | None], list[tuple[int, Path]]] = {}
    for path in sorted(run.glob("claude-*.log")):
        name = claude_log_name(path.name)
        if name is None:
            b.gap(path, "not a Claude job log name")
            continue
        groups.setdefault((name.kind, name.subject, name.number), []).append((name.retry, path))
    reviews: dict[tuple[str, int], int] = {}
    for (kind, subject, number), logs in sorted(groups.items(), key=lambda g: str(g[0])):
        paths = [path for _, path in sorted(logs)]
        role = kind if kind in ROLES else UNKNOWN
        ticket = subject if kind in TICKET_KINDS or (role == UNKNOWN and _key_of(subject)) else None
        key = _key_of(ticket) if ticket else None
        round_ = _ROUND_RE.search(subject) if kind == "review" else None
        if kind == "review":
            key = subject.split("-", 1)[0] if _KEY_RE.fullmatch(subject.split("-", 1)[0]) else None
        key = key or run_key
        results = [parse_claude_log(p.read_text(encoding="utf-8", errors="replace")) for p in paths]
        for path, result in zip(paths, results, strict=True):
            if result is None:
                b.gap(path, "unreadable Claude log; the job's tokens and outcome are lost")
        parsed = [log for log in results if log is not None]
        last = results[-1]
        if last is not None and last.timed_out:
            outcome = "timeout"
        else:
            outcome = "passed" if last is not None and last.ok else "failed"
        ended = _iso_mtime(paths[-1])
        attempt = number or (int(round_[1]) if round_ else 1)
        job_id = metrics.start_job(
            b.conn,
            run_id,
            ticket_id=b.ticket(ticket) if ticket else None,
            milestone_id=b.milestone(key) if key else None,
            role=role,
            agent=CLAUDE_SONNET if kind == "checkpoint" else CLAUDE_OPUS,
            attempt=attempt,
            started=_iso_mtime(paths[-1], sum(log.duration_s for log in parsed)),
            log_path=b.rel(paths[0]),
        )
        costs = [log.cost_usd for log in parsed if log.cost_usd is not None]
        metrics.finish_job(
            b.conn,
            job_id,
            ended=ended,
            outcome=outcome,
            tokens_in=sum(log.tokens_in for log in parsed),
            tokens_cached=sum(log.tokens_cached for log in parsed),
            tokens_out=sum(log.tokens_out for log in parsed),
            cost_usd=sum(costs) if costs else None,
            session_id=next((log.session_id for log in reversed(parsed) if log.session_id), None),
            log_path=b.rel(paths[-1]),
        )
        if key is None:
            b.gap(paths[0], "no milestone found for this job")
        b.count(key, "jobs", job_id)
        b.count(key, "runs", run_id)
        ends.append(ended)
        if kind == "review" and key and round_:
            reviews[(key, int(round_[1]))] = job_id
    return reviews


def _review_findings(b: _Backfill, run: Path, reviews: dict[tuple[str, int], int]) -> None:
    found = [(m[1], int(m[2]), p) for p in run.iterdir() if (m := _REVIEW_JSON_RE.match(p.name))]
    for key, round_, path in sorted(found):
        try:
            review = parse_review(path)
        except ReviewFileError as exc:
            b.gap(path, f"unreadable review ({exc})")
            continue
        milestone_id = b.milestone(key)
        for finding in review.findings:
            finding_id = metrics.add_finding(
                b.conn,
                milestone_id,
                finding.id,
                job_id=reviews.get((key, round_)),
                severity=finding.severity,
                route=finding.route,
                summary=finding.summary,
                resolved=finding.resolved,
                agent=CLAUDE_OPUS,
            )
            b.count(key, "findings", finding_id)


def _merges(b: _Backfill) -> None:
    """Who merged each ticket, from git's trailers (and the local model's pre-trailer
    wording, ADR 00 A4)."""
    git = Git(b.repo)
    merged_by = {LOCAL_MODEL_AGENT: b.local_agent, CLAUDE_HEADLESS_AGENT: CLAUDE_OPUS}
    try:
        out = git.run("log", "--reverse", "--format=%H%x1f%B%x1e")
    except GitError as exc:
        b.gaps.append(f"git: no merges recovered ({exc})")
        return
    for record in out.split("\x1e"):
        if not record.strip():
            continue
        sha, body = record.strip("\n").split("\x1f", 1)
        trailers = parse_trailers(body)
        ticket, agent = trailers.get("Task"), trailers.get("Agent")
        if ticket is None and "Implemented by the local model" in body:
            ticket, agent = body.split(":", 1)[0].strip(), LOCAL_MODEL_AGENT
        if ticket is None or _key_of(ticket) is None:
            continue
        b.ticket(ticket)
        metrics.upsert_ticket(
            b.conn,
            b.project_id,
            ticket,
            merged_by=merged_by.get(agent or "", UNKNOWN),
            commit=sha,
            lines_changed=git.commit_size(sha),
        )
        b.count(_key_of(ticket), "merges", ticket)


def _milestones(b: _Backfill) -> None:
    """Each milestone's doc, sign-off sheet, review rounds and dates."""
    state_path = b.runs_dir / "state.json"
    rounds: dict[str, list[int]] = {}
    if state_path.is_file():
        try:
            rounds = load_state(state_path).review_counts
        except (ValueError, TypeError) as exc:
            b.gap(state_path, f"unreadable ({exc}); review rounds not recovered")
    docs = b.repo / "docs"
    keys = {p.stem for p in (docs / "milestones").glob("*.md") if _KEY_RE.fullmatch(p.stem)}
    for key in sorted(keys | set(b.milestones)):
        doc_path, review_path = docs / "milestones" / f"{key}.md", docs / "reviews" / f"{key}.md"
        doc = milestone_doc(doc_path.read_text(encoding="utf-8")) if doc_path.is_file() else {}
        sheet = (
            signoff_sections(review_path.read_text(encoding="utf-8"))
            if review_path.is_file()
            else {}
        )
        started, ended = _commit_time(b.repo, f"{key}-start"), _commit_time(b.repo, f"{key}-done")
        round_counts = rounds.get(key)
        metrics.upsert_milestone(
            b.conn,
            b.project_id,
            key,
            title=doc.get("title"),
            outcome=doc.get("outcome"),
            done_when=doc.get("done_when"),
            signoff=sheet or None,
            review_rounds=len(round_counts) if isinstance(round_counts, list) else None,
            started=started.isoformat() if started else None,
            ended=ended.isoformat() if ended else None,
            status="done" if ended else None,
        )


def render(summary: Summary) -> str:
    """What the backfill wrote per milestone, then what it couldn't recover."""
    header = ("milestone", "runs", "tickets", "jobs", "findings", "merges")
    rows = [header] + [
        (key, *(str(getattr(c, name)) for name in header[1:]))
        for key, c in sorted(summary.written.items(), key=lambda kv: milestone_order(kv[0]))
    ]
    widths = [max(len(row[i]) for row in rows) for i in range(len(header))]
    lines = ["Written:"] + [
        "  " + "  ".join(cell.ljust(w) for cell, w in zip(row, widths, strict=True)).rstrip()
        for row in rows
    ]
    lines += ["", f"Gaps ({len(summary.gaps)}):" if summary.gaps else "Gaps: none"]
    lines += [f"  - {gap}" for gap in summary.gaps]
    return "\n".join(lines) + "\n"
