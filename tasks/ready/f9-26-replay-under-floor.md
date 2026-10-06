---
id: f9-26-replay-under-floor
milestone: f9-line-polish
depends_on: [f9-13-home-without-clog-and-verdict]
difficulty: 2
files:
  - factory_dashboard/templates/overview.html
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
On the Overview, the replay bar comes right after the floor, not at the bottom of the page under the charts.

### Context
Read `factory_dashboard/templates/overview.html` (`{% include "_partials/line.html" %}`, and `#replay` after `#spend`: its comment says why it sits outside `#line-live`), the `.replay` rules in `factory_dashboard/static/dashboard.css` (it sticks to the bottom only while replaying, f3-31), and the section-order test in `tests/factory_dashboard/test_overview.py`.
- The owner (2026-10-06): "the replay bar should be just below the factory line on mobile". The same place on desktop is fine.
- It must stay outside `#line-live`, which htmx refreshes every 5 s.

### Done when
- `#replay` is the next element after `#line-live` in `/`, and still outside it
- at 390 px the replay bar's top is within 40 px of the floor's bottom
- the section-order test lists the new order
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
