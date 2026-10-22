---
id: f171-05-fix-state-less-empty-milestones
milestone: f171-there-are-dupliacted-tickets-on-the
priority: 3
difficulty: 3
depends_on: []
files:
- factory_dashboard/board.py
tests:
- tests/factory_dashboard/test_board.py
- tests/factory_dashboard/test_milestones.py
finding: f171-there-are-dupliacted-tickets-on-the-C1265-1
---

### Goal
Fix a checkpoint finding on f171-02-board-shows-cards-only: State-less empty milestones with a status still appear

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.factory/tasks/done/f171-02-board-shows-cards-only.md`. What it found is under Finding:
- f171-there-are-dupliacted-tickets-on-the-C1265-1, should-fix: in `factory_dashboard/board.py`, line 329.

### Finding
f171-there-are-dupliacted-tickets-on-the-C1265-1: State-less empty milestones with a status still appear
> This also affects `factory_dashboard/milestones.py:151-152`: both filters require `status` to be null as well as `state` and active tickets to be absent. A row with no state, no active tickets, and a non-null status therefore still appears, contrary to the Goal: “The board and the milestones list leave out a milestone row that is no card and has no tickets, so no untitled "F107" or second "F4" shows.”

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 3317
gate_failures: ['stopped']
tokens: 1968114
```
