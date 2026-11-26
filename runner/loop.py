"""The scheduler (docs/workflow.md): which job runs next, the queue's turns, the idle line, the
session's rounds and the dry run. Each job kind runs in its own ``runner/<kind>_job.py``."""

import hashlib
import sqlite3
import statistics
import time
from collections import Counter
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from runner import (
    allowance,
    config,
    dispatch,
    metrics,
    notify,
    order,
    push,
    router,
    session,
    stacks,
    waits,
)
from runner.config import Config, project_checks, read_protected
from runner.developer_job import (
    MAIN_RED_KIND,
    _held_by_red_main,
    _look_at_main,
    _save_thinking,
    run_task,
    waits_for_main,
)
from runner.gates import (
    GateResult,
)
from runner.gitops import (
    Git,
    GitError,
)
from runner.lead_job import handle_escalation
from runner.planner_job import run_planner, run_setup, setting_up, ticket_minutes
from runner.procs import run_bounded
from runner.report import SessionReport, TaskRecord
from runner.review_job import (
    STAND_IN,
    _pre_review_turn,
    checkpoint,
    note_merge,
    pre_review_pick,
    review_reason,
    under_review,
)
from runner.session import (
    CHECKPOINT,
    CLAUDE,
    DIRECTION,
    ESCALATION,
    FIVE_HOUR,
    FIVE_HOUR_KIND,
    LIVE,
    LOGIN_HELD,
    LOGIN_KIND,
    MAIN,
    PARKED_REASON,
    PICKING,
    PLANNER,
    QUEUED,
    RESERVE_KIND,
    RETRY,
    REVIEW,
    RUNNER_AGENT,
    SETUP,
    SUPPORT,
    SWITCHES,
    WEEK,
    RunnerError,
    Session,
    _due,
    _has_branch,
    _metrics_failed,
    _record,
    _rel,
    _resets,
    _row_waits,
    check_backup,
    close_session,
    doing,
    enqueue,
    finish_row,
    local_clock,
    open_rows,
    open_session,
    row_key,
    switch_on,
    sync_cards,
    sync_tickets,
    waiting_rows,
)
from runner.state import State, load_state, save_state
from runner.tasks import (
    BUGS,
    LATER,
    Task,
    TaskError,
    blocked_ids,
    early_for,
    find_ticket,
    held_ids,
    load_dir,
    milestone_file,
    parse_task,
    pick_next,
    preflight,
    pulls,
    run_order,
    short_key,
    stopped_ids,
    task_ids,
    task_place,
)
from runner.waits import (
    AT_THE_LIMIT,
    FULL,
    LEAD_COST,
    _claude_windows_from,
    _five_hour_switched_on,
    _pick_windows,
    _wait_for_reset,
    _week_switched_on,
    check_login,
    park_review,
)

PUSH_KIND = "push"  # a push that needs the owner (ADR 42); its subject is the project's remote


def _push_item(s: Session, remote: str, text: str | None) -> None:
    """The push's desk item (ADR 42 item 7): open with ``text``, resolved without."""
    conn = metrics.open_db(s.cfg.metrics_db)
    try:
        project_id = metrics.find_project(conn, s.cfg.project_name)
        if project_id is None:
            return
        if text is not None:
            metrics.upsert_owner_item(
                conn, project_id, PUSH_KIND, remote, text=text, created=session.now().isoformat()
            )
            return
        for row in metrics.open_owner_items(conn, project_id):
            if row["kind"] == PUSH_KIND and row["subject"] == remote:
                metrics.resolve_owner_item(conn, row["id"], session.now().isoformat())
    finally:
        conn.close()


def check_push(s: Session) -> None:
    """What the owner signed off goes to the project's remote (ADR 42), at each pick and without
    asking it when no tag has changed. Never stops the work: a failure tries again."""
    remote = push.remote_of(s.repo)
    if remote is None:
        return
    try:
        tags = push.done_tags(s.repo)
        memory = push.read_memory(s.repo)
        if tags == memory.settled and not memory.failing_since:
            return
        address = config.machine_ntfy()
        with doing(s, "pushing to GitHub"):
            outcome = push.push_signed_off(
                s.repo, remote, address.rsplit("/", 1)[-1] if address else None
            )
        for tag in outcome.pushed:
            s.log(f"[{RUNNER_AGENT}] pushed {tag} to {remote}")
        if outcome.held:
            s.log(f"[{RUNNER_AGENT}] {outcome.held}")
            push.write_memory(s.repo, push.Memory(memory.settled, session.now().isoformat()))
            _push_item(s, remote, outcome.held)
        elif outcome.failed:
            since = memory.failing_since or session.now().isoformat()
            s.log(f"[{RUNNER_AGENT}] the push to {remote} failed, and a later pick tries again")
            push.write_memory(s.repo, push.Memory(memory.settled, since))
            if push.keeps_failing(since, session.now()):
                _push_item(s, remote, f"The push to {remote} keeps failing: {outcome.failed}")
        else:
            push.write_memory(s.repo, push.Memory(tags))
            _push_item(s, remote, None)
    except Exception as exc:  # a push never stops the work
        s.log(f"[{RUNNER_AGENT}] the push check failed ({type(exc).__name__}: {exc})")


# --- parking and the reserve (ADR 15 items 4, 5 and 10) --------------------------------


HOLD_POLL_S = 5.0  # how often the hold for the owner applies their requests (f6-22)


def project_pause(s: Session) -> str | None:
    """When the owner paused the session's project alone (F124 D1), else None: its turns run
    its planning and its requests, but no ticket, checkpoint or review."""
    found = _record(s, metrics.project_state, s.cfg.project_name)
    return None if found is None else metrics.paused_by_you(found[1])


def project_archived(s: Session) -> bool:
    """Whether the owner archived the session's project (F262 D1): held as its pause holds it."""
    found = _record(s, metrics.project_state, s.cfg.project_name)
    return found is not None and metrics.is_archived(found[1])


def paused_by_you_since(since: str) -> str:
    """A project's own pause in the run's words (F124 D4)."""
    return f"{dispatch.PAUSED} since {datetime.fromisoformat(since).astimezone():%H:%M}"


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
        elif row.kind == SETUP:
            with doing(s, f"setting {s.cfg.project_name} up: {row.reason}"):
                run_setup(s, row)
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


def choose_ticket(
    ready: list[Task],
    done: set[str],
    waiting: Collection[str],
    *,
    cards: Mapping[str, int],
    regate: Collection[str],
    parked: Mapping[str, dict[str, Any]],
    windows: dispatch.Windows,
    lane: Collection[str],
    protected: Collection[str],
    at: datetime,
    reviewing: Collection[str] = (),
    fill_gap: bool = True,
) -> Task | None:
    """The next ticket, for the runner (`_next_task`) and the dry run (`dry_run_plan`) alike (ADR
    44 item 9); ``waiting`` holds what a pause or a hold keeps from running. Without
    ``fill_gap`` a lead ticket that would only fill the gap is not taken (ADR 50 item 2):
    `project_round` asks every project that way first, so no project's lead ticket goes
    before another's developer ticket.

    A ticket waiting only for its gates (``regate``) goes first, whatever Claude's state: its
    gates run before main moves on and its work is thrown away. Then the fast lane's (``lane``,
    ADR 35 item 2): a lane card's tickets and what they wait for, one that can't run passed over.
    Then parked tickets whose reset has passed: work already begun goes on, whatever the pace
    (ADR 44 item 7). Then the fix tickets of a card between two review rounds (``reviewing``,
    `under_review`, F191 D7), held as any ticket is. While Claude is limited, only work that
    needs no Claude: developer tickets,
    which local takes. Over the week's pace line or past a mark, developer tickets go before
    lead ones, and the first lead ticket fills the gap when nothing else can start (ADR 50 item
    2); only Claude's real limit stops it (`_held_at_the_limit`). Each by place (f5 D6), a ticket
    waited for in its first waiter's place, read from the whole ready list (F173 D6)."""
    pulled = pulls(ready, cards)

    def first(tasks: list[Task]) -> Task | None:
        return pick_next(tasks, done, set(waiting), dict(cards), pulled)

    def lead(task: Task) -> bool:
        return router.lead_only(task.agent, task.files, protected)

    # no Claude needed (bug-04)
    if (task := first([t for t in ready if t.id in regate])) is not None:
        return task
    held = {t.id for t in ready if t.id in parked and parked[t.id]["kind"] != RESERVE_KIND}
    due = [t for t in ready if t.id in held and _due(parked[t.id], at)]
    began = due
    limited = windows.limited_until is not None and windows.limited_until > at
    free = [t for t in ready if t.id not in held and not (limited and lead(t))]
    held_in_lane = allowance.lead_hold(
        CLAUDE, windows.claude, LEAD_COST, at, reserves=dispatch.LANE_RESERVES
    )
    in_lane = [
        t
        for t in began + free
        if t.id in lane and (t in began or not lead(t) or held_in_lane is None)
    ]
    if (task := first(in_lane)) is not None:
        return task
    passed_over = waits._passed_over(windows, at) is not None
    if (task := first(began)) is not None:
        return task
    fixes = [
        t
        for t in free
        if t.milestone != BUGS
        and short_key(t.milestone) in reviewing
        and not (passed_over and lead(t))
    ]
    if (fix := first(fixes)) is not None and (
        not lead(fix)
        or (
            allowance.lead_hold(CLAUDE, windows.claude, LEAD_COST, at, reserves=windows.reserves)
            is None
            and waits._held_at_the_limit(windows, at) is None
        )
    ):
        return fix
    developers = [t for t in free if not lead(t)]
    task = first(developers if passed_over else free)
    if task is None and passed_over and fill_gap:
        task = first(free)  # nothing else can start: the first lead ticket fills the gap (ADR 50)
    if task is None or not lead(task):
        return task
    if waits._held_at_the_limit(windows, at) is not None:
        return first(developers)  # only Claude's real limit stops lead work
    # Past the 5-hour mark developer tickets go first, and a lead one fills the gap
    if (
        allowance.lead_hold(CLAUDE, windows.claude, LEAD_COST, at, reserves=windows.reserves)
        is None
    ):
        return task
    return first(developers) or (task if fill_gap else None)


def _next_task(
    s: Session, ready: list[Task], done: set[str], paused: set[str], *, fill_gap: bool = True
) -> Task | None:
    """`choose_ticket` from the session."""
    at = session.now()
    windows = waits._windows_now(s, at)
    lane = reserve_cards(s.repo, ready)
    return choose_ticket(
        ready,
        done,
        paused,
        cards=_cards(s.repo, ready),
        regate=s.state.regate,
        parked=s.state.parked,
        windows=windows,
        lane=lane,
        protected=tuple(read_protected(s.repo)),
        at=at,
        reviewing=under_review(s.state),
        fill_gap=fill_gap,
    )


def _hold_for_the_owner(s: Session) -> bool:
    """While the owner pauses the factory (ADR 22 item 5), the pick takes nothing but planning:
    the run neither ends nor sleeps to a reset, but holds, "paused by you", applying every
    request of theirs (a plant, a message, an approval, their resume) every ``HOLD_POLL_S``
    seconds: the run is git's one writer and nothing else runs meanwhile. The hold ends at the
    resume or as soon as a planner job can go (its ⚑, f6-14); the pick then runs it and holds
    again. The hold is no limit's `wait`: the pause's own usage event (`runner.requests`)
    counts it as stopped for the owner. False, and no hold, when the run has no project row to
    read a resume from: it ends instead."""
    since = datetime.fromisoformat(str(s.state.owner_pause)).astimezone()
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
    MAIN_RED_KIND: "failing check on main",
    LOGIN_KIND: "expired Claude login",
}


def _counted(count: int, what: str) -> str:
    return f"{count} {what}" if count == 1 else f"{count} {what}s"


def _tickets_wait(count: int, what: str, kind: str = "ticket") -> str:
    return f"{_counted(count, kind)} {'waits' if count == 1 else 'wait'} {what}"


def _lead_tickets_passed_over(
    s: Session, ready: list[Task], paused: set[str], held: Mapping[str, str], at: datetime
) -> str | None:
    """The lead tickets only Claude's real limit holds (ADR 50 item 3, F264 D3) and until when: a
    full window's reset, or a window's rest. None when there are none."""
    windows = waits._windows_now(s, at)
    if waits._held_at_the_limit(windows, at) is None:
        return None
    skipped = {*paused, *held, *waits_for_main(s, ready), *reserve_cards(s.repo, ready)}
    done = task_ids(s.tasks_dir("done"))
    protected = tuple(read_protected(s.repo))
    count = sum(
        router.lead_only(t.agent, t.files, protected)
        and t.id not in skipped
        and t.id not in s.state.parked
        and all(dep in done for dep in t.depends_on)
        for t in ready
    )
    if not count:
        return None
    holding = [
        w
        for w in windows.claude
        if allowance.lead_hold(CLAUDE, [w], FULL, at, reserves=AT_THE_LIMIT)
    ]
    ends = [(allowance.lead_goes_at(w, FULL, at), w) for w in holding]
    known = [(e, w) for e, w in ends if e is not None]
    if not known:
        return _tickets_wait(count, "for Claude", "lead ticket")
    end, last = max(known, key=lambda pair: pair[0])
    until = end.astimezone()
    if any(allowance.resting(w, at) for w in holding):
        return _tickets_wait(count, f"for Claude until {until:%a %H:%M}", "lead ticket")
    label = allowance.LABELS.get(last.name, last.name)
    return _tickets_wait(
        count, f"for Claude's {label} · until about {until:%a %H:%M}", "lead ticket"
    )


def _idle_line(s: Session, ready: list[Task], paused: set[str], held: Mapping[str, str]) -> str:
    """Why the run has nothing to run (F101 D2), each cause once, from what the pick knows:
    the tickets parked for Claude with the earliest reset, the lead tickets Claude's windows pass
    over, those behind a blocked or escalated one or a sign-off, and the open owner items by
    kind."""
    at = session.now()
    causes = []
    parked = [s.state.parked[t.id] for t in ready if t.id in s.state.parked]
    parked = [entry for entry in parked if not _due(entry, at)]
    if parked:
        resets = min(_resets(entry) for entry in parked).astimezone()
        if all(entry.get(LOGIN_HELD) for entry in parked):
            what = "for Claude's login"
        else:
            what = f"for Claude until {resets:%a %H:%M}"
        causes.append(_tickets_wait(len(parked), what))
    if passed_over := _lead_tickets_passed_over(s, ready, paused, held, at):
        causes.append(passed_over)
    if paused:
        causes.append(_tickets_wait(len(paused), "behind a blocked or escalated one"))
    if held:
        causes.append(_tickets_wait(len(held), "for a sign-off"))
    if red := waits_for_main(s, ready):
        causes.append(_tickets_wait(len(red), f"for {MAIN} to pass its checks"))
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
    new_day = local_clock().date() != s.report.started.astimezone().date()
    if new_day and (s.report.tasks or s.report.claude_runs):
        s.report.idle = True
        return False
    try:
        _idle_wait()
    except KeyboardInterrupt:
        s.log(f"[{RUNNER_AGENT}] Ended by you.")
        return False
    return True


def _planning_goes(s: Session) -> bool:
    """Whether a planner or setup job could run now, paused or not (`dispatch.plan`)."""
    rows = [row for row in open_rows(s) if row.kind in dispatch.PLANNING]
    return dispatch.pick(rows, [], dispatch.Windows(), session.now(), paused=True) is not None


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
    _follow_main(s.repo)
    if _runner_code(s.repo) == code:
        return False
    s.report.notes.append(RESTART_NOTE)
    session.set_activity(s, "restarting after a runner change")
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


def _follow_main(repo: Path) -> None:
    """ADR 46 item 3: the session's project's running app follows its main. Never raises."""
    try:
        stack = stacks.stack_for(repo)
        if stack is not None:
            stacks.follow_main(stack)
    except Exception as exc:
        stamp = f"{local_clock():%H:%M:%S}"
        print(f"[{stamp}] [{RUNNER_AGENT}] following main failed for {repo.name}: {exc}")


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
        stamp = f"{local_clock():%H:%M:%S}"
        print(f"[{stamp}] [{RUNNER_AGENT}] softfield's reinstall failed: {err or out}")


RESTART_NOTE = (
    "Stopped: Claude changed runner/ (a lead ticket or an escalation), "
    "so the runner needs a fresh process."
)


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
    # a fast-lane card's review is queued first, held only by a job of its own card (F242 D2)
    lane = [key for key in lane_reviews(s.repo, s.state) if not _holds_review(rows, key)]
    if lane:
        key = lane[0]
    elif due and not any(row.kind in SUPPORT for row in rows):
        key = due[0]
    else:
        return
    if s.project_id is not None:
        _record(s, metrics.upsert_milestone, s.project_id, key, status=metrics.REVIEW_DUE)
    enqueue(s, REVIEW, key, review_reason(key))


def sync_pause(s: Session) -> bool:
    """The owner's pause is the factory's (ADR 22 item 5): this project holds for an open
    pause event whichever project's request took it, and lets go once that event is resumed.
    A pause in state.json with no event holds until a resume. True when the state changed.
    2026-11-18: the top bar's Pause landed in travel-companion's state, and Softfield's
    direction ran under it."""
    db = getattr(s, "db", None)
    if db is None:  # no metrics database (or a test's stand-in session)
        return False
    was = s.state.owner_pause
    try:
        since = metrics.open_pause(db)
        if since is not None:
            s.state.owner_pause = since
        elif was is not None and metrics.pause_ended(db, was):
            s.state.owner_pause = None
    except Exception as exc:
        _metrics_failed(s, exc)
    return s.state.owner_pause != was


def apply_owner_requests(s: Session) -> None:
    """The owner's requests from the dashboard (f5 D2), at each pick: the run is git's one
    writer, so it applies them itself, as their console commands would, and turns off the
    switches whose 24 hours are over. A switch turned on frees what waited for it. The first
    time, the queue's order moves to its list (F222 D4). Best effort, like every write."""
    from runner.requests import apply_requests, move_to_list  # it imports this module

    at = session.now()
    was_on = {switch: switch_on(s.state, switch, at) for switch in SWITCHES}
    try:  # a move that fails leaves the numbers ordering the work, and the requests applied
        moved = move_to_list(s.repo)
    except Exception as exc:
        moved = [f"the board's order wasn't moved to its list: {type(exc).__name__}: {exc}"]
    listed = order.read_order(s.repo) if moved else None
    if listed is not None and s.project_id is not None:  # the dashboard's copy (F222 D5)
        _record(s, metrics.set_board_order, s.project_id, listed)
    try:
        lines = moved + apply_requests(s.repo, s.cfg.metrics_db, at, s.state)
    except Exception as exc:
        _metrics_failed(s, exc)
        return
    for line in lines:
        s.log(f"[{RUNNER_AGENT}] the owner's request: {line}")
    s.report.notes += [line for line in lines if line.startswith(notify.NOT_SENT)]
    if sync_pause(s) or lines:
        save_state(s.state, s.state_path)
        sync_tickets(s)  # a queued ticket shows in the queue at once
    if lines:
        sync_cards(s)  # an approved card shows Planted at once, not Seed (F245)
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
    lane_only: bool = False,
    fill_gap: bool = True,
    before_job: Callable[[], None] | None = None,
) -> bool:
    """Work through .softfield/tasks/ready (one milestone's, if given) and the queued jobs their
    runs
    trigger: directions, checkpoints and escalations (ADR 22). Each turn runs what
    `dispatch.pick` returns; the next ticket is `_next_task`'s. Returns True if Claude (a lead
    ticket or an escalation) changed the runner, which needs a restart.

    The fast lane goes before everything (ADR 35 item 2): its tickets, and a queued direction
    or escalation about one of them. Otherwise a queued job goes before any ticket, a parked
    one once its reset has passed; a ticket
    parked for a Claude limit goes first among tickets once its reset has passed. Until then
    only developer tickets run, and with none left the queue sleeps until the earliest reset.
    A lead ticket over Claude's week pace line is passed over, by `choose_ticket` (ADR 44).
    `dispatch.pick` is given empty windows on purpose (F219 D6): it receives one ticket, already
    chosen, and queued jobs park themselves as they start (`claude_hold`); a real window there
    would pass over a ticket at the 5-hour mark, and it would never park. While the owner pauses
    it (f5-18), it holds between jobs until they resume.

    With ``reviews`` (`runner run`, f4-20), a milestone whose tickets are all done queues its
    review, which stops the queue before its next ticket: ``s.report.review`` names it, for
    the command to review. One Claude can't take now parks instead, and the queue goes on
    (F53 D1). Without ``escalate``, no escalation is queued or run. With
    ``once``, it stops after one ticket and the jobs that ticket queued.

    For `run_projects` (ADR 30 item 6): without ``take_tickets`` it runs one queued job, so
    the round asks the fast lane again before the next;
    with ``lane_only`` (F235 D1) only the fast lane, its tickets and the directions and
    escalations about them, so the round can run every project's lane before any queued job;
    without ``fill_gap`` a lead ticket that would only fill the gap over the pace is left
    (F279 D5);
    without ``wait`` it never holds or sleeps here (for Claude's reset, the owner's pause or
    nothing to run) but returns, so the next project can go; ``before_job`` runs once a job is
    picked, before it starts (the factory's plan is stored then, F279 D1).

    With ``reviews`` and without ``once`` (the standing `runner run`), it doesn't return with
    nothing to run: it holds, saying what it waits for (`_idle_line`), and each turn applies
    the owner's requests and picks again (F101). It returns for a due review, the owner's
    Ctrl-C, or the day's report (`_idle_holds`). A Ctrl-C between two polls is `run_session`'s.
    """
    code = code_at_start(s.repo)
    ran: Task | None = None  # the ticket that ran, for ``once``
    idle: str | None = None  # the idle line the run shows while it holds (F101)
    while True:
        if _new_code(s, code):  # a commit made outside the run (a terminal session's)
            return True
        if idle is None:
            session.set_activity(s, PICKING)
        apply_owner_requests(s)
        check_backup(s)
        check_push(s)
        set_aside_unreadable(s)
        check_login(s)
        waits.fresh_reading(s)
        # ADR 48: a project started from the Projects page gets only its setup until it passes
        being_set_up = setting_up(s)
        if reviews and not being_set_up:
            _queue_due_review(s)
        _look_at_main(s)
        ready = load_dir(s.tasks_dir("ready"), s.cfg.default_max_diff)
        if milestone is not None:  # either form of the key (ADR 16 item 6)
            ready = [t for t in ready if short_key(t.milestone) == short_key(milestone)]
        done = task_ids(s.tasks_dir("done"))
        paused = blocked_ids(ready, stopped_ids(s.repo / ".softfield" / "tasks"))
        held = _held(s.repo, ready)
        rows = _runnable_rows(s, ready, escalate=escalate, reviews=reviews)
        behind = waiting_rows(s, ready)
        red = waits_for_main(s, ready)
        task = (
            _next_task(
                s, ready, done, paused | held.keys() | behind.keys() | red, fill_gap=fill_gap
            )
            if take_tickets
            else None
        )
        # the fast lane (ADR 35), with the escalated tickets of its cards (F191 D2)
        lane = lane_with_escalated(
            s.repo, ready, load_dir(s.tasks_dir("escalated"), s.cfg.default_max_diff)
        )
        if reviews:  # a fast-lane card's review goes with the lane (F242 D1)
            lane = lane | set(lane_reviews(s.repo, s.state))
        if lane_only:  # the round's first pass (F235 D1): nothing but the lane
            rows = [r for r in rows if r.kind in dispatch.LANE_KINDS and r.subject in lane]
            task = task if task is not None and task.id in lane else None
        if being_set_up:
            rows, task, lane = [r for r in rows if r.kind == SETUP], None, set()
        tickets = [] if task is None else [_dispatch_ticket(s, task, ready)]
        paused_by_owner = s.state.owner_pause is not None
        # F124 D1: the project's own pause holds what the factory's does, for it alone
        own_pause = None if being_set_up else project_pause(s)
        archived = not being_set_up and project_archived(s)  # F262 D3: held the same way
        job = dispatch.pick(
            rows,
            tickets,
            dispatch.Windows(),
            session.now(),
            paused=paused_by_owner or own_pause is not None or archived,
            first=lane,
            hold=dispatch.ARCHIVED if archived and not paused_by_owner else dispatch.PAUSED,
        )
        if once and ran is not None and not _about(job, ran):
            return False  # the round goes on: the lane, then the queue in project order
        if job is None:
            if paused_by_owner:
                if wait and _hold_for_the_owner(s):
                    continue
                return False
            if own_pause is not None or archived:  # an idle project, as the top bar ranks it
                line = IDLE + (
                    paused_by_you_since(own_pause) if own_pause is not None else dispatch.ARCHIVED
                )
                if line != idle:
                    idle = line
                    if wait:  # `run_projects` says it as its activity alone, each round
                        s.log(f"[{RUNNER_AGENT}] {line}")
                    session.set_activity(s, line)
                if wait and reviews and not once and _idle_holds(s):
                    continue
                return False
            # ADR 51: nothing else can start and Claude is out: Copilot reads a finished milestone
            if (
                reviews
                and not once
                and take_tickets
                and not lane_only
                and not being_set_up
                and _pre_review_turn(s)
            ):
                continue
            if wait and _wait_for_reset(s, ready, rows):
                continue
            if reviews and not once and wait:  # the standing command holds (F101 D1)
                line = _idle_line(s, ready, paused, held)
                if line != idle:
                    idle = line
                    s.log(f"[{RUNNER_AGENT}] {line}")
                    session.set_activity(s, line)
                if _idle_holds(s):
                    continue
            if not wait:  # `run_projects` goes to the next project; this one says why it waits
                if reviews and not once and take_tickets:
                    session.set_activity(s, _idle_line(s, ready, paused, held))
                return False
            if paused:
                s.report.notes.append("Paused (dependency escalated): " + ", ".join(sorted(paused)))
            if held:
                s.report.notes.append("Waiting: " + _waits_text(held))
            return False
        if idle is not None:
            idle = None
            session.set_activity(s, PICKING)
        if before_job is not None:
            before_job()
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
            if not take_tickets:  # one queued job a round: the fast lane goes next (F235 D1)
                return False
            continue
        with doing(s, task.id):
            rec = run_task(s, task)
        after_ticket(s, task, rec, escalate=escalate)
        s.picks += 1
        if _new_code(s, code):
            return True
        ran = task


def _about(job: dispatch.Pick | None, task: Task) -> bool:
    """Whether ``job`` is the work its ticket queued, which a ``once`` turn still runs: its
    direction or escalation, or its card's checkpoint. Anything else (a planner reply, a
    review, another ticket's job) goes back to `project_round`, which asks the fast lane and
    then each project in order (2026-11-18: travel-companion's turn ran three planner replies
    after its ticket while F122 waited in Softfield's lane)."""
    if job is None:
        return False
    if job.kind in (DIRECTION, ESCALATION):
        return job.subject == task.id
    return job.kind == CHECKPOINT and job.subject == task.milestone


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
    lane = lane_reviews(s.repo, s.state) if reviews and support else []  # F242 D2
    return [
        row
        for row in rows
        if (row.kind != ESCALATION or escalate)
        and (
            row.kind != REVIEW
            or (reviews and not support)
            or (row.subject in lane and not _holds_review(rows, row.subject))
        )
        and (row.kind != DIRECTION or row.subject in mine | gone)
    ]


def _dispatch_ticket(s: Session, task: Task, ready: list[Task]) -> dispatch.Ticket:
    """The ticket `_next_task` chose, as the pick sees it."""
    lead = router.lead_only(task.agent, task.files, tuple(read_protected(s.repo)))
    cards = _cards(s.repo, ready)
    early = early_for(task, cards, pulls(ready, cards))
    regate = task.id in s.state.regate
    return dispatch.Ticket(task.id, lead, task_place(task, cards), early_for=early, regate=regate)


def run_session(cfg: Config, *, once: bool, dry_run: bool, escalate: bool) -> SessionReport | None:
    """`runner run`: the queue, until a milestone's review is due (f4-20) or the owner ends
    it; with nothing to run it holds (F101). With ``once``, until it is empty."""
    if dry_run:
        dry_run_plan(cfg)
        return None
    s = open_session(cfg)
    check_backup(s)  # the run's start; each pick checks again (F20 D1)
    check_push(s)
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
    fast lane (ADR 35 item 2, F235 D1: its lane tickets, and the directions and escalations
    about them), then one queued job, the first project's that has one (the owner's planning
    replies, directions, checkpoints, escalations: they never wait behind another project's
    ticket, and the lane is asked again before the next), then one ticket
    from the first project that has one it can run, a lead ticket that only fills the gap over
    the pace last (F279 D5). While the owner pauses, no lane and no
    ticket (ADR 35 item 5): the planning replies still go. Returns (restart, a job ran)."""
    held = any(s.state.owner_pause is not None for s in sessions)
    for s in [] if held else sessions:
        restart, ran = turn(s, lane_only=True, once=True)
        if restart or ran:
            return restart, ran
    for s in sessions:
        restart, ran = turn(s, take_tickets=False)
        if restart or ran:
            return restart, ran
    if held:  # a pause holds every project
        return False, False
    # The gap is the factory's (ADR 50 item 2): a lead ticket fills it only when no project has
    # anything else that can start, so the second pass lets the first project's fill it.
    for fill_gap in (False, True):
        for s in sessions:
            restart, ran = turn(s, once=True, fill_gap=fill_gap)
            if restart or ran:
                return restart, ran
    return False, False


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
    running: list[Config] = []  # the round's projects, whose plan is stored (F279 D1)
    planned: list[datetime] = []  # when it was stored last

    def plan_now() -> None:  # never stops the run
        at = session.now()
        planned[:] = [at]
        try:
            store_plan(running, at)
        except Exception as exc:
            stamp = f"{local_clock():%H:%M:%S}"
            line = f"the queue's plan wasn't stored ({type(exc).__name__}: {exc})"
            print(f"[{stamp}] [{RUNNER_AGENT}] {line}", flush=True)

    def turn(s: Session, **kw: Any) -> tuple[bool, bool]:
        # A card or ticket committed outside the run (`softfield init`'s setup session, a
        # terminal session) reaches the board at the next round, not the next session
        head = session._main_head(s)
        if head is not None and synced.setdefault(s.repo, head) != head:
            sync_tickets(s)
            sync_cards(s)
            synced[s.repo] = head
        before = s.picks
        busy.append(s)
        restart = work_queue(
            s, escalate=escalate, reviews=True, wait=False, before_job=plan_now, **kw
        )
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
                    and local_clock().date() != s.report.started.astimezone().date()
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
                            stamp = f"{local_clock():%H:%M:%S}"
                            print(f"[{stamp}] [{RUNNER_AGENT}] {cfg.project_name}: {exc}")
                        continue
                    refused.discard(cfg.repo)
                    sessions[cfg.repo] = s
                live.append(s)
            for s in live:  # the round's hold is the factory's pause, as it stands now
                if sync_pause(s):
                    save_state(s.state, s.state_path)
            running[:] = [s.cfg for s in live]
            restart, ran = project_round(live, turn)
            if restart:
                return True
            if not ran:
                if not planned or session.now() - planned[0] >= PLAN_EVERY:
                    plan_now()
                _idle_wait()
    except KeyboardInterrupt:
        print(f"[{local_clock():%H:%M:%S}] [{RUNNER_AGENT}] Ended by you.", flush=True)
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
    at = session.now()
    return next(
        (r["run_dir"] for r in rows if at - datetime.fromisoformat(r["heartbeat"]) < LIVE), None
    )


def queue_ticket(cfg: Config, wanted: str) -> str:
    """Move a ticket from .softfield/tasks/later/ (or blocked/, F106 D3) to .softfield/tasks/ready/
    in a
    commit of its own (ADR 17 item 3); ``wanted`` is its id or a unique prefix. Tasks only, so the
    commit skips the hook.
    Refused while a run is live: the runner commits on the same branch."""
    if (run := live_run(cfg)) is not None:
        raise RunnerError(f"run {run} is running; queue {wanted} once it has stopped")
    return move_to_ready(cfg.repo, wanted)


def move_to_ready(repo: Path, wanted: str) -> str:
    """`queue_ticket`'s move and commit, for a caller that is git's one writer: the command
    once no run is live, or the run itself applying the owner's request (f5 D2). A ticket in
    later/ first, else one in blocked/, tried again (F106 D3): its ``task/<id>`` is copied to
    ``blocked/<id>`` first, since a lead ticket starts again from main and resets its branch."""
    tasks = repo / ".softfield" / "tasks"
    try:
        src = find_ticket(tasks, LATER, wanted)
    except TaskError as later:
        try:
            src = find_ticket(tasks, "blocked", wanted)
        except TaskError:
            raise later from None
    git = Git(repo)
    if src.parent.name == "blocked":
        keep_blocked_work(git, src.stem)
    _move_alone(git, src, tasks / "ready", f"queue {src.stem} (by the owner)")
    return src.stem


def keep_blocked_work(git: Git, task_id: str) -> None:
    """A ticket leaving blocked/ (tried again, set aside, or brought back by a replan): its
    ``task/<id>`` copied to ``blocked/<id>``, replacing an older copy, since a lead ticket
    starts again from main and resets its branch (F106 D3)."""
    if _has_branch(git, f"task/{task_id}"):
        git.run("branch", "-f", f"blocked/{task_id}", f"task/{task_id}")


def set_aside(repo: Path, wanted: str) -> str:
    """A blocked ticket moved to later/ in a commit of its own, the owner's ``set_aside``
    request (F106 D3); its branch stays as it is, copied too (``keep_blocked_work``) for when
    it is queued again from later/."""
    src = find_ticket(repo / ".softfield" / "tasks", "blocked", wanted)
    git = Git(repo)
    keep_blocked_work(git, src.stem)
    later = repo / ".softfield" / "tasks" / LATER
    _move_alone(git, src, later, f"set aside {src.stem} (by the owner)")
    return src.stem


def _move_alone(git: Git, src: Path, folder: Path, message: str) -> None:
    """A ticket moved to ``folder``, the move alone committed. Tasks only: the commit skips the
    hook."""
    dst = folder / src.name
    git.move(src, dst)
    paths = (src.relative_to(git.repo).as_posix(), dst.relative_to(git.repo).as_posix())
    git.run("commit", "-q", "--no-verify", "-m", message, "--", *paths)


def set_aside_unreadable(s: Session) -> None:
    """A ready ticket that doesn't parse, moved to later/ with a console line and a report note,
    so it waits on its card for a fix instead of stopping the run: F6's review wrote one with
    ``tests: []`` and every `load_dir` of ready/ raised (2026-10-22)."""
    ready, later = s.tasks_dir("ready"), s.tasks_dir(LATER)
    for path in sorted(ready.glob("*.md")):
        try:
            parse_task(path, s.cfg.default_max_diff)
        except (ValueError, yaml.YAMLError, UnicodeDecodeError) as exc:  # TaskError among them
            later.mkdir(parents=True, exist_ok=True)
            _move_alone(s.git, path, later, f"runner: set aside {path.stem}: {exc}")
            line = f"Set aside {path.stem} in later/: it doesn't read as a ticket ({exc})."
            s.log(f"[{RUNNER_AGENT}] {line}")
            s.report.notes.append(line)


def _held(repo: Path, ready: list[Task]) -> dict[str, str]:
    """Ready tickets whose milestone waits for another's sign-off (ADR 17 item 4)."""
    from runner.milestone import waits_for  # runner.milestone imports this module

    return held_ids(ready, waits_for(repo, (t.milestone for t in ready)))


def _cards(repo: Path, ready: list[Task]) -> dict[str, int]:
    """The ready tickets' places, from the queue's list (F222 D1, each card's short key and
    bug's id to its place); with no list yet, none, so they go by milestone, then id."""
    return order.places(order.read_order(repo) or [], ready)


def reserve_cards(repo: Path, ready: list[Task]) -> set[str]:
    """The ready tickets that may use Claude's reserve (ADR 34 item 3, F172 D3): those of a
    card in the fast lane (``**Fast lane:** yes``), and every ready ticket they wait for through
    ``depends_on``, whatever its card. A dependency already done adds nothing."""
    from runner.milestone import card  # runner.milestone imports this module

    marked = set()
    for key in {t.milestone for t in ready if t.milestone != BUGS}:
        doc = milestone_file(repo, "cards", key)
        if doc.is_file() and card(key, doc.read_text(encoding="utf-8")).reserve:
            marked.add(short_key(key))
    by_id = {t.id: t for t in ready}
    found: set[str] = set()
    todo = [t.id for t in ready if t.milestone != BUGS and short_key(t.milestone) in marked]
    while todo:
        task_id = todo.pop()
        if task_id in by_id and task_id not in found:
            found.add(task_id)
            todo.extend(by_id[task_id].depends_on)
    return found


def lane_with_escalated(repo: Path, ready: list[Task], escalated: list[Task]) -> set[str]:
    """`reserve_cards` plus the escalated tickets of a fast-lane card (F191 D2): the escalation
    moved its ticket out of ready/, but the card's place in the lane stays."""
    lane = reserve_cards(repo, ready)
    # the same reading as `reserve_cards`, over the escalated tickets
    return lane | reserve_cards(repo, escalated) & {t.id for t in escalated}


def lane_reviews(repo: Path, state: State) -> list[str]:
    """The full keys of the due reviews of cards in the fast lane (F242 D1), in milestone order:
    marked ``**Fast lane:** yes`` and not on its way out (still ready or building), whether or
    not they have a ready ticket. Their reviews go with the lane."""
    from runner.milestone import card, due_reviews  # runner.milestone imports this module

    found = []
    for key in due_reviews(repo, state):
        doc = milestone_file(repo, "cards", key)
        if not doc.is_file():
            continue
        parsed = card(key, doc.read_text(encoding="utf-8"))
        if parsed.reserve and parsed.state in ("ready", "building"):
            found.append(key)
    return found


def _holds_review(rows: Sequence[dispatch.Queued], key: str) -> bool:
    """Whether a checkpoint or an escalation of the card ``key`` is queued: its review waits."""
    short = short_key(key)
    return any(
        row.kind in SUPPORT and (row.subject == key or row.subject.startswith(f"{short}-"))
        for row in rows
    )


def _uses_reserve(s: Session, task: Task) -> bool:
    """Whether ``task`` may use Claude's reserve without the owner's switch (`reserve_cards`)."""
    return task.id in reserve_cards(s.repo, load_dir(s.tasks_dir("ready"), s.cfg.default_max_diff))


def _waits_text(held: dict[str, str]) -> str:
    return ", ".join(
        f"{task_id} waits for {key}'s sign-off" for task_id, key in sorted(held.items())
    )


def dry_run_plan(cfg: Config) -> None:
    """`runner run --dry-run` (f8-02): one project's `factory_plan`, printed."""
    dry_run_factory([cfg])


def dry_run_factory(configs: Sequence[Config]) -> None:
    """`softfield run --dry-run` (F279 D1): the factory's plan, as the runner would store it now,
    printed as one list (`print_plan`). It writes nothing."""
    print_plan(factory_plan(configs, session.now()))


WOULD_PARK = "would park or go to a stand-in"  # a queued job Claude's windows hold (bug-21)
NEXT = "Next: "  # the plan's last fact: what goes next
PLAN_EVERY = timedelta(minutes=1)  # a round that runs nothing stores the plan at most this often
_HEADS = {dispatch.LANE: "Fast lane", dispatch.JOBS: "Jobs", dispatch.GO: "Can go"}


@dataclass(frozen=True)
class _ProjectPlan:
    """One project's part of the factory's plan, read as `_project_plan` reads it."""

    name: str
    lines: tuple[dispatch.PlanLine, ...]
    chosen: str | None  # `choose_ticket`'s ticket; None while the owner holds the project
    windows: dispatch.Windows
    owner_pause: str | None  # the factory's pause, since when
    main_red: bool
    pre_review: Callable[[], str | None]  # the milestone Copilot would pre-review (ADR 51)
    minutes: tuple[float, ...]  # its last merged tickets' minutes (`ticket_minutes`)


def factory_plan(configs: Sequence[Config], at: datetime) -> dispatch.FactoryPlan:
    """The whole factory's plan (F279 D1–D4), in `project_round`'s order: every project's fast
    lane, then the queued jobs project by project in the owner's order, then the tickets that can
    go, then those that wait. The line picked is the first that goes: a job with no wait, or a
    project's `choose_ticket` ticket. With none, Copilot's pre-review if one is due (ADR 51).
    Reads each project's .softfield/tasks/, state.json and the metrics database if there is one;
    writes nothing (f1-33)."""
    projects = [_project_plan(cfg, at) for cfg in configs]
    chosen = {p.name: p.chosen for p in projects}

    def place(line: dispatch.PlanLine) -> tuple[int, bool]:
        # A lead ticket that only fills the gap goes after every project's tickets that can
        # start (F279 D5), as `project_round`'s second pass runs it; else project by project
        gap = line.group == dispatch.GO and (line.waits or "").startswith(dispatch.GAP)
        return dispatch.GROUPS.index(line.group), gap

    lines = tuple(sorted((line for p in projects for line in p.lines), key=place))

    def goes(line: dispatch.PlanLine) -> bool:
        if line.kind == dispatch.TICKET:
            return line.subject == chosen[line.project]
        return line.waits is None

    picked = next((n for n, line in enumerate(lines) if goes(line)), None)
    next_up, next_project = "nothing", None
    if picked is not None:
        next_up, next_project = (
            _job_name(lines[picked].kind, lines[picked].subject),
            lines[picked].project,
        )
    else:
        for p in projects:
            if (milestone := p.pre_review()) is not None:
                next_up = f"Copilot's pre-review of {short_key(milestone).upper()}"
                next_project = p.name
                break
    facts = [fact] if (fact := _claude_reading(projects, at)) else []
    developers = sum(
        line.who == "developer" and line.group == dispatch.GO and line.waits is None
        for line in lines
    )
    facts.append(_runway(developers, [m for p in projects for m in p.minutes]))
    facts.append(f"{NEXT}{next_up}" + (f" ({next_project})" if next_project else ""))
    return dispatch.FactoryPlan(
        at, picked, _sentence(projects, lines, at), tuple(facts), lines, next_up
    )


def _sentence(
    projects: Sequence[_ProjectPlan], lines: Sequence[dispatch.PlanLine], at: datetime
) -> str:
    """What drives the order now (F279 D4), from `choose_ticket`'s inputs, the first that
    applies: the owner's pause, a red main, Claude's limit, the pace line or a mark, the fast
    lane, else the board's order."""
    if (since := next((p.owner_pause for p in projects if p.owner_pause), None)) is not None:
        when = datetime.fromisoformat(since).astimezone()
        return f"Paused by you since {when:%H:%M}: only planning goes until you resume"
    if (red := next((p.name for p in projects if p.main_red), None)) is not None:
        return f"Main fails its tests on {red}: what needs main waits for its fix"
    for p in projects:
        if (limit := _limit_words(p.windows, at)) is not None:
            return limit
    for p in projects:
        over = waits._passed_over(p.windows, at) or allowance.lead_hold(
            CLAUDE, p.windows.claude, LEAD_COST, at, reserves=p.windows.reserves
        )
        if over is not None:
            return "Over pace: developers first, the lead when nothing else can"
    if any(line.group == dispatch.LANE for line in lines):
        return "The fast lane goes first"
    return "Your board's order, the lead and developers alike"


def _limit_words(windows: dispatch.Windows, at: datetime) -> str | None:
    """ "Claude at its limit until <when>" while a job is parked for a limit or a window is full
    or resting (`_held_at_the_limit`), else None."""
    limited = windows.limited_until is not None and windows.limited_until > at
    if not limited and waits._held_at_the_limit(windows, at) is None:
        return None
    ends = [windows.limited_until] if limited and windows.limited_until is not None else []
    for window in windows.claude:
        full = allowance.lead_hold(CLAUDE, [window], FULL, at, reserves=AT_THE_LIMIT) is not None
        if full and (end := allowance.lead_goes_at(window, FULL, at)) is not None:
            ends.append(end)
    if not ends:
        return "Claude at its limit: developers only"
    return f"Claude at its limit until {dispatch._when(max(ends), at)}: developers only"


def _claude_reading(projects: Sequence[_ProjectPlan], at: datetime) -> str | None:
    """Claude's week as the top bar reads it ("week 82% used, today's pace 42%"), else its
    5-hour window; None with no reading."""
    windows = next((p.windows.claude for p in projects if p.windows.claude), ())
    by_name = {w.name: w for w in windows}
    for name in ("seven_day", "five_hour"):
        window = by_name.get(name)
        if window is None or not window.capacity:
            continue
        text = f"Claude's {allowance.LABELS[name]} {window.used / window.capacity:.0%} used"
        if (line := allowance.pace_line(window, at)) is not None:
            text += f", today's pace {line / window.capacity:.0%}"
        if window.resets_at is not None:
            text += f"; resets {dispatch._when(window.resets_at, at)}"
        return text
    return None


def _runway(count: int, minutes: Sequence[float]) -> str:
    """The developers' runway (F279 D4): the tickets they can take now, and about how long they
    take at the median of the last merged tickets (`ticket_minutes`)."""
    if not count:
        return "No developer ticket can go now"
    text = f"{_counted(count, 'developer ticket')} can go now"
    if minutes:
        text += f", about {count * statistics.median(minutes):.0f} min"
    return text


def store_plan(configs: Sequence[Config], at: datetime) -> None:
    """The factory's plan stored in the metrics database (F279 D1), replacing the last one."""
    plan = factory_plan(configs, at)
    for db in dict.fromkeys(cfg.metrics_db for cfg in configs):
        conn = metrics.open_db(db)
        try:
            metrics.store_queue_plan(conn, plan)
        finally:
            conn.close()


def _project_plan(cfg: Config, at: datetime) -> _ProjectPlan:
    """One project's lines for `factory_plan`: `dispatch.plan`'s list, each job with what it
    waits for and why it is there, `choose_ticket`'s ticket as the runner would take it (ADR 44
    item 9), and each ticket's pre-flight problems (runner/instructions/task-writing.md). A due
    review not queued yet is listed as the run would queue it, and a support job an older
    state.json parked as the row the run makes of it. A queued job only Claude's windows hold
    would park or go to a stand-in as it starts, as the run picks it with none (bug-21)."""
    from runner.milestone import due_reviews  # runner.milestone imports this module

    tasks = cfg.repo / ".softfield" / "tasks"
    ready = load_dir(tasks / "ready", cfg.default_max_diff)
    done = task_ids(tasks / "done")
    paused = blocked_ids(ready, stopped_ids(tasks))
    state = load_state(cfg.runs_dir / "state.json")
    queued, readings, refusals = _stored_queue(cfg)
    queued += _parked_support(state.parked, at)
    if not any(q.kind in SUPPORT for q in queued):
        reviewing = {q.subject for q in queued if q.kind == REVIEW}
        due = [key for key in due_reviews(cfg.repo, state) if key not in reviewing]
        queued += [dispatch.Queued(REVIEW, key, review_reason(key), at.isoformat()) for key in due]
    behind = {
        q.subject: f"waits for its {q.kind}" for q in queued if q.kind in (DIRECTION, ESCALATION)
    }
    red = _held_by_red_main(cfg.repo, state, ready)
    behind |= {t: f"waits for {MAIN} to pass its checks" for t in red if t not in behind}
    tickets = _dispatch_tickets(
        cfg.repo, ready, done, paused, state.parked, at, behind, state.regate.keys()
    )
    claude = _claude_windows_from(cfg, readings, refusals, at)
    windows = _pick_windows(state, claude, queued, at)
    lane = lane_with_escalated(cfg.repo, ready, load_dir(tasks / "escalated", cfg.default_max_diff))
    lane |= set(lane_reviews(cfg.repo, state))  # a lane card's review (F242 D1)
    # the factory's pause, or the project's own (F124 D4): its tickets are "paused by you"
    stored = _stored_paused(cfg)  # its own pause (F124 D4) or its archive (F262 D3)
    own = metrics.paused_by_you(stored)
    by_the_owner = state.owner_pause is not None or own is not None or metrics.is_archived(stored)
    hold = dispatch.ARCHIVED if metrics.is_archived(stored) and state.owner_pause is None else None
    # A parked row says its own wait in the list: only a parked ticket limits the other rows. A
    # ticket's line goes by what `choose_ticket` goes by, a parked row's limit included.
    listed = _pick_windows(state, claude, [], at)
    why = hold or dispatch.PAUSED
    rows = dispatch.plan(queued, tickets, listed, at, paused=by_the_owner, first=lane, hold=why)
    held = dispatch.plan(queued, tickets, windows, at, paused=by_the_owner, first=lane, hold=why)
    free = dispatch.plan(
        queued, tickets, dispatch.Windows(), at, paused=by_the_owner, first=lane, hold=why
    )
    # The run picks a queued job with no windows; Claude's limit then parks it or hands it to a
    # stand-in as it starts (`claude_hold`): its line says so (bug-21)
    out = dispatch._limited(listed, at) or waits._held_at_the_limit(listed, at)
    lines = []
    for row, ticket, picked in zip(rows, held, free, strict=True):
        if ticket.pick.kind == dispatch.TICKET:
            lines.append(ticket)
        elif picked.waits is None and (row.waits or out) is not None:
            lines.append(dispatch.Line(row.pick, f"{WOULD_PARK} ({row.waits or out})"))
        else:
            lines.append(row)

    chosen = choose_ticket(
        ready,
        done,
        paused | _held(cfg.repo, ready).keys() | behind.keys(),
        cards=_cards(cfg.repo, ready),
        regate=state.regate,
        parked=state.parked,
        windows=windows,
        lane=lane,
        protected=tuple(read_protected(cfg.repo)),
        at=at,
        reviewing=under_review(state),
    )
    next_id = None if chosen is None or by_the_owner else chosen.id

    def pre_review_next() -> str | None:  # nothing else can start (ADR 51), as the runner asks
        if by_the_owner or not cfg.metrics_db.is_file() or not cfg.roles.get(STAND_IN):
            return None
        conn = metrics.open_db(cfg.metrics_db)
        try:
            project = metrics.find_project(conn, cfg.project_name)
            passed = None if project is None else metrics.passed_pre_reviews(conn, project)
        finally:
            conn.close()
        return pre_review_pick(cfg.repo, state, windows, at, passed)

    by_id = {t.id: t for t in ready}
    by_ticket = {t.id: t for t in tickets}
    name = cfg.project_name

    def plan_line(line: dispatch.Line) -> dispatch.PlanLine:
        kind, subject = line.pick.kind, line.pick.subject
        if kind != dispatch.TICKET:
            task = by_id.get(subject) if kind in (DIRECTION, ESCALATION) else None
            card = _card_of(task.milestone) if task else None
            if kind in (CHECKPOINT, REVIEW):
                card = _card_of(subject)
            where = dispatch.group(line, lane=lane)
            reason = line.pick.reason
            return dispatch.PlanLine(
                name, kind, subject, reason, None, where, line.waits, reason, card
            )
        task, ticket = by_id[subject], by_ticket[subject]
        goal = task.sections.get("Goal", "").strip()
        return dispatch.PlanLine(
            name,
            kind,
            subject,
            goal.splitlines()[0] if goal else "",
            "lead" if ticket.lead else "developer",
            dispatch.group(line, lane=lane, chosen=subject == next_id),
            line.waits,
            line.pick.reason,
            _card_of(task.milestone),
            ticket.early_for,
            tuple(preflight(task, cfg.repo)),
        )

    return _ProjectPlan(
        name,
        tuple(plan_line(line) for line in lines),
        next_id,
        windows,
        state.owner_pause,
        state.main_red is not None,
        pre_review_next,
        tuple(_stored_minutes(cfg)),
    )


def _card_of(key: str) -> str | None:
    """A milestone key's card, as the board names it; None for the bugs or a key that isn't one."""
    if key == BUGS:
        return None
    try:
        return short_key(key)
    except TaskError:
        return None


def _stored_minutes(cfg: Config) -> list[float]:
    """`ticket_minutes` for the project, none without a metrics database; a read makes none."""
    if not cfg.metrics_db.is_file():
        return []
    conn = metrics.open_db(cfg.metrics_db)
    try:
        project = metrics.find_project(conn, cfg.project_name)
        return [] if project is None else ticket_minutes(conn, project)
    finally:
        conn.close()


def _stored_paused(cfg: Config) -> str | None:
    """The project's ``paused`` for the dry run, which has no session; a read makes no
    database."""
    if not cfg.metrics_db.is_file():
        return None
    conn = metrics.open_db(cfg.metrics_db)
    try:
        found = metrics.project_state(conn, cfg.project_name)
    finally:
        conn.close()
    return None if found is None else found[1]


def _stored_queue(
    cfg: Config,
) -> tuple[list[dispatch.Queued], dict[str, sqlite3.Row], list[sqlite3.Row]]:
    """The project's open ``work_queue`` rows, Claude's latest readings and its refusals; none
    without a metrics database, and a read makes none."""
    if not cfg.metrics_db.is_file():
        return [], {}, []
    conn = metrics.open_db(cfg.metrics_db)
    try:
        project = metrics.find_project(conn, cfg.project_name)
        rows = [] if project is None else metrics.open_jobs(conn, project)
        readings = metrics.latest_readings(conn, f"{CLAUDE}-")
        refusals = metrics.refusals(conn, f"{CLAUDE}-")
    finally:
        conn.close()
    return [dispatch.Queued.from_row(row) for row in rows], readings, refusals


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
    regate: Collection[str] = (),
) -> list[dispatch.Ticket]:
    """The ready tickets in run order (f5 D6), each with what it waits for, as `_next_task`
    sees them: one parked for a limit until its reset, one ``behind`` its queued direction or
    escalation for it. Claude's windows aren't in it: `dispatch.plan` asks them."""
    behind = behind or {}
    held = _held(repo, ready)
    cards = _cards(repo, ready)
    pulled = pulls(ready, cards)
    protected = tuple(read_protected(repo))
    tickets = []
    for task in sorted(ready, key=lambda t: run_order(t, cards, pulled)):
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
        if entry is not None and _still_parked(entry, at):
            not_before = at if entry.get(RETRY) else _resets(entry)
        lead = router.lead_only(task.agent, task.files, protected)
        place, early = task_place(task, cards), early_for(task, cards, pulled)
        gates = task.id in regate
        tickets.append(dispatch.Ticket(task.id, lead, place, waits, not_before, early, gates))
    return tickets


def _still_parked(entry: dict[str, Any], at: datetime) -> bool:
    """A parked entry that says when its ticket goes: not an older run's at the week's reserve,
    nor one at the 5-hour window whose reset has passed, which began no work and so waits for
    Claude's windows as any lead ticket does (ADR 44 items 1 and 7)."""
    return entry["kind"] != RESERVE_KIND and not (
        entry["kind"] == FIVE_HOUR_KIND and _due(entry, at)
    )


def _job_name(kind: str, subject: str) -> str:
    if kind == dispatch.TICKET:
        return subject
    if kind == dispatch.REVIEW:
        return f"review {short_key(subject).upper()}"
    return f"{kind} {subject}"


def print_plan(plan: dispatch.FactoryPlan) -> None:
    """The factory's plan for the terminal (F279 D1): its sentence and facts, then each line
    in the order it would run under its group's heading, with its project, the pick marked,
    and each ticket's pre-flight problems under it; last, what goes next."""
    print(plan.sentence)
    for fact in plan.facts:
        if not fact.startswith(NEXT):  # the last line says it
            print(f"  · {fact}")
    heading = None
    for n, line in enumerate(plan.lines):
        if line.group != heading:
            heading = line.group
            print(f"{_HEADS.get(heading, 'Waits')}:")
        marker = "->" if n == plan.picked else "  "
        name = _job_name(line.kind, line.subject)
        print(f"{marker} {name}: {line.waits or 'runnable'}, {line.reason}  [{line.project}]")
        for problem in line.preflight:
            print(f"     pre-flight: {problem}")
    print(f"next: {plan.next_up}")


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
