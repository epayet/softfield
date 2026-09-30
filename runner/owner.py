"""The owner's side of a milestone (ADR 12 items 13 and 14).

``verdict`` is what ``runner milestone N`` prints last: ready for sign-off, or exactly what
needs the owner. ``signoff`` and ``decide_adr`` are the owner's own commands; headless jobs
never get them (only the owner accepts ADRs and signs off, lead.md "Authority").
"""

import re
from datetime import date
from pathlib import Path

from runner.gitops import RUNNER_AUTHOR, Git, with_trailers
from runner.milestone import footer_fields
from runner.state import State
from runner.tasks import STOPPED, blocked_ids, load_dir

# Review stops that need the owner, not another run (docs/workflow.md, review loop).
OWNER_STOPS = ("adr-needed", "security-unresolved", "unforeseen-cross-milestone")
_UNFINISHED = ("ready", *STOPPED)
_STATUS_MILESTONE = re.compile(r"^> \*\*Status:.*$", re.MULTILINE)
_STATUS_LINE = re.compile(r"^- \*\*Status:\*\*.*$", re.MULTILINE)
_TEST_STEPS = re.compile(r"^### \d+\. How to test it yourself\n(.*?)(?=^#|\Z)", re.M | re.S)


class OwnerError(RuntimeError):
    pass


def _ids(repo: Path, folder: str, milestone: int) -> list[str]:
    return sorted(p.stem for p in (repo / "tasks" / folder).glob(f"m{milestone}-*.md"))


def _needs_owner(stop: str) -> bool:
    return stop in OWNER_STOPS or stop.startswith(("end-to-end", "review output unusable"))


def verdict(repo: Path, milestone: int, state: State, review_stop: str) -> tuple[int, str]:
    """The last thing ``runner milestone`` prints, and its exit code: 0 ready, 2 needs you."""
    ready = [t for t in load_dir(repo / "tasks" / "ready", 1000) if t.milestone == milestone]
    needs = []
    for task_id in _ids(repo, "escalated", milestone):
        paused = sorted(blocked_ids(ready, {task_id}))
        behind = f"\n    paused behind it: {', '.join(paused)}" if paused else ""
        decision = state.owner.get(task_id)
        if decision:
            needs.append(f"  • {decision['adr']}: {decision['question']}{behind}")
        else:
            needs.append(f"  • {task_id} escalated with no decision: see its logs{behind}")
    for task_id in _ids(repo, "blocked", milestone):
        path = repo / "tasks" / "blocked" / f"{task_id}.md"
        reason = footer_fields(path.read_text(encoding="utf-8")).get("reason", "see its logs")
        needs.append(f"  • {task_id} blocked: {reason}")
    if _needs_owner(review_stop):
        needs.append(f"  • review stopped: {review_stop}")
    if needs:
        lines = ["⚠ NEEDS YOU", *needs, ""]
        lines.append(f"  Next: decide the above, then rerun  uv run runner milestone {milestone}")
        return 2, "\n".join(lines) + "\n"
    review = repo / "docs" / "reviews" / f"m{milestone}.md"
    lines = ["✅ READY FOR SIGN-OFF", f"  Review: {review.relative_to(repo)} ({review_stop})"]
    match = _TEST_STEPS.search(review.read_text(encoding="utf-8")) if review.is_file() else None
    if match:
        lines.append("  Test on your devices:")
        lines += [f"    {line}" for line in match.group(1).strip().splitlines()]
    lines += ["", f"  Then: uv run runner signoff {milestone}"]
    return 0, "\n".join(lines) + "\n"


def record_verdict(repo: Path, text: str) -> Path | None:
    """Append the verdict to the latest session report and commit it."""
    reports = sorted((repo / "docs" / "sessions").glob("*.md"))
    if not reports:
        return None
    with reports[-1].open("a", encoding="utf-8") as fh:
        fh.write(f"\n## Verdict\n\n```\n{text}```\n")
    Git(repo).commit_all(
        with_trailers("runner: milestone verdict", agent="runner"), author=RUNNER_AUTHOR
    )
    return reports[-1]


def _replace_line(path: Path, pattern: re.Pattern[str], line: str) -> None:
    text = path.read_text(encoding="utf-8")
    if not pattern.search(text):
        raise OwnerError(f"no status line in {path}")
    path.write_text(pattern.sub(line, text, count=1), encoding="utf-8")


def signoff(repo: Path, milestone: int, today: date, force: bool = False) -> None:
    """Mark milestone N done: its doc and review, the ``mN-done`` tag, one commit."""
    left = [f"{t} ({f})" for f in _UNFINISHED for t in _ids(repo, f, milestone)]
    if left and not force:
        raise OwnerError(
            "work is left: " + ", ".join(left) + ". Finish it, or sign off with --force."
        )
    doc = repo / "docs" / "milestones" / f"m{milestone}.md"
    _replace_line(
        doc,
        _STATUS_MILESTONE,
        f"> **Status: done.** Signed off by the owner on {today.isoformat()}."
        f" Base: git tag `m{milestone}-start`."
        f" Report: [`docs/reviews/m{milestone}.md`](../reviews/m{milestone}.md).",
    )
    review = repo / "docs" / "reviews" / f"m{milestone}.md"
    if review.is_file():
        _replace_line(
            review, _STATUS_LINE, f"- **Status:** done, signed off by the owner on {today}."
        )
    git = Git(repo)
    git.commit_all(f"M{milestone} signed off by the owner")
    git.run("tag", f"m{milestone}-done")


def decide_adr(repo: Path, number: int, status: str, today: date) -> Path:
    """Set ADR N's status ("Accepted" or "Rejected") with the date, in one commit."""
    found = sorted((repo / "docs" / "adr").glob(f"{number:02d}-*.md"))
    if not found:
        raise OwnerError(f"ADR {number} not found in docs/adr/")
    _replace_line(
        found[0], _STATUS_LINE, f"- **Status:** {status} (by the owner, {today.isoformat()})"
    )
    Git(repo).commit_all(f"ADR {number} {status.lower()} by the owner")
    return found[0]
