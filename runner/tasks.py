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


AGENTS = ("developer", "lead")  # who works a ticket (ADR 12 item 9)
_AGENT_SYNONYMS = {"junior": "developer"}  # old tickets' name for a developer (ADR 14 item 1)
# Folders whose tasks pause their dependants: waiting for the lead, or for the owner.
STOPPED = ("escalated", "blocked")


class TaskError(ValueError):
    pass


# A milestone is Coucou's `mN` (a bare number N in frontmatter or on the command line) or a
# named series like the factory's `f1` (the f1 plan): lowercase letters, then a number. It
# may carry a slug, `f3-factory-line` (ADR 16 item 6); its short form `f3` prefixes its ticket
# ids. A slug starts with a letter, so a ticket id is never a key.
_KEY_RE = re.compile(r"([a-z]+)(0|[1-9]\d*)(-[a-z][a-z0-9]*(?:-[a-z0-9]+)*)?")


def milestone_key(value: object) -> str:
    """``4``, ``"4"`` and ``"m4"`` are ``"m4"``; ``"f1"`` and ``"f3-factory-line"`` are
    themselves."""
    if isinstance(value, bool):
        raise TaskError(f"'milestone' must be a number or a key like f1, not {value!r}")
    text = str(value)
    if text.isascii() and text.isdigit() and (text == "0" or not text.startswith("0")):
        return f"m{text}"
    if isinstance(value, str) and _KEY_RE.fullmatch(text):
        return text
    raise TaskError(f"'milestone' must be a number or a key like f1, not {value!r}")


def command_arg(milestone: str) -> str:
    """What the owner types: ``4`` for m4 (as before), ``f1`` for f1, a named key whole."""
    return milestone[1:] if milestone.startswith("m") and milestone[1:].isdigit() else milestone


def _key_parts(key: str) -> tuple[str, int]:
    match = _KEY_RE.fullmatch(key)
    if match is None:
        raise TaskError(f"not a milestone key: {key!r}")
    return match.group(1), int(match.group(2))


def short_key(key: str) -> str:
    """``f3`` for ``f3-factory-line``: its tickets' prefix, ``f3-01-…``."""
    prefix, number = _key_parts(key)
    return f"{prefix}{number}"


def _named(key: str) -> bool:
    return key != short_key(key)


def next_milestone_key(key: str) -> str:
    """The next milestone's short key: ``f4`` after ``f3`` or ``f3-factory-line``."""
    prefix, number = _key_parts(key)
    return f"{prefix}{number + 1}"


def milestone_order(key: str) -> tuple[str, int]:
    """Sorts m9 before m10; a named key sorts as its short form."""
    return _key_parts(key)


def _doc_keys(repo: Path) -> dict[str, str]:
    """Short key -> full key, from each ``docs/milestones/<full key>.md``."""
    found: dict[str, str] = {}
    for path in sorted((repo / "docs" / "milestones").glob("*-*.md")):
        if _KEY_RE.fullmatch(path.stem):
            found.setdefault(short_key(path.stem), path.stem)
    return found


def full_key(repo: Path, key: str) -> str:
    """A key in either form, as its doc names it: ``f3`` is ``f3-factory-line`` once
    ``docs/milestones/f3-factory-line.md`` exists; otherwise the key as given."""
    return key if _named(key) else _doc_keys(repo).get(key, key)


def named_keys(repo: Path) -> dict[str, str]:
    """Short key -> full key, from the tickets' frontmatter and then the docs (which win)."""
    found: dict[str, str] = {}
    for path in sorted((repo / "tasks").glob("*/*.md")):
        try:
            meta, _ = split_frontmatter(path.read_text(encoding="utf-8"))
            key = milestone_key(meta.get("milestone"))
        except (TaskError, yaml.YAMLError, UnicodeDecodeError):
            continue
        if _named(key):
            found.setdefault(short_key(key), key)
    return found | _doc_keys(repo)


def milestone_arg(repo: Path, value: object) -> str:
    """A command's milestone in either form (``f3``, ``f3-factory-line``, ``4``) as its full
    key, from its doc or its tickets."""
    key = milestone_key(value)
    return key if _named(key) else named_keys(repo).get(key, key)


def milestone_file(repo: Path, folder: str, key: str) -> Path:
    """``docs/<folder>/<full key>.md``, or an existing one named by the short key (f2's)."""
    path = repo / "docs" / folder / f"{key}.md"
    short = repo / "docs" / folder / f"{short_key(key)}.md"
    return short if not path.is_file() and short.is_file() else path


@dataclass(frozen=True)
class Task:
    id: str
    milestone: str  # a key: m4, f1
    depends_on: tuple[str, ...]
    files: tuple[str, ...]
    tests: tuple[str, ...]
    max_diff: int
    finding: str | None
    sections: dict[str, str]
    path: Path
    agent: str = "developer"
    commands: tuple[str, ...] = ()  # a lead ticket's extra Bash prefixes (f1's probes)
    difficulty: int | None = None  # 1 to 10, set at plan time (ADR 14 item 5)
    difficulty_corrected: int | None = None  # set by the lead at review when it was off

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


# A lead ticket's `commands:` may never run git beyond the read-only tools it already has,
# the owner's commands, or the loop itself; nor a prefix of any of them (`uv run`).
_REFUSED_COMMANDS = tuple(
    ["git"]
    + [f"uv run runner {c}" for c in ("signoff", "accept", "reject", "milestone", "run", "review")]
)
_DRY_RUN = "uv run runner run --dry-run"  # read-only: a replan checks its tickets with it
_COMMAND_RE = re.compile(r"[\w@./:=+-]+( [\w@./:=+-]+)*")


def _commands(meta: dict[str, Any], agent: str) -> tuple[str, ...]:
    commands = _str_tuple(meta, "commands", required=False)
    if commands and agent != "lead":
        raise TaskError("only a lead ticket may name 'commands'")
    for command in commands:
        refused = command != _DRY_RUN and any(
            command == r or command.startswith(r + " ") or r.startswith(command + " ")
            for r in _REFUSED_COMMANDS
        )
        if refused or not _COMMAND_RE.fullmatch(command):
            raise TaskError(f"'commands' may not include {command!r}")
    return commands


def difficulty(meta: dict[str, Any], key: str) -> int | None:
    """``difficulty`` or ``difficulty_corrected``: absent, or an integer from 1 to 10 (the
    rubric is in docs/task-writing.md)."""
    if key not in meta:
        return None
    value = meta[key]
    if type(value) is not int or not 1 <= value <= 10:
        raise TaskError(f"'{key}' must be an integer from 1 to 10, not {value!r}")
    return value


def parse_task(path: Path, default_max_diff: int) -> Task:
    meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
    task_id = meta.get("id")
    if not isinstance(task_id, str) or task_id != path.stem:
        raise TaskError(f"'id' must match the file name ({path.stem})")
    milestone = milestone_key(meta.get("milestone"))
    if path.parent.parent.name == "tasks":  # tasks/<folder>/<id>.md: its repo has the docs
        milestone = full_key(path.parent.parent.parent, milestone)
    sections = parse_sections(body)
    missing = [name for name in SECTIONS if not sections.get(name)]
    if missing:
        raise TaskError(f"missing sections: {', '.join(missing)}")
    max_diff = meta.get("max_diff", default_max_diff)
    if not isinstance(max_diff, int) or max_diff <= 0:
        raise TaskError("'max_diff' must be a positive integer")
    finding = meta.get("finding")
    agent = meta.get("agent", "developer")
    agent = _AGENT_SYNONYMS.get(agent, agent) if isinstance(agent, str) else agent
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
        commands=_commands(meta, agent),
        difficulty=difficulty(meta, "difficulty"),
        difficulty_corrected=difficulty(meta, "difficulty_corrected"),
    )


def load_dir(directory: Path, default_max_diff: int) -> list[Task]:
    return [parse_task(p, default_max_diff) for p in sorted(directory.glob("*.md"))]


def queued_tests(tasks_dir: Path, current: str) -> set[str]:
    """Test files of the other developer tasks still in ``ready/``, ``escalated/`` or
    ``blocked/`` (ADR 01, item 1), less the current task's own.

    Their skeleton tests fail until those tasks are done, so the all-tests gate skips them.
    A lead ticket writes its tests in its own job, so they are never skeletons (f1-33).
    """
    tests: set[str] = set()
    own: set[str] = set()
    for name in ("ready", *STOPPED):
        for path in sorted((tasks_dir / name).glob("*.md")):
            meta, _ = split_frontmatter(path.read_text(encoding="utf-8"))
            listed = _str_tuple(meta, "tests", required=False)
            if path.stem == current:
                own.update(listed)
            elif meta.get("agent") != "lead":
                tests.update(listed)
    return tests - own


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
    return min(candidates, key=lambda t: (milestone_order(t.milestone), t.id), default=None)


def preflight(task: Task, repo: Path) -> list[str]:
    """Problems with the task's Context/Pattern references. Empty means OK.

    The ``tests:`` files may not exist yet: developers write their own (ADR 07 item 4).
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


_FOOTER_BLOCK_RE = re.compile(r"\n```yaml\n# --- runner ---\n.*?```\n", re.DOTALL)


def carry_footers(source: Path, target: Path) -> None:
    """Copy source's runner footers onto target, a rewritten copy of the same ticket that has
    none, so a requeued ticket keeps the attempts and tokens of its earlier runs."""
    target_text = target.read_text(encoding="utf-8")
    if "# --- runner ---" in target_text:
        return
    blocks = _FOOTER_BLOCK_RE.findall(source.read_text(encoding="utf-8"))
    if blocks:
        target.write_text(target_text.rstrip("\n") + "\n" + "".join(blocks), encoding="utf-8")
