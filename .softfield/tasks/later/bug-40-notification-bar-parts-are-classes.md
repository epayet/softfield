---
id: bug-40-notification-bar-parts-are-classes
milestone: bugs
difficulty: 3
depends_on: []
area: factory
priority: 68
finding: f12-F9
files:
  - factory_dashboard/templates/base.html
  - factory_dashboard/static/notify.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
The notification bar's parts are found by class, not by `role="body"` and `role="actions"`, which aren't ARIA roles, and a screen reader hears the bar.

### Context
Read `#notify-bar` in `factory_dashboard/templates/base.html` (line 165), its `[role=body]` lookups in `factory_dashboard/static/notify.js` (lines 82 and 101), its `[role=body]` and `[role=actions]` rules in `factory_dashboard/static/dashboard.css` (lines 453–478), and the `test_notification_bar_*` tests in `tests/factory_dashboard/test_app.py`.
- Name the parts `class="notify-body"` and `class="notify-actions"`, and give the bar `role="status"`. The template's other `[role=status]` lookups (lines 92 and 100) are the top bar's, inside `bar`: make sure they don't find the notification bar's.

### Done when
- the bar's markup has no `role="body"` or `role="actions"`, and has `role="status"`
- every `test_notification_bar_*` test passes, with its selectors changed to the classes and no assertion lost
- the bar looks as today at phone and desktop width
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
