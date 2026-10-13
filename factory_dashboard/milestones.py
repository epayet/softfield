"""The Milestones list page (f1-12, D8), with trends across them.

One row per milestone: key (a link to ``/milestones/{key}``), title, status, dates,
tickets merged, first-attempt pass rate, escalations, review rounds, Claude dollars,
net savings. Trends below: first-attempt rate, escalations, Claude dollars per merged
ticket and savings per milestone, as small charts (D5).
"""

import re
import sqlite3
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from factory_dashboard import queries
from factory_dashboard.app import Db, Now, Project, render
from runner import metrics
from runner.tasks import milestone_order, short_key

router = APIRouter()


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
    priority: int | None = None  # a card not done's (f6-18), with what its ↑ and ↓ ask for
    up: int | None = None
    down: int | None = None


UNMOVED = (None, "done", "removed")  # card states without a priority to change


def _with_moves(
    conn: sqlite3.Connection, project: str, rows: list[MilestoneRow]
) -> list[MilestoneRow]:
    """Each card not done with its priority, and the priorities its ↑ and ↓ ask for against
    its neighbours in the run order (priority, then milestone order), not the page's order."""
    cards = {
        row["key"]: row["priority"]
        for row in conn.execute(
            "SELECT m.key, m.state, m.status, m.priority FROM milestones m"
            " JOIN projects p ON p.id = m.project_id WHERE p.name = ?",
            (project,),
        )
        if row["state"] not in UNMOVED and row["status"] != "done" and row["priority"] is not None
    }
    order = sorted(cards, key=lambda key: (cards[key], milestone_order(key), key))
    moved = dict(zip(order, queries.moves([cards[key] for key in order]), strict=True))
    return [
        replace(r, priority=cards[r.key], up=moved[r.key][0], down=moved[r.key][1])
        if r.key in moved
        else r
        for r in rows
    ]


def milestone_rows(conn: sqlite3.Connection, project: str) -> list[MilestoneRow]:
    """Every milestone's summary, grouped and sorted: in progress first (by latest job),
    then not started (by priority), then done (by end date)."""
    # Lookup table for milestone status and dates.
    milestone_meta = conn.execute(
        "SELECT m.key, m.status, m.started, m.ended, m.id FROM milestones m"
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

    return _with_moves(conn, project, result)


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
            "active": "/milestones",
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
    tickets: list[sqlite3.Row]
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
    tickets = queries._tickets(conn, m["id"])
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
    # the planning page's Sign off, by the same rule (F50 D1); planning imports this module
    from factory_dashboard.planning import _review

    project_id = metrics.find_project(conn, project)
    review = None if project_id is None else _review(conn, project, project_id, short_key(key), now)
    return render(
        request,
        conn,
        project,
        "milestone.html",
        {
            "active": "/milestones",
            "milestone": detail,
            "outcome_html": _to_html(detail.outcome),
            "done_when_html": _to_html(detail.done_when),
            "signoff_html": signoff_html,
            "review": review,
        },
    )
