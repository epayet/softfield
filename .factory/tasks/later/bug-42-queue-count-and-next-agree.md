---
id: bug-42-queue-count-and-next-agree
milestone: bugs
difficulty: 3
depends_on: []
area: factory
priority: 70
finding: f3-review
files:
  - factory_dashboard/overview.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview's Queue panel counts the same tickets its "Next in line" lists, in one order.

### Context
Read `factory_dashboard/templates/_partials/queue.html`, `def queue` in `factory_dashboard/overview.py` (ready-now first, by milestone: the count) and `def run_order` in `factory_dashboard/queries.py` (`pick_next`'s order: Next in line), and `def _live_context` in `factory_dashboard/overview.py`, which hands both to the panel.
- Today the two can disagree: one panel, two orders. The runner's order is `run_order`'s, so the count follows it: the number of tickets `run_order` lists.

### Done when
- with a ticket waiting on a dependency, the count and the rows listed agree
- the count says "N tickets waiting" with N the number of tickets in `run_order`, batches counted by their tickets
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
