---
id: f9-17-fix-dial-colours-and-reset
milestone: f9-line-polish
depends_on: []
difficulty: 3
files:
  - factory_dashboard/templates/overview.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
finding: f3-25-dials
---

### Goal
On a phone, each allowance dial's ring is drawn in its window's colour (green, yellow or red) and shows the window's reset line under it.

### Context
Read the `allowance` section of `factory_dashboard/templates/overview.html`, the `.dial`, `.meter` and `.swatch` rules in `factory_dashboard/static/dashboard.css`, and `test_dial_fill_class_follows_bar_rule` in `tests/factory_dashboard/test_overview.py`.
- **What the review saw (f3-25):** the ring's stroke is `var(--c, var(--a2))`, and nothing sets `--c` for `.dial.under-mark`, `.past-mark` or `.nearly-out`: only `.meter > span` and `.swatch` have colour rules, so every ring is drawn in `--a2` whatever its state names say. The state is named on the svg, the colour is not.
- The phone CSS hides `#allowance .line:last-child`, which is the reset line ("resets in 2 h") that f3-25 asked for under each dial. Under 640 px the reset text is not on the screen.
- `test_dial_fill_class_follows_bar_rule` compares the state names inside an `if dial_match and meter_match`, with a regex that may match no row: it can pass having checked nothing. The `_meter_fills` helper in `tests/factory_dashboard/test_app.py` falls back from the bars to the dials, so a missing meter is not noticed.

### Done when
- a browser test at 390 px reads each ring's computed stroke: a window under its mark differs from one past its mark and from one above 95%, and each equals the colour of the same window's bar at 1440 px
- at 390 px each dial's reset text is visible, and the text is the row's own reset label
- `test_dial_fill_class_follows_bar_rule` fails if no row is found or a row has no dial or no meter
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
