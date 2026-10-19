"""The board's cards (f5 D4–D6, ADR 19 items 1–4): every milestone and every bug ticket, in
its growth stage. ``board`` returns plain data; ``/board`` (f5-16) draws it, read-only: a
column per stage, the totals, and a plain GET form for the search and the kind (``?q=``,
``?kind=``). ``milestone_card`` is one milestone's card, for its page (f5-17).

- **A milestone's stage** is derived from its thread and its tickets (D4), the first that
  holds: signed off → harvested; an idea no open thread is about (nor a message of the
  owner's on its way) → seed, as the desk's seeds; state planning, or an idea with one →
  sprouting, its note saying who the conversation waits for (F110 D4); every ticket done and the
  review's sheet stored → ripe, as the line's field has it; a ticket started → growing;
  otherwise → planted. Set-aside and removed tickets count for none of these.
- **A bug ticket's stage** is its ticket's state (ADR 19 item 2): set aside → seed, ready →
  planted, running or stopped → growing, done → harvested.
- **Left out:** a removed card, a removed ticket, and the ``bugs`` row (a standing key).
- **Order:** by priority, then key; harvested, the latest first, and only the latest
  ``HARVESTED``. A card in a stage of ``PLACED`` shows its place there, ``#1``… (F15 D1).
- **An order on its way** (F15 D4): while the latest ``reorder`` request is open, the cards
  come in its order (the cards it doesn't name after, in theirs), and each card it puts out of
  place says where it was. Places are counted before ``q`` and ``kind`` narrow the cards.
"""

import json
import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from factory_dashboard.app import Db, Now, Project, render
from factory_dashboard.line import _LONG_AGO, _natural, _when
from factory_dashboard.overview import running_jobs
from factory_dashboard.queries import ticket_priority
from runner import metrics
from runner.requests import REORDER
from runner.tasks import BUGS, DEFAULT_PRIORITY, short_key

router = APIRouter()

STAGES = ("seed", "sprouting", "planted", "growing", "ripe", "harvested")
# each stage's words on the page: its name, and what a card there is doing
WORDS = {
    "seed": ("Seed", "idea or set aside"),
    "sprouting": ("Sprouting", "being planned"),
    "planted": ("Planted", "tickets ready"),
    "growing": ("Growing", "in the factory"),
    "ripe": ("Ripe", "needs your sign-off"),
    "harvested": ("Harvested", "signed off or fixed"),
}
PLACED = ("seed", "sprouting", "planted", "growing")  # the stages whose order the owner sets
KINDS = ("factory", "product", "bug")
HARVESTED = 4  # the harvested cards shown; the rest are counted
SET_ASIDE = "ticket written, set aside"
STARTED = ("running", "done", "escalated", "blocked")  # a ticket's states once work began
_OFF = ("later", metrics.REMOVED)  # tickets that count for no stage


@dataclass(frozen=True)
class Work:
    """What runs now on a growing card."""

    ticket: str
    goal: str | None
    agent: str
    attempt: int


@dataclass(frozen=True)
class Card:
    key: str  # the short key in capitals, ``F5``; a bug's ticket id
    full_key: str  # for its link: the milestone's key, or the bug's ticket id
    title: str | None
    area: str  # factory or product
    bug: bool
    priority: int
    stage: str
    done: int = 0  # a milestone's tickets done, of ``total``
    total: int = 0  # set-aside ones aren't in it
    set_aside: int = 0
    note: str = ""
    running: Work | None = None  # on a growing card, from a live job
    place: int = 0  # its place in its stage, from 1; 0 in a stage not ``PLACED``
    on_its_way: bool = False  # an open reorder puts it out of place
    was: int = 0  # then, its place without the reorder

    @property
    def kind(self) -> str:
        """What the board's filter calls it: ``bug``, else its area."""
        return "bug" if self.bug else self.area


@dataclass(frozen=True)
class Board:
    stages: dict[str, list[Card]]  # every stage of ``STAGES``, in order
    more_harvested: int  # harvested cards beyond the ``HARVESTED`` shown


def _milestone_stage(
    m: sqlite3.Row, tickets: list[sqlite3.Row], threads: set[str], worked: set[int]
) -> str:
    """D4's rule, over the milestone's tickets that count."""
    if m["status"] == "done":
        return "harvested"
    if m["state"] == "idea" and short_key(m["key"]) not in threads:
        return "seed"
    if m["state"] in ("idea", "planning"):
        return "sprouting"
    if tickets and all(t["state"] == "done" for t in tickets) and m["signoff"] is not None:
        return "ripe"
    if any(t["state"] in STARTED or t["id"] in worked for t in tickets):
        return "growing"
    return "planted"


def _bug_stage(state: str | None, running: bool) -> str:
    if state == "later":
        return "seed"
    if state == "done":
        return "harvested"
    if running or state in ("running", "escalated", "blocked"):
        return "growing"
    return "planted"


def _card_note(
    key: str, stage: str, latest: Mapping[str, sqlite3.Row | None], sent: set[str]
) -> str:
    """Who a sprouting card's conversation waits for (D4). The owner's message still on its
    way to the runner counts as theirs at once (the owner, 2026-10-07)."""
    if stage != "sprouting":
        return ""
    if key in sent:
        return "the lead is answering"
    msg = latest.get(key)
    if msg is None:
        return ""
    if msg["author"] == "lead":
        return f"waits for your answer since {_when(msg['at']).strftime('%-d %b')}"
    if msg["author"] == "owner":
        return "the lead is answering"
    return ""


def _matches(card: Card, q: str | None, kind: str | None) -> bool:
    if kind and card.kind != kind:
        return False
    word = (q or "").strip().lower()
    return not word or word in card.key.lower() or word in (card.title or "").lower()


def _cards(conn: sqlite3.Connection, project: str, now: datetime) -> list[tuple[Card, datetime]]:
    """Every card of the project's, with when it was harvested. ``now`` tells which jobs are
    live."""
    milestones = conn.execute(
        "SELECT m.* FROM milestones m JOIN projects p ON p.id = m.project_id WHERE p.name = ?",
        (project,),
    ).fetchall()
    tickets: dict[int, list[sqlite3.Row]] = {}
    for t in conn.execute(
        "SELECT t.* FROM tickets t JOIN projects p ON p.id = t.project_id"
        " WHERE p.name = ? AND t.milestone_id IS NOT NULL AND t.state IS NOT ? ORDER BY t.ticket",
        (project, metrics.REMOVED),
    ):
        tickets.setdefault(t["milestone_id"], []).append(t)
    threads = {
        r["card"]
        for r in conn.execute(
            "SELECT t.card FROM planner_threads t JOIN projects p ON p.id = t.project_id"
            " WHERE p.name = ? AND t.archived IS NULL",
            (project,),
        )
    }
    # the owner's messages not yet picked up: one opens an archived thread again
    sent = {
        r["subject"]
        for r in conn.execute(
            "SELECT r.subject FROM owner_requests r JOIN projects p ON p.id = r.project_id"
            " WHERE p.name = ? AND r.kind = 'plan_message' AND r.done IS NULL",
            (project,),
        )
    }
    threads |= sent
    latest_messages: dict[str, sqlite3.Row] = {}
    for r in conn.execute(
        "SELECT t.card, m.author, m.at FROM planner_messages m"
        " JOIN planner_threads t ON t.id = m.thread_id"
        " WHERE t.archived IS NULL AND t.project_id IN"
        "   (SELECT id FROM projects WHERE name = ?)"
        " AND m.id = (SELECT max(id) FROM planner_messages WHERE thread_id = t.id)",
        (project,),
    ):
        latest_messages[r["card"]] = r
    # each ticket's jobs: that it has one, whether one still runs, when the latest ended
    worked: set[int] = set()
    at_work: set[int] = set()
    ended: dict[int, datetime] = {}
    for j in conn.execute(
        "SELECT j.ticket_id, j.outcome, j.ended FROM jobs j JOIN runs r ON r.id = j.run_id"
        " JOIN projects p ON p.id = r.project_id WHERE p.name = ? AND j.ticket_id IS NOT NULL"
        " AND coalesce(r.command, '') != 'bench'",
        (project,),
    ):
        worked.add(j["ticket_id"])
        if j["outcome"] == "running":
            at_work.add(j["ticket_id"])
        if j["ended"]:
            ended[j["ticket_id"]] = max(_when(j["ended"]), ended.get(j["ticket_id"], _LONG_AGO))
    live: dict[str, Work] = {}  # by ticket, its oldest live job
    for job in running_jobs(conn, project, now):
        if job.live and job.ticket:
            live.setdefault(job.ticket, Work(job.ticket, job.title, job.agent, job.attempt))

    def running(own: list[sqlite3.Row]) -> Work | None:
        names = {t["ticket"] for t in own}
        return next((work for ticket, work in live.items() if ticket in names), None)

    found: list[tuple[Card, datetime]] = []  # each card, and when it was harvested
    for m in milestones:
        own = tickets.get(m["id"], [])
        if m["key"] == BUGS:
            for t in own:
                stage = _bug_stage(t["state"], t["id"] in at_work)
                card = Card(
                    key=t["ticket"],
                    full_key=t["ticket"],
                    title=t["title"],
                    area=t["area"] or "",
                    bug=True,
                    priority=ticket_priority(t["body"], BUGS, None),
                    stage=stage,
                    note=SET_ASIDE if stage == "seed" else "",
                    running=running([t]) if stage == "growing" else None,
                )
                found.append((card, ended.get(t["id"], _LONG_AGO)))
            continue
        if m["state"] == metrics.REMOVED:
            continue
        counted = [t for t in own if t["state"] not in _OFF]
        stage = _milestone_stage(m, counted, threads, worked)
        key = short_key(m["key"]).upper()
        card = Card(
            key=key,
            full_key=m["key"],
            title=m["title"],
            area=m["area"] or ("factory" if m["key"].startswith("f") else "product"),
            bug=False,
            priority=DEFAULT_PRIORITY if m["priority"] is None else m["priority"],
            stage=stage,
            done=sum(t["state"] == "done" for t in counted),
            total=len(counted),
            set_aside=sum(t["state"] == "later" for t in own),
            note=_card_note(key.lower(), stage, latest_messages, sent),
            running=running(counted) if stage == "growing" else None,
        )
        found.append((card, _when(m["ended"]) if m["ended"] else _LONG_AGO))
    return found


def milestone_card(conn: sqlite3.Connection, project: str, now: datetime, key: str) -> Card | None:
    """The card of the milestone with this full key, for its page (f5-17); None for a removed
    one. The board keeps only the latest harvested cards; this finds any."""
    return next((c for c, _ in _cards(conn, project, now) if not c.bug and c.full_key == key), None)


def _order_on_its_way(conn: sqlite3.Connection, project: str) -> list[str] | None:
    """The keys of the latest open ``reorder``, as sent; None when none waits or the runner
    will refuse it (not a list of keys)."""
    row = conn.execute(
        "SELECT r.value FROM owner_requests r JOIN projects p ON p.id = r.project_id"
        " WHERE p.name = ? AND r.kind = ? AND r.done IS NULL ORDER BY r.id DESC LIMIT 1",
        (project, REORDER),
    ).fetchone()
    if row is None:
        return None
    try:
        keys = json.loads(row["value"] or "")
    except ValueError:
        return None
    if not isinstance(keys, list) or not all(isinstance(key, str) for key in keys):
        return None
    return keys


def _out_of_place(before: list[str], after: list[str]) -> set[str]:
    """The keys outside the longest run ``before`` and ``after`` share (F15 D3): a card whose
    neighbours moved past it is not out of place. Of two equally long runs, the one kept
    leaves out the card that came up: swapping two, the one moved up is out of place."""
    n, m = len(before), len(after)
    run = [[0] * (m + 1) for _ in range(n + 1)]  # run[i][j]: the longest of before[i:], after[j:]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            if before[i] == after[j]:
                run[i][j] = run[i + 1][j + 1] + 1
            else:
                run[i][j] = max(run[i + 1][j], run[i][j + 1])
    kept: set[str] = set()
    i = j = 0
    while i < n and j < m:
        if before[i] == after[j]:
            kept.add(before[i])
            i, j = i + 1, j + 1
        elif run[i][j + 1] >= run[i + 1][j]:
            j += 1
        else:
            i += 1
    return set(after) - kept


def _placed(
    conn: sqlite3.Connection, project: str, found: list[tuple[Card, datetime]]
) -> list[tuple[Card, datetime]]:
    """The cards in the board's order, each with its place in its stage, and an open reorder's
    order with its marks (F15 D1, D4)."""
    line = sorted(found, key=lambda c: (c[0].priority, _natural(c[0].key.lower())))
    sent = _order_on_its_way(conn, project)
    shown = line
    if sent is not None:
        rank = {key: n for n, key in enumerate(sent)}
        shown = sorted(line, key=lambda c: rank.get(c[0].key.lower(), len(rank)))  # stable
    placed: dict[str, Card] = {}
    for stage in PLACED:
        before = [card.key for card, _ in line if card.stage == stage]
        cards = [card for card, _ in shown if card.stage == stage]
        moved = _out_of_place(before, [card.key for card in cards])
        for n, card in enumerate(cards, start=1):
            if card.key in moved:
                was = before.index(card.key) + 1
                placed[card.key] = replace(card, place=n, on_its_way=True, was=was)
            else:
                placed[card.key] = replace(card, place=n)
    return [(placed.get(card.key, card), at) for card, at in shown]


def board(
    conn: sqlite3.Connection,
    project: str,
    now: datetime,
    q: str | None = None,
    kind: str | None = None,
) -> Board:
    """The project's cards by stage. ``q`` keeps the cards whose key or title contains it,
    whatever the case; ``kind`` is one of ``KINDS``. ``now`` tells which jobs are live."""
    found = _placed(conn, project, _cards(conn, project, now))
    kept = [(card, at) for card, at in found if _matches(card, q, kind)]
    stages: dict[str, list[Card]] = {stage: [] for stage in STAGES}
    for card, _ in kept:
        if card.stage != "harvested":
            stages[card.stage].append(card)
    harvested = sorted(  # the latest first
        (c for c in kept if c[0].stage == "harvested"), key=lambda c: c[1], reverse=True
    )
    stages["harvested"] = [card for card, _ in harvested[:HARVESTED]]
    return Board(stages, max(len(harvested) - HARVESTED, 0))


# --- the page (f5-16) ---------------------------------------------------------------------


@dataclass(frozen=True)
class Total:
    count: int
    label: str
    ripe: bool = False  # the one that waits for the owner


def _some(count: int, word: str) -> str:
    return f"{count} {word}{'' if count == 1 else 's'}"


def totals(found: Board) -> list[Total]:
    """The strip above the field: each stage's cards, then the tickets set aside on them."""
    seeds = found.stages["seed"]
    bugs = sum(card.bug for card in seeds)
    counts = {stage: len(cards) for stage, cards in found.stages.items()}
    return [
        Total(counts["seed"], f"Seeds: {_some(len(seeds) - bugs, 'idea')}, {_some(bugs, 'bug')}"),
        *(
            Total(
                counts[stage], ": ".join(WORDS[stage]), ripe=stage == "ripe" and counts[stage] > 0
            )
            for stage in ("sprouting", "planted", "growing", "ripe")
        ),
        Total(counts["harvested"] + found.more_harvested, "Harvested"),
        Total(
            sum(card.set_aside for cards in found.stages.values() for card in cards),
            "Tickets set aside",
        ),
    ]


@router.get("/board", response_class=HTMLResponse)
def board_page(
    request: Request,
    conn: Db,
    project: Project,
    now: Now,
    q: str | None = None,
    kind: str | None = None,
) -> HTMLResponse:
    kind = kind if kind in KINDS else ""  # anything else shows every kind
    found = board(conn, project, now, q=q, kind=kind)
    return render(
        request,
        conn,
        project,
        "board.html",
        {
            "active": "/board",
            "found": found,
            "words": WORDS,
            "totals": totals(found),
            "search": q or "",  # ``q`` is the links' ``?project=`` in every template
            "kind": kind,
            "kinds": [("", "All"), ("factory", "Factory"), ("product", "Product"), ("bug", "Bugs")],
        },
    )
