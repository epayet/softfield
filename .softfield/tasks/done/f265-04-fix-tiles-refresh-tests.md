---
id: f265-04-fix-tiles-refresh-tests
milestone: f265-the-factory-now-section-in-planning
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_planning.py
tests:
- tests/factory_dashboard/test_planning.py
finding: f265-the-factory-now-section-in-planning-C2444-3
tests_only: true
---

### Goal
Fix a checkpoint finding on f265-01-tiles-refresh's tests: The browser test verifies the factory tile but not the lead-window refresh or reload-free behavior.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f265-01-tiles-refresh.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f265-the-factory-now-section-in-planning-C2444-3, should-fix: in `tests/factory_dashboard/test_planning.py`, line 1289.

### Finding
f265-the-factory-now-section-in-planning-C2444-3: The browser test verifies the factory tile but not the lead-window refresh or reload-free behavior.
> The new browser test writes a running job and checks `#factory-now` after a poll, but it does not update and verify allowance/gauge content in `#lead-window`, nor explicitly verify that no navigation/reload occurred. The HTML attribute tests check presence rather than the live gauge update, so the second tile's refresh could regress undetected.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1157
gate_failures: []
tokens: 820846
```
