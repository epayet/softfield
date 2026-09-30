---
id: f1-11-timeline
milestone: f1
depends_on: [f1-07-replan-foundation]
difficulty: 6
files:
  - factory_dashboard/timeline.py
  - factory_dashboard/templates/timeline.html
  - factory_dashboard/static/charts.js
  - factory_dashboard/app.py
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_timeline.py
---

### Goal
`/timeline` draws runs and jobs over time, one lane per agent, coloured by outcome.

### Context
Follow the worked example: `factory_dashboard/overview.py`, `factory_dashboard/templates/overview.html` and `tests/factory_dashboard/test_overview.py`, with the fixture database in `tests/factory_dashboard/conftest.py` (extend it when your page needs more rows). The tables and columns are in `runner/metrics.py` (read it; it is the lead's file, so don't change it). Register your router in `factory_dashboard/app.py`. The Overview's strip shows the chart pattern (D5 in `docs/milestones/f1.md`): a `div` with `data-chart`, then a JSON block, drawn by one function in `factory_dashboard/static/charts.js`.
- Add one chart kind, `timeline`: lanes are agents, bars are jobs from start to end (a running job ends now), coloured by outcome (passed, failed, timeout, refused, running). Refusals (`usage_events` of kind `refusal`) are marked on their agent's lane. Hovering a bar shows the ticket, role and minutes; clicking opens `/jobs/{n}`.
- Filters: `milestone` (default: the latest) and `run`.
- Below the chart, a plain table of the same jobs, for reading without the chart.

**The dashboard is English-only: no gettext and no French.** Tests use `TestClient` and check the text the page shows, not only that it answers 200. Test the JSON block, not the drawing.

### Done when
- the JSON block has one lane per agent in the fixture and one bar per job, with its outcome, start and end
- a running job's bar ends at the time the page was rendered
- a refusal appears as a marker on its agent's lane
- `?milestone=m1` shows only m1's jobs
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
