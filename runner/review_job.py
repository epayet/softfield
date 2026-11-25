"""The runner's reviews short of the milestone review: checkpoints, their shadow and stand-in,
the pre-review, fix tickets, findings and the merges they cover (docs/workflow.md)."""

import re
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import replace
from datetime import datetime, timedelta
from functools import partial
from pathlib import Path
from typing import Any

import yaml

from runner import allowance, console, dispatch, metrics, prompts, router, session, waits
from runner.agents import GIT_READ_COMMANDS, Agent, JobResult, JobSpec, adapter_for
from runner.config import read_protected
from runner.developer_job import _log_running, block
from runner.gates import is_test_file
from runner.gitops import Git, with_trailers
from runner.lead_job import _repair_ticket, _written_tickets
from runner.report import TaskRecord
from runner.review import Finding, ReviewFileError, parse_checkpoint
from runner.session import (
    CHECK_TICKETS,
    CHECKPOINT,
    CLAUDE_HEADLESS_AGENT,
    Parked,
    Session,
    _merges,
    _milestone_row,
    _record,
    _record_readings,
    _record_refusal,
    _rel,
    _row_waits,
    _set_reason,
    _tokens_in,
    _tokens_out,
    _unpark_row,
    candidates,
    checkpoint_reason,
    enqueue,
    find_row,
    job_key,
    local_agent,
    next_number,
    record_start,
    record_ticket,
    runner_commit,
    with_progress,
)
from runner.state import State, save_state
from runner.tasks import (
    BUGS,
    Task,
    TaskError,
    milestone_file,
    milestone_key,
    parse_task,
    short_key,
    split_frontmatter,
    ticket_prefix,
)
from runner.waits import Hold, _park_support, agent_windows, claude_hold


def _name_checkpoint(s: Session) -> None:
    """The open checkpoint's reason brought up to date with the merges it now holds."""
    row = find_row(s, CHECKPOINT)
    if row is None or not (reason := checkpoint_reason(s.state)):
        return
    if (row.id or 0) < 0:
        s.unqueued[row.id or 0] = replace(row, reason=reason)
    elif row.id is not None:
        _record(s, _set_reason, row.id, reason)


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


def _finishes_its_card(s: Session, milestone: str) -> bool:
    """bug-65: the merge left its card with no ticket to build, and a merge of that card is
    still unchecked: no review round reads it (`_drop_covered_merges` kept it), so its
    checkpoint runs now, not after another card's merge."""
    from runner.milestone import _BUILDING, _ticket_milestones  # it imports this module

    key = short_key(milestone)
    if key == BUGS:  # no card: its merges wait for the count (ADR 19 item 2)
        return False
    building = set().union(*(_ticket_milestones(s.repo, folder) for folder in _BUILDING))
    if key in building:
        return False
    return any(_done_milestone(s, entry.split()[0]) == key for entry in s.state.unchecked)


def note_merge(s: Session, task: Task, rec: TaskRecord) -> None:
    """After a developer merge (``_merge`` lists it as unchecked): every ``checkpoint_every``
    of them, queue a checkpoint. One already queued runs on every merge since; one parked for
    Claude's re-check after a stand-in starts again at the next pick, for a stand-in on the new
    batch (F151 D1). One parked only for Claude's limit waits for its reset. A lead ticket's
    merge counts for none, but may be the one that completes its milestone (ADR 38)."""
    if rec.result != "done":
        return
    _drop_covered_merges(s)
    finished = _finishes_its_card(s, task.milestone)
    if not finished and (
        task.agent != "developer" or len(s.state.unchecked) < s.cfg.checkpoint_every
    ):
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


def review_reason(key: str) -> str:
    return f"{short_key(key).upper()}'s tickets are all done"
