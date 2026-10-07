"""The planning room's threads and replies (ADR 20 items 3–5, f6 D1–D3). No AI in it.

A thread is a card's (by its short key, ``f7``) or the ``general`` one. Each message the owner
sends is a ``plan_message`` request (f6 D1), queued as its own ``planner`` row whose subject
names the thread and the request (``f7#41``); the message itself stays in its request row.
The lead's reply ends with a fenced ``json`` block (D2), checked here before it is recorded.
"""

import json
import re
import subprocess
import unicodedata
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runner import prompts
from runner.tasks import (
    AREAS,
    BUGS,
    DEFAULT_PRIORITY,
    TaskError,
    milestone_key,
    milestone_order,
    short_key,
)

PLANNER = "planner"  # the role, and the queued job's kind (`dispatch.PLANNER`)
DRAFTS = ("docs/**", "tasks/later/**")  # what a card's planner job may edit (f6 D4)
DRAFT_DIRS = ("docs/", "tasks/later/")
READY_DIR = "tasks/ready/"
PLAN_MESSAGE = "plan_message"  # the request kind: subject the thread, value `message`'s JSON
PLANNING = "planning"  # the owner item a reply raises, about its thread (ADR 20 item 9)
GENERAL = "general"
MERGE = "merge"  # a card that repeats another, closed into it once approved (f6-12)
REPLAN = "replan"  # a running milestone redirected: it may change its ready tickets (f6-13)
PROPOSAL_KINDS = ("adr", "mockup", "plan", "seed", REPLAN, MERGE)
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


def plan_branch(thread: str) -> str | None:
    """The card's branch its drafts go on (f6 D4): ``plan/f7``. The general thread has none."""
    return None if thread == GENERAL else f"plan/{thread}"


def drafts(card: str) -> tuple[str, ...]:
    """What a card's planner job may edit: the drafts, and its card's ready tickets for a
    ``replan`` (f6-13)."""
    return (*DRAFTS, f"{READY_DIR}{card}-*")


def is_draft(path: str, card: str | None = None) -> bool:
    """Whether a planner job may change ``path`` on its plan branch (f6 D4): docs and the
    tickets in ``tasks/later/``, never code or ``tasks/done/``. Given its ``card``, the card's
    own tickets in ``tasks/ready/`` too, which only a ``replan`` may change (f6-13)."""
    if ".." in path.split("/"):
        return False
    return path.startswith(DRAFT_DIRS) or (card is not None and is_ready_ticket(path, card))


def is_ready_ticket(path: str, card: str) -> bool:
    """Whether ``path`` is one of ``card``'s tickets in ``tasks/ready/``: ``f7-01-….md``."""
    return re.fullmatch(rf"{READY_DIR}{re.escape(card)}-\d[\w.-]*\.md", path) is not None


def draft(repo: Path, thread: str, path: str) -> bytes | None:
    """A card's draft for the dashboard: the file at ``path`` on ``plan/<thread>`` while that
    branch exists, else on main; None when there is none, or when ``thread`` isn't a thread
    or ``path`` isn't a draft. It reads git only: planner jobs check the plan branch out."""
    try:
        thread = thread_key(thread)
    except PlannerError:
        return None
    # Every part a name: `./` and `//` mean other things to git's `<ref>:<path>`
    if not isinstance(path, str) or not is_draft(path):
        return None
    if any(part in ("", ".") or "\0" in part for part in path.split("/")):
        return None
    branch = plan_branch(thread)
    ref = f"refs/heads/{branch}" if branch else _MAIN
    if _git(repo, "rev-parse", "--verify", "-q", ref) is None:
        ref = _MAIN
    return _git(repo, "cat-file", "blob", f"{ref}:{path}")


_MAIN = "refs/heads/main"  # loop.MAIN; loop imports this module


def _git(repo: Path, *args: str) -> bytes | None:
    proc = subprocess.run(["git", *args], cwd=repo, capture_output=True, check=False)
    return proc.stdout if proc.returncode == 0 else None


def proposal_of(subject: object) -> tuple[str, str]:
    """A ``send_back``'s thread and proposal id, from its subject: ``f7/adr-23``."""
    thread, sep, wanted = subject.partition("/") if isinstance(subject, str) else ("", "", "")
    if not sep or not wanted:
        raise PlannerError(f"a proposal is <thread>/<id>, not {subject!r}")
    return thread_key(thread), wanted


def sent_back(proposal: Mapping[str, Any], text: str, comments: Mapping[int, str]) -> str:
    """The message a ``send_back`` becomes (f6 D1): the proposal, the owner's comments on its
    key points by number and title, then their words."""
    key_points = proposal.get("key_points")
    titles = {
        point.get("n"): point.get("title")
        for point in (key_points if isinstance(key_points, list) else [])
        if isinstance(point, dict)
    }
    lines = [f"I sent back your proposal “{proposal.get('title')}” ({proposal.get('id')})."]
    for n, comment in comments.items():
        title = f" ({titles[n]})" if isinstance(titles.get(n), str) else ""
        lines.append(f"- On its key point {n}{title}: {comment}")
    return "\n".join(lines) + (f"\n\n{text}" if text else "")


# A ticket relies on an ADR it names: by its path, or as "ADR 20".
_ADR_NAMED_RE = re.compile(r"\bdocs/adr/(\d+)-[\w.-]*\.md\b|\bADR (\d+)\b")
_PROPOSED_RE = re.compile(r"^- \*\*Status:\*\*[ \t]*Proposed\b", re.MULTILINE)
READY = "ready"  # the card's state once its plan is approved (f5 D4)
_STATE_RE = re.compile(r"\*\*State:\*\*[ \t]*[^·*\n]*?(?=[ \t]*(?:·|\*|$))", re.MULTILINE)


def named_adrs(text: str) -> set[int]:
    """The ADRs a ticket's text names, by number."""
    return {int(path or words) for path, words in _ADR_NAMED_RE.findall(text)}


def is_proposed(adr: str) -> bool:
    """Whether an ADR's status line still says Proposed."""
    return _PROPOSED_RE.search(adr) is not None


def ready_card(doc: str) -> str:
    """A card's milestone doc with its state set to ready, in its header (above the first
    ``## ``); a header without a state gets one under its title."""
    section = re.search(r"^## ", doc, re.MULTILINE)
    end = section.start() if section else len(doc)
    header, body = doc[:end], doc[end:]
    if _STATE_RE.search(header):
        return _STATE_RE.sub(f"**State:** {READY}", header, count=1) + body
    title, _, rest = doc.partition("\n")
    return f"{title}\n\n> **State:** {READY}\n{rest}"


# --- planting: a seed card, written by the runner without Claude (ADR 20 item 8, f6 D5) -------

IDEA = "idea"  # a planted card's state (f5 D4)
SEED = "seed"  # the proposal kind a general thread's idea comes as
SERIES = {"factory": "f", "product": "m"}  # an area's keys (ADR 19 item 2b)
_PLANT_VALUE = "a plant request is JSON with a title, its thoughts and an area"
_MAX_TITLE = 120
_MAX_THOUGHTS = 20_000
_SLUG_WORDS = 6
_TICKET_KEY_RE = re.compile(r"([a-z]+\d+)-\d")  # a ticket id's milestone, `f6` of `f6-04-…`


def slug(title: str) -> str:
    """A card's slug from its title: its first words, lowercase ASCII, starting with a letter
    as a key's slug must (``idea-2fa-…``); ``idea`` when no word is left."""
    plain = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode().lower()
    words = re.findall(r"[a-z0-9]+", plain)[:_SLUG_WORDS]
    if not words or not words[0][0].isalpha():
        words = [IDEA, *words]
    return "-".join(words)


def next_key(repo: Path, area: str) -> str:
    """The next free short key in the area's series: one past the highest a milestone doc or a
    ticket uses (``f7`` after ``f6-planning-room``)."""
    prefix = SERIES[area]
    keys = [path.stem for path in (repo / "docs" / "milestones").glob("*.md")]
    for path in (repo / "tasks").glob("*/*.md"):
        if found := _TICKET_KEY_RE.match(path.stem):
            keys.append(found[1])
    highest = 0
    for key in keys:
        try:
            series, number = milestone_order(milestone_key(key))
        except TaskError:  # bugs, a README
            continue
        if series == prefix:
            highest = max(highest, number)
    return f"{prefix}{highest + 1}"


def card_named(repo: Path, name: str) -> str | None:
    """The milestone doc whose slug is ``name``, in any series, if there is one."""
    for path in sorted((repo / "docs" / "milestones").glob(f"*-{name}.md")):
        if path.stem.partition("-")[2] == name:
            return path.stem
    return None


def _words(title: object, thoughts: object) -> tuple[str, str]:
    """An idea's title, on one line, and its thoughts, both trimmed and within bounds."""
    if not isinstance(title, str) or not title.strip() or len(title.strip().splitlines()) > 1:
        raise PlannerError("an idea has a title, on one line")
    if not isinstance(thoughts, str):
        raise PlannerError(_PLANT_VALUE)
    if len(title.strip()) > _MAX_TITLE:
        raise PlannerError(f"an idea's title is at most {_MAX_TITLE} characters")
    if len(thoughts.strip()) > _MAX_THOUGHTS:
        raise PlannerError(f"an idea's thoughts are at most {_MAX_THOUGHTS} characters")
    return title.strip(), thoughts.strip()


def _area(data: Mapping[str, Any]) -> str:
    area = data.get("area")
    if area in (None, ""):
        return "factory"  # product work is on hold (the owner, 2026-10-04)
    if area not in AREAS:
        raise PlannerError(f"an idea's area is {' or '.join(AREAS)}, not {area!r}")
    return str(area)


def _plant_data(value: object) -> dict[str, Any]:
    try:
        data = json.loads(value) if isinstance(value, str) else None
    except json.JSONDecodeError:
        data = None
    if not isinstance(data, dict):
        raise PlannerError(_PLANT_VALUE)
    return data


def planting(value: object) -> tuple[str, str, str]:
    """A ``plant`` request's value (f6 D1): the idea's title, its thoughts and its area
    (factory unless given)."""
    data = _plant_data(value)
    title, thoughts = _words(data.get("title"), data.get("thoughts") or "")
    return title, thoughts, _area(data)


def seed_words(proposal: Mapping[str, Any]) -> tuple[str, str]:
    """A ``seed`` proposal's title, and its key points as the card's thoughts."""
    key_points = proposal.get("key_points")
    lines = [
        f"{point.get('n')}. {point.get('title')}: {point.get('text')}"
        for point in (key_points if isinstance(key_points, list) else [])
        if isinstance(point, dict)
    ]
    return _words(proposal.get("title"), "\n".join(lines))


def seed_area(value: object) -> str:
    """The area an approved seed is planted in: the request's, if it gives one, else factory."""
    return "factory" if value in (None, "") else _area(_plant_data(value))


def seed_card(key: str, title: str, thoughts: str, area: str, note: str) -> str:
    """A planted card's milestone doc: an idea at the default priority, the owner's words
    under Notes. A quoted line in them is escaped: a sign-off is read from one anywhere."""
    notes = re.sub(r"^>", r"\\>", thoughts, flags=re.MULTILINE) or "(none)"
    header = f"> **State:** {IDEA} · **Priority:** {DEFAULT_PRIORITY} · **Area:** {area}"
    said = f"\n> {note}" if note else ""
    return f"# Milestone {key.upper()}: {title}\n\n{header}{said}\n\n## Notes\n{notes}\n"


def cards(repo: Path) -> set[str]:
    """Every card's short key, from its milestone doc: the cards a ``merge`` may name."""
    found = set()
    for path in (repo / "docs" / "milestones").glob("*.md"):
        try:
            key = milestone_key(path.stem)
        except TaskError:  # a README
            continue
        if key != BUGS:
            found.add(short_key(key))
    return found


# --- merging a duplicate card into the card it repeats (f6-12, D2 and D4) ---------------------

_CARD_DOC_RE = re.compile(r"docs/milestones/([a-z][a-z0-9-]*)\.md")
_HEADING_RE = re.compile(r"^(#{1,4}) ", re.MULTILINE)


def merge_cards(proposal: Mapping[str, Any]) -> tuple[str, str]:
    """A ``merge``'s duplicate (from its ``path``) and the card it joins (``into``), as short
    keys; refused when either isn't a card's, or they are the same."""
    name = proposal.get("id")
    path = proposal.get("path")
    found = _CARD_DOC_RE.fullmatch(path) if isinstance(path, str) else None
    try:
        duplicate = short_key(milestone_key(found[1])) if found else None
    except TaskError:
        duplicate = None
    if duplicate is None or duplicate == BUGS:
        raise PlannerError(f"merge {name}'s path is a card's doc in docs/milestones/, not {path!r}")
    into = proposal.get("into")
    try:
        kept = thread_key(into)
    except PlannerError:
        raise PlannerError(f"merge {name}'s into is the card it joins, not {into!r}") from None
    if kept in (GENERAL, duplicate):
        raise PlannerError(f"merge {name}'s into is another card, not {into!r}: not into itself")
    return duplicate, kept


def merge_words(proposal: Mapping[str, Any]) -> str:
    """A ``merge`` in words: ``merge F12 into F10``."""
    duplicate, kept = merge_cards(proposal)
    return f"merge {thread_name(duplicate)} into {thread_name(kept)}"


def card_notes(doc: str) -> str:
    """What a card holds below its header, for the card it merges into: its Notes section, or
    every section when it has none; headings two levels down, quoted lines escaped (a sign-off
    is read from one anywhere)."""
    notes = re.search(r"^## Notes[ \t]*\n(.*?)(?=^## |\Z)", doc, re.MULTILINE | re.DOTALL)
    first = re.search(r"^## ", doc, re.MULTILINE)
    text = notes[1] if notes else (doc[first.start() :] if first else "")
    text = _HEADING_RE.sub(lambda m: f"{m[1]}## ", text.strip())
    return re.sub(r"^>", r"\\>", text, flags=re.MULTILINE) or "(none)"


def merged_card(doc: str, notes: str, source: str) -> str:
    """The kept card's doc with ``notes`` at the end of its Notes section (made when it has
    none), under a heading saying where they came from."""
    block = f"### {source}\n{notes}\n"
    section = re.search(r"^## Notes[ \t]*\n.*?(?=^## |\Z)", doc, re.MULTILINE | re.DOTALL)
    if section is None:
        return f"{doc.rstrip()}\n\n## Notes\n{block}"
    body = section[0].rstrip("\n")
    after = doc[section.end() :]
    return f"{doc[: section.start()]}{body}\n\n{block}" + (f"\n{after}" if after else "")


def prompt(
    thread: str, text: str, comments: Mapping[int, str], threads: Collection[str] = ()
) -> str:
    """The planner job's prompt for one message: a card's drafts on its plan branch, none on
    the general thread (``prompts.PLANNER``); the other threads named, to spot a repeat."""
    lines = "".join(f"- On your point {n}: {comment}\n" for n, comment in comments.items())
    said = f"\nTheir comments on your last points:\n{lines}" if lines else ""
    others = [t for t in threads if t not in (thread, GENERAL)]
    others += [GENERAL] if GENERAL in threads and thread != GENERAL else []
    template = prompts.PLANNER_GENERAL if thread == GENERAL else prompts.PLANNER
    return template.format(
        thread=thread_name(thread),
        card=thread,
        comments=said,
        text=text or "(none)",
        threads=", ".join(thread_name(t) for t in others) or "none",
    )


def parse_reply(text: str, known: Collection[str] = ()) -> Reply:
    """A reply's free text and its last ``json`` block's points and proposals (f6 D2). A
    ``merge`` must name ``known`` cards (``cards``). A reply whose block is missing or broken
    is all text, with a note saying why."""
    whole = text.strip()
    blocks = list(_BLOCK_RE.finditer(whole))
    if not blocks:
        return Reply(whole, note="the reply has no json block, so its points weren't read")
    block = blocks[-1]
    try:
        points, proposals = _checked(block[1], known)
    except PlannerError as exc:
        return Reply(whole, note=f"the reply's json block was not read: {exc}")
    around = [whole[: block.start()].strip(), whole[block.end() :].strip()]
    return Reply("\n\n".join(part for part in around if part), points, proposals)


def stored_text(reply: Reply) -> str:
    """What the thread shows: the reply's text, then the note, if any."""
    return reply.text if reply.note is None else f"{reply.text}\n\n({reply.note}.)".strip()


def _checked(
    block: str, known: Collection[str]
) -> tuple[tuple[dict[str, Any], ...], tuple[dict[str, Any], ...]]:
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
        _proposal(proposal, known)
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


def _proposal(proposal: object, known: Collection[str]) -> None:
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
    if proposal["kind"] == MERGE:
        for card in merge_cards(proposal):
            if card not in known:
                raise PlannerError(f"merge {name} names {card}, but {card} is no card")
