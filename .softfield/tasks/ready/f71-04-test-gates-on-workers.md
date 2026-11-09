---
id: f71-04-test-gates-on-workers
milestone: f71-i-suspect-we-might-need-to
difficulty: 2
depends_on: []
agent: lead
files:
  - runner/config.py
  - runner/gates.py
  - tests/runner/test_gates.py
tests:
  - tests/runner/test_gates.py
---

### Goal
The `task-tests` and `tests-fail-on-main` gates run on the project's workers, as `all-tests` does, and `tests-fail-on-main` stops at its first failure.

### Context
Read `.softfield/cards/f71-i-suspect-we-might-need-to.md` ("What we saw on 2026-11-05", D9), `suite_args` in `runner/config.py`, and `gate_task_tests`, `gate_all_tests` and `gate_tests_fail_on_main` in `runner/gates.py`. `test_all_tests_runs_on_the_projects_workers` in `tests/runner/test_gates.py` is the test to follow.
- `tests-fail-on-main` passes on exit code 1 or 2, so one failure already gives its verdict: add `-x`.
- A test file that can't import what the task adds must still pass this gate on workers. Check which exit code that gives with `pytest-xdist`, and that a file with no tests still gives "no tests collected".
- A project with `test_workers = 0` keeps one process.

### Done when
- with `test_workers = 4`, both gates call pytest with `-n 4`; with 0, without `-n`
- `tests-fail-on-main` calls pytest with `-x`, and its verdicts are the same: tests that fail or can't import pass the gate, tests that pass or aren't collected fail it
- `tests-fail-on-main` still puts the branch back when it stops early
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
