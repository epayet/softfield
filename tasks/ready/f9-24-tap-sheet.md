---
id: f9-24-tap-sheet
milestone: f9-line-polish
depends_on: [f9-23-floor-taps]
difficulty: 3
files:
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/static/factory.js
  - factory_dashboard/templates/_partials/line.html
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
On a phone, tapping a crate opens its card as a sheet at the bottom of the screen, over the floor, with a Close button, instead of below the 1,700 px floor.

### Context
Read `factory_dashboard/templates/_partials/line.html` (`#crate-card` after the floor), the `#crate-card` rules in `factory_dashboard/static/dashboard.css`, and the crate card in `factory_dashboard/static/factory.js` (`showCard`, `hideCard`, the click and keydown listeners). Then the crate-card tests in `tests/factory_dashboard/test_line.py`.
- The owner (2026-10-06): "the tickets are clickable, but on mobile I have to scroll down to see it; it needs a closer box, perhaps where I was".
- Under 640 px the card is fixed to the bottom of the viewport, full width, above the floor and the replay bar. It has a visible Close button (Escape and a tap outside still close it). On desktop it stays where it is.
- The card is built from nodes, never HTML (`showCard`'s comment, f3-F1). Keep it so.

### Done when
- at 390 px, scrolled to the developer bay, tapping a working crate shows the card inside the viewport without scrolling, and its ticket link is visible
- the Close button, Escape and a tap outside each hide it
- at 1440 px the card is under the floor, as before
- the layout check passes at 390 px with the card open (mark the sheet `data-layout="overlay"`)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
