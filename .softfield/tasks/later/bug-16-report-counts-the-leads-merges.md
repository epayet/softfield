---
id: bug-16-report-counts-the-leads-merges
milestone: bugs
difficulty: 4
depends_on: []
agent: lead
area: factory
priority: 41
finding: f41-F3
files:
  - factory_dashboard/queries.py
tests:
  - tests/runner/test_report.py
---

### Goal
`softfield report` counts a lead ticket built in a terminal session as merged.

### Context
Read `def milestone_results` in `factory_dashboard/queries.py` (its `merged` counts tickets with a `commit`) and `tests/runner/test_report.py`, which is protected (f1 D1: what the report counts is the lead's call).
- Tickets the lead builds in a terminal session have no runner commit, so F41 read "0 of 2 merged".
- Count a ticket in `.softfield/tasks/done/` whose runner footer says `result: done` and whose `agent:` is `lead` as merged by the lead, however it got there. Find where the tickets table learns a ticket's folder and footer (the sync at each command's start) and use what it stores; add nothing to the schema unless it has to.

### Done when
- a milestone with one runner merge and one terminal-built lead ticket in `done/` reads "2 of 2" merged
- a lead ticket in `done/` without `result: done` (escalated, set aside) isn't counted
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
