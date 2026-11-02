---
id: bug-09-a-reject-reads-the-subject-once
milestone: bugs
difficulty: 3
depends_on: []
agent: lead
area: factory
priority: 33
finding: f31-F6
files:
  - runner/requests.py
tests:
  - tests/runner/test_requests.py
---

### Goal
A reject posted with a card's full key settles the proposal as one posted with its short key does.

### Context
Read `def _reject` and `def _settles` in `runner/requests.py`, and `def thread_key` and `def proposal_state` in `runner/planner.py`. `runner/**` is protected: tests first.
- `_reject` finds its thread through `thread_key`, but `_settles` and `proposal_state` compare the subject as posted. A reject posted as `f7-one-queue/plan` (the dashboard sends `f7/plan`) removes the branch and leaves the proposal showing open.
- Normalise the subject once, at the top of `_reject` and in `_settles`.

### Done when
- a reject posted as `f7-one-queue/plan` removes the branch and the proposal reads rejected
- one posted as `f7/plan` works as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
