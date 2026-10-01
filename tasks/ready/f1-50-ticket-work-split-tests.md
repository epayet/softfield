---
id: f1-50-ticket-work-split-tests
milestone: f1
depends_on: []
difficulty: 2
finding: f1-cp10
files:
  - factory_dashboard/templates/ticket.html
  - tests/factory_dashboard/test_tickets.py
tests:
  - tests/factory_dashboard/test_tickets.py
---

### Goal
Each row of "Who did the work" on `/tickets/{id}` names its agent and its cells, and the tests read each agent's row cell by cell, so a wrong count, role, minutes or dollars value fails them.

### Context
Read `factory_dashboard/tickets.py` (`ticket_agent_work`), `factory_dashboard/templates/ticket.html` (the `agent-work` section) and `test_ticket_agent_work_shows_two_agents` in `tests/factory_dashboard/test_tickets.py`. `write_fixture`, `tests/factory_dashboard/test_queries.py` and `tests/factory_dashboard/test_overview.py` stay untouched.
- Facts: f1-48 asked that tests "read the cells of the section, not just that the text appears". The merged test only checks that substrings occur anywhere in the section: `"1"` and `"2"` match any digit in any cell (or the `10000`/`200000` values), roles and minutes are never asserted, and `"merged"` is matched against the whole section. The order test finds `merged` by position, not by the row it is in.
- The `tests-fail-on-main` gate puts back main's `ticket.html` and runs your changed tests: they must fail there. Test-only changes always pass on main, so the tests must rely on the attributes this ticket adds to the template.
- The page has other tables (findings for this ticket), so parse rows from the `agent-work` section only (`section_raw`), never from the whole page.
- For `f1-11-ticket-b` the fixture gives: `claude-opus` (merged) with roles `escalation`, 1 job, 10 minutes, 10000 tokens in, cost `2.00`; `local-qwen3.6-35b-a3b` with roles `developer ×2`, 2 jobs, 20 minutes, 200000 tokens in, cost `–`.

### Done when
- in the `agent-work` table each body `<tr>` carries `data-agent` with the agent name, and each `<td>` carries `data-col`: `agent`, `roles`, `jobs`, `minutes`, `tokens-in`, `cost`, `merged`; the page looks the same
- for the ticket with two agents, the test finds each row by its `data-agent` and asserts the text of every `data-col` cell: agent, roles, jobs, minutes, tokens in, cost; and that only the merging agent's `merged` cell says `merged` (the other one is empty)
- the order test asserts the list of `data-agent` values in row order equals merger first, then the others by minutes
- the listed `tests:` pass, fail against main's template, and fail if the job count, roles or minutes of a row change
- all gates pass (see `docs/workflow.md`)
