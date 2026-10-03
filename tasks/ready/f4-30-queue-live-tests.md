---
id: f4-30-queue-live-tests
milestone: f4-always-on
depends_on: []
difficulty: 2
finding: f4-cp8
files:
  - tests/factory_dashboard/test_overview.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
Tests prove the Queue is part of the polled `/live` partial and sits beside Running now.

### Context
f4-10-queue-live moved the Queue into `factory_dashboard/templates/_partials/live.html` and its data into `_live_context`, but changed no test. Read `tasks/done/f4-10-queue-live.md` and the live and queue tests in `tests/factory_dashboard/test_overview.py` (`queue_rows`, `queue_client`, the tests using `serve`, `section`).
- Facts: every existing queue test reads `/`, so none would fail if the Queue left `/live`. The ids test at line 32 checks order on `/` only.

### Done when
- a test: `/live` returns the Queue section with the same rows, in the same order, as `/` (content of the rows, not presence)
- a test: a ticket added to the database between two `/live` calls appears in the second
- a test: on `/`, `#running` and `#queue` are inside one `.row`
- the listed `tests:` pass, and each new test fails if the Queue is taken out of `_partials/live.html` (check by hand)
- all gates pass (see `docs/workflow.md`)
