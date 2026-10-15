"""`softfield init`, `softfield doctor` and `softfield service install` (ADR 30 items 5, 7, 8).

``init`` writes the factory's files into the folder it runs in, new or existing, registers the
project and hands over to an interactive Claude session that sets the rest up with the owner
(``docs/bootstrap.md``). ``doctor`` says whether a project is ready for the web. ``service``
writes the systemd user units that keep the runner and the dashboard up.
"""

import json
import os
import re
import shutil
import tomllib
from dataclasses import dataclass
from pathlib import Path

from runner import checks, config, metrics
from runner.config import PROJECT_TOML, ConfigError, load_config
from runner.gitops import Git, GitError
from runner.tasks import TaskError, milestone_key

TEMPLATES = Path(__file__).parent / "templates"
FACTORY_DIRS = (
    "adr",
    "cards",
    "tasks/ready",
    "tasks/later",
    "tasks/done",
    "tasks/blocked",
    "tasks/escalated",
)
# What `init` writes, from `templates/`: (template, path in the project). An existing file
# stays as it is: the setup session merges what it needs (docs/bootstrap.md).
FILES = (
    ("project.toml", ".factory/project.toml"),
    ("protected-paths.txt", ".factory/protected-paths.txt"),
    ("project.md", ".factory/project.md"),
    ("pre-commit", ".factory/hooks/pre-commit"),
    ("AGENTS.md", "AGENTS.md"),
    ("CLAUDE.md", "CLAUDE.md"),
    ("opencode.json", "opencode.json"),
    ("developer.md", "docs/agents/developer.md"),
)
IGNORED = (".factory/var/", "BLOCKED.md")
_STATUS_RE = re.compile(r"^- \*\*Status:\*\*\s*(\w+)", re.MULTILINE)


class SetupError(RuntimeError):
    pass


def is_new(folder: Path) -> bool:
    """A folder with nothing in it but git's own files is a new project."""
    return not [p for p in folder.iterdir() if p.name not in (".git", ".gitignore")]


def init(folder: Path, db: Path) -> tuple[str, list[str]]:
    """The factory's files in ``folder`` (``git init`` first if needed), committed, and the
    project registered last in the owner's order. Returns ("new" or "existing", the paths
    written). Refuses a folder that is a project already, or a repo off its main or dirty."""
    if (folder / PROJECT_TOML).is_file():
        raise SetupError(f"{folder} is a project already: `softfield doctor` says what it needs")
    origin = "new" if is_new(folder) else "existing"
    git = Git(folder)
    if not (folder / ".git").exists():
        git.run("init", "-q", "-b", "main")
    elif not git.run("rev-parse", "--verify", "-q", "HEAD", check=False).strip():
        git.run("symbolic-ref", "HEAD", "refs/heads/main")  # a fresh `git init`: no commit yet
    elif (branch := git.run("rev-parse", "--abbrev-ref", "HEAD").strip()) != "main":
        raise SetupError(
            f"the factory works on a branch called main, and this repo is on {branch}: check"
            f" main out, or rename it (`git branch -m {branch} main`, and on your remote too)"
        )
    elif not git.is_clean():
        raise SetupError("commit or stash your changes first: init commits what it writes")
    name = folder.name
    written = []
    for directory in FACTORY_DIRS:
        (folder / ".factory" / directory).mkdir(parents=True, exist_ok=True)
        keep = folder / ".factory" / directory / ".gitkeep"
        if not any((folder / ".factory" / directory).iterdir()):
            keep.write_text("")
    for template, rel in FILES:
        path = folder / rel
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        text = (TEMPLATES / template).read_text(encoding="utf-8")
        path.write_text(text.replace("{name}", name).replace("{origin}", origin), encoding="utf-8")
        written.append(rel)
    (folder / ".factory/hooks/pre-commit").chmod(0o755)
    ignore = folder / ".gitignore"
    lines = ignore.read_text(encoding="utf-8").splitlines() if ignore.is_file() else []
    missing = [line for line in IGNORED if line not in lines]
    if missing:
        ignore.write_text("\n".join([*lines, *missing]) + "\n", encoding="utf-8")
        written.append(".gitignore")
    git.run("config", "core.hooksPath", ".factory/hooks")
    git.run("add", "-A")
    git.run(
        "-c", "user.name=Softfield runner", "-c", "user.email=runner@softfield.invalid",
        "commit", "-q", "--no-verify", "-m", "softfield init: the factory's files (ADR 30 item 7)",
    )  # fmt: skip
    register(folder, db)
    return origin, written


def register(folder: Path, db: Path) -> None:
    """The project in the metrics database, last in the owner's order, and paused while it is
    set up: the runner leaves it alone until `softfield doctor` passes (``ready``)."""
    conn = metrics.open_db(db)
    try:
        last = max((p.priority for p in metrics.projects_in_order(conn)), default=0)
        metrics.upsert_project(conn, folder.name, repo=str(folder))
        with conn:
            conn.execute(
                "UPDATE projects SET priority = ? WHERE name = ? AND priority = 100",
                (min(last + 1, 99), folder.name),
            )
        metrics.set_project_paused(conn, folder.name, metrics.SETTING_UP)
    finally:
        conn.close()


def publish_cards(folder: Path, name: str, db: Path) -> list[str]:
    """The project's cards on its Planning desk and board at once, as the runner's `sync_cards`
    puts them there at a session's start: the hand-over shouldn't wait for the runner's next
    round, which comes only between jobs (2026-10-14: the first card stayed off the desk while a
    developer job ran). Returns the keys it put there."""
    from runner.milestone import card, milestone_doc  # runner.milestone imports the loop

    conn = metrics.open_db(db)
    try:
        project = metrics.upsert_project(conn, name, repo=str(folder))
        published = []
        for path in sorted((folder / ".factory" / "cards").glob("*.md")):
            try:
                key = milestone_key(path.stem)
                text = path.read_text(encoding="utf-8")
            except (TaskError, OSError, UnicodeDecodeError):
                continue
            found = card(key, text)
            metrics.upsert_milestone(
                conn,
                project,
                key,
                title=milestone_doc(text).get("title"),
                state=found.state,
                priority=found.priority,
                area=found.area,
            )
            published.append(key)
        return published
    finally:
        conn.close()


def ready(name: str, db: Path) -> bool:
    """`softfield doctor` passed: a project still being set up goes to the runner, which takes
    it from its next round. Whether it was waiting for that."""
    conn = metrics.open_db(db)
    try:
        row = next((p for p in metrics.projects_in_order(conn) if p.name == name), None)
        if row is None or row.paused != metrics.SETTING_UP:
            return False
        metrics.set_project_paused(conn, name, None)
        return True
    finally:
        conn.close()


def plan_first_card(name: str, card: str, db: Path, at: str) -> bool:
    """The hand-over asks the lead to plan the first card, as the owner's "Plan this card." on
    its thread, so a proposal waits on the desk (2026-10-15: the card sat unplanned until the
    owner wrote to it). Not when the card's thread has begun or a message waits for it. Whether
    it asked."""
    from runner import planner

    thread = planner.thread_key(card)
    conn = metrics.open_db(db)
    try:
        project = metrics.find_project(conn, name)
        if project is None or metrics.find_thread(conn, project, thread) is not None:
            return False
        waiting = conn.execute(
            "SELECT 1 FROM owner_requests WHERE project_id = ? AND kind = ? AND subject = ?"
            " AND done IS NULL",
            (project, planner.PLAN_MESSAGE, thread),
        ).fetchone()
        if waiting is not None:
            return False
        value = json.dumps({"text": planner.PLAN_THE_CARD, "comments": {}})
        metrics.add_request(conn, project, planner.PLAN_MESSAGE, thread, value, at)
        return True
    finally:
        conn.close()


def bootstrap() -> Path:
    """The setup session's guide, in the Softfield checkout this runs from."""
    return config.HOME / "docs" / "bootstrap.md"


NEXT = """What happens now: Claude asks for your idea and how to build it, keeps your words as
the project's seed, drafts ADR 00 (the starting decisions) for your yes, and puts the first
piece of work on a card. It doesn't build the idea: the factory does, from the card, and you
plan and follow it on the dashboard. Claude ends by saying where."""


def claude_command(folder: Path, origin: str) -> list[str]:
    """The interactive Claude session that sets the project up with the owner: the setup guide
    is its instructions (not a file it may read), and it opens with the steps (the owner,
    2026-10-14: the first try said nothing, then built the idea)."""
    guide = bootstrap().read_text(encoding="utf-8") if bootstrap().is_file() else ""
    opening = (
        f"Start the setup of {folder.name}, a {origin} project: your first message, then the idea."
    )
    if origin == "existing":
        opening = f"Start the setup of {folder.name}, an existing project: your first message."
    return [
        "claude",
        "--add-dir",
        str(config.HOME / "docs"),
        "--append-system-prompt",
        guide,
        opening,
    ]


# --- doctor -----------------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    ok: bool
    what: str


def _adr_00(folder: Path) -> Path | None:
    found = sorted((folder / ".factory" / "adr").glob("00-*.md"))
    return found[0] if found else None


ACCEPTED_00 = "ADR 0 accepted by the owner"  # `softfield accept 0`'s commit (owner.decide_adr)


def _adr_00_finding(folder: Path) -> Finding:
    """ADR 00 accepted by the owner: its status says so and `softfield accept 0` committed it.
    A status written Accepted by hand (the setup session must not) doesn't count."""
    adr = _adr_00(folder)
    if adr is None:
        return Finding(False, "ADR 00 accepted: none in .factory/adr/")
    status = _STATUS_RE.search(adr.read_text(encoding="utf-8"))
    if status is None or status[1] != "Accepted":
        return Finding(False, "ADR 00 accepted: it waits for your yes")
    try:
        log = Git(folder).run("log", "--format=%s", "--", adr.relative_to(folder).as_posix())
    except GitError:
        log = ""
    if ACCEPTED_00 not in log.splitlines():
        return Finding(False, "ADR 00 accepted: only `softfield accept 0` accepts it, on your yes")
    return Finding(True, "ADR 00 accepted")


def first_card(folder: Path) -> str | None:
    """The project's first card's file name, without .md (``m1-hello``)."""
    cards = sorted(p.stem for p in (folder / ".factory" / "cards").glob("*.md"))
    return cards[0] if cards else None


def hand_over(name: str, card: str | None, host: str, *, planning: bool = False) -> str:
    """What `doctor` says when the project is ready: where it is and what to do next."""
    base = f"http://{host}:8765"
    lines = [f"Done: {name} is in the factory.", f"  The Projects page: {base}/projects"]
    if card:
        key = card.split("-", 1)[0]
        lines.append(f"  Its first card, {card}, on its Planning desk:")
        lines.append(f"  {base}/planning/{key}?project={name}")
    if planning:
        lines.append(
            "The lead plans it once the runner is running (`softfield run`): its proposal comes"
            " on the card's thread. Answer there; the runner builds it once you approve the plan."
        )
    else:
        lines.append(
            "Write to the card to plan it there; the runner builds it once you approve the plan."
        )
    return "\n".join(lines)


def proposed_adr_00(folder: Path) -> Path | None:
    """ADR 00 while it waits for the owner (Proposed), else None."""
    adr = _adr_00(folder)
    status = _STATUS_RE.search(adr.read_text(encoding="utf-8")) if adr else None
    return adr if adr is not None and status is not None and status[1] == "Proposed" else None


def doctor(
    folder: Path, db: Path, *, run_checks: bool = True, timeout: int = 1200
) -> list[Finding]:
    """Whether the web can take over (ADR 30 item 8): each check, passed or not, in order."""
    found: list[Finding] = []
    try:
        cfg = load_config(folder)
        project = tomllib.loads((folder / PROJECT_TOML).read_text(encoding="utf-8"))["project"]
        found.append(Finding(True, f"{PROJECT_TOML} loads"))
    except (OSError, KeyError, ValueError, ConfigError) as exc:
        return [Finding(False, f"{PROJECT_TOML} doesn't load: {exc}")]
    found.append(Finding(bool(project.get("description")), "a one-line description in [project]"))
    protected = folder / ".factory" / "protected-paths.txt"
    found.append(Finding(protected.is_file(), "protected paths in .factory/protected-paths.txt"))
    if project.get("origin") == "new":
        found.append(
            Finding((folder / ".factory/seed.md").is_file(), "the idea in .factory/seed.md")
        )
    found.append(_adr_00_finding(folder))
    cards = [p for p in (folder / ".factory" / "cards").glob("*.md")]
    found.append(Finding(bool(cards), "a first card in .factory/cards/"))
    conn = metrics.open_db(db)
    try:
        registered = metrics.find_project(conn, cfg.project_name) is not None
    finally:
        conn.close()
    found.append(Finding(registered, f"registered as {cfg.project_name}"))
    git = Git(folder)
    try:
        on_main = git.run("rev-parse", "--abbrev-ref", "HEAD").strip() == "main"
        clean = git.is_clean()
        hooked = git.run("config", "core.hooksPath", check=False).strip() == ".factory/hooks"
    except GitError:
        on_main = clean = hooked = False
    found.append(Finding(on_main and clean, "everything committed, on main"))
    found.append(Finding(hooked, "the commit hook (git config core.hooksPath .factory/hooks)"))
    if run_checks and on_main:
        failed = [c.name for c in checks.check_all(folder, timeout) if not c.ok]
        found.append(Finding(not failed, "softfield check-all passes" + (
            f": {', '.join(failed)} failed" if failed else "")))  # fmt: skip
    return found


# --- service ----------------------------------------------------------------------------------

UNITS = {
    "softfield-runner": ("The Softfield runner, for every project", "run"),
    "softfield-dashboard": ("The Softfield dashboard", "dashboard --lan"),
}


def unit(description: str, args: str, workdir: Path, path: str) -> str:
    """A systemd user unit for one `softfield` command, with the PATH it was installed from:
    a service doesn't get the shell's, and the runner calls claude, opencode, uv and git."""
    command = shutil.which("softfield") or str(Path.home() / ".local/bin/softfield")
    return (
        "[Unit]\n"
        f"Description={description} (ADR 30 item 5)\n"
        "After=network-online.target\n\n"
        "[Service]\n"
        f"ExecStart={command} {args}\n"
        f"WorkingDirectory={workdir}\n"
        f"Environment=PATH={path}\n"
        "Restart=on-failure\n"
        "RestartSec=30\n\n"
        "[Install]\n"
        "WantedBy=default.target\n"
    )


def install_units(folder: Path, workdir: Path, path: str | None = None) -> list[Path]:
    """The units in ``folder`` (``~/.config/systemd/user``); returns the files written."""
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for name, (description, args) in UNITS.items():
        target = folder / f"{name}.service"
        target.write_text(unit(description, args, workdir, path or os.environ.get("PATH", "")))
        written.append(target)
    return written
