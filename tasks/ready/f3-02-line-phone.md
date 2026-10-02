---
id: f3-02-line-phone
milestone: f3
depends_on: [f3-01-factory-line]
difficulty: 5
files:
  - factory_dashboard/static/factory.js
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/_partials/live.html
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
On a phone (under 640 px), the line is a portrait drawing of the same floor, top to bottom, and the allowances are four round dials.

### Context
Read `docs/milestones/f3-line-mockup/LinePhone.dc.html` (the picture: its SVG and the data in its script), `docs/milestones/f3.md` D11, `factory_dashboard/static/factory.js` (the desktop drawing, f3-01) and the browser test in `tests/factory_dashboard/test_line.py` (the pattern to follow).
- **The same document, a second layout in `factory_dashboard/static/factory.js`,** in this order:
  - the field (seeds and planting side by side, planted rows below);
  - the queue hopper;
  - the lead on the left with the reviewers on the right;
  - the developer bay, its machines side by side;
  - checks, with the retry belt going back up to the bay;
  - merged and ripe side by side;
  - the stash.
- **The dials:** each allowance becomes a ring filled to its percentage, with a tick at its mark ("kept for you" at 75%, the lead's reserve at 70%) and its label underneath. Ollama shows "–" and "no data".
- Every tap target is at least 44 px. No sideways scroll at 390 px.

### Done when
- at 390 px the browser test finds the portrait floor (no desktop floor) with one machine per agent, and no horizontal scroll
- at 1280 px it finds the desktop floor
- each dial shows its percentage and its mark (asserted from the drawing's attributes)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
