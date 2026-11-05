---
id: f219-03-review-waits-for-held-fixes
milestone: f219-lead-tickets-don-t-wait-on
agent: lead
difficulty: 4
depends_on: []
finding: f219-lead-tickets-don-t-wait-on-F1
files:
  - runner/milestone.py
tests:
  - tests/runner/test_milestone.py
---

### Goal
A review whose lead fix ticket is held by Claude's week waits for that fix, instead of paying for another round that reads no fixes.

### Context
Read the rounds loop of `review_milestone`, `run_milestone` and `PARKED` in `runner/milestone.py`, `due_reviews` and `_reviewed` there, and `_passed_over` and `_windows_now` in `runner/loop.py`. ADR 44 item 6 passes a lead ticket over with no park, so `work_queue(s, milestone=milestone)` returns with the fix still in `ready/`, and the next round starts at once. Three rounds of that end as "a finding came back a third time", with the fix never run.
- After `work_queue`, with no stop `reason`: when a lead ticket of this milestone is still in `ready/`, its dependencies done, and `loop._passed_over` holds it, the loop ends with no stop recorded. Its row is finished and `review_milestone` returns `PARKED`, whatever `park` is. `state.review_stop` stays unset, so `_reviewed` is false and `review_counts` keeps the rounds: `due_reviews` makes the review due again once the milestone's tickets are done, and it goes on from the next round.
- This doesn't lift the pace line for the fix: the fast lane and the lever do that, as for any lead ticket. A last round (`reason` set) stops as it does today.
- `runner/**` is protected: tests first.

### Done when
- with the week over its pace line and a round that writes a lead fix ticket, one review job runs, no stop is recorded and the fix stays in `ready/`
- once that ticket is in `done/`, `due_reviews` lists the milestone and the next review job is round 2
- on a fast lane card, or with the week's lever on, the fix runs and round 2 follows as today
- a developer's fix ticket runs and round 2 follows as today, over the line too
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
