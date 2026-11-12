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
import subprocess
import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple

from runner import config
from runner.gitops import Git, GitError

SHARE = Path("~/.local/share/softfield").expanduser()  # D3: run/ and data/ live here
MAIN = "main"
LOCK_WAIT = 60.0  # seconds a command waits for another on the same project (D3)
DOCKER_TIMEOUT = 900  # an `up` may build the image first
MAX_LINES = 2000
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
    """Run the app: the checkout at main if there is none yet, then ``up -d``."""
    with _locked(stack):
        if not stack.checkout.is_dir():
            try:
                Git(stack.repo).run("worktree", "add", "--detach", str(stack.checkout), MAIN)
            except GitError as exc:
                raise StackError(f"the checkout of {stack.project}'s main failed: {exc}") from exc
        stack.data.mkdir(parents=True, exist_ok=True)
        _check(_compose(stack, "up", "-d"), f"starting {stack.project}'s app")


def stop(stack: Stack) -> None:
    """Stop the app; its containers stay, so the next start is quick."""
    with _locked(stack):
        _check(_compose(stack, "stop"), f"stopping {stack.project}'s app")


def logs(stack: Stack, service: str | None = None, lines: int = 200) -> str:
    """The last ``lines`` lines of the app's logs, of one service or all; the error if Docker
    couldn't give them. ``service`` comes from a page's address: it is a name or nothing."""
    if service is not None and not _SERVICE.fullmatch(service):
        raise ValueError(f"not a service name: {service!r}")
    count = str(min(max(int(lines), 1), MAX_LINES))
    result = _compose(stack, "logs", "--no-color", "--tail", count, *([service] if service else []))
    return result.out if result.code == 0 else result.err or result.out


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
    if failed := _failed_update(stack):
        return StackState(
            UPDATE_FAILED, port, str(failed.get("at", "")), str(failed.get("tail", ""))
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
