from runner.gates import (
    dependency_changes,
    layout_problems,
    outside_allowed,
    parse_blocked,
    touching_protected,
)


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
