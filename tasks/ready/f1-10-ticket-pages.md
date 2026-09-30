---
id: f1-10-ticket-pages
milestone: f1
depends_on: [f1-09-job-page, f1-34-jobs-pages-fixes]
difficulty: 4
files:
  - factory_dashboard/tickets.py
  - factory_dashboard/templates/tickets.html
  - factory_dashboard/templates/ticket.html
  - factory_dashboard/app.py
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_tickets.py
---

### Goal
`/tickets` lists tickets, and `/tickets/{id}` tells one ticket's whole story.

### Context
Follow the worked example: `factory_dashboard/overview.py`, `factory_dashboard/templates/overview.html` and `tests/factory_dashboard/test_overview.py`, with the fixture database in `tests/factory_dashboard/conftest.py` (extend it when your page needs more rows). The tables and columns are in `runner/metrics.py` (read it; it is the lead's file, so don't change it). Register your router in `factory_dashboard/app.py`. `write_fixture`'s numbers are pinned by `tests/factory_dashboard/test_queries.py` and `tests/factory_dashboard/test_overview.py`: put the rows your page needs in a function of your own (as `write_live` is), not among f1's or m4's tickets and jobs.
- Facts: `tickets` has no date column, so "newest first" means by milestone, newest first (its `started`), then by ticket id, highest first. The reviews written so far leave `findings.ticket_id` empty (f1-23 fills it): a ticket's findings are those with its `ticket_id`, and none is a normal state.
- **The list:** newest first, filterable by `milestone` and `state`; columns: id, milestone, kind (lead or developer), difficulty, state, attempts, merged by, lines changed.
- **The page,** in this order: breadcrumbs (project › milestone › ticket); the goal and Done when (from the ticket's `body`); `depends_on` as links; the files; the result (state, merged by, commit, lines changed); every job in order from the first attempt to the merge, each linking to `/jobs/{n}`; the findings on its code, with severity.
- A ticket id is text like `m4-06-me-wiring`; an unknown one answers 404.

**The dashboard is English-only: no gettext and no French.** Tests use `TestClient` and check the text the page shows, not only that it answers 200.

### Done when
- the list shows the fixture's tickets newest first, and `?state=escalated` only the escalated ones
- a ticket escalated then merged shows all its jobs in order, the escalation among them, and its merge commit
- its `depends_on` link to their own pages, and its findings show with severity
- an unknown ticket is a 404
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
