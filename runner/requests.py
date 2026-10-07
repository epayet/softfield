"""The owner's requests from the dashboard (ADR 18 item 2, f5 D1 and D2).

The dashboard only writes a request row. The runner applies it, with the code of its console
command: at each pick, while a wait for the owner's 25% or their resume sleeps
(`take_switches`), and at the start of every ``runner`` command while no run is live. Each
request is finished once, with its result or its error, and never retried. Git and tasks/
keep one writer, and the run state.json, whose reserve switches (ADR 22 item 4) and pause
(item 5) the requests set.
"""

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import yaml

from runner import loop, metrics, milestone, owner, planner
from runner.gitops import RUNNER_AUTHOR, Git, GitError, with_trailers
from runner.state import State
from runner.tasks import (
    LATER,
    TaskError,
    full_key,
    milestone_arg,
    milestone_file,
    parse_task,
    preflight,
)

SIGNOFF = "signoff"  # subject: the milestone key
RESERVE = "reserve"  # subject: week or five_hour; value: on or off (f8 D4)
QUEUE = "queue"  # subject: the ticket id
PLAN_MESSAGE = planner.PLAN_MESSAGE  # subject: the thread; value: {text, comments} (f6 D1)
SEND_BACK = "send_back"  # subject: <thread>/<proposal id>; value: {text, comments}
ACCEPT_ADR = "accept_adr"  # subject: the card; value: the ADR's number
APPROVE_PLAN = "approve_plan"  # subject: the thread; its plan and its merges (f6-12)
PLANT = "plant"  # value: {title, thoughts, area}; or subject: general/<seed id>, value: {area}
PAUSE = "pause"  # no subject, no value (f5-18); the runner's usage event while it holds too
RESUME = "resume"
_STATE_ONLY = (RESERVE, PAUSE, RESUME)  # they change state.json alone: a wait takes them
_APPROVALS = (ACCEPT_ADR, APPROVE_PLAN)  # they commit on main: the only way drafts reach it
_COMMITS = (SIGNOFF, QUEUE, PLANT, *_APPROVALS)
_PROPOSAL_ID_RE = re.compile(r"[\w.-]{1,64}")
_SWITCHED = ("on", "off")
QUEUED_FOR_THE_LEAD = "queued for the lead"
_PLAIN = ("100644", "100755", "000000")  # a draft's mode: a file, or none (deleted)
_MAX_DIFF = 1000  # parse_task needs one; pre-flight doesn't read it


def _what(row: sqlite3.Row) -> str:
    """A request in a console line: ``signoff f4-always-on``, ``reserve week``; an idea's
    ``plant`` alone, its words being the owner's to read on the card."""
    if row["kind"] == PLANT and not row["subject"]:
        return PLANT
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
            return f"already paused, since {datetime.fromisoformat(since):%H:%M}"
        state.owner_pause = now.isoformat()
        metrics.add_usage_event(conn, loop.RUNNER_AGENT, state.owner_pause, PAUSE)
        return "paused: the runner finishes its job, then holds"
    if since is None:
        return "not paused"
    state.owner_pause = None
    metrics.add_usage_event(conn, loop.RUNNER_AGENT, since, PAUSE, resets_at=now.isoformat())
    return "resumed"


def _plan_message(
    conn: sqlite3.Connection, project_id: int, now: datetime, row: sqlite3.Row
) -> str:
    """The owner's message on a thread (ADR 20 items 3 and 9): kept on the thread with its
    comments by point, and queued as its own ``planner`` row (ADR 22 item 1); the thread's
    reply that waited for these answers is answered."""
    thread = planner.thread_key(row["subject"])
    text, comments = planner.message(row["value"])
    at = now.isoformat()
    thread_id = metrics.planner_thread(conn, project_id, thread, at)["id"]
    said = [{"n": n, "comment": comment} for n, comment in comments.items()]
    metrics.add_planner_message(conn, thread_id, "owner", at, text, points=said or None)
    subject = planner.row_subject(thread, row["id"])
    reason = f"your message on {planner.thread_name(thread)}"
    metrics.queue_job(conn, project_id, planner.PLANNER, subject, reason, at)
    for item in metrics.open_owner_items(conn, project_id):
        if item["kind"] == planner.PLANNING and item["subject"] == thread:
            metrics.resolve_owner_item(conn, item["id"], at)
    return QUEUED_FOR_THE_LEAD


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


def _undo(git: Git) -> None:
    """Main as it was before an approval that failed: it was clean (``_waits``)."""
    git.run("reset", "-q", "--hard", "HEAD")
    Path(git.repo, git.run("rev-parse", "--git-path", "SQUASH_MSG").strip()).unlink(missing_ok=True)


def _drafts(git: Git, branch: str) -> list[tuple[str, str]]:
    """Each path the plan branch changed since it left main, with its mode there."""
    changes = []
    for line in git.run("diff", "--raw", "--no-renames", f"{loop.MAIN}...{branch}").splitlines():
        meta, _, path = line.partition("\t")
        changes.append((meta.split()[1], path))
    return changes


def _outside(branch: str, changes: list[tuple[str, str]]) -> str | None:
    """Why the branch can't be merged, if it changes more than drafts: docs/ and the tickets
    in tasks/later/, as plain files (a link would lead an edit out of them)."""
    stray = [path for _, path in changes if not planner.is_draft(path)]
    if stray:
        return f"{branch} changes {', '.join(stray)}, outside docs/ and tasks/later/: not approved"
    links = [path for mode, path in changes if mode not in _PLAIN]
    if links:
        return f"{branch} changes {', '.join(links)}, not a plain file: not approved"
    return None


def _proposed(repo: Path, number: int) -> bool:
    found = sorted((repo / "docs" / "adr").glob(f"{number:02d}-*.md"))
    return bool(found) and planner.is_proposed(found[0].read_text(encoding="utf-8"))


def _ticket_problems(repo: Path, tickets: list[str]) -> list[str]:
    """Each merged ticket's pre-flight problems, and an ADR it relies on that is still
    Proposed, by ticket."""
    problems = []
    for rel in tickets:
        path = repo / rel
        try:
            task = parse_task(path, _MAX_DIFF)
        except (ValueError, yaml.YAMLError) as exc:  # TaskError, or a file that won't read
            problems.append(f"{path.stem}: {exc}")
            continue
        found = preflight(task, repo)
        elsewhere = [
            p.parent.name
            for p in (repo / "tasks").glob(f"*/{task.id}.md")
            if p.parent.name != LATER
        ]
        found += [f"already in tasks/{folder}/" for folder in sorted(elsewhere)]
        adrs = planner.named_adrs(path.read_text(encoding="utf-8"))
        found += [
            f"relies on ADR {n}, still Proposed: accept it first"
            for n in sorted(adrs)
            if _proposed(repo, n)
        ]
        problems += [f"{task.id}: {problem}" for problem in found]
    return problems


def _merges(conn: sqlite3.Connection, project_id: int, thread: str) -> list[tuple[str, str]]:
    """The ``merge`` proposals of the thread's latest lead message that lists proposals (f6
    D6's open ones): each duplicate and the card it joins."""
    return [
        planner.merge_cards(proposal)
        for proposal in metrics.latest_proposals(conn, project_id, thread)
        if proposal.get("kind") == planner.MERGE
    ]


def _merge(repo: Path, now: datetime, duplicate: str, kept: str) -> None:
    """The duplicate's notes appended to the kept card's Notes, saying where they came from,
    and its doc removed (``git rm``), for the approval's one commit. A card with tickets isn't
    merged away: they would be left without their milestone."""
    names = (planner.thread_name(duplicate), planner.thread_name(kept))
    docs = [milestone_file(repo, "milestones", full_key(repo, key)) for key in (duplicate, kept)]
    for name, path in zip(names, docs, strict=True):
        if not path.is_file():
            raise planner.PlannerError(f"{name} has no card in docs/milestones/: not merged")
    tickets = sorted(p.relative_to(repo).as_posix() for p in repo.glob(f"tasks/*/{duplicate}-*.md"))
    if tickets:
        raise planner.PlannerError(
            f"{names[0]} has tickets ({', '.join(tickets)}): it can't be merged away"
        )
    text = docs[0].read_text(encoding="utf-8")
    title = milestone.milestone_doc(text).get("title") or duplicate
    source = f"From {names[0]}: {title} (merged by the owner on {now.date().isoformat()})"
    doc = docs[1].read_text(encoding="utf-8")
    docs[1].write_text(planner.merged_card(doc, planner.card_notes(text), source), "utf-8")
    Git(repo).run("rm", "-q", "--", docs[0].relative_to(repo).as_posix())


def _merged(
    conn: sqlite3.Connection, project_id: int, now: datetime, merges: list[tuple[str, str]]
) -> None:
    """Each merged card's thread points to the kept card's, and its reply's item is answered."""
    at = now.isoformat()
    for duplicate, kept in merges:
        name, there = planner.thread_name(duplicate), planner.thread_name(kept)
        text = (
            f"The owner merged {name} into {there}: its notes are on {there}'s card now. "
            f"The conversation goes on on {there}'s thread: /planning/{kept}"
        )
        thread_id = metrics.planner_thread(conn, project_id, duplicate, at)["id"]
        metrics.add_planner_message(conn, thread_id, "lead", at, text)
        for item in metrics.open_owner_items(conn, project_id):
            if item["kind"] == planner.PLANNING and item["subject"] == duplicate:
                metrics.resolve_owner_item(conn, item["id"], at)


def _approve_plan(
    repo: Path, conn: sqlite3.Connection, project_id: int, now: datetime, subject: object
) -> str:
    """Merge a card's plan branch into main, queue its tickets and set the card ready, and
    apply the thread's ``merge`` proposals, in one commit; the branch then goes. Refused, with
    main as it was, when the branch changes more than drafts, clashes with main, a ticket fails
    pre-flight (the planner fixes it next), or a merge can't be applied. A thread with merges
    and no branch (the general one too) approves its merges alone."""
    thread = planner.thread_key(subject)
    branch = planner.plan_branch(thread)
    git = Git(repo)
    merges = _merges(conn, project_id, thread)
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
    if planned and branch is not None:
        changes = _drafts(git, branch)
        if (refused := _outside(branch, changes)) is not None:
            return refused
        tickets = sorted(
            path
            for mode, path in changes
            if path.startswith(f"tasks/{LATER}/") and path.endswith(".md") and mode != "000000"
        )
        try:
            git.run("merge", "-q", "--squash", branch)
        except GitError:
            _undo(git)
            return f"{branch} clashes with {loop.MAIN}: not approved"
    try:
        if planned:
            if problems := _ticket_problems(repo, tickets):
                _undo(git)
                return "not approved: " + "; ".join(problems)
            doc = milestone_file(repo, "milestones", full_key(repo, thread))
            if not doc.is_file():
                _undo(git)
                return f"{name} has no card in docs/milestones/: not approved"
            doc.write_text(planner.ready_card(doc.read_text(encoding="utf-8")), encoding="utf-8")
            for rel in tickets:
                git.move(repo / rel, repo / "tasks" / "ready" / Path(rel).name)
        for duplicate, kept in merges:
            _merge(repo, now, duplicate, kept)
        merged = [words.replace(" into ", " merged into ", 1) for words in joined]
        if planned:
            git.commit_all("; ".join([f"{name} plan approved by the owner", *merged]))
        else:
            git.commit_all(f"{'; '.join(merged)} by the owner")
    except Exception:
        _undo(git)
        raise
    _merged(conn, project_id, now, merges)
    said = [f"merged {words}" for words in joined]
    if not planned:
        return f"approved: {'; '.join(said)}"
    git.run("branch", "-q", "-D", str(branch))
    queued = ", ".join(Path(t).stem for t in tickets) or "nothing"
    return "; ".join([f"approved {branch}: queued {queued}", *said])


def _adr_number(value: object) -> int:
    text = str(value) if type(value) is int else value
    if not (isinstance(text, str) and text.isascii() and text.isdigit() and len(text) <= 4):
        raise planner.PlannerError(f"an ADR is named by its number, not {value!r}")
    return int(text)


def _accept_adr(repo: Path, db: Path, now: datetime, subject: object, value: object) -> str:
    """Merge ADR N's draft from the card's plan branch into main and accept it (``decide_adr``,
    one commit). The branch takes main's accepted copy, so approving the plan merges cleanly.
    An ADR already on main is accepted as it is."""
    thread = planner.thread_key(subject)
    number = _adr_number(value)
    git = Git(repo)
    branch = planner.plan_branch(thread)
    draft = None
    if branch is not None and _has_branch(git, branch):
        names = git.run("ls-tree", "--name-only", branch, "docs/adr/").splitlines()
        wanted = re.compile(rf"docs/adr/{number:02d}-[^/]+\.md")
        draft = next((name for name in sorted(names) if wanted.fullmatch(name)), None)
    if branch is None or draft is None:
        path = owner.decide_adr(repo, number, "Accepted", now.date(), db=db)
        return f"accepted {path.relative_to(repo).as_posix()}"
    git.run("checkout", branch, "--", draft)
    try:
        owner.decide_adr(repo, number, "Accepted", now.date(), db=db)
    except Exception:
        _undo(git)
        raise
    git.checkout(branch)
    try:
        git.run("checkout", loop.MAIN, "--", draft)
        message = f"runner: ADR {number} accepted on {loop.MAIN}"
        git.commit_all(with_trailers(message, agent="runner"), author=RUNNER_AUTHOR)
    finally:
        git.checkout(loop.MAIN)
    return f"accepted {draft}"


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
    goes on at a limit. The board has the card at once."""
    subject, value = row["subject"], row["value"]
    if subject:
        title, thoughts, source = _seed(conn, project_id, str(subject))
        area = planner.seed_area(value)
    else:
        title, thoughts, area = planner.planting(value)
        source = ""
    name = planner.slug(title)
    if (taken := planner.card_named(repo, name)) is not None:
        return f"{name} is a card already: {taken}"
    key = planner.next_key(repo, area)
    full = f"{key}-{name}"
    note = " ".join(filter(None, [f"Planted by the owner on {now.date().isoformat()}", source]))
    doc = planner.seed_card(key, title, thoughts, area, note + ".")
    found = milestone.card(full, doc)
    if (found.state, found.area) != (planner.IDEA, area) or milestone.milestone_after(doc):
        return f"an idea's title can't set its card: {title!r}"
    if milestone.milestone_doc(doc).get("title") != title:
        return f"an idea's title can't set its card: {title!r}"
    path = repo / "docs" / "milestones" / f"{full}.md"
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
    return f"planted {rel}"


def _waits(repo: Path, kind: str) -> str | None:
    """Why a request that commits must wait, if it must: a queue commits on the branch it is
    on, and a sign-off or an approval commits the whole tree, so none goes anywhere but a main
    that is as clean as it needs to be. It stays open for a later command or pick."""
    if kind not in _COMMITS:
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
            owner.signoff(repo, key, now.date(), db=db)
            return f"signed off {key}"
        if kind == QUEUE:
            if not subject:  # "" would match every ticket in later/
                return "a queue request names its ticket"
            return f"queued {loop.move_to_ready(repo, str(subject))}"
        if kind == RESERVE:
            return _switch(conn, project_id, state, now, subject, value)
        if kind in (PAUSE, RESUME):
            return _pause(conn, state, now, kind)
        if kind == PLAN_MESSAGE:
            return _plan_message(conn, project_id, now, row)
        if kind == SEND_BACK:
            return _send_back(conn, project_id, now, row)
        if kind == APPROVE_PLAN:
            return _approve_plan(repo, conn, project_id, now, subject)
        if kind == ACCEPT_ADR:
            return _accept_adr(repo, db, now, subject, value)
        if kind == PLANT:
            return _plant(repo, conn, project_id, now, row)
    except (owner.OwnerError, loop.RunnerError, TaskError, planner.PlannerError) as exc:
        return str(exc)
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"
    return f"unknown request: {kind}"


def _lapse(conn: sqlite3.Connection, project_id: int, state: State, now: datetime) -> list[str]:
    """The switches on for 24 hours turned off, each with a Needs-you item that asks to turn
    it on again (the owner, 2026-10-04)."""
    lines = []
    for switch in loop.lapse_switches(state, now):
        which = "the week's switch" if switch == loop.WEEK else "the 5-hour switch"
        text = (
            f"Claude's reserve: {which} went off after 24 hours."
            f" Turn “{loop.SWITCHES[switch]}” on again for 24 h?"
        )
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
    return lines


def _settle_waits(conn: sqlite3.Connection, project_id: int, state: State, now: datetime) -> None:
    """A ticket's reserve or 5-hour item answered once the ticket no longer waits for it: it
    ran, merged or went back (f8-03's stayed a day after it merged, 2026-10-06)."""
    for row in metrics.open_owner_items(conn, project_id):
        kind, subject = row["kind"], row["subject"]
        if kind not in (loop.RESERVE_KIND, loop.FIVE_HOUR_KIND) or subject in loop.SWITCHES:
            continue
        if (state.parked.get(subject) or {}).get("kind") != kind:
            metrics.resolve_owner_item(conn, row["id"], now.isoformat())


def apply_requests(repo: Path, db: Path, now: datetime, state: State) -> list[str]:
    """Apply the project's open requests, oldest first, after turning off the switches whose
    24 hours are over: one line per request done or left to wait, and per switch turned off.
    The switches are set on ``state``, for the caller to save. Nothing to do without the
    database or the project in it, and neither is made."""
    if not db.is_file():
        return []
    conn = metrics.open_db(db)
    try:
        project = metrics.find_project(conn, repo.name)
        if project is None:
            return []
        lines = _lapse(conn, project, state, now)
        _settle_waits(conn, project, state, now)
        for row in metrics.open_requests(conn, project):
            if (why := _waits(repo, row["kind"])) is not None:
                lines.append(f"{_what(row)}: {why}")
                continue
            result = _apply(repo, db, conn, project, state, now, row)
            if metrics.finish_request(conn, row["id"], now.isoformat(), result):
                lines.append(f"{_what(row)}: {result}")
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
        if kind not in _STATE_ONLY:
            continue
        if kind == RESERVE:
            result = _switch(conn, project_id, state, now, row["subject"], row["value"])
        else:
            result = _pause(conn, state, now, kind)
        if metrics.finish_request(conn, row["id"], now.isoformat(), result):
            lines.append(f"{_what(row)}: {result}")
    return lines
