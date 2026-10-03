---
id: f4-21-fix-initial-page-load-can
milestone: f4-always-on
difficulty: 4
depends_on: []
files:
- factory_dashboard/static/factory.js
tests:
- tests/factory_dashboard/test_line.py
finding: f4-always-on-C228-1
---

### Goal
Fix a checkpoint finding on f3-03-line-motion: Initial page load can falsely flash the checks light

### Context
A should-fix finding (f4-always-on-C228-1) by copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f3-03-line-motion.md`: in `factory_dashboard/static/factory.js`, line 28. What it found is under Finding.

### Finding
> `_prev` starts empty, so the first draw treats any nonzero checks count from earlier today as a new result and flashes the light. Establish the initial counts as a baseline; only later refreshes should trigger a flash.

### Done when
- what the finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: task-tests)
attempts: 3
tokens: 473679
logs: var/runs/20261003-201706/f4-21-fix-initial-page-load-can
```
