"""The planning room's threads and replies (ADR 20 items 3–5, f6 D1–D3). No AI in it.

A thread is a card's (by its short key, ``f7``) or the ``general`` one. Each message the owner
sends is a ``plan_message`` request (f6 D1), queued as its own ``planner`` row whose subject
names the thread and the request (``f7#41``); the message itself stays in its request row.
The lead's reply ends with a fenced ``json`` block (D2), checked here before it is recorded.
"""

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from runner.tasks import BUGS, TaskError, milestone_key, short_key

PLANNER = "planner"  # the role, and the queued job's kind (`dispatch.PLANNER`)
PLAN_MESSAGE = "plan_message"  # the request kind: subject the thread, value `message`'s JSON
PLANNING = "planning"  # the owner item a reply raises, about its thread (ADR 20 item 9)
GENERAL = "general"
PROPOSAL_KINDS = ("adr", "mockup", "plan", "seed", "replan")
_MAX_KEY = 64
_BLOCK_RE = re.compile(r"```json[ \t]*\n(.*?)\n?```", re.DOTALL)


class PlannerError(ValueError):
    """A request or a reply the runner can't read, with why."""


@dataclass(frozen=True)
class Reply:
    """A planner job's reply: its free text, and the block's points and proposals. ``note``
    says why there are none when the block was missing or broken."""

    text: str
    points: tuple[dict[str, Any], ...] = ()
    proposals: tuple[dict[str, Any], ...] = ()
    note: str | None = None


def thread_key(subject: object) -> str:
    """A ``plan_message``'s thread: ``general``, or a card's key in either form, as its short
    key (``f6-planning-room`` is ``f6``)."""
    if subject == GENERAL:
        return GENERAL
    refused = PlannerError(f"a thread is a card's key or general, not {subject!r}")
    # A bare number is a ticket's milestone (`m4`), never a card's key as the dashboard sends it
    if not isinstance(subject, str) or len(subject) > _MAX_KEY or subject.isdigit():
        raise refused
    try:
        key = milestone_key(subject)
    except TaskError:
        raise refused from None
    if key == BUGS:
        raise refused
    return short_key(key)


def thread_name(thread: str) -> str:
    """A thread in words: ``F7``, or ``the general thread``."""
    return "the general thread" if thread == GENERAL else thread.upper()


def row_subject(thread: str, request_id: int) -> str:
    """The planner row's subject for a message: ``f7#41``. One open row per kind and subject
    is the queue's rule, so each message needs its own."""
    return f"{thread}#{request_id}"


def request_of(subject: str) -> tuple[str, int]:
    """A planner row's thread and request id, from its subject."""
    thread, _, request_id = subject.rpartition("#")
    if not request_id.isdigit():
        raise PlannerError(f"a planner job's subject is <thread>#<request>, not {subject!r}")
    return thread_key(thread), int(request_id)


def message(value: object) -> tuple[str, dict[int, str]]:
    """A ``plan_message``'s value: its free text and the owner's comments by point number."""
    try:
        data = json.loads(value) if isinstance(value, str) else None
    except json.JSONDecodeError:
        data = None
    if not isinstance(data, dict):
        raise PlannerError("a message is JSON with its text and comments")
    text, comments = data.get("text"), data.get("comments", {})
    if not isinstance(text, str) or not isinstance(comments, dict):
        raise PlannerError("a message is JSON with its text and comments")
    by_point: dict[int, str] = {}
    for n, comment in comments.items():
        if not (isinstance(n, str) and n.isdigit() and isinstance(comment, str)):
            raise PlannerError("a message's comments are text by point number")
        if comment.strip():
            by_point[int(n)] = comment.strip()
    if not text.strip() and not by_point:
        raise PlannerError("a message has words or comments")
    return text.strip(), dict(sorted(by_point.items()))


PROMPT = """\
You are the lead, planning with the owner in the planning room \
(docs/adr/20-planning-room.md). This is their message on {thread}. Read what you need in the \
repo; change nothing.
{comments}
The owner's message:

{text}

Answer their comments first, then the message, in plain words, as numbered points: each \
with a title, an answer and a suggested action. Every point of yours they didn't comment on \
counts as agreed. End your reply with one fenced `json` block, nothing after it:

```json
{{"points": [{{"n": 1, "title": "…", "answer": "…", "action": "…"}}], "proposals": []}}
```"""


def prompt(thread: str, text: str, comments: Mapping[int, str]) -> str:
    """The planner job's prompt for one message (f6-02 writes how the planner plans)."""
    lines = "".join(f"- On your point {n}: {comment}\n" for n, comment in comments.items())
    said = f"\nTheir comments on your last points:\n{lines}" if lines else ""
    return PROMPT.format(thread=thread_name(thread), comments=said, text=text or "(none)")


def parse_reply(text: str) -> Reply:
    """A reply's free text and its last ``json`` block's points and proposals (f6 D2). A
    reply whose block is missing or broken is all text, with a note saying why."""
    whole = text.strip()
    blocks = list(_BLOCK_RE.finditer(whole))
    if not blocks:
        return Reply(whole, note="the reply has no json block, so its points weren't read")
    block = blocks[-1]
    try:
        points, proposals = _checked(block[1])
    except PlannerError as exc:
        return Reply(whole, note=f"the reply's json block was not read: {exc}")
    around = [whole[: block.start()].strip(), whole[block.end() :].strip()]
    return Reply("\n\n".join(part for part in around if part), points, proposals)


def stored_text(reply: Reply) -> str:
    """What the thread shows: the reply's text, then the note, if any."""
    return reply.text if reply.note is None else f"{reply.text}\n\n({reply.note}.)".strip()


def _checked(block: str) -> tuple[tuple[dict[str, Any], ...], tuple[dict[str, Any], ...]]:
    try:
        data = json.loads(block)
    except json.JSONDecodeError as exc:
        raise PlannerError(f"it is not JSON ({exc.msg})") from None
    if not isinstance(data, dict):
        raise PlannerError("it is not an object")
    points = data.get("points")
    proposals = data.get("proposals", [])
    if not isinstance(points, list):
        raise PlannerError("it has no list of points")
    if not isinstance(proposals, list):
        raise PlannerError("its proposals are not a list")
    _numbered(points, "point", ("title", "answer", "action"))
    for proposal in proposals:
        _proposal(proposal)
    return tuple(points), tuple(proposals)


def _numbered(items: list[Any], what: str, texts: tuple[str, ...]) -> None:
    """Each item an object with a whole ``n``, used once, and its ``texts`` as strings."""
    seen: set[int] = set()
    for item in items:
        if not isinstance(item, dict):
            raise PlannerError(f"a {what} is not an object")
        n = item.get("n")
        if type(n) is not int:
            raise PlannerError(f"a {what}'s n is a whole number, not {n!r}")
        if n in seen:
            raise PlannerError(f"{what} {n} is there twice")
        seen.add(n)
        for field in texts:
            if not isinstance(item.get(field), str):
                raise PlannerError(f"{what} {n} has no {field}")


def _proposal(proposal: object) -> None:
    if not isinstance(proposal, dict):
        raise PlannerError("a proposal is not an object")
    name = proposal.get("id")
    if not isinstance(name, str) or not isinstance(proposal.get("title"), str):
        raise PlannerError("a proposal has an id and a title")
    if proposal.get("kind") not in PROPOSAL_KINDS:
        kinds = ", ".join(PROPOSAL_KINDS)
        raise PlannerError(
            f"proposal {name}'s kind is one of {kinds}, not {proposal.get('kind')!r}"
        )
    if not isinstance(proposal.get("path"), str | None):
        raise PlannerError(f"proposal {name}'s path is not text")
    key_points = proposal.get("key_points")
    if not isinstance(key_points, list):
        raise PlannerError(f"proposal {name} has no list of key_points")
    _numbered(key_points, f"proposal {name}'s key point", ("title", "text"))
