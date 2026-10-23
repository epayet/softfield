---
id: f51-04-fix-empty-list-keeps-proposals-tests
milestone: f51-when-a-plan-depends-on-an
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_planning.py
tests:
- tests/factory_dashboard/test_planning.py
finding: f51-when-a-plan-depends-on-an-C1366-2
tests_only: true
---

### Goal
Fix a checkpoint finding on f51-03-empty-list-keeps-proposals's tests: The empty-proposals test does not verify the thread proposal remains actionable

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.factory/tasks/done/f51-03-empty-list-keeps-proposals.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f51-when-a-plan-depends-on-an-C1366-2, should-fix: in `tests/factory_dashboard/test_planning.py`, line 2475.

### Finding
f51-when-a-plan-depends-on-an-C1366-2: The empty-proposals test does not verify the thread proposal remains actionable
> The test checks only that the proposal title appears in thread text. It must also check that the thread renders the proposal card/link to `/planning/f9/proposals/merge-f9` with its open state; title presence alone does not establish that the actionable proposal was preserved.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
