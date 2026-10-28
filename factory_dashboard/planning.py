"""The planning room's desk (f6-06, F6 D6): ``/planning`` is the owner's desk.

- Two tiles: the factory now, with when the next reply is expected (planner jobs go first, so a
  pending message is answered once the running job is done, D1), and the lead's 5-hour window.
- ``desk(conn, project)``: what waits for the owner, in six groups (D6, and F31 D9's "Didn't go
  through" first); the Overview's Needs you and the top bar's count reuse its items' words and
  links (f6-09).
- "Plant an idea": a ``plant`` request through ``POST /requests``, the dashboard's only write.
"""

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from factory_dashboard.app import Db, Now, Project, ago, render
from factory_dashboard.coming import (
    GENERAL,
    DeskGroup,
    DeskItem,
    _acted_on,
    _card_titles,
    _held,
    _next_reply,
    _refused,
    _thread_title,
    _when,
    _writing,
    coming,
    reply_line,
)
from factory_dashboard.line import live_line
from factory_dashboard.merges import (
    _gone_merge,
    _known_cards,
    _merge_words,
)
from factory_dashboard.overview import (
    agent_allowances,
    running_jobs,
)
from runner import metrics
from runner.planner import (
    APPLIED,
    MERGE,
    ON_ITS_WAY,
    OPEN,
    PLANNER,
    PlannerError,
    is_proposed,
    merge_cards,
    proposal_state,
    thread_name,
)
from runner.tasks import (
    short_key,
)

router = APIRouter()

_ADR_NUMBER = re.compile(r"\.factory/adr/(\d+)-")
_NEXT_PICK = "on its way · the runner applies it at its next pick"


def _answers_wanted(
    conn: sqlite3.Connection, project_id: int, titles: dict[str, str], now: datetime
) -> list[DeskItem]:
    """Threads whose last message is the lead's: a reply the owner hasn't answered. An
    archived thread waits for nothing."""
    rows = conn.execute(
        "SELECT t.card, m.at FROM planner_threads t"
        " JOIN planner_messages m ON m.id = ("
        "   SELECT max(id) FROM planner_messages WHERE thread_id = t.id)"
        " WHERE t.project_id = ? AND m.author = 'lead' AND t.archived IS NULL ORDER BY m.id",
        (project_id,),
    ).fetchall()
    # a thread the owner answered, whose reply isn't written yet, waits for nothing (F51 D4)
    answered = {
        r["subject"]
        for r in conn.execute(
            "SELECT subject FROM owner_requests"
            " WHERE project_id = ? AND kind = 'plan_message' AND done IS NULL",
            (project_id,),
        ).fetchall()
    }
    rows = [r for r in rows if r["card"] not in answered]
    return [
        DeskItem(
            "answers",
            _thread_title(r["card"], titles),
            f"the lead replied {ago(now - _when(r['at']))} ago",
            f"/planning/{r['card']}",
        )
        for r in rows
    ]


def _part_name(proposal: dict[str, object]) -> str:
    """A proposal's short name on a card's desk item: ``ADR 27``, ``plan``, ``merge F34``."""
    kind = str(proposal.get("kind") or "proposal")
    if kind == "adr":
        number = _ADR_NUMBER.match(str(proposal.get("path") or ""))
        return f"ADR {int(number[1])}" if number else "ADR"
    if kind == MERGE:
        try:
            return f"merge {thread_name(merge_cards(proposal)[0])}"
        except PlannerError:
            return "merge"
    return "mock-up" if kind == "mockup" else kind


def _bundle(
    card: str,
    parts: list[tuple[dict[str, object], str]],
    repo: Path | None,
) -> DeskItem:
    """A card's open proposals as one desk item (F51 D1): the plan's title, the parts in the
    order they are settled (ADR first), the link to the first still to do."""
    parts = sorted(parts, key=lambda p: p[0].get("kind") != "adr")  # stable: ADR first
    leading = next((p for p, _ in parts if p.get("kind") in ("plan", "replan")), parts[0][0])
    total = sum(len(points) for p, _ in parts if isinstance(points := p.get("key_points"), list))
    words = f"{total} key points" if total else ""
    if len(parts) == 1 and (merged := _merge_words(parts[0][0])):  # a merge alone says what joins
        words = f"{merged} · {words}" if words else merged
    adr_open = any(p.get("kind") == "adr" and state == OPEN for p, state in parts)
    if repo is not None and adr_open and _adr_waits(repo, [p for p, _ in parts]):
        words = f"{words} · accept the ADR first" if words else "accept the ADR first"
    todo = next((p for p, state in parts if state == OPEN), None)
    on_its_way = todo is None
    shown = parts[0][0] if todo is None else todo
    title = str(leading.get("title") or leading["id"])
    name = thread_name(card)
    if not re.match(rf"{re.escape(name)}\b", title, re.IGNORECASE):  # "F82: …" names it already
        title = f"{name}: {title}"
    return DeskItem(
        "proposals",
        title,
        _NEXT_PICK if on_its_way else words or str(shown.get("kind") or ""),
        f"/planning/{card}/proposals/{shown['id']}",
        on_its_way=on_its_way,
        parts=tuple((_part_name(p), state == ON_ITS_WAY) for p, state in parts),
    )


def _open_proposals(
    conn: sqlite3.Connection,
    project_id: int,
    known: set[str] | None = None,
    repo: Path | None = None,
) -> list[DeskItem]:
    """The proposals in each thread's latest lead message that lists some, still open, on
    threads not archived. A card's make one item (F51 D1); the general thread's, one each."""
    rows = conn.execute(
        "SELECT t.card, m.at, m.proposals FROM planner_threads t"
        " JOIN planner_messages m ON m.id = ("
        "   SELECT max(id) FROM planner_messages WHERE thread_id = t.id AND author = 'lead'"
        "   AND proposals IS NOT NULL AND proposals != '[]')"
        " WHERE t.project_id = ? AND t.archived IS NULL ORDER BY m.id",
        (project_id,),
    ).fetchall()
    requests = conn.execute(
        "SELECT * FROM owner_requests WHERE project_id = ? ORDER BY id", (project_id,)
    ).fetchall()
    items = []
    for row in rows:
        since = _when(row["at"])
        later = [r for r in requests if _when(r["created"]) > since]
        card_parts: list[tuple[dict[str, object], str]] = []
        for proposal in json.loads(row["proposals"]):
            if not isinstance(proposal, dict) or not proposal.get("id"):
                continue
            if proposal.get(APPLIED) or _gone_merge(proposal, known):
                continue
            state = proposal_state(proposal, row["card"], later)
            if state not in (OPEN, ON_ITS_WAY):
                continue
            if row["card"] != GENERAL:
                card_parts.append((proposal, state))
                continue
            points = proposal.get("key_points")
            words = f"{len(points)} key points" if isinstance(points, list) and points else ""
            if merged := _merge_words(proposal):
                words = f"{merged} · {words}" if words else merged
            items.append(
                DeskItem(
                    "proposals",
                    str(proposal.get("title") or proposal["id"]),
                    _NEXT_PICK if state == ON_ITS_WAY else words or str(proposal.get("kind") or ""),
                    f"/planning/{row['card']}/proposals/{proposal['id']}",
                    on_its_way=state == ON_ITS_WAY,
                )
            )
        if card_parts:
            items.append(_bundle(row["card"], card_parts, repo))
    return items


def _ripe(conn: sqlite3.Connection, project: str, now: datetime) -> list[DeskItem]:
    """Every ticket done, its review written, and not signed off, as the line's field has
    them (F50 D1)."""
    return [
        DeskItem(
            "ripe",
            m["title"] or m["key"],
            "reviewed · waits for your sign-off",
            f"/planning/{short_key(m['key'])}",
        )
        for m in live_line(conn, project, now)["field"]["ripe"]
    ]


def _seeds(conn: sqlite3.Connection, project_id: int) -> list[DeskItem]:
    """Idea cards no thread is about yet."""
    threads = {
        r["card"]
        for r in conn.execute(
            "SELECT card FROM planner_threads WHERE project_id = ?", (project_id,)
        ).fetchall()
    }
    rows = conn.execute(
        "SELECT key, title FROM milestones WHERE project_id = ? AND state = 'idea' ORDER BY id",
        (project_id,),
    ).fetchall()
    return [
        DeskItem("seeds", r["title"] or r["key"], "an idea, not asked about yet", f"/planning/{k}")
        for r in rows
        if (k := short_key(r["key"])) not in threads
    ]


def _blocked(conn: sqlite3.Connection, project_id: int) -> list[DeskItem]:
    """Open blocked tickets with their reason: one plain DeskItem per row, oldest first.

    If the runner has a look on the card's thread and the lead has since replied, the words
    say where the fix waits. If the runner has a look but the lead hasn't yet, the words say
    the lead is looking. A bug ticket with no card gets nothing extra.
    """
    rows = conn.execute(
        "SELECT subject, text FROM owner_items"
        " WHERE project_id = ? AND kind = ? AND resolved IS NULL"
        " ORDER BY created, id",
        (project_id, "blocked"),
    ).fetchall()
    items: list[DeskItem] = []
    for r in rows:
        prefix = f"{r['subject']} blocked: "
        words = r["text"][len(prefix) :] if r["text"].startswith(prefix) else r["text"]
        ticket = r["subject"]
        # Find the latest runner message starting with "<ticket> blocked:" on this project
        runner = conn.execute(
            "SELECT m.at, t.card FROM planner_messages m"
            " JOIN planner_threads t ON t.id = m.thread_id"
            " WHERE t.project_id = ? AND m.author = 'runner'"
            " AND m.text LIKE ?"
            " ORDER BY m.at DESC LIMIT 1",
            (project_id, f"{ticket} blocked:%"),
        ).fetchone()
        if runner is not None:
            runner_at = runner["at"]
            card = runner["card"]
            # Check for a lead message after the runner's on the same thread
            lead = conn.execute(
                "SELECT max(id) FROM planner_messages"
                " WHERE thread_id = ("
                "   SELECT id FROM planner_threads"
                "   WHERE project_id = ? AND card = ?)"
                " AND author = 'lead' AND at > ?",
                (project_id, card, runner_at),
            ).fetchone()
            if lead["max(id)"] is not None:
                words = f"{words} · the lead's fix waits on {card.upper()}'s thread"
            else:
                words = f"{words} · the lead is looking at it"
        items.append(DeskItem("blocked", ticket, words, f"/tickets/{ticket}"))
    return items


def archived(conn: sqlite3.Connection, project: str, now: datetime) -> list[DeskItem]:
    """The archived threads, the most recently archived first (the owner, 2026-10-07). A
    message from the owner opens one again."""
    project_id = metrics.find_project(conn, project)
    if project_id is None:
        return []
    titles = _card_titles(conn, project_id)
    rows = conn.execute(
        "SELECT card, archived, archived_why FROM planner_threads"
        " WHERE project_id = ? AND archived IS NOT NULL ORDER BY archived DESC, id DESC",
        (project_id,),
    ).fetchall()
    return [
        DeskItem(
            "archived",
            _thread_title(r["card"], titles),
            " · ".join(
                filter(None, [r["archived_why"], f"archived {ago(now - _when(r['archived']))} ago"])
            ),
            f"/planning/{r['card']}",
        )
        for r in rows
    ]


def waiting_for_you(groups: list[DeskGroup]) -> list[DeskItem]:
    """The desk's items still waiting for the owner, in desk order: the Planning tab's count,
    Overview's Needs you and the arrows between pages (F35) read these."""
    return [item for group in groups for item in group.items if not item.on_its_way]


def desk_trail(
    conn: sqlite3.Connection, project: str, now: datetime, path: str
) -> dict[str, object]:
    """F35, the owner's Previous and Next between what waits for them: the pages of the desk's
    items still waiting, in desk order (what didn't go through stays on /planning). On one of
    them, its neighbours; on a page already done with, the first one left."""
    links = list(
        dict.fromkeys(
            item.link
            for item in waiting_for_you(desk(conn, project, now))
            if item.link.startswith("/planning/")
        )
    )
    if path in links:
        at = links.index(path)
        return {
            "previous": links[at - 1] if at > 0 else None,
            "next": links[at + 1] if at + 1 < len(links) else None,
            "words": f"{at + 1} of {len(links)} waiting for you",
        }
    return {
        "previous": None,
        "next": links[0] if links else None,
        "words": f"{len(links)} waiting for you" if links else "Nothing else waits for you",
    }


def desk(conn: sqlite3.Connection, project: str, now: datetime) -> list[DeskGroup]:
    """What waits for the owner (D6), in six groups in this order, empty ones included: what
    didn't go through first (F31 D9), blocked tickets (F106 D1), sign-offs, proposals,
    conversations, and seeds."""
    project_id = metrics.find_project(conn, project)
    if project_id is None:
        refusals: list[DeskItem] = []
        ripe: list[DeskItem] = []
        proposals: list[DeskItem] = []
        answers: list[DeskItem] = []
        seeds: list[DeskItem] = []
        blocked: list[DeskItem] = []
    else:
        titles = _card_titles(conn, project_id)
        refusals = _refused(conn, project_id, titles)
        repo = _repo(conn, project)
        ripe = _acted_on(conn, project_id, _ripe(conn, project, now))
        proposals = _open_proposals(conn, project_id, _known_cards(repo), repo)
        answers = _acted_on(conn, project_id, _answers_wanted(conn, project_id, titles, now))
        seeds = _acted_on(conn, project_id, _seeds(conn, project_id))
        blocked = _acted_on(conn, project_id, _blocked(conn, project_id))
    return [
        DeskGroup("refused", "Didn't go through", "--hazard", refusals),
        DeskGroup("blocked", "Blocked tickets", "--hazard", blocked),
        DeskGroup("ripe", "To sign off", "--qwen", ripe),
        DeskGroup("proposals", "Proposals to review", "--opus", proposals),
        DeskGroup("answers", "Your answers wanted", "--hazard", answers),
        DeskGroup("seeds", "Seeds, not asked about yet", "--ink-2", seeds),
    ]


# --- the tiles ----------------------------------------------------------------------------


def factory_now(conn: sqlite3.Connection, project: str, now: datetime) -> dict[str, object]:
    """The tile: the running job, the reply being written and the replies in line after it
    (F84 D6), or when the next reply is expected."""
    jobs = [j for j in running_jobs(conn, project, now) if j.live]
    project_id = metrics.find_project(conn, project)
    pending = project_id is not None and any(
        r["kind"] == PLANNER for r in metrics.open_jobs(conn, project_id)
    )
    working = [j for j in jobs if j.role != PLANNER]
    places = reply_line(conn, project, now, jobs)
    thread = _writing(places)
    writing: dict[str, object] | None = None
    if thread is not None and project_id is not None:
        line = [p for p in places.values() if p.place > 0]
        ends = [p.done for p in line if p.done is not None]
        writing = {
            "thread": thread,
            "title": _thread_title(thread, _card_titles(conn, project_id)),
            "elapsed": places[thread].elapsed,
            "count": len(line),
            "all": max(ends) if line and len(ends) == len(line) else None,
        }
    return {
        "running": working[0] if working else None,
        "writing": writing,
        "next_reply": _next_reply(
            conn, project, jobs, pending, _held(conn, project_id, now), thread
        ),
    }


@router.get("/planning", response_class=HTMLResponse)
def planning(request: Request, conn: Db, project: Project, now: Now) -> HTMLResponse:
    """The owner's desk: the two tiles, what waits for the owner, and Plant an idea."""
    window = next(
        (a for a in agent_allowances(conn, now) if a.label == "Claude" and a.window == "five_hour"),
        None,
    )
    week = next(
        (a for a in agent_allowances(conn, now) if a.label == "Claude" and a.window == "seven_day"),
        None,
    )
    c = coming(conn, project, now)
    return render(
        request,
        conn,
        project,
        "planning.html",
        {
            "active": "/planning",
            "factory": factory_now(conn, project, now),
            "window": window,
            "week": week,
            "coming": c,
            "groups": desk(conn, project, now),
            "archived": archived(conn, project, now),
        },
    )


# --- proposal review (f6-08) ----------------------------------------------------------------

_MOCKUP_RE = re.compile(r"\.factory/cards/[^/]+-mockup/[^/].*")
# Old mock-up path: ``docs/milestones/<name>-mockup/<file>`` (ADR 30's move).
_OLD_MOCKUP_RE = re.compile(r"^docs/milestones/([^/]+)-mockup/(.+)$")


def _resolve_mockup_path(path: str) -> str | None:
    """Convert an old mock-up path to the new format, or return it unchanged.

    Returns ``None`` when the path doesn't match either the old or new pattern.
    """
    if _MOCKUP_RE.fullmatch(path):
        return path
    match = _OLD_MOCKUP_RE.fullmatch(path)
    if match:
        return f".factory/cards/{match.group(1)}-mockup/{match.group(2)}"
    return None


def _repo(conn: sqlite3.Connection, project: str) -> Path | None:
    """The project's checkout; None when ``projects.repo`` isn't a folder here (a URL)."""
    row = conn.execute("SELECT repo FROM projects WHERE name = ?", (project,)).fetchone()
    repo = Path(row["repo"]) if row and row["repo"] else None
    return repo if repo and repo.is_dir() else None


def _adr_waits(
    repo: Path | None, proposals: list[dict[str, object]], accepting: frozenset[int] = frozenset()
) -> bool:
    """Whether the card has an ``adr`` proposal whose file on main is missing or still Proposed
    (as ``runner.requests`` reads it): Approve plan waits for it. An ADR in ``accepting`` has an
    open ``accept_adr`` request, which the runner applies before a later approval (F51 D2)."""
    for p in proposals:
        if p.get("kind") != "adr":
            continue
        number = _ADR_NUMBER.match(str(p.get("path") or ""))
        if number and int(number[1]) in accepting:
            continue
        found = (
            sorted((repo / ".factory" / "adr").glob(f"{number[1]}-*.md")) if repo and number else []
        )
        if not found or is_proposed(found[0].read_text(encoding="utf-8")):
            return True
    return False
