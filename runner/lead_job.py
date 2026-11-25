"""A lead ticket's job and an escalation (F290 D1): the headless lead on its branch and its
settling, the escalation's decision, the repair of a ticket a Claude job wrote, and the finish
of a developer's branch."""

import json
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from typing import Any

import yaml

from runner import checks, console, messages, prompts, router, session
from runner.agents import ANY, CHECK_COMMANDS, GIT_READ_COMMANDS, JobResult, JobSpec
from runner.config import project_checks
from runner.developer_job import (
    _check_all,
    _check_results,
    _logs_dir,
    _main_is_red,
    _merged_line,
    block,
)
from runner.gitops import LOCAL_MODEL_AGENT, with_trailers
from runner.rating_store import rate_finished
from runner.report import TaskRecord
from runner.session import (
    CHECK_TICKETS,
    CLAUDE_HEADLESS_AGENT,
    LOGIN_HELD,
    MAIN,
    NOTE_FILE,
    RUNNER_AGENT,
    Parked,
    Session,
    _catch_up,
    _clear_in_flight,
    _has_branch,
    _rel,
    _set_in_flight,
    candidates,
    job_key,
    record_ticket,
    runner_commit,
)
from runner.state import save_state
from runner.tasks import Task, append_footer, carry_footers, parse_task, preflight
from runner.waits import _park_support, claude_hold


@contextmanager
def _settling(
    s: Session, role: str, task: Task, session_id: str | None, agent: str | None = None
) -> Iterator[None]:
    """The runner's own steps on a Claude job's work once its session ended (check-all, the
    commits, the merge): still the job in flight, so a stop among them is recovered at the next
    start like one inside the session, its work kept on a branch and its session resumed.
    f17-01 (2026-10-16): stopped during the escalation's check-all, its finished work was left
    on main with nothing in flight, and the runner wouldn't start again. A stop keeps it.
    ``agent`` is the one whose session it was, else the role's first."""
    _set_in_flight(
        s,
        kind=role,
        ticket=task.id,
        subject=task.id,
        milestone=task.milestone,
        branch=s.git.current_branch(),
        agent=agent or s.cfg.agent_for(role).id,
        session_id=session_id,
    )
    yield
    _clear_in_flight(s)


def run_lead_task(s: Session, task: Task, rec: TaskRecord) -> None:
    """The lead's own ticket, as a headless job on its branch; merged only if check-all
    passes. A lead ticket that fails is blocked: there's no one above the lead but the owner.
    One that failed only where main fails too had its work kept: it merges from its branch,
    with no new session, once its checks pass (F106 D5)."""
    logs = rec.logs or _logs_dir(s.run_dir, task.id)
    branch = f"task/{task.id}"
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
    parked = s.state.interrupted.get(job_key(job.role, task.id))
    routed = _lead_route(s, task, parked)
    lead = routed.agent.id
    waited = s.state.waits_on_main.pop(task.id, None)
    if waited is not None:
        save_state(s.state, s.state_path)
    if waited is not None and _has_branch(s.git, waited):
        # its work was done when main went red (F106 D5): main joins it, its checks run again
        if not _catch_up(s, waited):
            rec.result = "stopped"
            block(s, task.path, f"its work on {waited} clashes with {MAIN}")
            return
        s.log(f"[{RUNNER_AGENT}] {task.id}'s work waited on {waited} for {MAIN}: checks again")
        _settle_or_step_up(s, task, rec, logs, job, lead, None)
        return
    if parked and parked["branch"] == branch:
        s.git.checkout(branch)  # an interrupted run's work, which its session resumes
    else:
        s.git.fresh_branch(branch, MAIN)
    if (result := _call_lead(s, task, rec, job, routed)) is not None:
        _settle_or_step_up(s, task, rec, logs, job, lead, result.session_id)


def _call_lead(
    s: Session, task: Task, rec: TaskRecord, job: JobSpec, routed: router.Route
) -> JobResult | None:
    """A lead ticket's job on its branch; None when Claude's limit parked it."""
    try:
        result = session.call_claude(
            s, job, task.milestone, task.id, ticket=task.id, park=True, routed=routed
        )
    except Parked:
        s.git.checkout(MAIN)
        rec.result = "parked"
        return None
    return result


def _settle_or_step_up(
    s: Session,
    task: Task,
    rec: TaskRecord,
    logs: Path,
    job: JobSpec,
    lead: str,
    session_id: str | None,
) -> None:
    """ADR 32 item 3 (F153 D3): when ``lead`` isn't the last agent `[roles] lead-ticket` lists
    and its check-all fails, the next agent gets one fresh job on the same branch, told of the
    earlier work and its check-all, before the ticket is blocked."""
    ids = list(s.cfg.roles.get(job.role, ()))
    up = ids[ids.index(lead) + 1] if lead in ids[:-1] else None
    with _settling(s, job.role, task, session_id, lead):
        settled = _settle_lead_task(s, task, rec, logs, job, lead, last=up is None)
    if settled or up is None:
        return
    branch = f"task/{task.id}"
    rec.attempts = 2
    s.git.checkout(branch)
    note = LEAD_STEP_UP_NOTE.format(
        agent=lead, branch=branch, main=MAIN, checks=_rel(s, logs / "check-all.txt")
    )
    routed = router.Route(
        s.cfg.agents[up], f"{up} steps up from {lead}, whose check-all failed (ADR 32 item 3)"
    )
    step = replace(job, prompt=job.prompt + note, resume=None)  # a fresh session, not lead's
    if (result := _call_lead(s, task, rec, step, routed)) is not None:
        with _settling(s, step.role, task, result.session_id, up):
            _settle_lead_task(s, task, rec, logs, step, up)


LEAD_STEP_UP_NOTE = (
    "\nAn earlier attempt by {agent} is committed on `{branch}` (`git diff {main}...{branch}`"
    " shows it) and failed `check-all`: its output is in `{checks}`. Build on that work or"
    " undo it, so the checks pass."
)


def _lead_route(s: Session, task: Task, interrupted: Mapping[str, Any] | None) -> router.Route:
    """Who does a lead ticket (ADR 32 item 1): an interrupted one resumes on the agent whose
    session it was; else the router picks by its difficulty."""
    agent = s.cfg.agents.get(str((interrupted or {}).get("agent") or ""))
    if agent is not None:
        return router.Route(agent, f"{agent.id}, whose interrupted session this ticket resumes")
    ticket = router.Ticket(task.id, task.difficulty, lead_only=True)
    return router.route(
        "lead-ticket",
        ticket,
        1,
        candidates(s, "lead-ticket"),
        {},
        {},
        {},
        session.now(),
        lead_first_up_to=s.cfg.lead_first_up_to,
    )


def _settle_lead_task(
    s: Session,
    task: Task,
    rec: TaskRecord,
    logs: Path,
    job: JobSpec,
    lead: str,
    *,
    last: bool = True,
) -> bool:
    """The lead ticket's work, merged once check-all passes, else blocked on its branch;
    ``lead`` is the agent that did it (ADR 32 item 4). Unless it's the ``last`` attempt, a
    failed check-all leaves it for the next agent's: False, and nothing settled."""
    branch = f"task/{task.id}"
    s.git.commit_all(with_trailers(f"wip {task.id} (lead)", agent=CLAUDE_HEADLESS_AGENT))
    if not s.git.changed_files(MAIN):  # an interrupted run's commit counts too
        s.git.checkout(MAIN)
        rec.result = "stopped"
        block(s, task.path, "the lead ticket changed nothing")
        return True
    failed = [r.name for r in _check_results(s, task.id, logs, "check-all.txt") if not r.ok]
    if failed:
        s.git.checkout(MAIN)
        if _main_is_red(s, task, failed, logs):
            rec.result = "waits for main"
            return True
        if not last:
            return False
        rec.result = "stopped"
        block(s, task.path, f"check-all failed; the work is on {branch}")
        return True
    rec.commit = s.git.squash_merge(
        branch,
        MAIN,
        with_trailers(f"{task.id}: {task.goal}", agent=CLAUDE_HEADLESS_AGENT, task=task.id),
    )
    target = s.tasks_dir("done") / task.path.name
    s.git.move(task.path, target)
    append_footer(target, {"result": "done", "agent": "lead", "attempts": rec.attempts})
    runner_commit(s, messages.done_message(task.id, rec))
    record_ticket(s, target, merged_by=lead, commit=rec.commit)
    rate_finished(s, task.id)
    s.git.run("branch", "-D", branch)
    rec.result = "done"
    _merged_line(s, lead, task.id, rec)
    return True


# --- escalation handling ------------------------------------------------------------


def _only_docs_and_tasks(s: Session) -> bool:
    changed = [line[3:] for line in s.git.run("status", "--porcelain").splitlines()]
    return checks.hook_can_skip(changed) or not changed


TICKET_REPAIR_PROMPT = """\
The ticket you {wrote}, {path}, fails the runner's pre-flight:
{problems}
Fix that file only: its `milestone:` is its card's key (as in its source ticket's frontmatter,
never a finding's key), it names repo-relative paths (`tests/conftest.py`, not `conftest.py`)
and only paths and symbols that exist, or that its `files:` or `tests:` list. If it still
fails, the runner blocks the ticket with these problems."""


def _ticket_problems(s: Session, path: Path) -> list[str]:
    try:
        return preflight(parse_task(path, s.cfg.default_max_diff), s.repo)
    except (OSError, ValueError, yaml.YAMLError) as e:
        return [f"the ticket doesn't parse: {e}"]


def _repair_ticket(
    s: Session,
    path: Path,
    session_id: str | None,
    *,
    role: str,
    wrote: str,
    milestone: str,
    subject: str,
    ticket: str | None = None,
) -> list[str]:
    """f2-F4: a ticket a Claude job wrote that fails pre-flight (a requeue naming a missing
    path: f1-36, f1-15, f2-06; a checkpoint's fix ticket with a finding key for milestone,
    which stopped the runner at its next pick) gets one turn of that job's session to fix it,
    as a direction's repair is checked (f1-50). Returns the problems left."""
    if not path.is_file() or not (problems := _ticket_problems(s, path)):
        return []
    rel = path.relative_to(s.repo).as_posix()
    s.log(f"{role} {subject}: {path.stem} fails pre-flight: {'; '.join(problems)}")
    job = JobSpec(
        role=role,
        prompt=TICKET_REPAIR_PROMPT.format(
            wrote=wrote, path=rel, problems="\n".join(f"- {p}" for p in problems)
        ),
        timeout=s.cfg.claude_timeout,
        edit=(rel,),
        commands=GIT_READ_COMMANDS,
        resume=session_id,
    )
    session.call_claude(s, job, milestone, subject, ticket=ticket, give_up=True)
    return _ticket_problems(s, path) if path.is_file() else ["the repair removed it"]


def _repair_requeue(s: Session, task: Task, requeued: Path, session: str | None) -> list[str]:
    problems = _repair_ticket(
        s,
        requeued,
        session,
        role="escalation",
        wrote="requeued",
        milestone=task.milestone,
        subject=task.id,
        ticket=task.id,
    )
    if problems:
        s.report.notes.append(f"Requeue of {task.id} still fails pre-flight after its repair.")
    return problems


def _written_tickets(s: Session) -> list[Path]:
    """The ready tickets a job added or changed, not yet committed."""
    lines = s.git.run("status", "--porcelain", "-uall", "--", ".softfield/tasks/ready").splitlines()
    paths = [s.repo / line[3:] for line in lines if line.endswith(".md")]
    return [p for p in paths if p.is_file()]


def handle_escalation(s: Session, task: Task, logs: Path, reason: str) -> None:
    """The lead's decision on an escalated ticket. While Claude can't take it (a limit, or the
    owner's share of its 5-hour window), it parks and the queue goes on; a parked escalation
    isn't counted (ADR 16 item 4)."""
    escalated = s.tasks_dir("escalated") / task.path.name
    used = s.state.escalations.get(task.id, 0)
    # One stopped part-way is the same escalation when it resumes: not counted again (one
    # parked for a limit was taken off the count when it parked)
    earlier = s.state.interrupted.get(job_key("escalation", task.id))
    resuming = earlier is not None and earlier.get("cause") not in ("limit", LOGIN_HELD)
    if used >= s.cfg.escalations_per_task and not resuming:
        block(s, escalated, f"{used} escalations used; last: {reason}")
        return
    resume = {"milestone": task.milestone, "logs": _rel(s, logs), "reason": reason}
    if (hold := claude_hold(s, session.now())) is not None:
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
        commands=(*CHECK_COMMANDS, *GIT_READ_COMMANDS, CHECK_TICKETS, f"git checkout {branch}"),
    )
    decision_path = logs / "decision.json"
    if earlier is None:  # only this escalation's decision counts (a parked one resumes too)
        decision_path.unlink(missing_ok=True)
    try:
        result = session.call_claude(
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
    s.log(
        console.merged(merger, task.id, 1, lines, session.clock() - s.ticket_started)
    )  # its one job
