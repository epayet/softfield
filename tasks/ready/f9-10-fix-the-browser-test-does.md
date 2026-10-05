---
id: f9-10-fix-the-browser-test-does
milestone: f9-line-polish
difficulty: 4
depends_on: []
files:
- tests/factory_dashboard/test_line.py
tests:
- tests/factory_dashboard/test_line.py
finding: f9-line-polish-C423-3
---

### Goal
Fix a checkpoint finding on f3-29-machine-today: The browser test does not verify the displayed merge count.

### Context
A should-fix finding (f9-line-polish-C423-3) by copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f3-29-machine-today.md`: in `tests/factory_dashboard/test_line.py`, line 1004. What it found is under Finding.

### Finding
> The test sets `merged_today` to 3 but only checks whether any text contains “merged today.” It would pass if the renderer displayed a wrong count, so it does not verify the required content.

### Done when
- what the finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
