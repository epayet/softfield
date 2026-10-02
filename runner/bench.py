"""`runner bench`: replay finished tickets for chosen agents, in identical conditions (ADR 14
item 8).

Each ticket × agent gets a throwaway copy of the repo under `[bench] dir`, detached at the
parent of the ticket's merge, with today's workflow files overlaid and the ticket back in
`tasks/ready/`. The agent gets the usual attempts and gates there, as jobs of role `bench`;
no Claude, so a failed last attempt is recorded as "would escalate". Nothing reaches main,
`tasks/` or a branch. The first refusal stops the bench. The logs stay in `var/bench/`.

The copy is a clone with its own `.git`, never a `git worktree`: OpenCode takes its project
from the git common dir, so in a worktree it edited the main checkout (f2-12).
"""

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from functools import partial
from pathlib import Path

from runner import console, metrics, prompts
from runner.agents import (
    CHECK_COMMANDS,
    GIT_READ_COMMANDS,
    Agent,
    JobResult,
    JobSpec,
    adapter_for,
)
from runner.config import Config, read_protected
from runner.gates import NO_CHANGES, GateContext, GateResult, parse_blocked, run_gates
from runner.gitops import RUNNER_AUTHOR, Git, with_trailers
from runner.local_model import empty_cause, is_local, warmup
from runner.loop import (
    MAIN,
    RUNNER_AGENT,
    RunnerError,
    Session,
    _attempt_end,
    _finish_attempt,
    _finish_run,
    _log_running,
    _metrics_failed,
    _prompt,
    _read_blocked,
    _record,
    _record_refusal,
    _start_heartbeat,
    next_number,
    now,
    record_start,
    with_progress,
)
from runner.report import SessionReport
from runner.state import load_state
from runner.tasks import _FOOTER_BLOCK_RE, Task, parse_task

ROLE = "bench"
# Today's workflow, laid over the old tree so every agent works to the same rules.
OVERLAY = ("AGENTS.md", "docs/agents", "opencode.json", "workflow")
WOULD_ESCALATE = "would escalate"


@dataclass(frozen=True)
class BenchResult:
    ticket: str
    agent: str
    outcome: str  # "passed", "would escalate" or "refused"
    attempts: int
    note: str = ""  # a refusal's reset


@dataclass
class BenchReport:
    results: list[BenchResult] = field(default_factory=list)
    stopped: str | None = None  # why the bench stopped early: the refusal and its reset


def bench_dir(cfg: Config) -> Path:
    return cfg.repo / "var" / "bench"


def merge_commit(git: Git, ticket: str) -> str:
    """The ticket's merge on main: the latest commit with its ``Task:`` trailer."""
    found = git.run("log", "-1", "--format=%H", f"--grep=^Task: {ticket}$", MAIN).strip()
    if not found:
        raise RunnerError(f"no merge of {ticket} on {MAIN} (a commit with `Task: {ticket}`)")
    return found


def _ticket_text(cfg: Config, ticket: str) -> str:
    path = cfg.repo / "tasks" / "done" / f"{ticket}.md"
    if not path.is_file():
        raise RunnerError(f"{ticket} isn't a finished ticket (no tasks/done/{ticket}.md)")
    return _FOOTER_BLOCK_RE.sub("\n", path.read_text(encoding="utf-8")).rstrip("\n") + "\n"


def _overlay(repo: Path, work: Path) -> None:
    for rel in OVERLAY:
        source, target = repo / rel, work / rel
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink(missing_ok=True)
        if source.is_dir():
            shutil.copytree(source, target)
        elif source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def _check_outside_repo(cfg: Config) -> None:
    copies = cfg.bench_copies.resolve()
    if copies.is_relative_to(cfg.repo.resolve()):
        raise RunnerError(f"[bench] dir must be outside the repo: {copies} is inside it")


def make_copy(cfg: Config, work: Path, parent: str, ticket: str, text: str) -> str:
    """A clone detached at ``parent``, with today's workflow and the ticket in ready/,
    committed so the gates see only the agent's changes. Returns that base commit."""
    work.parent.mkdir(parents=True, exist_ok=True)
    Git(work.parent).run("clone", "-q", "--local", "--no-checkout", str(cfg.repo), str(work))
    git = Git(work)
    git.run("remote", "remove", "origin")  # nothing in the copy leads back to the repo
    for key in ("user.name", "user.email"):  # commit as the repo does, global or local
        if value := Git(cfg.repo).run("config", key, check=False).strip():
            git.run("config", key, value)
    git.run("checkout", "-q", "--detach", parent)
    _overlay(cfg.repo, work)
    ready = work / "tasks" / "ready" / f"{ticket}.md"
    ready.parent.mkdir(parents=True, exist_ok=True)
    ready.write_text(text, encoding="utf-8")
    git.run("add", "-A")
    message = with_trailers(f"bench: {ticket} from {parent[:9]}", agent=RUNNER_AGENT)
    git.run(
        "commit", "-q", "--no-verify", "--allow-empty", "-m", message, "--author", RUNNER_AUTHOR
    )
    return git.head()


def remove_copy(work: Path) -> None:
    shutil.rmtree(work, ignore_errors=True)


def _open(cfg: Config) -> Session:
    """A session recorded as a `bench` run; its logs in `var/bench/`. state.json is only read."""
    started = now()
    run_dir = bench_dir(cfg) / f"bench-{started:%Y%m%d-%H%M%S}"
    run_dir.mkdir(parents=True, exist_ok=True)
    s = Session(
        cfg=cfg,
        git=Git(cfg.repo),
        state=load_state(cfg.runs_dir / "state.json"),
        report=SessionReport(started=started),
        run_dir=run_dir,
    )
    # Not `loop._start_run`: a bench may run beside the runner, so it closes none of its jobs
    # and leaves the tickets' rows alone.
    try:
        s.db = metrics.open_db(cfg.metrics_db)
    except Exception as exc:
        _metrics_failed(s, exc)
        return s
    s.project_id = _record(s, metrics.upsert_project, cfg.repo.name, repo=str(cfg.repo))
    if s.project_id is not None:
        at = started.isoformat()
        s.run_id = _record(
            s,
            metrics.upsert_run,
            s.project_id,
            run_dir.name,
            command=ROLE,
            started=at,
            heartbeat=at,
        )
    if s.run_id is not None:
        _start_heartbeat(s, s.run_id)
    return s


def _resets(at: datetime | None) -> str:
    if at is None:
        return "its reset is unknown"
    local = at.astimezone()
    return f"it resets {local:%a} {local.day} {local:%b %H:%M}"


def _attempt(
    s: Session, agent: Agent, task: Task, work: Path, prompt: str, attempt: int, logs: Path
) -> tuple[JobResult, int | None]:
    what = f"bench {task.id} attempt {attempt}/{s.cfg.max_attempts}"
    if is_local(agent):
        warmup(s.cfg.lm_base_url, s.cfg.lm_model, s.cfg.warmup_timeout)
    opencode = agent.harness == "opencode"
    log = logs / (f"{agent.harness}-{attempt}" + (".jsonl" if opencode else ".log"))
    s.log(console.start(agent.id, what))
    job_id = record_start(
        s,
        task.id,
        task.milestone,
        ROLE,
        agent.id,
        attempt=next_number(s, task.id, ROLE),  # across agents: the job's key has no agent
        log_path=log.relative_to(s.repo).as_posix(),
        routing_reason=f"benched with --agents (attempt {attempt} of {s.cfg.max_attempts})",
    )
    spec = JobSpec(
        ROLE,
        prompt,
        s.cfg.opencode_timeout if opencode else s.cfg.claude_timeout,
        edit=("**",),
        commands=CHECK_COMMANDS if opencode else (*CHECK_COMMANDS, *GIT_READ_COMMANDS),
        title=f"bench {task.id} attempt {attempt}",
    )
    run = with_progress(
        partial(adapter_for(agent.harness).run, agent, spec, work, log, now()),
        partial(_log_running, s, agent.id, what),
    )
    return run, job_id


def bench_one(s: Session, agent: Agent, ticket: str, parent: str, text: str) -> BenchResult:
    """One agent on one ticket, in its own copy, removed afterwards."""
    work = s.cfg.bench_copies / f"{s.run_dir.name}-{ticket}-{agent.id}"
    logs = s.run_dir / f"{ticket}-{agent.id}"
    logs.mkdir(parents=True, exist_ok=True)
    try:
        base = make_copy(s.cfg, work, parent, ticket, text)
        return _attempts(s, agent, work, base, logs, ticket)
    finally:
        remove_copy(work)


def _attempts(
    s: Session, agent: Agent, work: Path, base: str, logs: Path, ticket: str
) -> BenchResult:
    git = Git(work)
    task = parse_task(work / "tasks" / "ready" / f"{ticket}.md", s.cfg.default_max_diff)
    protected = tuple(read_protected(work))
    last: GateResult | None = None
    timed_out = False
    for attempt in range(1, s.cfg.max_attempts + 1):
        prompt = _prompt(task, last, timed_out=timed_out)
        run, job_id = _attempt(s, agent, task, work, prompt, attempt, logs)
        what = f"bench {ticket} attempt {attempt}/{s.cfg.max_attempts}"
        if run.refusal is not None:
            _record_refusal(s, agent.id, run, f"a bench of {ticket}")
            _attempt_end(s, agent.id, what, run, "refused")
            resets = _resets(run.refusal.resets_at)
            _finish_attempt(s, job_id, run, "refused", note=resets)
            return BenchResult(ticket, agent.id, "refused", attempt, resets)
        timed_out = run.timed_out
        final = attempt == s.cfg.max_attempts
        blocked = _read_blocked(work)
        if blocked is not None:
            (logs / f"BLOCKED-{attempt}.md").write_text(blocked, encoding="utf-8")
            note = f"BLOCKED: {parse_blocked(blocked) or 'invalid'}; {WOULD_ESCALATE}"
            _attempt_end(s, agent.id, what, run, note)
            _finish_attempt(s, job_id, run, "failed", note=note)
            return BenchResult(ticket, agent.id, WOULD_ESCALATE, attempt)
        git.commit_all(with_trailers(f"bench {ticket} attempt {attempt}", agent=agent.id))
        if git.changed_files(base):
            results = run_gates(GateContext(work, git, task, base, protected, s.cfg.gate_timeout))
        else:
            cause = empty_cause(run.refused_commands, run.timed_out)
            output = "The attempt changed no file. " + prompts.EMPTY[cause]
            results = [GateResult(NO_CHANGES, False, output)]
        gates_log = logs / f"gates-{attempt}.txt"
        gates_log.write_text(
            "\n\n".join(f"## {r.name}: {'ok' if r.ok else 'FAIL'}\n{r.output}" for r in results),
            encoding="utf-8",
        )
        last = next((r for r in results if not r.ok), None)
        rel = gates_log.relative_to(s.repo).as_posix()
        gates = [
            {"name": r.name, "ok": r.ok, "seconds": round(r.seconds, 1), "log": rel}
            for r in results
        ]
        outcome = "passed" if last is None else "timeout" if run.timed_out else "failed"
        escalates = WOULD_ESCALATE if last is not None and final else None
        _finish_attempt(s, job_id, run, outcome, gates=gates, note=escalates)
        if last is None:
            _attempt_end(s, agent.id, what, run, "passed")
            return BenchResult(ticket, agent.id, "passed", attempt)
        _attempt_end(s, agent.id, what, run, f"failed gate {last.name}")
    return BenchResult(ticket, agent.id, WOULD_ESCALATE, s.cfg.max_attempts)


def run_bench(cfg: Config, tickets: list[str], agent_ids: list[str]) -> BenchReport:
    """Each ticket for each agent, in order, until done or the first refusal."""
    if unknown := [a for a in agent_ids if a not in cfg.agents]:
        raise RunnerError(f"no such agent in workflow/runner.toml: {', '.join(unknown)}")
    _check_outside_repo(cfg)
    git = Git(cfg.repo)
    plan = [(t, merge_commit(git, t) + "^", _ticket_text(cfg, t)) for t in tickets]
    parents = [(t, git.run("rev-parse", parent).strip(), text) for t, parent, text in plan]
    git.run("worktree", "prune", check=False)  # leftovers of benches that used worktrees
    s = _open(cfg)
    report = BenchReport()
    try:
        for ticket, parent, text in parents:
            for agent_id in agent_ids:
                result = bench_one(s, cfg.agents[agent_id], ticket, parent, text)
                report.results.append(result)
                mark = "✔" if result.outcome == "passed" else "✖"
                s.log(f"{mark} [{agent_id}] {ticket}: {result.outcome} · attempt {result.attempts}")
                if result.outcome == "refused":
                    report.stopped = (
                        f"{agent_id} refused attempt {result.attempts} of {ticket}"
                        f" ({result.note}): the bench stops here"
                    )
                    s.log(f"⏸ [{agent_id}] {report.stopped}")
                    return report
    finally:
        verdict = report.stopped or f"{len(report.results)} benched"
        _finish_run(s, verdict)
    return report
