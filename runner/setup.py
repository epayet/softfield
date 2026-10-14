"""`softfield init`, `softfield doctor` and `softfield service install` (ADR 30 items 5, 7, 8).

``init`` writes the factory's files into the folder it runs in, new or existing, registers the
project and hands over to an interactive Claude session that sets the rest up with the owner
(``docs/bootstrap.md``). ``doctor`` says whether a project is ready for the web. ``service``
writes the systemd user units that keep the runner and the dashboard up.
"""

import os
import re
import shutil
import tomllib
from dataclasses import dataclass
from pathlib import Path

from runner import checks, config, metrics
from runner.config import PROJECT_TOML, ConfigError, load_config
from runner.gitops import Git, GitError

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
    elif git.run("rev-parse", "--abbrev-ref", "HEAD").strip() != "main":
        raise SetupError("check out main first: the factory works on main")
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
    """The project in the metrics database, last in the owner's order."""
    conn = metrics.open_db(db)
    try:
        last = max((p.priority for p in metrics.projects_in_order(conn)), default=0)
        metrics.upsert_project(conn, folder.name, repo=str(folder))
        with conn:
            conn.execute(
                "UPDATE projects SET priority = ? WHERE name = ? AND priority = 100",
                (min(last + 1, 99), folder.name),
            )
    finally:
        conn.close()


def bootstrap() -> Path:
    """The setup session's guide, in the Softfield checkout this runs from."""
    return config.HOME / "docs" / "bootstrap.md"


def claude_command(folder: Path, origin: str) -> list[str]:
    """The interactive Claude session that sets the project up with the owner."""
    prompt = (
        f"Set this {origin} project up for Softfield: read {bootstrap()} and follow it, "
        f"starting with the {'idea' if origin == 'new' else 'repo'}."
    )
    return ["claude", "--add-dir", str(config.HOME / "docs"), prompt]


# --- doctor -----------------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    ok: bool
    what: str


def _adr_00(folder: Path) -> Path | None:
    found = sorted((folder / ".factory" / "adr").glob("00-*.md"))
    return found[0] if found else None


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
    adr = _adr_00(folder)
    status = _STATUS_RE.search(adr.read_text(encoding="utf-8")) if adr else None
    found.append(
        Finding(
            status is not None and status[1] == "Accepted",
            "ADR 00 accepted" + ("" if adr else ": none in .factory/adr/"),
        )
    )
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
