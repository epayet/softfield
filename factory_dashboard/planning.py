"""The planning room's desk (f6-06, F6 D6): ``/planning`` is the owner's desk.

- Two tiles: the factory now, with when the next reply is expected (planner jobs go first, so a
  pending message is answered once the running job is done, D1), and the lead's 5-hour window.
- ``desk(conn, project)``: what waits for the owner, in five groups (D6, and F31 D9's "Didn't go
  through" first); the Overview's Needs you and the top bar's count reuse its items' words and
  links (f6-09).
- "Plant an idea": a ``plant`` request through ``POST /requests``, the dashboard's only write.
"""

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from factory_dashboard.app import Db, Now, Project, ago, render
from factory_dashboard.line import live_line
from factory_dashboard.overview import Running, agent_allowances, running_jobs
from runner import metrics
from runner.planner import (
    APPLIED,
    MERGE,
    PLANNER,
    PlannerError,
    cards,
    draft,
    is_proposed,
    merge_cards,
    merge_words,
    message,
    plan_changes,
    plant_words,
    thread_key,
)
from runner.requests import (
    ACCEPT_ADR,
    APPROVE_PLAN,
    DISMISS,
    PLANT,
    QUEUED_FOR_THE_LEAD,
    SEND_BACK,
    WORDS,
    Words,
    owners_words,
    refused,
)
from runner.tasks import short_key

router = APIRouter()

GENERAL = "general"
# A request's result when it worked (D1's table); any other result is a refusal.
# "approved: merged F12 into F10" too: a merge-only approval stayed open (2026-10-08)
WORKED = (QUEUED_FOR_THE_LEAD, "approved", "accepted ", "planted ")
_ADR_NUMBER = re.compile(r"docs/adr/(\d+)-")
_TYPICAL = 20  # finished jobs of the running one's role and agent that make its typical length


@dataclass(frozen=True)
class DeskItem:
    group: str
    title: str
    words: str
    link: str


@dataclass(frozen=True)
class RefusedItem(DeskItem):
    """The owner's words a request refused (F31 D9): in full, with the runner's reason, and
    where Try again puts them back."""

    id: int
    text: str  # an idea's thoughts, or the message with its comments by point
    note: str  # what Try again puts back in the Plant box (F31 D7); "" for a message
    again: str  # the thread whose reply box takes a message back; "" for an idea


@dataclass(frozen=True)
class DeskGroup:
    key: str
    name: str
    color: str  # a token from dashboard.css
    items: list[DeskItem]


def _when(at: str) -> datetime:
    return datetime.fromisoformat(at)


def _card_titles(conn: sqlite3.Connection, project_id: int) -> dict[str, str]:
    """Each card's title by its short key (``f7``), the key of a thread."""
    rows = conn.execute(
        "SELECT key, title FROM milestones WHERE project_id = ? ORDER BY id", (project_id,)
    ).fetchall()
    return {short_key(r["key"]): r["title"] or r["key"] for r in rows}


def _thread_title(card: str, titles: dict[str, str]) -> str:
    return "General" if card == GENERAL else titles.get(card, card)


def _answers_wanted(
    conn: sqlite3.Connection, project_id: int, titles: dict[str, str], now: datetime
) -> list[DeskItem]:
    """Threads whose last message is the lead's: a reply the owner hasn't answered. An
    archived thread waits for nothing."""
    rows = conn.execute(
        "SELECT t.card, m.at FROM planner_threads t"
        " JOIN planner_messages m ON m.id = ("
        "   SELECT max(id) FROM planner_messages WHERE thread_id = t.id)"
        " WHERE t.project_id = ? AND m.author = 'lead' AND t.archived IS NULL ORDER BY m.id",
        (project_id,),
    ).fetchall()
    return [
        DeskItem(
            "answers",
            _thread_title(r["card"], titles),
            f"the lead replied {ago(now - _when(r['at']))} ago",
            f"/planning/{r['card']}",
        )
        for r in rows
    ]


def _about(proposal: dict[str, object], card: str) -> list[tuple[str, str, str | None]]:
    """The requests about a proposal (D6): (kind, subject, value or None for any value)."""
    pid, kind = str(proposal.get("id")), proposal.get("kind")
    about: list[tuple[str, str, str | None]] = [(SEND_BACK, f"{card}/{pid}", None)]
    if kind == "adr":
        number = _ADR_NUMBER.match(str(proposal.get("path") or ""))
        if number:
            about.append((ACCEPT_ADR, card, str(int(number[1]))))
    elif kind in ("plan", "mockup", "replan", MERGE):
        about.append((APPROVE_PLAN, card, None))
    elif kind == "seed":
        about.append((PLANT, f"{GENERAL}/{pid}", None))
    return about


def _merge_words(proposal: dict[str, object]) -> str | None:
    """A ``merge`` proposal in words, ``merge F12 into F10``; None for another kind."""
    if proposal.get("kind") != MERGE:
        return None
    try:
        return merge_words(proposal)
    except PlannerError:
        return None


def _settled(requests: list[sqlite3.Row], about: list[tuple[str, str, str | None]]) -> bool:
    """An owner request about the proposal, pending or worked (a refusal leaves it open)."""
    for r in requests:
        for kind, subject, value in about:
            if r["kind"] != kind or r["subject"] != subject:
                continue
            if value is not None and str(r["value"] or "").strip() != value:
                continue
            if r["done"] is None or str(r["result"] or "").startswith(WORKED):
                return True
    return False


def _known_cards(repo: Path | None) -> set[str] | None:
    """Every card on main, or None when the checkout isn't here."""
    return None if repo is None else cards(repo)


def _gone_merge(proposal: dict[str, object], known: set[str] | None) -> bool:
    """A ``merge`` one of whose cards has left main: merged or dropped already, nothing to
    ask (2026-10-08: such merges filled the desk)."""
    if proposal.get("kind") != MERGE or known is None:
        return False
    try:
        return not set(merge_cards(proposal)) <= known
    except PlannerError:
        return False


def _open_proposals(
    conn: sqlite3.Connection, project_id: int, known: set[str] | None = None
) -> list[DeskItem]:
    """The proposals in each thread's latest lead message that lists some, still open, on
    threads not archived."""
    rows = conn.execute(
        "SELECT t.card, m.at, m.proposals FROM planner_threads t"
        " JOIN planner_messages m ON m.id = ("
        "   SELECT max(id) FROM planner_messages WHERE thread_id = t.id AND author = 'lead'"
        "   AND proposals IS NOT NULL AND proposals != '[]')"
        " WHERE t.project_id = ? AND t.archived IS NULL ORDER BY m.id",
        (project_id,),
    ).fetchall()
    requests = conn.execute(
        "SELECT * FROM owner_requests WHERE project_id = ? ORDER BY id", (project_id,)
    ).fetchall()
    items = []
    for row in rows:
        since = _when(row["at"])
        later = [r for r in requests if _when(r["created"]) > since]
        for proposal in json.loads(row["proposals"]):
            if not isinstance(proposal, dict) or not proposal.get("id"):
                continue
            if proposal.get(APPLIED) or _gone_merge(proposal, known):
                continue
            if _settled(later, _about(proposal, row["card"])):
                continue
            points = proposal.get("key_points")
            words = f"{len(points)} key points" if isinstance(points, list) and points else ""
            if merged := _merge_words(proposal):
                words = f"{merged} · {words}" if words else merged
            items.append(
                DeskItem(
                    "proposals",
                    str(proposal.get("title") or proposal["id"]),
                    words or str(proposal.get("kind") or ""),
                    f"/planning/{row['card']}/proposals/{proposal['id']}",
                )
            )
    return items


def _ripe(conn: sqlite3.Connection, project: str, now: datetime) -> list[DeskItem]:
    """Every ticket done and not signed off, as the line's field has them."""
    return [
        DeskItem(
            "ripe",
            m["title"] or m["key"],
            "every ticket merged · waits for your sign-off",
            f"/planning/{short_key(m['key'])}",
        )
        for m in live_line(conn, project, now)["field"]["ripe"]
    ]


def _seeds(conn: sqlite3.Connection, project_id: int) -> list[DeskItem]:
    """Idea cards no thread is about yet."""
    threads = {
        r["card"]
        for r in conn.execute(
            "SELECT card FROM planner_threads WHERE project_id = ?", (project_id,)
        ).fetchall()
    }
    rows = conn.execute(
        "SELECT key, title FROM milestones WHERE project_id = ? AND state = 'idea' ORDER BY id",
        (project_id,),
    ).fetchall()
    return [
        DeskItem("seeds", r["title"] or r["key"], "an idea, not asked about yet", f"/planning/{k}")
        for r in rows
        if (k := short_key(r["key"])) not in threads
    ]


def _message_thread(row: sqlite3.Row) -> str:
    """The thread a refused ``plan_message`` or ``send_back`` was for; the general thread when
    its subject names none."""
    subject = str(row["subject"] or "")
    if row["kind"] == SEND_BACK:
        subject = subject.partition("/")[0]
    try:
        return thread_key(subject)
    except PlannerError:
        return GENERAL


def _plant_note(value: object, words: Words) -> str:
    """A refused plant's words, whole, for the one Plant box: the note's text, or an older
    plant's title and thoughts."""
    try:
        return plant_words(value, words.title, words.text)
    except PlannerError:
        return "\n\n".join(filter(None, [words.title, words.text]))


def _refused(conn: sqlite3.Connection, project_id: int, titles: dict[str, str]) -> list[DeskItem]:
    """The owner's words the runner refused (F31 D9), until they dismiss them: a dismiss on
    its way takes one off at once."""
    rows = conn.execute(
        "SELECT * FROM owner_requests WHERE project_id = ? AND done IS NOT NULL"
        " AND dismissed IS NULL AND kind IN (?, ?, ?) ORDER BY id",
        (project_id, *WORDS),
    ).fetchall()
    dismissing = {
        str(r["subject"])
        for r in conn.execute(
            "SELECT subject FROM owner_requests WHERE project_id = ? AND kind = ? AND done IS NULL",
            (project_id, DISMISS),
        ).fetchall()
    }
    items: list[DeskItem] = []
    for r in rows:
        words = owners_words(r)
        if words is None or not refused(r) or str(r["id"]) in dismissing:
            continue
        if r["kind"] == PLANT:
            title, again = words.title or "Your idea", ""
        else:
            thread = _message_thread(r)
            title, again = f"Your message on {_thread_title(thread, titles)}", f"/planning/{thread}"
        reason = str(r["result"] or "")
        note = _plant_note(r["value"], words) if r["kind"] == PLANT else ""
        items.append(
            RefusedItem("refused", title, reason, "/planning", r["id"], words.text, note, again)
        )
    return items


def archived(conn: sqlite3.Connection, project: str, now: datetime) -> list[DeskItem]:
    """The archived threads, the most recently archived first (the owner, 2026-10-07). A
    message from the owner opens one again."""
    project_id = metrics.find_project(conn, project)
    if project_id is None:
        return []
    titles = _card_titles(conn, project_id)
    rows = conn.execute(
        "SELECT card, archived FROM planner_threads"
        " WHERE project_id = ? AND archived IS NOT NULL ORDER BY archived DESC, id DESC",
        (project_id,),
    ).fetchall()
    return [
        DeskItem(
            "archived",
            _thread_title(r["card"], titles),
            f"archived {ago(now - _when(r['archived']))} ago",
            f"/planning/{r['card']}",
        )
        for r in rows
    ]


def coming(conn: sqlite3.Connection, project: str, now: datetime) -> DeskGroup:
    """What is on its way: pending plants and threads waiting for the lead's reply."""
    project_id = metrics.find_project(conn, project)
    items: list[DeskItem] = []

    # Pending plant requests
    if project_id is not None:
        plant_rows = conn.execute(
            "SELECT * FROM owner_requests"
            " WHERE project_id = ? AND kind = 'plant' AND done IS NULL ORDER BY id",
            (project_id,),
        ).fetchall()
        for r in plant_rows:
            words = owners_words(r)  # leniently: the dashboard stores any value
            items.append(
                DeskItem(
                    "coming",
                    (words.title if words else "") or "Your idea",
                    "planting at the runner's next pick",
                    "",
                )
            )

    # Threads waiting for the lead: the owner's message is the latest and a planner row about
    # it is open, or an open plan_message request names it whatever is stored (the runner
    # stores that message, and makes the thread, only at its next pick). Each shows once.
    if project_id is not None:
        planned = {
            str(r["subject"] or "").split("#")[0]
            for r in metrics.open_jobs(conn, project_id)
            if r["kind"] == PLANNER
        }
        owners_last = conn.execute(
            "SELECT t.card FROM planner_threads t"
            " JOIN planner_messages m ON m.id = ("
            "   SELECT max(id) FROM planner_messages WHERE thread_id = t.id)"
            " WHERE t.project_id = ? AND m.author = 'owner' ORDER BY t.id",
            (project_id,),
        ).fetchall()
        asked = conn.execute(
            "SELECT subject FROM owner_requests"
            " WHERE project_id = ? AND kind = 'plan_message' AND done IS NULL ORDER BY id",
            (project_id,),
        ).fetchall()
        cards = [r["card"] for r in owners_last if r["card"] in planned]
        cards += [str(r["subject"]) for r in asked if r["subject"]]
        if cards:
            titles = _card_titles(conn, project_id)
            jobs = [j for j in running_jobs(conn, project, now) if j.live]
            next_reply = _next_reply(conn, project, jobs, True)
        for card in dict.fromkeys(cards):
            items.append(
                DeskItem(
                    "coming",
                    _thread_title(card, titles),
                    f"waiting for the lead · {next_reply}",
                    f"/planning/{card}",
                )
            )

    return DeskGroup("coming", "Coming", "--hazard", items)


def desk(conn: sqlite3.Connection, project: str, now: datetime) -> list[DeskGroup]:
    """What waits for the owner (D6), in five groups in this order, empty ones included: what
    didn't go through first (F31 D9)."""
    project_id = metrics.find_project(conn, project)
    if project_id is None:
        refusals: list[DeskItem] = []
        answers: list[DeskItem] = []
        proposals: list[DeskItem] = []
        ripe: list[DeskItem] = []
        seeds: list[DeskItem] = []
    else:
        titles = _card_titles(conn, project_id)
        refusals = _refused(conn, project_id, titles)
        answers = _answers_wanted(conn, project_id, titles, now)
        proposals = _open_proposals(conn, project_id, _known_cards(_repo(conn, project)))
        ripe = _ripe(conn, project, now)
        seeds = _seeds(conn, project_id)
    return [
        DeskGroup("refused", "Didn't go through", "--hazard", refusals),
        DeskGroup("answers", "Your answers wanted", "--hazard", answers),
        DeskGroup("proposals", "Proposals to review", "--opus", proposals),
        DeskGroup("ripe", "Finished, to talk through", "--qwen", ripe),
        DeskGroup("seeds", "Seeds, not asked about yet", "--ink-2", seeds),
    ]


# --- the tiles ----------------------------------------------------------------------------


def _typical(conn: sqlite3.Connection, project: str, job: Running) -> timedelta | None:
    """How long the last finished jobs of the running job's role and agent took, on average."""
    rows = conn.execute(
        "SELECT j.started, j.ended FROM jobs j JOIN runs r ON r.id = j.run_id"
        " JOIN projects p ON p.id = r.project_id"
        " WHERE p.name = ? AND j.role = ? AND j.agent = ? AND j.outcome != 'running'"
        " AND j.started IS NOT NULL AND j.ended IS NOT NULL ORDER BY j.id DESC LIMIT ?",
        (project, job.role, job.agent, _TYPICAL),
    ).fetchall()
    spans = [_when(r["ended"]) - _when(r["started"]) for r in rows]
    return sum(spans, timedelta()) / len(spans) if spans else None


def _what(job: Running) -> str:
    return job.ticket or job.role


def _next_reply(
    conn: sqlite3.Connection, project: str, jobs: list[Running], pending: bool
) -> str | None:
    """When the owner's pending message is answered: after the running job, planning going
    first (D1); ``None`` with nothing pending."""
    if not pending:
        return None
    if any(j.role == PLANNER for j in jobs):
        return "the lead is writing its reply now"
    if not jobs:
        return "at the factory's next pick"
    job = jobs[0]
    typical = _typical(conn, project, job)
    if typical is None:
        return f"after {_what(job)}"
    left = typical - job.elapsed
    if left < timedelta(minutes=1):
        return f"after {_what(job)}, any minute now"
    return f"after {_what(job)}, ~{ago(left)}"


def factory_now(conn: sqlite3.Connection, project: str, now: datetime) -> dict[str, object]:
    """The tile: the running job, and when the next reply is expected."""
    jobs = [j for j in running_jobs(conn, project, now) if j.live]
    project_id = metrics.find_project(conn, project)
    pending = project_id is not None and any(
        r["kind"] == PLANNER for r in metrics.open_jobs(conn, project_id)
    )
    working = [j for j in jobs if j.role != PLANNER]
    return {
        "running": working[0] if working else None,
        "next_reply": _next_reply(conn, project, jobs, pending),
    }


@router.get("/planning", response_class=HTMLResponse)
def planning(request: Request, conn: Db, project: Project, now: Now) -> HTMLResponse:
    """The owner's desk: the two tiles, what waits for the owner, and Plant an idea."""
    window = next(
        (a for a in agent_allowances(conn, now) if a.label == "Claude" and a.window == "five_hour"),
        None,
    )
    c = coming(conn, project, now)
    return render(
        request,
        conn,
        project,
        "planning.html",
        {
            "active": "/planning",
            "factory": factory_now(conn, project, now),
            "window": window,
            "coming": c,
            "groups": desk(conn, project, now),
            "archived": archived(conn, project, now),
        },
    )


# --- a thread (f6-07) ---------------------------------------------------------------------

# Each proposal kind's colour, a token from dashboard.css
_KIND_COLOR = {
    "adr": "--serious",
    "mockup": "--qwen",
    "plan": "--good",
    "replan": "--a7",
    "seed": "--ink-2",
}


@dataclass(frozen=True)
class Message:
    author: str
    at: str
    text: str
    points: list[dict[str, object]]  # a lead message's, or the owner's comments
    latest: bool  # the lead's latest points: the ones the owner comments on
    waiting: bool = False  # an open plan_message request not yet picked up


@dataclass(frozen=True)
class Proposal:
    kind: str
    title: str
    color: str
    answered: bool
    link: str


def _header(conn: sqlite3.Connection, project_id: int, thread: str) -> tuple[str, str, bool]:
    """The card's title, its status and area, and whether it is a seed (an idea card the
    owner may remove, f6-17), from its ``milestones`` row."""
    if thread == GENERAL:
        return "General", "", False
    rows = conn.execute(
        "SELECT key, title, status, area, state FROM milestones WHERE project_id = ? ORDER BY id",
        (project_id,),
    ).fetchall()
    for r in rows:
        if short_key(r["key"]) == thread:
            meta = " · ".join(x for x in (r["status"], r["area"]) if x)
            return r["title"] or r["key"], meta, r["state"] == "idea"
    return thread, "", False


def _messages(rows: list[sqlite3.Row]) -> list[Message]:
    latest = max((r["id"] for r in rows if r["author"] == "lead" and r["points"]), default=None)
    return [
        Message(
            r["author"],
            r["at"],
            r["text"],
            json.loads(r["points"]) if r["points"] else [],
            r["id"] == latest,
        )
        for r in rows
    ]


def _proposals(
    conn: sqlite3.Connection,
    project_id: int,
    thread: str,
    rows: list[sqlite3.Row],
    known: set[str] | None = None,
) -> list[Proposal]:
    """The proposals in the thread's latest lead message that lists some, open or answered as
    D6 defines open."""
    lead = [r for r in rows if r["author"] == "lead" and r["proposals"]]
    if not lead:
        return []
    since = _when(lead[-1]["at"])
    requests = [
        r
        for r in conn.execute(
            "SELECT * FROM owner_requests WHERE project_id = ? ORDER BY id", (project_id,)
        ).fetchall()
        if _when(r["created"]) > since
    ]
    return [
        Proposal(
            str(p.get("kind") or ""),
            str(p.get("title") or p["id"]),
            _KIND_COLOR.get(str(p.get("kind")), "--ink-2"),
            bool(p.get(APPLIED)) or _gone_merge(p, known) or _settled(requests, _about(p, thread)),
            f"/planning/{thread}/proposals/{p['id']}",
        )
        for p in json.loads(lead[-1]["proposals"])
        if isinstance(p, dict) and p.get("id")
    ]


_MAX_REQUEST_ID = 12


def _again(conn: sqlite3.Connection, project_id: int | None, thread: str, again: str) -> str:
    """The words of the refused message ``again`` names, for the thread's reply box; "" for
    anything else."""
    if project_id is None or not (again.isascii() and again.isdigit()):
        return ""
    if len(again) > _MAX_REQUEST_ID:
        return ""
    row = metrics.find_request(conn, int(again))
    if row is None or row["project_id"] != project_id or row["kind"] == PLANT:
        return ""
    words = owners_words(row)
    if words is None or not refused(row) or _message_thread(row) != thread:
        return ""
    return words.text


@router.get("/planning/{thread}", response_class=HTMLResponse)
def thread_page(
    request: Request, thread: str, conn: Db, project: Project, now: Now, again: str = ""
) -> HTMLResponse:
    """A card's thread: its messages and the lead's points, Send, and its proposals. ``again``
    names a refused message of the thread's (F31 D9): its words wait in the reply box."""
    project_id = metrics.find_project(conn, project)
    title, meta, seed = thread, "", False
    messages: list[Message] = []
    proposals: list[Proposal] = []
    pending = False
    archived_at: str | None = None
    archiving: str | None = None  # "on" or "off": an archive request the runner hasn't done
    if project_id is not None:
        title, meta, seed = _header(conn, project_id, thread)
        found = metrics.find_thread(conn, project_id, thread)
        archived_at = found["archived"] if found is not None else None
        asked = conn.execute(
            "SELECT value FROM owner_requests WHERE project_id = ? AND kind = 'archive'"
            " AND subject = ? AND done IS NULL ORDER BY id DESC LIMIT 1",
            (project_id, thread),
        ).fetchone()
        archiving = asked["value"] if asked is not None else None
        rows = conn.execute(
            "SELECT m.* FROM planner_messages m JOIN planner_threads t ON t.id = m.thread_id"
            " WHERE t.project_id = ? AND t.card = ? ORDER BY m.id",
            (project_id, thread),
        ).fetchall()
        messages = _messages(rows)
        proposals = _proposals(conn, project_id, thread, rows, _known_cards(_repo(conn, project)))
        pending = any(
            r["kind"] == PLANNER and str(r["subject"] or "").startswith(f"{thread}#")
            for r in metrics.open_jobs(conn, project_id)
        )
        # Append open plan_message requests as waiting messages
        for req in conn.execute(
            "SELECT * FROM owner_requests"
            " WHERE project_id = ? AND kind = 'plan_message'"
            " AND subject = ? AND done IS NULL ORDER BY id",
            (project_id, thread),
        ).fetchall():
            pending = True
            try:  # as the runner will read it; one it will refuse shows empty
                text, comments = message(req["value"])
            except PlannerError:
                text, comments = "", {}
            points = [{"n": n, "comment": c} for n, c in comments.items()]
            messages.append(Message("owner", req["created"], text, points, False, waiting=True))
    jobs = [j for j in running_jobs(conn, project, now) if j.live]
    return render(
        request,
        conn,
        project,
        "thread.html",
        {
            "again": _again(conn, project_id, thread, again),
            "active": "/planning",
            "thread": thread,
            "card_title": title,
            "card_meta": meta,
            "seed": seed,
            "has_thread": bool(messages),
            "archived_at": archived_at,
            "archiving": archiving,
            "messages": messages,
            "points": next((len(m.points) for m in messages if m.latest), 0),
            "proposals": proposals,
            "next_reply": _next_reply(conn, project, jobs, pending),
        },
    )


# --- proposal review (f6-08) ----------------------------------------------------------------

_MOCKUP_RE = re.compile(r"docs/milestones/[^/]+-mockup/[^/].*")


def _repo(conn: sqlite3.Connection, project: str) -> Path | None:
    """The project's checkout; None when ``projects.repo`` isn't a folder here (a URL)."""
    row = conn.execute("SELECT repo FROM projects WHERE name = ?", (project,)).fetchone()
    repo = Path(row["repo"]) if row and row["repo"] else None
    return repo if repo and repo.is_dir() else None


def _adr_waits(repo: Path | None, proposals: list[dict[str, object]]) -> bool:
    """Whether the card has an ``adr`` proposal whose file on main is missing or still Proposed
    (as ``runner.requests`` reads it): Approve plan waits for it."""
    for p in proposals:
        if p.get("kind") != "adr":
            continue
        number = _ADR_NUMBER.match(str(p.get("path") or ""))
        found = sorted((repo / "docs" / "adr").glob(f"{number[1]}-*.md")) if repo and number else []
        if not found or is_proposed(found[0].read_text(encoding="utf-8")):
            return True
    return False


@router.get("/planning/mockups/{thread}/{path:path}", response_class=HTMLResponse)
def mockup_file(thread: str, path: str, conn: Db, project: Project) -> HTMLResponse:
    """A mock-up's file from the card's plan branch (``planner.draft``), for a sandboxed
    ``<iframe>``; anything outside ``docs/milestones/*-mockup/`` is 404. Its CSP sandboxes it
    when opened on its own too: an origin of its own, so it can't post to ``/requests``."""
    repo = _repo(conn, project)
    content = draft(repo, thread, path) if repo and _MOCKUP_RE.fullmatch(path) else None
    if content is None:
        raise HTTPException(404, "no such mock-up")
    return HTMLResponse(
        content.decode("utf-8", errors="replace"),
        headers={"Content-Security-Policy": "sandbox allow-scripts"},
    )


@dataclass(frozen=True)
class PlanChange:
    path: str
    word: str  # "added", "changed", "set aside" or "removed"
    text: str | None  # from the plan branch, through ``draft``; None when gone or not a draft


def _plan_changes(repo: Path | None, thread: str, kind: str) -> list[PlanChange]:
    """What approving a ``plan`` or ``replan`` changes (f6-24), each with its text from the
    branch; none for another kind, or with no plan branch."""
    if repo is None or kind not in ("plan", "replan"):
        return []
    found = []
    for change in plan_changes(repo, thread):
        content = draft(repo, thread, change.source) if change.source else None
        text = content.decode("utf-8", errors="replace") if content is not None else None
        found.append(PlanChange(change.path, change.word, text))
    return found


@router.get("/planning/{thread}/proposals/{id}", response_class=HTMLResponse)
def proposal_review(
    request: Request, thread: str, id: str, conn: Db, project: Project
) -> HTMLResponse:
    """A proposal's review page: its key points, agreed by default, with Comment… on each,
    and Send back, Accept ADR, Approve plan or Plant it."""
    project_id = metrics.find_project(conn, project)
    proposal = None if project_id is None else metrics.find_proposal(conn, project_id, thread, id)
    if project_id is None or proposal is None:
        raise HTTPException(404, "no such proposal")
    rows = conn.execute(
        "SELECT m.* FROM planner_messages m JOIN planner_threads t ON t.id = m.thread_id"
        " WHERE t.project_id = ? AND t.card = ? ORDER BY m.id",
        (project_id, thread),
    ).fetchall()
    lead = [r for r in rows if r["author"] == "lead" and r["proposals"]]
    listed = [p for p in json.loads(lead[-1]["proposals"]) if isinstance(p, dict)] if lead else []
    kind = str(proposal.get("kind") or "")
    key_points = proposal.get("key_points")
    number = _ADR_NUMBER.match(str(proposal.get("path") or ""))
    path = str(proposal.get("path") or "")
    repo = _repo(conn, project)
    return render(
        request,
        conn,
        project,
        "proposal.html",
        {
            "active": "/planning",
            "thread": thread,
            "proposal": proposal,
            "kind": kind,
            "color": _KIND_COLOR.get(kind, "--ink-2"),
            "key_points": [p for p in key_points if isinstance(p, dict)]
            if isinstance(key_points, list)
            else [],
            "proposals": _proposals(conn, project_id, thread, rows, _known_cards(repo)),
            "adr_number": str(int(number[1])) if number else None,
            "merge": _merge_words(proposal),
            "mockup": f"/planning/mockups/{thread}/{path}" if _MOCKUP_RE.fullmatch(path) else None,
            "adr_waits": _adr_waits(repo, listed),
            "changes": _plan_changes(repo, thread, kind),
        },
    )
