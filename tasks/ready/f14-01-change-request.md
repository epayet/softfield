---
id: f14-01-change-request
milestone: f14-coming-planted-ideas-not-clickable
difficulty: 4
depends_on: []
agent: lead
files:
  - runner/requests.py
  - runner/metrics.py
  - factory_dashboard/requests.py
tests:
  - tests/runner/test_requests.py
  - tests/factory_dashboard/test_requests.py
---

### Goal
A new request kind, `change`, edits or cancels a plant or a message the runner hasn't taken yet; the runner applies every change before the other requests of the same pick.

### Context
Read `docs/milestones/f14-coming-planted-ideas-not-clickable.md` (D1 to D4), and in `runner/requests.py`: `apply_requests` (the loop over open requests), `_apply`, `_plant` and `_plan_message` (the values a change replaces), `_waits` and `_COMMITS`. `runner/metrics.py` has `finish_request` (once only) and `find_request`.
- Add `CHANGE` beside the other kinds and to `KINDS` in `factory_dashboard/requests.py`; it is not in `_COMMITS` (it never waits for main).
- The target's value is replaced with an `UPDATE owner_requests SET value = ? WHERE id = ? AND done IS NULL`, a new helper in `runner/metrics.py` beside `finish_request`.
- **Changes go first in the pick, and the other requests are read after them, so a cancelled target is never applied.**

### Done when
- a `change` cancelling an open plant finishes the plant as "cancelled by you" and itself as "cancelled": no card, no commit, no planner row
- a `change` with a new title and thoughts plants the idea with the new words in the same pick
- a `change` on an open `plan_message` edits or cancels it the same way (a cancelled one adds no thread message and no planner row)
- a `change` whose target is done finishes as "too late: already planted" (a plant) or "too late: already sent" (a message), and changes nothing
- a `change` naming no request, another kind (a sign-off, a pause), or a bad value finishes with why, and changes nothing
- two changes on the same target apply oldest first: the last edit wins; an edit after a cancel is too late
- a plant waiting for main can still be cancelled while the repo is on another branch
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
