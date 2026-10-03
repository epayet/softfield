---
id: f3-16-fix-overview-live-refresh
milestone: f3
depends_on: []
difficulty: 3
finding: f3-cp4
files:
  - factory_dashboard/templates/overview.html
  - factory_dashboard/templates/_partials/live.html
  - factory_dashboard/overview.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
On the Overview, Needs you and Now keep refreshing every 5 s for as long as the page is open, and Needs you comes back when a need appears after the page loaded with none.

### Context
Read `factory_dashboard/templates/overview.html`, `factory_dashboard/templates/_partials/live.html`, the `/live` route in `factory_dashboard/overview.py` and the live tests in `tests/factory_dashboard/test_overview.py`. f3-14-line-on-overview split the old `#live` wrapper into `#live-needs-you` and `#live-now`, each with `hx-get="/live"`, `hx-select` and `hx-swap="outerHTML"`.
- Facts: with `outerHTML` plus `hx-select="#now"`, the wrapper `div#live-now` is replaced by the bare `<section id="now">`, which has no `hx-get`: polling stops after the first refresh. Same for `#needs-you`.
- When there are no needs, `#needs-you` isn't rendered, so `hx-select="#needs-you"` matches nothing and the swap leaves the wrapper empty or removed: a need that appears later never shows.
- The same two wrappers are written twice, inline in `factory_dashboard/templates/overview.html` and in `factory_dashboard/templates/_partials/live.html`, which `/live` still returns.
- No test follows a refresh: the Overview tests only read the HTML once.

### Done when
- a browser test (see how `tests/factory_dashboard/test_line.py` opens a page with Playwright): load `/` with no needs, make a need appear in the database, wait for the next refresh, and the page shows that need's text under Needs you
- a browser test: after two refreshes the Now section still shows current content (change a running ticket between them)
- the wrappers are written once
- the listed `tests:` pass, and the new ones fail on the f3-14 templates
- all gates pass (see `docs/workflow.md`)
