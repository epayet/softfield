---
id: f191-05-fix-ticket-holds-only-its-review
milestone: f191-why-is-the-lead-reviewing-something
agent: lead
difficulty: 5
depends_on: [f191-04-limit-in-a-round-parks-the-review]
files:
  - runner/loop.py
  - runner/milestone.py
  - tests/runner/test_milestone.py
tests:
  - tests/runner/test_milestone.py
---

### Goal
Under `softfield run`, the queue a review runs after a round never sleeps for a Claude limit: a job Claude can't take holds that review only, and the factory goes on.

### Context
Read cause 4 and D5 in `.softfield/cards/f191-why-is-the-lead-reviewing-something.md`.
- `runner/milestone.py`: in `review_milestone`, `work_queue(s, milestone=milestone)` runs after a round, then a stop `reason` ends the loop, then the exit for a fix the week holds (`_fix_held_by_the_week`, F219 D3: the row is finished, PARKED returns, no stop is recorded). Extend that exit, don't build a second one. `due_reviews` and `_reviewed` say why no stop may be recorded.
- `runner/loop.py`: `work_queue` with no job calls `_wait_for_reset`, which sleeps to the first reset among parked tickets and every parked row it is given, a planner's or a checkpoint's as well as a fix ticket's. `wait=False` skips that sleep, but also `_hold_for_the_owner`, so with it alone the next round would start under a pause: the pause must still hold.
- Tests to follow in `tests/runner/test_milestone.py`: `test_a_review_waits_for_a_lead_fix_the_week_holds` for the exit, `test_a_review_parked_between_rounds_resumes_at_its_round_on_its_own_fixes` for the way back.

### Done when
- A round files a lead fix ticket and a limit parks it: the review returns PARKED with no stop in `state.review_stop`, its row is done, and a developer ticket of another card runs next.
- Once the fix ticket is done, the review comes due again and goes on from the next round.
- The same on a last round (a stop `reason`): the stop is recorded as today, the run goes on and the fix runs in the main queue after the reset.
- A round with no fix ticket, while a planner's or a checkpoint's row is parked until a reset: nothing sleeps; the next round parks through `park_review` if Claude is limited.
- A fix ticket that runs and merges goes on as today, and the review ends on its stop.
- The owner's pause during the inner queue holds it, as today: no round starts under a pause.
- `runner milestone` still waits for the reset in place.
