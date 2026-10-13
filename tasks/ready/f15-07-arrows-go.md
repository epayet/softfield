---
id: f15-07-arrows-go
milestone: f15-reprioritising-tickets
difficulty: 3
depends_on: [f15-05-replan]
agent: lead
commands: [rm factory_dashboard/templates/_partials/move.html]
files:
  - factory_dashboard/templates/_partials/queue.html
  - factory_dashboard/templates/milestones.html
  - factory_dashboard/templates/_partials/move.html
  - factory_dashboard/templates/board.html
tests:
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_milestones.py
---

### Goal
The ↑ and ↓ arrows leave Next in line and the Milestones page: the board is the one place the owner reorders.

### Context
Read `docs/milestones/f15-reprioritising-tickets.md` (D8). The arrows are `factory_dashboard/templates/_partials/move.html`, included by `factory_dashboard/templates/_partials/queue.html` (Next in line) and `factory_dashboard/templates/milestones.html` (each card's row); their tests are in `tests/factory_dashboard/test_overview.py` and `tests/factory_dashboard/test_milestones.py`.
- The owner (2026-10-13): "I'm actually not a fan of the arrows in overview and plan to kill them."
- Remove the two includes and the partial (`rm`, in `commands:`), and whatever in the two pages only served the arrows (the `#move-…` targets, their script or CSS if nothing else uses it). Each row still shows its priority as a number.
- Next in line gets one link, "Reorder on the board ›", to `/board`; the board's foot no longer says the Milestones list "keeps each card's ↑ and ↓".
- The `priority` request and `runner`'s side of it stay: a ticket's own priority is still set from the console and by the lead.
- A lead ticket because a developer's tools can't remove a file.

### Done when
- Next in line and the Milestones page hold no `move-button` and post no `priority` request
- each row still shows its priority
- Next in line links to the board
- `factory_dashboard/templates/_partials/move.html` is gone and nothing includes it
- the tests that pressed the arrows are replaced by tests of the above
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
