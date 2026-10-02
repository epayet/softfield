"""`runner backfill`: M1–M4 from their logs into the metrics database (f1-04, D2, D6).

Every test builds its own fake `var/runs` and repo in tmp_path; none reads the real ones.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from runner import backfill, metrics
from runner.gitops import Git
from tests.runner.conftest import git

LOCAL = "local-qwen3.6-35b-a3b"
RUN = "20260929-142614"

TICKET = """\
---
id: {id}
milestone: {milestone}
agent: {agent}
depends_on: []
files:
  - coucou/thing.py
tests:
  - tests/unit/test_thing.py
---

### Goal
{goal}

### Context
Nothing.

### Done when
Tests pass.
"""

# Real-shaped: OpenCode's `--format json` events, one per line.
OPENCODE_1 = (
    '{"type":"tool_use","timestamp":1790690340000,"sessionID":"ses_one",'
    '"part":{"tool":"edit","state":{"status":"completed"}}}\n'
    '{"type":"step_finish","timestamp":1790690347997,"sessionID":"ses_one",'
    '"part":{"type":"step-finish","tokens":{"total":7973,"input":7696,"output":201,'
    '"reasoning":76,"cache":{"write":0,"read":1000}},"cost":0}}\n'
)
OPENCODE_2 = (
    '{"type":"step_finish","timestamp":1790691000000,"sessionID":"ses_two",'
    '"part":{"tokens":{"input":5000,"output":100,"reasoning":0,"cache":{"read":2000}}}}\n'
    '{"type":"tool_use","timestamp":1790691060000,"sessionID":"ses_two",'
    '"part":{"tool":"bash","state":{"status":"error"}}}\n'
    '{"type":"step_finish","timestamp":1790691120000,"sessionID":"ses_two",'
    '"part":{"tokens":{"input":9000,"output":300,"reasoning":50,"cache":{"read":1000}}}}\n'
)
GATES_FAIL = (
    "## protected-paths: ok\n\n\n## ruff: ok\n157 files already formatted\n\n"
    "## mypy: FAIL\ntests/browser/test_thumbnail.py:32: error: Returning Any\n"
    "Found 1 error in 1 file (checked 156 source files)"
)
GATES_OK = "## protected-paths: ok\n\n\n## ruff: ok\n\n\n## mypy: ok\n"
CLAUDE_OK = json.dumps(
    {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "duration_ms": 124649,
        "num_turns": 25,
        "result": "done",
        "session_id": "672bd198",
        "total_cost_usd": 0.629,
        "usage": {
            "input_tokens": 34,
            "cache_creation_input_tokens": 41124,
            "cache_read_input_tokens": 592399,
            "output_tokens": 9070,
        },
    }
)
REVIEW = {
    "findings": [
        {
            "id": "m4-F1",
            "severity": "blocking",
            "route": "claude",
            "summary": "A bug.",
            "resolved": True,
            "security": False,
        },
        {"id": "m4-F2", "severity": "nit", "route": "backlog", "summary": "A nit."},
    ],
    "stop": None,
}
FOOTER = "\n```yaml\n# --- runner ---\n{fields}\n```\n"


def _claude_log(stdout: str, stderr: str = "") -> str:
    return stdout + "\n--- stderr ---\n" + stderr


def _ticket(
    repo: Path, folder: str, task_id: str, *, agent: str = "developer", footer: str = ""
) -> Path:
    milestone = task_id.split("-", 1)[0].removeprefix("m")
    path = repo / "tasks" / folder / f"{task_id}.md"
    text = TICKET.format(id=task_id, milestone=milestone, agent=agent, goal=f"Goal of {task_id}.")
    path.write_text(text + (FOOTER.format(fields=footer) if footer else ""), encoding="utf-8")
    return path


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def m4(repo: Path) -> Path:
    """A repo and var/runs shaped like M4's: one ticket merged at its second attempt, after a
    direction; a review round with its findings; an old M1 ticket known only by its footer."""
    git(repo, "tag", "m4-start")
    _write(
        repo / "docs" / "milestones" / "m4.md",
        "# Milestone 4: Compose\n\n## Outcome\nMum gets notes.\n\n## Done when\n- it works\n",
    )
    _write(
        repo / "docs" / "reviews" / "m4.md",
        "# M4 review\n\n### 1. What changed\nNotes.\n\n### 2. How to test it yourself\n1. Send.\n",
    )
    _ticket(repo, "done", "m4-01-thing", footer="result: done\nattempts: 2\ntokens: 23000")
    _ticket(repo, "done", "m1-01-old", footer="result: done\nattempts: 3\ntokens: 1200000")
    (repo / "coucou" / "thing.py").write_text("def thing() -> int:\n    return 1\n")
    git(repo, "add", "-A")
    git(
        repo,
        "commit",
        "-q",
        "-m",
        "m4-01-thing: Goal.\n\nAgent: local-model\nTask: m4-01-thing\nAttempts: 2",
    )
    git(repo, "tag", "m4-done")

    run = repo / "var" / "runs" / RUN
    logs = run / "m4-01-thing"
    _write(logs / "opencode-1.jsonl", OPENCODE_1)
    _write(logs / "gates-1.txt", GATES_FAIL)
    _write(logs / "direction.md", "Return a list.")
    _write(logs / "opencode-2.jsonl", OPENCODE_2)
    _write(logs / "gates-2.txt", GATES_OK)
    _write(logs / "last.diff", "")
    _write(run / "claude-direction-m4-01-thing.log", _claude_log(CLAUDE_OK))
    _write(run / "claude-review-m4-review-r1.log", _claude_log(CLAUDE_OK))
    _write(run / "review-m4-r1.json", json.dumps(REVIEW))
    _write(repo / "var" / "runs" / "state.json", json.dumps({"review_counts": {"4": [1]}}))
    return repo


def _run(repo: Path, db: Path) -> backfill.Summary:
    conn = metrics.open_db(db)
    try:
        return backfill.backfill(conn, repo, repo / "var" / "runs", local_agent=LOCAL)
    finally:
        conn.close()


def _rows(db: Path, sql: str, *args: object) -> list[dict[str, Any]]:
    conn = metrics.open_db(db)
    try:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]
    finally:
        conn.close()


TABLES = ("projects", "milestones", "runs", "tickets", "jobs", "findings")


def _counts(db: Path) -> dict[str, int]:
    return {t: _rows(db, f"SELECT count(*) AS n FROM {t}")[0]["n"] for t in TABLES}  # noqa: S608


# --- the parsers, on real-shaped fixtures ---------------------------------------------------


def test_a_gates_file_gives_each_gate_with_its_result():
    gates = backfill.parse_gates(GATES_FAIL, "var/runs/r/t/gates-1.txt")
    assert gates == [
        {"name": "protected-paths", "ok": True, "seconds": None, "log": "var/runs/r/t/gates-1.txt"},
        {"name": "ruff", "ok": True, "seconds": None, "log": "var/runs/r/t/gates-1.txt"},
        {"name": "mypy", "ok": False, "seconds": None, "log": "var/runs/r/t/gates-1.txt"},
    ]


def test_a_gates_file_without_gates_is_malformed():
    assert backfill.parse_gates("Traceback (most recent call last):\n", "g.txt") is None


def test_a_claude_log_gives_its_result_and_usage():
    log = backfill.parse_claude_log(_claude_log(CLAUDE_OK, "a warning"))
    assert log is not None
    assert log.ok and not log.timed_out
    assert log.tokens_in == 34
    assert log.tokens_cached == 592399
    assert log.tokens_out == 9070
    assert log.cost_usd == pytest.approx(0.629)
    assert log.session_id == "672bd198"
    assert log.duration_s == pytest.approx(124.649)


def test_a_timed_out_claude_log_says_so():
    log = backfill.parse_claude_log("--- timed out ---\n")
    assert log is not None
    assert log.timed_out and not log.ok


def test_an_unreadable_claude_log_is_malformed():
    assert backfill.parse_claude_log("not json\n--- stderr ---\nboom") is None


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("claude-escalation-m4-06-me-wiring.log", ("escalation", "m4-06-me-wiring", None, 0)),
        ("claude-lead-ticket-f1-03-state-retry1.log", ("lead-ticket", "f1-03-state", None, 1)),
        ("claude-review-m3-review-r2.log", ("review", "m3-review-r2", None, 0)),
        ("claude-escalation-m4-06-me-wiring-2.log", ("escalation", "m4-06-me-wiring", 2, 0)),
        ("claude-checkpoint-checkpoint-3-retry2.log", ("checkpoint", "checkpoint", 3, 2)),
        ("notes.log", None),
    ],
)
def test_a_claude_log_name_gives_its_job(name, expected):
    parsed = backfill.claude_log_name(name)
    got = None if parsed is None else (parsed.kind, parsed.subject, parsed.number, parsed.retry)
    assert got == expected


# --- a fake M4-shaped run ---------------------------------------------------------------------


def test_the_run_and_its_tickets_are_written(m4, tmp_path):
    db = tmp_path / "metrics.sqlite"
    _run(m4, db)
    [run] = _rows(db, "SELECT * FROM runs")
    assert run["run_dir"] == RUN
    assert run["started"].startswith("2026-09-29T14:26:14")
    tickets = {t["ticket"]: t for t in _rows(db, "SELECT * FROM tickets")}
    assert {"m4-01-thing", "m1-01-old"} <= set(tickets)
    assert tickets["m4-01-thing"]["state"] == "done"
    assert tickets["m4-01-thing"]["title"] == "Goal of m4-01-thing."


def test_a_tickets_difficulty_and_its_correction_are_stored(m4, tmp_path):
    path = m4 / "tasks" / "done" / "m4-01-thing.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("depends_on:", "difficulty: 6\ndifficulty_corrected: 8\ndepends_on:")
    )
    db = tmp_path / "metrics.sqlite"
    _run(m4, db)
    tickets = {t["ticket"]: t for t in _rows(db, "SELECT * FROM tickets")}
    assert (
        tickets["m4-01-thing"]["difficulty"],
        tickets["m4-01-thing"]["difficulty_corrected"],
    ) == (
        6,
        8,
    )
    assert tickets["m1-01-old"]["difficulty"] is None


def test_a_ticket_with_a_bad_difficulty_is_a_gap(m4, tmp_path):
    path = m4 / "tasks" / "done" / "m4-01-thing.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("depends_on:", "difficulty: 11\ndepends_on:")
    )
    summary = _run(m4, tmp_path / "metrics.sqlite")
    assert any("m4-01-thing.md" in gap and "difficulty" in gap for gap in summary.gaps)


def test_local_attempts_become_jobs_with_tokens_steps_peak_and_gates(m4, tmp_path):
    db = tmp_path / "metrics.sqlite"
    _run(m4, db)
    jobs = _rows(
        db,
        "SELECT jobs.* FROM jobs JOIN tickets ON tickets.id = jobs.ticket_id"
        " WHERE tickets.ticket = 'm4-01-thing' AND agent = ? ORDER BY attempt",
        LOCAL,
    )
    first, second = jobs
    assert (first["role"], first["attempt"], first["outcome"]) == ("developer", 1, "failed")
    assert (first["tokens_in"], first["tokens_out"], first["steps"]) == (7696, 277, 1)
    assert first["peak_context"] == 8696
    assert first["edit_streak"] == 1
    assert first["session_id"] == "ses_one"
    assert [(g["name"], g["ok"]) for g in json.loads(first["gates"])] == [
        ("protected-paths", True),
        ("ruff", True),
        ("mypy", False),
    ]
    assert first["log_path"] == f"var/runs/{RUN}/m4-01-thing/opencode-1.jsonl"
    # A direction came before the last attempt (ADR 12 item 6).
    assert (second["role"], second["attempt"], second["outcome"]) == ("last-attempt", 2, "passed")
    assert (second["tokens_in"], second["steps"], second["peak_context"]) == (14000, 2, 10000)
    assert second["refused_commands"] == 1
    assert second["started"] < second["ended"]


def test_claude_jobs_are_written_with_their_role_and_agent(m4, tmp_path):
    db = tmp_path / "metrics.sqlite"
    _run(m4, db)
    jobs = {j["role"]: j for j in _rows(db, "SELECT * FROM jobs WHERE agent LIKE 'claude-%'")}
    assert set(jobs) == {"direction", "review"}
    direction = jobs["direction"]
    assert direction["agent"] == "claude-opus"
    assert direction["outcome"] == "passed"
    assert (direction["tokens_in"], direction["tokens_cached"]) == (34, 592399)
    assert direction["cost_usd"] == pytest.approx(0.629)
    assert direction["ticket_id"] is not None
    review = jobs["review"]
    assert review["ticket_id"] is None
    assert review["log_path"] == f"var/runs/{RUN}/claude-review-m4-review-r1.log"


def test_review_findings_hang_off_their_review_job(m4, tmp_path):
    db = tmp_path / "metrics.sqlite"
    _run(m4, db)
    [review] = _rows(db, "SELECT id FROM jobs WHERE role = 'review'")
    findings = {f["key"]: f for f in _rows(db, "SELECT * FROM findings")}
    assert set(findings) == {"m4-F1", "m4-F2"}
    assert findings["m4-F1"]["severity"] == "blocking"
    assert findings["m4-F1"]["resolved"] == 1
    assert findings["m4-F1"]["job_id"] == review["id"]


def test_merges_come_from_git_trailers(m4, tmp_path):
    db = tmp_path / "metrics.sqlite"
    _run(m4, db)
    [ticket] = _rows(db, "SELECT * FROM tickets WHERE ticket = 'm4-01-thing'")
    assert ticket["merged_by"] == LOCAL
    sha = git(m4, "rev-parse", "m4-done").strip()
    assert ticket["commit"] == sha
    assert ticket["lines_changed"] == Git(m4).commit_size(sha) > 0


def test_the_milestone_gets_its_doc_review_and_dates(m4, tmp_path):
    db = tmp_path / "metrics.sqlite"
    _run(m4, db)
    [milestone] = _rows(db, "SELECT * FROM milestones WHERE key = 'm4'")
    assert milestone["title"] == "Compose"
    assert milestone["outcome"] == "Mum gets notes."
    assert milestone["done_when"] == "- it works"
    assert milestone["status"] == "done"
    assert milestone["review_rounds"] == 1
    assert json.loads(milestone["signoff"])["changed"] == "Notes."
    assert milestone["started"] is not None and milestone["ended"] is not None


def test_the_summary_counts_what_it_wrote_per_milestone(m4, tmp_path):
    summary = _run(m4, tmp_path / "metrics.sqlite")
    m4_counts = summary.written["m4"]
    assert (m4_counts.runs, m4_counts.tickets, m4_counts.jobs) == (1, 1, 4)
    assert (m4_counts.findings, m4_counts.merges) == (2, 1)
    text = backfill.render(summary)
    assert "m4" in text and "m1" in text


def test_a_named_milestone_gathers_its_short_tickets_doc_review_and_findings(repo, tmp_path):
    """ADR 16 item 6: f3-factory-line's tickets are f3-01-…, in either form of frontmatter."""
    git(repo, "tag", "f3-factory-line-start")
    _write(repo / "docs" / "milestones" / "f3-factory-line.md", "# Factory line\n")
    _write(repo / "docs" / "reviews" / "f3-factory-line.md", "# F3\n\n### 1. What changed\nA.\n")
    for task_id, key in (("f3-01-short", "f3"), ("f3-02-full", "f3-factory-line")):
        _write(
            repo / "tasks" / "done" / f"{task_id}.md",
            TICKET.format(id=task_id, milestone=key, agent="lead", goal="G."),
        )
    run = repo / "var" / "runs" / RUN
    _write(run / "f3-01-short" / "opencode-1.jsonl", OPENCODE_1)
    _write(run / "f3-01-short" / "gates-1.txt", GATES_OK)
    _write(run / "claude-review-f3-factory-line-review-r1.log", _claude_log(CLAUDE_OK))
    _write(run / "review-f3-factory-line-r1.json", json.dumps(REVIEW))
    state = {"review_counts": {"f3-factory-line": [2]}}
    _write(repo / "var" / "runs" / "state.json", json.dumps(state))
    db = tmp_path / "metrics.sqlite"
    summary = _run(repo, db)
    [milestone] = _rows(db, "SELECT * FROM milestones")
    assert (milestone["key"], milestone["title"]) == ("f3-factory-line", "Factory line")
    assert json.loads(milestone["signoff"])["changed"] == "A."
    assert milestone["review_rounds"] == 1 and milestone["started"] is not None
    tickets = _rows(db, "SELECT ticket, milestone_id FROM tickets ORDER BY ticket")
    assert tickets == [
        {"ticket": "f3-01-short", "milestone_id": milestone["id"]},
        {"ticket": "f3-02-full", "milestone_id": milestone["id"]},
    ]
    [review] = _rows(db, "SELECT id, milestone_id FROM jobs WHERE role = 'review'")
    assert review["milestone_id"] == milestone["id"]
    findings = _rows(db, "SELECT job_id, milestone_id FROM findings")
    assert findings == [{"job_id": review["id"], "milestone_id": milestone["id"]}] * 2
    assert set(summary.written) == {"f3-factory-line"}


# --- idempotent -------------------------------------------------------------------------------


def test_running_it_twice_gives_identical_row_counts(m4, tmp_path):
    db = tmp_path / "metrics.sqlite"
    _run(m4, db)
    first = _counts(db)
    _run(m4, db)
    assert _counts(db) == first
    assert first["jobs"] == 4


def test_a_run_the_runner_recorded_itself_is_left_alone(m4, tmp_path):
    db = tmp_path / "metrics.sqlite"
    conn = metrics.open_db(db)
    project = metrics.upsert_project(conn, m4.name)
    run_id = metrics.upsert_run(conn, project, RUN, command="milestone m4")
    metrics.start_job(
        conn,
        run_id,
        ticket_id=None,
        milestone_id=None,
        role="review",
        agent="claude-opus",
        attempt=1,
        started="2026-09-29T15:00:00+01:00",
    )
    conn.close()
    _run(m4, db)
    assert len(_rows(db, "SELECT * FROM jobs")) == 1
    [run] = _rows(db, "SELECT * FROM runs")
    assert run["command"] == "milestone m4"


# --- gaps ------------------------------------------------------------------------------------


def test_a_ticket_known_only_by_its_footers_is_a_gap(m4, tmp_path):
    summary = _run(m4, tmp_path / "metrics.sqlite")
    [gap] = [g for g in summary.gaps if "m1-01-old" in g]
    assert "3 attempt" in gap
    assert summary.written["m1"].tickets == 1


def test_missing_or_malformed_files_are_gaps_not_errors(m4, tmp_path):
    logs = m4 / "var" / "runs" / RUN / "m4-01-thing"
    (logs / "gates-2.txt").unlink()
    _write(logs / "gates-1.txt", "Traceback: nothing useful\n")
    _write(m4 / "var" / "runs" / RUN / "review-m4-r1.json", "{not json")
    _write(m4 / "var" / "runs" / RUN / "claude-direction-m4-01-thing.log", "garbage")
    _write(m4 / "var" / "runs" / "state.json", "{")
    _write(m4 / "tasks" / "done" / "m4-02-broken.md", "no frontmatter here\n")
    summary = _run(m4, tmp_path / "metrics.sqlite")
    text = "\n".join(summary.gaps)
    for expected in (
        "gates-1.txt",
        "gates-2.txt",
        "review-m4-r1.json",
        "claude-direction-m4-01-thing.log",
        "state.json",
        "m4-02-broken.md",
    ):
        assert expected in text
    assert summary.written["m4"].jobs == 4  # the jobs happened; only some facts are lost
    assert "gaps" in backfill.render(summary).lower()


def test_an_unknown_job_kind_gets_backfill_unknown(m4, tmp_path):
    _write(m4 / "var" / "runs" / RUN / "claude-mystery-m4-01-thing.log", _claude_log(CLAUDE_OK))
    db = tmp_path / "metrics.sqlite"
    _run(m4, db)
    [job] = _rows(db, "SELECT * FROM jobs WHERE role = 'backfill-unknown'")
    assert job["agent"] == "claude-opus"


def test_an_empty_or_missing_runs_folder_is_fine(repo, tmp_path):
    summary = _run(repo, tmp_path / "metrics.sqlite")
    assert summary.written == {} or all(c.jobs == 0 for c in summary.written.values())


def test_a_stray_file_in_var_runs_is_a_gap(m4, tmp_path):
    _write(m4 / "var" / "runs" / "m2-batch2.log", "old batch output")
    summary = _run(m4, tmp_path / "metrics.sqlite")
    assert any("m2-batch2.log" in g for g in summary.gaps)


def test_times_are_iso_with_an_offset(m4, tmp_path):
    db = tmp_path / "metrics.sqlite"
    _run(m4, db)
    for job in _rows(db, "SELECT started, ended FROM jobs"):
        for value in job.values():
            assert value[-6] in "+-" and value[-3] == ":"
