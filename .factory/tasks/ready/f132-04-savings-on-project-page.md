---
id: f132-04-savings-on-project-page
milestone: f132-the-overview-shows-the-whole-factory
difficulty: 3
depends_on: [f132-02-overview-live-every-project]
files:
  - factory_dashboard/overview.py
  - factory_dashboard/projects.py
  - factory_dashboard/templates/overview.html
  - factory_dashboard/templates/project.html
  - factory_dashboard/static/charts.js
tests:
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_projects.py
---

### Goal
Savings from delegating leaves the Overview for each project's page, where "so far" counts all of that project's delegated tickets instead of one card's; the Claude per milestone chart goes.

### Context
Read `.factory/cards/f132-the-overview-shows-the-whole-factory.md` ("What happens today", D8) and the Proposed side of `.factory/cards/f132-mockup/overview.html` (the grey panel).
- Today `overview` in `factory_dashboard/overview.py` draws the savings from `current_milestone`, the newest card not done, which is just the newest plant (F160 on 2026-10-20, F177 on 2026-10-27, M4 on coucou's Overview).
- `savings` in `factory_dashboard/queries.py` with no `key` sums the whole project.
- The project's page is `project_page` in `factory_dashboard/projects.py`, template `factory_dashboard/templates/project.html`; move the `#savings` panel from `factory_dashboard/templates/overview.html` there, its three figures as they are drawn (they read well on a phone). The heading becomes "Savings from delegating on <project>, so far".
- The `#spend` panel goes from the Overview and goes nowhere: the Milestones page already draws Claude's dollars per merged ticket and the net savings per milestone. Remove `spend_chart` from `factory_dashboard/overview.py` and the `spend` chart from `factory_dashboard/static/charts.js`, with their tests; the module's docstring stops naming them.
- Once the Overview no longer calls `current_milestone`, leave it for the Timeline (f132-07 removes that last use).

### Done when
- the Overview has neither panel
- `/projects/softfield` shows "Savings from delegating on softfield, so far" with the sums over all of softfield's delegated tickets, and no chart
- a project with no delegated ticket says "No delegated tickets yet."
- `spend_chart` and the `spend` chart are gone; the Milestones page's charts are unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
