---
id: f89-03-fix-meters-say-when-read
milestone: f89-does-allowance-refresh-at-the-beginning
difficulty: 2
depends_on: []
files:
- factory_dashboard/overview.py
tests:
- tests/factory_dashboard/test_overview.py
- tests/factory_dashboard/test_planning.py
finding: f89-does-allowance-refresh-at-the-beginning-C1881-2
---

### Goal
Fix a checkpoint finding on f89-02-meters-say-when-read: Read timestamps disappear for stale readings

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f89-02-meters-say-when-read.md`. What it found is under Finding:
- f89-does-allowance-refresh-at-the-beginning-C1881-2, should-fix: in `factory_dashboard/overview.py`, line 659.

### Finding
f89-does-allowance-refresh-at-the-beginning-C1881-2: Read timestamps disappear for stale readings
> The status check suppresses `read_label` when a reading's reset time has passed, even though the row still has an `at` timestamp. This breaks the ticket Goal: “The planning room's lead window and the Overview's allowance rows say when each reading was taken.” Show the label whenever a reading timestamp exists; reserve `None` for windows with no reading.

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 860
gate_failures: ['all-tests', 'stopped']
tokens: 23868
```
