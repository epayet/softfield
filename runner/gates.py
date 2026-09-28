"""The gates a task must pass before it is merged (docs/workflow.md)."""

import subprocess
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from runner import i18n
from runner.gitops import Git
from runner.tasks import Task, queued_tests

ALWAYS_ALLOWED = ("docs/discoveries.md",)
DEPENDENCY_FILES = ("pyproject.toml", "uv.lock")
DEPENDENCY_DIRS = ("coucou/static/coucou/vendor/",)
BLOCKED_FILE = "BLOCKED.md"
BLOCKED_CATEGORIES = ("false-assumption", "needs-file", "needs-info", "unrelated-problem")
_OUTPUT_LIMIT = 6000


@dataclass(frozen=True)
class GateResult:
    name: str
    ok: bool
    output: str = ""


@dataclass(frozen=True)
class GateContext:
    repo: Path
    git: Git
    task: Task
    base: str
    protected: tuple[str, ...]
    timeout: int


def matches_any(path: str, patterns: Iterable[str]) -> bool:
    pure = PurePosixPath(path)
    return any(pure.full_match(p) for p in patterns)


# --- file-level gates (pure functions over the list of changed files) -------------


def outside_allowed(changed: Iterable[str], allowed: Iterable[str]) -> list[str]:
    ok = set(allowed) | set(ALWAYS_ALLOWED)
    return sorted(f for f in changed if f not in ok)


def touching_protected(changed: Iterable[str], protected: Iterable[str]) -> list[str]:
    patterns = list(protected)
    return sorted(f for f in changed if matches_any(f, patterns))


def dependency_changes(changed: Iterable[str]) -> list[str]:
    return sorted(f for f in changed if f in DEPENDENCY_FILES or f.startswith(DEPENDENCY_DIRS))


def layout_problems(repo: Path) -> list[str]:
    """One unit test file per module, named after it: tests/unit/test_x.py <-> coucou/x.py."""
    problems = []
    for tests_dir, package in (("tests/unit", "coucou"), ("tests/runner", "runner")):
        root = repo / tests_dir
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.py")):
            rel = path.relative_to(repo).as_posix()
            if path.name in {"__init__.py", "conftest.py"}:
                continue
            if path.parent != root:
                problems.append(f"{rel}: unit tests live directly in {tests_dir}/")
            elif not path.name.startswith("test_"):
                problems.append(f"{rel}: unit test files are named test_<module>.py")
            elif not (repo / package / f"{path.name[5:]}").is_file():
                problems.append(f"{rel}: no module {package}/{path.name[5:]} to match it")
    return problems


def parse_blocked(text: str) -> str | None:
    """The category on the first line of BLOCKED.md, or None if it isn't valid."""
    first = text.strip().splitlines()[0] if text.strip() else ""
    if first.upper().startswith("CATEGORY:"):
        category = first.split(":", 1)[1].strip().lower()
        if category in BLOCKED_CATEGORIES:
            return category
    return None


# --- gates ----------------------------------------------------------------------


def _result(name: str, problems: list[str]) -> GateResult:
    return GateResult(name, not problems, "\n".join(problems))


def _command(name: str, ctx: GateContext, *args: str) -> GateResult:
    try:
        proc = subprocess.run(
            list(args),
            cwd=ctx.repo,
            capture_output=True,
            text=True,
            timeout=ctx.timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return GateResult(name, False, f"timed out after {ctx.timeout}s")
    output = (proc.stdout + proc.stderr).strip()
    if len(output) > _OUTPUT_LIMIT:
        output = "…(truncated)…\n" + output[-_OUTPUT_LIMIT:]
    return GateResult(name, proc.returncode == 0, output)


def gate_allowed_files(ctx: GateContext) -> GateResult:
    bad = outside_allowed(ctx.git.changed_files(ctx.base), ctx.task.files)
    return _result("allowed-files", [f"changed but not in files: {f}" for f in bad])


def gate_protected(ctx: GateContext) -> GateResult:
    bad = touching_protected(ctx.git.changed_files(ctx.base), ctx.protected)
    return _result("protected-paths", [f"protected path changed: {f}" for f in bad])


def gate_tests_unchanged(ctx: GateContext) -> GateResult:
    changed = ctx.git.changed_files(ctx.base)
    bad = [f for f in changed if f.startswith("tests/") and ctx.git.exists_at(ctx.base, f)]
    return _result("existing-tests-unchanged", [f"existing test file changed: {f}" for f in bad])


def gate_dependencies(ctx: GateContext) -> GateResult:
    bad = dependency_changes(ctx.git.changed_files(ctx.base))
    return _result("no-new-dependencies", [f"dependency file changed: {f}" for f in bad])


def gate_diff_size(ctx: GateContext) -> GateResult:
    size = ctx.git.diff_size(ctx.base)
    problems = [f"diff is {size} lines; max_diff is {ctx.task.max_diff}"]
    return _result("max-diff", problems if size > ctx.task.max_diff else [])


def gate_layout(ctx: GateContext) -> GateResult:
    return _result("layout", layout_problems(ctx.repo))


def gate_translations(ctx: GateContext) -> GateResult:
    """Every user-facing string has a French translation, compiled (ADR 00, A2)."""
    problems = i18n.regenerated_problems(ctx.repo, ctx.timeout)
    return _result("translations", problems + i18n.compiled_out_of_date(ctx.repo))


def gate_ruff(ctx: GateContext) -> GateResult:
    check = _command("ruff", ctx, "uv", "run", "ruff", "check", ".")
    if not check.ok:
        return check
    return _command("ruff", ctx, "uv", "run", "ruff", "format", "--check", ".")


def gate_mypy(ctx: GateContext) -> GateResult:
    return _command("mypy", ctx, "uv", "run", "mypy", "coucou", "tests", "runner")


def gate_task_tests(ctx: GateContext) -> GateResult:
    return _command("task-tests", ctx, "uv", "run", "pytest", "-q", *ctx.task.tests)


def gate_all_tests(ctx: GateContext) -> GateResult:
    skipped = sorted(queued_tests(ctx.repo / "tasks", ctx.task.id))
    return _command(
        "all-tests",
        ctx,
        "uv",
        "run",
        "pytest",
        "-q",
        "tests/unit",
        "tests/integration",
        "tests/runner",
        *(f"--ignore={path}" for path in skipped),
    )


GATES: tuple[Callable[[GateContext], GateResult], ...] = (
    gate_allowed_files,
    gate_protected,
    gate_tests_unchanged,
    gate_dependencies,
    gate_diff_size,
    gate_layout,
    gate_translations,
    gate_ruff,
    gate_mypy,
    gate_task_tests,
    gate_all_tests,
)


def run_gates(ctx: GateContext) -> list[GateResult]:
    """Run gates in order, stopping at the first failure."""
    results = []
    for gate in GATES:
        result = gate(ctx)
        results.append(result)
        if not result.ok:
            break
    return results
