---
id: bug-12-clear-out-marked-once-it-ran
milestone: bugs
difficulty: 2
depends_on: []
agent: lead
area: factory
priority: 36
finding: f55-dismiss-all-conversations-where-the-related-F2
files:
  - runner/requests.py
  - runner/metrics.py
tests:
  - tests/runner/test_requests.py
---

### Goal
F55's one-time clear-out is marked done only after it has run, so a failure leaves it to run again.

### Context
Read `def apply_requests` and `def _clear_out` in `runner/requests.py`, and `def once` in `runner/metrics.py`. `runner/**` is protected: tests first.
- `apply_requests` calls `metrics.once(conn, CLEAR_OUT, …)` (which marks it done, autocommit) before `_clear_out` runs: if `_clear_out` raised, the step would be lost for good and that start's requests left unapplied.
- Read whether it is done first, run `_clear_out`, then mark it done.

### Done when
- `_clear_out` raising leaves the clear-out unmarked, and the next `apply_requests` runs it again
- after a clean run it is marked, and runs no more
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
