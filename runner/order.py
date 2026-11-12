"""The queue's order (ADR 45, F222 D1): a project's ``.softfield/order.txt``, one open card's
short key (``f222``) or bug ticket's id per line, first in line first.

Only the runner writes it (`runner.requests`: the move and a drag); the pick reads it
(`runner.loop`). What the list doesn't name comes after all it names, and a line for a card or
bug that is done or gone orders nothing.
"""

from collections.abc import Iterable, Sequence
from pathlib import Path

from runner.tasks import BUGS, Task, short_key

ORDER_FILE = ".softfield/order.txt"


def order_path(repo: Path) -> Path:
    return repo / ORDER_FILE


def read_order(repo: Path) -> list[str] | None:
    """The list's keys, first first, each once and without blank lines; None when the project
    has no list (or it can't be read as a file)."""
    try:
        text = order_path(repo).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return list(dict.fromkeys(line.strip() for line in text.splitlines() if line.strip()))


def order_text(keys: Iterable[str]) -> str:
    """The list's text: one key per line."""
    return "".join(f"{key}\n" for key in keys)


def place_key(task: Task) -> str:
    """The key that places ``task`` on the list: a bug's own id, else its card's short key."""
    return task.id if task.milestone == BUGS else short_key(task.milestone)


def places(keys: Sequence[str], tasks: Iterable[Task]) -> dict[str, int]:
    """Each task's `place_key` mapped to its place on the list, 0 first; one the list doesn't
    name gets a place after all it names. The map `runner.tasks.task_priority` reads."""
    listed = {key: n for n, key in enumerate(keys)}
    return {place_key(t): listed.get(place_key(t), len(keys)) for t in tasks}
