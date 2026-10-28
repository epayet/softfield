"""Merge links (f109-01): a merged card's links both ways, "merged on", and a message's paths as
links. Imports neither page: the thread page and the desk import from here."""

import contextlib
import re
import sqlite3
from collections.abc import Callable
from pathlib import Path
from typing import Any

from runner.milestone import milestone_doc
from runner.planner import MERGE, PlannerError, cards, merge_cards, merge_words
from runner.tasks import TaskError, milestone_key, short_key

# Merge heading written by ``planner.merged_card``: captures source key, title and date.
_MERGE_HEADING_RE = re.compile(
    r"^#{3,} From ([A-Z]+\d+): (.+?) "
    r"\(merged by the (?:lead|owner) on (\d{4}-\d{2}-\d{2})\)[ \t]*$",
    re.MULTILINE,
)
# Path like /planning/f95 in plain text: escape first, then link.
_PLANNING_PATH_RE = re.compile(r"/planning/([a-z][a-z0-9-]+)")


def _merge_words(proposal: dict[str, object]) -> str | None:
    """A ``merge`` proposal in words, ``merge F12 into F10``; None for another kind."""
    if proposal.get("kind") != MERGE:
        return None
    try:
        return merge_words(proposal)
    except PlannerError:
        return None


def _known_cards(repo: Path | None) -> set[str] | None:
    """Every card on main, or None when the checkout isn't here."""
    return None if repo is None else cards(repo)


def _merge_links(
    repo: Path | None, thread: str
) -> tuple[list[dict[str, str]], list[dict[str, str]], str | None]:
    """Read merge headings from card docs on main.

    Returns ``(merged_into, merged_here, latest_title)``:
    - ``merged_into``: links from this thread to cards it was merged into
    - ``merged_here``: links from this thread to cards merged into it
    - ``latest_title``: the title from the latest merge heading referencing this thread
    """
    if repo is None:
        return [], [], None

    merged_into: list[dict[str, str]] = []
    merged_here: list[dict[str, str]] = []
    source_key = thread.upper()
    latest_title: str | None = None
    latest_date: str = ""

    cards_dir = repo / ".factory" / "cards"
    if not cards_dir.is_dir():
        return [], [], None

    for path in cards_dir.glob("*.md"):
        try:
            doc = path.read_text(encoding="utf-8")
        except OSError:
            continue

        card_key: str | None = None
        with contextlib.suppress(TaskError):  # a card file not named by a key
            card_key = short_key(milestone_key(path.stem))
        # "Merged into F95, <title>" names the kept card by its own title, not the merged one's
        card_title = milestone_doc(doc).get("title") or (card_key or "").upper()

        for match in _MERGE_HEADING_RE.finditer(doc):
            ref_key = match.group(1)
            title = match.group(2).strip()
            date = match.group(3)

            if ref_key == source_key:
                if card_key is not None:
                    merged_into.append(
                        {
                            "key": card_key,
                            "title": card_title,
                            "date": date,
                            "link": f"/planning/{card_key}",
                        }
                    )
                # Track the latest heading title for this source
                if date > latest_date:
                    latest_date = date
                    latest_title = title

            if card_key is not None and card_key == thread:
                merged_here.append(
                    {
                        "key": ref_key.lower(),
                        "title": title,
                        "date": date,
                        "link": f"/planning/{ref_key.lower()}",
                    }
                )

    return merged_into, merged_here, latest_title


def _gone_merge(proposal: dict[str, object], known: set[str] | None) -> bool:
    """A ``merge`` one of whose cards has left main: merged or dropped already, nothing to
    ask (2026-10-08: such merges filled the desk)."""
    if proposal.get("kind") != MERGE or known is None:
        return False
    try:
        return not set(merge_cards(proposal)) <= known
    except PlannerError:
        return False


def _text_with_links(text: str, q: str = "") -> str:
    """Escape ``text`` then turn ``/planning/<key>`` into links, keeping ``q`` (the page's
    ``?project=``). The text is a lead's plain line: the owner's messages stay as plain text."""
    escaped = (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )
    href = q.replace("&", "&amp;")
    return _PLANNING_PATH_RE.sub(
        lambda m: f'<a href="/planning/{m[1]}{href}">/planning/{m[1]}</a>', escaped
    )


def _merged_on(
    conn: sqlite3.Connection,
    project_id: int | None,
    thread: str,
    merged_into: list[dict[str, str]],
    known: set[str] | None,
    open_proposals: Callable[[], list[Any]],
) -> list[dict[str, object]]:
    """Merged-on blocks for a merged-away card's thread page.

    Returns one entry per kept card (most recent merge first), with open
    proposals and ticket counts. Only when the thread key is not in known
    (the card was merged away) and merged_into is non-empty. ``open_proposals`` gives the
    desk's open proposals (the desk's own rule, so this module needn't import it).
    """
    if project_id is None or not merged_into or known is None or thread in known:
        return []

    # Sort by date descending (most recent first)
    sorted_cards = sorted(merged_into, key=lambda m: m["date"], reverse=True)

    all_open = open_proposals()
    result: list[dict[str, object]] = []

    for card in sorted_cards:
        kept_key = card["key"]
        # Open proposals for this kept card's thread
        card_proposals = [
            p for p in all_open if p.link.startswith(f"/planning/{kept_key}/proposals/")
        ]
        # Tickets for this kept card
        milestone_rows = conn.execute(
            "SELECT m.key, m.id, t.state FROM milestones m"
            " JOIN tickets t ON t.milestone_id = m.id"
            " WHERE m.project_id = ? AND m.key LIKE ?"
            " AND t.state NOT IN ('later', 'removed')"
            " ORDER BY m.id",
            (project_id, f"{kept_key.upper()}-%"),
        ).fetchall()
        # N and M over the same rows: every milestone of the kept card (a replan has two)
        milestone = milestone_rows[0] if milestone_rows else None
        ticket_count = len(milestone_rows)
        done_count = sum(1 for row in milestone_rows if row["state"] == "done")
        card_data: dict[str, object] = {
            "key": kept_key,
            "title": card["title"],
            "date": card["date"],
            "link": card["link"],
            "proposals": card_proposals,
        }
        if milestone:
            card_data["milestone_key"] = milestone["key"]
            card_data["ticket_count"] = ticket_count
            card_data["done_count"] = done_count
        result.append(card_data)

    return result
