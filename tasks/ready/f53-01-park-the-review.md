---
id: f53-01-park-the-review
milestone: f53-why-is-milestone-diff-review-waiting
difficulty: 5
depends_on: []
agent: lead
files:
  - runner/milestone.py
  - runner/loop.py
  - runner/cli.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_milestone.py
---

### Goal
A review Claude can't take now parks its queue row until the hold ends, and the line goes on with other work, instead of the runner sleeping.

### Context
Read `docs/milestones/f53-why-is-milestone-diff-review-waiting.md` (D1), `review_milestone` and `run_due_review` in `runner/milestone.py`, `_review` in `runner/cli.py` (it prints a verdict for every stop), and in `runner/loop.py` `wait_for_room`, `claude_hold`, `_park_support` (the checkpoint's example to follow), `park_row` and `_queue_due_review`. The tests to replace: `test_a_review_at_80_percent_waits_for_the_reset_with_the_switch_off` and `test_the_5_hour_switch_turned_on_during_the_reviews_wait_ends_it` in `tests/runner/test_loop.py`.
- Check the hold at the top of each round, before `_e2e`.
- A parked review is not a stop: no `review_stop`, no verdict, no `finish_row`; its rounds in `state.review_counts` stay, so it resumes at the next round.
- **On 2026-10-08 the runner slept 3 h 30 in `wait_for_room` with about 40 developer tickets ready: the test must show a developer ticket picked while the review is parked.**

### Done when
- Claude at 80% of its 5-hour window, switch off: the review's row gets `not_before` at the hold's end, the console line says the review waits for Claude and when it resumes, e2e doesn't run, and the next pick is a ready developer ticket
- after the reset the review is picked before any ticket and starts at the round it was at (a parked round 2 doesn't redo round 1)
- the 5-hour switch turned on while it is parked: the next pick is the review
- a review parked between rounds, with another milestone's ticket merged meanwhile: the next round's prompt names only its own milestone's fix merges since the last round, not the other one
- `runner milestone <key>` (no queue to go back to) keeps waiting as today
- `wait_for_room` has no caller left in `runner run`'s path
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
