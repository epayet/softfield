---
id: bug-29-archive-row-shows-it-on-its-way
milestone: bugs
difficulty: 3
depends_on: []
agent: lead
area: factory
priority: 56
finding: f50-the-data-safety-review-it-asks-F6
files:
  - factory_dashboard/templates/thread.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
On a card's thread, Archive and Remove seed show the dashed "on its way" pill the moment they are pressed, in one row at the bottom of the page.

### Context
Read `#remove-seed` and `#archive` in `factory_dashboard/templates/thread.html` (lines 254–283), and Sign off's `hx-on::before-request` with its `#signing-off-shape` template (lines 44–56), the worked example. Lead ticket: its tests are in `tests/factory_dashboard/test_planning.py`.
- Today pressing Archive removes the button and leaves a grey status; Remove seed shows nothing until a reload. The owner asked on 2026-10-07 that a request show at once, on its way (f50-F6).
- The two are stacked blocks after `#conversation`, and `#archive` keeps a `margin-top: 6px` from when it sat in the header (f22-F2): put both in one wrapping row, without the margin.

### Done when
- pressing Archive puts "Archiving at the runner's next pick" in a dashed pill where the button was, before the answer comes; Unarchive reads "Opening again at the runner's next pick"
- pressing Remove puts "Removing at the runner's next pick" in a dashed pill in place of its button
- on a seed's thread, Remove seed and Archive sit in one row with no top margin
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
