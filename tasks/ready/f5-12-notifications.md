---
id: f5-12-notifications
milestone: f5-board
depends_on: []
agent: lead
difficulty: 4
files:
  - factory_dashboard/static/notify.js
  - factory_dashboard/templates/base.html
  - factory_dashboard/templates/_partials/live.html
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
While a dashboard page is open, the browser shows a notification when something new needs the owner, and when all the work is done (the queue is empty and nothing runs).

### Context
Read `docs/adr/18-dashboard-writes.md` item 4, `factory_dashboard/templates/base.html`, `factory_dashboard/templates/_partials/live.html` (polled every 5 s) and `factory_dashboard/static/charts.js` (how the dashboard's own scripts are loaded). Test-first where the server is involved.
- The live partial carries the facts as data attributes: the ids of open Needs-you items, and "all done". `factory_dashboard/static/notify.js` compares them after each swap (`htmx:afterSwap`), and notifies once per new item, and once when all done turns true.
- Ask permission with a small "Notify me" button in the top bar, never on load. No service worker, no third party.
- This is the first script with behaviour in the dashboard: add it to the worked examples in `docs/agents/developer.md`.

### Done when
- the live partial carries the item ids and the all-done flag (asserted from its HTML)
- `notify.js` notifies once per new item and once on all done (checked by hand at review, on desktop and phone)
- `uv run runner check-all --task f5-12-notifications` passes
