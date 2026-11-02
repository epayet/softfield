---
id: bug-24-a-queued-look-shows-its-message
milestone: bugs
difficulty: 3
depends_on: []
area: factory
priority: 51
finding: f106-where-do-blocked-tickets-go-for
files:
  - factory_dashboard/overview.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
A queued planner job that looks at a blocked ticket shows the runner's message in Next in line, as a plant's shows the owner's words.

### Context
Read `def queued_jobs` in `factory_dashboard/overview.py`: for a Planning row it reads the message from `owner_requests` by the subject's `#<id>`. A look at a blocked ticket has the subject `<card>#m<message id>` (ADR 29), so it finds none and shows only its reason. `def look_of` in `runner/planner.py` reads such a subject.
- When the suffix is `#m<id>`, read that message's text from `planner_messages` instead.

### Done when
- a queued look with subject `f12#m40`, where message 40 says "f12-03 blocked: …", shows that text (cut at 60 characters as other rows are)
- a plant's row (`#<request id>`) reads as today
- a look whose message is gone shows its reason only
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
