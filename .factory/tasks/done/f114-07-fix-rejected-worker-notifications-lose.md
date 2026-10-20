---
id: f114-07-fix-rejected-worker-notifications-lose
milestone: f114-i-want-to-be-notified-only
difficulty: 5
depends_on: []
files:
- factory_dashboard/static/notify.js
tests:
- tests/factory_dashboard/test_app.py
- tests/factory_dashboard/test_overview.py
finding: f69-i-want-a-button-to-switch-C1044-3
---

### Goal
Fix a checkpoint finding on f114-05-fix-bundled-notifications-lose-project: Rejected worker notifications lose tap navigation; bundle links also leave project values unencoded

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.factory/tasks/done/f114-05-fix-bundled-notifications-lose-project.md`. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1044-3, should-fix: in `factory_dashboard/static/notify.js`, line 24.

### Finding
f69-i-want-a-button-to-switch-C1044-3: Rejected worker notifications lose tap navigation; bundle links also leave project values unencoded
> This breaks the Goal: “Fix a checkpoint finding on f114-02-one-notification-opens-its-page: Bundled notifications lose project context, and rejected worker notifications cannot navigate on tap.” When `showNotification` rejects, the fallback notification has no `onclick` handler, so it cannot navigate. Also, line 57 concatenates the project value directly into the bundle URL; names containing `&` or `#` are truncated or misparsed, losing project context.

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 10049
gate_failures: ['task-tests', 'task-tests']
tokens: 1727935
```
