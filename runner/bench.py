"""`runner bench`: replay finished tickets for chosen agents, in identical conditions (ADR 14
item 8).

Each ticket × agent gets a throwaway copy of the repo under `[bench] dir`, detached at the
parent of the ticket's merge, with today's workflow files overlaid and the ticket back in
`tasks/ready/`. The agent gets the usual attempts and gates there, as jobs of role `bench`;
no Claude, so a failed last attempt is recorded as "would escalate". Nothing reaches main,
`tasks/` or a branch. The first refusal stops the bench. The logs stay in `var/bench/`.

The copy is a clone with its own `.git`, never a `git worktree`: OpenCode takes its project
from the git common dir, so in a worktree it edited the main checkout (f2-12). Nor does the
copy keep the repo's history: OpenCode also keys a project by its root commit and keeps one
directory per project, so a plain clone was given the main checkout too (f4-19). The copy's
history is a new root commit holding the tree at the parent, then the base commit the gates
diff against.

`runner bench --review` replays past checkpoints instead (ADR 16 item 10): each checkpoint ×
agent reviews the checkpoint's merges, read-only, in a copy at the last of them. Its findings
are scored against the known ones (the checkpoint's, and later ones on the same tickets that
the review didn't reject); a finding nobody knew is listed for the lead, not scored. The score
is the `bench` job's note (`factory_dashboard.queries.review_note`), which the Agents page's
eligibility reads.
"""

import json
import shutil
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime
from functools import partial
from pathlib import Path

from factory_dashboard.queries import connect, review_note
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
    _answer_json,
    _attempt_end,
    _finish_attempt,
    _finish_run,
    _log_running,
    _merge_files,
    _metrics_failed,
    _prompt,
    _read_blocked,
    _record,
    _record_readings,
    _record_refusal,
    _start_heartbeat,
    next_number,
    now,
    record_start,
    with_progress,
)
from runner.report import SessionReport
from runner.review import Finding, ReviewFileError, parse_checkpoint
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


def merge_commit(git: Git, ticket: str, recorded: str | None = None) -> str:
    """The ticket's merge on main: the latest commit with its ``Task:`` trailer, else the
    commit its metrics row ``recorded`` (an escalation that implemented it has no trailer,
    f4-24)."""
    found = git.run("log", "-1", "--format=%H", f"--grep=^Task: {ticket}$", MAIN).strip()
    if not found and recorded:
        found = git.run(
            "rev-parse", "--verify", "--quiet", f"{recorded}^{{commit}}", check=False
        ).strip()
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


def _clone(cfg: Config, work: Path, at: str, tickets: dict[str, str], message: str) -> str:
    """A clone holding ``at``'s tree under a root commit of its own, with today's workflow and
    ``tickets`` (path: text) written, committed so the gates see only the agent's changes.
    Returns that base commit."""
    work.parent.mkdir(parents=True, exist_ok=True)
    Git(work.parent).run("clone", "-q", "--local", "--no-checkout", str(cfg.repo), str(work))
    git = Git(work)
    git.run("remote", "remove", "origin")  # nothing in the copy leads back to the repo
    for key in ("user.name", "user.email"):  # commit as the repo does, global or local
        if value := Git(cfg.repo).run("config", key, check=False).strip():
            git.run("config", key, value)
    git.run("checkout", "-q", "--detach", at)
    # A new root holding `at`'s tree, and no ref left to the repo's history: OpenCode keys a
    # project by its root commit, and gave a copy sharing the repo's the main checkout (f4-19).
    # The copy's name makes the root its own, even beside a copy of the same `at`.
    title = f"bench: {work.name}, the tree of {at[:9]}"
    root = git.run("commit-tree", "-m", title, f"{at}^{{tree}}")
    git.run("checkout", "-q", "--detach", root.strip())
    for ref in git.run("for-each-ref", "--format=%(refname)").split():
        git.run("update-ref", "-d", ref)
    _overlay(cfg.repo, work)
    for rel, text in tickets.items():
        (work / rel).parent.mkdir(parents=True, exist_ok=True)
        (work / rel).write_text(text, encoding="utf-8")
    git.run("add", "-A")
    message = with_trailers(message, agent=RUNNER_AGENT)
    git.run(
        "commit", "-q", "--no-verify", "--allow-empty", "-m", message, "--author", RUNNER_AUTHOR
    )
    return git.head()


def make_copy(cfg: Config, work: Path, parent: str, ticket: str, text: str) -> str:
    """A clone of ``parent``'s tree, with today's workflow and the ticket in ready/.
    Returns its base commit."""
    ready = {f"tasks/ready/{ticket}.md": text}
    return _clone(cfg, work, parent, ready, f"bench: {ticket} from {parent[:9]}")


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


# --- review replays (ADR 16 item 10) --------------------------------------------------------

NEAR = 5  # lines apart that still count as the same place
KNOWN_ROLES = ("checkpoint", "review")  # whose findings on the reviewed tickets are known
NOTE_MAX = 300  # chars of a failed replay's answer kept on its job


@dataclass(frozen=True)
class Known:
    """A finding already known on a checkpoint's merges (a row of ``findings``)."""

    key: str
    severity: str
    file: str
    line: int | None
    summary: str


@dataclass(frozen=True)
class ReviewScore:
    hits: tuple[str, ...]  # the known findings' keys the agent reported too
    misses: tuple[str, ...]  # those it didn't
    missed_blocking: int  # of the misses, the blocking ones (ADR 14 item 12's bar)
    unscored: tuple[Finding, ...]  # what it found that nobody knew: for the lead to judge

    @property
    def note(self) -> str:
        return review_note(
            len(self.hits), len(self.misses), self.missed_blocking, len(self.unscored)
        )


@dataclass(frozen=True)
class Checkpoint:
    job: int  # its job row
    milestone: str
    agent: str  # who did it
    merges: tuple[str, ...]  # "ticket sha", as the runner's unchecked list has them
    known: tuple[Known, ...]


@dataclass(frozen=True)
class ReviewResult:
    checkpoint: int
    milestone: str
    agent: str
    outcome: str  # "passed", "failed" or "refused"
    score: ReviewScore | None = None
    note: str = ""  # a refusal's reset, or why it failed


@dataclass
class ReviewReport:
    reviews: list[ReviewResult] = field(default_factory=list)
    stopped: str | None = None


def _words(text: str) -> str:
    return " ".join(text.split()).casefold()


def matches(known: Known, found: Finding) -> bool:
    """The same finding: the same summary, or the same file at lines at most ``NEAR`` apart
    (either without a line: the file is enough)."""
    if known.summary and _words(known.summary) == _words(found.summary):
        return True
    if not known.file or known.file != found.file:
        return False
    return known.line is None or found.line is None or abs(known.line - found.line) <= NEAR


def score(known: tuple[Known, ...], found: tuple[Finding, ...]) -> ReviewScore:
    """Each known finding is a hit if one of ``found`` matches it (each used once), else a
    miss; what is left of ``found`` is unscored."""
    left = list(found)
    hits, misses, blocking = [], [], 0
    for k in known:
        match = next((f for f in left if matches(k, f)), None)
        if match is None:
            misses.append(k.key)
            blocking += k.severity == "blocking"
        else:
            left.remove(match)
            hits.append(k.key)
    return ReviewScore(tuple(hits), tuple(misses), blocking, tuple(left))


def _at(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _known(conn: sqlite3.Connection, job: int, ticket_ids: list[int]) -> tuple[Known, ...]:
    """The checkpoint's findings, and those of checkpoints and reviews (or backfilled ones)
    on its tickets; none the review rejected."""
    marks = ", ".join("?" for _ in ticket_ids)
    rows = conn.execute(
        "SELECT f.key, f.severity, f.file, f.line, f.summary FROM findings f"  # noqa: S608
        " LEFT JOIN jobs j ON j.id = f.job_id WHERE (f.job_id = ? OR (f.ticket_id IN"
        f" ({marks}) AND (f.job_id IS NULL OR j.role IN (?, ?))))"
        " AND ifnull(f.verdict, '') != 'rejected' ORDER BY f.id",
        (job, *ticket_ids, *KNOWN_ROLES),
    ).fetchall()
    return tuple(
        Known(r["key"], r["severity"] or "", r["file"] or "", r["line"], r["summary"] or "")
        for r in rows
    )


def checkpoints(
    conn: sqlite3.Connection, git: Git, project: str, milestone: str, agent: str
) -> list[Checkpoint]:
    """The milestone's passed checkpoints that ``agent`` didn't do, oldest first, each with
    the developer merges it reviewed: those whose last job ended after the project's checkpoint
    before it and by its start, plus the tickets its findings name."""
    rows = conn.execute(
        "SELECT j.id, j.agent, j.started, m.key FROM jobs j JOIN runs r ON r.id = j.run_id"
        " JOIN projects p ON p.id = r.project_id JOIN milestones m ON m.id = j.milestone_id"
        " WHERE p.name = ? AND j.role = 'checkpoint' AND j.ticket_id IS NULL"
        " AND j.outcome = 'passed' AND j.started IS NOT NULL",
        (project,),
    ).fetchall()
    ordered = sorted(rows, key=lambda r: (_at(r["started"]), r["id"]))
    merged = conn.execute(
        'SELECT t.id, t.ticket, t."commit", max(coalesce(j.ended, j.started)) AS at'
        " FROM tickets t"
        " JOIN projects p ON p.id = t.project_id JOIN jobs j ON j.ticket_id = t.id"
        " WHERE p.name = ? AND t.kind = 'developer' AND t.\"commit\" IS NOT NULL"
        " AND j.role != ? GROUP BY t.id HAVING at IS NOT NULL",
        (project, ROLE),
    ).fetchall()
    found = []
    for n, row in enumerate(ordered):
        if row["key"] != milestone or row["agent"] == agent:
            continue
        after = _at(ordered[n - 1]["started"]) if n else None
        until = _at(row["started"])
        reviewed = [
            t for t in merged if (after is None or after < _at(t["at"])) and _at(t["at"]) <= until
        ]
        named = conn.execute(
            "SELECT t.id, t.ticket, t.\"commit\", '' AS at FROM findings f"
            " JOIN tickets t ON t.id = f.ticket_id"
            " WHERE f.job_id = ?",
            (row["id"],),
        ).fetchall()
        tickets = {t["id"]: (t["ticket"], t["commit"]) for t in [*reviewed, *named]}
        if not tickets:
            continue
        found.append(
            Checkpoint(
                job=row["id"],
                milestone=milestone,
                agent=row["agent"],
                merges=tuple(f"{t} {merge_commit(git, t, c)}" for t, c in tickets.values()),
                known=_known(conn, row["id"], list(tickets)),
            )
        )
    return found


def _review_copy(cfg: Config, work: Path, cp: Checkpoint) -> None:
    """A clone at the last of the checkpoint's merges, each ticket in done/ as today."""
    shas = [m.split()[1] for m in cp.merges]
    at = Git(cfg.repo).run("merge-base", "--independent", *shas).split()[0]
    done = {f"tasks/done/{m.split()[0]}.md": _ticket_text(cfg, m.split()[0]) for m in cp.merges}
    _clone(cfg, work, at, done, f"bench: checkpoint {cp.job} at {at[:9]}")


def review_one(s: Session, agent: Agent, cp: Checkpoint) -> ReviewResult:
    """One agent replays one checkpoint, read-only, in its own copy, removed afterwards."""
    name = f"checkpoint-{cp.job}-{agent.id}"
    work = s.cfg.bench_copies / f"{s.run_dir.name}-{name}"
    logs = s.run_dir / name
    logs.mkdir(parents=True, exist_ok=True)
    try:
        _review_copy(s.cfg, work, cp)
        return _review(s, agent, cp, work, logs)
    finally:
        remove_copy(work)


def _review(s: Session, agent: Agent, cp: Checkpoint, work: Path, logs: Path) -> ReviewResult:
    opencode = agent.harness == "opencode"
    spec = JobSpec(
        ROLE,
        prompts.CHECKPOINT_SHADOW.format(merges=_merge_files(s, cp.merges)),
        s.cfg.opencode_timeout if opencode else s.cfg.claude_timeout,
        title=f"bench review of checkpoint {cp.job}",
    )
    log = logs / (f"{agent.harness}.jsonl" if opencode else f"{agent.harness}.log")
    what = f"bench review of {cp.milestone} checkpoint {cp.job}"
    s.log(console.start(agent.id, what))
    job_id = record_start(
        s,
        None,
        cp.milestone,
        ROLE,
        agent.id,
        attempt=next_number(s, None, ROLE),
        log_path=log.relative_to(s.repo).as_posix(),
        routing_reason=f"replays checkpoint {cp.job} (by {cp.agent}) with --review --agents",
    )
    run = with_progress(
        partial(adapter_for(agent.harness).run, agent, spec, work, log, now()),
        partial(_log_running, s, agent.id, what),
    )
    _record_readings(s, agent.id, run.readings)
    result = partial(ReviewResult, cp.job, cp.milestone, agent.id)
    if run.refusal is not None:
        _record_refusal(s, agent.id, run, f"a review replay of checkpoint {cp.job}")
        _attempt_end(s, agent.id, what, run, "refused")
        resets = _resets(run.refusal.resets_at)
        _finish_attempt(s, job_id, run, "refused", note=resets)
        return result("refused", note=resets)
    if not run.ok:
        note = run.text[:NOTE_MAX]
        _attempt_end(s, agent.id, what, run, "failed")
        _finish_attempt(s, job_id, run, "failed", note=note)
        return result("failed", note=note)
    answer = logs / "findings.json"
    answer.write_text(_answer_json(run.text), encoding="utf-8")
    try:
        found = parse_checkpoint(answer)
    except ReviewFileError as exc:
        note = f"findings unusable: {exc}"[:NOTE_MAX]
        _attempt_end(s, agent.id, what, run, "failed")
        _finish_attempt(s, job_id, run, "failed", note=note)
        return result("failed", note=note)
    scored = score(cp.known, found)
    new = [asdict(f) for f in scored.unscored]
    (logs / "new-findings.json").write_text(json.dumps(new, indent=2) + "\n", encoding="utf-8")
    _attempt_end(s, agent.id, what, run, scored.note)
    _finish_attempt(s, job_id, run, "passed", note=scored.note)
    return result("passed", score=scored, note=scored.note)


def run_review_bench(cfg: Config, milestones: list[str], agent_ids: list[str]) -> ReviewReport:
    """Each checkpoint of each milestone for each agent (not its own), in order, until done or
    the first refusal."""
    if unknown := [a for a in agent_ids if a not in cfg.agents]:
        raise RunnerError(f"no such agent in workflow/runner.toml: {', '.join(unknown)}")
    _check_outside_repo(cfg)
    if not cfg.metrics_db.is_file():
        raise RunnerError(f"no metrics database at {cfg.metrics_db}: nothing to replay")
    git = Git(cfg.repo)
    conn = connect(cfg.metrics_db)
    try:
        plan: list[tuple[Checkpoint, str]] = []
        for milestone in milestones:
            per_agent = {a: checkpoints(conn, git, cfg.repo.name, milestone, a) for a in agent_ids}
            for agent_id, found in per_agent.items():
                if not found:
                    raise RunnerError(
                        f"no checkpoint of {milestone} for {agent_id} to replay (its own are"
                        " skipped)"
                    )
            jobs = {cp.job: cp for found in per_agent.values() for cp in found}
            for job in sorted(jobs):
                plan += [(jobs[job], a) for a in agent_ids if jobs[job] in per_agent[a]]
    finally:
        conn.close()
    s = _open(cfg)
    report = ReviewReport()
    try:
        for cp, agent_id in plan:
            result = review_one(s, cfg.agents[agent_id], cp)
            report.reviews.append(result)
            mark = "✔" if result.outcome == "passed" else "✖"
            s.log(f"{mark} [{agent_id}] checkpoint {cp.job}: {result.outcome} · {result.note}")
            if result.outcome == "refused":
                report.stopped = (
                    f"{agent_id} refused the replay of checkpoint {cp.job} ({result.note}):"
                    " the bench stops here"
                )
                s.log(f"⏸ [{agent_id}] {report.stopped}")
                return report
    finally:
        _finish_run(s, report.stopped or f"{len(report.reviews)} replayed")
    return report
