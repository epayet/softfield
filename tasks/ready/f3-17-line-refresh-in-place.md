---
id: f3-17-line-refresh-in-place
milestone: f3
depends_on: []
agent: lead
difficulty: 5
files:
  - factory_dashboard/static/factory.js
  - factory_dashboard/templates/_partials/line.html
  - factory_dashboard/line.py
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
The floor refreshes in place: nothing flickers every 5 s, and a carrying belt keeps marching across refreshes.

### Context
Read `factory_dashboard/templates/_partials/line.html`, `factory_dashboard/static/factory.js` (`drawAll`, `drawFloor`, `draw`, `drawPhone`, `_prev`), `line_live` in `factory_dashboard/line.py`, the motion rules in `factory_dashboard/static/dashboard.css` (`roll`, `smoke`, `flash-green`) and the browser tests in `tests/factory_dashboard/test_line.py`. Test-first.
- **Why (owner, 2026-10-03):** "the factory on the homepage refreshes every 5 seconds and gets flicky every 5 seconds", and "factory lines currently don't move".
- **What causes it:**
  - `#line-live` is swapped whole (`hx-swap="outerHTML"`) from `/line/live` every 5 s.
  - The script then empties both SVGs (`svg.replaceChildren()`) and draws them again.
  - So every node is new, every CSS animation starts over, and the frame between the two shows nothing.
- **What to build:**
  - The floor's section stays in the page; only its document changes. Fetch the document (JSON) every 5 s under the same `window.liveIdle()` condition as the other live parts, and keep pausing while a replay plays.
  - Draw again only when the document differs from the one drawn. When it does differ, a node whose part didn't change stays the same node, so its animation runs on. Keying the groups by their existing `data-belt`, `data-machine` and `data-crate` attributes is one way.
  - Keep a JSON route for the document. `line_live` may answer JSON when asked with `Accept: application/json`, as `/line/replay` does.
- **f4-21's finding is folded in here:** `_prev` starts empty, so the first draw treats any non-zero checks count from earlier today as a new result and flashes the checks light. The first draw sets the baseline, and only a later refresh may flash.
- This is the worked example for factory.js: f3-19 and f3-20 build on it, so keep the drawing functions' signatures.

### Done when
- a browser test: after two refreshes with an unchanged document, the floor's nodes are the same objects (a marker set on one survives)
- a browser test: a carrying belt's rollers have a running animation after a refresh, and its `animation` was not restarted (the same node)
- a browser test: opening the page with a non-zero checks count today doesn't flash the checks light; a later refresh with a higher count does
- the replay still pauses the live refresh, and "Back to live" draws the live document again
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
