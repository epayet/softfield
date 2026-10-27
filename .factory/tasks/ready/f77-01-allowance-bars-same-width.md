---
id: f77-01-allowance-bars-same-width
milestone: f77-the-bars-in-the-agent-allowance
difficulty: 2
depends_on: [f9-29-week-pace]
files:
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
On the Overview, every window of the agent allowance is the same width, so Claude's 5-hour, Claude's week and Copilot's month bars are equally long.

### Context
Read `.factory/cards/f77-the-bars-in-the-agent-allowance.md` (Notes, D2), the `.allow` rules in `factory_dashboard/static/dashboard.css` (and the phone block under "Mobile: one row per window", f9-17), and `factory_dashboard/templates/_partials/allowance.html`.
- Today `.allow` is a wrapping flex row and each window (`.allow > div`) is as wide as its words, so a row with the "use reserve" lever is wider than Copilot's month.
- Make `.allow` a grid of equal columns, `repeat(auto-fit, minmax(220px, 1fr))`; the "Past both marks for:" line (`.allow .cards-on`) spans the whole row (`grid-column: 1 / -1`). Leave the phone block's one-row-per-window layout as it is.
- Follow the browser tests `test_allowance_bars_one_row_per_window_at_phone` and `test_allowance_bar_colours_match_at_phone_and_desktop` in `tests/factory_dashboard/test_overview.py` (the `page` and `allowance_client` fixtures).

### Done when
- at 1440 px, every `#allowance .meter` has the same width, to within 1 px (a browser test)
- at 390 px, each window is still one row and the layout check passes (the existing test stays green)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
