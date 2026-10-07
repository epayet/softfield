---
id: f6-27-fix-coming-rows-lose-the
milestone: f6-planning-room
difficulty: 3
depends_on: []
files:
- factory_dashboard/planning.py
tests:
- tests/factory_dashboard/test_planning.py
finding: f6-planning-room-C529-3
---

### Goal
Fix a checkpoint finding on f6-20-desk-coming: Coming rows lose the expected reply time because the job kind comparison is wrong.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f6-20-desk-coming.md`. What it found is under Finding:
- f6-planning-room-C529-3, should-fix: in `factory_dashboard/planning.py`, line 259.

### Finding
f6-planning-room-C529-3: Coming rows lose the expected reply time because the job kind comparison is wrong.
> `metrics.open_jobs` returns the planner kind as lowercase `planner`, but this comparison checks uppercase `PLANNER`. As a result, `_next_reply` receives `pending=False` and returns `None` for an open planner row, rather than the expected timing. This breaks the Goal's requirement that each thread appear “with when it is expected.”

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 2035
gate_failures: []
tokens: 1178085
```
