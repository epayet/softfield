---
id: f3-09-line-phone-fixes
milestone: f3
depends_on: [f3-02-line-phone]
difficulty: 4
finding: f3-cp3
files:
  - factory_dashboard/static/factory.js
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/overview.html
tests:
  - tests/factory_dashboard/test_line.py
  - tests/factory_dashboard/test_overview.py
---

### Goal
The phone's portrait floor is laid out as `LinePhone.dc.html` draws it, and the allowances on a phone are four round dials, each asserted from its drawing.

### Context
Read `tasks/done/f3-02-line-phone.md` (what it asked), `docs/milestones/f3-line-mockup/LinePhone.dc.html` (the picture), `drawPhone` in `factory_dashboard/static/factory.js` and the phone tests in `tests/factory_dashboard/test_line.py`.
- Facts, what f3-02 left out: no dials at all (nothing in the diff draws an allowance ring, its mark or "–"/"no data"); the field has no planting side or planted rows (only the seeds); there is no retry belt from checks to the bay; the lead is drawn on its own row, not left of the reviewers.
- Facts, the layout: the bay places machine `i` at x `18 + i*108` **and** y `30 + i*100`, so several developers run diagonally out of the 160-high bay (and over `checks`); `PHONE.rev2` is never used (the reviewers use `6 + i*180`); the SVG's `viewBox` is `0 0 358 1140` but the stash ends near y 1072.
- Facts, the tests: the phone test only compares the set of `data-machine` ids with the document. It does not check no sideways scroll at 390 px (`document.documentElement.scrollWidth`), the 44 px tap targets, the order of the stations top to bottom, nor that two machines don't overlap (`getBoundingClientRect`). It also calls `open_line` twice and passes the viewport only the first time.
- Facts, `drawAll` runs once at load: resizing across 640 px does not redraw.
- The dials live where the allowances are (the Overview's `allowance` section); the picture shows their look. Ollama shows "–" and "no data".

### Done when
- at 390 px, no horizontal scroll, the stations are in the picture's order top to bottom, and no two machines' boxes overlap (browser test)
- with three developers busy, all three sit inside the bay
- every tap target on the phone floor is at least 44 px
- each allowance dial carries its percentage and its mark (75% kept for you, 70% the lead's reserve), asserted from the drawing's attributes; Ollama's says "no data"
- crossing 640 px redraws the right floor
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
