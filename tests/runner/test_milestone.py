import json
import re
import sqlite3
from datetime import datetime, timedelta

import pytest

from runner import claude, cli, loop, metrics, milestone, owner
from runner.agents import JobResult
from runner.gates import GateResult
from runner.loop import close_session, open_session
from runner.milestone import (
    Card,
    card,
    footer_fields,
    milestone_after,
    milestone_doc,
    milestone_metrics,
    milestone_summary,
    signoff_sections,
)
from runner.report import TaskRecord
from runner.state import State, load_state
from runner.tasks import append_footer
from tests.runner.conftest import git, write_task
from tests.runner.test_loop import FIVE_RESETS, THURSDAY, _claude_at, _config


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
        path = write_task(repo / ".factory" / "tasks" / folder, tid)
        append_footer(path, {"attempts": attempts, "tokens": 1000 * attempts})
    requeued = repo / ".factory" / "tasks" / "done" / "m1-02-b.md"
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
    write_task(repo / ".factory" / "tasks" / "blocked", "m1-01-a")
    write_task(repo / ".factory" / "tasks" / "ready", "m1-02-b", deps="[m1-01-a]")
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
    (repo / ".factory" / "cards").mkdir(parents=True)
    (repo / ".factory" / "cards" / "m1.md").write_text(MILESTONE_DOC)
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


CARD_DOC = """\
# Milestone F5: the board

> **Status: planned** (2026-10-02).
> **State:** needs sign-off · **Priority:** 2 · **Area:** product

## Outcome
- **State:** idea · **Priority:** 9 (a mention below the header doesn't count)
"""


def test_a_card_reads_its_header_line():
    """f5 D4: a milestone doc's header holds its card."""
    assert card("f5-board", CARD_DOC) == Card("needs sign-off", 2, "product")
    building = "# F5\n\n> **State:** building · **Priority:** 2 · **Area:** factory\n"
    assert card("f5", building) == Card("building", 2, "factory")


def test_a_card_without_its_line_is_derived():
    """No state: done once signed off, else building; no priority: 100; no area: the key's
    series."""
    assert card("f2", "# F2\n\n> **Status: done.** Signed off.\n") == Card("done", 100, "factory")
    assert card("m4", MILESTONE_DOC) == Card("building", 100, "product")
    assert card("f6", "# F6\n> **Priority:** 7\n") == Card("building", 7, "factory")
    unknown = "# F7\n> **State:** someday · **Area:** garden\n"
    assert card("f7", unknown) == Card("building", 100, "factory")


def test_every_milestone_doc_gets_its_card_at_session_start(repo):
    """f5 D4: an idea with no tickets yet is a card on the board too, as a ticket is in the
    queue (`sync_tickets`)."""
    (repo / ".factory" / "cards").mkdir(parents=True)
    idea = "# Milestone F9: a garden\n\n> **State:** idea · **Priority:** 3\n"
    (repo / ".factory" / "cards" / "f9-garden.md").write_text(idea)
    (repo / ".factory" / "cards" / "m1.md").write_text(MILESTONE_DOC)
    (repo / ".factory" / "cards" / "notes.md").write_text("# Not a milestone\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "an idea")
    close_session(open_session(_config(repo)))
    rows = {r["key"]: r for r in _rows(repo, "milestones")}
    assert set(rows) == {"f9-garden", "m1"}
    garden = rows["f9-garden"]
    assert (garden["title"], garden["state"], garden["priority"]) == ("a garden", "idea", 3)
    assert garden["area"] == "factory"
    assert (rows["m1"]["state"], rows["m1"]["priority"], rows["m1"]["area"]) == (
        "building",
        100,
        "product",
    )


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


LIST_SHEET = """\
# Review: F26 numbers

- **Status:** reviewed; waiting for the owner's sign-off.

## Sign-off sheet

1. **What changed**
   - The two headings carry a number.
   - With nothing waiting, "Your desk" alone.
2. **How to test it yourself** (on the phone)
   1. Open `/planning`.
   2. Plant an idea.
3. **Left for later**
   - The numbers change on a reload.
4. **Decisions waiting for you:** none.
5. **How the work went**
   - One ticket, first attempt.
6. **What next**
   - **Factory:** run F19 next.
7. **What clogged the factory line**
   - A two-line card waited two days.

## What was built
One template.
"""


def test_the_sign_off_sheet_is_read_as_a_numbered_list_too():
    """F26's and F12's reviews wrote the sheet as lead.md lays it out, a numbered list with
    bold titles: nothing was stored, so neither showed on the owner's desk for sign-off
    (2026-10-12). A sheet is never dropped for its form."""
    assert signoff_sections(LIST_SHEET) == {
        "changed": '- The two headings carry a number.\n- With nothing waiting, "Your desk" alone.',
        "how_to_test": "(on the phone)\n1. Open `/planning`.\n2. Plant an idea.",
        "later": "- The numbers change on a reload.",
        "decisions": "none.",
        "lessons": "- One ticket, first attempt.",
        "what_next": "- **Factory:** run F19 next.",
        "clogged": "- A two-line card waited two days.",
    }
    # a numbered step inside a section is no section, and headings win where both are there
    assert signoff_sections(REVIEW_DOC)["how_to_test"] == "1. Send a photo."
    both = REVIEW_DOC.replace("Mum sees photos.", "1. **What next**\n   Not this.")
    assert "what_next" not in signoff_sections(both)


def test_a_review_written_outside_a_review_job_reaches_the_desk_at_session_start(repo):
    """The desk lists a milestone for sign-off once its sheet is stored (F50 D1). A sheet
    written by hand, or one the runner couldn't read when it was written, is stored at the
    next session's start, as the card is."""
    (repo / ".factory" / "cards").mkdir(parents=True)
    (repo / ".factory" / "reviews").mkdir(parents=True)
    (repo / ".factory" / "cards" / "m1.md").write_text(MILESTONE_DOC)
    (repo / ".factory" / "reviews" / "m1.md").write_text(LIST_SHEET)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "a review")
    close_session(open_session(_config(repo)))
    [row] = [r for r in _rows(repo, "milestones") if r["key"] == "m1"]
    assert json.loads(row["signoff"])["later"] == "- The numbers change on a reload."


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
    (repo / ".factory" / "reviews").mkdir(parents=True)
    (repo / ".factory" / "reviews" / "m1.md").write_text(REVIEW_DOC)
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
        (repo_ / ".factory" / "reviews").mkdir(parents=True, exist_ok=True)
        (repo_ / ".factory" / "reviews" / "m1.md").write_text(REVIEW_DOC)
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
    (repo / ".factory" / "reviews").mkdir()
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
    (repo / ".factory" / "reviews").mkdir()
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
    # the project's own test folders, from its project.toml (ADR 30), not a fixed list
    assert "`uv run pytest -q tests/unit tests/integration tests/runner tests/browser" in prompts[0]
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
    (repo / ".factory" / "reviews").mkdir()

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
        write_task(repo / ".factory" / "tasks" / "done", tid)
    assert milestone_metrics(repo, "f1").tasks == ["a"]
    assert "Who did the work in F1" in milestone_summary(repo, "f1")
    assert "there's no `f1-start` yet" in milestone_summary(repo, "f1")


def test_a_named_milestone_finds_its_short_tickets(repo):
    """ADR 16 item 6: f3-factory-line's tickets are f3-01-…, not f30's or f2's."""
    for tid in ("f3-01-a", "f30-01-b", "f2-01-c"):
        write_task(repo / ".factory" / "tasks" / "done", tid)
    assert milestone_metrics(repo, "f3-factory-line").tasks == ["a"]
    summary = milestone_summary(repo, "f3-factory-line")
    assert "there's no `f3-factory-line-start` yet" in summary


def test_a_named_milestone_run_records_its_doc_and_review(repo, monkeypatch):
    (repo / ".factory" / "cards").mkdir(parents=True)
    (repo / ".factory" / "cards" / "f3-factory-line.md").write_text(MILESTONE_DOC)
    (repo / ".factory" / "reviews").mkdir(parents=True)
    (repo / ".factory" / "reviews" / "f3-factory-line.md").write_text(REVIEW_DOC)
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
    (repo / ".factory" / "cards").mkdir(parents=True)
    (repo / ".factory" / "cards" / "f3-factory-line.md").write_text(MILESTONE_DOC)
    write_task(repo / ".factory" / "tasks" / "blocked", "f3-01-a")
    ready = write_task(repo / ".factory" / "tasks" / "ready", "f3-02-b", deps="[f3-01-a]")
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
    docs = repo / ".factory" / "cards"
    docs.mkdir(parents=True)
    (docs / "f3-factory-line.md").write_text("# F3\n\n> **Status: in review** (2026-10-02).\n")
    (docs / "f4-always-on.md").write_text("# F4\n\n> **After:** f3 signed off\n")
    (docs / "f5.md").write_text("# F5\n\n> **Status: planned**\n")
    keys = ["f4-always-on", "f5"]
    assert milestone.waits_for(repo, keys) == {"f4": "f3"}
    (docs / "f3-factory-line.md").write_text("# F3\n\n> **Status: done.** Signed off.\n")
    assert milestone.waits_for(repo, keys) == {}


def test_the_verdict_says_what_a_waiting_milestone_waits_for(repo, monkeypatch):
    docs = repo / ".factory" / "cards"
    docs.mkdir(parents=True)
    (docs / "m1.md").write_text("# M1\n\n> **After:** m0-base signed off\n")
    write_task(repo / ".factory" / "tasks" / "ready", "m1-01-a")
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
    path = write_task(repo / ".factory" / "tasks" / folder, task_id)
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
    (repo / ".factory" / "cards").mkdir(parents=True)
    (repo / ".factory" / "cards" / "f9-always-on.md").write_text(MILESTONE_DOC)
    milestone_ticket(repo, "done", "f9-01-a", "f9")
    assert milestone.due_reviews(repo, State()) == ["f9-always-on"]


def test_a_reviewed_or_signed_off_milestone_isnt_due_again(repo):
    milestone_ticket(repo, "done", "f9-01-a", "f9")
    assert milestone.due_reviews(repo, State(review_stop={"f9": "clean"})) == []
    # A review a restart cut short carries on, from the rounds in state.json.
    restarted = State(review_counts={"f9": [2]}, review_stop={"f9": milestone.RESTART})
    assert milestone.due_reviews(repo, restarted) == ["f9"]
    reviews = repo / ".factory" / "reviews"
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
    (repo / ".factory" / "cards").mkdir(parents=True)
    (repo / ".factory" / "cards" / "f9.md").write_text(MILESTONE_DOC)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "plan f9")
    plan = git(repo, "rev-parse", "HEAD").strip()
    milestone_ticket(repo, "done", "f9-01-a", "f9")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "f9-01-a merged")
    seen: list[tuple[str, str]] = []

    def review(cfg, key, base, *, park):
        assert park  # `runner run` has a queue to go back to (F53 D1)
        seen.append((key, base))
        return "clean"

    monkeypatch.setattr(milestone, "review_milestone", review)
    assert milestone.run_due_review(_config(repo), "f9") == "clean"
    assert seen == [("f9", "f9-start")]
    assert git(repo, "rev-parse", "f9-start^{commit}").strip() == plan
    milestone.run_due_review(_config(repo), "f9")  # a tag already there is kept
    assert git(repo, "rev-parse", "f9-start^{commit}").strip() == plan


def test_a_replanned_milestones_review_diffs_from_its_first_merge(repo, monkeypatch):
    """f3 review (f3-F5): F3's doc dated from F1, so its review read all of F2 and F4. The
    review starts where the milestone's first ticket was merged."""
    (repo / ".factory" / "cards").mkdir(parents=True)
    (repo / ".factory" / "cards" / "f9.md").write_text(MILESTONE_DOC)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "plan f9, long ago")
    (repo / "other.txt").write_text("another milestone's work")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "f8-01-x: other work\n\nTask: f8-01-x")
    before = git(repo, "rev-parse", "HEAD").strip()
    milestone_ticket(repo, "done", "f9-01-a", "f9")
    milestone_ticket(repo, "done", "f9-02-b", "f9")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "f9-01-a: the first\n\nTask: f9-01-a")
    git(repo, "commit", "-q", "--allow-empty", "-m", "f9-02-b: the second\n\nTask: f9-02-b")
    monkeypatch.setattr(milestone, "review_milestone", lambda cfg, key, base, **kw: "clean")
    milestone.run_due_review(_config(repo), "f9")
    assert git(repo, "rev-parse", "f9-start^{commit}").strip() == before


# --- a review Claude can't take now (F53 D1) ------------------------------------------------


@pytest.fixture
def clock(monkeypatch) -> list[datetime]:
    """`test_loop`'s fake clock: a sleep moves it on."""
    at = [THURSDAY]
    monkeypatch.setattr(loop, "now", lambda: at[0])
    monkeypatch.setattr("time.sleep", lambda s: at.__setitem__(0, at[0] + timedelta(seconds=s)))
    monkeypatch.setattr(loop, "fresh_reading", lambda s: None)  # no real `claude -p`
    return at


def _review_writes(job, repo_, findings: list[dict[str, object]]) -> None:
    out = re.search(r"Write (\S+) as:", job.prompt)
    assert out
    (repo_ / out[1]).write_text(json.dumps({"findings": findings, "stop": None}))
    (repo_ / ".factory" / "reviews").mkdir(parents=True, exist_ok=True)


LEAK: dict[str, object] = {
    "id": "f9-F1",
    "severity": "should-fix",
    "route": "local",
    "summary": "Leak",
}


def test_a_named_milestones_review_still_waits_for_claude(repo, monkeypatch, clock):
    """`runner milestone` has no queue to go back to: its review sleeps to the reset, before
    its e2e run."""
    _milestone_repo(repo)
    _claude_at(repo, 0.80)
    events: list[tuple[str, bool]] = []

    def run_e2e(*a):
        events.append(("e2e", loop.now() > FIVE_RESETS))
        return GateResult("e2e", True, "")

    def run_claude(job, repo_, timeout, log_path, now, resume=None):
        events.append(("review", loop.now() > FIVE_RESETS))
        _review_writes(job, repo_, [])
        return JobResult(ok=True, text="", duration_s=1.0)

    monkeypatch.setattr(claude, "run_claude", run_claude)
    monkeypatch.setattr(milestone, "run_e2e", run_e2e)
    assert milestone.review_milestone(_config(repo), "m1", "m1-start") == "clean"
    assert events == [("e2e", True), ("review", True)]
    [row] = _rows(repo, "work_queue")
    assert row["done"] is not None and row["not_before"] is None


def test_a_review_parked_between_rounds_resumes_at_its_round_on_its_own_fixes(
    repo, monkeypatch, clock, capsys
):
    """F53 D1, through `runner run`: round 1 leaves Claude at 80%, so round 2 parks. A ticket
    of another milestone merges meanwhile; after the reset round 2 runs, not round 1 again,
    and its prompt names the fix merge of its own milestone only."""
    milestone_ticket(repo, "done", "f9-01-a", "f9")
    milestone_ticket(repo, "ready", "f10-01-next", "f10")
    (repo / ".factory" / "project.toml").write_text("")  # `cli._repo` looks for it
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "tickets")
    events: list[str] = []
    merges: dict[str, str] = {}
    prompts: list[str] = []

    def run_task(s, task):
        events.append(f"{task.id} at {loop.now():%H:%M}")
        git(
            repo,
            "mv",
            f".factory/tasks/ready/{task.path.name}",
            f".factory/tasks/done/{task.path.name}",
        )
        git(repo, "commit", "-q", "-m", f"{task.id}: done\n\nAgent: local-m\nTask: {task.id}")
        merges[task.id] = git(repo, "rev-parse", "HEAD").strip()
        return TaskRecord(id=task.id, milestone=task.milestone, result="done")

    def run_e2e(*a):
        events.append("e2e")
        return GateResult("e2e", True, "")

    def run_claude(job, repo_, timeout, log_path, now, resume=None):
        prompts.append(job.prompt)
        found = re.search(r"milestone (\S+) of this project.*Round (\d)", job.prompt, re.S)
        assert found
        key, round_no = found.groups()
        events.append(f"{key} round {round_no}")
        if len(prompts) == 1:  # F9's round 1 files a fix ticket and uses up Claude's room
            milestone_ticket(repo_, "ready", "f9-02-fix", "f9")
            _claude_at(repo_, 0.80)
            _review_writes(job, repo_, [LEAK])
        else:
            _review_writes(job, repo_, [{**LEAK, "resolved": True}] if key == "f9" else [])
        return JobResult(ok=True, text="", duration_s=1.0)

    record = owner.record_verdict

    def record_verdict(repo_, text):
        events.append("verdict")
        return record(repo_, text)

    monkeypatch.chdir(repo)
    monkeypatch.setattr(cli, "load_config", lambda repo_: _config(repo))
    monkeypatch.setattr(loop, "run_task", run_task)
    monkeypatch.setattr(milestone, "run_e2e", run_e2e)
    monkeypatch.setattr(claude, "run_claude", run_claude)
    monkeypatch.setattr(owner, "record_verdict", record_verdict)
    monkeypatch.setattr(milestone, "wait_for_room", lambda *a: pytest.fail("the runner slept"))
    assert cli.main(["run", "--here"]) == 0
    assert events == [
        "e2e",
        "f9 round 1",
        "f9-02-fix at 12:00",
        # round 2 parks, with no e2e run and no verdict: the line goes on
        "f10-01-next at 12:00",
        "e2e",
        "f9 round 2",
        "verdict",
        "e2e",
        "f10 round 1",
        "verdict",
    ]
    assert clock[0] > FIVE_RESETS
    assert "the review of f9 waits for Claude · resumes 14:00" in capsys.readouterr().out
    again = prompts[1]
    assert f"- f9-02-fix: `git show {merges['f9-02-fix'][:9]}`" in again
    assert "f10-01-next" not in again and merges["f10-01-next"][:9] not in again
    state = load_state(_config(repo).runs_dir / "state.json")
    assert state.review_counts["f9"] == [1, 0] and state.review_stop["f9"] == "clean"
    assert all(row["done"] is not None for row in _rows(repo, "work_queue"))
    assert git(repo, "status", "--porcelain") == ""


def test_a_later_round_with_only_its_own_merges_reads_the_diff_since_the_last_round(repo):
    """Nothing else merged between the rounds: the fix diffs, as before F53."""
    milestone_ticket(repo, "done", "f9-01-a", "f9")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "review f9 round 1 (by Claude)")
    since = git(repo, "rev-parse", "HEAD").strip()
    git(repo, "commit", "-q", "--allow-empty", "-m", "f9-01-a: a fix\n\nTask: f9-01-a")
    s = open_session(_config(repo), None)
    assert milestone._last_round(s.git, "f9", 1, "f9-start") == f"{since}^"
    assert milestone._last_round(s.git, "f9", 0, "f9-start") == "f9-start"
    assert milestone._last_round(s.git, "f9", 2, "f9-start") == "f9-start"  # no such commit
    scope = milestone._fix_scope(s, "f9", since)
    assert scope.startswith(f"Re-review only the fix diffs `git diff {since}..main`")
    git(repo, "commit", "-q", "--allow-empty", "-m", "f10-01-x: other\n\nTask: f10-01-x")
    assert "`git diff" not in milestone._fix_scope(s, "f9", since)
