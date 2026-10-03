---
id: f3-10-line-phone-finish
milestone: f3
depends_on: []
difficulty: 3
finding: f3-cp8
files:
  - factory_dashboard/static/factory.js
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
The phone's portrait floor is finished as f3-09 asked: its stations sit where `LinePhone.dc.html` draws them, and browser tests at 390 px prove it.

### Context
f3-09-line-phone-fixes was merged with a one-line change (the lead no longer drawn 100 in from `PHONE.lead.x`) and no test. Read `tasks/done/f3-09-line-phone-fixes.md` for the picture's coordinates and the full Done when, which still stands; read `PHONE` and `drawPhone` in `factory_dashboard/static/factory.js` (from line 246) and the browser tests in `tests/factory_dashboard/test_line.py` (from line 563).
- Facts, still wrong in the phone code: the bay adds `i*100` to each developer's y as well as `i*108` to its x (lines 299-300), so developers run diagonally out of the bay and their box is 100 high, not 120; `PHONE.rev2` is unused (reviewers at `6 + i*180`, not 6 and 186 / 276 as the picture has them); `PHONE.bay`, `checks`, `merged`, `ripe`, `stash` and `lead` don't match the picture's y values and sizes; `drawAll` (line 328) only runs on `htmx:load`, so crossing 640 px doesn't redraw.
- Facts, tests: `test_a_phone_sees_the_portrait_floor` (line 586) still only compares `data-machine` ids; no test measures a box.

### Done when
- the f3-09 Done when holds: at 390 px no horizontal scroll, stations in the order field, queue, lead, reviewers, developers, checks, merged, stash, no two `[data-machine]` boxes overlap, three developers all inside the bay's rect, every box at least 44 px wide and high, and a resize from 1280 to 390 px and back draws the phone floor then the desktop one (browser tests)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
