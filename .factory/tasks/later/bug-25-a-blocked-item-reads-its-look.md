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
A blocked ticket on the desk says "the lead's fix waits on F<n>'s thread" only once the lead has answered the runner's look, and then links to that thread.

### Context
Read `def _blocked` in `factory_dashboard/planning.py` and `def look_of` in `runner/planner.py`. Lead ticket: its tests are in `tests/factory_dashboard/test_planning.py` (3,500 lines).
- Today any lead message on the card's thread after the runner's look counts, so a reply to another of the owner's questions there reads as the fix.
- Read instead whether the look's planner job (subject `<card>#m<message id>`, in the work queue) is done. When it is, the item's link is the card's thread; while it waits, "the lead is looking at it" and the ticket's page, as today.

### Done when
- a look still queued, with a lead reply on the thread to something else: "the lead is looking at it", linked to the ticket
- the look's job done: "the lead's fix waits on F<n>'s thread", linked to `/planning/<card>`
- a bug ticket with no card reads as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
