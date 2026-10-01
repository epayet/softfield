---
id: f1-39-ticket-findings-fix
milestone: f1
depends_on: [f1-36-ticket-pages-fixes]
difficulty: 2
finding: f1-cp7
files:
  - factory_dashboard/tickets.py
  - tests/factory_dashboard/test_tickets.py
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_tickets.py
---

### Goal
`/tickets/{id}` shows only findings written with that ticket's `ticket_id`, and a ticket with none shows no Findings section.

### Context
Read `ticket_findings` in `factory_dashboard/tickets.py`, `tests/factory_dashboard/test_tickets.py` and `tasks/done/f1-36-ticket-pages-fixes.md`. `write_fixture`, `tests/factory_dashboard/test_queries.py` and `tests/factory_dashboard/test_overview.py` stay untouched; extend `write_tickets` in `tests/factory_dashboard/conftest.py`.
- Facts: f1-36 kept `(findings.ticket_id = ? OR findings.ticket_id IS NULL)`, so every ticket of a milestone still lists the milestone's findings that have no ticket, which its Done when ruled out. `test_ticket_detail_shows_findings_with_severity` still passes only because of that: `M4-F1` and `M4-F2` have no `ticket_id`. `test_ticket_specific_finding_shows_only_on_that_ticket` branches on whether the section exists (`if … else`), so it passes either way for the other ticket. `ticket_id` is optional in `ticket_findings`, and with none it returns the whole milestone; the page always passes one.

### Done when
- a finding with a `ticket_id` shows on that ticket's page only, with its severity and summary; a finding without one shows on no ticket's page
- a ticket with no findings of its own has no Findings section
- tests: the findings test writes its own findings with a `ticket_id` (the `M4-*` ones are given one, or replaced); the other-ticket case asserts the section is absent, with no `if`; a milestone-wide finding is asserted absent from a ticket page
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
