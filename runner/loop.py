"""The per-task loop and the session around it (docs/workflow.md)."""

import hashlib
import itertools
import json
import math
import re
import select
import sqlite3
import sys
import threading
import time
from collections.abc import Callable, Collection, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from functools import partial
from pathlib import Path
from typing import Any, Concatenate, NoReturn

import yaml

from runner import (
    allowance,
    checks,
    console,
    dispatch,
    messages,
    metrics,
    prompts,
    ratings,
    router,
)
from runner.agents import (
    ANY,
    CHECK_COMMANDS,
    GIT_READ_COMMANDS,
    TRANSIENT,
    Agent,
    JobResult,
    JobSpec,
    Reading,
    adapter_for,
)
from runner.claude import Progress, backoff_seconds, probe
from runner.config import Config, read_protected
from runner.gates import (
    BLOCKED_FILE,
    HINTS,
    NO_CHANGES,
    GateContext,
    GateResult,
    autoformat,
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
    stop_reason,
    stream_facts,
    warmup,
)
from runner.procs import run_bounded
from runner.report import ClaudeRunRecord, SessionReport, TaskRecord
from runner.review import Finding, ReviewFileError, parse_checkpoint
from runner.state import State, load_state, save_state
from runner.tasks import (
    BUGS,
    LATER,
    STOPPED,
    Task,
    TaskError,
    append_footer,
    blocked_ids,
    carry_footers,
    command_arg,
    difficulty,
    find_ticket,
    held_ids,
    load_dir,
    milestone_file,
    milestone_key,
    parse_sections,
    parse_task,
    pick_next,
    preflight,
    run_order,
    short_key,
    split_frontmatter,
    stopped_ids,
    task_ids,
    task_priority,
    ticket_area,
    ticket_prefix,
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


def with_progress[T](
    work: Callable[[], T],
    tick: Callable[[float], None],
    poll: Callable[[], None] | None = None,
) -> T:
    """Run ``work`` in a thread; while it runs, ``tick`` gets the seconds elapsed every
    ``PROGRESS_EVERY`` seconds, and ``poll`` is called every ``POLL_S`` seconds, here (the
    metrics connection can't cross threads). Its result or exception comes back here."""
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
        if poll is not None:
            poll()
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
    # What the run says it does outside a job, and until when it waits (`set_activity`).
    activity: str | None = None
    waiting_until: datetime | None = None
    probed: bool = False  # a fresh reading of Claude's windows was taken (f4-07)
    # Queue rows the metrics database couldn't take (f8 D1): this session runs them still.
    unqueued: dict[int, dispatch.Queued] = field(default_factory=dict)
    running_row: dispatch.Queued | None = None  # the queued job running now: its job's row
    # A ticket's record while it waits behind its queued direction, for its last attempt.
    waiting: dict[str, TaskRecord] = field(default_factory=dict)

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
    # A parked support job is a queue row, tried again the same way (`_queue_parked`).
    # Its stored reset stays Claude's: a start that never reached the ticket had written its
    # own time over it (f1-22's said 23:00 for Claude's 01:40, f1-51).
    at = now()
    retried = [k for k, entry in state.parked.items() if not _due(entry, at)]
    for key in retried:
        state.parked[key][RETRY] = True
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
        if s.project_id is not None:
            _queue_parked(s, at)
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
# f2-05: an attempt stopped stuck isn't judged by the gates; the next is told why it stopped.
STOPPED_GATE = "stopped"
STOPPED_OUTPUT = (
    "The attempt was stopped early ({why}): it was getting nowhere. Its"
    " changes so far are committed on this branch. Make one small edit at a time, starting now,"
    " and don't plan the whole change before the first."
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
            OPEN_RUNS.append(s)
            set_activity(s, PICKING)
            if cut_off_job is not None:
                _record(s, metrics.end_interrupted, cut_off_job)
            # a bench beside the runner keeps its heartbeat fresh: leave it working
            _record(s, metrics.close_abandoned, s.project_id, s.run_id, now() - LIVE)
            if RESERVE.yes:  # handed on by this command's restart after the owner's yes
                _record(s, metrics.set_run_reserve, s.run_id)
            _start_heartbeat(s, s.run_id)
        sync_tickets(s)
        sync_cards(s)


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


TICKET_FOLDERS = ("ready", "done", *STOPPED, LATER)


def sync_tickets(s: Session) -> None:
    """Every ticket in tasks/ with its folder's state (f1 D4): the queue the dashboard reads.
    A ``ready`` row whose file is gone (deleted, like f1-30 by ADR 15) leaves it."""
    for folder in TICKET_FOLDERS:
        for path in sorted(s.tasks_dir(folder).glob("*.md")):
            record_ticket(s, path)
    if s.project_id is not None:
        ready = {path.stem for path in s.tasks_dir("ready").glob("*.md")}
        _record(s, metrics.remove_missing_tickets, s.project_id, ready)


def sync_cards(s: Session) -> None:
    """Every milestone doc's card (f5 D4) and title, as ``sync_tickets`` does for tickets: an
    idea with no tickets yet is on the board too. A doc not named by a key is left out."""
    from runner.milestone import card, milestone_doc  # runner.milestone imports this module

    if s.project_id is None:
        return
    for path in sorted((s.repo / "docs" / "milestones").glob("*.md")):
        try:
            key = milestone_key(path.stem)
            text = path.read_text(encoding="utf-8")
        except (TaskError, OSError, UnicodeDecodeError):
            continue
        found = card(key, text)
        _record(
            s,
            metrics.upsert_milestone,
            s.project_id,
            key,
            title=milestone_doc(text).get("title"),
            state=found.state,
            priority=found.priority,
            area=found.area,
        )


PICKING = "picking the next ticket"


def set_activity(s: Session, activity: str | None, waiting_until: datetime | None = None) -> None:
    """What the run does outside a job, and until when it waits (f1 D3, amended); None
    clears both. Best effort, like every write."""
    s.activity, s.waiting_until = activity, waiting_until
    if s.run_id is None:
        return
    until = waiting_until.isoformat() if waiting_until else None
    _record(s, metrics.update_run_activity, s.run_id, activity, until)


@contextmanager
def doing(s: Session, activity: str, waiting_until: datetime | None = None) -> Iterator[None]:
    """The run's activity while the block runs (the gates, check-all, a question, a ticket),
    then back to what it did before, so that it never goes blank while the run lives
    (f2-03)."""
    before = s.activity, s.waiting_until
    set_activity(s, activity, waiting_until)
    try:
        yield
    finally:
        set_activity(s, *before)


WAITING_FOR_CLAUDE = "waiting for Claude"


def wait_for_claude(
    s: Session, seconds: float, resumes: datetime, what: str | None, limit: bool = True
) -> None:
    """Sleep through a pause for Claude (a limit, a passing error, nothing to run without
    it), the run saying so, and for what, until it ends. A wait for a ``limit`` is kept as a
    ``wait`` usage event, from now to ``resumes``: what clogged the line (f3-04)."""
    if limit:
        at = now().isoformat()
        _record(s, metrics.add_usage_event, RUNNER_AGENT, at, "wait", resets_at=resumes.isoformat())
    waiting = f"{WAITING_FOR_CLAUDE} · {what}" if what else WAITING_FOR_CLAUDE
    with doing(s, f"{waiting} until {resumes:%H:%M}", resumes):
        time.sleep(seconds)


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
        area = ticket_area(meta)
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
        area=area,
    )


def _finish_run(s: Session, verdict: str) -> None:
    _stop_heartbeat(s)
    OPEN_RUNS[:] = [other for other in OPEN_RUNS if other is not s]
    if s.run_id is not None:
        _record(s, metrics.end_run, s.run_id, now().isoformat(), verdict)
    if s.db is not None:
        s.db.close()
        s.db = None


# The sessions whose run hasn't ended: `end_open_runs` ends them when the command exits.
OPEN_RUNS: list[Session] = []


def end_open_runs() -> None:
    """End every run this process left open: a Ctrl-C or a crash stopped it before
    `close_session` (f2-03). The command calls it on any exit; a run ended already isn't
    here."""
    for s in list(OPEN_RUNS):
        _finish_run(s, "interrupted")


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
    routing_reason: str | None = None,
) -> int | None:
    """Write a job as running (f1 D3), with why its agent was chosen, and beat the run's
    heartbeat. The page shows the job while it runs; the run's activity stays, for when it
    ends (f2-03). A job of the queued job running now (its role is the row's kind) is the
    row's job. Returns the job's id."""
    if s.run_id is None or s.project_id is None:
        return None
    at = now().isoformat()
    milestone_id = _record(s, metrics.upsert_milestone, s.project_id, milestone)
    ticket_id = _record(s, metrics.upsert_ticket, s.project_id, ticket) if ticket else None
    _record(s, metrics.update_run_heartbeat, s.run_id, at)
    job_id = _record(
        s,
        metrics.start_job,
        s.run_id,
        ticket_id=ticket_id,
        milestone_id=milestone_id,
        role=role,
        agent=agent,
        attempt=attempt,
        started=at,
        routing_reason=routing_reason,
        context_limit=context_limit,
        log_path=log_path,
    )
    row = s.running_row
    if job_id is not None and row is not None and row.kind == role and row.id and row.id > 0:
        _record(s, _set_started, row.id, job_id)
    return job_id


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


def claude_live_update(s: Session, job_id: int | None, progress: Progress) -> None:
    """``live_update`` for a Claude job: its tokens and turns so far (f1 D3, amended)."""
    if job_id is None or s.run_id is None:
        return
    _record(
        s,
        metrics.update_running_job,
        job_id,
        tokens_in=progress.tokens_in,
        tokens_cached=progress.tokens_cached,
        tokens_out=progress.tokens_out,
        steps=progress.turns,
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
        cost_usd=run.cost_usd,
        steps=run.num_turns,
        peak_context=run.peak_context,
        context_limit=context_limit,
        edit_streak=run.edit_streak,
        refused_commands=run.refused_commands,
        gates=gates,
        note=note,
        session_id=run.session_id,
        model=run.model or None,
    )
    _record(s, metrics.update_run_heartbeat, s.run_id, at)


def local_agent(cfg: Config) -> str:
    """The local developer (D6's `local-<model>`): the first local agent the developer role
    lists, else its first."""
    ids = cfg.roles.get("developer", ())
    local = next((i for i in ids if is_local(cfg.agents[i])), None)
    return local or cfg.agent_for("developer").id


# --- routing (f1-25, runner/router.py) ----------------------------------------------------

UNKNOWN = "plan"  # the one window of an agent with no reading: capacity unknown (ADR 15 item 2)


def candidates(s: Session, role: str) -> list[Agent]:
    """The agents `[roles]` lists for ``role``, in order."""
    s.cfg.agent_for(role)  # a role with no agent is a config error
    return [s.cfg.agents[agent_id] for agent_id in s.cfg.roles[role]]


def first_agent(s: Session, role: str) -> router.Route:
    return router.route(role, None, 1, candidates(s, role), {}, {}, {}, now())


def current_ratings(s: Session) -> dict[str, float]:
    """Each agent's rating as routing reads it (``routing_ratings``); every agent at the floor
    when the database can't be read: an estimate is never trusted (ADR 24 item 3)."""
    start = starting_ratings(s.cfg)
    found = _record(s, routing_ratings, start)
    return found if found is not None else {agent: ratings.LOWEST for agent in start}


def _at(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _rested(window: allowance.Window, rows: list[sqlite3.Row], at: datetime) -> allowance.Window:
    """A Claude window after the account's refusals: one in this window (or naming none) rests
    it until its reset, or with none given for ``allowance.COOLDOWN``. Its capacity stays the
    one Claude reports."""
    if window.resets_at is None:
        return window
    start = window.resets_at - window.length
    hits = [r for r in rows if r["window"] in (None, window.name) and _at(r["at"]) >= start]
    if not hits:
        return window
    last = hits[-1]
    until = _at(last["resets_at"]) if last["resets_at"] else _at(last["at"]) + allowance.COOLDOWN
    return replace(window, cooldown_until=until) if until > at else window


def agent_windows(
    s: Session, agents: Iterable[Agent], at: datetime
) -> dict[str, list[allowance.Window]]:
    """Each cloud agent's allowance windows now (ADR 15 items 1–3). Claude's come from the
    account's latest readings, whichever model read them; a window it hasn't read since its
    reset is unknown until refused. Another agent's readings (Copilot's month) count the same
    way. An agent with no reading at all (Ollama) has one window of unknown capacity, which
    its refusals rest (``allowance.learn``)."""
    windows: dict[str, list[allowance.Window]] = {}
    for agent in agents:
        if is_local(agent):
            continue
        if agent.harness == CLAUDE:
            read = rested_claude_windows(s, at)
            if not any(w.name == "seven_day" for w in read):
                read.append(allowance.Window("seven_day", "fixed", allowance.WEEK, None, None, 0.0))
            windows[agent.id] = read
            continue
        if read := _read_windows(s, agent.id, at):
            rows = [
                r for r in _record(s, metrics.refusals, agent.id) or [] if r["agent"] == agent.id
            ]
            windows[agent.id] = [_rested(w, rows, at) for w in read]
            continue
        refusals = [
            allowance.Refusal(_at(r["at"]), 0.0, _at(r["resets_at"]) if r["resets_at"] else None)
            for r in _record(s, metrics.refusals, agent.id) or []
            if r["agent"] == agent.id
        ]
        plan = allowance.Window(UNKNOWN, "fixed", allowance.MONTH, None, None, 0.0)
        windows[agent.id] = [allowance.learn(plan, refusals, at)]
    return windows


def route_developer(
    s: Session,
    task: Task,
    role: str,
    attempt: int,
    *,
    failed: str | None,
    refused: Collection[str],
) -> router.Route:
    """Who takes this attempt (ADR 15 items 6–7). Expected costs are left at 0, as for a lead
    ticket (``LEAD_COST``): no agent's share of a window per job is learned yet, so where it
    stands against its pace line decides. Lead work comes first (ADR 16 item 2)."""
    at = now()
    agents = candidates(s, role)
    ticket = router.Ticket(task.id, task.difficulty)
    return router.route(
        role,
        ticket,
        attempt,
        agents,
        current_ratings(s),
        agent_windows(s, agents, at),
        {},
        at,
        failed=failed,
        refused=refused,
        lead_ready=lead_work_ready(s),
        five_hour_cap=s.cfg.developer_five_hour_cap,
    )


def lead_work_ready(s: Session) -> bool:
    """Lead work waits (ADR 16 item 2): a lead ticket whose dependencies are done, a queued
    direction, escalation or checkpoint, or a checkpoint due."""
    if any(row.kind in (*SUPPORT, DIRECTION) for row in open_rows(s)):
        return True
    if len(s.state.unchecked) >= s.cfg.checkpoint_every:
        return True
    protected = tuple(read_protected(s.repo))
    ready = load_dir(s.tasks_dir("ready"), s.cfg.default_max_diff)
    done = task_ids(s.tasks_dir("done"))
    paused = blocked_ids(ready, stopped_ids(s.repo / "tasks"))
    return any(
        router.lead_only(t.agent, t.files, protected)
        and t.id not in paused
        and all(d in done for d in t.depends_on)
        for t in ready
    )


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
    is committed on its branch, its session and ``resets_at`` are in state.json. With
    ``five_hour``, only the owner's share of the 5-hour window held it (ADR 16 item 1)."""

    def __init__(self, resets_at: datetime, five_hour: bool = False) -> None:
        super().__init__(f"parked until {resets_at.isoformat()}")
        self.resets_at = resets_at
        self.five_hour = five_hour


# Support jobs that park in the queue rather than sleep in it (ADR 16 item 4): their queue
# row waits (f8 D3). A ticket's own jobs park in state.json's `parked`, keyed by its id.
SUPPORT = ("checkpoint", "escalation")
DIRECTION, ESCALATION, REVIEW = dispatch.DIRECTION, dispatch.ESCALATION, dispatch.REVIEW
QUEUED = (*SUPPORT, DIRECTION)  # the support jobs a ticket's run queues
FIVE_HOUR_HELD = "five_hour"  # a parked entry's flag: held by the owner's 25%, not a limit


def _park(
    s: Session,
    job: JobSpec,
    name: str,
    milestone: str,
    agent: str,
    job_id: int | None,
    session: str | None,
    resets_at: datetime | None,
    extra: Mapping[str, Any] | None = None,
) -> NoReturn:
    """Park the job: its changes committed on its branch (on ``parked/…`` if it ran on main),
    its session kept for the resume, its ticket held until the reset (with none given,
    ``backoff_min`` from now). ``extra`` is what a support job needs to start again."""
    at = now()
    resets = resets_at or at + timedelta(seconds=s.cfg.backoff_min)
    branch = s.git.current_branch()
    kept = "" if branch == MAIN else branch
    if not kept and not s.git.is_clean():  # a support job edits main: keep its work aside
        kept = _free_branch(s.git, f"parked/{job.role}-{name}")
        s.git.run("checkout", "-q", "-b", kept)
    if kept:
        s.git.commit_all(with_trailers(f"wip {name} (parked)", agent=CLAUDE_HEADLESS_AGENT))
    if kept and kept != branch:
        s.git.checkout(MAIN)
    entry = {"session_id": session or "", "branch": kept}
    s.state.interrupted[job_key(job.role, name)] = {**entry, "cause": "limit"}
    if job.role in QUEUED:
        subject = milestone if job.role == CHECKPOINT else name
        park_row(s, job.role, subject, resets, **(extra or {}))
    else:
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


# --- the work queue (ADR 22 item 1, f8 D1 and D3) -------------------------------------------


def open_rows(s: Session) -> list[dispatch.Queued]:
    """The queued jobs not yet done, oldest first, then any the database couldn't take."""
    rows = []
    if s.project_id is not None:
        found = _record(s, metrics.open_jobs, s.project_id) or []
        rows = [dispatch.Queued.from_row(row) for row in found]
    return [*rows, *s.unqueued.values()]


def find_row(s: Session, kind: str, subject: str | None = None) -> dispatch.Queued | None:
    """The open row of ``kind`` about ``subject`` (any, with None)."""
    return next((q for q in open_rows(s) if q.kind == kind and subject in (None, q.subject)), None)


def _row_of(s: Session, kind: str, subject: str) -> dispatch.Queued | None:
    """A support job's open row: one checkpoint reviews every merge, whatever its subject."""
    return find_row(s, kind, None if kind == CHECKPOINT else subject)


def row_key(row: dispatch.Queued) -> str:
    """What keys a queued job's needs in ``State.queued``."""
    return job_key(row.kind, row.subject)


def _row_name(row: dispatch.Queued) -> str:
    return row.kind if row.kind == CHECKPOINT else f"{row.kind} of {row.subject}"


def _set_not_before(conn: sqlite3.Connection, row_id: int, not_before: str | None) -> None:
    conn.execute("UPDATE work_queue SET not_before = ? WHERE id = ?", (not_before, row_id))


def _set_started(conn: sqlite3.Connection, row_id: int, job_id: int) -> None:
    """The row's job: its latest of the row's kind (a parked one's resume replaces it)."""
    conn.execute("UPDATE work_queue SET started_job = ? WHERE id = ?", (job_id, row_id))


def enqueue(s: Session, kind: str, subject: str, reason: str, /, **needs: Any) -> dispatch.Queued:
    """Queue a support job with its reason (ADR 22 item 1), and what it ``needs`` to start in
    ``State.queued``. The trigger decides when one is due; one already open (of the kind
    about the subject, or any checkpoint) is kept as it is."""
    if (found := _row_of(s, kind, subject)) is not None:
        return found
    at = now().isoformat()
    row_id = None
    if s.project_id is not None:
        row_id = _record(s, metrics.queue_job, s.project_id, kind, subject, reason, at)
    row = dispatch.Queued(kind, subject, reason, at, None, row_id)
    if row_id is None:  # the run goes on without the database: this session runs it still
        row = replace(row, id=min(s.unqueued, default=0) - 1)
        s.unqueued[row.id or 0] = row
    if needs:
        s.state.queued[row_key(row)] = dict(needs)
        save_state(s.state, s.state_path)
    return row


def _set_row(s: Session, row: dispatch.Queued, not_before: datetime | None) -> None:
    stamp = not_before.isoformat() if not_before else None
    if (row.id or 0) < 0:
        s.unqueued[row.id or 0] = replace(row, not_before=stamp)
    elif row.id is not None:
        _record(s, _set_not_before, row.id, stamp)


def park_row(
    s: Session, kind: str, subject: str, until: datetime, five_hour: bool = False, /, **needs: Any
) -> None:
    """Park a support job until ``until`` (f8 D3): its row waits, with what it needs to start
    again. ``five_hour``: only the owner's share of the 5-hour window holds it."""
    row = _row_of(s, kind, subject) or enqueue(s, kind, subject, PARKED_REASON)
    _set_row(s, row, until)
    entry = s.state.queued.setdefault(row_key(row), {})
    entry.update(needs)
    entry.pop(RETRY, None)
    entry.pop(FIVE_HOUR_HELD, None)
    if five_hour:
        entry[FIVE_HOUR_HELD] = True
    save_state(s.state, s.state_path)


def _unpark_row(s: Session, row: dispatch.Queued) -> None:
    """A parked row runs at once: a restart, or the owner's yes, may have freed Claude."""
    _set_row(s, row, None)
    s.state.queued.setdefault(row_key(row), {})[RETRY] = True
    save_state(s.state, s.state_path)


def _row_waits(s: Session, kind: str, subject: str) -> bool:
    """Whether a support job's row is parked until a time still ahead."""
    row = _row_of(s, kind, subject)
    return row is not None and row.not_before is not None and _at(row.not_before) > now()


def finish_row(s: Session, row: dispatch.Queued) -> None:
    """Mark a queued job done and drop what it kept."""
    if (row.id or 0) < 0:
        s.unqueued.pop(row.id or 0, None)
    elif row.id is not None:
        _record(s, metrics.finish_queued, row.id, now().isoformat())
    s.state.queued.pop(row_key(row), None)
    save_state(s.state, s.state_path)


def _merges(merged: Sequence[str]) -> str:
    names = [m.split()[0] for m in merged]
    return names[0] if len(names) < 2 else ", ".join(names[:-1]) + f" and {names[-1]}"


def _direction_reason(task_id: str, failures: Sequence[str]) -> str:
    return f"{task_id} failed: {', then '.join(failures) or 'its attempts'}"


def _queue_parked(s: Session, at: datetime) -> None:
    """At start (f8 D3): the support jobs an older state.json parked become queue rows, once;
    then every parked row is tried again at once, as a parked ticket is (2026-10-01)."""
    for key, entry in list(s.state.parked.items()):
        kind = entry["kind"]
        if kind not in QUEUED:
            continue
        del s.state.parked[key]
        dropped = ("kind", "resets_at", "branch", "session_id", RETRY, FIVE_HOUR_HELD)
        needs = {k: v for k, v in entry.items() if k not in dropped}
        if kind == CHECKPOINT:
            subject = str(entry.get("milestone") or CHECKPOINT)
            reason = f"after {_merges(s.state.unchecked)} merged"
        elif kind == ESCALATION:
            subject = key.partition(":")[2]
            reason = f"{subject}: {entry.get('reason', 'escalated')}"
        else:
            subject = key
            reason = _direction_reason(key, entry.get("gate_failures") or [])
        enqueue(s, kind, subject, reason, **needs)
    save_state(s.state, s.state_path)
    for row in open_rows(s):
        if row.not_before is not None and _at(row.not_before) > at:
            _unpark_row(s, row)


def waiting_rows(s: Session, ready: Iterable[Task]) -> dict[str, str]:
    """Ready tickets that wait behind their own queued direction or escalation (ADR 22
    item 1), with why."""
    ids = {t.id for t in ready}
    return {
        row.subject: f"waits for its {row.kind}"
        for row in open_rows(s)
        if row.kind in (DIRECTION, ESCALATION) and row.subject in ids
    }


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
    routed: router.Route | None = None,
    parked: Mapping[str, Any] | None = None,
) -> JobResult:
    """Run a lead job on the agent ``routed`` names, else the first its role lists, waiting
    out usage limits. Each trigger bounds its own runs (ADR 12 item 10); the count per
    milestone is kept for the metrics.

    With ``park`` (a ticket's job, a checkpoint or an escalation), a certain limit parks it
    instead of waiting: ``Parked`` is raised, and the queue goes on without Claude until the
    reset (ADR 15 item 10, ADR 16 item 4). ``parked`` is kept with it, to start it again.

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
    first, unless this job resumes and may have written its own.

    A ``job.resume`` session carries on an earlier job's with ``job.prompt``: one more turn."""
    attempt = unsure = transient = 0
    resume = job.resume
    interrupted = False
    resume_prompt, partial_note = job.prompt if resume else RESUME_PROMPT, PARTIAL_WORK_NOTE
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
    runner, reason = routed or first_agent(s, job.role)
    adapter, agent = adapter_for(runner.harness), runner.id
    what = job.role if ticket or subject == job.role else f"{job.role} {subject}"
    started = clock()
    s.log(console.start(agent, what))
    base = f"claude-{job.role}-{subject}" + (f"-{number}" if number > 1 else "")
    log = s.run_dir / f"{base}.log"
    job_id = s.last_job_id = record_start(
        s,
        ticket,
        milestone,
        job.role,
        agent,
        attempt=number,
        log_path=_rel(s, log),
        routing_reason=reason,
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
    # Claude's progress comes from the job's thread; its row is written from this one.
    latest: dict[str, Progress] = {}

    def write_progress() -> None:
        if (progress := latest.pop("progress", None)) is not None:
            claude_live_update(s, job_id, progress)

    while True:
        prompt = resume_prompt if resume else job.prompt + (partial_note if interrupted else "")
        resume_prompt = RESUME_PROMPT  # a later resume follows a pause for a limit
        log = s.run_dir / f"{base}{f'-retry{attempt}' if attempt else ''}.log"
        if attempt:
            s.log(console.resumed(agent, what))
        run = partial(
            adapter.run, runner, replace(job, prompt=prompt, resume=resume), s.repo, log, now()
        )
        if runner.harness == CLAUDE:
            run = partial(run, on_progress=partial(latest.__setitem__, "progress"))
        result = with_progress(
            run, lambda elapsed: s.log(console.running(agent, what, elapsed)), write_progress
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
            resumes = at + timedelta(seconds=pause)
            s.log(console.paused(agent, f"interrupted ({result.text})", resumes, at))
            wait_for_claude(s, pause, resumes, ticket or subject, limit=False)
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
                name = ticket or subject
                _park(s, job, name, milestone, agent, job_id, session, limit.resets_at, parked)
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
            wait_for_claude(s, wait, resumes, ticket or subject)
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
            steps=result.num_turns,
            note=_process_note(process_note),
            session_id=result.session_id,
            log_path=_rel(s, log),
            model=result.model or None,
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

    While Claude is limited, or at the owner's share of its 5-hour window, it raises ``Parked``
    instead, as does a limit during the direction: the ticket waits rather than going
    undirected (ADR 15 item 10, ADR 16 item 4). A parked direction isn't counted: its ticket
    gets it after the reset."""
    if (hold := claude_hold(s, now())) is not None:
        raise Parked(hold.until, hold.five_hour)
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


def _direction_needs(
    s: Session,
    rec: TaskRecord,
    logs: Path,
    timeouts: list[bool],
    last: GateResult | None,
    reset: str,
) -> dict[str, Any]:
    """What a queued direction and the last attempt after it read of the attempts so far,
    and why that attempt starts from main, if it does (`prompts.RESET`)."""
    return {
        "logs": _rel(s, logs),
        "gate": last.name if last else "",
        "output": last.output if last else "",
        "gate_failures": list(rec.gate_failures),
        "timeouts": list(timeouts),
        "reset": reset,
    }


def _wait_for_direction(s: Session, task: Task, rec: TaskRecord) -> None:
    """The ticket waits behind its queued direction (ADR 22 item 1): back on main, its last
    attempt not run, its record kept for when it goes on."""
    s.git.checkout(MAIN)
    rec.attempts -= 1  # the last attempt hasn't run
    rec.result = "parked"
    s.waiting[task.id] = rec


def _queue_direction(
    s: Session,
    task: Task,
    rec: TaskRecord,
    logs: Path,
    timeouts: list[bool],
    last: GateResult | None,
    reset: str,
) -> None:
    """Before the last attempt (ADR 12 item 6): queue the lead's direction, which the loop
    runs next, and the ticket's last attempt after it. Its thinking so far is saved now."""
    _save_thinking(rec, logs, s.repo)
    needs = _direction_needs(s, rec, logs, timeouts, last, reset)
    enqueue(s, DIRECTION, task.id, _direction_reason(task.id, rec.gate_failures), **needs)
    _wait_for_direction(s, task, rec)


def _park_direction(
    s: Session,
    task: Task,
    rec: TaskRecord,
    parked: Parked,
    logs: Path,
    timeouts: list[bool],
    last: GateResult | None,
    reset: str,
) -> None:
    """Hold a developer ticket at its direction until Claude's reset, with what its attempts
    left for the direction and the last attempt to read."""
    if not _row_waits(s, DIRECTION, task.id):  # parked before it ran: Claude was limited
        s.log(
            console.paused(
                RUNNER_AGENT, f"{task.id} waits for its direction", parked.resets_at, now()
            )
        )
        s.report.notes.append(f"Parked {task.id}: its direction waits for Claude's reset.")
    needs = _direction_needs(s, rec, logs, timeouts, last, reset)
    park_row(s, DIRECTION, task.id, parked.resets_at, parked.five_hour, **needs)
    _wait_for_direction(s, task, rec)


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


def _record_refusal(
    s: Session, agent: str, run: JobResult, what: str = "a developer attempt"
) -> None:
    """A cloud agent's refusal, for the allowance (ADR 15 item 2): its reset if it said."""
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
    s.report.notes.append(f"{agent} refused {what} ({sure}): {run.text[:200]}")


def _log_running(s: Session, agent: str, what: str, elapsed: float) -> None:
    s.log(console.running(agent, what, elapsed))


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
    failed: str | None = None,
) -> tuple[str, JobResult, int | None, int | None]:
    """One developer attempt, on the agent the router picks (``failed``: the agent of the
    attempt before, for a step up). A refusal doesn't count (ADR 14 item 10, ADR 15 item 12):
    it is recorded and the same attempt reruns on the next agent the router picks; a cloud
    agent's passing error is skipped the same way. With no one left, the last result stands.
    Only the local model is warmed up. Returns the agent, its result, its job row and its
    context limit."""
    refused: set[str] = set()
    for n in itertools.count(1):
        agent, reason = route_developer(s, task, role, attempt, failed=failed, refused=refused)
        local = is_local(agent)
        if local:
            with doing(s, "warm-up"):
                rec.warmup_s += warmup(s.cfg.lm_base_url, s.cfg.lm_model, s.cfg.warmup_timeout)
            _check_context(s)
        context_limit = s.context_limit if local else None
        name = f"{agent.harness}-{attempt}" + (f"-{n}" if n > 1 else "")
        log = logs / (f"{name}.jsonl" if agent.harness == "opencode" else f"{name}.log")
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
            routing_reason=reason,
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
        opencode = agent.harness == "opencode"
        spec = JobSpec(
            role,
            prompt,
            s.cfg.opencode_timeout if opencode else s.cfg.claude_timeout,
            edit=(ANY,),
            commands=CHECK_COMMANDS if opencode else (*CHECK_COMMANDS, *GIT_READ_COMMANDS),
            title=f"{task.id} attempt {attempt}",
        )
        if opencode:
            progress = partial(attempt_progress, s, agent.id, job_id, what, log, Ticker())
            run = OPENCODE.run(agent, spec, s.repo, log, now(), on_progress=progress)
        else:
            run = with_progress(
                partial(adapter_for(agent.harness).run, agent, spec, s.repo, log, now()),
                partial(_log_running, s, agent.id, what),
            )
            _record_readings(s, agent.id, run.readings)
        _tally(rec, run)
        skipped = run.refusal is not None or (run.transient and not local)
        if not skipped:
            return agent.id, run, job_id, context_limit
        _record_refusal(s, agent.id, run)
        refused.add(agent.id)
        if not any(
            a.id not in refused and a.harness not in router.READ_ONLY_HARNESSES
            for a in candidates(s, role)
        ):
            return agent.id, run, job_id, context_limit
        why = "refused" if run.refusal is not None else "transient"
        _attempt_end(s, agent.id, what, run, f"{why}, rerun on the next agent")
        _finish_attempt(s, job_id, run, "failed", note=why, context_limit=context_limit)
    raise AssertionError("unreachable: itertools.count never ends")


def run_task(s: Session, task: Task, directing: Mapping[str, Any] | None = None) -> TaskRecord:
    """One ticket. Its result is "parked" when it waits for Claude (a limit, the reserve, or
    its turn behind the support work a yes to the 5-hour question freed) or behind its queued
    direction. ``directing`` is that direction's needs: the run that gives it, then the last
    attempt."""
    kept = s.waiting.pop(task.id, None) if directing is not None else None
    rec = kept or TaskRecord(id=task.id, milestone=task.milestone)
    held = s.state.parked.pop(task.id, None)
    if held is not None:
        save_state(s.state, s.state_path)
        if held["kind"] == FIVE_HOUR_KIND:  # it waited out the reset: nothing left to answer
            _resolve_item(s, FIVE_HOUR_KIND, task.id)
    # The direction goes on in the logs of the attempts it reads.
    logs = rec.logs = s.repo / directing["logs"] if directing else _logs_dir(s.run_dir, task.id)
    if kept is None:
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

    protected = tuple(read_protected(s.repo))
    # Lead-only work never routes to a developer (ADR 14 item 11): a developer ticket whose
    # files are protected is the lead's.
    if router.lead_only(task.agent, task.files, protected):
        if task.agent != "lead":
            s.report.notes.append(f"{task.id} touches protected paths: the lead does it.")
        if at_reserve(s, task) or at_five_hour(s, task):
            rec.result = "parked"
            return rec
        run_lead_task(s, task, rec)
        return rec

    branch = f"task/{task.id}"
    # Attempts an interruption cut off count as timed out; their work stays on the branch.
    cut_off = s.state.timed_out.pop(task.id, 0)
    if cut_off:
        save_state(s.state, s.state_path)
    last = GateResult(INTERRUPTED_GATE, False, INTERRUPTED_OUTPUT) if cut_off else None
    timeouts = [True] * cut_off
    rec.attempts = rec.timeouts = cut_off
    if directing is not None:  # its attempts so far, then the direction it waited for
        last = GateResult(str(directing["gate"]), False, str(directing["output"]))
        timeouts = [bool(t) for t in directing["timeouts"]]
        rec.gate_failures = [str(g) for g in directing["gate_failures"]]
        rec.attempts, rec.timeouts = len(timeouts), sum(timeouts)
        if kept is None:  # a new process: the next attempt's thinking keeps its number
            rec.sessions = [""] * rec.attempts
    # A requeued ticket continues the branch its escalation kept (ADR 15 item 7).
    resumed = not rec.attempts and _has_branch(s.git, branch)
    _start_attempt(s, branch, "")
    earlier = s.git.changed_files(MAIN) if resumed and s.git.current_branch() == branch else []
    direction = ""
    pending = str(directing.get("reset") or "") if directing is not None else ""
    failed_agent: str | None = None  # who failed the attempt before, for a step up
    for attempt in range(rec.attempts + 1, s.cfg.max_attempts + 1):
        rec.attempts = attempt
        reset, pending = pending, ""
        if attempt == s.cfg.max_attempts and directing is not None:
            try:
                task, direction = give_direction(s, task, rec, logs)
            except Parked as parked:
                _park_direction(s, task, rec, parked, logs, timeouts, last, reset)
                return rec
            if (row := find_row(s, DIRECTION, task.id)) is not None:
                finish_row(s, row)  # its job is done; the last attempt isn't the row's
            direction, unusable = split_reset(direction)
            reset = "direction" if unusable else reset
        elif (
            attempt == s.cfg.max_attempts
            and attempt > 1
            and s.state.directions.get(task.id, 0) < s.cfg.directions_per_task
            and needs_direction(rec.gate_failures, timeouts)
        ):
            _queue_direction(s, task, rec, logs, timeouts, last, reset)
            return rec
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
            s,
            task,
            rec,
            role,
            attempt,
            what,
            prompt,
            logs,
            branch,
            directed=bool(direction),
            failed=failed_agent,
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
        stopped = stop_reason(run)
        if stopped:
            results = [GateResult(STOPPED_GATE, False, STOPPED_OUTPUT.format(why=stopped))]
        elif changed := s.git.changed_files(MAIN):
            # Formatting alone never costs an attempt (ADR 17 item 2).
            if autoformat(s.repo, changed, s.cfg.gate_timeout):
                local_wip_commit(s, f"wip {task.id} attempt {attempt} (formatted)")
            context = GateContext(s.repo, s.git, task, MAIN, protected, s.cfg.gate_timeout)
            with doing(s, f"gates · {task.id}"):
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
            note=stopped,
        )
        if failed is None:
            end("passed")
            _merge(s, task, rec, agent)
            return rec
        end(stopped or ("timed out, " if run.timed_out else "") + f"failed gate {failed.name}")
        if run.timed_out:
            s.report.notes.append(f"{task.id} attempt {attempt}: {agent} timed out.")
        if stopped:
            s.report.notes.append(f"{task.id} attempt {attempt}: {agent} {stopped}.")
        rec.gate_failures.append(failed.name)
        last, failed_agent = failed, agent

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


def _merge(s: Session, task: Task, rec: TaskRecord, agent: str) -> None:
    """Merge the work of ``agent``, the developer whose attempt passed."""
    branch = f"task/{task.id}"
    changes = s.git.numstat(MAIN)
    changed = s.git.changed_files(MAIN)
    rec.outside_files = outside_allowed(changed, (*task.files, *task.tests))
    rec.changed_tests = [f for f in changed if is_test_file(f) and s.git.exists_at(MAIN, f)]
    developer = s.cfg.agents[agent]
    local = is_local(developer)
    model = s.cfg.lm_model if local else developer.model
    by = "the local model" if local else agent
    rec.commit = s.git.squash_merge(
        branch,
        MAIN,
        with_trailers(
            messages.merge_message(task, rec, model, changes, by=by),
            agent=LOCAL_MODEL_AGENT if local else agent,
            task=task.id,
            model=model,
            attempts=str(rec.attempts),
        ),
        author=LOCAL_MODEL_AUTHOR if local else None,
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
    record_ticket(s, target, merged_by=agent, commit=rec.commit)
    rate_finished(s, task.id)
    s.git.run("branch", "-D", branch)
    rec.result = "done"
    # The next checkpoint reviews it, on another model than its author (ADR 15 item 9).
    s.state.unchecked.append(f"{task.id} {rec.commit} {agent}")
    save_state(s.state, s.state_path)
    _merged_line(s, agent, task.id, rec)


def _merged_line(s: Session, agent: str, task_id: str, rec: TaskRecord) -> None:
    lines = s.git.commit_size(rec.commit) if rec.commit else None
    s.log(console.merged(agent, task_id, rec.attempts, lines, clock() - s.ticket_started))


# --- lead tickets (ADR 12 item 9) --------------------------------------------------------


def _check_all(s: Session, task_id: str | None, logs: Path, name: str) -> bool:
    with doing(s, f"check-all · {task_id}" if task_id else "check-all on main"):
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
    """After a developer merge (``_merge`` lists it as unchecked): every ``checkpoint_every``
    of them, queue a checkpoint. One already queued runs on every merge since."""
    if rec.result != "done" or task.agent != "developer":
        return
    if find_row(s, CHECKPOINT) is not None:
        return
    if len(s.state.unchecked) >= s.cfg.checkpoint_every:
        reason = f"after {_merges(s.state.unchecked)} merged"
        enqueue(s, CHECKPOINT, task.milestone, reason, milestone=task.milestone)


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

# Jobs that attempt a ticket; a refused, skipped or parked one isn't an attempt (ADR 14 item 10).
_ATTEMPT_ROLES = ("developer", "last-attempt", "lead-ticket")
BENCH = "bench"  # a bench replay's jobs (runner/bench.py): a game each (ADR 24 item 3)
REPLAY = "replay ADR 24: "  # the recompute's rows (ADR 24 item 4): + the replayed change's label
REPLAY_FROM = REPLAY + "from "  # + the estimate: where an agent's recompute starts, not a game
_TICKET_RESULTS = {
    ratings.MERGED_FIRST: ratings.FIRST,
    ratings.MERGED_LATER: ratings.LATER,
    ratings.NOT_MERGED: ratings.LOST,
}


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


def routing_ratings(conn: sqlite3.Connection, start: Mapping[str, float]) -> dict[str, float]:
    """Each agent's rating now, at the floor until it has played ``ratings.MIN_GAMES`` coding
    games (a finding's penalty isn't one). The stored rating, and the Agents page, keep it.
    A recompute starts the count again: its rows replay the games before it."""
    current, _ = standing(conn, start)
    games: dict[str, int] = {}
    rows = conn.execute(
        "SELECT agent, ifnull(result, '') AS result FROM rating_changes WHERE skill = ?"
        " ORDER BY at, id",
        (ratings.CODING,),
    )
    for row in rows:
        if row["result"].startswith(REPLAY_FROM):
            games[row["agent"]] = 0
        elif not row["result"].removeprefix(REPLAY).startswith(ratings.FINDING_LABEL):
            games[row["agent"]] = games.get(row["agent"], 0) + 1
    return {agent: ratings.routing_rating(r, games.get(agent, 0)) for agent, r in current.items()}


def _attempts(
    conn: sqlite3.Connection, ticket_id: int, merged_by: str | None
) -> list[ratings.Attempt]:
    """A ticket's attempts in order. A merged ticket's last attempt merged if it passed;
    otherwise the merger (an escalation that finished or implemented it) is one more."""
    marks = ", ".join("?" for _ in _ATTEMPT_ROLES)
    rows = conn.execute(
        f"SELECT agent, outcome FROM jobs WHERE ticket_id = ? AND role IN ({marks})"  # noqa: S608
        " AND outcome NOT IN ('running', 'interrupted', 'refused')"
        " AND ifnull(note, '') NOT IN ('refused', 'transient', 'parked') ORDER BY started, id",
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
    reviewer (``checkpoint`` for a missed one), and a quarter off the author of the code once
    per ticket, whatever later verdicts come (ADR 24 item 1)."""
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
    penalised = {
        ticket
        for (ticket,) in conn.execute(
            "SELECT DISTINCT t.ticket FROM rating_changes r"  # noqa: S608
            f" JOIN tickets t ON t.id = r.ticket_id WHERE r.ticket_id IN ({marks})"
            " AND r.result LIKE ?",
            [*ids.values(), ratings.FINDING_LABEL + "%"],
        )
    }
    games = ratings.judged_games(judged, penalised)
    current, played = standing(conn, start)
    _write_changes(conn, ratings.rate(current, played, games), ids, at)


def rate_bench(
    conn: sqlite3.Connection,
    project_id: int,
    run_id: int,
    ticket: str,
    agent: str,
    start: Mapping[str, float],
    at: datetime,
) -> None:
    """``agent``'s bench replay of ``ticket`` in bench run ``run_id``, as one coding game, once
    (ADR 24 item 3). A replay with a refusal (or still running) is no game, and a ticket with
    no difficulty isn't rated."""
    row = conn.execute(
        "SELECT id, coalesce(difficulty_corrected, difficulty) AS difficulty"
        " FROM tickets WHERE project_id = ? AND ticket = ?",
        (project_id, ticket),
    ).fetchone()
    if row is None or row["difficulty"] is None:
        return
    jobs = conn.execute(
        "SELECT outcome, started FROM jobs WHERE run_id = ? AND ticket_id = ? AND role = ?"
        " AND agent = ? ORDER BY started, id",
        (run_id, row["id"], BENCH, agent),
    ).fetchall()
    game = _bench_game(agent, ticket, row["difficulty"], [job["outcome"] for job in jobs])
    if game is None:
        return
    began = _at(jobs[0]["started"])
    rated = conn.execute(
        "SELECT at FROM rating_changes WHERE agent = ? AND ticket_id = ? AND result LIKE ?",
        (agent, row["id"], ratings.BENCH_LABEL + "%"),
    )
    if any(_at(r["at"]) >= began for r in rated):
        return
    current, played = standing(conn, start)
    _write_changes(conn, ratings.rate(current, played, [game]), {ticket: row["id"]}, at)


def _bench_game(
    agent: str, ticket: str, difficulty: float, outcomes: Sequence[str]
) -> ratings.Game | None:
    """One bench run's replay of a ticket as a game; none with a refusal, still running, or
    void (it changed the main checkout, f7-06)."""
    if not outcomes or any(o in ("running", "interrupted", "refused", "void") for o in outcomes):
        return None
    passed = next((n for n, o in enumerate(outcomes, start=1) if o == "passed"), None)
    return ratings.bench_game(agent, ticket, difficulty, passed)


def void_benches_before(
    conn: sqlite3.Connection, project_id: int, agents: Mapping[str, Agent], cut_off: datetime
) -> dict[str, int]:
    """Void the OpenCode agents' ticket replays that started before ``cut_off``: until f7-06's
    fix they worked in the main checkout, so their gates said nothing about them (f7-07). Each
    agent's count of jobs voided; review benches, other harnesses and later jobs stay."""
    opencode = {a.id for a in agents.values() if a.harness == "opencode"}
    jobs = conn.execute(
        "SELECT j.id, j.agent, j.started FROM jobs j JOIN tickets t ON t.id = j.ticket_id"
        " WHERE j.role = ? AND t.project_id = ? AND j.outcome != 'void'",
        (BENCH, project_id),
    ).fetchall()
    voided: dict[str, int] = {}
    for job in jobs:
        if job["agent"] in opencode and _moment(job["started"]) < cut_off:
            conn.execute(
                "UPDATE jobs SET outcome = 'void', note = ? WHERE id = ?",
                (f"void: benched in the main checkout, before {cut_off.isoformat()}", job["id"]),
            )
            voided[job["agent"]] = voided.get(job["agent"], 0) + 1
    return voided


@dataclass(frozen=True)
class Replayed:
    """An agent's rating before and after the ADR 24 recompute."""

    agent: str
    before: float  # its standing
    after: float
    games: int  # its coding games replayed, as routing counts them
    written: bool  # False: the recompute changed nothing, so wrote nothing


def _moment(value: str) -> datetime:
    at = _at(value)
    return at if at.tzinfo else at.replace(tzinfo=UTC)  # a backfilled time may have no zone


def _recorded_games(
    conn: sqlite3.Connection, project_id: int
) -> tuple[list[tuple[datetime, ratings.Game]], dict[str, int]]:
    """The games the ratings have played, at their times, under ADR 24: each ticket's game and
    each verdict once, and every bench run's replay from its jobs (benches before ADR 24 were
    never rated). Findings on a merged ticket's code re-play its game a quarter lower (item 1),
    at the game's time; a penalty with no game to fold into stays, once per (agent, ticket).
    Earlier recomputes are left out. Also each ticket's id."""
    rows = conn.execute(
        "SELECT r.agent, r.skill, r.at, ifnull(r.result, '') AS result, t.id AS ticket_id,"
        " t.ticket, coalesce(t.difficulty_corrected, t.difficulty) AS difficulty"
        " FROM rating_changes r JOIN tickets t ON t.id = r.ticket_id"
        " WHERE t.project_id = ? AND ifnull(r.result, '') NOT LIKE ? ORDER BY r.at, r.id",
        (project_id, REPLAY + "%"),
    ).fetchall()
    found: dict[tuple[str, str], str] = {}  # (author, ticket): its first finding's label
    for row in rows:
        if row["result"].startswith(ratings.FINDING_LABEL):
            found.setdefault((row["agent"], row["ticket"]), row["result"])
    merged = (ratings.MERGED_FIRST, ratings.MERGED_LATER)
    folded = {
        (row["agent"], row["ticket"])
        for row in rows
        if row["result"] in merged and row["difficulty"] is not None
    } & found.keys()
    games: list[tuple[datetime, ratings.Game]] = []
    ids: dict[str, int] = {}
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        agent, ticket, label, difficulty = row["agent"], row["ticket"], row["result"], None
        if label in _TICKET_RESULTS:
            once, result, difficulty = "ticket", _TICKET_RESULTS[label], row["difficulty"]
            if (agent, ticket) in folded:
                result, label = result + ratings.FINDING, f"{label}, {found[agent, ticket]}"
        elif label.startswith(ratings.FINDING_LABEL):
            if (agent, ticket) in folded:
                continue
            once, result = "finding", ratings.FINDING  # ADR 24 item 1: one per ticket
        elif row["skill"] == ratings.REVIEWING and label.split(" ")[0] in ratings.VERDICT_RESULTS:
            once, result = label, ratings.VERDICT_RESULTS[label.split(" ")[0]]
            difficulty = row["difficulty"]
        else:
            continue  # a bench game is played from its jobs, below
        if (agent, ticket, once) in seen or (once != "finding" and difficulty is None):
            continue
        seen.add((agent, ticket, once))
        ids[ticket] = row["ticket_id"]
        game = ratings.Game(agent, row["skill"], ticket, difficulty, result, label)
        games.append((_moment(row["at"]), game))
    jobs = conn.execute(
        "SELECT j.run_id, j.agent, j.outcome, j.started, t.id AS ticket_id, t.ticket,"
        " coalesce(t.difficulty_corrected, t.difficulty) AS difficulty FROM jobs j"
        " JOIN tickets t ON t.id = j.ticket_id WHERE j.role = ? AND t.project_id = ?"
        " AND coalesce(t.difficulty_corrected, t.difficulty) IS NOT NULL"
        " ORDER BY j.started, j.id",
        (BENCH, project_id),
    ).fetchall()
    benched: dict[tuple[int, str, str], list[sqlite3.Row]] = {}
    for job in jobs:
        benched.setdefault((job["run_id"], job["ticket"], job["agent"]), []).append(job)
    for (_, ticket, agent), group in benched.items():
        outcomes = [job["outcome"] for job in group]
        if (replay := _bench_game(agent, ticket, group[0]["difficulty"], outcomes)) is not None:
            ids[ticket] = group[0]["ticket_id"]
            games.append((_moment(group[0]["started"]), replay))
    games.sort(key=lambda timed: timed[0])  # stable: same-moment games keep their order
    return games, ids


def replay_ratings(
    conn: sqlite3.Connection, project_id: int, start: Mapping[str, float], at: datetime
) -> list[Replayed]:
    """Recompute every agent's rating from its estimate in ``start``, re-playing its games in
    time order under ADR 24 (item 4). An agent it changes gets new rows after every existing
    one: a ``REPLAY_FROM`` start, then its replayed changes, so the history stays and
    ``standing`` reads the recompute as current. A second recompute writes nothing new."""
    timed, ids = _recorded_games(conn, project_id)
    changes = ratings.rate(start, {}, [game for _, game in timed])
    current, _ = standing(conn, start)
    latest = conn.execute("SELECT max(at) FROM rating_changes").fetchone()[0]
    if latest is not None:
        at = max(at, _moment(latest) + timedelta(microseconds=1))
    replayed: list[Replayed] = []
    rows: list[tuple[str, str, float, float, int | None, str]] = []
    for agent, estimate in start.items():
        mine = [change for change in changes if change.agent == agent]
        after = mine[-1].after if mine else estimate
        games = sum(
            c.skill == ratings.CODING and not c.label.startswith(ratings.FINDING_LABEL)
            for c in mine
        )
        written = not math.isclose(after, current[agent], rel_tol=0, abs_tol=1e-9)
        if written:
            rows.append((agent, ratings.CODING, current[agent], estimate, None, f"{estimate:g}"))
            rows += [(c.agent, c.skill, c.before, c.after, ids[c.ticket], c.label) for c in mine]
        replayed.append(Replayed(agent, current[agent], after, games, written))
    for (agent, skill, before, after, ticket_id, label), moment in zip(
        rows, ratings.moments(at, len(rows)), strict=True
    ):
        prefix = REPLAY_FROM if ticket_id is None else REPLAY
        metrics.add_rating_change(
            conn, agent, skill, before, after, at=moment, ticket_id=ticket_id, result=prefix + label
        )
    return replayed


def rate_finished(s: Session, ticket: str) -> None:
    """Rate a ticket that was merged or blocked (best effort, like every metrics write)."""
    if s.project_id is not None:
        _record(s, rate_ticket, s.project_id, ticket, starting_ratings(s.cfg), now())


CHECKPOINT = router.CHECKPOINT
STAND_IN = "checkpoint-stand-in"  # who does the checkpoint when Claude can't (ADR 16 item 9)


def _authors(s: Session, merged: Iterable[str]) -> list[Agent]:
    """The developers of the merges: each entry is "ticket commit agent"; one from before
    f1-25 has no agent: local's."""
    ids = [m.split()[2] if len(m.split()) > 2 else local_agent(s.cfg) for m in merged]
    return [s.cfg.agents[i] for i in dict.fromkeys(ids) if i in s.cfg.agents]


def checkpoint(s: Session, milestone: str, out: Path | None = None) -> None:
    """Review the unchecked merges. When Claude can't (a limit, or the owner's share of its
    5-hour window), a stand-in does it read-only; with none permitted, it parks and the queue
    goes on (ADR 16 items 4 and 9). ``out`` is a parked checkpoint's note, for its resume."""
    merged = list(s.state.unchecked)
    if (hold := claude_hold(s, now())) is not None:
        if not stand_in_checkpoint(s, milestone, merged, hold):
            _park_support(s, CHECKPOINT, milestone, hold, milestone=milestone)
        return
    out = out or s.run_dir / f"checkpoint-{len(s.report.claude_runs) + 1}.md"
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
    routed = router.route(
        job.role, None, 1, candidates(s, job.role), {}, {}, {}, now(), authors=_authors(s, merged)
    )
    try:
        call_claude(
            s,
            job,
            milestone,
            CHECKPOINT,
            notes=(out,),
            routed=routed,
            park=True,
            parked={"milestone": milestone, "out": _rel(s, out)},
        )
    except Parked:
        return
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
            record_findings(s, milestone, findings, routed.agent.id, prefix)
    s.git.commit_all(
        with_trailers(
            "checkpoint after " + ", ".join(m.split()[0] for m in merged) + " (by Claude)",
            agent=CLAUDE_HEADLESS_AGENT,
        )
    )
    shadow_checkpoint(s, milestone, merged, out)


# --- the checkpoint's shadow (ADR 14 item 12) ----------------------------------------------

SHADOW = "checkpoint-shadow"
SHADOW_NOTE_MAX = 300  # chars of a failed shadow's error kept on its job
_FENCED_JSON = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)


def _answer_json(text: str) -> str:
    """The JSON object in an answer: a fenced block's, else its first ``{`` to its last ``}``."""
    if found := _FENCED_JSON.search(text):
        return found[1]
    start, end = text.find("{"), text.rfind("}")
    return text[start : end + 1] if 0 <= start < end else text


def _merge_files(s: Session, merged: Iterable[str]) -> str:
    """Each merge's ticket and the files it changed: a read-only shadow may run no git."""
    lines = []
    for entry in merged:
        ticket, sha = entry.split()[:2]
        files = [f for f in s.git.run("show", "--name-only", "--format=", sha).splitlines() if f]
        lines.append(f"- {ticket} (tasks/done/{ticket}.md): {', '.join(files)}")
    return "\n".join(lines)


def shadow_checkpoint(s: Session, milestone: str, merged: list[str], out: Path) -> None:
    """Each agent `[roles] checkpoint-shadow` lists reviews the checkpoint's merges, read-only,
    paced by its allowance like any agent. Its findings and readings are recorded on its own
    job and never acted on; a refusal or an error is recorded and the run goes on. Its model
    may be unknown (`copilot-auto`), so ADR 15 item 9's other-model rule isn't checked."""
    agents = [s.cfg.agents[agent_id] for agent_id in s.cfg.roles.get(SHADOW, ())]
    if not agents:
        return
    job = JobSpec(
        role=SHADOW,
        prompt=prompts.CHECKPOINT_SHADOW.format(merges=_merge_files(s, merged)),
        timeout=s.cfg.claude_timeout,
        title=f"{milestone} checkpoint shadow",
    )
    at = now()
    windows = agent_windows(s, agents, at)
    for agent in agents:
        fit = allowance.answer(agent.id, windows.get(agent.id, ()), 0.0, at)
        if fit.ok:
            _shadow(s, agent, job, milestone, out, f"{agent.id}, a shadow: {fit.reason}")
        else:
            s.report.notes.append(f"The checkpoint's shadow on {agent.id} waits: {fit.reason}")
    if not s.git.is_clean():  # a shadow edits nothing: what it left never reaches the repo
        s.git.run("checkout", "-q", "--", ".")
        s.git.run("clean", "-q", "-fd")
        s.report.notes.append("The checkpoint's shadow left changes in the tree; dropped.")


def _shadow(s: Session, agent: Agent, job: JobSpec, milestone: str, out: Path, reason: str) -> None:
    base = out.with_name(f"{out.stem}-shadow-{agent.id}")
    what = "the checkpoint's shadow"
    _, findings, job_id = _read_only_review(s, agent, job, milestone, base, reason, what)
    if job_id is not None:
        record_findings(s, milestone, findings, agent.id, f"{milestone}-S{job_id}-")


def _read_only_review(
    s: Session, agent: Agent, job: JobSpec, milestone: str, base: Path, reason: str, what: str
) -> tuple[JobResult, tuple[Finding, ...], int | None]:
    """One read-only agent's review (``what`` it is, for the notes): its job row, its readings,
    and the findings in its answer (kept as ``base``.json). A refusal is recorded for its
    allowance; the caller records the findings. Returns the result, findings and job row."""
    log = base.with_suffix(".log")
    started = clock()
    s.log(console.start(agent.id, job.role))
    job_id = s.last_job_id = record_start(
        s,
        None,
        milestone,
        job.role,
        agent.id,
        attempt=next_number(s, None, job.role),
        log_path=_rel(s, log),
        routing_reason=reason,
    )
    result = with_progress(
        partial(adapter_for(agent.harness).run, agent, job, s.repo, log, now()),
        partial(_log_running, s, agent.id, job.role),
    )
    _record_readings(s, agent.id, result.readings)
    findings: tuple[Finding, ...] = ()
    note: str | None = None
    if result.ok:
        outcome = "passed"
        answer = base.with_suffix(".json")
        answer.write_text(_answer_json(result.text), encoding="utf-8")
        try:
            findings = parse_checkpoint(answer)
        except ReviewFileError as exc:
            note = f"findings unusable: {exc}"
            s.report.notes.append(f"{what.capitalize()} on {agent.id}: {note}")
    else:
        outcome = "refused" if result.refusal is not None else "failed"
        note = result.text[:SHADOW_NOTE_MAX]
        if result.refusal is not None:
            _record_refusal(s, agent.id, result, what)
        else:
            s.report.notes.append(f"{what.capitalize()} on {agent.id} failed: {note}")
    if job_id is not None:
        _record(
            s,
            metrics.finish_job,
            job_id,
            ended=now().isoformat(),
            outcome=outcome,
            tokens_in=_tokens_in(result),
            tokens_out=_tokens_out(result),
            cost_usd=result.cost_usd,
            steps=result.num_turns,
            note=note,
            session_id=result.session_id,
            model=result.model or None,
        )
    s.log(console.claude_end(agent.id, job.role, result.ok, clock() - started, result.cost_usd))
    return result, findings, job_id


# --- a stand-in for Claude's checkpoint (ADR 16 item 9) ------------------------------------


def stand_in_checkpoint(s: Session, milestone: str, merged: list[str], hold: "Hold") -> bool:
    """A checkpoint Claude can't take, done read-only by the first agent `[roles]
    checkpoint-stand-in` lists that may (its month a cap, not a pace). It is acted on as
    Claude's would be: each finding that isn't a nit becomes a fix ticket (`fix_ticket`),
    routed "local". False when none may, or its job failed: the checkpoint then parks."""
    agents = [s.cfg.agents[agent_id] for agent_id in s.cfg.roles.get(STAND_IN, ())]
    if not agents:
        return False
    at = now()
    windows = agent_windows(s, agents, at)
    routed = router.stand_in(agents, windows, at, _authors(s, merged), hold.reason)
    if routed is None:
        s.report.notes.append(f"No checkpoint stand-in may run now ({hold.reason}).")
        return False
    agent = routed.agent
    s.log("")
    s.log(console.ticket_header(f"{milestone} checkpoint", agent.id, None))
    s.log("Review the last merges: " + ", ".join(m.split()[0] for m in merged))
    job = JobSpec(
        role=CHECKPOINT,
        prompt=prompts.CHECKPOINT_STAND_IN.format(merges=_merge_files(s, merged)),
        timeout=s.cfg.claude_timeout,
        title=f"{milestone} checkpoint",
    )
    base = s.run_dir / f"checkpoint-{len(s.report.claude_runs) + 1}-{agent.id}"
    what = "the stand-in checkpoint"
    result, findings, job_id = _read_only_review(
        s, agent, job, milestone, base, routed.reason, what
    )
    if not result.ok:
        return False
    s.state.interrupted.pop(job_key(CHECKPOINT, CHECKPOINT), None)  # Claude's run is superseded
    prefix = f"{milestone}-C{job_id}-"
    acted, written = [], []
    for finding in findings:
        path = None
        if finding.actionable:
            path = fix_ticket(s.repo, milestone, finding, prefix + finding.id, agent.id)
        if path is not None:
            written.append(path)
            finding = replace(finding, route="local")
        acted.append(finding)
    if job_id is not None:
        record_findings(s, milestone, acted, agent.id, prefix)
    s.state.unchecked = []
    save_state(s.state, s.state_path)
    tickets = ", ".join(p.stem for p in written) or "none"
    s.report.notes.append(
        f"Checkpoint by {agent.id}, standing in for Claude: {len(findings)} findings;"
        f" fix tickets: {tickets}."
    )
    runner_commit(
        s,
        "checkpoint after " + ", ".join(m.split()[0] for m in merged) + f" (by {agent.id},"
        " standing in for Claude)",
    )
    for path in written:
        record_ticket(s, path)
    return True


_FIX_PATH_RE = re.compile(r"[\w-][\w.-]*(?:/[\w-][\w.-]*)*")  # repo-relative, never `..`
_TICKET_ID_RE = re.compile(r"[\w-]+")


def _fix_path(repo: Path, file: str) -> str:
    """The finding's ``file`` as a path in the repo, or "" when it isn't one. f4-25 … f4-29
    named `coucou/factory_dashboard/…`: the repo's own name first, then the real path."""
    if not _FIX_PATH_RE.fullmatch(file):
        return ""
    first, _, rest = file.partition("/")
    if not (repo / file).exists() and first == repo.name and rest:
        file = rest
    return file if (repo / file).exists() else ""


def fix_ticket(repo: Path, milestone: str, finding: Finding, key: str, by: str) -> Path | None:
    """A developer ticket in tasks/ready/ for a stand-in checkpoint's ``finding`` (``key``),
    from the ticket at fault in tasks/done/: its milestone (unless signed off: then
    ``milestone``, the running one), its tests, its difficulty, and the finding's file if it
    exists (else its files). The finding is untrusted text: it goes in the body, quoted, and
    only a checked path reaches the frontmatter. None when no done ticket is at fault."""
    from runner.milestone import signed_off  # runner.milestone imports this module

    if not _TICKET_ID_RE.fullmatch(finding.ticket):
        return None
    source_path = repo / "tasks" / "done" / f"{finding.ticket}.md"
    try:
        source = parse_task(source_path, 1)
    except (OSError, ValueError, yaml.YAMLError):
        return None
    if not signed_off(repo, source.milestone):
        milestone = source.milestone
    file = _fix_path(repo, finding.file)
    missing = finding.file if not file and _FIX_PATH_RE.fullmatch(finding.file) else ""
    prefix = ticket_prefix(milestone)  # a bug's fix is a bug (never signed off)
    numbers = [
        int(found[1])
        for path in (repo / "tasks").glob("*/*.md")
        if (found := re.match(rf"{re.escape(prefix)}-(\d+)-", path.stem))
    ]
    words = re.findall(r"[a-z0-9]+", finding.summary.lower())[:4]
    task_id = f"{prefix}-{max(numbers, default=0) + 1:02d}-fix" + "".join(f"-{w}" for w in words)
    meta: dict[str, Any] = {"id": task_id, "milestone": milestone}
    if milestone == source.milestone:  # its card and place in the queue (ADR 19)
        meta |= {"area": source.area} if source.area else {}
        meta |= {"priority": source.priority} if source.priority is not None else {}
    if source.difficulty is not None:
        meta["difficulty"] = source.difficulty
    meta |= {
        "depends_on": [],
        "files": [file] if file else list(source.files),
        "tests": list(source.tests),
        "finding": key,
    }
    summary = " ".join(finding.summary.split())
    where = (
        f"`{file}`" + (f", line {finding.line}" if finding.line else "") if file else "its files"
    )
    if missing:  # not in backticks: pre-flight would take it for a path the ticket needs
        where += f' (the finding named "{missing}", which isn\'t in the repo)'
    quoted = "\n".join(f"> {line}" for line in (finding.detail or summary).splitlines())
    body = (
        f"### Goal\nFix a checkpoint finding on {finding.ticket}: {summary}\n\n"
        f"### Context\nA {finding.severity} finding ({key}) by {by}, standing in for the lead at"
        f" a checkpoint, on the merge of `tasks/done/{finding.ticket}.md`: in {where}. What it"
        " found is under Finding.\n\n"
        f"### Finding\n{quoted}\n\n"
        "### Done when\n- what the finding describes no longer holds, and a test shows it\n"
        "- the listed `tests:` pass, and fail without the change\n- all gates pass\n"
    )
    frontmatter = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True)
    path = repo / "tasks" / "ready" / f"{task_id}.md"
    path.write_text(f"---\n{frontmatter}---\n\n{body}", encoding="utf-8")
    return path


# --- escalation handling ------------------------------------------------------------


def _only_docs_and_tasks(s: Session) -> bool:
    changed = [line[3:] for line in s.git.run("status", "--porcelain").splitlines()]
    return checks.hook_can_skip(changed) or not changed


REQUEUE_REPAIR_PROMPT = """\
The ticket you requeued, {path}, fails the runner's pre-flight:
{problems}
Fix that file only: name repo-relative paths (`tests/conftest.py`, not `conftest.py`) and only
paths and symbols that exist, or that its `files:` or `tests:` list. If it still fails, the
runner blocks the ticket with these problems."""


def _requeue_problems(s: Session, path: Path) -> list[str]:
    try:
        return preflight(parse_task(path, s.cfg.default_max_diff), s.repo)
    except (OSError, ValueError, yaml.YAMLError) as e:
        return [f"the ticket doesn't parse: {e}"]


def _repair_requeue(s: Session, task: Task, requeued: Path, session: str | None) -> list[str]:
    """f2-F4: a requeue naming a missing path (f1-36, f1-15, f2-06) cost the next run at its
    pre-flight. Pre-flight it now; with problems, the escalation's session gets one turn to
    fix them, as a direction's repair is checked (f1-50). Returns the problems left."""
    if not requeued.is_file() or not (problems := _requeue_problems(s, requeued)):
        return []
    rel = requeued.relative_to(s.repo).as_posix()
    s.log(f"escalation {task.id}: requeue fails pre-flight: {'; '.join(problems)}")
    job = JobSpec(
        role="escalation",
        prompt=REQUEUE_REPAIR_PROMPT.format(
            path=rel, problems="\n".join(f"- {p}" for p in problems)
        ),
        timeout=s.cfg.claude_timeout,
        edit=(rel,),
        commands=GIT_READ_COMMANDS,
        resume=session,
    )
    call_claude(s, job, task.milestone, task.id, ticket=task.id)
    problems = _requeue_problems(s, requeued) if requeued.is_file() else ["the repair removed it"]
    if problems:
        s.report.notes.append(f"Requeue of {task.id} still fails pre-flight after its repair.")
    return problems


def handle_escalation(s: Session, task: Task, logs: Path, reason: str) -> None:
    """The lead's decision on an escalated ticket. While Claude can't take it (a limit, or the
    owner's share of its 5-hour window), it parks and the queue goes on; a parked escalation
    isn't counted (ADR 16 item 4)."""
    escalated = s.tasks_dir("escalated") / task.path.name
    used = s.state.escalations.get(task.id, 0)
    if used >= s.cfg.escalations_per_task:
        block(s, escalated, f"{used} escalations used; last: {reason}")
        return
    resume = {"milestone": task.milestone, "logs": _rel(s, logs), "reason": reason}
    if (hold := claude_hold(s, now())) is not None:
        _park_support(s, "escalation", task.id, hold, **resume)
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
    try:
        result = call_claude(
            s,
            job,
            task.milestone,
            task.id,
            ticket=task.id,
            notes=(decision_path, logs / "escalation.md"),
            process_note=logs / NOTE_FILE,
            park=True,
            parked=resume,
        )
    except Parked:
        s.state.escalations[task.id] = used
        if not used:
            del s.state.escalations[task.id]
        save_state(s.state, s.state_path)
        return
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
    problems: list[str] = []
    if outcome == "requeue":
        requeued = s.tasks_dir("ready") / task.path.name
        problems = _repair_requeue(s, task, requeued, result.session_id)
        if requeued.is_file():
            carry_footers(escalated, requeued)
        if problems and requeued.is_file():  # blocked below as written, never committed to ready/
            escalated.write_text(requeued.read_text(encoding="utf-8"), encoding="utf-8")
            requeued.unlink()
        elif not problems:
            s.git.run("rm", "-q", str(escalated.relative_to(s.repo)))
        # Its next run builds on the branch, unless the lead found the work unusable
        if not problems and decision.get("reset") is True and _has_branch(s.git, branch):
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
    # Only an implemented ticket merges here, so only its commit is found by `Task:`
    task_trailer = {"task": task.id} if outcome == "implemented" else {}
    s.git.commit_all(
        with_trailers(
            f"escalation {task.id}: {outcome or 'no decision'} (by Claude)",
            agent=CLAUDE_HEADLESS_AGENT,
            **task_trailer,
        )
    )
    if problems:
        block(s, escalated, "the requeued ticket fails pre-flight: " + "; ".join(problems))
        return
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
    through ``RESERVE_ENV``; a new command asks again. A yes given ahead with
    `runner run --use-reserve` lasts ``until`` (24 hours, owner 2026-10-04), then the question
    is unanswered again."""

    granted: bool = False
    no: bool = False  # no answer, or no: later lead tickets wait without asking again
    until: datetime | None = None  # a granted yes lapses then; None: for the whole command

    @property
    def yes(self) -> bool:
        if self.granted and self.until is not None and now() >= self.until:
            self.granted, self.until = False, None
        return self.granted

    @yes.setter
    def yes(self, value: bool) -> None:
        self.granted, self.until = value, None

    def grant_until(self, until: datetime) -> None:
        self.granted, self.no, self.until = True, False, until


RESERVE = ReserveAnswer()
RESERVE_ENV = "COUCOU_RUNNER_RESERVE_YES"  # set only by cli's restart: "1", or the yes's end
USE_RESERVE_HOURS = 24  # `runner run --use-reserve` (owner, 2026-10-04)
# The 5-hour question's answer, its own (ADR 16 item 3): a yes to one doesn't answer the other.
FIVE_HOUR = ReserveAnswer()
FIVE_HOUR_ENV = "COUCOU_RUNNER_FIVE_HOUR_YES"
FIVE_HOUR_KIND = "five-hour"  # a lead ticket parked for the owner's 25%, and its owner item
RETRY = "retry"  # a parked entry's flag: a restart tries it again before its reset
CLAUDE = "claude"
# Where Claude's week stands now decides the question: a lead ticket's share of the week
# isn't learned yet, so its expected cost is left at 0.
LEAD_COST = 0.0


REQUEST_POLL_S = 5.0  # how often a waiting question checks the dashboard's answer (f5 D2)


def read_answer(timeout: float, poll: Callable[[], str | None] | None = None) -> str | None:
    """A line the owner types within ``timeout`` seconds; None with no terminal or no answer.
    With ``poll`` (the dashboard's answer, f5 D2), it is asked at once and every
    ``REQUEST_POLL_S`` seconds, and its answer counts as typed, terminal or not."""
    terminal = sys.stdin.isatty()
    if poll is None:
        if not terminal:
            return None
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        return sys.stdin.readline().strip() if ready else None
    deadline = clock() + timeout
    while True:
        if (answer := poll()) is not None:
            return answer
        left = deadline - clock()
        if left <= 0:
            return None
        wait = min(REQUEST_POLL_S, left)
        if not terminal:
            time.sleep(wait)
        elif select.select([sys.stdin], [], [], wait)[0]:
            return sys.stdin.readline().strip()


def _resets(entry: dict[str, Any]) -> datetime:
    return datetime.fromisoformat(str(entry["resets_at"]))


def _due(entry: dict[str, Any], at: datetime) -> bool:
    """Whether a parked job may run: its reset has passed, or a restart tries it at once."""
    return bool(entry.get(RETRY)) or _resets(entry) <= at


def _limits_ahead(
    s: Session, at: datetime, tickets: Collection[str] | None = None, *, five_hour: bool = True
) -> list[datetime]:
    """The resets still ahead of the jobs parked for a limit (of ``tickets``, if given): while
    there is one, Claude is limited and only local work runs. Without ``five_hour``, the jobs
    held only by the owner's share of the 5-hour window are left out: a yes may yet free them."""
    return [resets for resets, _ in _parked_ahead(s, at, tickets, five_hour=five_hour)]


def _parked_ahead(
    s: Session,
    at: datetime,
    tickets: Collection[str] | None = None,
    *,
    five_hour: bool = True,
    rows: Sequence[dispatch.Queued] | None = None,
) -> list[tuple[datetime, str]]:
    """`_limits_ahead`'s resets, each with what it is for: the parked tickets (``tickets``,
    if given) and the parked support jobs (``rows``, else every open one)."""
    found = [
        (_resets(entry), _parked_name(key))
        for key, entry in s.state.parked.items()
        if entry["kind"] != "reserve"
        and (five_hour or not entry.get(FIVE_HOUR_HELD))
        and (tickets is None or key in tickets)
        and not _due(entry, at)
    ]
    for row in open_rows(s) if rows is None else rows:
        if row.kind not in QUEUED or row.not_before is None or _at(row.not_before) <= at:
            continue
        if five_hour or not s.state.queued.get(row_key(row), {}).get(FIVE_HOUR_HELD):
            found.append((_at(row.not_before), _row_name(row)))
    return found


def _parked_name(key: str) -> str:
    """A parked key in words: ``escalation:f1-21`` is "escalation of f1-21"."""
    kind, _, name = key.partition(":")
    return f"{kind} of {name}" if name else kind


def _read_windows(s: Session, prefix: str, at: datetime) -> list[allowance.Window]:
    """The windows of the agents named ``prefix…`` from their latest readings (f1-44):
    capacity 1, usage the share read. A window whose reset has passed since is left out: its
    reading is stale."""
    return _windows_from(_record(s, metrics.latest_readings, prefix) or {}, at)


def _windows_from(readings: Mapping[str, sqlite3.Row], at: datetime) -> list[allowance.Window]:
    """`_read_windows` from ``metrics.latest_readings``' rows."""
    windows = []
    for name, row in readings.items():
        if name not in allowance.NAMED or row["value"] is None or not row["resets_at"]:
            continue
        resets = datetime.fromisoformat(row["resets_at"])
        if resets <= at:
            continue
        kind, length = allowance.NAMED[name]
        windows.append(
            allowance.Window(name, kind, length, resets, 1.0, float(row["value"]), measured=True)
        )
    return windows


def claude_windows(s: Session, at: datetime) -> list[allowance.Window]:
    """Claude's windows from its latest readings, each with what it keeps back: the week's
    reserve for the lead's support roles, the 5-hour window's share for the owner (ADR 16)."""
    return _kept_back(s.cfg, _read_windows(s, "claude-", at))


def _kept_back(cfg: Config, windows: Iterable[allowance.Window]) -> list[allowance.Window]:
    kept = {"seven_day": cfg.claude_reserve, "five_hour": cfg.five_hour_reserve}
    return [replace(w, reserve=kept.get(w.name, 0.0)) for w in windows]


def rested_claude_windows(s: Session, at: datetime) -> list[allowance.Window]:
    """Claude's windows, each resting after a refusal in it (`_rested`)."""
    rows = _record(s, metrics.refusals, f"{CLAUDE}-") or []
    return [_rested(w, rows, at) for w in claude_windows(s, at)]


PROBE_AGENT = "claude-haiku"  # the probe's model, and its readings' agent (f4-07)
PROBE_ROLE = "probe"
STALE_READING = timedelta(minutes=10)


def fresh_reading(s: Session) -> None:
    """Before Claude work, a fresh reading of its windows when the latest is over
    ``STALE_READING`` old (f4-07): readings are only taken while a Claude job runs, so a new
    session went by the last one's and once parked a lead ticket at the owner's share of the
    5-hour window when it had room (the owner, 2026-10-02). At most once per session; a probe
    that reads nothing leaves the stored reading to decide, and says so."""
    if s.probed or not lead_work_ready(s):
        return
    rows = (_record(s, metrics.latest_readings, f"{CLAUDE}-") or {}).values()
    if not rows:
        return  # nothing stored to correct: no window holds Claude back
    stored = max(_at(row["at"]) for row in rows)
    at = now()
    if at - stored < STALE_READING:
        return
    s.probed = True
    log = s.run_dir / f"claude-{PROBE_ROLE}.log"
    job_id = None
    if s.run_id is not None:
        job_id = _record(
            s,
            metrics.start_job,
            s.run_id,
            ticket_id=None,
            milestone_id=None,
            role=PROBE_ROLE,
            agent=PROBE_AGENT,
            attempt=1,
            started=at.isoformat(),
            log_path=_rel(s, log),
        )
    with doing(s, "reading Claude's windows"):
        result = probe(s.repo, log, at)
    _record_readings(s, PROBE_AGENT, result.readings)
    error = "" if result.ok else result.text.strip()[:200]
    why = "" if result.readings else error or "no rate_limit_event"
    if job_id is not None:
        _record(
            s,
            metrics.finish_job,
            job_id,
            ended=now().isoformat(),
            outcome="failed" if why else "passed",
            tokens_in=result.usage.get("input_tokens", 0),
            tokens_cached=result.usage.get("cache_read_input_tokens", 0),
            tokens_out=result.usage.get("output_tokens", 0),
            cost_usd=result.cost_usd,
            steps=result.num_turns,
            note=why or None,
            session_id=result.session_id,
            model=result.model or None,
        )
    if why:
        s.log(
            f"[{PROBE_AGENT}] no fresh reading of Claude's windows ({why}):"
            f" going by the stored one from {stored:%H:%M}"
        )
        return
    read = ", ".join(f"{r.window} {r.utilization:.0%}" for r in result.readings)
    s.log(f"[{PROBE_AGENT}] fresh reading of Claude's windows: {read}")


@dataclass(frozen=True)
class Hold:
    """Why Claude may not take a support job now, and until when."""

    until: datetime
    reason: str
    five_hour: bool  # only the owner's share of the 5-hour window holds it: a yes lifts it


def claude_hold(s: Session, at: datetime) -> Hold | None:
    """Whether a support job (a direction, a checkpoint, an escalation, a review) must wait
    for Claude (ADR 16 item 4): a job parked for a limit, a refusal still resting a window, or
    the owner's share of the 5-hour window with no yes. The week's reserve is theirs to use
    (ADR 15 item 4)."""
    if ahead := _limits_ahead(s, at, five_hour=False):
        return Hold(max(min(ahead), at + timedelta(minutes=1)), "Claude is limited", False)
    windows = rested_claude_windows(s, at)
    kept = {"seven_day", *(("five_hour",) if FIVE_HOUR.yes else ())}
    fit = allowance.answer(CLAUDE, windows, LEAD_COST, at, use_reserve=kept)
    if fit.ok:
        return None
    ends = [
        w.cooldown_until or w.resets_at
        for w in windows
        if not allowance.answer(CLAUDE, [w], LEAD_COST, at, use_reserve=kept).ok
    ]
    until = min(
        (e for e in ends if e is not None), default=at + timedelta(seconds=s.cfg.backoff_min)
    )
    five_hour = not FIVE_HOUR.yes and allowance.reserve_only(
        CLAUDE, windows, LEAD_COST, at, "five_hour"
    )
    return Hold(max(until, at + timedelta(minutes=1)), fit.reason, five_hour)


def _park_support(s: Session, role: str, name: str, hold: Hold, /, **resume: str) -> None:
    """Park a checkpoint or an escalation Claude can't take now (ADR 16 item 4): its row waits
    until ``hold`` ends (f8 D3), and the queue goes on meanwhile. ``resume`` is what it needs
    to start again; its session, if it had one, stays in ``interrupted``."""
    what = role if role == CHECKPOINT else f"{role} of {name}"
    park_row(s, role, name, hold.until, hold.five_hour, **resume)
    s.report.notes.append(f"Parked the {what}: {hold.reason}.")
    s.log(console.paused(RUNNER_AGENT, f"the {what} waits for Claude", hold.until, now()))


def run_queued(s: Session, row: dispatch.Queued, *, escalate: bool) -> None:
    """Run a queued support job (ADR 22). Its row is done when the job ends, unless it parked
    again (its row then waits for the reset); one whose subject is gone is done at once."""
    needs = dict(s.state.queued.get(row_key(row), {}))
    before, s.running_row = s.running_row, row
    try:
        if row.kind == CHECKPOINT:
            if s.state.unchecked:
                out = s.repo / needs["out"] if needs.get("out") else None
                checkpoint(s, str(needs.get("milestone") or row.subject), out)
        elif row.kind == ESCALATION:
            escalated = s.tasks_dir("escalated") / f"{row.subject}.md"
            if escalated.is_file():
                task = parse_task(escalated, s.cfg.default_max_diff)
                logs = s.repo / needs["logs"] if needs.get("logs") else s.run_dir / task.id
                with doing(s, f"escalation of {task.id}"):
                    handle_escalation(s, task, logs, str(needs.get("reason") or row.reason))
        elif row.kind == DIRECTION:
            path = s.tasks_dir("ready") / f"{row.subject}.md"
            if path.is_file() and needs.get("logs"):
                task = parse_task(path, s.cfg.default_max_diff)
                with doing(s, task.id):
                    rec = run_task(s, task, directing=needs)
                after_ticket(s, task, rec, escalate=escalate)
    finally:
        s.running_row = before
    if not _row_waits(s, row.kind, row.subject):
        finish_row(s, row)


def after_ticket(s: Session, task: Task, rec: TaskRecord, *, escalate: bool) -> None:
    """What a ticket's run triggers: its report line, a checkpoint due, an escalation."""
    if rec.result != "parked":  # a parked ticket is reported when it runs
        s.report.tasks.append(rec)
    note_merge(s, task, rec)
    if rec.result in ("escalated", "blocked", "preflight") and escalate:
        logs = rec.logs or s.run_dir / task.id
        _save_thinking(rec, logs, s.repo)
        reason = rec.note or rec.result
        needs = {"milestone": task.milestone, "logs": _rel(s, logs), "reason": reason}
        enqueue(s, ESCALATION, task.id, f"{task.id}: {reason}", **needs)


def wait_for_room(s: Session, what: str) -> None:
    """Before a support job nothing else waits behind (the review): while Claude can't take
    it, ask the 5-hour question once if only the owner's share holds it, else wait for the
    reset (ADR 16 items 3 and 4)."""
    while (hold := claude_hold(s, now())) is not None:
        if hold.five_hour and not FIVE_HOUR.no and (found := _at_five_hour(s, now())):
            _ask_five_hour(s, *found)
            continue
        at = now()
        wait = max(60.0, (hold.until - at).total_seconds() + 60)
        resumes = at + timedelta(seconds=wait)
        s.log(console.paused(RUNNER_AGENT, f"{what} waits for Claude ({hold.reason})", resumes, at))
        wait_for_claude(s, wait, resumes, what)


def _at_the_reserve(s: Session, at: datetime) -> tuple[str, datetime] | None:
    """``("21% of the week left, resets Mon 5 Oct 16:00", reset)`` when a lead ticket is
    refused only because it would dip into Claude's reserve; else None."""
    windows = claude_windows(s, at)
    if not allowance.reserve_only(CLAUDE, windows, LEAD_COST, at, "seven_day"):
        return None
    week = next((w for w in windows if w.name == "seven_day"), None)
    if week is None or week.resets_at is None:
        return None
    resets = week.resets_at.astimezone(at.tzinfo)
    left = f"{1 - week.used:.0%} of the week left"
    return f"{left}, resets {resets:%a} {resets.day} {resets:%b %H:%M}", resets


def _resolve_items(conn: sqlite3.Connection, project_id: int, kind: str, subject: str) -> None:
    """``kind``'s open items about ``subject`` (every one, for an empty subject) resolved."""
    at = now().isoformat()
    for row in metrics.open_owner_items(conn, project_id):
        if row["kind"] == kind and subject in ("", row["subject"]):
            metrics.resolve_owner_item(conn, row["id"], at)


def _resolve_item(s: Session, kind: str, subject: str) -> None:
    if s.project_id is not None:
        _record(s, _resolve_items, s.project_id, kind, subject)


def _reserve_granted(s: Session, task_id: str) -> None:
    """The owner said yes: the ticket's reserve item is answered now, not at the verdict, and
    the run is on the reserve (f1 D3 and D8, amended)."""
    _resolve_item(s, "reserve", task_id)
    if s.run_id is not None:
        _record(s, metrics.set_run_reserve, s.run_id)


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
        with doing(s, "asking you about Claude's reserve"):
            answer = read_answer(max(60.0, (resets - at).total_seconds() + 60))
        if answer is not None and answer.lower() in ("y", "yes"):
            RESERVE.yes = True
            s.log(f"✔ [{RUNNER_AGENT}] Claude's reserve is used for the rest of this run")
            _reserve_granted(s, task.id)
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


def _at_five_hour(s: Session, at: datetime) -> tuple[str, datetime] | None:
    """``("80%", reset)`` when Claude is refused only by the owner's share of its 5-hour
    window (ADR 16 item 1); else None."""
    windows = rested_claude_windows(s, at)
    if not allowance.reserve_only(CLAUDE, windows, LEAD_COST, at, "five_hour"):
        return None
    five = next((w for w in windows if w.name == "five_hour"), None)
    if five is None or five.resets_at is None:
        return None
    return f"{five.used:.0%}", five.resets_at.astimezone(at.tzinfo)


def _ask_five_hour(s: Session, used: str, resets: datetime) -> bool:
    """The 5-hour question (ADR 16 item 3), waiting for an answer until the window resets: it
    is asked only when nothing else can run. True on a yes, which lasts for the command."""
    at = now()
    s.log(
        f"? [{RUNNER_AGENT}] Claude's 5-hour window is at {used} (resets {resets:%H:%M}),"
        " kept for you. Use it for this run? [y/N]"
    )
    with doing(s, "asking you about Claude's 5-hour window"):
        wait = max(60.0, (resets - at).total_seconds() + 60)
        answer = read_answer(wait, poll=partial(_five_hour_requested, s))
    if answer is not None and answer.lower() in ("y", "yes"):
        FIVE_HOUR.yes = True
        s.log(f"✔ [{RUNNER_AGENT}] Claude's 5-hour window is used for the rest of this run")
        _five_hour_granted(s)
        return True
    if answer is not None or _at_five_hour(s, now()) is not None:
        FIVE_HOUR.no = True  # no, or no answer: the rest waits for the resets unasked
    return False


def _five_hour_requested(s: Session) -> str | None:
    """The owner's yes or no to the 5-hour question from the dashboard, if one is open (f5
    D2); taking it finishes the request."""
    from runner.requests import take_five_hour  # runner.requests imports this module

    if s.project_id is None:
        return None
    return _record(s, take_five_hour, s.project_id, now())


def _five_hour_granted(s: Session) -> None:
    """The owner said yes: the 5-hour items are answered, and what waited for it goes now."""
    _resolve_item(s, FIVE_HOUR_KIND, "")
    for entry in s.state.parked.values():
        if entry.get(FIVE_HOUR_HELD):
            entry[RETRY] = True
    save_state(s.state, s.state_path)
    for row in open_rows(s):
        if s.state.queued.get(row_key(row), {}).get(FIVE_HOUR_HELD):
            _unpark_row(s, row)


def _support_goes_first(s: Session, task: Task) -> bool:
    """After a yes: whether checkpoints or escalations it freed go before the ticket that
    asked (f4-01). That ticket isn't parked or counted: it stays in ready/ for the next pick."""
    freed = (
        row.kind in SUPPORT and row.not_before is None and s.state.queued[row_key(row)].get(RETRY)
        for row in open_rows(s)
        if row_key(row) in s.state.queued
    )
    if not any(freed):
        return False
    record_ticket(s, task.path)  # back to its folder's state, no longer running
    s.log(f"[{RUNNER_AGENT}] {task.id} waits its turn: the work parked for the window goes first")
    return True


def at_five_hour(s: Session, task: Task) -> bool:
    """Before a lead ticket: whether it waits for the owner's share of Claude's 5-hour window
    (ADR 16 items 1 and 3). The owner is asked once per command, only when nothing else can
    run (`_next_task`), with its own question and its own yes. With no yes, the ticket parks
    until the window resets and then goes on by itself; meanwhile it is a Needs-you item. A
    yes that frees parked support work lets that go first (`_support_goes_first`)."""
    at = now()
    found = None if FIVE_HOUR.yes else _at_five_hour(s, at)
    if found is None:
        return False
    used, resets = found
    text = (
        f"{task.id} waits for Claude's 5-hour window ({used} used, kept for you):"
        f" it goes on after {resets:%H:%M}, or at once if you answer y to the runner"
    )
    if s.project_id is not None:
        command = f"uv run runner milestone {command_arg(task.milestone)}"
        _record(
            s,
            metrics.upsert_owner_item,
            s.project_id,
            FIVE_HOUR_KIND,
            task.id,
            text=text,
            command=command,
            created=at.isoformat(),
        )
    if not FIVE_HOUR.no and _ask_five_hour(s, used, resets):
        return _support_goes_first(s, task)
    if _at_five_hour(s, now()) is None:  # the window reset while it waited
        _resolve_item(s, FIVE_HOUR_KIND, task.id)
        return False
    s.state.parked[task.id] = {
        "kind": FIVE_HOUR_KIND,
        "branch": "",
        "session_id": "",
        "resets_at": resets.isoformat(),
        "text": text,
        FIVE_HOUR_HELD: True,
    }
    save_state(s.state, s.state_path)
    s.report.notes.append(text)
    reason = f"Claude's 5-hour window is at {used}, kept for you"
    where = f"goes on after {resets:%H:%M}"
    s.log(console.stopped(task.id, "parked", reason, where, waiting_behind(s, task.id)))
    return True


def _waits_for_the_owner(s: Session, at: datetime) -> bool:
    """A lead ticket would stop at a question (the week's or the 5-hour window's)."""
    week = not (RESERVE.yes or RESERVE.no) and _at_the_reserve(s, at) is not None
    five = not (FIVE_HOUR.yes or FIVE_HOUR.no) and _at_five_hour(s, at) is not None
    return week or five


def _next_task(s: Session, ready: list[Task], done: set[str], paused: set[str]) -> Task | None:
    """Parked tickets whose reset has passed go first; while Claude is limited, only work that
    needs no Claude: developer tickets, which local takes. At Claude's reserve or the owner's
    share of its 5-hour window, developer tickets go before lead ones, so a question comes
    only when nothing else can run (ADR 15 item 5, ADR 16 item 3). Each by priority (f5 D6)."""
    at = now()
    cards = _cards(s.repo, ready)
    held = {t.id for t in ready if t.id in s.state.parked}
    due = [t for t in ready if t.id in held and _due(s.state.parked[t.id], at)]
    if (task := pick_next(due, done, paused, cards)) is not None:
        return task
    limited = bool(_limits_ahead(s, at, five_hour=False))
    free = [t for t in ready if t.id not in held and not (limited and t.agent != "developer")]
    task = pick_next(free, done, paused, cards)
    if task is None or task.agent != "lead" or not _waits_for_the_owner(s, at):
        return task
    developers = pick_next([t for t in free if t.agent != "lead"], done, paused, cards)
    return developers or task


def _wait_for_reset(s: Session, ready: list[Task], rows: Sequence[dispatch.Queued]) -> bool:
    """With nothing runnable left, sleep until the earliest reset a parked ticket or queued
    job (of ``rows``) waits for. False when none does: a ticket parked at the reserve waits
    for the owner, not the week."""
    at = now()
    ahead = _parked_ahead(s, at, {t.id for t in ready}, rows=rows)
    if not ahead:
        return False
    first, name = min(ahead)  # the parked job that resumes first is what the wait is for
    wait = max(60.0, (first - at).total_seconds() + 60)
    resumes = at + timedelta(seconds=wait)
    s.state.paused_until = resumes.isoformat()
    save_state(s.state, s.state_path)
    s.log(console.paused(RUNNER_AGENT, "nothing to run without Claude", resumes, at))
    s.report.notes.append(
        f"Paused {wait / 60:.0f} min for a Claude usage limit, with nothing to run."
    )
    wait_for_claude(s, wait, resumes, name)
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


def review_reason(key: str) -> str:
    return f"{short_key(key).upper()}'s tickets are all done"


def _queue_due_review(s: Session) -> None:
    """Queue the first milestone whose review is due (f4-20), marked so for the line's queue;
    a queued review no longer due (signed off, reviewed) is done. None is queued while a
    checkpoint or an escalation is: as under `runner milestone`, the review waits for it."""
    from runner.milestone import due_reviews  # runner.milestone imports this module

    due = due_reviews(s.repo, s.state)
    rows = open_rows(s)
    for row in rows:
        if row.kind == REVIEW and row.subject not in due:
            finish_row(s, row)
    if not due or any(row.kind in SUPPORT for row in rows):
        return
    if s.project_id is not None:
        _record(s, metrics.upsert_milestone, s.project_id, due[0], status=metrics.REVIEW_DUE)
    enqueue(s, REVIEW, due[0], review_reason(due[0]))


def apply_owner_requests(s: Session) -> None:
    """The owner's requests from the dashboard (f5 D2), at each pick: the run is git's one
    writer, so it applies them itself, as their console commands would. A yes to the 5-hour
    window frees what waited for it, as a typed yes does. Best effort, like every write."""
    from runner.requests import apply_requests  # runner.requests imports this module

    granted = FIVE_HOUR.yes
    try:
        lines = apply_requests(s.repo, s.cfg.metrics_db, now())
    except Exception as exc:
        _metrics_failed(s, exc)
        return
    for line in lines:
        s.log(f"[{RUNNER_AGENT}] the owner's request: {line}")
    if lines:
        sync_tickets(s)  # a queued ticket shows in the queue at once
    if FIVE_HOUR.yes and not granted:
        _five_hour_granted(s)


def work_queue(
    s: Session,
    *,
    milestone: str | None = None,
    escalate: bool = True,
    once: bool = False,
    reviews: bool = False,
) -> bool:
    """Work through tasks/ready (one milestone's, if given) and the queued jobs their runs
    trigger: directions, checkpoints and escalations (ADR 22). Each turn runs what
    `dispatch.pick` returns; the next ticket is `_next_task`'s. Returns True if Claude (a lead
    ticket or an escalation) changed the runner, which needs a restart.

    A queued job goes before any ticket, a parked one once its reset has passed; a ticket
    parked for a Claude limit goes first among tickets once its reset has passed. Until then
    only developer tickets run, and with none left the queue sleeps until the earliest reset.
    Claude's windows are checked by each job as it starts (a stand-in, a park), so the pick
    is given none.

    With ``reviews`` (`runner run`, f4-20), a milestone whose tickets are all done queues its
    review, which stops the queue before its next ticket: ``s.report.review`` names it, for
    the command to review. Without ``escalate``, no escalation is queued or run. With
    ``once``, it stops after one ticket and the jobs that ticket queued.
    """
    code = _runner_code(s.repo)
    ran = False  # a ticket ran, for ``once``
    while True:
        if _runner_code(s.repo) != code:
            # m4-07: Python keeps the old modules, so a runner fix made by an escalation
            # only takes effect in a new process. Stop rather than run requeued tasks stale.
            s.report.notes.append(RESTART_NOTE)
            set_activity(s, "restarting after a runner change")
            return True
        set_activity(s, PICKING)
        apply_owner_requests(s)
        fresh_reading(s)
        if reviews:
            _queue_due_review(s)
        ready = load_dir(s.tasks_dir("ready"), s.cfg.default_max_diff)
        if milestone is not None:  # either form of the key (ADR 16 item 6)
            ready = [t for t in ready if short_key(t.milestone) == short_key(milestone)]
        done = task_ids(s.tasks_dir("done"))
        paused = blocked_ids(ready, stopped_ids(s.repo / "tasks"))
        held = _held(s.repo, ready)
        rows = _runnable_rows(s, ready, escalate=escalate, reviews=reviews)
        behind = waiting_rows(s, ready)
        task = _next_task(s, ready, done, paused | held.keys() | behind.keys())
        tickets = [] if task is None else [_dispatch_ticket(s, task, ready)]
        job = dispatch.pick(rows, tickets, dispatch.Windows(), now())
        if once and ran and (job is None or job.kind == dispatch.TICKET):
            return False
        if job is None:
            if _wait_for_reset(s, ready, rows):
                continue
            if paused:
                s.report.notes.append("Paused (dependency escalated): " + ", ".join(sorted(paused)))
            if held:
                s.report.notes.append("Waiting: " + _waits_text(held))
            return False
        if job.kind == REVIEW:
            s.log(f"[runner] {review_reason(job.subject)}: its review is next.")
            s.report.review = job.subject
            return False
        if job.kind != dispatch.TICKET or task is None:  # a ticket: the one it was given
            row = next(r for r in rows if (r.kind, r.subject) == (job.kind, job.subject))
            run_queued(s, row, escalate=escalate)
            continue
        with doing(s, task.id):
            rec = run_task(s, task)
        after_ticket(s, task, rec, escalate=escalate)
        ran = True


def _runnable_rows(
    s: Session, ready: Sequence[Task], *, escalate: bool, reviews: bool
) -> list[dispatch.Queued]:
    """The queued jobs this command runs: escalations only with ``escalate``, reviews only
    with ``reviews`` and while no checkpoint or escalation is queued, and a direction only
    for a ticket of its queue (one whose ticket left ready/ is run, to be done)."""
    rows = open_rows(s)
    support = any(row.kind in SUPPORT for row in rows)
    mine = {t.id for t in ready}
    gone = {row.subject for row in rows} - {p.stem for p in s.tasks_dir("ready").glob("*.md")}
    return [
        row
        for row in rows
        if (row.kind != ESCALATION or escalate)
        and (row.kind != REVIEW or (reviews and not support))
        and (row.kind != DIRECTION or row.subject in mine | gone)
    ]


def _dispatch_ticket(s: Session, task: Task, ready: list[Task]) -> dispatch.Ticket:
    """The ticket `_next_task` chose, as the pick sees it."""
    lead = router.lead_only(task.agent, task.files, tuple(read_protected(s.repo)))
    return dispatch.Ticket(task.id, lead, task_priority(task, _cards(s.repo, ready)))


def run_session(cfg: Config, *, once: bool, dry_run: bool, escalate: bool) -> SessionReport | None:
    """`runner run`: the queue, until it is empty or a milestone's review is due (f4-20)."""
    if dry_run:
        dry_run_plan(cfg)
        return None
    s = open_session(cfg)
    restart = work_queue(s, escalate=escalate, once=once, reviews=True)
    report = close_session(s)
    report.restart = restart
    return report


LIVE = timedelta(minutes=2)  # f1 D3: an older heartbeat means the runner stopped


def live_run(cfg: Config) -> str | None:
    """The run of this project whose heartbeat is under ``LIVE`` old, if any; a bench isn't
    one: it never commits here, so the owner's commands and requests needn't wait for it."""
    if not cfg.metrics_db.is_file():
        return None
    conn = metrics.open_db(cfg.metrics_db)
    try:
        rows = conn.execute(
            "SELECT r.run_dir, r.heartbeat FROM runs r JOIN projects p ON p.id = r.project_id"
            " WHERE p.name = ? AND r.ended IS NULL AND r.heartbeat IS NOT NULL"
            " AND coalesce(r.command, '') != 'bench'",  # a bench works in copies, beside it
            (cfg.repo.name,),
        ).fetchall()
    finally:
        conn.close()
    at = now()
    return next(
        (r["run_dir"] for r in rows if at - datetime.fromisoformat(r["heartbeat"]) < LIVE), None
    )


def queue_ticket(cfg: Config, wanted: str) -> str:
    """Move a ticket from tasks/later/ to tasks/ready/ in a commit of its own (ADR 17 item
    3); ``wanted`` is its id or a unique prefix. Tasks only, so the commit skips the hook.
    Refused while a run is live: the runner commits on the same branch."""
    if (run := live_run(cfg)) is not None:
        raise RunnerError(f"run {run} is running; queue {wanted} once it has stopped")
    return move_to_ready(cfg.repo, wanted)


def move_to_ready(repo: Path, wanted: str) -> str:
    """`queue_ticket`'s move and commit, for a caller that is git's one writer: the command
    once no run is live, or the run itself applying the owner's request (f5 D2)."""
    tasks = repo / "tasks"
    src = find_ticket(tasks, LATER, wanted)
    dst = tasks / "ready" / src.name
    git = Git(repo)
    git.move(src, dst)
    paths = (src.relative_to(repo).as_posix(), dst.relative_to(repo).as_posix())
    git.run("commit", "-q", "--no-verify", "-m", f"queue {src.stem} (by the owner)", "--", *paths)
    return src.stem


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


def _held(repo: Path, ready: list[Task]) -> dict[str, str]:
    """Ready tickets whose milestone waits for another's sign-off (ADR 17 item 4)."""
    from runner.milestone import waits_for  # runner.milestone imports this module

    return held_ids(ready, waits_for(repo, (t.milestone for t in ready)))


def _cards(repo: Path, ready: list[Task]) -> dict[str, int]:
    """Short key -> the priority on its milestone doc's card (f5 D4), for the ready tickets'
    milestones that have a doc."""
    from runner.milestone import card  # runner.milestone imports this module

    found = {}
    for key in {t.milestone for t in ready if t.milestone != BUGS}:
        doc = milestone_file(repo, "milestones", key)
        if doc.is_file():
            found[short_key(key)] = card(key, doc.read_text(encoding="utf-8")).priority
    return found


def _waits_text(held: dict[str, str]) -> str:
    return ", ".join(
        f"{task_id} waits for {key}'s sign-off" for task_id, key in sorted(held.items())
    )


PARKED_REASON = "parked for a Claude limit"


def dry_run_plan(cfg: Config) -> None:
    """`runner run --dry-run` (f8-02): `dispatch.plan`'s list, each job with what it waits for
    and why it is there, and each ticket's pre-flight problems (docs/task-writing.md). Reads
    tasks/, state.json and the metrics database if there is one: any branch, any tree, and no
    run folder or row (f1-33). A due review not queued yet is listed as the run would queue
    it, and a support job an older state.json parked as the row the run makes of it."""
    from runner.milestone import due_reviews  # runner.milestone imports this module

    at = now()
    tasks = cfg.repo / "tasks"
    ready = load_dir(tasks / "ready", cfg.default_max_diff)
    done = task_ids(tasks / "done")
    paused = blocked_ids(ready, stopped_ids(tasks))
    state = load_state(cfg.runs_dir / "state.json")
    queued, readings = _stored_queue(cfg)
    queued += _parked_support(state.parked, at)
    if not any(q.kind in SUPPORT for q in queued):
        reviewing = {q.subject for q in queued if q.kind == REVIEW}
        due = [key for key in due_reviews(cfg.repo, state) if key not in reviewing]
        queued += [dispatch.Queued(REVIEW, key, review_reason(key), at.isoformat()) for key in due]
    behind = {
        q.subject: f"waits for its {q.kind}" for q in queued if q.kind in (DIRECTION, ESCALATION)
    }
    tickets = _dispatch_tickets(cfg.repo, ready, done, paused, state.parked, at, behind)
    windows = dispatch.Windows(
        _kept_back(cfg, _windows_from(readings, at)),
        _limited_until(state.parked, at),
        {
            *(("seven_day",) if RESERVE.yes else ()),
            *(("five_hour",) if FIVE_HOUR.yes else ()),
        },
    )
    _print_plan(dispatch.plan(queued, tickets, windows, at), ready, done, paused, cfg.repo)


def _stored_queue(cfg: Config) -> tuple[list[dispatch.Queued], dict[str, sqlite3.Row]]:
    """The project's open ``work_queue`` rows and Claude's latest readings; none without a
    metrics database, and a read makes none."""
    if not cfg.metrics_db.is_file():
        return [], {}
    conn = metrics.open_db(cfg.metrics_db)
    try:
        project = metrics.find_project(conn, cfg.repo.name)
        rows = [] if project is None else metrics.open_jobs(conn, project)
        readings = metrics.latest_readings(conn, f"{CLAUDE}-")
    finally:
        conn.close()
    return [dispatch.Queued.from_row(row) for row in rows], readings


def _parked_support(parked: Mapping[str, dict[str, Any]], at: datetime) -> list[dispatch.Queued]:
    """Support jobs an older state.json parked, as queue rows (`_queue_parked` makes them at
    the next start)."""
    return [
        dispatch.Queued(
            entry["kind"],
            key if entry["kind"] == DIRECTION else key.partition(":")[2] or entry["kind"],
            PARKED_REASON,
            entry.get("resets_at") or at.isoformat(),
            None if entry.get(RETRY) else entry.get("resets_at"),
        )
        for key, entry in parked.items()
        if entry["kind"] in QUEUED
    ]


def _dispatch_tickets(
    repo: Path,
    ready: list[Task],
    done: set[str],
    paused: set[str],
    parked: Mapping[str, dict[str, Any]],
    at: datetime,
    behind: Mapping[str, str] | None = None,
) -> list[dispatch.Ticket]:
    """The ready tickets in run order (f5 D6), each with what it waits for, as `_next_task`
    sees them: a ticket parked at the reserve waits for the owner, one parked for a limit
    until its reset, one ``behind`` its queued direction or escalation for it."""
    behind = behind or {}
    held = _held(repo, ready)
    cards = _cards(repo, ready)
    protected = tuple(read_protected(repo))
    tickets = []
    for task in sorted(ready, key=lambda t: run_order(t, cards)):
        waiting = [d for d in task.depends_on if d not in done]
        entry = parked.get(task.id)
        waits, not_before = None, None
        if task.id in paused:
            waits = "paused"
        elif task.id in held:
            waits = f"waits for {held[task.id]}'s sign-off"
        elif task.id in behind:
            waits = behind[task.id]
        elif waiting:
            waits = "waiting on " + ", ".join(waiting)
        elif entry is not None and entry["kind"] == "reserve":
            waits = "waits for you: Claude's reserve"
        if entry is not None and entry["kind"] != "reserve":
            not_before = at if entry.get(RETRY) else _resets(entry)
        lead = router.lead_only(task.agent, task.files, protected)
        tickets.append(
            dispatch.Ticket(task.id, lead, task_priority(task, cards), waits, not_before)
        )
    return tickets


def _limited_until(parked: Mapping[str, dict[str, Any]], at: datetime) -> datetime | None:
    """`claude_hold`'s limit: the first reset ahead of a job parked for one, the owner's
    share of the 5-hour window left out."""
    ahead = [
        _resets(entry)
        for entry in parked.values()
        if entry["kind"] != "reserve" and not entry.get(FIVE_HOUR_HELD) and not _due(entry, at)
    ]
    return min(ahead, default=None)


def _job_name(job: dispatch.Pick) -> str:
    if job.kind == dispatch.TICKET:
        return job.subject
    if job.kind == dispatch.REVIEW:
        return f"review {short_key(job.subject).upper()}"
    return f"{job.kind} {job.subject}"


def _print_plan(
    lines: list[dispatch.Line], ready: list[Task], done: set[str], paused: set[str], repo: Path
) -> None:
    """Each job in the order it would run, the next one marked, and each ticket's pre-flight
    problems."""
    print(f"ready: {len(ready)}  done: {len(done)}  paused: {len(paused)}")
    tasks = {t.id: t for t in ready}
    picked = next((line for line in lines if line.waits is None), None)
    for line in lines:
        marker = "->" if line is picked else "  "
        print(f"{marker} {_job_name(line.pick)}: {line.waits or 'runnable'}, {line.pick.reason}")
        if line.pick.kind == dispatch.TICKET:
            for problem in preflight(tasks[line.pick.subject], repo):
                print(f"     pre-flight: {problem}")
    print(f"next: {_job_name(picked.pick) if picked else 'nothing'}")


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
