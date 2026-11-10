"""May an agent take a job now? One rule for every agent's allowance (ADR 15 items 1, 2, 4, 5).

Pure: windows, refusals, past jobs and the time are parameters; the callers read the
metrics database. An agent has one or more windows, each with its capacity and usage in
one unit: Claude's are fractions of 1 (its readings), Ollama's tokens, Copilot's requests.

- **Fixed windows** (a week, a month) are paced. Spread: ``used + c`` stays under the pace
  line, ``(capacity − reserve) × elapsed / length``. In the last 10% (the sweep) the line is
  ``capacity − reserve``, and a capacity that is only learned or seeded may be passed.
- **Rolling windows** (Claude's 5 h) are a cap: ``used + c ≤ capacity − reserve``.
- Every window must agree; the tightest gives the reason. No window (local): always yes.
- **Learning:** a refusal sets the capacity at the usage it came at, and the window rests
  until its reset (with no reset known: for an hour, then the next window starts).
- **The reserve** is kept back: Claude's week for the lead's support roles, its 5-hour
  window for the owner (ADR 16 item 1). With ``use_reserve`` (every window's, or the names
  of those whose reserve may be used) a window is a cap on its whole capacity instead.
- **A lead ticket** (ADR 44) has its own question, ``lead_hold``: the same line and caps, but in
  the week's last 10% it may use the whole reserve, since what is left at the reset is lost.
"""

import math
import statistics
from collections.abc import Collection, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import NamedTuple

SWEEP = 0.1  # the last tenth of a fixed window
MARGIN = 1 / 7  # the pace line runs a day of the week ahead (ADR 25)
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
    # The share of capacity kept back: Claude's week 0.3 (support roles), 5 h 0.25 (the owner)
    reserve: float = 0.0
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


type Reserves = bool | Collection[str]  # every window's reserve, or the windows' names


def answer(
    agent: str,
    windows: Sequence[Window],
    cost: float,
    now: datetime,
    *,
    use_reserve: Reserves = False,
) -> Answer:
    """May ``agent`` take a job of expected cost ``cost`` now?"""
    if not windows:
        return Answer(True, f"{agent}: no allowance window, always allowed")
    checks = [_check(w, cost, now, _uses(use_reserve, w)) for w in windows]
    refused = [c for c in checks if not c[0]]
    ok, _, text = min(refused or checks, key=lambda c: c[1])
    return Answer(ok, f"{agent}: {text}")


def lead_hold(
    agent: str,
    windows: Sequence[Window],
    cost: float,
    now: datetime,
    *,
    reserves: Collection[str] = (),
) -> str | None:
    """Why a lead ticket may not start now, or None (ADR 44 items 1 and 2). A window in
    ``reserves`` is a cap on its whole capacity. Otherwise a fixed window is its pace line and, in
    its last 10%, a cap of 100%; a rolling one is its cap. A window resting after a refusal holds
    it, whatever its reserves."""
    checks = [_check(w, cost, now, w.name in reserves, whole_sweep=True) for w in windows]
    refused = [c for c in checks if not c[0]]
    return f"{agent}: {min(refused, key=lambda c: c[1])[2]}" if refused else None


def lead_goes_at(window: Window, cost: float, now: datetime) -> datetime | None:
    """About when ``lead_hold`` lets go of ``window`` with its usage as it stands: its rest's end,
    the moment its pace line reaches that usage or its last 10% opens, or its reset. None when
    nothing says."""
    if resting(window, now):
        return window.cooldown_until
    if window.capacity is None or window.resets_at is None:
        return None
    need = window.used + cost
    if window.kind == "rolling" or need >= window.capacity - EPS:
        return window.resets_at
    share = window.capacity * (1 - window.reserve)
    reached = need / share - MARGIN if share > 0 else 1.0
    start = window.resets_at - window.length
    return start + window.length * max(0.0, min(reached, 1 - SWEEP))


def elapsed_share(window: Window, now: datetime) -> float | None:
    """How much of a fixed ``window`` has gone by (0 to 1), or None for a rolling window or one
    with no reset known."""
    if window.kind == "rolling" or window.resets_at is None:
        return None
    return min(max((now - (window.resets_at - window.length)) / window.length, 0.0), 1.0)


def in_sweep(window: Window, now: datetime) -> bool:
    """Is ``window`` a fixed one in its last 10%?"""
    elapsed = elapsed_share(window, now)
    return elapsed is not None and elapsed >= 1 - SWEEP - EPS


def pace_line(window: Window, now: datetime) -> float | None:
    """Today's pace line of a fixed ``window``, in its capacity's unit: ``share × min(1, elapsed
    + MARGIN)`` (ADR 25), ``share`` being its capacity less its reserve. None for a rolling
    window, one with no reset known or no capacity yet. The last 10% has a cap, not a line:
    ``_check`` and the dashboard both read this."""
    elapsed = elapsed_share(window, now)
    if elapsed is None or window.capacity is None:
        return None
    return window.capacity * (1 - window.reserve) * min(1.0, elapsed + MARGIN)


def resting(window: Window, now: datetime) -> bool:
    """Is ``window`` resting after a refusal?"""
    return window.cooldown_until is not None and now < window.cooldown_until


def reserve_only(
    agent: str, windows: Sequence[Window], cost: float, now: datetime, name: str | None = None
) -> bool:
    """Is the job refused only because it would dip into a reserve (window ``name``'s, if
    given)? The other windows' reserves count as usable: each window has its own question,
    and the caller asks the owner."""
    if answer(agent, windows, cost, now).ok:
        return False
    if not answer(agent, windows, cost, now, use_reserve=True).ok:
        return False
    return any(
        w.reserve
        and (name is None or w.name == name)
        and w.capacity is not None
        and w.used + cost > w.capacity * (1 - w.reserve) + EPS
        for w in windows
    )


def _uses(use_reserve: Reserves, window: Window) -> bool:
    return use_reserve if isinstance(use_reserve, bool) else window.name in use_reserve


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
    window: Window, cost: float, now: datetime, use_reserve: bool, *, whole_sweep: bool = False
) -> tuple[bool, float, str]:
    """(allowed, headroom as a share of capacity, the reason without the agent). With
    ``whole_sweep`` (a lead ticket), a fixed window's last 10% is a cap on its whole capacity, and
    a full window holds even a job of no expected cost."""
    label = LABELS.get(window.name, window.name)
    if resting(window, now) and window.cooldown_until is not None:
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
    share = capacity * (1 - window.reserve)
    if window.kind == "rolling" or window.resets_at is None or use_reserve:
        cap = capacity if use_reserve else share
        ok = need <= cap + EPS
        note = " (using the reserve)" if use_reserve and window.reserve else ""
        return (
            ok,
            (cap - need) / capacity,
            f"{used}, {_side(ok)} its cap of {cap / capacity:.0%}{note}",
        )
    sweeping = in_sweep(window, now)
    if whole_sweep and sweeping:
        ok = need <= capacity + EPS and window.used < capacity - EPS
        word = "under" if ok else "at"
        text = f"{used}, in its last 10%, {word} its cap of 100%"
        return ok, (capacity - need) / capacity, text
    if sweeping:
        headroom = (share - need) / capacity
        if need <= share + EPS:
            return True, headroom, f"{used}, in its sweep, under {share / capacity:.0%}"
        if not window.measured and not window.reserve:
            return True, headroom, f"{used}, in its sweep, past its learned capacity until refused"
        return False, headroom, f"{used}, in its sweep, over {share / capacity:.0%}"
    line = pace_line(window, now) or 0.0
    ok = need <= line + EPS
    return (
        ok,
        (line - need) / capacity,
        f"{used}, {_side(ok)} its pace line of {line / capacity:.0%}",
    )


def _side(ok: bool) -> str:
    return "under" if ok else "over"


def _when(at: datetime, now: datetime) -> str:
    """``Mon 5 Oct 17:00``, in local time."""
    at = at.astimezone()
    return f"{at:%a} {at.day} {at:%b %H:%M}"
