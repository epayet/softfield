---
id: f114-06-fix-notification-tests-do-not
milestone: f114-i-want-to-be-notified-only
difficulty: 5
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
- tests/factory_dashboard/test_overview.py
finding: f69-i-want-a-button-to-switch-C1035-6
tests_only: true
---

### Goal
Fix a checkpoint finding on f114-02-one-notification-opens-its-page's tests: Notification tests do not verify batching or tap navigation behavior

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.factory/tasks/done/f114-02-one-notification-opens-its-page.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1035-6, should-fix: in `tests/factory_dashboard/test_app.py`, line 835.

### Finding
f69-i-want-a-button-to-switch-C1035-6: Notification tests do not verify batching or tap navigation behavior
> The notification tests cover a single new item and all-done, but do not assert that three new items produce one notification with the exact bundled title and newline-separated titles, that the next look produces none, or that the bundled link retains the project. They also do not exercise direct-notification click navigation, safe versus external service-worker messages, or the worker’s actual focus/postMessage and no-client openWindow behavior; `test_sw_finds_open_dashboard_tab_on_notification_tap` only checks for source-text fragments. Test those specified behaviors, including the rejected-worker fallback.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
