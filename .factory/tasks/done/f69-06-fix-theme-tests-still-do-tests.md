---
id: f69-06-fix-theme-tests-still-do-tests
milestone: f69-i-want-a-button-to-switch
area: factory
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
finding: f51-when-a-plan-depends-on-an-C1375-1
tests_only: true
---

### Goal
Fix a checkpoint finding on f69-05-fix-theme-tests-still-do's tests: Theme tests still do not prove chart redraw or the prior header height

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.factory/tasks/done/f69-05-fix-theme-tests-still-do.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f51-when-a-plan-depends-on-an-C1375-1, should-fix: in `tests/factory_dashboard/test_app.py`, line 2762.

### Finding
f51-when-a-plan-depends-on-an-C1375-1: Theme tests still do not prove chart redraw or the prior header height
> The chart assertion checks the spend series color, but its `--a2` token remains `#ff9640` in both themes, and the selector accepts any colored path; it can pass without a theme-driven chart redraw. Check the rendered series color for a token that changes between themes and verify it updates after switching. At line 2872, the 390px test treats the current dark header height as the prior-height baseline and compares it with the current light height; assert against the actual prior-height requirement instead.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 3896
gate_failures: ['stopped', 'stopped']
tokens: 858710
```
