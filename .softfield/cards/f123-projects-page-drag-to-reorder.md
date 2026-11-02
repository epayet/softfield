# Milestone F123: Projects page: drag projects into order, as on the board

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-14.

## Notes
From the terminal session of 2026-10-14 that built ADR 30 (sessions B, C, D).

The Projects page (`/projects`, ADR 30 item 6) orders projects with a number per project and one
"Send new order" (a `project_order` request, applied at the runner's next pick). The owner
doesn't like arrows and reorders by drag, then one send (owner.md, 2026-10-13). Once F15's
drag-and-send exists on the board (f15-04), use the same drag here and drop the numbers.
Mock-up: .softfield/cards/projects-page-mockup/projects.html.

## Plan (lead, 2026-10-27)
The board's drag and send (F15, Reprioritising tickets: f15-04) is on main, so the Projects page can take it now. Only the page changes: the `project_order` request and what the runner does with it stay as they are.

**The picture:** [`f123-mockup/projects-drag.html`](f123-mockup/projects-drag.html), on the three projects of 2026-10-27, with a Today / Proposed switch; the drag works in it.

## Expected outcome
- On the Projects page the owner drags a project by its grip (or uses its ⋯), sees what moved and from where, and sends the new order once, as on the board. The number boxes are gone.

## Done when
- On a phone, open `/projects`, drag coucou to the top: it reads "moved · was #3 · not sent yet" and the bar says "1 project moved". Drag it back: the mark and the bar go. Move it again and press "Send new order": every project reads "on its way · at the runner's next pick". After the runner's next pick the marks go and the order stays.

## Decisions
- **D1 The board's way of moving, on each project.** A grip ⠿ to drag by, a place (#1, #2…) in place of the number box, a ⋯ with Top, Up, Down and Bottom in a `<dialog>` like the board's `#order-sheet`. The page scrolls near its edges while dragging.
- **D2 What is moved is worked out from the order,** as on the board (F15 D3): a project put back is not moved, nor are those it passed. A moved project has the board's dashed hazard edge and "moved · was #N · not sent yet".
- **D3 The board's bar replaces the button.** `#order-bar` at the foot of the screen, shown only while something is out of place: "N projects moved. Nothing is sent yet. · Cancel · Send new order".
- **D4 Sent shows at once, and can be sent again.** After a send, and on any later load while a `project_order` waits, each project reads "on its way · at the runner's next pick" with the dashed hazard edge (the board's, not today's `--opus` one). Today's boxes lock once sent; now the owner can move again and send, which replaces the order on its way (the runner takes the latest), as on the board (F15 D4).
- **D5 One ordering script, shared** (the owner, 2026-10-27: "make it shared for the obviously common logic. the list of projects will grow"). `factory_dashboard/static/order.js`, a plain script loaded before the page's own (no modules, as `board.js`), defines `window.Order` with what both lists do alike, moved out of `board.js`:
  - `Order.outOfPlace(before, after)`: the keys of `after` outside the longest common run, as `board.js`'s today (and `board.py`'s `_out_of_place`).
  - `Order.move(line, key, {before, after})`: a new array with `key` just before `before` or just after `after`; the same array when `key` is either.
  - `Order.menuMove(shown, key, which)`: `which` is `top`, `up`, `down` or `bottom`; gives `{before}` or `{after}` among `shown`, or `null` when it can't move.
  - `Order.drag(grip, node, {among, foot, onDrop})`: a press on `grip` drags `node` (class `dragging`), marks where it lands (`drop-before`/`drop-after` on the others), scrolls near the top and bottom edges (minus `foot()`'s height, the bar), and on release calls `onDrop(key, {before}|{after})` with `node.dataset.key`. `among()` returns the nodes it may land among: one stage's slots on the board, every project on the Projects page.
  - `Order.send(kind, project, value)`: posts to `/requests` with `HX-Request: true`, resolves to true when the dashboard took it.
  What stays in each page's script: what a row looks like (its place, the "moved · was #N · not sent yet" note, the bar's words), stages on the board, and refetching after a send. The CSS for the grip, the ⋯, a dragged row and the drop line is made generic (`.movable`, `.grip`, `.more`, `.dragging`, `.drop-before`, `.drop-after`, not only under `.slot`), so the Projects page uses the same rules.
- **D6 Nothing changes on the server:** the same `POST /requests` with `kind=project_order` and the names in order; `projects.py` keeps `order_on_its_way` and the sort by it.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | shared-order-script | L | 5 | – | D5: `order.js` out of `board.js`, the board unchanged |
| 01 | projects-drag | D | 3 | – | D1, D4: the rows as plates with their place, an order on its way on every row, nothing locked (the number boxes stay) |
| 02 | projects-drag | D | 4 | both 01s | D1 to D4, D6: the grip, the ⋯, the bar and the send on `order.js`; the number boxes go |

Two tickets are numbered 01 because a planner job can't remove a draft from `plan/f123`: `f123-01-projects-drag` was the first plan's single ticket, so it now holds the rows. The rows ticket runs beside the lead's, so the line never waits on the lead alone.

Who builds: shared-order-script is the lead's. It changes the board's working drag, the owner's way of ordering everything, and only its browser tests tell whether it still works. A developer who broke it would leave the lead reviewing and finishing the work. The two Projects page tickets are the developer's: small and unprotected, they follow the board and call the shared script.
