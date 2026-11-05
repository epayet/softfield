---
id: f69-09-fix-theme-switch-plate-tests
milestone: f69-i-want-a-button-to-switch
area: factory
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
finding: f81-assess-the-current-ui-state-of-C1743-2
tests_only: true
---

### Goal
Fix a checkpoint finding on f69-07-theme-switch-plate's tests: Theme switch test checks presence, not its contents

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f69-07-theme-switch-plate.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f81-assess-the-current-ui-state-of-C1743-2, should-fix: in `tests/factory_dashboard/test_app.py`, line 2937.

### Finding
f81-assess-the-current-ui-state-of-C1743-2: Theme switch test checks presence, not its contents
> `test_every_page_has_the_theme_button` only matches a button with the expected ID. It would pass if the switch still displayed the old words or lacked its switch role, label, moon, or sun. Add assertions for the rendered button structure and absence of text; the behavior tests do not cover those requirements.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1054
gate_failures: []
tokens: 229455
```
