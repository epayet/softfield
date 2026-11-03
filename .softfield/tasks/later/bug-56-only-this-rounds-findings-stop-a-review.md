---
id: bug-56-only-this-rounds-findings-stop-a-review
milestone: bugs
difficulty: 2
depends_on: []
agent: lead
area: factory
finding: f149-is-docs-backlog-md-still-used-F7
files:
  - runner/review.py
tests:
  - tests/runner/test_review.py
---

### Goal
A review stops as "a finding came back a third time" only when one of its own findings did, not because of any finding in any other milestone.

### Context
`stop_reason` in `runner/review.py` tests every value in `seen`, which is `state.finding_seen`: all milestones' findings, kept for good. `m3-F7` has stood at 3 since M3, so any later review with one open finding stops after its first round, its fixes never re-reviewed. No other saved count reaches 3, yet 11 milestones have this stop reason, F2 and F159 among them.
Fix: test only this round's findings that hold the review (`Finding.holds_review`), by their count in `seen`. The signature stays. Leave the saved `m3-F7` count alone: it stops mattering.
`test_recurrence` in `tests/runner/test_review.py` is the worked example.

### Done when
- with `seen` holding another milestone's finding at 3, a round with an open finding of its own, below 3, gets `None`
- a round whose own open finding is at 3 still stops as "a finding came back a third time"
- a finding at 3 that this round marks resolved, or sets aside with `later` or `report`, doesn't stop it for that reason
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
