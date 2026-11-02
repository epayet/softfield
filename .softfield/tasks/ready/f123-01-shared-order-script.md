---
id: f123-01-shared-order-script
milestone: f123-projects-page-drag-to-reorder
agent: lead
difficulty: 5
depends_on: []
files:
  - factory_dashboard/static/order.js
  - factory_dashboard/static/board.js
  - factory_dashboard/templates/board.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
What the board does to order a list (what is out of place, a move, the menu's moves, the drag, the send) lives in one shared script that the Projects page can use next, and the board works exactly as before.

### Context
Read `.softfield/cards/f123-projects-page-drag-to-reorder.md`, D5: it names `window.Order`'s functions and their arguments. Take them out of `factory_dashboard/static/board.js` (`outOfPlace`, `move`, the `moves` table, the drag from `target` to `startDrag`, the `fetch` in the send). The rest stays in the board's script: stages, `work`, the slots, the sheet, refetching after a send.
- `factory_dashboard/static/order.js` is a plain script, no modules: `factory_dashboard/templates/board.html` loads it with `static(...)` just before the board's script.
- `_out_of_place` in `factory_dashboard/board.py` is the server's twin of `outOfPlace`: leave it as it is.
- In `factory_dashboard/static/dashboard.css`, "Moving cards": the rules for the grip, the ⋯, a dragged row and the drop line move from `.slot …` to class names any list can carry (D5's list). Keep the board's look; the `#field .card.moved` and `.card-way` rules stay the board's.
- The next ticket (f123-02) builds the Projects page on this, with every project a row in one list and `data-key` its name.

### Done when
- every test in `tests/factory_dashboard/test_board.py` passes unchanged, the drag, menu, send and edge-scroll tests included
- a new browser test loads only the shared script on a blank page with a three-item list and checks `Order.outOfPlace`, `Order.move` and `Order.menuMove` (a put-back item is not moved; `top` on the first item gives `null`)
- `factory_dashboard/static/board.js` no longer defines its own `outOfPlace`, drag or `fetch` to `/requests`
- the listed `tests:` pass, and the new test fails without the change
- all gates pass (see `docs/workflow.md`)
