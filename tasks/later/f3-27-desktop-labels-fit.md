---
id: f3-27-desktop-labels-fit
milestone: f3
depends_on: []
difficulty: 4
files:
  - factory_dashboard/static/factory.js
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
Every word on the desktop floor reads whole: no label runs into another, over a box it doesn't belong to, or off the edge of the floor, as the phone floor already guarantees.

### Context
Read the desktop drawing in `factory_dashboard/static/factory.js` (the belt paths and their `at` label positions, `machine`, the checks, merged, ripe and stash stations) and, in `tests/factory_dashboard/test_line.py`, `test_no_phone_label_overlaps_another_or_leaves_its_station` with its `LABELS` script, `overlaps` and `inside`: the pattern to follow, on `svg#floor` instead of `svg#floor-phone`. The picture: `docs/milestones/f3-line-mockup/Line.dc.html`.
- **What the review saw (f3-22, `var/shots/f3-22/desktop-1440-dark-line-live.png`, at 1440 px):**
  - "ruff · mypy / tests · gates" spills out of the left side of the Checks box;
  - "merged · 20" runs into the Checks box, and "lead tickets · 4" sits across its own belt;
  - "your sign-off" is cut by the floor's right edge;
  - Copilot's "off: checkpoint, …" and the plates' "rated …" are cut short inside their boxes.
- Move labels or shorten words; don't shrink the font below today's smallest. Keep every station, belt and machine id, and f3-17's rule (the same nodes across refreshes).

### Done when
- a browser test, light and dark, at 1440 px under reduced motion: on `svg#floor`, no label overlaps another, every label is inside the floor, a label with a frame is inside it, and no label overlaps another machine's shapes
- the same test passes at 1280 px
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
