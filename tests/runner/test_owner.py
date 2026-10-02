"""The owner's side (ADR 12 items 13 and 14): the verdict, sign-off and ADR decisions."""

import sqlite3
from datetime import date
from pathlib import Path

import pytest

from runner import owner
from runner.state import State
from runner.tasks import append_footer
from tests.runner.conftest import git, write_task

TODAY = date(2026, 10, 1)


def _review(repo: Path) -> None:
    (repo / "docs" / "reviews").mkdir(parents=True, exist_ok=True)
    (repo / "docs" / "reviews" / "m1.md").write_text(
        "# Milestone 1\n\n- **Status:** review done, waiting for sign-off.\n\n"
        "## Sign-off sheet\n\n### 2. How to test it yourself\n1. Pair a phone.\n2. Send.\n\n"
        "### 3. Left for later\n- nothing\n"
    )


def test_a_clean_milestone_is_ready_for_sign_off(repo: Path):
    _review(repo)
    code, text = owner.verdict(repo, "m1", State(), "clean")
    assert code == 0
    assert text.startswith("✅ READY FOR SIGN-OFF")
    assert "1. Pair a phone.\n" in text and "Left for later" not in text
    assert text.rstrip().endswith("Then: uv run runner signoff 1")


def test_a_decision_for_the_owner_says_what_and_what_next(repo: Path):
    write_task(repo / "tasks" / "escalated", "m1-02-photos")
    write_task(repo / "tasks" / "ready", "m1-03-gallery", "[m1-02-photos]")
    blocked = write_task(repo / "tasks" / "blocked", "m1-04-thing")
    append_footer(blocked, {"result": "blocked", "reason": "2 escalations used"})
    state = State(owner={"m1-02-photos": {"adr": "docs/adr/14-photos.md", "question": "Keep?"}})
    code, text = owner.verdict(repo, "m1", state, "clean")
    assert code == 2
    assert text.startswith("⚠ NEEDS YOU")
    assert "docs/adr/14-photos.md: Keep?" in text
    assert "paused behind it: m1-03-gallery" in text
    assert "m1-04-thing blocked: 2 escalations used" in text
    assert "then rerun  uv run runner milestone 1" in text


def test_a_review_that_stopped_for_the_owner_needs_you(repo: Path):
    code, text = owner.verdict(repo, "m1", State(), "adr-needed")
    assert code == 2 and "review stopped: adr-needed" in text


def _milestone(repo: Path) -> None:
    (repo / "docs" / "milestones").mkdir(parents=True)
    (repo / "docs" / "milestones" / "m1.md").write_text(
        "# Milestone 1\n\n> **Status: in review** (2026-09-30). Base: git tag `m1-start`.\n>\n"
        "> **Progress:** all done.\n\n## Outcome\n"
    )
    _review(repo)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "docs")


def test_signoff_marks_the_milestone_done_and_tags_it(repo: Path):
    _milestone(repo)
    owner.signoff(repo, "m1", TODAY)
    milestone = (repo / "docs" / "milestones" / "m1.md").read_text()
    assert "> **Status: done.** Signed off by the owner on 2026-10-01." in milestone
    assert "in review" not in milestone
    review = (repo / "docs" / "reviews" / "m1.md").read_text()
    assert "- **Status:** done, signed off by the owner on 2026-10-01." in review
    assert git(repo, "tag").split() == ["m1-done"]
    assert git(repo, "log", "-1", "--format=%s").strip() == "M1 signed off by the owner"
    assert git(repo, "status", "--porcelain") == ""


def test_signoff_refuses_while_work_is_left(repo: Path):
    _milestone(repo)
    write_task(repo / "tasks" / "escalated", "m1-02-photos")
    with pytest.raises(owner.OwnerError, match="m1-02-photos"):
        owner.signoff(repo, "m1", TODAY)
    owner.signoff(repo, "m1", TODAY, force=True)
    assert git(repo, "tag").split() == ["m1-done"]


def test_accept_and_reject_set_an_adrs_status(repo: Path):
    adr = repo / "docs" / "adr" / "14-photos.md"
    adr.parent.mkdir(parents=True)
    adr.write_text("# ADR 14\n\n- **Status:** Proposed (to explore)\n- **Date:** x\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "adr")
    owner.decide_adr(repo, 14, "Accepted", TODAY)
    assert "- **Status:** Accepted (by the owner, 2026-10-01)\n" in adr.read_text()
    assert git(repo, "log", "-1", "--format=%s").strip() == "ADR 14 accepted by the owner"
    owner.decide_adr(repo, 14, "Rejected", TODAY)
    assert "- **Status:** Rejected (by the owner, 2026-10-01)\n" in adr.read_text()
    with pytest.raises(owner.OwnerError, match="ADR 15"):
        owner.decide_adr(repo, 15, "Accepted", TODAY)


# --- owner items in the metrics database (f1 D8) -------------------------------------------


def _db(repo: Path) -> Path:
    return repo / "var" / "factory-metrics.sqlite"  # never the real one


def _items(repo: Path) -> dict[tuple[str, str], dict[str, object]]:
    conn = sqlite3.connect(_db(repo))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT * FROM owner_items ORDER BY id").fetchall()
        return {(r["kind"], r["subject"]): dict(r) for r in rows}
    finally:
        conn.close()


def _open(repo: Path) -> dict[tuple[str, str], dict[str, object]]:
    return {k: v for k, v in _items(repo).items() if v["resolved"] is None}


def _needs_you(repo: Path) -> State:
    write_task(repo / "tasks" / "escalated", "m1-02-photos")
    write_task(repo / "tasks" / "escalated", "m1-05-other")
    blocked = write_task(repo / "tasks" / "blocked", "m1-04-thing")
    append_footer(blocked, {"result": "blocked", "reason": "2 escalations used"})
    return State(owner={"m1-02-photos": {"adr": "docs/adr/14-photos.md", "question": "Keep?"}})


def test_the_verdicts_items_are_open_owner_items_with_a_command(repo: Path):
    state = _needs_you(repo)
    owner.verdict(repo, "m1", state, "adr-needed", db=_db(repo))
    items = _open(repo)
    assert set(items) == {
        ("adr", "docs/adr/14-photos.md"),
        ("escalated", "m1-05-other"),
        ("blocked", "m1-04-thing"),
        ("review-stop", "m1"),
    }
    adr = items[("adr", "docs/adr/14-photos.md")]
    assert adr["text"] == "Keep?" and adr["command"] == "uv run runner accept 14"
    blocked = items[("blocked", "m1-04-thing")]
    assert "2 escalations used" in str(blocked["text"])
    assert blocked["command"] == "uv run runner milestone 1"
    assert items[("review-stop", "m1")]["text"] == "adr-needed"
    assert all(item["created"] for item in items.values())
    assert [row["name"] for row in _projects(repo)] == [repo.name]


RESERVE_TEXT = (
    "m1-03-lead waits for Claude's reserve (21% of the week left, resets Mon 5 Oct 16:00):"
    " rerun and answer y to use it"
)


def _reserve(text: str = RESERVE_TEXT) -> State:
    """A lead ticket parked at the reserve with no answer (ADR 15 item 5)."""
    entry = {"kind": "reserve", "resets_at": "2026-10-05T16:00:00+00:00", "text": text}
    return State(parked={"m1-03-lead": entry, "m2-01-lead": {**entry, "text": "later"}})


def test_a_ticket_waiting_for_the_reserve_needs_you_until_a_rerun_runs_it(repo: Path):
    write_task(repo / "tasks" / "ready", "m1-03-lead")
    code, text = owner.verdict(repo, "m1", _reserve(), "tickets paused: m1-03-lead", db=_db(repo))
    assert code == 2 and f"  • {RESERVE_TEXT}" in text
    assert "later" not in text  # another milestone's
    item = _open(repo)[("reserve", "m1-03-lead")]
    assert (item["text"], item["command"]) == (RESERVE_TEXT, "uv run runner milestone 1")
    owner.verdict(repo, "m1", State(), "clean", db=_db(repo))
    assert ("reserve", "m1-03-lead") not in _open(repo)


def _projects(repo: Path) -> list[sqlite3.Row]:
    conn = sqlite3.connect(_db(repo))
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute("SELECT * FROM projects").fetchall()
    finally:
        conn.close()


def test_the_same_verdict_twice_leaves_the_same_rows(repo: Path):
    state = _needs_you(repo)
    owner.verdict(repo, "m1", state, "clean", db=_db(repo))
    first = _items(repo)
    owner.verdict(repo, "m1", state, "clean", db=_db(repo))
    assert _items(repo) == first


def test_a_rerun_that_clears_a_blocked_ticket_resolves_its_item(repo: Path):
    state = _needs_you(repo)
    owner.verdict(repo, "m1", state, "clean", db=_db(repo))
    (repo / "tasks" / "blocked" / "m1-04-thing.md").unlink()
    write_task(repo / "tasks" / "done", "m1-04-thing")
    write_task(repo / "tasks" / "escalated", "m2-01-later")  # another milestone's: untouched
    owner.verdict(repo, "m2", State(), "clean", db=_db(repo))
    assert ("blocked", "m1-04-thing") in _open(repo)
    owner.verdict(repo, "m1", state, "clean", db=_db(repo))
    assert ("blocked", "m1-04-thing") not in _open(repo)
    assert _items(repo)[("blocked", "m1-04-thing")]["resolved"]
    assert ("escalated", "m2-01-later") in _open(repo)


def test_sign_off_waiting_is_an_item_that_signoff_resolves(repo: Path):
    _milestone(repo)
    code, _ = owner.verdict(repo, "m1", State(), "clean", db=_db(repo))
    assert code == 0
    item = _open(repo)[("signoff", "m1")]
    assert item["command"] == "uv run runner signoff 1"
    assert "1. Pair a phone." in str(item["text"]) and "2. Send." in str(item["text"])
    owner.signoff(repo, "m1", TODAY, db=_db(repo))
    assert _open(repo) == {}
    conn = sqlite3.connect(_db(repo))
    try:
        status, ended = conn.execute("SELECT status, ended FROM milestones").fetchone()
    finally:
        conn.close()
    assert status == "done" and ended


def _owner_score(repo: Path) -> object:
    conn = sqlite3.connect(_db(repo))
    try:
        return conn.execute("SELECT owner_score FROM milestones").fetchone()[0]
    finally:
        conn.close()


def test_signoff_stores_the_owners_score(repo: Path):
    """ADR 14 item 14: how the result felt on the devices, 1 to 10."""
    _milestone(repo)
    owner.signoff(repo, "m1", TODAY, db=_db(repo), score=7)
    assert _owner_score(repo) == 7


def test_signoff_without_a_score_leaves_it_empty(repo: Path):
    _milestone(repo)
    owner.signoff(repo, "m1", TODAY, db=_db(repo))
    assert _owner_score(repo) is None


@pytest.mark.parametrize("score", [0, 11])
def test_signoff_refuses_a_score_out_of_range_before_changing_anything(repo: Path, score: int):
    _milestone(repo)
    with pytest.raises(owner.OwnerError, match="1 to 10"):
        owner.signoff(repo, "m1", TODAY, db=_db(repo), score=score)
    assert git(repo, "tag") == "" and git(repo, "status", "--porcelain") == ""
    assert not _db(repo).exists()


def test_the_verdict_is_on_the_milestone_row(repo: Path):
    _needs_you(repo)
    owner.verdict(repo, "m1", State(), "clean", db=_db(repo))
    conn = sqlite3.connect(_db(repo))
    try:
        assert conn.execute("SELECT key, verdict FROM milestones").fetchall() == [
            ("m1", "needs you")
        ]
    finally:
        conn.close()


def test_accept_and_reject_resolve_the_adrs_item(repo: Path):
    adr = repo / "docs" / "adr" / "14-photos.md"
    adr.parent.mkdir(parents=True)
    adr.write_text("# ADR 14\n\n- **Status:** Proposed\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "adr")
    owner.verdict(repo, "m1", _needs_you(repo), "clean", db=_db(repo))
    owner.decide_adr(repo, 14, "Accepted", TODAY, db=_db(repo))
    assert ("adr", "docs/adr/14-photos.md") not in _open(repo)
    assert ("blocked", "m1-04-thing") in _open(repo)


def test_a_database_that_cant_be_opened_leaves_the_owners_commands_working(repo: Path, capsys):
    (repo / "var").mkdir()
    (repo / "var" / "a-file").write_text("")
    code, _ = owner.verdict(repo, "m1", State(), "adr-needed", db=repo / "var" / "a-file" / "x")
    assert code == 2
    assert "metrics database" in capsys.readouterr().err


def test_a_factory_milestone_uses_its_key_everywhere(repo: Path):
    """f1's tickets, docs, commands and tag are named f1, not m1 (the f1 plan)."""
    write_task(repo / "tasks" / "escalated", "m1-02-photos")  # another milestone's: not f1's
    blocked = write_task(repo / "tasks" / "blocked", "f1-02-report")
    append_footer(blocked, {"result": "blocked", "reason": "check-all failed"})
    code, text = owner.verdict(repo, "f1", State(), "clean")
    assert code == 2 and "f1-02-report blocked" in text and "m1-02-photos" not in text
    assert "uv run runner milestone f1" in text
    blocked.unlink()
    (repo / "docs" / "milestones").mkdir(parents=True)
    (repo / "docs" / "milestones" / "f1.md").write_text(
        "# Factory 1\n\n> **Status: in review** (2026-10-01).\n"
    )
    (repo / "docs" / "reviews").mkdir(parents=True)
    (repo / "docs" / "reviews" / "f1.md").write_text("# F1\n\n- **Status:** review done.\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "docs")
    code, text = owner.verdict(repo, "f1", State(), "clean")
    assert code == 0 and "Review: docs/reviews/f1.md" in text
    assert text.rstrip().endswith("uv run runner signoff f1")
    owner.signoff(repo, "f1", TODAY, force=True)
    assert "git tag `f1-start`" in (repo / "docs" / "milestones" / "f1.md").read_text()
    assert git(repo, "tag").split() == ["f1-done"]
    assert git(repo, "log", "-1", "--format=%s").strip() == "F1 signed off by the owner"
