---
id: f81-17-fix-readout-units-and-belt-tests
milestone: f81-assess-the-current-ui-state-of
agent: lead
area: factory
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f89-does-allowance-refresh-at-the-beginning-C1881-1
tests_only: true
---

### Goal
Fix a checkpoint finding on f81-12-fix-readout-units-and-belt-markup's tests: The markup test does not verify direct list-item parents or exercise the fast-lane bay

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f81-12-fix-readout-units-and-belt-markup.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f89-does-allowance-refresh-at-the-beginning-C1881-1, should-fix: in `tests/factory_dashboard/test_overview.py`, line 1042.

### Finding
f89-does-allowance-refresh-at-the-beginning-C1881-1: The markup test does not verify direct list-item parents or exercise the fast-lane bay
> This test only rules out `<div>` inside the ordered list; other invalid wrappers could still pass, and the default client does not ensure the fast-lane bay is rendered. It also only inspects the queue, so an empty `<small>` in the running difficulty readout could return without failing the test. Exercise a fast-lane case, verify each `<li>` is directly parented by an `<ol>` or `<ul>`, and check the running readout for empty `<small>` elements.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
