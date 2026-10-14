---
id: f6-28-fix-coming-tests-do-not
milestone: f6-planning-room
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_planning.py
tests:
- tests/factory_dashboard/test_planning.py
finding: f6-planning-room-C529-4
tests_only: true
---

### Goal
Fix a checkpoint finding on f6-20-desk-coming's tests: Coming tests do not check the reply time or the Overview's Needs you count.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f6-20-desk-coming.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f6-planning-room-C529-4, should-fix: in `tests/factory_dashboard/test_planning.py`, line 890.

### Finding
f6-planning-room-C529-4: Coming tests do not check the reply time or the Overview's Needs you count.
> The open-planner test only checks for the generic phrase “waiting for the lead,” so it passes when the expected time is missing (`None`). The count test compares the Planning tab count but never checks Overview's Needs you, despite the Done when requiring both to remain unchanged.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 2125
gate_failures: []
tokens: 1902559
```
