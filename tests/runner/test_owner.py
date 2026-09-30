"""The owner's side (ADR 12 items 13 and 14): the verdict, sign-off and ADR decisions."""

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
    code, text = owner.verdict(repo, 1, State(), "clean")
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
    code, text = owner.verdict(repo, 1, state, "clean")
    assert code == 2
    assert text.startswith("⚠ NEEDS YOU")
    assert "docs/adr/14-photos.md: Keep?" in text
    assert "paused behind it: m1-03-gallery" in text
    assert "m1-04-thing blocked: 2 escalations used" in text
    assert "then rerun  uv run runner milestone 1" in text


def test_a_review_that_stopped_for_the_owner_needs_you(repo: Path):
    code, text = owner.verdict(repo, 1, State(), "adr-needed")
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
    owner.signoff(repo, 1, TODAY)
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
        owner.signoff(repo, 1, TODAY)
    owner.signoff(repo, 1, TODAY, force=True)
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
