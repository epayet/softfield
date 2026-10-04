import json
import re
import sqlite3

import pytest

from runner import claude, metrics, milestone, owner
from runner.agents import JobResult
from runner.gates import GateResult
from runner.milestone import (
    footer_fields,
    milestone_after,
    milestone_doc,
    milestone_metrics,
    milestone_summary,
    signoff_sections,
)
from runner.state import State
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
        "decisions": "None.",
        "lessons": "- 2026-09-30: 2 merged.",
    }
    with_next = REVIEW_DOC.replace("### 3. Left", "### 6. What next\nAn album page.\n\n### 3. Left")
    assert signoff_sections(with_next)["what_next"] == "An album page."
    assert signoff_sections("# nothing\n") == {}


def test_the_sign_off_sheet_has_what_clogged_the_factory_line():
    """Item 7 of lead.md's sheet (the owner, 2026-10-02)."""
    clogged = REVIEW_DOC.replace(
        "## What was built",
        "### 7. What clogged the factory line\n- 11 h waiting for Claude.\n\n## What was built",
    )
    assert signoff_sections(clogged)["clogged"] == "- 11 h waiting for Claude."


def test_a_milestone_run_records_its_doc(repo, monkeypatch):
    _milestone_repo(repo)
    monkeypatch.setattr(milestone, "review_milestone", lambda *a: "clean")
    assert milestone.run_milestone(_config(repo), "m1", "m1-start") == "clean"
    [row] = _rows(repo, "milestones")
    assert (row["key"], row["title"], row["status"]) == ("m1", "Photos for Mum", "in progress")
    assert row["outcome"] == "- Mum sees photos."
    assert row["done_when"] == "- A photo shows.\n- Tests pass."
    assert row["started"]
    assert row["signoff"] is None  # no review report yet


def test_a_milestone_run_records_a_sign_off_sheet_written_outside_the_runner(repo, monkeypatch):
    """A review done interactively (f1's) reaches the dashboard at the next run, not only at
    a headless review or a backfill."""
    _milestone_repo(repo)
    (repo / "docs" / "reviews").mkdir(parents=True)
    (repo / "docs" / "reviews" / "m1.md").write_text(REVIEW_DOC)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "review")
    monkeypatch.setattr(milestone, "review_milestone", lambda *a: "clean")
    milestone.run_milestone(_config(repo), "m1", "m1-start")
    [row] = _rows(repo, "milestones")
    assert json.loads(str(row["signoff"]))["decisions"] == "None."


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


def _checkpoint_finding(repo, key: str, ticket: str | None = None) -> None:
    """A finding an earlier checkpoint recorded on its job, about ``ticket`` (merged by the
    local model, difficulty 5) if given."""
    conn = metrics.open_db(_config(repo).metrics_db)
    try:
        project = metrics.upsert_project(conn, repo.name)
        milestone_id = metrics.upsert_milestone(conn, project, "m1")
        ticket_id = None
        if ticket:
            ticket_id = metrics.upsert_ticket(
                conn, project, ticket, milestone_id=milestone_id, difficulty=5, merged_by="local-m"
            )
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
            conn,
            milestone_id,
            key,
            job_id=job,
            ticket_id=ticket_id,
            severity="nit",
            summary="Odd name",
            file="a.py",
            agent="claude-sonnet",
        )
    finally:
        conn.close()


def test_the_final_verdicts_move_the_reviewer_and_the_author_once(repo, monkeypatch):
    """f1-24 (ADR 15 item 9): the verdicts as the review loop stops, each rated once."""
    _milestone_repo(repo)
    (repo / "docs" / "reviews").mkdir()
    _checkpoint_finding(repo, "m1-C1-1", ticket="m1-01-thing")
    rounds = [
        {"findings": [], "checkpoint_verdicts": {"m1-C1-1": "confirmed"}, "score": 8},
        {"findings": [], "checkpoint_verdicts": {"m1-C1-1": "rejected"}, "score": 4},
    ]

    def run_claude(job, repo_, timeout, log_path, now, resume=None):
        out = re.search(r"Write (\S+) as:", job.prompt)
        assert out
        (repo_ / out[1]).write_text(json.dumps(rounds.pop(0) if rounds else {"findings": []}))
        return JobResult(ok=True, text="", duration_s=1.0)

    monkeypatch.setattr(claude, "run_claude", run_claude)
    monkeypatch.setattr(milestone, "run_e2e", lambda *a: GateResult("e2e", True, ""))
    milestone.review_milestone(_config(repo), "m1", "m1-start")
    milestone.review_milestone(_config(repo), "m1", "m1-start")  # a rerun rates nothing again
    changes = [(c["agent"], c["skill"], c["result"]) for c in _rows(repo, "rating_changes")]
    assert changes == [
        ("claude-sonnet", "reviewing", "confirmed m1-C1-1"),
        ("local-m", "coding", "finding m1-C1-1"),
    ]


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


def test_a_named_milestone_finds_its_short_tickets(repo):
    """ADR 16 item 6: f3-factory-line's tickets are f3-01-…, not f30's or f2's."""
    for tid in ("f3-01-a", "f30-01-b", "f2-01-c"):
        write_task(repo / "tasks" / "done", tid)
    assert milestone_metrics(repo, "f3-factory-line").tasks == ["a"]
    summary = milestone_summary(repo, "f3-factory-line")
    assert "there's no `f3-factory-line-start` yet" in summary


def test_a_named_milestone_run_records_its_doc_and_review(repo, monkeypatch):
    (repo / "docs" / "milestones").mkdir(parents=True)
    (repo / "docs" / "milestones" / "f3-factory-line.md").write_text(MILESTONE_DOC)
    (repo / "docs" / "reviews").mkdir(parents=True)
    (repo / "docs" / "reviews" / "f3-factory-line.md").write_text(REVIEW_DOC)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "plan")
    git(repo, "tag", "f3-factory-line-start")
    monkeypatch.setattr(milestone, "review_milestone", lambda *a: "clean")
    milestone.run_milestone(_config(repo), "f3-factory-line", "f3-factory-line-start")
    [row] = _rows(repo, "milestones")
    assert (row["key"], row["title"]) == ("f3-factory-line", "Photos for Mum")
    assert row["started"]
    assert json.loads(str(row["signoff"]))["decisions"] == "None."


def test_a_named_milestone_waits_for_tickets_written_with_its_short_key(repo, monkeypatch):
    (repo / "docs" / "milestones").mkdir(parents=True)
    (repo / "docs" / "milestones" / "f3-factory-line.md").write_text(MILESTONE_DOC)
    write_task(repo / "tasks" / "blocked", "f3-01-a")
    ready = write_task(repo / "tasks" / "ready", "f3-02-b", deps="[f3-01-a]")
    ready.write_text(ready.read_text().replace("milestone: 1\n", "milestone: f3\n"))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "tickets")
    monkeypatch.setattr(milestone, "work_queue", lambda s, milestone=None: False)
    monkeypatch.setattr(milestone, "review_milestone", lambda *a: pytest.fail("reviewed early"))
    stop = milestone.run_milestone(_config(repo), "f3-factory-line", "HEAD")
    assert stop == milestone.PAUSED + "f3-02-b"


def test_the_first_milestone_run_tags_its_start_and_a_rerun_keeps_it(repo, monkeypatch):
    """f2 review: no plan session tagged `f2-start`, so the review had no base to diff."""
    monkeypatch.setattr(milestone, "work_queue", lambda s, milestone=None: False)
    monkeypatch.setattr(milestone, "review_milestone", lambda *a: "clean")
    first = git(repo, "rev-parse", "HEAD").strip()
    milestone.run_milestone(_config(repo), "f3", "f3-start")
    (repo / "later.txt").write_text("x")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "later")
    milestone.run_milestone(_config(repo), "f3", "f3-start")
    assert git(repo, "rev-parse", "f3-start^{commit}").strip() == first


def test_a_paused_stop_always_needs_the_owner():
    from runner.owner import _needs_owner

    assert _needs_owner(milestone.PAUSED + "m1-02-b")
    assert _needs_owner(milestone.WAITS + "m0's sign-off: m1-02-b")


@pytest.mark.parametrize(
    "header",
    [
        "> **After:** f3-factory-line signed off",
        "> **Status: planned** (2026-10-02). **After:** f3-factory-line signed off.",
        "After: `f3-factory-line` signed off",
    ],
)
def test_milestone_after_reads_the_header(header):
    """ADR 17 item 4: in the header blockquote or under the title."""
    assert milestone_after(f"# Milestone F4: always on\n\n{header}\n\n## Outcome\n") == (
        "f3-factory-line"
    )


def test_milestone_after_is_none_without_the_line_or_below_the_header():
    assert milestone_after(MILESTONE_DOC) is None
    body = "# Milestone F4: x\n\n## Outcome\n- After: f3 signed off, the line runs.\n"
    assert milestone_after(body) is None


def test_a_milestone_waits_until_its_after_is_signed_off(repo):
    docs = repo / "docs" / "milestones"
    docs.mkdir(parents=True)
    (docs / "f3-factory-line.md").write_text("# F3\n\n> **Status: in review** (2026-10-02).\n")
    (docs / "f4-always-on.md").write_text("# F4\n\n> **After:** f3 signed off\n")
    (docs / "f5.md").write_text("# F5\n\n> **Status: planned**\n")
    keys = ["f4-always-on", "f5"]
    assert milestone.waits_for(repo, keys) == {"f4": "f3"}
    (docs / "f3-factory-line.md").write_text("# F3\n\n> **Status: done.** Signed off.\n")
    assert milestone.waits_for(repo, keys) == {}


def test_the_verdict_says_what_a_waiting_milestone_waits_for(repo, monkeypatch):
    docs = repo / "docs" / "milestones"
    docs.mkdir(parents=True)
    (docs / "m1.md").write_text("# M1\n\n> **After:** m0-base signed off\n")
    write_task(repo / "tasks" / "ready", "m1-01-a")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "tickets")
    monkeypatch.setattr(milestone, "work_queue", lambda s, milestone=None: False)
    monkeypatch.setattr(milestone, "review_milestone", lambda *a: pytest.fail("reviewed early"))
    stop = milestone.run_milestone(_config(repo), "m1", "HEAD")
    assert stop == "waits for m0-base's sign-off: m1-01-a"
    code, text = owner.verdict(repo, "m1", State(), stop)
    assert code == 2
    assert "  • m1 waits for m0-base's sign-off: m1-01-a\n" in text


# --- the reviews `runner run` starts (f4-20) -----------------------------------------------


def milestone_ticket(repo, folder: str, task_id: str, key: str) -> None:
    path = write_task(repo / "tasks" / folder, task_id)
    path.write_text(path.read_text().replace("milestone: 1\n", f"milestone: {key}\n"))


def test_a_milestone_whose_tickets_are_all_done_is_due_for_review(repo):
    milestone_ticket(repo, "done", "f9-01-a", "f9")
    milestone_ticket(repo, "done", "f9-02-b", "f9")
    milestone_ticket(repo, "later", "f9-03-aside", "f9")  # set aside: not part of the build
    milestone_ticket(repo, "done", "f10-01-c", "f10")
    milestone_ticket(repo, "ready", "f10-02-d", "f10")
    milestone_ticket(repo, "done", "f11-01-e", "f11")
    milestone_ticket(repo, "escalated", "f11-02-f", "f11")
    milestone_ticket(repo, "done", "bug-01-g", "bugs")  # ADR 19: no review, no sign-off
    assert milestone.due_reviews(repo, State()) == ["f9"]


def test_a_due_review_goes_by_the_milestones_full_key(repo):
    (repo / "docs" / "milestones").mkdir(parents=True)
    (repo / "docs" / "milestones" / "f9-always-on.md").write_text(MILESTONE_DOC)
    milestone_ticket(repo, "done", "f9-01-a", "f9")
    assert milestone.due_reviews(repo, State()) == ["f9-always-on"]


def test_a_reviewed_or_signed_off_milestone_isnt_due_again(repo):
    milestone_ticket(repo, "done", "f9-01-a", "f9")
    assert milestone.due_reviews(repo, State(review_stop={"f9": "clean"})) == []
    # A review a restart cut short carries on, from the rounds in state.json.
    restarted = State(review_counts={"f9": [2]}, review_stop={"f9": milestone.RESTART})
    assert milestone.due_reviews(repo, restarted) == ["f9"]
    reviews = repo / "docs" / "reviews"
    reviews.mkdir(parents=True)
    (reviews / "f9.md").write_text(REVIEW_DOC)  # reviewed interactively
    assert milestone.due_reviews(repo, State()) == []
    assert milestone.due_reviews(repo, State(review_counts={"f9": [3]})) == ["f9"]  # a Ctrl-C
    (reviews / "f9.md").unlink()
    git(repo, "tag", "f9-done")
    assert milestone.due_reviews(repo, State()) == []


def test_a_due_review_diffs_from_the_plans_commit(repo, monkeypatch):
    """No plan session tagged F3's or F4's start: the review tags the commit that added the
    milestone's doc, where `runner milestone` would have tagged its first run."""
    (repo / "docs" / "milestones").mkdir(parents=True)
    (repo / "docs" / "milestones" / "f9.md").write_text(MILESTONE_DOC)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "plan f9")
    plan = git(repo, "rev-parse", "HEAD").strip()
    milestone_ticket(repo, "done", "f9-01-a", "f9")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "f9-01-a merged")
    seen: list[tuple[str, str]] = []

    def review(cfg, key, base):
        seen.append((key, base))
        return "clean"

    monkeypatch.setattr(milestone, "review_milestone", review)
    assert milestone.run_due_review(_config(repo), "f9") == "clean"
    assert seen == [("f9", "f9-start")]
    assert git(repo, "rev-parse", "f9-start^{commit}").strip() == plan
    milestone.run_due_review(_config(repo), "f9")  # a tag already there is kept
    assert git(repo, "rev-parse", "f9-start^{commit}").strip() == plan
