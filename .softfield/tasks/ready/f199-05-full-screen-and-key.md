---
id: f199-05-full-screen-and-key
milestone: f199-let-s-improve-the-factory-floor
difficulty: 3
depends_on: [f199-01-the-map]
files:
  - factory_dashboard/templates/floor.html
  - factory_dashboard/static/factory.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
The map's thin bar has a way back to the Overview and a Full screen button, and the phone's map shows how to read it behind a "?".

### Context
The picture: Proposed in `.softfield/cards/f199-mockup/floor.html` (the "?" at the top right of the upright map, the words in `WHAT.legend`, the key on the wide map). The bar is in `factory_dashboard/templates/floor.html`.
- Full screen uses the browser's `requestFullscreen` on the page's root, and `exitFullscreen` for the same button pressed again. A browser without it shows no button.
- The "?" opens `#crate-card`, as `showSeeds` in `factory_dashboard/static/factory.js` does.
- Every colour on the map has its words in that key: three crates, three belts, the tile's fill and two edges.

### Done when
- the bar holds "Overview" (a link to `/`, keeping `?project=`) and "Full screen", at least 44 px each
- pressing Full screen fills the screen, and the map grows to fit with nothing scrolling; pressing it again leaves full screen and the button says so
- with `document.fullscreenEnabled` false, no button shows
- on the upright map, "?" opens the key's words; on the wide map the key is drawn and "?" isn't there
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
