---
id: f3-14-line-on-overview
milestone: f3
depends_on: [f3-05-line-panels, f3-07-replay-controls, f3-11-replay-steps]
difficulty: 5
files:
  - factory_dashboard/line.py
  - factory_dashboard/overview.py
  - factory_dashboard/templates/overview.html
  - factory_dashboard/templates/line.html
  - factory_dashboard/templates/_partials/live.html
  - factory_dashboard/templates/base.html
tests:
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_line.py
  - tests/factory_dashboard/test_app.py
---

### Goal
The Overview becomes the factory line: `/` shows the allowance and Needs you at the top, then the floor with its replay bar, then Now and the other panels; `/line` redirects to `/`.

### Context
Read `factory_dashboard/templates/line.html`, `factory_dashboard/templates/_partials/line.html`, `factory_dashboard/templates/overview.html`, `factory_dashboard/templates/_partials/live.html`, `line_page` and `line_live` in `factory_dashboard/line.py`, the `overview` route in `factory_dashboard/overview.py`, the tab list in `factory_dashboard/templates/base.html`, and the tests that open `/line` in `tests/factory_dashboard/test_line.py` and `tests/factory_dashboard/test_app.py`.
- **What `/line` does today moves to `/`, not away:** the replay URLs on `.page` (`data-replay`, set by `line_page`), the `line_seen` cookie it sets, the `factory_dashboard/static/factory.js` script and the replay bar. `/line/live` and `/line/replay` stay as they are.
- **Two refreshes:** `#live` (Needs you, Now) is swapped whole every 5 s from `/live`, and `#line-live` (the floor) from `/line/live`. The floor sits between Needs you and Now, so it can't sit inside `#live`.
- **The order on `/`:** allowance and Needs you at the top (the owner, 2026-10-03), the floor, then Now and the rest. F4's and F5's Overview tickets adapt to this.
- **Navigation:** the "Factory line" tab goes; "Overview" is the factory.
- **Tests:** the browser tests that open `/line` open `/` instead; a test that `/line` answers a redirect to `/`, keeping `?project=`.

### Done when
- `/` holds `svg#floor`, the `#factory-line` JSON and the replay bar, and the browser tests on the floor and the replay pass on `/`
- the sections on `/` come in the order above; Now still refreshes from `/live` and the floor from `/line/live`
- `/line?project=x` redirects to `/?project=x`; no tab links to `/line`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
