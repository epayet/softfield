---
id: f9-29-week-pace
milestone: f9-line-polish
depends_on: [f9-28-allowance-live]
agent: lead
difficulty: 3
files:
  - runner/allowance.py
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/allowance.html
  - factory_dashboard/templates/_partials/queue.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/runner/test_allowance.py
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview shows when Claude's week pacing holds lead tickets back: the week meter carries today's pace line and says in words whether the factory is on pace or over it, and a held lead ticket's row in Next in line says so, with until when.

### Context
Read `_check` in `runner/allowance.py` (a fixed window's pace line: `share * min(1, elapsed + MARGIN)`, ADR 25), `agent_allowances` and `WindowAllowance` in `factory_dashboard/overview.py` (the week's `mark` is the reserve, not the pace), the allowance partial f9-28 made, and the ticket rows of `factory_dashboard/templates/_partials/queue.html`.
- The picture to build: `.softfield/cards/f9-mockup/week-pace.html` (Proposed). The pace line is a dashed hazard post with a small flag; the stretch used beyond it is hazard-striped; under the meter, a plate with a short hazard-stripe edge (like `.reserve-bay`) reads "Over pace: lead tickets wait until about <day HH:MM> · developers go on". On pace, there is only the post and "on pace" on the meter's second line, no stripes and no plate. Two new legend lines say what the post and the stripes mean. New CSS uses the tokens only.
- The owner (2026-10-07): "i understand there is a pacing through the week logic for claude lead tickets, that's not quite visible on the dashboard whenever we hit that"; again on F116 (2026-10-27): "I want to be able to visualise when the claude pacing happens somehow". Today only the Tickets page's row reason says "over its pace line of N%".
- Make the pace line a public, pure function in `runner/allowance.py`, used by `_check` too, so the dashboard and the runner can't disagree; with it, a pure function for when the line next reaches a given use (the "until about" time). In the sweep at the week's end, or with the week's reserve lever on, there is no pace line: draw neither post nor plate.
- A lead ticket's row in Next in line adds "held by Claude's week pace until about <day HH:MM>" while the factory is over pace, except for a card marked to use both reserves (`reserve_cards`, F172 D6), which isn't held. Developer rows never say it.

### Done when
- a unit test of the pace function at three points of a week, matching `_check`'s decisions, and one of the "until" time
- over pace, the week row shows the post, the striped stretch and the plate with "lead tickets wait until about …"; on pace, the post and "on pace", no plate
- over pace, a lead ticket's row in Next in line says "held by Claude's week pace until about …"; a developer's row doesn't
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
