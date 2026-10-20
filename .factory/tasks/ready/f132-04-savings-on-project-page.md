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
tests:
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_projects.py
---

### Goal
Savings from delegating and Claude per milestone leave the Overview for each project's page, where "so far" counts all of that project's delegated tickets instead of one card's.

### Context
Read `.factory/cards/f132-the-overview-shows-the-whole-factory.md` ("What happens today", D8) and the Proposed side of `.factory/cards/f132-mockup/overview.html` (the grey panel).
- Today `overview` in `factory_dashboard/overview.py` draws both from `current_milestone`, the newest card not done, which is now just the newest plant (F160, a card merged away, on 2026-10-20).
- `savings` in `factory_dashboard/queries.py` with no `key` sums the whole project; `spend_chart` in `factory_dashboard/overview.py` is already per project.
- The project's page is `project_page` in `factory_dashboard/projects.py`, template `factory_dashboard/templates/project.html`; move the two sections from `factory_dashboard/templates/overview.html` as they are drawn (the same `#savings` and `#spend` panels, and `factory_dashboard/static/charts.js` draws the chart from `data-chart="spend"`).
- The heading becomes "Savings from delegating on <project>, so far".
- Once the Overview no longer calls `current_milestone`, leave it for the Timeline (f132-07 removes that last use).

### Done when
- the Overview has neither panel
- `/projects/softfield` shows "Savings from delegating on softfield, so far" with the sums over all of softfield's delegated tickets, and the Claude per milestone chart of softfield's milestones
- a project with no delegated ticket says "No delegated tickets yet."
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
