---
id: f1-06-dashboard-service
milestone: f1
depends_on: [f1-05-runner-report]
agent: lead
difficulty: 8
files:
  - factory_dashboard/app.py
  - tests/factory_dashboard/conftest.py
  - factory_dashboard/overview.py
  - factory_dashboard/templates/base.html
  - factory_dashboard/templates/overview.html
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/static/charts.js
  - runner/cli.py
  - runner/report.py
  - docs/agents/junior.md
tests:
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_app.py
---

### Goal
`uv run runner dashboard` serves the factory dashboard at `127.0.0.1`, with its Overview page built as the worked example developers will copy.

### Context
Read `docs/milestones/f1.md` (D1, D3, D4, D5, D8, D9) and `docs/adr/13-factory-dashboard.md` §2–3. Look at `docs/milestones/f1-mockup.html` for the design (its styles and the Overview), but don't copy its data or script. Test with FastAPI's `TestClient` against `tests/factory_dashboard/conftest.py`, a fixture database written with `runner/metrics.py`.
- **`factory_dashboard/app.py`:** the FastAPI app, Jinja2 templates, static files, the database opened read-only (`file:…?mode=ro`, one connection per request), a `?project=` filter every page keeps, and `include_router` per page module. `runner dashboard [--port 8765]` runs it with uvicorn on `127.0.0.1` only.
- **`factory_dashboard/templates/base.html`:** the top bar with the project filter and a tab per D1 page (links to routes not built yet are fine), breadcrumbs, the vendored htmx and ECharts, `factory_dashboard/static/dashboard.css` and `factory_dashboard/static/charts.js`.
- **`factory_dashboard/overview.py` + `factory_dashboard/templates/overview.html`,** top to bottom: **Needs you** (D8: open owner items, a waiting queue with no live run, a stale heartbeat), **Running now** (D3, an htmx partial refreshed every 5 s), the queue with the command that drains it (D4), the last verdict, a Claude allowance bar (tokens this window from the jobs), savings for the current milestone (D7, from `factory_dashboard/queries.py`), and one ECharts strip as the example of D5.
- **The worked example:** a short "Dashboard pages" entry under worked examples in `docs/agents/junior.md`: a page is a module with an `APIRouter` and its own SQL, a template extending `factory_dashboard/templates/base.html`, and a test file that checks the rendered text and each chart's JSON.
- **Session reports** (`runner/report.py`) shrink to a summary and the dashboard's link for the run.

### Done when
- `/` shows Needs you, Running now, the queue with its command, the last verdict, the allowance bar and savings, for the fixture's project; `?project=other` shows only that project
- a running job with a fresh heartbeat is under Running now; with a 3-minute-old heartbeat it's a Needs-you item instead
- the Running-now partial answers on its own URL for htmx
- the chart's JSON block holds the fixture's numbers
- the app refuses to write (the database is opened read-only)
- `uv run runner check-all --task f1-06-dashboard-service` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
