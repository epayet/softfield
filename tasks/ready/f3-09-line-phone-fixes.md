---
id: f3-09-line-phone-fixes
milestone: f3
depends_on: [f3-02-line-phone]
difficulty: 3
finding: f3-cp3
files:
  - factory_dashboard/static/factory.js
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
The phone's portrait floor puts its stations where `LinePhone.dc.html` draws them, and a browser test at 390 px proves it.

### Context
Read `drawPhone` and `drawAll` in `factory_dashboard/static/factory.js` (lines 246-345), the browser tests in `tests/factory_dashboard/test_line.py` (from line 537), and lines 92-160 of `docs/milestones/f3-line-mockup/LinePhone.dc.html` (the picture's coordinates). Nothing else is needed.
- Facts, the layout: the `PHONE` table doesn't match the picture from the lead down. In the picture the lead is 14,494 160×118 with the reviewers to its right (186,514 and 276,514, each 70×98); the bay is 8,640 342×190 with developers side by side at x 18, 128, 238, y 690, 104×120 each; checks 134,868; merged 14,962; ripe 186,962; stash 40,1046 278×86 (it ends at 1132, inside the SVG's `viewBox` `0 0 358 1140`, which lives in `factory_dashboard/templates/_partials/line.html` and needn't change).
- Facts, the bugs: the bay adds `i*100` to each developer's y as well as `i*108` to its x, so developers run diagonally out of the bay; `PHONE.rev2` is never used (reviewers use `6 + i*180`); the lead is drawn 100 in from `PHONE.lead.x`, across the whole row.
- Facts, the tests: `test_a_phone_sees_the_portrait_floor` only compares the `data-machine` ids, and calls `open_line` a second time without the viewport (so it reloads at 1360 px). `line_client` has two developers (`LOCAL`, `GPT_OSS`); for three, add a third developer machine to the JSON in the page's `#factory-line` block before the page is served.
- Facts, resizing: `drawAll` only runs on `htmx:load`, so crossing 640 px doesn't redraw.
- Out of this ticket: the allowance dials, the field's planting side and planted rows, the retry belt.

### Done when
- at 390 px: no horizontal scroll (`document.documentElement.scrollWidth` ≤ 390), the stations' tops (`getBoundingClientRect`) come in the order field, queue, lead, reviewers, developers, checks, merged, stash, and no two `[data-machine]` boxes overlap (browser test)
- with three developers, all three boxes sit inside the bay's rect (browser test)
- every `[data-machine]` box on the phone floor is at least 44 px wide and high at 390 px
- resizing from 1280 to 390 px shows and draws the phone floor, and back again the desktop one (browser test)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 9359
logs: var/runs/20261003-074205/f3-09-line-phone-fixes
```
