---
id: f1-31-eligibility-view
milestone: f1
depends_on: [f1-26-checkpoint-shadow, f1-15-agents-page]
difficulty: 4
files:
  - factory_dashboard/agents.py
  - factory_dashboard/templates/agents.html
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_agents.py
---

### Goal
Stretch: the Agents page shows which roles each agent has earned by shadowing, and why not yet for the others.

### Context
Follow the worked example: `factory_dashboard/overview.py`, `factory_dashboard/templates/overview.html` and `tests/factory_dashboard/test_overview.py`, with the fixture database in `tests/factory_dashboard/conftest.py` (extend it when your page needs more rows). The tables and columns are in `runner/metrics.py` (read it; it is the lead's file, so don't change it). Register your router in `factory_dashboard/app.py`. This ticket extends `factory_dashboard/agents.py`.
- The eligibility query is in `factory_dashboard/queries.py` (from f1-26); use it.
- A panel, agents × shadowed roles: "eligible" or the reason it isn't yet (for example "reviewing 6 < 8"), and the number of shadow jobs behind it. The owner changes `[roles]` by hand at a milestone review; the page only says who qualifies.

**The dashboard is English-only: no gettext and no French.** Tests use `TestClient` and check the text the page shows, not only that it answers 200.

### Done when
- an agent meeting every bar shows "eligible" for its role; one that doesn't shows the reason
- an agent that never shadowed isn't listed
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
