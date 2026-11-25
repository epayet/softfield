"""The planner's and the setup's jobs (ADR 20, f6, F122, ADR 48): a card's plan branch and its
drafts, the merges a reply applies, where the work stands, a card's name, and setting a project
up. `runner/loop.py` schedules them."""

import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path

from runner import config, dispatch, look, metrics, notify, order, planner, prompts, session
from runner import setup as project_setup
from runner.agents import ANY, GIT_READ_COMMANDS, JobSpec
from runner.config import Config
from runner.gitops import RUNNER_AUTHOR, Git, GitError, with_trailers
from runner.session import (
    CHECK_TICKETS,
    CLAUDE_HEADLESS_AGENT,
    MAIN,
    PLANNER,
    RUNNER_AGENT,
    SETUP,
    Parked,
    Session,
    _at,
    _has_branch,
    _record,
    _rel,
    first_agent,
    waiting_rows,
)
from runner.state import State
from runner.tasks import (
    BUGS,
    TaskError,
    blocked_ids,
    full_key,
    load_dir,
    milestone_file,
    milestone_key,
    milestone_order,
    short_key,
    stopped_ids,
    task_ids,
)
from runner.waits import _park_support, claude_hold

# --- plan branches (f6 D4) -------------------------------------------------------------------


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
    from runner.loop import _dispatch_tickets  # runner.loop imports this module

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
