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
Read the "Set aside" panel in `factory_dashboard/templates/tickets.html` (f4-18), `factory_dashboard/requests.py` and its worked example in `docs/agents/developer.md` ("a button that asks the runner"), and `tests/factory_dashboard/test_tickets.py` (`test_later_tickets_panel_shows_ticket_with_title_and_queue_command` and the `later_client` fixture it uses).
- The button posts a `queue` request whose subject is the ticket's id, the way the worked example does, and keeps the `uv run runner queue <id>` command beside it for the console.
- After the click, the button's place shows the request partial (`factory_dashboard/templates/_partials/request.html`: "Asked: the runner will do it.", then the runner's result, "queued <id>").
- What the owner asked for shows at once (the owner, 2026-10-07): the button is disabled as the request leaves, as the reserve lever's is in `factory_dashboard/templates/_partials/allowance.html` (`hx-on::before-request`).
- Each row needs its own place for the answer: the id of an element can't be shared between rows.

### Done when
- each set-aside ticket's row has a Queue button whose request (its `hx-vals`, parsed as JSON) is `queue` with that ticket's id as subject, asserted within the row
- with two set-aside tickets, each button's answer goes to a place in its own row
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 2671
gate_failures: []
tokens: 2677546
```
