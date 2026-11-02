---
id: f59-02-reports-page
milestone: f59-periodic-review-of-the-factory
difficulty: 6
depends_on: [f59-01-reports-week-numbers, f132-02-overview-live-every-project]
agent: lead
files:
  - factory_dashboard/reports.py
  - factory_dashboard/app.py
  - factory_dashboard/templates/reports.html
  - factory_dashboard/templates/base.html
  - factory_dashboard/static/charts.js
  - factory_dashboard/static/dashboard.css
  - tests/factory_dashboard/test_reports.py
tests:
  - tests/factory_dashboard/test_reports.py
---

### Goal
A Reports tab shows one week at a time, for the whole factory or one project: the week strip, its numbers beside the week before, the lead's written read when there is one, four graphs over every week and who did what.

### Context
Read `.softfield/cards/f59-periodic-review-of-the-factory.md` (D4, D5, D7) and build the Proposed of the mock-up, `.softfield/cards/f59-mockup/reports.html`, in the factory theme.
- Numbers from `week` and `series` in `factory_dashboard/reports.py` (f59-01); the routes go in the same module, registered in `factory_dashboard/app.py` as the others are.
- The whole factory is F132's list of every project (its D4, built by f132-02 in `factory_dashboard/overview.py`); the page is factory-wide as F132 D2 says, with its own scope switch (`?scope=<project>`).
- Graphs: `data-chart` and a JSON script, drawn by `factory_dashboard/static/charts.js`, as `factory_dashboard/templates/milestones.html` does; existing tokens only (`--opus`, `--qwen`, `--rule`, `--ink-2`).
- The read is `.softfield/reports/<monday>.md` in the factory's own project (D5); show the scope's section; a quoted line is drawn as a quote plate (D7), with no buttons yet.
- The tab goes after Timeline in `factory_dashboard/templates/base.html`.

### Done when
- `/reports` opens the newest finished week; `/reports/2026-10-19` that week; an unknown or non-Monday date answers 404
- the strip lists "This week" (numbers so far, dashed) then every past week, newest first, each saying "read written" or "numbers only"
- each tile shows its number and the week before's; a rate with no attempts shows "no attempts", not 0%
- `?scope=<project>` shows only that project's numbers and its section of the read; an unknown scope shows the whole factory
- a week with a file shows its read with the quoted lines as plates; one without says "No read for this week: numbers only"
- the four graphs carry every week of `series`, and each colour is named beside its graph
- on a 390 px wide screen nothing scrolls sideways except the week strip and the Who did what table
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
