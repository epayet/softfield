"""``runner check-all``: every check in one command (ADR 12 items 1 and 15).

Developers end each attempt with it, the lead's pre-commit hook runs it, and headless jobs must
pass it before the runner commits their work. It runs everything and reports every failure,
then exits non-zero, so nothing hides behind a pipe (M4: `mypy | tail`).
"""

from collections.abc import Callable, Collection
from dataclasses import dataclass
from pathlib import Path

from runner import i18n
from runner.config import project_checks
from runner.gates import layout_problems
from runner.procs import run_bounded

# Commits that touch only these skip the hook: they can't break a check.
HOOK_SKIPS = (
    "docs/",
    *(f".factory/{d}" for d in ("tasks/", "cards/", "adr/", "planning/", "reviews/", "sessions/")),
    ".factory/seed.md",
    ".factory/project.md",
)
_OUTPUT_LIMIT = 4000
# Set by git for hooks; a test's git subprocess would inherit them and write into the
# commit being made (it did once: `commit -a` failed on a test fixture's file). The author
# ones override a test repo's own `user.name`: test_setup saw the owner's name, not the
# runner's, and blocked a lead commit (2026-10-15).
GIT_HOOK_ENV = (
    "GIT_INDEX_FILE",
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_PREFIX",
    "GIT_OBJECT_DIRECTORY",
    "GIT_AUTHOR_NAME",
    "GIT_AUTHOR_EMAIL",
    "GIT_AUTHOR_DATE",
    "GIT_CONFIG_PARAMETERS",
)


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    output: str = ""


def _exec(repo: Path, args: list[str], timeout: int) -> tuple[int | None, str]:
    code, out, err = run_bounded(args, repo, timeout)
    if code is None:
        return None, f"timed out after {timeout}s"
    output = (out + err).strip()
    if len(output) > _OUTPUT_LIMIT:
        output = "…(truncated)…\n" + output[-_OUTPUT_LIMIT:]
    return code, output


def _i18n_problems(repo: Path, timeout: int) -> list[str]:
    if not project_checks(repo).translations:
        return []
    return i18n.regenerated_problems(repo, timeout) + i18n.compiled_out_of_date(repo)


def _command(repo: Path, name: str, args: list[str], timeout: int) -> Check:
    code, output = _exec(repo, args, timeout)
    return Check(name, code == 0, output)


def _problems(name: str, problems: list[str]) -> Check:
    return Check(name, not problems, "\n".join(problems))


def check_all(
    repo: Path,
    timeout: int,
    *,
    task_id: str | None = None,
    fix: bool = False,
    only: Collection[str] | None = None,
) -> list[Check]:
    """Run every check, every test file on main included (ADR 21). ``fix`` formats first;
    ``task_id`` names the task, whose checks are the same as any other's. ``only`` runs just
    the checks it names (the runner's look at main, F106 D5)."""
    if fix:
        _exec(repo, ["uv", "run", "ruff", "format", "."], timeout)
        _exec(repo, ["uv", "run", "ruff", "check", "--fix", "."], timeout)
    project = project_checks(repo)
    tests = ["uv", "run", "pytest", "-q", "-p", "no:cacheprovider", *project.test_dirs]
    runs: list[tuple[str, Callable[[], Check]]] = [
        (
            "ruff check",
            lambda: _command(repo, "ruff check", ["uv", "run", "ruff", "check", "."], timeout),
        ),
        (
            "ruff format",
            lambda: _command(
                repo, "ruff format", ["uv", "run", "ruff", "format", "--check", "."], timeout
            ),
        ),
        (
            "mypy",
            lambda: (
                _command(repo, "mypy", ["uv", "run", "mypy", *project.mypy], timeout)
                if project.mypy
                else Check("mypy", True)
            ),
        ),
        ("translations", lambda: _problems("translations", _i18n_problems(repo, timeout))),
        ("layout", lambda: _problems("layout", layout_problems(repo))),
        ("tests", lambda: _command(repo, "tests", tests, timeout)),
    ]
    return [run() for name, run in runs if only is None or name in only]


def render(results: list[Check]) -> str:
    lines = []
    for result in results:
        lines.append(f"## {result.name}: {'ok' if result.ok else 'FAIL'}")
        if not result.ok and result.output:
            lines.append(result.output)
    failed = [r.name for r in results if not r.ok]
    lines.append("")
    lines.append(
        f"check-all: {len(failed)} failed ({', '.join(failed)})" if failed else "check-all: OK"
    )
    return "\n".join(lines) + "\n"


def hook_can_skip(staged: list[str]) -> bool:
    """A commit that only touches docs or tasks can't break a check (ADR 12 item 15)."""
    return bool(staged) and all(path.startswith(HOOK_SKIPS) for path in staged)
