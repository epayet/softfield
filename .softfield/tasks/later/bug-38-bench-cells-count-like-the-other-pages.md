---
id: bug-38-bench-cells-count-like-the-other-pages
milestone: bugs
difficulty: 2
depends_on: []
area: factory
priority: 66
finding: f1-S166-1
files:
  - factory_dashboard/bench.py
tests:
  - tests/factory_dashboard/test_bench.py
---

### Goal
A Bench cell says the attempt number the bench passed at, and counts cached tokens as the other pages do.

### Context
Read `def _cell` and `def bench_grid` in `factory_dashboard/bench.py`, and `tests/factory_dashboard/test_bench.py`.
- Today "passed at attempt N" is the number of jobs in the cell's run, not the attempt the job ran (`jobs.attempt`), and its tokens add `tokens_in` and `tokens_out` but leave out `tokens_cached` (f1-C165-1).
- Select `attempt` and `tokens_cached` with the jobs, and use them.

### Done when
- a cell whose run recorded only attempt 3 (the first two in an earlier, voided run) reads "passed at attempt 3"
- a cell's tokens are in + cached + out
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
