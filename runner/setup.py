"""`softfield init`, `softfield doctor` and `softfield service install` (ADR 30 items 5, 7, 8).

``init`` writes the factory's files into the folder it runs in, new or existing, and hands over
to an interactive Claude session that sets the rest up with the owner
(``runner/instructions/bootstrap.md``). ``doctor`` says whether a project is ready for the web;
``create`` adds it to the factory once it is (F236). ``service``
writes the systemd user units that keep the runner and the dashboard up.
"""

import json
import os
import re
import shutil
import sqlite3
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from runner import checks, config, metrics, prompts
from runner.config import PROJECT_TOML, ConfigError, load_config
from runner.gitops import Git, GitError
from runner.tasks import TaskError, milestone_key

TEMPLATES = Path(__file__).parent / "templates"
FACTORY_DIRS = (
    "adr",
    "cards",
    "reviews",
    "tasks/ready",
    "tasks/later",
    "tasks/done",
    "tasks/blocked",
    "tasks/escalated",
)
# What `init` writes, from `templates/`: (template, path in the project), all in the dot folder
# (ADR 41 item 1). An existing file stays as it is.
FILES = (
    ("project.toml", ".softfield/project.toml"),
    ("protected-paths.txt", ".softfield/protected-paths.txt"),
    ("project.md", ".softfield/project.md"),
    ("pre-commit", ".softfield/hooks/pre-commit"),
    ("README.md", ".softfield/README.md"),
    ("gitignore", ".softfield/.gitignore"),
    ("developer.md", ".softfield/developer.md"),
)
_STATUS_RE = re.compile(r"^- \*\*Status:\*\*\s*(\w+)", re.MULTILINE)


class SetupError(RuntimeError):
    pass


def is_new(folder: Path) -> bool:
    """A folder with nothing in it but git's own files is a new project."""
    return not [p for p in folder.iterdir() if p.name not in (".git", ".gitignore")]


def project_name(folder: Path) -> str | None:
    """The name in the folder's project.toml; None without one, or when it can't be read."""
    try:
        text = (folder / PROJECT_TOML).read_text(encoding="utf-8")
        return str(tomllib.loads(text)["project"]["name"])
    except (OSError, KeyError, ValueError):
        return None


def _decide(
    folder: Path,
    db: Path,
    previous: str | None,
    ask: Callable[[str, list[str]], str] | None,
    yes: bool = False,
    confirm: Callable[[str], str] | None = None,
) -> tuple[str, str, str | None]:
    """What ``init`` does about a project the database already holds under the folder's name
    (F136 D1, D2, D4), before it writes anything. Returns (the new project's name, "new",
    "continue" or "keep", the old row to rename)."""
    named = project_name(folder)
    name = named or folder.name
    is_project = (folder / PROJECT_TOML).is_file()
    conn = metrics.open_db(db)
    try:
        state = metrics.project_state(conn, name)
        if state is None:
            if is_project:
                raise SetupError(f"{folder} is a project already: `softfield doctor` says what")
            return name, "new", None
        repo, paused = state
        if paused == metrics.FORGOTTEN:
            choices = ["keep"] + (["continue"] if named else [])
            said = f"{name} is a forgotten project in the database (its folder: {repo})."
            old = name
            new_name = name
            goes = _what_goes(conn, name)
        elif is_project:
            raise SetupError(
                f"{folder} is a project already: `softfield doctor` says what it needs"
            )
        elif repo == str(folder):
            return name, "new", None
        else:
            choices = ["keep"]
            new_name = metrics.free_name(conn, name, 2)
            said = f"{name} is a project already, in {repo}; this one would be {new_name}."
            old = None
            goes = ""
    finally:
        conn.close()
    if old is not None:
        choices.append("fresh")
    if previous is not None and previous not in choices:
        raise SetupError(f"--previous {previous} isn't possible here: {' or '.join(choices)}")
    if previous is None:
        if ask is None:
            raise SetupError(
                f"{said} Say what to do with it: `softfield init --previous {'|'.join(choices)}`"
            )
        previous = ask(said, choices)
        if previous not in choices:
            raise SetupError(f"no such choice: {previous}")
        if previous == "fresh":
            typed = (
                confirm(f"Start fresh deletes {goes}.\nType {name} to do it: ") if confirm else ""
            )
            if typed.strip() != name:
                raise SetupError("not confirmed: nothing was changed")
    elif previous == "fresh" and not yes:
        raise SetupError(f"`--previous fresh` deletes {goes}: add --yes to say so")
    return new_name, previous, old


def _what_goes(conn: sqlite3.Connection, name: str) -> str:
    """What "start fresh" deletes of a project, in words."""
    row = conn.execute(
        "SELECT"
        " (SELECT count(*) FROM milestones WHERE project_id = p.id),"
        " (SELECT count(*) FROM tickets WHERE project_id = p.id),"
        " (SELECT count(*) FROM planner_threads WHERE project_id = p.id),"
        " (SELECT count(*) FROM runs WHERE project_id = p.id)"
        " FROM projects p WHERE p.name = ?",
        (name,),
    ).fetchone()
    cards, tickets, threads, runs = row
    return (
        f"{name}'s old entry for good: {cards} cards, {tickets} tickets, {threads} threads,"
        f" {runs} runs and their costs"
    )


def init(
    folder: Path,
    db: Path,
    previous: str | None = None,
    ask: Callable[[str, list[str]], str] | None = None,
    yes: bool = False,
    confirm: Callable[[str], str] | None = None,
) -> tuple[str, list[str]]:
    """The factory's files in ``folder`` (``git init`` first if needed), committed. The project
    is not registered: `softfield create` does that once `doctor` passes. Returns ("new" or
    "existing", the paths written). Refuses a folder that is a project already, or a repo off
    its main or dirty. A project of the same name in the database means a choice first
    (``previous``, or ``ask``)."""
    name, action, old = _decide(folder, db, previous, ask, yes, confirm)
    if action == "continue":  # nothing written or committed; `create` brings the old entry back
        origin = tomllib.loads((folder / PROJECT_TOML).read_text(encoding="utf-8"))["project"].get(
            "origin", "existing"
        )
        return str(origin), []
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
    written = []
    for directory in FACTORY_DIRS:
        (folder / ".softfield" / directory).mkdir(parents=True, exist_ok=True)
        keep = folder / ".softfield" / directory / ".gitkeep"
        if not any((folder / ".softfield" / directory).iterdir()):
            keep.write_text("")
    for template, rel in FILES:
        path = folder / rel
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        text = (TEMPLATES / template).read_text(encoding="utf-8")
        path.write_text(text.replace("{name}", name).replace("{origin}", origin), encoding="utf-8")
        written.append(rel)
    (folder / ".softfield/hooks/pre-commit").chmod(0o755)
    # A developer's BLOCKED.md stays out of git without touching the repo's own .gitignore
    exclude = Path(folder, git.run("rev-parse", "--git-path", "info/exclude").strip())
    exclude.parent.mkdir(parents=True, exist_ok=True)
    kept = exclude.read_text(encoding="utf-8") if exclude.is_file() else ""
    if "BLOCKED.md" not in kept.splitlines():
        exclude.write_text(kept + "BLOCKED.md\n", encoding="utf-8")
    git.run("config", "core.hooksPath", ".softfield/hooks")
    git.run("add", "-A")
    if not git.is_clean():
        git.run(
            "-c", "user.name=Softfield runner", "-c", "user.email=runner@softfield.invalid",
            "commit", "-q", "--no-verify", "-m", "softfield init: the factory's files (ADR 30)",
        )  # fmt: skip
    if old is not None:  # forgotten: kept under the first free name-N, or deleted for good
        conn = metrics.open_db(db)
        try:
            if action == "fresh":
                if (old_id := metrics.find_project(conn, old)) is not None:
                    metrics.delete_project(conn, old_id)
            else:
                metrics.rename_project(conn, old, metrics.free_name(conn, old, 1))
        finally:
            conn.close()
    return origin, written


def register(folder: Path, db: Path, name: str | None = None) -> None:
    """The project in the metrics database, last in the owner's order and not paused: the
    runner takes it from its next round. Only `create` calls it, once `doctor`'s checks pass
    (F236 D1). A forgotten row of the same folder comes back, history and place included.
    ``name`` is the one in its project.toml."""
    name = name or folder.name
    conn = metrics.open_db(db)
    try:
        last = max((p.priority for p in metrics.projects_in_order(conn)), default=0)
        metrics.upsert_project(conn, name, repo=str(folder))
        with conn:
            conn.execute(
                "UPDATE projects SET priority = ? WHERE name = ? AND priority = 100",
                (min(last + 1, 99), name),
            )
        metrics.set_project_paused(conn, name, None)
    finally:
        conn.close()


CREATE_NOTHING = "Nothing was added to the factory."


def registration(folder: Path, db: Path, name: str) -> str:
    """What `create` finds under ``name`` in the database: "new" (no row), "back" (this folder's
    forgotten row), "finish" (this folder's, still marked set up by an older init), "already"
    (registered), or raises SetupError naming the other folder that holds the name (F236 D1)."""
    conn = metrics.open_db(db)
    try:
        state = metrics.project_state(conn, name)
    finally:
        conn.close()
    if state is None:
        return "new"
    repo, paused = state
    if repo != str(folder):
        raise SetupError(
            f"{name} is held by {repo or 'another folder'}, not this one: nothing was written."
            " Change `name` in .softfield/project.toml, or `softfield forget` that project first"
        )
    if paused == metrics.FORGOTTEN:
        return "back"
    return "finish" if paused == metrics.SETTING_UP else "already"


def registered(db: Path, name: str) -> bool:
    """Whether a live (not forgotten) project of this name is in the factory's list."""
    conn = metrics.open_db(db)
    try:
        return any(p.name == name for p in metrics.projects_in_order(conn))
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
        for path in sorted((folder / ".softfield" / "cards").glob("*.md")):
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
                area=found.area,
            )
            published.append(key)
        return published
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
    return config.INSTRUCTIONS / "bootstrap.md"


NEXT = """What happens now: Claude asks for your idea and how to build it, keeps your words as
the project's seed, drafts ADR 00 (the starting decisions) for your yes, and puts the first
piece of work on a card. It doesn't build the idea: the factory does, from the card, and you
plan and follow it on the dashboard. Claude ends by saying where."""


def lead_command(folder: Path, args: list[str]) -> list[str]:
    """A terminal lead session in ``folder``: a plain ``claude`` stays plain (ADR 41 item 3)."""
    system = prompts.lead_session(config.HOME, folder / config.PROJECT_MD)
    add = ["--add-dir", str(config.INSTRUCTIONS)]
    return ["claude", *add, "--append-system-prompt", system, *args]


def claude_command(folder: Path, origin: str, name: str | None = None) -> list[str]:
    """The interactive Claude session that sets the project up with the owner: the setup guide
    is its instructions (not a file it may read), and it opens with the steps (the owner,
    2026-10-14: the first try said nothing, then built the idea)."""
    guide = bootstrap().read_text(encoding="utf-8") if bootstrap().is_file() else ""
    name = name or folder.name
    opening = f"Start the setup of {name}, a {origin} project: your first message, then the idea."
    if origin == "existing":
        opening = f"Start the setup of {name}, an existing project: your first message."
    return [
        "claude",
        "--add-dir",
        str(config.INSTRUCTIONS),
        "--append-system-prompt",
        guide,
        opening,
    ]


# --- doctor -----------------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    ok: bool
    what: str
    needed: bool = True  # the project waits for it; else it's only said


def passes(findings: list[Finding]) -> bool:
    """Every check the project waits for passed: the web can take over."""
    return all(f.ok for f in findings if f.needed)


PHONE_STEPS = "docs/notifications-on-the-phone.md"  # in Softfield's checkout


def _phone_finding() -> Finding:
    """The phone's notifications (ADR 31 item 5): the machine's `[notify] ntfy`, read, never
    sent to. Not needed: without it nothing is sent, and the dashboard still shows it all."""
    try:
        address = config.machine_ntfy()
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return Finding(False, f"notifications on your phone: the machine's settings: {exc}", False)
    if address is not None:
        return Finding(True, "notifications on your phone set up (ntfy)", False)
    return Finding(
        False,
        "notifications on your phone, if you want them: run `softfield notify setup`,"
        f" then the steps in Softfield's {PHONE_STEPS}",
        False,
    )


def _adr_00(folder: Path) -> Path | None:
    found = sorted((folder / ".softfield" / "adr").glob("00-*.md"))
    return found[0] if found else None


ACCEPTED_00 = "ADR 0 accepted by the owner"  # `softfield accept 0`'s commit (owner.decide_adr)


def _adr_00_finding(folder: Path) -> Finding:
    """ADR 00 accepted by the owner: its status says so and `softfield accept 0` committed it.
    A status written Accepted by hand (the setup session must not) doesn't count."""
    adr = _adr_00(folder)
    if adr is None:
        return Finding(False, "ADR 00 accepted: none in .softfield/adr/")
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
    cards = sorted(p.stem for p in (folder / ".softfield" / "cards").glob("*.md"))
    return cards[0] if cards else None


def hand_over(name: str, card: str | None, host: str, *, planning: bool = False) -> str:
    """What `create` says when the project is in the factory: where it is and what to do next."""
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
        load_config(folder)
        project = tomllib.loads((folder / PROJECT_TOML).read_text(encoding="utf-8"))["project"]
        found.append(Finding(True, f"{PROJECT_TOML} loads"))
    except (OSError, KeyError, ValueError, ConfigError) as exc:
        return [Finding(False, f"{PROJECT_TOML} doesn't load: {exc}")]
    found.append(Finding(bool(project.get("description")), "a one-line description in [project]"))
    protected = folder / ".softfield" / "protected-paths.txt"
    found.append(Finding(protected.is_file(), "protected paths in .softfield/protected-paths.txt"))
    if project.get("origin") == "new":
        found.append(
            Finding((folder / ".softfield/seed.md").is_file(), "the idea in .softfield/seed.md")
        )
    found.append(_adr_00_finding(folder))
    cards = [p for p in (folder / ".softfield" / "cards").glob("*.md")]
    found.append(Finding(bool(cards), "a first card in .softfield/cards/"))
    git = Git(folder)
    try:
        on_main = git.run("rev-parse", "--abbrev-ref", "HEAD").strip() == "main"
        clean = git.is_clean()
        hooked = git.run("config", "core.hooksPath", check=False).strip() == ".softfield/hooks"
    except GitError:
        on_main = clean = hooked = False
    found.append(Finding(on_main and clean, "everything committed, on main"))
    found.append(Finding(hooked, "the commit hook (git config core.hooksPath .softfield/hooks)"))
    if run_checks and on_main:
        failed = [c.name for c in checks.check_all(folder, timeout) if not c.ok]
        found.append(Finding(not failed, "softfield check-all passes" + (
            f": {', '.join(failed)} failed" if failed else "")))  # fmt: skip
    found.append(_phone_finding())
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
