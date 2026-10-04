---
id: f4-29-fix-queue-reason-tests-do
milestone: f4-always-on
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f4-always-on-C231-5
---

### Goal
Make the queue reason tests show that each reason belongs to its own ticket and to no other.

### Context
A should-fix finding (f4-always-on-C231-5) on the merge of `tasks/done/f4-08-queue-waits-for.md` said the dependency, escalation and Claude-wait tests checked a phrase anywhere in the Queue section, and did not use the `queue_rows` helper. That is out of date: f3-05-line-panels (commit e83ffa7) removed the Queue panel and `queue_rows`, and the reason is no longer shown on the page at all (the "Next in line" rows in `factory_dashboard/templates/_partials/running.html` show number, ticket, title and kind only). Do not bring back a Queue panel or `queue_rows`, and do not touch templates or `factory_dashboard/overview.py`.

Today the three tests (`test_a_ticket_whose_dependency_is_ready_waits_for_that_id`, `test_a_ticket_whose_dependency_is_escalated_waits_for_escalation`, `test_a_lead_ticket_waits_for_claude`, around line 429) read `queue()` directly through the `waits(db_path)` helper (line 416), a dict of ticket to `waits_for`. Each checks one ticket's entry only, so a reason that also appeared on another ticket would go unnoticed. The fixture tickets and their states are listed in the docstring of `write_queue` in `tests/factory_dashboard/conftest.py`; ready-now tickets have `waits_for` of None. `queue_client` writes it without Claude waiting, `queue_claude_client` with.

Change only these three tests: each compares the whole `waits(db_path)` dict for its fixture to the expected ticket-to-reason dict, so the named reason sits on its ticket and every other ticket has its own expected value. Run the tests first and read the actual dict from the failure output rather than guessing it.

### Done when
- the three tests each assert the full ticket-to-reason mapping for their fixture
- changing any one expected reason to another ticket makes a test fail (try it once, then restore)
- the listed `tests:` pass
- all gates pass (`uv run runner check-all --fix --task f4-29-fix-queue-reason-tests-do`)
