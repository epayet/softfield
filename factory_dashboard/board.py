"""The board's cards (f5 D4–D6, ADR 19 items 1–4): every milestone and every bug ticket, in
its growth stage. ``board`` returns plain data; ``/board`` (f5-16) draws it: a column per
stage, a plot per stage with its count (F15 D2), and a plain GET form for the search and the
kind (``?q=``, ``?kind=``). Its script moves cards and sends the whole order as one
``reorder`` (F15 D1, D3), through ``POST /requests``. ``milestone_card`` is one milestone's
card, for its page (f5-17).

- **A milestone's stage** is derived from its thread and its tickets (D4), the first that
  holds: signed off → harvested; an idea no open thread is about (nor a message of the
  owner's on its way) → seed, as the desk's seeds; state planning, or an idea with one →
  sprouting, its note saying who the conversation waits for (F110 D4); every ticket done and the
  review's sheet stored → ripe, as the line's field has it; otherwise → planted, ``started``
  once a ticket has (F154 D1). Set-aside and removed tickets count for none of these.
- **A bug ticket's stage** is its ticket's state (ADR 19 item 2): set aside → seed, ready →
  planted, running or stopped → planted and started, done → harvested.
- **Left out:** a removed card, a removed ticket, and the ``bugs`` row (a standing key).
- **Order:** by priority, then key; harvested, the latest first, and only the latest
  ``HARVESTED``. A card in a stage of ``PLACED`` shows its place there, ``#1``… (F15 D1).
- **An order on its way** (F15 D4): while the latest ``reorder`` request is open, the cards
  come in its order (the cards it doesn't name after, in theirs), and each card it puts out of
  place says where it was. Places are counted before ``q`` and ``kind`` narrow the cards.
"""

import json
import sqlite3
import statistics
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from factory_dashboard.app import Db, Now, Project, render
from factory_dashboard.line import _LONG_AGO, _natural, _when
from factory_dashboard.overview import Running, running_jobs
from factory_dashboard.queries import depends_on, local, ticket_priority
from runner import metrics
from runner.config import read_protected
from runner.loop import ticket_minutes
from runner.milestone import card as milestone_header
from runner.requests import REORDER
from runner.router import lead_only
from runner.tasks import BUGS, DEFAULT_PRIORITY, milestone_file, short_key

router = APIRouter()

STAGES = ("seed", "sprouting", "planted", "ripe", "harvested")
# each stage's words on the page (F154 D2): its name, what a card there is doing, and what
# moves it on ("" for the last)
WORDS = {
    "seed": ("Seed", "an idea, or a ticket set aside", "a conversation with the lead plans it"),
    "sprouting": ("Sprouting", "being planned with the lead", "you approve the plan"),
    "planted": ("Planted", "in line for the factory", "every ticket done, then Claude reviews it"),
    "ripe": ("Ripe", "needs your sign-off", "you sign off"),
    "harvested": ("Harvested", "signed off or fixed", ""),
}
PLACED = ("seed", "sprouting", "planted")  # the stages whose order the owner sets
RESERVABLE = ("planted",)  # the stages a card may be marked to use the reserve in
KINDS = ("factory", "product", "bug")
HARVESTED = 4  # the harvested cards shown; the rest are counted
SET_ASIDE = "Set aside, won't run until you queue it ›"  # its card's action (F159)
STARTED = ("running", "done", "escalated", "blocked")  # a ticket's states once work began
_OFF = ("later", metrics.REMOVED)  # tickets that count for no stage


@dataclass(frozen=True)
class Work:
    """What runs now on a planted card."""

    ticket: str
    goal: str | None
    agent: str
    attempt: int


@dataclass(frozen=True)
class ReviewStep:
    """The review step on a started card whose tickets are all done."""

    label: str
    text: str


@dataclass(frozen=True)
class DevWork:
    """What a planted card holds for the developers (F146 D4)."""

    look: str  # ``can``, ``waits`` or ``none`` (D3)
    now: int = 0  # developer tickets that can start now
    after: int = 0  # ... that can run once developer tickets before them have
    waiting: int = 0  # ... that wait for a lead ticket
    waits_for: tuple[str, ...] = ()  # those lead tickets, in id order
    # on a ``can`` card: the first lead ticket left, else ``review``; ``review`` too on a card
    # whose every ticket is done
    then: str | None = None


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
    started: bool = False  # a planted card with a ticket started: it says "growing" (F154 D3)
    running: Work | None = None  # on a planted card, from a live job
    review_step: ReviewStep | None = None  # on a started card with all tickets done
    place: int = 0  # its place in its stage, from 1; 0 in a stage not ``PLACED``
    on_its_way: bool = False  # an open reorder puts it out of place
    was: int = 0  # then, its place without the reorder
    waits: tuple[str, ...] = ()  # other card keys this card's ready tickets depend on
    reserve: bool = False  # a planted card marked to use Claude's reserve (F172 D6)
    developers: DevWork | None = None  # its developer work; None outside the developers' view
    thread: str = ""  # its conversation's short key, lower case; "" for a bug or none (f15-06)
    setting_aside: bool = False  # an open request sets its thread aside

    @property
    def kind(self) -> str:
        """What the board's filter calls it: ``bug``, else its area."""
        return "bug" if self.bug else self.area


@dataclass(frozen=True)
class Board:
    stages: dict[str, list[Card]]  # every stage of ``STAGES``, in order
    more_harvested: int  # harvested cards beyond the ``HARVESTED`` shown
    # every card not harvested, in the order shown, whatever ``q`` and ``kind`` keep: the key a
    # reorder names it by, and its stage. The page sends it whole, with its moves (F15 D10)
    line: tuple[tuple[str, str], ...] = ()
    # with the developers' view: the planted cards developers can work on, their tickets, and the
    # minutes that work takes (the median merged ticket's, None with no merged ticket) (F146 D4)
    developers: tuple[int, int, float | None] = (0, 0, None)


def _developer_ticket(row: sqlite3.Row, protected: list[str]) -> bool:
    """Whether the developers take this ticket: the runner's rule (F146 D1)."""
    files = json.loads(row["files"]) if row["files"] else []
    return not lead_only(row["kind"] or "", files, protected)


def _dev_resolver(
    rows: dict[str, sqlite3.Row], protected: list[str]
) -> Callable[[sqlite3.Row], frozenset[str]]:
    """For a ready developer ticket, the unfinished lead-side tickets it waits for, directly or
    through other developer tickets: none means developers alone can run it (F146 D2). A
    dependency that isn't a ready developer ticket (set aside, blocked, unknown) is named."""
    seen: dict[str, frozenset[str]] = {}

    def leads(row: sqlite3.Row) -> frozenset[str]:
        name = row["ticket"]
        if name in seen:
            return seen[name]
        seen[name] = frozenset()  # a cycle adds nothing
        found: set[str] = set()
        for dep in depends_on(row):
            other = rows.get(dep)
            if other is not None and other["state"] == "done":
                continue
            if (
                other is not None
                and other["state"] == "ready"
                and _developer_ticket(other, protected)
            ):
                found |= leads(other)
            else:
                found.add(dep)
        seen[name] = frozenset(found)
        return seen[name]

    return leads


def _dev_work(
    own: list[sqlite3.Row],
    rows: dict[str, sqlite3.Row],
    leads: Callable[[sqlite3.Row], frozenset[str]],
    protected: list[str],
) -> DevWork:
    """D3 and D4's line for one card's tickets (set-aside and removed ones already left out)."""
    now = after = waiting = 0
    waits_for: set[str] = set()
    for t in own:
        if t["state"] != "ready" or not _developer_ticket(t, protected):
            continue
        named = leads(t)
        if named:
            waiting += 1
            waits_for |= named
        elif all(rows.get(d) is not None and rows[d]["state"] == "done" for d in depends_on(t)):
            now += 1
        else:
            after += 1
    if now + after == 0 and waiting == 0:
        # every ticket done: what is left is Claude's review, not the lead's tickets
        done = bool(own) and all(t["state"] == "done" for t in own)
        return DevWork("none", then="review" if done else None)
    look = "can" if now + after else "waits"
    then = None
    if look == "can":
        left = [t for t in own if t["state"] != "done" and not _developer_ticket(t, protected)]
        then = left[0]["ticket"] if left else "review"
    return DevWork(look, now, after, waiting, tuple(sorted(waits_for)), then)


def _milestone_stage(m: sqlite3.Row, tickets: list[sqlite3.Row], threads: set[str]) -> str:
    """D4's rule, over the milestone's tickets that count."""
    if m["status"] == "done":
        return "harvested"
    if m["state"] == "idea" and short_key(m["key"]) not in threads:
        return "seed"
    if m["state"] in ("idea", "planning"):
        return "sprouting"
    if tickets and all(t["state"] == "done" for t in tickets) and m["signoff"] is not None:
        return "ripe"
    return "planted"


def _milestone_started(tickets: list[sqlite3.Row], worked: set[int]) -> bool:
    """Whether a planted milestone has a ticket started (F154 D1)."""
    return any(t["state"] in STARTED or t["id"] in worked for t in tickets)


def _review_step(
    milestone_full_key: str,
    started: bool,
    done: int,
    total: int,
    signoff: object,
    live_jobs: list[Running],
    stop_items: dict[str, str],
) -> ReviewStep | None:
    """The review step on a started planted card whose counted tickets are all done.

    Only applies when every ticket is done and the review's sheet isn't stored yet.
    """
    if not started or done != total or signoff is not None:
        return None
    short = short_key(milestone_full_key)
    # live review job on this milestone
    for job in live_jobs:
        if job.role == "review" and job.milestone == milestone_full_key:
            return ReviewStep(
                label="Review running",
                text=f"{job.agent} reads the work · then it's yours to sign off",
            )
    # unresolved review-stop item
    if short in stop_items:
        return ReviewStep(
            label="Review stopped",
            text=f"{stop_items[short]} · shown under Needs you",
        )
    return ReviewStep(
        label="Review next",
        text="Claude reviews it before the next ticket · then it's yours to sign off",
    )


def _bug_stage(state: str | None) -> str:
    if state == "later":
        return "seed"
    if state == "done":
        return "harvested"
    return "planted"


def _bug_started(state: str | None, running: bool) -> bool:
    """Whether a planted bug runs or has stopped (F154 D1)."""
    return state not in ("later", "done") and (
        running or state in ("running", "escalated", "blocked")
    )


def _card_waits(
    tickets: list[sqlite3.Row],
    all_name_to_mkey: dict[str, str],
    done: set[str],
    own_key: str,
) -> tuple[str, ...]:
    """The other card keys a milestone's ready tickets depend on, in key order, each once (a
    bug ticket by its id, as its card is named). Empty when any ready ticket can start or only
    depends on its own milestone."""
    ready = [t for t in tickets if t["state"] == "ready"]
    if not ready:
        return ()
    # if any ready ticket can start (no deps or all deps done), card waits for nothing
    for t in ready:
        deps = depends_on(t)
        if not deps or all(d in done for d in deps):
            return ()
    # collect the other card keys from unfinished deps
    others: set[str] = set()
    for t in ready:
        for dep in depends_on(t):
            m = all_name_to_mkey.get(dep)
            if m is None:
                continue
            if m != own_key and dep not in done:
                others.add(dep if m == BUGS else m.upper())  # a bug's card is its ticket
    return tuple(sorted(others))


def _card_note(
    key: str,
    stage: str,
    latest: Mapping[str, sqlite3.Row | None],
    sent: set[str],
    waits: tuple[str, ...] = (),
) -> str:
    """Who a sprouting card's conversation waits for (D4). The owner's message still on its
    way to the runner counts as theirs at once (the owner, 2026-10-07). For planted cards,
    a "waits for F22" line when its ready tickets depend on other cards."""
    if stage != "sprouting":
        if stage == "planted" and waits:
            return f"waits for {', '.join(waits)}"
        return ""
    if key in sent:
        return "the lead is answering"
    msg = latest.get(key)
    if msg is None:
        return ""
    if msg["author"] == "lead":
        return f"waits for your answer since {local(msg['at']).strftime('%-d %b')}"
    if msg["author"] == "owner":
        return "the lead is answering"
    return ""


def marked(repo: Path | None, key: str) -> bool:
    """Whether the card doc of this full key says ``**Reserve:** yes`` (F172 D1), read as
    ``loop.reserve_cards`` reads it: the mark is in no table. No checkout or no doc: no."""
    if repo is None:
        return False
    doc = milestone_file(repo, "cards", key)
    return doc.is_file() and milestone_header(key, doc.read_text(encoding="utf-8")).reserve


def _matches(card: Card, q: str | None, kind: str | None) -> bool:
    if kind and card.kind != kind:
        return False
    word = (q or "").strip().lower()
    return not word or word in card.key.lower() or word in (card.title or "").lower()


def _cards(
    conn: sqlite3.Connection, project: str, now: datetime, developers: bool = False
) -> list[tuple[Card, datetime]]:
    """Every card of the project's, with when it was harvested. ``now`` tells which jobs are
    live. ``developers`` fills each card's ``developers`` (F146)."""
    from factory_dashboard.planning import _repo  # planning.py imports this module

    repo = _repo(conn, project)
    protected: list[str] = []
    if repo is not None:
        try:
            protected = read_protected(repo)
        except OSError:
            protected = []
    milestones = conn.execute(
        "SELECT m.*, m.state FROM milestones m JOIN projects p ON p.id = m.project_id"
        " WHERE p.name = ?",
        (project,),
    ).fetchall()
    mkey: dict[int, str] = {}  # milestone id → its short key (lowercase)
    for m in milestones:
        mkey[m["id"]] = short_key(m["key"]).lower()
    tickets: dict[int, list[sqlite3.Row]] = {}
    all_name_to_mkey: dict[str, str] = {}  # ticket name → milestone's short key
    done_tickets: set[str] = set()
    by_name: dict[str, sqlite3.Row] = {}
    for t in conn.execute(
        "SELECT t.* FROM tickets t JOIN projects p ON p.id = t.project_id"
        " WHERE p.name = ? AND t.milestone_id IS NOT NULL AND t.state IS NOT ? ORDER BY t.ticket",
        (project, metrics.REMOVED),
    ):
        tickets.setdefault(t["milestone_id"], []).append(t)
        all_name_to_mkey[t["ticket"]] = mkey[t["milestone_id"]]
        if t["state"] == "done":
            done_tickets.add(t["ticket"])
        by_name[t["ticket"]] = t
    leads = _dev_resolver(by_name, protected)

    def dev_work(stage: str, own: list[sqlite3.Row]) -> DevWork | None:
        if not developers:
            return None
        if stage != "planted":
            return DevWork("none")
        return _dev_work([t for t in own if t["state"] not in _OFF], by_name, leads, protected)

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
    # the threads a set-aside request waits on, as thread.py finds one (f15-06)
    setting_aside = {
        r["subject"]
        for r in conn.execute(
            "SELECT r.subject FROM owner_requests r JOIN projects p ON p.id = r.project_id"
            " WHERE p.name = ? AND r.kind = 'archive' AND r.value = 'on' AND r.done IS NULL",
            (project,),
        )
    }
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
    all_jobs: list[Running] = []  # every live job, once for the whole board
    for job in running_jobs(conn, project, now):
        all_jobs.append(job)
        if job.live and job.ticket:
            live.setdefault(job.ticket, Work(job.ticket, job.title, job.agent, job.attempt))
    # unresolved review-stop items, by milestone key
    stop_items: dict[str, str] = {}
    for r in conn.execute(
        "SELECT subject, text FROM owner_items"
        " JOIN projects p ON p.id = owner_items.project_id"
        " WHERE p.name = ? AND kind = 'review-stop' AND resolved IS NULL",
        (project,),
    ):
        mk = short_key(r["subject"])
        stop_items[mk] = r["text"] or ""

    def running(own: list[sqlite3.Row]) -> Work | None:
        names = {t["ticket"] for t in own}
        return next((work for ticket, work in live.items() if ticket in names), None)

    found: list[tuple[Card, datetime]] = []  # each card, and when it was harvested
    for m in milestones:
        if (
            m["state"] is None
            and m["ended"] is None
            and m["status"] != "done"
            and m["id"] not in tickets
        ):
            continue
        own = tickets.get(m["id"], [])
        if m["key"] == BUGS:
            for t in own:
                stage = _bug_stage(t["state"])
                started = _bug_started(t["state"], t["id"] in at_work)
                card = Card(
                    key=t["ticket"],
                    full_key=t["ticket"],
                    title=t["title"],
                    area=t["area"] or "",
                    bug=True,
                    priority=ticket_priority(t["body"], BUGS, None),
                    stage=stage,
                    note=SET_ASIDE if stage == "seed" else "",
                    started=started,
                    running=running([t]) if stage == "planted" else None,
                    developers=dev_work(stage, [t]),
                )
                found.append((card, ended.get(t["id"], _LONG_AGO)))
            continue
        if m["state"] == metrics.REMOVED:
            continue
        counted = [t for t in own if t["state"] not in _OFF]
        stage = _milestone_stage(m, counted, threads)
        started = stage == "planted" and _milestone_started(counted, worked)
        key = short_key(m["key"]).upper()
        if stage == "planted":
            waits = _card_waits(own, all_name_to_mkey, done_tickets, mkey[m["id"]])
        else:
            waits = ()
        thread = key.lower() if key.lower() in threads else ""
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
            note=_card_note(key.lower(), stage, latest_messages, sent, waits),
            waits=waits,
            reserve=stage in RESERVABLE and marked(repo, m["key"]),
            started=started,
            running=running(counted) if stage == "planted" else None,
            developers=dev_work(stage, own),
            thread=thread,
            setting_aside=bool(thread) and thread in setting_aside,
            review_step=_review_step(
                m["key"],
                started,
                sum(t["state"] == "done" for t in counted),
                len(counted),
                m["signoff"],
                all_jobs,
                stop_items,
            ),
        )
        found.append((card, _when(m["ended"]) if m["ended"] else _LONG_AGO))
    return found


def milestone_card(conn: sqlite3.Connection, project: str, now: datetime, key: str) -> Card | None:
    """The card of the milestone with this full key, for its page (f5-17); None for a removed
    one. The board keeps only the latest harvested cards; this finds any."""
    return next((c for c in milestone_cards(conn, project, now) if c.full_key == key), None)


def milestone_cards(conn: sqlite3.Connection, project: str, now: datetime) -> list[Card]:
    """Every milestone's card, bugs left out, in no particular order."""
    return [c for c, _ in _cards(conn, project, now) if not c.bug]


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
    developers: bool = False,
) -> Board:
    """The project's cards by stage. ``q`` keeps the cards whose key or title contains it,
    whatever the case; ``kind`` is one of ``KINDS``. ``now`` tells which jobs are live.
    ``developers`` adds each card's developer work and the board's totals (F146 D4)."""
    found = _placed(conn, project, _cards(conn, project, now, developers))
    kept = [(card, at) for card, at in found if _matches(card, q, kind)]
    stages: dict[str, list[Card]] = {stage: [] for stage in STAGES}
    for card, _ in kept:
        if card.stage != "harvested":
            stages[card.stage].append(card)
    harvested = sorted(  # the latest first
        (c for c in kept if c[0].stage == "harvested"), key=lambda c: c[1], reverse=True
    )
    stages["harvested"] = [card for card, _ in harvested[:HARVESTED]]
    line = tuple((card.key.lower(), card.stage) for card, _ in found if card.stage != "harvested")
    return Board(
        stages,
        max(len(harvested) - HARVESTED, 0),
        line,
        _developer_totals(conn, project, [card for card, _ in found])
        if developers
        else (0, 0, None),
    )


def _developer_totals(
    conn: sqlite3.Connection, project: str, cards: list[Card]
) -> tuple[int, int, float | None]:
    """The cards of look ``can``, their tickets, and those tickets' minutes (F146 D4)."""
    can = [c.developers for c in cards if c.developers and c.developers.look == "can"]
    tickets = sum(d.now + d.after for d in can)
    row = conn.execute("SELECT id FROM projects WHERE name = ?", (project,)).fetchone()
    minutes = ticket_minutes(conn, row["id"]) if row else []
    return len(can), tickets, tickets * statistics.median(minutes) if minutes else None


def reserve_marked(conn: sqlite3.Connection, project: str, now: datetime) -> list[Card]:
    """The planted cards marked to use Claude's reserve, in the board's order: the
    Overview names them under Claude's meters (F172 D6)."""
    found = board(conn, project, now)
    return [c for stage in RESERVABLE for c in found.stages[stage] if c.reserve]


# --- the page (f5-16) ---------------------------------------------------------------------


@router.get("/board", response_class=HTMLResponse)
def board_page(
    request: Request,
    conn: Db,
    project: Project,
    now: Now,
    q: str | None = None,
    kind: str | None = None,
    view: str | None = None,
) -> HTMLResponse:
    kind = kind if kind in KINDS else ""  # anything else shows every kind
    view = "developers" if view == "developers" else ""  # anything else is the normal board
    found = board(conn, project, now, q=q, kind=kind, developers=bool(view))
    # the lever is a link to the other view, keeping the project, the search and the kind (D5)
    lever = {"project": project, "q": q or "", "kind": kind, "view": "" if view else "developers"}
    _, _, minutes = found.developers
    return render(
        request,
        conn,
        project,
        "board.html",
        {
            "active": "/board",
            "found": found,
            "words": WORDS,
            "search": q or "",  # ``q`` is the links' ``?project=`` in every template
            "kind": kind,
            "kinds": [("", "All"), ("factory", "Factory"), ("product", "Product"), ("bug", "Bugs")],
            "view": view,
            "lever": "/board?" + urlencode({k: v for k, v in lever.items() if v}),
            "dev_time": _hours(minutes) if minutes else "",
        },
    )


def _hours(minutes: float) -> str:
    """``5 h 05 min``, or ``45 min`` under the hour (F146's mock-up)."""
    h, m = divmod(round(minutes), 60)
    return f"{h} h {m:02d} min" if h else f"{m} min"
