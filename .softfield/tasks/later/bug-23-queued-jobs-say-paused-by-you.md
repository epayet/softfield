---
id: bug-23-queued-jobs-say-paused-by-you
milestone: bugs
difficulty: 2
depends_on: []
area: factory
priority: 50
finding: f8-one-queue-F5
files:
  - factory_dashboard/overview.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
While the owner pauses the factory, the Overview's queued jobs say "paused by you", as the top bar does.

### Context
Read `def queued_jobs` in `factory_dashboard/overview.py`: it calls `dispatch.plan` without `paused`. `plan` in `runner/dispatch.py` takes `paused`, and `def paused_since` in `factory_dashboard/queries.py` says whether the owner paused. Follow the `queued_jobs` tests in `tests/factory_dashboard/test_overview.py`.
- Pass `paused=queries.paused_since(conn) is not None`.

### Done when
- with the factory paused, a queued checkpoint's row in Next in line reads "paused by you"
- a queued planner job still reads as today (planning goes on through a pause)
- not paused, every row reads as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
