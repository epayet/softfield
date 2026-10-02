---
id: f5-08-signoff-button
milestone: f5-board
depends_on: [f5-07-replan]
difficulty: 3
files:
  - factory_dashboard/milestones.py
  - factory_dashboard/templates/milestone.html
tests:
  - tests/factory_dashboard/test_milestones.py
---

### Goal
A milestone page whose tickets are all done shows a "Sign off" button that asks the runner to sign it off.

### Context
Read `factory_dashboard/milestones.py` (the `/milestones/{key}` route), `factory_dashboard/templates/milestone.html`, `factory_dashboard/requests.py` and its worked example in `docs/agents/developer.md` ("a button that asks the runner"), and `tests/factory_dashboard/test_milestones.py`.
- The button posts a `signoff` request with the milestone's key, the way the worked example does. It shows only when the milestone isn't done and none of its tickets is in ready, running, escalated or blocked.
- After the click, the button's place shows the request partial ("Asked: the runner will do it", then the result).

### Done when
- a milestone with every ticket done, not signed off, shows the button with its key in the request
- a milestone with a ready ticket, or already done, shows no button
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
