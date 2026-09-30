from pathlib import Path

from runner import gates
from runner.gates import (
    GateContext,
    GateResult,
    added_skips,
    dependency_changes,
    gate_all_tests,
    gate_tests_fail_on_main,
    is_test_file,
    layout_problems,
    outside_allowed,
    parse_blocked,
    touching_protected,
)
from runner.gitops import Git
from runner.tasks import parse_task
from tests.runner.conftest import git, write_task


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
    vendored = "factory_dashboard/static/vendor/htmx.min.js"
    changed = ["uv.lock", "coucou/static/coucou/vendor/alpine.js", vendored, "a.py"]
    assert dependency_changes(changed) == [
        "coucou/static/coucou/vendor/alpine.js",
        vendored,
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


def test_layout_matches_browser_tests_to_js_modules(repo):
    js = repo / "coucou" / "static" / "coucou" / "js"
    js.mkdir(parents=True)
    (js / "outbox.js").write_text("")
    browser = repo / "tests" / "browser"
    browser.mkdir()
    (browser / "conftest.py").write_text("")
    (browser / "test_outbox.py").write_text("")
    assert layout_problems(repo) == []
    (browser / "test_render.py").write_text("")
    assert layout_problems(repo) == [
        "tests/browser/test_render.py: no module coucou/static/coucou/js/render.js to match it"
    ]


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


def test_added_skips_finds_ways_to_silence_a_test():
    diff = "\n".join(
        [
            "+++ b/tests/unit/test_thing.py",
            "+@pytest.mark.skip(reason='later')",
            "+    pytest.xfail('flaky')",
            "+pytestmark = pytest.mark.skipif(True, reason='x')",
            "-@pytest.mark.skip",  # removing a skip is fine
            "+def test_skipping_rope():",
            "+    assert skip_count == 0",
        ]
    )
    assert added_skips(diff) == [
        "@pytest.mark.skip(reason='later')",
        "pytest.xfail('flaky')",
        "pytestmark = pytest.mark.skipif(True, reason='x')",
    ]


def test_is_test_file():
    assert is_test_file("tests/unit/test_thing.py")
    assert is_test_file("tests/browser/test_render.py")
    assert not is_test_file("tests/e2e/test_display.py")  # runs on staging
    assert not is_test_file("tests/browser/conftest.py")
    assert not is_test_file("coucou/test_utils.py")


def _branch_with(repo: Path, files: dict[str, str | None]) -> GateContext:
    """A task branch off main that writes (or deletes, for None) the given files."""
    git(repo, "checkout", "-q", "-b", "task/x")
    for rel, text in files.items():
        if text is None:
            (repo / rel).unlink()
        else:
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "wip")
    task = parse_task(write_task(repo / "var", "m1-01-thing"), 1000)
    return GateContext(repo, Git(repo), task, "main", (), 60)


def _fake_pytest(monkeypatch, code: int, seen: dict[str, str]):
    def fake_exec(ctx: GateContext, *args: str) -> tuple[int | None, str]:
        seen["args"] = " ".join(args)
        seen["thing"] = (ctx.repo / "coucou" / "thing.py").read_text()
        seen["new_exists"] = str((ctx.repo / "coucou" / "new.py").exists())
        seen["test"] = (ctx.repo / "tests" / "unit" / "test_thing.py").read_text()
        return code, "pytest output"

    monkeypatch.setattr(gates, "_exec", fake_exec)


def test_new_tests_run_against_mains_code_and_must_fail(repo: Path, monkeypatch):
    ctx = _branch_with(
        repo,
        {
            "coucou/thing.py": "def thing() -> int:\n    return 42\n",
            "coucou/new.py": "X = 1\n",
            "tests/unit/test_thing.py": "def test_thing():\n    assert thing() == 42\n",
        },
    )
    seen: dict[str, str] = {}
    _fake_pytest(monkeypatch, 1, seen)
    result = gate_tests_fail_on_main(ctx)
    assert result.ok, result.output
    # While the tests ran: main's code, the branch's tests.
    assert "raise NotImplementedError" in seen["thing"]
    assert seen["new_exists"] == "False"
    assert "thing() == 42" in seen["test"]
    assert seen["args"].endswith("tests/unit/test_thing.py")
    # Afterwards the branch is back as it was.
    assert "return 42" in (repo / "coucou" / "thing.py").read_text()
    assert (repo / "coucou" / "new.py").exists()
    assert git(repo, "status", "--porcelain") == ""


def test_tests_that_pass_without_the_change_fail_the_gate(repo: Path, monkeypatch):
    ctx = _branch_with(
        repo,
        {
            "coucou/thing.py": "def thing() -> int:\n    return 42\n",
            "tests/unit/test_thing.py": "def test_thing():\n    assert True\n",
        },
    )
    _fake_pytest(monkeypatch, 0, {})
    result = gate_tests_fail_on_main(ctx)
    assert not result.ok
    assert "pass without your code change" in result.output
    assert "return 42" in (repo / "coucou" / "thing.py").read_text()


def test_no_changed_tests_means_the_lead_wrote_them(repo: Path, monkeypatch):
    ctx = _branch_with(repo, {"coucou/thing.py": "def thing() -> int:\n    return 42\n"})
    _fake_pytest(monkeypatch, 0, {})
    assert gate_tests_fail_on_main(ctx).ok


def _diff(path: str, *added: str) -> str:
    lines = [f"diff --git a/{path} b/{path}", f"--- a/{path}", f"+++ b/{path}", "@@ -1 +1 @@"]
    return "\n".join([*lines, *(f"+{line}" for line in added)]) + "\n"


def test_weak_test_patterns_flag_what_a_person_cant_do():
    diff = _diff(
        "tests/browser/test_compose.py",
        "    if page.get_by_role('alert').is_visible():",
        "    if page.locator('li').count() > 0:",
        "    page.evaluate(\"() => el.dispatchEvent(new Event('submit'))\")",
        "    page.evaluate(\"() => { el.value = 'x'; }\")",
        "    time.sleep(1)",
        "    page.wait_for_timeout(500)",
        '    page.wait_for_function("window.sent.length === 1")',
        "    page.wait_for_function(",
        '        f"window.sent.length === {n}"',
        "    )",
    )
    problems = gates.weak_test_patterns(diff)
    assert len(problems) == 8
    assert all(p.startswith("tests/browser/test_compose.py: ") for p in problems)
    assert "wait_for_function" in problems[-1]


def test_weak_test_patterns_let_good_waits_and_other_folders_through():
    good = _diff(
        "tests/browser/test_me.py",
        '    page.wait_for_function("() => window.sent.length === 1")',
        '    page.wait_for_function("t => document.title === t", arg="x")',
        "    page.wait_for_function(",
        '        "async () => (await navigator.serviceWorker.ready) !== null"',
        "    )",
        "    assert page.get_by_role('button').is_visible()",
        "    count = len(items)",
        "    page.wait_for_timeout(1000)  # pattern-ok: proves nothing arrives",
    )
    elsewhere = _diff("tests/integration/test_revocation.py", "    time.sleep(0.1)")
    assert gates.weak_test_patterns(good + elsewhere) == []


def test_empty_modules_are_flagged(tmp_path: Path):
    (tmp_path / "coucou").mkdir()
    (tmp_path / "coucou" / "real.py").write_text('"""Doc."""\n\nX = 1\n')
    (tmp_path / "coucou" / "empty.py").write_text('"""Only a docstring."""\n# and a comment\n')
    (tmp_path / "coucou" / "empty.js").write_text("// nothing\n/* at\n all */\n\n")
    (tmp_path / "coucou" / "real.js").write_text("// a module\nexport const x = 1;\n")
    added = ["coucou/real.py", "coucou/empty.py", "coucou/empty.js", "coucou/real.js"]
    assert gates.empty_modules(tmp_path, added) == [
        "coucou/empty.py: a new module with no code in it",
        "coucou/empty.js: a new module with no code in it",
    ]
