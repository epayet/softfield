"""A project's app on its Docker Compose stack (ADR 46, F239 D1 to D4): the only module that runs
``docker``. The runner and the dashboard both import it.

The stack runs main, from a checkout of its own (``run/<project>``, a detached worktree, like
Softfield's ``live``), under the project's name as Compose's project, with its lasting data in
``data/<project>``, outside every git tree. Every command is fixed here: what a caller passes in
is a project from the registry, a service name checked as one, and a number."""

import fcntl
import json
import os
import re
import shutil
import subprocess
import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, NamedTuple

from runner import config
from runner.gitops import Git, GitError

SHARE = Path("~/.local/share/softfield").expanduser()  # D3: run/ and data/ live here
MAIN = "main"
LOCK_WAIT = 60.0  # seconds a command waits for another on the same project (D3)
DOCKER_TIMEOUT = 900  # an `up` may build the image first
MAX_LINES = 2000
TAIL_LINES = 40  # of a failed build, kept in the result file
KEEP_COPIES = 3  # of the data folder, before the newest rebuilds (D8)
MAX_RESTARTS = 3  # restarted more than this: crashed, not starting
# Exit codes of a container `docker compose stop` ended: none, SIGTERM's, SIGKILL's after 10 s
STOPPED_CODES = {0, 137, 143}
_SERVICE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")

RUNNING, STARTING, STOPPED, CRASHED, UPDATE_FAILED = (
    "running",
    "starting",
    "stopped",
    "crashed",
    "update failed",
)
NO_DOCKER = "no docker"  # Docker missing, or this user can't use it: `detail` says which


class StackError(RuntimeError):
    """A Compose command that failed or couldn't run, in plain words."""


class Result(NamedTuple):
    code: int
    out: str
    err: str


@dataclass(frozen=True)
class Stack:
    project: str  # Compose's project name and the run and data folders' name
    repo: Path
    service: str  # the main service: its port is the app's link
    path: str = "/"

    @property
    def checkout(self) -> Path:
        return SHARE / "run" / self.project

    @property
    def data(self) -> Path:
        return SHARE / "data" / self.project

    @property
    def result_file(self) -> Path:
        """The last update's result, ``{"commit", "ok", "at", "tail"}`` (D3)."""
        return SHARE / "run" / f"{self.project}.json"

    @property
    def lock_file(self) -> Path:
        return SHARE / "run" / f"{self.project}.lock"


@dataclass(frozen=True)
class StackState:
    word: str  # RUNNING, STARTING, STOPPED, CRASHED, UPDATE_FAILED or NO_DOCKER
    url_port: int | None = None  # the main service's published host port
    since: str = ""
    detail: str = ""
    commit: str = ""  # of an UPDATE_FAILED: the commit the update failed on


def _docker(args: Sequence[str], cwd: Path, env: Mapping[str, str]) -> Result:
    """``docker <args>``: every Docker call goes through here, and the tests replace it (D1).
    A missing binary or a timeout is a failed result, never an exception."""
    try:
        proc = subprocess.run(
            ["docker", *args],
            cwd=cwd,
            env=dict(env),
            capture_output=True,
            text=True,
            timeout=DOCKER_TIMEOUT,
            check=False,
        )
    except FileNotFoundError:
        return Result(127, "", "docker is not installed on this machine")
    except subprocess.TimeoutExpired:
        return Result(124, "", f"docker {' '.join(args[:4])} took over {DOCKER_TIMEOUT} s")
    return Result(proc.returncode, proc.stdout, proc.stderr)


def _compose_name(name: str) -> str:
    """A Compose project name, which is also a folder's: lower case letters, digits, - and _,
    so nothing in a project's name climbs out of ``run/`` or ``data/``."""
    return re.sub(r"[^a-z0-9_-]+", "-", name.lower()).strip("-_") or "app"


def _common_dir(path: Path) -> str:
    return Git(path).run("rev-parse", "--path-format=absolute", "--git-common-dir").strip()


def _is_softfield(repo: Path) -> bool:
    """Whether ``repo`` is the Softfield this code runs from (``live`` is a worktree of it):
    it runs from ``live`` with its own commands, never from a stack (ADR 46 item 8)."""
    home = config.HOME
    if home.resolve() == repo.resolve():
        return True
    try:
        return _common_dir(home) == _common_dir(repo)
    except (GitError, OSError):
        return False


def stack_for(repo: Path) -> Stack | None:
    """The project's stack, from its ``[run]``; None without one, and for Softfield itself."""
    run = config.project_run(repo)
    if run is None or _is_softfield(repo):
        return None
    project = _compose_name(config.project_name(repo))
    return Stack(project=project, repo=repo, service=run.service, path=run.path)


def _env(stack: Stack) -> dict[str, str]:
    return {**os.environ, "APP_DATA": str(stack.data)}


def _cwd(stack: Stack) -> Path:
    return stack.checkout if stack.checkout.is_dir() else stack.repo


def _compose(stack: Stack, *args: str) -> Result:
    return _docker(["compose", "-p", stack.project, *args], _cwd(stack), _env(stack))


def _last_lines(text: str, count: int = 5) -> str:
    return "\n".join(text.strip().splitlines()[-count:])


def _check(result: Result, what: str) -> None:
    if result.code != 0:
        said = _last_lines(result.err or result.out) or f"exit code {result.code}"
        raise StackError(f"{what} failed: {said}")


@contextmanager
def _locked(stack: Stack) -> Iterator[None]:
    """One Compose command at a time on a project, across the runner and the dashboard (D3)."""
    stack.lock_file.parent.mkdir(parents=True, exist_ok=True)
    with stack.lock_file.open("a") as handle:
        deadline = time.monotonic() + LOCK_WAIT
        while True:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise StackError(
                        f"{stack.project}'s app is busy with another command; try again soon"
                    ) from None
                time.sleep(0.1)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def start(stack: Stack) -> None:
    """Run the app: the checkout at main if there is none yet, then ``up -d --build``. The build
    is there because `follow_main` moves a stopped app's checkout without building it: a plain
    ``up -d`` would start the image of an older main. A start that works clears a failed update
    of that commit."""
    with _locked(stack):
        if not stack.checkout.is_dir():
            try:
                Git(stack.repo).run("worktree", "add", "--detach", str(stack.checkout), MAIN)
            except GitError as exc:
                raise StackError(f"the checkout of {stack.project}'s main failed: {exc}") from exc
        stack.data.mkdir(parents=True, exist_ok=True)
        _check(_compose(stack, "up", "-d", "--build"), f"starting {stack.project}'s app")
        with suppress(GitError):  # the app runs; only the record of it would be missing
            _write_result(stack, Git(stack.checkout).head(), True)


def stop(stack: Stack) -> None:
    """Stop the app; its containers stay, so the next start is quick."""
    with _locked(stack):
        _check(_compose(stack, "stop"), f"stopping {stack.project}'s app")


def _stamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _tail(text: str) -> str:
    return _last_lines(text, TAIL_LINES)


def _write_result(stack: Stack, commit: str, ok: bool, tail: str = "") -> None:
    record = {"commit": commit, "ok": ok, "at": _stamp(), "tail": tail}
    try:
        stack.result_file.write_text(json.dumps(record), encoding="utf-8")
    except OSError as exc:
        print(f"[{_stamp()}] {stack.project}'s update result couldn't be written: {exc}")


def _is_running(stack: Stack) -> bool:
    """Whether any of the app's containers is up, whatever its health."""
    result = _compose(stack, "ps", "--all", "--format", "json")
    if result.code != 0:
        return False
    try:
        return any(c.get("State") in ("running", "restarting") for c in _containers(result.out))
    except ValueError:
        return False


def _copy_data(stack: Stack, commit: str) -> None:
    """D8: the data folder, copied beside itself before a rebuild; the newest copies stay."""
    stack.data.mkdir(parents=True, exist_ok=True)
    prefix = f"{stack.project}.before-"
    target = stack.data.parent / f"{prefix}{commit[:12]}"
    try:
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(stack.data, target, symlinks=True)
        os.utime(target)  # a copy keeps its source's times: the newest is the one made now
    except OSError as exc:
        shutil.rmtree(target, ignore_errors=True)
        raise StackError(f"copying {stack.project}'s data failed: {exc}") from exc
    copies = sorted(
        (p for p in stack.data.parent.glob(f"{prefix}*") if p.is_dir()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for old in copies[KEEP_COPIES:]:
        shutil.rmtree(old, ignore_errors=True)


def follow_main(stack: Stack) -> bool:
    """ADR 46 items 3 and 4: when main has moved, the app's checkout follows (detached); if the
    app was running it is rebuilt, after a copy of its data. Whether the checkout moved. Never
    raises: a failure goes to the result file, which `state` reads, and to the console, and the
    old containers keep running."""
    try:
        with _locked(stack):
            if not stack.checkout.is_dir():
                return False  # not started yet: `start` makes it at main
            main = Git(stack.repo).run("rev-parse", MAIN).strip()
            if Git(stack.checkout).head() == main:
                return False
            running = _is_running(stack)
            Git(stack.checkout).run("checkout", "-q", "--detach", main)
            if not running:
                return True
            try:
                _copy_data(stack, main)
            except StackError as exc:
                _write_result(stack, main, False, str(exc))
                print(f"[{_stamp()}] {stack.project}'s app didn't update: {exc}")
                return True
            built = _compose(stack, "up", "-d", "--build")
            if built.code == 0:
                _write_result(stack, main, True)
            else:
                tail = _tail(f"{built.out}\n{built.err}") or f"exit code {built.code}"
                _write_result(stack, main, False, tail)
                print(f"[{_stamp()}] {stack.project}'s app didn't update: {_last_lines(tail)}")
            return True
    except (StackError, GitError, OSError) as exc:
        print(f"[{_stamp()}] {stack.project}'s app couldn't follow main: {exc}")
        return False


def logs(stack: Stack, service: str | None = None, lines: int = 200) -> str:
    """The last ``lines`` lines of the app's logs, of one service or all; the error if Docker
    couldn't give them. ``service`` comes from a page's address: it is a name or nothing."""
    if service is not None and not _SERVICE.fullmatch(service):
        raise ValueError(f"not a service name: {service!r}")
    count = str(min(max(int(lines), 1), MAX_LINES))
    result = _compose(stack, "logs", "--no-color", "--tail", count, *([service] if service else []))
    return result.out if result.code == 0 else result.err or result.out


def services(stack: Stack) -> list[str]:
    """The names of the stack's services; empty when Docker couldn't say."""
    result = _compose(stack, "config", "--services")
    if result.code != 0:
        return []
    names = (line.strip() for line in result.out.splitlines())
    return [n for n in names if _SERVICE.fullmatch(n)]


def _containers(out: str) -> list[dict[str, Any]]:
    """``ps --format json``: one array before Compose 2.21, one object a line since."""
    text = out.strip()
    if not text:
        return []
    if text.startswith("["):
        found = json.loads(text)
    else:
        found = [json.loads(line) for line in text.splitlines() if line.strip()]
    return [c for c in found if isinstance(c, dict)]


def _port(container: dict[str, Any]) -> int | None:
    for publisher in container.get("Publishers") or []:
        port = publisher.get("PublishedPort")
        if isinstance(port, int) and port > 0:
            return port
    return None


def _restarts(stack: Stack, container: dict[str, Any]) -> int:
    """How often Docker restarted it: ``ps`` doesn't say, ``inspect`` of its id does."""
    ident = str(container.get("ID", ""))
    if not _SERVICE.fullmatch(ident):
        return 0
    result = _docker(["inspect", "--format", "{{.RestartCount}}", ident], _cwd(stack), _env(stack))
    try:
        return int(result.out.strip()) if result.code == 0 else 0
    except ValueError:
        return 0


def _failed_update(stack: Stack) -> dict[str, Any] | None:
    """The last update's result when it failed on the commit the checkout is at."""
    try:
        record = json.loads(stack.result_file.read_text(encoding="utf-8"))
        commit = Git(stack.checkout).head() if stack.checkout.is_dir() else ""
    except (OSError, ValueError, GitError):
        return None
    if not isinstance(record, dict) or record.get("ok") is not False:
        return None
    return record if commit and record.get("commit") == commit else None


def _describe(container: dict[str, Any]) -> str:
    return f"{container.get('Name', container.get('Service', '?'))}: {container.get('Status', '')}"


def _crashed(stack: Stack, containers: list[dict[str, Any]]) -> dict[str, Any] | None:
    for container in containers:
        state, code = container.get("State"), container.get("ExitCode", 0)
        if state == "exited" and code not in STOPPED_CODES:
            return container
        if state == "dead" or container.get("Health") == "unhealthy":
            return container
        if state == "restarting" and _restarts(stack, container) > MAX_RESTARTS:
            return container
    return None


def state(stack: Stack) -> StackState:
    """The app's state from ``ps``, in one word; Docker failing is a state, not an exception."""
    result = _compose(stack, "ps", "--all", "--format", "json")
    if result.code != 0:
        return StackState(NO_DOCKER, detail=_last_lines(result.err or result.out))
    try:
        containers = _containers(result.out)
    except ValueError:
        return StackState(NO_DOCKER, detail="docker compose ps printed something unreadable")
    main = next((c for c in containers if c.get("Service") == stack.service), None)
    port = _port(main) if main else None
    since = str(main.get("CreatedAt", "")) if main else ""
    up = any(c.get("State") in ("running", "restarting") for c in containers)
    # a failed update matters while the old app still runs; stopped, it is just stopped
    if up and (failed := _failed_update(stack)):
        return StackState(
            UPDATE_FAILED,
            port,
            str(failed.get("at", "")),
            str(failed.get("tail", "")),
            str(failed.get("commit", "")),
        )
    if not containers:
        return StackState(STOPPED)
    if crashed := _crashed(stack, containers):
        return StackState(CRASHED, port, since, _describe(crashed))
    if main is None or main.get("State") == "exited":
        return StackState(STOPPED, port, since)
    if main.get("State") == "running" and main.get("Health", "") in ("", "healthy"):
        return StackState(RUNNING, port, since)
    return StackState(STARTING, port, since, _describe(main))
