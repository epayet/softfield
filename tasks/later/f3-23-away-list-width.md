---
id: f3-23-away-list-width
milestone: f3
depends_on: []
difficulty: 2
files:
  - factory_dashboard/templates/_partials/away.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
"While you were away" lists each merged ticket across the panel's whole width, so a night's tickets take a screen, not ten.

### Context
Read `factory_dashboard/templates/_partials/away.html`, the `.steps` rules in `factory_dashboard/static/dashboard.css`, and `open_overview` and the away tests in `tests/factory_dashboard/test_overview.py`.
- **What the review saw (f3-22, `var/shots/f3-22/desktop-1440-dark-away.png`):** each item's text is squeezed into a column about 110 px wide, and the 27 tickets of one night make the Overview about 10,600 px tall at 1440 px wide.
- **Why:** `.steps li` is a two-column grid (`110px 1fr`) made for a "when" and a "what"; the away items have only the `.what` span, so it lands in the 110 px column. Other pages use `.steps` with both columns: keep their layout as it is.
- The ticket name stays a link to `/tickets/<ticket name>`, followed by its title and "(merged by …)".

### Done when
- a browser test at 1440 px wide over `write_away`'s rows: each `#away li .what` is at least 80% of the panel's inner width
- the away tests still pass, and a page that uses `.steps` with a `.when` keeps its two columns
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
