"""The factory line (f3 D11): the live floor at ``/line``, and the worked example for a
drawing. ``live_line`` builds one JSON document holding every rule; ``static/factory.js`` only
draws it (and lays it out), so its tests are on this document, plus one browser test.

- **Stations** (ids fixed): the field (seeds, planting, rows), the queue, the lead, the
  reviewers, the developer bay, the checks (the runner's gates, not an agent), merged, ripe and
  the stash. One machine per agent, on the station its roles give it.
- **Trips**, from the jobs (D10, on D11's belts): a job's start brings its crate to its station,
  on the belt from where it waits; its end sends it on (``_after``). A checkpoint is a batch
  crate, ``merged→reviewers``, then off the floor. A move with no belt (a direction, a parked
  lead ticket going back to the queue) simply moves the crate.
- **Today**: each belt counts its trips since local midnight (``now``'s own midnight), and is
  ``carrying`` while a live job's crate came on it.
- **The field**: rows are milestones with ready or running tickets, ripe ones have every
  ticket merged and wait for the owner's sign-off, the stash holds signed-off ones, seeds are
  tickets set aside (``later``, which lists them), planting counts the cards being planned
  with the owner (``_planting``). Its five stations' counts come from the board's cards
  (``board.py``), one each: seed, sprouting, planted, ripe, harvested; at a past ``at``,
  which the board doesn't know, from ``field``.
- **A wait** (f9-01): while the live run waits instead of working, ``wait`` names the one
  machine or station it waits at and says for what (``_wait``); the floor draws it clogged.
- **Any moment** (f3-06): ``live_line(..., at=t)`` applies the same rules to the jobs whose
  times cover ``t`` (an unfinished one until its run's last heartbeat) and to each ticket's
  state then, rebuilt from its trips. ``replay`` is the document at ``since`` and every event
  up to ``until``; ``static/factory.js`` only steps through it.
"""

import json
import re
import sqlite3
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from factory_dashboard import queries
from factory_dashboard.app import Db, Now, Project, render
from factory_dashboard.jobs import _failed_gate
from factory_dashboard.overview import LIVE, live_runs
from runner import dispatch, loop, metrics
from runner.config import Config, load_config
from runner.tasks import milestone_order, short_key

if TYPE_CHECKING:
    from factory_dashboard.board import Board  # board.py imports from here

router = APIRouter()

STATIONS = {
    "seeds": "Seeds",
    "planting": "Planting",
    "rows": "Planted rows",
    "queue": "Queue",
    "lead": "The lead",
    "reviewers": "Reviewers",
    "developers": "Developer bay",
    "checks": "Checks",
    "merged": "Merged today",
    "ripe": "Ripe",
    "stash": "Harvest stash",
}
BELTS = {  # D11's ids, and the words on them
    "seeds→planting": "sprouting",
    "planting→rows": "planted",
    "rows→queue": "tickets",
    "queue→lead": "lead tickets",
    "queue→developers": "developer",
    "lead→checks": "lead's work: to checks",
    "developers→checks": "to checks",
    "checks→developers": "failed: retry",
    "checks→lead": "failed twice: direction · 3×: escalation",
    "checks→merged": "merged",
    "merged→ripe": "ripened",
    "ripe→stash": "your sign-off",
    "merged→reviewers": "checkpoints",
}
FIELD_BELTS = ("seeds→planting", "planting→rows", "rows→queue")  # not counted until f3-08
DEVELOPER_ROLES = ("developer", "last-attempt")
REVIEWER_ROLES = ("checkpoint", "checkpoint-stand-in", "checkpoint-shadow")
LEAD_ROLES = ("lead-ticket", "direction", "escalation", "review", "narrative")
TICKET_ROLES = ("developer", "last-attempt", "direction", "escalation", "lead-ticket")
BATCH_ROLES = (*REVIEWER_ROLES, "review")
STAND_IN = "checkpoint-stand-in"
MACHINE_STATIONS = ("lead", "reviewers", "developers")
_LONG_AGO = datetime.min.replace(tzinfo=UTC)
EVENTS = ("trip", "check", "machine", "limit", "card", "idle")  # at one moment, in this order
IDLE = timedelta(minutes=40)  # D10: a longer stretch with nothing working is one event
REPLAY_LIMIT = timedelta(days=7)  # the longest stretch ``/line/replay`` serves
SEEN = "line_seen"  # the cookie: when the owner last opened the line


def _station(roles: Iterable[str]) -> str | None:
    """The station a set of roles puts an agent on: the lead's roles first, then reviewing."""
    found = set(roles)
    for station, own in (
        ("lead", LEAD_ROLES),
        ("reviewers", REVIEWER_ROLES),
        ("developers", DEVELOPER_ROLES),
    ):
        if found & set(own):
            return station
    return None


def _when(at: str) -> datetime:
    moment = datetime.fromisoformat(at)
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


@dataclass(frozen=True)
class Job:
    id: int
    ticket: str | None
    done: bool  # its ticket is merged
    role: str
    agent: str
    started: datetime
    ended: datetime | None
    outcome: str
    note: str | None

    @property
    def station(self) -> str:
        return _station([self.role]) or "lead"

    @property
    def crate(self) -> str:
        return self.ticket or f"{self.role}-{self.id}"


@dataclass(frozen=True)
class Trip:
    at: datetime
    crate: str
    belts: tuple[str, ...]
    to: str | None  # a station; None: off the floor
    job: int | None = None  # the job whose start or end moved it


def _on_belts(*belts: str) -> tuple[str, ...]:
    return tuple(b for b in belts if b in BELTS)  # no belt: the crate is simply moved


def _stopped_short(job: Job) -> bool:
    """A job that stopped before its end: parked by a limit, refused or interrupted."""
    return job.outcome in ("interrupted", "refused") or job.note in ("parked", "interrupted")


def _merge(machine: str) -> tuple[str, tuple[str, ...]]:
    return "merged", _on_belts(f"{machine}→checks", "checks→merged")


def _after(job: Job, following: Job | None) -> tuple[str, tuple[str, ...]]:
    """Where a ticket's crate goes when ``job`` ends, and on which belts. Directions and
    findings are text: they skip the checks."""
    machine, passed = job.station, job.outcome == "passed"
    if machine == "lead" and _stopped_short(job):
        return "queue", ()
    if job.role == "direction":
        return ("developers", ()) if passed else (machine, ())
    if job.role == "escalation":
        if following is not None and following.station != "lead":  # requeued
            return "queue", ()
        if following is None and passed and job.done:  # finished or implemented
            return _merge(machine)
        return machine, ()
    if passed:
        return _merge(machine)
    return "checks", _on_belts(f"{machine}→checks")


def _ticket_trips(jobs: Sequence[Job]) -> list[Trip]:
    trips, here = [], "queue"
    for n, job in enumerate(jobs):
        if job.station != here:  # from wherever it waits to the job's machine
            belts = _on_belts(f"{here}→{job.station}")
            trips.append(Trip(job.started, job.crate, belts, job.station, job.id))
            here = job.station
        if job.ended is None:
            break
        there, belts = _after(job, jobs[n + 1] if n + 1 < len(jobs) else None)
        if there != here:
            trips.append(Trip(job.ended, job.crate, belts, there, job.id))
            here = there
    return trips


def _batch_trips(job: Job) -> list[Trip]:
    belts = _on_belts(f"merged→{job.station}")
    trips = [Trip(job.started, job.crate, belts, job.station, job.id)]
    if job.ended is not None:
        trips.append(Trip(job.ended, job.crate, (), None, job.id))
    return trips


# --- the data -------------------------------------------------------------------------------


def _jobs(conn: sqlite3.Connection, project: str) -> list[Job]:
    """The project's jobs that move a crate, in the order they started."""
    rows = conn.execute(
        "SELECT j.*, t.ticket, t.state FROM jobs j JOIN runs r ON r.id = j.run_id"
        " JOIN projects p ON p.id = r.project_id LEFT JOIN tickets t ON t.id = j.ticket_id"
        " WHERE p.name = ? AND j.started IS NOT NULL",
        (project,),
    ).fetchall()
    found = [
        Job(
            id=r["id"],
            ticket=r["ticket"],
            done=r["state"] == "done",
            role=r["role"],
            agent=r["agent"],
            started=_when(r["started"]),
            ended=_when(r["ended"]) if r["ended"] else None,
            outcome=r["outcome"],
            note=r["note"],
        )
        for r in rows
        if (r["ticket"] and r["role"] in TICKET_ROLES)
        or (not r["ticket"] and r["role"] in BATCH_ROLES)
    ]
    return sorted(found, key=lambda j: (j.started, j.id))


def trips(conn: sqlite3.Connection, project: str) -> list[Trip]:
    """Every crate's trips in the project, in time order."""
    jobs = _jobs(conn, project)
    by_ticket: dict[str, list[Job]] = {}
    found: list[Trip] = []
    for job in jobs:
        if job.ticket:
            by_ticket.setdefault(job.ticket, []).append(job)
        else:
            found += _batch_trips(job)
    for own in by_ticket.values():
        found += _ticket_trips(own)
    return sorted(found, key=lambda trip: trip.at)  # stable: a crate's own trips keep their order


@dataclass(frozen=True)
class Work:
    """A job and the stretch it keeps its machine working."""

    job: int
    role: str
    agent: str
    attempt: int
    ticket: str | None
    started: datetime
    until: datetime | None  # its end; unfinished: its run's last heartbeat, plus ``LIVE``
    tokens_in: int | None
    steps: int | None

    @property
    def crate(self) -> str:
        return self.ticket or f"{self.role}-{self.job}"

    def covers(self, at: datetime) -> bool:
        return self.until is not None and self.started <= at < self.until


def _work(conn: sqlite3.Connection, project: str) -> list[Work]:
    """Every job of the project, in the order they started."""
    rows = conn.execute(
        "SELECT j.id, j.role, j.agent, j.attempt, j.started, j.ended, j.tokens_in, j.steps,"
        " t.ticket, r.heartbeat FROM jobs j JOIN runs r ON r.id = j.run_id"
        " JOIN projects p ON p.id = r.project_id LEFT JOIN tickets t ON t.id = j.ticket_id"
        " WHERE p.name = ? AND j.started IS NOT NULL",
        (project,),
    ).fetchall()
    found = []
    for r in rows:
        if r["ended"]:
            until: datetime | None = _when(r["ended"])
        else:
            until = _when(r["heartbeat"]) + LIVE if r["heartbeat"] else None
        found.append(
            Work(
                job=r["id"],
                role=r["role"],
                agent=r["agent"],
                attempt=r["attempt"],
                ticket=r["ticket"],
                started=_when(r["started"]),
                until=until,
                tokens_in=r["tokens_in"],
                steps=r["steps"],
            )
        )
    return sorted(found, key=lambda w: (w.started, w.job))


def _crates(
    work: Sequence[Work], at: datetime, tickets: dict[str, sqlite3.Row]
) -> list[tuple[Work, dict[str, Any]]]:
    """The jobs at work at ``at``, each with the crate its machine works on."""
    found = []
    for w in work:
        if not w.covers(at):
            continue
        ticket = tickets.get(w.ticket) if w.ticket else None
        crate = {
            "ticket": w.ticket,
            "title": ticket["title"] if ticket else None,
            "kind": _kind(ticket["kind"]) if ticket else "batch",
            "role": w.role,
            "attempt": w.attempt,
            "minutes": int((at - w.started).total_seconds() // 60),
        }
        found.append((w, crate))
    return found


def _working(
    work: Sequence[Work], at: datetime, tickets: dict[str, sqlite3.Row]
) -> dict[str, dict[str, Any]]:
    """Each working agent's role and crate at ``at`` (its oldest job's)."""
    found: dict[str, dict[str, Any]] = {}
    for w, crate in _crates(work, at, tickets):
        found.setdefault(w.agent, {"role": w.role, "crate": crate})
    return found


def _states(
    conn: sqlite3.Connection, project: str, every: Sequence[Trip], at: datetime
) -> dict[str, str]:
    """Each ticket's state at ``at``. After its last trip, its row's (merged: done); before,
    where its trips left its crate (merged: done, on the floor: running, in the queue: ready),
    and ``planned`` while it waits for a milestone that hasn't started."""
    rows = conn.execute(
        "SELECT t.ticket, t.state, m.started FROM tickets t JOIN projects p ON p.id = t.project_id"
        " LEFT JOIN milestones m ON m.id = t.milestone_id WHERE p.name = ?",
        (project,),
    ).fetchall()
    moves: dict[str, list[Trip]] = {}
    for trip in every:
        moves.setdefault(trip.crate, []).append(trip)
    states = {}
    for r in rows:
        own = moves.get(r["ticket"], [])
        past = [t for t in own if t.at <= at]
        if past and past[-1].to == "merged":
            state = "done"
        elif len(past) == len(own):  # no trips, or after the last one
            state = r["state"]
        elif past and past[-1].to != "queue":
            state = "running"
        else:
            state = "ready"
        if state == "ready" and r["started"] and _when(r["started"]) > at:
            state = "planned"
        states[r["ticket"]] = state
    return states


def _config(conn: sqlite3.Connection, project: str) -> Config | None:
    """The project's ``.softfield/project.toml``, or None when its repo can't be read."""
    row = conn.execute("SELECT repo FROM projects WHERE name = ?", (project,)).fetchone()
    if row is None or not row["repo"]:
        return None
    try:
        return load_config(Path(row["repo"]))
    except (OSError, ValueError, KeyError, TypeError):  # missing, unreadable or invalid
        return None


def _scale(rating: float | None) -> float:
    """Stronger agents are bigger, with a bigger chimney."""
    return round(0.8 + 0.04 * rating, 2) if rating is not None else 1.0


def _display_rating(rating: float | None) -> str:
    """The rating as it appears on a plate: rounded to one decimal, no trailing zero."""
    if rating is None:
        return ""
    r = round(rating, 1)
    if r == int(r):
        return str(int(r))
    return f"{r:g}"


def _name(agent: str) -> str:
    if agent.startswith(queries.LEAD_PREFIX):
        return agent.removeprefix(queries.LEAD_PREFIX).capitalize()
    if agent.startswith("copilot-"):
        return "Copilot"
    return agent.removeprefix("local-").removeprefix("ollama-")


def _where(agent: str, local: bool) -> str:
    if local:
        return "local GPU"
    for prefix, where in (
        ("ollama-", "Ollama cloud"),
        ("claude-", "Claude"),
        ("copilot-", "Copilot"),
    ):
        if agent.startswith(prefix):
            return where
    return "cloud"


def _limit(conn: sqlite3.Connection, agent: str, now: datetime) -> datetime | None:
    """When the agent's open limit resets: its own refusal's, or any Claude agent's for Claude
    (one account); None when no limit is open at ``now``."""
    like = queries.LEAD_PREFIX + "%" if agent.startswith(queries.LEAD_PREFIX) else agent
    resets = [
        _when(r["resets_at"])
        for r in conn.execute(
            "SELECT at, resets_at FROM usage_events WHERE kind = 'refusal' AND agent LIKE ?"
            " AND resets_at IS NOT NULL",
            (like,),
        )
        if _when(r["at"]) <= now < _when(r["resets_at"])
    ]
    return max(resets) if resets else None


def _machines(
    conn: sqlite3.Connection,
    config: Config | None,
    jobs: Sequence[Job],
    working: dict[str, dict[str, Any]],
    now: datetime,
    merged_by: dict[str, int] | None = None,
    next_lead: str | None = None,
) -> list[dict[str, Any]]:
    """One machine per agent a role names in the config (or, without one, a job used), on the
    station its roles give it: the lead first, then the reviewers, then the developers."""
    ever: dict[str, set[str]] = {}
    for job in jobs:
        ever.setdefault(job.agent, set()).add(job.role)
    roles: dict[str, set[str]] = {}
    if config is None:
        roles = {agent: set(own) for agent, own in ever.items()}
    else:
        for role, ids in config.roles.items():
            for agent in ids:
                roles.setdefault(agent, set()).add(role)
        for agent in working:  # a job on an agent no role names any more
            roles.setdefault(agent, set())
    agents = config.agents if config else {}
    stand_ins = (
        set(config.roles.get(STAND_IN, ())) - set(config.roles.get("checkpoint", ()))
        if config
        else set()
    )

    found = []
    for agent, own in roles.items():
        station = _station(own) or (
            _station([working[agent]["role"]]) if agent in working else None
        )
        if station is None:
            continue
        model = agents[agent].model if agent in agents else ""
        local = agent.startswith("local-") or model.startswith("lmstudio/")
        rating = queries._rating(conn, agent)
        if rating is None and agent in agents:
            rating = agents[agent].rating
        reset = _limit(conn, agent, now)
        if agent in working:
            state = "working"
        elif reset is not None:
            state = "waiting"
        elif config is not None and not own:
            state = "off"
        else:
            state = "idle"
        lost = ever.get(agent, set()) - own if config is not None else set()
        merged_today = (merged_by or {}).get(agent, 0)
        found.append(
            {
                "id": agent,
                "station": station,
                "name": _name(agent),
                "where": _where(agent, local),
                "local": local,
                "rating": _display_rating(rating),
                "scale": _scale(rating),
                "state": state,
                "crate": working[agent]["crate"] if agent in working else None,
                "reset": reset.astimezone(now.tzinfo).strftime("%H:%M") if reset else None,
                "stand_in": agent in stand_ins,
                "off": sorted(r for r in lost if _station([r])),
                "merged_today": merged_today,
                "next_ticket": next_lead,
            }
        )
    return sorted(found, key=lambda m: MACHINE_STATIONS.index(m["station"]))


def _natural(ticket: str) -> list[tuple[int, str]]:
    """Sorts f9-04 before f23-01, and f9-4 before f9-10."""
    return [(int(p), "") if p.isdigit() else (-1, p) for p in re.split(r"(\d+)", ticket)]


def _planting(conn: sqlite3.Connection, project: str, rows: Iterable[sqlite3.Row]) -> set[str]:
    """The cards being planned with the owner, by short key: an idea or a card in planning,
    and any card an open thread is about that has no ticket yet. The general thread is about
    no card."""
    rows = list(rows)
    ticketed = {short_key(r["key"]) for r in rows if r["ticket"]}
    cards = {short_key(r["key"]) for r in rows if r["state"] in ("idea", "planning")}
    threads = conn.execute(
        "SELECT t.card FROM planner_threads t JOIN projects p ON p.id = t.project_id"
        " WHERE p.name = ? AND t.archived IS NULL AND t.card != 'general'",
        (project,),
    )
    return cards | {r["card"] for r in threads if r["card"] not in ticketed}


def _field(
    conn: sqlite3.Connection, project: str, ticket_states: dict[str, str], at: datetime
) -> dict[str, Any]:
    """The field at ``at``: a milestone is on it once started, ripe once every ticket is done
    and its review is written (its sign-off sheet stored, F50 D1), in the stash once signed
    off."""
    rows = conn.execute(
        "SELECT m.key, m.title, m.status, m.state, m.started, m.ended, m.signoff, t.ticket,"
        " t.title AS goal FROM milestones m"
        " JOIN projects p ON p.id = m.project_id LEFT JOIN tickets t ON t.milestone_id = m.id"
        " WHERE p.name = ?",
        (project,),
    ).fetchall()
    milestones: dict[str, dict[str, Any]] = {}
    for r in rows:
        if r["started"] and _when(r["started"]) > at:
            continue
        m = milestones.setdefault(
            r["key"],
            {
                "key": r["key"],
                "title": r["title"],
                "done": r["status"] == "done" and not (r["ended"] and _when(r["ended"]) > at),
                "ended": r["ended"],
                "reviewed": r["signoff"] is not None,
                "states": [],
            },
        )
        if r["ticket"] and ticket_states.get(r["ticket"]):
            state = ticket_states[r["ticket"]]
            if state not in ("later", metrics.REMOVED):
                m["states"].append(state)
    planted, ripe, stash = [], [], []
    for m in sorted(milestones.values(), key=lambda m: milestone_order(m["key"])):
        states = m["states"]
        if m["done"]:
            stash.append(m)
        elif "ready" in states or "running" in states or (states and not m["reviewed"]):
            planted.append(
                {
                    "key": m["key"],
                    "title": m["title"],
                    "ready": states.count("ready"),
                    "running": states.count("running"),
                    "done": states.count("done"),
                    "total": len(states),
                }
            )
        elif states and all(s == "done" for s in states):
            ripe.append(m)
    stash.sort(key=lambda m: _when(m["ended"]) if m["ended"] else _LONG_AGO, reverse=True)
    later = sorted((t for t, state in ticket_states.items() if state == "later"), key=_natural)
    goals = {r["ticket"]: r["goal"] for r in rows if r["ticket"]}
    return {
        "seeds": len(later),
        "later": [{"ticket": t, "title": goals.get(t)} for t in later],
        "planting": len(_planting(conn, project, rows)),
        "rows": planted,
        "ripe": [{"key": m["key"], "title": m["title"]} for m in ripe],
        "stash": [{"key": m["key"], "title": m["title"], "ended": m["ended"]} for m in stash],
    }


def _kind(kind: str | None) -> str:
    return "lead" if kind == "lead" else "developer"


def _tickets(conn: sqlite3.Connection, project: str) -> dict[str, sqlite3.Row]:
    return {
        r["ticket"]: r
        for r in conn.execute(
            "SELECT t.ticket, t.title, t.kind, m.key AS milestone FROM tickets t"
            " JOIN projects p ON p.id = t.project_id"
            " LEFT JOIN milestones m ON m.id = t.milestone_id WHERE p.name = ?",
            (project,),
        )
    }


def _due_reviews(conn: sqlite3.Connection, project: str, now: datetime) -> list[dict[str, Any]]:
    """The reviews `runner run` takes before its next ticket (f4-20), as batch crates. One
    the runner parked until Claude's reset (F53) says so in `waits`, the hour in local time;
    parked between two rounds, its milestone is under `review` and gets its crate all the
    same."""
    parked: dict[str, datetime] = {}
    row = conn.execute("SELECT id FROM projects WHERE name = ?", (project,)).fetchone()
    for job in metrics.open_jobs(conn, row["id"]) if row else []:
        if job["kind"] == "review" and job["not_before"]:
            until = _when(job["not_before"])
            if until > now:
                parked[job["subject"]] = until
    keys = [
        r["key"]
        for r in conn.execute(
            "SELECT m.key, m.status FROM milestones m JOIN projects p ON p.id = m.project_id"
            " WHERE p.name = ? AND m.status IN (?, 'review')",
            (project, metrics.REVIEW_DUE),
        )
        if r["status"] == metrics.REVIEW_DUE or r["key"] in parked
    ]
    return [
        {
            "ticket": None,
            "role": "review",
            "title": f"review {short_key(key).upper()}",
            "kind": "batch",
            "milestone": key,
            "waits": (
                [f"Claude's reset at {parked[key].astimezone():%H:%M}"] if key in parked else []
            ),
        }
        for key in sorted(keys, key=milestone_order)
    ]


def live_line(
    conn: sqlite3.Connection,
    project: str,
    now: datetime,
    at: datetime | None = None,
    *,
    cards: "Board | None" = None,
) -> dict[str, Any]:
    """D11's document at ``at`` (default ``now``): stations, machines with their state and
    crate, belts with that day's count (since ``at``'s midnight) and ``carrying``, Now and the
    queue in run order. The jobs working are those whose times cover ``at``."""
    live = at is None  # the board knows only the present
    at = at or now
    midnight = at.replace(hour=0, minute=0, second=0, microsecond=0)
    tickets = _tickets(conn, project)
    jobs = _jobs(conn, project)
    every = trips(conn, project)
    found = [t for t in every if t.at <= at]
    today = [t for t in found if t.at >= midnight]
    states = _states(conn, project, every, at)

    # What works then, and the belt that brought each crate.
    carrying: set[str] = set()
    now_working = []
    work = _work(conn, project)
    for w, on in _crates(work, at, tickets):
        came = [t for t in found if t.crate == w.crate]
        if came:
            carrying.update(came[-1].belts)
        now_working.append({**on, "agent": w.agent, "tokens_in": w.tokens_in, "steps": w.steps})
    working = _working(work, at, tickets)

    field = _field(conn, project, states, at)
    merged = [
        {
            "ticket": t.crate,
            "title": tickets[t.crate]["title"],
            "kind": _kind(tickets[t.crate]["kind"]),
            "milestone": tickets[t.crate]["milestone"],
        }
        for t in today
        if t.to == "merged" and t.crate in tickets
    ]
    upcoming = queries.run_order(conn, project, states)
    tickets_next: list[dict[str, Any]] = [
        {
            "ticket": u.ticket,
            "title": u.title,
            "kind": _kind(u.kind),
            "milestone": u.milestone,
            "waits": list(u.waits),
            "priority": u.priority,
            "early_for": u.early_for,
        }
        for u in upcoming
    ]
    # a parked review goes behind the last ticket that can run; the run order is kept
    reviews = _due_reviews(conn, project, now)
    free = max((n for n, t in enumerate(tickets_next, start=1) if not t["waits"]), default=0)
    ordered = [
        *(r for r in reviews if not r["waits"]),
        *tickets_next[:free],
        *(r for r in reviews if r["waits"]),
        *tickets_next[free:],
    ]
    queue = [{**crate, "number": n} for n, crate in enumerate(ordered, start=1)]

    counts: dict[str, int | None] = {belt: sum(belt in t.belts for t in today) for belt in BELTS}
    counts.update(dict.fromkeys(FIELD_BELTS))
    merges: dict[str, datetime] = {}  # each milestone's last merge
    for t in found:
        if t.to == "merged" and t.crate in tickets:
            merges[tickets[t.crate]["milestone"]] = t.at
    counts["merged→ripe"] = sum(merges.get(m["key"], midnight) > midnight for m in field["ripe"])
    counts["ripe→stash"] = sum(
        bool(m["ended"]) and midnight <= _when(m["ended"]) <= at for m in field["stash"]
    )

    config = _config(conn, project)
    merged_by: dict[str, int] = {}
    for t in today:
        if t.to == "merged" and t.job is not None:
            for j in jobs:
                if j.id == t.job:
                    merged_by[j.agent] = merged_by.get(j.agent, 0) + 1
                    break
    next_lead: str | None = None
    for q in queue:
        if q["kind"] == "lead":
            next_lead = q["ticket"]
            break
    machines = _machines(conn, config, jobs, working, at, merged_by=merged_by, next_lead=next_lead)
    count = {
        "seeds": field["seeds"],
        "planting": field["planting"],
        "rows": len(field["rows"]),
        "queue": len(queue),
        "checks": None,
        "merged": len(merged),
        "ripe": len(field["ripe"]),
        "stash": len(field["stash"]),
        **{s: sum(m["station"] == s for m in machines) for s in MACHINE_STATIONS},
    }
    if live:
        from factory_dashboard.board import board  # board.py imports from this module

        if cards is None:
            cards = board(conn, project, now)
        stages = {stage: len(found) for stage, found in cards.stages.items()}
        count.update(
            seeds=stages["seed"],
            planting=stages["sprouting"],
            rows=stages["planted"],
            ripe=stages["ripe"],
            stash=stages["harvested"] + cards.more_harvested,
        )
    return {
        "at": at.isoformat(),
        "stations": [
            {"id": key, "label": label, "count": count[key]} for key, label in STATIONS.items()
        ],
        "machines": machines,
        "belts": [
            {
                "id": belt,
                "label": label,
                "from": belt.split("→")[0],
                "to": belt.split("→")[1],
                "today": counts[belt],
                "carrying": belt in carrying,
            }
            for belt, label in BELTS.items()
        ],
        "queue": queue,
        "merged": merged,
        "field": field,
        "now": {"working": now_working, "next": queue[:3]},
        "clog": _clog(conn, project, machines, midnight, at),
        "wait": _wait(conn, project, machines, queue, field, now) if live else None,
    }


# What the run says while it waits (``loop.set_activity``): `wait_for_claude`'s words, with the
# job it waits for, and the two causes `_idle_line` gives for Claude.
_CLAUDE_WAIT = re.compile(
    re.escape(loop.WAITING_FOR_CLAUDE) + r"(?: · (?P<what>.+?))?(?: until \d\d:\d\d)?"
)
_IDLE_CLAUDE = re.compile(
    r"for Claude(?P<reserve>'s reserve · the week resets| until) (?P<when>\S+ \d\d:\d\d)"
)
_FOR_YOU = "waiting for you: "


def _short(ticket: str) -> str:
    return "-".join(ticket.split("-")[:2])


def _nothing_ready(queue: Sequence[dict[str, Any]]) -> str:
    """The queue's own clog: the first milestone whose tickets wait, and on which ticket."""
    stuck = [c for c in queue if c["ticket"] and c["waits"]]
    if not stuck:
        return "nothing ready: " + ("no ticket can run yet" if queue else "the queue is empty")
    first = stuck[0]
    key = first["milestone"]
    many = sum(c["milestone"] == key for c in stuck) > 1
    whose = f"{short_key(key).upper()}'s" if key else "the"
    waits = "next tickets wait" if many else "next ticket waits"
    return f"nothing ready: {whose} {waits} on {_short(first['waits'][0])}"


def _wait(
    conn: sqlite3.Connection,
    project: str,
    machines: Sequence[dict[str, Any]],
    queue: Sequence[dict[str, Any]],
    field: dict[str, Any],
    now: datetime,
) -> dict[str, Any] | None:
    """What the runner waits for instead of working (f9-01), from its live run's activity and
    ``waiting_until``; None while it works. One clog at a time, at the machine the wait names:
    Claude's for its reset, a job parked for it or its reserve, the lead's desk for the owner
    (their pause, a sign-off, an open item), else the queue, with what its tickets wait on."""
    claude = next((m for m in machines if m["id"].startswith(queries.LEAD_PREFIX)), None)
    desk = next((m for m in machines if m["station"] == "lead"), None)

    def at(kind: str, machine: dict[str, Any] | None, words: str) -> dict[str, Any]:
        return {
            "kind": kind,
            "station": machine["station"] if machine else "queue",
            "machine": machine["id"] if machine else None,
            "words": words,
        }

    for run in live_runs(conn, project, now):
        activity = run.activity or ""
        if found := _CLAUDE_WAIT.fullmatch(activity):
            limited = _limit(conn, queries.LEAD_PREFIX, now) is not None
            until = run.waiting_until if limited else None  # a retry's own minute says little
            what = found["what"]
            parts = (
                "waiting for Claude's reset" if limited else "waiting for Claude",
                f"{_when(until).astimezone(now.tzinfo):%H:%M}" if until else None,
                _short(what) if what and " " not in what else what,
            )
            return at("claude", claude, " · ".join(p for p in parts if p))
        if activity == dispatch.PAUSED:
            return at("owner", desk, _FOR_YOU + "the factory is paused")
        if not activity.startswith(loop.IDLE):
            continue
        if found := _IDLE_CLAUDE.search(activity):
            reserve = "reserve" in found["reserve"]
            words = "reserve · the week resets" if reserve else "reset ·"
            return at("claude", claude, f"waiting for Claude's {words} {found['when']}")
        asked = activity.partition(_FOR_YOU)[2]
        if asked or "for a sign-off" in activity:
            ripe = [short_key(m["key"]).upper() for m in field["ripe"]]
            if ripe and "sign-off" in activity:
                asked = "sign off " + ", ".join(ripe[:3])
            return at("owner", desk, _FOR_YOU + (asked or "a sign-off"))
        return at("queue", None, _nothing_ready(queue))
    return None


def _clog(
    conn: sqlite3.Connection,
    project: str,
    machines: Sequence[dict[str, Any]],
    since: datetime,
    at: datetime,
) -> dict[str, Any]:
    """What clogged the line from ``since`` to ``at`` (f3-04), for the floor's developers."""
    names = {m["id"]: m["name"] for m in machines if m["station"] == "developers"}
    found = queries.clog(conn, project, since, at, machines=list(names))
    return {
        "limit": found.limit,
        "failed": found.failed,
        "failures": found.failures,
        "idle": [
            {"agent": i.agent, "name": names[i.agent], "minutes": i.minutes, "share": i.share}
            for i in found.idle
        ],
        "owner": found.owner,
        "live": found.live,
    }


# --- replay (f3-06) -------------------------------------------------------------------------


def _stages(field: dict[str, Any]) -> dict[str, str]:
    """Each milestone's stage on the field: ``rows``, ``ripe`` or ``stash``."""
    stages = {r["key"]: "rows" for r in field["rows"]}
    stages |= {m["key"]: "ripe" for m in field["ripe"]}
    return stages | {m["key"]: "stash" for m in field["stash"]}


def _idle(
    work: Sequence[Work], since: datetime, until: datetime
) -> list[tuple[datetime, datetime]]:
    """The stretches longer than ``IDLE`` with no job working, between ``since`` and ``until``."""
    found, cursor = [], since
    spans = sorted((w.started, w.until) for w in work if w.until is not None)
    for start, end in [*spans, (until, until)]:
        if end <= cursor:
            continue
        start = min(max(start, since), until)
        if start - cursor > IDLE:
            found.append((cursor, start))
        cursor = max(cursor, min(end, until))
        if cursor >= until:
            break
    return found


def replay(
    conn: sqlite3.Connection, project: str, since: datetime, until: datetime
) -> dict[str, Any]:
    """The line's document at ``since`` (``line``), then every event after it up to ``until``
    in time order, each ``{at, kind, ...}``:
    - ``trip``: a crate moves, ``{crate, belts, to}``;
    - ``check``: a crate's work passes or fails the checks, ``{crate, passed, gate}``;
    - ``machine``: a machine changes state or crate, ``{machine, state, ticket, reset}``;
    - ``limit``: an agent's limit starts or ends, ``{agent, state, resets}``;
    - ``card``: a milestone changes stage on the field, ``{card, stage}`` (None: off it);
    - ``idle``: nothing works for over 40 min, one event ``{until, minutes}`` (D10).
    Times are in ``since``'s zone."""
    zone = since.tzinfo

    def iso(moment: datetime) -> str:
        return moment.astimezone(zone).isoformat()

    def inside(moment: datetime) -> bool:
        return since < moment <= until

    every, work, jobs = trips(conn, project), _work(conn, project), _jobs(conn, project)
    tickets, config = _tickets(conn, project), _config(conn, project)
    gates = {
        r["id"]: _failed_gate(r["gates"])
        for r in conn.execute(
            "SELECT j.id, j.gates FROM jobs j JOIN runs r ON r.id = j.run_id"
            " JOIN projects p ON p.id = r.project_id WHERE p.name = ? AND j.gates IS NOT NULL",
            (project,),
        )
    }
    events: list[dict[str, Any]] = []
    for trip in every:
        if not inside(trip.at):
            continue
        at = iso(trip.at)
        events.append(
            {
                "at": at,
                "kind": "trip",
                "crate": trip.crate,
                "belts": list(trip.belts),
                "to": trip.to,
            }
        )
        if any(belt.endswith("→checks") for belt in trip.belts):
            passed = trip.to == "merged"
            gate = None if passed or trip.job is None else gates.get(trip.job)
            events.append(
                {"at": at, "kind": "check", "crate": trip.crate, "passed": passed, "gate": gate}
            )

    def floor(moment: datetime) -> dict[str, tuple[str, str | None, str | None]]:
        machines = _machines(conn, config, jobs, _working(work, moment, tickets), moment)
        return {
            m["id"]: (m["state"], (m["crate"] or {}).get("ticket"), m["reset"]) for m in machines
        }

    before = floor(since)
    on_floor = set(before)
    claude = any(agent.startswith(queries.LEAD_PREFIX) for agent in on_floor)
    limits = []
    for r in conn.execute(
        "SELECT agent, at, resets_at FROM usage_events WHERE kind = 'refusal'"
        " AND resets_at IS NOT NULL ORDER BY at"
    ):
        if r["agent"] in on_floor or (claude and r["agent"].startswith(queries.LEAD_PREFIX)):
            limits.append((r["agent"], _when(r["at"]), _when(r["resets_at"])))
    for agent, start, end in limits:
        for moment, state in ((start, "start"), (end, "end")):
            if inside(moment):
                events.append(
                    {"at": iso(moment), "kind": "limit", "agent": agent, "state": state,
                     "resets": iso(end)}
                )  # fmt: skip

    moments = {w.started for w in work} | {w.until for w in work if w.until is not None}
    moments |= {moment for _, start, end in limits for moment in (start, end)}
    for moment in sorted(m for m in moments if inside(m)):
        after = floor(moment.astimezone(zone))
        for machine, (state, ticket, reset) in after.items():
            if before.get(machine) != (state, ticket, reset):
                events.append(
                    {"at": iso(moment), "kind": "machine", "machine": machine, "state": state,
                     "ticket": ticket, "reset": reset}
                )  # fmt: skip
        before = after

    def stages(moment: datetime) -> dict[str, str]:
        return _stages(_field(conn, project, _states(conn, project, every, moment), moment))

    changes = {t.at for t in every if t.to == "merged"}
    for r in conn.execute(
        "SELECT m.started, m.ended FROM milestones m JOIN projects p ON p.id = m.project_id"
        " WHERE p.name = ?",
        (project,),
    ):
        changes |= {_when(r[key]) for key in ("started", "ended") if r[key]}
    was = stages(since)
    for moment in sorted(m for m in changes if inside(m)):
        then = stages(moment)
        for card in sorted(was.keys() | then.keys(), key=milestone_order):
            if was.get(card) != then.get(card):
                events.append(
                    {"at": iso(moment), "kind": "card", "card": card, "stage": then.get(card)}
                )
        was = then

    for start, end in _idle(work, since, until):
        minutes = int((end - start).total_seconds() // 60)
        events.append({"at": iso(start), "kind": "idle", "until": iso(end), "minutes": minutes})

    events.sort(key=lambda e: (_when(e["at"]), EVENTS.index(e["kind"])))
    return {
        "since": since.isoformat(),
        "until": until.isoformat(),
        "line": live_line(conn, project, until, at=since),
        "events": events,
    }


def overnight(now: datetime, seen: str | None) -> datetime:
    """Where "overnight" starts: when the owner last opened the line (``seen``, the cookie),
    else 20:00 yesterday."""
    evening = (now - timedelta(days=1)).replace(hour=20, minute=0, second=0, microsecond=0)
    try:
        last = _when(seen) if seen else None
    except ValueError:
        return evening
    return last.astimezone(now.tzinfo) if last is not None and last < now else evening


# --- the routes -----------------------------------------------------------------------------


def _context(conn: sqlite3.Connection, project: str, now: datetime) -> dict[str, Any]:
    # the server's local time: the counts start at its midnight
    return {"active": "/line", "line": live_line(conn, project, now.astimezone())}


@router.get("/line")
def line_redirect(request: Request) -> RedirectResponse:
    """The factory line is now the overview; /line redirects to / keeping query params."""

    query = request.url.query
    target = "/" + ("?" + query if query else "")
    return RedirectResponse(target, status_code=307)


def _moment(value: str, name: str) -> datetime:
    try:
        return _when(value)
    except ValueError:
        raise HTTPException(400, f"{name} is not an ISO time") from None


@router.get("/line/replay")
def line_replay(
    request: Request,
    conn: Db,
    project: Project,
    now: Now,
    since: str | None = None,
    until: str | None = None,
) -> dict[str, Any]:
    """``replay`` as JSON, read-only: from ``since`` (default overnight) to ``until`` (default
    now), at most ``REPLAY_LIMIT`` long."""
    end = _moment(until, "until") if until else now.astimezone()
    start = _moment(since, "since") if since else overnight(end, request.cookies.get(SEEN))
    if start >= end:
        raise HTTPException(400, "since must come before until")
    return replay(conn, project, max(start, end - REPLAY_LIMIT), end)


@router.get("/line/live", response_class=HTMLResponse)
def line_live(request: Request, conn: Db, project: Project, now: Now) -> Response:
    """The floor and its document; only the document, as JSON, when asked with ``Accept:
    application/json``: the page fetches it every 5 s and draws it in place (f3-17)."""
    context = _context(conn, project, now)
    if "application/json" in request.headers.get("accept", ""):
        # keys sorted, as the page's own block (``tojson``): an unchanged document reads the same
        return Response(json.dumps(context["line"], sort_keys=True), media_type="application/json")
    return render(request, conn, project, "_partials/line.html", context)
