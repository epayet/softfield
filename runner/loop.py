"""The per-task loop and the session around it (docs/workflow.md)."""

import json
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from runner import prompts
from runner.claude import (
    CHECK_TOOLS,
    EDIT_TOOLS,
    GIT_READ_TOOLS,
    ClaudeJob,
    ClaudeResult,
    UsageLimited,
    backoff_seconds,
    run_claude,
)
from runner.config import Config, read_protected
from runner.gates import BLOCKED_FILE, GateContext, GateResult, parse_blocked, run_gates
from runner.gitops import (
    LOCAL_MODEL_AGENT,
    LOCAL_MODEL_AUTHOR,
    RUNNER_AUTHOR,
    Git,
    with_trailers,
)
from runner.local_model import (
    loaded_context_length,
    run_opencode,
    warmup,
)
from runner.report import ClaudeRunRecord, SessionReport, TaskRecord
from runner.state import State, load_state, save_state
from runner.tasks import (
    Task,
    append_footer,
    blocked_ids,
    load_dir,
    pick_next,
    preflight,
    task_ids,
)

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


def open_session(cfg: Config) -> Session:
    git = Git(cfg.repo)
    if git.current_branch() != MAIN or not git.is_clean():
        raise RunnerError("start the runner on a clean main branch")
    started = now()
    run_dir = cfg.runs_dir / f"{started:%Y%m%d-%H%M%S}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return Session(
        cfg=cfg,
        git=git,
        state=load_state(cfg.runs_dir / "state.json"),
        report=SessionReport(started=started),
        run_dir=run_dir,
    )


# --- headless Claude, with usage-limit pauses and the milestone cap -------------------


def call_claude(s: Session, job: ClaudeJob, milestone: int, subject: str) -> ClaudeResult | None:
    """Run a headless Claude job, or return None if the milestone's cap is used up."""
    if s.state.runs_used(milestone) >= s.cfg.headless_runs_per_milestone:
        s.report.notes.append(
            f"Skipped a {job.kind} run for {subject}: headless cap"
            f" ({s.cfg.headless_runs_per_milestone}) reached for milestone {milestone}."
        )
        return None
    attempt = 0
    while True:
        try:
            result = run_claude(
                job,
                s.repo,
                s.cfg.claude_timeout,
                s.run_dir / f"claude-{job.kind}-{subject}.log",
                now(),
            )
            break
        except UsageLimited as limit:
            wait = (
                max(60.0, (limit.resets_at - now()).total_seconds() + 60)
                if limit.resets_at
                else backoff_seconds(attempt, s.cfg.backoff_min, s.cfg.backoff_max)
            )
            attempt += 1
            s.state.paused_until = (
                datetime.fromtimestamp(now().timestamp() + wait).astimezone().isoformat()
            )
            save_state(s.state, s.state_path)
            s.log(f"Claude usage limit reached; pausing {wait / 60:.0f} min, then resuming.")
            s.report.notes.append(f"Paused {wait / 60:.0f} min for a Claude usage limit.")
            time.sleep(wait)
    s.state.paused_until = None
    s.state.count_run(milestone)
    save_state(s.state, s.state_path)
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
    loaded = loaded_context_length(s.cfg.lm_base_url, s.cfg.lm_model)
    if loaded:
        s.report.notes.append(f"LM Studio loaded the model with {loaded:,} tokens of context.")


def _read_blocked(repo: Path) -> str | None:
    path = repo / BLOCKED_FILE
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    path.unlink()
    return text


def _prompt(task: Task, attempt: int, last: GateResult | None) -> str:
    if last is None:
        return prompts.local_prompt(task)
    template = prompts.RETRY if attempt == 2 else prompts.FRESH
    return prompts.local_prompt(task, template.format(gate=last.name, output=last.output))


def _finish_escalation(s: Session, task: Task, rec: TaskRecord, reason: str, logs: Path) -> None:
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
            "logs": logs.relative_to(s.repo).as_posix(),
        },
    )
    runner_commit(s, f"runner: escalate {task.id} ({reason})")
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

    problems = preflight(task, s.repo)
    if problems:
        (logs / "preflight.txt").write_text("\n".join(problems), encoding="utf-8")
        rec.result = "preflight"
        _finish_escalation(s, task, rec, "pre-flight failed", logs)
        return rec

    branch = f"task/{task.id}"
    s.git.fresh_branch(branch, MAIN)
    protected = tuple(read_protected(s.repo))
    last: GateResult | None = None
    for attempt in range(1, s.cfg.max_attempts + 1):
        rec.attempts = attempt
        if attempt >= 3:
            s.git.fresh_branch(branch, MAIN)
        rec.warmup_s += warmup(s.cfg.lm_base_url, s.cfg.lm_model, s.cfg.warmup_timeout)
        _check_context(s)
        run = run_opencode(
            s.repo,
            s.cfg.opencode_model,
            f"{task.id} attempt {attempt}",
            _prompt(task, attempt, last),
            s.cfg.opencode_timeout,
            logs / f"opencode-{attempt}.jsonl",
        )
        rec.model_s += run.duration_s
        rec.tokens_in += run.tokens.input
        rec.tokens_out += run.tokens.output + run.tokens.reasoning
        rec.steps += run.tokens.steps

        blocked_text = _read_blocked(s.repo)
        if blocked_text is not None:
            (logs / f"BLOCKED-{attempt}.md").write_text(blocked_text, encoding="utf-8")
            category = parse_blocked(blocked_text) or "invalid"
            if category == "unrelated-problem":
                s.report.notes.append(f"{task.id} reported an unrelated problem (see logs).")
            else:
                rec.blocked = category
                rec.result = "blocked"
                local_wip_commit(s, f"wip {task.id} attempt {attempt} (blocked)")
                _finish_escalation(s, task, rec, f"BLOCKED: {category}", logs)
                return rec

        local_wip_commit(s, f"wip {task.id} attempt {attempt}")
        started = time.monotonic()
        results = run_gates(GateContext(s.repo, s.git, task, MAIN, protected, s.cfg.gate_timeout))
        rec.gates_s += time.monotonic() - started
        (logs / f"gates-{attempt}.txt").write_text(
            "\n\n".join(f"## {r.name}: {'ok' if r.ok else 'FAIL'}\n{r.output}" for r in results),
            encoding="utf-8",
        )
        failed = next((r for r in results if not r.ok), None)
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
        s, task, rec, f"gates failed {rec.attempts}x (last: {last.name if last else '?'})", logs
    )
    return rec


def _merge(s: Session, task: Task, rec: TaskRecord) -> None:
    branch = f"task/{task.id}"
    rec.commit = s.git.squash_merge(
        branch,
        MAIN,
        with_trailers(
            f"{task.id}: {task.goal}\n\nImplemented by the local model ({s.cfg.lm_model}) via"
            f" the runner in {rec.attempts} attempt(s).",
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
        },
    )
    runner_commit(s, f"runner: {task.id} done")
    s.git.run("branch", "-D", branch)
    rec.result = "done"
    s.log(f"{task.id}: merged after {rec.attempts} attempt(s)")


# --- escalation handling ------------------------------------------------------------


def handle_escalation(s: Session, task: Task, logs: Path, reason: str) -> None:
    job = ClaudeJob(
        kind="escalation",
        prompt=prompts.ESCALATION.format(
            id=task.id, reason=reason, logs=logs.relative_to(s.repo).as_posix()
        ),
        allowed_tools=(*EDIT_TOOLS, *CHECK_TOOLS, *GIT_READ_TOOLS),
    )
    result = call_claude(s, job, task.milestone, task.id)
    if result is None:
        return
    decision_path = logs / "decision.json"
    try:
        outcome = json.loads(decision_path.read_text(encoding="utf-8")).get("outcome")
    except (OSError, json.JSONDecodeError):
        outcome = None
    escalated = s.tasks_dir("escalated") / task.path.name
    if outcome == "requeue":
        s.git.run("rm", "-q", str(escalated.relative_to(s.repo)))
    elif outcome == "implemented":
        s.git.move(escalated, s.tasks_dir("done") / task.path.name)
    notes = logs / "escalation.md"
    if notes.is_file():
        s.report.notes.append(f"Escalation {task.id} ({outcome}): " + notes.read_text().strip())
    s.git.commit_all(
        with_trailers(
            f"escalation {task.id}: {outcome or 'no decision'} (by Claude)",
            agent=CLAUDE_HEADLESS_AGENT,
        )
    )


# --- the session ------------------------------------------------------------------


def run_session(cfg: Config, *, once: bool, dry_run: bool, escalate: bool) -> SessionReport | None:
    s = open_session(cfg)
    while True:
        ready = load_dir(s.tasks_dir("ready"), cfg.default_max_diff)
        done = task_ids(s.tasks_dir("done"))
        escalated = task_ids(s.tasks_dir("escalated"))
        paused = blocked_ids(ready, escalated)
        task = pick_next(ready, done, paused)
        if dry_run:
            _print_plan(ready, done, paused, task)
            return None
        if task is None:
            if paused:
                s.report.notes.append("Paused (dependency escalated): " + ", ".join(sorted(paused)))
            break
        rec = run_task(s, task)
        s.report.tasks.append(rec)
        if rec.result != "done" and escalate:
            reason = rec.note or rec.result
            handle_escalation(s, task, rec.logs or s.run_dir / task.id, reason)
        if once:
            break
    return close_session(s)


def close_session(s: Session) -> SessionReport:
    from runner import report as report_mod

    s.report.ended = now()
    if not s.report.tasks and not s.report.claude_runs:
        s.log("Nothing to do.")
        return s.report
    path = report_mod.write(s.repo, s.report, s.cfg.prices)
    if s.cfg.narrative and s.report.tasks:
        milestone = s.report.tasks[0].milestone
        job = ClaudeJob(
            kind="narrative",
            prompt=prompts.NARRATIVE.format(report=path.relative_to(s.repo).as_posix()),
            allowed_tools=EDIT_TOOLS,
        )
        call_claude(s, job, milestone, "session")
    runner_commit(s, f"runner: session report {path.stem}")
    s.log(f"Session report: {path.relative_to(s.repo)}")
    return s.report


def _print_plan(ready: list[Task], done: set[str], paused: set[str], nxt: Task | None) -> None:
    print(f"ready: {len(ready)}  done: {len(done)}  paused: {len(paused)}")
    for task in sorted(ready, key=lambda t: (t.milestone, t.id)):
        waiting = [d for d in task.depends_on if d not in done]
        status = (
            "paused"
            if task.id in paused
            else ("waiting on " + ", ".join(waiting) if waiting else "runnable")
        )
        marker = "->" if nxt and task.id == nxt.id else "  "
        print(f"{marker} {task.id}: {status}")
    print(f"next: {nxt.id if nxt else 'nothing'}")


def run_e2e(repo: Path, timeout: int) -> GateResult:
    proc = subprocess.run(
        ["uv", "run", "pytest", "-q", "-m", "e2e", "tests/e2e"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return GateResult("e2e", proc.returncode == 0, (proc.stdout + proc.stderr)[-4000:])
