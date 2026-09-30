---
id: f1-08-jobs-list
milestone: f1
depends_on: [f1-33-runner-check-fixes]
difficulty: 4
files:
  - factory_dashboard/jobs.py
  - factory_dashboard/templates/jobs.html
  - factory_dashboard/app.py
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_jobs.py
---

### Goal
`/jobs` lists every job, newest first, with filters.

### Context
Follow the worked example: `factory_dashboard/overview.py`, `factory_dashboard/templates/overview.html` and `tests/factory_dashboard/test_overview.py`, with the fixture database in `tests/factory_dashboard/conftest.py` (extend it when your page needs more rows). The tables and columns are in `runner/metrics.py` (read it; it is the lead's file, so don't change it). Register your router in `factory_dashboard/app.py`. `write_fixture`'s numbers are pinned by `tests/factory_dashboard/test_queries.py` and `tests/factory_dashboard/test_overview.py`: put the rows your page needs in a function of your own (as `write_live` is), not among f1's or m4's tickets and jobs.
- `jobs.gates` is JSON, `[{"name", "ok", "seconds", "log"}]` in the order they ran; Claude jobs have none.
- Filters are query parameters, each optional, and combine: `project`, `milestone` (a key like `m4`), `ticket`, `agent`, `role`, `outcome`. The filter form keeps the values chosen.
- Columns: when it started, ticket (a link to `/tickets/{id}`), role, agent, attempt, outcome, minutes, tokens in / out, the failed gate if any. Each row links to `/jobs/{n}` (built by the next ticket).
- At most 200 rows, with a line saying how many more there are.

**The dashboard is English-only: no gettext and no French.** Tests use `TestClient` and check the text the page shows, not only that it answers 200.

### Done when
- with no filter, the fixture's jobs show newest first
- `?agent=claude-opus&role=escalation` shows only those jobs; an unknown value shows "No jobs match" and keeps the form
- a failed attempt shows its failed gate's name; a running job shows "running"
- more than 200 jobs shows 200 and "N more"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
