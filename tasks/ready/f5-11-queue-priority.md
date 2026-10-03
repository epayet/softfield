---
id: f5-11-queue-priority
milestone: f5-board
depends_on: [f5-07-replan, f4-10-queue-live, f4-30-queue-live-tests]
difficulty: 2
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/live.html
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview's queue follows the runner's new order (priority first) and shows each ticket's priority.

### Context
Read `factory_dashboard/overview.py` (`queue`, as f4-08 and f4-10 left it), `runner/tasks.py` (`pick_next`'s order since f5-06), `runner/metrics.py` (where a ticket's and a milestone's priority are stored) and `tests/factory_dashboard/test_overview.py`.
- A ticket's priority is its own, else its milestone's, else 100, as in `pick_next`. Ready-now tickets still come before waiting ones. Within each group sort by `(priority, milestone order, id)`.
- Add a "Priority" column.

### Done when
- a ticket in a priority-1 milestone is listed before one in an earlier milestone with priority 5
- each row shows its priority, asserted within the row
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
