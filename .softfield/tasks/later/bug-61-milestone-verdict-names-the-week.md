---
id: bug-61-milestone-verdict-names-the-week
milestone: bugs
difficulty: 2
depends_on: []
agent: lead
area: factory
finding: f219-lead-tickets-don-t-wait-on-F2
files:
  - runner/milestone.py
tests:
  - tests/runner/test_milestone.py
---

### Goal
`softfield milestone` says that lead tickets wait for Claude's week when that is why they wait, and puts nothing on the owner's desk for it.

### Context
Read `run_milestone` and `PAUSED` in `runner/milestone.py`, `_needs_owner` in `runner/owner.py`, and `_passed_over` in `runner/loop.py`. A lead ticket the week holds stays in `ready/`, so `run_milestone` returns "tickets paused behind a blocked or escalated one: …". That is false, and `_needs_owner` turns it into a desk item, which ADR 44 item 6 says a held ticket doesn't make.
- Tickets stopped behind a blocked one keep today's words and desk item. Only when Claude's windows alone hold what is left does the stop change, to a new text `_needs_owner` doesn't match.

### Done when
- with the week over its pace line and a milestone's lead ticket ready, the stop names Claude's week and `_needs_owner` is false for it
- with a ticket behind a blocked one, the stop and the desk item are as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
