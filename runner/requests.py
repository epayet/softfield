"""The owner's requests from the dashboard (ADR 18 item 2, f5 D1 and D2).

The dashboard only writes a request row. The runner applies it, with the code of its console
command: at each pick, while a wait for the owner's 25% or their resume sleeps
(`take_switches`), and at the start of every ``runner`` command while no run is live. Each
request is finished once, with its result or its error, and never retried. Git and .softfield/tasks/
keep one writer, and the run state.json, whose reserve switches (ADR 22 item 4) and pause
(item 5) the requests set.
"""

import json
import re
import sqlite3
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

import yaml

from runner import loop, metrics, milestone, notify, order, owner, planner
from runner.config import project_name
from runner.gitops import RUNNER_AUTHOR, Git, GitError, with_trailers
from runner.state import State
from runner.tasks import (
    BUGS,
    LATER,
    TaskError,
    carry_footers,
    full_key,
    milestone_arg,
    milestone_file,
    milestone_key,
    milestone_order,
    parse_task,
    preflight,
    short_key,
    split_frontmatter,
    task_priority,
)

SIGNOFF = "signoff"  # subject: the milestone key
RESERVE = "reserve"  # subject: week, five_hour or a card's short key; value: on or off (f8 D4)
QUEUE = "queue"  # subject: the ticket id, in later/ or blocked/ (F106 D3)
SET_ASIDE = "set_aside"  # subject: a blocked ticket's id, moved to later/ (F106 D3)
PLAN_MESSAGE = planner.PLAN_MESSAGE  # subject: the thread; value: {text, comments} (f6 D1)
SEND_BACK = "send_back"  # subject: <thread>/<proposal id>; value: {text, comments}
ACCEPT_ADR = "accept_adr"  # subject: the card; value: the ADR's number
APPROVE_PLAN = "approve_plan"  # subject: the thread; its plan and its merges (f6-12)
FIRST = "first"  # an approval's value: the card also goes first, in the fast lane (F224)
PLANT = "plant"  # value: {title, thoughts, area}; or subject: general/<seed id>, value: {area}
DROP_SEED = "drop_seed"  # subject: the idea card's short key; no value (f6-17)
PRIORITY = "priority"  # subject: a ticket in ready/ or later/, or a card; value: N (f6-18)
ARCHIVE = "archive"  # subject: the thread; value: on or off (the owner, 2026-10-07)
PAUSE = "pause"  # no subject, no value (f5-18); the runner's usage event while it holds too
RESUME = "resume"
DISMISS = "dismiss"  # subject: a refused request's id; no value (F31 D9)
REJECT = "reject"  # subject: <thread>/<proposal id>; no value: won't do (F31 D2)
# subject: an open plant's or plan_message's request id; value: its new words, or {cancel: true}
CHANGE = "change"  # (F14 D1)
# no subject; value: a JSON list, the open cards' short keys and bug ticket ids in the board's
REORDER = "reorder"  # order (F15 D3)
PROJECT_ORDER = "project_order"  # value: a JSON list of project names, first first (ADR 30)
_STATE_ONLY = (RESERVE, PAUSE, RESUME)  # they change state.json alone: a wait takes them
_APPROVALS = (ACCEPT_ADR, APPROVE_PLAN)  # they commit on main: the only way drafts reach it
_COMMITS = (SIGNOFF, QUEUE, SET_ASIDE, PLANT, DROP_SEED, PRIORITY, REORDER, REJECT, *_APPROVALS)
_PROPOSAL_ID_RE = re.compile(r"[\w.-]{1,64}")
_SWITCHED = ("on", "off")
QUEUED_FOR_THE_LEAD = "queued for the lead"
CARD_PLACE = "a ticket runs in its card's place: move the card on the board"  # F173 D3
_PLAIN = ("100644", "100755", "000000")  # a draft's mode: a file, or none (deleted)
_MAX_DIFF = 1000  # parse_task needs one; pre-flight doesn't read it
# The kinds that carry the owner's words (F31 D9). Their value may name, as `again`, the refused
# request Try again sent anew (F48 D2): the desk reads it, the runner doesn't.
WORDS = (PLANT, PLAN_MESSAGE, SEND_BACK)
_MAX_REQUEST_ID = 12
BY_YOU = "by you"  # the owner's own Archive; F31 D1's is planner.APPROVED
CANCELLED_BY_YOU = "cancelled by you"  # a plant or a message a change cancelled (F14 D2)
CANCELLED, CHANGED, TOO_LATE = "cancelled", "changed", "too late: already "  # a change's results
# Each one's result when it worked (F6 D1's table): any other is a refusal. A change that is an
# edit carries the owner's words too (f14-04), its own kind beside WORDS: no retry names one.
_WORKED = {
    PLANT: "planted ",
    PLAN_MESSAGE: QUEUED_FOR_THE_LEAD,
    SEND_BACK: QUEUED_FOR_THE_LEAD,
    CHANGE: CHANGED,
}
# What a change may change (F14 D3): each one's word for taken, and the keys its words are under
_CHANGEABLE = {PLANT: "planted", PLAN_MESSAGE: "sent"}
_WORD_KEYS = {PLANT: ("title", "thoughts", "text"), PLAN_MESSAGE: ("text", "comments")}
_CHANGE_VALUE = 'a change is JSON with the new words, or {"cancel": true}'

type _Row = sqlite3.Row | Mapping[str, object]


def _what(row: sqlite3.Row) -> str:
    """A request in a console line: ``signoff f4-always-on``, ``reserve week``; an idea's
    ``plant`` alone, its words being the owner's to read on the card."""
    if row["kind"] == PLANT and not row["subject"]:
        return PLANT
    if row["kind"] in (REORDER, PROJECT_ORDER):  # its value is the whole board, or every project
        return str(row["kind"])
    if row["kind"] == CHANGE:  # its value is the owner's words too
        return " ".join(filter(None, [CHANGE, row["subject"]]))
    return " ".join(str(part) for part in (row["kind"], row["subject"] or row["value"]) if part)


def _switch(
    conn: sqlite3.Connection,
    project_id: int,
    state: State,
    now: datetime,
    switch: object,
    value: object,
) -> str:
    """A reserve switch turned on (for 24 hours) or off; the items the owner acted on are
    answered: the switch's own lapse item and, when on, the tickets parked for it."""
    if switch not in loop.SWITCHES:
        return f"a reserve switch is {' or '.join(loop.SWITCHES)}, not {switch!r}"
    if value not in _SWITCHED:
        return f"a reserve switch is turned on or off, not {value!r}"
    name, on = str(switch), value == "on"
    parked = loop.FIVE_HOUR_KIND if name == loop.FIVE_HOUR else loop.RESERVE_KIND
    for row in metrics.open_owner_items(conn, project_id):
        kind, subject = row["kind"], row["subject"]
        lapsed = kind == loop.RESERVE_KIND and subject == name
        waiting = on and kind == parked and subject not in loop.SWITCHES
        if lapsed or waiting:
            metrics.resolve_owner_item(conn, row["id"], now.isoformat())
    return f"Claude's reserve: {loop.set_switch(state, name, on, now)}"


def _pause(conn: sqlite3.Connection, state: State, now: datetime, kind: str) -> str:
    """The owner pauses the factory, or resumes it (ADR 22 item 5): the pick takes nothing
    while ``state`` holds the pause. The hold is a ``pause`` usage event from when it took to
    the resume, open meanwhile: what clogged the line counts it as stopped for the owner."""
    since = state.owner_pause
    if kind == PAUSE:
        if since is not None:
            return f"already paused, since {datetime.fromisoformat(since).astimezone():%H:%M}"
        state.owner_pause = now.isoformat()
        metrics.add_usage_event(conn, loop.RUNNER_AGENT, state.owner_pause, PAUSE)
        return "paused: the runner finishes its job, then holds"
    if since is None:
        return "not paused"
    state.owner_pause = None
    metrics.add_usage_event(conn, loop.RUNNER_AGENT, since, PAUSE, resets_at=now.isoformat())
    return "resumed"


def _kept_card(repo: Path, thread: str) -> str | None:
    """The one card ``thread``'s was merged into, when it has none on main any more: read from
    the headings the merges wrote (F109 D2). None with a card on main, with no merge, or with
    two kept cards (a key planted twice before f109-02: the runner can't tell which is meant)."""
    if thread == planner.GENERAL:
        return None
    if milestone_file(repo, "cards", full_key(repo, thread)).is_file():
        return None
    kept = set()
    for path in (repo / ".softfield" / "cards").glob("*.md"):
        if thread in planner.merged_keys(path.read_text(encoding="utf-8")):
            try:
                kept.add(planner.thread_key(path.stem))
            except planner.PlannerError:  # a README
                continue
    return kept.pop() if len(kept) == 1 else None


def _plan_message(
    conn: sqlite3.Connection,
    project_id: int,
    now: datetime,
    row: sqlite3.Row,
    repo: Path | None = None,
) -> str:
    """The owner's message on a thread (ADR 20 items 3 and 9): kept on the thread with its
    comments by point, and queued as its own ``planner`` row (ADR 22 item 1); the thread's
    reply that waited for these answers is answered. Written on the thread of a card merged
    away (F107, 2026-10-13), it is the kept card's thread's: a job there could only answer
    that it has no card."""
    thread = planner.thread_key(row["subject"])
    text, comments = planner.message(_first_words(conn, project_id, thread, row))
    at = now.isoformat()
    sent_on = ""
    if repo is not None and (kept := _kept_card(repo, thread)) is not None:
        name, there = planner.thread_name(thread), planner.thread_name(kept)
        old = metrics.planner_thread(conn, project_id, thread, at)
        pointer = (
            f"Your message went to {there}'s thread, where {name} was merged: /planning/{kept}"
        )
        metrics.add_planner_message(conn, old["id"], "lead", at, pointer)
        if old["archived"] is None:
            metrics.set_thread_archived(conn, old["id"], at, planner.APPROVED)
        _resolve_items(conn, project_id, now, [thread])
        sent_on = f" on {there}, where {name} was merged"
        thread = kept
    found = metrics.planner_thread(conn, project_id, thread, at)
    thread_id = found["id"]
    if found["archived"] is not None:  # the owner's message opens an archived thread again
        metrics.set_thread_archived(conn, thread_id, None)
    said = [{"n": n, "comment": comment} for n, comment in comments.items()]
    metrics.add_planner_message(conn, thread_id, "owner", at, text, points=said or None)
    subject = planner.row_subject(thread, row["id"])
    reason = f"your message on {planner.thread_name(thread)}"
    metrics.queue_job(conn, project_id, planner.PLANNER, subject, reason, at)
    for item in metrics.open_owner_items(conn, project_id):
        if item["kind"] == planner.PLANNING and item["subject"] == thread:
            metrics.resolve_owner_item(conn, item["id"], at)
    return QUEUED_FOR_THE_LEAD + sent_on


def _first_words(
    conn: sqlite3.Connection, project_id: int, thread: str, row: sqlite3.Row
) -> object:
    """A message's value, or "Plan this card." for a card's first message sent with no words
    (the box says the lead reads the card too; 2026-10-15). Written back on the request, so the
    planner job, which reads it again, reads the same."""
    try:
        planner.message(row["value"])
        return row["value"]
    except planner.EmptyMessage:
        found = metrics.find_thread(conn, project_id, thread)
        if thread == planner.GENERAL or (
            found is not None and metrics.planner_messages(conn, found["id"])
        ):
            raise
    value = json.dumps({"text": planner.PLAN_THE_CARD, "comments": {}})
    metrics.change_request(conn, row["id"], value)
    return value


def _carry_on(
    conn: sqlite3.Connection, project_id: int, now: datetime, duplicate: str, kept: str, notes: str
) -> None:
    """f49-03 (the owner, 2026-10-13): after a merge the lead carries on on the kept card. The
    duplicate's notes are the kept thread's next message from the owner, queued for the lead
    as any message is, so the answer and the plan come there and no "go" is asked for."""
    said = f"From {planner.thread_name(duplicate)}, merged here:\n{notes}"
    value = json.dumps({"text": said, "comments": {}})
    at = now.isoformat()
    request_id = metrics.add_request(conn, project_id, PLAN_MESSAGE, kept, value, at)
    asked = metrics.find_request(conn, request_id)
    if asked is None:  # just written
        raise planner.PlannerError(f"the message for {planner.thread_name(kept)} is gone")
    metrics.finish_request(conn, request_id, at, _plan_message(conn, project_id, now, asked))


def _archive(
    conn: sqlite3.Connection, project_id: int, now: datetime, subject: object, value: object
) -> str:
    """Archive a thread, or open it again (the owner, 2026-10-07): an archived thread leaves the
    desk and its Needs-you item goes; the Planning page lists it under Archived."""
    thread = planner.thread_key(subject)
    name = planner.thread_name(thread)
    if value not in _SWITCHED:
        return f"archive is on or off, not {value!r}"
    found = metrics.find_thread(conn, project_id, thread)
    if found is None:
        return f"{name} has no thread to archive"
    at = now.isoformat()
    if value == "off":
        if found["archived"] is None:
            return f"{name} is not archived"
        metrics.set_thread_archived(conn, found["id"], None)
        return f"{name} is open again"
    if found["archived"] is not None:
        return f"{name} is archived already"
    metrics.set_thread_archived(conn, found["id"], at, BY_YOU)
    _resolve_items(conn, project_id, now, [thread])
    return f"archived {name}"


def _send_back(conn: sqlite3.Connection, project_id: int, now: datetime, row: sqlite3.Row) -> str:
    """The owner's comments on a proposal's key points (f6 D1): they become a ``plan_message``
    on its thread, finished at once, so the lead revises it on its next job."""
    thread, wanted = planner.proposal_of(row["subject"])
    text, comments = planner.message(row["value"])
    proposal = metrics.find_proposal(conn, project_id, thread, wanted)
    if proposal is None:
        raise planner.PlannerError(f"{planner.thread_name(thread)} has no proposal {wanted}")
    said = json.dumps({"text": planner.sent_back(proposal, text, comments), "comments": {}})
    at = now.isoformat()
    request_id = metrics.add_request(conn, project_id, PLAN_MESSAGE, thread, said, at)
    message = metrics.find_request(conn, request_id)
    if message is None:  # just written
        raise planner.PlannerError(f"the message for {planner.thread_name(thread)} is gone")
    result = _plan_message(conn, project_id, now, message)
    metrics.finish_request(conn, request_id, at, result)
    return result


# --- approvals: the card's drafts reach main only here (ADR 20 items 6 and 7, f6 D4) ---------


def _has_branch(git: Git, branch: str) -> bool:
    return bool(git.run("branch", "--list", branch).strip())


def _undo(git: Git, *made: Path | None) -> None:
    """Main as it was before an approval that failed: it was clean (``_waits``). ``made``, the
    files it wrote that main hadn't, which the reset leaves (untracked)."""
    git.run("reset", "-q", "--hard", "HEAD")
    Path(git.repo, git.run("rev-parse", "--git-path", "SQUASH_MSG").strip()).unlink(missing_ok=True)
    for path in made:
        if path is not None:
            path.unlink(missing_ok=True)


def _drafts(git: Git, branch: str) -> list[tuple[str, str]]:
    """Each path approving the plan branch changes, with its mode there (``planner.plan_range``)."""
    changes = []
    span = planner.plan_range(Path(git.repo), branch)
    for line in git.run("diff", "--raw", "--no-renames", *span).splitlines():
        meta, _, path = line.partition("\t")
        changes.append((meta.split()[1], path))
    return changes


_OUTSIDE = "outside docs/, .softfield/cards/, .softfield/adr/ and .softfield/tasks/later/"
_BUILDING = "building"  # a card's state while its tickets run (f5 D4): a plan keeps it
_PLANNING = "planning"  # a card's state while its first plan is drafted


def _why_not_blocked(path: str, mode: str, card: str, replan: bool, placed: set[str]) -> str:
    """Why the plan branch may not change a blocked ticket: a ``replan`` only removes its card's,
    written again in .softfield/tasks/ready/ or .softfield/tasks/later/ (ADR 29 item 3)."""
    if not planner.is_ready_ticket(path, card, planner.BLOCKED_DIR):
        return "another card's blocked ticket"
    if not replan:
        return "a blocked ticket only a replan brings back"
    if mode != "000000":
        return "a blocked ticket edited but left in .softfield/tasks/blocked/"
    return "" if Path(path).name in placed else "a blocked ticket removed and put nowhere"


def _why_not(
    path: str,
    mode: str,
    card: str,
    replan: bool,
    running: str | None,
    later: set[str],
    placed: set[str],
) -> str | None:
    """Why the plan branch may not change ``path``: a draft may change, and a ``replan`` its
    card's ready tickets too (f6-13), but not the running one, and one it removes only to set
    it aside in .softfield/tasks/later/; its card's blocked ones only to bring them back to one of
    the ``placed`` names, in ready/ or later/ (``_why_not_blocked``)."""
    if planner.is_draft(path):
        return None
    if path.startswith(planner.BLOCKED_DIR):
        return _why_not_blocked(path, mode, card, replan, placed) or None
    if not path.startswith(planner.READY_DIR):
        return _OUTSIDE
    if not planner.is_draft(path, card):
        return "another milestone's ticket"
    if not replan:
        return "a ready ticket only a replan changes"
    name = Path(path).name
    if name.removesuffix(".md") == running:
        return "the running ticket"
    if mode == "000000" and name not in later:
        return "a ready ticket removed, not set aside in .softfield/tasks/later/"
    return None


def _outside(
    branch: str, changes: list[tuple[str, str]], card: str, replan: bool, running: str | None
) -> str | None:
    """Why the branch can't be merged, if it changes more than it may (``_why_not``), or as
    other than plain files (a link would lead an edit out of them)."""
    later = {
        Path(path).name
        for mode, path in changes
        if path.startswith(f".softfield/tasks/{LATER}/") and mode != "000000"
    }
    placed = later | {
        Path(path).name
        for mode, path in changes
        if path.startswith(planner.READY_DIR) and mode != "000000"
    }
    stray: dict[str, list[str]] = {}
    for mode, path in changes:
        if (why := _why_not(path, mode, card, replan, running, later, placed)) is not None:
            stray.setdefault(why, []).append(path)
    if stray:  # the first reason found, with every path it holds for
        why, paths = next(iter(stray.items()))
        return f"{branch} changes {', '.join(paths)}, {why}: not approved"
    links = [path for mode, path in changes if mode not in _PLAIN]
    if links:
        return f"{branch} changes {', '.join(links)}, not a plain file: not approved"
    return None


_ADR_STATUS_RE = re.compile(r"^- \*\*Status:\*\*.*$", re.MULTILINE)  # as owner.decide_adr
_CARD_DOC_RE = re.compile(r"\.softfield/cards/[^/]+\.md")


def _owners_mark(path: str, before: str | None, after: str | None) -> bool:
    """Whether a draft sets what only the owner sets: an ADR's status (a new ADR may only be
    Proposed; ``accept_adr``), or a card's sign-off (``signoff``)."""
    if path.startswith(".softfield/adr/"):
        status = [_ADR_STATUS_RE.search(t or "") for t in (before, after)]
        was, now = (m[0] if m else None for m in status)
        return was != now and not (before is None and planner.is_proposed(after or ""))
    if _CARD_DOC_RE.fullmatch(path) and after is not None:
        done = [
            t is not None and milestone.card(Path(path).stem, t).state == "done"
            for t in (before, after)
        ]
        return done[1] and not done[0]
    return False


def _owners_marks(git: Git, branch: str, changes: list[tuple[str, str]]) -> str | None:
    """Why the branch can't be merged, if a draft sets what only the owner sets."""
    marked = []
    # the merged tree: a file main renamed is at its new name there, and not on the branch
    source = planner.merged_tree(Path(git.repo), branch) or branch
    for mode, path in changes:
        on_main = Path(git.repo, path)
        before = on_main.read_text(encoding="utf-8") if on_main.is_file() else None
        after = None if mode == "000000" else git.run("show", f"{source}:{path}")
        if _owners_mark(path, before, after):
            marked.append(path)
    if not marked:
        return None
    said = ", ".join(marked)
    return f"{branch} changes {said}, which only the owner sets (accept_adr, signoff): not approved"


def _proposed(repo: Path, number: int) -> bool:
    found = sorted((repo / ".softfield" / "adr").glob(f"{number:02d}-*.md"))
    return bool(found) and planner.is_proposed(found[0].read_text(encoding="utf-8"))


def _proposed_adrs(repo: Path, changes: list[tuple[str, str]]) -> list[int]:
    """The numbers of the ADRs in ``changes`` (the ones a branch drafted, new to main) that are
    still Proposed on the merged tree: a failed accept must not let their plan merge (F51 D3)."""
    found = []
    for mode, path in changes:
        name = re.fullmatch(r"\.softfield/adr/(\d+)-[^/]+\.md", path)
        file = repo / path
        if (
            name
            and mode != "000000"
            and file.is_file()
            and planner.is_proposed(file.read_text(encoding="utf-8"))
        ):
            found.append(int(name[1]))
    return sorted(found)


def ticket_problems(repo: Path, tickets: list[str]) -> list[str]:
    """Each merged ticket's pre-flight problems, and an ADR it relies on that is still
    Proposed, by ticket: one in .softfield/tasks/later/ to be queued, or a ready one a replan
    changed.
    """
    problems = []
    for rel in tickets:
        path = repo / rel
        try:
            task = parse_task(path, _MAX_DIFF)
        except (ValueError, yaml.YAMLError, OSError) as exc:  # TaskError, or one that won't read
            problems.append(f"{path.stem}: {exc}")
            continue
        found = preflight(task, repo)
        elsewhere = [
            p.parent.name
            for p in (repo / ".softfield" / "tasks").glob(f"*/{task.id}.md")
            if p.parent.name not in (LATER, path.parent.name)
        ]
        found += [f"already in .softfield/tasks/{folder}/" for folder in sorted(elsewhere)]
        adrs = planner.named_adrs(path.read_text(encoding="utf-8"))
        found += [
            f"relies on ADR {n}, still Proposed: accept it first"
            for n in sorted(adrs)
            if _proposed(repo, n)
        ]
        problems += [f"{task.id}: {problem}" for problem in found]
    return problems


def _merges(proposals: list[dict[str, object]]) -> list[tuple[str, str]]:
    """The ``merge`` proposals among the thread's open ones: each duplicate and the card it
    joins."""
    return [
        planner.merge_cards(proposal)
        for proposal in proposals
        if proposal.get("kind") == planner.MERGE and not proposal.get(planner.APPLIED)
    ]


class _Moved(NamedTuple):
    """What a merge moved: the duplicate's notes, what the kept thread's line says of it (the
    lead's summary, else its title), and its thread's export when the merge made the file."""

    notes: str
    said: str
    made: Path | None


def _summary(proposal: Mapping[str, object]) -> str | None:
    """A ``merge``'s summary of the duplicate's thread (F49 D3), when it gives one."""
    summary = proposal.get("summary")
    return summary.strip() or None if isinstance(summary, str) else None


def _merge(
    repo: Path,
    conn: sqlite3.Connection,
    project_id: int,
    now: datetime,
    duplicate: str,
    kept: str,
    by: str = "owner",
    summary: str | None = None,
) -> _Moved:
    """The duplicate's notes appended to the kept card's Notes, saying where they came from,
    then the lead's ``summary`` of its thread (F49 D3); its doc removed (``git rm``) and its
    thread exported to .softfield/planning/ (F49 D4), for the merge's one commit. A card with
    tickets isn't merged away: they would be left without their milestone."""
    names = (planner.thread_name(duplicate), planner.thread_name(kept))
    docs = [milestone_file(repo, "cards", full_key(repo, key)) for key in (duplicate, kept)]
    for name, path in zip(names, docs, strict=True):
        if not path.is_file():
            raise planner.PlannerError(f"{name} has no card in .softfield/cards/: not merged")
    tickets = sorted(
        p.relative_to(repo).as_posix() for p in repo.glob(f".softfield/tasks/*/{duplicate}-*.md")
    )
    if tickets:
        raise planner.PlannerError(
            f"{names[0]} has tickets ({', '.join(tickets)}): it can't be merged away"
        )
    text = docs[0].read_text(encoding="utf-8")
    title = milestone.milestone_doc(text).get("title") or duplicate
    source = (
        f"From {names[0]}: {title} (merged by the {by} on {now.astimezone().date().isoformat()})"
    )
    doc = docs[1].read_text(encoding="utf-8")
    notes = planner.card_notes(text)
    docs[1].write_text(planner.merged_card(doc, notes, source, summary=summary), "utf-8")
    Git(repo).run("rm", "-q", "--", docs[0].relative_to(repo).as_posix())
    made = _export(repo, conn, project_id, duplicate, docs[0].stem, title, into=names[1])
    return _Moved(notes, summary or title, made)


def _merged(
    conn: sqlite3.Connection,
    project_id: int,
    now: datetime,
    merges: list[tuple[str, str, str]],
    by: str = "owner",
) -> None:
    """Each merged card's thread points to the kept card's, and it leaves the board; the kept
    card's thread says what was merged (each merge's duplicate, kept card and what ``_merge``
    said of it), and its next job reads the duplicate's thread (F49 D4). When the owner
    approved the merge, the thread is archived and its item answered: they have seen it. When
    the lead merged on its own (F49 D1), the thread stays on the desk until the owner reads the
    reply: F63, F64 and F65's answers were archived unseen (2026-10-08)."""
    at = now.isoformat()
    for duplicate, kept, said in merges:
        metrics.remove_cards(conn, project_id, gone=duplicate)
        name, there = planner.thread_name(duplicate), planner.thread_name(kept)
        text = (
            f"The {by} merged {name} into {there}: its notes are on {there}'s card now. "
            f"The conversation goes on on {there}'s thread: /planning/{kept}"
        )
        thread_id = metrics.planner_thread(conn, project_id, duplicate, at)["id"]
        metrics.add_planner_message(conn, thread_id, "lead", at, text)
        if by == "owner":  # a message from the owner opens it again
            metrics.set_thread_archived(conn, thread_id, at, planner.APPROVED)
        kept_id = metrics.planner_thread(conn, project_id, kept, at)["id"]
        metrics.add_planner_message(conn, kept_id, "lead", at, f"Merged {name} here: {said}")
        unread = metrics.unread_merges(conn, kept_id)
        if duplicate not in unread:
            metrics.set_unread_merges(conn, kept_id, [*unread, duplicate])
    if by == "owner":
        _resolve_items(conn, project_id, now, [d for d, _, _ in merges])


def _resolve_items(
    conn: sqlite3.Connection, project_id: int, now: datetime, threads: list[str]
) -> None:
    """The threads' planning items answered: they leave Needs you."""
    for item in metrics.open_owner_items(conn, project_id):
        if item["kind"] == planner.PLANNING and item["subject"] in threads:
            metrics.resolve_owner_item(conn, item["id"], now.isoformat())


def auto_merge(
    repo: Path,
    conn: sqlite3.Connection,
    project_id: int,
    now: datetime,
    proposal: Mapping[str, object],
    thread: str | None = None,
) -> str | None:
    """F49 D1, D2: a planner reply's ``merge``, applied by the runner straight after the job,
    in one commit on main by the lead. None when it is applied (or its duplicate is gone
    already); otherwise why not, main unchanged, and the proposal waits for the owner. The
    lead then carries on on the kept card (f49-03), unless ``thread``, the reply's, is it."""
    try:
        duplicate, kept = planner.merge_cards(proposal)
    except planner.PlannerError as exc:
        return str(exc)
    if not milestone_file(repo, "cards", full_key(repo, duplicate)).is_file():
        return None
    git = Git(repo)
    name = planner.thread_name(duplicate)
    branch = planner.plan_branch(duplicate)
    if branch is not None and _has_branch(git, branch) and _drafts(git, branch):
        return f"{name} has drafts on {branch}"
    moved: _Moved | None = None
    try:
        moved = _merge(
            repo, conn, project_id, now, duplicate, kept, by="lead", summary=_summary(proposal)
        )
        message = f"{name} merged into {planner.thread_name(kept)} by the lead"
        git.commit_all(with_trailers(message, agent=loop.CLAUDE_HEADLESS_AGENT))
    except planner.PlannerError as exc:
        _undo(git, None if moved is None else moved.made)
        return str(exc)
    except Exception:
        _undo(git, None if moved is None else moved.made)
        raise
    _merged(conn, project_id, now, [(duplicate, kept, moved.said)], by="lead")
    if kept != thread:
        _carry_on(conn, project_id, now, duplicate, kept, moved.notes)
    return None


def _ready_changes(
    repo: Path, changes: list[tuple[str, str]]
) -> tuple[list[str], list[str], list[str]]:
    """A replan's ready tickets, by path, read before the merge while main is checked out: those it
    adds, changes, and sets aside (removed from .softfield/tasks/ready/: ``_outside`` has checked
    each
    goes to .softfield/tasks/later/)."""
    added: list[str] = []
    changed: list[str] = []
    aside: list[str] = []
    for mode, path in sorted(changes, key=lambda change: change[1]):
        if not path.startswith(planner.READY_DIR):
            continue
        if mode == "000000":
            aside.append(path)
        elif (repo / path).is_file():
            changed.append(path)
        else:
            added.append(path)
    return added, changed, aside


def _brought_back(repo: Path, changes: list[tuple[str, str]], card: str) -> dict[str, str]:
    """A replan's blocked tickets brought back (ADR 29 item 3), read while main is checked out:
    each of ``card``'s tickets in .softfield/tasks/blocked/ on main, by path, to the path the branch
    wrote it at again, in .softfield/tasks/ready/ or .softfield/tasks/later/."""
    placed = {
        Path(path).name: path
        for mode, path in changes
        if path.startswith((planner.READY_DIR, f".softfield/tasks/{LATER}/")) and mode != "000000"
    }
    brought = {}
    for found in sorted((repo / planner.BLOCKED_DIR).glob(f"{card}-*.md")):
        rel = found.relative_to(repo).as_posix()
        if planner.is_ready_ticket(rel, card, planner.BLOCKED_DIR) and found.name in placed:
            brought[rel] = placed[found.name]
    return brought


def _unblock(git: Git, brought: Mapping[str, str]) -> None:
    """After the plan branch's merge: each blocked copy's runner footers carried onto the ticket
    the replan wrote again, and the copy removed (``git rm``), whether the branch removed it or not:
    a planner job can't. Its failed work is kept as for a Try again (``loop.keep_blocked_work``)."""
    for blocked, back in brought.items():
        loop.keep_blocked_work(git, Path(blocked).stem)
        source = Path(git.repo, blocked)
        if not source.is_file():  # the branch removed it: main's copy holds the footers
            git.run("checkout", "-q", "HEAD", "--", blocked)
        carry_footers(source, Path(git.repo, back))
        git.run("rm", "-q", "--", blocked)


def _put_back(
    git: Git, branch: str, changes: list[tuple[str, str]], card: str, running: str | None
) -> dict[str, str]:
    """A replan's tickets that a Try again put back in .softfield/tasks/ready/ on main after the
    branch was drafted (f170 D2): each of ``card``'s tickets the branch adds in ready/ or later/
    that its base lacks while main holds the name in ready/, by main's path, to the branch's path.
    The running ticket is not one: its clash is refused as any other."""
    base = git.run("merge-base", loop.MAIN, branch).strip()
    found = {}
    removed = {path for mode, path in changes if mode == "000000"}
    for mode, path in changes:
        name = Path(path).name
        if mode == "000000" or not name.startswith(f"{card}-") or Path(name).stem == running:
            continue
        if not path.startswith((planner.READY_DIR, f".softfield/tasks/{LATER}/")):
            continue
        mine = f"{planner.READY_DIR}{name}"
        if mine in removed:
            continue
        if Path(git.repo, mine).is_file() and not git.run(
            "ls-tree", "--name-only", base, "--", path
        ):
            found[mine] = path
    return found


def _replace_put_back(git: Git, put_back: Mapping[str, str]) -> None:
    """After the squash: main's ready copy (read from ``HEAD``) gives its runner footers to the
    branch's ticket, which wins; a ticket the replan set aside in later/ loses the ready copy."""
    for mine, path in put_back.items():
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder, "main.md")
            source.write_text(git.run("show", f"HEAD:{mine}"), encoding="utf-8")
            carry_footers(source, Path(git.repo, path))
        if path != mine:
            git.run("rm", "-q", "-f", "--", mine)


def clash_words(branch: str) -> str:
    """What a plan branch that clashes with main asks of the owner (F139-F1): its planner job
    rebuilds it on main."""
    return f"{branch} clashes with {loop.MAIN}: press Refresh against main on its page"


def plan_clash(repo: Path, thread: str) -> str | None:
    """``clash_words`` when the card's plan branch exists and clashes with main, for its page."""
    try:
        branch = planner.plan_branch(planner.thread_key(thread))
    except planner.PlannerError:
        return None
    if branch is None or not _has_branch(Git(repo), branch):
        return None
    return None if planner.merged_tree(repo, branch) is not None else clash_words(branch)


def _clash_settles(git: Git, branch: str, put_back: Mapping[str, str]) -> bool:
    """Whether ``branch`` merges with main, or clashes only on tickets ``_settle_clash`` takes."""
    if planner.merged_tree(Path(git.repo), branch) is not None:
        return True
    # exit 1 on a clash: the tree's id, then each clashing path
    out = git.run(
        "merge-tree",
        "--write-tree",
        "--name-only",
        "--no-messages",
        loop.MAIN,
        branch,
        check=False,
    )
    clashing = set(out.splitlines()[1:]) - {""}
    return bool(clashing) and clashing <= set(put_back)


def _settle_clash(git: Git, put_back: Mapping[str, str]) -> bool:
    """A squash that stopped on conflicts: true when every one is a ticket in ``put_back``, now
    taken as the branch wrote it."""
    unmerged = git.run("diff", "--name-only", "--diff-filter=U").split()
    if not unmerged or not set(unmerged) <= set(put_back):
        return False
    for path in unmerged:
        git.run("checkout", "-q", "--theirs", "--", path)
        git.run("add", "--", path)
    return True


def _export(
    repo: Path,
    conn: sqlite3.Connection,
    project_id: int,
    thread: str,
    key: str,
    title: str | None,
    into: str | None = None,
) -> Path | None:
    """The card's thread written whole to ``.softfield/planning/<card's full key>.md`` (f20 D2), for
    the approval's commit, or the merge's ``into`` a card (F49 D4); the file, when this made it,
    for an undo to remove (``_undo`` restores one main had). None when the card has no thread."""
    found = metrics.find_thread(conn, project_id, thread)
    if found is None:
        return None
    messages = metrics.planner_messages(conn, found["id"])
    text = planner.export(planner.thread_name(thread), title, messages, into)
    path = repo / ".softfield" / "planning" / f"{key}.md"
    made = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path if made else None


def _approve_plan(
    repo: Path,
    conn: sqlite3.Connection,
    project_id: int,
    state: State,
    now: datetime,
    subject: object,
    value: object = None,
) -> str:
    """Merge a card's plan branch into main, queue its tickets and set the card ready, apply the
    thread's ``merge`` proposals, and write the card's thread to .softfield/planning/ (``_export``),
    in one commit; the branch then goes. Refused, with main as it was, when the branch changes more
    than drafts, clashes with main, a ticket fails pre-flight (the planner fixes it next), or a
    merge can't be applied. A thread with merges and no branch (the general one too) approves its
    merges alone.

    A ``replan`` (f6-13) may change its card's ready tickets too, but not the running one: a changed
    one is pre-flighted, one moved to .softfield/tasks/later/ stays there, and the owner's pause is
    lifted once it is applied. A building card keeps its state. It may bring back its card's
    blocked tickets too (ADR 29 item 3): the blocked copy goes (``_unblock``), its item answered.

    With the value ``first`` (F224), a plan whose card has a ticket in ready after the approval
    also goes first in the queue's list and in the fast lane, in the same commit; with none, or
    with merges alone, it is approved as plain. Any other value is refused before a change."""
    if value is not None and value != FIRST:
        return f"an approval is plain or {FIRST}, not {value!r}"
    thread = planner.thread_key(subject)
    branch = planner.plan_branch(thread)
    git = Git(repo)
    # Won't do holds (F31 D2): a merge the owner rejected is not applied with the plan
    rejected = _rejected(conn, project_id, thread)
    proposals = [
        proposal
        for proposal in metrics.latest_proposals(conn, project_id, thread)
        if proposal.get("id") not in rejected
    ]
    merges = _merges(proposals)
    summaries = {
        planner.merge_cards(p)[0]: _summary(p)
        for p in proposals
        if p.get("kind") == planner.MERGE and not p.get(planner.APPLIED)
    }
    # A duplicate whose card left the repo was merged (or dropped) already: approving its merge
    # again settles it rather than refusing it forever (F24, F45, F47 on 2026-10-08)
    gone = [d for d, _ in merges if not milestone_file(repo, "cards", full_key(repo, d)).is_file()]
    merges = [(d, k) for d, k in merges if d not in gone]
    already = [f"{planner.thread_name(d)} merged already" for d in gone]
    if gone and not merges and not (branch is not None and _has_branch(git, branch)):
        _resolve_items(conn, project_id, now, gone)
        return f"approved: {'; '.join(already)}"
    replan = any(proposal.get("kind") == planner.REPLAN for proposal in proposals)
    running = (state.in_flight or {}).get("ticket") or None
    if branch is None and not merges:
        raise planner.PlannerError("the general thread has no plan to approve")
    planned = branch is not None and _has_branch(git, branch)
    if branch is not None and not planned and not merges:
        raise planner.PlannerError(f"there is no {branch} to approve")
    name = planner.thread_name(thread)
    if planned and (into := dict(merges).get(thread)) is not None:
        there = planner.thread_name(into)
        return f"{branch} has drafts for {name}, which merges into {there}: send it back"
    joined = [f"{planner.thread_name(d)} into {planner.thread_name(k)}" for d, k in merges]
    tickets: list[str] = []
    added: list[str] = []
    changed: list[str] = []
    aside: list[str] = []
    brought: dict[str, str] = {}
    put_back: dict[str, str] = {}
    drafted: list[tuple[str, str]] = []
    if planned and branch is not None:
        # a note main merged into the card while the plan was drafted is kept with it, not refused
        if planner.merged_tree(repo, branch) is None and loop.catch_up_plan(git, branch, thread):
            git.checkout(loop.MAIN)
        changes = _drafts(git, branch)
        if replan:
            put_back = _put_back(git, branch, changes, thread, running)
        # a clash lists everything since the branch left main (F139-F1): its planner job
        # rebuilds it; one ``_settle_clash`` takes is approved (f170 D2)
        if not _clash_settles(git, branch, put_back):
            return clash_words(branch)
        if (refused := _outside(branch, changes, thread, replan, running)) is not None:
            return refused
        if (refused := _owners_marks(git, branch, changes)) is not None:
            return refused
        # an ADR already on main may stay Proposed: only a drafted one waits for its accept
        drafted = [(mode, path) for mode, path in changes if not (repo / path).exists()]
        added, changed, aside = _ready_changes(repo, changes)
        if replan:
            brought = _brought_back(repo, changes, thread)
        # a blocked ticket brought back to later/ stays there, set aside (ADR 29 item 3)
        aside += sorted(
            back
            for back in [*brought.values(), *put_back.values()]
            if not back.startswith(planner.READY_DIR)
        )
        set_aside = {Path(path).name for path in aside}
        tickets = sorted(
            path
            for mode, path in changes
            if path.startswith(f".softfield/tasks/{LATER}/")
            and path.endswith(".md")
            and mode != "000000"
            and Path(path).name not in set_aside
        )
        try:
            git.run("merge", "-q", "--squash", branch)
        except GitError:
            if not _settle_clash(git, put_back):
                _undo(git)
                return f"{branch} clashes with {loop.MAIN}: not approved"
    made: Path | None = None
    moved: dict[tuple[str, str], _Moved] = {}
    entering = False  # F222 D2: the card enters the line, last
    going: bool | None = False  # F224: the card goes first, marked (None: its mark won't take)
    nothing_first = False  # F224 D4: asked to go first with no ticket to run
    line: list[str] = []
    try:
        if planned:
            _replace_put_back(git, put_back)
            _unblock(git, brought)
            checked = sorted([*tickets, *added, *changed], key=lambda path: Path(path).name)
            if problems := ticket_problems(repo, checked):
                _undo(git)
                return "not approved: " + "; ".join(problems)
            if waiting := _proposed_adrs(repo, drafted):
                _undo(git)
                return "not approved: " + "; ".join(
                    f"relies on ADR {n}, still Proposed: accept it first" for n in waiting
                )
            doc = milestone_file(repo, "cards", full_key(repo, thread))
            if not doc.is_file():
                _undo(git)
                return f"{name} has no card in .softfield/cards/: not approved"
            text = doc.read_text(encoding="utf-8")
            # a plan of docs alone leaves a card with no ticket as it was (f196-02)
            state_was = milestone.card(doc.stem, text).state
            if state_was != _BUILDING and _has_tickets(git, None, thread):
                doc.write_text(planner.ready_card(text), encoding="utf-8")
                # F222 D2: a first plan's approval puts the card last in line
                entering = not replan and state_was in (planner.IDEA, _PLANNING)
            for rel in tickets:
                git.move(repo / rel, repo / ".softfield" / "tasks" / "ready" / Path(rel).name)
            if value == FIRST:
                going = _goes_first(repo, doc, thread)
                if going is None:
                    _undo(git)
                    return f"{name}'s header can't take the fast lane's mark: not approved"
                nothing_first = not going
        for d, kept in merges:
            summary = summaries.get(d)
            moved[d, kept] = _merge(repo, conn, project_id, now, d, kept, summary=summary)
        merged = [words.replace(" into ", " merged into ", 1) for words in joined]
        if planned:
            if going or entering:  # read after the squash: the tickets and the card are in it
                line = _first(repo, state, thread) if going else _last(repo, state, thread)
                (listed := order.order_path(repo)).write_text(order.order_text(line), "utf-8")
                git.run("add", "--", listed.relative_to(repo).as_posix())
            title = milestone.milestone_doc(doc.read_text(encoding="utf-8")).get("title")
            made = _export(repo, conn, project_id, thread, doc.stem, title)
            git.commit_all("; ".join([f"{name} plan approved by the owner", *merged]))
        else:
            git.commit_all(f"{'; '.join(merged)} by the owner")
    except Exception:
        _undo(git, made, *(m.made for m in moved.values()))  # untracked: the reset leaves them
        raise
    if going or entering:
        metrics.set_board_order(conn, project_id, line)
    if going:
        _free_parked(repo, conn, project_id, state, now)
    _merged(conn, project_id, now, [(d, k, m.said) for (d, k), m in moved.items()])
    _resolve_items(conn, project_id, now, gone)
    for blocked in brought:
        _answered_block(conn, project_id, now, Path(blocked).stem)
    for (duplicate, kept), m in moved.items():
        if kept != thread:  # there the lead is on the kept card already
            _carry_on(conn, project_id, now, duplicate, kept, m.notes)
    said = [f"merged {words}" for words in joined] + already
    if not planned:
        return f"approved: {'; '.join(said)}"
    git.run("branch", "-q", "-D", str(branch))
    queued = ", ".join(sorted(Path(t).stem for t in [*tickets, *added])) or "nothing"
    parts = [f"approved {branch}: queued {queued}"]
    parts += [
        f"{what} {', '.join(Path(t).stem for t in found)}"
        for what, found in (
            ("changed", changed),
            ("set aside", aside),
        )
        if found
    ]
    parts += [
        f"{Path(path).stem}: the lead's fix replaced the ticket Try again put back"
        for path in put_back.values()
    ]
    parts += said
    if replan and state.owner_pause is not None:  # applied while the line held: it goes on
        parts.append(_pause(conn, state, now, RESUME))
    if nothing_first:
        parts.append(f"{name} has no ticket in ready: nothing goes first")
    if entering and not going:
        parts.append(f"{name} goes last on the board")
    if going:
        parts.append(f"{name} goes first on the board, in the fast lane")
    return "; ".join(parts)


def _adr_number(value: object) -> int:
    text = str(value) if type(value) is int else value
    if not (isinstance(text, str) and text.isascii() and text.isdigit() and len(text) <= 4):
        raise planner.PlannerError(f"an ADR is named by its number, not {value!r}")
    return int(text)


def _adr_draft(git: Git, branch: str, number: int) -> str | None:
    """The branch's draft of ADR N: the file main doesn't have, else the one still Proposed. A
    branch that merged main also holds main's ADRs of that number (2026-11-02: the first in
    name order took an Accept meant for the draft)."""
    names = git.run("ls-tree", "--name-only", branch, ".softfield/adr/").splitlines()
    wanted = re.compile(rf"\.softfield/adr/{number:02d}-[^/]+\.md")
    found = [name for name in names if wanted.fullmatch(name)]
    new = [name for name in found if not Path(git.repo, name).is_file()]
    own = new or [n for n in found if planner.is_proposed(git.run("show", f"{branch}:{n}"))]
    if len(own) > 1:
        raise planner.PlannerError(f"{branch} has several ADR {number}s: {', '.join(own)}")
    return own[0] if own else None


def _adr_path(draft: str, number: int) -> str:
    """The draft's path under another number."""
    folder, name = draft.rsplit("/", 1)
    return f"{folder}/{number:02d}-{name.split('-', 1)[1]}"


def _free_adr_number(repo: Path) -> int:
    numbers = [int(p.name.split("-")[0]) for p in (repo / ".softfield" / "adr").glob("[0-9]*-*.md")]
    return max(numbers, default=0) + 1


def _renumber_draft(repo: Path, draft: str, target: str, old: int, new: int) -> None:
    """Move the checked out draft to its free number, its heading with it."""
    Git(repo).run("mv", draft, target)
    path = repo / target
    text = path.read_text(encoding="utf-8")
    path.write_text(re.sub(rf"^# ADR {old}\b", f"# ADR {new}", text, flags=re.M), encoding="utf-8")


def _renumber_mentions(git: Git, draft: str, target: str, old: int, new: int) -> None:
    """On the plan branch: what this branch alone drafted says the ADR's new number."""
    changed = git.run("diff", "--name-only", f"{loop.MAIN}...HEAD").splitlines()
    for name in changed:
        path = Path(git.repo, name)
        if not name.startswith((".softfield/cards/", ".softfield/tasks/")) or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        moved = re.sub(rf"\bADR {old}\b", f"ADR {new}", text).replace(
            Path(draft).name, Path(target).name
        )
        if moved != text:
            path.write_text(moved, encoding="utf-8")


def _has_tickets(git: Git, branch: str | None, thread: str) -> bool:
    """Whether the card has a ticket anywhere: on main in any folder, or drafted on its branch."""
    found = list(Path(git.repo, ".softfield", "tasks").glob(f"*/{thread}-*.md"))
    if found or branch is None or not _has_branch(git, branch):
        return bool(found)
    names = git.run("ls-tree", "-r", "--name-only", branch, ".softfield/tasks/").splitlines()
    return any(Path(name).name.startswith(f"{thread}-") for name in names)


def _ask_for_the_plan(
    conn: sqlite3.Connection, project_id: int, now: datetime, thread: str, adr: str
) -> None:
    """Accepting an ADR queues no work, so a card with an ADR and no tickets would wait for ever
    (F127, 2026-11-02): its thread's lead is asked for the plan."""
    said = json.dumps(
        {
            "text": f"(Sent by the runner.) {adr} is accepted and this card has no tickets yet."
            " Draft the plan and its tickets.",
            "comments": {},
        }
    )
    at = now.isoformat()
    request_id = metrics.add_request(conn, project_id, PLAN_MESSAGE, thread, said, at)
    message = metrics.find_request(conn, request_id)
    if message is None:  # just written
        raise planner.PlannerError(f"the message for {planner.thread_name(thread)} is gone")
    metrics.finish_request(conn, request_id, at, _plan_message(conn, project_id, now, message))


def _accept_adr(
    repo: Path,
    db: Path,
    conn: sqlite3.Connection,
    project_id: int,
    now: datetime,
    subject: object,
    value: object,
) -> str:
    """Merge ADR N's draft from the card's plan branch into main and accept it (``decide_adr``,
    one commit). The branch takes main's accepted copy, so approving the plan merges cleanly.
    An ADR already on main is accepted as it is. A number main already gave another ADR moves
    to the next free one, and a card left with no tickets asks its lead for the plan."""
    thread = planner.thread_key(subject)
    number = _adr_number(value)
    git = Git(repo)
    branch = planner.plan_branch(thread)
    draft = _adr_draft(git, branch, number) if branch and _has_branch(git, branch) else None
    if branch is None or draft is None:
        path = owner.decide_adr(repo, number, "Accepted", now.astimezone().date(), db=db)
        accepted = path.relative_to(repo).as_posix()
        result = f"accepted {accepted}"
    else:
        git.run("checkout", branch, "--", draft)
        new = number
        target = draft
        others = (repo / ".softfield" / "adr").glob(f"{number:02d}-*.md")
        if any(p.relative_to(repo).as_posix() != draft for p in others):
            new = _free_adr_number(repo)
            target = _adr_path(draft, new)
        try:
            if target != draft:
                _renumber_draft(repo, draft, target, number, new)
            owner.decide_adr(
                repo,
                new,
                "Accepted",
                now.astimezone().date(),
                db=db,
                path=repo / target,
                asked_as=number,
            )
        except Exception:
            _undo(git)
            raise
        git.checkout(branch)
        try:
            if target != draft:
                git.run("rm", "-q", draft)
                _renumber_mentions(git, draft, target, number, new)
            git.run("checkout", loop.MAIN, "--", target)
            message = f"runner: ADR {new} accepted on {loop.MAIN}"
            git.commit_all(with_trailers(message, agent="runner"), author=RUNNER_AUTHOR)
        finally:
            git.checkout(loop.MAIN)
        result = f"accepted {target}"
        if target != draft:
            result += f" (number {number} was taken, so it is ADR {new})"
    if thread != planner.GENERAL and not _has_tickets(git, branch, thread):
        _ask_for_the_plan(conn, project_id, now, thread, f"ADR {number}")
    return result


# --- planting: a seed card without Claude (ADR 20 item 8, f6 D5) -----------------------------


def _seed(conn: sqlite3.Connection, project_id: int, subject: str) -> tuple[str, str, str]:
    """An approved seed of the general thread's: its title, its key points as thoughts, and
    a note saying where it came from."""
    thread, wanted = planner.proposal_of(subject)
    if thread != planner.GENERAL:
        raise planner.PlannerError(
            f"only the general thread's seeds are planted, not {planner.thread_name(thread)}'s"
        )
    proposal = (
        metrics.find_proposal(conn, project_id, thread, wanted)
        if _PROPOSAL_ID_RE.fullmatch(wanted)
        else None
    )
    if proposal is None:
        raise planner.PlannerError(f"the general thread has no proposal {wanted}")
    kind = str(proposal.get("kind"))
    if kind != planner.SEED:
        article = "an" if kind[:1] in "aeiou" else "a"
        raise planner.PlannerError(f"proposal {wanted} is {article} {kind}, not a seed")
    title, thoughts = planner.seed_words(proposal)
    return title, thoughts, f"from the general thread's {wanted}"


def _plant(
    repo: Path, conn: sqlite3.Connection, project_id: int, now: datetime, row: sqlite3.Row
) -> str:
    """Write the idea's seed card and commit it alone (f6 D5): the next free key in its
    area's series, the slug from its title, the owner's words under Notes. No Claude, so it
    goes on at a limit. The board has the card at once. The value's ``again`` (F48 D2) is the
    desk's: nothing here reads it."""
    subject, value = row["subject"], row["value"]
    if subject:
        title, thoughts, source = _seed(conn, project_id, str(subject))
        area = planner.seed_area(value, planner.project_area(repo))
    else:
        title, thoughts, area = planner.planting(value, planner.project_area(repo))
        source = ""
    # A taken slug is no refusal (F48 D1): the same words again are planted already, and a
    # note that only starts like a card takes the slug's first free -2, -3, …
    slug = name = planner.slug(title)
    n = 1
    while (taken := planner.card_named(repo, name)) is not None:
        there = repo / ".softfield" / "cards" / f"{taken}.md"
        if planner.holds(there.read_text(encoding="utf-8"), title, thoughts):
            return f"planted already: {there.relative_to(repo).as_posix()}"
        n += 1
        name = f"{slug}-{n}"
    key = planner.next_key(repo, area, metrics.thread_cards(conn, project_id))
    full = f"{key}-{name}"
    note = " ".join(
        filter(None, [f"Planted by the owner on {now.astimezone().date().isoformat()}", source])
    )
    doc = planner.seed_card(key, title, thoughts, area, note + ".")
    found = milestone.card(full, doc)
    if (found.state, found.area) != (planner.IDEA, area) or milestone.milestone_after(doc):
        return f"an idea's title can't set its card: {title!r}"
    if milestone.milestone_doc(doc).get("title") != title:
        return f"an idea's title can't set its card: {title!r}"
    path = repo / ".softfield" / "cards" / f"{full}.md"
    rel = path.relative_to(repo).as_posix()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc, encoding="utf-8")
    git = Git(repo)
    try:
        git.run("add", "--", rel)
        message = with_trailers(f"{key.upper()} planted by the owner", agent="runner")
        git.run("commit", "-q", "--no-verify", "-m", message, "--author", RUNNER_AUTHOR, "--", rel)
    except GitError:
        git.run("reset", "-q", "--", rel, check=False)
        path.unlink(missing_ok=True)
        raise
    metrics.upsert_milestone(
        conn, project_id, full, title=title, state=found.state, priority=found.priority, area=area
    )
    if subject or not planner.asks(value):  # a seed the lead wrote, or one the owner sends later
        return f"planted {rel}"
    # "Plant and ask the lead": the owner's words are also the card thread's first message, so
    # the lead answers them (the owner, 2026-10-07 and 2026-10-08). It waits at a limit.
    said = json.dumps({"text": planner.plant_words(value, title, thoughts), "comments": {}})
    at = now.isoformat()
    request_id = metrics.add_request(conn, project_id, PLAN_MESSAGE, key, said, at)
    asked = metrics.find_request(conn, request_id)
    if asked is None:  # just written
        raise planner.PlannerError(f"the message for {planner.thread_name(key)} is gone")
    metrics.finish_request(conn, request_id, at, _plan_message(conn, project_id, now, asked))
    return f"planted {rel}, {QUEUED_FOR_THE_LEAD}"


def _drop_seed(
    repo: Path, conn: sqlite3.Connection, project_id: int, now: datetime, subject: object
) -> str:
    """Remove an idea card the owner no longer wants (f6-17): its doc ``git rm``ed in a commit
    of its own, its thread told, its pending planner rows closed, its reply's item answered,
    and the card off the board. Refused, main unchanged, for a card that isn't an idea or that
    a ticket in .softfield/tasks/ belongs to."""
    thread = planner.thread_key(subject)
    name = planner.thread_name(thread)
    if thread == planner.GENERAL:
        return f"{name} is not a seed: not removed"
    doc = milestone_file(repo, "cards", full_key(repo, thread))
    if not doc.is_file():
        return f"{name} has no card in .softfield/cards/: not removed"
    state = milestone.card(doc.stem, doc.read_text(encoding="utf-8")).state
    if state != planner.IDEA:
        return f"{name} is {state}, not an idea: not removed"
    tickets = sorted(
        p.relative_to(repo).as_posix() for p in repo.glob(f".softfield/tasks/*/{thread}-*.md")
    )
    if tickets:
        return f"{name} has tickets ({', '.join(tickets)}): not removed"
    rel = doc.relative_to(repo).as_posix()
    git = Git(repo)
    try:
        git.run("rm", "-q", "--", rel)
        message = with_trailers(f"{name} removed by the owner", agent="runner")
        git.run("commit", "-q", "--no-verify", "-m", message, "--author", RUNNER_AUTHOR, "--", rel)
    except GitError:
        git.run("reset", "-q", "--", rel, check=False)
        git.run("checkout", "-q", "--", rel, check=False)
        raise
    at = now.isoformat()
    if thread in metrics.thread_cards(conn, project_id):
        thread_id = metrics.planner_thread(conn, project_id, thread, at)["id"]
        text = f"Removed by the owner on {now.astimezone().date().isoformat()}."
        metrics.add_planner_message(conn, thread_id, "lead", at, text)
    for row in metrics.open_jobs(conn, project_id):
        if row["kind"] == planner.PLANNER and str(row["subject"]).rpartition("#")[0] == thread:
            metrics.finish_queued(conn, row["id"], at)
    for item in metrics.open_owner_items(conn, project_id):
        if item["kind"] == planner.PLANNING and item["subject"] == thread:
            metrics.resolve_owner_item(conn, item["id"], at)
    metrics.remove_cards(conn, project_id, gone=thread)
    return f"removed {rel}"


# --- the owner's words a request refused: on the desk until dismissed (F31 D9) ---------------


@dataclass(frozen=True)
class Words:
    """The owner's words in a request: an idea's title and thoughts, or a message (no title)
    with its comments by point."""

    title: str
    text: str


def _plant_words(data: object) -> Words | None:
    if not isinstance(data, dict):
        return None
    if isinstance(text := data.get("text"), str):  # one box (F31 D7)
        return Words(planner.heading(text), text.strip())
    title, thoughts = data.get("title") or "", data.get("thoughts") or ""
    if not (isinstance(title, str) and isinstance(thoughts, str)):
        return None
    return Words(title.strip(), thoughts.strip())


def _message_words(data: object) -> Words | None:
    if not isinstance(data, dict):
        return None
    text, comments = data.get("text") or "", data.get("comments") or {}
    if not (isinstance(text, str) and isinstance(comments, dict)):
        return None
    if not all(isinstance(comment, str) for comment in comments.values()):
        return None
    said = "\n".join(f"On point {n}: {c.strip()}" for n, c in comments.items() if c.strip())
    return Words("", "\n\n".join(filter(None, [text.strip(), said])))


def _edit_words(data: object) -> Words | None:
    """A ``change``'s new words (f14-04), read without the request it names: a plant's title
    and thoughts, or the text of a one-box note or a message, with its comments by point. A
    cancel carries none."""
    if data == {"cancel": True}:
        return Words("", "")
    if isinstance(data, dict) and "text" not in data and ("title" in data or "thoughts" in data):
        return _plant_words(data)
    return _message_words(data)


def owners_words(row: _Row) -> Words | None:
    """The owner's words a ``plant`` (not a seed's), ``plan_message`` or ``send_back`` carries,
    or a ``change`` that is an edit, read leniently: a value the runner couldn't read is still
    theirs, so it is kept whole. None for another kind, or with no words."""
    kind, value = row["kind"], row["value"]
    if kind not in (*WORDS, CHANGE) or not isinstance(value, str):
        return None
    if kind == PLANT and row["subject"]:
        return None
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        data = None
    if kind == CHANGE:
        words = _edit_words(data)
    else:
        words = _plant_words(data) if kind == PLANT else _message_words(data)
    if words is None:  # not as the dashboard writes it
        words = Words("", value.strip())
    return words if words.title or words.text else None


def refused(row: _Row) -> bool:
    """Whether the owner's words in a request didn't go through and wait on the desk: done
    with a result that isn't its kind's worked one, and not dismissed. One they cancelled
    themselves (F14) was not refused; an edit that came too late, or whose words the runner
    couldn't take, was (f14-04)."""
    if row["done"] is None or row["dismissed"] is not None or owners_words(row) is None:
        return False
    if row["result"] == CANCELLED_BY_YOU:
        return False
    return not str(row["result"] or "").startswith(_WORKED[str(row["kind"])])


def _dismiss(conn: sqlite3.Connection, project_id: int, now: datetime, subject: object) -> str:
    """The owner dismisses a refused request's words from the desk: when is kept on it, its
    words with it. Refused for a request that wasn't refused or carries no words."""
    wanted = subject if isinstance(subject, str) else ""
    if not (wanted.isascii() and wanted.isdigit() and len(wanted) <= _MAX_REQUEST_ID):
        return f"a dismiss names a refused request by its id, not {subject!r}"
    row = metrics.find_request(conn, int(wanted))
    if row is None or row["project_id"] != project_id:
        return f"there is no request {wanted}"
    if owners_words(row) is None:
        return f"request {wanted} carries no words of yours: nothing to dismiss"
    if row["dismissed"] is not None:
        return f"request {wanted} is dismissed already"
    if not refused(row):
        return f"request {wanted} wasn't refused: nothing to dismiss"
    metrics.dismiss_request(conn, row["id"], now.isoformat())
    return f"dismissed request {wanted}"


# --- change: a waiting plant or message edited or cancelled (F14 D1 to D4) --------------------


def _change(conn: sqlite3.Connection, project_id: int, now: datetime, row: sqlite3.Row) -> str:
    """The owner edits or cancels a plant or a message the runner hasn't taken (F14 D2): a
    cancel finishes it as cancelled by them; an edit replaces its words, what else it said
    (an idea's area, "ask the lead") kept, for the same pick to apply. Too late once it is
    done. Refused, nothing changed, for another kind of request or words its kind can't take."""
    subject = row["subject"]
    wanted = subject if isinstance(subject, str) else ""
    if not (wanted.isascii() and wanted.isdigit() and len(wanted) <= _MAX_REQUEST_ID):
        return f"a change names a waiting request by its id, not {subject!r}"
    target = metrics.find_request(conn, int(wanted))
    if target is None or target["project_id"] != project_id:
        return f"there is no request {wanted}"
    kind = str(target["kind"])
    if kind not in _CHANGEABLE:
        return f"request {wanted} is a {kind}: only a plant or a message is changed"
    if target["done"] is not None:
        was = CANCELLED if target["result"] == CANCELLED_BY_YOU else _CHANGEABLE[kind]
        return f"{TOO_LATE}{was}"
    try:
        data = json.loads(row["value"]) if isinstance(row["value"], str) else None
    except json.JSONDecodeError:
        data = None
    if not isinstance(data, dict):
        return _CHANGE_VALUE
    if "cancel" in data:
        if data != {"cancel": True}:
            return _CHANGE_VALUE
        metrics.finish_request(conn, target["id"], now.isoformat(), CANCELLED_BY_YOU)
        return CANCELLED
    if kind == PLANT and target["subject"]:
        return "a seed's words are the lead's: it can only be cancelled"
    keys = _WORD_KEYS[kind]
    if not any(key in data for key in keys):
        return _CHANGE_VALUE
    try:
        before = json.loads(target["value"]) if isinstance(target["value"], str) else None
    except json.JSONDecodeError:
        before = None
    kept = {k: v for k, v in before.items() if k not in keys} if isinstance(before, dict) else {}
    value = json.dumps({**kept, **data})
    if kind == PLANT:  # read as the pick will: words it would refuse change nothing
        planner.planting(value)
    else:
        planner.message(value)
    metrics.change_request(conn, target["id"], value)
    return CHANGED


# --- reprioritising: a ticket's or a card's priority, from the dashboard (f6-18) --------------

_TICKET_ID_RE = re.compile(r"(?:[a-z]+\d+|bug)-\d+(?:-[a-z0-9]+)*")  # not a card's key
_MAX_ID = 120
_MOVABLE = ("ready", LATER)  # the folders whose tickets the owner reorders
_TICKET_PRIORITY_RE = re.compile(r"^priority:.*$", re.MULTILINE)
_CARD_PRIORITY_RE = re.compile(r"(\*\*Priority:\*\*[ \t]*)\d+")
_CARD_STATE_RE = re.compile(r"\*\*State:\*\*[ \t]*[^·*\n]*[^·*\n \t]")


def _whole(value: object) -> int:
    text = str(value) if type(value) is int else value
    if not (isinstance(text, str) and text.isascii() and text.isdigit() and len(text) <= 6):
        raise planner.PlannerError(f"a priority is a whole number from 0, not {value!r}")
    return int(text)


def _commit_files(git: Git, texts: Mapping[Path, str], message: str) -> None:
    """Each path rewritten (or made) as its text, and they alone committed together, by the
    runner; as they were, or gone again, if the commit fails."""
    before = {path: path.read_text(encoding="utf-8") if path.exists() else None for path in texts}
    rels = [path.relative_to(git.repo).as_posix() for path in texts]
    for path, text in texts.items():
        path.write_text(text, encoding="utf-8")
    try:
        git.run("add", "--", *rels)
        message = with_trailers(message, agent="runner")
        git.run(
            "commit", "-q", "--no-verify", "-m", message, "--author", RUNNER_AUTHOR, "--", *rels
        )
    except GitError:
        git.run("reset", "-q", "--", *rels, check=False)
        for path, was in before.items():
            if was is None:
                path.unlink(missing_ok=True)
            else:
                path.write_text(was, encoding="utf-8")
        raise


def _commit_file(git: Git, path: Path, text: str, message: str) -> None:
    """``path`` rewritten as ``text`` and committed alone, by the runner; as it was if the
    commit fails."""
    _commit_files(git, {path: text}, message)


def _ticket_with(text: str, priority: int) -> str:
    """A ticket's text with its frontmatter's ``priority:`` set, added last when it has none."""
    head, sep, body = text.removeprefix("---\n").partition("\n---\n")
    if _TICKET_PRIORITY_RE.search(head):
        head = _TICKET_PRIORITY_RE.sub(f"priority: {priority}", head, count=1)
    else:
        head = f"{head}\npriority: {priority}"
    return f"---\n{head}{sep}{body}"


def _card_with(doc: str, priority: int) -> str:
    """A card's milestone doc with its header's Priority set: in place, else after its state,
    else on a line of its own under the title (as ``planner.ready_card``)."""
    section = re.search(r"^## ", doc, re.MULTILINE)
    end = section.start() if section else len(doc)
    header, body = doc[:end], doc[end:]
    said = f"**Priority:** {priority}"
    if _CARD_PRIORITY_RE.search(header):
        return _CARD_PRIORITY_RE.sub(lambda m: f"{m.group(1)}{priority}", header, count=1) + body
    if (state := _CARD_STATE_RE.search(header)) is not None:
        return f"{header[: state.end()]} · {said}{header[state.end() :]}{body}"
    title, _, rest = doc.partition("\n")
    return f"{title}\n\n> {said}\n{rest}"


def _ticket_priority(
    repo: Path,
    conn: sqlite3.Connection,
    project_id: int,
    state: State,
    ticket: str,
    priority: int,
) -> str:
    """A bug ticket's ``priority:``, for one in .softfield/tasks/ready/ or .softfield/tasks/later/
    that isn't running; the dashboard's row gets its new text at once. A feature ticket runs in
    its card's place, so its priority is refused (F173 D3)."""
    if ticket == (state.in_flight or {}).get("ticket"):
        return f"{ticket} is running: its priority stays"
    found = sorted((repo / ".softfield" / "tasks").glob(f"*/{ticket}.md"))
    path = next((p for p in found if p.parent.name in _MOVABLE), None)
    if path is None:
        if found:
            return f"{ticket} is in .softfield/tasks/{found[0].parent.name}/: its priority stays"
        return f"{ticket} is no ticket in .softfield/tasks/ready/ or .softfield/tasks/later/"
    task = parse_task(path, _MAX_DIFF)
    if task.milestone != BUGS:
        return CARD_PLACE
    was = task_priority(task, {})
    if was == priority:
        return f"priority of {ticket} is {priority} already"
    changed = _ticket_with(path.read_text(encoding="utf-8"), priority)
    if split_frontmatter(changed)[0].get("priority") != priority:
        return f"{ticket}'s frontmatter can't take a priority: not changed"
    _commit_file(Git(repo), path, changed, f"{ticket}: priority {was} → {priority}, by the owner")
    row = conn.execute(
        "SELECT 1 FROM tickets WHERE project_id = ? AND ticket = ?", (project_id, ticket)
    ).fetchone()
    if row is not None:  # else the next sync makes it
        metrics.upsert_ticket(conn, project_id, ticket, body=changed)
    return f"priority of {ticket} set to {priority}"


def _card_priority(
    repo: Path, conn: sqlite3.Connection, project_id: int, subject: object, priority: int
) -> str:
    """A card's header Priority, for a card not done; the board's row gets it at once."""
    thread = planner.thread_key(subject)
    name = planner.thread_name(thread)
    if thread == planner.GENERAL:
        return f"{name} has no priority"
    doc = milestone_file(repo, "cards", full_key(repo, thread))
    if not doc.is_file():
        return f"{name} has no card in .softfield/cards/: its priority stays"
    text = doc.read_text(encoding="utf-8")
    found = milestone.card(doc.stem, text)
    if found.state == "done":
        return f"{name} is done: its priority stays"
    if found.priority == priority:
        return f"priority of {name} is {priority} already"
    changed = _card_with(text, priority)
    if milestone.card(doc.stem, changed) != replace(found, priority=priority):
        return f"{name}'s header can't take a priority: not changed"
    message = f"{name}: priority {found.priority} → {priority}, by the owner"
    _commit_file(Git(repo), doc, changed, message)
    metrics.upsert_milestone(conn, project_id, milestone_key(doc.stem), priority=priority)
    return f"priority of {name} set to {priority}"


def _priority(
    repo: Path,
    conn: sqlite3.Connection,
    project_id: int,
    state: State,
    subject: object,
    value: object,
) -> str:
    """The owner reorders the work (f6-18): a bug ticket's ``priority:`` or a card's header
    Priority set, in a commit of its own, for the next pick to follow. Refused, main
    unchanged, for a ticket done or running, a card done, or a value that isn't a whole
    number from 0."""
    if not subject:
        return "a priority request names a ticket or a card"
    priority = _whole(value)
    if isinstance(subject, str) and len(subject) <= _MAX_ID and _TICKET_ID_RE.fullmatch(subject):
        return _ticket_priority(repo, conn, project_id, state, subject, priority)
    return _card_priority(repo, conn, project_id, subject, priority)


# --- reorder: the board's whole order, sent once (F15 D3, D5, D10) ----------------------------

REPLACED = "replaced by a later order"
_REORDER_VALUE = "a reorder is a JSON list of card keys and bug ticket ids, first in line first"
_SHORT_KEY_RE = re.compile(r"[a-z]+\d+")

type _Tie = tuple[tuple[str, int], str]  # what `run_order` sorts by after the priority


@dataclass(frozen=True)
class _Placed:
    """An open card or bug ticket on the board: the file its priority is in, the priority, and
    what orders it among equals."""

    path: Path
    text: str
    priority: int
    tie: _Tie
    card: milestone.Card | None = None  # a bug ticket has none


def _board(repo: Path, state: State) -> dict[str, _Placed]:
    """What a reorder may place, by the key the board sends: each card not done by its short
    key, and each bug ticket in .softfield/tasks/ready/ or .softfield/tasks/later/ that isn't
    running by
    its id."""
    found: dict[str, _Placed] = {}
    for path in sorted((repo / ".softfield" / "cards").glob("*.md")):
        try:
            key = milestone_key(path.stem)
        except TaskError:  # a README
            continue
        if key == BUGS:
            continue
        text = path.read_text(encoding="utf-8")
        card = milestone.card(path.stem, text)
        if card.state != "done":
            tie = (milestone_order(key), "")
            found.setdefault(short_key(key), _Placed(path, text, card.priority, tie, card))
    running = (state.in_flight or {}).get("ticket")
    for folder in _MOVABLE:
        for path in sorted((repo / ".softfield" / "tasks" / folder).glob("bug-*.md")):
            try:
                task = parse_task(path, _MAX_DIFF)
            except (ValueError, yaml.YAMLError, OSError):  # as ticket_problems: it won't read
                continue
            if task.milestone != BUGS or task.id == running:
                continue
            text = path.read_text(encoding="utf-8")
            tie = (milestone_order(BUGS), task.id)
            found.setdefault(task.id, _Placed(path, text, task_priority(task, {}), tie))
    return found


def _open_bug(repo: Path, key: str) -> bool:
    """Whether ``key`` is a bug ticket not done: the running one, or one blocked or escalated,
    keeps its line on the list though no reorder may place it."""
    if not (len(key) <= _MAX_ID and key.startswith("bug-") and _TICKET_ID_RE.fullmatch(key)):
        return False
    found = (repo / ".softfield" / "tasks").glob(f"*/{key}.md")
    return any(path.parent.name != "done" for path in found)


def _current(repo: Path, board: Mapping[str, _Placed]) -> list[str]:
    """The open cards and bugs in the order the pick takes them now: the queue's list without
    a line for one done or gone, then what it doesn't name by card number, then ticket id
    (ADR 45 item 2); with no list, by their numbers, as ``run_order`` sorts them."""
    listed = order.read_order(repo)
    if listed is None:
        return sorted(board, key=lambda key: (board[key].priority, board[key].tie))
    kept = [key for key in listed if key in board or _open_bug(repo, key)]
    named = set(kept)
    return kept + sorted((key for key in board if key not in named), key=lambda k: board[k].tie)


def _last(repo: Path, state: State, key: str) -> list[str]:
    """The queue's list with ``key`` strictly last (F222 D2): every open card and bug in the order
    the pick takes them (`_current`, so one the list didn't name too), then ``key``. Read from
    the working tree, so a card and tickets just merged are in it."""
    board = _board(repo, state)
    return [*(k for k in _current(repo, board) if k != key), key]


def _first(repo: Path, state: State, key: str) -> list[str]:
    """The queue's list with ``key`` strictly first (F224), every other open card and bug in the
    order the pick takes them (`_current`). Read from the working tree, as ``_last`` is."""
    board = _board(repo, state)
    return [key, *(k for k in _current(repo, board) if k != key)]


def _goes_first(repo: Path, doc: Path, thread: str) -> bool | None:
    """F224 D4: whether the approved card goes first. With a ticket in ready and a card a lane may
    hold (ready or building), its header is marked ``**Fast lane:** yes`` (once, ``_card_marked``)
    and True; with none, False and nothing written; None when the header can't take the mark."""
    ready = repo / ".softfield" / "tasks" / "ready"
    text = doc.read_text(encoding="utf-8")
    found = milestone.card(doc.stem, text)
    if found.state not in _RESERVE_CARD_STATES or not any(ready.glob(f"{thread}-*.md")):
        return False
    marked = _card_marked(text, True)
    if milestone.card(doc.stem, marked) != replace(found, reserve=True):
        return None
    doc.write_text(marked, encoding="utf-8")
    return True


def _bug_in_later(repo: Path, wanted: str) -> bool:
    """Whether ``wanted`` names a bug ticket in .softfield/tasks/later/ (what Queue then moves
    first, ``loop.move_to_ready``)."""
    path = repo / ".softfield" / "tasks" / LATER / f"{wanted}.md"
    return wanted.startswith("bug-") and path.is_file()


def _queue_last(
    repo: Path, conn: sqlite3.Connection, project_id: int, state: State, ticket: str
) -> None:
    """The bug Queue just moved to ready/ put last on the list, in a commit of the list alone."""
    line = _last(repo, state, ticket)
    _commit_file(Git(repo), order.order_path(repo), order.order_text(line), QUEUED_LAST)
    metrics.set_board_order(conn, project_id, line)


QUEUED_LAST = "the queued bug goes last on the board, by the owner"
MOVED = "the board's order, kept in .softfield/order.txt from now on (F222)"


def move_to_list(repo: Path) -> list[str]:
    """F222 D4, once per project, as the runner's pick applies the owner's requests (just
    before `apply_requests`, so a reorder reads the list): with no queue list and an open
    card, the list written in the order the pick takes the work today (`_current`), in a
    commit of that file alone, on main only. Nothing with no open card, and nothing again once
    there is a list. The caller copies the list to ``board_order``."""
    path = order.order_path(repo)
    if path.exists() or path.is_symlink():
        return []
    git = Git(repo)
    if git.current_branch() != loop.MAIN:
        return []  # the next apply on main moves it
    board = _board(repo, State())  # the running bug ticket keeps its place too
    if not any(placed.card is not None for placed in board.values()):
        return []
    keys = _current(repo, board)
    try:
        _commit_file(git, path, order.order_text(keys), MOVED)
    except GitError as exc:
        return [f"{MOVED}: not yet, {exc}"]
    return [f"{MOVED}: {len(keys)} cards and bugs in line"]


def _numbers(line: list[tuple[int, _Tie]]) -> list[int]:
    """The priorities that put ``line`` (each one's priority and what orders it among equals)
    in its order, with as many kept as can be: neighbours may share a number when the tie
    between them falls the right way. One that changes takes the lowest that fits after the
    one before it."""

    def lowest(before: tuple[int, _Tie] | None, tie: _Tie) -> int:
        if before is None:
            return 0
        return before[0] if before[1] < tie else before[0] + 1

    # kept[j]: how many keep their number up to j when j keeps its own, and the one kept
    # before it (-1: none)
    kept: dict[int, tuple[int, int]] = {-1: (0, -1)}
    for i in range(-1, len(line)):
        if i not in kept:  # no numbering lets it stay
            continue
        before = None if i < 0 else line[i]
        for j in range(i + 1, len(line)):
            priority, tie = line[j]
            least = lowest(before, tie)
            if priority >= least and kept[i][0] + 1 > kept.get(j, (0, -1))[0]:
                kept[j] = (kept[i][0] + 1, i)
            before = (least, tie)
    last = max(kept, key=lambda j: kept[j][0])
    stay = set()
    while last >= 0:
        stay.add(last)
        last = kept[last][1]
    numbers: list[int] = []
    before = None
    for j, (priority, tie) in enumerate(line):
        number = priority if j in stay else lowest(before, tie)
        numbers.append(number)
        before = (number, tie)
    return numbers


def _renumbered(key: str, placed: _Placed, priority: int) -> str:
    """The card's doc or the bug ticket with its new priority, checked as the ``priority``
    request checks it."""
    if placed.card is None:
        changed = _ticket_with(placed.text, priority)
        if split_frontmatter(changed)[0].get("priority") != priority:
            raise planner.PlannerError(f"{key}'s frontmatter can't take a priority: not reordered")
        return changed
    changed = _card_with(placed.text, priority)
    if milestone.card(placed.path.stem, changed) != replace(placed.card, priority=priority):
        raise planner.PlannerError(f"{key.upper()}'s header can't take a priority: not reordered")
    return changed


def _reorder(
    repo: Path, conn: sqlite3.Connection, project_id: int, state: State, value: object
) -> str:
    """The board's order, sent whole (F15 D3, D5): the queue's list (.softfield/order.txt,
    F222 D1) rewritten as the order sent, open keys only, and each card's header Priority and
    bug ticket's ``priority:`` set to agree with it (F222 D9, until f222-04), in one commit of
    the files that changed, and none when the order holds already. An open card or bug the
    order doesn't name comes after the ones it names, in the order it had. A key that is no
    open card or bug ticket (unknown, done, removed, running, general) is skipped and named.
    A card's tickets follow it: they have no ``priority:`` of their own (F173,
    ``task_priority``). Refused, main unchanged, for a value that isn't a JSON list of strings
    or holds a key twice."""
    try:
        keys = json.loads(value) if isinstance(value, str) else None
    except json.JSONDecodeError:
        keys = None
    if not isinstance(keys, list) or not all(isinstance(key, str) for key in keys):
        return _REORDER_VALUE
    seen: set[str] = set()
    for key in keys:
        if key in seen:
            return f"a reorder names each card once: {key[:_MAX_ID]} is there twice"
        seen.add(key)
    board = _board(repo, state)
    sent = [key for key in keys if key in board]
    placed = set(sent)
    written = sent + [key for key in _current(repo, board) if key not in placed]
    line = [key for key in written if key in board]
    numbers = _numbers([(board[key].priority, board[key].tie) for key in line])
    moved = {
        key: number
        for key, number in zip(line, numbers, strict=True)
        if number != board[key].priority
    }
    texts = {key: _renumbered(key, board[key], number) for key, number in moved.items()}
    files = {board[key].path: text for key, text in texts.items()}
    listed = order.order_path(repo)
    text = order.order_text(written)
    was = listed.read_text(encoding="utf-8") if listed.is_file() else None
    if text != was and (written or was is not None):  # F222 D1: the list, whole
        files[listed] = text
    if files:
        _commit_files(Git(repo), files, "the board's order, by the owner")
    metrics.set_board_order(conn, project_id, written)
    for key, number in moved.items():
        if board[key].card is not None:
            stem = board[key].path.stem
            metrics.upsert_milestone(conn, project_id, milestone_key(stem), priority=number)
            continue
        row = conn.execute(
            "SELECT 1 FROM tickets WHERE project_id = ? AND ticket = ?", (project_id, key)
        ).fetchone()
        if row is not None:  # else the next sync makes it
            metrics.upsert_ticket(conn, project_id, key, body=texts[key])
    result = f"reordered: {len(moved)} card{'' if len(moved) == 1 else 's'} changed"
    skipped = [
        key.upper() if _SHORT_KEY_RE.fullmatch(key) else key[:_MAX_ID]
        for key in keys
        if key not in board
    ]
    return f"{result}, skipped {', '.join(skipped)}" if skipped else result


# --- reserve on a card: it may use Claude's reserve (ADR 34, F172 D1, D2, D4) ------------------

_RESERVE_CARD_STATES = ("ready", _BUILDING)  # a card whose tickets may still run
_CARD_AREA_RE = re.compile(r"\*\*Area:\*\*[ \t]*[^·*\n]*[^·*\n \t]")
_CARD_PRIORITY_FIELD_RE = re.compile(r"\*\*Priority:\*\*[ \t]*\d+")
# the field with the " · " before it, up to the next field or the line's end
_CARD_RESERVE_FIELD_RE = re.compile(
    r"(?:[ \t]*·[ \t]*)?\*\*(?:Fast lane|Reserve):\*\*[^·*\n]*?(?=[ \t]*(?:·|\n|$))"
)
_MARK = "**Fast lane:** yes"


def _card_reserve_subject(subject: object) -> str | None:
    """A card's short key as a reserve request names it (``f142``), or None."""
    if isinstance(subject, str) and len(subject) <= _MAX_ID and _SHORT_KEY_RE.fullmatch(subject):
        return subject
    return None


def _card_marked(doc: str, on: bool) -> str:
    """A card's doc with its header's ``**Fast lane:** yes`` (F172 D1): written after its Area,
    else its Priority, else its State, else on a line of its own under the title; or removed
    with its `` · ``."""
    section = re.search(r"^## ", doc, re.MULTILINE)
    end = section.start() if section else len(doc)
    header, body = doc[:end], doc[end:]
    header = _CARD_RESERVE_FIELD_RE.sub("", header, count=1)
    if not on:
        return header + body
    for field in (_CARD_AREA_RE, _CARD_PRIORITY_FIELD_RE, _CARD_STATE_RE):
        if (found := field.search(header)) is not None:
            return f"{header[: found.end()]} · {_MARK}{header[found.end() :]}{body}"
    title, _, rest = doc.partition("\n")
    return f"{title}\n\n> {_MARK}\n{rest}"


def _free_parked(
    repo: Path, conn: sqlite3.Connection, project_id: int, state: State, now: datetime
) -> None:
    """F172 D4: the marked cards' tickets parked at either reserve, and those they wait for
    (``loop.reserve_cards``), go at the next pick; their Needs-you items are answered."""
    ready = []
    for path in sorted((repo / ".softfield" / "tasks" / "ready").glob("*.md")):
        try:
            ready.append(parse_task(path, _MAX_DIFF))
        except (ValueError, yaml.YAMLError, OSError):  # as ticket_problems: it won't read
            continue
    held = (loop.RESERVE_KIND, loop.FIVE_HOUR_KIND)
    freed = {
        task_id
        for task_id in loop.reserve_cards(repo, ready)
        if (state.parked.get(task_id) or {}).get("kind") in held
    }
    for task_id in freed:
        state.parked[task_id][loop.RETRY] = True
    for row in metrics.open_owner_items(conn, project_id):
        if row["kind"] in held and row["subject"] in freed:
            metrics.resolve_owner_item(conn, row["id"], now.isoformat())


def _card_reserve(
    repo: Path,
    conn: sqlite3.Connection,
    project_id: int,
    state: State,
    now: datetime,
    subject: object,
    value: object,
) -> str:
    """The owner puts a ready or building card in the fast lane (it may use Claude's reserve),
    or takes it out (F172 D2): its header's ``**Fast lane:** yes`` written or removed in a commit of
    its own. Marked, its tickets parked at either reserve go (``_free_parked``). Already so,
    nothing is committed."""
    key = _card_reserve_subject(subject)
    if key is None:
        return f"a reserve request names week, five_hour or a card, not {subject!r}"
    if value not in _SWITCHED:
        return f"a card's reserve is turned on or off, not {value!r}"
    on = value == "on"
    name = planner.thread_name(key)
    doc = milestone_file(repo, "cards", full_key(repo, key))
    if not doc.is_file():
        return f"{name} has no card in .softfield/cards/: not marked"
    text = doc.read_text(encoding="utf-8")
    found = milestone.card(doc.stem, text)
    if found.state not in _RESERVE_CARD_STATES:
        return f"{name} is {found.state}: only a planted card goes in the fast lane"
    said = f"{name} in the fast lane" if on else f"{name} out of the fast lane"
    if found.reserve == on:
        return f"{name} is {'' if on else 'not '}in the fast lane already"
    changed = _card_marked(text, on)
    if milestone.card(doc.stem, changed) != replace(found, reserve=on):
        return f"{name}'s header can't take the fast lane's mark: not changed"
    _commit_file(Git(repo), doc, changed, f"{said}, by the owner")
    if on:
        _free_parked(repo, conn, project_id, state, now)
    return said


def _reserve(
    repo: Path,
    conn: sqlite3.Connection,
    project_id: int,
    state: State,
    now: datetime,
    subject: object,
    value: object,
) -> str:
    """A reserve request: one of the owner's two switches (``_switch``), or a card's mark
    (``_card_reserve``, F172 D2)."""
    if subject in loop.SWITCHES:
        return _switch(conn, project_id, state, now, subject, value)
    return _card_reserve(repo, conn, project_id, state, now, subject, value)


def _commits(kind: str, subject: object) -> bool:
    """Whether a request commits: a reserve request on a card does, its switches don't."""
    return kind in _COMMITS or (kind == RESERVE and subject not in loop.SWITCHES)


def _waits(repo: Path, kind: str, subject: object = None) -> str | None:
    """Why a request that commits must wait, if it must: a queue commits on the branch it is
    on, and a sign-off or an approval commits the whole tree, so none goes anywhere but a main
    that is as clean as it needs to be. It stays open for a later command or pick."""
    if not _commits(kind, subject):
        return None
    git = Git(repo)
    if git.current_branch() != loop.MAIN:
        return f"waits for the repo to be on {loop.MAIN}"
    if kind == SIGNOFF and not git.is_clean():
        return f"waits for a clean {loop.MAIN}: a sign-off commits the whole tree"
    if kind in _APPROVALS and not git.is_clean():
        return f"waits for a clean {loop.MAIN}: an approval commits on it"
    return None


def _apply(
    repo: Path,
    db: Path,
    conn: sqlite3.Connection,
    project_id: int,
    state: State,
    now: datetime,
    row: sqlite3.Row,
) -> str:
    """One request, as its console command; its result, or the error that command prints."""
    kind, subject, value = row["kind"], row["subject"], row["value"]
    try:
        if kind == SIGNOFF:
            key = milestone_arg(repo, subject)
            owner.signoff(repo, key, now.astimezone().date(), db=db)
            return f"signed off {key}"
        if kind in (QUEUE, SET_ASIDE):
            if not subject:  # "" would match every ticket in the folder
                return f"a {kind} request names its ticket"
            if kind == QUEUE:
                from_later = _bug_in_later(repo, str(subject))
                said, ticket = "queued", loop.move_to_ready(repo, str(subject))
                if from_later:  # F222 D2: a queued bug goes last in line
                    _queue_last(repo, conn, project_id, state, ticket)
            else:
                said, ticket = "set aside", loop.set_aside(repo, str(subject))
            _answered_block(conn, project_id, now, ticket)
            return f"{said} {ticket}"
        if kind == RESERVE:
            return _reserve(repo, conn, project_id, state, now, subject, value)
        if kind in (PAUSE, RESUME):
            return _pause(conn, state, now, kind)
        if kind == PLAN_MESSAGE:
            return _plan_message(conn, project_id, now, row, repo)
        if kind == SEND_BACK:
            return _send_back(conn, project_id, now, row)
        if kind == APPROVE_PLAN:
            return _approve_plan(repo, conn, project_id, state, now, subject, value)
        if kind == ACCEPT_ADR:
            return _accept_adr(repo, db, conn, project_id, now, subject, value)
        if kind == PLANT:
            return _plant(repo, conn, project_id, now, row)
        if kind == DROP_SEED:
            return _drop_seed(repo, conn, project_id, now, subject)
        if kind == ARCHIVE:
            return _archive(conn, project_id, now, subject, value)
        if kind == PRIORITY:
            return _priority(repo, conn, project_id, state, subject, value)
        if kind == REORDER:
            return _reorder(repo, conn, project_id, state, value)
        if kind == PROJECT_ORDER:
            return _project_order(conn, value)
        if kind == DISMISS:
            return _dismiss(conn, project_id, now, subject)
        if kind == REJECT:
            return _reject(repo, conn, project_id, now, subject)
        if kind == CHANGE:
            return _change(conn, project_id, now, row)
    except (owner.OwnerError, loop.RunnerError, TaskError, planner.PlannerError) as exc:
        return str(exc)
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"
    return f"unknown request: {kind}"


_PROJECT_ORDER_VALUE = "a projects' order is a JSON list of project names, first first"


def _project_order(conn: sqlite3.Connection, value: str | None) -> str:
    """The Projects page's order, sent whole (ADR 30 item 6): the runner works in it from its
    next pick. Nothing in git changes, so it never waits for a clean main."""
    try:
        names = json.loads(value or "")
    except ValueError:
        return _PROJECT_ORDER_VALUE
    if not isinstance(names, list) or not names or not all(isinstance(n, str) for n in names):
        return _PROJECT_ORDER_VALUE
    unknown = metrics.set_project_order(conn, names)
    names_now = ", ".join(p.name for p in metrics.projects_in_order(conn))
    return f"the projects' order: {names_now}" + (
        f" (no project {', '.join(unknown)})" if unknown else ""
    )


def _lapse(
    repo: Path, conn: sqlite3.Connection, project_id: int, state: State, now: datetime
) -> list[str]:
    """The switches on for 24 hours turned off, each with a Needs-you item that asks to turn
    it on again (the owner, 2026-10-04), and a notification to the phone when it opens (ADR 31
    item 3): one that wasn't sent is a line too, starting ``notify.NOT_SENT``."""
    lines = []
    for switch in loop.lapse_switches(state, now):
        which = "the week's switch" if switch == loop.WEEK else "the 5-hour switch"
        text = (
            f"Claude's reserve: {which} went off after 24 hours."
            f" Turn “{loop.SWITCHES[switch]}” on again for 24 h?"
        )
        was_open = (loop.RESERVE_KIND, switch) in notify.open_items(conn, project_id)
        metrics.upsert_owner_item(
            conn,
            project_id,
            loop.RESERVE_KIND,
            switch,
            text=text,
            command=loop.switch_command(switch),
            created=now.isoformat(),
        )
        lines.append(text)
        if not was_open:
            message = notify.item_message(loop.RESERVE_KIND, switch)
            if (note := notify.to_owner(project_name(repo), *message)) is not None:
                lines.append(note)
    return lines


def _answered_block(conn: sqlite3.Connection, project_id: int, now: datetime, ticket: str) -> None:
    """A ticket out of blocked/, tried again or set aside: its item leaves the desk (F106 D3)."""
    for row in metrics.open_owner_items(conn, project_id):
        if row["kind"] == loop.BLOCKED_KIND and row["subject"] == ticket:
            metrics.resolve_owner_item(conn, row["id"], now.isoformat())


def _settle_waits(conn: sqlite3.Connection, project_id: int, state: State, now: datetime) -> None:
    """A ticket's reserve or 5-hour item answered once the ticket no longer waits for it: it
    ran, merged or went back (f8-03's stayed a day after it merged, 2026-10-06)."""
    for row in metrics.open_owner_items(conn, project_id):
        kind, subject = row["kind"], row["subject"]
        if kind not in (loop.RESERVE_KIND, loop.FIVE_HOUR_KIND) or subject in loop.SWITCHES:
            continue
        if (state.parked.get(subject) or {}).get("kind") != kind:
            metrics.resolve_owner_item(conn, row["id"], now.isoformat())


def _settles(row: sqlite3.Row, result: str) -> str | None:
    """The thread a worked approval is about (F31 D1): an ``approve_plan``'s or an
    ``accept_adr``'s card, or the general thread for a seed planted from it."""
    if not result.startswith(planner.WORKED):
        return None
    subject = str(row["subject"] or "")
    if row["kind"] in (APPROVE_PLAN, ACCEPT_ADR):
        try:
            return planner.thread_key(subject)
        except planner.PlannerError:
            return None
    if row["kind"] == PLANT and subject.startswith(f"{planner.GENERAL}/"):
        return planner.GENERAL
    if row["kind"] == REJECT:
        return subject.partition("/")[0]
    return None


def _settled(
    proposal: dict[str, object], card: str, asked: list[sqlite3.Row], known: set[str]
) -> bool:
    """Approved or rejected by the owner (or applied), or a merge one of whose cards has left
    main."""
    if planner.proposal_state(proposal, card, asked) in (planner.APPROVED, planner.REJECTED):
        return True
    if proposal.get("kind") != planner.MERGE:
        return False
    try:
        return not set(planner.merge_cards(proposal)) <= known
    except planner.PlannerError:
        return False


def _close_if_settled(
    repo: Path, conn: sqlite3.Connection, project_id: int, now: datetime, thread: str, result: str
) -> None:
    """F31 D1: once every proposal of the thread's latest set is settled (approved, or a merge
    whose card has left main), one lead line says so and the thread is archived as approved,
    its item resolved. A thread with no proposals, or one still open, stays."""
    found = metrics.find_thread(conn, project_id, thread)
    if found is None or found["archived"] is not None:
        return
    listed, asked = _latest(conn, project_id, found["id"])
    known = planner.cards(repo)
    if not listed or not all(_settled(p, thread, asked, known) for p in listed):
        return
    at = now.isoformat()
    states = [planner.proposal_state(p, thread, asked) for p in listed]
    if all(state == planner.REJECTED for state in states):  # nothing taken: won't do
        why, line = (
            planner.REJECTED,
            f"Rejected by the owner on {now.astimezone().date().isoformat()}: won't do",
        )
    else:  # a reject that closes a thread with approvals isn't called one
        said = "Settled" if result.startswith(planner.REJECTED) else "Approved"
        why, line = (
            planner.APPROVED,
            f"{said} by the owner on {now.astimezone().date().isoformat()}: {result}",
        )
    metrics.add_planner_message(conn, found["id"], "lead", at, line)
    metrics.set_thread_archived(conn, found["id"], at, why)
    _resolve_items(conn, project_id, now, [thread])


def _latest(
    conn: sqlite3.Connection, project_id: int, thread_id: int
) -> tuple[list[dict[str, object]], list[sqlite3.Row]]:
    """The proposals of the thread's latest lead message that lists some, and the owner's
    requests made since it."""
    lead = [
        m
        for m in metrics.planner_messages(conn, thread_id)
        if m["author"] == "lead" and m["proposals"] not in (None, "", "[]")
    ]
    if not lead:
        return [], []
    since = datetime.fromisoformat(lead[-1]["at"])
    listed = [p for p in json.loads(lead[-1]["proposals"]) if isinstance(p, dict) and p.get("id")]
    asked = [
        r
        for r in conn.execute(
            "SELECT * FROM owner_requests WHERE project_id = ? ORDER BY id", (project_id,)
        ).fetchall()
        if datetime.fromisoformat(r["created"]) >= since
    ]
    return listed, asked


def _rejected(conn: sqlite3.Connection, project_id: int, thread: str) -> set[object]:
    """The ids of the thread's latest proposals the owner rejected (F31 D2)."""
    found = metrics.find_thread(conn, project_id, thread)
    if found is None:
        return set()
    listed, asked = _latest(conn, project_id, found["id"])
    return {p["id"] for p in listed if planner.proposal_state(p, thread, asked) == planner.REJECTED}


def _reject(
    repo: Path, conn: sqlite3.Connection, project_id: int, now: datetime, subject: object
) -> str:
    """Won't do (F31 D2). A draft (an ADR, a mock-up, a plan or a replan): the card's plan branch
    goes, so every draft of the set is rejected with it, and a card with no ticket in
    .softfield/tasks/ that isn't building leaves main in a commit of its own (as ``_drop_seed``). A
    merge or a seed: nothing changes but that proposal. Refused, nothing changed, for a proposal not
    in the thread's latest reply, or one settled already."""
    wanted = subject if isinstance(subject, str) else ""
    card, _, pid = wanted.partition("/")
    if not card or not _PROPOSAL_ID_RE.fullmatch(pid):
        return f"a reject names <thread>/<proposal id>, not {subject!r}"
    thread = planner.thread_key(card)
    name = planner.thread_name(thread)
    found = metrics.find_thread(conn, project_id, thread)
    listed, asked = _latest(conn, project_id, found["id"]) if found is not None else ([], [])
    proposal = next((p for p in listed if p.get("id") == pid), None)
    if proposal is None:
        return f"{name}'s latest reply has no proposal {pid}: not rejected"
    mine = [r for r in asked if r["subject"] != wanted or r["kind"] != REJECT or r["done"]]
    if planner.proposal_state(proposal, thread, mine) in (planner.APPROVED, planner.REJECTED):
        return f"{pid} is settled already: not rejected"
    if proposal.get("kind") not in planner.DRAFTED:
        return f"rejected {pid}"
    git = Git(repo)
    branch = planner.plan_branch(thread)
    drafts = [str(p["id"]) for p in listed if p.get("kind") in planner.DRAFTED]
    said = f"{planner.REJECTED_DRAFTS}{branch} ({', '.join(drafts)})"
    if branch is not None and _has_branch(git, branch):
        git.run("branch", "-q", "-D", branch)
    doc = milestone_file(repo, "cards", full_key(repo, thread))
    if thread == planner.GENERAL or not doc.is_file():
        return said
    state = milestone.card(doc.stem, doc.read_text(encoding="utf-8")).state
    tickets = list(repo.glob(f".softfield/tasks/*/{thread}-*.md"))
    if tickets or state == _BUILDING:
        return said
    rel = doc.relative_to(repo).as_posix()
    try:
        git.run("rm", "-q", "--", rel)
        message = with_trailers(f"{name} rejected by the owner", agent="runner")
        git.run("commit", "-q", "--no-verify", "-m", message, "--author", RUNNER_AUTHOR, "--", rel)
    except GitError:
        git.run("reset", "-q", "--", rel, check=False)
        git.run("checkout", "-q", "--", rel, check=False)
        raise
    at = now.isoformat()
    for row in metrics.open_jobs(conn, project_id):
        if row["kind"] == planner.PLANNER and str(row["subject"]).rpartition("#")[0] == thread:
            metrics.finish_queued(conn, row["id"], at)
    metrics.remove_cards(conn, project_id, gone=thread)
    return f"{said}; {name} removed"


CLEAR_OUT = metrics.ONCE_STEPS[0]  # F55 D3: once per database
_SETTLED_CARDS = ("ready", "building", "needs sign-off", "done")


def _clear_out(repo: Path, conn: sqlite3.Connection, project_id: int, now: datetime) -> list[str]:
    """F55 D3, once: archive as approved each open card thread the owner settled before F31
    D1 did it: its card ready, building, needing sign-off or done, or gone from main; the
    lead's message its last; no proposal of its latest set open."""
    known = planner.cards(repo)
    asked = conn.execute(
        "SELECT * FROM owner_requests WHERE project_id = ? ORDER BY id", (project_id,)
    ).fetchall()
    archived = []
    for found in conn.execute(
        "SELECT * FROM planner_threads WHERE project_id = ? AND archived IS NULL AND card != ?",
        (project_id, planner.GENERAL),
    ).fetchall():
        card = str(found["card"])
        said = metrics.planner_messages(conn, found["id"])
        if not said or said[-1]["author"] != "lead":
            continue
        if card in known:
            doc = milestone_file(repo, "cards", full_key(repo, card))
            if (
                milestone.card(doc.stem, doc.read_text(encoding="utf-8")).state
                not in _SETTLED_CARDS
            ):
                continue
        lead = [m for m in said if m["author"] == "lead" and m["proposals"] not in (None, "", "[]")]
        if lead and card in known:  # a gone card's proposals have nothing left to ask
            since = datetime.fromisoformat(lead[-1]["at"])
            later = [r for r in asked if datetime.fromisoformat(r["created"]) >= since]
            listed = [p for p in json.loads(lead[-1]["proposals"]) if isinstance(p, dict)]
            if not all(_settled(p, card, later, known) for p in listed):
                continue
        metrics.set_thread_archived(conn, found["id"], now.isoformat(), planner.APPROVED)
        _resolve_items(conn, project_id, now, [card])
        archived.append(card)
    names = [planner.thread_name(c) for c in sorted(archived, key=lambda c: milestone_order(c))]
    return [f"archived the settled threads of {', '.join(names)} (F55)"] if names else []


def apply_requests(repo: Path, db: Path, now: datetime, state: State) -> list[str]:
    """Apply the project's open requests, the changes then the others, each oldest first, after
    turning off the switches whose 24 hours are over: one line per request done or left to
    wait, and per switch turned off.
    The switches are set on ``state``, for the caller to save. Nothing to do without the
    database or the project in it, and neither is made."""
    if not db.is_file():
        return []
    conn = metrics.open_db(db)
    try:
        project = metrics.find_project(conn, project_name(repo))
        if project is None:
            return []
        lines = _lapse(repo, conn, project, state, now)
        if metrics.once(conn, CLEAR_OUT, now.isoformat()):
            lines += _clear_out(repo, conn, project, now)
        _settle_waits(conn, project, state, now)
        owner.heal_signed_off(repo, conn, project)
        # Changes go first (F14 D2), and the others are read after them: a cancelled plant or
        # message is never applied, and an edited one goes with its new words
        for row in metrics.open_requests(conn, project):
            if row["kind"] != CHANGE:
                continue
            result = _apply(repo, db, conn, project, state, now, row)
            if metrics.finish_request(conn, row["id"], now.isoformat(), result):
                lines.append(f"{_what(row)}: {result}")
        waiting = metrics.open_requests(conn, project)
        # Only the latest order is the board's (F15 D4): an earlier one still open is replaced
        latest = max((row["id"] for row in waiting if row["kind"] == REORDER), default=None)
        for row in waiting:
            if (why := _waits(repo, row["kind"], row["subject"])) is not None:
                lines.append(f"{_what(row)}: {why}")
                continue
            if row["kind"] == REORDER and row["id"] != latest:
                result = REPLACED
            else:
                result = _apply(repo, db, conn, project, state, now, row)
            if metrics.finish_request(conn, row["id"], now.isoformat(), result):
                lines.append(f"{_what(row)}: {result}")
                if (thread := _settles(row, result)) is not None:
                    _close_if_settled(repo, conn, project, now, thread, result)
        return lines
    finally:
        conn.close()


def take_switches(
    conn: sqlite3.Connection, project_id: int, state: State, now: datetime
) -> list[str]:
    """The open requests that change ``state`` alone (a switch, a pause, a resume) applied
    and finished, for a wait that sleeps for the owner's 25% or their resume; the others wait
    for the pick, which may commit."""
    lines = []
    for row in metrics.open_requests(conn, project_id):
        kind = row["kind"]
        if kind not in _STATE_ONLY or _commits(kind, row["subject"]):  # a card's mark commits
            continue
        if kind == RESERVE:
            result = _switch(conn, project_id, state, now, row["subject"], row["value"])
        else:
            result = _pause(conn, state, now, kind)
        if metrics.finish_request(conn, row["id"], now.isoformat(), result):
            lines.append(f"{_what(row)}: {result}")
    return lines
