---
id: bug-25-a-blocked-item-reads-its-look
milestone: bugs
difficulty: 4
depends_on: []
agent: lead
area: factory
priority: 52
finding: f106-where-do-blocked-tickets-go-for-F3
files:
  - factory_dashboard/planning.py
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A blocked ticket's "The lead's fix" plate, on the desk and on its page, says the fix waits on F<n>'s thread only once the lead has answered the runner's look.

### Context
Read `def get_blocked_info` in `factory_dashboard/planning.py` and `def look_of` in `runner/planner.py`. Lead ticket: its tests are in `tests/factory_dashboard/test_planning.py` (3,500 lines).
- Today any lead message on the card's thread after the runner's look sets `lead_replied`, so a reply to another of the owner's questions there reads as the fix.
- Read instead whether the look's planner job (subject `<card>#m<message id>`, in the work queue) is done. While it waits, the plate says "The lead is reading the work and its logs; its fix comes here", as with no reply.

### Done when
- a look still queued, with a lead reply on the thread to something else: the plate says the lead is reading
- the look's job done: the plate says the fix waits on F<n>'s thread, with its link to `/planning/<card>`
- a bug ticket with no card reads as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
