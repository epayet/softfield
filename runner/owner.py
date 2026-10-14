"""The owner's side of a milestone (ADR 12 items 13 and 14).

``verdict`` is what ``runner milestone N`` prints last: ready for sign-off, or exactly what
needs the owner. ``signoff`` and ``decide_adr`` are the owner's own commands; headless jobs
never get them (only the owner accepts ADRs and signs off, lead.md "Authority").
"""

import re
import sqlite3
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import yaml

from runner import metrics
from runner.config import project_name
from runner.gitops import RUNNER_AUTHOR, Git, with_trailers
from runner.milestone import WAITS, footer_fields, signoff_sections
from runner.state import State
from runner.tasks import (
    STOPPED,
    TaskError,
    blocked_ids,
    command_arg,
    load_dir,
    milestone_file,
    milestone_key,
    short_key,
    split_frontmatter,
)

# Review stops that need the owner, not another run (docs/workflow.md, review loop).
OWNER_STOPS = ("adr-needed", "security-unresolved", "unforeseen-cross-milestone")
_UNFINISHED = ("ready", *STOPPED)
_STATUS_MILESTONE = re.compile(r"^> \*\*Status:.*$", re.MULTILINE)
_STATUS_LINE = re.compile(r"^- \*\*Status:\*\*.*$", re.MULTILINE)
_CARD_STATE_LINE = re.compile(r"^> \*\*State:\*\*.*$", re.MULTILINE)  # a planning-room card
_TEST_STEPS = re.compile(r"^### \d+\. How to test it yourself\n(.*?)(?=^#|\Z)", re.M | re.S)


class OwnerError(RuntimeError):
    pass


def _milestone_of(repo: Path, task_id: str) -> str:
    """The short key of the milestone a ticket's ``milestone:`` names: a re-homed ticket keeps
    its old id. One with no file, or whose frontmatter won't parse, counts by its id."""
    for path in sorted((repo / ".factory" / "tasks").glob(f"*/{task_id}.md")):
        try:
            meta, _ = split_frontmatter(path.read_text(encoding="utf-8"))
            return short_key(milestone_key(meta["milestone"]))
        except (TaskError, KeyError, yaml.YAMLError):
            break
    return task_id.split("-", 1)[0]


def _ids(repo: Path, folder: str, milestone: str) -> list[str]:
    """The tickets in ``folder`` that count for ``milestone`` (``_milestone_of``)."""
    paths = sorted((repo / ".factory" / "tasks" / folder).glob("*.md"))
    return [p.stem for p in paths if _milestone_of(repo, p.stem) == short_key(milestone)]


def _needs_owner(stop: str) -> bool:
    return stop in OWNER_STOPS or stop.startswith(
        ("end-to-end", "review output unusable", "tickets paused", WAITS)
    )


# --- owner items in the metrics database (f1 D8): best effort ----------------------------

_ADR_NUMBER = re.compile(r"(?:^|/)(\d+)-[^/]*$")
# The items a rerun of ``runner milestone`` can clear, by kind: whether the subject is a
# ticket of the milestone (``m4-06-…``) or the milestone itself.
_RERUN_KINDS = {
    "escalated": True,
    "blocked": True,
    "reserve": True,
    "five-hour": True,  # a lead ticket waiting for the owner's 25% (ADR 16 item 3)
    "review-stop": False,
    "signoff": False,
}


def _reserve_waits(repo: Path, state: State, milestone: str) -> list[tuple[str, str]]:
    """The milestone's tickets parked at Claude's reserve with no answer (ADR 15 item 5), with
    what the loop told the owner; a rerun asks again."""
    return sorted(
        (task_id, str(entry.get("text") or f"{task_id} waits for Claude's reserve"))
        for task_id, entry in state.parked.items()
        if entry.get("kind") == "reserve" and _milestone_of(repo, task_id) == short_key(milestone)
    )


@dataclass(frozen=True)
class OwnerItem:
    kind: str  # adr, escalated, blocked, reserve, review-stop, signoff
    subject: str  # the ADR's path, the ticket, or the milestone
    text: str
    command: str


def owner_items(repo: Path, milestone: str, state: State, review_stop: str) -> list[OwnerItem]:
    """What the verdict asks of the owner, each with the command that answers it."""
    rerun = f"uv run runner milestone {command_arg(milestone)}"
    items = []
    for task_id in _ids(repo, "escalated", milestone):
        decision = state.owner.get(task_id)
        if decision:
            number = _ADR_NUMBER.search(decision["adr"])
            command = f"uv run runner accept {int(number[1])}" if number else rerun
            adr = decision["adr"] or task_id
            items.append(OwnerItem("adr", adr, decision["question"], command))
        else:
            text = f"{task_id} escalated with no decision: see its logs"
            items.append(OwnerItem("escalated", task_id, text, rerun))
    for task_id in _ids(repo, "blocked", milestone):
        path = repo / ".factory" / "tasks" / "blocked" / f"{task_id}.md"
        reason = footer_fields(path.read_text(encoding="utf-8")).get("reason", "see its logs")
        items.append(OwnerItem("blocked", task_id, f"{task_id} blocked: {reason}", rerun))
    for task_id, text in _reserve_waits(repo, state, milestone):
        items.append(OwnerItem("reserve", task_id, text, rerun))
    if _needs_owner(review_stop):
        items.append(OwnerItem("review-stop", milestone, review_stop, rerun))
    return items


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _write(repo: Path, db: Path | None, write: Callable[[sqlite3.Connection, int], None]) -> None:
    """One write to the metrics database; the owner's commands work on without it."""
    if db is None:
        return
    try:
        conn = metrics.open_db(db)
        try:
            write(conn, metrics.upsert_project(conn, project_name(repo), repo=str(repo)))
        finally:
            conn.close()
    except Exception as exc:
        print(
            f"runner: the metrics database failed ({type(exc).__name__}: {exc});"
            " the owner items weren't updated.",
            file=sys.stderr,
        )


def _cleared_by_rerun(repo: Path, milestone: str) -> Callable[[str, str], bool]:
    """Whether an item is one of ``milestone``'s that a rerun of it clears: a ticket's, by the
    milestone it counts for (``_milestone_of``)."""

    def wanted(kind: str, subject: str) -> bool:
        if kind not in _RERUN_KINDS:
            return False
        if _RERUN_KINDS[kind]:
            return _milestone_of(repo, subject) == short_key(milestone)
        return subject == milestone

    return wanted


def _record_items(
    repo: Path,
    milestone: str,
    said: str,
    items: list[OwnerItem],
    conn: sqlite3.Connection,
    project: int,
) -> None:
    """The verdict's items open; this milestone's earlier ones a rerun cleared, resolved."""
    at = _now()
    metrics.upsert_milestone(conn, project, milestone, verdict=said)
    for item in items:
        metrics.upsert_owner_item(
            conn, project, item.kind, item.subject, text=item.text, command=item.command, created=at
        )
    current = {(item.kind, item.subject) for item in items}
    cleared = _cleared_by_rerun(repo, milestone)
    _resolve(
        conn,
        project,
        lambda kind, subject: (kind, subject) not in current and cleared(kind, subject),
    )


def _resolve(conn: sqlite3.Connection, project: int, wanted: Callable[[str, str], bool]) -> None:
    at = _now()
    for row in metrics.open_owner_items(conn, project):
        if wanted(row["kind"], row["subject"]):
            metrics.resolve_owner_item(conn, row["id"], at)


def rerun_started(repo: Path, milestone: str, db: Path | None = None) -> None:
    """``runner milestone <key>`` is starting: the milestone's items a rerun answers are
    resolved now, not at its verdict (f1 D8, amended); the verdict reopens what still applies."""
    _write(
        repo, db, lambda conn, project: _resolve(conn, project, _cleared_by_rerun(repo, milestone))
    )


def verdict(
    repo: Path, milestone: str, state: State, review_stop: str, db: Path | None = None
) -> tuple[int, str]:
    """The last thing ``runner milestone`` prints, and its exit code: 0 ready, 2 needs you.
    With a metrics ``db``, its items become owner items there (f1 D8)."""
    items = owner_items(repo, milestone, state, review_stop)
    ready = [
        t
        for t in load_dir(repo / ".factory" / "tasks" / "ready", 1000)
        if short_key(t.milestone) == short_key(milestone)
    ]
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
        path = repo / ".factory" / "tasks" / "blocked" / f"{task_id}.md"
        reason = footer_fields(path.read_text(encoding="utf-8")).get("reason", "see its logs")
        needs.append(f"  • {task_id} blocked: {reason}")
    needs += [f"  • {text}" for _, text in _reserve_waits(repo, state, milestone)]
    if review_stop.startswith(WAITS):  # another milestone's sign-off (ADR 17 item 4)
        needs.append(f"  • {milestone} {review_stop}")
    elif _needs_owner(review_stop):
        needs.append(f"  • review stopped: {review_stop}")
    if needs:
        lines = ["⚠ NEEDS YOU", *needs, ""]
        rerun = f"uv run runner milestone {command_arg(milestone)}"
        lines.append(f"  Next: decide the above, then rerun  {rerun}")
        _write(
            repo,
            db,
            lambda conn, project: _record_items(repo, milestone, "needs you", items, conn, project),
        )
        return 2, "\n".join(lines) + "\n"
    review = milestone_file(repo, "reviews", milestone)
    lines = ["✅ READY FOR SIGN-OFF", f"  Review: {review.relative_to(repo)} ({review_stop})"]
    match = _TEST_STEPS.search(review.read_text(encoding="utf-8")) if review.is_file() else None
    steps = match.group(1).strip() if match else ""
    if steps:
        lines.append("  Test on your devices:")
        lines += [f"    {line}" for line in steps.splitlines()]
    signoff_command = f"uv run runner signoff {command_arg(milestone)}"
    lines += ["", f"  Then: {signoff_command}"]
    text = f"Test on your devices:\n{steps}" if steps else f"Review: {review.relative_to(repo)}"
    items.append(OwnerItem("signoff", milestone, text, signoff_command))
    _write(
        repo,
        db,
        lambda conn, project: _record_items(repo, milestone, "ready", items, conn, project),
    )
    return 0, "\n".join(lines) + "\n"


def record_verdict(repo: Path, text: str) -> Path | None:
    """Append the verdict to the latest session report and commit it."""
    reports = sorted((repo / ".factory" / "sessions").glob("*.md"))
    if not reports:
        return None
    with reports[-1].open("a", encoding="utf-8") as fh:
        fh.write(f"\n## Verdict\n\n```\n{text}```\n")
    Git(repo).commit_all(
        with_trailers("runner: milestone verdict", agent="runner"), author=RUNNER_AUTHOR
    )
    return reports[-1]


def _signed_doc(doc: Path, status: str) -> str:
    """The milestone doc with its status line done. A planning-room card has a State line
    instead (``> **State:** ready · …``): its state becomes done, and the status line goes
    under it (2026-10-08: F41 and F55 couldn't be signed off)."""
    text = doc.read_text(encoding="utf-8")
    if _STATUS_MILESTONE.search(text):
        return _STATUS_MILESTONE.sub(lambda _: status, text, count=1)
    if (found := _CARD_STATE_LINE.search(text)) is None:
        raise OwnerError(f"no status line in {doc}")
    line = re.sub(r"(\*\*State:\*\*\s*)[^·\n]*?(\s*(?:·|$))", r"\1done\2", found[0], count=1)
    return f"{text[: found.start()]}{line}\n{status}{text[found.end() :]}"


def _signed_review(review: Path, line: str) -> str:
    """The review with its status line done; a review written without one (the sign-off
    sheet first) gets it under its title."""
    text = review.read_text(encoding="utf-8")
    if _STATUS_LINE.search(text):
        return _STATUS_LINE.sub(lambda _: line, text, count=1)
    title, newline, rest = text.partition("\n")
    return f"{title}\n\n{line}\n{rest}" if newline else f"{title}\n\n{line}\n"


def _replace_line(path: Path, pattern: re.Pattern[str], line: str) -> None:
    text = path.read_text(encoding="utf-8")
    if not pattern.search(text):
        raise OwnerError(f"no status line in {path}")
    path.write_text(pattern.sub(line, text, count=1), encoding="utf-8")


_MILESTONE_KINDS = ("signoff", "review-stop")  # items whose subject is a milestone key


def _signed_off(
    milestone: str,
    score: int | None,
    sheet: dict[str, str],
    conn: sqlite3.Connection,
    project: int,
) -> None:
    metrics.upsert_milestone(
        conn,
        project,
        milestone,
        status="done",
        ended=_now(),
        owner_score=score,
        signoff=sheet or None,
    )
    # every item about the milestone: its sign-off, and a review stop the owner has settled.
    # Other kinds name a ticket, not a milestone key (f8-03's reserve item broke F7's, f7-F2).
    _resolve(
        conn,
        project,
        lambda kind, subject: (
            kind in _MILESTONE_KINDS and short_key(subject) == short_key(milestone)
        ),
    )


def signoff(
    repo: Path,
    milestone: str,
    today: date,
    force: bool = False,
    db: Path | None = None,
    score: int | None = None,
) -> None:
    """Mark a milestone done: its doc and review, the ``<key>-done`` tag, one commit. With a
    metrics ``db``, the milestone's row is done and its sign-off item resolved. The owner's
    optional ``score`` (1-10, ADR 14 item 14) is how the result felt on the devices."""
    if score is not None and not 1 <= score <= 10:
        raise OwnerError(f"a score is 1 to 10, not {score}")
    left = [f"{t} ({f})" for f in _UNFINISHED for t in _ids(repo, f, milestone)]
    if left and not force:
        raise OwnerError(
            "work is left: " + ", ".join(left) + ". Finish it, or sign off with --force."
        )
    doc = milestone_file(repo, "cards", milestone)
    review = milestone_file(repo, "reviews", milestone)
    status = (
        f"> **Status: done.** Signed off by the owner on {today.isoformat()}."
        f" Base: git tag `{milestone}-start`."
        f" Report: [`.factory/reviews/{review.name}`](../reviews/{review.name})."
    )
    # Both files are checked before either is written: a refusal leaves no half sign-off
    new_doc = _signed_doc(doc, status)
    sheet = signoff_sections(review.read_text(encoding="utf-8")) if review.is_file() else {}
    new_review = (
        _signed_review(review, f"- **Status:** done, signed off by the owner on {today}.")
        if review.is_file()
        else None
    )
    doc.write_text(new_doc, encoding="utf-8")
    if new_review is not None:
        review.write_text(new_review, encoding="utf-8")
    git = Git(repo)
    git.commit_all(f"{milestone.upper()} signed off by the owner")
    git.run("tag", f"{milestone}-done")
    _write(repo, db, lambda conn, project: _signed_off(milestone, score, sheet, conn, project))


def _is_adr(number: int) -> Callable[[str, str], bool]:
    def wanted(kind: str, subject: str) -> bool:
        found = _ADR_NUMBER.search(subject)
        return kind == "adr" and found is not None and int(found[1]) == number

    return wanted


def decide_adr(repo: Path, number: int, status: str, today: date, db: Path | None = None) -> Path:
    """Set ADR N's status ("Accepted" or "Rejected") with the date, in one commit. With a
    metrics ``db``, the owner items asking about it are resolved."""
    found = sorted((repo / ".factory" / "adr").glob(f"{number:02d}-*.md"))
    if not found:
        raise OwnerError(f"ADR {number} not found in .factory/adr/")
    _replace_line(
        found[0], _STATUS_LINE, f"- **Status:** {status} (by the owner, {today.isoformat()})"
    )
    Git(repo).commit_all(f"ADR {number} {status.lower()} by the owner")
    _write(repo, db, lambda conn, project: _resolve(conn, project, _is_adr(number)))
    return found[0]
