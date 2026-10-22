---
id: f173-01-board-order-only
milestone: f173-dragging-a-card-on-the-board
agent: lead
difficulty: 5
depends_on: []
files:
  - runner/tasks.py
  - runner/requests.py
  - factory_dashboard/queries.py
  - docs/task-format.md
  - docs/agents/lead.md
tests:
  - tests/runner/test_tasks.py
  - tests/runner/test_requests.py
  - tests/factory_dashboard/test_queries.py
---

### Goal
The work runs in the board's order alone: a feature ticket runs in its card's place, and has no `priority:` of its own.

### Context
Read D1 to D5 in `.factory/cards/f173-dragging-a-card-on-the-board.md`, then `task_priority`, `run_order` and pre-flight in `runner/tasks.py`, `_ticket_priority`, `_board` and `_reorder` in `runner/requests.py`, and `ticket_priority`, `in_run_order` and `run_order` in `factory_dashboard/queries.py`.
- The case on 2026-10-22: F153's card was dragged first (priority 0), but its tickets said `priority: 100`, so `run_order` put them after every other card's tickets.
- A bug ticket's `priority:` stays: it is the bug's place on the board, written by a drag (`_reorder`). Only a feature ticket's goes.
- Strip `priority:` from every feature ticket in `.factory/tasks/ready/` and `.factory/tasks/later/` in the same change, or pre-flight refuses them; leave the ticket in flight (the runner's state names it) and `done/` as they are.
- `docs/agents/lead.md`'s "A ticket that repairs main goes first" rule keeps `depends_on` and drops `priority: 0` (D4).
- Grep the tests for `priority:` on a feature ticket and for `run_order`: a test that expected a ticket's number to beat another card's now expects the card's order, and one that writes a feature ticket's priority now expects a refusal.

### Done when
- a feature ticket on a card at 0 is picked before one on a card at 1, and inside one card tickets go by what they wait for, then id
- a bug ticket still runs by its own `priority:` among the cards, as today
- `softfield check-tickets` refuses a feature ticket with `priority:`, saying the board orders the work; a bug ticket with one passes
- the `priority` request on a feature ticket is refused with "a ticket runs in its card's place: move the card on the board"; on a bug it works as today
- the dashboard's `run_order` lists tickets in the order the runner picks them, for the cases above
- no feature ticket in ready/ or later/ has a `priority:`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
