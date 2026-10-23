---
id: bug-08-seed-refuses-a-rejected-proposal
milestone: bugs
difficulty: 3
depends_on: []
agent: lead
area: factory
priority: 32
finding: f31-F7
files:
  - runner/requests.py
tests:
  - tests/runner/test_requests.py
---

### Goal
A seed the owner rejected can't be planted, even from a page left open.

### Context
Read `def _seed` and `def _approve_plan` in `runner/requests.py`, and `def proposal_state` in `runner/planner.py`. `runner/**` is protected: tests first.
- `_seed` plants an approved seed without reading its state. `_approve_plan` already refuses a rejected plan's merge: do the same here, with the same kind of reason.

### Done when
- approving a seed whose proposal the owner rejected plants nothing, and the request's result says it was rejected
- an open seed still plants as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
