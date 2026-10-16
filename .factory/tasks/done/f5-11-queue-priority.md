---
id: f5-11-queue-priority
milestone: f5-board
depends_on: [f5-07-replan, f5-09-queue-button, f9-05-later-kind-column]
difficulty: 2
files:
  - factory_dashboard/tickets.py
  - factory_dashboard/templates/tickets.html
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_tickets.py
---

### Goal
The Tickets page's Set aside table lists the set-aside tickets by priority, lower first, and shows each one's priority.

### Context
**The Overview's queue is done** (f6-18): `queue` in `factory_dashboard/overview.py` follows the runner's order, and Next in line shows each ticket's priority. What is left is the backlog: the set-aside tickets (the bug tickets of `.factory/tasks/later/`) are listed by id, with no priority.
Read `list_later_tickets` in `factory_dashboard/tickets.py`, the "Set aside" panel in `factory_dashboard/templates/tickets.html`, `ticket_priority` in `factory_dashboard/queries.py`, and `tests/factory_dashboard/test_tickets.py` (the `later_client` fixture and the tests that use it).
- A ticket's priority is its own `priority:` (in `tickets.body`, its file's text), else 50 for a bug ticket, else its milestone's (`milestones.priority`), else 100. `ticket_priority` reads it so, from the ticket's body, its milestone's key and its milestone's priority.
- The order: priority, then the ticket's id.
- Add a "Priority" column. The other columns stay as f5-09 and f9-05 left them.
- Put your fixture rows in your own function in `tests/factory_dashboard/conftest.py` (Edit it, anchored on its last lines; `write_later` is the example).

### Done when
- a set-aside ticket whose text says `priority: 5` is listed before one with an earlier id and no priority of its own
- a bug ticket with no `priority:` shows 50, and a milestone's ticket with none shows its milestone's priority, each asserted within its row
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 4464
gate_failures: []
tokens: 2398255
```
