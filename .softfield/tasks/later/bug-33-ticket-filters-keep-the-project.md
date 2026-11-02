---
id: bug-33-ticket-filters-keep-the-project
milestone: bugs
difficulty: 3
depends_on: []
area: factory
priority: 61
finding: f4-always-on-F5
files:
  - factory_dashboard/templates/tickets.html
  - factory_dashboard/templates/ticket.html
tests:
  - tests/factory_dashboard/test_tickets.py
---

### Goal
On a second project, the Tickets page's milestone links and its filter form show that project's tickets, not the default one's.

### Context
Read `factory_dashboard/templates/tickets.html` (the milestone link, `/tickets?milestone={{ t.milestone }}{{ q }}`, and the filter form) and `factory_dashboard/templates/ticket.html` (the same link); `q` is `"?project=…"`, built in `factory_dashboard/app.py`. The worked example for the form is the hidden `project` input in `factory_dashboard/templates/board.html`.
- Today the link reads `/tickets?milestone=f1?project=…` (two `?`), and the form drops `project`.
- Build the link's query with `urlencode` (both keys in one query), and add a hidden `project` input to the form.

### Done when
- on project "coucou", a ticket's milestone link is `/tickets?milestone=f1&project=coucou`, on the list and on the ticket's page
- following it lists only coucou's f1 tickets
- submitting the filter form on project "coucou" keeps `project=coucou`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
