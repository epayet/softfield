---
id: f121-03-what-counts-as-a-test
milestone: f121-projects-not-on-main-or-not
agent: lead
difficulty: 5
depends_on: [f121-02-check-commands-from-project]
files:
  - runner/config.py
  - runner/gates.py
  - runner/templates/project.toml
tests:
  - tests/runner/test_config.py
  - tests/runner/test_gates.py
---

### Goal
Which files are tests, which exit codes mean "these tests fail" and which lines silence a test come from the project's `[checks]`, so `tests-fail-on-main` and `no-new-skips` hold on a project that isn't pytest.

### Context
Read D4 and D5 in `.softfield/cards/f121-projects-not-on-main-or-not.md`, then `is_test_file`, `added_skips`, `_SKIP_RE`, `gate_no_new_skips` and `gate_tests_fail_on_main` in `runner/gates.py`, and `Checks` in `runner/config.py`.
- New keys: `test_files` (globs, default `["tests/**/test_*.py"]`), `fails_on_main` (exit codes, default `[1, 2]`) and `skip_patterns` (regexes, default today's `_SKIP_RE` pattern). Globs match as `matches_any` does.
- `tests/e2e/` stays out of the task's tests, as today.
- `gate_tests_fail_on_main` puts back main's code for every changed file that isn't a test file (today: outside `tests/`), runs the project's `test` command on the changed test files, and passes when the exit code is in `fails_on_main`. Its "no tests collected" message stays for pytest's 5 only.
- `gate_no_new_skips` reads the added lines of the changed test files, not of `tests/`. A tests-only ticket's rule ("changes only tests") uses test files too.
- A bad regex in `skip_patterns` raises `ConfigError`.

### Done when
- with no new keys, the gates judge exactly as today (pytest's 1 and 2 pass, 5 and 0 fail; `tests/test_x.py` is a test, `tests/e2e/test_x.py` is not)
- with `test_files = ["src/**/*.test.js"]` and `fails_on_main = [1]`, a branch adding `src/a.test.js` whose test command exits 1 on main's code passes `tests-fail-on-main`; exiting 0 or 2 fails it
- with `skip_patterns = ['\.only\(']`, a `.only(` added in a test file fails `no-new-skips`, and in a file that isn't a test it doesn't
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
