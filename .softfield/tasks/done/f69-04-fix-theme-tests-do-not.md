---
id: f69-04-fix-theme-tests-do-not
milestone: f69-i-want-a-button-to-switch
area: factory
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
finding: f69-i-want-a-button-to-switch-C1035-2
tests_only: true
---

### Goal
Fix a checkpoint finding on f69-03-fix-theme-tests-do-not's tests: Theme tests do not verify rendered chart colors or the prior header height

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f69-03-fix-theme-tests-do-not.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1035-2, should-fix: in `tests/factory_dashboard/test_app.py`, line 1926.

### Finding
f69-i-want-a-button-to-switch-C1035-2: Theme tests do not verify rendered chart colors or the prior header height
> The theme-switch assertions check CSS custom-property values, not that a chart redraws with the new colors or that the rendered floor uses them. The 390px test compares dark and light heights on the same current header, so it does not establish that the header is no taller than it was before the button was added. Check the actual rendered colors and compare the header against the prior-height requirement.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 3710
gate_failures: []
tokens: 749885
```
