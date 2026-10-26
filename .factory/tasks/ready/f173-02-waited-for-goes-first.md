---
id: f173-02-waited-for-goes-first
milestone: f173-dragging-a-card-on-the-board
agent: lead
difficulty: 5
depends_on: []
files:
  - runner/tasks.py
  - runner/loop.py
  - runner/dispatch.py
  - factory_dashboard/queries.py
  - factory_dashboard/templates/_partials/queue.html
tests:
  - tests/runner/test_tasks.py
  - tests/runner/test_loop.py
  - tests/factory_dashboard/test_queries.py
---

### Goal
A ticket that a higher ticket waits for runs in that ticket's place in the line, so the top card's work is done first, with the dashboard saying why it runs early.

### Context
Read D6 and D7 in `.factory/cards/f173-dragging-a-card-on-the-board.md`, then `task_priority`, `run_order`, `pick_next` and `blocked_ids` in `runner/tasks.py`, `_next_task`, `_dispatch_ticket` and `reserve_cards` in `runner/loop.py` (`reserve_cards` already walks what a ticket waits for: follow it), the dry run's ticket list in `runner/loop.py` (the function that sorts `ready` by `run_order` and builds `dispatch.Ticket`s), `Ticket` and `_ticket_line` in `runner/dispatch.py`, `Upcoming`, `in_run_order` and `run_order` in `factory_dashboard/queries.py`, and `factory_dashboard/templates/_partials/queue.html`.
- The case on 2026-10-26: F15 at place 4 has f15-06-card-actions waiting on f73-02-set-aside-button, which waits on f73-01-set-aside-list and f42-01-review-page-room; f73-01 waits on f26-02-group-counts, which waits on f63-01-desk-order (F73 and F42 at 6, F26 at 7, F63 at 14). F132's tickets at 5 all ran before them.
- `pulls` is computed once from the whole ready list and passed to every `pick_next` in `_next_task`, even those that pick from a subset (the parked ones, the developers'): a developer ticket that a lead ticket waits for keeps its pull.
- `task_priority` and `_reorder` in `runner/requests.py` stay as they are: the board's drag writes only a card's or a bug's own place.
- Ties: a pulled ticket sorts by its waiter's key (priority, milestone order, id), then its own id, so a chain pulled by F15 goes before F171 at the same place when F15 comes first in milestone order.

### Done when
- with the case above in a test, the runner picks f63-01-desk-order and f42-01-review-page-room before any ticket of a card at 5, and f15-06-card-actions as soon as its chain is merged
- a ticket that nothing ready waits for runs in its own card's place, as today; a done or set-aside waiter pulls nothing; a cycle in `depends_on` doesn't hang
- a developer ticket a lead ticket waits for is pulled in `_next_task`'s developer pick too
- the dashboard's `run_order` lists the same order, and Next in line reads "early: <waiter id> waits for it" for a pulled ticket; the dry run's reason names it too
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
