---
id: f1-30-allowance-forecast
milestone: f1
depends_on: [f1-25-router]
difficulty: 5
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/overview.html
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
Stretch: the Overview shows one allowance bar per service, with when it will run out and what's left to spend before it resets.

### Context
Follow the worked example: `factory_dashboard/overview.py`, `factory_dashboard/templates/overview.html` and `tests/factory_dashboard/test_overview.py`, with the fixture database in `tests/factory_dashboard/conftest.py` (extend it when your page needs more rows). The tables and columns are in `runner/metrics.py` (read it; it is the lead's file, so don't change it). Register your router in `factory_dashboard/app.py`. This ticket extends the Overview itself.
- The forecast is computed by `forecast` in `runner/router.py` (the router uses the same one); call it, don't rewrite it.
- One bar per service (Claude, Ollama, Copilot): used in the current window (tokens or requests from the jobs), the reset time, the run-out forecast, and "leftovers to spend" when it will reset with credit unused. A service with no data yet says "no data yet".

**The dashboard is English-only: no gettext and no French.** Tests use `TestClient` and check the text the page shows, not only that it answers 200.

### Done when
- with fixture jobs and refusals, each service's bar shows its use, reset and forecast
- a service that will reset unused shows its leftovers
- a service with no jobs shows "no data yet"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
