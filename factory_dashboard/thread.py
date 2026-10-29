"""A thread's page (f6-07): ``/planning/{thread}``, its messages and the lead's points, Send,
its proposals' standing, a finished card's review and Sign off, and the reserve lever. What it
shares with the desk and the other planning pages stays in ``planning``."""

import contextlib
import json
import re
import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from factory_dashboard.app import Db, Now, Project, render
from factory_dashboard.coming import (
    _MAX_REQUEST_ID,
    GENERAL,
    _card_titles,
    _edit_words,
    _edited,
    _held,
    _message_thread,
    _next_reply,
    _retried,
    _when,
    _writing,
    reply_line,
)
from factory_dashboard.line import live_line
from factory_dashboard.merges import (
    Names,
    _adr_titles,
    _gone_merge,
    _known_cards,
    _merge_links,
    _merged_on,
    _text_with_links,
)
from factory_dashboard.milestones import _to_html
from factory_dashboard.overview import Change, open_changes, running_jobs
from factory_dashboard.planning import _open_proposals, _repo, _waiting_for_lead, desk_trail
from runner import metrics
from runner.planner import (
    APPROVED,
    ON_ITS_WAY,
    OPEN,
    PLANNER,
    PlannerError,
    message,
    proposal_requests,
    proposal_state,
)
from runner.requests import CHANGE, PLANT, owners_words, refused
from runner.tasks import full_key, milestone_file, short_key

router = APIRouter()

REVISING = "being revised"  # F100: an open proposal while the owner's message waits for the lead

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
    text_html: str | None = None  # the lead's or the runner's text as linked HTML (F37 D3)


@dataclass(frozen=True)
class Proposal:
    kind: str
    title: str
    color: str
    state: str  # F31 D3: open, on its way, approved, rejected or sent back; F100: being revised
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
    revising = thread in _waiting_for_lead(conn, project_id)  # F100
    found = []
    for p in json.loads(lead[-1]["proposals"]):
        if not isinstance(p, dict) or not p.get("id"):
            continue
        state = APPROVED if _gone_merge(p, known) else proposal_state(p, thread, requests)
        found.append(
            Proposal(
                str(p.get("kind") or ""),
                str(p.get("title") or p["id"]),
                _KIND_COLOR.get(str(p.get("kind")), "--ink-2"),
                REVISING if revising and state == OPEN else state,
                f"/planning/{thread}/proposals/{p['id']}",
            )
        )
    return found


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
    revising: bool = False  # F100: open, but the owner's message waits for the lead


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
    revising = state == OPEN and thread in _waiting_for_lead(conn, project_id)
    return Standing(state, pending if state == ON_ITS_WAY else None, said, revising)


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
    if project_id is not None:
        title, meta, seed = _header(conn, project_id, thread)
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
    repo = _repo(conn, project)
    # F37 D3: the lead's and the runner's words link their paths, cards and tickets; the
    # owner's stay plain
    q = "?" + urlencode({"project": project})
    names = _names(conn, project_id, repo)
    for i, msg in enumerate(messages):
        if msg.author == "lead":
            points = [_point_links(p, q, names) if isinstance(p, dict) else p for p in msg.points]
            text_html = _text_with_links(msg.text, q, names)
            messages[i] = replace(msg, points=points, text_html=text_html)
        elif msg.author == "runner":
            messages[i] = replace(msg, text_html=_text_with_links(msg.text, q, names))
    jobs = [j for j in running_jobs(conn, project, now) if j.live]
    merged_into, merged_here, latest_title = _merge_links(repo, thread)
    known = _known_cards(repo)
    # When the card has no milestone row, use the heading's title for the h2
    if title == thread and latest_title:
        title = latest_title
    # "An earlier F73" only when the key has a card on main again (D4): a merged card keeps
    # its milestone row, marked removed, so a row says nothing
    card_on_main = known is not None and thread in known
    words = _again(conn, project_id, thread, again)
    merged_on = _merged_on(
        conn,
        project_id,
        thread,
        merged_into,
        known,
        lambda: _open_proposals(conn, project_id or 0, known),
    )
    # F30 D1: the latest exchange first (the lead's latest message, under what came after it),
    # the older messages folded under Earlier; each newest first
    lead = [i for i, msg in enumerate(messages) if msg.author == "lead"]
    split = lead[-1] if lead else -1
    latest = [*reversed(messages[split + 1 :]), *messages[split : split + 1]]
    earlier = list(reversed(messages[:split])) if lead else []
    # F84: the reply being written, or this thread's place in the lead's line
    places = reply_line(conn, project, now, jobs)
    held = _held(conn, project_id, now, thread)
    place = places.get(thread) if pending and held is None else None
    next_reply = (
        place.words
        if place is not None
        else _next_reply(conn, project, jobs, pending, held, _writing(places))
    )
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
            "next_reply": next_reply,
            "writing_now": place is not None and place.place == 0,
            "merged_into": merged_into,
            "merged_here": merged_here,
            "merged_on": merged_on,
            "card_on_main": card_on_main,
        },
    )


def _names(conn: sqlite3.Connection, project_id: int | None, repo: Path | None) -> Names:
    """What a lead's line on the project may name (F37 D2)."""
    if project_id is None:
        return Names()
    tickets = conn.execute("SELECT ticket FROM tickets WHERE project_id = ?", (project_id,))
    return Names(
        _card_titles(conn, project_id),
        _known_cards(repo) or set(),
        {r["ticket"] for r in tickets.fetchall()},
        _adr_titles(repo),
    )


_POINT_WORDS = ("title", "answer", "action")


def _point_links(point: dict[str, object], q: str, names: Names) -> dict[str, object]:
    """A lead's point with its words as HTML too (``title_html`` and so on), linked."""
    linked = {
        f"{key}_html": _text_with_links(str(point[key]), q, names)
        for key in _POINT_WORDS
        if point.get(key)
    }
    return {**point, **linked}


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
