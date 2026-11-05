---
id: f179-06-fix-lead-split-tests
milestone: f179-how-is-sonnet-doing-as-an
difficulty: 4
depends_on: []
files:
- tests/factory_dashboard/test_queries.py
tests:
- tests/factory_dashboard/test_queries.py
finding: f69-i-want-a-button-to-switch-C1849-2
tests_only: true
---

### Goal
Fix a checkpoint finding on f179-01-lead-split's tests: The date-filter test does not exercise the end bound.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f179-01-lead-split.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1849-2, should-fix: in `tests/factory_dashboard/test_queries.py`.

### Finding
f69-i-want-a-button-to-switch-C1849-2: The date-filter test does not exercise the end bound.
> `test_start_and_end_keep_tickets_by_first_job_started` checks only `start`; add assertions that `end` includes and excludes tickets according to their first job's start time.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
