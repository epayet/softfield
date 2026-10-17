---
id: f69-05-fix-theme-tests-still-do
milestone: f69-i-want-a-button-to-switch
area: factory
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
finding: f69-i-want-a-button-to-switch-C1044-2
tests_only: true
---

### Goal
Fix a checkpoint finding on f69-04-fix-theme-tests-do-not's tests: Theme tests still do not verify rendered chart colors or the prior header height

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.factory/tasks/done/f69-04-fix-theme-tests-do-not.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1044-2, should-fix: in `tests/factory_dashboard/test_app.py`, line 2221.

### Finding
f69-i-want-a-button-to-switch-C1044-2: Theme tests still do not verify rendered chart colors or the prior header height
> The theme-switch test checks CSS custom properties, not the chart’s rendered series colors or that the chart redraws with them. The 390px test uses a 96px ceiling and compares light height to the current dark height; neither establishes the previous header height requirement. Assert the chart’s actual updated colors and compare the header against the prior-height baseline.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
