---
id: f5-00-gate-every-test-file
milestone: f5-board
depends_on: []
agent: lead
difficulty: 2
files:
  - runner/tasks.py
  - runner/gates.py
  - runner/checks.py
  - docs/workflow.md
tests:
  - tests/runner/test_gates.py
  - tests/runner/test_checks.py
  - tests/runner/test_tasks.py
---

### Goal
The all-tests gate and `runner check-all` run every test file on main, whatever tickets the queue holds ([ADR 21](../../docs/adr/21-gate-every-test-file.md), accepted 2026-10-04).

### Context
Read `docs/adr/21-gate-every-test-file.md`, then `runner/tasks.py` (`queued_tests`), `runner/gates.py` (the all-tests gate, where `skipped` feeds `--ignore=`) and `runner/checks.py` (the same in `check-all`). Test-first.
- `queued_tests` and both `--ignore` lists go. A test that asserts an `--ignore` is passed (`tests/runner/test_gates.py`, `tests/runner/test_checks.py`) becomes one that asserts no `--ignore=` is passed while another ticket in `ready/` lists a test file. `test_queued_tests_are_the_other_queued_tasks_tests` in `tests/runner/test_tasks.py` goes with the function.
- The task's own tests still run through `task-tests` and `tests-fail-on-main`, unchanged.
- In `docs/workflow.md`, gate 12 no longer mentions skipping other tasks' `tests:` files; cite ADR 21 instead of ADR 01 there.
- On 2026-10-04 the files the skip hid (`tests/factory_dashboard/test_line.py`, `tests/factory_dashboard/test_overview.py`, `tests/factory_dashboard/test_milestones.py`, `tests/factory_dashboard/test_tickets.py`, `tests/factory_dashboard/test_app.py`) passed on main (188 passed), so main stays green.

### Done when
- with a ticket in `ready/` listing an existing test file, the all-tests gate's and `check-all`'s pytest commands carry no `--ignore=`
- `queued_tests` no longer exists (`grep -rn queued_tests runner tests` finds nothing)
- `uv run runner check-all --task f5-00-gate-every-test-file` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
