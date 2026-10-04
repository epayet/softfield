---
id: f8-06-switch-buttons
milestone: f8-one-queue
depends_on: [f8-05-replan]
difficulty: 3
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/live.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
Beside Claude's week and 5-hour meters, a switch says whether the factory may use the reserve kept there, and turning it posts the owner's request.

### Context
Read D4 in `docs/milestones/f8-one-queue.md`, `factory_dashboard/requests.py` and its worked example in `docs/agents/developer.md` ("a button that asks the runner"), the allowance section of `factory_dashboard/templates/_partials/live.html`, and `tests/factory_dashboard/test_overview.py`.
- The switch's state comes from the runner's state (`reserve` in `var/runs/state.json`, as f8-04 stores it); its label says what it does: "Let the factory use the week's reserve", "Let the factory use your 25% of the 5-hour window".
- Each posts a `reserve` request with subject `week` or `five_hour` and value `on` or `off`.

### Done when
- each meter row has its switch, showing the stored state, and its request carries the right subject and value (asserted within that row)
- a meter of another agent has no switch
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
