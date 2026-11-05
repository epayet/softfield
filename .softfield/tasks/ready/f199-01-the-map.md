---
id: f199-01-the-map
milestone: f199-let-s-improve-the-factory-floor
agent: lead
difficulty: 8
depends_on: [f132-05-floor-every-project]
commands: [mv]
files:
  - factory_dashboard/line.py
  - factory_dashboard/templates/floor.html
  - factory_dashboard/static/factory.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
A new page, `/floor`, shows the whole factory from above on a grid, every machine, belt and pile on one screen with no scrolling, on a phone held upright and on a wide screen alike.

### Context
The picture to build: Proposed in `.softfield/cards/f199-mockup/floor.html`; its script's `WIDE`, `TALL`, `drawMap`, `mapBelt` and `mapMachine` are the starting point, its CSS under "the map" too. Decisions D1–D5 in `.softfield/cards/f199-let-s-improve-the-factory-floor.md`.
- `live_line` in `factory_dashboard/line.py` gives the document; add `field.planted` (D4) from `board` in `factory_dashboard/board.py`, as `live_line` already reads its stage counts.
- `factory_dashboard/static/factory.js`: `drawFloor`, `drawAll`, `morph` and the replay code. The map draws through `morph`, so an unchanged node keeps its animation. `drawFloor` draws `svg#map` when the page has one, else the old floors, which stay on the Overview until f199-03.
- Keep what the document says: `wait` draws the clog sign on its machine and in the top line, the checks light flashes as it does today, F132's project plate stays on a crate when there are several projects.
- Ornament (ticks, stripes, grid, plate headers) uses ink, rules and the hazard stripe only, as `.softfield/cards/f88-add-to-lead-memory-that-new.md` says. Nothing on the page or in its code names a game.
- If the ticket f9-27-phone-rows-compact is still in the ready folder, move it to the later folder with `mv`: this card replaces the drawing it changes. Add a line saying so under f9-27 in `.softfield/cards/f9-line-polish.md`.

### Done when
- `/floor` at 390 × 700, 844 × 390 and 1440 × 900, light and dark: nothing scrolls, and every station and machine of the document is on screen (a browser test)
- at 390 × 700 the upright table is drawn, at 844 × 390 and 1440 × 900 the wide one; turning the phone redraws it
- no label overlaps another or leaves its station, in either table, as `test_no_phone_label_overlaps_another_or_leaves_its_station` checks the phone floor
- every planted card is one tile, in the board's order: 57 cards, 57 tiles; a card with 2 of 4 tickets merged is half filled, and a card with a ticket started has the orange edge
- a replay's document, which has no `field.planted`, draws `field.rows` as tiles without an error
- a job working: the top line names its machine, what it works on and its minutes. A wait: the sign, the wait's words, and the machine clogged
- an unchanged document leaves every node in place, as `test_an_unchanged_document_leaves_every_node_of_the_floor_in_place` checks today
- the Overview's floor still draws as before
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
