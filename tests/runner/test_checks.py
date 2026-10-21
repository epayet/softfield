"""`runner check-all`: every check, one command, a non-zero exit on any failure (ADR 12)."""

from pathlib import Path

from runner import checks
from tests.runner.conftest import write_task


def _fake_exec(results: dict[str, int], calls: list[list[str]]):
    def run(repo: Path, args: list[str], timeout: int) -> tuple[int | None, str]:
        calls.append(args)
        key = " ".join(args[2:4])
        return results.get(key, 0), f"output of {key}"

    return run


def test_every_check_runs_and_failures_are_all_reported(repo: Path, monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(checks, "_exec", _fake_exec({"ruff check": 1, "mypy coucou": 1}, calls))
    monkeypatch.setattr(checks, "_i18n_problems", lambda repo, timeout: [])
    results = checks.check_all(repo, 60)
    assert [r.name for r in results] == [
        "ruff check",
        "ruff format",
        "mypy",
        "translations",
        "layout",
        "tests",
    ]
    assert [r.name for r in results if not r.ok] == ["ruff check", "mypy"]
    assert calls[-1][:3] == ["uv", "run", "pytest"]


def test_fix_formats_before_checking(repo: Path, monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(checks, "_exec", _fake_exec({}, calls))
    monkeypatch.setattr(checks, "_i18n_problems", lambda repo, timeout: [])
    checks.check_all(repo, 60, fix=True)
    assert calls[0] == ["uv", "run", "ruff", "format", "."]
    assert calls[1] == ["uv", "run", "ruff", "check", "--fix", "."]


def test_other_queued_tasks_tests_run_too(repo: Path, monkeypatch):
    """ADR 21: every test file on main is checked, whatever the queue holds."""
    write_task(repo / ".factory" / "tasks" / "ready", "m1-01-mine")
    other = write_task(repo / ".factory" / "tasks" / "ready", "m1-02-other")
    other.write_text(other.read_text().replace("tests/unit/test_thing.py", "tests/unit/test_x.py"))
    calls: list[list[str]] = []
    monkeypatch.setattr(checks, "_exec", _fake_exec({}, calls))
    monkeypatch.setattr(checks, "_i18n_problems", lambda repo, timeout: [])
    checks.check_all(repo, 60, task_id="m1-01-mine")
    assert not [arg for arg in calls[-1] if arg.startswith("--ignore")]


def test_a_tasks_own_tests_run_even_when_another_queued_task_lists_them(repo: Path, monkeypatch):
    """f1-33: f1's lead tickets listed existing files that other queued tickets also listed,
    and no gate ran them."""
    write_task(repo / ".factory" / "tasks" / "ready", "m1-01-mine")
    write_task(
        repo / ".factory" / "tasks" / "ready", "m1-02-other"
    )  # lists tests/unit/test_thing.py too
    lead = write_task(repo / ".factory" / "tasks" / "ready", "m1-03-lead")
    lead.write_text(
        lead.read_text()
        .replace("milestone: 1\n", "milestone: 1\nagent: lead\n")
        .replace("tests/unit/test_thing.py", "tests/unit/test_lead.py")
    )
    calls: list[list[str]] = []
    monkeypatch.setattr(checks, "_exec", _fake_exec({}, calls))
    monkeypatch.setattr(checks, "_i18n_problems", lambda repo, timeout: [])
    checks.check_all(repo, 60, task_id="m1-01-mine")
    assert not [arg for arg in calls[-1] if arg.startswith("--ignore=")]


def test_only_runs_the_checks_it_names(repo: Path, monkeypatch):
    """F106 D5: the runner runs on main only the checks a lead ticket failed."""
    calls: list[list[str]] = []
    monkeypatch.setattr(checks, "_exec", _fake_exec({"ruff check": 1}, calls))

    def translations(repo: Path, timeout: int) -> list[str]:
        raise AssertionError("translations ran")

    monkeypatch.setattr(checks, "_i18n_problems", translations)
    monkeypatch.setattr(checks, "layout_problems", lambda repo: ["tests/stray_tmp.py"])
    results = checks.check_all(repo, 60, only=["layout", "ruff check"])
    assert [(r.name, r.ok) for r in results] == [("ruff check", False), ("layout", False)]
    assert calls == [["uv", "run", "ruff", "check", "."]]


def test_report_ends_with_a_verdict():
    results = [checks.Check("ruff check", True), checks.Check("mypy", False, "bad type")]
    text = checks.render(results)
    assert "mypy: FAIL" in text and "bad type" in text
    assert text.rstrip().endswith("check-all: 1 failed (mypy)")
    assert checks.render([checks.Check("mypy", True)]).rstrip().endswith("check-all: OK")


def test_docs_and_tasks_only_commits_skip_the_hook():
    assert checks.hook_can_skip([".factory/adr/12-x.md", ".factory/tasks/ready/m5-01-x.md"])
    assert not checks.hook_can_skip(["docs/a.md", "runner/loop.py"])
    assert not checks.hook_can_skip([])


def test_the_hook_reads_the_commits_index_before_anything_clears_it():
    """`git commit -a` stages into a temporary index named by GIT_INDEX_FILE. The hook once
    unset it first, saw nothing staged and ran every check on a docs-only commit; the
    command clears it itself, once it has read what is staged."""
    hook = Path(__file__).parents[2] / ".factory" / "hooks" / "pre-commit"
    code = [line for line in hook.read_text().splitlines() if not line.startswith("#")]
    assert not [line for line in code if "GIT_INDEX_FILE" in line]
    assert code[-1] == "exec softfield check-all --hook"
