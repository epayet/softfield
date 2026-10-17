---
id: f114-08-fix-bundled-link-test-accepts
milestone: f114-i-want-to-be-notified-only
difficulty: 5
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
- tests/factory_dashboard/test_overview.py
finding: f69-i-want-a-button-to-switch-C1044-4
tests_only: true
---

### Goal
Fix a checkpoint finding on f114-05-fix-bundled-notifications-lose-project's tests: Bundled-link test accepts malformed destinations

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.factory/tasks/done/f114-05-fix-bundled-notifications-lose-project.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1044-4, should-fix: in `tests/factory_dashboard/test_app.py`, line 1043.

### Finding
f69-i-want-a-button-to-switch-C1044-4: Bundled-link test accepts malformed destinations
> `test_bundled_notifications_include_the_project_context` only checks that the link contains `?project=coucou`, so a wrong path or malformed URL can pass. Check the exact `/planning?project=coucou` destination (or its parsed path and query) to verify the project is kept on the required page.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
