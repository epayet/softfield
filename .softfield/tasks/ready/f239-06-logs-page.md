---
id: f239-06-logs-page
milestone: f239-i-want-to-be-able-to-3
difficulty: 3
depends_on: [f239-04-replan]
files:
  - factory_dashboard/projects.py
  - factory_dashboard/templates/app_logs.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_projects.py
---

### Goal
A project's app has a logs page: its state on top, then the last 200 lines of its stack's logs, refreshed every 5 seconds while the page is open, for all services or one.

### Context
The picture to build is the Logs part of `.softfield/cards/f239-mockup/projects-run.html`. Read ADR 46 item 9 and D5 in `.softfield/cards/f239-i-want-to-be-able-to-3.md`, then `logs` and `state` in runner/stacks.py (f239-01) and `projects_page` in `factory_dashboard/projects.py`.
- `GET /projects/{name}/logs`, with `?service=` for one service: 404 for a name not in the registry or without `[run]`. The log block is a partial the page polls with htmx every 5 s; it stays scrolled to the bottom unless the owner scrolled up.
- Lines are shown as text, escaped, in the mono font; the newest line last.
- A pause button stops the refresh, for reading; the page says "updated at HH:MM:SS".

### Done when
- the page shows the last lines `logs` returns, escaped, and the service chooser lists the stack's services
- `?service=web` asks `logs` for that service only
- an unknown project answers 404
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
