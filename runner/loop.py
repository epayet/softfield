"""The per-task loop and the session around it (docs/workflow.md)."""

import hashlib
import re
import sqlite3
import time
from collections import Counter
from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from dataclasses import replace
from datetime import datetime, timedelta
from functools import partial
from pathlib import Path
from typing import Any

import yaml

from runner import (
    allowance,
    config,
    console,
    dispatch,
    look,
    metrics,
    notify,
    order,
    planner,
    prompts,
    push,
    router,
    session,
    stacks,
    waits,
)
from runner.agents import (
    ANY,
    GIT_READ_COMMANDS,
    Agent,
    JobResult,
    JobSpec,
    adapter_for,
)
from runner.config import Config, project_checks, read_protected
from runner.developer_job import (
    MAIN_RED_KIND,
    _held_by_red_main,
    _log_running,
    _look_at_main,
    _save_thinking,
    block,
    run_task,
    waits_for_main,
)
from runner.gates import (
    GateResult,
    is_test_file,
)
from runner.gitops import (
    RUNNER_AUTHOR,
    Git,
    GitError,
    with_trailers,
)
from runner.lead_job import _repair_ticket, _written_tickets, handle_escalation
from runner.procs import run_bounded
from runner.report import SessionReport, TaskRecord
from runner.review import Finding, ReviewFileError, parse_checkpoint
from runner.session import (
    CHECK_TICKETS,
    CHECKPOINT,
    CLAUDE,
    CLAUDE_HEADLESS_AGENT,
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
    Parked,
    RunnerError,
    Session,
    _at,
    _due,
    _has_branch,
    _merges,
    _metrics_failed,
    _milestone_row,
    _record,
    _record_readings,
    _record_refusal,
    _rel,
    _resets,
    _row_waits,
    _set_reason,
    _tokens_in,
    _tokens_out,
    _unpark_row,
    candidates,
    check_backup,
    checkpoint_reason,
    close_session,
    doing,
    enqueue,
    find_row,
    finish_row,
    first_agent,
    job_key,
    local_agent,
    local_clock,
    next_number,
    open_rows,
    open_session,
    record_start,
    record_ticket,
    row_key,
    runner_commit,
    switch_on,
    sync_cards,
    sync_tickets,
    waiting_rows,
    with_progress,
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
    full_key,
    held_ids,
    load_dir,
    milestone_file,
    milestone_key,
    milestone_order,
    parse_task,
    pick_next,
    preflight,
    pulls,
    run_order,
    short_key,
    split_frontmatter,
    stopped_ids,
    task_ids,
    task_place,
    ticket_prefix,
)
from runner.waits import (
    AT_THE_LIMIT,
    FULL,
    LEAD_COST,
    Hold,
    _claude_windows_from,
    _five_hour_switched_on,
    _park_support,
    _pick_windows,
    _wait_for_reset,
    _week_switched_on,
    agent_windows,
    check_login,
    claude_hold,
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


# --- routing (f1-25, runner/router.py) ----------------------------------------------------


def _name_checkpoint(s: Session) -> None:
    """The open checkpoint's reason brought up to date with the merges it now holds."""
    row = find_row(s, CHECKPOINT)
    if row is None or not (reason := checkpoint_reason(s.state)):
        return
    if (row.id or 0) < 0:
        s.unqueued[row.id or 0] = replace(row, reason=reason)
    elif row.id is not None:
        _record(s, _set_reason, row.id, reason)


def catch_up_plan(git: Git, branch: str, card: str) -> bool:
    """Merge main into the card's plan branch, staying on it (f6 D4). A clash only in the card's
    own doc, where each conflict is text both sides added at one place (a note main merged in, the
    plan's new sections), keeps both, main's first: before this, every merged note left its plan
    refused for good (F210, F211, F231, F235 on 2026-11-09). False, back on main with the branch
    as it was, on any other clash."""
    git.checkout(branch)
    doc = milestone_file(git.repo, "cards", full_key(git.repo, card))
    name, email = RUNNER_AUTHOR.removesuffix(">").split(" <")
    who = ("-c", f"user.name={name}", "-c", f"user.email={email}")
    message = with_trailers(f"runner: merge {MAIN} into {branch}", agent=RUNNER_AGENT)
    try:
        git.run(*who, "-c", "merge.conflictStyle=diff3", "merge", "-q", "--no-verify",
                "--no-edit", "-m", message, MAIN)  # fmt: skip
        return True
    except GitError:
        pass
    rel = doc.relative_to(git.repo).as_posix()
    unmerged = git.run("diff", "--name-only", "--diff-filter=U").split()
    # merging main into the branch, git's "theirs" is main
    text = doc.read_text(encoding="utf-8") if unmerged == [rel] else ""
    both = both_added(text, theirs_first=True) if text else None
    if both is None:
        git.run("merge", "--abort", check=False)
        git.checkout(MAIN)
        return False
    doc.write_text(both, encoding="utf-8")
    git.run("add", "--", rel)
    git.run(*who, "commit", "-q", "--no-verify", "--no-edit")
    return True


def both_added(text: str, theirs_first: bool = False) -> str | None:
    """A file with diff3 conflict marks, each conflict settled as both sides' lines, ours first
    unless ``theirs_first``; None when a conflict changed a line its base held (then both edits
    can't stand)."""
    out: list[str] = []
    sides: dict[str, list[str]] = {"ours": [], "theirs": []}
    part = ""  # "", then "ours", "base", "theirs" inside a conflict
    for line in text.splitlines(keepends=True):
        if line.startswith("<<<<<<< ") and part == "":
            part = "ours"
        elif line.startswith("||||||| ") and part == "ours":
            part = "base"
        elif line.rstrip("\r\n") == "=======" and part == "base":
            part = "theirs"
        elif line.startswith(">>>>>>> ") and part == "theirs":
            first, then = ("theirs", "ours") if theirs_first else ("ours", "theirs")
            out += sides[first] + sides[then]
            sides, part = {"ours": [], "theirs": []}, ""
        elif part == "base":
            return None
        elif part:
            sides[part].append(line)
        else:
            out.append(line)
    return None if part else "".join(out)


# --- checkpoints (ADR 12 item 8) ------------------------------------------------------


def _done_milestone(s: Session, ticket: str) -> str | None:
    """The short key of a merged ticket's milestone, from its file in done/."""
    try:
        text = (s.tasks_dir("done") / f"{ticket}.md").read_text(encoding="utf-8")
        meta, _ = split_frontmatter(text)
        return short_key(milestone_key(meta.get("milestone")))
    except (OSError, TaskError, yaml.YAMLError, UnicodeDecodeError):
        return None


def under_review(state: State) -> set[str]:
    """The short keys of the cards whose review has rounds and no stop (F191 D7): between two
    rounds, its fix tickets run in the main queue and its next round reads them."""
    stopped = {short_key(key) for key in state.review_stop}
    return {short_key(key) for key, rounds in state.review_counts.items() if rounds} - stopped


def _drop_covered_merges(s: Session) -> None:
    """ADR 38: merges the milestone's review will read leave `unchecked` and `recheck`: their
    milestone's review is due, or stopped at `restart` with its fix tickets to come. Not the
    fixes of a review's last round: no round reads those, so they keep their checkpoint. One
    log line says so."""
    from runner.milestone import RESTART, due_reviews  # runner.milestone imports this module

    covered = {short_key(key) for key in due_reviews(s.repo, s.state)}
    covered |= {short_key(key) for key, stop in s.state.review_stop.items() if stop == RESTART}
    covered |= under_review(s.state)  # its next round reads them (F191 D7)
    covered.discard(s.last_round or "")
    if not covered or not (s.state.unchecked or s.state.recheck):
        return
    dropped: dict[str, list[str]] = {}

    def keep(entry: str) -> bool:
        ticket = entry.split()[0]
        key = _done_milestone(s, ticket)
        if key is None or key not in covered:
            return True
        if ticket not in dropped.setdefault(key, []):
            dropped[key].append(ticket)
        return False

    s.state.unchecked = [m for m in s.state.unchecked if keep(m)]
    s.state.recheck = [m for m in s.state.recheck if keep(m)]
    if not dropped:
        return
    if not s.state.recheck:
        s.state.recheck_filed = []
    if not (s.state.unchecked or s.state.recheck):
        # a parked checkpoint's session: the next checkpoint must not carry it on, on these merges
        s.state.interrupted.pop(job_key(CHECKPOINT, CHECKPOINT), None)
    save_state(s.state, s.state_path)
    for key, tickets in dropped.items():
        s.log(f"no checkpoint: {key.upper()}'s review reads {', '.join(tickets)}")


def note_merge(s: Session, task: Task, rec: TaskRecord) -> None:
    """After a developer merge (``_merge`` lists it as unchecked): every ``checkpoint_every``
    of them, queue a checkpoint. One already queued runs on every merge since; one parked for
    Claude's re-check after a stand-in starts again at the next pick, for a stand-in on the new
    batch (F151 D1). One parked only for Claude's limit waits for its reset. A lead ticket's
    merge counts for none, but may be the one that completes its milestone (ADR 38)."""
    if rec.result != "done":
        return
    _drop_covered_merges(s)
    if task.agent != "developer" or len(s.state.unchecked) < s.cfg.checkpoint_every:
        return
    if (row := find_row(s, CHECKPOINT)) is not None:
        if s.state.recheck and _row_waits(s, CHECKPOINT, row.subject):
            _unpark_row(s, row)
        return
    enqueue(s, CHECKPOINT, task.milestone, checkpoint_reason(s.state), milestone=task.milestone)


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
    milestone_id = _milestone_row(s, milestone)
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
    _drop_covered_merges(s)
    if not (s.state.unchecked or s.state.recheck):
        return  # the review reads what was left; its row is finished with no job
    merged = list(dict.fromkeys([*s.state.recheck, *s.state.unchecked]))
    if (hold := claude_hold(s, session.now())) is not None:
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
        edit=(".softfield/tasks/ready/**", ".softfield/developer.md", ".softfield/var/runs/**"),
        # pytest: the tickets' pre-flight test; its commit skips the hook
        commands=(*GIT_READ_COMMANDS, "uv run pytest", CHECK_TICKETS),
    )
    s.log("")
    s.log(console.ticket_header(f"{milestone} checkpoint", "lead", None))
    s.log("Review the last merges: " + ", ".join(m.split()[0] for m in merged))
    routed = router.route(
        job.role,
        None,
        1,
        candidates(s, job.role),
        {},
        {},
        {},
        session.now(),
        authors=_authors(s, merged),
    )
    try:
        result = session.call_claude(
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
    # A ticket it wrote that fails to parse stopped the runner at its next pick (travel
    # companion's f3-07, its milestone a finding's key): one repair turn, else it's blocked.
    broken: dict[Path, list[str]] = {}
    for ticket in _written_tickets(s):
        problems = _repair_ticket(
            s,
            ticket,
            result.session_id,
            role="checkpoint",
            wrote="wrote",
            milestone=milestone,
            subject=CHECKPOINT,
        )
        if problems:
            broken[ticket] = problems
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
    for ticket, problems in broken.items():
        block(s, ticket, "the checkpoint wrote it failing pre-flight: " + "; ".join(problems))
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
        lines.append(f"- {ticket} (.softfield/tasks/done/{ticket}.md): {', '.join(files)}")
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
    at = session.now()
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
    started = session.clock()
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
        partial(adapter_for(agent.harness).run, agent, job, s.repo, log, session.now()),
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
            ended=session.now().isoformat(),
            outcome=outcome,
            tokens_in=_tokens_in(result),
            tokens_out=_tokens_out(result),
            cost_usd=result.cost_usd,
            steps=result.num_turns,
            note=note,
            session_id=result.session_id,
            model=result.model or None,
        )
    s.log(
        console.claude_end(
            agent.id, job.role, result.ok, session.clock() - started, result.cost_usd
        )
    )
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
    at = session.now()
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


# --- a pre-review of a finished milestone while Claude is out (ADR 51) -----------------------

PRE_REVIEW = "pre-review"


def pre_review(s: Session, milestone: str) -> bool:
    """Copilot (the first agent `[roles] checkpoint-stand-in` lists that its month's pace line
    permits) reads ``milestone``, finished, against its card, read-only. Each finding that isn't a
    nit goes in a developer's fix ticket (`fix_tickets`); one that would need the lead (an
    `agent: lead` ticket, or a file under a protected path) files nothing and stays `report`.
    Its findings are recorded for the review to judge. Claude's re-check isn't asked
    (`state.recheck` is untouched). Choosing the milestone and when to run are the caller's.
    False when none may run or its job failed: nothing is written."""
    from runner.milestone import _done_tickets  # it imports this module

    agents = [s.cfg.agents[agent_id] for agent_id in s.cfg.roles.get(STAND_IN, ())]
    if not agents:
        return False
    at = session.now()
    windows = agent_windows(s, agents, at)
    # No authors: a read-only agent never wrote a merge, so its model can't be an author's
    routed = router.stand_in(agents, windows, at, (), "no other work can start", paced=True)
    if routed is None:
        s.report.notes.append(f"No pre-review of {milestone} may run now.")
        return False
    agent = routed.agent
    tickets = sorted(_done_tickets(s.repo, milestone))
    changed = _ticket_files(s, tickets)
    card = milestone_file(s.repo, "cards", milestone).relative_to(s.repo).as_posix()
    s.log("")
    s.log(console.ticket_header(f"{milestone} pre-review", agent.id, None))
    job = JobSpec(
        role=PRE_REVIEW,
        prompt=prompts.PRE_REVIEW.format(
            card=card,
            tickets="\n".join(f"- {t} (.softfield/tasks/done/{t}.md)" for t in tickets),
            files=", ".join(changed) or "none",
        ),
        timeout=s.cfg.claude_timeout,
        title=f"{milestone} pre-review",
    )
    number = len(list(s.run_dir.glob("pre-review-*.json"))) + 1
    base = s.run_dir / f"pre-review-{number}-{agent.id}"
    result, findings, job_id = _read_only_review(
        s, agent, job, milestone, base, routed.reason, "the pre-review"
    )
    if not result.ok:
        return False
    prefix = f"{milestone}-P{job_id}-"
    filed = fix_tickets(s.repo, milestone, {prefix + f.id: f for f in findings}, agent.id)
    protected = tuple(read_protected(s.repo))
    for path in dict.fromkeys(filed.values()):
        task = parse_task(path, s.cfg.default_max_diff)  # the lead's work is not Copilot's to file
        if router.lead_only(task.agent, (*task.files, *task.tests), protected):
            path.unlink()
            filed = {k: p for k, p in filed.items() if p != path}
    written = list(dict.fromkeys(filed.values()))
    # D4: a finding that filed nothing is the review's to read, whatever route Copilot gave
    acted = [
        replace(f, route="local" if prefix + f.id in filed else "report") if f.actionable else f
        for f in findings
    ]
    if job_id is not None:
        record_findings(s, milestone, acted, agent.id, prefix, by_ticket=True)
    tickets_text = ", ".join(p.stem for p in written) or "none"
    s.report.notes.append(
        f"Pre-review of {milestone} by {agent.id}: {len(findings)} findings;"
        f" fix tickets: {tickets_text}."
    )
    runner_commit(s, f"pre-review of {milestone} (by {agent.id}, while Claude is out)")
    for path in written:
        record_ticket(s, path)
    return True


def _ticket_files(s: Session, tickets: Sequence[str]) -> list[str]:
    """The files the merges of ``tickets`` (a `Task:` trailer) changed, outside .softfield/.
    Not a diff from the milestone's start: other milestones' work merged in between isn't its
    own (F285's start-to-HEAD diff named F97's files)."""
    if not tickets:
        return []
    trailer = "^Task: (" + "|".join(re.escape(t) for t in tickets) + ")$"
    files: dict[str, None] = {}
    for sha in reversed(s.git.run("log", "-E", f"--grep={trailer}", "--format=%H").split()):
        for f in s.git.run("show", "--name-only", "--format=", sha).splitlines():
            if f and not f.startswith(".softfield/"):
                files[f] = None
    return list(files)


PRE_REVIEWS_MAX = 3  # per milestone (ADR 51 item 4)
PRE_REVIEW_RETRY = timedelta(hours=1)  # after one that couldn't run or failed


def _merged_since(repo: Path, milestone: str, since: datetime) -> bool:
    """Whether a done ticket of ``milestone`` merged after ``since``."""
    from runner.milestone import _done_tickets  # it imports this module

    tickets = _done_tickets(repo, milestone)
    if not tickets:
        return False
    trailer = "^Task: (" + "|".join(re.escape(t) for t in tickets) + ")$"
    log = Git(repo).run("log", "-E", f"--grep={trailer}", "--format=%cI")
    return any(datetime.fromisoformat(line) > since for line in log.split())


def pre_review_pick(
    repo: Path,
    state: State,
    windows: dispatch.Windows,
    at: datetime,
    passed: Mapping[str, Sequence[str]] | None,
) -> str | None:
    """The milestone to pre-review when nothing else can start (ADR 51 items 2 and 4), for the
    runner and the dry run alike (ADR 44 item 9): Claude at its real limit, and the first
    milestone in `due_reviews` order with fewer than three passed pre-reviews (``passed``: their
    start times by key) and a merge since the last. None with no ``passed`` (no database)."""
    from runner.milestone import due_reviews  # it imports this module

    if passed is None or waits._held_at_the_limit(windows, at) is None:
        return None
    for key in due_reviews(repo, state):
        starts = passed.get(key, ())
        if len(starts) >= PRE_REVIEWS_MAX:
            continue
        if starts and not _merged_since(repo, key, max(map(datetime.fromisoformat, starts))):
            continue
        return key
    return None


def _pre_review_turn(s: Session) -> bool:
    """With nothing else to start, the pre-review `pre_review_pick` names, if any. Whether
    one ran: the turn then picks again."""
    if s.project_id is None:
        return False
    at = session.now()
    passed = _record(s, metrics.passed_pre_reviews, s.project_id)
    key = pre_review_pick(s.repo, s.state, waits._windows_now(s, at), at, passed)
    if (
        key is None
        or at - s.pre_review_failed.get(key, at - 2 * PRE_REVIEW_RETRY) < PRE_REVIEW_RETRY
    ):
        return False
    if pre_review(s, key):
        return True
    s.pre_review_failed[key] = at
    return False


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
    """A ticket (the lead's when the ticket at fault was itself a fix: it has `finding:`;
    else a developer's) in .softfield/tasks/ready/ for a stand-in checkpoint's ``findings`` (by
    key), on one ticket at fault and of one kind, from that ticket in .softfield/tasks/done/: its
    milestone (unless signed off: then ``milestone``, the running one), its tests, its difficulty,
    and the findings' files that exist (else its files). A `test` kind is `tests_only`: tests in
    `files:`, which pass on main. The findings are untrusted text: they go in the body, quoted, and
    only checked paths reach the frontmatter. None when no done ticket is at fault."""
    from runner.milestone import signed_off  # runner.milestone imports this module

    first = next(iter(findings.values()))
    tests_only = first.kind == "test"
    if not _TICKET_ID_RE.fullmatch(first.ticket):
        return None
    source_path = repo / ".softfield" / "tasks" / "done" / f"{first.ticket}.md"
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
        for path in (repo / ".softfield" / "tasks").glob("*/*.md")
        if (found := re.match(rf"{re.escape(prefix)}-(\d+)-", path.stem))
    ]
    # Named by the ticket at fault, not the finding's first words, cut mid-phrase (F171 D4)
    slug = re.sub(r"^[^-]+-\d+-(?:fix(?:-|$))?", "", first.ticket.lower())
    words = re.findall(r"[a-z0-9]+", slug)[:4] + (["tests"] if tests_only else [])
    task_id = f"{prefix}-{max(numbers, default=0) + 1:02d}-fix" + "".join(f"-{w}" for w in words)
    meta: dict[str, Any] = {"id": task_id, "milestone": milestone}
    if source.finding is not None:  # a fix of a fix is the lead's (f68-08)
        meta["agent"] = "lead"
    if milestone == source.milestone:  # its card (ADR 19); the list places it (ADR 45)
        meta |= {"area": source.area} if source.area else {}
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
        f" `.softfield/tasks/done/{first.ticket}.md`.{kind} What it found is under Finding:\n"
        + "\n".join(places_text)
        + "\n\n### Finding\n"
        + "\n\n".join(quotes)
        + f"\n\n### Done when\n{done}"
    )
    frontmatter = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True)
    path = repo / ".softfield" / "tasks" / "ready" / f"{task_id}.md"
    path.write_text(f"---\n{frontmatter}---\n\n{body}", encoding="utf-8")
    return path


# --- parking and the reserve (ADR 15 items 4, 5 and 10) --------------------------------


HOLD_POLL_S = 5.0  # how often the hold for the owner applies their requests (f6-22)


def _plan_branch(s: Session, branch: str) -> bool:
    """Check out a card's plan branch for its planner job (f6 D4): caught up with main, or
    new from main. Returns whether it is new. One that clashes with main is used as it is."""
    if not _has_branch(s.git, branch):
        s.git.run("checkout", "-q", "-b", branch, MAIN)
        return True
    if not catch_up_plan(s.git, branch, branch.removeprefix("plan/")):
        if kept := _rebuild(s.git, branch):
            s.report.notes.append(
                f"{branch} clashed with {MAIN}: rebuilt on it from its own commits,"
                f" its old tip kept as {kept}."
            )
        else:
            s.report.notes.append(
                f"{branch} clashes with {MAIN}: the planner drafted on it as it is."
            )
            s.git.checkout(branch)
    return False


# The commit F139 gave each plan branch that left main before its move (F139-F1): main has the
# move already, so a rebuild leaves it out.
F139_MOVE = "F139: this branch's folder moves to .softfield"


def _rebuild(git: Git, branch: str) -> str:
    """A plan branch that clashes with main, rebuilt on main from its own commits, oldest first
    (F139-F1): merges and F139's move left out, its drafts under .factory/ carried to their new
    folder, and where a draft and main both changed a line, the draft's wins. The branch moves
    only when every commit replays, checked out, its old tip kept as ``superseded/plan-<card>``,
    which is returned; otherwise "", on main, with the branch and main as they were."""
    log = git.run("log", "--reverse", "--no-merges", "--format=%H%x1f%s", f"{MAIN}..{branch}")
    commits = [
        sha
        for sha, _, subject in (line.partition("\x1f") for line in log.splitlines())
        if subject != F139_MOVE
    ]
    name, email = RUNNER_AUTHOR.removesuffix(">").split(" <")
    git.run("checkout", "-q", "--detach", MAIN)
    for sha in commits:
        try:
            git.run(
                *("-c", f"user.name={name}", "-c", f"user.email={email}"),
                *("-c", "merge.directoryRenames=true"),
                *("cherry-pick", "--allow-empty", "--keep-redundant-commits", "-X", "theirs", sha),
            )
        except GitError:
            git.run("cherry-pick", "--abort", check=False)
            git.run("reset", "-q", "--hard", check=False)
            git.checkout(MAIN)
            return ""
    kept = f"superseded/{branch.replace('/', '-')}"
    git.run("branch", "-f", kept, branch)
    git.run("checkout", "-q", "-B", branch)
    return kept


def _commit_drafts(s: Session, thread: str, branch: str, subject: str, new: bool) -> dict[str, str]:
    """After a planner job: commit its drafts on ``branch`` and go back to main (f6 D4). What
    it changed outside the drafts' folders and its card's ready tickets (a replan's, f6-13) is
    dropped; a new branch with no drafts goes. Returns the mock-up pages the commit added or
    changed, path to text (F152)."""
    if s.git.current_branch() != branch:  # never commit drafts anywhere else
        s.git.checkout(MAIN)
        return {}
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
    pages: dict[str, str] = {}
    if s.git.commit_all(
        with_trailers(f"planner {subject}: drafts (by Claude)", agent=CLAUDE_HEADLESS_AGENT)
    ):
        # -z: paths unquoted; --no-renames: a moved mock-up is added at its new path
        changed = s.git.run(
            "diff", "--name-only", "-z", "--no-renames", "--diff-filter=AM", "HEAD~1", "HEAD"
        )
        for path in changed.split("\0"):
            if planner.is_mockup_file(path):
                pages[path] = (s.repo / path).read_text(encoding="utf-8", errors="replace")
    s.git.checkout(MAIN)
    if new and not s.git.run("rev-list", f"{MAIN}..{branch}").strip():
        s.git.run("branch", "-q", "-D", branch)
    return pages


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
                refused = auto_merge(s.repo, s.db, s.project_id, session.now(), proposal, thread)
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


def _all_cards(repo: Path) -> list[tuple[str, str]]:
    """Every milestone doc's card as (short key, state), as `sync_cards` reads them, in the
    queue's order (ADR 45): the list's, then what it doesn't name by card number."""
    from runner.milestone import card  # runner.milestone imports this module

    found = []
    for path in sorted((repo / ".softfield" / "cards").glob("*.md")):
        try:
            key = milestone_key(path.stem)
            text = path.read_text(encoding="utf-8")
        except (TaskError, OSError, UnicodeDecodeError):
            continue
        if key != BUGS:
            found.append((short_key(key), card(key, text).state, milestone_order(key)))
    places = {key: n for n, key in enumerate(order.read_order(repo) or [])}
    found.sort(key=lambda c: (places.get(c[0], len(places)), c[2]))
    return [(key, state) for key, state, _ in found]


def work_stands(
    cfg: Config, state: State, minutes: Sequence[float], behind: Mapping[str, str] | None = None
) -> str:
    """Where the work stands, for a planner job's prompt (F21 D1), from `dry_run_plan`'s
    inputs: the job in flight, the ready tickets in run order with what each waits for
    (``behind`` its queued direction or escalation), every card, and ``minutes``
    (`ticket_minutes`). It reads .softfield/tasks/ and .softfield/cards/ and writes nothing."""
    tasks = cfg.repo / ".softfield" / "tasks"
    ready = load_dir(tasks / "ready", cfg.default_max_diff)
    done = task_ids(tasks / "done")
    paused = blocked_ids(ready, stopped_ids(tasks))
    by_id = {t.id: t for t in ready}
    listed = [
        planner.ReadyTicket(
            ticket.id,
            by_id[ticket.id].milestone,
            "lead" if ticket.lead else "developer",
            # a dependency in the block's words: "waits for <id>"
            ticket.waits and ticket.waits.replace("waiting on ", "waits for ", 1),
            ticket.early_for,
        )
        for ticket in _dispatch_tickets(
            cfg.repo, ready, done, paused, state.parked, session.now(), behind, state.regate.keys()
        )
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
        if (looked := planner.look_of(row.subject)) is not None:  # the runner's (ADR 29)
            thread, message_id = looked
            runners = _record(s, metrics.find_planner_message, message_id)
            if runners is None or runners["author"] != planner.RUNNER:
                raise planner.PlannerError(f"the runner's message {message_id} is gone")
            text, comments = str(runners["text"]), dict[int, str]()
        else:
            thread, request_id = planner.request_of(row.subject)
            request = _record(s, metrics.find_request, request_id)
            text, comments = planner.message(request["value"] if request else None)
    except planner.PlannerError as exc:
        s.report.notes.append(f"The planner's {row.subject} can't run: {exc}.")
        return
    if (hold := claude_hold(s, session.now())) is not None:
        _park_support(s, PLANNER, row.subject, hold)
        return
    at = session.now().isoformat()
    found = _record(s, metrics.planner_thread, s.project_id, thread, at)
    if found is None:
        return
    branch = planner.plan_branch(thread)
    threads = _record(s, metrics.thread_cards, s.project_id) or []
    earlier = ""
    if not found["session_id"]:  # a new thread, or replies written outside a job
        said = list(_record(s, metrics.planner_messages, found["id"]) or [])
        # up to the lead's last reply: the owner's or the runner's after it are this message
        # or queued ones
        while said and said[-1]["author"] != "lead":
            said.pop()
        earlier = planner.history(said)
    # F49 D4: the threads of the cards merged into this one, read once, by a resumed job too
    merged = _record(s, metrics.unread_merges, found["id"]) or []
    for card in merged:
        gone = _record(s, metrics.find_thread, s.project_id, card)
        if gone is not None:
            said = list(_record(s, metrics.planner_messages, gone["id"]) or [])
            earlier += planner.history(said, merged=card)
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
        prompt=planner.prompt(
            thread, text, comments, threads, earlier, stands, blocked=looked is not None
        ),
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
        web=True,  # ADR 33
    )
    milestone = "" if thread == planner.GENERAL else full_key(s.repo, thread)
    new = branch is not None and _plan_branch(s, branch)
    pages: dict[str, str] = {}
    try:
        result = session.call_claude(s, job, milestone, row.subject, park=True)
    except Parked:
        return
    finally:
        if branch is not None:
            pages = _commit_drafts(s, thread, branch, row.subject, new)
    if result.ok:
        reply = planner.parse_reply(
            result.text, planner.cards(s.repo)
        )  # main's: merges apply there
        reply = planner.with_mockups(reply, pages)
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
    if result.ok and merged:  # read: a merge this reply applied is still to read
        unread = _record(s, metrics.unread_merges, found["id"]) or []
        left = [card for card in unread if card not in merged]
        _record(s, metrics.set_unread_merges, found["id"], left)
    _record(
        s,
        metrics.add_planner_message,
        found["id"],
        "lead",
        session.now().isoformat(),
        planner.stored_text(reply),
        points=None if reply.note else reply.points,
        proposals=None if reply.note and not reply.proposals else reply.proposals,
        job_id=s.last_job_id,
    )
    name = planner.thread_name(thread)
    if looked is not None:
        item = (
            f"The lead looked at a ticket blocked on {name}: your answers are wanted."
            if result.ok
            else f"The lead couldn't look at the ticket blocked on {name}: it waits on your desk."
        )
    else:
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
        created=session.now().isoformat(),
    )
    # each reply is news, said as what happened
    session._notify(s, *notify.planner_message(thread, looked=looked is not None, ok=result.ok))


# ADR 48 item 4, exactly: it may edit anything in the new project's folder and run these. Never
# `docker` (ADR 46 item 7), never `softfield accept` or `create`: the owner's yes does those.
SETUP_COMMANDS = (
    "uv",
    "git status",
    "git diff",
    "git log",
    "git add",
    "git commit",
    "softfield check-all",
    "softfield doctor",
    "ss -ltn",
)
ADR_00 = ".softfield/adr/00-initial.md"


def setting_up(s: Session) -> bool:
    """Whether the session's project was started from the Projects page and is still being set
    up (ADR 48): the runner gives it nothing but its ``setup`` jobs until it passes."""
    found = _record(s, metrics.project_state, s.cfg.project_name)
    return found is not None and found[1] == metrics.SETTING_UP


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


def _setup_said(s: Session, subject: str) -> tuple[str, str, dict[int, str], bool]:
    """A setup row's thread, and what was said on it this round: nothing for the first round
    (``m1``), the owner's message (``m1#41``) or the runner's (``m1#m12``, True)."""
    if "#" not in subject:
        return planner.thread_key(subject), "", {}, False
    if (looked := planner.look_of(subject)) is not None:
        thread, message_id = looked
        runners = _record(s, metrics.find_planner_message, message_id)
        if runners is None or runners["author"] != planner.RUNNER:
            raise planner.PlannerError(f"the runner's message {message_id} is gone")
        return thread, str(runners["text"]), {}, True
    thread, request_id = planner.request_of(subject)
    request = _record(s, metrics.find_request, request_id)
    text, comments = planner.message(request["value"] if request else None)
    return thread, text, comments, False


def _with_adr_00(s: Session, reply: planner.Reply) -> planner.Reply:
    """The setup's reply with ADR 00 as an ``adr`` proposal, which its Approve needs (F122 D4):
    one the lead wrote on main without listing it is listed by the runner."""
    if reply.note is not None or not (s.repo / ADR_00).is_file():
        return reply
    if any(p.get("kind") == "adr" and p.get("path") == ADR_00 for p in reply.proposals):
        return reply
    listed = {
        "id": "adr-00",
        "kind": "adr",
        "title": "ADR 00: Initial decisions",
        "path": ADR_00,
        "key_points": [
            {
                "n": 1,
                "title": "Listed by the runner",
                "text": "The lead wrote ADR 00 without listing it: read it before you approve.",
            }
        ],
    }
    return replace(reply, proposals=(*reply.proposals, listed))


def run_setup(s: Session, row: dispatch.Queued) -> None:
    """Set a project started from the Projects page up (F122 D3, ADR 48 items 4 and 5): the
    lead, headless, in its folder on main, with ``prompts.SETUP`` (bootstrap.md and the form)
    and ADR 48's tools, on the planner's agents and under its reserve. It commits its own work.
    Its reply is the lead's message on M1's thread, as a planner's is, with ADR 00 as an
    ``adr`` proposal; a later round (the owner's message, the runner's) resumes its session.
    A message whose request is gone is done."""
    from runner import setup as project_setup  # it imports the planner, which imports this

    if s.project_id is None:
        return
    if not setting_up(s):  # its tools never reach a project already in the factory
        s.report.notes.append(f"The setup's {row.subject}: the project isn't being set up.")
        return
    try:
        thread, said, comments, runners = _setup_said(s, row.subject)
    except planner.PlannerError as exc:
        s.report.notes.append(f"The setup's {row.subject} can't run: {exc}.")
        return
    if (hold := claude_hold(s, session.now())) is not None:
        _park_support(s, SETUP, row.subject, hold)
        return
    found = _record(s, metrics.planner_thread, s.project_id, thread, session.now().isoformat())
    if found is None:
        return
    form = project_setup.form(s.repo, s.cfg.project_name)
    job = JobSpec(
        role=SETUP,
        prompt=prompts.setup_prompt(
            config.HOME,
            form.name,
            form.idea,
            form.built_with,
            form.app,
            said,
            comments,
            runner=runners,
        ),
        timeout=s.cfg.claude_timeout,
        edit=(ANY,),
        commands=SETUP_COMMANDS,
        resume=found["session_id"] or None,
        title=f"setting up: {row.reason}",
    )
    try:
        result = session.call_claude(
            s,
            job,
            full_key(s.repo, thread),
            row.subject,
            park=True,
            routed=first_agent(s, PLANNER),  # Opus, as the planner's jobs (ADR 48 item 4)
        )
    except Parked:
        return
    _left_on_main(s, row.subject)
    if result.ok:
        reply = _with_adr_00(s, planner.parse_reply(result.text, planner.cards(s.repo)))
    else:  # the owner's words, or the form, are there to try again
        failed = f"the lead's setup failed ({result.text.strip()[:200]}): send a message to retry"
        reply = planner.Reply("", note=failed)
    if reply.note is not None:
        s.report.notes.append(f"The setup's reply on {row.subject}: {reply.note}.")
    if result.session_id:
        _record(s, metrics.set_thread_session, found["id"], result.session_id)
    _record(
        s,
        metrics.add_planner_message,
        found["id"],
        "lead",
        session.now().isoformat(),
        planner.stored_text(reply),
        points=None if reply.note else reply.points,
        proposals=None if reply.note and not reply.proposals else reply.proposals,
        job_id=s.last_job_id,
    )
    name = s.cfg.project_name
    item = (
        f"The lead set {name} up: ADR 00 waits for your yes on its first card."
        if result.ok
        else f"The lead couldn't set {name} up: write on its first card to try again."
    )
    _record(
        s,
        metrics.upsert_owner_item,
        s.project_id,
        planner.PLANNING,
        thread,
        text=item,
        created=session.now().isoformat(),
    )
    session._notify(s, *notify.planner_message(thread, looked=False, ok=result.ok))


def _left_on_main(s: Session, subject: str) -> None:
    """After a setup job: back on main, and what it left uncommitted committed as its own, so
    the folder stays a clean main the next pick and the owner's approval can work on."""
    try:
        if s.git.current_branch() != MAIN:
            s.report.notes.append(f"The setup's {subject} left main: back on it.")
            s.git.checkout(MAIN)
        if not s.git.is_clean():
            message = with_trailers(
                "setup: what the lead left uncommitted", agent=CLAUDE_HEADLESS_AGENT
            )
            s.git.commit_all(message)
            s.report.notes.append(f"The setup's {subject} left work uncommitted: committed.")
    except GitError as exc:
        s.report.notes.append(f"The setup's {subject} left its folder unsettled: {exc}.")


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
) -> Task | None:
    """The next ticket, for the runner (`_next_task`) and the dry run (`dry_run_plan`) alike (ADR
    44 item 9); ``waiting`` holds what a pause or a hold keeps from running.

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
    if task is None and passed_over:
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
    return first(developers) or task


def _next_task(s: Session, ready: list[Task], done: set[str], paused: set[str]) -> Task | None:
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
    without ``wait`` it never holds or sleeps here (for Claude's reset, the owner's pause or
    nothing to run) but returns, so the next project can go.

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
            _next_task(s, ready, done, paused | held.keys() | behind.keys() | red)
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
    from the first project that has one it can run. While the owner pauses, no lane and no
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
    for s in sessions:
        restart, ran = turn(s, once=True)
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
            restart, ran = project_round(live, turn)
            if restart:
                return True
            if not ran:
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
    """`runner run --dry-run` (f8-02): `dispatch.plan`'s list, each job with what it waits for and
    why it is there, with `choose_ticket`'s ticket marked as next as the runner would take it
    (ADR 44 item 9), and each ticket's pre-flight problems
    (runner/instructions/task-writing.md).
    Reads
    .softfield/tasks/, state.json and the metrics database if there is one: any branch, any tree,
    and
    no run folder or row (f1-33). A due review not queued yet is listed as the run would queue it,
    and a support job an older state.json parked as the row the run makes of it."""
    from runner.milestone import due_reviews  # runner.milestone imports this module

    at = session.now()
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
    lines = [h if h.pick.kind == dispatch.TICKET else r for r, h in zip(rows, held, strict=True)]
    chosen = choose_ticket(
        ready,
        done,
        paused
        | _held(cfg.repo, ready).keys()
        | behind.keys()
        | _held_by_red_main(cfg.repo, state, ready),
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

    _print_plan(lines, ready, done, paused, cfg.repo, next_id, pre_review_next)


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


def _job_name(job: dispatch.Pick) -> str:
    if job.kind == dispatch.TICKET:
        return job.subject
    if job.kind == dispatch.REVIEW:
        return f"review {short_key(job.subject).upper()}"
    return f"{job.kind} {job.subject}"


def _print_plan(
    lines: list[dispatch.Line],
    ready: list[Task],
    done: set[str],
    paused: set[str],
    repo: Path,
    next_ticket: str | None,
    pre_review: Callable[[], str | None] = lambda: None,
) -> None:
    """Each job in the order it would run, the next one marked, and each ticket's pre-flight
    problems. Of the tickets only ``next_ticket`` can be next (`choose_ticket`); with nothing
    else to run, ``pre_review`` names the milestone Copilot would pre-review (ADR 51)."""
    print(f"ready: {len(ready)}  done: {len(done)}  paused: {len(paused)}")
    tasks = {t.id: t for t in ready}

    def goes(line: dispatch.Line) -> bool:
        if line.pick.kind == dispatch.TICKET:
            return line.pick.subject == next_ticket
        return line.waits is None

    picked = next((line for line in lines if goes(line)), None)
    for line in lines:
        marker = "->" if line is picked else "  "
        print(f"{marker} {_job_name(line.pick)}: {line.waits or 'runnable'}, {line.pick.reason}")
        if line.pick.kind == dispatch.TICKET:
            for problem in preflight(tasks[line.pick.subject], repo):
                print(f"     pre-flight: {problem}")
    if picked is None and (milestone := pre_review()) is not None:
        print(f"next: Copilot's pre-review of {short_key(milestone).upper()}")
        return
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
