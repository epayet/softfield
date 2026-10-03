---
id: f4-10-queue-live
milestone: f4-always-on
depends_on: [f4-08-queue-waits-for]
difficulty: 4
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/overview.html
  - factory_dashboard/templates/_partials/live.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Queue refreshes with Running now every 5 s, and sits beside it on a wide screen, scrolling inside a fixed height, so a long queue no longer pushes the page down.

### Context
Read `factory_dashboard/overview.py` (`_live_context`, `overview`, `live`), `factory_dashboard/templates/overview.html`, `factory_dashboard/templates/_partials/live.html`, `factory_dashboard/static/dashboard.css` (`.row`, `.scroll`) and the live tests in `tests/factory_dashboard/test_overview.py`.
- Facts: only `#live` (Needs you, Running now) is polled (`hx-trigger="every 5s"`). The Queue is drawn once at page load, so its count drifts from Needs you's "N tickets waiting" until a reload.
- Move the Queue section into the `/live` partial and its data into `_live_context`. Put Running now and the Queue side by side in a `.row`: they stack under 640 px. The Queue's table scrolls inside a max height of about 60% of the viewport.
- Keep the section ids `running` and `queue`, which the tests and the review use.

### Done when
- `/live` returns the Queue with the same rows and order as `/`
- a ticket added to the database between two `/live` calls appears in the second
- on `/`, `#running` and `#queue` are inside one `.row`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 872
gate_failures: []
tokens: 939301
```
