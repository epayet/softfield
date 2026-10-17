---
id: f69-03-fix-theme-tests-do-not
milestone: f69-i-want-a-button-to-switch
area: factory
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
finding: f69-i-want-a-button-to-switch-C1026-3
tests_only: true
---

### Goal
Fix a checkpoint finding on f69-01-theme-button's tests: Theme tests do not verify the promised visual changes or persistence.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.factory/tasks/done/f69-01-theme-button.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1026-3, should-fix: in `tests/factory_dashboard/test_app.py`, line 1841.

### Finding
f69-i-want-a-button-to-switch-C1026-3: Theme tests do not verify the promised visual changes or persistence.
> The click test checks only the button text/title and `data-theme`, not that charts and the floor actually change without a reload. The persistence test stops after the click without reloading or visiting another page, and the system-preference test reloads after changing the emulated scheme instead of checking a live change. The 390px test accepts any header up to 150px rather than comparing against the prior height. Add assertions for rendered chart/floor colors, reload and cross-page persistence, live system changes, and the actual prior-height requirement; these are required by the ticket’s Done when.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 3880
gate_failures: []
tokens: 2388850
```
