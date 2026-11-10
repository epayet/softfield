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
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import overload

import yaml

from runner.tasks import (
    BUG_PRIORITY,
    BUGS,
    DEFAULT_PRIORITY,
    Task,
    TaskError,
    blocked_ids,
    early_for,
    milestone_order,
    pick_next,
    pulls,
    short_key,
    split_frontmatter,
)
from runner.tasks import run_order as _run_order
from runner.tasks import task_priority as _task_priority
from runner.usage import CACHE_READ_WEIGHT, OUTPUT_WEIGHT

DOLLARS_PER_TOKEN = 4 / 1_000_000  # per token-equivalent (D7)


@overload
def local(at: str | datetime) -> datetime: ...
@overload
def local(at: None) -> None: ...
@overload
def local(at: str | datetime | None) -> datetime | None: ...
def local(at: str | datetime | None) -> datetime | None:
    """A stored time in the machine's zone, for a page to print (F187 D3). A naive value counts
    as UTC."""
    if at is None:
        return None
    moment = datetime.fromisoformat(at) if isinstance(at, str) else at
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone()


# D7's seed: the lead's M4 tickets L0–L3 took 3.5M token-equivalents for 1,979 lines.
SEED_TOKENS_PER_LINE = 3_500_000 / 1979
SEED_DOLLARS_PER_LINE = SEED_TOKENS_PER_LINE * DOLLARS_PER_TOKEN
LEAD_PREFIX = "claude-"  # Claude's agents, whose jobs cost dollars, whatever their role
LOCAL_ROLES = ("developer", "last-attempt")  # a developer's attempts at a ticket
LEAD_ROLES = ("lead-ticket", "direction", "escalation", "checkpoint", "review", "narrative")
UNKNOWN_AGENT = "backfill-unknown"  # D6
PAUSE = "pause"  # the runner's usage event while the owner pauses it (`runner.requests`)
SEVERITIES = ("blocking", "should-fix", "nit")
EASY_LEAD_UP_TO = 4  # Sonnet takes difficulty 4 and below (ADR 32)


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


@dataclass(frozen=True)
class LeadRow:
    """One row of the lead split: per agent and difficulty band, how the lead tickets went."""

    band: str
    agent: str
    tickets: int = 0
    merged: int = 0
    first_time: int = 0
    step_ups: int = 0
    dollars: float = 0.0
    would_have: float = 0.0
    saved: float = 0.0
    reviewed: int = 0
    should_fix: int = 0
    blocking: int = 0


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
        "SELECT t.id AS ticket_id, t.difficulty, t.lines_changed, j.cost_usd, j.tokens_in,"
        " j.tokens_cached, j.tokens_out, j.role, j.agent FROM tickets t"
        " LEFT JOIN jobs j ON j.ticket_id = t.id"
        " WHERE t.project_id = ? AND t.kind = 'lead'"
        ' AND t."commit" IS NOT NULL AND t.lines_changed > 0 AND t.difficulty IS NOT NULL',
        (project_id,),
    ).fetchall()
    totals: dict[int, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
    seen: set[int] = set()
    for row in rows:
        diff = row["difficulty"]
        total = totals[diff]
        # Count each merged lead ticket once for the denominator, regardless of jobs.
        tid = row["ticket_id"]
        if tid not in seen:
            seen.add(tid)
            total[2] += row["lines_changed"]
        # Only sum dollars and tokens from lead-role jobs; non-lead jobs contribute none.
        if row["role"] in LEAD_ROLES:
            total[0] += dollars(row)
        if row["role"] in LEAD_ROLES:
            total[1] += _equivalents(row)
    return {
        d: (dollars / lines, tokens / lines)
        for d, (dollars, tokens, lines) in totals.items()
        if lines > 0
    }


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
    conn: sqlite3.Connection,
    milestone_id: int,
    rates: dict[int, tuple[float, float]] | None = None,
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
        per_line = (
            rates.get(ticket["difficulty"], (SEED_DOLLARS_PER_LINE, SEED_TOKENS_PER_LINE))
            if rates is not None
            else (SEED_DOLLARS_PER_LINE, SEED_TOKENS_PER_LINE)
        )
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


def savings(
    conn: sqlite3.Connection,
    project: str,
    key: str | None = None,
    rates: dict[int, tuple[float, float]] | None = None,
) -> Savings:
    """D7's savings for one milestone, or for all of them with no ``key``."""
    project_id = _project_id(conn, project)
    if project_id is None:
        return Savings()
    if rates is None:
        rates = _lead_rates(conn, project_id)
    parts = [
        _milestone_savings(conn, m["id"], rates)
        for m in _milestones(conn, project)
        if key is None or m["key"] == key
    ]
    return _combine([agent for part in parts for agent in part.agents])


# --- lead split (F179 D1, D2, D3) -------------------------------------------------------


def _opus_mean_by_diff(
    conn: sqlite3.Connection, project_id: int
) -> tuple[dict[int, float], float | None]:
    """Opus's mean dollars per merged lead ticket, by difficulty and overall.

    Only counts tickets where Opus is the owner (first real attempt) and
    the ticket is merged (has a passed job).
    """
    rows = conn.execute(
        "SELECT t.id, t.difficulty FROM tickets t "
        "WHERE t.project_id = ? AND t.kind = 'lead' "
        'AND t."commit" IS NOT NULL AND t.difficulty IS NOT NULL',
        (project_id,),
    ).fetchall()
    totals: dict[int, list[float]] = defaultdict(lambda: [0.0, 0.0])
    overall_total: float = 0.0
    overall_count: float = 0.0
    for ticket in rows:
        owner = _ticket_owner(conn, ticket["id"])
        if owner != "claude-opus":
            continue
        if not conn.execute(
            "SELECT 1 FROM jobs WHERE ticket_id = ? AND outcome = 'passed' LIMIT 1",
            (ticket["id"],),
        ).fetchone():
            continue
        roles = ("lead-ticket", "direction", "escalation", "checkpoint", "review", "narrative")
        marks = ", ".join("?" for _ in roles)
        jobs = conn.execute(
            "SELECT * FROM jobs WHERE ticket_id = ? "  # noqa: S608, UP031
            "AND agent = 'claude-opus' "
            "AND role IN (%s)" % marks,
            (ticket["id"], *roles),
        ).fetchall()
        if not jobs:
            continue
        total_cost = sum(dollars(j) for j in jobs)
        totals[ticket["difficulty"]][0] += total_cost
        totals[ticket["difficulty"]][1] += 1.0
        overall_total += total_cost
        overall_count += 1.0
    by_diff = {d: total / count for d, (total, count) in totals.items() if count > 0}
    overall = overall_total / overall_count if overall_count > 0 else None
    return by_diff, overall


def _ticket_owner(conn: sqlite3.Connection, ticket_id: int) -> str | None:
    """The owner of a lead ticket: agent of its first lead-ticket job that is an attempt.
    Jobs with note 'parked' or 'interrupted' are not attempts."""
    roles = ("lead-ticket", "direction", "escalation", "checkpoint", "review", "narrative")
    marks = ", ".join("?" for _ in roles)
    all_jobs = conn.execute(
        "SELECT agent, note FROM jobs WHERE ticket_id = ? "  # noqa: S608, UP031
        "AND role IN (%s) "
        "ORDER BY id ASC" % marks,
        (ticket_id, *roles),
    ).fetchall()
    for j in all_jobs:
        if j["note"] not in ("parked", "interrupted"):
            return str(j["agent"])
    return None


def _ticket_first_started(conn: sqlite3.Connection, ticket_id: int) -> str | None:
    """The first job's started time for a ticket."""
    row = conn.execute(
        "SELECT started FROM jobs WHERE ticket_id = ? AND started IS NOT NULL "
        "ORDER BY started ASC LIMIT 1",
        (ticket_id,),
    ).fetchone()
    return str(row["started"]) if row else None


def _ticket_is_reviewed(conn: sqlite3.Connection, milestone_id: int, ticket_id: int) -> bool:
    """Whether a ticket's milestone has a passed review job."""
    row = conn.execute(
        "SELECT 1 FROM jobs WHERE milestone_id = ? AND role = 'review' "
        "AND outcome = 'passed' LIMIT 1",
        (milestone_id,),
    ).fetchone()
    return row is not None


def _ticket_findings(
    conn: sqlite3.Connection, milestone_id: int, ticket_id: int
) -> tuple[int, int]:
    """Count should-fix and blocking findings for a ticket."""
    row = conn.execute(
        "SELECT sum(severity = 'should-fix') AS sf, sum(severity = 'blocking') AS bl "
        "FROM findings WHERE milestone_id = ? AND ticket_id = ?",
        (milestone_id, ticket_id),
    ).fetchone()
    return int(row["sf"] or 0), int(row["bl"] or 0)


def _band(diff: int | None) -> str | None:
    """The difficulty band for a ticket's difficulty, or None if no difficulty."""
    if diff is None:
        return None
    if diff <= EASY_LEAD_UP_TO:
        return f"difficulty {EASY_LEAD_UP_TO} or below"
    return f"difficulty {EASY_LEAD_UP_TO + 1} and up"


def lead_split(
    conn: sqlite3.Connection,
    project: str,
    key: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> list[LeadRow]:
    """Per agent and difficulty band, how the lead tickets went (D1, D2, D3).
    ``key`` keeps one milestone's tickets; ``start``/``end`` keep tickets whose
    first job started in them. A project with no lead ticket returns ``[]``."""
    project_id = _project_id(conn, project)
    if project_id is None:
        return []

    # Determine which milestones and tickets to consider
    if key is not None:
        m = _milestone(conn, project, key)
        if m is None:
            return []
        milestones = [m]
    else:
        milestones = _milestones(conn, project)

    # Gather lead tickets from the relevant milestones
    ticket_rows: list[sqlite3.Row] = []
    for m in milestones:
        rows = conn.execute(
            "SELECT id, difficulty, milestone_id FROM tickets "
            "WHERE milestone_id = ? AND kind = 'lead'",
            (m["id"],),
        ).fetchall()
        ticket_rows.extend(rows)

    if not ticket_rows:
        return []

    # Filter by start/end on first job's started time
    if start is not None:
        start_dt = datetime.fromisoformat(start) if isinstance(start, str) else start
    else:
        start_dt = None
    if end is not None:
        end_dt = datetime.fromisoformat(end) if isinstance(end, str) else end
    else:
        end_dt = None

    filtered: list[sqlite3.Row] = []
    for t in ticket_rows:
        fs = _ticket_first_started(conn, t["id"])
        if fs is None:
            continue
        fs_time = _time(fs)
        if start_dt is not None and fs_time < start_dt:
            continue
        if end_dt is not None and fs_time > end_dt:
            continue
        filtered.append(t)

    if not filtered:
        return []

    # Group by (band, agent)
    band_agent: dict[tuple[str, str], list[sqlite3.Row]] = defaultdict(list)
    for t in filtered:
        b = _band(t["difficulty"])
        if b is None:
            continue
        owner = _ticket_owner(conn, t["id"])
        if owner is None:
            continue
        band_agent[(b, owner)].append(t)

    # Opus mean dollars by difficulty and overall
    opus_mean, overall_mean = _opus_mean_by_diff(conn, project_id)

    # Aggregate per (band, agent)
    rows_out: list[LeadRow] = []
    for (band, agent), tickets in sorted(band_agent.items()):
        merged = 0
        first_time = 0
        step_ups = 0
        dollars_total = 0.0
        reviewed = 0
        should_fix = 0
        blocking = 0

        for t in tickets:
            # Check if ticket is merged (has a passed job)
            if conn.execute(
                "SELECT 1 FROM jobs WHERE ticket_id = ? AND outcome = 'passed' LIMIT 1",
                (t["id"],),
            ).fetchone():
                merged += 1

            # Get all jobs for first attempt analysis
            all_jobs = conn.execute(
                "SELECT outcome, note, agent FROM jobs WHERE ticket_id = ? ORDER BY id ASC",
                (t["id"],),
            ).fetchall()

            # Find first real attempt (not parked/interrupted)
            first_real_outcome = None
            for j in all_jobs:
                if j["note"] not in ("parked", "interrupted"):
                    first_real_outcome = j["outcome"]
                    break

            if first_real_outcome == "passed":
                first_time += 1
            elif first_real_outcome == "failed":
                # Check if a later Opus job passed (step-up)
                has_opus_pass = any(
                    j["outcome"] == "passed" and j["agent"] == "claude-opus" for j in all_jobs[1:]
                )
                if has_opus_pass:
                    step_ups += 1

            # Sum dollars from all jobs on this ticket
            job_rows = conn.execute(
                "SELECT cost_usd, tokens_in, tokens_cached, tokens_out, agent "
                "FROM jobs WHERE ticket_id = ?",
                (t["id"],),
            ).fetchall()
            for j in job_rows:
                dollars_total += dollars(j)

            # Review and findings
            if _ticket_is_reviewed(conn, t["milestone_id"], t["id"]):
                reviewed += 1
            sf, bl = _ticket_findings(conn, t["milestone_id"], t["id"])
            should_fix += sf
            blocking += bl

        # Would-have and saved (not for Opus rows)
        diff = tickets[0]["difficulty"]
        would_have = 0.0
        saved = 0.0
        if agent != "claude-opus":
            rate = opus_mean.get(diff, overall_mean)
            if rate is not None:
                would_have = rate
                saved = would_have - dollars_total

        rows_out.append(
            LeadRow(
                band=band,
                agent=agent,
                tickets=len(tickets),
                merged=merged,
                first_time=first_time,
                step_ups=step_ups,
                dollars=round(dollars_total, 2),
                would_have=round(would_have, 2),
                saved=round(saved, 2),
                reviewed=reviewed,
                should_fix=should_fix,
                blocking=blocking,
            )
        )

    return rows_out


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
    priority: int = DEFAULT_PRIORITY  # as the runner reads it (f6-18)
    early_for: str | None = None  # the ticket it runs early for: that one waits for it (F173 D7)

    @property
    def ready_now(self) -> bool:
        return not self.waits


def depends_on(ticket: sqlite3.Row) -> tuple[str, ...]:
    """A ticket row's ``depends_on`` (JSON), as a tuple."""
    return tuple(json.loads(ticket["depends_on"])) if ticket["depends_on"] else ()


def ticket_priority(body: str | None, milestone: str | None, card: int | None) -> int:
    """A ticket row's priority as the runner reads it (`runner.tasks.task_priority`): a bug's
    ``priority:`` in its text, else 50; a feature ticket's card's, else 100, whatever its text
    says (F173 D5). Lower goes first."""
    if milestone != BUGS:
        return DEFAULT_PRIORITY if card is None else card
    try:
        meta = split_frontmatter(body or "")[0]
    except (TaskError, yaml.YAMLError):
        meta = {}
    own = meta.get("priority")
    return own if type(own) is int and own >= 0 else BUG_PRIORITY


def as_task(
    ticket: str, milestone: str | None, after: Sequence[str], priority: int | None = None
) -> Task:
    """Enough of a ``Task`` for ``pick_next``: its id, milestone, dependencies and priority."""
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
        priority=priority,
    )


def in_run_order(
    ready: Sequence[Task],
    done: set[str],
    stopped: set[str],
    cards: Mapping[str, int] | None = None,
) -> tuple[list[Task], list[Task]]:
    """``pick_next`` applied again and again, each pick counted as merged: the tickets of
    ``ready`` in the order the runner takes them, then those it never would (waiting on a
    ticket that isn't ready, or paused behind a ``stopped`` one). ``cards`` maps a card's
    short key to its place on the board, as the runner's pick has it; a ticket waited for
    goes in its first waiter's place, read from the whole of ``ready`` (F173 D6)."""
    cards = cards or {}
    paused = blocked_ids(ready, stopped)
    pulled = pulls(ready, cards)
    left, merged, picked = list(ready), set(done), []
    while (task := pick_next(left, merged, paused, cards, pulled)) is not None:
        picked.append(task)
        left.remove(task)
        merged.add(task.id)
    return picked, sorted(left, key=lambda t: _run_order(t, cards, pulled))


def run_order(
    conn: sqlite3.Connection, project: str, states: Mapping[str, str] | None = None
) -> list[Upcoming]:
    """The project's ``ready`` tickets in the order the runner will take them, each with the
    dependencies it still waits for (none: ready now); those it can't take yet come last.
    ``states`` overrides tickets' states (the line at a past moment, f3-06). Each has its
    priority, which orders them as it does the runner's pick (f6-18)."""
    rows = conn.execute(
        "SELECT t.ticket, t.title, t.kind, t.state, t.depends_on, t.body, m.key AS milestone,"
        " m.priority AS card FROM tickets t JOIN projects p ON p.id = t.project_id"
        " LEFT JOIN milestones m ON m.id = t.milestone_id WHERE p.name = ?",
        (project,),
    ).fetchall()
    state = {r["ticket"]: (states or {}).get(r["ticket"], r["state"]) for r in rows}
    done = {r["ticket"] for r in rows if state[r["ticket"]] == "done"}
    stopped = {r["ticket"] for r in rows if state[r["ticket"]] in STOPPED_STATES}
    ready = {r["ticket"]: r for r in rows if state[r["ticket"]] == "ready"}
    tasks = [
        as_task(
            r["ticket"],
            r["milestone"],
            depends_on(r),
            ticket_priority(r["body"], r["milestone"], r["card"]),
        )
        for r in ready.values()
    ]
    cards = {  # each feature ticket's priority is its card's place
        short_key(t.milestone): t.priority
        for t in tasks
        if t.milestone != BUGS and t.priority is not None
    }
    picked, left = in_run_order(tasks, done, stopped, cards)
    pulled = pulls(tasks, cards)
    return [
        Upcoming(
            ticket=t.id,
            title=ready[t.id]["title"],
            kind=ready[t.id]["kind"],
            milestone=ready[t.id]["milestone"],
            waits=tuple(d for d in t.depends_on if d not in done),
            priority=_task_priority(t, cards),
            early_for=early_for(t, cards, pulled),
        )
        for t in [*picked, *left]
    ]


# --- what clogged the line (f3 D11, f3-04) --------------------------------------------------

LIVE = timedelta(minutes=2)  # an unfinished run or job lives until its last heartbeat, plus this
NOT_ATTEMPTS = ("parked", "interrupted", "refused", "transient")  # notes of jobs that stopped short

type Span = tuple[datetime, datetime]


@dataclass(frozen=True)
class Idle:
    """A developer machine's minutes without a job of its own while another job ran, and their
    share of the runner's live time."""

    agent: str
    minutes: int
    share: float


@dataclass(frozen=True)
class Clog:
    """Where the line's time went between ``since`` and ``now``, in minutes (D11)."""

    limit: int  # waiting for Claude's limit, while a runner lived
    failed: int  # failed developer attempts
    failures: int  # how many
    idle: tuple[Idle, ...]  # per developer machine
    owner: int  # an owner item open while no job ran
    live: int  # the runner's live time


def _time(at: str) -> datetime:
    moment = datetime.fromisoformat(at)
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


def _until(ended: str | None, heartbeat: str | None) -> datetime | None:
    if ended:
        return _time(ended)
    return _time(heartbeat) + LIVE if heartbeat else None


def _union(spans: Iterable[Span]) -> list[Span]:
    merged: list[Span] = []
    for start, end in sorted(s for s in spans if s[0] < s[1]):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def _overlap(a: Sequence[Span], b: Sequence[Span]) -> list[Span]:
    return _union((max(s, t), min(e, f)) for s, e in a for t, f in b)


def _without(a: Sequence[Span], b: Sequence[Span]) -> list[Span]:
    """``a`` less ``b``; ``b`` is a union."""
    found = []
    for start, end in a:
        cursor = start
        for s, e in b:
            if e <= cursor or s >= end:
                continue
            if s > cursor:
                found.append((cursor, s))
            cursor = max(cursor, e)
        if cursor < end:
            found.append((cursor, end))
    return found


def _minutes(spans: Iterable[Span]) -> float:
    return sum((end - start).total_seconds() for start, end in spans) / 60


def clog(
    conn: sqlite3.Connection,
    project: str,
    since: datetime,
    now: datetime,
    machines: Sequence[str] | None = None,
) -> Clog:
    """What clogged the line between ``since`` and ``now`` (D11 says what each number counts):
    Claude's limit while a runner lived, failed developer attempts, each developer machine
    (``machines``; default: the agents that ran a developer job) idle while another job ran,
    and the owner's open items and pauses while no job ran. Only what had happened by ``now``
    counts."""
    window = [(since, now)]
    runs = conn.execute(
        "SELECT r.started, r.ended, r.heartbeat FROM runs r JOIN projects p ON p.id = r.project_id"
        " WHERE p.name = ? AND r.started IS NOT NULL",
        (project,),
    ).fetchall()
    live = _overlap(
        _union(
            (_time(r["started"]), until)
            for r in runs
            if (until := _until(r["ended"], r["heartbeat"])) is not None
        ),
        window,
    )

    jobs = conn.execute(
        "SELECT j.agent, j.role, j.started, j.ended, j.outcome, j.note, r.heartbeat FROM jobs j"
        " JOIN runs r ON r.id = j.run_id JOIN projects p ON p.id = r.project_id"
        " WHERE p.name = ? AND j.started IS NOT NULL",
        (project,),
    ).fetchall()
    spans: dict[str, list[Span]] = defaultdict(list)
    failed: list[Span] = []
    for j in jobs:
        until = _until(j["ended"], j["heartbeat"])
        if until is None:
            continue
        span = (_time(j["started"]), until)
        spans[j["agent"]].append(span)
        if (
            j["role"] in LOCAL_ROLES
            and j["outcome"] == "failed"
            and j["note"] not in NOT_ATTEMPTS
            and until <= now  # it had failed by then
        ):
            failed.append(span)
    lost = [clipped for span in failed if (clipped := _overlap([span], window))]
    busy = _union(s for own in spans.values() for s in own)

    limits = conn.execute(
        "SELECT at, resets_at FROM usage_events WHERE resets_at IS NOT NULL"
        " AND ((kind = 'refusal' AND agent LIKE ?) OR kind = 'wait')",
        (LEAD_PREFIX + "%",),
    ).fetchall()
    limit = _overlap(_union((_time(r["at"]), _time(r["resets_at"])) for r in limits), live)

    items = conn.execute(
        "SELECT i.created, i.resolved FROM owner_items i JOIN projects p ON p.id = i.project_id"
        " WHERE p.name = ? AND i.created IS NOT NULL",
        (project,),
    ).fetchall()
    # The owner's pause (f5-18), from when it took to their resume, or on while it holds
    pauses = conn.execute(
        "SELECT at AS created, resets_at AS resolved FROM usage_events WHERE kind = ?", (PAUSE,)
    ).fetchall()
    opened = _union(
        (_time(r["created"]), _time(r["resolved"]) if r["resolved"] else now)
        for r in [*items, *pauses]
    )
    owner = _without(_overlap(opened, window), busy)

    if machines is None:
        machines = sorted({j["agent"] for j in jobs if j["role"] in LOCAL_ROLES})
    alive, working = _minutes(live), _overlap(busy, live)
    idle = []
    for agent in machines:
        minutes = _minutes(_without(working, _union(spans.get(agent, []))))
        idle.append(Idle(agent, round(minutes), round(minutes / alive, 2) if alive else 0.0))
    return Clog(
        limit=round(_minutes(limit)),
        failed=round(sum(_minutes(part) for part in lost)),
        failures=len(lost),
        idle=tuple(idle),
        owner=round(_minutes(owner)),
        live=round(alive),
    )


def paused_since(conn: sqlite3.Connection) -> str | None:
    """When the owner's pause took (f5-18), while the runner still holds for it: its usage
    event's ``at``, with no ``resets_at`` until they resume."""
    row = conn.execute(
        "SELECT at FROM usage_events WHERE kind = ? AND resets_at IS NULL ORDER BY at DESC LIMIT 1",
        (PAUSE,),
    ).fetchone()
    return None if row is None else str(row["at"])


def trends(conn: sqlite3.Connection, project: str) -> list[Trend]:
    """Each milestone's results and savings, oldest first."""
    project_id = _project_id(conn, project)
    if project_id is None:
        return []
    rates = _lead_rates(conn, project_id)
    found = []
    for m in _milestones(conn, project):
        results = milestone_results(conn, project, m["key"])
        if results is not None:
            found.append(Trend(results, _milestone_savings(conn, m["id"], rates)))
    return found


# --- away (f3-21) --------------------------------------------------------------------------------


@dataclass(frozen=True)
class AwayTicket:
    """A ticket that reached ``done`` in the span: its name (``/tickets/<ticket>``), title,
    who merged it, the display name of the merger, how many developer attempts it had,
    the ticket kind, a context label, the finish time, how long it took, and the blocked
    ticket IDs."""

    ticket: str
    title: str | None
    merged_by: str | None
    display_name: str | None = None
    attempts: int = 0
    kind: str | None = None
    label: str = ""
    blocked_ids: tuple[str, ...] = ()
    finished: datetime | None = None
    took: timedelta | None = None


@dataclass(frozen=True)
class Away:
    """What happened since ``since``: merged tickets, failed jobs, escalations,
    blocked tickets, owner items created, Claude spend, and the blocked ticket IDs."""

    merged: tuple[AwayTicket, ...]
    failed: int
    escalations: int
    blocked: int
    needs_you: int
    claude_usd: float
    blocked_ids: tuple[str, ...] = ()


def away(conn: sqlite3.Connection, project: str, since: datetime, now: datetime) -> Away:
    """Tickets that reached ``done`` in the span (latest first), failed developer jobs,
    escalations started, blocked tickets, owner items created, and Claude spend (f3-21)."""

    # times are compared as moments, not strings: the runner writes its own local offset
    def within(at: str | None) -> bool:
        return at is not None and since <= _time(at) <= now

    jobs = conn.execute(
        "SELECT j.role, j.agent, j.started, j.ended, j.outcome, j.note, j.cost_usd, j.tokens_in,"
        " j.tokens_cached, j.tokens_out, t.ticket, t.title, t.merged_by, t.state FROM jobs j"
        " JOIN runs r ON r.id = j.run_id JOIN projects p ON p.id = r.project_id"
        " LEFT JOIN tickets t ON t.id = j.ticket_id WHERE p.name = ?",
        (project,),
    ).fetchall()

    last: dict[str, tuple[datetime, sqlite3.Row]] = {}  # a done ticket's last ended job
    for j in jobs:
        if j["state"] == "done" and j["ended"]:
            at = _time(j["ended"])
            if j["ticket"] not in last or at > last[j["ticket"]][0]:
                last[j["ticket"]] = (at, j)

    # ticket kinds for the merged tickets
    ticket_names: list[str] = [j["ticket"] for _, j in last.values() if j["ticket"]]
    kinds: dict[str, str] = {}
    if ticket_names:
        marks = ",".join("?" for _ in ticket_names)
        for row in conn.execute(
            f"SELECT ticket, kind FROM tickets WHERE ticket IN ({marks})",  # noqa: S608
            ticket_names,
        ):
            kinds[str(row["ticket"])] = row["kind"]

    # developer attempts per ticket
    attempts: dict[str, int] = {}
    for j in jobs:
        if j["ticket"] and j["role"] in LOCAL_ROLES:
            attempts[j["ticket"]] = attempts.get(j["ticket"], 0) + 1

    # earliest started time per ticket (for took calculation)
    first_started: dict[str, datetime] = {}
    for j in jobs:
        if j["ticket"] and j["started"]:
            s = _time(j["started"])
            if j["ticket"] not in first_started or s < first_started[j["ticket"]]:
                first_started[j["ticket"]] = s

    def _display_name(agent: str | None) -> str | None:
        if not agent:
            return None
        if agent.startswith(LEAD_PREFIX):
            return agent.removeprefix(LEAD_PREFIX).capitalize()
        if agent.startswith("copilot-"):
            return "Copilot"
        return agent.removeprefix("local-").removeprefix("ollama-")

    def _label(
        merged_by: str | None, kind: str | None, dev_attempts: int, dev_outcomes: Sequence[str]
    ) -> str:
        if not merged_by:
            return ""
        if merged_by == "claude-opus":
            if kind == "lead":
                return "lead ticket"
            if dev_attempts > 0:
                if dev_attempts == 1:
                    if dev_outcomes and dev_outcomes[0] == "passed":
                        return "1st try"
                    return "after 1 developer attempt"  # the row's "finished 10:32" follows
                return f"after {dev_attempts} developer attempts"
            return ""
        if dev_attempts > 0:
            if dev_attempts == 1:
                return "1st try"
            return f"{dev_attempts} attempts"
        return ""

    merged = tuple(
        AwayTicket(
            j["ticket"],
            j["title"],
            j["merged_by"],
            display_name=_display_name(j["merged_by"]),
            attempts=attempts.get(j["ticket"], 0),
            kind=kinds.get(j["ticket"]),
            label=_label(
                j["merged_by"],
                kinds.get(j["ticket"]),
                attempts.get(j["ticket"], 0),
                tuple(
                    j2["outcome"]
                    for j2 in jobs
                    if j2["ticket"] == j["ticket"] and j2["role"] in LOCAL_ROLES
                ),
            ),
            finished=at,
            took=(at - first_started[j["ticket"]]) if j["ticket"] in first_started else None,
        )
        for at, j in sorted(last.values(), key=lambda found: found[0], reverse=True)
        if since <= at <= now
    )

    owner = conn.execute(
        "SELECT o.created FROM owner_items o JOIN projects p ON p.id = o.project_id"
        " WHERE p.name = ?",
        (project,),
    ).fetchall()
    blocked = conn.execute(
        "SELECT COUNT(*) FROM tickets t JOIN projects p ON p.id = t.project_id"
        " WHERE p.name = ? AND t.state = 'blocked'",
        (project,),
    ).fetchone()[0]

    blocked_ids_rows = conn.execute(
        "SELECT t.ticket FROM tickets t JOIN projects p ON p.id = t.project_id"
        " WHERE p.name = ? AND t.state = 'blocked' ORDER BY t.ticket",
        (project,),
    ).fetchall()
    blocked_ids = tuple(str(r["ticket"]) for r in blocked_ids_rows)

    return Away(
        merged=merged,
        failed=sum(  # as the clog counts them: not an attempt stopped short (f3-F4)
            j["role"] in LOCAL_ROLES
            and j["outcome"] == "failed"
            and j["note"] not in NOT_ATTEMPTS
            and within(j["ended"])
            for j in jobs
        ),
        escalations=sum(j["role"] == "escalation" and within(j["started"]) for j in jobs),
        blocked=int(blocked),
        needs_you=sum(within(o["created"]) for o in owner),
        claude_usd=sum(dollars(j) for j in jobs if within(j["started"])),  # uncosted: its tokens
        blocked_ids=blocked_ids,
    )
