---
id: f69-10-fix-radius-test-dead-code
milestone: f69-i-want-a-button-to-switch
area: factory
difficulty: 2
depends_on: [f69-09-fix-theme-switch-plate-tests]
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
finding: f69-07-radius-test-dead-code
tests_only: true
---

### Goal
Fix a checkpoint finding on f69-07-theme-switch-plate's tests: `test_no_border_radius_except_top_bar_status_dot` can no longer fail.

### Context
In `tests/factory_dashboard/test_app.py`, `test_no_border_radius_except_top_bar_status_dot`: f69-07 indented the gauge-mark check, the new theme-switch check and `pytest.fail(...)` under the status-dot `if`, right after its `continue`. Those lines are now unreachable, so a `border-radius` added to any rule passes silently. Before f69-07 the gauge check and `pytest.fail` sat at the loop's level.

### Done when
- the gauge-mark and theme-switch checks and `pytest.fail` are back at the loop's level, so a rule with a `border-radius` other than the allowed ones fails the test (a test shows it, on a CSS string with a stray radius)
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 2649
gate_failures: ['mypy']
tokens: 1595340
```
