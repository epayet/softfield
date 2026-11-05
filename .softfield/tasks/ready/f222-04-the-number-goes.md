---
id: f222-04-the-number-goes
milestone: f222-when-milestones-plans-get-approved-do
agent: lead
difficulty: 5
depends_on: [f222-01-approved-goes-last, f222-03-pages-read-the-order]
files:
  - runner/tasks.py
  - runner/milestone.py
  - runner/planner.py
  - runner/dispatch.py
  - runner/loop.py
  - runner/requests.py
  - runner/metrics.py
  - runner/prompts.py
  - runner/instructions/task-format.md
  - runner/instructions/lead.md
  - runner/instructions/author/owner.md
tests:
  - tests/runner/test_tasks.py
  - tests/runner/test_milestone.py
  - tests/runner/test_planner.py
  - tests/runner/test_dispatch.py
  - tests/runner/test_requests.py
  - tests/runner/test_metrics.py
---

### Goal
The priority number is gone: from the code, the open cards and bugs, the database and the instructions, so the list is the only order left.

### Context
Read `.softfield/cards/f222-when-milestones-plans-get-approved-do.md`: D7, D8, and `.softfield/adr/45-one-queue-order-no-priority.md` items 5 and 6.
- `runner/requests.py`: `_numbers`, `_renumbered`, `_card_with`, `_ticket_with`, `_card_priority`, `_ticket_priority`, `_priority` and the `PRIORITY` request go. A request of that kind still waiting is answered as refused, saying the board orders the work.
- `runner/tasks.py`: `_priority`, `Task.priority` and `BUG_PRIORITY`. `runner/milestone.py`: `DEFAULT_PRIORITY` and `Card.priority`. `runner/planner.py`: a planted card's header, `ReadyTicket` and `where_it_stands`. `runner/dispatch.py`: `Ticket.priority`.
- `runner/metrics.py`: `projects.priority` stays; it is the Projects page's own order. Drop `milestones.priority` in a new last step of `MIGRATIONS`.
- `runner/instructions/task-format.md` keeps a single line: the order is in the list. `runner/instructions/author/owner.md`'s rule "The board's order is the only order" says the same. The header of the docs in `.softfield/cards/` of done cards isn't touched.
- Don't edit the open cards and bugs by hand: there are about a hundred here, and other projects have their own. The runner does it once per project, in the step f222-02 added to make the list: when an open card's header or a bug in `.softfield/tasks/ready/` or `.softfield/tasks/later/` still has a number, it removes that and nothing else, in one commit. Pre-flight reads a bug's `priority:` only after this step has run, so a project not yet moved isn't refused.

### Done when
- no code in `runner/` or `factory_dashboard/` orders work by a card's or a bug's priority, and a doc of a done card still saying it reads as before
- the step above removes the numbers in one commit, changes nothing else in those files, and on its second run commits nothing
- pre-flight refuses `priority:` on any ticket, feature or bug, saying the board orders the work
- a planted card's header has no Priority
- `softfield run --dry-run` says "place N", and a planner's "Where the work stands" lists cards in order, without numbers
- the order the dry run gives is the same before and after this ticket
- `softfield check-tickets` passes
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
