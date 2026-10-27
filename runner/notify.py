"""Notifications to a closed phone, through ntfy (ADR 31).

The runner sends one the moment it stores something that needs the owner: what kind of
thing it is and which project, never a card's title, a reply or an item's text (item 1),
opening the dashboard's page where the owner acts. Nothing is kept about the sending
(item 4): a failure or the 5-second limit is a short reason for the run's report.
"""

import secrets
import socket
import sqlite3
import string
import tomllib
import urllib.request
from pathlib import Path
from urllib.parse import quote

from runner import config, metrics
from runner.tasks import TaskError, short_key

TIMEOUT = 5  # seconds; a notification never holds a job up longer (item 3)
PORT = 8765  # `softfield dashboard --lan`'s
NOT_SENT = "The phone's notification wasn't sent"
TEST = "Notifications work"  # `softfield notify test`'s words
TOPIC_LENGTH = 24
NTFY = "https://ntfy.sh/"

REPLY = "The lead answered you"
LOOK = "The lead looked at a blocked ticket"
FAILED = "The lead couldn't answer you"
SIGNOFF = "A card is ready for your sign-off"
REVIEW_STOP = "A review stopped"
DECISION = "A ticket needs your decision"
RESERVE = "Claude's reserve: your choice"
OTHER = "Something needs you"
# Each owner item's kind (runner/owner.py, runner/loop.py, runner/requests.py): its words,
# and whether it opens its card's thread rather than the Overview (item 1)
_KINDS = {
    "planning": (REPLY, True),
    "signoff": (SIGNOFF, True),
    "review-stop": (REVIEW_STOP, True),
    "adr": (DECISION, False),
    "escalated": (DECISION, False),
    "blocked": (DECISION, False),
    "reserve": (RESERVE, False),
    "five-hour": (RESERVE, False),
}
OVERVIEW = "/"


def thread_page(card: str) -> str:
    """A card's thread by its short key (``f7`` for ``f7-one-queue``); a thread named
    otherwise (``general``) as it is."""
    try:
        return f"/planning/{short_key(card)}"
    except TaskError:
        return f"/planning/{card}"


def item_message(kind: str, subject: str) -> tuple[str, str]:
    """An owner item's words and the page it opens: its card's thread or the Overview."""
    words, on_card = _KINDS.get(kind, (OTHER, False))
    return words, thread_page(subject) if on_card else OVERVIEW


def planner_message(thread: str, *, looked: bool, ok: bool) -> tuple[str, str]:
    """What a planner job's end says, opening the card's thread: a reply, the runner's own
    look at a blocked ticket, or a job that failed."""
    words = REPLY if ok and not looked else LOOK if ok else FAILED
    return words, thread_page(thread)


def items_message(items: list[tuple[str, str]], card: str) -> tuple[str, str] | None:
    """The one notification for the items a verdict about ``card`` opened (item 2)."""
    if not items:
        return None
    if len(items) == 1:
        return item_message(*items[0])
    return f"{len(items)} things need you on one card", thread_page(card)


def open_items(conn: sqlite3.Connection, project_id: int) -> set[tuple[str, str]]:
    """The project's open items, read before an upsert: one stored again while open is no
    news, a new one or one that opens again is (item 3)."""
    return {(r["kind"], r["subject"]) for r in metrics.open_owner_items(conn, project_id)}


def lan_ip() -> str:
    """This machine's home-network address: the source address of a UDP socket "connected"
    to a public IP. A UDP connect only picks the route; it sends nothing. OSError if none."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
        udp.connect(("1.1.1.1", 80))
        return str(udp.getsockname()[0])


def _home() -> str:
    """The dashboard's home address, as `softfield dashboard --lan` serves it."""
    try:
        return f"http://{lan_ip()}:{PORT}"
    except OSError:
        return f"http://127.0.0.1:{PORT}"


def _post(address: str, body: bytes, headers: dict[str, str]) -> None:
    """The one web request; tests replace it, so none reaches the network."""
    request = urllib.request.Request(address, data=body, headers=headers, method="POST")  # noqa: S310 - checked
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:  # noqa: S310 - checked
        response.read()


def send(title: str, words: str, path: str) -> str | None:
    """One notification, "<title> · <words>", opening ``path`` on the dashboard. None when
    it went or no `[notify] ntfy` is set; else why not, for the run's report. Never raises."""
    try:
        address = config.machine_ntfy()
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return f"{NOT_SENT}: the machine's settings can't be read ({exc})."
    if address is None:
        return None
    if not address.startswith(("https://", "http://")):
        return f"{NOT_SENT}: [notify] ntfy is no web address."
    try:
        headers = {"Title": title, "Click": f"{_home()}{path}"}
        _post(address, f"{title} · {words}".encode(), headers)
    except Exception as exc:  # a timeout, a refusal, no network: the job goes on
        return f"{NOT_SENT} ({type(exc).__name__}: {exc})."
    return None


def to_owner(project: str, words: str, path: str) -> str | None:
    """``send`` for a project's page: titled by the project, opening it on that project."""
    return send(project, words, f"{path}?project={quote(project, safe='')}")


# --- `softfield notify setup` -------------------------------------------------------------


def _topic(address: str) -> str:
    return address.rstrip("/").rsplit("/", 1)[-1]


def setup(machine: Path) -> tuple[str, bool]:
    """The topic in the machine's `[notify]`, and whether it was written now: a new one of
    random lowercase letters and digits when it has none; every other line is kept."""
    text = machine.read_text(encoding="utf-8") if machine.is_file() else ""
    table = tomllib.loads(text).get("notify")
    if isinstance(table, dict) and table.get("ntfy"):
        return _topic(str(table["ntfy"])), False
    alphabet = string.ascii_lowercase + string.digits
    topic = "".join(secrets.choice(alphabet) for _ in range(TOPIC_LENGTH))
    line = f'ntfy = "{NTFY}{topic}"\n'
    lines = text.splitlines(keepends=True)
    header = next((i for i, x in enumerate(lines) if x.strip() == "[notify]"), None)
    if header is not None:  # the table without its address, or with an empty one
        empty = None
        for i in range(header + 1, len(lines)):
            if lines[i].lstrip().startswith("["):  # the next table
                break
            if lines[i].split("=")[0].strip() == "ntfy":
                empty = i
        if empty is None:
            lines.insert(header + 1, line)
        else:  # a second key would leave the whole file unreadable
            lines[empty] = line
        new = "".join(lines)
    else:
        before = "" if not text else "\n" if text.endswith("\n") else "\n\n"
        new = f"{text}{before}[notify]\n{line}"
    machine.parent.mkdir(parents=True, exist_ok=True)
    machine.write_text(new, encoding="utf-8")
    return topic, True
