"""The per-task loop and the session around it (docs/workflow.md)."""

import hashlib
import json
import sqlite3
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Concatenate

from runner import checks, messages, metrics, prompts
from runner.claude import (
    CHECK_TOOLS,
    EDIT_TOOLS,
    GIT_READ_TOOLS,
    READ_TOOLS,
    ClaudeJob,
    ClaudeResult,
    UsageLimited,
    backoff_seconds,
    run_claude,
)
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
    with_trailers,
)
from runner.local_model import (
    OPENCODE_DB,
    OpencodeRun,
    TokenTotals,
    empty_cause,
    loaded_context_length,
    run_opencode,
    session_reasoning,
    warmup,
)
from runner.report import ClaudeRunRecord, SessionReport, TaskRecord
from runner.state import State, load_state, save_state
from runner.tasks import (
    STOPPED,
    Task,
    append_footer,
    blocked_ids,
    carry_footers,
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
    # Jobs so far per (ticket, role group): the next job's `attempt` and its log's number.
    job_numbers: dict[tuple[str | None, str], int] = field(default_factory=dict)
    last_job_id: int | None = None  # the last Claude job's row, for its findings

    @property
    def repo(self) -> Path:
        return self.cfg.repo

    @property
    def state_path(self) -> Path:
        return self.cfg.runs_dir / "state.json"

    def tasks_dir(self, name: str) -> Path:
        return self.repo / "tasks" / name

    def log(self, message: str) -> None:
        print(f"[{now():%H:%M:%S}] {message}", flush=True)


def open_session(cfg: Config, command: str | None = "run") -> Session:
    """A session on a clean main. With a ``command``, it is recorded as a run in the metrics
    database; None records nothing."""
    git = Git(cfg.repo)
    if git.current_branch() != MAIN or not git.is_clean():
        raise RunnerError("start the runner on a clean main branch")
    started = now()
    run_dir = cfg.runs_dir / f"{started:%Y%m%d-%H%M%S}"
    run_dir.mkdir(parents=True, exist_ok=True)
    s = Session(
        cfg=cfg,
        git=git,
        state=load_state(cfg.runs_dir / "state.json"),
        report=SessionReport(started=started),
        run_dir=run_dir,
    )
    if command is not None:
        _start_run(s, command)
    return s


# --- the metrics database (f1 D2, D3): best effort ----------------------------------------


def _metrics_failed(s: Session, exc: Exception) -> None:
    if not s.db_failed:
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


def _start_run(s: Session, command: str) -> None:
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
        sync_tickets(s)


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
    except Exception:
        return
    goal = parse_sections(body).get("Goal", "").strip()
    difficulty = meta.get("difficulty")
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
        difficulty=difficulty if type(difficulty) is int else None,
        merged_by=merged_by,
        commit=commit,
        lines_changed=s.git.commit_size(commit) if commit else None,
    )


def _finish_run(s: Session, verdict: str) -> None:
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


def _finish_attempt(
    s: Session,
    job_id: int | None,
    run: OpencodeRun,
    outcome: str,
    *,
    gates: list[dict[str, object]] | None = None,
    note: str | None = None,
) -> None:
    if job_id is None or s.run_id is None:
        return
    at = now().isoformat()
    _record(
        s,
        metrics.finish_job,
        job_id,
        ended=at,
        outcome=outcome,
        tokens_in=run.tokens.input,
        tokens_out=run.tokens.output + run.tokens.reasoning,
        steps=run.tokens.steps,
        peak_context=run.tokens.peak,
        context_limit=s.context_limit,
        edit_streak=run.facts.edit_streak,
        refused_commands=run.facts.refused,
        gates=gates,
        note=note,
        session_id=run.facts.session_id or None,
    )
    _record(s, metrics.update_run_heartbeat, s.run_id, at)


def local_agent(cfg: Config) -> str:
    """D6: `local-<model>`, the LM Studio key without its publisher."""
    return "local-" + cfg.lm_model.rsplit("/", 1)[-1]


def claude_agent(s: Session, job: ClaudeJob) -> str:
    """D6: `claude-sonnet` for the checkpoint model's jobs, else the default `claude-opus`."""
    if job.model and job.model == s.cfg.checkpoint_model:
        return "claude-sonnet"
    return "claude-opus"


# --- headless Claude, with usage-limit pauses ------------------------------------------


UNSURE_LIMIT_RETRIES = 3  # an error that only looks like a limit: pause, but not forever
RESUME_PROMPT = (
    "You were stopped by a Claude usage limit, which has now reset. Carry on with the same"
    " job from where you stopped; `git diff` shows the changes you had made."
)
PARTIAL_WORK_NOTE = (
    "\n\nA previous run of this job was stopped part-way by a Claude usage limit. The files"
    " it changed are still in the working tree: check `git diff` (and any new files) before"
    " you start, and build on them or undo them."
)


def call_claude(
    s: Session, job: ClaudeJob, milestone: str, subject: str, *, ticket: str | None = None
) -> ClaudeResult:
    """Run a headless Claude job, waiting out usage limits. Each trigger bounds its own runs
    (ADR 12 item 10); the count per milestone is kept for the metrics.

    A job stopped mid-way by a limit resumes its session after the reset (f1: lead tickets
    cost 0.5-1.5M, so a limit will land inside one); if the session can't be resumed, it
    starts again, told that its partial work is in the tree.

    Each job is a row in the metrics database, with ``ticket`` (None for a milestone-wide
    job), and has its own logs: a second escalation of a ticket doesn't overwrite the first's."""
    attempt = unsure = 0
    resume: str | None = None
    interrupted = False
    number = next_number(s, ticket, job.kind)
    agent = claude_agent(s, job)
    base = f"claude-{job.kind}-{subject}" + (f"-{number}" if number > 1 else "")
    log = s.run_dir / f"{base}.log"
    job_id = s.last_job_id = record_start(
        s, ticket, milestone, job.kind, agent, attempt=number, log_path=_rel(s, log)
    )
    while True:
        prompt = (
            RESUME_PROMPT if resume else job.prompt + (PARTIAL_WORK_NOTE if interrupted else "")
        )
        log = s.run_dir / f"{base}{f'-retry{attempt}' if attempt else ''}.log"
        try:
            result = run_claude(
                replace(job, prompt=prompt), s.repo, s.cfg.claude_timeout, log, now(), resume=resume
            )
        except UsageLimited as limit:
            if not limit.certain:
                unsure += 1
                if unsure > UNSURE_LIMIT_RETRIES:
                    s.report.notes.append(
                        f"{job.kind} {subject}: failed {unsure} times with what looked like a"
                        " usage limit; treated as a failure."
                    )
                    result = ClaudeResult(ok=False, text=str(limit), duration_s=0.0)
                    break
            _record(
                s,
                metrics.add_usage_event,
                agent,
                now().isoformat(),
                "refusal",
                resets_at=limit.resets_at.isoformat() if limit.resets_at else None,
            )
            wait = (
                max(60.0, (limit.resets_at - now()).total_seconds() + 60)
                if limit.resets_at
                else backoff_seconds(attempt, s.cfg.backoff_min, s.cfg.backoff_max)
            )
            attempt += 1
            resume = limit.session_id or resume
            interrupted = True
            s.state.paused_until = (
                datetime.fromtimestamp(now().timestamp() + wait).astimezone().isoformat()
            )
            save_state(s.state, s.state_path)
            s.log(f"Claude usage limit reached; pausing {wait / 60:.0f} min, then resuming.")
            s.report.notes.append(f"Paused {wait / 60:.0f} min for a Claude usage limit.")
            time.sleep(wait)
            continue
        if resume and not result.ok and result.num_turns == 0:
            resume = None  # the session couldn't be resumed: start again, told about the tree
            attempt += 1
            continue
        break
    s.state.paused_until = None
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
            session_id=result.session_id,
            log_path=_rel(s, log),
        )
    s.report.claude_runs.append(
        ClaudeRunRecord(
            kind=job.kind,
            subject=subject,
            duration_s=result.duration_s,
            tokens_in=result.usage.get("input_tokens", 0),
            tokens_out=result.usage.get("output_tokens", 0),
            cache_read=result.usage.get("cache_read_input_tokens", 0),
            ok=result.ok,
        )
    )
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
    attempt: int,
    last: GateResult | None,
    timed_out: bool = False,
    direction: str = "",
) -> str:
    if last is None:
        return prompts.local_prompt(task)
    if direction:
        template, hint = prompts.DIRECTED, ""
    else:
        template = prompts.RETRY if attempt == 2 else prompts.FRESH
        hint = HINTS.get(last.name, "")
    extra = template.format(gate=last.name, hint=hint, output=last.output, direction=direction)
    return prompts.local_prompt(task, (prompts.TIMED_OUT if timed_out else "") + extra)


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
    repair the ticket instead. Returns the (maybe repaired) task and the direction."""
    s.state.directions[task.id] = s.state.directions.get(task.id, 0) + 1
    save_state(s.state, s.state_path)
    (logs / "last.diff").write_text(s.git.diff(MAIN), encoding="utf-8")
    rel = logs.relative_to(s.repo).as_posix()
    thinking = _save_thinking(rec, logs, s.repo)
    job = ClaudeJob(
        kind="direction",
        prompt=prompts.DIRECTION.format(
            id=task.id,
            task=task.path.relative_to(s.repo).as_posix(),
            logs=rel,
            thinking=", ".join(thinking) or "not available",
            streak=rec.edit_streak,
            timeouts=rec.timeouts,
        ),
        allowed_tools=(*READ_TOOLS, *GIT_READ_TOOLS, "Edit(var/runs/**)"),
    )
    call_claude(s, job, task.milestone, task.id, ticket=task.id)
    direction_file, ticket_file = logs / "direction.md", logs / "ticket.md"
    direction = (
        direction_file.read_text(encoding="utf-8").strip() if direction_file.is_file() else ""
    )
    rec.directed = bool(direction)
    if ticket_file.is_file():
        s.git.checkout(MAIN)
        task.path.write_text(ticket_file.read_text(encoding="utf-8"), encoding="utf-8")
        s.git.commit_all(
            with_trailers(
                f"direction {task.id}: ticket repaired (by Claude)", agent=CLAUDE_HEADLESS_AGENT
            )
        )
        task = parse_task(task.path, s.cfg.default_max_diff)
        record_ticket(s, task.path, "running")
    return task, direction


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
    s.log(f"{task.id}: escalated ({reason})")


def _logs_dir(run_dir: Path, task_id: str) -> Path:
    """A fresh log folder, so a requeued task's second run doesn't overwrite the first."""
    logs, n = run_dir / task_id, 1
    while logs.exists():
        n += 1
        logs = run_dir / f"{task_id}-run{n}"
    logs.mkdir(parents=True)
    return logs


def run_task(s: Session, task: Task) -> TaskRecord:
    rec = TaskRecord(id=task.id, milestone=task.milestone)
    logs = rec.logs = _logs_dir(s.run_dir, task.id)
    s.log(f"{task.id}: {task.goal}")
    record_ticket(s, task.path, "running")

    problems = preflight(task, s.repo)
    if problems:
        (logs / "preflight.txt").write_text("\n".join(problems), encoding="utf-8")
        rec.result = "preflight"
        _finish_escalation(s, task, rec, "pre-flight failed", logs, "\n".join(problems))
        return rec

    if task.agent == "lead":
        run_lead_task(s, task, rec)
        return rec

    branch = f"task/{task.id}"
    s.git.fresh_branch(branch, MAIN)
    protected = tuple(read_protected(s.repo))
    last: GateResult | None = None
    timeouts: list[bool] = []
    direction = ""
    for attempt in range(1, s.cfg.max_attempts + 1):
        rec.attempts = attempt
        if (
            attempt == s.cfg.max_attempts
            and attempt > 1
            and s.state.directions.get(task.id, 0) < s.cfg.directions_per_task
            and needs_direction(rec.gate_failures, timeouts)
        ):
            task, direction = give_direction(s, task, rec, logs)
        if attempt >= 3:
            s.git.fresh_branch(branch, MAIN)
        rec.warmup_s += warmup(s.cfg.lm_base_url, s.cfg.lm_model, s.cfg.warmup_timeout)
        _check_context(s)
        log = logs / f"opencode-{attempt}.jsonl"
        job_id = record_start(
            s,
            task.id,
            task.milestone,
            "last-attempt" if direction else "developer",
            local_agent(s.cfg),
            attempt=next_number(s, task.id, "local"),
            log_path=_rel(s, log),
            context_limit=s.context_limit,
        )
        run = run_opencode(
            s.repo,
            s.cfg.opencode_model,
            f"{task.id} attempt {attempt}",
            _prompt(task, attempt, last, bool(timeouts and timeouts[-1]), direction),
            s.cfg.opencode_timeout,
            log,
            on_progress=partial(live_update, s, job_id),
        )
        rec.model_s += run.duration_s
        rec.tokens_in += run.tokens.input
        rec.tokens_out += run.tokens.output + run.tokens.reasoning
        rec.steps += run.tokens.steps
        rec.sessions.append(run.facts.session_id)
        rec.edit_streak = max(rec.edit_streak, run.facts.edit_streak)
        rec.timeouts += run.timed_out
        timeouts.append(run.timed_out)

        blocked_text = _read_blocked(s.repo)
        if blocked_text is not None:
            (logs / f"BLOCKED-{attempt}.md").write_text(blocked_text, encoding="utf-8")
            category = parse_blocked(blocked_text) or "invalid"
            if category == "unrelated-problem":
                s.report.notes.append(f"{task.id} reported an unrelated problem (see logs).")
            else:
                _finish_attempt(s, job_id, run, "failed", note=f"BLOCKED: {category}")
                rec.blocked = category
                rec.result = "blocked"
                local_wip_commit(s, f"wip {task.id} attempt {attempt} (blocked)")
                _finish_escalation(s, task, rec, f"BLOCKED: {category}", logs, blocked_text)
                return rec

        local_wip_commit(s, f"wip {task.id} attempt {attempt}")
        started = time.monotonic()
        if s.git.changed_files(MAIN):
            context = GateContext(s.repo, s.git, task, MAIN, protected, s.cfg.gate_timeout)
            results = run_gates(context)
        else:
            # An untouched tree passes every gate, and there'd be nothing to merge (m4-06).
            cause = empty_cause(run.facts, run.timed_out)
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
        _finish_attempt(
            s,
            job_id,
            run,
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
            _merge(s, task, rec)
            return rec
        if run.timed_out:
            s.report.notes.append(f"{task.id} attempt {attempt}: OpenCode timed out.")
        rec.gate_failures.append(failed.name)
        last = failed
        s.log(f"{task.id}: attempt {attempt} failed gate {failed.name}")

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
    s.git.run("branch", "-D", branch)
    rec.result = "done"
    s.log(f"{task.id}: merged after {rec.attempts} attempt(s)")


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
    s.report.notes.append(f"Blocked {task_path.stem}: {reason}")
    s.log(f"{task_path.stem}: blocked ({reason})")


def run_lead_task(s: Session, task: Task, rec: TaskRecord) -> None:
    """The lead's own ticket, as a headless job on its branch; merged only if check-all
    passes. A lead ticket that fails is blocked: there's no one above the lead but the owner."""
    logs = rec.logs or _logs_dir(s.run_dir, task.id)
    branch = f"task/{task.id}"
    s.git.fresh_branch(branch, MAIN)
    rec.attempts = 1
    job = ClaudeJob(
        kind="lead-ticket",
        prompt=prompts.LEAD_TICKET.format(
            id=task.id, task=task.path.relative_to(s.repo).as_posix()
        ),
        allowed_tools=(
            *EDIT_TOOLS,
            *CHECK_TOOLS,
            *GIT_READ_TOOLS,
            *(f"Bash({command}:*)" for command in task.commands),
        ),
    )
    call_claude(s, job, task.milestone, task.id, ticket=task.id)
    if not s.git.commit_all(with_trailers(f"wip {task.id} (lead)", agent=CLAUDE_HEADLESS_AGENT)):
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
    record_ticket(s, target, merged_by=claude_agent(s, job), commit=rec.commit)
    s.git.run("branch", "-D", branch)
    rec.result = "done"
    s.log(f"{task.id}: merged (lead ticket)")


# --- checkpoints (ADR 12 item 8) ------------------------------------------------------


def note_merge(s: Session, task: Task, rec: TaskRecord) -> None:
    """Count a developer merge; every ``checkpoint_every`` of them, run a checkpoint."""
    if rec.result != "done" or task.agent != "developer":
        return
    s.state.unchecked.append(f"{task.id} {rec.commit}")
    save_state(s.state, s.state_path)
    if len(s.state.unchecked) >= s.cfg.checkpoint_every:
        checkpoint(s, task.milestone)


def checkpoint(s: Session, milestone: str) -> None:
    merged = list(s.state.unchecked)
    out = s.run_dir / f"checkpoint-{len(s.report.claude_runs) + 1}.md"
    job = ClaudeJob(
        kind="checkpoint",
        prompt=prompts.CHECKPOINT.format(
            merges="\n".join(f"- {m.split()[0]}: `git show {m.split()[1]}`" for m in merged),
            out=out.relative_to(s.repo).as_posix(),
        ),
        allowed_tools=(
            *READ_TOOLS,
            *GIT_READ_TOOLS,
            "Bash(uv run pytest:*)",  # the tickets' pre-flight test; its commit skips the hook
            "Edit(tasks/ready/**)",
            "Edit(docs/agents/developer.md)",
            "Edit(var/runs/**)",
        ),
        model=s.cfg.checkpoint_model,
    )
    call_claude(s, job, milestone, "checkpoint")
    s.state.unchecked = []
    save_state(s.state, s.state_path)
    if out.is_file():
        s.report.notes.append("Checkpoint: " + out.read_text(encoding="utf-8").strip())
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
    rec_sessions = [p for p in sorted(logs.glob("thinking-*.md"))]
    job = ClaudeJob(
        kind="escalation",
        prompt=prompts.ESCALATION.format(
            id=task.id,
            reason=reason,
            logs=logs.relative_to(s.repo).as_posix(),
            thinking=", ".join(p.relative_to(s.repo).as_posix() for p in rec_sessions)
            or "not available",
        ),
        allowed_tools=(*EDIT_TOOLS, *CHECK_TOOLS, *GIT_READ_TOOLS),
    )
    call_claude(s, job, task.milestone, task.id, ticket=task.id)
    decision_path = logs / "decision.json"
    try:
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        decision = {}
    outcome = decision.get("outcome")
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
        record_ticket(s, done, merged_by=claude_agent(s, job), commit=s.git.head())
    elif outcome == "requeue" and (s.tasks_dir("ready") / task.path.name).is_file():
        record_ticket(s, s.tasks_dir("ready") / task.path.name)


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
        task = pick_next(ready, done, paused)
        if task is None:
            if paused:
                s.report.notes.append("Paused (dependency escalated): " + ", ".join(sorted(paused)))
            return False
        rec = run_task(s, task)
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
        s.log("Nothing to do.")
        return s.report
    claude = claude_tokens(transcripts_dir(s.repo), s.report.started, s.report.ended)
    path = report_mod.write(s.repo, s.report, claude)
    if s.cfg.narrative and s.report.tasks:
        milestone = s.report.tasks[0].milestone
        job = ClaudeJob(
            kind="narrative",
            prompt=prompts.NARRATIVE.format(report=path.relative_to(s.repo).as_posix()),
            allowed_tools=EDIT_TOOLS,
        )
        call_claude(s, job, milestone, "session")
    merged = sum(t.result == "done" for t in s.report.tasks)
    _finish_run(s, f"{merged} merged, {len(s.report.tasks) - merged} not")
    runner_commit(s, messages.session_message(s.report, path.relative_to(s.repo).as_posix()))
    s.log(f"Session report: {path.relative_to(s.repo)}")
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
    proc = subprocess.run(
        ["uv", "run", "pytest", "-q", "-m", "e2e", *browsers, "tests/e2e"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return GateResult("e2e", proc.returncode == 0, (proc.stdout + proc.stderr)[-4000:])
