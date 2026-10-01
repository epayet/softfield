"""May an agent take a job now? One rule for every agent's allowance (ADR 15 items 1, 2, 4, 5).

Pure: windows, refusals, past jobs and the time are parameters; the callers read the
metrics database. An agent has one or more windows, each with its capacity and usage in
one unit: Claude's are fractions of 1 (its readings), Ollama's tokens, Copilot's requests.

- **Fixed windows** (a week, a month) are paced. Spread: ``used + c`` stays under the pace
  line, ``(capacity − reserve) × elapsed / length``. In the last 10% (the sweep) the line is
  ``capacity − reserve``, and a capacity that is only learned or seeded may be passed.
- **Rolling windows** (Claude's 5 h) are a cap: ``used + c ≤ capacity``.
- Every window must agree; the tightest gives the reason. No window (local): always yes.
- **Learning:** a refusal sets the capacity at the usage it came at, and the window rests
  until its reset (with no reset known: for an hour, then the next window starts).
- **The reserve** (Claude's week) is kept for the lead's support roles: with
  ``use_reserve`` a fixed window is a cap on its whole capacity instead of a pace.
"""

import math
import statistics
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import NamedTuple

SWEEP = 0.1  # the last tenth of a fixed window
COOLDOWN = timedelta(hours=1)  # after a refusal with no reset given
EPS = 1e-9

HOUR = timedelta(hours=1)
DAY = timedelta(days=1)
WEEK = timedelta(days=7)
MONTH = timedelta(days=30)

# Windows that name themselves (Claude's readings, f1-44; D2's `usage_events.window`).
NAMED = {
    "five_hour": ("rolling", 5 * HOUR),
    "seven_day": ("fixed", WEEK),
    "month": ("fixed", MONTH),
}
LABELS = {"five_hour": "5-hour window", "seven_day": "week"}


@dataclass(frozen=True)
class Window:
    name: str
    kind: str  # "rolling" or "fixed"
    length: timedelta
    resets_at: datetime | None
    capacity: float | None  # None: unknown, used until refused
    used: float
    reserve: float = 0.0  # the share of capacity kept for support roles (Claude's week: 0.3)
    measured: bool = False  # the provider reports the capacity (Claude): never swept past
    cooldown_until: datetime | None = None  # set by `learn` after a refusal


@dataclass(frozen=True)
class Refusal:
    at: datetime
    used: float  # the window's usage when it came
    resets_at: datetime | None = None  # when the provider said it would allow again


@dataclass(frozen=True)
class PastJob:
    agent: str
    difficulty: int
    cost: float


class Answer(NamedTuple):
    ok: bool
    reason: str  # one line for `jobs.routing_reason`


def answer(
    agent: str, windows: Sequence[Window], cost: float, now: datetime, *, use_reserve: bool = False
) -> Answer:
    """May ``agent`` take a job of expected cost ``cost`` now?"""
    if not windows:
        return Answer(True, f"{agent}: no allowance window, always allowed")
    checks = [_check(w, cost, now, use_reserve) for w in windows]
    refused = [c for c in checks if not c[0]]
    ok, _, text = min(refused or checks, key=lambda c: c[1])
    return Answer(ok, f"{agent}: {text}")


def reserve_only(agent: str, windows: Sequence[Window], cost: float, now: datetime) -> bool:
    """Is the job refused only because it would dip into a reserve? The caller asks the owner."""
    if answer(agent, windows, cost, now).ok:
        return False
    if not answer(agent, windows, cost, now, use_reserve=True).ok:
        return False
    return any(
        w.reserve and w.capacity is not None and w.used + cost > w.capacity * (1 - w.reserve) + EPS
        for w in windows
    )


def learn(window: Window, refusals: Sequence[Refusal], now: datetime) -> Window:
    """``window`` after its agent's refusals so far: a learned capacity, and a cooldown.

    The latest refusal sets the capacity at its usage, when a reset says which window that
    usage belongs to. The window then rests until the reset; with none, for an hour, after
    which the caller counts usage as a new window, capacity still unknown.
    """
    past = [r for r in refusals if r.at <= now]
    if not past:
        return window
    last = max(past, key=lambda r: r.at)
    resets_at = last.resets_at
    in_this_window = window.resets_at is not None and last.at >= window.resets_at - window.length
    if resets_at is None and in_this_window:
        resets_at = window.resets_at
    capacity = window.capacity
    if last.resets_at is not None or window.resets_at is not None:
        capacity = last.used
    until = resets_at or last.at + COOLDOWN
    return replace(window, capacity=capacity, cooldown_until=until if until > now else None)


def window_shape(name: str, resets_ahead: Sequence[timedelta]) -> tuple[str, timedelta]:
    """A window's kind and length, from its name or how far ahead its resets have been seen.

    Hours ahead means rolling (its length rounded up to the hour); days means fixed: a week,
    or a month past seven days.
    """
    if name in NAMED:
        return NAMED[name]
    furthest = max(resets_ahead)
    if furthest <= DAY:
        return "rolling", max(1, math.ceil(furthest / HOUR)) * HOUR
    return "fixed", WEEK if furthest <= WEEK else MONTH


def expected_cost(agent: str, difficulty: int, past_jobs: Sequence[PastJob], seed: float) -> float:
    """The median cost of ``agent``'s past jobs at ``difficulty``, else of all its jobs, else
    ``seed`` (from config)."""
    mine = [j for j in past_jobs if j.agent == agent]
    same = [j.cost for j in mine if j.difficulty == difficulty]
    if same:
        return statistics.median(same)
    if mine:
        return statistics.median(j.cost for j in mine)
    return seed


def _check(
    window: Window, cost: float, now: datetime, use_reserve: bool
) -> tuple[bool, float, str]:
    """(allowed, headroom as a share of capacity, the reason without the agent)."""
    label = LABELS.get(window.name, window.name)
    if window.cooldown_until is not None and now < window.cooldown_until:
        return (
            False,
            -math.inf,
            f"{label} refused, waiting until {_when(window.cooldown_until, now)}",
        )
    if window.capacity is None:
        return True, math.inf, f"{label} capacity unknown, used until refused"
    capacity = window.capacity
    need = window.used + cost
    used = f"{label} {window.used / capacity:.0%} used"
    if window.kind == "rolling" or window.resets_at is None or use_reserve:
        ok = need <= capacity + EPS
        note = " (using the reserve)" if use_reserve and window.reserve else ""
        return ok, (capacity - need) / capacity, f"{used}, {_side(ok)} its cap of 100%{note}"
    share = capacity * (1 - window.reserve)
    elapsed = min(max((now - (window.resets_at - window.length)) / window.length, 0.0), 1.0)
    if elapsed >= 1 - SWEEP - EPS:
        headroom = (share - need) / capacity
        if need <= share + EPS:
            return True, headroom, f"{used}, in its sweep, under {share / capacity:.0%}"
        if not window.measured and not window.reserve:
            return True, headroom, f"{used}, in its sweep, past its learned capacity until refused"
        return False, headroom, f"{used}, in its sweep, over {share / capacity:.0%}"
    line = share * elapsed
    ok = need <= line + EPS
    return (
        ok,
        (line - need) / capacity,
        f"{used}, {_side(ok)} its pace line of {line / capacity:.0%}",
    )


def _side(ok: bool) -> str:
    return "under" if ok else "over"


def _when(at: datetime, now: datetime) -> str:
    """``Mon 5 Oct 17:00``, in the caller's time zone."""
    at = at.astimezone(now.tzinfo)
    return f"{at:%a} {at.day} {at:%b %H:%M}"
