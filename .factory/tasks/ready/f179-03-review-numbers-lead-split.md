---
id: f179-03-review-numbers-lead-split
milestone: f179-how-is-sonnet-doing-as-an
difficulty: 3
depends_on: [f179-01-lead-split]
agent: lead
files:
  - runner/report.py
  - tests/runner/test_report.py
tests:
  - tests/runner/test_report.py
---

### Goal
A milestone review's Numbers show "Lead tickets by model": that milestone's split and the project's saving to date.

### Context
Read `.factory/cards/f179-how-is-sonnet-doing-as-an.md`, D6. Write the test first.
- `def milestone_report` in `runner/report.py`: the new section goes after "### Savings from delegating", built like its table (`_usd`, `_pass_rate`).
- The rows: `lead_split` in `factory_dashboard/queries.py` (f179-01), with the milestone's `key`, then without it for the **All milestones** line.

### Done when
- a milestone with a Sonnet lead ticket shows a row per agent and band: merged, first time, step-ups, dollars, would-have, saved, should-fix and blocking
- the **All milestones** line gives the project's saving to date
- a milestone with no lead ticket shows "No lead tickets." under the heading
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
