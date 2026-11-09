---
id: f232-01-plants-wait-two-minutes
milestone: f232-i-can-t-edit-a-seed
agent: lead
difficulty: 2
depends_on: []
files:
  - runner/requests.py
tests:
  - tests/runner/test_requests.py
---

### Goal
The runner leaves a plant from the Plant box open for its first 2 minutes, so the owner can still edit or cancel it from Coming seeds when the factory is idle or paused.

### Context
Read "Why it happens" and D1 to D4 in `.softfield/cards/f232-i-can-t-edit-a-seed.md`, then `apply_requests`, `_waits` and `_change` (the function that applies a `change` to a plant or message) in `runner/requests.py`.
- Add `PLANT_HOLD = timedelta(minutes=2)` beside `PLANT` in `runner/requests.py`; the dashboard imports it in f232-02.
- In the second loop of `apply_requests`, a row of kind `PLANT` with no `subject` whose `created` is less than `PLANT_HOLD` before `now` is skipped: left open, not finished, and no line added for it (D4).
- Leave alone: a plant with a `subject` (a seed from a review idea), every other kind, and the changes loop that runs first: a cancel or an edit of a held plant applies at once.

### Done when
- a plant created 30 seconds before `now` stays open after `apply_requests`, and adds no line
- a plant created 3 minutes before `now` is planted as today
- a cancel of a plant created 30 seconds before `now` finishes the plant as "cancelled by you"
- an edit of a held plant changes its words, and they are the ones planted once the 2 minutes are over
- a plant with a `subject` is applied at once, as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
