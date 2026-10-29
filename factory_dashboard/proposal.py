"""A proposal's review page (f6-08) and the mock-up route: ``/planning/{thread}/proposals/{id}``
and ``/planning/mockups/{thread}/{path}``. What the thread page shares with them stays in
``planning``."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from factory_dashboard.app import Db, Now, Project, render
from factory_dashboard.merges import _known_cards, _merge_words
from factory_dashboard.planning import (
    _ADR_NUMBER,
    _MOCKUP_RE,
    _adr_waits,
    _repo,
    _resolve_mockup_path,
    desk_trail,
)
from factory_dashboard.thread import _KIND_COLOR, _has_proposals, _proposals, _standing
from runner import metrics
from runner.planner import draft, plan_changes
from runner.tasks import split_frontmatter

router = APIRouter()


@router.get("/planning/mockups/{thread}/{path:path}", response_class=HTMLResponse)
def mockup_file(thread: str, path: str, conn: Db, project: Project) -> HTMLResponse:
    """A mock-up's file from the card's plan branch (``planner.draft``), for a sandboxed
    ``<iframe>``; anything outside ``.factory/cards/*-mockup/`` is 404. Its CSP sandboxes it
    when opened on its own too: an origin of its own, so it can't post to ``/requests``."""
    repo = _repo(conn, project)
    content = draft(repo, thread, path) if repo and _MOCKUP_RE.fullmatch(path) else None
    if content is None:
        raise HTTPException(404, "no such mock-up")
    return HTMLResponse(
        content.decode("utf-8", errors="replace"),
        headers={"Content-Security-Policy": "sandbox allow-scripts"},
    )


@dataclass(frozen=True)
class PlanChange:
    path: str
    word: str  # "added", "changed", "set aside" or "removed"
    text: str | None  # from the plan branch, through ``draft``; None when gone or not a draft
    who: str = ""  # a ticket's builder, lead or developer (F31 D8); "" for another file
    difficulty: str = ""  # a ticket's difficulty, as its frontmatter gives it


def _plan_changes(repo: Path | None, thread: str, kind: str) -> list[PlanChange]:
    """What approving a ``plan`` or ``replan`` changes (f6-24), each with its text from the
    branch; none for another kind, or with no plan branch."""
    if repo is None or kind not in ("plan", "replan"):
        return []
    found = []
    for change in plan_changes(repo, thread):
        content = draft(repo, thread, change.source) if change.source else None
        text = content.decode("utf-8", errors="replace") if content is not None else None
        found.append(PlanChange(change.path, change.word, text, *_who(change.path, text)))
    return found


# F73 D6: Refresh against main is Send back with these words, so the owner types nothing
REFRESH_WORDS = (
    "Check this against main as it is now: renumber what is taken, drop what is done or gone,"
    " and update the tickets."
)

_WORD_COLOR = {"added": "--good", "changed": "--a7"}  # set aside and removed: --muted (D8)


def _who(path: str, text: str | None) -> tuple[str, str]:
    """A ticket's builder and difficulty from its frontmatter (F31 D8); ("", "") for any other
    file, or a ticket that won't read."""
    if text is None or not path.startswith(".factory/tasks/"):
        return "", ""
    try:
        meta, _ = split_frontmatter(text)
    except (ValueError, yaml.YAMLError):
        return "", ""
    agent = meta.get("agent") or "developer"
    who = "lead" if agent == "lead" else "developer"
    difficulty = meta.get("difficulty")
    return who, str(difficulty) if isinstance(difficulty, int) else ""


@router.get("/planning/{thread}/proposals/{id}", response_class=HTMLResponse)
def proposal_review(
    request: Request, thread: str, id: str, conn: Db, project: Project, now: Now
) -> HTMLResponse:
    """A proposal's review page: its key points, agreed by default, with Comment… on each,
    and Send back, Accept ADR, Approve plan or Plant it."""
    project_id = metrics.find_project(conn, project)
    proposal = None if project_id is None else metrics.find_proposal(conn, project_id, thread, id)
    if project_id is None or proposal is None:
        raise HTTPException(404, "no such proposal")
    rows = conn.execute(
        "SELECT m.* FROM planner_messages m JOIN planner_threads t ON t.id = m.thread_id"
        " WHERE t.project_id = ? AND t.card = ? ORDER BY m.id",
        (project_id, thread),
    ).fetchall()
    lead = [r for r in rows if r["author"] == "lead" and _has_proposals(r["proposals"])]
    listed = [p for p in json.loads(lead[-1]["proposals"]) if isinstance(p, dict)] if lead else []
    kind = str(proposal.get("kind") or "")
    key_points = proposal.get("key_points")
    number = _ADR_NUMBER.match(str(proposal.get("path") or ""))
    path = str(proposal.get("path") or "")
    repo = _repo(conn, project)
    resolved = _resolve_mockup_path(path) if path else None
    mockup: str | None = None
    mockup_gone: str | None = None
    if resolved is not None:
        content = draft(repo, thread, resolved) if repo else None
        if content is not None:
            mockup = f"/planning/mockups/{thread}/{resolved}"
        else:
            mockup_gone = path
    accepting = frozenset(
        int(r["value"])
        for r in metrics.open_requests(conn, project_id)
        if r["kind"] == "accept_adr"
        and r["subject"] == thread
        and str(r["value"] or "").isascii()
        and str(r["value"] or "").isdigit()
    )
    waits = _adr_waits(repo, listed, accepting)
    archived = conn.execute(
        "SELECT archived FROM planner_threads WHERE project_id = ? AND card = ?",
        (project_id, thread),
    ).fetchone()
    drafted = (now - datetime.fromisoformat(lead[-1]["at"])).days if lead else 0
    return render(
        request,
        conn,
        project,
        "proposal.html",
        {
            "active": "/planning",
            "adr_on_its_way": (
                ", ".join(str(n) for n in sorted(accepting))
                if accepting and not waits and _adr_waits(repo, listed)
                else ""
            ),
            "thread": thread,
            "proposal": proposal,
            "kind": kind,
            "color": _KIND_COLOR.get(kind, "--ink-2"),
            "key_points": [p for p in key_points if isinstance(p, dict)]
            if isinstance(key_points, list)
            else [],
            "proposals": _proposals(conn, project_id, thread, rows, _known_cards(repo)),
            "adr_number": str(int(number[1])) if number else None,
            "merge": _merge_words(proposal),
            "mockup": mockup,
            "mockup_gone": mockup_gone,
            "adr_waits": waits,
            "changes": _plan_changes(repo, thread, kind),
            "word_color": _WORD_COLOR,
            "standing": _standing(conn, project_id, thread, proposal, lead, _known_cards(repo)),
            "trail": desk_trail(conn, project, now, request.url.path),
            "archived": bool(archived and archived["archived"]),
            "drafted_days": drafted,
            "refresh_words": REFRESH_WORDS,
        },
    )
