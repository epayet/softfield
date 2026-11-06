---
id: f215-03-fix-floor-without-grid-tests
milestone: f215-i-m-not-a-fan-of
difficulty: 1
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
finding: f89-does-allowance-refresh-at-the-beginning-C1900-2
tests_only: true
---

### Goal
Fix a checkpoint finding on f215-01-floor-without-grid's tests: Background and theme-token tests check presence, not the required values

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f215-01-floor-without-grid.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f89-does-allowance-refresh-at-the-beginning-C1900-2, should-fix: in `tests/factory_dashboard/test_app.py`, line 3384.

### Finding
f89-does-allowance-refresh-at-the-beginning-C1900-2: Background and theme-token tests check presence, not the required values
> `test_body_has_no_grid` checks only that `background-color` appears, so it would pass if its value were wrong rather than `var(--bg)`. The ticket also requires `--grid` to remain defined in both themes, but no test in this file checks that. Assert the expected background-color value and the token definitions in the dark and light theme blocks.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1001
gate_failures: []
tokens: 286003
```
