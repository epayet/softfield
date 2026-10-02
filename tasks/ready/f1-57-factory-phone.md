---
id: f1-57-factory-phone
milestone: f1
depends_on: [f1-54-factory-replay]
difficulty: 6
files:
  - factory_dashboard/static/factory.js
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/line.html
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
On a phone, the factory line fits the screen without sideways scrolling, reads in words too, and keeps Play within reach.

### Context
Read `docs/milestones/f1.md` D10 ("What the page shows"). Follow f1-53's and f1-54's work: `factory_dashboard/static/factory.js`, `factory_dashboard/templates/line.html` and the browser tests in `tests/factory_dashboard/test_line.py`. Open `docs/milestones/f1-factory-mockup.html` in a browser at 400 px wide.
- **Under 640 px, a portrait floor** that fills the width: the queue at the top, the developer bay and the lead side by side, Checks, Merged, then the shadow agent; developers stacked one under another in the bay, each with its name, ticket and time, LOCAL/CLOUD plate and rating gauge inside; machine names above the machines. No "last / next" text on the drawing.
- **"The same, in words"** below the floor, folded by default: each station as a card (Queue with its tickets as chips in run order, each machine with what it's working on, Checks, Merged newest first) and the belts between them with their last and next trip.
- **The Play bar sticks** to the bottom of the screen while the floor is on screen: the slider on one row, Play, ◀, ▶ and the speed on the next.
- **Taps:** a tap on a crate or a chip opens its details and outlines its dependencies until a tap elsewhere clears both; a tap on a belt shows its last and next trip. Hover never sticks on touch.
- **Text stays readable:** no drawing text below 10 px on a 400 px screen.

### Done when
- at 400 × 860 the floor has no horizontal scroll and every machine and station is inside it (browser test)
- tapping a crate then the page title leaves no outline and no details open
- the Play bar is inside the viewport after scrolling to the bottom of the floor
- the list in words names each station and lists the queue in run order
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
