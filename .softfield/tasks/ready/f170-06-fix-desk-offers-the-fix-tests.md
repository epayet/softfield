---
id: f170-06-fix-desk-offers-the-fix-tests
milestone: f170-there-s-a-blocked-ticket-that
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_planning.py
tests:
- tests/factory_dashboard/test_planning.py
finding: f170-there-s-a-blocked-ticket-that-C1695-2
tests_only: true
---

### Goal
Fix a checkpoint finding on f170-03-desk-offers-the-fix's tests: Blocked-ticket tests miss required rendered content and preserve obsolete expectations

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f170-03-desk-offers-the-fix.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f170-there-s-a-blocked-ticket-that-C1695-2, should-fix: in `tests/factory_dashboard/test_planning.py`.

### Finding
f170-there-s-a-blocked-ticket-that-C1695-2: Blocked-ticket tests miss required rendered content and preserve obsolete expectations
> The ticket explicitly says to change `test_runner_message_only_says_lead_is_looking` and `test_runner_message_then_lead_says_waits_on_thread`, but they still assert the forbidden lead-status suffixes and do not check that the runner’s ticket-wait count is retained. `test_blocked_ticket_with_replan_shows_approve_button` checks the data fields and button request, but not that the rendered item contains the exact first-point and replan text or that its link targets `/planning/f9`. `test_blocked_bug_ticket_keeps_standard_buttons` checks only that generic button classes occur somewhere; it should check the correct labels and styles on each button, which would catch the changed bug-ticket behavior.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
