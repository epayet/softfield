"""The planning room's desk (f6-06, F6 D6): ``/planning`` is the owner's desk.

- Two tiles: the factory now, with when the next reply is expected (planner jobs go first, so a
  pending message is answered once the running job is done, D1), and the lead's 5-hour window.
- ``desk(conn, project)``: what waits for the owner, in five groups (D6, and F31 D9's "Didn't go
  through" first); the Overview's Needs you and the top bar's count reuse its items' words and
  links (f6-09).
- "Plant an idea": a ``plant`` request through ``POST /requests``, the dashboard's only write.
"""

import contextlib
import json
import re
import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import yaml
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from factory_dashboard.app import Db, Now, Project, ago, render
from factory_dashboard.board import RESERVABLE, milestone_cards
from factory_dashboard.line import live_line
from factory_dashboard.milestones import _to_html
from factory_dashboard.overview import (
    CANCELLING,
    Change,
    Running,
    agent_allowances,
    open_changes,
    running_jobs,
)
from runner import metrics
from runner.milestone import milestone_doc
from runner.planner import (
    APPLIED,
    APPROVED,
    MERGE,
    ON_ITS_WAY,
    OPEN,
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
    proposal_requests,
    proposal_state,
    thread_key,
)
from runner.requests import (
    CHANGE,
    DISMISS,
    PLAN_MESSAGE,
    PLANT,
    RESERVE,
    SEND_BACK,
    WORDS,
    Words,
    owners_words,
    refused,
)
from runner.tasks import (
    TaskError,
    full_key,
    milestone_file,
    milestone_key,
    short_key,
    split_frontmatter,
)

router = APIRouter()

GENERAL = "general"
# A request's result when it worked (D1's table); any other result is a refusal.
_ADR_NUMBER = re.compile(r"\.factory/adr/(\d+)-")
# Merge heading written by ``planner.merged_card``: captures source key, title and date.
_MERGE_HEADING_RE = re.compile(
    r"^#{3,} From ([A-Z]+\d+): (.+?) "
    r"\(merged by the (?:lead|owner) on (\d{4}-\d{2}-\d{2})\)[ \t]*$",
    re.MULTILINE,
)
# Path like /planning/f95 in plain text: escape first, then link.
_PLANNING_PATH_RE = re.compile(r"/planning/([a-z][a-z0-9-]+)")
_TYPICAL = 20  # finished jobs of the running one's role and agent that make its typical length


@dataclass(frozen=True)
class DeskItem:
    group: str
    title: str
    words: str
    link: str
    # the owner acted on it and the runner hasn't yet: it shows dashed, on its way, and no
    # longer counts as waiting for them (the owner, 2026-10-08)
    on_its_way: bool = field(default=False, kw_only=True)


@dataclass(frozen=True)
class RefusedItem(DeskItem):
    """The owner's words a request refused (F31 D9): in full, with the runner's reason, and
    where Try again puts them back. An edit that didn't go through is one too (f14-04): a
    plant's has no Try again (neither ``note`` nor ``again``), the idea being a card by then."""

    id: int
    text: str  # an idea's thoughts, or the message with its comments by point; an edit's words
    note: str  # what Try again puts back in the Plant box (F31 D7); "" for a message
    again: str  # the thread whose reply box takes a message back; "" for an idea


@dataclass(frozen=True)
class WaitingPlant(DeskItem):
    """A plant the runner hasn't taken (F14): its row opens to edit or cancel it, until a
    change is on its way; then it shows that change, whose status polls."""

    id: int
    text: str  # what the editor's box holds: the note, or an older plant's thoughts
    titled: bool  # written as a title and thoughts, and edited as the two; else one note
    seed: bool  # a seed's words are the lead's: Cancel it only
    cancelled: bool = False
    change: int | None = None  # the open change's request


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


def _merge_words(proposal: dict[str, object]) -> str | None:
    """A ``merge`` proposal in words, ``merge F12 into F10``; None for another kind."""
    if proposal.get("kind") != MERGE:
        return None
    try:
        return merge_words(proposal)
    except PlannerError:
        return None


def _known_cards(repo: Path | None) -> set[str] | None:
    """Every card on main, or None when the checkout isn't here."""
    return None if repo is None else cards(repo)


def _merge_links(
    repo: Path | None, thread: str
) -> tuple[list[dict[str, str]], list[dict[str, str]], str | None]:
    """Read merge headings from card docs on main.

    Returns ``(merged_into, merged_here, latest_title)``:
    - ``merged_into``: links from this thread to cards it was merged into
    - ``merged_here``: links from this thread to cards merged into it
    - ``latest_title``: the title from the latest merge heading referencing this thread
    """
    if repo is None:
        return [], [], None

    merged_into: list[dict[str, str]] = []
    merged_here: list[dict[str, str]] = []
    source_key = thread.upper()
    latest_title: str | None = None
    latest_date: str = ""

    cards_dir = repo / ".factory" / "cards"
    if not cards_dir.is_dir():
        return [], [], None

    for path in cards_dir.glob("*.md"):
        try:
            doc = path.read_text(encoding="utf-8")
        except OSError:
            continue

        card_key: str | None = None
        with contextlib.suppress(TaskError):  # a card file not named by a key
            card_key = short_key(milestone_key(path.stem))
        # "Merged into F95, <title>" names the kept card by its own title, not the merged one's
        card_title = milestone_doc(doc).get("title") or (card_key or "").upper()

        for match in _MERGE_HEADING_RE.finditer(doc):
            ref_key = match.group(1)
            title = match.group(2).strip()
            date = match.group(3)

            if ref_key == source_key:
                if card_key is not None:
                    merged_into.append(
                        {
                            "key": card_key,
                            "title": card_title,
                            "date": date,
                            "link": f"/planning/{card_key}",
                        }
                    )
                # Track the latest heading title for this source
                if date > latest_date:
                    latest_date = date
                    latest_title = title

            if card_key is not None and card_key == thread:
                merged_here.append(
                    {
                        "key": ref_key.lower(),
                        "title": title,
                        "date": date,
                        "link": f"/planning/{ref_key.lower()}",
                    }
                )

    return merged_into, merged_here, latest_title


def _gone_merge(proposal: dict[str, object], known: set[str] | None) -> bool:
    """A ``merge`` one of whose cards has left main: merged or dropped already, nothing to
    ask (2026-10-08: such merges filled the desk)."""
    if proposal.get("kind") != MERGE or known is None:
        return False
    try:
        return not set(merge_cards(proposal)) <= known
    except PlannerError:
        return False


def _text_with_links(text: str, q: str = "") -> str:
    """Escape ``text`` then turn ``/planning/<key>`` into links, keeping ``q`` (the page's
    ``?project=``). The text is a lead's plain line: the owner's messages stay as plain text."""
    escaped = (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )
    href = q.replace("&", "&amp;")
    return _PLANNING_PATH_RE.sub(
        lambda m: f'<a href="/planning/{m[1]}{href}">/planning/{m[1]}</a>', escaped
    )


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
            state = proposal_state(proposal, row["card"], later)
            if state not in (OPEN, ON_ITS_WAY):
                continue
            points = proposal.get("key_points")
            words = f"{len(points)} key points" if isinstance(points, list) and points else ""
            if merged := _merge_words(proposal):
                words = f"{merged} · {words}" if words else merged
            items.append(
                DeskItem(
                    "proposals",
                    str(proposal.get("title") or proposal["id"]),
                    _NEXT_PICK if state == ON_ITS_WAY else words or str(proposal.get("kind") or ""),
                    f"/planning/{row['card']}/proposals/{proposal['id']}",
                    on_its_way=state == ON_ITS_WAY,
                )
            )
    return items


def _merged_on(
    conn: sqlite3.Connection,
    project_id: int | None,
    thread: str,
    merged_into: list[dict[str, str]],
    known: set[str] | None,
) -> list[dict[str, object]]:
    """Merged-on blocks for a merged-away card's thread page.

    Returns one entry per kept card (most recent merge first), with open
    proposals and ticket counts. Only when the thread key is not in known
    (the card was merged away) and merged_into is non-empty.
    """
    if project_id is None or not merged_into or known is None or thread in known:
        return []

    # Sort by date descending (most recent first)
    sorted_cards = sorted(merged_into, key=lambda m: m["date"], reverse=True)

    all_open = _open_proposals(conn, project_id, known)
    result: list[dict[str, object]] = []

    for card in sorted_cards:
        kept_key = card["key"]
        # Open proposals for this kept card's thread
        card_proposals = [
            p for p in all_open if p.link.startswith(f"/planning/{kept_key}/proposals/")
        ]
        # Tickets for this kept card
        milestone_rows = conn.execute(
            "SELECT m.key, m.id, t.state FROM milestones m"
            " JOIN tickets t ON t.milestone_id = m.id"
            " WHERE m.project_id = ? AND m.key LIKE ?"
            " AND t.state NOT IN ('later', 'removed')"
            " ORDER BY m.id",
            (project_id, f"{kept_key.upper()}-%"),
        ).fetchall()
        # N and M over the same rows: every milestone of the kept card (a replan has two)
        milestone = milestone_rows[0] if milestone_rows else None
        ticket_count = len(milestone_rows)
        done_count = sum(1 for row in milestone_rows if row["state"] == "done")
        card_data: dict[str, object] = {
            "key": kept_key,
            "title": card["title"],
            "date": card["date"],
            "link": card["link"],
            "proposals": card_proposals,
        }
        if milestone:
            card_data["milestone_key"] = milestone["key"]
            card_data["ticket_count"] = ticket_count
            card_data["done_count"] = done_count
        result.append(card_data)

    return result


def _ripe(conn: sqlite3.Connection, project: str, now: datetime) -> list[DeskItem]:
    """Every ticket done, its review written, and not signed off, as the line's field has
    them (F50 D1)."""
    return [
        DeskItem(
            "ripe",
            m["title"] or m["key"],
            "reviewed · waits for your sign-off",
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


def _retried(conn: sqlite3.Connection, project_id: int) -> set[int]:
    """The requests a later one with the owner's words names as ``again`` (F48 D2): Try again
    sent their words anew, and that retry, pending or done, stands for them."""
    rows = conn.execute(
        "SELECT id, value FROM owner_requests WHERE project_id = ? AND kind IN (?, ?, ?)",
        (project_id, *WORDS),
    ).fetchall()
    found = set()
    for r in rows:
        try:
            data = json.loads(r["value"] or "")
        except json.JSONDecodeError:
            continue
        named = data.get("again") if isinstance(data, dict) else None
        if type(named) is int:
            named = str(named)
        if not (isinstance(named, str) and named.isascii() and named.isdigit()):
            continue
        if len(named) <= _MAX_REQUEST_ID and int(named) < r["id"]:
            found.add(int(named))
    return found


def _edited(conn: sqlite3.Connection, project_id: int, change: sqlite3.Row) -> sqlite3.Row | None:
    """The plant or message a ``change`` names, in its own project; None for anything else."""
    subject = str(change["subject"] or "")
    if not (subject.isascii() and subject.isdigit() and len(subject) <= _MAX_REQUEST_ID):
        return None
    row = metrics.find_request(conn, int(subject))
    if row is None or row["project_id"] != project_id:
        return None
    return row if row["kind"] in (PLANT, PLAN_MESSAGE) else None


def _edit_words(words: Words) -> str:
    """An edit's new words, whole: a plant's new title with its thoughts, or the text."""
    return "\n\n".join(filter(None, [words.title, words.text]))


def _failed_edit(
    conn: sqlite3.Connection, project_id: int, titles: dict[str, str], change: sqlite3.Row
) -> tuple[str, str]:
    """A refused edit's title on the desk, saying what was edited, and the thread whose reply
    box takes a message's back ("" for a plant's: planting its words again would make a
    second card)."""
    target = _edited(conn, project_id, change)
    if target is None:
        return "Your edit", ""
    if target["kind"] == PLANT:
        was = owners_words(target)
        return f"Your edit of {(was.title if was else '') or 'your idea'}", ""
    thread = _message_thread(target)
    return f"Your edit on {_thread_title(thread, titles)}", f"/planning/{thread}"


def _blocked(conn: sqlite3.Connection, project_id: int) -> list[DeskItem]:
    """Open blocked tickets with their reason: one plain DeskItem per row, oldest first.

    If the runner has a look on the card's thread and the lead has since replied, the words
    say where the fix waits. If the runner has a look but the lead hasn't yet, the words say
    the lead is looking. A bug ticket with no card gets nothing extra.
    """
    rows = conn.execute(
        "SELECT subject, text FROM owner_items"
        " WHERE project_id = ? AND kind = ? AND resolved IS NULL"
        " ORDER BY created, id",
        (project_id, "blocked"),
    ).fetchall()
    items: list[DeskItem] = []
    for r in rows:
        prefix = f"{r['subject']} blocked: "
        words = r["text"][len(prefix) :] if r["text"].startswith(prefix) else r["text"]
        ticket = r["subject"]
        # Find the latest runner message starting with "<ticket> blocked:" on this project
        runner = conn.execute(
            "SELECT m.at, t.card FROM planner_messages m"
            " JOIN planner_threads t ON t.id = m.thread_id"
            " WHERE t.project_id = ? AND m.author = 'runner'"
            " AND m.text LIKE ?"
            " ORDER BY m.at DESC LIMIT 1",
            (project_id, f"{ticket} blocked:%"),
        ).fetchone()
        if runner is not None:
            runner_at = runner["at"]
            card = runner["card"]
            # Check for a lead message after the runner's on the same thread
            lead = conn.execute(
                "SELECT max(id) FROM planner_messages"
                " WHERE thread_id = ("
                "   SELECT id FROM planner_threads"
                "   WHERE project_id = ? AND card = ?)"
                " AND author = 'lead' AND at > ?",
                (project_id, card, runner_at),
            ).fetchone()
            if lead["max(id)"] is not None:
                words = f"{words} · the lead's fix waits on {card.upper()}'s thread"
            else:
                words = f"{words} · the lead is looking at it"
        items.append(DeskItem("blocked", ticket, words, f"/tickets/{ticket}"))
    return items


def _refused(conn: sqlite3.Connection, project_id: int, titles: dict[str, str]) -> list[DeskItem]:
    """The owner's words the runner refused (F31 D9), until they dismiss them: a dismiss on
    its way takes one off at once, and so does a retry (``_retried``). An edit of a waiting
    plant or message that didn't go through is among them (f14-04), never a cancel."""
    rows = conn.execute(
        "SELECT * FROM owner_requests WHERE project_id = ? AND done IS NOT NULL"
        " AND dismissed IS NULL AND kind IN (?, ?, ?, ?) ORDER BY id",
        (project_id, *WORDS, CHANGE),
    ).fetchall()
    dismissing = {
        str(r["subject"])
        for r in conn.execute(
            "SELECT subject FROM owner_requests WHERE project_id = ? AND kind = ? AND done IS NULL",
            (project_id, DISMISS),
        ).fetchall()
    }
    retried = _retried(conn, project_id)
    items: list[DeskItem] = []
    for r in rows:
        words = owners_words(r)
        if words is None or not refused(r) or str(r["id"]) in dismissing or r["id"] in retried:
            continue
        text = words.text
        if r["kind"] == CHANGE:
            title, again = _failed_edit(conn, project_id, titles, r)
            text = _edit_words(words)
        elif r["kind"] == PLANT:
            title, again = words.title or "Your idea", ""
        else:
            thread = _message_thread(r)
            title, again = f"Your message on {_thread_title(thread, titles)}", f"/planning/{thread}"
        reason = str(r["result"] or "")
        note = _plant_note(r["value"], words) if r["kind"] == PLANT else ""
        items.append(RefusedItem("refused", title, reason, "/planning", r["id"], text, note, again))
    return items


def archived(conn: sqlite3.Connection, project: str, now: datetime) -> list[DeskItem]:
    """The archived threads, the most recently archived first (the owner, 2026-10-07). A
    message from the owner opens one again."""
    project_id = metrics.find_project(conn, project)
    if project_id is None:
        return []
    titles = _card_titles(conn, project_id)
    rows = conn.execute(
        "SELECT card, archived, archived_why FROM planner_threads"
        " WHERE project_id = ? AND archived IS NOT NULL ORDER BY archived DESC, id DESC",
        (project_id,),
    ).fetchall()
    return [
        DeskItem(
            "archived",
            _thread_title(r["card"], titles),
            " · ".join(
                filter(None, [r["archived_why"], f"archived {ago(now - _when(r['archived']))} ago"])
            ),
            f"/planning/{r['card']}",
        )
        for r in rows
    ]


def _titled(value: object) -> bool:
    """Whether a plant was written as a title and thoughts (the older form); a one-box note
    (F31 D7), like a value that won't read, is edited as one text."""
    try:
        data = json.loads(value) if isinstance(value, str) else None
    except json.JSONDecodeError:
        return False
    return isinstance(data, dict) and "text" not in data


def _taken_plant(conn: sqlite3.Connection, project_id: int, subject: str) -> sqlite3.Row | None:
    """The plant an open change names, once the runner has finished it; None for anything
    else (a message's change is its thread's to show)."""
    if not (subject.isascii() and subject.isdigit() and len(subject) <= _MAX_REQUEST_ID):
        return None
    row = metrics.find_request(conn, int(subject))
    if row is None or row["project_id"] != project_id or row["kind"] != PLANT:
        return None
    return row if row["done"] is not None else None


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
        changes = open_changes(conn, project_id)
        for r in plant_rows:
            words = owners_words(r)  # leniently: the dashboard stores any value
            plant = WaitingPlant(
                "coming",
                (words.title if words else "") or "Your idea",
                "planting at the runner's next pick",
                "",
                id=r["id"],
                text=words.text if words else "",
                titled=bool(words and words.title) and _titled(r["value"]),
                seed=bool(r["subject"]),
            )
            change = changes.pop(str(r["id"]), None)
            if change is not None and change.cancel:
                plant = replace(plant, words=CANCELLING, cancelled=True)
            elif change is not None:
                plant = replace(
                    plant, title=change.title or plant.title, words=f"changed · {plant.words}"
                )
            if change is not None:
                plant = replace(plant, change=change.id, on_its_way=True)
            items.append(plant)
        # A change made from a page drawn before the runner took its plant: its row stays,
        # for the runner's "too late" to show where the owner asked (F14 D2)
        for subject, change in changes.items():
            late = _taken_plant(conn, project_id, subject)
            if late is None:
                continue
            words = owners_words(late)
            items.append(
                WaitingPlant(
                    "coming",
                    (words.title if words else "") or "Your idea",
                    "your change came too late: the runner had taken it",
                    "",
                    id=late["id"],
                    text="",
                    titled=False,
                    seed=bool(late["subject"]),
                    change=change.id,
                    on_its_way=True,
                )
            )

    # Threads waiting for the lead: the owner's message (or the runner's look at a blocked
    # ticket, ADR 29) is the latest and a planner row about it is open, or an open plan_message
    # request names it whatever is stored (the runner stores that message, and makes the
    # thread, only at its next pick). Each shows once.
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
            " WHERE t.project_id = ? AND m.author IN ('owner', 'runner') ORDER BY t.id",
            (project_id,),
        ).fetchall()
        asked = conn.execute(
            "SELECT id, subject FROM owner_requests"
            " WHERE project_id = ? AND kind = 'plan_message' AND done IS NULL ORDER BY id",
            (project_id,),
        ).fetchall()
        # F14: a message the owner cancelled waits for no reply, as on its thread
        cancelled = {subject for subject, change in changes.items() if change.cancel}
        cards = [r["card"] for r in owners_last if r["card"] in planned]
        cards += [
            str(r["subject"]) for r in asked if r["subject"] and str(r["id"]) not in cancelled
        ]
        if cards:
            titles = _card_titles(conn, project_id)
            jobs = [j for j in running_jobs(conn, project, now) if j.live]
        for card in dict.fromkeys(cards):
            held = _held(conn, project_id, now, card)
            next_reply = _next_reply(conn, project, jobs, True, held)
            items.append(
                DeskItem(
                    "coming",
                    _thread_title(card, titles),
                    f"waiting for the lead · {next_reply}",
                    f"/planning/{card}",
                )
            )

    return DeskGroup("coming", "Coming", "--hazard", items)


_NEXT_PICK = "on its way · the runner applies it at its next pick"


def _acted_on(conn: sqlite3.Connection, project_id: int, items: list[DeskItem]) -> list[DeskItem]:
    """The owner's Archive, Sign off or Remove seed still waiting for the runner, or Try again
    and Set aside on a blocked ticket (F106 D3): the item shows on its way, dashed, saying what
    is coming (the owner, 2026-10-08: an archived thread still looked like it needed them)."""
    pending = conn.execute(
        "SELECT kind, subject, value FROM owner_requests WHERE project_id = ? AND done IS NULL"
        " AND kind IN ('archive', 'signoff', 'drop_seed', 'queue', 'set_aside')",
        (project_id,),
    ).fetchall()
    asked: dict[str, str] = {}
    tickets: dict[str, str] = {}  # by ticket id: a blocked ticket's item links to its page
    for r in pending:
        subject = str(r["subject"] or "")
        if r["kind"] == "archive" and r["value"] == "on":
            asked[subject] = "archiving at the runner's next pick"
        elif r["kind"] == "signoff":
            asked[short_key(subject) if subject else subject] = (
                "signing off at the runner's next pick"
            )
        elif r["kind"] == "drop_seed":
            asked[subject] = "removing at the runner's next pick"
        elif r["kind"] == "queue":
            tickets[subject] = "Trying again at the runner's next pick"
        elif r["kind"] == "set_aside":
            tickets[subject] = "Set aside at the runner's next pick"
    found = []
    for item in items:
        thread = item.link.removeprefix("/planning/").split("/")[0]
        if item.link.startswith("/tickets/"):
            words = tickets.get(item.link.removeprefix("/tickets/"))
        else:
            words = asked.get(thread) if "/proposals/" not in item.link else None
        found.append(replace(item, words=words, on_its_way=True) if words else item)
    return found


def waiting_for_you(groups: list[DeskGroup]) -> list[DeskItem]:
    """The desk's items still waiting for the owner, in desk order: the Planning tab's count,
    Overview's Needs you and the arrows between pages (F35) read these."""
    return [item for group in groups for item in group.items if not item.on_its_way]


def desk_trail(
    conn: sqlite3.Connection, project: str, now: datetime, path: str
) -> dict[str, object]:
    """F35, the owner's Previous and Next between what waits for them: the pages of the desk's
    items still waiting, in desk order (what didn't go through stays on /planning). On one of
    them, its neighbours; on a page already done with, the first one left."""
    links = list(
        dict.fromkeys(
            item.link
            for item in waiting_for_you(desk(conn, project, now))
            if item.link.startswith("/planning/")
        )
    )
    if path in links:
        at = links.index(path)
        return {
            "previous": links[at - 1] if at > 0 else None,
            "next": links[at + 1] if at + 1 < len(links) else None,
            "words": f"{at + 1} of {len(links)} waiting for you",
        }
    return {
        "previous": None,
        "next": links[0] if links else None,
        "words": f"{len(links)} waiting for you" if links else "Nothing else waits for you",
    }


def desk(conn: sqlite3.Connection, project: str, now: datetime) -> list[DeskGroup]:
    """What waits for the owner (D6), in six groups in this order, empty ones included: what
    didn't go through first (F31 D9)."""
    project_id = metrics.find_project(conn, project)
    if project_id is None:
        refusals: list[DeskItem] = []
        answers: list[DeskItem] = []
        proposals: list[DeskItem] = []
        ripe: list[DeskItem] = []
        seeds: list[DeskItem] = []
        blocked: list[DeskItem] = []
    else:
        titles = _card_titles(conn, project_id)
        refusals = _refused(conn, project_id, titles)
        answers = _acted_on(conn, project_id, _answers_wanted(conn, project_id, titles, now))
        proposals = _open_proposals(conn, project_id, _known_cards(_repo(conn, project)))
        ripe = _acted_on(conn, project_id, _ripe(conn, project, now))
        seeds = _acted_on(conn, project_id, _seeds(conn, project_id))
        blocked = _acted_on(conn, project_id, _blocked(conn, project_id))
    return [
        DeskGroup("refused", "Didn't go through", "--hazard", refusals),
        DeskGroup("blocked", "Blocked tickets", "--hazard", blocked),
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


_FIVE_HOURS = timedelta(hours=5)


def _held(
    conn: sqlite3.Connection, project_id: int | None, now: datetime, thread: str | None = None
) -> str | None:
    """Why the lead's reply waits when its planner job is parked for a Claude limit (the
    owner, 2026-10-08: it said "at the factory's next pick" while the week was used up); None
    when it isn't. A wait past 5 hours can only be the weekly limit. ``thread``: that thread's
    job only."""
    if project_id is None:
        return None
    until = [
        _when(r["not_before"])
        for r in metrics.open_jobs(conn, project_id)
        if r["kind"] == PLANNER
        and r["not_before"]
        and _when(r["not_before"]) > now
        and (thread is None or str(r["subject"] or "").split("#")[0] == thread)
    ]
    if not until:
        return None
    first = min(until)
    which = "weekly" if first - now > _FIVE_HOURS else "5-hour"
    return f"waits for Claude's {which} limit, until {first.astimezone():%a %H:%M}"


def _next_reply(
    conn: sqlite3.Connection,
    project: str,
    jobs: list[Running],
    pending: bool,
    held: str | None = None,
) -> str | None:
    """When the owner's pending message is answered: after the running job, planning going
    first (D1), or once Claude's limit resets (``held``); ``None`` with nothing pending."""
    if not pending:
        return None
    if held is not None:
        return held
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
        "next_reply": _next_reply(conn, project, jobs, pending, _held(conn, project_id, now)),
    }


@router.get("/planning", response_class=HTMLResponse)
def planning(request: Request, conn: Db, project: Project, now: Now) -> HTMLResponse:
    """The owner's desk: the two tiles, what waits for the owner, and Plant an idea."""
    window = next(
        (a for a in agent_allowances(conn, now) if a.label == "Claude" and a.window == "five_hour"),
        None,
    )
    week = next(
        (a for a in agent_allowances(conn, now) if a.label == "Claude" and a.window == "seven_day"),
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
            "week": week,
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
    latest: bool  # the lead's latest message, with points: the ones the owner comments on
    waiting: bool = False  # an open plan_message request not yet picked up
    id: int = 0  # a waiting message's request: what a change names (F14 D1)
    change: Change | None = None  # a waiting message's open change: on its way, no more edits
    text_html: str | None = None  # pre-rendered HTML for lead messages without points


@dataclass(frozen=True)
class Proposal:
    kind: str
    title: str
    color: str
    state: str  # F31 D3: open, on its way, approved, rejected or sent back
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


_SHEET = (  # what the owner acts on (F50 D2); the rest stays on the milestone page
    ("changed", "What changed"),
    ("how_to_test", "How to test"),
    ("decisions", "Decisions waiting for you"),
)


@dataclass(frozen=True)
class Review:
    """A card's written review on its page (F50 D2, D3): its sheet's sections, and whether
    the owner can sign it off now or a sign-off is on its way."""

    key: str  # the card's full key: the milestone page's and the signoff request's
    sections: list[tuple[str, str]]  # (heading, HTML from the lead's Markdown)
    ripe: bool
    signing_off: bool
    refused: str | None = None  # the runner's word on the last sign-off, the card still ripe


def _review(
    conn: sqlite3.Connection, project: str, project_id: int, thread: str, now: datetime
) -> Review | None:
    """The card's review once its sign-off sheet is stored; None before."""
    if thread == GENERAL:
        return None
    row = next(
        (
            r
            for r in conn.execute(
                "SELECT key, signoff FROM milestones WHERE project_id = ? AND signoff IS NOT NULL",
                (project_id,),
            ).fetchall()
            if short_key(r["key"]) == thread
        ),
        None,
    )
    if row is None:
        return None
    sheet = json.loads(row["signoff"])
    sections = [
        (heading, _to_html(sheet[key]))
        for key, heading in _SHEET
        if isinstance(sheet.get(key), str) and sheet[key].strip()
    ]
    ripe = any(m["key"] == row["key"] for m in live_line(conn, project, now)["field"]["ripe"])
    last = conn.execute(
        "SELECT done, result FROM owner_requests WHERE project_id = ? AND kind = 'signoff'"
        " AND subject IN (?, ?) ORDER BY id DESC LIMIT 1",
        (project_id, row["key"], thread),
    ).fetchone()
    signing_off = last is not None and last["done"] is None
    # a done sign-off on a card still ripe was refused (a dirty main, tickets left): its word
    # stays under the button after a reload (F50 D3)
    refused = last["result"] if last is not None and last["done"] and ripe else None
    return Review(row["key"], sections, ripe, signing_off, refused)


def _messages(rows: list[sqlite3.Row]) -> list[Message]:
    # F30 D1: the owner comments on the lead's latest message, the one drawn at the top; when
    # it has no points (a plain answer, an approval note), the older points fold under Earlier
    # with no Comment… boxes
    lead = [r for r in rows if r["author"] == "lead"]
    latest = lead[-1]["id"] if lead and lead[-1]["points"] else None
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


def _has_proposals(proposals: str | None) -> bool:
    """Whether a lead message's proposals column lists proposals (not ``'[]'``)."""
    return proposals is not None and proposals != "[]"


def _proposals(
    conn: sqlite3.Connection,
    project_id: int,
    thread: str,
    rows: list[sqlite3.Row],
    known: set[str] | None = None,
) -> list[Proposal]:
    """The proposals in the thread's latest lead message that lists some, each with where it
    stands (F31 D3); a merge whose card has left main is approved."""
    lead = [r for r in rows if r["author"] == "lead" and _has_proposals(r["proposals"])]
    if not lead:
        return []
    requests = _since(conn, project_id, lead[-1]["at"])
    return [
        Proposal(
            str(p.get("kind") or ""),
            str(p.get("title") or p["id"]),
            _KIND_COLOR.get(str(p.get("kind")), "--ink-2"),
            APPROVED if _gone_merge(p, known) else proposal_state(p, thread, requests),
            f"/planning/{thread}/proposals/{p['id']}",
        )
        for p in json.loads(lead[-1]["proposals"])
        if isinstance(p, dict) and p.get("id")
    ]


def _since(conn: sqlite3.Connection, project_id: int, at: str) -> list[sqlite3.Row]:
    """The owner's requests made after ``at`` (a lead message's), oldest first."""
    since = _when(at)
    return [
        r
        for r in conn.execute(
            "SELECT * FROM owner_requests WHERE project_id = ? ORDER BY id", (project_id,)
        ).fetchall()
        if _when(r["created"]) > since
    ]


REPLACED = "replaced by a newer reply"


@dataclass(frozen=True)
class Standing:
    """Where a proposal stands on its review page (F31 D3): its state; the request on its
    way (its status polls); the runner's word on the latest request about it (a refusal's
    reason while it is open again)."""

    state: str
    pending: sqlite3.Row | Mapping[str, Any] | None
    said: str


def _standing(
    conn: sqlite3.Connection,
    project_id: int,
    thread: str,
    proposal: dict[str, object],
    lead: list[sqlite3.Row],
    known: set[str] | None,
) -> Standing:
    listed = [p for p in json.loads(lead[-1]["proposals"]) if isinstance(p, dict)] if lead else []
    if proposal.get("id") not in {p.get("id") for p in listed}:
        return Standing(REPLACED, None, "")
    if _gone_merge(proposal, known):
        return Standing(APPROVED, None, "")
    requests = _since(conn, project_id, lead[-1]["at"])
    state = proposal_state(proposal, thread, requests)
    about = proposal_requests(proposal, thread, requests)
    pending = next((r for r in reversed(about) if r["done"] is None), None)
    done = [r for r in about if r["done"] is not None]
    said = str(done[-1]["result"] or "") if done else ""
    return Standing(state, pending if state == ON_ITS_WAY else None, said)


_MAX_REQUEST_ID = 12


@dataclass(frozen=True)
class ReserveLever:
    """A planted card's "may use Claude's reserve" lever (F172 D6), started or not."""

    on: bool  # its doc says ``**Reserve:** yes``
    asked: str | None  # "on" or "off": the owner's latest request the runner hasn't taken


def _reserve_lever(
    conn: sqlite3.Connection, project: str, project_id: int, now: datetime, thread: str
) -> ReserveLever | None:
    """The card's lever, as the board has its mark; None for a card in no ``RESERVABLE``
    stage, or with every ticket done (F172 D6: only while it has work to run, not in its
    review). A lever pulled shows on its way, as ``reserve_switches`` finds a switch's."""
    found = next((c for c in milestone_cards(conn, project, now) if c.key.lower() == thread), None)
    if found is None or found.stage not in RESERVABLE or found.done >= found.total:
        return None
    asked = conn.execute(
        "SELECT value FROM owner_requests WHERE project_id = ? AND kind = ? AND subject = ?"
        " AND done IS NULL ORDER BY id DESC LIMIT 1",
        (project_id, RESERVE, thread),
    ).fetchone()
    return ReserveLever(found.reserve, asked["value"] if asked is not None else None)


def _again(conn: sqlite3.Connection, project_id: int | None, thread: str, again: str) -> str:
    """The words of the refused message ``again`` names, for the thread's reply box, or of a
    message's edit that didn't go through (f14-04: its thread is the message's); "" for
    anything else, and for one retried already (F48 D2)."""
    if project_id is None or not (again.isascii() and again.isdigit()):
        return ""
    if len(again) > _MAX_REQUEST_ID:
        return ""
    row = metrics.find_request(conn, int(again))
    if row is None or row["project_id"] != project_id or row["kind"] == PLANT:
        return ""
    if row["id"] in _retried(conn, project_id):
        return ""
    words = owners_words(row)
    if words is None or not refused(row):
        return ""
    sent = _edited(conn, project_id, row) if row["kind"] == CHANGE else row
    if sent is None or sent["kind"] == PLANT or _message_thread(sent) != thread:
        return ""
    return _edit_words(words) if row["kind"] == CHANGE else words.text


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
    review: Review | None = None
    lever: ReserveLever | None = None
    if project_id is not None:
        title, meta, seed = _header(conn, project_id, thread)
        lever = _reserve_lever(conn, project, project_id, now, thread)
        review = _review(conn, project, project_id, thread, now)
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
        changes = open_changes(conn, project_id)
        # Append open plan_message requests as waiting messages
        for req in conn.execute(
            "SELECT * FROM owner_requests"
            " WHERE project_id = ? AND kind = 'plan_message'"
            " AND subject = ? AND done IS NULL ORDER BY id",
            (project_id, thread),
        ).fetchall():
            try:  # as the runner will read it; one it will refuse shows empty
                text, comments = message(req["value"])
            except PlannerError:
                text, comments = "", {}
            # F14: a cancelled message waits for no reply; an edit shows its new words at once
            change = changes.get(str(req["id"]))
            if change is None or not change.cancel:
                pending = True
            if change is not None and not change.cancel:
                edit = metrics.find_request(conn, change.id)
                with contextlib.suppress(PlannerError):  # one the runner will refuse: as it was
                    text, comments = message(edit["value"] if edit is not None else None)
            points = [{"n": n, "comment": c} for n, c in comments.items()]
            messages.append(
                Message("owner", req["created"], text, points, False, True, req["id"], change)
            )
    # Lead messages without points: convert /planning/<key> paths to links
    q = "?" + urlencode({"project": project})
    for i, msg in enumerate(messages):
        if msg.author == "lead" and not msg.points and msg.text:
            messages[i] = replace(msg, text_html=_text_with_links(msg.text, q))
    jobs = [j for j in running_jobs(conn, project, now) if j.live]
    repo = _repo(conn, project)
    merged_into, merged_here, latest_title = _merge_links(repo, thread)
    known = _known_cards(repo)
    # When the card has no milestone row, use the heading's title for the h2
    if title == thread and latest_title:
        title = latest_title
    # "An earlier F73" only when the key has a card on main again (D4): a merged card keeps
    # its milestone row, marked removed, so a row says nothing
    card_on_main = known is not None and thread in known
    words = _again(conn, project_id, thread, again)
    merged_on = _merged_on(conn, project_id, thread, merged_into, known)
    # F30 D1: the latest exchange first (the lead's latest message, under what came after it),
    # the older messages folded under Earlier; each newest first
    lead = [i for i, msg in enumerate(messages) if msg.author == "lead"]
    split = lead[-1] if lead else -1
    latest = [*reversed(messages[split + 1 :]), *messages[split : split + 1]]
    earlier = list(reversed(messages[:split])) if lead else []
    return render(
        request,
        conn,
        project,
        "thread.html",
        {
            "again": words,
            "again_id": str(int(again)) if words else "",  # the reply's hidden field (F48 D2)
            "active": "/planning",
            "thread": thread,
            "card_title": title,
            "card_meta": meta,
            "note": _note(repo, thread),
            "reserve_lever": lever,
            "seed": seed,
            "has_thread": bool(messages),
            "archived_at": archived_at,
            "archiving": archiving,
            "review": review,
            "trail": desk_trail(conn, project, now, request.url.path),
            "messages": latest,
            "earlier": earlier,
            "points": next((len(m.points) for m in messages if m.latest), 0),
            "proposals": proposals,
            "next_reply": _next_reply(
                conn, project, jobs, pending, _held(conn, project_id, now, thread)
            ),
            "merged_into": merged_into,
            "merged_here": merged_here,
            "merged_on": merged_on,
            "card_on_main": card_on_main,
        },
    )


# --- proposal review (f6-08) ----------------------------------------------------------------

_MOCKUP_RE = re.compile(r"\.factory/cards/[^/]+-mockup/[^/].*")
# Old mock-up path: ``docs/milestones/<name>-mockup/<file>`` (ADR 30's move).
_OLD_MOCKUP_RE = re.compile(r"^docs/milestones/([^/]+)-mockup/(.+)$")


def _resolve_mockup_path(path: str) -> str | None:
    """Convert an old mock-up path to the new format, or return it unchanged.

    Returns ``None`` when the path doesn't match either the old or new pattern.
    """
    if _MOCKUP_RE.fullmatch(path):
        return path
    match = _OLD_MOCKUP_RE.fullmatch(path)
    if match:
        return f".factory/cards/{match.group(1)}-mockup/{match.group(2)}"
    return None


def _repo(conn: sqlite3.Connection, project: str) -> Path | None:
    """The project's checkout; None when ``projects.repo`` isn't a folder here (a URL)."""
    row = conn.execute("SELECT repo FROM projects WHERE name = ?", (project,)).fetchone()
    repo = Path(row["repo"]) if row and row["repo"] else None
    return repo if repo and repo.is_dir() else None


def _note(repo: Path | None, thread: str) -> str:
    """The owner's whole note: the card's doc between ``## Notes`` and the next ``## `` line.
    "" for no checkout, no doc, no section, "(none)" or the general thread (F90 D2)."""
    if repo is None or thread == GENERAL:
        return ""
    try:
        text = milestone_file(repo, "cards", full_key(repo, thread)).read_text(encoding="utf-8")
    except OSError:
        return ""
    found = re.search(r"^## Notes[ \t]*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    note = found[1].strip() if found else ""
    if note == "(none)":
        return ""
    # the factory's marks, not the owner's words: a merged note's "### From F18: …" heading,
    # and the backslash seed_card and merged_card put before a line's ">" or "#"
    return re.sub(r"^(?:#{1,6} |\\(?=[>#]))", "", note, flags=re.MULTILINE)


def _adr_waits(repo: Path | None, proposals: list[dict[str, object]]) -> bool:
    """Whether the card has an ``adr`` proposal whose file on main is missing or still Proposed
    (as ``runner.requests`` reads it): Approve plan waits for it."""
    for p in proposals:
        if p.get("kind") != "adr":
            continue
        number = _ADR_NUMBER.match(str(p.get("path") or ""))
        found = (
            sorted((repo / ".factory" / "adr").glob(f"{number[1]}-*.md")) if repo and number else []
        )
        if not found or is_proposed(found[0].read_text(encoding="utf-8")):
            return True
    return False


@router.get("/planning/mockups/{thread}/{path:path}", response_class=HTMLResponse)
def mockup_file(thread: str, path: str, conn: Db, project: Project) -> HTMLResponse:
    """A mock-up's file from the card's plan branch (``planner.draft``), for a sandboxed
    ``<iframe>``; anything outside ``.factory/cards/*-mockup/`` is 404. Its CSP sandboxes it
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
    who: str = ""  # a ticket's builder, lead or developer (F31 D8); "" for another file
    difficulty: str = ""  # a ticket's difficulty, as its frontmatter gives it


def _plan_changes(repo: Path | None, thread: str, kind: str) -> list[PlanChange]:
    """What approving a ``plan`` or ``replan`` changes (f6-24), each with its text from the
    branch; none for another kind, or with no plan branch."""
    if repo is None or kind not in ("plan", "replan"):
        return []
    found = []
    for change in plan_changes(repo, thread):
        content = draft(repo, thread, change.source) if change.source else None
        text = content.decode("utf-8", errors="replace") if content is not None else None
        found.append(PlanChange(change.path, change.word, text, *_who(change.path, text)))
    return found


_WORD_COLOR = {"added": "--good", "changed": "--a7"}  # set aside and removed: --muted (D8)


def _who(path: str, text: str | None) -> tuple[str, str]:
    """A ticket's builder and difficulty from its frontmatter (F31 D8); ("", "") for any other
    file, or a ticket that won't read."""
    if text is None or not path.startswith(".factory/tasks/"):
        return "", ""
    try:
        meta, _ = split_frontmatter(text)
    except (ValueError, yaml.YAMLError):
        return "", ""
    agent = meta.get("agent") or "developer"
    who = "lead" if agent == "lead" else "developer"
    difficulty = meta.get("difficulty")
    return who, str(difficulty) if isinstance(difficulty, int) else ""


@router.get("/planning/{thread}/proposals/{id}", response_class=HTMLResponse)
def proposal_review(
    request: Request, thread: str, id: str, conn: Db, project: Project, now: Now
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
    lead = [r for r in rows if r["author"] == "lead" and _has_proposals(r["proposals"])]
    listed = [p for p in json.loads(lead[-1]["proposals"]) if isinstance(p, dict)] if lead else []
    kind = str(proposal.get("kind") or "")
    key_points = proposal.get("key_points")
    number = _ADR_NUMBER.match(str(proposal.get("path") or ""))
    path = str(proposal.get("path") or "")
    repo = _repo(conn, project)
    resolved = _resolve_mockup_path(path) if path else None
    mockup: str | None = None
    mockup_gone: str | None = None
    if resolved is not None:
        content = draft(repo, thread, resolved) if repo else None
        if content is not None:
            mockup = f"/planning/mockups/{thread}/{resolved}"
        else:
            mockup_gone = path
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
            "mockup": mockup,
            "mockup_gone": mockup_gone,
            "adr_waits": _adr_waits(repo, listed),
            "changes": _plan_changes(repo, thread, kind),
            "word_color": _WORD_COLOR,
            "standing": _standing(conn, project_id, thread, proposal, lead, _known_cards(repo)),
            "trail": desk_trail(conn, project, now, request.url.path),
        },
    )
