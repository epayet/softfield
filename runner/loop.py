"""The per-task loop and the session around it (docs/workflow.md)."""

import hashlib
import itertools
import json
import math
import re
import sqlite3
import threading
import time
from collections import Counter
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
    backup,
    checks,
    config,
    console,
    dispatch,
    look,
    messages,
    metrics,
    planner,
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
from runner.config import Config, project_checks, read_protected
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
    difficulty,
    find_ticket,
    full_key,
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
    # The metrics database's copies (F20 D1), None without `[backup]`; a failure is noted once
    backups: backup.Backups | None = None
    backup_failed: bool = False
    picks: int = 0  # jobs run so far, tickets and queued jobs (`run_projects`'s round)

    @property
    def repo(self) -> Path:
        return self.cfg.repo

    @property
    def state_path(self) -> Path:
        return self.cfg.runs_dir / "state.json"

    def tasks_dir(self, name: str) -> Path:
        return self.repo / ".factory" / "tasks" / name

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
    # A ticket parked at the reserve goes by the week's switch again at the next command
    # (ADR 15 item 5, ADR 22 item 4).
    asked = [k for k, entry in state.parked.items() if entry.get("kind") == RESERVE_KIND]
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
    if cfg.backup is not None:
        s.backups = backup.Backups(cfg.metrics_db, cfg.backup)
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


@contextmanager
def _settling(s: Session, role: str, task: Task, session_id: str | None) -> Iterator[None]:
    """The runner's own steps on a Claude job's work once its session ended (check-all, the
    commits, the merge): still the job in flight, so a stop among them is recovered at the next
    start like one inside the session, its work kept on a branch and its session resumed.
    f17-01 (2026-10-16): stopped during the escalation's check-all, its finished work was left
    on main with nothing in flight, and the runner wouldn't start again. A stop keeps it."""
    _set_in_flight(
        s,
        kind=role,
        ticket=task.id,
        subject=task.id,
        milestone=task.milestone,
        branch=s.git.current_branch(),
        agent=s.cfg.agent_for(role).id,
        session_id=session_id,
    )
    yield
    _clear_in_flight(s)


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
    session id for its next run; a local attempt counts as timed out, unless it had finished:
    then its gates run again. Returns the console line that says what was recovered."""
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
    elif not git.run("rev-parse", "--verify", "-q", f"refs/heads/{branch}", check=False).strip():
        # its branch is gone (Softfield's repo was split from Coucou's, ADR 30; or deleted by
        # hand): nothing to put away, and the ticket starts again from main
        state.in_flight = None
        save_state(state, state_path)
        return f"↺ [{agent}] the interrupted {name}'s branch {branch} is gone: it starts again"
    elif git.current_branch() != branch:
        git.checkout(branch)  # the tree's changes come along
    if kind == "local":
        what = f"attempt {job.get('attempt', '?')} of {ticket}"
        done = f"wip {ticket} attempt {job.get('attempt', '?')}"
        # The attempt's own commit at the tip of a clean branch: it had finished, and the stop
        # came during its gates. f19-01's third attempt passed its own check-all at minute 57,
        # was stopped 13 minutes into the gates, and would have been run again (2026-10-13).
        finished = git.is_clean() and git.run("log", "-1", "--format=%s").strip() in (
            done,
            f"{done} (formatted)",
        )
        kept = finished or git.commit_all(
            with_trailers(f"{done} (interrupted)", agent=LOCAL_MODEL_AGENT),
            author=LOCAL_MODEL_AUTHOR,
        )
        if finished:
            state.regate[str(ticket)] = {
                "attempt": job.get("attempt"),
                "agent": agent,
                "job_id": job.get("job_id"),
            }
            after = "it had finished, so only its gates run again"
        else:
            state.timed_out[str(ticket)] = state.timed_out.get(str(ticket), 0) + 1
            after = "it counts as timed out"
    else:
        what = f"{kind} {name}"
        message = WIP_INTERRUPTED.format(name=ticket or kind)
        kept = git.commit_all(with_trailers(message, agent=CLAUDE_HEADLESS_AGENT))
        session = str(job.get("session_id") or "")
        # off main, its branch holds the work even with nothing left to commit (a lead ticket
        # stopped during its check-all: the runner had committed it)
        where = target if target and (kept or branch != MAIN) else ""
        kept = kept or bool(where)  # what the line below says
        state.interrupted[job_key(kind, str(name))] = {"session_id": session, "branch": where}
        after = (
            f"its session {session} resumes on its next run"
            if session
            else "it starts again on its next run"
        )
    if target is not None or git.current_branch() != MAIN:
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
        s.cfg.project_name,
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
            if switch_on(s.state, WEEK, now()):  # the owner lets this run use the reserve
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
    """Every ticket in .factory/tasks/ with its folder's state (f1 D4): the queue the dashboard
    reads.
    A row whose file is in no folder (deleted, like f1-30 by ADR 15, or f4-21 while blocked)
    leaves it, unless it is done."""
    present = set()
    for folder in TICKET_FOLDERS:
        for path in sorted(s.tasks_dir(folder).glob("*.md")):
            record_ticket(s, path)
            present.add(path.stem)
    if s.project_id is not None:
        _record(s, metrics.remove_missing_tickets, s.project_id, present)


def sync_cards(s: Session) -> None:
    """Every milestone doc's card (f5 D4) and title, as ``sync_tickets`` does for tickets: an
    idea with no tickets yet is on the board too. A doc not named by a key is left out, and a
    card whose doc is gone (merged away, dropped, deleted) leaves the board (f6-17)."""
    from runner.milestone import (  # runner.milestone imports this module
        card,
        milestone_doc,
        signoff_sections,
    )

    if s.project_id is None:
        return
    present = set()
    for path in sorted((s.repo / ".factory" / "cards").glob("*.md")):
        try:
            key = milestone_key(path.stem)
        except TaskError:
            continue
        present.add(short_key(key))  # an unreadable doc's card stays where it is
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        found = card(key, text)
        # A review's sheet too: the desk lists a milestone for sign-off once it is stored, and
        # one written outside a review job (or unread when it was written) would never be
        review = milestone_file(s.repo, "reviews", key)
        try:
            sheet = signoff_sections(review.read_text(encoding="utf-8")) if review.is_file() else {}
        except (OSError, UnicodeDecodeError):
            sheet = {}
        _record(
            s,
            metrics.upsert_milestone,
            s.project_id,
            key,
            title=milestone_doc(text).get("title"),
            state=found.state,
            priority=found.priority,
            area=found.area,
            signoff=sheet or None,
        )
    _record(s, metrics.remove_cards, s.project_id, present=present)


PICKING = "picking the next ticket"
# A planner job checks its drafted tickets as Approve will (`runner check-tickets`, read-only)
CHECK_TICKETS = "softfield check-tickets"


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


def check_backup(s: Session) -> None:
    """The metrics database's copy, when one is due (F20 D1): at the run's start, at each pick
    and while it waits. A failure is a console line and a report note (once until a copy
    works again), never an error that stops the run; a later check tries again."""
    if s.backups is None:
        return
    try:
        path = s.backups.check(now())
    except Exception as exc:
        line = (
            f"The metrics database's backup failed ({type(exc).__name__}: {exc}); the run went"
            " on, and a later check tries again."
        )
        s.log(f"[{RUNNER_AGENT}] {line}")
        if not s.backup_failed:
            s.backup_failed = True
            s.report.notes.append(line)
        return
    if path is not None:
        s.backup_failed = False
        s.log(f"[{RUNNER_AGENT}] backed up the metrics database to {path}")


BACKUP_POLL_S = 3600.0  # how often a long sleep stops to check the backup (F20 D1)
WAITING_FOR_CLAUDE = "waiting for Claude"


def wait_for_claude(
    s: Session,
    seconds: float,
    resumes: datetime,
    what: str | None,
    limit: bool = True,
    until: Callable[[], bool] | None = None,
) -> None:
    """Sleep through a pause for Claude (a limit, a passing error, nothing to run without
    it), the run saying so, and for what, until it ends. A wait for a ``limit`` is kept as a
    ``wait`` usage event, from now to ``resumes``: what clogged the line (f3-04). With
    ``until``, it is asked at once and every ``SWITCH_POLL_S`` seconds, and ends the wait. The
    backup is checked every ``BACKUP_POLL_S`` seconds of it, or every poll."""
    if limit:
        at = now().isoformat()
        _record(s, metrics.add_usage_event, RUNNER_AGENT, at, "wait", resets_at=resumes.isoformat())
    waiting = f"{WAITING_FOR_CLAUDE} · {what}" if what else WAITING_FOR_CLAUDE
    with doing(s, f"{waiting} until {resumes:%H:%M}", resumes):
        if until is None:
            step = BACKUP_POLL_S if s.backups is not None else seconds
            left = seconds
            while left > 0:
                time.sleep(min(step, left))
                left -= step
                check_backup(s)
            return
        ends = now() + timedelta(seconds=seconds)
        while (left := (ends - now()).total_seconds()) > 0 and not until():
            time.sleep(min(SWITCH_POLL_S, left))
            check_backup(s)


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
    # The planning room's general thread is about no milestone (f6-01)
    milestone_id = (
        _record(s, metrics.upsert_milestone, s.project_id, milestone) if milestone else None
    )
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
    paused = blocked_ids(ready, stopped_ids(s.repo / ".factory" / "tasks"))
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
PLANNER = dispatch.PLANNER
# The queued jobs whose rows park: the support jobs a ticket's run queues, and the owner's
# messages to the planner (f6-01)
QUEUED = (*SUPPORT, DIRECTION, PLANNER)
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


def _set_reason(conn: sqlite3.Connection, row_id: int, reason: str) -> None:
    conn.execute("UPDATE work_queue SET reason = ? WHERE id = ?", (reason, row_id))


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


def checkpoint_reason(state: State) -> str:
    """A queued checkpoint's reason: the merges Claude re-checks after a stand-in (f8-08),
    then those no checkpoint has reviewed yet."""
    parts = []
    if state.recheck:
        parts.append(f"Claude re-checks {_merges(state.recheck)}, after a stand-in")
    if state.unchecked:
        parts.append(f"after {_merges(state.unchecked)} merged")
    return "; ".join(parts)


def _name_checkpoint(s: Session) -> None:
    """The open checkpoint's reason brought up to date with the merges it now holds."""
    row = find_row(s, CHECKPOINT)
    if row is None or not (reason := checkpoint_reason(s.state)):
        return
    if (row.id or 0) < 0:
        s.unqueued[row.id or 0] = replace(row, reason=reason)
    elif row.id is not None:
        _record(s, _set_reason, row.id, reason)


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
            reason = checkpoint_reason(s.state)
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


def _brief(s: Session, role: str) -> str:
    """What a new lead session starts with (f21 D2, `prompts.brief`). A section that isn't
    there is a note in the session report, once, and the job goes with the rest."""
    # A project's own docs/agents/ (Softfield's) or the shared ones (ADR 30 item 4)
    home = s.repo if (s.repo / prompts.LEAD_DOC).is_file() else config.HOME
    text, missing = prompts.brief(home, role)
    rules = s.repo / config.PROJECT_MD
    if text and rules.is_file():
        text += "This project's own rules (.factory/project.md):\n\n"
        text += rules.read_text(encoding="utf-8").strip() + "\n\n" + prompts.BRIEF_END
    if missing:
        note = (
            f"The {role} prompt went without {', '.join(missing)}: not found in {home}/docs/agents/"
            " (`SECTIONS` in runner/prompts.py names the lead.md headings)."
        )
        if note not in s.report.notes:
            s.report.notes.append(note)
    return text


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

    A ``job.resume`` session carries on an earlier job's with ``job.prompt``: one more turn.

    A new session's prompt starts with the owner's preferences and the lead.md sections its
    role needs (f21 D2); a resumed one has them already."""
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
        if resume:
            prompt = resume_prompt
        else:
            prompt = _brief(s, job.role) + job.prompt + (partial_note if interrupted else "")
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
    elapsed = clock() - started
    s.log(console.claude_end(agent, what, result.ok, elapsed, result.cost_usd, result.timed_out))
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
    kept: Collection[str] = (),
) -> str:
    """The developer's prompt. A retry builds on the branch unless ``reset`` says why it was
    reset (`prompts.RESET`); a requeued ticket's first attempt lists the ``earlier`` run's
    files left on its branch, and a retry after a timeout the files ``kept`` on it."""
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
    cut_short = ""
    if timed_out and not reset:
        cut_short = prompts.TIMED_OUT
        if kept:
            cut_short += prompts.TIMED_OUT_FILES.format(files=", ".join(kept))
    return prompts.local_prompt(task, cut_short + extra)


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
        edit=(".factory/var/runs/**",),
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


def _regate(
    s: Session,
    task: Task,
    rec: TaskRecord,
    logs: Path,
    protected: tuple[str, ...],
    entry: Mapping[str, Any],
) -> GateResult | None:
    """The gates a stop cut off, on the finished attempt's branch: the gate that failed, or
    None when they all pass. The attempt's job, ended as interrupted, gets its real outcome."""
    attempt = entry["attempt"]
    started = time.monotonic()
    if changed := s.git.changed_files(MAIN):
        if autoformat(s.repo, changed, s.cfg.gate_timeout):
            local_wip_commit(s, f"wip {task.id} attempt {attempt} (formatted)")
        context = GateContext(s.repo, s.git, task, MAIN, protected, s.cfg.gate_timeout)
        with doing(s, f"gates · {task.id}"):
            results = run_gates(context)
    else:
        results = [GateResult(NO_CHANGES, False, "The attempt changed no file.")]
    rec.gates_s += time.monotonic() - started
    gates_log = logs / f"gates-{attempt}.txt"
    gates_log.write_text(
        "\n\n".join(f"## {r.name}: {'ok' if r.ok else 'FAIL'}\n{r.output}" for r in results),
        encoding="utf-8",
    )
    failed = next((r for r in results if not r.ok), None)
    outcome = "passed" if failed is None else f"failed gate {failed.name}"
    s.log(f"↺ [{entry['agent']}] attempt {attempt} of {task.id}, gates run again: {outcome}")
    if entry.get("job_id") is not None and s.run_id is not None:
        _record(
            s,
            metrics.regate_job,
            entry["job_id"],
            outcome="passed" if failed is None else "failed",
            gates=[
                {
                    "name": r.name,
                    "ok": r.ok,
                    "seconds": round(r.seconds, 1),
                    "log": _rel(s, gates_log),
                }
                for r in results
            ],
            note="gates run again after a stop",
        )
    return failed


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
    regate = s.state.regate.pop(task.id, None)
    if regate is not None:
        save_state(s.state, s.state_path)
    reset_at_start = _start_attempt(s, branch, "")
    if regate is not None and not reset_at_start and isinstance(regate.get("attempt"), int):
        rec.attempts, timeouts = regate["attempt"], [False] * regate["attempt"]
        last = _regate(s, task, rec, logs, protected, regate)
        if last is None:
            _merge(s, task, rec, str(regate["agent"]))
            return rec
        rec.gate_failures.append(last.name)
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
        timed_out = bool(timeouts and timeouts[-1])
        prompt = _prompt(
            task,
            last,
            timed_out=timed_out,
            direction=direction,
            reset=reset,
            earlier=earlier,
            kept=s.git.changed_files(MAIN) if timed_out and not reset else (),
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
        result = call_claude(s, job, task.milestone, task.id, ticket=task.id, park=True)
    except Parked:
        s.git.checkout(MAIN)
        rec.result = "parked"
        return
    with _settling(s, job.role, task, result.session_id):
        _settle_lead_task(s, task, rec, logs, job)


def _settle_lead_task(s: Session, task: Task, rec: TaskRecord, logs: Path, job: JobSpec) -> None:
    """The lead ticket's work, merged once check-all passes, else blocked on its branch."""
    branch = f"task/{task.id}"
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
        reason = checkpoint_reason(s.state)
        enqueue(s, CHECKPOINT, task.milestone, reason, milestone=task.milestone)


def _ticket_row(
    conn: sqlite3.Connection, project_id: int, ticket: str
) -> tuple[int, int | None] | None:
    """A ticket's row and its milestone's, if it has one: a finding naming a ticket never adds
    one."""
    row = conn.execute(
        "SELECT id, milestone_id FROM tickets WHERE project_id = ? AND ticket = ?",
        (project_id, ticket),
    ).fetchone()
    return (int(row[0]), row[1]) if row else None


def record_findings(
    s: Session,
    milestone: str,
    findings: Iterable[Finding],
    agent: str,
    prefix: str = "",
    *,
    by_ticket: bool = False,
) -> None:
    """Findings on the last Claude job, keyed by ``prefix`` and their ids (ADR 14 item 13).
    With ``by_ticket`` (a checkpoint's), each is the milestone's of the ticket at fault, for
    that milestone's review to judge: a checkpoint's merges may span milestones, and F8's
    findings were all filed under F9's, so its review saw none (f8 review)."""
    if s.project_id is None:
        return
    milestone_id = _record(s, metrics.upsert_milestone, s.project_id, milestone)
    if milestone_id is None:
        return
    for finding in findings:
        found = _record(s, _ticket_row, s.project_id, finding.ticket) if finding.ticket else None
        ticket_id, at_fault = found or (None, None)
        _record(
            s,
            metrics.add_finding,
            at_fault if by_ticket and at_fault is not None else milestone_id,
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


RECHECK_NOTE = (
    "\n\nA stand-in reviewed {merges} while you were out: this checkpoint checks them again."
    " It already filed findings on {filed}; its fix tickets carry `finding:`. Don't file those"
    " again."
)


def _recheck_note(state: State) -> str:
    """What Claude's re-check is told of the stand-in's work: only checked ids and paths."""
    if not state.recheck:
        return ""
    filed = ", ".join(
        f"{ticket} ({file})" if file else ticket for ticket, file in state.recheck_filed
    )
    return RECHECK_NOTE.format(merges=_merges(state.recheck), filed=filed or "nothing")


def checkpoint(s: Session, milestone: str, out: Path | None = None) -> None:
    """Review the unchecked merges, and those only a stand-in reviewed (f8-08). When Claude
    can't (a limit, or the owner's share of its 5-hour window), a stand-in reviews the
    unchecked ones read-only and the checkpoint parks, for Claude to check them all again once
    it may; the queue goes on (ADR 16 items 4 and 9). ``out`` is a parked checkpoint's note,
    for its resume."""
    merged = list(dict.fromkeys([*s.state.recheck, *s.state.unchecked]))
    if (hold := claude_hold(s, now())) is not None:
        if s.state.unchecked:  # never the stand-in again on what it reviewed
            stand_in_checkpoint(s, milestone, list(s.state.unchecked), hold)
        _park_support(s, CHECKPOINT, milestone, hold, milestone=milestone)
        _name_checkpoint(s)
        return
    out = out or s.run_dir / f"checkpoint-{len(s.report.claude_runs) + 1}.md"
    findings_out = out.with_suffix(".json")
    job = JobSpec(
        role="checkpoint",
        prompt=prompts.CHECKPOINT.format(
            merges="\n".join(f"- {m.split()[0]}: `git show {m.split()[1]}`" for m in merged),
            out=out.relative_to(s.repo).as_posix(),
            findings=findings_out.relative_to(s.repo).as_posix(),
        )
        + _recheck_note(s.state),
        timeout=s.cfg.claude_timeout,
        edit=(".factory/tasks/ready/**", "docs/agents/developer.md", ".factory/var/runs/**"),
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
    s.state.unchecked, s.state.recheck, s.state.recheck_filed = [], [], []
    save_state(s.state, s.state_path)
    if out.is_file():
        s.report.notes.append("Checkpoint: " + out.read_text(encoding="utf-8").strip())
    try:
        findings = parse_checkpoint(findings_out)
    except ReviewFileError as exc:
        s.report.notes.append(f"Checkpoint findings unusable: {exc}")
    else:
        # Keyed by the checkpoint's job, unique in the milestone (the review judges them).
        # Every one is recorded: the prompt names what a stand-in filed, and a filter on
        # (ticket, file) dropped a new problem in a file it had flagged (f8 review).
        if s.last_job_id is not None:
            prefix = f"{milestone}-C{s.last_job_id}-"
            record_findings(s, milestone, findings, routed.agent.id, prefix, by_ticket=True)
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
        lines.append(f"- {ticket} (.factory/tasks/done/{ticket}.md): {', '.join(files)}")
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
        record_findings(s, milestone, findings, agent.id, f"{milestone}-S{job_id}-", by_ticket=True)


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
    Claude's would be: each finding that isn't a nit goes in a fix ticket (`fix_tickets`, one
    per ticket at fault and kind of fix), routed "local"; its merges then wait for Claude's
    re-check (f8-08). False when none may, or its job failed: the merges stay unchecked."""
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
    filed = fix_tickets(s.repo, milestone, {prefix + f.id: f for f in findings}, agent.id)
    written = list(dict.fromkeys(filed.values()))
    acted = [replace(f, route="local") if prefix + f.id in filed else f for f in findings]
    if job_id is not None:
        record_findings(s, milestone, acted, agent.id, prefix, by_ticket=True)
    # Its merges wait for Claude's re-check (f8-08), with what it filed: checked ids only
    s.state.recheck = list(dict.fromkeys([*s.state.recheck, *merged]))
    for f in acted:
        safe = _TICKET_ID_RE.fullmatch(f.ticket) and (not f.file or _FIX_PATH_RE.fullmatch(f.file))
        if safe and [f.ticket, f.file] not in s.state.recheck_filed:
            s.state.recheck_filed.append([f.ticket, f.file])
    s.state.unchecked = [m for m in s.state.unchecked if m not in merged]
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


def fix_tickets(
    repo: Path, milestone: str, findings: Mapping[str, Finding], by: str
) -> dict[str, Path]:
    """The fix tickets for a stand-in checkpoint's ``findings`` (by key) that aren't nits: one
    per ticket at fault and kind of fix, with all of its findings (f8-09: Copilot's two
    checkpoints filed seven, five about one weak assertion each). Each filed key's ticket."""
    groups: dict[tuple[str, str], dict[str, Finding]] = {}
    for key, finding in findings.items():
        if finding.actionable:
            groups.setdefault((finding.ticket, finding.kind), {})[key] = finding
    filed: dict[str, Path] = {}
    for group in groups.values():
        if (path := fix_ticket(repo, milestone, group, by)) is not None:
            filed |= dict.fromkeys(group, path)
    return filed


def fix_ticket(repo: Path, milestone: str, findings: Mapping[str, Finding], by: str) -> Path | None:
    """A developer ticket in .factory/tasks/ready/ for a stand-in checkpoint's ``findings`` (by
    key), on one ticket at fault and of one kind, from that ticket in .factory/tasks/done/: its
    milestone (unless signed off: then ``milestone``, the running one), its tests, its difficulty,
    and the findings' files that exist (else its files). A `test` kind is `tests_only`: tests in
    `files:`, which pass on main. The findings are untrusted text: they go in the body, quoted, and
    only checked paths reach the frontmatter. None when no done ticket is at fault."""
    from runner.milestone import signed_off  # runner.milestone imports this module

    first = next(iter(findings.values()))
    tests_only = first.kind == "test"
    if not _TICKET_ID_RE.fullmatch(first.ticket):
        return None
    source_path = repo / ".factory" / "tasks" / "done" / f"{first.ticket}.md"
    try:
        source = parse_task(source_path, 1)
    except (OSError, ValueError, yaml.YAMLError):
        return None
    if not signed_off(repo, source.milestone):
        milestone = source.milestone
    places = {key: _fix_path(repo, f.file) for key, f in findings.items()}
    named = [p for p in places.values() if p and (p.startswith("tests/") or not tests_only)]
    files = list(dict.fromkeys(named))
    tests = list(source.tests)
    if tests_only:
        files = files or [t for t in source.tests if t.startswith("tests/")] or tests
        tests = list(dict.fromkeys([*(f for f in files if is_test_file(f)), *tests]))
    prefix = ticket_prefix(milestone)  # a bug's fix is a bug (never signed off)
    numbers = [
        int(found[1])
        for path in (repo / ".factory" / "tasks").glob("*/*.md")
        if (found := re.match(rf"{re.escape(prefix)}-(\d+)-", path.stem))
    ]
    words = re.findall(r"[a-z0-9]+", first.summary.lower())[:4]
    task_id = f"{prefix}-{max(numbers, default=0) + 1:02d}-fix" + "".join(f"-{w}" for w in words)
    meta: dict[str, Any] = {"id": task_id, "milestone": milestone}
    if milestone == source.milestone:  # its card and place in the queue (ADR 19)
        meta |= {"area": source.area} if source.area else {}
        meta |= {"priority": source.priority} if source.priority is not None else {}
    if source.difficulty is not None:
        meta["difficulty"] = source.difficulty
    meta |= {
        "depends_on": [],
        "files": files or list(source.files),
        "tests": tests,
        "finding": ", ".join(findings),
    }
    if tests_only:
        meta["tests_only"] = True
    summaries = {key: " ".join(f.summary.split()) for key, f in findings.items()}
    places_text, quotes = [], []
    for key, finding in findings.items():
        file = places[key]
        where = f"`{file}`" + (f", line {finding.line}" if finding.line else "") if file else ""
        where = where or ("its tests" if tests_only else "its files")
        if not file and _FIX_PATH_RE.fullmatch(finding.file):  # unquoted: pre-flight would
            where += f' (the finding named "{finding.file}", which isn\'t in the repo)'  # want it
        places_text.append(f"- {key}, {finding.severity}: in {where}.")
        detail = finding.detail or summaries[key]
        quotes.append(
            f"{key}: {summaries[key]}\n" + "\n".join(f"> {x}" for x in detail.splitlines())
        )
    count = "a checkpoint finding" if len(findings) == 1 else f"{len(findings)} checkpoint findings"
    on = f"{first.ticket}'s tests" if tests_only else first.ticket
    if tests_only:
        kind = (
            " It found the code right and its tests weak: change only tests. They pass on"
            " main's code, as they should."
        )
        done = (
            "- each finding above no longer holds: the tests it names check content, and would"
            " fail if the code were wrong\n- the listed `tests:` pass, with no change outside"
            " `tests/`\n- all gates pass\n"
        )
    else:
        kind = ""
        done = (
            "- what each finding describes no longer holds, and a test shows it\n"
            "- the listed `tests:` pass, and fail without the change\n- all gates pass\n"
        )
    body = (
        f"### Goal\nFix {count} on {on}: {'; '.join(summaries.values())}\n\n"
        f"### Context\nBy {by}, standing in for the lead at a checkpoint, on the merge of"
        f" `.factory/tasks/done/{first.ticket}.md`.{kind} What it found is under Finding:\n"
        + "\n".join(places_text)
        + "\n\n### Finding\n"
        + "\n\n".join(quotes)
        + f"\n\n### Done when\n{done}"
    )
    frontmatter = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True)
    path = repo / ".factory" / "tasks" / "ready" / f"{task_id}.md"
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
    # One stopped part-way is the same escalation when it resumes: not counted again (one
    # parked for a limit was taken off the count when it parked)
    earlier = s.state.interrupted.get(job_key("escalation", task.id))
    resuming = earlier is not None and earlier.get("cause") != "limit"
    if used >= s.cfg.escalations_per_task and not resuming:
        block(s, escalated, f"{used} escalations used; last: {reason}")
        return
    resume = {"milestone": task.milestone, "logs": _rel(s, logs), "reason": reason}
    if (hold := claude_hold(s, now())) is not None:
        _park_support(s, "escalation", task.id, hold, **resume)
        return
    s.state.escalations[task.id] = used + (0 if resuming else 1)
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
            tests=" ".join(project_checks(s.repo).test_dirs),  # the project's own (ADR 30)
            thinking=", ".join(p.relative_to(s.repo).as_posix() for p in rec_sessions)
            or "not available",
        ),
        timeout=s.cfg.claude_timeout,
        edit=(ANY,),
        # `finish` checks out the ticket's branch itself: only that one (ADR 15 item 8)
        commands=(*CHECK_COMMANDS, *GIT_READ_COMMANDS, f"git checkout {branch}"),
    )
    decision_path = logs / "decision.json"
    if earlier is None:  # only this escalation's decision counts (a parked one resumes too)
        decision_path.unlink(missing_ok=True)
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
    with _settling(s, job.role, task, result.session_id):
        _settle_escalation(s, task, logs, job, result, decision_path)


def _settle_escalation(
    s: Session, task: Task, logs: Path, job: JobSpec, result: JobResult, decision_path: Path
) -> None:
    """What the escalation's decision does. A session cut off at its time limit is judged by
    the decision it wrote, its work by check-all as any other's (f17-01 wrote "implemented",
    then was cut off waiting on its own second check-all); one with no decision keeps its
    work off main."""
    escalated = s.tasks_dir("escalated") / task.path.name
    branch = f"task/{task.id}"
    try:
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        decision = {}
    outcome = decision.get("outcome")
    if result.timed_out:
        agent = s.cfg.agent_for(job.role).id
        said = f"it had decided {outcome}: check-all decides" if outcome else "with no decision"
        s.log(f"  ↳ [{agent}] cut off at its time limit, {said}")
        s.report.notes.append(f"Escalation {task.id} was cut off at its time limit, {said}.")
    on = s.git.current_branch()
    if not outcome and on == MAIN and not _only_docs_and_tasks(s):
        kept = f"escalation/{task.id}"
        s.git.run("checkout", "-q", "-B", kept)
        s.git.commit_all(
            with_trailers(f"escalation {task.id}: no decision", agent=CLAUDE_HEADLESS_AGENT)
        )
        s.git.checkout(MAIN)
        block(s, escalated, f"the escalation ended with no decision; its work is on {kept}")
        return
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


# The owner's two switches (ADR 22 item 4, f8 D4), one per window (ADR 16 item 3), in
# state.json: off (the default) parks a lead ticket at the window's reserve, on lets it run.
# The console asks nothing.
WEEK = "week"
FIVE_HOUR = "five_hour"
SWITCHES = {
    WEEK: "Let the factory use the week's reserve",
    FIVE_HOUR: "Let the factory use your 25% of the 5-hour window",
}
USE_RESERVE_HOURS = 24  # on lasts this long, then turns itself off (owner, 2026-10-04)
SWITCH_POLL_S = 60.0  # how often a wait for the owner's 25% checks for the switch (f5 D2)
HOLD_POLL_S = 5.0  # how often the hold for the owner applies their requests (f6-22)
FIVE_HOUR_KIND = "five-hour"  # a lead ticket parked for the owner's 25%, and its owner item
RESERVE_KIND = "reserve"  # a lead ticket parked at the week's reserve, a lapsed switch's item
RETRY = "retry"  # a parked entry's flag: a restart tries it again before its reset
CLAUDE = "claude"
# Where Claude's week stands now decides the park: a lead ticket's share of the week
# isn't learned yet, so its expected cost is left at 0.
LEAD_COST = 0.0


def _switch_ends(state: State, switch: str) -> datetime | None:
    since = state.switches.get(switch)
    return None if since is None else _at(since) + timedelta(hours=USE_RESERVE_HOURS)


def switch_on(state: State, switch: str, at: datetime) -> bool:
    """Whether ``switch`` is on at ``at``: turned on less than 24 hours before."""
    ends = _switch_ends(state, switch)
    return ends is not None and at < ends


def set_switch(state: State, switch: str, on: bool, at: datetime) -> str:
    """Turn ``switch`` on for 24 hours from ``at`` (again, if it was on), or off; in words."""
    if not on:
        state.switches.pop(switch, None)
        return f"“{SWITCHES[switch]}” is off"
    state.switches[switch] = at.isoformat()
    ends = at + timedelta(hours=USE_RESERVE_HOURS)
    return f"“{SWITCHES[switch]}” is on until {ends:%a %H:%M}"


def lapse_switches(state: State, at: datetime) -> list[str]:
    """The switches whose 24 hours are over, turned off: the runner asks again for each."""
    lapsed = [s for s in SWITCHES if s in state.switches and not switch_on(state, s, at)]
    for switch in lapsed:
        del state.switches[switch]
    return lapsed


def switch_command(switch: str) -> str:
    """The console command that turns ``switch`` on (`runner reserve`)."""
    return f"softfield reserve {switch.replace('_', '-')} on"


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
        parks = row.kind in QUEUED or row.kind == REVIEW  # a review's row parks too (F53 D1)
        if not parks or row.not_before is None or _at(row.not_before) <= at:
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
    five_hour: bool  # only the owner's share of the 5-hour window holds it: its switch lifts it


def claude_hold(s: Session, at: datetime, *, owners: bool = False) -> Hold | None:
    """Whether a support job (a direction, a checkpoint, an escalation, a review) must wait
    for Claude (ADR 16 item 4): a job parked for a limit, a refusal still resting a window, or
    the owner's share of the 5-hour window with its switch off. The week's reserve is theirs
    to use (ADR 15 item 4). The ``owners`` own work (a planner job) may use both reserves
    (ADR 20 item 2)."""
    if ahead := _limits_ahead(s, at, five_hour=False):
        return Hold(max(min(ahead), at + timedelta(minutes=1)), "Claude is limited", False)
    windows = rested_claude_windows(s, at)
    five_on = owners or switch_on(s.state, FIVE_HOUR, at)
    kept = {"seven_day", *(("five_hour",) if five_on else ())}
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
    five_hour = not five_on and allowance.reserve_only(CLAUDE, windows, LEAD_COST, at, "five_hour")
    return Hold(max(until, at + timedelta(minutes=1)), fit.reason, five_hour)


def _park_support(s: Session, role: str, name: str, hold: Hold, /, **resume: str) -> None:
    """Park a checkpoint or an escalation Claude can't take now (ADR 16 item 4): its row waits
    until ``hold`` ends (f8 D3), and the queue goes on meanwhile. ``resume`` is what it needs
    to start again; its session, if it had one, stays in ``interrupted``."""
    what = role if role == CHECKPOINT else f"{role} of {name}"
    park_row(s, role, name, hold.until, hold.five_hour, **resume)
    s.report.notes.append(f"Parked the {what}: {hold.reason}.")
    s.log(console.paused(RUNNER_AGENT, f"the {what} waits for Claude", hold.until, now()))


def park_review(s: Session, milestone: str) -> bool:
    """Before a round of a review `runner run` started (F53 D1): when Claude can't take it
    now, its row parks until the hold ends, as a checkpoint's does, and the queue goes on with
    the developers' tickets. Returns whether it parked. A parked review is no stop: its rounds
    stay in ``State.review_counts``, for it to go on from the round it was at."""
    if (hold := claude_hold(s, now())) is None:
        return False
    _park_support(s, REVIEW, milestone, hold)
    return True


def _plan_branch(s: Session, branch: str) -> bool:
    """Check out a card's plan branch for its planner job (f6 D4): caught up with main, or
    new from main. Returns whether it is new. One that clashes with main is used as it is."""
    if not _has_branch(s.git, branch):
        s.git.run("checkout", "-q", "-b", branch, MAIN)
        return True
    if not _catch_up(s, branch):
        s.report.notes.append(f"{branch} clashes with {MAIN}: the planner drafted on it as it is.")
        s.git.checkout(branch)
    return False


def _commit_drafts(s: Session, thread: str, branch: str, subject: str, new: bool) -> None:
    """After a planner job: commit its drafts on ``branch`` and go back to main (f6 D4). What
    it changed outside the drafts' folders and its card's ready tickets (a replan's, f6-13) is
    dropped; a new branch with no drafts goes."""
    if s.git.current_branch() != branch:  # never commit drafts anywhere else
        s.git.checkout(MAIN)
        return
    status = s.git.run("status", "--porcelain", "--untracked-files=all").splitlines()
    stray = [(line[:2], line[3:]) for line in status if not planner.is_draft(line[3:], thread)]
    for code, path in stray:
        if code == "??":
            (s.repo / path).unlink(missing_ok=True)
        else:
            s.git.run("checkout", "-q", "HEAD", "--", path)
    if stray:
        dropped = ", ".join(path for _, path in stray)
        s.report.notes.append(f"The planner's {subject} changed {dropped}, outside its drafts.")
    s.git.commit_all(
        with_trailers(f"planner {subject}: drafts (by Claude)", agent=CLAUDE_HEADLESS_AGENT)
    )
    s.git.checkout(MAIN)
    if new and not s.git.run("rev-list", f"{MAIN}..{branch}").strip():
        s.git.run("branch", "-q", "-D", branch)


def _auto_merge(s: Session, reply: planner.Reply, thread: str) -> planner.Reply:
    """F49 D1: the reply's merges, applied on main now (the planner job left it there): each
    one applied is stored as such, so the owner is never asked; one the runner can't apply
    waits for the owner's Approve, and the reply says why."""
    from runner.requests import auto_merge  # runner.requests imports this module

    if s.db is None or s.project_id is None or s.git.current_branch() != MAIN:
        return reply
    proposals, why = [], []
    for proposal in reply.proposals:
        if proposal.get("kind") == planner.MERGE:
            try:
                refused = auto_merge(s.repo, s.db, s.project_id, now(), proposal, thread)
            except Exception as exc:  # a merge never stops the run: the owner can approve it
                refused = f"{type(exc).__name__}: {exc}"
            if refused is None:
                proposal = {**proposal, planner.APPLIED: True}
            else:
                what = str(proposal.get("title") or proposal.get("id") or "a merge")
                why.append((f"The runner didn't apply {what}", refused))
        proposals.append(proposal)
    if why and reply.points:  # F41 D2: the text folds under the points, so this is one too
        said = tuple(
            {
                "n": len(reply.points) + i,
                "title": title,
                "answer": f"{refused}.",
                "action": "It waits for your Approve.",
            }
            for i, (title, refused) in enumerate(why, 1)
        )
        return replace(reply, points=reply.points + said, proposals=tuple(proposals))
    lines = [f"{title}: {refused}. It waits for your Approve." for title, refused in why]
    text = "\n\n".join([reply.text.rstrip(), *lines]) if why else reply.text
    return replace(reply, text=text, proposals=tuple(proposals))


MERGED_LATELY = 20  # the merged tickets whose durations give the planner its median (F21 D1)


def ticket_minutes(conn: sqlite3.Connection, project_id: int) -> list[float]:
    """The minutes of work each of the project's last 20 merged tickets took, the latest
    first: its finished jobs added up (attempts, directions, escalations). A read."""
    rows = conn.execute(
        "SELECT j.ticket_id, j.started, j.ended FROM jobs j"
        " JOIN tickets t ON t.id = j.ticket_id"
        " WHERE t.project_id = ? AND t.state = 'done'"
        " AND j.started IS NOT NULL AND j.ended IS NOT NULL"
        " ORDER BY j.ended DESC, j.id DESC",
        (project_id,),
    ).fetchall()
    minutes: dict[int, float] = {}
    for row in rows:
        ticket = row["ticket_id"]
        if ticket not in minutes and len(minutes) == MERGED_LATELY:
            continue
        took = (_at(row["ended"]) - _at(row["started"])).total_seconds() / 60
        minutes[ticket] = minutes.get(ticket, 0.0) + took
    return list(minutes.values())


def _all_cards(repo: Path) -> list[tuple[str, str, int]]:
    """Every milestone doc's card as (short key, state, priority), as `sync_cards` reads them."""
    from runner.milestone import card  # runner.milestone imports this module

    found = []
    for path in sorted((repo / ".factory" / "cards").glob("*.md")):
        try:
            key = milestone_key(path.stem)
            text = path.read_text(encoding="utf-8")
        except (TaskError, OSError, UnicodeDecodeError):
            continue
        if key != BUGS:
            read = card(key, text)
            found.append((short_key(key), read.state, read.priority))
    return found


def work_stands(
    cfg: Config, state: State, minutes: Sequence[float], behind: Mapping[str, str] | None = None
) -> str:
    """Where the work stands, for a planner job's prompt (F21 D1), from `dry_run_plan`'s
    inputs: the job in flight, the ready tickets in run order with what each waits for
    (``behind`` its queued direction or escalation), every card, and ``minutes``
    (`ticket_minutes`). It reads .factory/tasks/ and .factory/cards/ and writes nothing."""
    tasks = cfg.repo / ".factory" / "tasks"
    ready = load_dir(tasks / "ready", cfg.default_max_diff)
    done = task_ids(tasks / "done")
    paused = blocked_ids(ready, stopped_ids(tasks))
    by_id = {t.id: t for t in ready}
    listed = [
        planner.ReadyTicket(
            ticket.id,
            by_id[ticket.id].milestone,
            "lead" if ticket.lead else "developer",
            ticket.priority,
            # a dependency in the block's words: "waits for <id>"
            ticket.waits and ticket.waits.replace("waiting on ", "waits for ", 1),
        )
        for ticket in _dispatch_tickets(cfg.repo, ready, done, paused, state.parked, now(), behind)
    ]
    return planner.where_it_stands(state.in_flight, listed, _all_cards(cfg.repo), minutes)


def _name_card(s: Session, thread: str, title: str) -> None:
    """F31 D7: the lead's ``title`` for a card still an idea on main: its doc's heading alone,
    rewritten in a commit of its own, and its board row's title; the file and the key stay.
    On any other card, nothing. A title that would set the card (its state, its area, what it
    waits for) is ignored, with a note. The heading is the only line of main a planner's reply
    changes."""
    from runner.milestone import card, milestone_after, milestone_doc  # it imports this module

    if thread == planner.GENERAL or s.git.current_branch() != MAIN:
        return
    path = milestone_file(s.repo, "cards", full_key(s.repo, thread))
    if not path.is_file():
        return
    before = path.read_text(encoding="utf-8")
    was = card(path.stem, before)
    if was.state != planner.IDEA:
        return
    doc = planner.named_card(before, title)
    if doc is None or doc == before:
        return
    name = planner.thread_name(thread)
    same = card(path.stem, doc) == was and milestone_after(doc) == milestone_after(before)
    if not same or milestone_doc(doc).get("title") != title:
        s.report.notes.append(f"The lead's title {title!r} can't be {name}'s heading: ignored.")
        return
    rel = _rel(s, path)
    path.write_text(doc, encoding="utf-8")
    try:
        s.git.run("add", "--", rel)
        message = with_trailers(f"{name} named by the lead", agent=CLAUDE_HEADLESS_AGENT)
        s.git.run("commit", "-q", "--no-verify", "-m", message, "--", rel)
    except GitError as exc:  # a name never stops the run: the card keeps its heading
        s.git.run("reset", "-q", "--", rel, check=False)
        path.write_text(before, encoding="utf-8")
        s.report.notes.append(f"The lead's title for {name} wasn't committed: {exc}.")
        return
    if s.project_id is not None:
        _record(s, metrics.upsert_milestone, s.project_id, path.stem, title=title)


def run_planner(s: Session, row: dispatch.Queued) -> None:
    """Answer one of the owner's messages (ADR 20 items 1–4, f6 D1–D3): a planner job on its
    thread's Claude session (a new one for a new thread), its reply's points and proposals
    recorded, and a Needs-you item until the owner answers. A card's job drafts on its plan
    branch, which the runner commits (f6 D4). It may use the owner's 25% of the 5-hour
    window; at a limit its row parks and the message waits. A message whose request or
    project is gone is done."""
    if s.project_id is None:
        return
    try:
        thread, request_id = planner.request_of(row.subject)
        request = _record(s, metrics.find_request, request_id)
        text, comments = planner.message(request["value"] if request else None)
    except planner.PlannerError as exc:
        s.report.notes.append(f"The planner's {row.subject} can't run: {exc}.")
        return
    if (hold := claude_hold(s, now(), owners=True)) is not None:
        _park_support(s, PLANNER, row.subject, hold)
        return
    at = now().isoformat()
    found = _record(s, metrics.planner_thread, s.project_id, thread, at)
    if found is None:
        return
    branch = planner.plan_branch(thread)
    threads = _record(s, metrics.thread_cards, s.project_id) or []
    earlier = ""
    if not found["session_id"]:  # a new thread, or replies written outside a job
        said = list(_record(s, metrics.planner_messages, found["id"]) or [])
        # up to the lead's last reply: the owner's after it are this message or queued ones
        while said and said[-1]["author"] == "owner":
            said.pop()
        earlier = planner.history(said)
    try:  # on main, before the plan branch: the runner's order, not a draft's
        ready = load_dir(s.tasks_dir("ready"), s.cfg.default_max_diff)
        minutes = _record(s, ticket_minutes, s.project_id) or []
        stands = work_stands(s.cfg, s.state, minutes, waiting_rows(s, ready))
    except Exception as exc:  # the block never costs the owner their answer
        s.report.notes.append(
            f"The planner's {row.subject} ran without where the work stands: {exc}."
        )
        stands = ""
    job = JobSpec(
        role=PLANNER,
        prompt=planner.prompt(thread, text, comments, threads, earlier, stands),
        timeout=s.cfg.claude_timeout,
        # A card's drafts, on its plan branch only; the general thread only talks (f6 D4)
        edit=planner.drafts(thread) if branch else (),
        commands=(
            *GIT_READ_COMMANDS,
            look.COMMAND,  # ADR 28: the database and the dashboard's pages, read-only
            *((CHECK_TICKETS, f"git checkout {branch}") if branch else ()),
        ),
        resume=found["session_id"] or None,
        title=f"planning: {row.reason}",
    )
    milestone = "" if thread == planner.GENERAL else full_key(s.repo, thread)
    new = branch is not None and _plan_branch(s, branch)
    try:
        result = call_claude(s, job, milestone, row.subject, park=True)
    except Parked:
        return
    finally:
        if branch is not None:
            _commit_drafts(s, thread, branch, row.subject, new)
    if result.ok:
        reply = planner.parse_reply(
            result.text, planner.cards(s.repo)
        )  # main's: merges apply there
    else:  # its message is the owner's to send again
        failed = f"the lead's job failed ({result.text.strip()[:200]}): send the message again"
        reply = planner.Reply("", note=failed)
    if reply.note is not None:
        s.report.notes.append(f"The planner's reply on {row.subject}: {reply.note}.")
    reply = _auto_merge(s, reply, thread)
    if reply.ignored is not None:
        s.report.notes.append(f"The planner's reply on {row.subject}: {reply.ignored}.")
    if reply.title is not None:  # after the merges: a card merged away has no heading left
        _name_card(s, thread, reply.title)
    if result.session_id:
        _record(s, metrics.set_thread_session, found["id"], result.session_id)
    _record(
        s,
        metrics.add_planner_message,
        found["id"],
        "lead",
        now().isoformat(),
        planner.stored_text(reply),
        points=None if reply.note else reply.points,
        proposals=None if reply.note else reply.proposals,
        job_id=s.last_job_id,
    )
    name = planner.thread_name(thread)
    item = (
        f"The lead answered your message on {name}: your answers are wanted."
        if result.ok
        else f"The lead couldn't answer your message on {name}: send it again."
    )
    _record(
        s,
        metrics.upsert_owner_item,
        s.project_id,
        planner.PLANNING,
        thread,
        text=item,
        created=now().isoformat(),
    )


def run_queued(s: Session, row: dispatch.Queued, *, escalate: bool) -> None:
    """Run a queued support job (ADR 22). Its row is done when the job ends, unless it parked
    again (its row then waits for the reset); one whose subject is gone is done at once."""
    needs = dict(s.state.queued.get(row_key(row), {}))
    before, s.running_row = s.running_row, row
    try:
        if row.kind == CHECKPOINT:
            if s.state.unchecked or s.state.recheck:
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
        elif row.kind == PLANNER:
            with doing(s, f"answering {row.reason}"):
                run_planner(s, row)
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
    """Before a support job with no queue to go back to (a review under `runner milestone`):
    while Claude can't take it, wait for the reset (ADR 16 items 3 and 4). When only the
    owner's share holds it, the 5-hour switch turned on meanwhile ends the wait. `runner run`
    parks its reviews instead (`park_review`)."""
    while (hold := claude_hold(s, now())) is not None:
        at = now()
        wait = max(60.0, (hold.until - at).total_seconds() + 60)
        resumes = at + timedelta(seconds=wait)
        s.log(console.paused(RUNNER_AGENT, f"{what} waits for Claude ({hold.reason})", resumes, at))
        until = partial(_five_hour_switched, s) if hold.five_hour else None
        wait_for_claude(s, wait, resumes, what, until=until)


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


def _week_switched_on(s: Session) -> None:
    """The owner turned the week's switch on: the tickets parked at the reserve go now, and
    the run is on the reserve (f1 D3 and D8, amended). `runner.requests` answered the items."""
    for entry in s.state.parked.values():
        if entry["kind"] == RESERVE_KIND:
            entry[RETRY] = True
    save_state(s.state, s.state_path)
    if s.run_id is not None:
        _record(s, metrics.set_run_reserve, s.run_id)


def at_reserve(s: Session, task: Task) -> bool:
    """Before a lead ticket: whether it waits for Claude's reserve (ADR 15 item 5): with the
    week's switch off, the ticket parks and becomes a Needs-you item naming the switch (ADR
    22 item 4); it goes once the switch is on. It parks only when nothing else can run
    (`_next_task`). Support roles may always use the reserve."""
    at = now()
    found = None if switch_on(s.state, WEEK, at) else _at_the_reserve(s, at)
    if found is None:
        return False
    where, resets = found
    text = f"{task.id} waits for Claude's reserve ({where}): turn on “{SWITCHES[WEEK]}” to run it"
    s.state.parked[task.id] = {
        "kind": RESERVE_KIND,
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
            RESERVE_KIND,
            task.id,
            text=text,
            command="softfield run --use-reserve week",
            created=at.isoformat(),
        )
    s.report.notes.append(text)
    reason = f"Claude is at its reserve ({where})"
    s.log(console.stopped(task.id, "parked", reason, "waits for you", waiting_behind(s, task.id)))
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


def _five_hour_switched(s: Session) -> bool:
    """While the run waits for the owner's 25%: whether the 5-hour switch is on now, taking
    the dashboard's switches alone (f5 D2); the other requests wait for the pick."""
    at = now()
    if not switch_on(s.state, FIVE_HOUR, at):
        _take_switches(s, at)
    return switch_on(s.state, FIVE_HOUR, at)


def _take_switches(s: Session, at: datetime) -> None:
    """During a wait, the owner's requests that change state.json alone (`take_switches`):
    the switches, the pause and the resume. A switch turned on frees what waited for it."""
    from runner.requests import take_switches  # runner.requests imports this module

    if s.project_id is None:
        return
    was_on = {switch: switch_on(s.state, switch, at) for switch in SWITCHES}
    for line in _record(s, take_switches, s.project_id, s.state, at) or []:
        s.log(f"[{RUNNER_AGENT}] the owner's request: {line}")
    save_state(s.state, s.state_path)
    if switch_on(s.state, FIVE_HOUR, at) and not was_on[FIVE_HOUR]:
        _five_hour_switched_on(s)
    if switch_on(s.state, WEEK, at) and not was_on[WEEK]:
        _week_switched_on(s)


def _five_hour_switched_on(s: Session) -> None:
    """The owner turned the 5-hour switch on: what waited for it goes now. `runner.requests`
    answered the items."""
    for entry in s.state.parked.values():
        if entry.get(FIVE_HOUR_HELD):
            entry[RETRY] = True
    save_state(s.state, s.state_path)
    for row in open_rows(s):
        if s.state.queued.get(row_key(row), {}).get(FIVE_HOUR_HELD):
            _unpark_row(s, row)


def at_five_hour(s: Session, task: Task) -> bool:
    """Before a lead ticket: whether it waits for the owner's share of Claude's 5-hour window
    (ADR 16 items 1 and 3). With the 5-hour switch off (ADR 22 item 4), the ticket parks
    until the window resets and then goes on by itself; meanwhile it is a Needs-you item
    naming the switch, and the switch turned on lets it go at once. It parks only when
    nothing else can run (`_next_task`)."""
    at = now()
    found = None if switch_on(s.state, FIVE_HOUR, at) else _at_five_hour(s, at)
    if found is None:
        return False
    used, resets = found
    text = (
        f"{task.id} waits for Claude's 5-hour window ({used} used, kept for you):"
        f" it goes on after {resets:%H:%M}, or at once if you turn on “{SWITCHES[FIVE_HOUR]}”"
    )
    if s.project_id is not None:
        _record(
            s,
            metrics.upsert_owner_item,
            s.project_id,
            FIVE_HOUR_KIND,
            task.id,
            text=text,
            command=switch_command(FIVE_HOUR),
            created=at.isoformat(),
        )
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
    """A lead ticket would park for a switch that is off (the week's or the 5-hour's)."""
    week = not switch_on(s.state, WEEK, at) and _at_the_reserve(s, at) is not None
    five = not switch_on(s.state, FIVE_HOUR, at) and _at_five_hour(s, at) is not None
    return week or five


def _next_task(s: Session, ready: list[Task], done: set[str], paused: set[str]) -> Task | None:
    """Parked tickets whose reset has passed go first; while Claude is limited, only work that
    needs no Claude: developer tickets, which local takes. At Claude's reserve or the owner's
    share of its 5-hour window with its switch off, developer tickets go before lead ones, so
    a lead ticket parks only when nothing else can run (ADR 15 item 5, ADR 16 item 3). Each by
    priority (f5 D6)."""
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
    for the owner, not the week. While work waits for the owner's 25%, the 5-hour switch
    turned on ends the sleep."""
    at = now()
    tickets = {t.id for t in ready}
    ahead = _parked_ahead(s, at, tickets, rows=rows)
    if not ahead:
        return False
    held = len(ahead) > len(_parked_ahead(s, at, tickets, five_hour=False, rows=rows))
    first, name = min(ahead)  # the parked job that resumes first is what the wait is for
    wait = max(60.0, (first - at).total_seconds() + 60)
    resumes = at + timedelta(seconds=wait)
    s.state.paused_until = resumes.isoformat()
    save_state(s.state, s.state_path)
    s.log(console.paused(RUNNER_AGENT, "nothing to run without Claude", resumes, at))
    s.report.notes.append(
        f"Paused {wait / 60:.0f} min for a Claude usage limit, with nothing to run."
    )
    wait_for_claude(s, wait, resumes, name, until=partial(_five_hour_switched, s) if held else None)
    s.state.paused_until = None
    save_state(s.state, s.state_path)
    return True


def _hold_for_the_owner(s: Session) -> bool:
    """While the owner pauses the factory (ADR 22 item 5), the pick takes nothing but planning:
    the run neither ends nor sleeps to a reset, but holds, "paused by you", applying every
    request of theirs (a plant, a message, an approval, their resume) every ``HOLD_POLL_S``
    seconds: the run is git's one writer and nothing else runs meanwhile. The hold ends at the
    resume or as soon as a planner job can go (its ⚑, f6-14); the pick then runs it and holds
    again. The hold is no limit's `wait`: the pause's own usage event (`runner.requests`)
    counts it as stopped for the owner. False, and no hold, when the run has no project row to
    read a resume from: it ends instead."""
    since = datetime.fromisoformat(str(s.state.owner_pause)).astimezone(now().tzinfo)
    paused = f"Paused by you since {since:%H:%M}"
    if s.project_id is None:
        s.report.notes.append(f"{paused}: `softfield resume`, then run again.")
        return False
    s.log(f"[{RUNNER_AGENT}] {paused}: nothing runs until you resume.")
    with doing(s, dispatch.PAUSED):
        while s.state.owner_pause is not None and not _planning_goes(s):
            time.sleep(HOLD_POLL_S)
            apply_owner_requests(s)
            check_backup(s)
    if s.state.owner_pause is None:
        s.log(f"[{RUNNER_AGENT}] Resumed by you.")
    return True


IDLE = "Idle: "
# An open owner item's kind, in the idle line's words; the two switches' items are left out:
# the tickets parked for them are named already.
OWNER_WAITS = {
    "adr": "decision",
    "escalated": "escalated ticket",
    "blocked": "blocked ticket",
    "review-stop": "review",
    "signoff": "sign-off",
    "planning": "planning reply",
}


def _counted(count: int, what: str) -> str:
    return f"{count} {what}" if count == 1 else f"{count} {what}s"


def _tickets_wait(count: int, what: str) -> str:
    return f"{_counted(count, 'ticket')} {'waits' if count == 1 else 'wait'} {what}"


def _idle_line(s: Session, ready: list[Task], paused: set[str], held: Mapping[str, str]) -> str:
    """Why the run has nothing to run (F101 D2), each cause once, from what the pick knows:
    the tickets parked for Claude with the earliest reset, those behind a blocked or escalated
    one or a sign-off, and the open owner items by kind."""
    at = now()
    causes = []
    parked = [s.state.parked[t.id] for t in ready if t.id in s.state.parked]
    parked = [entry for entry in parked if not _due(entry, at)]
    if parked:
        resets = min(_resets(entry) for entry in parked).astimezone(at.tzinfo)
        when = f"{resets:%a %H:%M}"
        if all(entry["kind"] == RESERVE_KIND for entry in parked):
            what = f"for Claude's reserve · the week resets {when}"
        else:
            what = f"for Claude until {when}"
        causes.append(_tickets_wait(len(parked), what))
    if paused:
        causes.append(_tickets_wait(len(paused), "behind a blocked or escalated one"))
    if held:
        causes.append(_tickets_wait(len(held), "for a sign-off"))
    items = [] if s.project_id is None else _record(s, metrics.open_owner_items, s.project_id)
    kinds = Counter(row["kind"] for row in items or [])
    asked = [
        _counted(count, OWNER_WAITS.get(kind, kind))
        for kind, count in kinds.items()
        if kind not in (RESERVE_KIND, FIVE_HOUR_KIND)
    ]
    if asked:
        causes.append("waiting for you: " + ", ".join(asked))
    if not ready:
        causes.insert(0, "nothing is ready")
    return IDLE + (" · ".join(causes) or "nothing can run yet")


def _idle_wait() -> None:
    """One poll of the idle hold. The owner's Ctrl-C ends it."""
    time.sleep(HOLD_POLL_S)


def _idle_holds(s: Session) -> bool:
    """With nothing to run, the standing `runner run` holds instead of ending (F101 D1): one
    ``HOLD_POLL_S`` here, then the queue's next turn applies the owner's requests, checks the
    backup, reads Claude's windows and picks again. The hold starts no job itself. False to
    end the session: the owner's Ctrl-C, or the first idle poll of a new day when the session
    has work to report (D3: ``report.idle``, and the command starts the next session)."""
    if now().date() != s.report.started.date() and (s.report.tasks or s.report.claude_runs):
        s.report.idle = True
        return False
    try:
        _idle_wait()
    except KeyboardInterrupt:
        s.log(f"[{RUNNER_AGENT}] Ended by you.")
        return False
    return True


def _planning_goes(s: Session) -> bool:
    """Whether a planner job could run now, paused or not (`dispatch.plan`)."""
    rows = [row for row in open_rows(s) if row.kind == PLANNER]
    return dispatch.pick(rows, [], dispatch.Windows(), now(), paused=True) is not None


# --- the session ------------------------------------------------------------------


def _runner_code(repo: Path) -> str:
    """A fingerprint of the runner's source, to notice an escalation changing it: the repo's
    own runner/ (Softfield's, when it works on itself) and the code this process runs from."""
    digest = hashlib.sha256()
    for path in sorted({*(repo / "runner").rglob("*.py"), *(config.HOME / "runner").rglob("*.py")}):
        digest.update(path.as_posix().encode() + b"\0" + path.read_bytes())
    return digest.hexdigest()


_CODE_AT_START: dict[Path, str] = {}  # the runner's code as this process first saw it, by repo


def code_at_start(repo: Path) -> str:
    """The fingerprint this process runs on, taken the first time ``repo``'s turn comes: not at
    each turn, or `run_projects` calling `work_queue` again after ``live`` moved would compare
    the new code with itself and never restart (2026-10-14: it ran an hour on old code)."""
    return _CODE_AT_START.setdefault(repo, _runner_code(repo))


def _new_code(s: Session, code: str) -> bool:
    """Whether the runner must restart: ``live`` followed a merge into Softfield's main (only
    when ``s`` is Softfield's session: `update_live`), or Claude changed this repo's runner/.
    m4-07: Python keeps the old modules, so new code only runs in a new process; stop rather
    than run the next job stale. Called when a job ends, so the factory updates at the end
    of its own work, and before each pick, for a commit made outside the run."""
    update_live(s.repo)
    if _runner_code(s.repo) == code:
        return False
    s.report.notes.append(RESTART_NOTE)
    set_activity(s, "restarting after a runner change")
    return True


def update_live(repo: Path) -> bool:
    """ADR 30 item 5: Softfield runs from ``live``, a checkout of its main of its own. When
    ``repo`` is Softfield and its main has moved, ``live`` follows (detached, as main stays
    checked out in ``repo``); the runner then restarts on the new code, and the dashboard
    reloads. Whether it moved. Never from a branch: only main's merged, checked commits."""
    home = config.HOME
    if home == repo.resolve():
        return False  # run from the work tree itself (`uv run softfield`, tests)
    try:
        here, there = Git(home), Git(repo)
        common = ("rev-parse", "--path-format=absolute", "--git-common-dir")
        if here.run(*common).strip() != there.run(*common).strip():
            return False  # another project
        main = there.run("rev-parse", MAIN).strip()
        if here.head() == main:
            return False
        changed = here.run("diff", "--name-only", "HEAD", main).split()
        here.run("checkout", "-q", "--detach", main)
    except (GitError, OSError):
        return False
    if {"pyproject.toml", "uv.lock"} & set(changed):
        _reinstall(home)  # the new code's dependencies, before the restart imports it
    return True


def softfield_repo() -> Path | None:
    """The Softfield work tree ``live`` is a checkout of (its main work tree), or None when
    this code runs from somewhere else."""
    try:
        common = Git(config.HOME).run("rev-parse", "--path-format=absolute", "--git-common-dir")
    except (GitError, OSError):
        return None
    repo = Path(common.strip()).parent
    return None if repo.resolve() == config.HOME.resolve() else repo


def _reinstall(home: Path) -> None:
    """`uv tool install` of ``live`` again, for a merge that changed its dependencies. Best
    effort: a failure shows on the console, and the restart tries the new code anyway."""
    code, out, err = run_bounded(
        ["uv", "tool", "install", "-e", str(home), "--reinstall"], home, 600
    )
    if code != 0:
        print(f"[{now():%H:%M:%S}] [{RUNNER_AGENT}] softfield's reinstall failed: {err or out}")


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
    writer, so it applies them itself, as their console commands would, and turns off the
    switches whose 24 hours are over. A switch turned on frees what waited for it. Best
    effort, like every write."""
    from runner.requests import apply_requests  # runner.requests imports this module

    at = now()
    was_on = {switch: switch_on(s.state, switch, at) for switch in SWITCHES}
    try:
        lines = apply_requests(s.repo, s.cfg.metrics_db, at, s.state)
    except Exception as exc:
        _metrics_failed(s, exc)
        return
    for line in lines:
        s.log(f"[{RUNNER_AGENT}] the owner's request: {line}")
    if lines:
        save_state(s.state, s.state_path)
        sync_tickets(s)  # a queued ticket shows in the queue at once
    if switch_on(s.state, WEEK, at) and not was_on[WEEK]:
        _week_switched_on(s)
    if switch_on(s.state, FIVE_HOUR, at) and not was_on[FIVE_HOUR]:
        _five_hour_switched_on(s)


def work_queue(
    s: Session,
    *,
    milestone: str | None = None,
    escalate: bool = True,
    once: bool = False,
    reviews: bool = False,
    take_tickets: bool = True,
    wait: bool = True,
) -> bool:
    """Work through .factory/tasks/ready (one milestone's, if given) and the queued jobs their runs
    trigger: directions, checkpoints and escalations (ADR 22). Each turn runs what
    `dispatch.pick` returns; the next ticket is `_next_task`'s. Returns True if Claude (a lead
    ticket or an escalation) changed the runner, which needs a restart.

    A queued job goes before any ticket, a parked one once its reset has passed; a ticket
    parked for a Claude limit goes first among tickets once its reset has passed. Until then
    only developer tickets run, and with none left the queue sleeps until the earliest reset.
    Claude's windows are checked by each job as it starts (a stand-in, a park), so the pick
    is given none. While the owner pauses it (f5-18), it holds between jobs until they resume.

    With ``reviews`` (`runner run`, f4-20), a milestone whose tickets are all done queues its
    review, which stops the queue before its next ticket: ``s.report.review`` names it, for
    the command to review. One Claude can't take now parks instead, and the queue goes on
    (F53 D1). Without ``escalate``, no escalation is queued or run. With
    ``once``, it stops after one ticket and the jobs that ticket queued.

    For `run_projects` (ADR 30 item 6): without ``take_tickets`` it runs only the queued jobs;
    without ``wait`` it never holds or sleeps here (for Claude's reset, the owner's pause or
    nothing to run) but returns, so the next project can go.

    With ``reviews`` and without ``once`` (the standing `runner run`), it doesn't return with
    nothing to run: it holds, saying what it waits for (`_idle_line`), and each turn applies
    the owner's requests and picks again (F101). It returns for a due review, the owner's
    Ctrl-C, or the day's report (`_idle_holds`). A Ctrl-C between two polls is `run_session`'s.
    """
    code = code_at_start(s.repo)
    ran = False  # a ticket ran, for ``once``
    idle: str | None = None  # the idle line the run shows while it holds (F101)
    while True:
        if _new_code(s, code):  # a commit made outside the run (a terminal session's)
            return True
        if idle is None:
            set_activity(s, PICKING)
        apply_owner_requests(s)
        check_backup(s)
        fresh_reading(s)
        if reviews:
            _queue_due_review(s)
        ready = load_dir(s.tasks_dir("ready"), s.cfg.default_max_diff)
        if milestone is not None:  # either form of the key (ADR 16 item 6)
            ready = [t for t in ready if short_key(t.milestone) == short_key(milestone)]
        done = task_ids(s.tasks_dir("done"))
        paused = blocked_ids(ready, stopped_ids(s.repo / ".factory" / "tasks"))
        held = _held(s.repo, ready)
        rows = _runnable_rows(s, ready, escalate=escalate, reviews=reviews)
        behind = waiting_rows(s, ready)
        task = (
            _next_task(s, ready, done, paused | held.keys() | behind.keys())
            if take_tickets
            else None
        )
        tickets = [] if task is None else [_dispatch_ticket(s, task, ready)]
        paused_by_owner = s.state.owner_pause is not None
        job = dispatch.pick(rows, tickets, dispatch.Windows(), now(), paused=paused_by_owner)
        if once and ran and (job is None or job.kind == dispatch.TICKET):
            return False
        if job is None:
            if paused_by_owner:
                if wait and _hold_for_the_owner(s):
                    continue
                return False
            if wait and _wait_for_reset(s, ready, rows):
                continue
            if reviews and not once and wait:  # the standing command holds (F101 D1)
                line = _idle_line(s, ready, paused, held)
                if line != idle:
                    idle = line
                    s.log(f"[{RUNNER_AGENT}] {line}")
                    set_activity(s, line)
                if _idle_holds(s):
                    continue
            if not wait:  # `run_projects` goes to the next project; this one says why it waits
                if reviews and not once and take_tickets:
                    set_activity(s, _idle_line(s, ready, paused, held))
                return False
            if paused:
                s.report.notes.append("Paused (dependency escalated): " + ", ".join(sorted(paused)))
            if held:
                s.report.notes.append("Waiting: " + _waits_text(held))
            return False
        if idle is not None:
            idle = None
            set_activity(s, PICKING)
        if job.kind == REVIEW:
            if park_review(s, job.subject):  # the line goes on meanwhile (F53 D1)
                continue
            s.log(f"[runner] {review_reason(job.subject)}: its review is next.")
            s.report.review = job.subject
            return False
        if job.kind != dispatch.TICKET or task is None:  # a ticket: the one it was given
            row = next(r for r in rows if (r.kind, r.subject) == (job.kind, job.subject))
            run_queued(s, row, escalate=escalate)
            s.picks += 1
            if _new_code(s, code):  # the job just merged into Softfield: its code, now
                return True
            continue
        with doing(s, task.id):
            rec = run_task(s, task)
        after_ticket(s, task, rec, escalate=escalate)
        s.picks += 1
        if _new_code(s, code):
            return True
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
    """`runner run`: the queue, until a milestone's review is due (f4-20) or the owner ends
    it; with nothing to run it holds (F101). With ``once``, until it is empty."""
    if dry_run:
        dry_run_plan(cfg)
        return None
    s = open_session(cfg)
    check_backup(s)  # the run's start; each pick checks again (F20 D1)
    try:
        restart = work_queue(s, escalate=escalate, once=once, reviews=True)
    except KeyboardInterrupt:
        # Between two idle polls (the pick's reads, the owner's requests) the run still shows
        # its idle line: the Ctrl-C ends it as one in the poll does, with its report (F101).
        if not (s.activity or "").startswith(IDLE):
            raise
        s.log(f"[{RUNNER_AGENT}] Ended by you.")
        restart = False
    report = close_session(s)
    report.restart = restart
    return report


# --- every project (ADR 30 item 6) -----------------------------------------------------

type Turn = Callable[..., tuple[bool, bool]]  # one project's turn: (restart, it ran a job)


def project_round(sessions: Sequence[Session], turn: Turn) -> tuple[bool, bool]:
    """One round of `run_projects`, the projects in the owner's order: first every project's
    queued jobs (the owner's planning replies, directions, checkpoints, escalations: they never
    wait behind another project's ticket), then one ticket from the first project that has one
    it can run; while the owner pauses, no ticket. Returns (restart, a job ran)."""
    for s in sessions:
        restart, ran = turn(s, take_tickets=False)
        if restart or ran:
            return restart, ran
    if any(s.state.owner_pause is not None for s in sessions):  # a pause holds every project
        return False, False
    for s in sessions:
        restart, ran = turn(s, once=True)
        if restart or ran:
            return restart, ran
    return False, False


def _main_head(s: Session) -> str | None:
    try:
        return s.git.run("rev-parse", MAIN).strip()
    except (GitError, OSError):
        return None


def run_projects(
    configs: Callable[[], list[Config]],
    review: Callable[[Config, str], bool],
    *,
    escalate: bool = True,
) -> bool:
    """`softfield run` (ADR 30 item 6): every registered project, ``configs()`` read again each
    round so a new order takes effect at the next pick. Each project keeps its own session
    (its run, its report, its state.json); a round is `project_round`'s; with nothing to run
    anywhere it waits one poll. A project that can't open a session (not on a clean main)
    is skipped and said once. A due review closes its project's session and runs, as after
    a single project's `runner run`. Returns True when the runner's code changed: restart."""
    sessions: dict[Path, Session] = {}
    refused: set[Path] = set()
    busy: list[Session] = []  # the session in a turn: a Ctrl-C there leaves it as it is
    synced: dict[Path, str] = {}  # each project's main, as its cards and tickets were read

    def turn(s: Session, **kw: Any) -> tuple[bool, bool]:
        # A card or ticket committed outside the run (`softfield init`'s setup session, a
        # terminal session) reaches the board at the next round, not the next session
        head = _main_head(s)
        if head is not None and synced.setdefault(s.repo, head) != head:
            sync_tickets(s)
            sync_cards(s)
            synced[s.repo] = head
        before = s.picks
        busy.append(s)
        restart = work_queue(s, escalate=escalate, reviews=True, wait=False, **kw)
        busy.remove(s)
        key = s.report.review
        if key is not None and not restart:
            close_session(sessions.pop(s.repo))
            # its project opens a new session next round; a review that changed runner/
            # restarts through the `finally` below, which closes the others' sessions
            return review(s.cfg, key), True
        return restart, s.picks > before

    try:
        while True:
            cfgs = configs()
            for repo in [r for r in sessions if r not in {c.repo for c in cfgs}]:
                close_session(sessions.pop(repo))  # paused or gone: its session ends
            live: list[Session] = []
            for cfg in cfgs:
                s = sessions.get(cfg.repo)
                if (
                    s is not None
                    and now().date() != s.report.started.date()
                    and (s.report.tasks or s.report.claude_runs)
                ):
                    close_session(sessions.pop(cfg.repo))  # the day's report (F101 D3)
                    s = None
                if s is None:
                    try:
                        s = open_session(cfg)
                    except RunnerError as exc:
                        if cfg.repo not in refused:
                            refused.add(cfg.repo)
                            print(f"[{now():%H:%M:%S}] [{RUNNER_AGENT}] {cfg.project_name}: {exc}")
                        continue
                    refused.discard(cfg.repo)
                    sessions[cfg.repo] = s
                live.append(s)
            restart, ran = project_round(live, turn)
            if restart:
                return True
            if not ran:
                _idle_wait()
    except KeyboardInterrupt:
        print(f"[{now():%H:%M:%S}] [{RUNNER_AGENT}] Ended by you.", flush=True)
        if busy:  # mid-job, as one project's run: no report, the next start recovers it
            for s in sessions.values():
                if s not in busy:
                    close_session(s)
            raise
    finally:
        if not busy:
            for s in sessions.values():
                close_session(s)
    return False


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
            (cfg.project_name,),
        ).fetchall()
    finally:
        conn.close()
    at = now()
    return next(
        (r["run_dir"] for r in rows if at - datetime.fromisoformat(r["heartbeat"]) < LIVE), None
    )


def queue_ticket(cfg: Config, wanted: str) -> str:
    """Move a ticket from .factory/tasks/later/ to .factory/tasks/ready/ in a commit of its own (ADR
    17 item
    3); ``wanted`` is its id or a unique prefix. Tasks only, so the commit skips the hook.
    Refused while a run is live: the runner commits on the same branch."""
    if (run := live_run(cfg)) is not None:
        raise RunnerError(f"run {run} is running; queue {wanted} once it has stopped")
    return move_to_ready(cfg.repo, wanted)


def move_to_ready(repo: Path, wanted: str) -> str:
    """`queue_ticket`'s move and commit, for a caller that is git's one writer: the command
    once no run is live, or the run itself applying the owner's request (f5 D2)."""
    tasks = repo / ".factory" / "tasks"
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
        doc = milestone_file(repo, "cards", key)
        if doc.is_file():
            found[short_key(key)] = card(key, doc.read_text(encoding="utf-8")).priority
    return found


def _waits_text(held: dict[str, str]) -> str:
    return ", ".join(
        f"{task_id} waits for {key}'s sign-off" for task_id, key in sorted(held.items())
    )


PARKED_REASON = "parked for a Claude limit"


def dry_run_plan(cfg: Config) -> None:
    """`runner run --dry-run` (f8-02): `dispatch.plan`'s list, each job with what it waits for and
    why it is there, and each ticket's pre-flight problems (docs/task-writing.md). Reads
    .factory/tasks/, state.json and the metrics database if there is one: any branch, any tree, and
    no run folder or row (f1-33). A due review not queued yet is listed as the run would queue it,
    and a support job an older state.json parked as the row the run makes of it."""
    from runner.milestone import due_reviews  # runner.milestone imports this module

    at = now()
    tasks = cfg.repo / ".factory" / "tasks"
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
            *(("seven_day",) if switch_on(state, WEEK, at) else ()),
            *(("five_hour",) if switch_on(state, FIVE_HOUR, at) else ()),
        },
    )
    lines = dispatch.plan(queued, tickets, windows, at, paused=state.owner_pause is not None)
    _print_plan(lines, ready, done, paused, cfg.repo)


def _stored_queue(cfg: Config) -> tuple[list[dispatch.Queued], dict[str, sqlite3.Row]]:
    """The project's open ``work_queue`` rows and Claude's latest readings; none without a
    metrics database, and a read makes none."""
    if not cfg.metrics_db.is_file():
        return [], {}
    conn = metrics.open_db(cfg.metrics_db)
    try:
        project = metrics.find_project(conn, cfg.project_name)
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


NO_E2E = "no end-to-end tests in [checks]"


def run_e2e(repo: Path, timeout: int) -> GateResult:
    """The project's end-to-end tests (``[checks] e2e``); passed when it has none."""
    if not (dirs := project_checks(repo).e2e):
        return GateResult("e2e", True, NO_E2E)
    browsers = [arg for name in E2E_BROWSERS for arg in ("--browser", name)]
    code, out, err = run_bounded(
        ["uv", "run", "pytest", "-q", "-m", "e2e", *browsers, *dirs], repo, timeout
    )
    if code is None:
        return GateResult("e2e", False, f"timed out after {timeout}s\n" + (out + err)[-4000:])
    return GateResult("e2e", code == 0, (out + err)[-4000:])
