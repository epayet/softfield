---
id: f1-12-milestones-list
milestone: f1
depends_on: [f1-07-replan-foundation]
difficulty: 4
files:
  - factory_dashboard/milestones.py
  - factory_dashboard/templates/milestones.html
  - factory_dashboard/app.py
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_milestones.py
---

### Goal
`/milestones` lists the milestones, newest first, with the trends across them.

### Context
Follow the worked example: `factory_dashboard/overview.py`, `factory_dashboard/templates/overview.html` and `tests/factory_dashboard/test_overview.py`, with the fixture database in `tests/factory_dashboard/conftest.py` (extend it when your page needs more rows). The tables and columns are in `runner/metrics.py` (read it; it is the lead's file, so don't change it). Register your router in `factory_dashboard/app.py`. The numbers come from `factory_dashboard/queries.py` (`runner report` uses the same ones); use its functions rather than new SQL where one exists.
- A row per milestone: key (a link to `/milestones/{key}`, built by the next ticket), title, status, dates, tickets merged, first-attempt pass rate, escalations, review rounds, Claude dollars, net savings.
- Trends below: first-attempt rate, escalations, Claude dollars per merged ticket and savings per milestone, as small charts (D5 in `docs/milestones/f1.md`, one chart kind per trend is fine, or one `trend` kind reused).

**The dashboard is English-only: no gettext and no French.** Tests use `TestClient` and check the text the page shows, not only that it answers 200.

### Done when
- the fixture's milestones show newest first, with the numbers `factory_dashboard/queries.py` gives
- a milestone with no tickets yet shows dashes, not zeros or an error
- each trend's JSON block holds one point per milestone, oldest first
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
