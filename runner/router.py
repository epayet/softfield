"""Who does a job (ADR 15 items 6, 7 and 9; ADR 14 items 10–11).

Pure: candidates, ratings, allowance windows, expected costs and the time are parameters;
the loop reads them from the config and the metrics database. Every answer comes with one
plain line, the job's ``routing_reason``.

- **A developer job, cloud first and paced:** the best-rated candidate that covers the
  ticket's difficulty and that ``runner.allowance`` permits now; else local, the floor.
- **Step up:** after a failed attempt, the cheapest permitted candidate rated at least 2
  points above the one that failed; else that one again, if it is still permitted.
  "Cheapest" is the lowest rated: with today's agents, local → Sonnet → Opus.
- **A refusal** doesn't count: the caller passes the agents that refused this attempt, and
  they are skipped. Local never refuses, so there is always someone.
- **Lead-only work** (a lead ticket, or one touching protected paths) never goes to a
  developer: ``LeadOnly`` is raised.
- **Lead work first** (ADR 16 item 2): Claude takes a developer ticket only when no lead
  work is ready and its 5-hour window is under the developers' cap.
- **A checkpoint** goes to the first agent its role lists whose model differs from every
  author of the merges it reviews. When Claude can't take it, a read-only agent may stand in
  (ADR 16 item 9): ``stand_in``.
- **A lead ticket** (ADR 32 item 1): with two agents listed and a limit, the first takes a
  ticket of difficulty up to the limit, the second the rest and an unestimated one; with one
  agent, or the limit 0, the last listed takes them all.
"""

from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import NamedTuple

from runner import allowance
from runner.agents import Agent
from runner.gates import touching_protected
from runner.local_model import is_local
from runner.ratings import may_review

DEVELOPER_ROLES = ("developer", "last-attempt")
CHECKPOINT = "checkpoint"
LEAD_TICKET = "lead-ticket"
STEP_UP = 2  # rating points above the agent that failed (ADR 15 item 7)
READ_ONLY_HARNESSES = frozenset({"copilot"})  # reviews only, never a developer (f1-22)
CLAUDE = "claude"  # the lead's harness: its 5-hour window is shared with the owner (ADR 16)

type _Rating = Callable[[Agent], float]
type _Permitted = Callable[[Agent], bool]


class LeadOnly(ValueError):
    """A developer role was asked to route lead-only work."""


@dataclass(frozen=True)
class Ticket:
    id: str
    difficulty: int | None  # None: not estimated, so any rating covers it
    lead_only: bool = False


class Route(NamedTuple):
    agent: Agent
    reason: str  # one line for `jobs.routing_reason`


def lead_only(kind: str, files: Collection[str], protected: Collection[str]) -> bool:
    """A ticket only the lead may do: ``agent: lead``, or files under a protected path."""
    return kind == "lead" or bool(touching_protected(files, protected))


def route(
    role: str,
    ticket: Ticket | None,
    attempt: int,
    candidates: Sequence[Agent],
    ratings: Mapping[str, float],
    windows: Mapping[str, Sequence[allowance.Window]],
    costs: Mapping[str, float],
    now: datetime,
    *,
    failed: str | None = None,
    refused: Collection[str] = (),
    authors: Collection[Agent] = (),
    lead_ready: bool = False,
    five_hour_cap: float = 1.0,
    lead_first_up_to: int = 0,
) -> Route:
    """The agent for ``role``'s job on ``ticket`` (None for a milestone-wide job).

    ``candidates`` are the agents ``[roles]`` lists for it, in order; ``ratings`` their
    ratings now (an agent missing takes its config estimate); ``windows`` and ``costs`` each
    agent's allowance windows and its expected cost in their unit. ``failed`` names the agent
    whose attempt failed before this one, ``refused`` the agents that refused this attempt,
    ``authors`` the developers whose merges a checkpoint reviews. ``lead_ready`` says lead
    work waits (a lead ticket, a direction, an escalation or a checkpoint), and
    ``five_hour_cap`` is the share of Claude's 5-hour window a developer job may start under;
    ``lead_first_up_to`` the hardest lead ticket the first lead agent takes (0: none)."""
    if role in DEVELOPER_ROLES:
        if ticket is None or ticket.lead_only:
            raise LeadOnly(f"{ticket.id if ticket else 'this job'} is the lead's work, not {role}")
        return _developer(
            ticket,
            attempt,
            candidates,
            ratings,
            windows,
            costs,
            now,
            failed,
            refused,
            lead_ready,
            five_hour_cap,
        )
    if not candidates:
        raise LookupError(f"[roles] {role} names no agent")
    if role == CHECKPOINT and authors:
        return _reviewer(candidates, authors)
    if role == LEAD_TICKET:
        return _lead(ticket, candidates, lead_first_up_to)
    return Route(candidates[0], f"{candidates[0].id}, the first agent [roles] {role} names")


def _developer(
    ticket: Ticket,
    attempt: int,
    candidates: Sequence[Agent],
    ratings: Mapping[str, float],
    windows: Mapping[str, Sequence[allowance.Window]],
    costs: Mapping[str, float],
    now: datetime,
    failed: str | None,
    refused: Collection[str],
    lead_ready: bool,
    five_hour_cap: float,
) -> Route:
    pool = [a for a in candidates if a.harness not in READ_ONLY_HARNESSES and a.id not in refused]
    if not pool:
        raise LookupError(f"every developer for {ticket.id} refused attempt {attempt}")

    def rating(agent: Agent) -> float:
        return ratings.get(agent.id, float(agent.rating))

    answers = {
        a.id: _lead_first(a, windows.get(a.id, ()), lead_ready, five_hour_cap)
        or allowance.answer(a.id, windows.get(a.id, ()), costs.get(a.id, 0.0), now)
        for a in pool
        if not is_local(a)
    }

    def permitted(agent: Agent) -> bool:
        return is_local(agent) or answers[agent.id].ok

    if failed is not None and attempt > 1:
        before = next((a for a in candidates if a.id == failed), None)
        floor = rating(before) if before is not None else ratings.get(failed, 0.0)
        above = [a for a in pool if rating(a) >= floor + STEP_UP and permitted(a)]
        if above:
            up = min(above, key=rating)  # the cheapest; the first listed on a tie
            why = "" if is_local(up) else ": " + answers[up.id].reason
            return Route(
                up,
                f"step up from {failed} (rated {_r(floor)}) to {up.id}"
                f" (rated {_r(rating(up))}){why}",
            )
        if before is not None and before in pool and permitted(before):
            return Route(
                before, f"{failed} again: no permitted agent rated {_r(floor + STEP_UP)} or more"
            )
        first = _first_pick(ticket, pool, rating, answers, permitted, refused)
        why = answers[failed].reason if failed in answers else "it isn't a candidate now"
        return Route(first.agent, f"{failed} may not retry: {why}; {first.reason}")
    return _first_pick(ticket, pool, rating, answers, permitted, refused)


def _lead_first(
    agent: Agent, windows: Sequence[allowance.Window], lead_ready: bool, cap: float
) -> allowance.Answer | None:
    """Claude refused a developer job so the lead's work has room (ADR 16 item 2); else None."""
    if agent.harness != CLAUDE:
        return None
    if lead_ready:
        return allowance.Answer(False, f"{agent.id}: lead work is ready, it goes first")
    five = next((w for w in windows if w.name == "five_hour" and w.capacity), None)
    if five is not None and five.capacity and five.used >= five.capacity * cap - allowance.EPS:
        return allowance.Answer(
            False,
            f"{agent.id}: 5-hour window {five.used / five.capacity:.0%} used,"
            f" not under the developers' cap of {cap:.0%}",
        )
    return None


def stand_in(
    candidates: Sequence[Agent],
    windows: Mapping[str, Sequence[allowance.Window]],
    now: datetime,
    authors: Collection[Agent],
    because: str,
) -> Route | None:
    """Who does a checkpoint Claude can't take (ADR 16 item 9; ``because`` says why): the first
    agent listed that its allowance permits, its month a cap at its capacity rather than a pace
    (emergency use). Its model is unknown, so never one whose harness wrote a merge."""
    for agent in candidates:
        if any(author.harness == agent.harness for author in authors):
            continue
        fit = allowance.answer(agent.id, windows.get(agent.id, ()), 0.0, now, use_reserve=True)
        if fit.ok:
            return Route(agent, f"{agent.id} stands in for Claude ({because}): {fit.reason}")
    return None


def _first_pick(
    ticket: Ticket,
    pool: Sequence[Agent],
    rating: _Rating,
    answers: Mapping[str, allowance.Answer],
    permitted: _Permitted,
    refused: Collection[str],
) -> Route:
    need = ticket.difficulty or 0
    cloud = [a for a in pool if not is_local(a)]
    covering = [a for a in cloud if rating(a) >= need]
    allowed = [a for a in covering if permitted(a)]
    if allowed:
        best = max(allowed, key=rating)  # the first listed on a tie
        return Route(
            best,
            f"{best.id} (rated {_r(rating(best))}) covers difficulty {ticket.difficulty or '?'},"
            f" the best permitted: {answers[best.id].reason}",
        )
    local = next((a for a in pool if is_local(a)), None)
    if covering:
        why = "; ".join(answers[a.id].reason for a in covering)
    elif cloud:
        why = f"no cloud agent rated {need} or more"
    else:
        why = "no cloud agent listed"
    if refused:
        why = f"{', '.join(sorted(refused))} refused this attempt" + (f"; {why}" if cloud else "")
    if local is None:  # only cloud agents listed: the first left tries, until refused
        return Route(pool[0], f"{pool[0].id}, the first left: {why}")
    return Route(local, f"{local.id}, the floor: {why}")


def _lead(ticket: Ticket | None, candidates: Sequence[Agent], up_to: int) -> Route:
    if len(candidates) < 2 or up_to <= 0:
        last = candidates[-1]
        return Route(last, f"{last.id}, the last agent [roles] {LEAD_TICKET} names")
    first, second = candidates[0], candidates[1]
    difficulty = ticket.difficulty if ticket is not None else None
    if difficulty is None:
        why = f"of no difficulty (the first agent only up to {up_to})"
        return Route(second, f"{second.id}, a lead ticket {why}")
    if difficulty <= up_to:
        return Route(
            first,
            f"{first.id}, a lead ticket of difficulty {difficulty} (the first agent up to {up_to})",
        )
    return Route(
        second,
        f"{second.id}, a lead ticket of difficulty {difficulty} (the second agent above {up_to})",
    )


def _reviewer(candidates: Sequence[Agent], authors: Collection[Agent]) -> Route:
    names = ", ".join(dict.fromkeys(a.id for a in authors))
    for agent in candidates:
        if all(may_review(agent, author) for author in authors):
            return Route(agent, f"{agent.id}, another model than the authors ({names})")
    first = candidates[0]
    return Route(
        first,
        f"{first.id}, the only checkpoint agent: [roles] checkpoint lists no other model"
        f" than the authors ({names})",
    )


def _r(value: float) -> str:
    """A rating as it reads best: ``7``, ``6.4``."""
    return f"{round(value, 1):g}"
