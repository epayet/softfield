"""The Milestones list page (f1-12, D8), with trends across them.

One row per milestone: key (a link to ``/milestones/{key}``), title, status, dates,
tickets merged, first-attempt pass rate, escalations, review rounds, Claude dollars,
net savings. Trends below: first-attempt rate, escalations, Claude dollars per merged
ticket and savings per milestone, as small charts (D5). The list has no tab since the board
(f5-17): the board links to it.

``/milestones/{key}`` is the milestone's card's page (f5-17, after
``.softfield/cards/f5-board-mockup/Card.dc.html``): its stage on the board, place and area,
how far it has grown, then what the page showed before, its tickets now in run order.
"""

import contextlib
import json
import re
import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, Response

from factory_dashboard import queries
from factory_dashboard.app import Db, Now, Project, render, templates
from factory_dashboard.board import RESERVABLE, STAGES, WORDS, Card, milestone_card
from factory_dashboard.line import _natural
from runner import metrics
from runner.config import ConfigError, project_shots
from runner.milestone import milestone_doc
from runner.requests import RESERVE
from runner.shots import FAILED, LIST_FILE, NEW, SHOTS_DIR, TAKEN
from runner.tasks import TaskError, full_key, milestone_file, short_key

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


def _short(key: str) -> str:
    """A milestone's short key, the queue's name for it; a key no card has, itself."""
    try:
        return short_key(key)
    except TaskError:
        return key


def milestone_rows(
    conn: sqlite3.Connection,
    project: str,
    trends: list[queries.Trend] | None = None,
) -> list[MilestoneRow]:
    """Every milestone's summary, grouped and sorted: in progress first (by latest job),
    then not started (in the queue's order, F222 D5), then done (by end date)."""
    if trends is None:
        trends = queries.trends(conn, project)
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
    for trend in trends:
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
    with_tickets = {
        r["milestone_id"]
        for r in conn.execute(
            "SELECT t.milestone_id FROM tickets t JOIN projects p ON p.id = t.project_id"
            " WHERE p.name = ? AND t.state IS NOT ?",
            (project, metrics.REMOVED),
        )
    }
    no_data_rows: list[MilestoneRow] = []
    for m in no_data:
        if m["key"] not in seen:
            info = meta.get(m["key"], {})
            if (
                info.get("state") is None
                and info.get("ended") is None
                and info.get("status") != "done"
                and milestone_ids.get(m["key"]) not in with_tickets
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

    # Merge and sort: in progress → not started → done
    all_rows = [*with_data, *no_data_rows]
    places = queries.board_places(conn, project)

    def _ip_key(r: MilestoneRow) -> tuple[int, float, str]:
        mid = milestone_ids.get(r.key)
        latest = latest_jobs.get(mid) if mid else None
        if latest and isinstance(latest, str):
            ts = datetime.fromisoformat(latest).timestamp()
        else:
            ts = 0.0
        return (0, -ts, r.key)

    def _ns_key(r: MilestoneRow) -> tuple[int, int, list[tuple[int, str]], str]:
        return (1, queries.place(places, _short(r.key)), _natural(r.key), r.key)

    def _done_key(r: MilestoneRow) -> tuple[int, float, str]:
        ended = r.ended
        ts = datetime.fromisoformat(ended).timestamp() if ended and isinstance(ended, str) else 0.0
        return (2, -ts, r.key)

    in_progress = [r for r in all_rows if r.key in in_progress_keys]
    not_started = [r for r in all_rows if r.key in not_started_keys]
    done = [r for r in all_rows if r.key in done_keys]

    return (
        sorted(in_progress, key=_ip_key)
        + sorted(not_started, key=_ns_key)
        + sorted(done, key=_done_key)
    )


def _rate_chart(
    conn: sqlite3.Connection, project: str, trends: list[queries.Trend] | None = None
) -> dict[str, Any]:
    if trends is None:
        trends = queries.trends(conn, project)
    points = [p for p in trends if p.results.merged > 0]
    return {
        "labels": [p.results.key.upper() for p in points],
        "rate": [
            round(p.results.pass_rate * 100, 1) if p.results.pass_rate is not None else None
            for p in points
        ],
    }


def _esc_chart(
    conn: sqlite3.Connection, project: str, trends: list[queries.Trend] | None = None
) -> dict[str, Any]:
    if trends is None:
        trends = queries.trends(conn, project)
    points = [p for p in trends if p.results.merged > 0]
    return {
        "labels": [p.results.key.upper() for p in points],
        "count": [p.results.escalations for p in points],
    }


def _dollars_chart(
    conn: sqlite3.Connection, project: str, trends: list[queries.Trend] | None = None
) -> dict[str, Any]:
    if trends is None:
        trends = queries.trends(conn, project)
    points = [p for p in trends if p.results.merged > 0]
    return {
        "labels": [p.results.key.upper() for p in points],
        "dollars": [
            round(p.results.claude.dollars / p.results.merged, 2) if p.results.merged else None
            for p in points
        ],
    }


def _savings_chart(
    conn: sqlite3.Connection, project: str, trends: list[queries.Trend] | None = None
) -> dict[str, Any]:
    if trends is None:
        trends = queries.trends(conn, project)
    points = [p for p in trends if p.results.merged > 0]
    return {
        "labels": [p.results.key.upper() for p in points],
        "savings": [round(p.savings.net, 2) for p in points],
    }


@router.get("/milestones", response_class=HTMLResponse)
def milestones_list(request: Request, conn: Db, project: Project, now: Now) -> HTMLResponse:
    trends = queries.trends(conn, project)
    rows = milestone_rows(conn, project, trends)
    return render(
        request,
        conn,
        project,
        "milestones.html",
        {
            "active": "/board",  # where its link is, now it has no tab (f5-17)
            "picker_to": "/milestones",
            "milestones": rows,
            "rate": _rate_chart(conn, project, trends),
            "esc": _esc_chart(conn, project, trends),
            "dollars": _dollars_chart(conn, project, trends),
            "savings": _savings_chart(conn, project, trends),
        },
    )


def idea_vals(idea: Idea, ask: bool) -> str:
    """The JSON ``hx-vals`` of an idea's Plant (``ask`` false) or Plant and ask the lead: a
    ``plant`` request whose value is ``{text, ask, area, from}`` (D4), to the idea's project."""
    review = idea.id.split("/")[0].upper()
    value = {
        "text": f"{idea.text} From {review}'s review.",
        "ask": ask,
        "area": idea.area,
        "from": idea.id,
    }
    return json.dumps({"kind": "plant", "project": idea.project, "value": json.dumps(value)})


def idea_plate(idea: Idea) -> str:
    """The idea drawn as a plate (``_partials/idea.html``), as HTML."""
    return templates.get_template("_partials/idea.html").render(
        idea=idea, vals_plant=idea_vals(idea, False), vals_ask=idea_vals(idea, True)
    )


def _inline_markup(text: str) -> str:
    """Process ``[text](url)`` links, `` `code` ``, and `` **bold** `` in text."""

    # Links: http/https only become <a>; others become plain text
    def _replace_link(m: re.Match[str]) -> str:
        link_text = m.group(1)
        url = m.group(2)
        if url.startswith(("http://", "https://")):
            return f'<a href="{url}">{link_text}</a>'
        return link_text

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _replace_link, text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return text


def _to_html(text: str | None, ideas: Iterator[Idea] | None = None) -> str:
    """Turn ``1. x`` numbered lines into ``<ol>``, an indented ``- x`` under a bullet into a
    nested ``<ul>``, `` **x** `` into ``<strong>x</strong>``, `` `x` `` into ``<code>x</code>``,
    and ``[text](url)`` into links (http/https only). Escapes first. With ``ideas``, each
    quoted line (``> …``) is drawn in place as the next idea's plate (F164 D5); with none
    left it stays a plain line."""
    if text is None:
        return ""
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    lines = escaped.split("\n")
    html_parts: list[str] = []
    in_ol: bool = False
    in_ul: bool = False
    in_nested_ul: bool = False
    for line in lines:
        stripped = line.strip()
        # Idea plates
        if ideas is not None and stripped.startswith("&gt;") and len(stripped) > len("&gt;"):
            idea = next(ideas, None)
            if idea is not None:
                if in_nested_ul:
                    html_parts.append("</ul>")
                    in_nested_ul = False
                if in_ul:
                    html_parts.append("</ul>")
                    in_ul = False
                if in_ol:
                    html_parts.append("</ol>")
                    in_ol = False
                html_parts.append(idea_plate(idea))
                continue
        # Numbered list item
        ol_match = re.match(r"^(\s*)(\d+)\.\s+(.*)", line)
        if ol_match:
            if not in_ol:
                html_parts.append("<ol>")
                in_ol = True
            text_part = _inline_markup(ol_match.group(3))
            html_parts.append(f"<li>{text_part}</li>")
            continue
        # Bullet list item (with optional indent for nesting)
        ul_match = re.match(r"^(\s*)(- )(.*)", line)
        if ul_match:
            indent = ul_match.group(1)
            text_part = ul_match.group(3)
            is_nested = bool(indent) and not in_nested_ul
            # Close nested ul if we were in one
            if in_nested_ul:
                html_parts.append("</ul>")
                in_nested_ul = False
            # Start nested ul if this item is nested
            if is_nested:
                html_parts.append("<ul>")
                in_nested_ul = True
            # Start outer ul if we're not in one and this item is not nested
            elif not in_ul:
                html_parts.append("<ul>")
                in_ul = True
            text_part = _inline_markup(text_part)
            html_parts.append(f"<li>{text_part}</li>")
            continue
        # Regular line
        if in_nested_ul:
            html_parts.append("</ul>")
            in_nested_ul = False
        if in_ul:
            html_parts.append("</ul>")
            in_ul = False
        if in_ol:
            html_parts.append("</ol>")
            in_ol = False
        if stripped:
            html_parts.append(f"<p>{_inline_markup(stripped)}</p>")
    if in_nested_ul:
        html_parts.append("</ul>")
    if in_ul:
        html_parts.append("</ul>")
    if in_ol:
        html_parts.append("</ol>")
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
    moment = queries.local(at)
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
class CaughtRow:
    """One finding from a milestone's review: its severity, summary, and what happened."""

    severity: str
    summary: str
    outcome: str


@dataclass(frozen=True)
class SpendRow:
    """One row of a milestone's spend by role: label, dollars, and share of the largest."""

    label: str
    usd: float
    share: float


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
    caught: list[CaughtRow]
    spend: list[SpendRow]


_SEVERITY_ORDER = {"blocking": 0, "should-fix": 1, "nit": 2}

_ROLE_LABELS: dict[str, str] = {
    "review": "The review",
    "escalation": "The lead finishing a developer's ticket",
    "planner": "Planning",
    "lead-ticket": "The lead's tickets",
    "direction": "Directions for developers",
    "checkpoint": "Checkpoints",
}


def _outcome(finding: sqlite3.Row) -> str:
    """The outcome word for a finding, per D11."""
    if finding["resolved"]:
        return "fixed"
    route = str(finding["route"] or "")
    if route == "report":
        return "left"
    if route in ("local", "later", "backlog"):
        return "ticket"
    if route == "adr":
        return "for you"
    return "left"


def _caught(conn: sqlite3.Connection, milestone_id: int) -> list[CaughtRow]:
    """The milestone's findings, ordered by severity then key (D11)."""
    rows = conn.execute(
        "SELECT severity, summary, route, resolved, key FROM findings"
        " WHERE milestone_id = ? ORDER BY severity, key",
        (milestone_id,),
    ).fetchall()

    def _sev_key(r: sqlite3.Row) -> tuple[int, str]:
        return (_SEVERITY_ORDER.get(r["severity"], 99), r["key"])

    found: list[sqlite3.Row] = sorted(rows, key=_sev_key)
    return [
        CaughtRow(
            severity=str(r["severity"] or ""),
            summary=str(r["summary"] or ""),
            outcome=_outcome(r),
        )
        for r in found
    ]


def _spend_label(role: str) -> str:
    """The plain label for a job role (D10)."""
    label = _ROLE_LABELS.get(role, role)
    if role == "developer":
        return "Developers, on your GPU"
    return label


def _milestone_spend(conn: sqlite3.Connection, milestone_id: int) -> list[SpendRow]:
    """The milestone's dollars by role, largest first, with share (D10)."""
    rows = conn.execute(
        "SELECT j.role, sum(j.cost_usd) as total_cost"
        " FROM jobs j WHERE j.milestone_id = ?"
        " GROUP BY j.role",
        (milestone_id,),
    ).fetchall()

    # Developer roles with jobs but no dollars
    dev_rows = conn.execute(
        "SELECT 1 FROM jobs WHERE milestone_id = ? AND role = 'developer' LIMIT 1",
        (milestone_id,),
    ).fetchone()

    # Build list of (role, usd)
    spend: list[tuple[str, float]] = []
    seen_roles: set[str] = set()
    for r in rows:
        role = str(r["role"] or "")
        usd = float(r["total_cost"] or 0)
        spend.append((role, usd))
        seen_roles.add(role)

    # Add developer row if it has jobs but no dollars
    if dev_rows and "developer" not in seen_roles:
        spend.append(("developer", 0.0))

    # Sort by dollars descending
    spend.sort(key=lambda x: -x[1])

    # Compute share
    max_usd = spend[0][1] if spend else 0.0
    if max_usd == 0:
        return []

    return [
        SpendRow(
            label=_spend_label(role),
            usd=round(usd, 2),
            share=round(usd / max_usd, 2),
        )
        for role, usd in spend
    ]


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
    caught = _caught(conn, m["id"])
    spend = _milestone_spend(conn, m["id"])
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
        caught=caught,
        spend=spend,
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


@dataclass(frozen=True)
class ShotPicture:
    """One picture of a page (f85-02 / F85 D7): its address when it was taken, else why not."""

    width: str  # "phone" or "wide"
    src: str | None
    say: str  # the plain words in the dashed plate when there is no picture
    why: str  # the reason recorded in ``shots.json``, if any


@dataclass(frozen=True)
class ShotPlate:
    address: str
    href: str | None  # the page as it is now, else the address stays plain text
    before: list[ShotPicture]
    after: list[ShotPicture]


@dataclass(frozen=True)
class ShotsPanel:
    plates: list[ShotPlate]
    taken: str  # when the list was written
    mockup: str | None  # the card's mock-up proposal on its planning thread


SHOT_NAME = re.compile(r"(before|after)-(phone|wide)-[1-9][0-9]*\.png")
SAFE_KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")
WIDTHS = ("phone", "wide")


def _is_factory(repo: Path) -> bool:
    """Whether ``repo`` holds the factory's own code (as ``_factory_project`` tells)."""
    return (repo / "runner" / "loop.py").is_file() and (
        repo / "factory_dashboard" / "app.py"
    ).is_file()


def _shot_href(address: str, project: str, factory: bool, live: str) -> str | None:
    """The link to a page as it is now: the dashboard's own for the factory, else the project's
    ``live`` joined to the address; None for anything else (plain text, never a link that goes
    nowhere or somewhere foreign)."""
    if not address.startswith("/") or address.startswith("//"):
        return None
    if any(c in address for c in "\\\"'<> ") or any(ord(c) < 32 for c in address):
        return None
    if factory:
        return address + ("&" if "?" in address else "?") + urlencode({"project": project})
    if live.startswith(("http://", "https://")):
        return live.rstrip("/") + address
    return None


def _shot_pictures(
    listed: dict[str, Any], folder: Path, n: int, when: str, src: str
) -> list[ShotPicture]:
    recorded = listed.get("pictures")
    recorded = recorded if isinstance(recorded, dict) else {}
    found: list[ShotPicture] = []
    for width in WIDTHS:
        name = f"{when}-{width}-{n}.png"
        entry = recorded.get(name)
        state = entry.get("state") if isinstance(entry, dict) else None
        why = str(entry.get("reason") or "") if isinstance(entry, dict) else ""
        if state == TAKEN and (folder / name).is_file():
            found.append(ShotPicture(width, f"{src}/{name}", "", ""))
        elif state == NEW and when == "before":
            found.append(ShotPicture(width, None, "This page didn't exist before", ""))
        elif state == FAILED:
            say = (
                "The page before couldn't be drawn"
                if when == "before"
                else "The page couldn't be drawn"
            )
            found.append(ShotPicture(width, None, say, why))
        else:
            found.append(ShotPicture(width, None, "No picture was taken", ""))
    return found


def _mockup_link(conn: sqlite3.Connection, project_id: int | None, thread: str) -> str | None:
    """The card's latest mock-up proposal on its planning thread, even when later replies list
    only other proposals, as F85's own does."""
    if project_id is None:
        return None
    rows = conn.execute(
        "SELECT m.proposals FROM planner_messages m JOIN planner_threads t ON t.id = m.thread_id"
        " WHERE t.project_id = ? AND t.card = ? AND m.author = 'lead'"
        " AND m.proposals IS NOT NULL ORDER BY m.id DESC",
        (project_id, thread),
    ).fetchall()
    for row in rows:
        for proposal in json.loads(row["proposals"]):
            if (
                isinstance(proposal, dict)
                and proposal.get("kind") == "mockup"
                and proposal.get("id")
            ):
                return f"/planning/{thread}/proposals/{proposal['id']}"
    return None


def shots_panel(
    conn: sqlite3.Connection,
    project: str,
    project_id: int | None,
    repo: Path | None,
    key: str,
    q: str,
) -> ShotsPanel | None:
    """The card's "Before and after" panel from f85-01's list in its project's picture folder;
    None without the list (or a checkout)."""
    if repo is None or not SAFE_KEY.fullmatch(key):
        return None
    folder = repo / SHOTS_DIR / key
    try:
        listed = json.loads((folder / LIST_FILE).read_text(encoding="utf-8"))
        taken = _date(
            datetime.fromtimestamp((folder / LIST_FILE).stat().st_mtime, tz=UTC).isoformat()
        )
    except (OSError, ValueError):
        return None
    pages = listed.get("pages") if isinstance(listed, dict) else None
    if not isinstance(pages, list):
        return None
    try:
        live = project_shots(repo)
    except ConfigError:
        live = None
    factory = _is_factory(repo)
    src = f"/milestones/{quote(key)}/shots"
    suffix = q if q else ""
    plates = [
        ShotPlate(
            address=str(address),
            href=_shot_href(str(address), project, factory, live.live if live else ""),
            before=[
                replace(p, src=p.src + suffix if p.src else None)
                for p in _shot_pictures(listed, folder, n, "before", src)
            ],
            after=[
                replace(p, src=p.src + suffix if p.src else None)
                for p in _shot_pictures(listed, folder, n, "after", src)
            ],
        )
        for n, address in enumerate(pages, start=1)
    ]
    return ShotsPanel(
        plates=plates,
        taken=taken,
        mockup=(link + q) if (link := _mockup_link(conn, project_id, short_key(key))) else None,
    )


@router.get("/milestones/{key}/shots/{file}")
def milestone_shot(key: str, file: str, conn: Db, project: Project) -> Response:
    """A picture of the card's panel, from its project's picture folder (D7). Only the names the
    runner gives them (``before|after-phone|wide-<n>.png``) of a card the project has: anything
    else is 404."""
    from factory_dashboard.planning import _repo

    repo = _repo(conn, project)
    if (
        repo is None
        or not SAFE_KEY.fullmatch(key)
        or not SHOT_NAME.fullmatch(file)
        or queries._milestone(conn, project, key) is None
    ):
        raise HTTPException(404, "no such picture")
    path = repo / SHOTS_DIR / key / file
    if path.is_symlink() or not path.is_file():
        raise HTTPException(404, "no such picture")
    return Response(
        path.read_bytes(), media_type="image/png", headers={"Cache-Control": "no-cache"}
    )


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
    ideas = iter(review_ideas(conn, project, key)) if detail.signoff else None
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
                signoff_html[k] = _to_html(detail.signoff[k], ideas)
    # the thread page's Sign off, by the same rule (F50 D1); they import this module
    from factory_dashboard.planning import _repo
    from factory_dashboard.thread import _review

    project_id = metrics.find_project(conn, project)
    review = None if project_id is None else _review(conn, project, project_id, short_key(key), now)
    card = milestone_card(conn, project, now, key)  # None for a removed one: no stage
    grew = how_it_grew(card, detail.started, detail.ended)
    repo = _repo(conn, project)
    # under "What changed", so only where that shows (F85 D7)
    shots = (
        shots_panel(conn, project, project_id, repo, key, "?" + urlencode({"project": project}))
        if detail.signoff
        else None
    )
    # from the card's doc; no checkout or no doc: the stored copy, as before F158
    about = read_card_doc(repo, key) or AboutDoc(
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
            "shots": shots,
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


def _normalise_idea_text(text: str) -> str:
    """Whitespace collapsed, one final full stop dropped."""
    norm = re.sub(r"\s+", " ", text).strip()
    return norm[:-1] if norm.endswith(".") else norm


def _same_text(idea_text: str, request_text: str) -> bool:
    """Whether a plant request's text is the idea's (a request may add to it); an idea with
    no text once normalised matches no request."""
    norm_idea = _normalise_idea_text(idea_text)
    return bool(norm_idea) and _normalise_idea_text(request_text).startswith(norm_idea)


def review_ideas(conn: sqlite3.Connection, project: str, key: str) -> list[Idea]:
    """The review's ideas from its stored sign-off sheet, each with its area, the project it
    plants in and whether it is planted, on its way or refused (D2, D3)."""
    detail = get_milestone_detail(conn, project, key)
    if detail is None or detail.signoff is None:
        return []

    sheet = detail.signoff
    ideas: list[Idea] = []
    n = 0
    factory: str | None = None  # looked up once, on the first factory idea

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
        last_bullet = ""  # the nearest bullet above, in this section only (D2)
        for line in section_text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("- "):
                last_bullet = stripped
                continue
            if stripped.startswith(">") and len(stripped) > 1:
                n += 1
                text = stripped[1:].strip()
                # Area: product when the nearest bullet above starts with **Product
                area = "product" if last_bullet.startswith("- **Product") else "factory"
                # Project: product → the review's own; factory → the factory's own
                if area == "factory" and factory is None:
                    factory = _factory_project(conn, project)
                target_project = project if area == "product" else str(factory)
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

    plants: dict[str, list[tuple[sqlite3.Row, dict[str, Any]]]] = {}  # newest first, by project
    for name in {idea.project for idea in ideas}:
        plants[name] = []
        for req in conn.execute(
            "SELECT r.* FROM owner_requests r JOIN projects p ON p.id = r.project_id"
            " WHERE p.name = ? AND r.kind = 'plant' ORDER BY r.id DESC",
            (name,),
        ):
            with contextlib.suppress(json.JSONDecodeError):
                value = json.loads(req["value"] or "{}")
                if isinstance(value, dict):
                    plants[name].append((req, value))

    def matching(idea: Idea) -> sqlite3.Row | None:
        """The latest request whose ``from`` is the idea's id, else the latest hand-made one
        (no ``from``) whose text is the idea's: a press of another idea never counts (D3)."""
        found = plants[idea.project]
        return next((r for r, v in found if v.get("from") == idea.id), None) or next(
            (
                r
                for r, v in found
                if not v.get("from") and _same_text(idea.text, str(v.get("text") or ""))
            ),
            None,
        )

    return [_update_idea_state(i, req) if (req := matching(i)) else i for i in ideas]


def _update_idea_state(idea: Idea, req: sqlite3.Row) -> Idea:
    """Update an idea's state based on a plant request, returning a new Idea."""
    if req["done"] is None:
        return replace(idea, state="on its way")
    result = str(req["result"] or "")
    if result.startswith("planted "):
        card_path = result[len("planted ") :]
        return replace(idea, state="planted", card=short_key(Path(card_path).stem))
    return replace(idea, state="refused", said=result)
