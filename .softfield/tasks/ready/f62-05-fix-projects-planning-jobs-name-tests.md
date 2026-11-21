---
id: f62-05-fix-projects-planning-jobs-name-tests
milestone: f62-claude-opus-review-on-overview-does
agent: lead
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_jobs.py
tests:
- tests/factory_dashboard/test_jobs.py
- tests/factory_dashboard/test_projects.py
- tests/factory_dashboard/test_coming.py
finding: f275-a-project-created-by-web-interface-C2611-2
tests_only: true
---

### Goal
Fix a checkpoint finding on f62-03-projects-planning-jobs-name-the-card's tests: Ticket-cell tests do not verify the required links and fallback per cell

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f62-03-projects-planning-jobs-name-the-card.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f275-a-project-created-by-web-interface-C2611-2, should-fix: in `tests/factory_dashboard/test_jobs.py`, line 388.

### Finding
f275-a-project-created-by-web-interface-C2611-2: Ticket-cell tests do not verify the required links and fallback per cell
> `test_ticket_cell_names_the_card_for_ticketless_review` is presence-based rather than content-based: it checks `F158` and a planning link anywhere in the HTML, not that the added review job's exact Ticket cell contains `F158`, nor that it uses that job's `?project=`. It never verifies the developer Ticket cell still has the exact `/tickets/<ticket>?project=` link or that a ticketless non-card role has an exact `–` cell. `test_projects.py::test_a_running_ticketless_review_names_the_card_on_projects_page` likewise checks the planning link anywhere in the page instead of inside the exact running line; `test_coming.py::test_a_pending_message_after_a_ticketless_review_says_after_review_f158` is narrower but only does not cover planner/checkpoint card naming.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
