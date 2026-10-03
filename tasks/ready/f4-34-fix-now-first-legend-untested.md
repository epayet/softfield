---
id: f4-34-fix-now-first-legend-untested
milestone: f3
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f3-18-now-first-checkpoint-2
---

### Goal
Fix a checkpoint finding on f3-18-now-first: the legend's fold and the compact allowance row have no test.

### Context
The merge of `tasks/done/f3-18-now-first.md` changed only the section order in `test_the_overview_shows_every_panel_in_order`. What the ticket also asks is not checked by any test:
- The `.legend` block now sits inside a `<details>` (summary "How to read the floor") in `factory_dashboard/templates/_partials/line.html`, after the floor svgs, without `open`.
- `.allow` in `factory_dashboard/static/dashboard.css` went from `display: grid` to `display: flex; flex-wrap: wrap`. The ticket asks for one compact row under Now; no test or screenshot looks at it, at desktop or under 640 px.
- The ticket's "Done when" asks for a test that reads the positions of `#needs-you`, `#now`, `#allowance` and `#line-live` in the HTML; the id list covers the sections but nothing checks the legend.

### Done when
- a test reads `/` and shows the four legend entries inside a `<details>` that has no `open` attribute, whose summary reads "How to read the floor", placed after the floor's svgs, and not anywhere before them
- a browser test (see `tests/factory_dashboard/test_line.py` for how) opens `/` at desktop width and at a phone width and checks that the allowance rows sit side by side where there is room, and that each row's label and percent are visible
- the listed `tests:` pass, and fail without the behaviour they check
- all gates pass
