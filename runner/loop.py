"""The per-task loop and the session around it (docs/workflow.md)."""

import hashlib
import json
import select
import sqlite3
import sys
import threading
import time
from collections.abc import Callable, Collection, Iterable, Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from functools import partial
from pathlib import Path
from typing import Any, Concatenate, NoReturn

from runner import allowance, checks, console, messages, metrics, prompts, ratings
from runner.agents import (
    ANY,
    CHECK_COMMANDS,
    GIT_READ_COMMANDS,
    TRANSIENT,
    JobResult,
    JobSpec,
    Reading,
    adapter_for,
)
from runner.claude import backoff_seconds
from runner.config import Config, read_protected
from runner.gates import (
    BLOCKED_FILE,
    HINTS,
    NO_CHANGES,
    GateContext,
    GateResult,
    is_test_file,
    outside_allowed,
    parse_blocked,
    run_gates,
)
from runner.gitops import (
    LOCAL_MODEL_AGENT,
    LOCAL_MODEL_AUTHOR,
    RUNNER_AUTHOR,
    Git,
    GitError,
    with_trailers,
)
from runner.local_model import ADAPTER as OPENCODE
from runner.local_model import (
    LIVE_EVERY,
    OPENCODE_DB,
    TokenTotals,
    empty_cause,
    is_local,
    loaded_context_length,
    session_reasoning,
    stream_facts,
    warmup,
)
from runner.procs import run_bounded
from runner.report import ClaudeRunRecord, SessionReport, TaskRecord
from runner.review import Finding, ReviewFileError, parse_checkpoint
from runner.state import State, load_state, save_state
from runner.tasks import (
    STOPPED,
    Task,
    append_footer,
    blocked_ids,
    carry_footers,
    command_arg,
    difficulty,
    load_dir,
    milestone_key,
    milestone_order,
    parse_sections,
    parse_task,
    pick_next,
    preflight,
    split_frontmatter,
    stopped_ids,
    task_ids,
)
from runner.usage import claude_tokens, transcripts_dir

MAIN = "main"
RUNNER_AGENT = "runner"
CLAUDE_HEADLESS_AGENT = "claude-headless"


class RunnerError(RuntimeError):
    pass


def now() -> datetime:
    return datetime.now().astimezone()


def clock() -> float:
    """Seconds for the console's timings; a test swaps it to skip ten minutes."""
    return time.monotonic()


PROGRESS_EVERY = 600.0  # seconds between the console's progress lines (f1-42)
POLL_S = 1.0  # how often a job in a thread is checked for a due progress line


class Ticker:
    """When the next progress line is due: every ``PROGRESS_EVERY`` seconds from its start."""

    def __init__(self) -> None:
        self.started = clock()
        self.next_at = self.started + PROGRESS_EVERY

    def due(self) -> float | None:
        """The seconds elapsed if a progress line is due, else None."""
        at = clock()
        if at < self.next_at:
            return None
        while self.next_at <= at:
            self.next_at += PROGRESS_EVERY
        return at - self.started


def with_progress[T](work: Callable[[], T], tick: Callable[[float], None]) -> T:
    """Run ``work`` in a thread; while it runs, ``tick`` gets the seconds elapsed every
    ``PROGRESS_EVERY`` seconds. Its result or exception comes back here."""
    box: dict[str, Any] = {}

    def target() -> None:
        try:
            box["value"] = work()
        except BaseException as exc:
            box["error"] = exc

    ticker = Ticker()
    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    while thread.is_alive():
        thread.join(POLL_S)
        if thread.is_alive() and (elapsed := ticker.due()) is not None:
            tick(elapsed)
    if "error" in box:
        raise box["error"]
    value: T = box["value"]
    return value


def runner_commit(s: "Session", message: str) -> bool:
    """The runner's own bookkeeping (task moves, reports), attributed to it (ADR 00 A4)."""
    return s.git.commit_all(with_trailers(message, agent=RUNNER_AGENT), author=RUNNER_AUTHOR)


def local_wip_commit(s: "Session", message: str) -> bool:
    """The model's work on its task branch; squashed away on merge, kept on escalation."""
    return s.git.commit_all(
        with_trailers(message, agent=LOCAL_MODEL_AGENT), author=LOCAL_MODEL_AUTHOR
    )


@dataclass
class Session:
    cfg: Config
    git: Git
    state: State
    report: SessionReport
    run_dir: Path
    context_checked: bool = False
    context_limit: int | None = None  # the context LM Studio loaded, if it said
    # The metrics database (f1 D2), best effort: None when it couldn't be opened.
    db: sqlite3.Connection | None = None
    project_id: int | None = None
    run_id: int | None = None
    db_failed: bool = False
    # The thread that beats the run's heartbeat while the process lives (f1-49), and its stop.
    heartbeat: threading.Thread | None = None
    heartbeat_stop: threading.Event = field(default_factory=threading.Event)
    # Jobs so far per (ticket, role group): the next job's `attempt` and its log's number.
    job_numbers: dict[tuple[str | None, str], int] = field(default_factory=dict)
    last_job_id: int | None = None  # the last Claude job's row, for its findings
    ticket_started: float = 0.0  # `clock()` when the current ticket started, for the console

    @property
    def repo(self) -> Path:
        return self.cfg.repo

    @property
    def state_path(self) -> Path:
        return self.cfg.runs_dir / "state.json"

    def tasks_dir(self, name: str) -> Path:
        return self.repo / "tasks" / name

    def log(self, message: str) -> None:
        """One console line (`runner.console`); an empty one is a blank line."""
        print(f"[{now():%H:%M:%S}] {message}" if message else "", flush=True)


def open_session(cfg: Config, command: str | None = "run") -> Session:
    """A session on a clean main. With a ``command``, it is recorded as a run in the metrics
    database; None records nothing."""
    git = Git(cfg.repo)
    state_path = cfg.runs_dir / "state.json"
    state = load_state(state_path)
    cut_off = state.in_flight
    recovered = _recover(git, state, state_path) if cut_off is not None else ""
    # A ticket parked at the reserve is asked about again by the next command (ADR 15 item 5);
    # a later session of the same command goes by its answer, in `RESERVE`.
    asked = [k for k, entry in state.parked.items() if entry.get("kind") == "reserve"]
    for key in asked:
        del state.parked[key]
    # A ticket parked for a limit is tried again at once: the owner may have reset the
    # allowance before restarting (2026-10-01). Still limited, it parks on Claude's new reset.
    at = now()
    retried = [k for k, entry in state.parked.items() if _resets(entry) > at]
    for key in retried:
        state.parked[key]["resets_at"] = at.isoformat()
    if asked or retried:
        save_state(state, state_path)
    # Without an in-flight job, a dirty tree isn't the runner's: leave it to the owner.
    if git.current_branch() != MAIN or not git.is_clean():
        raise RunnerError("start the runner on a clean main branch")
    started = now()
    run_dir = cfg.runs_dir / f"{started:%Y%m%d-%H%M%S}"
    run_dir.mkdir(parents=True, exist_ok=True)
    s = Session(
        cfg=cfg, git=git, state=state, report=SessionReport(started=started), run_dir=run_dir
    )
    if command is not None:
        _start_run(s, command, cut_off.get("job_id") if cut_off else None)
    if recovered:
        s.log(recovered)
        s.report.notes.append(recovered)
    return s


# --- recovery after an interruption (ADR 15 item 11) ---------------------------------------


INTERRUPTED_PROMPT = (
    "Your earlier run of this job was interrupted (a Ctrl-C, a crash or a reboot). Carry on"
    " with the same job from where you stopped."
)
INTERRUPTED_NOTE = (
    "\n\nAn earlier run of this job was interrupted part-way (a Ctrl-C, a crash or a reboot)."
)
ON_THIS_BRANCH = (
    " The changes it had made are committed on this branch: check `git show HEAD` before you"
    " go on, and build on them or undo them."
)
ON_ANOTHER_BRANCH = (
    " The changes it had made were kept on the branch `{branch}`, not here: `git diff"
    " {main}...{branch}` shows them. Make again the ones you still want."
)
WIP_INTERRUPTED = "wip {name} (interrupted)"
# A local attempt cut off before its gates ran: what the next attempt is told.
INTERRUPTED_GATE = "interrupted"
INTERRUPTED_OUTPUT = (
    "The attempt was cut off (a Ctrl-C, a crash or a reboot) before its gates ran. Its changes"
    " are committed on this branch."
)


def job_key(kind: str, name: str) -> str:
    """What names a Claude job across runs: its kind and its ticket, else its subject."""
    return f"{kind}:{name}"


def _set_in_flight(s: Session, **entry: Any) -> None:
    s.state.in_flight = {**entry, "started": now().isoformat()}
    save_state(s.state, s.state_path)


def _clear_in_flight(s: Session) -> None:
    if s.state.in_flight is not None:
        s.state.in_flight = None
        save_state(s.state, s.state_path)


def _in_flight_session(s: Session, session_id: str | None) -> None:
    """The in-flight Claude job's session, once known: what its next run resumes."""
    if s.state.in_flight is not None and session_id:
        s.state.in_flight["session_id"] = session_id
        save_state(s.state, s.state_path)


def _free_branch(git: Git, name: str) -> str:
    """``name``, or ``name-2``, ``name-3``…: an earlier interruption's branch is kept."""
    taken = set(git.run("branch", "--list", "--format=%(refname:short)").split())
    candidate, n = name, 1
    while candidate in taken:
        n += 1
        candidate = f"{name}-{n}"
    return candidate


def _recover(git: Git, state: State, state_path: Path) -> str:
    """Put away what an interrupted job left: its changes committed to its branch (or to
    ``interrupted/…`` when it ran on main), main checked out clean. A Claude job keeps its
    session id for its next run; a local attempt counts as timed out. Returns the console
    line that says what was recovered."""
    job = state.in_flight or {}
    kind, ticket, branch = str(job["kind"]), job.get("ticket"), str(job["branch"])
    agent = str(job.get("agent") or RUNNER_AGENT)
    name = ticket or job.get("subject") or kind
    target: str | None = branch
    if branch == MAIN:
        target = None
        if not git.is_clean():
            target = _free_branch(git, f"interrupted/{kind}-{ticket or job.get('milestone')}")
            git.run("checkout", "-q", "-b", target)
    elif git.current_branch() != branch:
        git.checkout(branch)  # the tree's changes come along
    if kind == "local":
        what = f"attempt {job.get('attempt', '?')} of {ticket}"
        message = f"wip {ticket} attempt {job.get('attempt', '?')} (interrupted)"
        kept = git.commit_all(
            with_trailers(message, agent=LOCAL_MODEL_AGENT), author=LOCAL_MODEL_AUTHOR
        )
        state.timed_out[str(ticket)] = state.timed_out.get(str(ticket), 0) + 1
        after = "it counts as timed out"
    else:
        what = f"{kind} {name}"
        message = WIP_INTERRUPTED.format(name=ticket or kind)
        kept = git.commit_all(with_trailers(message, agent=CLAUDE_HEADLESS_AGENT))
        session = str(job.get("session_id") or "")
        where = target if kept and target else ""
        state.interrupted[job_key(kind, str(name))] = {"session_id": session, "branch": where}
        after = (
            f"its session {session} resumes on its next run"
            if session
            else "it starts again on its next run"
        )
    if target is not None:
        git.checkout(MAIN)
    state.in_flight = None
    save_state(state, state_path)
    changes = f"its changes are on {target}" if kept else "it had changed nothing"
    return f"↺ [{agent}] recovered the interrupted {what}: {changes}; {after}"


# --- the metrics database (f1 D2, D3): best effort ----------------------------------------


HEARTBEAT_EVERY = LIVE_EVERY  # seconds between the heartbeat thread's beats (f1-49)
_failed_lock = threading.Lock()  # the heartbeat thread and the run may fail at once


def _metrics_failed(s: Session, exc: Exception) -> None:
    with _failed_lock:
        if s.db_failed:
            return
        s.db_failed = True
    s.report.notes.append(
        f"The metrics database failed ({type(exc).__name__}: {exc}); the run went on"
        " without the rows it couldn't write. Later failures aren't listed."
    )


def _record[**P, T](
    s: Session,
    write: Callable[Concatenate[sqlite3.Connection, P], T],
    *args: P.args,
    **kwargs: P.kwargs,
) -> T | None:
    """One write to the metrics database. A write that fails is noted once in the session
    report and never stops the run."""
    if s.db is None:
        return None
    try:
        return write(s.db, *args, **kwargs)
    except Exception as exc:
        _metrics_failed(s, exc)
        return None


def _rel(s: Session, path: Path) -> str:
    return path.relative_to(s.repo).as_posix()


def _start_run(s: Session, command: str, cut_off_job: int | None = None) -> None:
    try:
        s.db = metrics.open_db(s.cfg.metrics_db)
    except Exception as exc:
        _metrics_failed(s, exc)
        return
    s.project_id = _record(
        s,
        metrics.upsert_project,
        s.repo.name,
        repo=str(s.repo),
        description=s.cfg.project_description or None,
    )
    if s.project_id is not None:
        at = s.report.started.isoformat()
        s.run_id = _record(
            s,
            metrics.upsert_run,
            s.project_id,
            s.run_dir.name,
            command=command,
            started=at,
            heartbeat=at,
        )
        if s.run_id is not None:
            if cut_off_job is not None:
                _record(s, metrics.end_interrupted, cut_off_job)
            _record(s, metrics.close_abandoned, s.project_id, s.run_id)
            _start_heartbeat(s, s.run_id)
        sync_tickets(s)


def _start_heartbeat(s: Session, run_id: int) -> None:
    """Beat the run's heartbeat every ``HEARTBEAT_EVERY`` seconds, whatever the run is doing
    (f1-49): a Claude job, the gates, check-all or a pause write nothing until they end. The
    thread has its own connection (sqlite3's can't cross threads) and is a daemon, so a crash
    or a Ctrl-C leaves the heartbeat stale, as D3 wants."""

    def beat() -> None:
        try:
            conn = metrics.open_db(s.cfg.metrics_db)
        except Exception as exc:
            _metrics_failed(s, exc)
            return
        try:
            while not s.heartbeat_stop.wait(HEARTBEAT_EVERY):
                try:
                    metrics.update_run_heartbeat(conn, run_id, now().isoformat())
                except Exception as exc:
                    _metrics_failed(s, exc)
        finally:
            conn.close()

    s.heartbeat = threading.Thread(target=beat, name="runner-heartbeat", daemon=True)
    s.heartbeat.start()


def _stop_heartbeat(s: Session) -> None:
    if s.heartbeat is not None:
        s.heartbeat_stop.set()
        s.heartbeat.join()  # a beat in flight lands before the run's end, never after
        s.heartbeat = None


TICKET_FOLDERS = ("ready", "done", *STOPPED)


def sync_tickets(s: Session) -> None:
    """Every ticket in tasks/ with its folder's state (f1 D4): the queue the dashboard reads."""
    for folder in TICKET_FOLDERS:
        for path in sorted(s.tasks_dir(folder).glob("*.md")):
            record_ticket(s, path)


def record_ticket(
    s: Session,
    path: Path,
    state: str | None = None,
    *,
    merged_by: str | None = None,
    commit: str | None = None,
) -> None:
    """A ticket's row: its text and its state (its folder's, unless given). A merge adds who
    merged it, the commit and its lines changed. A file that doesn't parse is left out."""
    if s.project_id is None:
        return
    try:
        text = path.read_text(encoding="utf-8")
        meta, body = split_frontmatter(text)
        milestone = milestone_key(meta.get("milestone"))
        estimate = difficulty(meta, "difficulty")
        corrected = difficulty(meta, "difficulty_corrected")
    except Exception:
        return
    goal = parse_sections(body).get("Goal", "").strip()
    depends_on, files = meta.get("depends_on") or [], meta.get("files") or []
    _record(
        s,
        metrics.upsert_ticket,
        s.project_id,
        path.stem,
        milestone_id=_record(s, metrics.upsert_milestone, s.project_id, milestone),
        title=goal.splitlines()[0] if goal else None,
        body=text,
        kind="lead" if meta.get("agent") == "lead" else "developer",
        depends_on=[str(d) for d in depends_on] if isinstance(depends_on, list) else None,
        files=[str(f) for f in files] if isinstance(files, list) else None,
        state=state or path.parent.name,
        difficulty=estimate,
        difficulty_corrected=corrected,
        merged_by=merged_by,
        commit=commit,
        lines_changed=s.git.commit_size(commit) if commit else None,
    )


def _finish_run(s: Session, verdict: str) -> None:
    _stop_heartbeat(s)
    if s.run_id is not None and s.project_id is not None:
        at = now().isoformat()
        _record(
            s,
            metrics.upsert_run,
            s.project_id,
            s.run_dir.name,
            ended=at,
            heartbeat=at,
            verdict=verdict,
        )
    if s.db is not None:
        s.db.close()
        s.db = None


def next_number(s: Session, ticket: str | None, group: str) -> int:
    """The next job number for a ticket (or the milestone, with None) in this session: the
    `attempt` of its row, and the number that keeps its log apart from an earlier one's."""
    number = s.job_numbers[(ticket, group)] = s.job_numbers.get((ticket, group), 0) + 1
    return number


def record_start(
    s: Session,
    ticket: str | None,
    milestone: str,
    role: str,
    agent: str,
    *,
    attempt: int = 1,
    log_path: str | None = None,
    context_limit: int | None = None,
) -> int | None:
    """Write a job as running (f1 D3) and beat the run's heartbeat; returns the job's id."""
    if s.run_id is None or s.project_id is None:
        return None
    at = now().isoformat()
    milestone_id = _record(s, metrics.upsert_milestone, s.project_id, milestone)
    ticket_id = _record(s, metrics.upsert_ticket, s.project_id, ticket) if ticket else None
    _record(s, metrics.update_run_heartbeat, s.run_id, at)
    return _record(
        s,
        metrics.start_job,
        s.run_id,
        ticket_id=ticket_id,
        milestone_id=milestone_id,
        role=role,
        agent=agent,
        attempt=attempt,
        started=at,
        context_limit=context_limit,
        log_path=log_path,
    )


def live_update(s: Session, job_id: int | None, tokens: TokenTotals) -> None:
    """Every 30 s of an attempt: its tokens and steps so far, and the run's heartbeat."""
    if job_id is None or s.run_id is None:
        return
    _record(
        s,
        metrics.update_running_job,
        job_id,
        tokens_in=tokens.input,
        tokens_out=tokens.output + tokens.reasoning,
        steps=tokens.steps,
    )
    _record(s, metrics.update_run_heartbeat, s.run_id, now().isoformat())


def _total(tokens: TokenTotals) -> int:
    return tokens.input + tokens.output + tokens.reasoning


def attempt_progress(
    s: Session,
    agent: str,
    job_id: int | None,
    what: str,
    log: Path,
    ticker: Ticker,
    tokens: TokenTotals,
) -> None:
    """``live_update``, plus a console line every ``PROGRESS_EVERY`` seconds."""
    live_update(s, job_id, tokens)
    if (elapsed := ticker.due()) is None:
        return
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines() if log.is_file() else []
    streak = stream_facts(lines).edit_streak
    s.log(console.local_progress(agent, what, elapsed, _total(tokens), tokens.steps, streak))


def _tokens_in(run: JobResult) -> int:
    return run.usage.get("input_tokens", 0)


def _tokens_out(run: JobResult) -> int:
    return run.usage.get("output_tokens", 0) + run.usage.get("reasoning_tokens", 0)


def _attempt_end(s: Session, agent: str, what: str, run: JobResult, outcome: str) -> None:
    total = _tokens_in(run) + _tokens_out(run)
    s.log(console.local_end(agent, what, outcome, run.duration_s, total, run.num_turns))


def _finish_attempt(
    s: Session,
    job_id: int | None,
    run: JobResult,
    outcome: str,
    *,
    gates: list[dict[str, object]] | None = None,
    note: str | None = None,
    context_limit: int | None = None,
) -> None:
    _clear_in_flight(s)
    if job_id is None or s.run_id is None:
        return
    at = now().isoformat()
    _record(
        s,
        metrics.finish_job,
        job_id,
        ended=at,
        outcome=outcome,
        tokens_in=_tokens_in(run),
        tokens_out=_tokens_out(run),
        steps=run.num_turns,
        peak_context=run.peak_context,
        context_limit=context_limit,
        edit_streak=run.edit_streak,
        refused_commands=run.refused_commands,
        gates=gates,
        note=note,
        session_id=run.session_id,
    )
    _record(s, metrics.update_run_heartbeat, s.run_id, at)


def local_agent(cfg: Config) -> str:
    """The developer role's agent: the local model in f1 (D6's `local-<model>`)."""
    return cfg.agent_for("developer").id


# --- headless Claude, with usage-limit pauses ------------------------------------------


UNSURE_LIMIT_RETRIES = 3  # an error that only looks like a limit: pause, but not forever
# A lost connection, an overload, a server error: resume after these waits, then fail.
TRANSIENT_WAITS = (60, 300, 900)
RESUME_PROMPT = (
    "You were stopped by a Claude usage limit, which has now reset. Carry on with the same"
    " job from where you stopped; `git diff` shows the changes you had made."
)
PARTIAL_WORK_NOTE = (
    "\n\nA previous run of this job was stopped part-way by a Claude usage limit. The files"
    " it changed are still in the working tree: check `git diff` (and any new files) before"
    " you start, and build on them or undo them."
)
# A parked job (ADR 15 item 10), resumed after the reset: its changes were committed.
PARKED_PROMPT = (
    "You were stopped by a Claude usage limit, which has now reset. Carry on with the same job"
    " from where you stopped."
)
PARKED_NOTE = "\n\nAn earlier run of this job was stopped part-way by a Claude usage limit."


class Parked(Exception):
    """A Claude job stopped by a limit and parked instead of waiting (ADR 15 item 10): its work
    is committed on its branch, its session and ``resets_at`` are in state.json."""

    def __init__(self, resets_at: datetime) -> None:
        super().__init__(f"parked until {resets_at.isoformat()}")
        self.resets_at = resets_at


def _park(
    s: Session,
    job: JobSpec,
    name: str,
    milestone: str,
    agent: str,
    job_id: int | None,
    session: str | None,
    resets_at: datetime | None,
) -> NoReturn:
    """Park the job: its changes committed on its branch, its session kept for the resume, its
    ticket held until the reset (with none given, ``backoff_min`` from now)."""
    at = now()
    resets = resets_at or at + timedelta(seconds=s.cfg.backoff_min)
    branch = s.git.current_branch()
    kept = "" if branch == MAIN else branch
    if kept:
        s.git.commit_all(with_trailers(f"wip {name} (parked)", agent=CLAUDE_HEADLESS_AGENT))
    entry = {"session_id": session or "", "branch": kept}
    s.state.interrupted[job_key(job.role, name)] = {**entry, "cause": "limit"}
    s.state.parked[name] = {"kind": job.role, **entry, "resets_at": resets.isoformat()}
    s.state.in_flight = None
    s.state.count_run(milestone)
    save_state(s.state, s.state_path)
    if job_id is not None:
        _record(
            s, metrics.finish_job, job_id, ended=at.isoformat(), outcome="failed", note="parked"
        )
    s.report.claude_runs.append(
        ClaudeRunRecord(
            kind=job.role,
            subject=name,
            duration_s=0.0,
            tokens_in=0,
            tokens_out=0,
            cache_read=0,
            ok=False,
        )
    )
    s.log(console.paused(agent, f"Claude usage limit, {name} parked", resets, at))
    s.report.notes.append(f"Parked {name} ({job.role}) for a Claude usage limit.")
    raise Parked(resets)


def _record_readings(s: Session, agent: str, readings: tuple[Reading, ...]) -> None:
    """Claude's windows as its stream reported them (f1-44); a later reading of a window at
    the same moment replaces an earlier one, so writing them again changes nothing."""
    at = now().isoformat()
    for reading in readings:
        _record(
            s,
            metrics.add_usage_event,
            agent,
            at,
            "reading",
            window=reading.window,
            value=reading.utilization,
            resets_at=reading.resets_at.isoformat(),
        )


def _note_summary(notes: tuple[Path, ...]) -> str:
    """What a job's notes say it did: decision.json's outcome, then a note's first line."""
    parts = []
    for path in notes:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix == ".json":
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and data.get("outcome"):
                parts.append(str(data["outcome"]))
        elif line := console.first_line(text):
            parts.append(line)
    return " · ".join(parts)


NOTE_FILE = "note.md"  # a direction's or an escalation's process note, in the ticket's logs
PROCESS_NOTE_MAX = 2000  # chars: a note is 2-4 lines; more is cut


def _process_note(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    return path.read_text(encoding="utf-8", errors="replace").strip()[:PROCESS_NOTE_MAX] or None


def call_claude(
    s: Session,
    job: JobSpec,
    milestone: str,
    subject: str,
    *,
    ticket: str | None = None,
    notes: tuple[Path, ...] = (),
    park: bool = False,
    process_note: Path | None = None,
) -> JobResult:
    """Run a lead job on the agent its role names, waiting out usage limits. Each trigger
    bounds its own runs (ADR 12 item 10); the count per milestone is kept for the metrics.

    With ``park`` (a ticket's job), a certain limit parks it instead of waiting: ``Parked``
    is raised, and the queue goes on without Claude until the reset (ADR 15 item 10).

    A job stopped mid-way by a limit resumes its session after the reset (f1: lead tickets
    cost 0.5-1.5M, so a limit will land inside one); if the session can't be resumed, it
    starts again, told that its partial work is in the tree.

    Each job is a row in the metrics database, with ``ticket`` (None for a milestone-wide
    job), and has its own logs: a second escalation of a ticket doesn't overwrite the first's.

    On the console (f1-42): a start line, a progress line every ``PROGRESS_EVERY`` seconds,
    each pause with its resume time, and an end line with what the job did, from ``notes``
    (the files it writes) or else its answer's first line.

    While it runs, it is the in-flight job in state.json (ADR 15 item 11); a run of it that was
    interrupted resumes its session, told where its changes were kept.

    A direction or an escalation writes a ``process_note`` (ADR 14 item 13), kept as its job's
    note. A ticket's direction and escalation share its logs, so an earlier job's is removed
    first, unless this job resumes and may have written its own."""
    attempt = unsure = transient = 0
    resume: str | None = None
    interrupted = False
    resume_prompt, partial_note = RESUME_PROMPT, PARTIAL_WORK_NOTE
    if (earlier := s.state.interrupted.pop(job_key(job.role, ticket or subject), None)) is not None:
        kept = earlier["branch"]
        where = (
            ""
            if not kept
            else ON_THIS_BRANCH
            if kept == s.git.current_branch()
            else ON_ANOTHER_BRANCH.format(branch=kept, main=MAIN)
        )
        if earlier.get("cause") == "limit":
            resume_prompt, partial_note = PARKED_PROMPT + where, PARKED_NOTE + where
        else:
            resume_prompt, partial_note = INTERRUPTED_PROMPT + where, INTERRUPTED_NOTE + where
        resume = earlier["session_id"] or None
        interrupted = True
    elif process_note is not None:
        process_note.unlink(missing_ok=True)
    number = next_number(s, ticket, job.role)
    runner = s.cfg.agent_for(job.role)
    adapter, agent = adapter_for(runner.harness), runner.id
    what = job.role if ticket or subject == job.role else f"{job.role} {subject}"
    started = clock()
    s.log(console.start(agent, what))
    base = f"claude-{job.role}-{subject}" + (f"-{number}" if number > 1 else "")
    log = s.run_dir / f"{base}.log"
    job_id = s.last_job_id = record_start(
        s, ticket, milestone, job.role, agent, attempt=number, log_path=_rel(s, log)
    )
    _set_in_flight(
        s,
        kind=job.role,
        ticket=ticket,
        subject=subject,
        milestone=milestone,
        branch=s.git.current_branch(),
        agent=agent,
        job_id=job_id,
        session_id=resume,
    )
    while True:
        prompt = resume_prompt if resume else job.prompt + (partial_note if interrupted else "")
        resume_prompt = RESUME_PROMPT  # a later resume follows a pause for a limit
        log = s.run_dir / f"{base}{f'-retry{attempt}' if attempt else ''}.log"
        if attempt:
            s.log(console.resumed(agent, what))
        result = with_progress(
            partial(
                adapter.run,
                runner,
                replace(job, prompt=prompt, resume=resume),
                s.repo,
                log,
                now(),
            ),
            lambda elapsed: s.log(console.running(agent, what, elapsed)),
        )
        _record_readings(s, agent, result.readings)
        if result.error == TRANSIENT:
            if transient >= len(TRANSIENT_WAITS):
                s.report.notes.append(
                    f"{job.role} {subject}: failed {transient + 1} times on a passing error"
                    f" ({result.text}); treated as a failure."
                )
                break
            pause = TRANSIENT_WAITS[transient]
            transient += 1
            attempt += 1
            resume = result.session_id or resume
            interrupted = True
            _in_flight_session(s, resume)
            at = now()
            s.log(
                console.paused(
                    agent, f"interrupted ({result.text})", at + timedelta(seconds=pause), at
                )
            )
            time.sleep(pause)
            continue
        if (limit := result.refusal) is not None:  # a limit (ADR 15 item 12)
            if not limit.certain:
                unsure += 1
                if unsure > UNSURE_LIMIT_RETRIES:
                    s.report.notes.append(
                        f"{job.role} {subject}: failed {unsure} times with what looked like a"
                        " usage limit; treated as a failure."
                    )
                    break
            _record(
                s,
                metrics.add_usage_event,
                agent,
                now().isoformat(),
                "refusal",
                window=limit.window,
                resets_at=limit.resets_at.isoformat() if limit.resets_at else None,
            )
            if park and limit.certain:
                session = result.session_id or resume
                _park(s, job, ticket or subject, milestone, agent, job_id, session, limit.resets_at)
            # A known limit with no time: retry at the minimum, since a refused call costs
            # nothing and the exponential backoff overshot a 5 h window by hours (f1).
            wait = (
                max(60.0, (limit.resets_at - now()).total_seconds() + 60)
                if limit.resets_at
                else s.cfg.backoff_min
                if limit.certain
                else backoff_seconds(attempt, s.cfg.backoff_min, s.cfg.backoff_max)
            )
            attempt += 1
            resume = result.session_id or resume
            interrupted = True
            _in_flight_session(s, resume)
            at = now()
            resumes = at + timedelta(seconds=wait)
            s.state.paused_until = resumes.isoformat()
            save_state(s.state, s.state_path)
            why = "Claude usage limit" if limit.certain else "what looks like a Claude usage limit"
            s.log(console.paused(agent, why, resumes, at))
            s.report.notes.append(f"Paused {wait / 60:.0f} min for a Claude usage limit.")
            time.sleep(wait)
            continue
        if resume and not result.ok and result.num_turns == 0:
            resume = None  # the session couldn't be resumed: start again, told about the tree
            attempt += 1
            continue
        break
    s.state.paused_until = None
    s.state.in_flight = None
    s.state.count_run(milestone)
    save_state(s.state, s.state_path)
    if job_id is not None:
        _record(
            s,
            metrics.finish_job,
            job_id,
            ended=now().isoformat(),
            outcome="passed" if result.ok else "failed",
            tokens_in=result.usage.get("input_tokens", 0),
            tokens_cached=result.usage.get("cache_read_input_tokens", 0),
            tokens_out=result.usage.get("output_tokens", 0),
            cost_usd=result.cost_usd,
            note=_process_note(process_note),
            session_id=result.session_id,
            log_path=_rel(s, log),
        )
    s.report.claude_runs.append(
        ClaudeRunRecord(
            kind=job.role,
            subject=subject,
            duration_s=result.duration_s,
            tokens_in=result.usage.get("input_tokens", 0),
            tokens_out=result.usage.get("output_tokens", 0),
            cache_read=result.usage.get("cache_read_input_tokens", 0),
            ok=result.ok,
        )
    )
    s.log(console.claude_end(agent, what, result.ok, clock() - started, result.cost_usd))
    if line := console.summary(agent, _note_summary(notes) or result.text):
        s.log(line)
    return result


# --- one task ---------------------------------------------------------------------


def _check_context(s: Session) -> None:
    """Record the context LM Studio loaded, for the report. The owner sets it there, not here."""
    if s.context_checked:
        return
    s.context_checked = True
    loaded = s.context_limit = loaded_context_length(s.cfg.lm_base_url, s.cfg.lm_model)
    if loaded:
        s.report.notes.append(f"LM Studio loaded the model with {loaded:,} tokens of context.")


def _read_blocked(repo: Path) -> str | None:
    path = repo / BLOCKED_FILE
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    path.unlink()
    return text


def _prompt(
    task: Task,
    last: GateResult | None,
    *,
    timed_out: bool = False,
    direction: str = "",
    reset: str = "",
    earlier: Collection[str] = (),
) -> str:
    """The developer's prompt. A retry builds on the branch unless ``reset`` says why it was
    reset (`prompts.RESET`); a requeued ticket's first attempt lists the ``earlier`` run's
    files left on its branch."""
    if last is None:
        extra = prompts.EARLIER.format(files=", ".join(earlier)) if earlier else ""
        return prompts.local_prompt(task, extra)
    branch = prompts.RESET[reset] if reset else prompts.KEPT
    if direction:
        template, hint = prompts.DIRECTED, ""
    else:
        template = prompts.FRESH if reset else prompts.RETRY
        hint = HINTS.get(last.name, "")
    extra = template.format(
        gate=last.name, hint=hint, output=last.output, direction=direction, branch=branch
    )
    # After a reset there is nothing of the timed-out attempt left to keep
    return prompts.local_prompt(
        task, (prompts.TIMED_OUT if timed_out and not reset else "") + extra
    )


RESET_LINE = "reset: true"


def split_reset(direction: str) -> tuple[str, bool]:
    """A direction without its ``reset: true`` line, and whether it had one (ADR 15 item 7)."""
    lines = direction.splitlines()
    kept = [line for line in lines if line.strip().lower() != RESET_LINE]
    return "\n".join(kept).strip(), len(kept) != len(lines)


def _has_branch(git: Git, branch: str) -> bool:
    return bool(git.run("branch", "--list", branch).strip())


def _catch_up(s: Session, branch: str) -> bool:
    """Check out ``branch`` with main merged in, so it holds the latest tickets and code (a
    direction's repair, a requeue, other merges). False, back on main, if they clash."""
    s.git.checkout(branch)
    name, email = RUNNER_AUTHOR.removesuffix(">").split(" <")
    message = with_trailers(f"runner: merge {MAIN} into {branch}", agent=RUNNER_AGENT)
    try:
        s.git.run(
            *("-c", f"user.name={name}", "-c", f"user.email={email}"),
            *("merge", "-q", "--no-verify", "--no-edit", "-m", message, MAIN),
        )
    except GitError:
        s.git.run("merge", "--abort", check=False)
        s.git.checkout(MAIN)
        return False
    return True


def _start_attempt(s: Session, branch: str, reset: str) -> str:
    """Put the ticket's branch in place for its next attempt: its work so far, caught up with
    main, unless ``reset`` (why) asks for main itself. Returns why it was reset, if it was."""
    if not reset and _has_branch(s.git, branch):
        if _catch_up(s, branch):
            return ""
        reset = "conflict"
    s.git.fresh_branch(branch, MAIN)
    return reset


# Failures the gate output explains by itself; anything else earns the lead's direction.
MECHANICAL = ("ruff", "translations", NO_CHANGES)


def needs_direction(failures: list[str], timeouts: list[bool]) -> bool:
    """Whether the last attempt gets the lead's direction (ADR 12 item 6)."""
    if any(timeouts):
        return True
    if len(failures) >= 2 and failures[-1] == failures[-2]:
        return True
    return any(f not in MECHANICAL for f in failures)


def _save_thinking(rec: TaskRecord, logs: Path, repo: Path) -> list[str]:
    """Write the developer's thinking per attempt next to the logs; returns the files written."""
    written = []
    for attempt, session in enumerate(rec.sessions, start=1):
        text = session_reasoning(OPENCODE_DB, session)
        if text:
            path = logs / f"thinking-{attempt}.md"
            path.write_text(text + "\n", encoding="utf-8")
            written.append(path.relative_to(repo).as_posix())
    return written


def give_direction(s: Session, task: Task, rec: TaskRecord, logs: Path) -> tuple[Task, str]:
    """Before the last attempt, the lead reads the work and writes a short direction; it may
    repair the ticket instead. Returns the (maybe repaired) task and the direction.

    While Claude is limited it raises ``Parked`` instead, as does a limit during the direction:
    the ticket waits rather than going undirected (ADR 15 item 10). A parked direction isn't
    counted: its ticket gets it after the reset."""
    if ahead := _limits_ahead(s, now()):
        raise Parked(min(ahead))
    (logs / "last.diff").write_text(s.git.diff(MAIN), encoding="utf-8")
    rel = logs.relative_to(s.repo).as_posix()
    _save_thinking(rec, logs, s.repo)
    # Every attempt's, including a parked ticket's earlier ones
    thinking = sorted(p.relative_to(s.repo).as_posix() for p in logs.glob("thinking-*.md"))
    job = JobSpec(
        role="direction",
        prompt=prompts.DIRECTION.format(
            id=task.id,
            task=task.path.relative_to(s.repo).as_posix(),
            logs=rel,
            thinking=", ".join(thinking) or "not available",
            streak=rec.edit_streak,
            timeouts=rec.timeouts,
        ),
        timeout=s.cfg.claude_timeout,
        edit=("var/runs/**",),
        commands=GIT_READ_COMMANDS,
    )
    direction_file, ticket_file = logs / "direction.md", logs / "ticket.md"
    call_claude(
        s,
        job,
        task.milestone,
        task.id,
        ticket=task.id,
        notes=(direction_file,),
        park=True,
        process_note=logs / NOTE_FILE,
    )
    s.state.directions[task.id] = s.state.directions.get(task.id, 0) + 1
    save_state(s.state, s.state_path)
    direction = (
        direction_file.read_text(encoding="utf-8").strip() if direction_file.is_file() else ""
    )
    rec.directed = bool(direction)
    if ticket_file.is_file():
        s.git.checkout(MAIN)
        original = task.path.read_text(encoding="utf-8")
        task.path.write_text(ticket_file.read_text(encoding="utf-8"), encoding="utf-8")
        repaired = parse_task(task.path, s.cfg.default_max_diff)
        # f1-50: a repair naming a missing path fails the developer's all-tests gate
        if problems := preflight(repaired, s.repo):
            task.path.write_text(original, encoding="utf-8")
            s.log(f"direction {task.id}: repair dropped, pre-flight: {'; '.join(problems)}")
            return task, direction
        s.git.commit_all(
            with_trailers(
                f"direction {task.id}: ticket repaired (by Claude)", agent=CLAUDE_HEADLESS_AGENT
            )
        )
        task = repaired
        record_ticket(s, task.path, "running")
    return task, direction


def _park_direction(
    s: Session,
    task: Task,
    rec: TaskRecord,
    parked: Parked,
    branch: str,
    logs: Path,
    timeouts: list[bool],
    last: GateResult | None,
) -> None:
    """Hold a developer ticket at its direction until Claude's reset, with what its attempts
    left for the direction and the last attempt to read."""
    if task.id not in s.state.parked:  # parked before its direction ran: Claude was limited
        s.log(
            console.paused(
                RUNNER_AGENT, f"{task.id} waits for its direction", parked.resets_at, now()
            )
        )
        s.report.notes.append(f"Parked {task.id}: its direction waits for Claude's reset.")
    entry = s.state.parked.setdefault(
        task.id,
        {
            "kind": "direction",
            "branch": branch,
            "session_id": "",
            "resets_at": parked.resets_at.isoformat(),
        },
    )
    entry.update(
        logs=_rel(s, logs),
        gate=last.name if last else "",
        output=last.output if last else "",
        gate_failures=rec.gate_failures,
        timeouts=timeouts,
    )
    save_state(s.state, s.state_path)
    s.git.checkout(MAIN)
    rec.attempts -= 1  # the last attempt hasn't run
    rec.result = "parked"


def _finish_escalation(
    s: Session, task: Task, rec: TaskRecord, reason: str, logs: Path, detail: str = ""
) -> None:
    branch = f"task/{task.id}"
    if s.git.current_branch() == branch:
        (logs / "last.diff").write_text(s.git.diff(MAIN), encoding="utf-8")
        s.git.checkout(MAIN)
    target = s.tasks_dir("escalated") / task.path.name
    s.git.move(task.path, target)
    append_footer(
        target,
        {
            "result": "escalated",
            "reason": reason,
            "attempts": rec.attempts,
            "tokens": rec.tokens_in + rec.tokens_out,
            "logs": logs.relative_to(s.repo).as_posix(),
        },
    )
    runner_commit(
        s,
        messages.escalation_message(task.id, reason, detail, logs.relative_to(s.repo).as_posix()),
    )
    record_ticket(s, target)
    rec.note = reason
    where = f"logs in {logs.relative_to(s.repo).as_posix()}"
    s.log(console.stopped(task.id, "escalated", reason, where, waiting_behind(s, task.id)))


def waiting_behind(s: Session, task_id: str) -> int:
    """How many ready tickets wait, directly or not, on a stopped one."""
    return len(blocked_ids(load_dir(s.tasks_dir("ready"), s.cfg.default_max_diff), {task_id}))


def _logs_dir(run_dir: Path, task_id: str) -> Path:
    """A fresh log folder, so a requeued task's second run doesn't overwrite the first."""
    logs, n = run_dir / task_id, 1
    while logs.exists():
        n += 1
        logs = run_dir / f"{task_id}-run{n}"
    logs.mkdir(parents=True)
    return logs


def _tally(rec: TaskRecord, run: JobResult) -> None:
    rec.model_s += run.duration_s
    rec.tokens_in += _tokens_in(run)
    rec.tokens_out += _tokens_out(run)
    rec.steps += run.num_turns
    rec.sessions.append(run.session_id or "")
    rec.edit_streak = max(rec.edit_streak, run.edit_streak)
    rec.timeouts += run.timed_out


def _record_refusal(s: Session, agent: str, run: JobResult) -> None:
    """A cloud developer's refusal, for the allowance (ADR 15 item 2): its reset if it said."""
    if (limit := run.refusal) is None:
        return
    _record(
        s,
        metrics.add_usage_event,
        agent,
        now().isoformat(),
        "refusal",
        window=limit.window,
        resets_at=limit.resets_at.isoformat() if limit.resets_at else None,
    )
    sure = "a limit" if limit.certain else "an error that may be a limit"
    s.report.notes.append(f"{agent} refused a developer attempt ({sure}): {run.text[:200]}")


def _develop(
    s: Session,
    task: Task,
    rec: TaskRecord,
    role: str,
    attempt: int,
    what: str,
    prompt: str,
    logs: Path,
    branch: str,
    *,
    directed: bool,
) -> tuple[str, JobResult, int | None, int | None]:
    """One developer attempt, on the agents ``role`` lists in order. A refusal doesn't count
    (ADR 14 item 10): it is recorded and the same attempt reruns on the next agent; the last
    agent's result stands, a refusal included (f1-25's router replaces the list order). Only the
    local model is warmed up. Returns the agent, its result, its job row and its context limit.
    """
    s.cfg.agent_for(role)  # a role with no agent is a config error
    ids = s.cfg.roles[role]
    for n, agent_id in enumerate(ids, start=1):
        agent = s.cfg.agents[agent_id]
        if agent.harness != "opencode":
            raise RunnerError(f"{agent.id}: developer attempts run on OpenCode agents (f1-25)")
        local = is_local(agent)
        if local:
            rec.warmup_s += warmup(s.cfg.lm_base_url, s.cfg.lm_model, s.cfg.warmup_timeout)
            _check_context(s)
        context_limit = s.context_limit if local else None
        log = logs / (f"opencode-{attempt}.jsonl" if n == 1 else f"opencode-{attempt}-{n}.jsonl")
        s.log(console.start(agent.id, what + (" (directed)" if directed else "")))
        job_id = record_start(
            s,
            task.id,
            task.milestone,
            role,
            agent.id,
            attempt=next_number(s, task.id, "local"),
            log_path=_rel(s, log),
            context_limit=context_limit,
        )
        _set_in_flight(
            s,
            kind="local",
            ticket=task.id,
            branch=branch,
            agent=agent.id,
            job_id=job_id,
            attempt=attempt,
        )
        spec = JobSpec(
            role,
            prompt,
            s.cfg.opencode_timeout,
            edit=(ANY,),
            commands=CHECK_COMMANDS,
            title=f"{task.id} attempt {attempt}",
        )
        progress = partial(attempt_progress, s, agent.id, job_id, what, log, Ticker())
        run = OPENCODE.run(agent, spec, s.repo, log, now(), on_progress=progress)
        _tally(rec, run)
        if run.refusal is None:
            return agent.id, run, job_id, context_limit
        _record_refusal(s, agent.id, run)
        if n == len(ids):
            return agent.id, run, job_id, context_limit
        _attempt_end(s, agent.id, what, run, "refused, rerun on the next agent")
        _finish_attempt(s, job_id, run, "failed", note="refused", context_limit=context_limit)
    raise AssertionError("unreachable: the role names at least one agent")


def run_task(s: Session, task: Task) -> TaskRecord:
    """One ticket. Its result is "parked" when it waits for Claude: a limit, or the reserve."""
    rec = TaskRecord(id=task.id, milestone=task.milestone)
    held = s.state.parked.pop(task.id, None)
    if held is not None:
        save_state(s.state, s.state_path)
    # A direction parked for a limit goes on in the logs of the attempts it reads.
    directing = held if held is not None and held["kind"] == "direction" else None
    logs = rec.logs = s.repo / directing["logs"] if directing else _logs_dir(s.run_dir, task.id)
    s.ticket_started = clock()
    s.log("")
    s.log(console.ticket_header(task.id, task.agent, task.difficulty))
    s.log(task.goal)
    record_ticket(s, task.path, "running")

    problems = preflight(task, s.repo)
    if problems:
        (logs / "preflight.txt").write_text("\n".join(problems), encoding="utf-8")
        rec.result = "preflight"
        _finish_escalation(s, task, rec, "pre-flight failed", logs, "\n".join(problems))
        return rec

    if task.agent == "lead":
        if at_reserve(s, task):
            rec.result = "parked"
            return rec
        run_lead_task(s, task, rec)
        return rec

    branch = f"task/{task.id}"
    # Attempts an interruption cut off count as timed out; their work stays on the branch.
    cut_off = s.state.timed_out.pop(task.id, 0)
    if cut_off:
        save_state(s.state, s.state_path)
    protected = tuple(read_protected(s.repo))
    last = GateResult(INTERRUPTED_GATE, False, INTERRUPTED_OUTPUT) if cut_off else None
    timeouts = [True] * cut_off
    rec.attempts = rec.timeouts = cut_off
    if directing is not None:  # its attempts so far, then the direction it waited for
        last = GateResult(str(directing["gate"]), False, str(directing["output"]))
        timeouts = [bool(t) for t in directing["timeouts"]]
        rec.gate_failures = [str(g) for g in directing["gate_failures"]]
        rec.attempts, rec.timeouts = len(timeouts), sum(timeouts)
    # A requeued ticket continues the branch its escalation kept (ADR 15 item 7).
    resumed = not rec.attempts and _has_branch(s.git, branch)
    _start_attempt(s, branch, "")
    earlier = s.git.changed_files(MAIN) if resumed and s.git.current_branch() == branch else []
    direction = pending = ""
    for attempt in range(rec.attempts + 1, s.cfg.max_attempts + 1):
        rec.attempts = attempt
        reset, pending = pending, ""
        if (
            attempt == s.cfg.max_attempts
            and attempt > 1
            and s.state.directions.get(task.id, 0) < s.cfg.directions_per_task
            and needs_direction(rec.gate_failures, timeouts)
        ):
            try:
                task, direction = give_direction(s, task, rec, logs)
            except Parked as parked:
                _park_direction(s, task, rec, parked, branch, logs, timeouts, last)
                return rec
            direction, unusable = split_reset(direction)
            reset = "direction" if unusable else reset
        if reset or s.git.current_branch() != branch:  # a reset, or back from a repair on main
            reset = _start_attempt(s, branch, reset)
        what = f"attempt {attempt}/{s.cfg.max_attempts}"
        role = "last-attempt" if direction else "developer"
        prompt = _prompt(
            task,
            last,
            timed_out=bool(timeouts and timeouts[-1]),
            direction=direction,
            reset=reset,
            earlier=earlier,
        )
        agent, run, job_id, context_limit = _develop(
            s, task, rec, role, attempt, what, prompt, logs, branch, directed=bool(direction)
        )
        timeouts.append(run.timed_out)

        end = partial(_attempt_end, s, agent, what, run)
        finish = partial(_finish_attempt, s, job_id, run, context_limit=context_limit)
        blocked_text = _read_blocked(s.repo)
        if blocked_text is not None:
            (logs / f"BLOCKED-{attempt}.md").write_text(blocked_text, encoding="utf-8")
            category = parse_blocked(blocked_text) or "invalid"
            if category == "unrelated-problem":
                s.report.notes.append(f"{task.id} reported an unrelated problem (see logs).")
            else:
                end(f"stopped, BLOCKED: {category}")
                finish("failed", note=f"BLOCKED: {category}")
                rec.blocked = category
                rec.result = "blocked"
                local_wip_commit(s, f"wip {task.id} attempt {attempt} (blocked)")
                _finish_escalation(s, task, rec, f"BLOCKED: {category}", logs, blocked_text)
                return rec

        edited = local_wip_commit(s, f"wip {task.id} attempt {attempt}")
        if run.timed_out and not edited:  # its work so far is judged unusable (ADR 15 item 7)
            pending = "timeout"
        started = time.monotonic()
        if s.git.changed_files(MAIN):
            context = GateContext(s.repo, s.git, task, MAIN, protected, s.cfg.gate_timeout)
            results = run_gates(context)
        else:
            # An untouched tree passes every gate, and there'd be nothing to merge (m4-06).
            cause = empty_cause(run.refused_commands, run.timed_out)
            results = [
                GateResult(
                    NO_CHANGES, False, "The attempt changed no file. " + prompts.EMPTY[cause]
                )
            ]
        rec.gates_s += time.monotonic() - started
        gates_log = logs / f"gates-{attempt}.txt"
        gates_log.write_text(
            "\n\n".join(f"## {r.name}: {'ok' if r.ok else 'FAIL'}\n{r.output}" for r in results),
            encoding="utf-8",
        )
        failed = next((r for r in results if not r.ok), None)
        finish(
            "passed" if failed is None else "timeout" if run.timed_out else "failed",
            gates=[
                {
                    "name": r.name,
                    "ok": r.ok,
                    "seconds": round(r.seconds, 1),
                    "log": _rel(s, gates_log),
                }
                for r in results
            ],
        )
        if failed is None:
            end("passed")
            _merge(s, task, rec)
            return rec
        end(("timed out, " if run.timed_out else "") + f"failed gate {failed.name}")
        if run.timed_out:
            s.report.notes.append(f"{task.id} attempt {attempt}: OpenCode timed out.")
        rec.gate_failures.append(failed.name)
        last = failed

    rec.result = "escalated"
    _finish_escalation(
        s,
        task,
        rec,
        f"gates failed {rec.attempts}x (last: {last.name if last else '?'})",
        logs,
        last.output if last else "",
    )
    return rec


def _merge(s: Session, task: Task, rec: TaskRecord) -> None:
    branch = f"task/{task.id}"
    changes = s.git.numstat(MAIN)
    changed = s.git.changed_files(MAIN)
    rec.outside_files = outside_allowed(changed, (*task.files, *task.tests))
    rec.changed_tests = [f for f in changed if is_test_file(f) and s.git.exists_at(MAIN, f)]
    rec.commit = s.git.squash_merge(
        branch,
        MAIN,
        with_trailers(
            messages.merge_message(task, rec, s.cfg.lm_model, changes),
            agent=LOCAL_MODEL_AGENT,
            task=task.id,
            model=s.cfg.lm_model,
            attempts=str(rec.attempts),
        ),
        author=LOCAL_MODEL_AUTHOR,
    )
    target = s.tasks_dir("done") / task.path.name
    s.git.move(task.path, target)
    append_footer(
        target,
        {
            "result": "done",
            "attempts": rec.attempts,
            "duration_s": round(rec.model_s + rec.gates_s),
            "gate_failures": rec.gate_failures or "[]",
            "tokens": rec.tokens_in + rec.tokens_out,
        },
    )
    runner_commit(s, messages.done_message(task.id, rec))
    record_ticket(s, target, merged_by=local_agent(s.cfg), commit=rec.commit)
    rate_finished(s, task.id)
    s.git.run("branch", "-D", branch)
    rec.result = "done"
    _merged_line(s, local_agent(s.cfg), task.id, rec)


def _merged_line(s: Session, agent: str, task_id: str, rec: TaskRecord) -> None:
    lines = s.git.commit_size(rec.commit) if rec.commit else None
    s.log(console.merged(agent, task_id, rec.attempts, lines, clock() - s.ticket_started))


# --- lead tickets (ADR 12 item 9) --------------------------------------------------------


def _check_all(s: Session, task_id: str | None, logs: Path, name: str) -> bool:
    results = checks.check_all(s.repo, s.cfg.gate_timeout, task_id=task_id)
    (logs / name).write_text(checks.render(results), encoding="utf-8")
    return all(r.ok for r in results)


def block(s: Session, task_path: Path, reason: str) -> None:
    """Move a task to blocked/ with its reason; its dependants pause (ADR 12 item 10)."""
    target = s.tasks_dir("blocked") / task_path.name
    s.git.move(task_path, target)
    append_footer(target, {"result": "blocked", "reason": reason})
    runner_commit(s, f"runner: {task_path.stem} blocked: {reason}")
    record_ticket(s, target)
    rate_finished(s, task_path.stem)
    s.report.notes.append(f"Blocked {task_path.stem}: {reason}")
    where = f"ticket in {target.relative_to(s.repo).as_posix()}"
    s.log(console.stopped(task_path.stem, "blocked", reason, where, waiting_behind(s, target.stem)))


def run_lead_task(s: Session, task: Task, rec: TaskRecord) -> None:
    """The lead's own ticket, as a headless job on its branch; merged only if check-all
    passes. A lead ticket that fails is blocked: there's no one above the lead but the owner."""
    logs = rec.logs or _logs_dir(s.run_dir, task.id)
    branch = f"task/{task.id}"
    parked = s.state.interrupted.get(job_key("lead-ticket", task.id))
    if parked and parked["branch"] == branch:
        s.git.checkout(branch)  # an interrupted run's work, which its session resumes
    else:
        s.git.fresh_branch(branch, MAIN)
    rec.attempts = 1
    job = JobSpec(
        role="lead-ticket",
        prompt=prompts.LEAD_TICKET.format(
            id=task.id, task=task.path.relative_to(s.repo).as_posix()
        ),
        timeout=s.cfg.claude_timeout,
        edit=(ANY,),
        commands=(*CHECK_COMMANDS, *GIT_READ_COMMANDS, *task.commands),
    )
    try:
        call_claude(s, job, task.milestone, task.id, ticket=task.id, park=True)
    except Parked:
        s.git.checkout(MAIN)
        rec.result = "parked"
        return
    s.git.commit_all(with_trailers(f"wip {task.id} (lead)", agent=CLAUDE_HEADLESS_AGENT))
    if not s.git.changed_files(MAIN):  # an interrupted run's commit counts too
        s.git.checkout(MAIN)
        rec.result = "stopped"
        block(s, task.path, "the lead ticket changed nothing")
        return
    if not _check_all(s, task.id, logs, "check-all.txt"):
        s.git.checkout(MAIN)
        rec.result = "stopped"
        block(s, task.path, f"check-all failed; the work is on {branch}")
        return
    rec.commit = s.git.squash_merge(
        branch,
        MAIN,
        with_trailers(f"{task.id}: {task.goal}", agent=CLAUDE_HEADLESS_AGENT, task=task.id),
    )
    target = s.tasks_dir("done") / task.path.name
    s.git.move(task.path, target)
    append_footer(target, {"result": "done", "agent": "lead", "attempts": 1})
    runner_commit(s, messages.done_message(task.id, rec))
    lead = s.cfg.agent_for(job.role).id
    record_ticket(s, target, merged_by=lead, commit=rec.commit)
    rate_finished(s, task.id)
    s.git.run("branch", "-D", branch)
    rec.result = "done"
    _merged_line(s, lead, task.id, rec)


# --- checkpoints (ADR 12 item 8) ------------------------------------------------------


def note_merge(s: Session, task: Task, rec: TaskRecord) -> None:
    """Count a developer merge; every ``checkpoint_every`` of them, run a checkpoint."""
    if rec.result != "done" or task.agent != "developer":
        return
    s.state.unchecked.append(f"{task.id} {rec.commit}")
    save_state(s.state, s.state_path)
    # While Claude is limited, the checkpoint waits for a merge after the reset (ADR 15 item 10).
    if len(s.state.unchecked) >= s.cfg.checkpoint_every and not _limits_ahead(s, now()):
        checkpoint(s, task.milestone)


def _ticket_id(conn: sqlite3.Connection, project_id: int, ticket: str) -> int | None:
    """A ticket's row, if it has one: a finding naming a ticket never adds one."""
    row = conn.execute(
        "SELECT id FROM tickets WHERE project_id = ? AND ticket = ?", (project_id, ticket)
    ).fetchone()
    return int(row[0]) if row else None


def record_findings(
    s: Session, milestone: str, findings: Iterable[Finding], agent: str, prefix: str = ""
) -> None:
    """Findings on the last Claude job, keyed by ``prefix`` and their ids (ADR 14 item 13)."""
    if s.project_id is None:
        return
    milestone_id = _record(s, metrics.upsert_milestone, s.project_id, milestone)
    if milestone_id is None:
        return
    for finding in findings:
        ticket_id = _record(s, _ticket_id, s.project_id, finding.ticket) if finding.ticket else None
        _record(
            s,
            metrics.add_finding,
            milestone_id,
            prefix + finding.id,
            job_id=s.last_job_id,
            ticket_id=ticket_id,
            severity=finding.severity,
            route=finding.route,
            file=finding.file or None,
            line=finding.line,
            summary=finding.summary,
            detail=finding.detail or None,
            resolved=finding.resolved,
            agent=agent,
        )


# --- ratings (ADR 14 items 6–7, ADR 15 item 9; runner/ratings.py) ---------------------------

# Jobs that attempt a ticket; a refused or parked one isn't an attempt (ADR 14 item 10).
_ATTEMPT_ROLES = ("developer", "last-attempt", "lead-ticket")
REPLAYED = ("m1", "m2", "m3", "m4")  # the local model's history before ratings (ADR 14 item 7)


def starting_ratings(cfg: Config) -> dict[str, float]:
    """Each agent's estimate in `[agents.*] rating`, where its rating starts."""
    return {agent.id: float(agent.rating) for agent in cfg.agents.values()}


def standing(
    conn: sqlite3.Connection, start: Mapping[str, float]
) -> tuple[dict[str, float], dict[str, set[str]]]:
    """Each agent's rating now (its latest change, else its start) and the tickets it was
    rated on. Only agents with a start are rated."""
    current, played = dict(start), dict[str, set[str]]()
    rows = conn.execute(
        "SELECT r.agent, r.after, t.ticket FROM rating_changes r"
        " LEFT JOIN tickets t ON t.id = r.ticket_id ORDER BY r.at, r.id"
    )
    for row in rows:
        if row["agent"] in current:
            current[row["agent"]] = float(row["after"])
        if row["ticket"]:
            played.setdefault(row["agent"], set()).add(row["ticket"])
    return current, played


def _attempts(
    conn: sqlite3.Connection, ticket_id: int, merged_by: str | None
) -> list[ratings.Attempt]:
    """A ticket's attempts in order. A merged ticket's last attempt merged if it passed;
    otherwise the merger (an escalation that finished or implemented it) is one more."""
    marks = ", ".join("?" for _ in _ATTEMPT_ROLES)
    rows = conn.execute(
        f"SELECT agent, outcome FROM jobs WHERE ticket_id = ? AND role IN ({marks})"  # noqa: S608
        " AND outcome NOT IN ('running', 'interrupted', 'refused')"
        " AND ifnull(note, '') NOT IN ('refused', 'parked') ORDER BY started, id",
        (ticket_id, *_ATTEMPT_ROLES),
    ).fetchall()
    attempts = [ratings.Attempt(row["agent"]) for row in rows]
    if merged_by is None:
        return attempts
    if rows and rows[-1]["outcome"] == "passed":
        attempts[-1] = ratings.Attempt(rows[-1]["agent"], merged=True)
    else:
        attempts.append(ratings.Attempt(merged_by, merged=True))
    return attempts


def _write_changes(
    conn: sqlite3.Connection, changes: list[ratings.Change], ids: Mapping[str, int], at: datetime
) -> None:
    for change, moment in zip(changes, ratings.moments(at, len(changes)), strict=True):
        metrics.add_rating_change(
            conn,
            change.agent,
            change.skill,
            change.before,
            change.after,
            at=moment,
            ticket_id=ids[change.ticket],
            result=change.label,
        )


def rate_ticket(
    conn: sqlite3.Connection,
    project_id: int,
    ticket: str,
    start: Mapping[str, float],
    at: datetime,
) -> None:
    """A merged or blocked ticket's coding games, once. A ticket with no difficulty isn't
    rated: there's nothing to play against."""
    row = conn.execute(
        "SELECT id, coalesce(difficulty_corrected, difficulty) AS difficulty, merged_by"
        " FROM tickets WHERE project_id = ? AND ticket = ?",
        (project_id, ticket),
    ).fetchone()
    if row is None or row["difficulty"] is None:
        return
    labels = ", ".join("?" for _ in ratings.TICKET_LABELS)
    rated = conn.execute(
        f"SELECT 1 FROM rating_changes WHERE ticket_id = ? AND result IN ({labels})",  # noqa: S608
        (row["id"], *ratings.TICKET_LABELS),
    ).fetchone()
    if rated:
        return
    attempts = _attempts(conn, row["id"], row["merged_by"])
    games = ratings.ticket_games(ticket, row["difficulty"], attempts)
    current, played = standing(conn, start)
    _write_changes(conn, ratings.rate(current, played, games), {ticket: row["id"]}, at)


def rate_verdicts(
    conn: sqlite3.Connection,
    project_id: int,
    milestone: str,
    start: Mapping[str, float],
    checkpoint: str | None,
    at: datetime,
) -> None:
    """The final review's verdicts on the milestone's findings, each once: a game for the
    reviewer (``checkpoint`` for a missed one) and a quarter off the author of the code."""
    rows = conn.execute(
        "SELECT f.key, f.verdict, f.agent, t.id AS ticket_id, t.ticket, t.merged_by,"
        " coalesce(t.difficulty_corrected, t.difficulty) AS difficulty FROM findings f"
        " JOIN milestones m ON m.id = f.milestone_id JOIN tickets t ON t.id = f.ticket_id"
        " WHERE m.project_id = ? AND m.key = ? AND f.verdict IS NOT NULL ORDER BY f.id",
        (project_id, milestone),
    ).fetchall()
    ids = {row["ticket"]: row["ticket_id"] for row in rows}
    marks = ", ".join("?" for _ in ids)
    done = {
        result.split(" ", 1)[1]
        for (result,) in conn.execute(
            f"SELECT result FROM rating_changes WHERE ticket_id IN ({marks})"  # noqa: S608
            " AND result LIKE '% %'",
            list(ids.values()),
        )
    }
    judged = [
        ratings.Judged(
            row["key"],
            row["ticket"],
            row["difficulty"],
            row["verdict"],
            checkpoint if row["verdict"] == "missed" else row["agent"],
            row["merged_by"],
        )
        for row in rows
        if row["key"] not in done
    ]
    current, played = standing(conn, start)
    _write_changes(conn, ratings.rate(current, played, ratings.judged_games(judged)), ids, at)


def replay_ratings(
    conn: sqlite3.Connection, project_id: int, agent: str, start: float
) -> list[ratings.Change]:
    """Seed ``agent``'s rating from its M1–M4 tickets, from ``start`` in merge order (a
    ticket's last job), each change at its ticket's merge: a second replay rewrites the same
    rows."""
    rows = conn.execute(
        "SELECT t.id, t.ticket, t.merged_by, coalesce(t.difficulty_corrected, t.difficulty)"
        " AS difficulty, max(coalesce(j.ended, j.started)) AS merged_at FROM tickets t"
        " JOIN milestones m ON m.id = t.milestone_id JOIN jobs j ON j.ticket_id = t.id"
        " WHERE t.project_id = ? AND m.key IN (SELECT value FROM json_each(?))"
        " AND coalesce(t.difficulty_corrected, t.difficulty) IS NOT NULL"
        " GROUP BY t.id HAVING sum(j.agent = ?) > 0 ORDER BY merged_at, t.id",
        (project_id, json.dumps(REPLAYED), agent),
    ).fetchall()
    games, times, ids = [], {}, {}
    last: datetime | None = None
    for row in rows:
        merged = datetime.fromisoformat(row["merged_at"])
        last = merged if last is None or merged > last else last + timedelta(microseconds=1)
        times[row["ticket"]], ids[row["ticket"]] = last, row["id"]
        attempts = _attempts(conn, row["id"], row["merged_by"])
        ticket = ratings.ticket_games(row["ticket"], row["difficulty"], attempts)
        games += [game for game in ticket if game.agent == agent]
    changes = ratings.rate({agent: start}, {}, games)
    for change in changes:
        _write_changes(conn, [change], ids, times[change.ticket])
    return changes


def rate_finished(s: Session, ticket: str) -> None:
    """Rate a ticket that was merged or blocked (best effort, like every metrics write)."""
    if s.project_id is not None:
        _record(s, rate_ticket, s.project_id, ticket, starting_ratings(s.cfg), now())


def checkpoint(s: Session, milestone: str) -> None:
    merged = list(s.state.unchecked)
    out = s.run_dir / f"checkpoint-{len(s.report.claude_runs) + 1}.md"
    findings_out = out.with_suffix(".json")
    job = JobSpec(
        role="checkpoint",
        prompt=prompts.CHECKPOINT.format(
            merges="\n".join(f"- {m.split()[0]}: `git show {m.split()[1]}`" for m in merged),
            out=out.relative_to(s.repo).as_posix(),
            findings=findings_out.relative_to(s.repo).as_posix(),
        ),
        timeout=s.cfg.claude_timeout,
        edit=("tasks/ready/**", "docs/agents/developer.md", "var/runs/**"),
        # pytest: the tickets' pre-flight test; its commit skips the hook
        commands=(*GIT_READ_COMMANDS, "uv run pytest"),
    )
    s.log("")
    s.log(console.ticket_header(f"{milestone} checkpoint", "lead", None))
    s.log("Review the last merges: " + ", ".join(m.split()[0] for m in merged))
    call_claude(s, job, milestone, "checkpoint", notes=(out,))
    s.state.unchecked = []
    save_state(s.state, s.state_path)
    if out.is_file():
        s.report.notes.append("Checkpoint: " + out.read_text(encoding="utf-8").strip())
    try:
        findings = parse_checkpoint(findings_out)
    except ReviewFileError as exc:
        s.report.notes.append(f"Checkpoint findings unusable: {exc}")
    else:
        # Keyed by the checkpoint's job, unique in the milestone (the review judges them)
        if s.last_job_id is not None:
            prefix = f"{milestone}-C{s.last_job_id}-"
            record_findings(s, milestone, findings, s.cfg.agent_for(job.role).id, prefix)
    s.git.commit_all(
        with_trailers(
            "checkpoint after " + ", ".join(m.split()[0] for m in merged) + " (by Claude)",
            agent=CLAUDE_HEADLESS_AGENT,
        )
    )


# --- escalation handling ------------------------------------------------------------


def _only_docs_and_tasks(s: Session) -> bool:
    changed = [line[3:] for line in s.git.run("status", "--porcelain").splitlines()]
    return checks.hook_can_skip(changed) or not changed


def handle_escalation(s: Session, task: Task, logs: Path, reason: str) -> None:
    escalated = s.tasks_dir("escalated") / task.path.name
    used = s.state.escalations.get(task.id, 0)
    if used >= s.cfg.escalations_per_task:
        block(s, escalated, f"{used} escalations used; last: {reason}")
        return
    s.state.escalations[task.id] = used + 1
    save_state(s.state, s.state_path)
    branch = f"task/{task.id}"
    # The branch gets main (the escalated ticket, newer code), for a lead that finishes it.
    if _has_branch(s.git, branch) and _catch_up(s, branch):
        s.git.checkout(MAIN)
    rec_sessions = [p for p in sorted(logs.glob("thinking-*.md"))]
    job = JobSpec(
        role="escalation",
        prompt=prompts.ESCALATION.format(
            id=task.id,
            reason=reason,
            logs=logs.relative_to(s.repo).as_posix(),
            thinking=", ".join(p.relative_to(s.repo).as_posix() for p in rec_sessions)
            or "not available",
        ),
        timeout=s.cfg.claude_timeout,
        edit=(ANY,),
        # `finish` checks out the ticket's branch itself: only that one (ADR 15 item 8)
        commands=(*CHECK_COMMANDS, *GIT_READ_COMMANDS, f"git checkout {branch}"),
    )
    decision_path = logs / "decision.json"
    call_claude(
        s,
        job,
        task.milestone,
        task.id,
        ticket=task.id,
        notes=(decision_path, logs / "escalation.md"),
        process_note=logs / NOTE_FILE,
    )
    try:
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        decision = {}
    outcome = decision.get("outcome")
    on = s.git.current_branch()
    if outcome == "finish" or on != MAIN:
        _finish_branch(s, task, logs, job, outcome, on)
        return
    # Its work reaches main only if every check passes (ADR 12 item 11).
    if not _only_docs_and_tasks(s) and not _check_all(s, None, logs, "check-all.txt"):
        branch = f"escalation/{task.id}"
        s.git.run("checkout", "-q", "-B", branch)
        s.git.commit_all(
            with_trailers(f"escalation {task.id}: failed check-all", agent=CLAUDE_HEADLESS_AGENT)
        )
        s.git.checkout(MAIN)
        block(s, escalated, f"the escalation's work failed check-all; it is on {branch}")
        return
    if outcome == "requeue":
        requeued = s.tasks_dir("ready") / task.path.name
        if requeued.is_file():
            carry_footers(escalated, requeued)
        s.git.run("rm", "-q", str(escalated.relative_to(s.repo)))
        # Its next run builds on the branch, unless the lead found the work unusable
        if decision.get("reset") is True and _has_branch(s.git, branch):
            s.git.run("branch", "-D", branch)
    elif outcome == "implemented":
        s.git.move(escalated, s.tasks_dir("done") / task.path.name)
    elif outcome == "owner":
        s.state.owner[task.id] = {
            "adr": str(decision.get("adr", "")),
            "question": str(decision.get("question", "")),
        }
        save_state(s.state, s.state_path)
    notes = logs / "escalation.md"
    if notes.is_file():
        s.report.notes.append(f"Escalation {task.id} ({outcome}): " + notes.read_text().strip())
    s.git.commit_all(
        with_trailers(
            f"escalation {task.id}: {outcome or 'no decision'} (by Claude)",
            agent=CLAUDE_HEADLESS_AGENT,
        )
    )
    done = s.tasks_dir("done") / task.path.name
    if outcome == "implemented" and done.is_file():
        record_ticket(s, done, merged_by=s.cfg.agent_for(job.role).id, commit=s.git.head())
        rate_finished(s, task.id)
    elif outcome == "requeue" and (s.tasks_dir("ready") / task.path.name).is_file():
        record_ticket(s, s.tasks_dir("ready") / task.path.name)


def _finish_branch(
    s: Session, task: Task, logs: Path, job: JobSpec, outcome: str | None, on: str
) -> None:
    """An escalation that finished the developer's work on ``task/<id>`` (ADR 15 item 8):
    squash-merged as `_merge` does once `check-all --task` passes, crediting the lead (who
    merged it) and the developer (a trailer). Anything else off main is kept and blocked."""
    branch = f"task/{task.id}"
    escalated = s.tasks_dir("escalated") / task.path.name
    if on == MAIN:  # "finish" without checking the branch out: its edits stay off main
        on = f"escalation/{task.id}"
        s.git.run("checkout", "-q", "-B", on)
    s.git.commit_all(
        with_trailers(
            f"escalation {task.id}: {outcome or 'no decision'} (by Claude)",
            agent=CLAUDE_HEADLESS_AGENT,
        )
    )
    why = ""
    if outcome != "finish" or on != branch:
        why = f"the escalation answered {outcome or 'nothing'} on {on}, not finish on {branch}"
    elif not s.git.changed_files(MAIN):
        why = f"the finished {branch} changes nothing"
    elif not _check_all(s, task.id, logs, "check-all.txt"):
        why = "the finished work failed check-all"
    if why:
        s.git.checkout(MAIN)
        block(s, escalated, f"{why}; its work is on {on}")
        return
    changes = s.git.numstat(MAIN)
    commit = s.git.squash_merge(
        branch,
        MAIN,
        with_trailers(
            messages.finish_message(task, s.cfg.lm_model, changes),
            agent=CLAUDE_HEADLESS_AGENT,
            developer=LOCAL_MODEL_AGENT,
            task=task.id,
            model=s.cfg.lm_model,
        ),
    )
    target = s.tasks_dir("done") / task.path.name
    s.git.move(escalated, target)
    append_footer(target, {"result": "done", "finished_by": "lead"})
    notes = logs / "escalation.md"
    if notes.is_file():
        s.report.notes.append(f"Escalation {task.id} (finish): " + notes.read_text().strip())
    runner_commit(s, f"runner: {task.id} done, finished by the lead, merged as {commit[:9]}")
    merger = s.cfg.agent_for(job.role).id
    record_ticket(s, target, merged_by=merger, commit=commit)
    rate_finished(s, task.id)
    s.git.run("branch", "-D", branch)
    lines = s.git.commit_size(commit)
    s.log(console.merged(merger, task.id, 1, lines, clock() - s.ticket_started))  # its one job


# --- parking and the reserve (ADR 15 items 4, 5 and 10) --------------------------------


@dataclass
class ReserveAnswer:
    """The owner's answer to the reserve question, for the running command only (the owner,
    2026-10-01): kept in memory, never in state.json. cli's self-restart hands a yes on
    through ``RESERVE_ENV``; a new command asks again."""

    yes: bool = False
    no: bool = False  # no answer, or no: later lead tickets wait without asking again


RESERVE = ReserveAnswer()
RESERVE_ENV = "COUCOU_RUNNER_RESERVE_YES"  # set only by cli's restart after a yes
CLAUDE = "claude"
# Where Claude's week stands now decides the question: a lead ticket's share of the week
# isn't learned yet, so its expected cost is left at 0.
LEAD_COST = 0.0


def read_answer(timeout: float) -> str | None:
    """A line the owner types within ``timeout`` seconds; None with no terminal or no answer."""
    if not sys.stdin.isatty():
        return None
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    return sys.stdin.readline().strip() if ready else None


def _resets(entry: dict[str, Any]) -> datetime:
    return datetime.fromisoformat(str(entry["resets_at"]))


def _limits_ahead(
    s: Session, at: datetime, tickets: Collection[str] | None = None
) -> list[datetime]:
    """The resets still ahead of the jobs parked for a limit (of ``tickets``, if given): while
    there is one, Claude is limited and only local work runs."""
    return [
        _resets(entry)
        for ticket, entry in s.state.parked.items()
        if entry["kind"] != "reserve"
        and (tickets is None or ticket in tickets)
        and _resets(entry) > at
    ]


def claude_windows(s: Session, at: datetime) -> list[allowance.Window]:
    """Claude's windows from its latest readings (f1-44): capacity 1, usage the share read. A
    window whose reset has passed since is left out: its reading is stale."""
    windows = []
    for name, row in (_record(s, metrics.latest_readings, "claude-") or {}).items():
        if name not in allowance.NAMED or row["value"] is None or not row["resets_at"]:
            continue
        resets = datetime.fromisoformat(row["resets_at"])
        if resets <= at:
            continue
        kind, length = allowance.NAMED[name]
        reserve = s.cfg.claude_reserve if name == "seven_day" else 0.0
        windows.append(
            allowance.Window(
                name, kind, length, resets, 1.0, float(row["value"]), reserve, measured=True
            )
        )
    return windows


def _at_the_reserve(s: Session, at: datetime) -> tuple[str, datetime] | None:
    """``("21% of the week left, resets Mon 5 Oct 16:00", reset)`` when a lead ticket is
    refused only because it would dip into Claude's reserve; else None."""
    windows = claude_windows(s, at)
    if not allowance.reserve_only(CLAUDE, windows, LEAD_COST, at):
        return None
    week = next((w for w in windows if w.reserve), None)
    if week is None or week.resets_at is None:
        return None
    resets = week.resets_at.astimezone(at.tzinfo)
    left = f"{1 - week.used:.0%} of the week left"
    return f"{left}, resets {resets:%a} {resets.day} {resets:%b %H:%M}", resets


def at_reserve(s: Session, task: Task) -> bool:
    """Before a lead ticket: whether it waits for Claude's reserve (ADR 15 item 5). The owner
    is asked once per command, and only when nothing else can run (`_next_task`), so the
    question waits for an answer until the week resets (the owner, 2026-10-01). With no yes,
    the ticket is parked and becomes an owner item. Support roles never ask: they may always
    use the reserve."""
    at = now()
    found = None if RESERVE.yes else _at_the_reserve(s, at)
    if found is None:
        return False
    where, resets = found
    if not RESERVE.no:
        s.log(
            f"? [{RUNNER_AGENT}] Claude is at its reserve ({where})."
            " Use it for the rest of this run? [y/N]"
        )
        answer = read_answer(max(60.0, (resets - at).total_seconds() + 60))
        if answer is not None and answer.lower() in ("y", "yes"):
            RESERVE.yes = True
            s.log(f"✔ [{RUNNER_AGENT}] Claude's reserve is used for the rest of this run")
            return False
        if answer is None and _at_the_reserve(s, now()) is None:
            return False  # the week reset while it waited: no reserve to ask about
        RESERVE.no = True
    text = f"{task.id} waits for Claude's reserve ({where}): rerun and answer y to use it"
    s.state.parked[task.id] = {
        "kind": "reserve",
        "branch": "",
        "session_id": "",
        "resets_at": resets.isoformat(),
        "text": text,
    }
    save_state(s.state, s.state_path)
    if s.project_id is not None:
        _record(
            s,
            metrics.upsert_owner_item,
            s.project_id,
            "reserve",
            task.id,
            text=text,
            command=f"uv run runner milestone {command_arg(task.milestone)}",
            created=at.isoformat(),
        )
    s.report.notes.append(text)
    reason = f"Claude is at its reserve ({where})"
    s.log(console.stopped(task.id, "parked", reason, "asks you", waiting_behind(s, task.id)))
    return True


def _next_task(s: Session, ready: list[Task], done: set[str], paused: set[str]) -> Task | None:
    """Parked tickets whose reset has passed go first; while Claude is limited, only work that
    needs no Claude: developer tickets, which local takes. At Claude's reserve, developer
    tickets go before lead ones, so the reserve question comes only when nothing else can run
    (ADR 15 item 5)."""
    at = now()
    held = {t.id for t in ready if t.id in s.state.parked}
    due = [t for t in ready if t.id in held and _resets(s.state.parked[t.id]) <= at]
    if (task := pick_next(due, done, paused)) is not None:
        return task
    limited = bool(_limits_ahead(s, at))
    free = [t for t in ready if t.id not in held and not (limited and t.agent != "developer")]
    task = pick_next(free, done, paused)
    if task is None or task.agent != "lead" or RESERVE.yes or RESERVE.no:
        return task
    if _at_the_reserve(s, at) is None:
        return task
    developers = pick_next([t for t in free if t.agent != "lead"], done, paused)
    return developers or task


def _wait_for_reset(s: Session, ready: list[Task]) -> bool:
    """With nothing runnable left, sleep until the earliest reset a parked ticket waits for.
    False when none does: a ticket parked at the reserve waits for the owner, not the week."""
    at = now()
    ahead = _limits_ahead(s, at, {t.id for t in ready})
    if not ahead:
        return False
    wait = max(60.0, (min(ahead) - at).total_seconds() + 60)
    resumes = at + timedelta(seconds=wait)
    s.state.paused_until = resumes.isoformat()
    save_state(s.state, s.state_path)
    s.log(console.paused(RUNNER_AGENT, "nothing to run without Claude", resumes, at))
    s.report.notes.append(
        f"Paused {wait / 60:.0f} min for a Claude usage limit, with nothing to run."
    )
    time.sleep(wait)
    s.state.paused_until = None
    save_state(s.state, s.state_path)
    return True


# --- the session ------------------------------------------------------------------


def _runner_code(repo: Path) -> str:
    """A fingerprint of the runner's source, to notice an escalation changing it."""
    digest = hashlib.sha256()
    for path in sorted((repo / "runner").rglob("*.py")):
        digest.update(path.as_posix().encode() + b"\0" + path.read_bytes())
    return digest.hexdigest()


RESTART_NOTE = (
    "Stopped: Claude changed runner/ (a lead ticket or an escalation), "
    "so the runner needs a fresh process."
)


def work_queue(
    s: Session, *, milestone: str | None = None, escalate: bool = True, once: bool = False
) -> bool:
    """Work through tasks/ready (one milestone's, if given): tasks, directions, checkpoints
    and escalations. Returns True if Claude (a lead ticket or an escalation) changed the
    runner, which needs a restart.

    A ticket parked for a Claude limit goes first once its reset has passed; until then only
    developer tickets run, and with none left the queue sleeps until the earliest reset.
    """
    code = _runner_code(s.repo)
    while True:
        if _runner_code(s.repo) != code:
            # m4-07: Python keeps the old modules, so a runner fix made by an escalation
            # only takes effect in a new process. Stop rather than run requeued tasks stale.
            s.report.notes.append(RESTART_NOTE)
            return True
        ready = load_dir(s.tasks_dir("ready"), s.cfg.default_max_diff)
        if milestone is not None:
            ready = [t for t in ready if t.milestone == milestone]
        done = task_ids(s.tasks_dir("done"))
        paused = blocked_ids(ready, stopped_ids(s.repo / "tasks"))
        task = _next_task(s, ready, done, paused)
        if task is None:
            if _wait_for_reset(s, ready):
                continue
            if paused:
                s.report.notes.append("Paused (dependency escalated): " + ", ".join(sorted(paused)))
            return False
        rec = run_task(s, task)
        if rec.result != "parked":  # a parked ticket is reported when it runs
            s.report.tasks.append(rec)
        note_merge(s, task, rec)
        if rec.result in ("escalated", "blocked", "preflight") and escalate:
            logs = rec.logs or s.run_dir / task.id
            _save_thinking(rec, logs, s.repo)
            handle_escalation(s, task, logs, rec.note or rec.result)
        if once:
            return False


def run_session(cfg: Config, *, once: bool, dry_run: bool, escalate: bool) -> SessionReport | None:
    if dry_run:
        # Reads tasks/ only: any branch, any tree, and no run folder or row (f1-33).
        tasks = cfg.repo / "tasks"
        ready = load_dir(tasks / "ready", cfg.default_max_diff)
        done = task_ids(tasks / "done")
        paused = blocked_ids(ready, stopped_ids(tasks))
        _print_plan(ready, done, paused, pick_next(ready, done, paused), cfg.repo)
        return None
    s = open_session(cfg)
    work_queue(s, escalate=escalate, once=once)
    return close_session(s)


def close_session(s: Session) -> SessionReport:
    from runner import report as report_mod

    s.report.ended = now()
    if not s.report.tasks and not s.report.claude_runs:
        _finish_run(s, "nothing to do")
        s.log("[runner] Nothing to do.")
        return s.report
    claude = claude_tokens(transcripts_dir(s.repo), s.report.started, s.report.ended)
    path = report_mod.write(s.repo, s.report, claude)
    if s.cfg.narrative and s.report.tasks:
        milestone = s.report.tasks[0].milestone
        job = JobSpec(
            role="narrative",
            prompt=prompts.NARRATIVE.format(report=path.relative_to(s.repo).as_posix()),
            timeout=s.cfg.claude_timeout,
            edit=(ANY,),
        )
        call_claude(s, job, milestone, "session")
    merged = sum(t.result == "done" for t in s.report.tasks)
    _finish_run(s, f"{merged} merged, {len(s.report.tasks) - merged} not")
    runner_commit(s, messages.session_message(s.report, path.relative_to(s.repo).as_posix()))
    s.log(f"[runner] Session report: {path.relative_to(s.repo)}")
    return s.report


def _print_plan(
    ready: list[Task], done: set[str], paused: set[str], nxt: Task | None, repo: Path
) -> None:
    """What would run next, and each ready task's pre-flight problems (docs/task-writing.md)."""
    print(f"ready: {len(ready)}  done: {len(done)}  paused: {len(paused)}")
    for task in sorted(ready, key=lambda t: (milestone_order(t.milestone), t.id)):
        waiting = [d for d in task.depends_on if d not in done]
        status = (
            "paused"
            if task.id in paused
            else ("waiting on " + ", ".join(waiting) if waiting else "runnable")
        )
        marker = "->" if nxt and task.id == nxt.id else "  "
        print(f"{marker} {task.id}: {status}")
        for problem in preflight(task, repo):
            print(f"     pre-flight: {problem}")
    print(f"next: {nxt.id if nxt else 'nothing'}")


# ADR 00 and docs/testing.md: end-to-end runs in Chromium and WebKit.
E2E_BROWSERS = ("chromium", "webkit")


def run_e2e(repo: Path, timeout: int) -> GateResult:
    browsers = [arg for name in E2E_BROWSERS for arg in ("--browser", name)]
    code, out, err = run_bounded(
        ["uv", "run", "pytest", "-q", "-m", "e2e", *browsers, "tests/e2e"], repo, timeout
    )
    if code is None:
        return GateResult("e2e", False, f"timed out after {timeout}s\n" + (out + err)[-4000:])
    return GateResult("e2e", code == 0, (out + err)[-4000:])
