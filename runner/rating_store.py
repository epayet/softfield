"""The agents' ratings in the metrics database (F290 D1; ADR 14 items 6–7, ADR 15 item 9,
ADR 24): the starting ratings, the standings, a ticket's, a review's and a bench's games, and
the replay. The maths is in ``runner/ratings.py``."""

import math
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from runner import metrics, ratings, session
from runner.agents import Agent
from runner.config import Config
from runner.session import Session, _at, _record

# Jobs that attempt a ticket; a refused, skipped or parked one isn't an attempt (ADR 14 item 10).
_ATTEMPT_ROLES = ("developer", "last-attempt", "lead-ticket")
BENCH = "bench"  # a bench replay's jobs (runner/bench.py): a game each (ADR 24 item 3)
REPLAY = "replay ADR 24: "  # the recompute's rows (ADR 24 item 4): + the replayed change's label
REPLAY_FROM = REPLAY + "from "  # + the estimate: where an agent's recompute starts, not a game
_TICKET_RESULTS = {
    ratings.MERGED_FIRST: ratings.FIRST,
    ratings.MERGED_LATER: ratings.LATER,
    ratings.NOT_MERGED: ratings.LOST,
}


def starting_ratings(cfg: Config) -> dict[str, float]:
    """Each agent's estimate in `[agents.*] rating`, where its rating starts."""
    return {agent.id: float(agent.rating) for agent in cfg.agents.values()}


def standing(
    conn: sqlite3.Connection, start: Mapping[str, float]
) -> tuple[dict[str, float], dict[str, set[str]]]:
    """Each agent's rating now (its latest change, else its start) and the tickets it was
    rated on. Only agents with a start are rated."""
    current, played = dict(start), dict[str, set[str]]()
    rows = conn.execute(
        "SELECT r.agent, r.after, t.ticket FROM rating_changes r"
        " LEFT JOIN tickets t ON t.id = r.ticket_id ORDER BY r.at, r.id"
    )
    for row in rows:
        if row["agent"] in current:
            current[row["agent"]] = float(row["after"])
        if row["ticket"]:
            played.setdefault(row["agent"], set()).add(row["ticket"])
    return current, played


def routing_ratings(conn: sqlite3.Connection, start: Mapping[str, float]) -> dict[str, float]:
    """Each agent's rating now, at the floor until it has played ``ratings.MIN_GAMES`` coding
    games (a finding's penalty isn't one). The stored rating, and the Agents page, keep it.
    A recompute starts the count again: its rows replay the games before it."""
    current, _ = standing(conn, start)
    games: dict[str, int] = {}
    rows = conn.execute(
        "SELECT agent, ifnull(result, '') AS result FROM rating_changes WHERE skill = ?"
        " ORDER BY at, id",
        (ratings.CODING,),
    )
    for row in rows:
        if row["result"].startswith(REPLAY_FROM):
            games[row["agent"]] = 0
        elif not row["result"].removeprefix(REPLAY).startswith(ratings.FINDING_LABEL):
            games[row["agent"]] = games.get(row["agent"], 0) + 1
    return {agent: ratings.routing_rating(r, games.get(agent, 0)) for agent, r in current.items()}


def _attempts(
    conn: sqlite3.Connection, ticket_id: int, merged_by: str | None
) -> list[ratings.Attempt]:
    """A ticket's attempts in order. A merged ticket's last attempt merged if it passed;
    otherwise the merger (an escalation that finished or implemented it) is one more."""
    marks = ", ".join("?" for _ in _ATTEMPT_ROLES)
    rows = conn.execute(
        f"SELECT agent, outcome FROM jobs WHERE ticket_id = ? AND role IN ({marks})"  # noqa: S608
        " AND outcome NOT IN ('running', 'interrupted', 'refused')"
        " AND ifnull(note, '') NOT IN ('refused', 'transient', 'parked') ORDER BY started, id",
        (ticket_id, *_ATTEMPT_ROLES),
    ).fetchall()
    attempts = [ratings.Attempt(row["agent"]) for row in rows]
    if merged_by is None:
        return attempts
    if rows and rows[-1]["outcome"] == "passed":
        attempts[-1] = ratings.Attempt(rows[-1]["agent"], merged=True)
    else:
        attempts.append(ratings.Attempt(merged_by, merged=True))
    return attempts


def _write_changes(
    conn: sqlite3.Connection, changes: list[ratings.Change], ids: Mapping[str, int], at: datetime
) -> None:
    for change, moment in zip(changes, ratings.moments(at, len(changes)), strict=True):
        metrics.add_rating_change(
            conn,
            change.agent,
            change.skill,
            change.before,
            change.after,
            at=moment,
            ticket_id=ids[change.ticket],
            result=change.label,
        )


def rate_ticket(
    conn: sqlite3.Connection,
    project_id: int,
    ticket: str,
    start: Mapping[str, float],
    at: datetime,
) -> None:
    """A merged or blocked ticket's coding games, once. A ticket with no difficulty isn't
    rated: there's nothing to play against."""
    row = conn.execute(
        "SELECT id, coalesce(difficulty_corrected, difficulty) AS difficulty, merged_by"
        " FROM tickets WHERE project_id = ? AND ticket = ?",
        (project_id, ticket),
    ).fetchone()
    if row is None or row["difficulty"] is None:
        return
    labels = ", ".join("?" for _ in ratings.TICKET_LABELS)
    rated = conn.execute(
        f"SELECT 1 FROM rating_changes WHERE ticket_id = ? AND result IN ({labels})",  # noqa: S608
        (row["id"], *ratings.TICKET_LABELS),
    ).fetchone()
    if rated:
        return
    attempts = _attempts(conn, row["id"], row["merged_by"])
    games = ratings.ticket_games(ticket, row["difficulty"], attempts)
    current, played = standing(conn, start)
    _write_changes(conn, ratings.rate(current, played, games), {ticket: row["id"]}, at)


def rate_verdicts(
    conn: sqlite3.Connection,
    project_id: int,
    milestone: str,
    start: Mapping[str, float],
    checkpoint: str | None,
    at: datetime,
) -> None:
    """The final review's verdicts on the milestone's findings, each once: a game for the
    reviewer (``checkpoint`` for a missed one), and a quarter off the author of the code once
    per ticket, whatever later verdicts come (ADR 24 item 1)."""
    rows = conn.execute(
        "SELECT f.key, f.verdict, f.agent, t.id AS ticket_id, t.ticket, t.merged_by,"
        " coalesce(t.difficulty_corrected, t.difficulty) AS difficulty FROM findings f"
        " JOIN milestones m ON m.id = f.milestone_id JOIN tickets t ON t.id = f.ticket_id"
        " WHERE m.project_id = ? AND m.key = ? AND f.verdict IS NOT NULL ORDER BY f.id",
        (project_id, milestone),
    ).fetchall()
    ids = {row["ticket"]: row["ticket_id"] for row in rows}
    marks = ", ".join("?" for _ in ids)
    done = {
        result.split(" ", 1)[1]
        for (result,) in conn.execute(
            f"SELECT result FROM rating_changes WHERE ticket_id IN ({marks})"  # noqa: S608
            " AND result LIKE '% %'",
            list(ids.values()),
        )
    }
    judged = [
        ratings.Judged(
            row["key"],
            row["ticket"],
            row["difficulty"],
            row["verdict"],
            checkpoint if row["verdict"] == "missed" else row["agent"],
            row["merged_by"],
        )
        for row in rows
        if row["key"] not in done
    ]
    penalised = {
        ticket
        for (ticket,) in conn.execute(
            "SELECT DISTINCT t.ticket FROM rating_changes r"  # noqa: S608
            f" JOIN tickets t ON t.id = r.ticket_id WHERE r.ticket_id IN ({marks})"
            " AND r.result LIKE ?",
            [*ids.values(), ratings.FINDING_LABEL + "%"],
        )
    }
    games = ratings.judged_games(judged, penalised)
    current, played = standing(conn, start)
    _write_changes(conn, ratings.rate(current, played, games), ids, at)


def rate_bench(
    conn: sqlite3.Connection,
    project_id: int,
    run_id: int,
    ticket: str,
    agent: str,
    start: Mapping[str, float],
    at: datetime,
) -> None:
    """``agent``'s bench replay of ``ticket`` in bench run ``run_id``, as one coding game, once
    (ADR 24 item 3). A replay with a refusal (or still running) is no game, and a ticket with
    no difficulty isn't rated."""
    row = conn.execute(
        "SELECT id, coalesce(difficulty_corrected, difficulty) AS difficulty"
        " FROM tickets WHERE project_id = ? AND ticket = ?",
        (project_id, ticket),
    ).fetchone()
    if row is None or row["difficulty"] is None:
        return
    jobs = conn.execute(
        "SELECT outcome, started FROM jobs WHERE run_id = ? AND ticket_id = ? AND role = ?"
        " AND agent = ? ORDER BY started, id",
        (run_id, row["id"], BENCH, agent),
    ).fetchall()
    game = _bench_game(agent, ticket, row["difficulty"], [job["outcome"] for job in jobs])
    if game is None:
        return
    began = _at(jobs[0]["started"])
    rated = conn.execute(
        "SELECT at FROM rating_changes WHERE agent = ? AND ticket_id = ? AND result LIKE ?",
        (agent, row["id"], ratings.BENCH_LABEL + "%"),
    )
    if any(_at(r["at"]) >= began for r in rated):
        return
    current, played = standing(conn, start)
    _write_changes(conn, ratings.rate(current, played, [game]), {ticket: row["id"]}, at)


def _bench_game(
    agent: str, ticket: str, difficulty: float, outcomes: Sequence[str]
) -> ratings.Game | None:
    """One bench run's replay of a ticket as a game; none with a refusal, still running, or
    void (it changed the main checkout, f7-06)."""
    if not outcomes or any(o in ("running", "interrupted", "refused", "void") for o in outcomes):
        return None
    passed = next((n for n, o in enumerate(outcomes, start=1) if o == "passed"), None)
    return ratings.bench_game(agent, ticket, difficulty, passed)


def void_benches_before(
    conn: sqlite3.Connection, project_id: int, agents: Mapping[str, Agent], cut_off: datetime
) -> dict[str, int]:
    """Void the OpenCode agents' ticket replays that started before ``cut_off``: until f7-06's
    fix they worked in the main checkout, so their gates said nothing about them (f7-07). Each
    agent's count of jobs voided; review benches, other harnesses and later jobs stay."""
    opencode = {a.id for a in agents.values() if a.harness == "opencode"}
    jobs = conn.execute(
        "SELECT j.id, j.agent, j.started FROM jobs j JOIN tickets t ON t.id = j.ticket_id"
        " WHERE j.role = ? AND t.project_id = ? AND j.outcome != 'void'",
        (BENCH, project_id),
    ).fetchall()
    voided: dict[str, int] = {}
    for job in jobs:
        if job["agent"] in opencode and _moment(job["started"]) < cut_off:
            conn.execute(
                "UPDATE jobs SET outcome = 'void', note = ? WHERE id = ?",
                (f"void: benched in the main checkout, before {cut_off.isoformat()}", job["id"]),
            )
            voided[job["agent"]] = voided.get(job["agent"], 0) + 1
    return voided


@dataclass(frozen=True)
class Replayed:
    """An agent's rating before and after the ADR 24 recompute."""

    agent: str
    before: float  # its standing
    after: float
    games: int  # its coding games replayed, as routing counts them
    written: bool  # False: the recompute changed nothing, so wrote nothing


def _moment(value: str) -> datetime:
    at = _at(value)
    return at if at.tzinfo else at.replace(tzinfo=UTC)  # a backfilled time may have no zone


def _recorded_games(
    conn: sqlite3.Connection, project_id: int
) -> tuple[list[tuple[datetime, ratings.Game]], dict[str, int]]:
    """The games the ratings have played, at their times, under ADR 24: each ticket's game and
    each verdict once, and every bench run's replay from its jobs (benches before ADR 24 were
    never rated). Findings on a merged ticket's code re-play its game a quarter lower (item 1),
    at the game's time; a penalty with no game to fold into stays, once per (agent, ticket).
    Earlier recomputes are left out. Also each ticket's id."""
    rows = conn.execute(
        "SELECT r.agent, r.skill, r.at, ifnull(r.result, '') AS result, t.id AS ticket_id,"
        " t.ticket, coalesce(t.difficulty_corrected, t.difficulty) AS difficulty"
        " FROM rating_changes r JOIN tickets t ON t.id = r.ticket_id"
        " WHERE t.project_id = ? AND ifnull(r.result, '') NOT LIKE ? ORDER BY r.at, r.id",
        (project_id, REPLAY + "%"),
    ).fetchall()
    found: dict[tuple[str, str], str] = {}  # (author, ticket): its first finding's label
    for row in rows:
        if row["result"].startswith(ratings.FINDING_LABEL):
            found.setdefault((row["agent"], row["ticket"]), row["result"])
    merged = (ratings.MERGED_FIRST, ratings.MERGED_LATER)
    folded = {
        (row["agent"], row["ticket"])
        for row in rows
        if row["result"] in merged and row["difficulty"] is not None
    } & found.keys()
    games: list[tuple[datetime, ratings.Game]] = []
    ids: dict[str, int] = {}
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        agent, ticket, label, difficulty = row["agent"], row["ticket"], row["result"], None
        if label in _TICKET_RESULTS:
            once, result, difficulty = "ticket", _TICKET_RESULTS[label], row["difficulty"]
            if (agent, ticket) in folded:
                result, label = result + ratings.FINDING, f"{label}, {found[agent, ticket]}"
        elif label.startswith(ratings.FINDING_LABEL):
            if (agent, ticket) in folded:
                continue
            once, result = "finding", ratings.FINDING  # ADR 24 item 1: one per ticket
        elif row["skill"] == ratings.REVIEWING and label.split(" ")[0] in ratings.VERDICT_RESULTS:
            once, result = label, ratings.VERDICT_RESULTS[label.split(" ")[0]]
            difficulty = row["difficulty"]
        else:
            continue  # a bench game is played from its jobs, below
        if (agent, ticket, once) in seen or (once != "finding" and difficulty is None):
            continue
        seen.add((agent, ticket, once))
        ids[ticket] = row["ticket_id"]
        game = ratings.Game(agent, row["skill"], ticket, difficulty, result, label)
        games.append((_moment(row["at"]), game))
    jobs = conn.execute(
        "SELECT j.run_id, j.agent, j.outcome, j.started, t.id AS ticket_id, t.ticket,"
        " coalesce(t.difficulty_corrected, t.difficulty) AS difficulty FROM jobs j"
        " JOIN tickets t ON t.id = j.ticket_id WHERE j.role = ? AND t.project_id = ?"
        " AND coalesce(t.difficulty_corrected, t.difficulty) IS NOT NULL"
        " ORDER BY j.started, j.id",
        (BENCH, project_id),
    ).fetchall()
    benched: dict[tuple[int, str, str], list[sqlite3.Row]] = {}
    for job in jobs:
        benched.setdefault((job["run_id"], job["ticket"], job["agent"]), []).append(job)
    for (_, ticket, agent), group in benched.items():
        outcomes = [job["outcome"] for job in group]
        if (replay := _bench_game(agent, ticket, group[0]["difficulty"], outcomes)) is not None:
            ids[ticket] = group[0]["ticket_id"]
            games.append((_moment(group[0]["started"]), replay))
    games.sort(key=lambda timed: timed[0])  # stable: same-moment games keep their order
    return games, ids


def replay_ratings(
    conn: sqlite3.Connection, project_id: int, start: Mapping[str, float], at: datetime
) -> list[Replayed]:
    """Recompute every agent's rating from its estimate in ``start``, re-playing its games in
    time order under ADR 24 (item 4). An agent it changes gets new rows after every existing
    one: a ``REPLAY_FROM`` start, then its replayed changes, so the history stays and
    ``standing`` reads the recompute as current. A second recompute writes nothing new."""
    timed, ids = _recorded_games(conn, project_id)
    changes = ratings.rate(start, {}, [game for _, game in timed])
    current, _ = standing(conn, start)
    latest = conn.execute("SELECT max(at) FROM rating_changes").fetchone()[0]
    if latest is not None:
        at = max(at, _moment(latest) + timedelta(microseconds=1))
    replayed: list[Replayed] = []
    rows: list[tuple[str, str, float, float, int | None, str]] = []
    for agent, estimate in start.items():
        mine = [change for change in changes if change.agent == agent]
        after = mine[-1].after if mine else estimate
        games = sum(
            c.skill == ratings.CODING and not c.label.startswith(ratings.FINDING_LABEL)
            for c in mine
        )
        written = not math.isclose(after, current[agent], rel_tol=0, abs_tol=1e-9)
        if written:
            rows.append((agent, ratings.CODING, current[agent], estimate, None, f"{estimate:g}"))
            rows += [(c.agent, c.skill, c.before, c.after, ids[c.ticket], c.label) for c in mine]
        replayed.append(Replayed(agent, current[agent], after, games, written))
    for (agent, skill, before, after, ticket_id, label), moment in zip(
        rows, ratings.moments(at, len(rows)), strict=True
    ):
        prefix = REPLAY_FROM if ticket_id is None else REPLAY
        metrics.add_rating_change(
            conn, agent, skill, before, after, at=moment, ticket_id=ticket_id, result=prefix + label
        )
    return replayed


def rate_finished(s: Session, ticket: str) -> None:
    """Rate a ticket that was merged or blocked (best effort, like every metrics write)."""
    if s.project_id is not None:
        _record(s, rate_ticket, s.project_id, ticket, starting_ratings(s.cfg), session.now())


def current_ratings(s: Session) -> dict[str, float]:
    """Each agent's rating as routing reads it (``routing_ratings``); every agent at the floor
    when the database can't be read: an estimate is never trusted (ADR 24 item 3)."""
    start = starting_ratings(s.cfg)
    found = _record(s, routing_ratings, start)
    return found if found is not None else {agent: ratings.LOWEST for agent in start}
