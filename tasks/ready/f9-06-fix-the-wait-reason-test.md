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
---

### Goal
Fix a checkpoint finding on f4-39-next-in-line-says-why: The wait-reason test does not prove reasons belong only to their own rows.

### Context
A should-fix finding (f9-line-polish-C420-1) by copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f4-39-next-in-line-says-why.md`: in `tests/factory_dashboard/test_overview.py`, line 959. What it found is under Finding.

### Finding
> The test checks that each ticket and each expected reason appear somewhere in Next in line, then checks that a ticket's row contains its expected reason if that ticket appears there. It never asserts that a row lacks other tickets' reasons or that the tickets occupy separate rows, so output that mixes reasons across rows could pass despite the ticket's requirement.

### Done when
- what the finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
