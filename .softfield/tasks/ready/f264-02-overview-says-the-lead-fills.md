---
id: f264-02-overview-says-the-lead-fills
milestone: f264-the-factory-should-never-stay-idle
agent: developer
difficulty: 2
depends_on: [f264-01-lead-fills-the-gap, f264-03-no-park-at-the-five-hour-mark]
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/allowance_bar.html
  - factory_dashboard/templates/_partials/allowance.html
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview's allowance words say what Claude's pace and marks now do: lead tickets go last past them, the lead takes over when nothing else can run, and only the real limit makes them wait.

### Context
Read D4 in `.softfield/cards/f264-the-factory-should-never-stay-idle.md`, then in `factory_dashboard/overview.py`: `claude_pace` (it builds `WeekPace` and the held row's words from `allowance.lead_hold` and `allowance.lead_goes_at`) and the Claude rows' mark words (search "kept for you from here"); the pace plate in `factory_dashboard/templates/_partials/allowance_bar.html`; the switch label and the legend in `factory_dashboard/templates/_partials/allowance.html`. The tests are in `tests/factory_dashboard/test_overview.py` (search `Over pace`, `kept for you` and `use reserve`).
- f264-01 added `_held_at_the_limit` in `runner/loop.py`: a lead ticket waits for Claude only at 100% of a window or a rest after a refusal.
- Over the line, the plate reads "Over pace", then "developers first; the lead takes over when nothing else can run", then the small line "planning, reviews and the fast lane go on · today's pace N%". A held lead row says "goes when nothing else can".
- At 100% or a rest, the plate and rows say "lead tickets wait until" the reset or the rest's end, as `allowance.lead_goes_at` gives it.
- Both marks' words read "lead tickets go last from here". The switch label reads "keep board order" instead of "use reserve". In the legend, the mark's line reads "the mark: past it, lead tickets go after developers, planning and reviews; only 100% makes them wait", and the switch's line reads "keep board order: lead tickets keep the board's order past the mark; on lasts 24 hours, then turns itself off".
- The "Last hours" plate doesn't change. No element is added, moved or removed.

### Done when
- a week at 34% used with a pace line of 26% shows the new plate words and the row "goes when nothing else can"
- a week at 80% used shows the same words, not a wait; a week at 100% shows "lead tickets wait until" its reset
- both Claude rows' marks say "lead tickets go last from here", the switches say "keep board order", and the legend has the two new lines
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
