---
id: f4-26-fix-the-cached-token-regression
milestone: f4-always-on
difficulty: 2
depends_on:
- f4-36-fix-reserve-pill-test-deleted
files:
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f4-always-on-C231-2
---

### Goal
Fix a checkpoint finding on f4-06-running-tokens: The cached-token regression test is nested and never collected

### Context
A should-fix finding (f4-always-on-C231-2) by copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f4-06-running-tokens.md`: in `tests/factory_dashboard/test_overview.py`, line 201. What it found is under Finding.

### Finding
> This test function is indented inside test_a_run_on_the_reserve_has_the_pill, so pytest does not collect or execute it. The cached-token summation therefore has no active regression test, despite the test body asserting the expected result.

### Done when
- what the finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
