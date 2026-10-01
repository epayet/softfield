"""The factory's metrics database (ADR 13 item 1, f1 D2).

Plain functions over a ``sqlite3.Connection``. Every write is an upsert on its table's natural
key, so the runner and the backfill can repeat one safely, and commits at once, so a crash
loses nothing. Times are ISO-8601 text passed in by the caller; lists and dicts are stored as
JSON. An optional argument left as ``None`` keeps the column's current value.
"""

import json
import sqlite3
from collections.abc import Mapping, Sequence
from pathlib import Path

_V1 = """
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    repo TEXT,
    description TEXT
);
CREATE TABLE milestones (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    key TEXT NOT NULL,
    title TEXT,
    status TEXT,
    started TEXT,
    ended TEXT,
    verdict TEXT,
    review_rounds INTEGER,
    review_score REAL,
    owner_score REAL,
    outcome TEXT,
    done_when TEXT,
    signoff TEXT,
    UNIQUE (project_id, key)
);
CREATE TABLE runs (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    run_dir TEXT NOT NULL,
    command TEXT,
    started TEXT,
    ended TEXT,
    heartbeat TEXT,
    verdict TEXT,
    UNIQUE (project_id, run_dir)
);
CREATE TABLE tickets (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    milestone_id INTEGER REFERENCES milestones(id),
    ticket TEXT NOT NULL,
    title TEXT,
    body TEXT,
    kind TEXT,
    depends_on TEXT,
    files TEXT,
    state TEXT,
    difficulty INTEGER,
    difficulty_corrected INTEGER,
    merged_by TEXT,
    "commit" TEXT,
    lines_changed INTEGER,
    UNIQUE (project_id, ticket)
);
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    ticket_id INTEGER REFERENCES tickets(id),
    milestone_id INTEGER REFERENCES milestones(id),
    role TEXT NOT NULL,
    agent TEXT NOT NULL,
    attempt INTEGER NOT NULL,
    started TEXT,
    ended TEXT,
    outcome TEXT NOT NULL DEFAULT 'running',
    tokens_in INTEGER,
    tokens_cached INTEGER,
    tokens_out INTEGER,
    requests INTEGER,
    cost_usd REAL,
    steps INTEGER,
    peak_context INTEGER,
    context_limit INTEGER,
    edit_streak INTEGER,
    refused_commands INTEGER,
    routing_reason TEXT,
    gates TEXT,
    note TEXT,
    session_id TEXT,
    log_path TEXT
);
-- A milestone-wide job has no ticket; SQL's NULLs never collide, so the key uses 0.
CREATE UNIQUE INDEX jobs_key ON jobs (run_id, ifnull(ticket_id, 0), role, attempt);
CREATE TABLE findings (
    id INTEGER PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),
    milestone_id INTEGER NOT NULL REFERENCES milestones(id),
    ticket_id INTEGER REFERENCES tickets(id),
    key TEXT NOT NULL,
    severity TEXT,
    route TEXT,
    file TEXT,
    line INTEGER,
    summary TEXT,
    detail TEXT,
    agent TEXT,
    verdict TEXT,
    resolved INTEGER,
    UNIQUE (milestone_id, key)
);
CREATE TABLE rating_changes (
    id INTEGER PRIMARY KEY,
    agent TEXT NOT NULL,
    skill TEXT NOT NULL,
    before REAL,
    after REAL,
    ticket_id INTEGER REFERENCES tickets(id),
    result TEXT,
    at TEXT NOT NULL,
    UNIQUE (agent, skill, at)
);
CREATE TABLE usage_events (
    id INTEGER PRIMARY KEY,
    agent TEXT NOT NULL,
    at TEXT NOT NULL,
    kind TEXT NOT NULL,
    value REAL,
    resets_at TEXT,
    UNIQUE (agent, at, kind)
);
CREATE TABLE owner_items (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    kind TEXT NOT NULL,
    subject TEXT NOT NULL,
    text TEXT,
    command TEXT,
    created TEXT,
    resolved TEXT,
    UNIQUE (project_id, kind, subject)
);
"""

# f1-44: Claude reads two windows at once, so a usage event is keyed by its window too
# (NULL for an event of no particular window, kept apart from the named ones by ifnull).
# SQLite can't drop a table's UNIQUE, so the table is rebuilt.
_V2 = """
ALTER TABLE usage_events RENAME TO usage_events_v1;
CREATE TABLE usage_events (
    id INTEGER PRIMARY KEY,
    agent TEXT NOT NULL,
    at TEXT NOT NULL,
    kind TEXT NOT NULL,
    "window" TEXT,
    value REAL,
    resets_at TEXT
);
INSERT INTO usage_events (id, agent, at, kind, value, resets_at)
    SELECT id, agent, at, kind, value, resets_at FROM usage_events_v1;
DROP TABLE usage_events_v1;
CREATE UNIQUE INDEX usage_events_key ON usage_events (agent, at, kind, ifnull("window", ''));
"""

# One step per schema version: step N takes the database from version N-1 to N. Append only.
MIGRATIONS: list[str] = [_V1, _V2]

type Value = str | int | float | Sequence[object] | Mapping[str, object] | None


def open_db(path: Path) -> sqlite3.Connection:
    """Open (creating it if needed) and migrate the database; a second open is a no-op."""
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, isolation_level=None, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    version: int = conn.execute("PRAGMA user_version").fetchone()[0]
    for number, step in enumerate(MIGRATIONS[version:], start=version + 1):
        conn.executescript(f"BEGIN;\n{step}\nPRAGMA user_version = {number};\nCOMMIT;")
    return conn


def _sql_value(value: Value) -> str | int | float | None:
    if value is None or isinstance(value, str | int | float):
        return value
    return json.dumps(value if isinstance(value, Mapping) else list(value))


def _given(**fields: Value) -> dict[str, Value]:
    return {name: value for name, value in fields.items() if value is not None}


def _upsert(
    conn: sqlite3.Connection,
    table: str,
    conflict: str,
    key: dict[str, Value],
    values: dict[str, Value],
) -> int:
    """Insert ``key`` + ``values``, or update ``values`` on the row ``conflict`` matches."""
    columns = [*key, *values]
    names = ", ".join(f'"{c}"' for c in columns)
    marks = ", ".join("?" for _ in columns)
    # With nothing to update, a no-op update still makes RETURNING give the row's id.
    sets = ", ".join(f'"{c}" = excluded."{c}"' for c in values or list(key)[:1])
    sql = (
        f"INSERT INTO {table} ({names}) VALUES ({marks}) "  # noqa: S608 - names are ours
        f"ON CONFLICT ({conflict}) DO UPDATE SET {sets} RETURNING id"
    )
    row = conn.execute(sql, [_sql_value(v) for v in [*key.values(), *values.values()]]).fetchone()
    return int(row[0])


def _update(
    conn: sqlite3.Connection, table: str, row_id: int, values: dict[str, Value], where: str = ""
) -> None:
    if not values:
        return
    sets = ", ".join(f'"{c}" = ?' for c in values)
    conn.execute(
        f"UPDATE {table} SET {sets} WHERE id = ?{where}",  # noqa: S608 - names are ours
        [*(_sql_value(v) for v in values.values()), row_id],
    )


def upsert_project(
    conn: sqlite3.Connection, name: str, *, repo: str | None = None, description: str | None = None
) -> int:
    return _upsert(
        conn, "projects", "name", {"name": name}, _given(repo=repo, description=description)
    )


def upsert_milestone(
    conn: sqlite3.Connection,
    project_id: int,
    key: str,
    *,
    title: str | None = None,
    status: str | None = None,
    started: str | None = None,
    ended: str | None = None,
    verdict: str | None = None,
    review_rounds: int | None = None,
    review_score: float | None = None,
    owner_score: float | None = None,
    outcome: str | None = None,
    done_when: str | None = None,
    signoff: Mapping[str, object] | None = None,
) -> int:
    values = _given(
        title=title,
        status=status,
        started=started,
        ended=ended,
        verdict=verdict,
        review_rounds=review_rounds,
        review_score=review_score,
        owner_score=owner_score,
        outcome=outcome,
        done_when=done_when,
        signoff=signoff,
    )
    return _upsert(
        conn, "milestones", "project_id, key", {"project_id": project_id, "key": key}, values
    )


def upsert_run(
    conn: sqlite3.Connection,
    project_id: int,
    run_dir: str,
    *,
    command: str | None = None,
    started: str | None = None,
    ended: str | None = None,
    heartbeat: str | None = None,
    verdict: str | None = None,
) -> int:
    values = _given(
        command=command, started=started, ended=ended, heartbeat=heartbeat, verdict=verdict
    )
    key: dict[str, Value] = {"project_id": project_id, "run_dir": run_dir}
    return _upsert(conn, "runs", "project_id, run_dir", key, values)


def update_run_heartbeat(conn: sqlite3.Connection, run_id: int, at: str) -> None:
    _update(conn, "runs", run_id, {"heartbeat": at})


def upsert_ticket(
    conn: sqlite3.Connection,
    project_id: int,
    ticket: str,
    *,
    milestone_id: int | None = None,
    title: str | None = None,
    body: str | None = None,
    kind: str | None = None,
    depends_on: Sequence[str] | None = None,
    files: Sequence[str] | None = None,
    state: str | None = None,
    difficulty: int | None = None,
    difficulty_corrected: int | None = None,
    merged_by: str | None = None,
    commit: str | None = None,
    lines_changed: int | None = None,
) -> int:
    values = _given(
        milestone_id=milestone_id,
        title=title,
        body=body,
        kind=kind,
        depends_on=depends_on,
        files=files,
        state=state,
        difficulty=difficulty,
        difficulty_corrected=difficulty_corrected,
        merged_by=merged_by,
        commit=commit,
        lines_changed=lines_changed,
    )
    key: dict[str, Value] = {"project_id": project_id, "ticket": ticket}
    return _upsert(conn, "tickets", "project_id, ticket", key, values)


def start_job(
    conn: sqlite3.Connection,
    run_id: int,
    *,
    ticket_id: int | None,
    milestone_id: int | None,
    role: str,
    agent: str,
    attempt: int,
    started: str,
    routing_reason: str | None = None,
    context_limit: int | None = None,
    session_id: str | None = None,
    log_path: str | None = None,
) -> int:
    """Write a job as ``running`` (f1 D3). Starting it again restarts the same row."""
    key: dict[str, Value] = {
        "run_id": run_id,
        "ticket_id": ticket_id,
        "role": role,
        "attempt": attempt,
    }
    values: dict[str, Value] = {
        "milestone_id": milestone_id,
        "agent": agent,
        "started": started,
        "ended": None,
        "outcome": "running",
    }
    values |= _given(
        routing_reason=routing_reason,
        context_limit=context_limit,
        session_id=session_id,
        log_path=log_path,
    )
    conflict = "run_id, ifnull(ticket_id, 0), role, attempt"
    return _upsert(conn, "jobs", conflict, key, values)


def finish_job(
    conn: sqlite3.Connection,
    job_id: int,
    *,
    ended: str,
    outcome: str,
    tokens_in: int | None = None,
    tokens_cached: int | None = None,
    tokens_out: int | None = None,
    requests: int | None = None,
    cost_usd: float | None = None,
    steps: int | None = None,
    peak_context: int | None = None,
    context_limit: int | None = None,
    edit_streak: int | None = None,
    refused_commands: int | None = None,
    gates: Sequence[Mapping[str, object]] | None = None,
    note: str | None = None,
    session_id: str | None = None,
    log_path: str | None = None,
) -> None:
    values = _given(
        ended=ended,
        outcome=outcome,
        tokens_in=tokens_in,
        tokens_cached=tokens_cached,
        tokens_out=tokens_out,
        requests=requests,
        cost_usd=cost_usd,
        steps=steps,
        peak_context=peak_context,
        context_limit=context_limit,
        edit_streak=edit_streak,
        refused_commands=refused_commands,
        gates=gates,
        note=note,
        session_id=session_id,
        log_path=log_path,
    )
    _update(conn, "jobs", job_id, values)


def close_abandoned(conn: sqlite3.Connection, project_id: int, run_id: int) -> int:
    """Mark ``interrupted`` every job an earlier run of the project left ``running`` (a Ctrl-C,
    a crash), ended at that run's last heartbeat, and end those runs. Only one runner works a
    repo at a time, so a new run means the old ones are gone. Returns how many jobs it closed."""
    stale = conn.execute(
        "SELECT j.id, r.id AS run, coalesce(r.heartbeat, j.started) AS at FROM jobs j"
        " JOIN runs r ON r.id = j.run_id"
        " WHERE r.project_id = ? AND r.id != ? AND j.outcome = 'running'",
        (project_id, run_id),
    ).fetchall()
    for job, run, at in stale:
        conn.execute("UPDATE jobs SET outcome = 'interrupted', ended = ? WHERE id = ?", (at, job))
        conn.execute(
            "UPDATE runs SET ended = coalesce(ended, ?), verdict = coalesce(verdict, ?)"
            " WHERE id = ?",
            (at, "interrupted", run),
        )
    conn.commit()
    return len(stale)


def update_running_job(
    conn: sqlite3.Connection,
    job_id: int,
    *,
    tokens_in: int | None = None,
    tokens_cached: int | None = None,
    tokens_out: int | None = None,
    requests: int | None = None,
    steps: int | None = None,
    peak_context: int | None = None,
    edit_streak: int | None = None,
) -> None:
    """The live fields of a job still running (f1 D3); a finished job is left alone."""
    values = _given(
        tokens_in=tokens_in,
        tokens_cached=tokens_cached,
        tokens_out=tokens_out,
        requests=requests,
        steps=steps,
        peak_context=peak_context,
        edit_streak=edit_streak,
    )
    _update(conn, "jobs", job_id, values, where=" AND outcome = 'running'")


def add_finding(
    conn: sqlite3.Connection,
    milestone_id: int,
    key: str,
    *,
    job_id: int | None = None,
    ticket_id: int | None = None,
    severity: str | None = None,
    route: str | None = None,
    file: str | None = None,
    line: int | None = None,
    summary: str | None = None,
    detail: str | None = None,
    agent: str | None = None,
    verdict: str | None = None,
    resolved: bool | None = None,
) -> int:
    values = _given(
        job_id=job_id,
        ticket_id=ticket_id,
        severity=severity,
        route=route,
        file=file,
        line=line,
        summary=summary,
        detail=detail,
        agent=agent,
        verdict=verdict,
        resolved=resolved,
    )
    natural: dict[str, Value] = {"milestone_id": milestone_id, "key": key}
    return _upsert(conn, "findings", "milestone_id, key", natural, values)


def add_rating_change(
    conn: sqlite3.Connection,
    agent: str,
    skill: str,
    before: float,
    after: float,
    *,
    at: str,
    ticket_id: int | None = None,
    result: str | None = None,
) -> int:
    key: dict[str, Value] = {"agent": agent, "skill": skill, "at": at}
    values: dict[str, Value] = {"before": before, "after": after}
    values |= _given(ticket_id=ticket_id, result=result)
    return _upsert(conn, "rating_changes", "agent, skill, at", key, values)


def add_usage_event(
    conn: sqlite3.Connection,
    agent: str,
    at: str,
    kind: str,
    *,
    window: str | None = None,
    value: float | None = None,
    resets_at: str | None = None,
) -> int:
    """A refusal, a reset or a reading (f1-44: a window's share used, 0–1) of ``window``."""
    key: dict[str, Value] = {"agent": agent, "at": at, "kind": kind, "window": window}
    conflict = "agent, at, kind, ifnull(\"window\", '')"
    return _upsert(conn, "usage_events", conflict, key, _given(value=value, resets_at=resets_at))


def upsert_owner_item(
    conn: sqlite3.Connection,
    project_id: int,
    kind: str,
    subject: str,
    *,
    text: str | None = None,
    command: str | None = None,
    created: str | None = None,
) -> int:
    """An item the owner must act on (f1 D8). An open one keeps its ``created``; one that was
    resolved opens again, created anew."""
    key: dict[str, Value] = {"project_id": project_id, "kind": kind, "subject": subject}
    values = _given(text=text, command=command, created=created)
    columns = [*key, *values]
    sets = [f'"{c}" = excluded."{c}"' for c in values if c != "created"]
    if "created" in values:
        sets.append("created = iif(resolved IS NULL, created, excluded.created)")
    sets.append("resolved = NULL")
    row = conn.execute(
        f"INSERT INTO owner_items ({', '.join(columns)}) "  # noqa: S608 - names are ours
        f"VALUES ({', '.join('?' for _ in columns)}) "
        f"ON CONFLICT (project_id, kind, subject) DO UPDATE SET {', '.join(sets)} RETURNING id",
        [_sql_value(v) for v in [*key.values(), *values.values()]],
    ).fetchone()
    return int(row[0])


def resolve_owner_item(conn: sqlite3.Connection, item_id: int, at: str) -> None:
    _update(conn, "owner_items", item_id, {"resolved": at})


def open_owner_items(conn: sqlite3.Connection, project_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM owner_items WHERE project_id = ? AND resolved IS NULL ORDER BY id",
        (project_id,),
    ).fetchall()
