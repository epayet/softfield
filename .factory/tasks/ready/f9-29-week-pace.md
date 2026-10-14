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
tests:
  - tests/runner/test_allowance.py
  - tests/factory_dashboard/test_overview.py
---

### Goal
Claude's week meter shows today's pace line, and says in words whether the factory is on pace or over it, holding lead tickets back while developers go on.

### Context
Read `_check` in `runner/allowance.py` (a fixed window's pace line: `share * min(1, elapsed + MARGIN)`, ADR 25), `agent_allowances` and `WindowAllowance` in `factory_dashboard/overview.py` (the week's `mark` is the reserve, not the pace), and the allowance partial f9-28 made.
- The owner (2026-10-07): "i understand there is a pacing through the week logic for claude lead tickets, that's not quite visible on the dashboard whenever we hit that". Today only a queue row's reason says "over its pace line of N%".
- Make the pace line a public, pure function in `runner/allowance.py` (used by `_check` too, so the dashboard and the runner can't disagree), and give the week row a second tick at it, titled "today's pace".
- Words under the week row: "on pace" when used is under the line; "over pace: lead tickets wait until about <day HH:MM>, developers go on" when it isn't, the time being when the line passes today's use.

### Done when
- a unit test of the pace function at three points of a week, matching `_check`'s decisions
- the week row shows the pace tick and "on pace" under it, and "over pace: lead tickets wait until about …" over it
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
