---
id: f191-04-limit-in-a-round-parks-the-review
milestone: f191-why-is-the-lead-reviewing-something
agent: lead
difficulty: 6
depends_on: []
files:
  - runner/loop.py
  - runner/milestone.py
  - tests/runner/test_milestone.py
tests:
  - tests/runner/test_milestone.py
---

### Goal
Under `softfield run`, a Claude limit that lands inside a review's round parks the review, so developer tickets run until the reset, instead of stopping every project.

### Context
Read "What happened (lead, 2026-11-02)" and D4 in `.softfield/cards/f191-why-is-the-lead-reviewing-something.md`.
- `runner/milestone.py`: `review_milestone` checks `park_review` before a round, then calls `call_claude` with no `park`; the early return there is the shape to follow for PARKED.
- `runner/loop.py`: `call_claude` (with `park`, a certain refusal or an expired login calls `_park`, which raises `Parked`; without it, both wait in place), `_park` (it parks a row only for `QUEUED` roles, and `REVIEW` isn't one: `state.parked` is for tickets), `park_row`, `park_review`.
- The session is kept in `state.interrupted` under `job_key(job.role, subject)`; the round's number, so its subject, is the same on the way back.
- Tests to follow in `tests/runner/test_milestone.py`: `test_a_review_parked_between_rounds_resumes_at_its_round_on_its_own_fixes` for the park through `softfield run`, `test_a_named_milestones_review_still_waits_for_claude` for what must not change.
- On 2026-10-30 at 05:54 this stopped the factory for 28 hours, with the wait set for 2 November.

### Done when
- A review under `softfield run` refused by a certain limit mid-round parks its row until the reset, `review_milestone` returns PARKED and the run goes on: a developer ticket runs next.
- After the reset the same round goes on with its session resumed; no round is counted twice and no stop was recorded meanwhile.
- An expired login during a round parks the review the same way, and it goes on once the login works.
- A refusal with no time given parks for the same minimum `_park` gives any job.
- `state.parked` holds no entry for the review.
- `runner milestone` still waits for the reset in place.

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
