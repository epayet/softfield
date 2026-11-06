---
id: f89-04-fix-meters-say-when-read-tests
milestone: f89-does-allowance-refresh-at-the-beginning
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_planning.py
tests:
- tests/factory_dashboard/test_planning.py
- tests/factory_dashboard/test_overview.py
finding: f89-does-allowance-refresh-at-the-beginning-C1881-3
tests_only: true
---

### Goal
Fix a checkpoint finding on f89-02-meters-say-when-read's tests: Read-label tests check presence, not the promised uniqueness and row-specific content

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f89-02-meters-say-when-read.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f89-does-allowance-refresh-at-the-beginning-C1881-3, should-fix: in `tests/factory_dashboard/test_planning.py`, line 283.

### Finding
f89-does-allowance-refresh-at-the-beginning-C1881-3: Read-label tests check presence, not the promised uniqueness and row-specific content
> The lead-window test uses `in` and would pass if “read at 03:59” appeared more than once, despite the Done when requiring it once. Also, `test_each_claude_row_shows_its_own_read_label` in `tests/factory_dashboard/test_overview.py` checks the same timestamp in both rows, so it would not catch one row displaying another window's reading time. Assert the exact occurrence count and use distinct timestamps with exact row-specific expectations.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 2753
gate_failures: []
tokens: 2445667
```
