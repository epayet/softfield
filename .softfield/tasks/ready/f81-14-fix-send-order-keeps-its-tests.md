---
id: f81-14-fix-send-order-keeps-its-tests
milestone: f81-assess-the-current-ui-state-of
agent: lead
difficulty: 1
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
finding: f69-i-want-a-button-to-switch-C1830-2
tests_only: true
---

### Goal
Fix a checkpoint finding on f81-09-send-order-keeps-its-colour's tests: Send-order test does not check its disabled appearance

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f81-09-send-order-keeps-its-colour.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1830-2, should-fix: in `tests/factory_dashboard/test_app.py`, line 3976.

### Finding
f69-i-want-a-button-to-switch-C1830-2: Send-order test does not check its disabled appearance
> The test checks only that the rendered button has `btn` and `go`; those classes are present even though the CSS cascade makes the disabled button transparent. It should check the enabled hazard background and the disabled plate background after styles are applied.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
