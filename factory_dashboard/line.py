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
- **The field**, until f3-08 brings the board's cards: rows are milestones with ready or
  running tickets, ripe ones have every ticket merged and wait for the owner's sign-off, the
  stash holds signed-off ones, seeds are tickets set aside (``later``).
"""

import sqlite3
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from factory_dashboard import queries
from factory_dashboard.app import Db, Now, Project, render
from factory_dashboard.overview import running_jobs
from runner.config import Config, load_config
from runner.tasks import milestone_order

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
            trips.append(
                Trip(job.started, job.crate, _on_belts(f"{here}→{job.station}"), job.station)
            )
            here = job.station
        if job.ended is None:
            break
        there, belts = _after(job, jobs[n + 1] if n + 1 < len(jobs) else None)
        if there != here:
            trips.append(Trip(job.ended, job.crate, belts, there))
            here = there
    return trips


def _batch_trips(job: Job) -> list[Trip]:
    belts = _on_belts(f"merged→{job.station}")
    trips = [Trip(job.started, job.crate, belts, job.station)]
    if job.ended is not None:
        trips.append(Trip(job.ended, job.crate, (), None))
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


def _config(conn: sqlite3.Connection, project: str) -> Config | None:
    """The project's ``workflow/runner.toml``, or None when its repo can't be read."""
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
        found.append(
            {
                "id": agent,
                "station": station,
                "name": _name(agent),
                "where": _where(agent, local),
                "local": local,
                "rating": rating,
                "scale": _scale(rating),
                "state": state,
                "crate": working[agent]["crate"] if agent in working else None,
                "reset": reset.astimezone(now.tzinfo).strftime("%H:%M") if reset else None,
                "stand_in": agent in stand_ins,
                "off": sorted(r for r in lost if _station([r])),
            }
        )
    return sorted(found, key=lambda m: MACHINE_STATIONS.index(m["station"]))


def _field(conn: sqlite3.Connection, project: str) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT m.key, m.title, m.status, m.ended, t.state FROM milestones m"
        " JOIN projects p ON p.id = m.project_id LEFT JOIN tickets t ON t.milestone_id = m.id"
        " WHERE p.name = ?",
        (project,),
    ).fetchall()
    milestones: dict[str, dict[str, Any]] = {}
    for r in rows:
        m = milestones.setdefault(
            r["key"],
            {
                "key": r["key"],
                "title": r["title"],
                "status": r["status"],
                "ended": r["ended"],
                "states": [],
            },
        )
        if r["state"]:
            m["states"].append(r["state"])
    planted, ripe, stash = [], [], []
    for m in sorted(milestones.values(), key=lambda m: milestone_order(m["key"])):
        states = m["states"]
        if m["status"] == "done":
            stash.append(m)
        elif "ready" in states or "running" in states:
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
    seeds = conn.execute(
        "SELECT COUNT(*) FROM tickets t JOIN projects p ON p.id = t.project_id"
        " WHERE p.name = ? AND t.state = 'later'",
        (project,),
    ).fetchone()[0]
    return {
        "seeds": seeds,
        "planting": 0,
        "rows": planted,
        "ripe": [{"key": m["key"], "title": m["title"]} for m in ripe],
        "stash": [{"key": m["key"], "title": m["title"], "ended": m["ended"]} for m in stash],
    }


def _kind(kind: str | None) -> str:
    return "lead" if kind == "lead" else "developer"


def live_line(conn: sqlite3.Connection, project: str, now: datetime) -> dict[str, Any]:
    """D11's document at ``now``: stations, machines with their state and crate, belts with
    today's count (since ``now``'s midnight) and ``carrying``, Now and the queue in run order."""
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tickets = {
        r["ticket"]: r
        for r in conn.execute(
            "SELECT t.ticket, t.title, t.kind, m.key AS milestone FROM tickets t"
            " JOIN projects p ON p.id = t.project_id"
            " LEFT JOIN milestones m ON m.id = t.milestone_id WHERE p.name = ?",
            (project,),
        )
    }
    jobs = _jobs(conn, project)
    found = [t for t in trips(conn, project) if t.at <= now]
    today = [t for t in found if t.at >= midnight]

    # What works now: the live runs' jobs, and the belt that brought each crate.
    working: dict[str, dict[str, Any]] = {}
    carrying: set[str] = set()
    now_working = []
    for run in running_jobs(conn, project, now):
        if not run.live:
            continue
        crate = run.ticket or f"{run.role}-{run.job}"
        came = [t for t in found if t.crate == crate]
        if came:
            carrying.update(came[-1].belts)
        ticket = tickets.get(run.ticket) if run.ticket else None
        minutes = int(run.elapsed.total_seconds() // 60)
        on = {
            "ticket": run.ticket,
            "title": ticket["title"] if ticket else None,
            "kind": _kind(ticket["kind"]) if ticket else "batch",
            "role": run.role,
            "attempt": run.attempt,
            "minutes": minutes,
        }
        working.setdefault(run.agent, {"role": run.role, "crate": on})
        now_working.append(
            {**on, "agent": run.agent, "tokens_in": run.tokens_in, "steps": run.steps}
        )

    field = _field(conn, project)
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
    queue = [
        {
            "ticket": u.ticket,
            "title": u.title,
            "kind": _kind(u.kind),
            "milestone": u.milestone,
            "number": n,
            "waits": list(u.waits),
        }
        for n, u in enumerate(queries.run_order(conn, project), start=1)
    ]

    counts: dict[str, int | None] = {belt: sum(belt in t.belts for t in today) for belt in BELTS}
    counts.update(dict.fromkeys(FIELD_BELTS))
    merges: dict[str, datetime] = {}  # each milestone's last merge
    for t in found:
        if t.to == "merged" and t.crate in tickets:
            merges[tickets[t.crate]["milestone"]] = t.at
    counts["merged→ripe"] = sum(merges.get(m["key"], midnight) > midnight for m in field["ripe"])
    counts["ripe→stash"] = sum(
        bool(m["ended"]) and midnight <= _when(m["ended"]) <= now for m in field["stash"]
    )

    config = _config(conn, project)
    machines = _machines(conn, config, jobs, working, now)
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
    return {
        "at": now.isoformat(),
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
        "clog": None,  # f3-04: what clogged the line today
    }


# --- the routes -----------------------------------------------------------------------------


def _context(conn: sqlite3.Connection, project: str, now: datetime) -> dict[str, Any]:
    # the server's local time: the counts start at its midnight
    return {"active": "/line", "line": live_line(conn, project, now.astimezone())}


@router.get("/line", response_class=HTMLResponse)
def line_page(request: Request, conn: Db, project: Project, now: Now) -> HTMLResponse:
    return render(request, conn, project, "line.html", _context(conn, project, now))


@router.get("/line/live", response_class=HTMLResponse)
def line_live(request: Request, conn: Db, project: Project, now: Now) -> HTMLResponse:
    """The floor and its document, for htmx to swap in every 5 s."""
    return render(request, conn, project, "_partials/line.html", _context(conn, project, now))
