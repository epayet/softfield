"""The numbers a milestone review needs (f1 D7, ADR 14 item 16), shared by ``runner report``
and the dashboard's pages.

Plain functions over a read-only connection that return data, never text. Dollars are
API-equivalent: a Claude job's ``cost_usd``, or its token-equivalents at ≈$4 per 1M when the
cost wasn't kept. Local jobs cost nothing. The lead is a role, not a harness: a job is the
lead's when its role is one of ``LEAD_ROLES``, so Sonnet doing a developer's ticket is a
developer (factory-f1 finding 5).
"""

import json
import re
import sqlite3
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path

from runner.tasks import Task, blocked_ids, milestone_order, pick_next
from runner.usage import CACHE_READ_WEIGHT, OUTPUT_WEIGHT

DOLLARS_PER_TOKEN = 4 / 1_000_000  # per token-equivalent (D7)
# D7's seed: the lead's M4 tickets L0–L3 took 3.5M token-equivalents for 1,979 lines.
SEED_TOKENS_PER_LINE = 3_500_000 / 1979
SEED_DOLLARS_PER_LINE = SEED_TOKENS_PER_LINE * DOLLARS_PER_TOKEN
LEAD_PREFIX = "claude-"  # Claude's agents, whose jobs cost dollars, whatever their role
LOCAL_ROLES = ("developer", "last-attempt")  # a developer's attempts at a ticket
LEAD_ROLES = ("lead-ticket", "direction", "escalation", "checkpoint", "review", "narrative")
UNKNOWN_AGENT = "backfill-unknown"  # D6
SEVERITIES = ("blocking", "should-fix", "nit")


def connect(path: Path) -> sqlite3.Connection:
    """The metrics database, read-only; a missing file is an ``OperationalError``."""
    conn = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


@dataclass(frozen=True)
class Spend:
    """What some jobs used; ``agent`` is set on a per-agent line."""

    jobs: int = 0
    tokens_in: int = 0
    tokens_cached: int = 0
    tokens_out: int = 0
    dollars: float = 0.0
    agent: str | None = None

    @property
    def tokens(self) -> int:
        return self.tokens_in + self.tokens_cached + self.tokens_out

    @property
    def token_equivalents(self) -> float:
        """Input-token equivalents, weighted by price (``runner.usage``)."""
        return (
            self.tokens_in
            + CACHE_READ_WEIGHT * self.tokens_cached
            + OUTPUT_WEIGHT * self.tokens_out
        )


@dataclass(frozen=True)
class MilestoneResults:
    key: str
    title: str | None
    tickets: int
    merged: int
    developer_tickets: int  # developer tickets with at least one attempt
    first_attempt: int  # of those, merged after one attempt that passed
    attempts: int
    escalations: int
    directions: int
    checkpoints: int
    review_rounds: int
    findings: dict[str, int]  # by severity, most severe first
    local: Spend
    claude: Spend
    agents: tuple[Spend, ...]

    @property
    def pass_rate(self) -> float | None:
        return self.first_attempt / self.developer_tickets if self.developer_tickets else None


@dataclass(frozen=True)
class Savings:
    """D7's savings from delegating, in dollars with token-equivalents underneath. ``agents``
    splits them per developer agent; a per-agent line has ``agent`` set."""

    tickets: int = 0
    lines: int = 0  # merged by the developer itself
    doing_itself: float = 0.0
    supporting: float = 0.0
    doing_itself_tokens: float = 0.0
    supporting_tokens: float = 0.0
    agent: str | None = None
    agents: tuple["Savings", ...] = field(default=())

    @property
    def net(self) -> float:
        return self.doing_itself - self.supporting


@dataclass(frozen=True)
class Trend:
    results: MilestoneResults
    savings: Savings


# --- helpers -------------------------------------------------------------------------------


def is_claude(agent: str | None) -> bool:
    """Whether the agent's jobs cost dollars (and are counted in token-equivalents)."""
    return bool(agent) and str(agent).startswith(LEAD_PREFIX)


def _is_lead(job: sqlite3.Row) -> bool:
    return job["role"] in LEAD_ROLES


def _equivalents(job: sqlite3.Row) -> float:
    return (
        (job["tokens_in"] or 0)
        + CACHE_READ_WEIGHT * (job["tokens_cached"] or 0)
        + OUTPUT_WEIGHT * (job["tokens_out"] or 0)
    )


def dollars(job: sqlite3.Row) -> float:
    """A job's API-equivalent dollars: its cost, or its tokens priced; 0 for a free agent."""
    if not is_claude(job["agent"]):
        return 0.0
    if job["cost_usd"] is not None:
        return float(job["cost_usd"])
    return _equivalents(job) * DOLLARS_PER_TOKEN


def _spend(jobs: Sequence[sqlite3.Row], agent: str | None = None) -> Spend:
    return Spend(
        jobs=len(jobs),
        tokens_in=sum(j["tokens_in"] or 0 for j in jobs),
        tokens_cached=sum(j["tokens_cached"] or 0 for j in jobs),
        tokens_out=sum(j["tokens_out"] or 0 for j in jobs),
        dollars=sum(dollars(j) for j in jobs),
        agent=agent,
    )


def _project_id(conn: sqlite3.Connection, project: str) -> int | None:
    row = conn.execute("SELECT id FROM projects WHERE name = ?", (project,)).fetchone()
    return int(row["id"]) if row else None


def _milestones(conn: sqlite3.Connection, project: str) -> list[sqlite3.Row]:
    """The project's milestones, oldest first (by when they started, then by key)."""
    rows = conn.execute(
        "SELECT m.* FROM milestones m JOIN projects p ON p.id = m.project_id WHERE p.name = ?",
        (project,),
    ).fetchall()

    def order(m: sqlite3.Row) -> tuple[int, float, tuple[str, int]]:
        started = m["started"]
        at = datetime.fromisoformat(started).timestamp() if started else 0.0
        return (0 if started else 1, at, milestone_order(m["key"]))

    return sorted(rows, key=order)


def _milestone(conn: sqlite3.Connection, project: str, key: str) -> sqlite3.Row | None:
    return next((m for m in _milestones(conn, project) if m["key"] == key), None)


def _tickets(conn: sqlite3.Connection, milestone_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM tickets WHERE milestone_id = ? ORDER BY ticket", (milestone_id,)
    ).fetchall()


def _jobs(conn: sqlite3.Connection, milestone_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM jobs WHERE milestone_id = ? ORDER BY id", (milestone_id,)
    ).fetchall()


def _by_ticket(jobs: Iterable[sqlite3.Row]) -> dict[int, list[sqlite3.Row]]:
    found: dict[int, list[sqlite3.Row]] = defaultdict(list)
    for job in jobs:
        if job["ticket_id"] is not None:
            found[job["ticket_id"]].append(job)
    return found


# --- milestone results ---------------------------------------------------------------------


def milestone_results(conn: sqlite3.Connection, project: str, key: str) -> MilestoneResults | None:
    """A milestone's tickets, attempts, Claude jobs, findings and spend; None if unknown."""
    m = _milestone(conn, project, key)
    if m is None:
        return None
    jobs = _jobs(conn, m["id"])
    tickets = [t for t in _tickets(conn, m["id"]) if t["state"] != "removed"]
    attempts = _by_ticket(j for j in jobs if j["role"] in LOCAL_ROLES)
    developer = [t for t in tickets if t["kind"] == "developer" and attempts.get(t["id"])]
    first = [
        t
        for t in developer
        if t["commit"]
        and len(attempts[t["id"]]) == 1
        and attempts[t["id"]][0]["outcome"] == "passed"
    ]
    roles = Counter(j["role"] for j in jobs)
    rounds = m["review_rounds"]
    if rounds is None:
        rounds = len({j["attempt"] for j in jobs if j["role"] == "review"})
    by_agent: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for job in jobs:
        by_agent[job["agent"]].append(job)
    return MilestoneResults(
        key=key,
        title=m["title"],
        tickets=len(tickets),
        merged=sum(1 for t in tickets if t["commit"]),
        developer_tickets=len(developer),
        first_attempt=len(first),
        attempts=sum(len(a) for a in attempts.values()),
        escalations=roles["escalation"],
        directions=roles["direction"],
        checkpoints=roles["checkpoint"],
        review_rounds=int(rounds),
        findings=_findings(conn, m["id"]),
        local=_spend([j for j in jobs if not is_claude(j["agent"])]),
        claude=_spend([j for j in jobs if is_claude(j["agent"])]),
        agents=tuple(_spend(by_agent[a], agent=a) for a in sorted(by_agent)),
    )


def _findings(conn: sqlite3.Connection, milestone_id: int) -> dict[str, int]:
    rows = conn.execute(
        "SELECT ifnull(severity, 'unknown') AS severity, count(*) AS n FROM findings"
        " WHERE milestone_id = ? GROUP BY 1",
        (milestone_id,),
    ).fetchall()
    counts = {row["severity"]: int(row["n"]) for row in rows}
    ordered = [s for s in SEVERITIES if s in counts] + sorted(set(counts) - set(SEVERITIES))
    return {s: counts[s] for s in ordered}


# --- savings (D7) --------------------------------------------------------------------------


def _lead_rates(conn: sqlite3.Connection, project_id: int) -> dict[int, tuple[float, float]]:
    """The lead's measured (dollars, token-equivalents) per line, by difficulty, from its
    merged tickets whose Claude jobs were recorded."""
    rows = conn.execute(
        "SELECT id, difficulty, lines_changed FROM tickets WHERE project_id = ? AND kind = 'lead'"
        ' AND "commit" IS NOT NULL AND lines_changed > 0 AND difficulty IS NOT NULL',
        (project_id,),
    ).fetchall()
    totals: dict[int, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
    for ticket in rows:
        jobs = conn.execute("SELECT * FROM jobs WHERE ticket_id = ?", (ticket["id"],)).fetchall()
        lead = [j for j in jobs if _is_lead(j)]
        if not lead:
            continue
        total = totals[ticket["difficulty"]]
        total[0] += sum(dollars(j) for j in lead)
        total[1] += sum(_equivalents(j) for j in lead)
        total[2] += ticket["lines_changed"]
    return {d: (dollars / lines, tokens / lines) for d, (dollars, tokens, lines) in totals.items()}


def _merged_itself(ticket: sqlite3.Row, jobs: Sequence[sqlite3.Row]) -> bool:
    """Whether a developer merged the ticket: its merger tried it, or did none of the lead's
    jobs on it (an escalation's finish is the lead's merge)."""
    merger = ticket["merged_by"]
    if not merger:
        return False
    if any(j["agent"] == merger and j["role"] in LOCAL_ROLES for j in jobs):
        return True
    return not any(j["agent"] == merger and _is_lead(j) for j in jobs)


def _developer_of(ticket: sqlite3.Row, jobs: Sequence[sqlite3.Row], merged_itself: bool) -> str:
    """Who a delegated ticket went to: who merged it, or who last tried it."""
    if merged_itself:
        return str(ticket["merged_by"])
    tried = [j["agent"] for j in jobs if j["role"] in LOCAL_ROLES]
    return str(tried[-1]) if tried else UNKNOWN_AGENT


def _add(parts: Sequence[Savings], agent: str | None = None) -> Savings:
    return Savings(
        tickets=sum(p.tickets for p in parts),
        lines=sum(p.lines for p in parts),
        doing_itself=sum(p.doing_itself for p in parts),
        supporting=sum(p.supporting for p in parts),
        doing_itself_tokens=sum(p.doing_itself_tokens for p in parts),
        supporting_tokens=sum(p.supporting_tokens for p in parts),
        agent=agent,
    )


def _combine(per_agent: Sequence[Savings]) -> Savings:
    groups: dict[str, list[Savings]] = defaultdict(list)
    for part in per_agent:
        groups[part.agent or UNKNOWN_AGENT].append(part)
    agents = tuple(_add(groups[name], agent=name) for name in sorted(groups))
    return replace(_add(per_agent), agents=agents)


def _milestone_savings(
    conn: sqlite3.Connection, milestone_id: int, rates: dict[int, tuple[float, float]]
) -> Savings:
    """Per delegated ticket: what the lead would have spent on the lines its developer merged,
    against the lead's jobs on it, the attempts of a developer that costs dollars (Sonnet),
    and its share of the lead's milestone-wide jobs (reviews, checkpoints)."""
    jobs = _jobs(conn, milestone_id)
    by_ticket = _by_ticket(jobs)
    worked = [t for t in _tickets(conn, milestone_id) if t["commit"] or by_ticket.get(t["id"])]
    if not worked:
        return Savings()
    wide = [j for j in jobs if j["ticket_id"] is None and _is_lead(j)]
    share_dollars = sum(dollars(j) for j in wide) / len(worked)
    share_tokens = sum(_equivalents(j) for j in wide) / len(worked)
    parts = []
    for ticket in worked:
        if ticket["kind"] != "developer":
            continue
        own = by_ticket.get(ticket["id"], [])
        merged_itself = _merged_itself(ticket, own)
        lines = int(ticket["lines_changed"] or 0) if merged_itself else 0
        per_line = rates.get(ticket["difficulty"], (SEED_DOLLARS_PER_LINE, SEED_TOKENS_PER_LINE))
        paid = [
            j for j in own if _is_lead(j) or (j["role"] in LOCAL_ROLES and is_claude(j["agent"]))
        ]
        parts.append(
            Savings(
                tickets=1,
                lines=lines,
                doing_itself=lines * per_line[0],
                doing_itself_tokens=lines * per_line[1],
                supporting=sum(dollars(j) for j in paid) + share_dollars,
                supporting_tokens=sum(_equivalents(j) for j in paid) + share_tokens,
                agent=_developer_of(ticket, own, merged_itself),
            )
        )
    return _combine(parts)


def savings(conn: sqlite3.Connection, project: str, key: str | None = None) -> Savings:
    """D7's savings for one milestone, or for all of them with no ``key``."""
    project_id = _project_id(conn, project)
    if project_id is None:
        return Savings()
    rates = _lead_rates(conn, project_id)
    parts = [
        _milestone_savings(conn, m["id"], rates)
        for m in _milestones(conn, project)
        if key is None or m["key"] == key
    ]
    return _combine([agent for part in parts for agent in part.agents])


# --- eligibility (ADR 14 item 12, ADR 15 item 9, ADR 16 item 10) ---------------------------

# The starting bars per role: the rating, and the milestones whose checkpoints it replayed.
BARS = {"checkpoint": (8.0, 2)}
REVIEW_BENCH = "bench"  # a review replay is a `bench` job with no ticket (`runner bench --review`)
_REVIEW_NOTE_RE = re.compile(
    r"(\d+) found, (\d+) missed \((\d+) blocking\), (\d+) new to judge", re.ASCII
)


def review_note(found: int, missed: int, blocking: int, new: int) -> str:
    """A review replay's score, as its job's note: the known findings it found and missed
    (``blocking`` of them blocking), and the ``new`` ones nobody knew, left for the lead."""
    return f"{found} found, {missed} missed ({blocking} blocking), {new} new to judge"


def parse_review_note(note: str | None) -> tuple[int, int, int, int] | None:
    """``review_note``'s numbers back, or None for any other note."""
    found = _REVIEW_NOTE_RE.fullmatch(note or "")
    if found is None:
        return None
    return int(found[1]), int(found[2]), int(found[3]), int(found[4])


@dataclass(frozen=True)
class Replay:
    """One scored review replay: a checkpoint of ``milestone_id`` replayed by ``agent``."""

    agent: str
    milestone_id: int
    found: int
    missed: int
    blocking: int  # missed blocking findings
    new: int


def review_replays(conn: sqlite3.Connection, project: str) -> list[Replay]:
    """The project's scored review replays, oldest first; a refused or failed one has no
    score and isn't one."""
    rows = conn.execute(
        "SELECT j.agent, j.milestone_id, j.note FROM jobs j JOIN runs r ON r.id = j.run_id"
        " JOIN projects p ON p.id = r.project_id WHERE p.name = ? AND j.role = ?"
        " AND j.ticket_id IS NULL AND j.outcome = 'passed' AND j.milestone_id IS NOT NULL"
        " ORDER BY j.id",
        (project, REVIEW_BENCH),
    ).fetchall()
    return [
        Replay(row["agent"], row["milestone_id"], *score)
        for row in rows
        if (score := parse_review_note(row["note"])) is not None
    ]


@dataclass(frozen=True)
class Eligibility:
    """Whether an agent that replayed ``role``'s jobs meets its starting bars; ``reason``
    says what it lacks, or what it met."""

    agent: str
    role: str
    eligible: bool
    reason: str


def _rating(conn: sqlite3.Connection, agent: str) -> float | None:
    """The agent's one rating: its latest change, whatever its skill (ADR 15 item 9)."""
    row = conn.execute(
        "SELECT after FROM rating_changes WHERE agent = ? ORDER BY at DESC, id DESC LIMIT 1",
        (agent,),
    ).fetchone()
    return None if row is None else float(row["after"])


def _eligible(conn: sqlite3.Connection, agent: str, replays: Sequence[Replay]) -> Eligibility:
    """The checkpoint's bars, from its review replays (ADR 16 item 10): a rating ≥ 8, replays
    of 2+ milestones' checkpoints, no blocking finding missed in any, and a rating ≥ the
    difficulty of the tickets it reviewed: every developer ticket merged in those milestones."""
    role = "checkpoint"
    need, milestones = BARS[role]
    replayed = sorted({r.milestone_id for r in replays})
    missed = sum(r.blocking for r in replays)
    marks = ", ".join("?" for _ in replayed)
    hardest = conn.execute(
        f"SELECT max(coalesce(difficulty_corrected, difficulty)) FROM tickets WHERE milestone_id"  # noqa: S608
        f" IN ({marks}) AND kind = 'developer' AND \"commit\" IS NOT NULL",
        replayed,
    ).fetchone()[0]
    rating = _rating(conn, agent)
    lacks = []
    if rating is None:
        lacks.append("no rating yet")
    elif rating < need:
        lacks.append(f"rated {rating:g}, needs {need:g}")
    if len(replayed) < milestones:
        lacks.append(
            f"replayed checkpoints of {len(replayed)} milestone"
            f"{'' if len(replayed) == 1 else 's'}, needs {milestones}"
        )
    if missed:
        lacks.append(f"{missed} missed blocking finding{'' if missed == 1 else 's'}")
    if rating is not None and hardest is not None and rating < hardest:
        lacks.append(f"rated {rating:g}, below difficulty {hardest} of a ticket it reviewed")
    if lacks:
        return Eligibility(agent, role, False, "; ".join(lacks))
    met = (
        f"rated {rating:g} over replays of {len(replayed)} milestones, no missed blocking"
        f" finding, tickets up to difficulty {hardest if hardest is not None else '?'}"
    )
    return Eligibility(agent, role, True, met)


def eligibility(conn: sqlite3.Connection, project: str) -> list[Eligibility]:
    """Per agent that replayed checkpoints in the project (`runner bench --review`), whether
    it meets the checkpoint's starting bars (ADR 14 item 12, read through ADR 16 item 10); the
    owner changes `[roles]` at a milestone review."""
    by_agent: dict[str, list[Replay]] = defaultdict(list)
    for replay in review_replays(conn, project):
        by_agent[replay.agent].append(replay)
    return [_eligible(conn, agent, by_agent[agent]) for agent in sorted(by_agent)]


# --- the run order (f1 D10) ----------------------------------------------------------------

STOPPED_STATES = ("escalated", "blocked")  # their dependants pause (`runner.tasks.stopped_ids`)


@dataclass(frozen=True)
class Upcoming:
    """A ``ready`` ticket in the order the runner will take it."""

    ticket: str
    title: str | None
    kind: str | None
    milestone: str | None
    waits: tuple[str, ...]  # its dependencies not merged yet

    @property
    def ready_now(self) -> bool:
        return not self.waits


def depends_on(ticket: sqlite3.Row) -> tuple[str, ...]:
    """A ticket row's ``depends_on`` (JSON), as a tuple."""
    return tuple(json.loads(ticket["depends_on"])) if ticket["depends_on"] else ()


def as_task(ticket: str, milestone: str | None, after: Sequence[str]) -> Task:
    """Enough of a ``Task`` for ``pick_next``: its id, milestone and dependencies."""
    return Task(
        id=ticket,
        milestone=milestone or "m0",
        depends_on=tuple(after),
        files=(),
        tests=(),
        max_diff=0,
        finding=None,
        sections={},
        path=Path(ticket),
    )


def in_run_order(
    ready: Sequence[Task], done: set[str], stopped: set[str]
) -> tuple[list[Task], list[Task]]:
    """``pick_next`` applied again and again, each pick counted as merged: the tickets of
    ``ready`` in the order the runner takes them, then those it never would (waiting on a
    ticket that isn't ready, or paused behind a ``stopped`` one)."""
    paused = blocked_ids(ready, stopped)
    left, merged, picked = list(ready), set(done), []
    while (task := pick_next(left, merged, paused)) is not None:
        picked.append(task)
        left.remove(task)
        merged.add(task.id)
    return picked, sorted(left, key=lambda t: (milestone_order(t.milestone), t.id))


def run_order(conn: sqlite3.Connection, project: str) -> list[Upcoming]:
    """The project's ``ready`` tickets in the order the runner will take them, each with the
    dependencies it still waits for (none: ready now); those it can't take yet come last."""
    rows = conn.execute(
        "SELECT t.ticket, t.title, t.kind, t.state, t.depends_on, m.key AS milestone"
        " FROM tickets t JOIN projects p ON p.id = t.project_id"
        " LEFT JOIN milestones m ON m.id = t.milestone_id WHERE p.name = ?",
        (project,),
    ).fetchall()
    done = {r["ticket"] for r in rows if r["state"] == "done"}
    stopped = {r["ticket"] for r in rows if r["state"] in STOPPED_STATES}
    ready = {r["ticket"]: r for r in rows if r["state"] == "ready"}
    tasks = [as_task(r["ticket"], r["milestone"], depends_on(r)) for r in ready.values()]
    picked, left = in_run_order(tasks, done, stopped)
    return [
        Upcoming(
            ticket=t.id,
            title=ready[t.id]["title"],
            kind=ready[t.id]["kind"],
            milestone=ready[t.id]["milestone"],
            waits=tuple(d for d in t.depends_on if d not in done),
        )
        for t in [*picked, *left]
    ]


def trends(conn: sqlite3.Connection, project: str) -> list[Trend]:
    """Each milestone's results and savings, oldest first."""
    found = []
    for m in _milestones(conn, project):
        results = milestone_results(conn, project, m["key"])
        if results is not None:
            found.append(Trend(results, savings(conn, project, m["key"])))
    return found
