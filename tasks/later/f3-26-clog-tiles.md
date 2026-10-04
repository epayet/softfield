---
id: f3-26-clog-tiles
milestone: f3
depends_on: []
difficulty: 3
files:
  - factory_dashboard/templates/overview.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
"What clogged the line today" reads at a glance: four tiles with a big number each, the ones that cost time in the clog colour, and the biggest clog under them.

### Context
Read the `clog` section and the `savings` section's `.stats` tiles in `factory_dashboard/templates/overview.html` (the pattern to follow), the `.stats` and `.stat` rules in `factory_dashboard/static/dashboard.css`, and the clog tests in `tests/factory_dashboard/test_overview.py`. The pictures: the four tiles under Now in `docs/milestones/f3-line-mockup/LinePhone.dc.html` (the section labelled "What clogged the line today": a two-by-two grid, the number big, the words under it), and the clog panel of `docs/milestones/f3-line-mockup/Line.dc.html` (non-zero numbers in the clog colour).
- **What the review saw (f3-22, `var/shots/f3-22/desktop-1440-light-clog.png`):** four plain label and value lines, all one colour, so "22 · 250 min" of failed attempts looks the same as "0 min".
- **The tiles,** in today's order: waiting for Claude's limit (minutes), failed attempts (minutes, "on N failed attempts" under it), machines idle while one job runs ("N of M"), stopped for you (minutes). A tile whose number is not zero gets the clog colour through the `--clog` token; a zero stays the ordinary ink.
- Two by two under 640 px, four in a row above it. The "Biggest clog" line stays under the tiles. The section id stays `clog`.

### Done when
- `#clog` renders four tiles with today's four numbers and their words
- a tile with a non-zero number has the clog class and a zero one hasn't (a test with fixture jobs that give one zero and one non-zero number)
- a browser test at 390 px: the tiles are two by two
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
