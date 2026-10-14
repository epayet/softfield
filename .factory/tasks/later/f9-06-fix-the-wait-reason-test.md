---
id: f9-06-fix-the-wait-reason-test
milestone: f9-line-polish
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f9-line-polish-C420-1
tests_only: true
---

### Goal
Fix a checkpoint finding on f4-39-next-in-line-says-why's tests: The wait-reason test does not prove reasons belong only to their own rows.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.factory/tasks/done/f4-39-next-in-line-says-why.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f9-line-polish-C420-1, should-fix: in `tests/factory_dashboard/test_overview.py`, `test_next_in_line_says_why`.

### Finding
f9-line-polish-C420-1: The wait-reason test does not prove reasons belong only to their own rows.
> The test checks that each ticket and each expected reason appear somewhere in Next in line, then checks that a ticket's row contains its expected reason if that ticket appears there. It never asserts that a row lacks other tickets' reasons or that the tickets occupy separate rows, so output that mixes reasons across rows could pass despite the ticket's requirement.

### Done when
- each of `f1-14-lead`, `f1-12-waits-running` and `f1-13-waits-escalated` is found in exactly one Next in line row, and the test fails if a ticket's row is missing (no `if ticket in row` that skips it)
- that row holds its own reason and none of the other two reasons
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
