---
id: f81-11-fix-now-readouts-tests
milestone: f81-assess-the-current-ui-state-of
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
- tests/factory_dashboard/test_app.py
finding: f81-assess-the-current-ui-state-of-C1743-4
tests_only: true
---

### Goal
Fix a checkpoint finding on f81-06-now-readouts's tests: Running-job test checks text but not readout markup

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f81-06-now-readouts.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f81-assess-the-current-ui-state-of-C1743-4, should-fix: in `tests/factory_dashboard/test_overview.py`, line 87.

### Finding
f81-assess-the-current-ui-state-of-C1743-4: Running-job test checks text but not readout markup
> `test_a_job_with_a_fresh_heartbeat_is_running_now` checks the displayed strings after stripping tags, so it would pass if the old plain facts remained instead of `.readouts` and individual `.readout` plates. Assert the readout structure and number/unit/label placement, including the waiting-job words case.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
