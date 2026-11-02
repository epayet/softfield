---
id: f179-04-weekly-report-lead-split
milestone: f179-how-is-sonnet-doing-as-an
difficulty: 3
depends_on: [f179-01-lead-split, f59-03-weekly-report-job]
agent: lead
files:
  - factory_dashboard/reports.py
  - runner/prompts.py
  - tests/factory_dashboard/test_reports.py
  - tests/runner/test_prompts.py
tests:
  - tests/factory_dashboard/test_reports.py
  - tests/runner/test_prompts.py
---

### Goal
The weekly report's brief carries the week's lead tickets by model, so the lead's read says how Sonnet did and what it saved.

### Context
Read `.factory/cards/f179-how-is-sonnet-doing-as-an.md`, D7, and `.factory/cards/f59-periodic-review-of-the-factory.md`, D3 and D6. Write the tests first.
- `class Week` in `factory_dashboard/reports.py` gains `lead`, from `lead_split` in `factory_dashboard/queries.py` (f179-01) with the week's start and end, for each project of the scope.
- The brief is f59-03's `REPORT` in `runner/prompts.py`, and the text it builds from `week`: add the split there, one line per agent and band.

### Done when
- a week with a Sonnet lead ticket has it in `Week.lead`, and the week before has its own
- the brief's text for that week names Sonnet's tickets, its dollars, Opus's would-have and the saving
- a week with no lead ticket says nothing about the split
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
