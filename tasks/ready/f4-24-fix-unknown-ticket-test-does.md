---
id: f4-24-fix-unknown-ticket-test-does
milestone: f4-always-on
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f4-always-on-C228-4
---

### Goal
Fix a checkpoint finding on f4-04-running-goal: Unknown-ticket test does not assert that the goal line is absent

### Context
A should-fix finding (f4-always-on-C228-4) by copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f4-04-running-goal.md`: in `tests/factory_dashboard/test_overview.py`, line 178. What it found is under Finding.

### Finding
> Despite its name, this test checks only that the activity remains visible and the run card exists. It never checks that no title/goal line is rendered, so an unknown ticket could incorrectly show a goal and the test would still pass.

### Done when
- what the finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
