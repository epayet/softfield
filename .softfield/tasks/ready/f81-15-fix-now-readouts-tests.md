---
id: f81-15-fix-now-readouts-tests
milestone: f81-assess-the-current-ui-state-of
agent: lead
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
- tests/factory_dashboard/test_overview.py
finding: f69-i-want-a-button-to-switch-C1830-3
tests_only: true
---

### Goal
Fix a checkpoint finding on f81-10-fix-now-readouts's tests: Queue separator test checks template source, not rendered text

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f81-10-fix-now-readouts.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1830-3, should-fix: in `tests/factory_dashboard/test_app.py`, line 3385.

### Finding
f69-i-want-a-button-to-switch-C1830-3: Queue separator test checks template source, not rendered text
> The test searches for a source-code substring rather than checking the queued-jobs branch's rendered text. The companion check in `test_overview.py` strips tags by replacing them with spaces, which can manufacture the separator it is meant to verify. Assert the actual rendered count and label with the text-node whitespace preserved.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
