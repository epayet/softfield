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
Main already holds part of this; build on it, don't redo it:
- The bar is `header.map-bar` in `factory_dashboard/templates/floor.html` (lines 7–11). It already has the "‹ Overview" link (`a.map-back`, `href="/{{ q }}"`), but its CSS in `factory_dashboard/static/dashboard.css` (lines 710–716) gives it `min-height: 36px`, short of 44.
- The wide map's key is already drawn: `legend()` in `factory_dashboard/static/factory.js` (lines 778–793), called from `drawMap` (line 860) when the table has a `legend` box. `TALL.legend` is `null` (line 564), so the upright map draws nothing yet.
- The "?" uses the map card that f199-04 built, not `#crate-card`: a `<g>` marked by `what(g, "legend")` (line 840) is opened on tap by the click listener (line 1276) through `showMapCard`, whose `key in WHAT` branch shows `WHAT.legend` (line 820), the key's words. The picture is in `.softfield/cards/f199-mockup/floor.html` lines 829–834: a 26×17 `seedplot` rect at x 330, y 2 with a "?" title text, drawn only when the table has no legend.
- Every colour on the map has its words in the key: three crates, three belts (carrying, faint "today", the red one coming back), the tile's fill and two edges (orange started, dashed bug). `WHAT.legend` already says all of them; `legend()` draws the crates and two belts only.
- Full screen uses `document.documentElement.requestFullscreen()`, and `document.exitFullscreen()` when the same button is pressed again; `document.fullscreenElement` says which; the `fullscreenchange` event fires both ways (Escape too). A browser where `document.fullscreenEnabled` is false shows no button. `.map-page` is already `position: fixed; inset: 0` and `.map` fills the rest of the column, so the map grows with the window.
- Tests: the map's browser tests are at the end of `tests/factory_dashboard/test_line.py` (from line 3179): `open_map(page, line_client, UPRIGHT or WIDE_SCREEN)`, `MAP`, and `test_tapping_the_queue_station_shows_a_link_to_queue` (line 3472) as the example to copy. To make `fullscreenEnabled` false, run `page.add_init_script` defining it as false on `Document.prototype` before `open_map`.

### Done when
- the bar holds "Overview" (a link to `/`, keeping `?project=`) and "Full screen", each at least 44 px tall in a browser test
- pressing Full screen makes `document.fullscreenElement` set and the button's words change (e.g. "Exit full screen"); pressing it again clears it and the words go back; the page doesn't scroll either way
- with `document.fullscreenEnabled` false, no Full screen button is in the bar
- on the upright map (`UPRIGHT`), a "?" is drawn and a tap on it shows `#map-card` with "How to read the map"; on `WIDE_SCREEN`, `[data-legend]` is drawn and there is no "?"
- the wide key also draws the faint "today" belt and a tile's fill, orange edge and dashed edge, each with its words
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
