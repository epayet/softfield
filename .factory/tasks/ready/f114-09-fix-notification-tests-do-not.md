---
id: f114-09-fix-notification-tests-do-not
milestone: f114-i-want-to-be-notified-only
difficulty: 5
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
- tests/factory_dashboard/test_overview.py
finding: f69-i-want-a-button-to-switch-C1044-5
tests_only: true
---

### Goal
Fix a checkpoint finding on f114-06-fix-notification-tests-do-not's tests: Notification tests do not exercise the specified navigation and worker behaviors

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.factory/tasks/done/f114-06-fix-notification-tests-do-not.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1044-5, should-fix: in `tests/factory_dashboard/test_app.py`, line 1471.

### Finding
f69-i-want-a-button-to-switch-C1044-5: Notification tests do not exercise the specified navigation and worker behaviors
> The service-worker test checks source-text fragments rather than running notification clicks, so it does not verify focus and `postMessage` with a client or `openWindow` without one. The listener test checks rejected external/null links but never verifies that a safe local link navigates. The direct-click test invokes no real notification handler because it uses an empty `window.shown` fallback, and the rejected-worker test checks only the fallback body, not that tapping navigates. Finally, the three-item bundle test uses three identical ADR titles and does not assert the exact ordered body of distinct item titles; the bundle-link checks only test for a project substring. Exercise these paths and assert their actual outputs.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
