---
id: f81-16-fix-now-readouts-tests-tests
milestone: f81-assess-the-current-ui-state-of
agent: lead
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
- tests/factory_dashboard/test_app.py
finding: f69-i-want-a-button-to-switch-C1844-1
tests_only: true
---

### Goal
Fix a checkpoint finding on f81-11-fix-now-readouts-tests's tests: Readout assertions accept incorrect values

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f81-11-fix-now-readouts-tests.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1844-1, should-fix: in `tests/factory_dashboard/test_overview.py`, line 112.

### Finding
f69-i-want-a-button-to-switch-C1844-1: Readout assertions accept incorrect values
> The captured values are checked with substring matches: `112 min` can satisfy the elapsed assertion, `142k` the token assertion, and `130 s` the heartbeat assertion. The waiting test similarly accepts a time such as `115:00`. Compare each captured value to the exact expected content; also assert the expected plate count rather than `>= 4`, which allows duplicate or unexpected plates.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
