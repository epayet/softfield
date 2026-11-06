---
id: f197-03-fix-plant-box-asks-first-tests
milestone: f197-reverse-plant-and-plant-and-ask
difficulty: 1
depends_on: []
files:
- tests/factory_dashboard/test_planning.py
tests:
- tests/factory_dashboard/test_planning.py
finding: f89-does-allowance-refresh-at-the-beginning-C1900-1
tests_only: true
---

### Goal
Fix a checkpoint finding on f197-01-plant-box-asks-first's tests: Plant-box tests do not enforce the full requested behavior

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f197-01-plant-box-asks-first.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f89-does-allowance-refresh-at-the-beginning-C1900-1, should-fix: in `tests/factory_dashboard/test_planning.py`, line 2112.

### Finding
f89-does-allowance-refresh-at-the-beginning-C1900-1: Plant-box tests do not enforce the full requested behavior
> The class checks only require `plain` or `go` to be present, so they can pass with contradictory extra classes. No test checks that `#plant-ask` precedes `#plant-only`, that the accompanying line matches the required text, or that submitting each button sends the intended `ask` value. Add assertions for the exact classes, order, text, and submitted values.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
