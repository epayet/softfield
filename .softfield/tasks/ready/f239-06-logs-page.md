---
id: f239-06-logs-page
milestone: f239-i-want-to-be-able-to-3
difficulty: 3
depends_on: [f239-04-replan, f239-08-services-and-commit]
files:
  - factory_dashboard/stacks_routes.py
  - factory_dashboard/templates/app_logs.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_stacks_routes.py
---

### Goal
A project's app has a logs page: its state on top, then the last 200 lines of its stack's logs, refreshed every 5 seconds while the page is open, for all services or one.

### Context
The picture to build is the Logs part of `.softfield/cards/f239-mockup/projects-run.html`. Read ADR 46 item 9 and D5 in `.softfield/cards/f239-i-want-to-be-able-to-3.md`, then `logs`, `state` and `services` in runner/stacks.py (f239-01; f239-08 adds `services`) and `stack_of`, `app_row` and the routes in `factory_dashboard/stacks_routes.py` (f239-03).
- `GET /projects/{name}/logs`, with `?service=` for one service, goes in `stacks_routes.py` beside Run and Stop, using `stack_of`: 404 for a name not in the registry or without `[run]`, and for a `service` not in `services(stack)` (`logs` itself raises `ValueError` for a malformed one). It is a GET: no guard, no write. The log block is a partial the page polls with htmx every 5 s; it stays scrolled to the bottom unless the owner scrolled up.
- Lines are shown as text, escaped, in the mono font; the newest line last.
- A pause button stops the refresh, for reading; the page says "updated at HH:MM:SS".

### Done when
- the page shows the last lines `logs` returns, escaped, and the service chooser lists the stack's services
- `?service=web` asks `logs` for that service only
- an unknown project, and an unknown service, answer 404
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
