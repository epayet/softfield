---
id: bug-10-a-sent-back-proposal-opens-again
milestone: bugs
difficulty: 4
depends_on: []
agent: lead
area: factory
priority: 34
finding: f31-F5
files:
  - runner/planner.py
tests:
  - tests/runner/test_planner.py
---

### Goal
A proposal the owner sent back reads "open" again, with its buttons, once the lead has answered on its thread.

### Context
Read `def proposal_state` in `runner/planner.py`. `runner/**` is protected: tests first.
- Today it reads only requests, so a proposal sent back stays "sent back", with no buttons, until the lead lists it again. The planner prompt asks the lead to; this is the backstop.
- Give `proposal_state` the time of the thread's latest lead message, and count a `send_back` older than it as answered.

### Done when
- a proposal sent back, then a lead message on its thread: it reads open
- sent back with no lead message since: it reads sent back
- a rejected or approved proposal keeps its state whatever the lead says after
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
