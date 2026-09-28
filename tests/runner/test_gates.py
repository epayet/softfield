from pathlib import Path

from runner import gates
from runner.gates import (
    GateContext,
    GateResult,
    dependency_changes,
    gate_all_tests,
    layout_problems,
    outside_allowed,
    parse_blocked,
    touching_protected,
)
from runner.gitops import Git
from runner.tasks import parse_task
from tests.runner.conftest import write_task


def test_outside_allowed_permits_discoveries():
    changed = ["coucou/a.py", "coucou/b.py", "docs/discoveries.md"]
    assert outside_allowed(changed, ["coucou/a.py"]) == ["coucou/b.py"]


def test_protected_globs():
    patterns = ["coucou/devices/**", "coucou/authz.py", "runner/**"]
    changed = [
        "coucou/devices/views/x.py",
        "coucou/authz.py",
        "coucou/ordering.py",
        "runner/cli.py",
    ]
    assert touching_protected(changed, patterns) == [
        "coucou/authz.py",
        "coucou/devices/views/x.py",
        "runner/cli.py",
    ]


def test_dependency_changes():
    assert dependency_changes(["uv.lock", "coucou/static/coucou/vendor/alpine.js", "a.py"]) == [
        "coucou/static/coucou/vendor/alpine.js",
        "uv.lock",
    ]


def test_layout(repo):
    assert layout_problems(repo) == []
    (repo / "tests" / "unit" / "test_missing.py").write_text("")
    (repo / "tests" / "unit" / "sub").mkdir()
    (repo / "tests" / "unit" / "sub" / "test_thing.py").write_text("")
    (repo / "tests" / "unit" / "helpers.py").write_text("")
    problems = layout_problems(repo)
    assert "tests/unit/test_missing.py: no module coucou/missing.py to match it" in problems
    assert "tests/unit/sub/test_thing.py: unit tests live directly in tests/unit/" in problems
    assert "tests/unit/helpers.py: unit test files are named test_<module>.py" in problems


def test_parse_blocked():
    assert parse_blocked("CATEGORY: needs-info\nWhat is X?") == "needs-info"
    assert parse_blocked("category: Needs-File\n") == "needs-file"
    assert parse_blocked("I'm stuck") is None
    assert parse_blocked("CATEGORY: vibes") is None
    assert parse_blocked("") is None
    # ADR 04 item 2: a heading above the category is fine, within the first 5 lines.
    assert parse_blocked("# BLOCKED.md\n\nCATEGORY: needs-file\nmsgfmt is denied") == "needs-file"
    assert parse_blocked("a\nb\nc\nd\ne\nCATEGORY: needs-info") is None
    assert parse_blocked("# BLOCKED\nCATEGORY: vibes\nCATEGORY: needs-info") is None


def test_all_tests_skips_other_queued_tasks_tests(repo: Path, monkeypatch):
    current = write_task(repo / "tasks" / "ready", "m1-01-current")
    other = write_task(repo / "tasks" / "ready", "m1-02-other")
    other.write_text(other.read_text().replace("test_thing.py", "test_other.py"))
    calls: list[tuple[str, ...]] = []

    def fake_command(name: str, ctx: GateContext, *args: str) -> GateResult:
        calls.append(args)
        return GateResult(name, True, "")

    monkeypatch.setattr(gates, "_command", fake_command)
    ctx = GateContext(repo, Git(repo), parse_task(current, 150), "main", (), 60)
    assert gate_all_tests(ctx).ok
    assert "--ignore=tests/unit/test_other.py" in calls[0]
    assert "--ignore=tests/unit/test_thing.py" not in calls[0]
