---
id: f9-27-phone-rows-compact
milestone: f9-line-polish
depends_on: [f9-25-seeds-and-planting]
agent: lead
difficulty: 4
files:
  - factory_dashboard/static/factory.js
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
On a phone, the planted rows take about half their space today. Each row keeps its progress bar, and a "Show all N" toggle opens the rest when the owner wants them.

### Context
Read in `factory_dashboard/static/factory.js` `rows`, `drawPhone` (`PHONE_HEIGHT`, the field plot's height, and every station and `PHONE_BELTS` path below it) and `drawFloor`. Then the phone floor tests in `tests/factory_dashboard/test_line.py`.
- The owner (2026-10-06): "the planted rows look kinda nice but take a lot of space on mobile. Either a more compact way, or a way to expand if I want to see more. The progress bar of each milestone is nice."
- Today: up to 4 rows, 50 px apart, in a 262 px box, inside a 438 px field. Everything below is placed by absolute coordinates.
- Suggested: one line per row (name, bar, "7/19" on the same line), the 3 most active first (running, then most ready), then "Show all N". The toggle redraws the phone floor with every row, and the stations below move down by the same amount (an offset, not new coordinates by hand). Desktop unchanged.
- This is SVG geometry, so it's the lead's (F3's lesson). Keep it a small core the developers can follow.

### Done when
- at 390 px with 5 planted rows, the field is at most 300 px tall and shows 3 rows with bars and "Show all 5"
- tapping "Show all 5" shows all five, and every station and belt below moves down with no overlap (layout check); tapping again closes it
- the 5-second refresh keeps the toggle's state
- each row still links to its milestone (f9-03)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
