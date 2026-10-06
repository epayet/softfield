"""The factory's metrics database (f1 D2): schema, migrations and idempotent writes."""

import json
import sqlite3
from datetime import datetime, timedelta

import pytest

from runner import metrics

TABLES = {
    "projects",
    "milestones",
    "runs",
    "tickets",
    "jobs",
    "findings",
    "rating_changes",
    "usage_events",
    "owner_items",
    "owner_requests",
    "work_queue",
    "planner_threads",
    "planner_messages",
}
T0 = "2026-09-30T15:23:11+02:00"
T1 = "2026-09-30T15:40:00+02:00"


@pytest.fixture
def db(tmp_path):
    conn = metrics.open_db(tmp_path / "factory-metrics.sqlite")
    yield conn
    conn.close()


@pytest.fixture
def ids(db):
    project = metrics.upsert_project(db, "coucou", repo="/src/coucou")
    milestone = metrics.upsert_milestone(db, project, "f1", title="The factory measures itself")
    run = metrics.upsert_run(db, project, "20260930-152311", command="milestone f1", started=T0)
    ticket = metrics.upsert_ticket(db, project, "f1-01-metrics-db", milestone_id=milestone)
    return {"project": project, "milestone": milestone, "run": run, "ticket": ticket}


def _tables(conn):
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return {row[0] for row in rows}


def _count(conn, table):
    return conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]  # noqa: S608


def _job(db, ids, **overrides):
    fields = {
        "ticket_id": ids["ticket"],
        "milestone_id": ids["milestone"],
        "role": "developer",
        "agent": "local-qwen3.6-35b-a3b",
        "attempt": 1,
        "started": T0,
    }
    return metrics.start_job(db, ids["run"], **(fields | overrides))


def test_a_fresh_path_gets_every_table_and_the_latest_version(tmp_path):
    path = tmp_path / "nested" / "folder" / "factory-metrics.sqlite"
    conn = metrics.open_db(path)
    assert path.is_file()
    assert _tables(conn) >= TABLES
    assert conn.execute("PRAGMA user_version").fetchone()[0] == 9 == len(metrics.MIGRATIONS)
    assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    conn.close()


def test_opening_again_changes_nothing(tmp_path):
    path = tmp_path / "factory-metrics.sqlite"
    conn = metrics.open_db(path)
    metrics.upsert_project(conn, "coucou")
    schema = conn.execute("SELECT sql FROM sqlite_master ORDER BY name").fetchall()
    conn.close()

    again = metrics.open_db(path)
    assert again.execute("SELECT sql FROM sqlite_master ORDER BY name").fetchall() == schema
    assert again.execute("PRAGMA user_version").fetchone()[0] == len(metrics.MIGRATIONS)
    assert _count(again, "projects") == 1
    again.close()


def test_a_version_1_database_keeps_its_usage_events_and_gains_a_window(tmp_path):
    """f1-44: the database already holds f1's refusals when the window column arrives."""
    path = tmp_path / "factory-metrics.sqlite"
    old = sqlite3.connect(path, isolation_level=None)
    old.executescript(f"BEGIN;\n{metrics.MIGRATIONS[0]}\nPRAGMA user_version = 1;\nCOMMIT;")
    old.execute(
        "INSERT INTO usage_events (agent, at, kind, resets_at) VALUES (?, ?, ?, ?)",
        ("claude-opus", T0, "refusal", T1),
    )
    old.close()

    conn = metrics.open_db(path)
    row = conn.execute("SELECT agent, at, kind, resets_at, window FROM usage_events").fetchone()
    assert tuple(row) == ("claude-opus", T0, "refusal", T1, None)
    metrics.add_usage_event(conn, "claude-opus", T0, "refusal", resets_at=T1)
    assert _count(conn, "usage_events") == 1
    conn.close()


def test_a_version_2_database_keeps_its_runs_and_gains_their_activity(tmp_path):
    """f1-51: the runs already written stay; the new columns start empty."""
    path = tmp_path / "factory-metrics.sqlite"
    old = sqlite3.connect(path, isolation_level=None)
    steps = "\n".join(metrics.MIGRATIONS[:2])
    old.executescript(f"BEGIN;\n{steps}\nPRAGMA user_version = 2;\nCOMMIT;")
    old.execute("INSERT INTO projects (name) VALUES ('coucou')")
    old.execute(
        "INSERT INTO runs (project_id, run_dir, started, heartbeat) VALUES (1, 'r1', ?, ?)",
        (T0, T1),
    )
    old.close()

    conn = metrics.open_db(path)
    assert conn.execute("PRAGMA user_version").fetchone()[0] == len(metrics.MIGRATIONS)
    row = conn.execute(
        "SELECT run_dir, started, heartbeat, activity, waiting_until, reserve FROM runs"
    ).fetchone()
    assert tuple(row) == ("r1", T0, T1, None, None, None)
    conn.close()


def test_a_version_3_database_keeps_its_jobs_and_gains_an_empty_model(tmp_path):
    """f2-04: the jobs already written stay; their model is empty until backfill reads it."""
    path = tmp_path / "factory-metrics.sqlite"
    old = sqlite3.connect(path, isolation_level=None)
    steps = "\n".join(metrics.MIGRATIONS[:3])
    old.executescript(f"BEGIN;\n{steps}\nPRAGMA user_version = 3;\nCOMMIT;")
    old.execute("INSERT INTO projects (name) VALUES ('coucou')")
    old.execute("INSERT INTO runs (project_id, run_dir) VALUES (1, 'r1')")
    old.execute(
        "INSERT INTO jobs (run_id, role, agent, attempt, log_path)"
        " VALUES (1, 'review', 'claude-opus', 1, 'var/runs/r1/claude-review-f1.log')"
    )
    old.close()

    conn = metrics.open_db(path)
    assert conn.execute("PRAGMA user_version").fetchone()[0] == len(metrics.MIGRATIONS)
    row = conn.execute("SELECT agent, log_path, model FROM jobs").fetchone()
    assert tuple(row) == ("claude-opus", "var/runs/r1/claude-review-f1.log", None)
    conn.close()


def test_a_version_4_database_keeps_its_items_and_gains_an_empty_request_table(tmp_path):
    """f5 D1: the owner's requests from the dashboard get a table of their own."""
    path = tmp_path / "factory-metrics.sqlite"
    old = sqlite3.connect(path, isolation_level=None)
    steps = "\n".join(metrics.MIGRATIONS[:4])
    old.executescript(f"BEGIN;\n{steps}\nPRAGMA user_version = 4;\nCOMMIT;")
    old.execute("INSERT INTO projects (name) VALUES ('coucou')")
    old.execute("INSERT INTO owner_items (project_id, kind, subject) VALUES (1, 'signoff', 'f4')")
    old.close()

    conn = metrics.open_db(path)
    assert conn.execute("PRAGMA user_version").fetchone()[0] == len(metrics.MIGRATIONS)
    assert _count(conn, "owner_items") == 1 and _count(conn, "owner_requests") == 0
    conn.close()


def test_a_version_5_database_keeps_its_milestones_and_gains_empty_cards(tmp_path):
    """f5 D4: a milestone's card (state, priority, area) starts empty until the runner syncs."""
    path = tmp_path / "factory-metrics.sqlite"
    old = sqlite3.connect(path, isolation_level=None)
    steps = "\n".join(metrics.MIGRATIONS[:5])
    old.executescript(f"BEGIN;\n{steps}\nPRAGMA user_version = 5;\nCOMMIT;")
    old.execute("INSERT INTO projects (name) VALUES ('coucou')")
    old.execute("INSERT INTO milestones (project_id, key, title) VALUES (1, 'f4', 'Always on')")
    old.close()

    conn = metrics.open_db(path)
    assert conn.execute("PRAGMA user_version").fetchone()[0] == len(metrics.MIGRATIONS)
    row = conn.execute("SELECT key, title, state, priority, area FROM milestones").fetchone()
    assert tuple(row) == ("f4", "Always on", None, None, None)
    conn.close()


def test_a_version_6_database_keeps_its_tickets_and_gains_an_empty_area(tmp_path):
    """f5 D5: a bug ticket's area (factory or product); earlier tickets have none."""
    path = tmp_path / "factory-metrics.sqlite"
    old = sqlite3.connect(path, isolation_level=None)
    steps = "\n".join(metrics.MIGRATIONS[:6])
    old.executescript(f"BEGIN;\n{steps}\nPRAGMA user_version = 6;\nCOMMIT;")
    old.execute("INSERT INTO projects (name) VALUES ('coucou')")
    old.execute("INSERT INTO tickets (project_id, ticket) VALUES (1, 'f4-01-a')")
    old.close()

    conn = metrics.open_db(path)
    assert conn.execute("PRAGMA user_version").fetchone()[0] == len(metrics.MIGRATIONS)
    row = conn.execute("SELECT ticket, area FROM tickets").fetchone()
    assert tuple(row) == ("f4-01-a", None)
    project = conn.execute("SELECT id FROM projects").fetchone()[0]
    metrics.upsert_ticket(conn, project, "bug-01-x", area="product")
    metrics.upsert_ticket(conn, project, "bug-01-x", state="done")
    area = conn.execute("SELECT area FROM tickets WHERE ticket = 'bug-01-x'").fetchone()[0]
    assert area == "product"
    conn.close()


@pytest.mark.parametrize("version", [5, 7])
def test_an_older_database_keeps_its_requests_and_gains_an_empty_work_queue(tmp_path, version):
    """f8 D1: the queue arrives empty beside what the database already holds."""
    path = tmp_path / "factory-metrics.sqlite"
    old = sqlite3.connect(path, isolation_level=None)
    steps = "\n".join(metrics.MIGRATIONS[:version])
    old.executescript(f"BEGIN;\n{steps}\nPRAGMA user_version = {version};\nCOMMIT;")
    old.execute("INSERT INTO projects (name) VALUES ('coucou')")
    old.execute(
        "INSERT INTO owner_requests (project_id, kind, subject, created)"
        " VALUES (1, 'signoff', 'f7', ?)",
        (T0,),
    )
    old.close()

    conn = metrics.open_db(path)
    assert conn.execute("PRAGMA user_version").fetchone()[0] == len(metrics.MIGRATIONS)
    assert _count(conn, "owner_requests") == 1 and _count(conn, "work_queue") == 0
    columns = [row[1] for row in conn.execute("PRAGMA table_info(work_queue)")]
    assert columns == [
        "id",
        "project_id",
        "kind",
        "subject",
        "reason",
        "created",
        "not_before",
        "started_job",
        "done",
    ]
    conn.close()


def test_a_queued_job_is_open_oldest_first_until_finished_once(db, ids):
    """f8 D1: triggers queue rows; the project's open ones come back in the order queued."""
    project = ids["project"]
    other = metrics.upsert_project(db, "elsewhere")
    later = "2026-09-30T18:00:00+02:00"
    review = metrics.queue_job(db, project, "review", "f1", "4 merges since the last", T1)
    checkpoint = metrics.queue_job(
        db, project, "checkpoint", "f1-02-a", "2 developer merges", T0, not_before=later
    )
    metrics.queue_job(db, other, "review", "x1", "elsewhere's review", T0)
    assert review != checkpoint

    rows = metrics.open_jobs(db, project)
    assert [
        (r["id"], r["kind"], r["subject"], r["reason"], r["created"], r["not_before"]) for r in rows
    ] == [
        (checkpoint, "checkpoint", "f1-02-a", "2 developer merges", T0, later),
        (review, "review", "f1", "4 merges since the last", T1, None),
    ]
    assert all(r["done"] is None and r["started_job"] is None for r in rows)

    assert metrics.finish_queued(db, checkpoint, T1)
    assert [r["id"] for r in metrics.open_jobs(db, project)] == [review]
    # Finished once: a second finish changes nothing and says so.
    assert not metrics.finish_queued(db, checkpoint, later)
    done = db.execute("SELECT done FROM work_queue WHERE id = ?", (checkpoint,)).fetchone()[0]
    assert done == T1


def test_jobs_queued_at_the_same_time_stay_in_the_order_queued(db, ids):
    project = ids["project"]
    first = metrics.queue_job(db, project, "escalation", "f1-03-b", "blocked twice", T0)
    second = metrics.queue_job(db, project, "direction", "f1-04-c", "gates failed", T0)
    assert [r["id"] for r in metrics.open_jobs(db, project)] == [first, second]


def test_a_milestone_keeps_its_card(db, ids):
    """f5 D4: state, priority and area are upserted like the rest; None keeps them."""
    project = ids["project"]
    metrics.upsert_milestone(db, project, "f1", state="building", priority=2, area="factory")
    metrics.upsert_milestone(db, project, "f1", status="review")
    row = db.execute("SELECT state, priority, area FROM milestones WHERE key = 'f1'").fetchone()
    assert tuple(row) == ("building", 2, "factory")


def test_a_request_is_open_until_finished_once_with_its_result(db, ids):
    """f5 D1: the dashboard adds a row; the runner finishes it with what came of it."""
    project = ids["project"]
    other = metrics.upsert_project(db, "elsewhere")
    first = metrics.add_request(db, project, "signoff", "f4-always-on", None, T0)
    second = metrics.add_request(db, project, "five_hour", None, "yes", T1)
    metrics.add_request(db, other, "queue", "x1-01-thing", None, T0)
    assert first != second
    rows = metrics.open_requests(db, project)
    assert [(r["id"], r["kind"], r["subject"], r["value"]) for r in rows] == [
        (first, "signoff", "f4-always-on", None),
        (second, "five_hour", None, "yes"),
    ]
    assert [r["created"] for r in rows] == [T0, T1]
    assert all(r["done"] is None and r["result"] is None for r in rows)

    assert metrics.finish_request(db, first, T1, "signed off f4-always-on")
    assert [r["id"] for r in metrics.open_requests(db, project)] == [second]
    # Finished once: a second finish changes nothing and says so.
    assert not metrics.finish_request(db, first, "2026-10-01T00:00:00+02:00", "again")
    row = db.execute("SELECT done, result FROM owner_requests WHERE id = ?", (first,)).fetchone()
    assert tuple(row) == (T1, "signed off f4-always-on")


def test_a_project_is_found_by_name_without_being_made(db, ids):
    assert metrics.find_project(db, "coucou") == ids["project"]
    assert metrics.find_project(db, "nowhere") is None
    assert _count(db, "projects") == 1


def test_a_job_records_the_model_it_ran_on(db, ids):
    """f2-04: started on the agent's model, finished on the one its harness reported."""
    job = _job(db, ids, agent="claude-sonnet", model="sonnet")
    assert db.execute("SELECT model FROM jobs").fetchone()[0] == "sonnet"
    metrics.finish_job(db, job, ended=T1, outcome="passed", model="claude-sonnet-5-5")
    assert db.execute("SELECT model FROM jobs").fetchone()[0] == "claude-sonnet-5-5"
    metrics.finish_job(db, job, ended=T1, outcome="passed")  # None keeps it
    assert db.execute("SELECT model FROM jobs").fetchone()[0] == "claude-sonnet-5-5"
    metrics.set_job_model(db, job, "claude-sonnet-5-6")
    assert db.execute("SELECT model FROM jobs").fetchone()[0] == "claude-sonnet-5-6"


def test_a_run_says_what_it_does_and_until_when_it_waits(db, ids):
    metrics.update_run_activity(db, ids["run"], "waiting for Claude", waiting_until=T1)
    row = db.execute("SELECT activity, waiting_until FROM runs").fetchone()
    assert tuple(row) == ("waiting for Claude", T1)

    metrics.update_run_activity(db, ids["run"], "gates · f1-21")
    row = db.execute("SELECT activity, waiting_until FROM runs").fetchone()
    assert tuple(row) == ("gates · f1-21", None)  # the wait ended with it

    metrics.update_run_activity(db, ids["run"], None)
    row = db.execute("SELECT activity, waiting_until FROM runs").fetchone()
    assert tuple(row) == (None, None)


def test_a_run_on_the_reserve_says_so(db, ids):
    assert db.execute("SELECT reserve FROM runs").fetchone()[0] is None
    metrics.set_run_reserve(db, ids["run"])
    assert db.execute("SELECT reserve FROM runs").fetchone()[0] == 1


def test_an_ended_run_leaves_nothing_looking_alive(db, ids):
    """f2-03: after a Ctrl-C, run 20261002-055804 kept ended NULL and reserve 1."""
    metrics.update_run_activity(db, ids["run"], "waiting for Claude · f1-21 until 15:40", T1)
    metrics.set_run_reserve(db, ids["run"])
    job = _job(db, ids)
    metrics.end_run(db, ids["run"], T1, "interrupted")
    row = db.execute(
        "SELECT ended, heartbeat, verdict, activity, waiting_until, reserve FROM runs"
    ).fetchone()
    assert tuple(row) == (T1, T1, "interrupted", None, None, 0)
    outcome, ended = db.execute("SELECT outcome, ended FROM jobs WHERE id = ?", (job,)).fetchone()
    assert (outcome, ended) == ("interrupted", T1)


def test_ready_tickets_no_longer_in_tasks_are_removed(db, ids):
    project = ids["project"]
    metrics.upsert_ticket(db, project, "f1-01-metrics-db", state="ready")
    metrics.upsert_ticket(db, project, "f1-30-allowance-forecast", state="ready")
    metrics.upsert_ticket(db, project, "m4-06-me-wiring", state="done")
    other = metrics.upsert_project(db, "elsewhere")
    metrics.upsert_ticket(db, other, "x1-01-other", state="ready")

    assert metrics.remove_missing_tickets(db, project, {"f1-01-metrics-db"}) == 1
    states = dict(db.execute("SELECT ticket, state FROM tickets").fetchall())
    assert states == {
        "f1-01-metrics-db": "ready",
        "f1-30-allowance-forecast": "removed",
        "m4-06-me-wiring": "done",  # only the queue's rows: history stays
        "x1-01-other": "ready",  # another project's queue isn't ours
    }


def test_foreign_keys_are_enforced(db):
    with pytest.raises(sqlite3.IntegrityError):
        metrics.upsert_run(db, 999, "20260930-152311", command="run", started=T0)


def test_the_same_project_and_milestone_twice_is_one_row(db):
    first = metrics.upsert_project(db, "coucou", repo="/old")
    assert metrics.upsert_project(db, "coucou", repo="/new") == first
    assert [tuple(r) for r in db.execute("SELECT repo FROM projects")] == [("/new",)]

    m = metrics.upsert_milestone(db, first, "m4", title="Old", status="in progress")
    signoff = {"changed": "a", "lessons": ["b"]}
    again = metrics.upsert_milestone(db, first, "m4", status="done", signoff=signoff)
    assert again == m
    row = db.execute("SELECT title, status, signoff FROM milestones").fetchone()
    assert (row["title"], row["status"]) == ("Old", "done")  # an omitted field is kept
    assert json.loads(row["signoff"]) == signoff


def test_the_same_run_twice_is_one_row_with_the_later_values(db, ids):
    again = metrics.upsert_run(
        db, ids["project"], "20260930-152311", command="milestone f1", ended=T1, verdict="ok"
    )
    assert again == ids["run"]
    row = db.execute("SELECT started, ended, verdict FROM runs").fetchone()
    assert tuple(row) == (T0, T1, "ok")

    metrics.update_run_heartbeat(db, ids["run"], T1)
    assert db.execute("SELECT heartbeat FROM runs").fetchone()[0] == T1


def test_the_same_ticket_twice_is_one_row_with_the_later_values(db, ids):
    again = metrics.upsert_ticket(
        db,
        ids["project"],
        "f1-01-metrics-db",
        title="The metrics database",
        state="done",
        files=["runner/metrics.py"],
        depends_on=[],
    )
    assert again == ids["ticket"]
    assert _count(db, "tickets") == 1
    row = db.execute("SELECT milestone_id, title, state, files, depends_on FROM tickets").fetchone()
    assert (row["milestone_id"], row["title"], row["state"]) == (
        ids["milestone"],
        "The metrics database",
        "done",
    )
    assert json.loads(row["files"]) == ["runner/metrics.py"]
    assert json.loads(row["depends_on"]) == []


def test_a_ticket_keeps_difficulty_and_its_correction_apart(db, ids):
    metrics.upsert_ticket(db, ids["project"], "f1-01-metrics-db", difficulty=6)
    metrics.upsert_ticket(db, ids["project"], "f1-01-metrics-db", difficulty_corrected=8)
    row = db.execute("SELECT difficulty, difficulty_corrected FROM tickets").fetchone()
    assert tuple(row) == (6, 8)


def test_starting_the_same_job_twice_is_one_row_with_the_later_values(db, ids):
    job = _job(db, ids, agent="first")
    assert _job(db, ids, agent="second", started=T1) == job
    row = db.execute("SELECT agent, started, outcome FROM jobs").fetchone()
    assert tuple(row) == ("second", T1, "running")

    other_attempt = _job(db, ids, attempt=2)
    other_role = _job(db, ids, role="direction")
    assert len({job, other_attempt, other_role}) == 3


def test_a_milestone_wide_job_twice_is_one_row(db, ids):
    """No ticket: SQL's NULLs are all distinct, so the key must still match."""
    job = _job(db, ids, ticket_id=None, role="checkpoint", agent="claude-sonnet")
    assert _job(db, ids, ticket_id=None, role="checkpoint", agent="claude-sonnet") == job
    assert _count(db, "jobs") == 1


def test_finish_job_sets_the_end_the_outcome_and_the_rest(db, ids):
    job = _job(db, ids)
    gates = [{"name": "tests", "ok": True, "seconds": 12.5, "log": "var/runs/x/tests.log"}]
    metrics.finish_job(
        db,
        job,
        ended=T1,
        outcome="passed",
        tokens_in=1000,
        tokens_cached=800,
        tokens_out=200,
        requests=3,
        cost_usd=0.25,
        steps=42,
        peak_context=50_000,
        context_limit=180_000,
        edit_streak=4,
        refused_commands=1,
        gates=gates,
        note="ran the tests early",
        session_id="abc",
        log_path="var/runs/x/opencode-1.log",
    )
    row = db.execute("SELECT * FROM jobs WHERE id = ?", (job,)).fetchone()
    assert (row["ended"], row["outcome"], row["started"]) == (T1, "passed", T0)
    assert (row["tokens_in"], row["tokens_cached"], row["tokens_out"]) == (1000, 800, 200)
    assert (row["requests"], row["cost_usd"], row["steps"]) == (3, 0.25, 42)
    assert (row["peak_context"], row["context_limit"], row["edit_streak"]) == (50_000, 180_000, 4)
    assert (row["refused_commands"], row["note"], row["session_id"]) == (
        1,
        "ran the tests early",
        "abc",
    )
    assert row["log_path"] == "var/runs/x/opencode-1.log"
    assert json.loads(row["gates"]) == gates


def test_update_running_job_changes_only_the_live_fields(db, ids):
    job = _job(db, ids, routing_reason="first attempt")
    before = dict(db.execute("SELECT * FROM jobs WHERE id = ?", (job,)).fetchone())
    metrics.update_running_job(db, job, tokens_in=500, tokens_out=50, steps=7)
    after = dict(db.execute("SELECT * FROM jobs WHERE id = ?", (job,)).fetchone())
    changed = {key for key in after if after[key] != before[key]}
    assert changed == {"tokens_in", "tokens_out", "steps"}
    assert after["outcome"] == "running"


def test_update_running_job_leaves_a_finished_job_alone(db, ids):
    job = _job(db, ids)
    metrics.finish_job(db, job, ended=T1, outcome="failed", tokens_in=900)
    metrics.update_running_job(db, job, tokens_in=500)
    assert tuple(db.execute("SELECT tokens_in, outcome FROM jobs").fetchone()) == (900, "failed")


def test_the_same_finding_twice_is_one_row_with_the_later_values(db, ids):
    job = _job(db, ids, ticket_id=None, role="review", agent="claude-opus")
    first = metrics.add_finding(
        db,
        ids["milestone"],
        "f1-F1",
        job_id=job,
        ticket_id=ids["ticket"],
        severity="should-fix",
        file="runner/metrics.py",
        line=12,
        summary="Old",
    )
    again = metrics.add_finding(db, ids["milestone"], "f1-F1", summary="New", verdict="confirmed")
    assert again == first
    row = db.execute("SELECT severity, line, summary, verdict FROM findings").fetchone()
    assert tuple(row) == ("should-fix", 12, "New", "confirmed")


def test_ratings_usage_and_owner_items_are_idempotent(db, ids):
    for _ in range(2):
        metrics.add_rating_change(
            db, "local-qwen3.6-35b-a3b", "coding", 1500, 1516, at=T1, ticket_id=ids["ticket"]
        )
        metrics.add_usage_event(db, "claude-opus", T0, "refusal", resets_at=T1)
        item = metrics.upsert_owner_item(
            db, ids["project"], "adr", "docs/adr/15-x.md", text="Accept?", created=T0
        )
    assert [_count(db, t) for t in ("rating_changes", "usage_events", "owner_items")] == [1, 1, 1]

    metrics.resolve_owner_item(db, item, T1)
    assert db.execute("SELECT resolved FROM owner_items").fetchone()[0] == T1


def test_two_windows_read_at_once_are_two_rows_and_reading_again_changes_nothing(db):
    """f1-44: one stream reads Claude's 5-hour and weekly windows at the same moment."""
    for _ in range(2):
        for window, value in (("five_hour", 0.07), ("seven_day", 0.79)):
            metrics.add_usage_event(
                db, "claude-opus", T0, "reading", window=window, value=value, resets_at=T1
            )
    rows = db.execute("SELECT window, value FROM usage_events ORDER BY id").fetchall()
    assert [tuple(r) for r in rows] == [("five_hour", 0.07), ("seven_day", 0.79)]


def test_an_open_owner_item_keeps_its_created_and_a_resolved_one_reopens(db, ids):
    item = metrics.upsert_owner_item(db, ids["project"], "blocked", "f1-02-x", created=T0)
    metrics.upsert_owner_item(db, ids["project"], "blocked", "f1-02-x", text="Why", created=T1)
    assert [dict(r) for r in metrics.open_owner_items(db, ids["project"])] == [
        {
            "id": item,
            "project_id": ids["project"],
            "kind": "blocked",
            "subject": "f1-02-x",
            "text": "Why",
            "command": None,
            "created": T0,
            "resolved": None,
        }
    ]
    metrics.resolve_owner_item(db, item, T1)
    assert metrics.open_owner_items(db, ids["project"]) == []
    metrics.upsert_owner_item(db, ids["project"], "blocked", "f1-02-x", created=T1)
    [row] = metrics.open_owner_items(db, ids["project"])
    assert (row["id"], row["created"], row["resolved"]) == (item, T1, None)


def test_writes_are_committed_at_once(tmp_path):
    """A crash loses nothing (ADR 13 item 1): another connection sees each write."""
    path = tmp_path / "factory-metrics.sqlite"
    writer = metrics.open_db(path)
    metrics.upsert_project(writer, "coucou")
    reader = sqlite3.connect(path)
    assert reader.execute("SELECT name FROM projects").fetchall() == [("coucou",)]
    reader.close()
    writer.close()


def test_a_new_run_closes_what_a_stopped_run_left_running(db, ids):
    stale = _job(db, ids)
    metrics.update_run_heartbeat(db, ids["run"], T1)
    run = metrics.upsert_run(db, ids["project"], "20260930-170000", started=T1, heartbeat=T1)
    current = metrics.start_job(
        db,
        run,
        ticket_id=ids["ticket"],
        milestone_id=None,
        role="lead",
        agent="claude",
        attempt=1,
        started=T1,
    )
    assert metrics.close_abandoned(db, ids["project"], run) == 1
    jobs = db.execute("SELECT id, outcome, ended FROM jobs ORDER BY id").fetchall()
    assert [tuple(j) for j in jobs] == [(stale, "interrupted", T1), (current, "running", None)]
    old = db.execute("SELECT ended, verdict FROM runs WHERE id = ?", (ids["run"],)).fetchone()
    assert tuple(old) == (T1, "interrupted")
    assert metrics.close_abandoned(db, ids["project"], run) == 0


def test_a_new_run_leaves_a_live_run_alone(db, ids):
    """2026-10-04: a bench running beside `runner run` had its jobs marked interrupted when
    the runner started. A run whose heartbeat is fresh is still working."""
    bench = _job(db, ids)
    metrics.update_run_heartbeat(db, ids["run"], T1)
    run = metrics.upsert_run(db, ids["project"], "20260930-170000", started=T1, heartbeat=T1)
    fresh_after = datetime.fromisoformat(T1) - timedelta(minutes=2)
    assert metrics.close_abandoned(db, ids["project"], run, alive_after=fresh_after) == 0
    assert db.execute("SELECT outcome FROM jobs WHERE id = ?", (bench,)).fetchone()[0] == "running"
    stale_after = datetime.fromisoformat(T1) + timedelta(minutes=1)
    assert metrics.close_abandoned(db, ids["project"], run, alive_after=stale_after) == 1
