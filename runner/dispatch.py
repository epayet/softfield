"""Which job runs next, and why (ADR 22 item 2, f8 D2). No AI in it.

Pure: the queued jobs, the ready tickets, Claude's windows and the time are parameters; the
callers read the metrics database, ``.softfield/tasks/`` and ``state.json``.

- A ticket whose finished attempt waits only for its gates (a regate) goes right after the
  planner's jobs: its gates need no model, and main moving on would throw its work away.
- Then by kind: planner, escalation, direction, checkpoint, review, then tickets: a parked
  ticket whose reset has passed, then lead tickets, then developer tickets, each in the run
  order the caller gives (`pick_next`'s: priority, milestone, id, or the place of the ticket
  that waits for it). Queued jobs of one kind
  go by age.
- A job that can't run now is skipped with its reason, and the next one is taken: a queued
  row before its ``not_before``, a ticket that waits (a dependency, a pause, a sign-off), or
  Claude work while Claude is limited or its windows say no. Queued jobs aren't paced, and may
  use the week's reserve (ADR 15 item 4, ADR 44 items 4 and 5). A lead ticket asks
  ``allowance.lead_hold`` (ADR 44): the week's pace line, then the whole reserve in its last 10%,
  and the reserves the owner lets the factory use. One parked mid-work goes at its reset whatever
  the pace (item 7). Developer tickets never wait for Claude: that keeps "lead work first,
  developers meanwhile" (ADR 16 item 2) without a path of its own.
- ``plan`` lists every job and says why each waits, for the dry run and the pages. The next ticket
  itself is `loop.choose_ticket`'s, for the runner and the dry run alike (ADR 44 item 9).
- While the owner pauses the factory, every job waits, "paused by you" (ADR 22 item 5), but
  the planner's: the owner pauses to talk a change through on /planning (its ⚑, f6-14).
- The fast lane goes before everything (ADR 35 item 2): the caller's ``first`` (a lane card's
  tickets and what they wait for), each queued direction or escalation about one of them,
  then those tickets in the order given. They may use both of Claude's reserves (item 4),
  never a real limit, and the owner's pause holds them too (item 5).
"""

import sqlite3
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from datetime import datetime

from runner import allowance

PLANNER = "planner"
ESCALATION = "escalation"
DIRECTION = "direction"
CHECKPOINT = "checkpoint"
REVIEW = "review"
KINDS = (PLANNER, ESCALATION, DIRECTION, CHECKPOINT, REVIEW)  # in the order they go
TICKET = "ticket"

CLAUDE = "claude"
COST = 0.0  # a job's share of Claude's windows isn't learned yet (`loop.LEAD_COST`)
SUPPORT_RESERVE = "seven_day"  # the week's reserve is the support roles' (ADR 15 item 4)
LANE_RESERVES = frozenset({"seven_day", "five_hour"})  # the fast lane's (ADR 35 item 4)
GOES_WITH = (ESCALATION, DIRECTION)  # a ticket's own work: it joins the lane with it
LANE_KINDS = (ESCALATION, DIRECTION, REVIEW)  # the queued rows the lane takes (F242 D1)
UNKNOWN_KIND = "unknown kind of job"
PAUSED = "paused by you"  # the owner paused the factory (f5-18): every line but planning waits


@dataclass(frozen=True)
class Queued:
    """A ``work_queue`` row (f8 D1)."""

    kind: str
    subject: str
    reason: str
    created: str  # ISO
    not_before: str | None = None  # ISO: it waits until then
    id: int | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Queued":
        return cls(
            row["kind"],
            row["subject"] or "",
            row["reason"] or "",
            row["created"],
            row["not_before"],
            row["id"],
        )


@dataclass(frozen=True)
class Ticket:
    """A ready ticket, as the caller sees it."""

    id: str
    lead: bool  # only the lead may do it (`router.lead_only`)
    priority: int
    waits: str | None = None  # a dependency, a pause, a sign-off: never picked
    not_before: datetime | None = None  # parked for a Claude limit until then, mid-work
    early_for: str | None = None  # the ticket it runs early for: that one waits for it (F173 D7)
    regate: bool = False  # its attempt finished and only its gates wait (`state.regate`)


@dataclass(frozen=True)
class Windows:
    """What may keep Claude from a job now."""

    claude: Sequence[allowance.Window] = ()  # with their reserves
    limited_until: datetime | None = None  # a job parked for a limit resets then
    reserves: Collection[str] = frozenset()  # the windows whose reserve the owner lets it use


@dataclass(frozen=True)
class Pick:
    kind: str  # one of KINDS, or TICKET
    subject: str  # a ticket id or a milestone key
    reason: str


@dataclass(frozen=True)
class Line:
    """One job in the order it would run, and why it can't now (None: it can)."""

    pick: Pick
    waits: str | None


def pick(
    queued: Sequence[Queued],
    tickets: Sequence[Ticket],
    windows: Windows,
    now: datetime,
    *,
    paused: bool = False,
    first: Collection[str] = frozenset(),
) -> Pick | None:
    """The job that runs next, or None when every one waits."""
    lines = plan(queued, tickets, windows, now, paused=paused, first=first)
    return next((line.pick for line in lines if not line.waits), None)


def plan(
    queued: Sequence[Queued],
    tickets: Sequence[Ticket],
    windows: Windows,
    now: datetime,
    *,
    paused: bool = False,
    first: Collection[str] = frozenset(),
) -> list[Line]:
    """Every job in the order it would run, each with what it waits for, the fast lane's
    (``first``'s ticket ids) on top. While the owner pauses the factory (ADR 22 item 5), every
    one waits for them but a planner job, which keeps its own wait (its ⚑, f6-14)."""
    rows = sorted(queued, key=lambda q: (_rank(q.kind), _at(q.created), q.id or 0))
    lane_rows = [q for q in rows if q.kind in LANE_KINDS and q.subject in first]
    rows = [q for q in rows if not (q.kind in LANE_KINDS and q.subject in first)]
    lane = [_queued_line(q, windows, now, LANE_RESERVES) for q in lane_rows]
    lane += [_ticket_line(t, windows, now, lane=True) for t in tickets if t.id in first]
    tickets = [t for t in tickets if t.id not in first]
    ordered = sorted(tickets, key=lambda t: _ticket_rank(t, now))  # stable: the run order
    regate = [_ticket_line(t, windows, now) for t in ordered if t.regate]
    lines = lane + [_queued_line(q, windows, now) for q in rows if q.kind == PLANNER]
    lines += regate  # after the planner's jobs, before every other job (bug-04)
    lines += [_queued_line(q, windows, now) for q in rows if q.kind in KINDS and q.kind != PLANNER]
    lines += [_ticket_line(t, windows, now) for t in ordered if not t.regate]
    unknown = [q for q in rows if q.kind not in KINDS]
    lines += [Line(Pick(q.kind, q.subject, q.reason), UNKNOWN_KIND) for q in unknown]
    if not paused:
        return lines
    return [line if line.pick.kind == PLANNER else Line(line.pick, PAUSED) for line in lines]


def _rank(kind: str) -> int:
    return KINDS.index(kind) if kind in KINDS else len(KINDS)


def _ticket_rank(t: Ticket, now: datetime) -> int:
    if t.regate:
        return -1  # its gates run before anything else but the planner's jobs (`_next_task`)
    if t.not_before is not None and t.not_before <= now and t.waits is None:
        return 0  # parked, and its reset has passed: it goes first (`_next_task`)
    return 1 if t.lead else 2


def _queued_line(
    q: Queued, windows: Windows, now: datetime, reserves: Collection[str] = frozenset()
) -> Line:
    job = Pick(q.kind, q.subject, q.reason)
    if q.not_before is not None and (until := _at(q.not_before)) > now:
        return Line(job, f"waits until {_when(until, now)}")
    return Line(job, _claude_says(windows, now, {SUPPORT_RESERVE, *windows.reserves, *reserves}))


def _ticket_line(t: Ticket, windows: Windows, now: datetime, *, lane: bool = False) -> Line:
    who = "lead" if t.lead else "developer"
    place = f"early for {t.early_for}" if t.early_for else f"priority {t.priority}"
    reason = "its gates wait" if t.regate else place
    if lane:
        reason = f"fast lane, {reason}"
    reason += f", {who} ticket"
    if t.not_before is not None and t.not_before <= now:
        reason += ", its reset has passed"
    job = Pick(TICKET, t.id, reason)
    if t.waits is not None:
        return Line(job, t.waits)
    if t.regate:
        return Line(job, None)  # its gates need no Claude: no limit or reserve holds them
    if t.not_before is not None and t.not_before > now:
        return Line(job, f"waits until {_when(t.not_before, now)}")
    if not t.lead or t.not_before is not None:  # past its reset: its work goes on (ADR 44 item 7)
        return Line(job, None)
    reserves = LANE_RESERVES if lane else windows.reserves
    held = allowance.lead_hold(CLAUDE, windows.claude, COST, now, reserves=reserves)
    return Line(job, _limited(windows, now) or held)


def _limited(windows: Windows, now: datetime) -> str | None:
    if windows.limited_until is not None and windows.limited_until > now:
        return f"Claude is limited until {_when(windows.limited_until, now)}"
    return None


def _claude_says(windows: Windows, now: datetime, reserves: Collection[str]) -> str | None:
    """Why Claude can't take a queued job now, or None when it can."""
    fit = allowance.answer(CLAUDE, windows.claude, COST, now, use_reserve=reserves)
    return _limited(windows, now) or (None if fit.ok else fit.reason)


def _at(text: str) -> datetime:
    return datetime.fromisoformat(text)


def _when(at: datetime, now: datetime) -> str:
    """``Mon 5 Oct 17:00``, in local time."""
    at = at.astimezone()
    return f"{at:%a} {at.day} {at:%b %H:%M}"
