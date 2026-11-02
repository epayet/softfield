---
id: bug-53-every-proposal-says-its-age
milestone: bugs
difficulty: 2
depends_on: []
agent: developer
area: factory
finding: f73-i-want-to-be-able-to-F4
files:
  - factory_dashboard/templates/proposal.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
An ADR or a merge waiting for days says how old its draft is, as a plan does.

### Context
From the old backlog file, in the review's words:

The stale note ("Drafted N days ago…") shows only on a plan, mock-up or replan (`proposal.html`, `#stale`), because its words point at Refresh. An ADR or a merge waiting three days says nothing about its age, while F73's outcome says "a proposal that has waited says how old its draft is". Fix: on the others, "Drafted N days ago: the code may have moved." without the Refresh sentence, and a test on an ADR. Stays: an ADR's text ages slower than a plan's tickets, and the runner's pre-flight still refuses a stale plan.

### Done when
- an ADR drafted days ago shows "Drafted N days ago: the code may have moved.", without the Refresh sentence
- the listed `tests:` pass
- all gates pass (see `docs/workflow.md`)
