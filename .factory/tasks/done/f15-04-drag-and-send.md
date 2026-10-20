---
id: f15-04-drag-and-send
milestone: f15-reprioritising-tickets
difficulty: 7
depends_on: [f15-03-the-field]
agent: lead
files:
  - factory_dashboard/static/board.js
  - factory_dashboard/templates/board.html
  - factory_dashboard/board.py
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
On the board the owner drags cards into the order they want, sees what moved and from where, and sends the new order once.

### Context
Read `.factory/cards/f15-reprioritising-tickets.md` (D1, D3, D4, D9) and the picture, `.factory/cards/f15-mockup/board-edit.html`: its script is the behaviour to build (`startDrag`, `tick`, `endDrag`, `place`, `outOfPlace`, `work`, `bar`, the Top / Up / Down / Bottom row of `sheet`). `POST /requests` and its guard are in `factory_dashboard/requests.py` (unchanged here); the request is f15-01's `reorder`.
- **Drag by the grip**, in the seed, sprouting, planted and growing stages: the card follows the pointer, a line shows where it lands, the page scrolls near its top and bottom edges, and it lands only inside its own stage. Our own pointer code in `board.js` (D9), no library. The grip has `touch-action: none`; the rest of the card scrolls the page as usual.
- **Without dragging:** a ⋯ button on the card opens "Top / Up / Down / Bottom" for the same moves (keyboard and screen readers use this).
- **What moved** is worked out from the order (`outOfPlace`), not from what was touched: a card put back where it was is not moved. A moved card is dashed orange and says "moved · was #7 · not sent yet".
- **The bar**, fixed at the bottom while something is moved: "3 cards moved. Nothing is sent yet.", Cancel (back to the order shown before) and "Send new order".
- **Send** posts one `reorder` request whose value is the whole open order: the page holds the server's order of all open cards (from `board`, as a data attribute or a JSON block) and a move inside a stage puts the card just before the card it was dropped above in that whole order (after the one above it when dropped last). Then the board is fetched again and shows f15-02's on-its-way marks; the cards stay draggable and a second send replaces the first.
- The header's "Read-only" badge goes; `test_the_page_is_read_only_and_links_to_the_factory_floor` is rewritten to what the page now posts (one kind, `reorder`).
- Reduced motion: no transition on the dragged card.

### Done when
- in Chromium at 390 × 844, dragging the third planted card by its grip above the first makes it `#1`, dashed, "moved · was #3 · not sent yet", and the bar says "1 card moved"
- dragging it back to third removes the mark and the bar
- the ⋯ menu's Top, Up, Down and Bottom do the same moves, by keyboard too
- Cancel restores the order and removes the bar
- Send posts exactly one request, kind `reorder`, whose value lists every open card once with the moved one before the card it was dropped above; afterwards the card reads "on its way · was #3 · at the runner's next pick"
- a card can't be dropped into another stage; a ripe or harvested card has no grip
- a drag near the bottom edge scrolls the page
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
