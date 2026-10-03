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
The Overview becomes the factory line. `/` shows the allowance and Needs you at the top, then the floor with its replay bar, then Now and the other panels. `/line` redirects to `/`.

### Context
Read these first:
- `factory_dashboard/templates/line.html`, `factory_dashboard/templates/_partials/line.html`, `factory_dashboard/templates/overview.html` and `factory_dashboard/templates/_partials/live.html`
- `line_page` and `line_live` in `factory_dashboard/line.py`
- the `overview` route in `factory_dashboard/overview.py`
- the tab list in `factory_dashboard/templates/base.html`
- the tests that open `/line` in `tests/factory_dashboard/test_line.py` and `tests/factory_dashboard/test_app.py`

- **What `/line` does today moves to `/`, not away.** That covers:
  - the replay URLs on `.page` (`data-replay` and `data-replay-day`, set by `line_page`). They still point at `/line/replay?project=…&since=…`.
  - the `line_seen` cookie it sets
  - the `factory_dashboard/static/factory.js` script
  - the replay bar

  `/line/live` and `/line/replay` stay as they are.
- **Two refreshes.** Today `#live` holds Needs you and Now and is swapped whole every 5 s from `/live`. `#line-live` (the floor) is swapped from `/line/live`.
- **Splitting `#live`.** The floor sits between Needs you and Now, so on `/` they need two separate wrappers. Each wrapper still refreshes every 5 s from `/live` and takes only its own part of the answer, using htmx's `hx-select`. The Needs-you wrapper must render even when there are no needs, so it is still there to refresh. `/live` itself keeps answering both sections (`test_the_live_partial_answers_on_its_own_for_htmx`).
- **The order on `/`.** The allowance and Needs you come at the top (the owner, 2026-10-03). The floor and its replay bar come next, then Now, then verdict, savings and spend. F4's and F5's Overview tickets adapt to this.
- **Navigation.** The "Factory line" tab goes; "Overview" is the factory.
- **Tests.**
  - The browser tests that open `/line` open `/` instead.
  - Add a test that `/line` answers a redirect to `/`, keeping `?project=`. TestClient follows redirects unless the request passes `follow_redirects=False`.

### Done when
- `/` holds `svg#floor`, the `#factory-line` JSON and the replay bar, and the browser tests on the floor and the replay pass on `/`
- the sections on `/` come in the order above, Needs you and Now still refresh from `/live`, and the floor still refreshes from `/line/live`
- `/line?project=x` redirects to `/?project=x`, and no tab links to `/line`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
