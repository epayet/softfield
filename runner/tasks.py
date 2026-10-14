"""Task files: parsing, validation, picking and pre-flight (docs/task-format.md)."""

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# A ticket is a goal, the context and acceptance criteria (ADR 07 item 2). "Pattern to
# follow" and "Steps" are optional.
SECTIONS = ("Goal", "Context", "Done when")
_PATH_RE = re.compile(r"`([\w./-]+\.(?:py|js|html|css|md|toml|json|txt))`")
# Code only: `def name` in backticks, or followed by ( or : as in a code block; prose such as
# "adds a class to" names no symbol (f42-02)
_SYMBOL_RE = re.compile(r"`(?:def|class)\s+([A-Za-z_]\w*)|\b(?:def|class)\s+([A-Za-z_]\w*)\s*[(:]")


AGENTS = ("developer", "lead")  # who works a ticket (ADR 12 item 9)
_AGENT_SYNONYMS = {"junior": "developer"}  # old tickets' name for a developer (ADR 14 item 1)
# Folders whose tasks pause their dependants: waiting for the lead, or for the owner.
STOPPED = ("escalated", "blocked")
# Tickets set aside: never taken, until the owner queues one again (ADR 17 item 3).
LATER = "later"


class TaskError(ValueError):
    pass


# A milestone is Coucou's `mN` (a bare number N in frontmatter or on the command line) or a
# named series like the factory's `f1` (the f1 plan): lowercase letters, then a number. It
# may carry a slug, `f3-factory-line` (ADR 16 item 6); its short form `f3` prefixes its ticket
# ids. A slug starts with a letter, so a ticket id is never a key.
_KEY_RE = re.compile(r"([a-z]+)(0|[1-9]\d*)(-[a-z][a-z0-9]*(?:-[a-z0-9]+)*)?")
# ADR 19 item 2: bug tickets, `bug-<nn>-<slug>`, belong to this standing key, outside the
# milestones: never planned, reviewed or signed off; done when they merge.
BUGS = "bugs"
_BUG_ID_RE = re.compile(r"bug-\d{2,}-[a-z0-9]+(?:-[a-z0-9]+)*")
AREAS = ("factory", "product")  # ADR 19 item 2b
BUG_PRIORITY = 50  # f5 D5: a bug's default
DEFAULT_PRIORITY = 100  # f5 D4: a milestone card's default, so a ticket's with neither


def milestone_key(value: object) -> str:
    """``4``, ``"4"`` and ``"m4"`` are ``"m4"``; ``"f1"``, ``"f3-factory-line"`` and
    ``"bugs"`` are themselves."""
    if isinstance(value, bool):
        raise TaskError(f"'milestone' must be a number or a key like f1, not {value!r}")
    text = str(value)
    if text.isascii() and text.isdigit() and (text == "0" or not text.startswith("0")):
        return f"m{text}"
    if isinstance(value, str) and (text == BUGS or _KEY_RE.fullmatch(text)):
        return text
    raise TaskError(f"'milestone' must be a number or a key like f1, not {value!r}")


def command_arg(milestone: str) -> str:
    """What the owner types: ``4`` for m4 (as before), ``f1`` for f1, a named key whole."""
    return milestone[1:] if milestone.startswith("m") and milestone[1:].isdigit() else milestone


def ticket_prefix(key: str) -> str:
    """What a milestone's ticket ids start with: ``f3`` for ``f3-factory-line``, ``bug`` for
    ``bugs``."""
    return "bug" if key == BUGS else short_key(key)


def _key_parts(key: str) -> tuple[str, int]:
    if key == BUGS:  # before every milestone at equal priorities (f5 D6)
        return BUGS, 0
    match = _KEY_RE.fullmatch(key)
    if match is None:
        raise TaskError(f"not a milestone key: {key!r}")
    return match.group(1), int(match.group(2))


def short_key(key: str) -> str:
    """``f3`` for ``f3-factory-line``: its tickets' prefix, ``f3-01-…``. ``bugs`` is itself."""
    if key == BUGS:
        return key
    prefix, number = _key_parts(key)
    return f"{prefix}{number}"


def _named(key: str) -> bool:
    return key != short_key(key)


def next_milestone_key(key: str) -> str:
    """The next milestone's short key: ``f4`` after ``f3`` or ``f3-factory-line``."""
    if key == BUGS:
        raise TaskError("bugs has no next milestone")
    prefix, number = _key_parts(key)
    return f"{prefix}{number + 1}"


def milestone_order(key: str) -> tuple[str, int]:
    """Sorts m9 before m10; a named key sorts as its short form."""
    return _key_parts(key)


def _doc_keys(repo: Path) -> dict[str, str]:
    """Short key -> full key, from each ``.factory/cards/<full key>.md``."""
    found: dict[str, str] = {}
    for path in sorted((repo / ".factory" / "cards").glob("*-*.md")):
        if _KEY_RE.fullmatch(path.stem):
            found.setdefault(short_key(path.stem), path.stem)
    return found


def full_key(repo: Path, key: str) -> str:
    """A key in either form, as its doc names it: ``f3`` is ``f3-factory-line`` once
    ``.factory/cards/f3-factory-line.md`` exists; otherwise the key as given."""
    return key if _named(key) else _doc_keys(repo).get(key, key)


def named_keys(repo: Path) -> dict[str, str]:
    """Short key -> full key, from the tickets' frontmatter and then the docs (which win)."""
    found: dict[str, str] = {}
    for path in sorted((repo / ".factory" / "tasks").glob("*/*.md")):
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
    if key == BUGS:  # `runner milestone|review|signoff|…` (ADR 19 item 2)
        raise TaskError(f"{BUGS} is no milestone: its tickets run under `runner run`")
    return key if _named(key) else named_keys(repo).get(key, key)


def milestone_file(repo: Path, folder: str, key: str) -> Path:
    """``.factory/<folder>/<full key>.md``, or an existing one named by the short key (f2's)."""
    path = repo / ".factory" / folder / f"{key}.md"
    short = repo / ".factory" / folder / f"{short_key(key)}.md"
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
    priority: int | None = None  # lower first (ADR 19 item 3); a bug's defaults to 50
    area: str | None = None  # factory or product (ADR 19 item 2b); required on a bug
    tests_only: bool = False  # a weak test's fix: its tests pass on main (f8-09)

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
        if line.startswith(("## ", "### ")):  # a `##` heading counts too (f23-01)
            if current is not None:
                sections[current] = "\n".join(lines).strip()
            current, lines = line.lstrip("#").strip(), []
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
    + [f"softfield {c}" for c in ("signoff", "accept", "reject", "milestone", "run", "review")]
)
_DRY_RUN = "softfield run --dry-run"  # read-only: a replan checks its tickets with it
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


def _priority(meta: dict[str, Any], milestone: str) -> int | None:
    """``priority``: absent (a bug's is 50; a milestone ticket's comes from its card) or a
    whole number from 0, lower first."""
    if "priority" not in meta:
        return BUG_PRIORITY if milestone == BUGS else None
    value = meta["priority"]
    if type(value) is not int or value < 0:
        raise TaskError(f"'priority' must be a whole number from 0, not {value!r}")
    return value


def ticket_area(meta: dict[str, Any]) -> str | None:
    """``area``: absent, or factory or product. A bug without one fails pre-flight."""
    if "area" not in meta:
        return None
    if meta["area"] not in AREAS:
        raise TaskError(f"'area' must be factory or product, not {meta['area']!r}")
    return str(meta["area"])


def parse_task(path: Path, default_max_diff: int) -> Task:
    meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
    task_id = meta.get("id")
    if not isinstance(task_id, str) or task_id != path.stem:
        raise TaskError(f"'id' must match the file name ({path.stem})")
    milestone = milestone_key(meta.get("milestone"))
    bug_id = task_id.startswith("bug-")
    if bug_id != (milestone == BUGS) or (bug_id and not _BUG_ID_RE.fullmatch(task_id)):
        raise TaskError(f"a bug ticket is bug-<nn>-<slug> with 'milestone: {BUGS}', and only it")
    if (
        path.parent.parent.name == "tasks"
    ):  # .factory/tasks/<folder>/<id>.md: its repo has the cards
        milestone = full_key(path.parents[3], milestone)
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
    tests_only = meta.get("tests_only", False)
    if not isinstance(tests_only, bool):
        raise TaskError(f"'tests_only' must be true or false, not {tests_only!r}")
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
        priority=_priority(meta, milestone),
        area=ticket_area(meta),
        tests_only=tests_only,
    )


def load_dir(directory: Path, default_max_diff: int) -> list[Task]:
    return [parse_task(p, default_max_diff) for p in sorted(directory.glob("*.md"))]


def task_ids(directory: Path) -> set[str]:
    return {p.stem for p in directory.glob("*.md")}


def find_ticket(tasks_dir: Path, folder: str, wanted: str) -> Path:
    """The ticket in ``tasks_dir/folder`` whose id is ``wanted`` or starts with it. None, or
    more than one, is an error that lists the choices; one found in another folder says
    where it is."""
    paths = sorted((tasks_dir / folder).glob("*.md"))
    matches = [p for p in paths if p.stem == wanted] or [
        p for p in paths if p.stem.startswith(wanted)
    ]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        elsewhere = sorted(
            f".factory/tasks/{p.parent.name}/{p.name}"
            for p in tasks_dir.glob("*/*.md")
            if p.parent.name != folder and p.stem.startswith(wanted)
        )
        if elsewhere:
            raise TaskError(f"{wanted} isn't in .factory/tasks/{folder}/: " + ", ".join(elsewhere))
    choices = ", ".join(p.stem for p in matches or paths) or "none"
    found = "matches several tickets" if matches else "matches no ticket"
    raise TaskError(f"{wanted} {found} in .factory/tasks/{folder}/. Choices: {choices}")


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


def held_ids(ready: Iterable[Task], waits: Mapping[str, str]) -> dict[str, str]:
    """Ready tasks whose milestone waits for another's sign-off (ADR 17 item 4), each with the
    milestone it waits for; ``waits`` maps a short key to that milestone. Never picked."""
    return {t.id: waits[short_key(t.milestone)] for t in ready if short_key(t.milestone) in waits}


def task_priority(task: Task, cards: Mapping[str, int]) -> int:
    """A ticket's own ``priority:``, else its milestone card's (``cards`` maps a short key to
    it), else 100. Lower goes first (ADR 19 item 3)."""
    if task.priority is not None:
        return task.priority
    return cards.get(short_key(task.milestone), DEFAULT_PRIORITY)


def run_order(task: Task, cards: Mapping[str, int]) -> tuple[int, tuple[str, int], str]:
    """f5 D6: priority, then milestone order, then id."""
    return task_priority(task, cards), milestone_order(task.milestone), task.id


def pick_next(
    ready: Iterable[Task],
    done: set[str],
    paused: set[str],
    cards: Mapping[str, int] | None = None,
) -> Task | None:
    """The runnable ticket that goes first: dependencies, pauses and holds (in ``paused``)
    filter before the order."""
    candidates = [
        t for t in ready if t.id not in paused and all(dep in done for dep in t.depends_on)
    ]
    return min(candidates, key=lambda t: run_order(t, cards or {}), default=None)


TESTS_ONLY = (
    "`files:` lists only tests, so no test can fail on main's code (the tests-fail-on-main"
    " gate): the lead does it, unless it says `tests_only: true`"
)
TESTS_ONLY_CODE = "a `tests_only` ticket lists only tests in `files:`"
AREA_MISSING = "a bug ticket needs `area:` (factory or product), ADR 19 item 2b"


def preflight(task: Task, repo: Path) -> list[str]:
    """Problems with the task's files and Context/Pattern references. Empty means OK.

    The ``tests:`` files may not exist yet: developers write their own (ADR 07 item 4).
    A ticket that changes only tests escalates before any attempt (f4-23, f4-28, f4-36),
    unless it says so: a weak test's fix, whose tests pass on main (f8-09).
    """
    text = task.sections["Context"] + "\n" + task.sections.get("Pattern to follow", "")
    problems = []
    only_tests = all(f.startswith("tests/") for f in task.files)
    if task.tests_only and not only_tests:
        problems.append(TESTS_ONLY_CODE)
    elif task.files and only_tests and not task.tests_only:
        problems.append(TESTS_ONLY)
    if task.milestone == BUGS and task.area is None:
        problems.append(AREA_MISSING)
    paths = set(_PATH_RE.findall(text))
    listed = (*task.files, *task.tests)
    named = {Path(f).name for f in listed}  # `overview.py` once its path is listed (f33-01)
    for rel in sorted(paths):
        if (repo / rel).exists() or rel in listed or ("/" not in rel and rel in named):
            continue  # a listed one may be new
        problems.append(f"referenced path does not exist: {rel}")
    symbols = {a or b for a, b in _SYMBOL_RE.findall(task.sections["Context"])}
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
