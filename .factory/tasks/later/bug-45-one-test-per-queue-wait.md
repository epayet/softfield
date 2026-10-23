---
id: bug-45-one-test-per-queue-wait
milestone: bugs
difficulty: 2
depends_on: []
area: factory
priority: 73
finding: f4-always-on-F6
tests_only: true
files:
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_tickets.py
tests:
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_tickets.py
---

### Goal
No two dashboard tests assert the same thing under different names.

### Context
The code is right; the tests repeat themselves.
- In `tests/factory_dashboard/test_overview.py`, `test_a_ticket_whose_dependency_is_ready_waits_for_that_id` and `test_a_ticket_whose_dependency_is_escalated_waits_for_escalation` both assert `waits(db_path) == WAITS`. Keep one, named for the whole queue (`test_each_waiting_ticket_names_what_it_waits_for`), with the two comments saying which rows of `WAITS` are the running and the escalated dependency.
- In `tests/factory_dashboard/test_tickets.py`, f4-38's two tests insert inline the same `later` ticket the `later_client` fixture already has: use the fixture.

### Done when
- one test holds the `WAITS` assertion, and every key of `WAITS` is still checked
- f4-38's two tests use `later_client`, with every assertion they have today
- all gates pass (see `docs/workflow.md`)
