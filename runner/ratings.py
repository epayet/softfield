"""Each agent's one rating, from 1 to 10 (ADR 14 items 6–7, ADR 15 item 9).

Pure: ratings, results and history are parameters; the runner reads the metrics database and
writes ``rating_changes`` (``runner.loop``). Coding results and review verdicts move the same
rating; a change's ``skill`` names which moved it.

- **A game** is played against a ticket's difficulty (the corrected one when set). The
  expected result is a logistic of the gap, ``1 / (1 + exp(−(rating − difficulty) / SCALE))``:
  0.5 at rating = difficulty, and 0.75 two points above it (``SCALE = 2 / ln 3 ≈ 1.82``). The
  rating moves by ``(result − expected) × K``, and stays within 1–10.
- **K** is 2 over an agent's first 5 tickets (its estimate is provisional) and 1 after.
- **A ticket:** the attempt that merged scores 1 if it was its agent's first on the ticket, 0.5
  if later; every other agent that attempted it scores 0, once. Never merged: 0 for each.
- **A confirmed finding on a ticket's code** lowers that ticket's result by 0.25 after the
  fact: its author's rating moves by −0.25 × K, with nothing expected. The final review's
  "missed" findings are real problems too, so they count the same.
- **A judged finding is a reviewer's game** against the reviewed ticket's difficulty:
  confirmed 1, rejected 0, missed 0 (for the reviewer that should have caught it).
"""

import math
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from runner.agents import Agent

CODING, REVIEWING = "coding", "reviewing"  # rating_changes.skill: what moved the rating
SCALE = 2 / math.log(3)  # a 2-point lead expects 0.75
K, K_PROVISIONAL = 1.0, 2.0
PROVISIONAL_TICKETS = 5
LOWEST, HIGHEST = 1.0, 10.0

FIRST, LATER, LOST = 1.0, 0.5, 0.0
FINDING = -0.25  # off the ticket's result, per finding the final review confirms on its code
MERGED_FIRST, MERGED_LATER, NOT_MERGED = "merged at the first attempt", "merged later", "not merged"
TICKET_LABELS = (MERGED_FIRST, MERGED_LATER, NOT_MERGED)
VERDICT_RESULTS = {"confirmed": 1.0, "rejected": 0.0, "missed": 0.0}
ON_THE_CODE = ("confirmed", "missed")  # verdicts that say the ticket's code has a problem

# Models a harness picks for itself: unknown, so possibly the author's (D6: `copilot-auto`)
UNKNOWN_MODELS = frozenset({"auto"})
FAMILIES = ("opus", "sonnet", "haiku")  # Claude's, whichever harness runs them


@dataclass(frozen=True)
class Game:
    agent: str
    skill: str  # CODING or REVIEWING
    ticket: str
    difficulty: float | None  # None: an adjustment by ``result × K``, not a game
    result: float
    label: str  # rating_changes.result


@dataclass(frozen=True)
class Change:
    agent: str
    skill: str
    ticket: str
    before: float
    after: float
    label: str


@dataclass(frozen=True)
class Attempt:
    agent: str
    merged: bool = False  # this attempt's work was merged


@dataclass(frozen=True)
class Judged:
    """A finding the final review judged, with the agents it concerns."""

    key: str
    ticket: str
    difficulty: float | None  # the reviewed ticket's
    verdict: str  # confirmed, rejected or missed
    reviewer: str | None  # who found it, or, missed, who should have
    author: str | None  # who merged the ticket's code


def expected(rating: float, difficulty: float) -> float:
    return 1 / (1 + math.exp(-(rating - difficulty) / SCALE))


def rate(
    ratings: Mapping[str, float], played: Mapping[str, Collection[str]], games: Iterable[Game]
) -> list[Change]:
    """Play ``games`` in order from ``ratings``, given the tickets each agent was rated on
    before. An agent with no rating to start from is left out."""
    current = dict(ratings)
    tickets = {agent: set(seen) for agent, seen in played.items()}
    changes = []
    for game in games:
        if game.agent not in current:
            continue
        seen = tickets.setdefault(game.agent, set())
        seen.add(game.ticket)
        k = K_PROVISIONAL if len(seen) <= PROVISIONAL_TICKETS else K
        before = current[game.agent]
        if game.difficulty is None:
            step = game.result * k
        else:
            step = (game.result - expected(before, game.difficulty)) * k
        after = min(HIGHEST, max(LOWEST, before + step))
        current[game.agent] = after
        changes.append(Change(game.agent, game.skill, game.ticket, before, after, game.label))
    return changes


def ticket_games(ticket: str, difficulty: float, attempts: Sequence[Attempt]) -> list[Game]:
    """A finished ticket's games, its agents in the order they first attempted it."""
    merger = next((a.agent for a in attempts if a.merged), None)
    order = list(dict.fromkeys(a.agent for a in attempts))
    games = []
    for agent in order:
        if agent != merger:
            games.append(Game(agent, CODING, ticket, difficulty, LOST, NOT_MERGED))
            continue
        tries = sum(a.agent == agent for a in attempts)
        result, label = (FIRST, MERGED_FIRST) if tries == 1 else (LATER, MERGED_LATER)
        games.append(Game(agent, CODING, ticket, difficulty, result, label))
    return games


def judged_games(findings: Iterable[Judged]) -> list[Game]:
    """The reviewers' games and the authors' quarter-point findings. A finding with no reviewed
    difficulty or no reviewer moves no reviewer; one with no author costs no one."""
    games = []
    for f in findings:
        if f.verdict not in VERDICT_RESULTS:
            continue
        if f.reviewer is not None and f.difficulty is not None:
            result = VERDICT_RESULTS[f.verdict]
            label = f"{f.verdict} {f.key}"
            games.append(Game(f.reviewer, REVIEWING, f.ticket, f.difficulty, result, label))
        if f.author is not None and f.verdict in ON_THE_CODE:
            games.append(Game(f.author, CODING, f.ticket, None, FINDING, f"finding {f.key}"))
    return games


def model_of(agent: Agent) -> str | None:
    """The model behind an agent, whatever the harness; None when the harness picks it."""
    name = agent.model.lower().rsplit("/", 1)[-1]
    name = name.removesuffix("-cloud").removesuffix(":cloud")
    if name in UNKNOWN_MODELS:
        return None
    return next((family for family in FAMILIES if family in name), name)


def may_review(reviewer: Agent, author: Agent) -> bool:
    """A reviewer is always another model than the author (ADR 15 item 9): Opus through
    Copilot is still Opus. An unknown model may be the author's, so it may not. The lead's
    own tickets need no reviewer (``needs_reviewer``)."""
    theirs, ours = model_of(reviewer), model_of(author)
    return theirs is not None and ours is not None and theirs != ours


def needs_reviewer(kind: str) -> bool:
    """A ticket's kind (``tickets.kind``): the lead's own work isn't reviewed by itself."""
    return kind != "lead"


def moments(at: datetime, n: int) -> list[str]:
    """``n`` distinct times from ``at``, a microsecond apart: rating_changes is keyed by
    (agent, skill, at), so changes written at one moment would otherwise overwrite each other."""
    return [(at + timedelta(microseconds=i)).isoformat() for i in range(n)]
