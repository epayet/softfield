---
id: f5-09-queue-button
milestone: f5-board
depends_on: [f5-07-replan, f4-18-later-list]
difficulty: 3
files:
  - factory_dashboard/tickets.py
  - factory_dashboard/templates/tickets.html
tests:
  - tests/factory_dashboard/test_tickets.py
---

### Goal
Each set-aside ticket on the Tickets page has a "Queue" button that asks the runner to move it back to the queue.

### Context
Read the "Set aside" panel in `factory_dashboard/templates/tickets.html` (f4-18), `factory_dashboard/requests.py` and its worked example in `docs/agents/developer.md` ("a button that asks the runner"), and `tests/factory_dashboard/test_tickets.py`.
- The button posts a `queue` request with the ticket's id, the way the worked example does, and keeps the `uv run runner queue <id>` command beside it for the console.

### Done when
- each set-aside ticket's row has a Queue button whose request names that ticket, asserted within the row
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
