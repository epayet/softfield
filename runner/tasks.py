"""Task files: parsing, validation, picking and pre-flight (docs/task-format.md)."""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# A ticket is a goal, the context and acceptance criteria (ADR 07 item 2). "Pattern to
# follow" and "Steps" are optional.
SECTIONS = ("Goal", "Context", "Done when")
_PATH_RE = re.compile(r"`([\w./-]+\.(?:py|js|html|css|md|toml|json|txt))`")
_SYMBOL_RE = re.compile(r"\b(?:def|class)\s+([A-Za-z_]\w*)")


AGENTS = ("junior", "lead")  # who works a ticket (ADR 12 item 9)
# Folders whose tasks pause their dependants: waiting for the lead, or for the owner.
STOPPED = ("escalated", "blocked")


class TaskError(ValueError):
    pass


@dataclass(frozen=True)
class Task:
    id: str
    milestone: int
    depends_on: tuple[str, ...]
    files: tuple[str, ...]
    tests: tuple[str, ...]
    max_diff: int
    finding: str | None
    sections: dict[str, str]
    path: Path
    agent: str = "junior"

    @property
    def goal(self) -> str:
        return self.sections["Goal"].strip().splitlines()[0] if self.sections["Goal"] else ""


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        raise TaskError("task file must start with YAML frontmatter (---)")
    try:
        head, body = text[4:].split("\n---\n", 1)
    except ValueError as exc:
        raise TaskError("frontmatter is not closed with ---") from exc
    meta = yaml.safe_load(head) or {}
    if not isinstance(meta, dict):
        raise TaskError("frontmatter must be a mapping")
    return meta, body


def parse_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    lines: list[str] = []
    for line in body.splitlines():
        if line.startswith("### "):
            if current is not None:
                sections[current] = "\n".join(lines).strip()
            current, lines = line[4:].strip(), []
        elif current is not None:
            lines.append(line)
    if current is not None:
        sections[current] = "\n".join(lines).strip()
    return sections


def _str_tuple(meta: dict[str, Any], key: str, required: bool) -> tuple[str, ...]:
    value = meta.get(key, [] if not required else None)
    if value is None or not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise TaskError(f"'{key}' must be a list of strings")
    if required and not value:
        raise TaskError(f"'{key}' must not be empty")
    return tuple(value)


def parse_task(path: Path, default_max_diff: int) -> Task:
    meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
    task_id = meta.get("id")
    if not isinstance(task_id, str) or task_id != path.stem:
        raise TaskError(f"'id' must match the file name ({path.stem})")
    milestone = meta.get("milestone")
    if not isinstance(milestone, int):
        raise TaskError("'milestone' must be an integer")
    sections = parse_sections(body)
    missing = [name for name in SECTIONS if not sections.get(name)]
    if missing:
        raise TaskError(f"missing sections: {', '.join(missing)}")
    max_diff = meta.get("max_diff", default_max_diff)
    if not isinstance(max_diff, int) or max_diff <= 0:
        raise TaskError("'max_diff' must be a positive integer")
    finding = meta.get("finding")
    agent = meta.get("agent", "junior")
    if agent not in AGENTS:
        raise TaskError(f"'agent' must be one of {', '.join(AGENTS)}")
    return Task(
        id=task_id,
        milestone=milestone,
        depends_on=_str_tuple(meta, "depends_on", required=False),
        files=_str_tuple(meta, "files", required=True),
        tests=_str_tuple(meta, "tests", required=True),
        max_diff=max_diff,
        finding=str(finding) if finding is not None else None,
        sections=sections,
        path=path,
        agent=agent,
    )


def load_dir(directory: Path, default_max_diff: int) -> list[Task]:
    return [parse_task(p, default_max_diff) for p in sorted(directory.glob("*.md"))]


def queued_tests(tasks_dir: Path, current: str) -> set[str]:
    """Test files of the other tasks still in ``ready/`` or ``escalated/`` (ADR 01, item 1).

    Their skeleton tests fail until those tasks are done, so the all-tests gate skips them.
    """
    tests: set[str] = set()
    for name in ("ready", *STOPPED):
        for path in sorted((tasks_dir / name).glob("*.md")):
            if path.stem != current:
                meta, _ = split_frontmatter(path.read_text(encoding="utf-8"))
                tests.update(_str_tuple(meta, "tests", required=False))
    return tests


def task_ids(directory: Path) -> set[str]:
    return {p.stem for p in directory.glob("*.md")}


def stopped_ids(tasks_dir: Path) -> set[str]:
    """Tasks waiting in escalated/ or blocked/: their dependants pause."""
    return set().union(*(task_ids(tasks_dir / name) for name in STOPPED))


def blocked_ids(ready: Iterable[Task], escalated: set[str]) -> set[str]:
    """Ready tasks that (transitively) depend on an escalated task are paused."""
    tasks = list(ready)
    blocked = set(escalated)
    changed = True
    while changed:
        changed = False
        for task in tasks:
            if task.id not in blocked and blocked.intersection(task.depends_on):
                blocked.add(task.id)
                changed = True
    return blocked - escalated


def pick_next(ready: Iterable[Task], done: set[str], paused: set[str]) -> Task | None:
    candidates = [
        t for t in ready if t.id not in paused and all(dep in done for dep in t.depends_on)
    ]
    return min(candidates, key=lambda t: (t.milestone, t.id), default=None)


def preflight(task: Task, repo: Path) -> list[str]:
    """Problems with the task's Context/Pattern references. Empty means OK.

    The ``tests:`` files may not exist yet: juniors write their own (ADR 07 item 4).
    """
    text = task.sections["Context"] + "\n" + task.sections.get("Pattern to follow", "")
    problems = []
    paths = set(_PATH_RE.findall(text))
    for rel in sorted(paths):
        if not (repo / rel).exists() and rel not in (*task.files, *task.tests):  # may be new
            problems.append(f"referenced path does not exist: {rel}")
    symbols = set(_SYMBOL_RE.findall(task.sections["Context"]))
    if symbols:
        corpus = "\n".join(
            (repo / f).read_text(encoding="utf-8")
            for f in (*task.files, *sorted(paths))
            if (repo / f).is_file()
        )
        for name in sorted(symbols):
            if not re.search(rf"\b(?:def|class)\s+{re.escape(name)}\b", corpus):
                problems.append(f"symbol not found in the task's files: {name}")
    return problems


def append_footer(path: Path, fields: dict[str, object]) -> None:
    lines = ["", "```yaml", "# --- runner ---"]
    lines += [f"{key}: {value}" for key, value in fields.items()]
    lines.append("```")
    with path.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
