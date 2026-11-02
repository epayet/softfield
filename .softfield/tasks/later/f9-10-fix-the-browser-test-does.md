---
id: f9-10-fix-the-browser-test-does
milestone: f9-line-polish
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_line.py
tests:
- tests/factory_dashboard/test_line.py
finding: f9-line-polish-C423-3
tests_only: true
---

### Goal
Fix a checkpoint finding on f3-29-machine-today's tests: The browser test does not verify the displayed merge count.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f3-29-machine-today.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f9-line-polish-C423-3, should-fix: in `tests/factory_dashboard/test_line.py`, `test_idle_machine_with_merges_says_merged_today`.
- The words are drawn by `machine` in `factory_dashboard/static/factory.js`: "N merged today" under "idle".

### Finding
f9-line-polish-C423-3: The browser test does not verify the displayed merge count.
> The test sets `merged_today` to 3 but only checks whether any text contains “merged today.” It would pass if the renderer displayed a wrong count, so it does not verify the required content.

### Done when
- the test asserts that one of the machine's texts is exactly "3 merged today", so "0 merged today", "undefined merged today" or "merged today" alone would fail it
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
