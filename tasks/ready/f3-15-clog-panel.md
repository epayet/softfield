---
id: f3-15-clog-panel
milestone: f3
depends_on: [f3-04-clog-today, f3-05-line-panels, f3-16-fix-overview-live-refresh]
difficulty: 3
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/live.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
Beside Now, the Overview shows "What clogged the line today": the four numbers from the line's `clog`, in plain words, and one line naming the biggest.

### Context
Read the `aria-label="What clogged the line today"` section of `docs/milestones/f3-line-mockup/Line.dc.html` (markup to read, not a page to open), `docs/milestones/f3.md` D11 ("What clogged the line today": f3-04 wrote there what each number is), `clog` in `factory_dashboard/queries.py`, `live_line` in `factory_dashboard/line.py` and `_live_context` in `factory_dashboard/overview.py`.
- `live_line(...)["clog"]` holds the four numbers (f3-04); f3-05 already calls `live_line` in `_live_context`. Use the labels from the mock-up.
- When `clog` is `None` there's no panel at all, not an empty one.

### Done when
- with a `clog` document the panel `#clog` shows the four numbers with their labels, and the biggest one named
- with `clog` `None` the page has no `#clog` section
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
