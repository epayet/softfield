---
id: bug-20-review-bench-guards-the-main-checkout
milestone: bugs
difficulty: 4
depends_on: []
agent: lead
area: factory
priority: 46
finding: f7-factory-fixes-F4
files:
  - runner/bench.py
tests:
  - tests/runner/test_bench.py
---

### Goal
`softfield bench --review` notices when a reviewer read or touched the main checkout instead of its copy, as a ticket bench does.

### Context
Read `def bench_one` (its `main_status` check around the attempt) and `def _review` in `runner/bench.py`, and their tests in `tests/runner/test_bench.py`. `runner/**` is protected: tests first.
- A review replay is read-only, but before f7-06's `PWD` fix an OpenCode reviewer read the main checkout, not the copy at the checkpoint, and nothing caught it. Compare `main_status` around `_review` as `bench_one` does, and record a changed main as the bench's outcome.
- Add one sentence to the review bench's docstring: OpenCode review-bench scores from before 2026-10-05 may have reviewed the wrong tree.

### Done when
- a review replay that changes the main checkout is recorded as such, and its score isn't counted
- one that leaves main alone scores as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
