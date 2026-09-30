---
id: f1-14-runs-pages
milestone: f1
depends_on: [f1-10-ticket-pages]
difficulty: 3
files:
  - factory_dashboard/runs.py
  - factory_dashboard/templates/runs.html
  - factory_dashboard/templates/run.html
  - factory_dashboard/app.py
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_runs.py
---

### Goal
`/runs` lists runs, newest first, and `/runs/{run_dir}` shows what one run did.

### Context
Follow the worked example: `factory_dashboard/overview.py`, `factory_dashboard/templates/overview.html` and `tests/factory_dashboard/test_overview.py`, with the fixture database in `tests/factory_dashboard/conftest.py` (extend it when your page needs more rows). The tables and columns are in `runner/metrics.py` (read it; it is the lead's file, so don't change it). Register your router in `factory_dashboard/app.py`. `factory_dashboard/tickets.py` shows a list and a page in one module.
- **The list:** run dir, command, start, minutes, verdict, jobs, tickets merged. A run still going (no end, heartbeat under 2 minutes old) says "running"; one with no end and an older heartbeat says "stopped".
- **The page:** the same facts, then its jobs in order (links to `/jobs/{n}`) and the tickets it touched (links to `/tickets/{id}`).
- An unknown run answers 404.

**The dashboard is English-only: no gettext and no French.** Tests use `TestClient` and check the text the page shows, not only that it answers 200.

### Done when
- the fixture's runs show newest first, with their verdicts
- a run with a fresh heartbeat shows "running", and one whose heartbeat is 3 minutes old shows "stopped"
- a run's page lists its jobs in order and links its tickets
- an unknown run is a 404
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
