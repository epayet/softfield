"""A developer ticket's job (F290 D1): its attempts, gates, direction, merge, red main and
block. `runner.loop` schedules it; the lead and review jobs import what they share with it."""

import itertools
import sqlite3
import time
from collections.abc import Collection, Iterable, Mapping, Sequence
from functools import partial
from http.client import HTTPException
from pathlib import Path
from typing import Any

from runner import (
    checks,
    console,
    messages,
    metrics,
    notify,
    planner,
    prompts,
    router,
    session,
)
from runner.agents import (
    ANY,
    CHECK_COMMANDS,
    GIT_READ_COMMANDS,
    JobResult,
    JobSpec,
    adapter_for,
)
from runner.config import read_protected
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
    GitError,
    with_trailers,
)
from runner.local_model import ADAPTER as OPENCODE
from runner.local_model import (
    OPENCODE_DB,
    empty_cause,
    is_local,
    loaded_context_length,
    session_reasoning,
    stop_reason,
    warmup,
)
from runner.report import TaskRecord
from runner.session import (
    CLAUDE_HEADLESS_AGENT,
    DIRECTION,
    FIVE_HOUR_KIND,
    MAIN,
    NOTE_FILE,
    PLANNER,
    RUNNER_AGENT,
    Parked,
    Session,
    Ticker,
    _attempt_end,
    _catch_up,
    _direction_reason,
    _finish_attempt,
    _has_branch,
    _record,
    _record_readings,
    _record_refusal,
    _rel,
    _row_waits,
    _set_in_flight,
    _tokens_in,
    _tokens_out,
    attempt_progress,
    candidates,
    doing,
    enqueue,
    find_row,
    finish_row,
    lead_work_ready,
    local_wip_commit,
    next_number,
    park_row,
    record_start,
    record_ticket,
    runner_commit,
    with_progress,
)
from runner.state import State, save_state
from runner.tasks import (
    Task,
    TaskError,
    append_footer,
    blocked_ids,
    load_dir,
    parse_task,
    preflight,
)
from runner.waits import (
    agent_windows,
    claude_hold,
)

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
    from runner.loop import current_ratings  # runner.loop imports this module

    at = session.now()
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
    for attempt, session_id in enumerate(rec.sessions, start=1):
        text = session_reasoning(OPENCODE_DB, session_id)
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
    if (hold := claude_hold(s, session.now())) is not None:
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
        edit=(".softfield/var/runs/**",),
        commands=GIT_READ_COMMANDS,
    )
    direction_file, ticket_file = logs / "direction.md", logs / "ticket.md"
    session.call_claude(
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
                RUNNER_AGENT, f"{task.id} waits for its direction", parked.resets_at, session.now()
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
            try:
                with doing(s, "warm-up"):
                    rec.warmup_s += warmup(s.cfg.lm_base_url, s.cfg.lm_model, s.cfg.warmup_timeout)
            except (OSError, HTTPException) as exc:
                # A model that just crashed answers with an error, and this stopped every
                # project's run (2026-11-03). The attempt finds out for itself, and costs one.
                note = f"{task.id} attempt {attempt}: the warm-up failed: {exc}"
                s.log(note)
                s.report.notes.append(note)
            else:
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
            run = OPENCODE.run(agent, spec, s.repo, log, session.now(), on_progress=progress)
        else:
            run = with_progress(
                partial(adapter_for(agent.harness).run, agent, spec, s.repo, log, session.now()),
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
    note = str(entry.get("note") or "gates run again after a stop")
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
            note=note,
        )
    return failed


def run_task(s: Session, task: Task, directing: Mapping[str, Any] | None = None) -> TaskRecord:
    """One ticket. Its result is "parked" when it waits for Claude (a limit, the 5-hour window, or
    its turn behind the support work a yes to the 5-hour question freed) or behind its queued
    direction. ``directing`` is that direction's needs: the run that gives it, then the last
    attempt."""
    from runner.loop import run_lead_task  # runner.loop imports this module

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
        s.ticket_started = session.clock()
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
    waited = s.state.waits_on_main.pop(task.id, None)
    if regate is not None or waited is not None:
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
        if failed.name == ALL_TESTS and _waits_for_red_main(s, task, logs, attempt, job_id, agent):
            rec.attempts = attempt - 1  # it costs no attempt (F80 F1)
            rec.result = "waits for main"
            return rec
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
    from runner.loop import rate_finished  # runner.loop imports this module

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
    s.log(console.merged(agent, task_id, rec.attempts, lines, session.clock() - s.ticket_started))


# --- lead tickets (ADR 12 item 9) --------------------------------------------------------


def _check_results(s: Session, task_id: str | None, logs: Path, name: str) -> list[checks.Check]:
    with doing(s, f"check-all · {task_id}" if task_id else "check-all on main"):
        results = checks.check_all(s.repo, s.cfg.gate_timeout, task_id=task_id)
    (logs / name).write_text(checks.render(results), encoding="utf-8")
    return results


def _check_all(s: Session, task_id: str | None, logs: Path, name: str) -> bool:
    return all(r.ok for r in _check_results(s, task_id, logs, name))


def _on_main(s: Session, names: Sequence[str], logs: Path) -> list[checks.Check]:
    """Only the checks ``names``, on main (F106 D5)."""
    with doing(s, f"{', '.join(names)} on main"):
        results = checks.check_all(s.repo, s.cfg.gate_timeout, only=names)
    (logs / "check-main.txt").write_text(checks.render(results), encoding="utf-8")
    return results


MAIN_RED_KIND = "main-red"  # main fails a lead ticket's checks too; its subject is the check
FIRST_LINES = 3  # of the failing check's output, in the owner's item


def red_main_text(failing: checks.Check, task_id: str, branch: str, mender: str | None) -> str:
    """The owner's item when main fails a check a lead ticket failed (F106 D5)."""
    lines = " / ".join(line for line in failing.output.splitlines()[:FIRST_LINES] if line.strip())
    text = f"main fails {failing.name}" + (f": {lines}" if lines else "")
    text += f" · {task_id}'s work waits on {branch}; no other lead ticket runs until main passes"
    return text + (f" · {mender} would mend it" if mender else "")


def _mender(s: Session, task_id: str, failing: Sequence[checks.Check]) -> str | None:
    """The first ready ticket whose ``files:`` names a file the failing checks name."""
    said = "\n".join(c.output for c in failing)
    for t in load_dir(s.tasks_dir("ready"), s.cfg.default_max_diff):
        if t.id != task_id and any(f in said for f in t.files):
            return t.id
    return None


def _main_is_red(s: Session, task: Task, failed: Sequence[str], logs: Path) -> bool:
    """F106 D5: a lead ticket failed ``failed``; whether main fails every one of them too. Then
    the ticket isn't blocked: its work waits on its branch for main to pass, the owner has one
    item saying what fails and which ticket would mend it, and no other lead ticket runs."""
    on_main = _on_main(s, failed, logs)
    if any(r.ok for r in on_main):
        return False
    branch = f"task/{task.id}"
    mender = _mender(s, task.id, on_main)
    s.state.main_red = {
        "checks": list(failed),
        "head": session._main_head(s),
        "ticket": task.id,
        "mender": mender,
    }
    s.state.waits_on_main[task.id] = branch
    save_state(s.state, s.state_path)
    text = red_main_text(on_main[0], task.id, branch, mender)
    if s.project_id is not None:
        _record(
            s,
            metrics.upsert_owner_item,
            s.project_id,
            MAIN_RED_KIND,
            on_main[0].name,
            text=text,
            command="",
            created=session.now().isoformat(),
        )
    s.report.notes.append(f"Main is red: {text}")
    s.log(f"⚠ [{RUNNER_AGENT}] {text}")
    return True


ALL_TESTS = "all-tests"  # the one gate main itself can fail: the others judge the diff alone
MAIN_TESTS = "tests"  # check-all's name for it


def _waits_for_red_main(
    s: Session, task: Task, logs: Path, attempt: int, job_id: int | None, agent: str
) -> bool:
    """F80 F1: a developer attempt failed only ``all-tests``; whether main fails them too. Then
    it waits on its branch as a lead ticket does (F106 D5), costing no attempt and no game: once
    main passes, only its gates run again, and its job gets their outcome."""
    s.git.checkout(MAIN)
    if not _main_is_red(s, task, [MAIN_TESTS], logs):
        s.git.checkout(f"task/{task.id}")
        return False
    s.state.regate[task.id] = {
        "attempt": attempt,
        "agent": agent,
        "job_id": job_id,
        "note": "gates run again once main passed",
    }
    save_state(s.state, s.state_path)
    return True


def _look_at_main(s: Session) -> None:
    """While main is red, each commit on it that could change a check (not docs or tickets
    alone) runs the checks it failed again; once it passes them all, the owner's item
    resolves and the lead's tickets run again (F106 D5)."""
    red = s.state.main_red
    head = session._main_head(s)
    if red is None or head is None or head == red["head"]:
        return
    try:
        changed = s.git.run("diff", "--name-only", str(red["head"]), head).split()
    except GitError:
        changed = []  # its old head is gone: look again
    red["head"] = head
    save_state(s.state, s.state_path)
    if checks.hook_can_skip(changed):
        return
    names = list(red["checks"])
    if not all(r.ok for r in _on_main(s, names, _logs_dir(s.run_dir, "main"))):
        return
    s.state.main_red = None
    save_state(s.state, s.state_path)
    _resolve_item(s, MAIN_RED_KIND, "")
    s.log(f"[{RUNNER_AGENT}] main passes {', '.join(names)} again: the lead's tickets run again")


def waits_for_main(s: Session, ready: Iterable[Task]) -> set[str]:
    """The tickets held while main is red, all but the one that would mend it: the lead's, and
    a developer's whose work waits on its branch (F80 F1)."""
    return _held_by_red_main(s.repo, s.state, ready)


def _held_by_red_main(repo: Path, state: State, ready: Iterable[Task]) -> set[str]:
    red = state.main_red
    if red is None:
        return set()
    protected = tuple(read_protected(repo))
    return {
        t.id
        for t in ready
        if (router.lead_only(t.agent, t.files, protected) or t.id in state.waits_on_main)
        and t.id != red.get("mender")
    }


BLOCKED_KIND = "blocked"  # a blocked ticket's owner item; its subject is the ticket's id


def blocked_text(task_id: str, reason: str, waiting: int) -> str:
    """A blocked ticket's owner item (F106 D1), as ``block`` and the verdict write it."""
    if not waiting:
        return f"{task_id} blocked: {reason}"
    behind = f"{waiting} ticket waits" if waiting == 1 else f"{waiting} tickets wait"
    return f"{task_id} blocked: {reason} · {behind} behind it"


def block(s: Session, task_path: Path, reason: str) -> None:
    """Move a task to blocked/ with its reason; its dependants pause (ADR 12 item 10). The owner
    has it on their desk at once (F106 D1), with no command: the desk's buttons answer it."""
    from runner.loop import rate_finished  # runner.loop imports this module

    target = s.tasks_dir("blocked") / task_path.name
    s.git.move(task_path, target)
    append_footer(target, {"result": "blocked", "reason": reason})
    runner_commit(s, f"runner: {task_path.stem} blocked: {reason}")
    record_ticket(s, target)
    rate_finished(s, task_path.stem)
    s.report.notes.append(f"Blocked {task_path.stem}: {reason}")
    waiting = waiting_behind(s, target.stem)
    if s.project_id is not None:
        was_open = _record(s, notify.open_items, s.project_id)
        _record(
            s,
            metrics.upsert_owner_item,
            s.project_id,
            BLOCKED_KIND,
            target.stem,
            text=blocked_text(target.stem, reason, waiting),
            command="",  # an older item's rerun command goes too
            created=session.now().isoformat(),
        )
        if was_open is not None and (BLOCKED_KIND, target.stem) not in was_open:
            session._notify(s, *notify.item_message(BLOCKED_KIND, target.stem))  # ADR 31 item 3
    where = f"ticket in {target.relative_to(s.repo).as_posix()}"
    s.log(console.stopped(task_path.stem, "blocked", reason, where, waiting))
    _look_at_block(s, target, reason, escalated=task_path.parent.name == "escalated")


def _look_at_block(s: Session, ticket: Path, reason: str, *, escalated: bool) -> None:
    """ADR 29 items 1, 4–6: one look each time a ticket of a card is blocked. The runner's own
    message on the card's thread (an archived one opens again) and its planner row; none for a
    bug, which has no card, nor without the metrics database."""
    if s.project_id is None or s.db is None:
        return
    try:
        thread = planner.thread_key(parse_task(ticket, s.cfg.default_max_diff).milestone)
    except (TaskError, planner.PlannerError):  # a bug's thread key is refused: no card
        return
    branches = ([f"escalation/{ticket.stem}"] if escalated else []) + [f"task/{ticket.stem}"]
    branch = next((b for b in branches if _has_branch(s.git, b)), None)
    runs = [p for p in s.run_dir.glob(f"{ticket.stem}*") if _run_of(p.name, ticket.stem)]
    logs = max(runs, key=lambda p: _run_of(p.name, ticket.stem) or 0, default=s.run_dir)
    text = planner.look_text(ticket.stem, reason, branch, _rel(s, logs))
    _record(s, _queue_look, s.project_id, thread, text, session.now().isoformat())


def _run_of(name: str, task_id: str) -> int | None:
    """Which run of ``task_id`` a log folder is (``_logs_dir``'s names): 1, 2, …, else None."""
    if name == task_id:
        return 1
    n = name.removeprefix(f"{task_id}-run")
    return int(n) if n != name and n.isdigit() else None


def _queue_look(conn: sqlite3.Connection, project_id: int, thread: str, text: str, at: str) -> None:
    found = metrics.planner_thread(conn, project_id, thread, at)
    if found["archived"] is not None:  # as an owner's message does
        metrics.set_thread_archived(conn, found["id"], None)
    said = metrics.add_planner_message(conn, found["id"], planner.RUNNER, at, text)
    reason = f"a ticket blocked on {planner.thread_name(thread)}"
    metrics.queue_job(conn, project_id, PLANNER, planner.look_subject(thread, said), reason, at)


def _resolve_items(conn: sqlite3.Connection, project_id: int, kind: str, subject: str) -> None:
    """``kind``'s open items about ``subject`` (every one, for an empty subject) resolved."""
    at = session.now().isoformat()
    for row in metrics.open_owner_items(conn, project_id):
        if row["kind"] == kind and subject in ("", row["subject"]):
            metrics.resolve_owner_item(conn, row["id"], at)


def _resolve_item(s: Session, kind: str, subject: str) -> None:
    if s.project_id is not None:
        _record(s, _resolve_items, s.project_id, kind, subject)
