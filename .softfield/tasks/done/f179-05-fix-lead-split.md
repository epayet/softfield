---
id: f179-05-fix-lead-split
milestone: f179-how-is-sonnet-doing-as-an
difficulty: 4
depends_on: []
files:
- factory_dashboard/queries.py
tests:
- tests/factory_dashboard/test_queries.py
finding: f69-i-want-a-button-to-switch-C1849-1
---

### Goal
Fix a checkpoint finding on f179-01-lead-split: The fallback Opus mean does not represent the mean across Opus tickets.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f179-01-lead-split.md`. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1849-1, should-fix: in `factory_dashboard/queries.py`, line 588.

### Finding
f69-i-want-a-button-to-switch-C1849-1: The fallback Opus mean does not represent the mean across Opus tickets.
> The Done when says “a difficulty Opus never did takes Opus's mean over all its lead tickets.” This averages difficulty-level means equally, rather than averaging Opus-owned tickets, so difficulties with different ticket counts skew the fallback. Also, `_opus_mean_by_diff` includes any committed lead ticket with an Opus lead-role job, rather than limiting the baseline to tickets Opus owned and merged.

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1185
gate_failures: []
tokens: 1238537
```
