---
id: f1-50-ticket-work-split-tests
milestone: f1
depends_on: []
difficulty: 2
finding: f1-cp10
files:
  - tests/factory_dashboard/test_tickets.py
tests:
  - tests/factory_dashboard/test_tickets.py
---

### Goal
The "Who did the work" tests on `/tickets/{id}` read each agent's row cell by cell, so a wrong count, role, minutes or dollars value fails them.

### Context
Read `factory_dashboard/tickets.py` (`ticket_agent_work`), `factory_dashboard/templates/ticket.html` (the `agent-work` section) and `test_ticket_agent_work_shows_two_agents` in `tests/factory_dashboard/test_tickets.py`. `write_fixture`, `tests/factory_dashboard/test_queries.py` and `tests/factory_dashboard/test_overview.py` stay untouched.
- Facts: f1-48 asked that tests "read the cells of the section, not just that the text appears". The merged test only checks that substrings occur anywhere in the section: `"1"` and `"2"` match any digit in any cell (or the `10000`/`200000` values), roles and minutes are never asserted, and `"merged"` is matched against the whole section. The order test finds `merged` by position, not by the row it is in.

### Done when
- for the ticket with two agents, the test parses each `<tr>` of the section and asserts, per agent row: the agent, roles text, job count, minutes, tokens in and cost in their own `<td>`; and that only the merging agent's row has `merged` in the last cell
- the order test asserts the row order (merger first, then by minutes) from the parsed rows
- the listed `tests:` pass, and fail if the job count, roles or minutes of a row change
- all gates pass (see `docs/workflow.md`)
