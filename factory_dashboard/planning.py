"""The planning room's desk (f6-06, F6 D6): ``/planning`` is the owner's desk.

- Two tiles: the factory now, with when the next reply is expected (planner jobs go first, so a
  pending message is answered once the running job is done, D1), and the lead's 5-hour window.
- ``desk(conn, project)``: what waits for the owner, in six groups (D6, and F31 D9's "Didn't go
  through" first); the Overview's Needs you and the top bar's count reuse its items' words and
  links (f6-09).
- "Plant an idea": a ``plant`` request through ``POST /requests``, the dashboard's only write.
"""

import json
import re
import sqlite3
from collections.abc import Callable, Collection, Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from factory_dashboard.app import Db, Now, Project, ago, render
from factory_dashboard.coming import (
    GENERAL,
    DeskGroup,
    DeskItem,
    Part,
    Place,
    _acted_on,
    _card_titles,
    _held,
    _next_reply,
    _refused,
    _thread_title,
    _when,
    _writing,
    coming,
    reply_line,
)
from factory_dashboard.line import live_line
from factory_dashboard.merges import (
    _gone_merge,
    _known_cards,
    _merge_words,
)
from factory_dashboard.overview import (
    agent_allowances,
    open_changes,
    running_jobs,
)
from runner import metrics
from runner.planner import (
    APPLIED,
    APPROVED,
    DRAFTED,
    MERGE,
    ON_ITS_WAY,
    OPEN,
    PLANNER,
    REJECTED,
    PlannerError,
    is_proposed,
    merge_cards,
    proposal_state,
    thread_name,
)
from runner.requests import BY_YOU, _latest
from runner.tasks import (
    short_key,
)

router = APIRouter()

_ADR_NUMBER = re.compile(r"(?:\.softfield/adr|docs/adr)/(\d+)-")
_NEXT_PICK = "on its way · the runner applies it at its next pick"

# F210 D8: a card's proposals read ADR, mock-up, plan or replan, merge, seed; anything else last
_READING = {"adr": 0, "mockup": 1, "plan": 2, "replan": 2, "merge": 3, "seed": 4}


def reading_order[T](
    items: Iterable[T], proposal_of: Callable[[T], Mapping[str, object]]
) -> list[T]:
    """``items`` in a card's reading order (F210 D8), by the kind of each one's proposal dict;
    items of the same kind keep their order."""
    return sorted(
        items, key=lambda item: _READING.get(str(proposal_of(item).get("kind")), len(_READING))
    )


def _asked(conn: sqlite3.Connection, project_id: int) -> list[str]:
    """The cards an open ``plan_message`` request names, the runner not yet having stored the
    message; a message the owner cancelled (F14) waits for no reply."""
    cancelled = {s for s, change in open_changes(conn, project_id).items() if change.cancel}
    rows = conn.execute(
        "SELECT id, subject FROM owner_requests"
        " WHERE project_id = ? AND kind = 'plan_message' AND done IS NULL ORDER BY id",
        (project_id,),
    ).fetchall()
    return [str(r["subject"]) for r in rows if r["subject"] and str(r["id"]) not in cancelled]


def _last_messages(conn: sqlite3.Connection, project_id: int) -> list[sqlite3.Row]:
    """Each thread's latest message, oldest first."""
    return conn.execute(
        "SELECT t.card, m.at, m.author, t.archived FROM planner_threads t"
        " JOIN planner_messages m ON m.id = ("
        "   SELECT max(id) FROM planner_messages WHERE thread_id = t.id)"
        " WHERE t.project_id = ? ORDER BY m.id",
        (project_id,),
    ).fetchall()


def _waiting_order(
    conn: sqlite3.Connection, project_id: int, last: list[sqlite3.Row]
) -> dict[str, None]:
    """The cards the lead owes a reply, in order: the owner's (or the runner's, ADR 29) message
    is the thread's latest and a planner job about it is open, or an open ``plan_message``
    request names the card."""
    planned = {
        str(r["subject"] or "").split("#")[0]
        for r in metrics.open_jobs(conn, project_id)
        if r["kind"] == PLANNER
    }
    return dict.fromkeys(
        [r["card"] for r in last if r["author"] in ("owner", "runner") and r["card"] in planned]
        + _asked(conn, project_id)
    )


def _waiting_for_lead(conn: sqlite3.Connection, project_id: int) -> set[str]:
    """The thread cards whose owner's message waits for the lead (F74, F100)."""
    return set(_waiting_order(conn, project_id, _last_messages(conn, project_id)))


def _replies(
    conn: sqlite3.Connection, project_id: int, project: str, now: datetime, cards: Collection[str]
) -> dict[str, tuple[Place | None, bool, str]]:
    """For each card the lead owes a reply (F84): its place in the lead's line (none while held
    for a Claude limit), whether it is held, and the words for when the reply comes."""
    if not cards:
        return {}
    jobs = [j for j in running_jobs(conn, project, now) if j.live]
    places = reply_line(conn, project, now, jobs)
    writing = _writing(places)
    found = {}
    for card in cards:
        held = _held(conn, project_id, now, card)
        place = places.get(card) if held is None else None
        if place is not None:
            reply = place.words
        else:  # pending, so never None
            reply = _next_reply(conn, project, jobs, True, held, writing) or ""
        found[card] = (place, held is not None, reply)
    return found


def _revising(
    conn: sqlite3.Connection, project_id: int, project: str, now: datetime
) -> dict[str, str]:
    """For each card the lead owes a reply, what its open proposals say (F100): ``being
    revised`` and when the reply comes."""
    replies = _replies(conn, project_id, project, now, _waiting_for_lead(conn, project_id))
    return {card: f"being revised · {words}" for card, (_, _, words) in replies.items()}


def _answers_wanted(
    conn: sqlite3.Connection,
    project_id: int,
    project: str,
    titles: dict[str, str],
    now: datetime,
) -> list[DeskItem]:
    """One box per conversation (F74): threads whose last message is the lead's, a reply the
    owner hasn't answered (an archived thread waits for nothing), then the threads the lead owes
    a reply (``_waiting_order``), dashed and on their way. Those are listed whatever is stored:
    archived, or no thread yet. The lead's replies come newest first (F185 D3)."""
    last = _last_messages(conn, project_id)
    waiting = _waiting_order(conn, project_id, last)
    items = [
        DeskItem(
            "answers",
            _thread_title(r["card"], titles),
            f"the lead replied {ago(now - _when(r['at']))} ago",
            f"/planning/{r['card']}",
        )
        for r in reversed(last)
        if r["author"] == "lead" and r["archived"] is None and r["card"] not in waiting
    ]
    # F84 D4: in the lead's order, the reply being written first, then the plants, then
    # the messages the runner hasn't placed, then those held for a Claude limit
    placed: list[DeskItem] = []
    rest: list[DeskItem] = []
    later: list[DeskItem] = []
    for card, (place, held, reply) in _replies(conn, project_id, project, now, waiting).items():
        said = reply if place is not None else f"waiting for the lead · {reply}"
        item = DeskItem(
            "answers",
            _thread_title(card, titles),
            said,
            f"/planning/{card}",
            on_its_way=True,
            place=place,
        )
        (placed if place is not None else later if held else rest).append(item)
    placed.sort(key=lambda item: item.place.place if item.place else 0)
    return items + placed + rest + later


def _part_name(proposal: dict[str, object]) -> str:
    """A proposal's short name on a card's desk item: ``ADR 27``, ``plan``, ``merge F34``."""
    kind = str(proposal.get("kind") or "proposal")
    if kind == "adr":
        number = _ADR_NUMBER.match(str(proposal.get("path") or ""))
        return f"ADR {int(number[1])}" if number else "ADR"
    if kind == MERGE:
        try:
            return f"merge {thread_name(merge_cards(proposal)[0])}"
        except PlannerError:
            return "merge"
    return "mock-up" if kind == "mockup" else kind


def _key_points(proposal: Mapping[str, object]) -> int:
    points = proposal.get("key_points")
    return len(points) if isinstance(points, list) else 0


def _proposal_words(parts: list[tuple[dict[str, object], str]], repo: Path | None) -> str:
    """What a card's open proposals add to its box: their key points in all, what a merge alone
    joins, and "accept the ADR first" while its ADR waits on main."""
    total = sum(_key_points(p) for p, _ in parts)
    words = f"{total} key points" if total else ""
    if len(parts) == 1 and (merged := _merge_words(parts[0][0])):  # a merge alone says what joins
        words = f"{merged} · {words}" if words else merged
    adr_open = any(p.get("kind") == "adr" and state == OPEN for p, state in parts)
    if repo is not None and adr_open and _adr_waits(repo, [p for p, _ in parts]):
        words = f"{words} · accept the ADR first" if words else "accept the ADR first"
    return words


def _bundle(
    card: str,
    parts: list[tuple[dict[str, object], str]],
    repo: Path | None,
    revising: str | None = None,
) -> DeskItem:
    """A card's open proposals as one desk item (F51 D1): the plan's title, the parts in reading
    order (F210 D8), each with its page and key points, the link to the first still to do.
    ``revising`` (F100): the owner's message waits for the lead, who may change them; they show
    dashed."""
    parts = reading_order(parts, lambda p: p[0])
    leading = next((p for p, _ in parts if p.get("kind") in ("plan", "replan")), parts[0][0])
    words = _proposal_words(parts, repo)
    todo = next((p for p, state in parts if state == OPEN), None)
    on_its_way = todo is None or revising is not None
    shown = parts[0][0] if todo is None else todo
    title = str(leading.get("title") or leading["id"])
    name = thread_name(card)
    if not re.match(rf"{re.escape(name)}\b", title, re.IGNORECASE):  # "F82: …" names it already
        title = f"{name}: {title}"
    return DeskItem(
        "proposals",
        title,
        _NEXT_PICK if todo is None else revising or words or str(shown.get("kind") or ""),
        f"/planning/{card}/proposals/{shown['id']}",
        on_its_way=on_its_way,
        parts=tuple(
            Part(
                _part_name(p),
                state == ON_ITS_WAY,
                f"/planning/{card}/proposals/{p['id']}",
                _key_points(p),
            )
            for p, state in parts
        ),
    )


def _listed(
    conn: sqlite3.Connection, project_id: int, known: set[str] | None = None
) -> list[tuple[str, datetime, list[tuple[dict[str, object], str]]]]:
    """Each thread not archived whose latest lead message listing proposals still has some
    open or on their way: its card, when the lead wrote it, and those proposals with their
    state, as listed. Oldest message first."""
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
    found = []
    for row in rows:
        since = _when(row["at"])
        later = [r for r in requests if _when(r["created"]) > since]
        parts: list[tuple[dict[str, object], str]] = []
        for proposal in json.loads(row["proposals"]):
            if not isinstance(proposal, dict) or not proposal.get("id"):
                continue
            if proposal.get(APPLIED) or _gone_merge(proposal, known):
                continue
            state = proposal_state(proposal, row["card"], later)
            if state in (OPEN, ON_ITS_WAY):
                parts.append((proposal, state))
        if parts:
            found.append((str(row["card"]), since, parts))
    return found


def _general_items(
    since: datetime,
    parts: list[tuple[dict[str, object], str]],
    now: datetime,
    revising: str | None,
) -> list[DeskItem]:
    """The general thread's open proposals, one item each (F51 D1): each takes its own press."""
    items = []
    for proposal, state in parts:
        points = _key_points(proposal)
        words = f"{points} key points" if points else ""
        if merged := _merge_words(proposal):
            words = f"{merged} · {words}" if words else merged
        asked = state == OPEN and revising is not None
        on_its_way = state == ON_ITS_WAY or asked
        if state == ON_ITS_WAY:
            words = _NEXT_PICK
        elif revising is not None:
            words = revising
        else:  # F108: when the lead proposed it
            words = f"{words or proposal.get('kind') or ''} · proposed {ago(now - since)} ago"
        items.append(
            DeskItem(
                "answers",
                str(proposal.get("title") or proposal["id"]),
                words,
                f"/planning/{GENERAL}/proposals/{proposal['id']}",
                on_its_way=on_its_way,
            )
        )
    return items


def _open_proposals(
    conn: sqlite3.Connection,
    project_id: int,
    now: datetime,
    known: set[str] | None = None,
    repo: Path | None = None,
    revising: dict[str, str] | None = None,
) -> list[DeskItem]:
    """The proposals in each thread's latest lead message that lists some, still open, on
    threads not archived: a card's make one item (F51 D1), the general thread's one each. The
    Overview's notices read them; the desk puts them in their card's box (F210 D1).
    ``revising`` (F100): the cards whose owner's message waits for the lead, with the words;
    their open proposals are on their way too."""
    revising = revising or {}
    items = []
    for card, since, parts in _listed(conn, project_id, known):
        if card == GENERAL:
            items += _general_items(since, parts, now, revising.get(card))
            continue
        item = _bundle(card, parts, repo, revising.get(card))
        if any(state == OPEN for _, state in parts):
            item = replace(item, words=item.words + f" · proposed {ago(now - since)} ago")
        items.append(item)
    return items


def _with_proposals(
    ripe: list[DeskItem],
    answers: list[DeskItem],
    listed: list[tuple[str, datetime, list[tuple[dict[str, object], str]]]],
    repo: Path | None,
    now: datetime,
    revising: Mapping[str, str],
) -> tuple[list[DeskItem], list[DeskItem]]:
    """F210 D1, D9: each card's open proposals join the row holding its conversation, ripe or
    an answer wanted, as one box: the conversation's words, then the proposals' (F108's
    "proposed N ago" goes: the words say when the lead replied). Dashed when the conversation
    is, or every proposal. A card with proposals and no conversation row is a box of its own,
    linking to its thread, after the answered ones, newest first; so are the general thread's,
    one each."""
    cards = {card: parts for card, _, parts in listed if card != GENERAL}

    def joined(item: DeskItem) -> DeskItem:
        card = item.link.removeprefix("/planning/")
        parts = cards.pop(card, None) if "/" not in card else None
        if parts is None:
            return item
        bundle = _bundle(card, parts, repo)
        said = _proposal_words(parts, repo)
        if card in revising and "being revised" not in item.words:  # F100: the lead may change them
            said = f"{said}, being revised" if said else "being revised"
        return replace(
            item,
            words=" · ".join(filter(None, [item.words, said])),
            parts=bundle.parts,
            on_its_way=item.on_its_way or all(p.on_its_way for p in bundle.parts),
        )

    ripe = [joined(item) for item in ripe]
    answers = [joined(item) for item in answers]
    alone: list[DeskItem] = []
    for card, since, parts in reversed(listed):
        if card == GENERAL:
            alone += _general_items(since, parts, now, revising.get(card))
        elif card in cards:
            bundle = _bundle(card, parts, repo, revising.get(card))
            words = bundle.words
            if any(state == OPEN for _, state in parts) and not bundle.on_its_way:
                words += f" · proposed {ago(now - since)} ago"
            alone.append(replace(bundle, group="answers", words=words, link=f"/planning/{card}"))
    answered = [a for a in answers if not a.on_its_way]
    dashed = [a for a in answers if a.on_its_way]
    return ripe, answered + alone + dashed


def _closing(conn: sqlite3.Connection, project_id: int, card: str, known: set[str] | None) -> bool:
    """F75: the runner will archive this thread at its next pick. It follows
    ``_close_if_settled``: every proposal of the latest set is approved, rejected, a merge that
    has left main (``_gone_merge``) or on its way, and at least one is on its way (D1). A pending
    reject on a draft takes every draft of the set (D2). An archived thread, or one with no
    proposals, is never closing."""
    found = metrics.find_thread(conn, project_id, card)
    if found is None or found["archived"] is not None:
        return False
    listed, asked = _latest(conn, project_id, found["id"])
    if not listed:
        return False
    kinds = {str(p["id"]): p.get("kind") for p in listed}
    drafts_go = any(
        r["kind"] == "reject"
        and r["done"] is None
        and str(r["subject"] or "").startswith(f"{card}/")
        and kinds.get(str(r["subject"]).partition("/")[2]) in DRAFTED
        for r in asked
    )
    on_its_way = False
    for proposal in listed:
        state = proposal_state(proposal, card, asked)
        if drafts_go and proposal.get("kind") in DRAFTED and state == OPEN:
            state = ON_ITS_WAY
        if state == ON_ITS_WAY:
            on_its_way = True
        elif state not in (APPROVED, REJECTED) and not _gone_merge(proposal, known):
            return False
    return on_its_way


def _ripe(
    conn: sqlite3.Connection, project: str, now: datetime, line: dict[str, Any] | None = None
) -> list[DeskItem]:
    """Every ticket done, its review written, and not signed off, as the line's field has
    them (F50 D1)."""
    if line is None:
        line = live_line(conn, project, now)
    items: list[DeskItem] = []
    for m in line["field"]["ripe"]:
        milestone_row = conn.execute(
            "SELECT id FROM milestones WHERE key = ?", (m["key"],)
        ).fetchone()
        milestone_id = milestone_row["id"] if milestone_row else 0
        row = conn.execute(
            "SELECT max(ended) as ended FROM jobs"
            " WHERE milestone_id = ? AND role = 'review' AND outcome != 'running'"
            " AND ended IS NOT NULL",
            (milestone_id,),
        ).fetchone()
        if row and row["ended"]:
            words = f"reviewed {ago(now - _when(row['ended']))} ago · waits for your sign-off"
        else:
            words = "reviewed · waits for your sign-off"
        items.append(
            DeskItem(
                "ripe",
                m["title"] or m["key"],
                words,
                f"/planning/{short_key(m['key'])}",
            )
        )
    return items


def _seeds(conn: sqlite3.Connection, project_id: int) -> list[DeskItem]:
    """Idea cards no thread is about yet, and no message on its way (F74 D4)."""
    threads = {
        r["card"]
        for r in conn.execute(
            "SELECT card FROM planner_threads WHERE project_id = ?", (project_id,)
        ).fetchall()
    } | set(_asked(conn, project_id))
    rows = conn.execute(
        "SELECT key, title FROM milestones WHERE project_id = ? AND state = 'idea' ORDER BY id",
        (project_id,),
    ).fetchall()
    return [
        DeskItem("seeds", r["title"] or r["key"], "an idea, not asked about yet", f"/planning/{k}")
        for r in rows
        if (k := short_key(r["key"])) not in threads
    ]


_WORK_ON_BRANCH = re.compile(r"\s*[.,;]\s*(?:its|the) work is on task/\S+", re.IGNORECASE)


@dataclass(frozen=True)
class BlockedFacts:
    """What the desk and a ticket's page say of a blocked ticket (f170-04)."""

    reason: str  # the runner's reason, without where its work is: the desk's line
    fix_card: str | None = None  # the thread the runner asked the lead on
    fix_first_point: str | None = None
    fix_replan: dict[str, object] | None = None
    lead_replied: bool = False

    @property
    def sentence(self) -> str:
        """The reason as a page shows it: its first letter raised, one full stop."""
        text = self.reason.rstrip(".")
        return f"{text[:1].upper()}{text[1:]}."


def get_blocked_info(conn: sqlite3.Connection, project_id: int, ticket: str) -> BlockedFacts | None:
    """The facts of ``ticket``'s open ``blocked`` item, or None when it has none.

    With the runner's look on the card's thread: whether the lead has replied since, the first
    point of that reply, and its replan while the owner can still approve it. A bug ticket with
    no card gets nothing extra.
    """
    row = conn.execute(
        "SELECT text FROM owner_items"
        " WHERE project_id = ? AND kind = ? AND subject = ? AND resolved IS NULL"
        " ORDER BY created, id DESC LIMIT 1",
        (project_id, "blocked", ticket),
    ).fetchone()
    if row is None:
        return None
    reason = row["text"].removeprefix(f"{ticket} blocked: ")
    # Find the latest runner message starting with "<ticket> blocked:" on this project
    runner = conn.execute(
        "SELECT m.at, m.thread_id, t.card FROM planner_messages m"
        " JOIN planner_threads t ON t.id = m.thread_id"
        " WHERE t.project_id = ? AND m.author = 'runner'"
        " AND m.text LIKE ?"
        " ORDER BY m.at DESC LIMIT 1",
        (project_id, f"{ticket} blocked:%"),
    ).fetchone()
    if runner is None:
        return BlockedFacts(reason)
    card = runner["card"]
    # Only "its work is on task/…" goes: "· N tickets wait behind it" may follow it
    reason = _WORK_ON_BRANCH.sub("", reason)
    # The lead's latest reply after the look, the one listing proposals if any does: what an
    # approval reads (metrics.latest_proposals), whatever else the lead has said since
    lead = conn.execute(
        "SELECT at, points, proposals FROM planner_messages"
        " WHERE thread_id = ? AND author = 'lead' AND at > ?"
        " ORDER BY proposals IS NOT NULL AND proposals != '[]' DESC, id DESC LIMIT 1",
        (runner["thread_id"], runner["at"]),
    ).fetchone()
    if lead is None:
        return BlockedFacts(reason, card)
    points = json.loads(lead["points"]) if lead["points"] else []
    since = _when(lead["at"])
    asked = [
        r
        for r in conn.execute(
            "SELECT * FROM owner_requests WHERE project_id = ? ORDER BY id", (project_id,)
        ).fetchall()
        if _when(r["created"]) > since
    ]
    fix_replan: dict[str, object] | None = None
    for prop in json.loads(lead["proposals"]) if lead["proposals"] else []:
        if (
            isinstance(prop, dict)
            and prop.get("kind") == "replan"
            and proposal_state(prop, card, asked) in (OPEN, ON_ITS_WAY)  # not once settled
        ):
            key_points = prop.get("key_points", [])
            fix_replan = {
                "title": str(prop.get("title", "")),
                "key_points": len(key_points) if isinstance(key_points, list) else 0,
            }
    return BlockedFacts(
        reason,
        card,
        str(points[0].get("title", "")) if points else None,
        fix_replan,
        lead_replied=True,
    )


def _blocked(conn: sqlite3.Connection, project_id: int) -> list[DeskItem]:
    """Open blocked tickets with their reason: one plain DeskItem per row, oldest first."""
    rows = conn.execute(
        "SELECT subject FROM owner_items"
        " WHERE project_id = ? AND kind = ? AND resolved IS NULL"
        " ORDER BY created, id",
        (project_id, "blocked"),
    ).fetchall()
    items: list[DeskItem] = []
    for r in rows:
        ticket = r["subject"]
        facts = get_blocked_info(conn, project_id, ticket)
        if facts is not None:  # each row is an open item, so it always finds it
            items.append(
                DeskItem(
                    "blocked",
                    ticket,
                    facts.reason,
                    f"/tickets/{ticket}",
                    fix_card=facts.fix_card,
                    fix_first_point=facts.fix_first_point,
                    fix_replan=facts.fix_replan,
                    lead_replied=facts.lead_replied,
                )
            )
    return items


def _put_aside(conn: sqlite3.Connection, project_id: int) -> dict[str, str]:
    """F73 D1: the threads the owner archived themselves while their latest lead message that
    lists proposals still has one open, each with what waits in it: ``1 ADR, 1 plan``."""
    rows = conn.execute(
        "SELECT t.card, m.at, m.proposals FROM planner_threads t"
        " JOIN planner_messages m ON m.id = ("
        "   SELECT max(id) FROM planner_messages WHERE thread_id = t.id AND author = 'lead'"
        "   AND proposals IS NOT NULL AND proposals != '[]')"
        " WHERE t.project_id = ? AND t.archived IS NOT NULL AND t.archived_why = ?",
        (project_id, BY_YOU),
    ).fetchall()
    requests = conn.execute(
        "SELECT * FROM owner_requests WHERE project_id = ? ORDER BY id", (project_id,)
    ).fetchall()
    waiting = {}
    for row in rows:
        since = _when(row["at"])
        later = [r for r in requests if _when(r["created"]) > since]
        kinds: dict[str, int] = {}
        for proposal in json.loads(row["proposals"]):
            if not isinstance(proposal, dict) or not proposal.get("id") or proposal.get(APPLIED):
                continue
            if proposal_state(proposal, row["card"], later) in (OPEN, ON_ITS_WAY):
                kind = str(proposal.get("kind") or "proposal")
                name = {"adr": "ADR", "mockup": "mock-up"}.get(kind, kind)
                kinds[name] = kinds.get(name, 0) + 1
        if kinds:
            waiting[row["card"]] = ", ".join(
                f"{n} {name}{'s' if n > 1 else ''}" for name, n in kinds.items()
            )
    return waiting


def _archived_threads(
    conn: sqlite3.Connection, project: str, now: datetime, aside: bool
) -> list[DeskItem]:
    """The archived threads set aside (``aside``) or not, the most recently archived first."""
    project_id = metrics.find_project(conn, project)
    if project_id is None:
        return []
    titles = _card_titles(conn, project_id)
    waiting = _put_aside(conn, project_id)
    rows = conn.execute(
        "SELECT card, archived, archived_why FROM planner_threads"
        " WHERE project_id = ? AND archived IS NOT NULL ORDER BY archived DESC, id DESC",
        (project_id,),
    ).fetchall()
    items = []
    for r in rows:
        if (r["card"] in waiting) != aside:
            continue
        when = ago(now - _when(r["archived"]))
        words = (
            f"{waiting[r['card']]} · set aside {when} ago"
            if aside
            else " · ".join(filter(None, [r["archived_why"], f"archived {when} ago"]))
        )
        items.append(
            DeskItem(
                "set aside" if aside else "archived",
                _thread_title(r["card"], titles),
                words,
                f"/planning/{r['card']}",
            )
        )
    return items


def archived(conn: sqlite3.Connection, project: str, now: datetime) -> list[DeskItem]:
    """The archived threads, the most recently archived first (the owner, 2026-10-07), but
    those set aside (F73). A message from the owner opens one again."""
    return _archived_threads(conn, project, now, aside=False)


def set_aside(conn: sqlite3.Connection, project: str, now: datetime) -> list[DeskItem]:
    """F73 D1: the threads the owner archived with a proposal still open, to come back to,
    the most recently archived first."""
    return _archived_threads(conn, project, now, aside=True)


def waiting_for_you(groups: list[DeskGroup]) -> list[DeskItem]:
    """The desk's items still waiting for the owner, in desk order: the Planning tab's count,
    Overview's Needs you and the arrows between pages (F35) read these. Seeds wait on no one
    (F103 D1): the desk lists them, but they are left out here."""
    return [
        item
        for group in groups
        if group.key != "seeds"
        for item in group.items
        if not item.on_its_way
    ]


def desk_trail(
    conn: sqlite3.Connection, project: str, now: datetime, path: str
) -> dict[str, object]:
    """F35, the owner's Previous and Next between what waits for them: the pages of the desk's
    items still waiting, in desk order (what didn't go through stays on /planning), each box's
    own page then its proposals not on their way (F210 D2). "N of M" counts boxes. A step inside
    a box names where it goes; one to another box says Previous or Next. On a page already
    done with, Next is the first one left."""
    steps: dict[str, tuple[int, str]] = {}  # each page: its box's number and its name
    boxes = 0
    for item in waiting_for_you(desk(conn, project, now)):
        if not item.link.startswith("/planning/") or item.link in steps:
            continue
        boxes += 1
        steps[item.link] = (boxes, "conversation")
        for part in item.parts:
            if not part.on_its_way and part.link not in steps:
                steps[part.link] = (boxes, part.name)
    links = list(steps)
    if path not in steps:
        return {
            "previous": None,
            "next": links[0] if links else None,
            "previous_label": "Previous",
            "next_label": "Next",
            "words": f"{boxes} waiting for you" if links else "Nothing else waits for you",
        }
    at = links.index(path)
    box = steps[path][0]
    previous = links[at - 1] if at > 0 else None
    after = links[at + 1] if at + 1 < len(links) else None
    inside_before = previous is not None and steps[previous][0] == box
    inside_after = after is not None and steps[after][0] == box
    return {
        "previous": previous,
        "next": after,
        "previous_label": _capital(steps[previous][1])
        if previous and inside_before
        else "Previous",
        "next_label": f"Next: {steps[after][1]}" if after and inside_after else "Next",
        "words": f"{box} of {boxes} waiting for you",
    }


def _capital(name: str) -> str:
    return name[:1].upper() + name[1:]


def _ripe_takes_its_thread(
    ripe: list[DeskItem], answers: list[DeskItem], revising: Mapping[str, str]
) -> tuple[list[DeskItem], list[DeskItem]]:
    """A ripe card's conversation is its one row in To sign off (F65 D8): dashed and being
    revised while the lead owes a reply, then the lead's reply and the sign-off it waits for.
    That conversation leaves Your answers wanted."""
    threads = {a.link: a for a in answers}
    taken: set[str] = set()
    rows: list[DeskItem] = []
    for item in ripe:
        thread = threads.get(item.link)
        if thread is None:
            rows.append(item)
            continue
        taken.add(item.link)
        if thread.on_its_way:
            card = item.link.removeprefix("/planning/")
            words = revising.get(card, "being revised")
            rows.append(replace(item, words=words, on_its_way=True, place=thread.place))
        else:
            rows.append(replace(item, words=f"{thread.words} · reviewed, waits for your sign-off"))
    return rows, [a for a in answers if a.link not in taken]


def desk(
    conn: sqlite3.Connection, project: str, now: datetime, *, line: dict[str, Any] | None = None
) -> list[DeskGroup]:
    """What waits for the owner (D6), in five groups in this order, empty ones included: what
    didn't go through first (F31 D9), blocked tickets (F106 D1), sign-offs, conversations
    (F185 D1), each card's with its open proposals in one box (F210 D1), and seeds."""
    project_id = metrics.find_project(conn, project)
    if project_id is None:
        refusals: list[DeskItem] = []
        ripe: list[DeskItem] = []
        answers: list[DeskItem] = []
        seeds: list[DeskItem] = []
        blocked: list[DeskItem] = []
    else:
        titles = _card_titles(conn, project_id)
        refusals = _refused(conn, project_id, titles)
        repo = _repo(conn, project)
        known = _known_cards(repo)
        revising = _revising(conn, project_id, project, now)
        ripe = _ripe(conn, project, now, line=line)
        answers = _answers_wanted(conn, project_id, project, titles, now)
        ripe, answers = _ripe_takes_its_thread(ripe, answers, revising)
        closing = {
            a.link.removeprefix("/planning/")
            for a in answers
            if not a.on_its_way
            and _closing(conn, project_id, a.link.removeprefix("/planning/"), known)
        }
        listed = _listed(conn, project_id, known)
        ripe, answers = _with_proposals(ripe, answers, listed, repo, now, revising)
        ripe = _acted_on(conn, project_id, ripe)
        answers = _acted_on(conn, project_id, answers, closing)
        seeds = _acted_on(conn, project_id, _seeds(conn, project_id))
        blocked = _acted_on(conn, project_id, _blocked(conn, project_id))
    return [
        DeskGroup("refused", "Didn't go through", "--hazard", refusals),
        DeskGroup("blocked", "Blocked tickets", "--hazard", blocked),
        DeskGroup("ripe", "To sign off", "--qwen", ripe),
        DeskGroup("answers", "Your answers wanted", "--hazard", answers),
        DeskGroup("seeds", "Seeds, not asked about yet", "--ink-2", seeds),
    ]


# --- the tiles ----------------------------------------------------------------------------


def factory_now(conn: sqlite3.Connection, project: str, now: datetime) -> dict[str, object]:
    """The tile: the running job, the reply being written and the replies in line after it
    (F84 D6), or when the next reply is expected."""
    jobs = [j for j in running_jobs(conn, project, now) if j.live]
    project_id = metrics.find_project(conn, project)
    pending = project_id is not None and any(
        r["kind"] == PLANNER for r in metrics.open_jobs(conn, project_id)
    )
    working = [j for j in jobs if j.role != PLANNER]
    places = reply_line(conn, project, now, jobs)
    thread = _writing(places)
    writing: dict[str, object] | None = None
    if thread is not None and project_id is not None:
        line = [p for p in places.values() if p.place > 0]
        ends = [p.done for p in line if p.done is not None]
        writing = {
            "thread": thread,
            "title": _thread_title(thread, _card_titles(conn, project_id)),
            "elapsed": places[thread].elapsed,
            "count": len(line),
            "all": max(ends) if line and len(ends) == len(line) else None,
        }
    return {
        "running": working[0] if working else None,
        "writing": writing,
        "next_reply": _next_reply(
            conn, project, jobs, pending, _held(conn, project_id, now), thread
        ),
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
            "set_aside": set_aside(conn, project, now),
        },
    )


# --- proposal review (f6-08) ----------------------------------------------------------------

_MOCKUP_RE = re.compile(r"\.softfield/cards/[^/]+-mockup/[^/].*")
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
        return f".softfield/cards/{match.group(1)}-mockup/{match.group(2)}"
    return None


def _repo(conn: sqlite3.Connection, project: str) -> Path | None:
    """The project's checkout; None when ``projects.repo`` isn't a folder here (a URL)."""
    row = conn.execute("SELECT repo FROM projects WHERE name = ?", (project,)).fetchone()
    repo = Path(row["repo"]) if row and row["repo"] else None
    return repo if repo and repo.is_dir() else None


def _adr_waits(
    repo: Path | None, proposals: list[dict[str, object]], accepting: frozenset[int] = frozenset()
) -> bool:
    """Whether the card has an ``adr`` proposal whose file on main is missing or still Proposed
    (as ``runner.requests`` reads it): Approve plan waits for it. An ADR in ``accepting`` has an
    open ``accept_adr`` request, which the runner applies before a later approval (F51 D2)."""
    for p in proposals:
        if p.get("kind") != "adr":
            continue
        number = _ADR_NUMBER.match(str(p.get("path") or ""))
        if number and int(number[1]) in accepting:
            continue
        path = str(p.get("path") or "")
        if path.startswith("docs/adr/"):
            # Old path: check if the exact file exists on main and is still Proposed
            if repo is None:
                return True
            main_path = repo / path
            if not main_path.exists():
                return True
            if is_proposed(main_path.read_text(encoding="utf-8")):
                return True
        else:
            found = (
                sorted((repo / ".softfield" / "adr").glob(f"{number[1]}-*.md"))
                if repo and number
                else []
            )
            if not found or is_proposed(found[0].read_text(encoding="utf-8")):
                return True
    return False
