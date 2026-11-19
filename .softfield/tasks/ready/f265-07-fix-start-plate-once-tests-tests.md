---
id: f265-07-fix-start-plate-once-tests-tests
milestone: f265-the-factory-now-section-in-planning
agent: lead
difficulty: 1
depends_on: []
files:
- tests/factory_dashboard/test_projects.py
tests:
- tests/factory_dashboard/test_projects.py
tests_only: true
---

### Goal
Make `test_start_it_sends_the_forms_json_and_shows_the_plate_at_once` prove that the request's polling adds no second plate.

### Context
By the lead, at a checkpoint, on the merge of `.softfield/tasks/done/f265-05-fix-start-plate-once-tests.md`. The code is right; its test is still weak: change only tests. They pass on main's code, as they should.
- `plate_.count() == 1` in `tests/factory_dashboard/test_projects.py` (about line 477) runs right after the plate first appears, before `#start-sent` shows "Asked", so any duplicate plate added by polling later would not be counted.
- The bug (bug-68) is duplicate plates from the request partial's polling bubbling to the form's listeners, so the check has to come after the poll has delivered "Asked", and after at least one more poll.

### Done when
- the one-plate check runs after `#start-sent` shows "Asked" and after a further poll has had time to happen (wait on a visible effect or advance the page clock, not a fixed sleep), and would fail without the `event.target !== form` guards in `factory_dashboard/templates/projects.html`
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
