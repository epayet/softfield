---
id: f192-02-board-back-redraws
milestone: f192-when-i-click-use-the-fast
difficulty: 4
depends_on: [f192-01-board-plate-on-its-way]
files:
  - factory_dashboard/static/board.js
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
Coming back to the board with the back button shows the field as it is now, so a fast lane lever just pulled is already on its card.

### Context
Read D3 in `.softfield/cards/f192-when-i-click-use-the-fast.md`. The steps are the ones at the end of the send handler in `factory_dashboard/static/board.js` (fetch the page, replace `#field .stages` and `#board-line`, `show`, `setUp`): one function for both, fetching with `{ cache: "no-cache" }` on this path. On a failed fetch, leave the page as it is, with no reload.

A browser test, as in `tests/factory_dashboard/test_line.py` (its `page` fixture fails on any error the page throws, and it serves `/static/` from disk). A real back in a test may not come from the browser's memory, and would pass without the change, so route `/board` to answer a second body with a plate the first lacks, and dispatch `new PageTransitionEvent("pageshow", {persisted: true})`.

### Done when
- a `pageshow` with `persisted` true draws the second body's field, with each card's grip and ⋯ working
- a `pageshow` with `persisted` false on a normal load fetches nothing
- with a card moved and not sent, that `pageshow` fetches nothing and the moves stay
- the listed `tests:` pass, and fail without the change
