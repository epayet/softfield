---
id: f9-09-fix-idle-machines-omit-their
milestone: f9-line-polish
difficulty: 4
depends_on: []
files:
- factory_dashboard/static/factory.js
tests:
- tests/factory_dashboard/test_line.py
finding: f9-line-polish-C423-2
---

### Goal
Fix a checkpoint finding on f3-29-machine-today: Idle machines omit their idle label and can hide the merge count.

### Context
A should-fix finding (f9-line-polish-C423-2) by copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f3-29-machine-today.md`: in `factory_dashboard/static/factory.js`, line 261. What it found is under Finding.

### Finding
> This branch renders only one message: a lead’s next ticket takes precedence over its merge count, and a non-lead with merges gets the count instead of “idle.” The ticket requires the count under the idle label and the lead’s next ticket as additional information.

### Done when
- what the finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 2087
gate_failures: []
tokens: 1509381
```
