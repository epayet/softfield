"""How the runner waits on Claude's limits: the windows and readings, the login check, the
hold, parking support jobs, passing over and waiting for room (f290 D1). The owner's
switches themselves are in `runner/session.py`, which its jobs share."""

import sqlite3
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from functools import partial

from runner import allowance, console, dispatch, metrics, session
from runner.agents import Agent
from runner.claude import probe
from runner.config import Config
from runner.local_model import is_local
from runner.session import (
    CHECKPOINT,
    CLAUDE,
    FIVE_HOUR,
    FIVE_HOUR_HELD,
    LOGIN_CHECK,
    LOGIN_HELD,
    LOGIN_REASON,
    QUEUED,
    RESERVE_KIND,
    RETRY,
    REVIEW,
    RUNNER_AGENT,
    SWITCHES,
    WEEK,
    Session,
    _at,
    _due,
    _login_asked,
    _login_items,
    _record,
    _record_readings,
    _rel,
    _resets,
    _row_name,
    _set_row,
    _unpark_row,
    doing,
    lead_work_ready,
    open_rows,
    park_row,
    row_key,
    switch_on,
    wait_for_claude,
)
from runner.state import State, save_state
from runner.tasks import Task

# --- routing (f1-25, runner/router.py) ----------------------------------------------------

UNKNOWN = "plan"  # the one window of an agent with no reading: capacity unknown (ADR 15 item 2)


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


# --- parking and the reserve (ADR 15 items 4, 5 and 10) --------------------------------


# Where Claude's week stands now decides the park: a lead ticket's share of the week
# isn't learned yet, so its expected cost is left at 0.
LEAD_COST = 0.0


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
    login: bool = True,
) -> list[tuple[datetime, str]]:
    """`_limits_ahead`'s resets, each with what it is for: the parked tickets (``tickets``,
    if given) and the parked support jobs (``rows``, else every open one). Without ``login``,
    the jobs held only for an expired login are left out: no time ends their wait."""
    rows = open_rows(s) if rows is None else rows
    return _ahead_in(s.state, rows, at, tickets, five_hour=five_hour, login=login)


def _ahead_in(
    state: State,
    rows: Sequence[dispatch.Queued],
    at: datetime,
    tickets: Collection[str] | None = None,
    *,
    five_hour: bool = True,
    login: bool = True,
) -> list[tuple[datetime, str]]:
    """`_parked_ahead` from what the state and the queue hold, for a run and a dry run alike."""
    found = [
        (_resets(entry), _parked_name(key))
        for key, entry in state.parked.items()
        if entry["kind"] != RESERVE_KIND
        and (five_hour or not entry.get(FIVE_HOUR_HELD))
        and (login or not entry.get(LOGIN_HELD))
        and (tickets is None or key in tickets)
        and not _due(entry, at)
    ]
    for row in rows:
        parks = row.kind in QUEUED or row.kind == REVIEW  # a review's row parks too (F53 D1)
        if not parks or row.not_before is None or _at(row.not_before) <= at:
            continue
        needs = state.queued.get(row_key(row), {})
        if (five_hour or not needs.get(FIVE_HOUR_HELD)) and (login or not needs.get(LOGIN_HELD)):
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


def _claude_windows_from(
    cfg: Config, readings: Mapping[str, sqlite3.Row], refusals: list[sqlite3.Row], at: datetime
) -> list[allowance.Window]:
    """Claude's windows for the runner and the dry run alike (F219 D3): from its latest readings,
    each with what it keeps back (the week's reserve for the lead's support roles, the 5-hour
    window's share for the owner, ADR 16), and resting after a refusal in it (`_rested`)."""
    return [_rested(w, refusals, at) for w in _kept_back(cfg, _windows_from(readings, at))]


def _kept_back(cfg: Config, windows: Iterable[allowance.Window]) -> list[allowance.Window]:
    kept = {"seven_day": cfg.claude_reserve, "five_hour": cfg.five_hour_reserve}
    return [replace(w, reserve=kept.get(w.name, 0.0)) for w in windows]


def rested_claude_windows(s: Session, at: datetime) -> list[allowance.Window]:
    """`_claude_windows_from` the metrics database."""
    readings = _record(s, metrics.latest_readings, f"{CLAUDE}-") or {}
    refusals = _record(s, metrics.refusals, f"{CLAUDE}-") or []
    return _claude_windows_from(s.cfg, readings, refusals, at)


def _pick_windows(
    state: State, claude: Sequence[allowance.Window], rows: Sequence[dispatch.Queued], at: datetime
) -> dispatch.Windows:
    """What may keep Claude from a ticket now, for `choose_ticket` and `dispatch.plan`."""
    reserves = {
        name
        for name, switch in (("seven_day", WEEK), ("five_hour", FIVE_HOUR))
        if switch_on(state, switch, at)
    }
    return dispatch.Windows(claude, _limited_until(state, rows, at), reserves)


def _windows_now(s: Session, at: datetime) -> dispatch.Windows:
    return _pick_windows(s.state, rested_claude_windows(s, at), open_rows(s), at)


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
    at = session.now()
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
            ended=session.now().isoformat(),
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
            f" going by the stored one from {stored.astimezone():%H:%M}"
        )
        return
    read = ", ".join(f"{r.window} {r.utilization:.0%}" for r in result.readings)
    s.log(f"[{PROBE_AGENT}] fresh reading of Claude's windows: {read}")


def _resolve_login_items(conn: sqlite3.Connection) -> None:
    at = session.now().isoformat()
    for row in _login_items(conn):
        metrics.resolve_owner_item(conn, row["id"], at)


def check_login(s: Session) -> None:
    """At each pick, with a job held for the login or the owner still asked, and at most every
    ``LOGIN_CHECK``: one probe. A failed one holds the jobs until the next check; a passing one
    clears the item and frees them, with no restart. A new session asks at its first pick: the
    owner may have logged in before restarting, and the restart's retries wait for this."""
    entries = [entry for entry in s.state.parked.values() if entry.get(LOGIN_HELD)]
    rows = [r for r in open_rows(s) if s.state.queued.get(row_key(r), {}).get(LOGIN_HELD)]
    if not entries and not rows and not _login_asked(s):
        return
    at = session.now()
    if s.login_checked is not None and at - s.login_checked < LOGIN_CHECK:
        return
    s.login_checked = at
    with doing(s, "checking Claude's login"):
        result = probe(s.repo, s.run_dir / "claude-login.log", at)
    _record_readings(s, PROBE_AGENT, result.readings)
    if result.ok:
        for entry in entries:
            del entry[LOGIN_HELD]
            entry[RETRY] = True
        for row in rows:
            del s.state.queued[row_key(row)][LOGIN_HELD]
            _unpark_row(s, row)
        _record(s, _resolve_login_items)
        s.log(f"[{RUNNER_AGENT}] Claude's login works again: {len(entries) + len(rows)} jobs go on")
    else:
        until = at + LOGIN_CHECK
        for entry in entries:
            entry.pop(RETRY, None)
            entry["resets_at"] = until.isoformat()
        for row in rows:
            s.state.queued[row_key(row)].pop(RETRY, None)
            _set_row(s, row, until)
        s.log(f"[{RUNNER_AGENT}] {LOGIN_REASON}: asked again at {until.astimezone():%H:%M}")
    save_state(s.state, s.state_path)


@dataclass(frozen=True)
class Hold:
    """Why Claude may not take a support job now, and until when."""

    until: datetime
    reason: str
    five_hour: bool  # only the owner's share of the 5-hour window holds it: its switch lifts it
    login: bool = False  # only an expired login holds it: `check_login` frees it


def claude_hold(s: Session, at: datetime) -> Hold | None:
    """Whether a support job (a direction, a checkpoint, an escalation, a review) must wait
    for Claude (ADR 16 item 4): a job parked for a limit, or a window at its real limit or
    resting after a refusal. Neither the week's reserve nor the 5-hour mark holds it (ADR 50
    items 3 and 4)."""
    if ahead := _limits_ahead(s, at, five_hour=False):
        login = not _parked_ahead(s, at, five_hour=False, login=False)
        reason = LOGIN_REASON if login else "Claude is limited"
        return Hold(max(min(ahead), at + timedelta(minutes=1)), reason, False, login)
    windows = rested_claude_windows(s, at)
    kept = {"seven_day", "five_hour"}
    fit = allowance.answer(CLAUDE, windows, FULL, at, use_reserve=kept)
    if fit.ok:
        return None
    ends = [
        w.cooldown_until or w.resets_at
        for w in windows
        if not allowance.answer(CLAUDE, [w], FULL, at, use_reserve=kept).ok
    ]
    until = min(
        (e for e in ends if e is not None), default=at + timedelta(seconds=s.cfg.backoff_min)
    )
    return Hold(max(until, at + timedelta(minutes=1)), fit.reason, False)


def _park_support(s: Session, role: str, name: str, hold: Hold, /, **resume: str) -> None:
    """Park a checkpoint or an escalation Claude can't take now (ADR 16 item 4): its row waits
    until ``hold`` ends (f8 D3), and the queue goes on meanwhile. ``resume`` is what it needs
    to start again; its session, if it had one, stays in ``interrupted``."""
    what = role if role == CHECKPOINT else f"{role} of {name}"
    flag = {LOGIN_HELD: True} if hold.login else {}
    park_row(s, role, name, hold.until, hold.five_hour, **resume, **flag)
    s.report.notes.append(f"Parked the {what}: {hold.reason}.")
    s.log(console.paused(RUNNER_AGENT, f"the {what} waits for Claude", hold.until, session.now()))


def park_review(s: Session, milestone: str) -> bool:
    """Before a round of a review `runner run` started (F53 D1): when Claude can't take it
    now, its row parks until the hold ends, as a checkpoint's does, and the queue goes on with
    the developers' tickets. Returns whether it parked. A parked review is no stop: its rounds
    stay in ``State.review_counts``, for it to go on from the round it was at."""
    if (hold := claude_hold(s, session.now())) is None:
        return False
    _park_support(s, REVIEW, milestone, hold)
    return True


def wait_for_room(s: Session, what: str) -> None:
    """Before a support job with no queue to go back to (a review under `runner milestone`):
    while Claude can't take it, wait for the reset (ADR 16 items 3 and 4). When only the
    owner's share holds it, the 5-hour switch turned on meanwhile ends the wait. `runner run`
    parks its reviews instead (`park_review`)."""
    while (hold := claude_hold(s, session.now())) is not None:
        at = session.now()
        wait = max(60.0, (hold.until - at).total_seconds() + 60)
        resumes = at + timedelta(seconds=wait)
        s.log(console.paused(RUNNER_AGENT, f"{what} waits for Claude ({hold.reason})", resumes, at))
        until = partial(_five_hour_switched, s) if hold.five_hour else None
        wait_for_claude(s, wait, resumes, what, until=until)


def _week_switched_on(s: Session) -> None:
    """The owner turned the week's switch on: the run is on the reserve, and the lead tickets the
    week held go at the next pick (ADR 44 item 3)."""
    if s.run_id is not None:
        _record(s, metrics.set_run_reserve, s.run_id)


def _five_hour_switched(s: Session) -> bool:
    """While the run waits for the owner's 25%: whether the 5-hour switch is on now, taking
    the dashboard's switches alone (f5 D2); the other requests wait for the pick."""
    at = session.now()
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


def _passing_over(windows: dispatch.Windows, at: datetime) -> list[allowance.Window]:
    """The windows that pass a lead ticket over, rather than park it: all but the 5-hour window at
    the owner's share, which parks it when nothing else can run (ADR 44 items 6 and 8). One
    resting after a refusal has nothing to ask the owner: it passes it over too."""
    return [w for w in windows.claude if w.name != "five_hour" or allowance.resting(w, at)]


def _passed_over(windows: dispatch.Windows, at: datetime) -> str | None:
    """Why the windows pass a lead ticket over now, or None."""
    passing = _passing_over(windows, at)
    return allowance.lead_hold(CLAUDE, passing, LEAD_COST, at, reserves=windows.reserves)


AT_THE_LIMIT = dispatch.LANE_RESERVES  # whole capacities: only a real limit holds
FULL = dispatch.FULL


def _held_at_the_limit(windows: dispatch.Windows, at: datetime) -> str | None:
    """Why Claude's real limit keeps a lead ticket from a gap, or None (ADR 50 item 3, F264 D1):
    a window at 100%, or resting after a refusal. The pace line and the marks only order."""
    return allowance.lead_hold(CLAUDE, windows.claude, FULL, at, reserves=AT_THE_LIMIT)


def _wait_for_reset(s: Session, ready: list[Task], rows: Sequence[dispatch.Queued]) -> bool:
    """With nothing runnable left, sleep until the earliest reset a parked ticket or queued
    job (of ``rows``) waits for. False when none does: a lead ticket the week holds is parked for
    nothing, and each pick asks again. While work waits for the owner's 25%, the 5-hour switch
    turned on ends the sleep."""
    at = session.now()
    tickets = {t.id for t in ready}
    # An expired login has no reset to sleep to: the run holds, and each pick checks it
    ahead = _parked_ahead(s, at, tickets, rows=rows, login=False)
    if not ahead:
        return False
    held = len(ahead) > len(_parked_ahead(s, at, tickets, five_hour=False, rows=rows, login=False))
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


def _limited_until(state: State, rows: Sequence[dispatch.Queued], at: datetime) -> datetime | None:
    """`claude_hold`'s limit: the first reset ahead of a job parked for one, the owner's
    share of the 5-hour window left out."""
    return min((resets for resets, _ in _ahead_in(state, rows, at, five_hour=False)), default=None)
