"""The gates a task must pass before it is merged (docs/workflow.md)."""

import ast
import re
import subprocess
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field, replace
from pathlib import Path, PurePosixPath

from runner import i18n
from runner.gitops import Git
from runner.tasks import Task, queued_tests

ALWAYS_ALLOWED = ("docs/discoveries.md",)
DEPENDENCY_FILES = ("pyproject.toml", "uv.lock")
DEPENDENCY_DIRS = ("coucou/static/coucou/vendor/", "factory_dashboard/static/vendor/")
BLOCKED_FILE = "BLOCKED.md"
BLOCKED_CATEGORIES = ("false-assumption", "needs-file", "needs-info", "unrelated-problem")
_OUTPUT_LIMIT = 6000
# Ways to silence a test instead of fixing the code (ADR 07 item 4).
_SKIP_RE = re.compile(
    r"pytest\.mark\.(skip|skipif|xfail)\b|pytest\.(skip|xfail|importorskip)\(|\.(skip|fixme)\("
)

# One line per gate, told to the local model on a retry: what to do, not only what failed
# (ADR 07 item 6).
NO_CHANGES = "no-changes"

HINTS = {
    NO_CHANGES: "Your previous attempt changed nothing: it ended before any edit. Make the"
    " changes the task asks for, starting with the smallest one.",
    "protected-paths": "Undo your changes to the protected files listed below. If the goal"
    " can't be reached without them, write BLOCKED.md with `CATEGORY: needs-file`.",
    "no-new-skips": "Remove the skip/xfail you added. Fix the code, or the test if it's wrong.",
    "no-new-dependencies": "Undo the dependency change and use what's already installed.",
    "max-diff": "Your diff is far bigger than the goal needs: you probably rewrote a file."
    " Make small, targeted edits instead.",
    "layout": "Keep one test file per module, named test_<module>.py, directly in its folder.",
    "translations": "Add the missing French to coucou/locale/fr/LC_MESSAGES/ and compile it"
    " with msgfmt, as AGENTS.md shows.",
    "ruff": "Run `uv run ruff format` and `uv run ruff check --fix` on your files, then fix"
    " what's left.",
    "mypy": "Fix the type errors below.",
    "task-tests": "Make these tests pass. Change a test only if it's wrong about the goal.",
    "all-tests": "Your change broke other tests. Fix the code; change a test only if the goal"
    " changes that behaviour.",
    "tests-fail-on-main": "Your tests also pass without your code change, so they don't test"
    ' it. Make them check the behaviour in "Done when".',
    "test-patterns": "Test as a person would: click, fill, select_option, then wait with"
    ' locator.wait_for() or wait_for_function("() => ..."). Never skip a step with `if`,'
    " never set values or fire events from JavaScript, never sleep. Delete empty modules.",
}


@dataclass(frozen=True)
class GateResult:
    name: str
    ok: bool
    output: str = ""
    seconds: float = field(default=0.0, compare=False)  # set by run_gates, for the metrics


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


def is_test_file(path: str) -> bool:
    """A pytest file the task gates run (e2e runs on staging, not here)."""
    pure = PurePosixPath(path)
    return (
        path.startswith("tests/")
        and not path.startswith("tests/e2e/")
        and pure.name.startswith("test_")
        and pure.suffix == ".py"
    )


def added_skips(diff: str) -> list[str]:
    """Added lines of a unified diff that skip or xfail a test."""
    return [
        line[1:].strip()
        for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++") and _SKIP_RE.search(line)
    ]


# Weak test patterns (ADR 12 item 3), in the browser and end-to-end tests only. Each one let a
# test pass without testing what a person does (m4-F1, F2, F7; m4-06's CSP trap).
PATTERN_DIRS = ("tests/browser/", "tests/e2e/")
PATTERN_OK = "# pattern-ok:"
_WEAK_PATTERNS = (
    (
        re.compile(r"^\s*(if|elif)\b.*\.(is_visible|count)\("),
        "a test that skips a step when something is missing passes without testing",
    ),
    (
        re.compile(r"dispatchEvent\(|\.value\s*=(?!=)"),
        "sets a value or fires an event from JavaScript: act as a person would",
    ),
    (re.compile(r"\btime\.sleep\(|\.wait_for_timeout\("), "sleeps instead of waiting for a result"),
)
_WAIT_FN = re.compile(r"\.wait_for_function\(\s*(.*)$")
_STRING = re.compile(r"^\s*f?[\"']")
# A predicate that is a function: "() => …", "async () => …", "x => …", "function …".
_FUNCTION_STRING = re.compile(r"^\s*f?[\"']\s*(\(|async\b|\w+\s*=>|function\b)")
_BARE_WAIT = (
    "wait_for_function with a bare expression: the real pages' CSP blocks it once it"
    ' polls. Pass a function: "() => ..."'
)


def _bare_wait(argument: str) -> bool:
    return bool(_STRING.match(argument)) and not _FUNCTION_STRING.match(argument)


def weak_test_patterns(diff: str) -> list[str]:
    """Added lines of a unified diff, in the browser and e2e tests, that match a weak pattern."""
    problems: list[str] = []
    path = ""
    waiting = False  # the previous added line opened wait_for_function( with no argument
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else ""
            waiting = False
            continue
        if not line.startswith("+") or not path.startswith(PATTERN_DIRS):
            continue
        code = line[1:]
        if PATTERN_OK in code:
            waiting = False
            continue
        if waiting and code.strip():
            if _bare_wait(code):
                problems.append(f"{path}: {_BARE_WAIT}: {code.strip()}")
            waiting = False
        for pattern, why in _WEAK_PATTERNS:
            if pattern.search(code):
                problems.append(f"{path}: {why}: {code.strip()}")
        if match := _WAIT_FN.search(code):
            argument = match.group(1)
            if not argument.strip():
                waiting = True
            elif _bare_wait(argument):
                problems.append(f"{path}: {_BARE_WAIT}: {code.strip()}")
    return problems


_JS_COMMENT = re.compile(r"//[^\n]*|/\*.*?\*/", re.DOTALL)


def empty_modules(repo: Path, added: Iterable[str]) -> list[str]:
    """New Python or JavaScript modules with no code, only comments or a docstring (m4-F7)."""
    problems = []
    for rel in added:
        path = repo / rel
        if not path.is_file() or path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8")
        if rel.endswith(".py"):
            try:
                body = ast.parse(text).body
            except SyntaxError:
                continue
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                body = body[1:]
            empty = not body
        elif rel.endswith(".js"):
            empty = not _JS_COMMENT.sub("", text).strip()
        else:
            continue
        if empty:
            problems.append(f"{rel}: a new module with no code in it")
    return problems


# test folder -> (module folder, module suffix): tests/unit/test_x.py <-> coucou/x.py, and
# tests/browser/test_x.py <-> coucou/static/coucou/js/x.js (ADR 06 item 2).
LAYOUTS = {
    "tests/unit": ("coucou", ".py"),
    "tests/runner": ("runner", ".py"),
    "tests/browser": ("coucou/static/coucou/js", ".js"),
    "tests/factory_dashboard": ("factory_dashboard", ".py"),
}


def layout_problems(repo: Path) -> list[str]:
    """One test file per module, named after it (ADR 00 A1, ADR 06)."""
    problems = []
    for tests_dir, (package, suffix) in LAYOUTS.items():
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
            elif not (repo / package / f"{path.stem[5:]}{suffix}").is_file():
                problems.append(f"{rel}: no module {package}/{path.stem[5:]}{suffix} to match it")
    return problems


BLOCKED_CATEGORY_WITHIN = 5  # lines; a heading above the category is fine (ADR 04 item 2)


def parse_blocked(text: str) -> str | None:
    """The category from the first ``CATEGORY:`` line near the top of BLOCKED.md, or None."""
    for line in text.strip().splitlines()[:BLOCKED_CATEGORY_WITHIN]:
        if line.strip().upper().startswith("CATEGORY:"):
            category = line.split(":", 1)[1].strip().lower()
            return category if category in BLOCKED_CATEGORIES else None
    return None


# --- gates ----------------------------------------------------------------------


def _result(name: str, problems: list[str]) -> GateResult:
    return GateResult(name, not problems, "\n".join(problems))


def _exec(ctx: GateContext, *args: str) -> tuple[int | None, str]:
    """Run a command in the repo: its exit code (None on timeout) and trimmed output."""
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
        return None, f"timed out after {ctx.timeout}s"
    output = (proc.stdout + proc.stderr).strip()
    if len(output) > _OUTPUT_LIMIT:
        output = "…(truncated)…\n" + output[-_OUTPUT_LIMIT:]
    return proc.returncode, output


def _command(name: str, ctx: GateContext, *args: str) -> GateResult:
    code, output = _exec(ctx, *args)
    return GateResult(name, code == 0, output)


def gate_protected(ctx: GateContext) -> GateResult:
    bad = touching_protected(ctx.git.changed_files(ctx.base), ctx.protected)
    return _result("protected-paths", [f"protected path changed: {f}" for f in bad])


def gate_no_new_skips(ctx: GateContext) -> GateResult:
    """Juniors may change tests (ADR 07 item 4), but not silence them."""
    added = added_skips(ctx.git.run("diff", "-U0", f"{ctx.base}...HEAD", "--", "tests/"))
    return _result("no-new-skips", [f"skip added: {line}" for line in added])


def gate_dependencies(ctx: GateContext) -> GateResult:
    bad = dependency_changes(ctx.git.changed_files(ctx.base))
    return _result("no-new-dependencies", [f"dependency file changed: {f}" for f in bad])


def gate_diff_size(ctx: GateContext) -> GateResult:
    """A backstop against a rewritten file, not a sizing tool (ADR 07 item 8)."""
    size = ctx.git.diff_size(ctx.base)
    problems = [f"diff is {size} lines, over the limit of {ctx.task.max_diff}"]
    return _result("max-diff", problems if size > ctx.task.max_diff else [])


def gate_layout(ctx: GateContext) -> GateResult:
    return _result("layout", layout_problems(ctx.repo))


def gate_test_patterns(ctx: GateContext) -> GateResult:
    diff = ctx.git.run("diff", "-U0", f"{ctx.base}...HEAD", "--", *PATTERN_DIRS)
    added = ctx.git.run("diff", "--name-only", "--diff-filter=A", f"{ctx.base}...HEAD")
    problems = weak_test_patterns(diff) + empty_modules(ctx.repo, added.split())
    return _result("test-patterns", problems)


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
    return _command(
        "mypy", ctx, "uv", "run", "mypy", "coucou", "tests", "runner", "factory_dashboard"
    )


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
        "tests/browser",
        "tests/factory_dashboard",
        *(f"--ignore={path}" for path in skipped),
    )


def gate_tests_fail_on_main(ctx: GateContext) -> GateResult:
    """The test files a task added or changed must fail against main's code (ADR 07 item 4).

    Puts back main's version of every changed file outside tests/, runs the changed test
    files, then resets the branch. Tests that pass without the task's code don't test it.
    """
    name = "tests-fail-on-main"
    changed = ctx.git.changed_files(ctx.base)
    tests = sorted(f for f in changed if is_test_file(f))
    if not tests:
        return GateResult(name, True, "no test files changed")
    try:
        for path in changed:
            if path.startswith("tests/"):
                continue
            if ctx.git.exists_at(ctx.base, path):
                ctx.git.run("checkout", ctx.base, "--", path)
            else:
                (ctx.repo / path).unlink(missing_ok=True)
        code, output = _exec(ctx, "uv", "run", "pytest", "-q", "-p", "no:cacheprovider", *tests)
    finally:
        ctx.git.run("reset", "-q", "--hard", "HEAD")
    if code in (1, 2):  # tests failed, or couldn't import what the task adds
        return GateResult(name, True, "fail without the change: " + ", ".join(tests))
    why = "no tests collected" if code == 5 else "they pass without your code change"
    return GateResult(name, False, f"{', '.join(tests)}: {why}\n{output}")


GATES: tuple[Callable[[GateContext], GateResult], ...] = (
    gate_protected,
    gate_no_new_skips,
    gate_dependencies,
    gate_diff_size,
    gate_layout,
    gate_test_patterns,
    gate_translations,
    gate_ruff,
    gate_mypy,
    gate_task_tests,
    gate_all_tests,
    gate_tests_fail_on_main,
)


def run_gates(ctx: GateContext) -> list[GateResult]:
    """Run gates in order, stopping at the first failure."""
    results = []
    for gate in GATES:
        started = time.monotonic()
        result = replace(gate(ctx), seconds=time.monotonic() - started)
        results.append(result)
        if not result.ok:
            break
    return results
