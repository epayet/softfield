---
id: f222-03-pages-read-the-order
milestone: f222-when-milestones-plans-get-approved-do
agent: lead
difficulty: 5
depends_on: [f222-02-one-order-file]
files:
  - factory_dashboard/queries.py
  - factory_dashboard/board.py
  - factory_dashboard/overview.py
  - factory_dashboard/tickets.py
  - factory_dashboard/milestones.py
  - factory_dashboard/line.py
  - factory_dashboard/templates/_partials/queue.html
  - factory_dashboard/templates/ticket.html
  - factory_dashboard/templates/tickets.html
  - factory_dashboard/templates/milestone.html
  - factory_dashboard/templates/milestones.html
tests:
  - tests/factory_dashboard/test_queries.py
  - tests/factory_dashboard/test_board.py
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_tickets.py
  - tests/factory_dashboard/test_milestones.py
---

### Goal
The dashboard takes the queue's order from the database copy of the list, and no page shows a priority number.

### Context
The picture to build: `.softfield/cards/f222-mockup/no-priority.html`. Read `.softfield/cards/f222-when-milestones-plans-get-approved-do.md`: D5, D6.
- `factory_dashboard/queries.py`: `ticket_priority`, `in_run_order`. `factory_dashboard/board.py`: `_placed`, whose `Card.place` is already the place in a stage. `factory_dashboard/overview.py`, `factory_dashboard/tickets.py` and `factory_dashboard/milestones.py` join `m.priority`.
- The fast lane's rows in `factory_dashboard/templates/_partials/queue.html` already say the card as `t.card`: Next in line does the same.
- The board's order stays as `runner/requests.py` reads it, so a card's page and the runner agree.

### Done when
- the board, Next in line, Tickets and Milestones sort by `queries.board_places`, unlisted after listed, the same order the runner's dry run gives on the same data
- Next in line says the ticket's card (`F171`) or `bug` in place of "priority N", and "early: … waits for it" stays
- a card in Seed, Sprouting or Planted says "Place: #N in Planted" with its stage's name; a ripe or harvested one has no such row
- a ticket in ready says "In line with F169, #1 in Planted" above its goal, or its own place if it's a bug; a done, blocked or set-aside ticket has no such line
- the place on those pages follows a drag without anything being stored on the card or ticket
- the Priority column is gone from Milestones and from Set aside on Tickets
- a set-aside ticket's page says "Queued, it goes to the end of the line; move it on the board once it is there."
- a page test finds no "priority" and no `P<number>` on `/`, `/tickets`, a set-aside ticket's page, a queued ticket's page, `/milestones` and a card's page
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
