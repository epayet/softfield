---
id: f192-03-fix-back-redraw-stage-and-tests
milestone: f192
difficulty: 4
depends_on: []
files:
  - factory_dashboard/static/board.js
  - tests/factory_dashboard/test_board.py
tests:
  - tests/factory_dashboard/test_board.py
finding: f192-02-board-back-redraws
---

### Goal
Make the back-button redraw of the board (`pageshow` with `persisted`) read each card's stage by its key and prove, in tests, that the field shows what the server holds now.

### Context
`factory_dashboard/static/board.js`: the `pageshow` handler builds `sent` with `stages[i]?.[1]`, the stage of the i-th slot of the fresh page, while `line` is the order from before. When the fresh page's slot order differs from `line`, a card gets another card's stage. The handler also keeps the old `line` and never reads the fresh `board-line`.

`tests/factory_dashboard/test_board.py`, the three `test_pageshow_*` tests:
- the `persisted: true` test only counts grips and menus, which exist before the pageshow too; it never shows that new server data reaches the field.
- `test_pageshow_with_moved_card_fetches_and_keeps_moves` says "fetches" in its name while its docstring says nothing is fetched, and it asserts no fetch count.

### Done when
- Each card's stage after a back redraw comes from the slot with the same key, whatever the order of the fresh page.
- A test changes the database after the page opened (a card's fast lane lever, or its stage), fires `pageshow` with `persisted: true`, and asserts the changed content is on the card (its text, class or stage), not only that grips exist.
- A test with unsent moves asserts that no board request is made and the order stays; its name and docstring agree.
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
