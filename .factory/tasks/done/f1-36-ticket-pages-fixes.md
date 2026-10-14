---
id: f1-36-ticket-pages-fixes
milestone: f1
depends_on: [f1-10-ticket-pages]
difficulty: 3
finding: f1-cp4
files:
  - factory_dashboard/tickets.py
  - factory_dashboard/templates/ticket.html
  - factory_dashboard/templates/tickets.html
  - tests/factory_dashboard/test_tickets.py
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_tickets.py
---

### Goal
`/tickets/{id}` shows that ticket's own findings and its merge commit, and the tests would catch a wrong page.

### Context
Read `factory_dashboard/tickets.py`, `factory_dashboard/templates/ticket.html`, `factory_dashboard/templates/tickets.html` and `tests/factory_dashboard/test_tickets.py`; f1-10's spec is `tasks/done/f1-10-ticket-pages.md`. `write_fixture`, `tests/factory_dashboard/test_queries.py` and `tests/factory_dashboard/test_overview.py` stay untouched; put new rows in your own `tests/factory_dashboard/conftest.py` function (extend `write_tickets`).
- Facts about the page: `ticket_findings` selects by `milestone_id`, so every ticket of a milestone lists all of the milestone's findings; f1-10 asked for the findings with the ticket's own `ticket_id` (none is normal). The commit shows as its first 12 characters followed by "…", and no test reads it. The list prints "–" for 0 lines changed. `tests/factory_dashboard/conftest.py` has both a `tickets_client` fixture and `tests/factory_dashboard/test_tickets.py` a duplicate `client_with_tickets`; `tickets_client` is unused.
- Facts about the tests: `test_list_shows_tickets_newest_first` never checks that f1 tickets come before m4 ones, nor the order inside f1 (its comment names 12, 11, 10, 6, 5, 4 but asserts only the count of 9 and the two m4 ids). `test_ticket_detail_shows_result` ends in `"lines changed" in result.lower() or "50"`, true of any result; `test_ticket_detail_shows_all_jobs_in_order` counts `/jobs/` links in the whole page, not in the jobs section, and never checks the order; the findings test passes only because findings are attached to the milestone, so it hides the bug above; the 404 test, the state filter and the milestone filter are the only ones that read a whole row. No test uses the `milestone` filter or checks the breadcrumbs (project › milestone › ticket).

### Done when
- a finding written with a `ticket_id` shows on that ticket's page only, with its severity; a ticket with none shows no Findings section
- the page shows the merge commit (the full hash, or a short one without a trailing "…")
- the list shows 0 lines changed as 0
- tests: the whole list order is asserted (f1 before m4, highest id first inside f1); the result section is read cell by cell (state, merged by, commit, lines changed); jobs are read in order from the jobs section; `?milestone=` is tested; the breadcrumbs are tested; one fixture is used, not two
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1570
gate_failures: []
tokens: 1574955
```
