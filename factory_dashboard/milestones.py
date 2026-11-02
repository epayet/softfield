"""The Milestones list page (f1-12, D8), with trends across them.

One row per milestone: key (a link to ``/milestones/{key}``), title, status, dates,
tickets merged, first-attempt pass rate, escalations, review rounds, Claude dollars,
net savings. Trends below: first-attempt rate, escalations, Claude dollars per merged
ticket and savings per milestone, as small charts (D5). The list has no tab since the board
(f5-17): the board links to it.

``/milestones/{key}`` is the milestone's card's page (f5-17, after
``.softfield/cards/f5-board-mockup/Card.dc.html``): its stage on the board, priority and area,
how far it has grown, then what the page showed before, its tickets now in run order.
"""

import contextlib
import json
import re
import sqlite3
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from factory_dashboard import queries
from factory_dashboard.app import Db, Now, Project, render
from factory_dashboard.board import RESERVABLE, STAGES, WORDS, Card, milestone_card
from factory_dashboard.line import _natural
from runner import metrics
from runner.milestone import milestone_doc
from runner.requests import RESERVE
from runner.tasks import full_key, milestone_file, short_key

router = APIRouter()


@dataclass(frozen=True)
class AboutDoc:
    """The card page's "What it's about" (F158 D1): Outcome and Done when as HTML, and the
    owner's note as plain text."""

    outcome_html: str
    done_when_html: str
    note: str


@dataclass(frozen=True)
class Idea:
    """One idea from a review's sign-off sheet (D1, D2, D3)."""

    id: str
    text: str
    area: str  # "product" or "factory"
    project: str  # where it plants
    state: str  # "plant", "on its way", "planted", "refused"
    card: str | None  # the planted card's short key, else None
    said: str | None  # a refusal's words, else None


def read_card_doc(repo: Path | None, thread: str) -> AboutDoc | None:
    """The card's Outcome, Done when and note from its doc in ``.softfield/cards/``;
    None when there is no checkout or no doc."""
    # thread imports this module
    from factory_dashboard.thread import _note

    if repo is None:
        return None
    try:
        text = milestone_file(repo, "cards", full_key(repo, thread)).read_text(encoding="utf-8")
    except OSError:
        return None
    doc = milestone_doc(text)
    note = _note(repo, thread)
    if doc.get("outcome") is None and doc.get("done_when") is None and not note:
        return None
    return AboutDoc(
        outcome_html=_to_html(doc.get("outcome")),
        done_when_html=_to_html(doc.get("done_when")),
        note=note,
    )


@dataclass(frozen=True)
class MilestoneRow:
    key: str
    title: str | None
    status: str | None
    started: str | None
    ended: str | None
    tickets: int
    merged: int
    pass_rate: float | None
    escalations: int
    review_rounds: int
    claude_dollars: float
    net_savings: float
    priority: int | None = None  # a card not done's (f6-18)


UNMOVED = (None, "done", "removed")  # card states without a priority to change


def _with_priorities(
    conn: sqlite3.Connection, project: str, rows: list[MilestoneRow]
) -> list[MilestoneRow]:
    """Each card not done with its priority; the others keep none."""
    cards = {
        row["key"]: row["priority"]
        for row in conn.execute(
            "SELECT m.key, m.state, m.status, m.priority FROM milestones m"
            " JOIN projects p ON p.id = m.project_id WHERE p.name = ?",
            (project,),
        )
        if row["state"] not in UNMOVED and row["status"] != "done" and row["priority"] is not None
    }
    return [replace(r, priority=cards[r.key]) if r.key in cards else r for r in rows]


def milestone_rows(conn: sqlite3.Connection, project: str) -> list[MilestoneRow]:
    """Every milestone's summary, grouped and sorted: in progress first (by latest job),
    then not started (by priority), then done (by end date)."""
    # Lookup table for milestone status and dates.
    milestone_meta = conn.execute(
        "SELECT m.key, m.status, m.started, m.ended, m.id, m.state FROM milestones m"
        " JOIN projects p ON p.id = m.project_id WHERE p.name = ?",
        (project,),
    ).fetchall()
    meta: dict[str, dict[str, str | None]] = {}
    milestone_ids: dict[str, int] = {}
    for row in milestone_meta:
        meta[row["key"]] = {
            "status": row["status"],
            "started": row["started"],
            "ended": row["ended"],
            "state": row["state"],
        }
        milestone_ids[row["key"]] = row["id"]

    # Latest job start time per milestone.
    latest_jobs: dict[int, str | None] = {}
    for row in conn.execute(
        "SELECT milestone_id, MAX(started) as latest_started FROM jobs"
        " WHERE milestone_id IS NOT NULL GROUP BY milestone_id",
    ):
        latest_jobs[row["milestone_id"]] = row["latest_started"]

    # Group milestone keys by status.
    in_progress_keys: list[str] = []
    not_started_keys: list[str] = []
    done_keys: list[str] = []
    for row in milestone_meta:
        key = row["key"]
        mid = row["id"]
        status = row["status"]
        if status == "done":
            done_keys.append(key)
        elif latest_jobs.get(mid):
            in_progress_keys.append(key)
        else:
            not_started_keys.append(key)

    # Milestones with data from trends.
    with_data: list[MilestoneRow] = []
    for trend in queries.trends(conn, project):
        r = trend.results
        s = trend.savings
        if r.merged == 0:
            continue
        info = meta.get(r.key, {})
        with_data.append(
            MilestoneRow(
                key=r.key,
                title=r.title,
                status=info.get("status"),
                started=info.get("started"),
                ended=info.get("ended"),
                tickets=r.tickets,
                merged=r.merged,
                pass_rate=r.pass_rate,
                escalations=r.escalations,
                review_rounds=r.review_rounds,
                claude_dollars=r.claude.dollars,
                net_savings=s.net,
            )
        )

    # Milestones without tickets (from the DB).
    no_data = conn.execute(
        "SELECT m.key, m.title, m.status, m.started, m.ended FROM milestones m"
        " JOIN projects p ON p.id = m.project_id WHERE p.name = ?"
        " ORDER BY m.key",
        (project,),
    ).fetchall()
    seen = {row.key for row in with_data}
    no_data_rows: list[MilestoneRow] = []
    for m in no_data:
        if m["key"] not in seen:
            info = meta.get(m["key"], {})
            mid = milestone_ids.get(m["key"])
            if (
                info.get("state") is None
                and info.get("ended") is None
                and info.get("status") != "done"
                and (
                    mid is None
                    or mid
                    not in {
                        r["milestone_id"]
                        for r in conn.execute(
                            "SELECT t.milestone_id FROM tickets t"
                            " JOIN projects p ON p.id = t.project_id"
                            " WHERE p.name = ? AND t.state IS NOT ?",
                            (project, metrics.REMOVED),
                        )
                    }
                )
            ):
                continue
            no_data_rows.append(
                MilestoneRow(
                    key=m["key"],
                    title=m["title"],
                    status=m["status"],
                    started=m["started"],
                    ended=m["ended"],
                    tickets=0,
                    merged=0,
                    pass_rate=None,
                    escalations=0,
                    review_rounds=0,
                    claude_dollars=0.0,
                    net_savings=0.0,
                )
            )

    # Merge and sort: in progress → not started → done.
    all_rows: list[MilestoneRow] = [*with_data, *no_data_rows]

    def _ip_key(r: MilestoneRow) -> tuple[int, float, str]:
        mid = milestone_ids.get(r.key)
        latest = latest_jobs.get(mid) if mid else None
        if latest and isinstance(latest, str):
            ts = datetime.fromisoformat(latest).timestamp()
        else:
            ts = 0.0
        return (0, -ts, r.key)

    def _ns_key(r: MilestoneRow) -> tuple[int, int, str]:
        p = r.priority if r.priority is not None else 100
        return (1, p, r.key)

    def _done_key(r: MilestoneRow) -> tuple[int, float, str]:
        ended = r.ended
        ts = datetime.fromisoformat(ended).timestamp() if ended and isinstance(ended, str) else 0.0
        return (2, -ts, r.key)

    in_progress = [r for r in all_rows if r.key in in_progress_keys]
    not_started = [r for r in all_rows if r.key in not_started_keys]
    done = [r for r in all_rows if r.key in done_keys]

    result = (
        sorted(in_progress, key=_ip_key)
        + sorted(not_started, key=_ns_key)
        + sorted(done, key=_done_key)
    )

    return _with_priorities(conn, project, result)


def _rate_chart(conn: sqlite3.Connection, project: str) -> dict[str, Any]:
    points = [p for p in queries.trends(conn, project) if p.results.merged > 0]
    return {
        "labels": [p.results.key.upper() for p in points],
        "rate": [
            round(p.results.pass_rate * 100, 1) if p.results.pass_rate is not None else None
            for p in points
        ],
    }


def _esc_chart(conn: sqlite3.Connection, project: str) -> dict[str, Any]:
    points = [p for p in queries.trends(conn, project) if p.results.merged > 0]
    return {
        "labels": [p.results.key.upper() for p in points],
        "count": [p.results.escalations for p in points],
    }


def _dollars_chart(conn: sqlite3.Connection, project: str) -> dict[str, Any]:
    points = [p for p in queries.trends(conn, project) if p.results.merged > 0]
    return {
        "labels": [p.results.key.upper() for p in points],
        "dollars": [
            round(p.results.claude.dollars / p.results.merged, 2) if p.results.merged else None
            for p in points
        ],
    }


def _savings_chart(conn: sqlite3.Connection, project: str) -> dict[str, Any]:
    points = [p for p in queries.trends(conn, project) if p.results.merged > 0]
    return {
        "labels": [p.results.key.upper() for p in points],
        "savings": [round(p.savings.net, 2) for p in points],
    }


@router.get("/milestones", response_class=HTMLResponse)
def milestones_list(request: Request, conn: Db, project: Project, now: Now) -> HTMLResponse:
    rows = milestone_rows(conn, project)
    return render(
        request,
        conn,
        project,
        "milestones.html",
        {
            "active": "/board",  # where its link is, now it has no tab (f5-17)
            "milestones": rows,
            "rate": _rate_chart(conn, project),
            "esc": _esc_chart(conn, project),
            "dollars": _dollars_chart(conn, project),
            "savings": _savings_chart(conn, project),
        },
    )


def _to_html(text: str | None) -> str:
    """Turn ``- item`` lines into ``<ul><li>`` and ``**x**`` into ``<strong>x</strong>``,
    escaping the text first."""
    if text is None:
        return ""
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    lines = escaped.split("\n")
    html_parts: list[str] = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            item_text = stripped[2:]
            item_text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", item_text)
            html_parts.append(f"<li>{item_text}</li>")
        else:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            if stripped:
                html_parts.append(f"<p>{stripped}</p>")
    if in_list:
        html_parts.append("</ul>")
    return "".join(html_parts)


@dataclass(frozen=True)
class TicketRow:
    """A ticket on its card's page (f5-17)."""

    ticket: str
    goal: str | None
    who: str  # its last job's agent, else who will take it
    state: str  # in the page's words: "set aside", "waits for f4-04-…"
    mark: str  # the row's class: its state in the database


_WHO = {"lead": "the lead", "developer": "a developer"}
# the page's order: done, being worked on, ready (as the runner will take them), set aside
_GROUPS = {"done": 0, "running": 1, "escalated": 1, "blocked": 1, "ready": 2, "later": 4}


def ticket_rows(conn: sqlite3.Connection, project: str, milestone_id: int) -> list[TicketRow]:
    """The card's tickets in run order, each with who did or will do it and its state. The
    ready ones come as ``run_order`` has them; removed ones are left out."""
    tickets = [t for t in queries._tickets(conn, milestone_id) if t["state"] != metrics.REMOVED]
    last: dict[int, str] = {}  # each ticket's last job's agent
    for job in conn.execute(
        "SELECT j.ticket_id, j.agent FROM jobs j JOIN runs r ON r.id = j.run_id"
        " WHERE j.milestone_id = ? AND j.ticket_id IS NOT NULL AND j.agent IS NOT NULL"
        " AND coalesce(r.command, '') != 'bench' ORDER BY j.id",
        (milestone_id,),
    ):
        last[job["ticket_id"]] = job["agent"]
    upcoming = {u.ticket: (n, u) for n, u in enumerate(queries.run_order(conn, project))}

    def order(t: sqlite3.Row) -> tuple[int, int, list[tuple[int, str]]]:
        turn = upcoming[t["ticket"]][0] if t["ticket"] in upcoming else 0
        return (_GROUPS.get(t["state"], 3), turn, _natural(t["ticket"]))

    rows: list[TicketRow] = []
    for t in sorted(tickets, key=order):
        state = t["state"] or "–"
        if state == "later":
            state = "set aside"
        elif t["ticket"] in upcoming and upcoming[t["ticket"]][1].waits:
            state = "waits for " + ", ".join(upcoming[t["ticket"]][1].waits)
        rows.append(
            TicketRow(
                ticket=t["ticket"],
                goal=t["title"],
                who=last.get(t["id"]) or _WHO.get(t["kind"], "–"),
                state=state,
                mark=t["state"] or "",
            )
        )
    return rows


@dataclass(frozen=True)
class Grown:
    """A stage in "How it grew"."""

    stage: str
    name: str
    current: bool
    later: bool  # after the card's own: dimmed
    when: str  # its date, where the database has one


def _date(at: str) -> str:
    moment = datetime.fromisoformat(at)
    return f"{moment.day} {moment:%b %H:%M}"


def how_it_grew(card: Card | None, started: str | None, ended: str | None) -> list[Grown]:
    """The five stages, the card's own marked and the later ones dimmed. Only two have a date
    in the database: ``started`` on planted, once a ticket has (F154 D4), and ``ended`` on
    harvested."""
    at = STAGES.index(card.stage) if card else -1
    grown: list[Grown] = []
    for n, stage in enumerate(STAGES):
        when = ""
        if stage == "planted" and started and (at > n or (at == n and card and card.started)):
            when = ("growing since " if at == n else "") + _date(started)
        if stage == "harvested" and ended and at == n:
            when = _date(ended)
        grown.append(Grown(stage, WORDS[stage][0], current=at == n, later=at < n, when=when))
    return grown


@dataclass(frozen=True)
class MilestoneDetail:
    key: str
    title: str | None
    status: str | None
    started: str | None
    ended: str | None
    outcome: str | None
    done_when: str | None
    signoff: dict[str, str] | None
    review_score: float | None
    owner_score: float | None
    results: queries.MilestoneResults | None
    savings: queries.Savings | None
    tickets: list[TicketRow]
    runs: list[sqlite3.Row]
    findings: dict[str, int]


def get_milestone_detail(
    conn: sqlite3.Connection, project: str, key: str
) -> MilestoneDetail | None:
    m = queries._milestone(conn, project, key)
    if m is None:
        return None
    results = queries.milestone_results(conn, project, key)
    savings = queries.savings(conn, project, key)
    tickets = ticket_rows(conn, project, m["id"])
    # A milestone's runs are the runs of its jobs (runs has no milestone_id).
    runs = conn.execute(
        "SELECT DISTINCT r.run_dir FROM runs r"
        " JOIN jobs j ON j.run_id = r.id"
        " WHERE j.milestone_id = ? ORDER BY r.started DESC",
        (m["id"],),
    ).fetchall()
    findings = queries._findings(conn, m["id"])
    signoff: dict[str, str] | None = None
    if m["signoff"]:
        import json as _json

        signoff = {k: v for k, v in _json.loads(m["signoff"]).items() if isinstance(v, str)}
    return MilestoneDetail(
        key=key,
        title=m["title"],
        status=m["status"],
        started=m["started"],
        ended=m["ended"],
        outcome=m["outcome"],
        done_when=m["done_when"],
        signoff=signoff,
        review_score=m["review_score"],
        owner_score=m["owner_score"],
        results=results,
        savings=savings,
        tickets=tickets,
        runs=runs,
        findings=findings,
    )


@dataclass(frozen=True)
class ReserveLever:
    """A planted card's fast lane lever (F172 D6, D8), started or not."""

    on: bool  # its doc says ``**Fast lane:** yes``
    asked: str | None  # "on" or "off": the owner's latest request the runner hasn't taken


def _reserve_lever(
    conn: sqlite3.Connection, project_id: int | None, card: Card | None
) -> ReserveLever | None:
    """The card's lever, as the board has its mark; None for a card in no ``RESERVABLE``
    stage, or with every ticket done (F172 D6: only while it has work to run, not in its
    review). A lever pulled shows on its way, as ``reserve_switches`` finds a switch's."""
    if project_id is None or card is None:
        return None
    if card.stage not in RESERVABLE or card.done >= card.total:
        return None
    asked = conn.execute(
        "SELECT value FROM owner_requests WHERE project_id = ? AND kind = ? AND subject = ?"
        " AND done IS NULL ORDER BY id DESC LIMIT 1",
        (project_id, RESERVE, card.key.lower()),
    ).fetchone()
    return ReserveLever(card.reserve, asked["value"] if asked is not None else None)


@router.get("/milestones/{key}", response_class=HTMLResponse)
def milestone_detail(
    key: str,
    request: Request,
    conn: Db,
    project: Project,
    now: Now,
) -> HTMLResponse:
    detail = get_milestone_detail(conn, project, key)
    if detail is None:
        return HTMLResponse(status_code=404, content="Not found")
    signoff_html: dict[str, str] = {}
    if detail.signoff:
        for k in (
            "changed",
            "how_to_test",
            "decisions",
            "what_next",
            "later",
            "lessons",
            "clogged",
        ):
            if k in detail.signoff:
                signoff_html[k] = _to_html(detail.signoff[k])
    # the thread page's Sign off, by the same rule (F50 D1); they import this module
    from factory_dashboard.planning import _repo
    from factory_dashboard.thread import _review

    project_id = metrics.find_project(conn, project)
    review = None if project_id is None else _review(conn, project, project_id, short_key(key), now)
    card = milestone_card(conn, project, now, key)  # None for a removed one: no stage
    grew = how_it_grew(card, detail.started, detail.ended)
    # from the card's doc; no checkout or no doc: the stored copy, as before F158
    about = read_card_doc(_repo(conn, project), key) or AboutDoc(
        _to_html(detail.outcome), _to_html(detail.done_when), ""
    )
    return render(
        request,
        conn,
        project,
        "milestone.html",
        {
            "active": "/board",  # the board is how a milestone is found (f5-17)
            "milestone": detail,
            "card": card,
            "reserve_lever": _reserve_lever(conn, project_id, card),
            "words": WORDS,
            "grew": grew,
            # the header's "growing since", on a started card's own stage (F154 D4)
            "growing_since": next((g.when for g in grew if g.current and g.when), ""),
            "thread": short_key(key),
            "about": about,
            "signoff_html": signoff_html,
            "review": review,
        },
    )


def _factory_project(conn: sqlite3.Connection, review_project: str) -> str:
    """The factory's own project: the registered project whose repo folder holds the
    factory's code (``runner/loop.py`` and ``factory_dashboard/app.py``); the review's
    own project when no such project exists."""
    try:
        rows = conn.execute("SELECT repo, name FROM projects").fetchall()
    except Exception:
        return review_project
    for row in rows:
        repo = row["repo"]
        if not repo:
            continue
        with contextlib.suppress(Exception):
            p = Path(repo)
            if (
                p.is_dir()
                and (p / "runner" / "loop.py").is_file()
                and (p / "factory_dashboard" / "app.py").is_file()
            ):
                return str(row["name"])
    return review_project


def review_ideas(conn: sqlite3.Connection, project: str, key: str) -> list[Idea]:
    """The review's ideas from its stored sign-off sheet, each with its area, the project it
    plants in and whether it is planted, on its way or refused (D2, D3)."""
    detail = get_milestone_detail(conn, project, key)
    if detail is None or detail.signoff is None:
        return []

    sheet = detail.signoff
    what_next = sheet.get("what_next")
    if not what_next:
        return []

    # Parse quoted lines from all sections in order
    ideas: list[Idea] = []
    n = 0
    last_bullet: str = ""  # nearest bullet above the current line

    for section_key in (
        "changed",
        "how_to_test",
        "decisions",
        "what_next",
        "later",
        "lessons",
        "clogged",
    ):
        section_text = sheet.get(section_key, "")
        if not section_text:
            continue
        for line in section_text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("- "):
                last_bullet = stripped
                continue
            if stripped.startswith(">") and len(stripped) > 1:
                n += 1
                text = stripped[1:].strip()
                # Area: product when the nearest bullet above starts with **Product
                area = "product" if "**Product" in last_bullet else "factory"
                # Project: product → the review's own; factory → the factory's own
                target_project = project if area == "product" else _factory_project(conn, project)
                ideas.append(
                    Idea(
                        id=f"{short_key(key)}/{n}",
                        text=text,
                        area=area,
                        project=target_project,
                        state="plant",
                        card=None,
                        said=None,
                    )
                )

    if not ideas:
        return []

    for idea in ideas:
        # Determine state from owner_requests of the idea's own target project
        idea_project = idea.project
        project_id_row = conn.execute(
            "SELECT id FROM projects WHERE name = ?", (idea_project,)
        ).fetchone()
        if project_id_row is None:
            continue
        project_id = project_id_row["id"]

        plant_requests = conn.execute(
            "SELECT * FROM owner_requests WHERE project_id = ? AND kind = 'plant' ORDER BY id DESC",
            (project_id,),
        ).fetchall()

        # Build a list of (request, parsed_value) pairs
        req_list: list[tuple[sqlite3.Row, dict[str, Any]]] = []
        for req in plant_requests:
            try:
                value = json.loads(req["value"] or "{}")
            except json.JSONDecodeError:
                continue
            if not isinstance(value, dict):
                continue
            req_list.append((req, value))

        req = None
        req_value: dict[str, Any] = {}
        # Try matching by request's ``from`` field first
        for r, v in req_list:
            if v.get("from") == idea.id:
                req, req_value = r, v
                break
        # Then by target project name (with text similarity check)
        if req is None:
            for r, v in req_list:
                target = v.get("project") or v.get("area") or ""
                if target == idea.project:
                    req_text = v.get("text", "")
                    norm_idea = re.sub(r"\s+", " ", idea.text).strip()
                    if norm_idea.endswith("."):
                        norm_idea = norm_idea[:-1]
                    norm_req = re.sub(r"\s+", " ", req_text).strip()
                    if norm_req.endswith("."):
                        norm_req = norm_req[:-1]
                    if norm_req.startswith(norm_idea):
                        req, req_value = r, v
                        break
        # Then by project_id (with text similarity check)
        if req is None:
            for r, v in req_list:
                if r["project_id"] == project_id:
                    req_text = v.get("text", "")
                    norm_idea = re.sub(r"\s+", " ", idea.text).strip()
                    if norm_idea.endswith("."):
                        norm_idea = norm_idea[:-1]
                    norm_req = re.sub(r"\s+", " ", req_text).strip()
                    if norm_req.endswith("."):
                        norm_req = norm_req[:-1]
                    if norm_req.startswith(norm_idea):
                        req, req_value = r, v
                        break
        if req is None:
            continue

        from_id = req_value.get("from")
        req_text = req_value.get("text", "")

        # Exact match on ``from``
        if from_id == idea.id:
            idea = _update_idea_state(idea, req)
        else:
            # Hand-made plant: text matches (whitespace collapsed, final full stop ignored)
            norm_idea = re.sub(r"\s+", " ", idea.text).strip()
            if norm_idea.endswith("."):
                norm_idea = norm_idea[:-1]
            norm_req = re.sub(r"\s+", " ", req_text).strip()
            if norm_req.endswith("."):
                norm_req = norm_req[:-1]
            if norm_req.startswith(norm_idea):
                idea = _update_idea_state(idea, req)

        # Rebuild the list since Idea is frozen
        idx = next(i for i, ix in enumerate(ideas) if ix.id == idea.id)
        ideas[idx] = idea

    return ideas


def _update_idea_state(idea: Idea, req: sqlite3.Row) -> Idea:
    """Update an idea's state based on a plant request, returning a new Idea."""
    if req["done"] is None:
        return replace(idea, state="on its way")
    result = str(req["result"] or "")
    if result.startswith("planted "):
        card_path = result[len("planted ") :]
        return replace(idea, state="planted", card=short_key(Path(card_path).stem))
    return replace(idea, state="refused", said=result)
