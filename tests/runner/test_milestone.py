import json
import re
import sqlite3

import pytest

from runner import claude, metrics, milestone
from runner.agents import JobResult
from runner.gates import GateResult
from runner.milestone import (
    footer_fields,
    milestone_doc,
    milestone_metrics,
    milestone_summary,
    signoff_sections,
)
from runner.tasks import append_footer
from tests.runner.conftest import git, write_task
from tests.runner.test_loop import _config


def test_footer_fields_reads_the_last_footer(tmp_path):
    path = write_task(tmp_path, "m1-01-a")
    append_footer(path, {"result": "escalated", "attempts": 3})
    append_footer(path, {"result": "done", "attempts": 1})
    assert footer_fields(path.read_text()) == {"result": "done", "attempts": "1"}


def test_milestone_metrics(repo):
    for folder, tid, attempts in [
        ("done", "m1-01-a", 1),
        ("done", "m1-02-b", 2),
        ("escalated", "m1-03-c", 3),
        ("done", "m2-01-d", 1),
    ]:
        path = write_task(repo / "tasks" / folder, tid)
        append_footer(path, {"attempts": attempts, "tokens": 1000 * attempts})
    requeued = repo / "tasks" / "done" / "m1-02-b.md"
    requeued.write_text(
        requeued.read_text().replace("attempts: 2", "result: escalated\nattempts: 2")
    )
    append_footer(requeued, {"attempts": 1, "tokens": 500})
    metrics = milestone_metrics(repo, "m1")
    # f0: m1-02-b was escalated, requeued and merged: 3 attempts in all, and it counts as escalated
    assert (metrics.done, metrics.escalated, sorted(metrics.attempts)) == (2, 2, [1, 3, 3])
    assert metrics.tasks == ["a", "b"]
    assert metrics.local_tokens == 1000 + 2000 + 500 + 3000  # every footer, requeues included
    assert round(metrics.escalation_rate, 2) == 0.67


def test_milestone_summary_without_a_start_tag(repo):
    assert "there's no `m7-start` yet" in milestone_summary(repo, "m7")


def test_a_milestone_stops_for_a_restart_before_the_review(repo, monkeypatch):
    monkeypatch.setattr(milestone, "work_queue", lambda s, milestone=None: True)
    monkeypatch.setattr(
        milestone, "review_milestone", lambda *a: pytest.fail("reviewed with stale code")
    )
    assert milestone.run_milestone(_config(repo), "m1", "HEAD") == milestone.RESTART


def test_no_review_while_tickets_wait_behind_a_blocked_one(repo, monkeypatch):
    """f1: f1-16 was blocked with 15 tickets behind it, and the runner went on to review the
    half-built milestone, spending its one review loop (ADR 12 item 10)."""
    write_task(repo / "tasks" / "blocked", "m1-01-a")
    write_task(repo / "tasks" / "ready", "m1-02-b", deps="[m1-01-a]")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "tickets")
    monkeypatch.setattr(milestone, "work_queue", lambda s, milestone=None: False)
    monkeypatch.setattr(milestone, "review_milestone", lambda *a: pytest.fail("reviewed early"))
    stop = milestone.run_milestone(_config(repo), "m1", "HEAD")
    assert stop == milestone.PAUSED + "m1-02-b"


MILESTONE_DOC = """\
# Milestone 1: Photos for Mum

> **Status: in progress** (2026-09-30). Base: git tag `m1-start`.

## Outcome

- Mum sees photos.

## Decisions

- D1: none.

## Done when
- A photo shows.
- Tests pass.
"""

REVIEW_DOC = """\
# Milestone 1: review report

- **Status:** review done, waiting for sign-off.

## Sign-off sheet

### 1. What changed
Mum sees photos.

### 2. How to test it yourself
1. Send a photo.

### 3. Left for later
- Albums.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-09-30: 2 merged.

## What was built
Lots.
"""


def _rows(repo, table):
    conn = sqlite3.connect(_config(repo).metrics_db)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(f"SELECT * FROM {table} ORDER BY id")]  # noqa: S608
    finally:
        conn.close()


def _milestone_repo(repo):
    (repo / "docs" / "milestones").mkdir(parents=True)
    (repo / "docs" / "milestones" / "m1.md").write_text(MILESTONE_DOC)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "plan")
    git(repo, "tag", "m1-start")


def test_the_milestone_doc_parts():
    assert milestone_doc(MILESTONE_DOC) == {
        "title": "Photos for Mum",
        "outcome": "- Mum sees photos.",
        "done_when": "- A photo shows.\n- Tests pass.",
    }
    assert milestone_doc("# Factory 1\n") == {"title": "Factory 1"}


def test_the_sign_off_sections_leave_a_missing_heading_out():
    assert signoff_sections(REVIEW_DOC) == {
        "changed": "Mum sees photos.",
        "how_to_test": "1. Send a photo.",
        "later": "- Albums.",
        "lessons": "- 2026-09-30: 2 merged.",
    }
    with_next = REVIEW_DOC.replace("### 3. Left", "### 6. What next\nAn album page.\n\n### 3. Left")
    assert signoff_sections(with_next)["what_next"] == "An album page."
    assert signoff_sections("# nothing\n") == {}


def test_a_milestone_run_records_its_doc(repo, monkeypatch):
    _milestone_repo(repo)
    monkeypatch.setattr(milestone, "review_milestone", lambda *a: "clean")
    assert milestone.run_milestone(_config(repo), "m1", "m1-start") == "clean"
    [row] = _rows(repo, "milestones")
    assert (row["key"], row["title"], row["status"]) == ("m1", "Photos for Mum", "in progress")
    assert row["outcome"] == "- Mum sees photos."
    assert row["done_when"] == "- A photo shows.\n- Tests pass."
    assert row["started"]


def test_a_review_records_its_rounds_findings_and_sign_off_sheet(repo, monkeypatch):
    _milestone_repo(repo)
    rounds = [
        [
            {"id": "m1-F1", "severity": "should-fix", "route": "claude", "summary": "Leak"},
            {"id": "m1-F2", "severity": "nit", "route": "backlog", "summary": "Name"},
        ],
        [
            {
                "id": "m1-F1",
                "severity": "should-fix",
                "route": "claude",
                "summary": "Leak",
                "resolved": True,
            }
        ],
    ]

    def run_claude(job, repo_, timeout, log_path, now, resume=None):
        out = re.search(r"Write (\S+) as:", job.prompt)
        assert out
        (repo_ / out[1]).write_text(json.dumps({"findings": rounds.pop(0), "stop": None}))
        (repo_ / "docs" / "reviews").mkdir(parents=True, exist_ok=True)
        (repo_ / "docs" / "reviews" / "m1.md").write_text(REVIEW_DOC)
        return JobResult(ok=True, text="", duration_s=1.0)

    monkeypatch.setattr(claude, "run_claude", run_claude)
    monkeypatch.setattr(milestone, "run_e2e", lambda *a: GateResult("e2e", True, ""))
    assert milestone.review_milestone(_config(repo), "m1", "m1-start") == "clean"
    [row] = _rows(repo, "milestones")
    assert row["review_rounds"] == 2 and row["status"] == "review"
    assert json.loads(str(row["signoff"]))["how_to_test"] == "1. Send a photo."
    reviews = [j["id"] for j in _rows(repo, "jobs") if j["role"] == "review"]
    findings = {f["key"]: f for f in _rows(repo, "findings")}
    assert set(findings) == {"m1-F1", "m1-F2"}
    leak = findings["m1-F1"]
    assert (leak["job_id"], leak["resolved"], leak["severity"]) == (reviews[1], 1, "should-fix")
    assert (leak["route"], leak["summary"], leak["milestone_id"]) == ("claude", "Leak", row["id"])
    assert (findings["m1-F2"]["job_id"], findings["m1-F2"]["resolved"]) == (reviews[0], 0)


def _checkpoint_finding(repo, key: str) -> None:
    """A finding an earlier checkpoint recorded on its job."""
    conn = metrics.open_db(_config(repo).metrics_db)
    try:
        project = metrics.upsert_project(conn, repo.name)
        milestone_id = metrics.upsert_milestone(conn, project, "m1")
        run = metrics.upsert_run(conn, project, "earlier")
        job = metrics.start_job(
            conn,
            run,
            ticket_id=None,
            milestone_id=milestone_id,
            role="checkpoint",
            agent="claude-sonnet",
            attempt=1,
            started="2026-10-01T10:00:00+00:00",
        )
        metrics.add_finding(
            conn, milestone_id, key, job_id=job, severity="nit", summary="Odd name", file="a.py"
        )
    finally:
        conn.close()


def test_the_last_rounds_verdicts_and_score_land_on_the_findings_and_milestone(repo, monkeypatch):
    """f1-23 (ADR 14 item 13): the final review judges each checkpoint finding."""
    _milestone_repo(repo)
    (repo / "docs" / "reviews").mkdir()
    _checkpoint_finding(repo, "m1-C1-1")
    _checkpoint_finding(repo, "m1-C1-2")
    leak = {"id": "m1-F1", "severity": "should-fix", "route": "claude", "summary": "Leak"}
    rounds = [
        {"findings": [leak], "checkpoint_verdicts": {"m1-C1-1": "rejected"}, "score": 4},
        {
            "findings": [{**leak, "resolved": True, "file": "a.py", "line": 3, "detail": "d"}],
            "checkpoint_verdicts": {
                "m1-C1-1": "confirmed",
                "m1-C1-2": "rejected",
                "m1-F1": "missed",
                "m1-F9": "missed",  # no such finding: not recorded
            },
            "score": 8,
        },
    ]
    prompts: list[str] = []

    def run_claude(job, repo_, timeout, log_path, now, resume=None):
        prompts.append(job.prompt)
        out = re.search(r"Write (\S+) as:", job.prompt)
        assert out
        (repo_ / out[1]).write_text(json.dumps(rounds.pop(0)))
        return JobResult(ok=True, text="", duration_s=1.0)

    monkeypatch.setattr(claude, "run_claude", run_claude)
    monkeypatch.setattr(milestone, "run_e2e", lambda *a: GateResult("e2e", True, ""))
    milestone.review_milestone(_config(repo), "m1", "m1-start")
    assert "m1-C1-1 (nit, a.py): Odd name" in prompts[0]
    findings = {f["key"]: f for f in _rows(repo, "findings")}
    assert set(findings) == {"m1-C1-1", "m1-C1-2", "m1-F1"}
    assert [findings[k]["verdict"] for k in ("m1-C1-1", "m1-C1-2", "m1-F1")] == [
        "confirmed",
        "rejected",
        "missed",
    ]
    assert (findings["m1-F1"]["file"], findings["m1-F1"]["line"]) == ("a.py", 3)
    assert findings["m1-F1"]["detail"] == "d"
    [row] = _rows(repo, "milestones")
    assert row["review_score"] == 8


def test_a_review_without_a_score_leaves_it_empty(repo, monkeypatch):
    _milestone_repo(repo)
    (repo / "docs" / "reviews").mkdir()

    def run_claude(job, repo_, timeout, log_path, now, resume=None):
        out = re.search(r"Write (\S+) as:", job.prompt)
        assert out
        (repo_ / out[1]).write_text(json.dumps({"findings": [], "stop": None}))
        return JobResult(ok=True, text="", duration_s=1.0)

    monkeypatch.setattr(claude, "run_claude", run_claude)
    monkeypatch.setattr(milestone, "run_e2e", lambda *a: GateResult("e2e", True, ""))
    assert milestone.review_milestone(_config(repo), "m1", "m1-start") == "clean"
    [row] = _rows(repo, "milestones")
    assert row["review_score"] is None


def test_a_factory_milestones_metrics_and_summary(repo):
    for tid in ("f1-01-a", "m1-01-b"):
        write_task(repo / "tasks" / "done", tid)
    assert milestone_metrics(repo, "f1").tasks == ["a"]
    assert "Who did the work in F1" in milestone_summary(repo, "f1")
    assert "there's no `f1-start` yet" in milestone_summary(repo, "f1")


def test_a_paused_stop_always_needs_the_owner():
    from runner.owner import _needs_owner

    assert _needs_owner(milestone.PAUSED + "m1-02-b")
