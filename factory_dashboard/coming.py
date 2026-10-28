"""The desk's Coming side (f6-20, F14, F31 D9): what the owner sent that is on its way, a waiting
plant's edit and cancel, and Didn't go through, with the classes the desk's items are, and the
reply line (F84) that says where a waiting thread's reply stands. Imports no page module
(F143 D4): ``planning.py`` and ``thread.py`` import from here."""

import json
import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta

from factory_dashboard.app import ago
from factory_dashboard.overview import CANCELLING, Running, open_changes, running_jobs
from runner import metrics
from runner.planner import (
    PLANNER,
    PlannerError,
    plant_words,
    thread_key,
)
from runner.requests import (
    CHANGE,
    DISMISS,
    PLAN_MESSAGE,
    PLANT,
    SEND_BACK,
    WORDS,
    Words,
    owners_words,
    refused,
)
from runner.tasks import short_key

GENERAL = "general"
_TYPICAL = 20  # finished jobs of the running one's role and agent that make its typical length
_MINUTE = timedelta(minutes=1)
_LOOKING = "a ticket blocked on"  # the reason of a planner row that looks at a blocked ticket
_MAX_REQUEST_ID = 12


@dataclass(frozen=True)
class Place:
    """Where a waiting thread's reply stands (F84 D1): being written (``place`` 0) or its place
    in the lead's line, with the words Coming and the thread say."""

    place: int
    words: str
    done: timedelta | None  # about when its reply is written; None without a typical length
    elapsed: timedelta | None = None  # being written: for how long
    typical: timedelta | None = None  # being written: a reply's usual length


@dataclass(frozen=True)
class DeskItem:
    group: str
    title: str
    words: str
    link: str
    # the owner acted on it and the runner hasn't yet: it shows dashed, on its way, and no
    # longer counts as waiting for them (the owner, 2026-10-08)
    on_its_way: bool = field(default=False, kw_only=True)
    place: Place | None = field(default=None, kw_only=True)  # a waiting thread's (F84)
    # a card's open proposals as one item (F51 D1): each part's name, and whether it is on its way
    parts: tuple[tuple[str, bool], ...] = field(default=(), kw_only=True)


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
        # F84 D4: in the lead's order, the reply being written first, then the plants, then
        # the messages the runner hasn't placed, then those held for a Claude limit
        placed: list[DeskItem] = []
        rest: list[DeskItem] = []
        later: list[DeskItem] = []
        if cards:
            titles = _card_titles(conn, project_id)
            jobs = [j for j in running_jobs(conn, project, now) if j.live]
            places = reply_line(conn, project, now, jobs)
            writing = _writing(places)
        for card in dict.fromkeys(cards):
            held = _held(conn, project_id, now, card)
            place = places.get(card) if held is None else None
            reply = _next_reply(conn, project, jobs, True, held, writing)
            said = place.words if place is not None else f"waiting for the lead · {reply}"
            item = DeskItem(
                "coming", _thread_title(card, titles), said, f"/planning/{card}", place=place
            )
            (placed if place is not None else rest if held is None else later).append(item)
        placed.sort(key=lambda item: item.place.place if item.place else 0)
        items = placed + items + rest + later

    return DeskGroup("coming", "Coming", "--hazard", items)


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


# --- the tiles ----------------------------------------------------------------------------


def _typical(
    conn: sqlite3.Connection, project: str, role: str, agent: str | None = None
) -> timedelta | None:
    """How long the last finished jobs of a role and agent (any agent: None) took, on average."""
    rows = conn.execute(
        "SELECT j.started, j.ended FROM jobs j JOIN runs r ON r.id = j.run_id"
        " JOIN projects p ON p.id = r.project_id"
        " WHERE p.name = ? AND j.role = ? AND (? IS NULL OR j.agent = ?)"
        " AND j.outcome != 'running'"
        " AND j.started IS NOT NULL AND j.ended IS NOT NULL ORDER BY j.id DESC LIMIT ?",
        (project, role, agent, agent, _TYPICAL),
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
    writing: str | None = None,
) -> str | None:
    """When the owner's pending message is answered: after the running job, planning going
    first (D1), or once Claude's limit resets (``held``); ``None`` with nothing pending.
    ``writing``: the thread whose reply the lead is writing (F84), for a thread not placed."""
    if not pending:
        return None
    if held is not None:
        return held
    if not jobs:
        return "at the factory's next pick"
    job = _ahead(jobs)
    what = _what(job) if job.role != PLANNER else _reply_of(writing)
    typical = _typical(conn, project, job.role, job.agent)
    if typical is None:
        return f"after {what}"
    left = typical - job.elapsed
    if left < _MINUTE:
        return f"after {what}, any minute now"
    return f"after {what}, ~{ago(left)}"


def _ahead(jobs: list[Running]) -> Running:
    """The live job the lead's line waits for: a planner job first (D1), else the oldest."""
    return next((j for j in jobs if j.role == PLANNER), jobs[0])


def _reply_of(thread: str | None) -> str:
    return f"{thread.upper()}'s reply" if thread else "the lead's reply"


def _ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _about(left: timedelta) -> str:
    return "any minute now" if left < _MINUTE else f"about {ago(left)}"


def _writing(places: Mapping[str, Place]) -> str | None:
    """The thread whose reply the lead is writing, if any."""
    return next((thread for thread, p in places.items() if p.place == 0), None)


def reply_line(
    conn: sqlite3.Connection, project: str, now: datetime, jobs: list[Running]
) -> dict[str, Place]:
    """F84 D1: each thread with an open planner row, by its short key: being written (its row's
    ``started_job`` is a live job, ``jobs``), or its place among the rows not started, in
    ``dispatch.plan``'s order (``queued_jobs`` in overview.py). A row that waits (parked for a
    Claude limit) has no place, and nothing has one while no job runs: they read as before."""
    from runner import dispatch

    project_id = metrics.find_project(conn, project)
    if project_id is None or not jobs:
        return {}
    rows = [r for r in metrics.open_jobs(conn, project_id) if r["kind"] == PLANNER]
    live = {j.job: j for j in jobs}
    ahead = _ahead(jobs)
    what = _what(ahead) if ahead.role != PLANNER else _reply_of(None)
    typical = _typical(conn, project, ahead.role, ahead.agent)
    left = None if typical is None else max(typical - ahead.elapsed, timedelta(0))
    found: dict[str, Place] = {}
    for r in rows:
        job = live.get(r["started_job"])
        if job is None:
            continue
        thread = str(r["subject"] or "").split("#")[0]
        looking = str(r["reason"] or "").startswith(_LOOKING)
        doing = "looking at the blocked ticket" if looking else "writing this reply"
        words = f"the lead is {doing} · {ago(job.elapsed)} in"
        mine = left if job is ahead else None
        if mine is not None:
            words += ", any minute now" if mine < _MINUTE else f", about {ago(mine)} left"
        found[thread] = Place(0, words, mine, job.elapsed, typical if job is ahead else None)
        if job is ahead:
            what = _reply_of(thread)
    # a reply after the one ahead takes a planner reply's usual length, on the lead's agent
    reply = _typical(conn, project, PLANNER, ahead.agent if ahead.role == PLANNER else None)
    queued = [dispatch.Queued.from_row(r) for r in rows if r["started_job"] not in live]
    writing = int(_writing(found) is not None)  # the reply being written is first in line
    n = 0
    for line in dispatch.plan(queued, [], dispatch.Windows(), now):
        thread = line.pick.subject.split("#")[0]
        if line.waits is not None or thread in found:
            continue
        n += 1
        starts = left if n == 1 else None
        if left is not None and reply is not None:
            starts = left + (n - 1) * reply
        when = "" if starts is None else f" · {_about(starts)}"
        rank = n + writing
        words = f"next, after {what}{when}" if n == 1 else f"{_ordinal(rank)} in line{when}"
        done = None if starts is None or reply is None else starts + reply
        found[thread] = Place(rank, words, done)
    return found
