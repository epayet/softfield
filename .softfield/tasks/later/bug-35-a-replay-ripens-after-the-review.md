---
id: bug-35-a-replay-ripens-after-the-review
milestone: bugs
difficulty: 4
depends_on: []
area: factory
priority: 63
finding: f50-the-data-safety-review-it-asks-F3
files:
  - factory_dashboard/line.py
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
In the line's replay, a card turns ripe only from the end of its first review job, not as soon as its tickets are done.

### Context
Read `def _field` and `def live_line` in `factory_dashboard/line.py`, and the replay tests in `tests/factory_dashboard/test_line.py`.
- Today `_field` reads "reviewed" from `milestones.signoff` whatever the moment, so a replay shows a card ripe before its review existed.
- In a replay at time T, a card is reviewed only if a job with `role = 'review'` for that milestone ended before T. Live (no replay) stays as today.

### Done when
- a replay at a moment between the last ticket's merge and the review job's end: the card isn't ripe
- a replay after the review job ended: it is ripe
- the live line is unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
