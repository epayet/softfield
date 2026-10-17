---
id: f114-05-fix-bundled-notifications-lose-project
milestone: f114-i-want-to-be-notified-only
difficulty: 5
depends_on: []
files:
- factory_dashboard/static/notify.js
tests:
- tests/factory_dashboard/test_app.py
- tests/factory_dashboard/test_overview.py
finding: f69-i-want-a-button-to-switch-C1035-5
---

### Goal
Fix a checkpoint finding on f114-02-one-notification-opens-its-page: Bundled notifications lose project context, and rejected worker notifications cannot navigate on tap

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.factory/tasks/done/f114-02-one-notification-opens-its-page.md`. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1035-5, should-fix: in `factory_dashboard/static/notify.js`, line 24.

### Finding
f69-i-want-a-button-to-switch-C1035-5: Bundled notifications lose project context, and rejected worker notifications cannot navigate on tap
> The multi-item branch uses `/planning` without the current project, breaking the Done when: “Several: the title ‘N things need you’ ... the link `/planning` with the page's project kept as the item links keep it.” Also, when `showNotification` rejects, the fallback creates a direct `Notification` without an `onclick` handler, so tapping it does not open its link, contrary to: “a click on a notification shown without a service worker takes the page to its link.”

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 4053
gate_failures: []
tokens: 991147
```
