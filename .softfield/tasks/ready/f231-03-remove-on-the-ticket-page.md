---
id: f231-03-remove-on-the-ticket-page
milestone: f231-there-are-many-bugs-in-the
difficulty: 3
depends_on: [f231-02-drop-a-set-aside-ticket]
files:
  - factory_dashboard/templates/ticket.html
  - factory_dashboard/tickets.py
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_tickets.py
---

### Goal
A set-aside ticket's page has Remove beside Queue it, asked once more before it is sent, and shows "Removing · on its way" the moment it is.

### Context
The picture to build: `.softfield/cards/f231-mockup/remove-a-set-aside-ticket.html` (Proposed). Read D3 in `.softfield/cards/f231-there-are-many-bugs-in-the.md`.
- `factory_dashboard/templates/ticket.html`: the `#aside` section. Queue it there is the worked example for a button that posts a request and turns the plate to "on its way"; `#remove-seed` in `factory_dashboard/templates/thread.html` is the example for the fold that asks once more.
- The request is `{"kind": "drop_ticket", "project": …, "subject": <the ticket id>}`, posted to `/requests` as Queue it posts.
- `factory_dashboard/tickets.py` sets `on_its_way` from an open `queue` request; find an open `drop_ticket` the same way, so a page loaded after the press shows "Removing · on its way · at the runner's next pick" and no buttons.
- The panel's first line becomes "This ticket won't run until you queue it, or you remove it."

### Done when
- a set-aside ticket's page has Queue it and Remove; Remove opens "Remove <short id>? It leaves the board and won't run." with a second Remove that posts `drop_ticket`
- with an open `drop_ticket` for the ticket, the page shows "Removing · on its way · at the runner's next pick" and neither button
- a ready, blocked or done ticket's page has no Remove
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
