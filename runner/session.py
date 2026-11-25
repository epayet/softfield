"""What every runner job shares (F290 D1): the session, the clock, the job records, the queue's
rows, routing and ``call_claude``. It imports nothing from the job modules or `runner.loop`, which
import it (F290 D4). A name the tests patch is reached as ``session.now()`` (F290 D5)."""

import json
import sqlite3
import threading
import time
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from functools import partial
from pathlib import Path
from typing import Any, Concatenate, NoReturn

from runner import (
    backup,
    config,
    console,
    dispatch,
    messages,
    metrics,
    notify,
    order,
    prompts,
    router,
)
from runner.agents import (
    ANY,
    LOGIN,
    TRANSIENT,
    Agent,
    JobResult,
    JobSpec,
    Reading,
    adapter_for,
)
from runner.claude import Progress, backoff_seconds
from runner.config import Config, read_protected
from runner.gitops import (
    LOCAL_MODEL_AGENT,
    LOCAL_MODEL_AUTHOR,
    RUNNER_AUTHOR,
    Git,
    GitError,
    with_trailers,
)
from runner.local_model import (
    LIVE_EVERY,
    TokenTotals,
    is_local,
    stream_facts,
)
from runner.report import ClaudeRunRecord, SessionReport, TaskRecord
from runner.state import State, load_state, save_state
from runner.tasks import (
    LATER,
    STOPPED,
    Task,
    TaskError,
    blocked_ids,
    difficulty,
    full_key,
    load_dir,
    milestone_file,
    milestone_key,
    parse_sections,
    short_key,
    split_frontmatter,
    stopped_ids,
    task_ids,
    ticket_area,
)
from runner.usage import claude_tokens, transcripts_dir

MAIN = "main"
RUNNER_AGENT = "runner"
CLAUDE_HEADLESS_AGENT = "claude-headless"


class RunnerError(RuntimeError):
    pass


def now() -> datetime:
    """The moment, in UTC: every stored time is (F187 D1). A person's view converts it with
    ``.astimezone()``."""
    return datetime.now(UTC)


def local_clock() -> datetime:
    """The moment in the machine's zone, for what a person reads (the console's stamps)."""
    return now().astimezone()


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
    # The milestone whose review stops after this round, while its fixes run: no round reads them
    last_round: str | None = None
    ticket_started: float = 0.0  # `clock()` when the current ticket started, for the console
    # What the run says it does outside a job, and until when it waits (`set_activity`).
    activity: str | None = None
    waiting_until: datetime | None = None
    pre_review_failed: dict[str, datetime] = field(default_factory=dict)  # when one didn't run
    probed: bool = False  # a fresh reading of Claude's windows was taken (f4-07)
    login_checked: datetime | None = None  # when Claude's login last answered (`check_login`)
    # Queue rows the metrics database couldn't take (f8 D1): this session runs them still.
    unqueued: dict[int, dispatch.Queued] = field(default_factory=dict)
    running_row: dispatch.Queued | None = None  # the queued job running now: its job's row
    # A ticket's record while it waits behind its queued direction, for its last attempt.
    waiting: dict[str, TaskRecord] = field(default_factory=dict)
    # The metrics database's copies (F20 D1), None without `[backup]`; a failure is noted once
    backups: backup.Backups | None = None
    backup_failed: bool = False
    utc_settled: bool = False  # F187 D5: the old times are converted, or a collision was said once
    picks: int = 0  # jobs run so far, tickets and queued jobs (`run_projects`'s round)

    @property
    def repo(self) -> Path:
        return self.cfg.repo

    @property
    def state_path(self) -> Path:
        return self.cfg.runs_dir / "state.json"

    def tasks_dir(self, name: str) -> Path:
        return self.repo / ".softfield" / "tasks" / name

    def log(self, message: str) -> None:
        """One console line (`runner.console`); an empty one is a blank line."""
        print(f"[{local_clock():%H:%M:%S}] {message}" if message else "", flush=True)


def open_session(cfg: Config, command: str | None = "run") -> Session:
    """A session on a clean main. With a ``command``, it is recorded as a run in the metrics
    database; None records nothing."""
    git = Git(cfg.repo)
    state_path = cfg.runs_dir / "state.json"
    state = load_state(state_path)
    cut_off = state.in_flight
    recovered = _recover(git, state, state_path) if cut_off is not None else ""
    # A ticket no longer parks at the week's reserve (ADR 44 item 6): an older run's entry goes,
    # and `_start_run` its desk item.
    # Nor at the 5-hour mark (ADR 50 items 3 and 4): the same.
    asked = [
        k
        for k, entry in state.parked.items()
        if entry.get("kind") in (RESERVE_KIND, FIVE_HOUR_KIND)
    ]
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
    run_dir = cfg.runs_dir / f"{started.astimezone():%Y%m%d-%H%M%S}"
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
        state.interrupted[job_key(kind, str(name))] = {
            "session_id": session,
            "branch": where,
            "agent": agent,  # the session resumes on it (ADR 32 item 1)
        }
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


def _notify(s: Session, words: str, path: str) -> None:
    """One notification to the owner's phone (ADR 31); one that wasn't sent is a report note."""
    if (note := notify.to_owner(s.cfg.project_name, words, path)) is not None:
        s.report.notes.append(note)


def _rel(s: Session, path: Path) -> str:
    return path.relative_to(s.repo).as_posix()


def _shown(s: Session, path: Path) -> str:
    """``path`` as a prompt names it: from the repo when it is inside, else whole."""
    return _rel(s, path) if path.is_relative_to(s.repo) else path.as_posix()


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
        _record(s, _resolve_reserve_parks, s.project_id, at)
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


def _resolve_reserve_parks(conn: sqlite3.Connection, project_id: int, at: str) -> None:
    """The desk items of tickets an older run parked at the week's reserve (ADR 44 item 6) or at
    the 5-hour mark (ADR 50 item 3), and the items of earlier lapsed switches (F97 D7: a lapse
    now asks nothing), all answered."""
    for row in metrics.open_owner_items(conn, project_id):
        if row["kind"] in (FIVE_HOUR_KIND, RESERVE_KIND):
            metrics.resolve_owner_item(conn, row["id"], at)


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
    """Every ticket in .softfield/tasks/ with its folder's state (f1 D4): the queue the dashboard
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
        _record(s, metrics.fold_short_milestones, s.project_id)  # F171 D2


def sync_cards(s: Session) -> None:
    """Every milestone doc's card (f5 D4) and title, as ``sync_tickets`` does for tickets: an
    idea with no tickets yet is on the board too. A doc not named by a key is left out, and a
    card whose doc is gone (merged away, dropped, deleted) leaves the board (f6-17). The
    queue's list too, as ``board_order`` (F222 D5)."""
    from runner.milestone import (  # runner.milestone imports this module
        card,
        milestone_doc,
        signoff_sections,
    )

    if s.project_id is None:
        return
    present = set()
    for path in sorted((s.repo / ".softfield" / "cards").glob("*.md")):
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
            area=found.area,
            signoff=sheet or None,
        )
    _record(s, metrics.remove_cards, s.project_id, present=present)
    # F222 D5: the dashboard's copy of the queue's list, equal to the file (none: no list)
    _record(s, metrics.set_board_order, s.project_id, order.read_order(s.repo) or [])


PICKING = "picking the next ticket"
# A job that writes tickets checks them as Approve will (`runner check-tickets`, read-only)
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
    path: Path | None = None
    if s.backups is not None:
        path = _backup_copy(s, s.backups)
    _convert_old_times(s, path)


def _convert_old_times(s: Session, copy: Path | None) -> None:
    """F187 D5: once, right after a copy holds the old times as they were, they become UTC.
    With no backup set, a copy is written beside the database first. A collision on a unique
    key changes nothing, leaves the step owed, and is said once."""
    if s.utc_settled or (s.backups is not None and copy is None):
        return
    try:
        conn = metrics.open_db(s.cfg.metrics_db)
    except Exception:
        return
    try:
        if not metrics.utc_step_owed(conn):
            s.utc_settled = True
            return
        if copy is None:
            backup.copy(s.cfg.metrics_db, s.cfg.metrics_db.parent, now())
        changed = metrics.convert_old_times_to_utc(conn, now().astimezone(UTC).isoformat())
        s.utc_settled = True
        s.log(f"[{RUNNER_AGENT}] converted {changed} stored times to UTC (F187)")
    except sqlite3.IntegrityError as exc:
        s.utc_settled = True
        line = (
            f"Converting the stored times to UTC (F187) hit a clash ({exc}); nothing changed, and"
            " the next run tries again."
        )
        s.log(f"[{RUNNER_AGENT}] {line}")
        s.report.notes.append(line)
    except Exception as exc:
        line = f"converting the stored times to UTC failed ({exc}); a later check tries again."
        s.log(f"[{RUNNER_AGENT}] {line}")
    finally:
        conn.close()


def _backup_copy(s: Session, backups: backup.Backups) -> Path | None:
    """The new copy when one is due; a failure is noted once (see ``check_backup``)."""
    try:
        path = backups.check(now())
    except Exception as exc:
        line = (
            f"The metrics database's backup failed ({type(exc).__name__}: {exc}); the run went"
            " on, and a later check tries again."
        )
        s.log(f"[{RUNNER_AGENT}] {line}")
        if not s.backup_failed:
            s.backup_failed = True
            s.report.notes.append(line)
        return None
    if path is not None:
        s.backup_failed = False
        s.log(f"[{RUNNER_AGENT}] backed up the metrics database to {path}")
    return path


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
    with doing(s, f"{waiting} until {resumes.astimezone():%H:%M}", resumes):
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


def _milestone_row(s: Session, milestone: str) -> int | None:
    """The milestone's row, by its card's full key: a ticket may name it short (`milestone:
    f2`), and F2's and F4's tickets then sat on a row of their own, so the card holding the
    review's sheet looked empty and theirs waited for a review that was done (2026-10-22)."""
    if s.project_id is None:
        return None
    return _record(s, metrics.upsert_milestone, s.project_id, full_key(s.repo, milestone))


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
        milestone_id=_milestone_row(s, milestone),
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
    milestone_id = _milestone_row(s, milestone) if milestone else None
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


def candidates(s: Session, role: str) -> list[Agent]:
    """The agents `[roles]` lists for ``role``, in order."""
    s.cfg.agent_for(role)  # a role with no agent is a config error
    return [s.cfg.agents[agent_id] for agent_id in s.cfg.roles[role]]


def first_agent(s: Session, role: str) -> router.Route:
    return router.route(role, None, 1, candidates(s, role), {}, {}, {}, now())


def _at(value: str) -> datetime:
    return datetime.fromisoformat(value)


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
    paused = blocked_ids(ready, stopped_ids(s.repo / ".softfield" / "tasks"))
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
# A resumed session still reads its first prompt's paths: the F97 review (2026-11-24), parked
# by a limit, wrote its findings to the earlier run's folder and the round stopped unread.
RUN_FOLDER_NOTE = (
    " This run's files go in `{run}`: a file your first instructions put in another run's"
    " folder goes in this one instead, with the same name."
)


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
PLANNER, SETUP = dispatch.PLANNER, dispatch.SETUP
# The queued jobs whose rows park: the support jobs a ticket's run queues, and the owner's
# messages to the planner (f6-01) or to a project's setup (ADR 48 item 4)
QUEUED = (*SUPPORT, DIRECTION, PLANNER, SETUP)
FIVE_HOUR_HELD = "five_hour"  # a parked entry's flag: held by the owner's 25%, not a limit
# An expired login (bug-59). A job it stopped parks as for a limit, flagged, until the next
# check of the login (`check_login`); the item on the owner's desk is one for the whole machine.
LOGIN_HELD = "login"  # a parked entry's flag, and an interrupted job's cause
LOGIN_KIND = "claude-login"
LOGIN_SUBJECT = "claude"
LOGIN_TEXT = "Claude's login has expired: log in again on this machine."
LOGIN_CHECK = timedelta(minutes=5)
LOGIN_REASON = "Claude's login has expired"


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
    *,
    login: bool = False,
) -> NoReturn:
    """Park the job: its changes committed on its branch (on ``parked/…`` if it ran on main),
    its session kept for the resume, its ticket held until the reset (with none given,
    ``backoff_min`` from now). ``extra`` is what a support job needs to start again. With
    ``login``, an expired login stopped it, not a limit. A review's round parks its review's
    row, about its milestone (F191 D4): it goes on from that round, resuming its session."""
    at = now()
    flag = {LOGIN_HELD: True} if login else {}
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
    cause = LOGIN_HELD if login else "limit"
    s.state.interrupted[job_key(job.role, name)] = {**entry, "agent": agent, "cause": cause}
    if job.role in QUEUED or job.role == REVIEW:
        subject = milestone if job.role in (CHECKPOINT, REVIEW) else name
        park_row(s, job.role, subject, resets, **(extra or {}), **flag)
    else:
        s.state.parked[name] = {
            "kind": job.role,
            **entry,
            "resets_at": resets.isoformat(),
            **flag,
        }
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
    why = LOGIN_REASON if login else "Claude usage limit"
    s.log(console.paused(agent, f"{why}, {name} parked", resets, at))
    s.report.notes.append(f"Parked {name} ({job.role}): {why}.")
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
    home = config.HOME
    text, missing = prompts.brief(home, role)
    rules = s.repo / config.PROJECT_MD
    if text and rules.is_file():
        text += "This project's own rules (.softfield/project.md):\n\n"
        text += rules.read_text(encoding="utf-8").strip() + "\n\n" + prompts.BRIEF_END
    if missing:
        note = (
            f"The {role} prompt went without {', '.join(missing)}:"
            f" not found in {home}/runner/instructions/"
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
    give_up: bool = False,
) -> JobResult:
    """Run a lead job on the agent ``routed`` names, else the first its role lists, waiting
    out usage limits. Each trigger bounds its own runs (ADR 12 item 10); the count per
    milestone is kept for the metrics.

    With ``give_up`` (a repair turn: nothing to resume), a certain limit or an expired login
    ends the call at once, as a failed run, after being recorded as usual.

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
        resume_prompt += RUN_FOLDER_NOTE.format(run=_shown(s, s.run_dir))
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
            adapter.run,
            runner,
            replace(job, prompt=prompt, resume=resume, system=_brief(s, job.role)),
            s.repo,
            log,
            now(),
        )
        if runner.harness == CLAUDE:
            run = partial(run, on_progress=partial(latest.__setitem__, "progress"))
        result = with_progress(
            run, lambda elapsed: s.log(console.running(agent, what, elapsed)), write_progress
        )
        _record_readings(s, agent, result.readings)
        if result.error == LOGIN:
            _login_expired(s)
            if give_up:
                break
            session = result.session_id or resume
            at = now()
            resumes = at + LOGIN_CHECK
            if park:
                name = ticket or subject
                _park(s, job, name, milestone, agent, job_id, session, resumes, parked, login=True)
            # No queue to go back to (a review under `runner milestone`): it waits where it is
            attempt += 1
            resume = session
            interrupted = True
            _in_flight_session(s, resume)
            s.log(console.paused(agent, LOGIN_REASON, resumes, at))
            wait_for_claude(s, LOGIN_CHECK.total_seconds(), resumes, ticket or subject, limit=False)
            continue
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
            if give_up and limit.certain:
                s.log(f"[{agent}] {what}: refused by a usage limit; given up, not waited for")
                break
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


CHECKPOINT = router.CHECKPOINT
# The owner's two switches (ADR 22 item 4, f8 D4), one per window (ADR 16 item 3), in
# state.json: off (the default), past the window's line or mark lead tickets go after the
# developers'; on, they keep the board's order to the window's real limit (ADR 50 item 6). The
# console asks nothing.
WEEK = "week"
FIVE_HOUR = "five_hour"
SWITCHES = {
    WEEK: "Keep the board's order past the week's pace and mark",
    FIVE_HOUR: "Keep the board's order past the 5-hour mark",
}
USE_RESERVE_HOURS = 24  # on lasts this long, then turns itself off (owner, 2026-10-04)
SWITCH_POLL_S = 60.0  # how often a wait for the owner's 25% checks for the switch (f5 D2)
FIVE_HOUR_KIND = "five-hour"  # a lead ticket parked for the owner's 25%, and its owner item
RESERVE_KIND = "reserve"  # an older run's park at the week's reserve; a run's start answers them
RETRY = "retry"  # a parked entry's flag: a restart tries it again before its reset
CLAUDE = "claude"


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
    ends = (at + timedelta(hours=USE_RESERVE_HOURS)).astimezone()
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


def _login_items(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """The open login items of every project: the login is the machine's, and so the item."""
    rows: list[sqlite3.Row] = conn.execute(
        "SELECT id FROM owner_items WHERE kind = ? AND resolved IS NULL", (LOGIN_KIND,)
    ).fetchall()
    return rows


def _login_asked(s: Session) -> bool:
    """Whether the owner's desk, in any project, already asks them to log in."""
    found = _record(s, _login_items)
    return bool(found)


def _login_expired(s: Session) -> None:
    """A job found the login expired: the next check is ``LOGIN_CHECK`` from now, and the
    owner is asked once, whatever else it stopped, here or in another project."""
    at = now()
    s.login_checked = at
    if s.project_id is None or _login_asked(s):
        return
    _record(
        s,
        metrics.upsert_owner_item,
        s.project_id,
        LOGIN_KIND,
        LOGIN_SUBJECT,
        text=LOGIN_TEXT,
        command="",
        created=at.isoformat(),
    )
    s.report.notes.append(LOGIN_TEXT)
    _notify(s, *notify.item_message(LOGIN_KIND, LOGIN_SUBJECT))


LIVE = timedelta(minutes=2)  # f1 D3: an older heartbeat means the runner stopped


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


PARKED_REASON = "parked for a Claude limit"


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


def _main_head(s: Session) -> str | None:
    try:
        return s.git.run("rev-parse", MAIN).strip()
    except (GitError, OSError):
        return None
