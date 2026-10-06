---
id: f9-18-fix-milestone-filter-tests-can
milestone: f9-line-polish
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_timeline.py
tests:
- tests/factory_dashboard/test_timeline.py
finding: f9-line-polish-C467-3
tests_only: true
---

### Goal
Fix a checkpoint finding on f9-04-timeline-milestone-filter's tests: Milestone-filter tests can pass without proving the requested filters work.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f9-04-timeline-milestone-filter.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f9-line-polish-C467-3, should-fix: in `tests/factory_dashboard/test_timeline.py`, line 160.

### Finding
f9-line-polish-C467-3: Milestone-filter tests can pass without proving the requested filters work.
> `test_empty_milestone_returns_all_milestones` only asserts more than one bar, so it can pass when only the default milestone is shown; assert the expected jobs from both milestones. `test_no_milestone_param_uses_default` only asserts at least one bar, so it does not prove the default milestone is the only one shown. `test_form_preserves_project` checks only that input attributes exist, not that the hidden input is inside the form with the correct project value. Also verify the selected option for a non-default milestone and for All milestones.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
