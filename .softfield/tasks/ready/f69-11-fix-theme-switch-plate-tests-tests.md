---
id: f69-11-fix-theme-switch-plate-tests-tests
milestone: f69-i-want-a-button-to-switch
agent: lead
area: factory
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
finding: f69-i-want-a-button-to-switch-C1826-1
tests_only: true
---

### Goal
Fix a checkpoint finding on f69-09-fix-theme-switch-plate-tests's tests: Theme-button test still does not verify its rendered contents

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f69-09-fix-theme-switch-plate-tests.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1826-1, should-fix: in `tests/factory_dashboard/test_app.py`, line 2971.

### Finding
f69-i-want-a-button-to-switch-C1826-1: Theme-button test still does not verify its rendered contents
> The test checks only that role, aria-label, aria-checked, title, and the theme-switch class occur, then checks that there is no text. It never checks the label’s value or that the button contains the moon and sun icons, so an empty label or missing icons would pass. The separate behavior tests do not cover those contents either.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
