---
id: f265-03-board-catches-up
milestone: f265-the-factory-now-section-in-planning
difficulty: 2
depends_on: [f265-02-live-parts-catch-up]
files:
  - factory_dashboard/static/board.js
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
The board catches up as soon as the owner stops scrolling or typing, and its plate line says when its refresh is held, so a moved ticket never waits for a reload.

### Context
Read the owner's board note under Notes, and D5, D6 and D8 in `.softfield/cards/f265-the-factory-now-section-in-planning.md`.
- `factory_dashboard/static/board.js`: `follow` (every 10 s, and on `visibilitychange`), `busy`, and `sayFresh` with its `EVERY` words. f265-02 added the `live-resume` event on `document` in `factory_dashboard/templates/base.html`: read where it is sent.
- `follow` also runs on `live-resume`, the way it runs on `visibilitychange`.
- `sayFresh` gets one more state, after unsent moves and a failed fetch: when the last turn of `follow` was skipped because `window.liveIdle()` was false, the words are "Refresh held while you scroll or type", with the same `stale` class as the others; a turn that goes through brings back `EVERY`. A skip for a drag or the ⋯ menu changes nothing.
- Follow the existing browser tests around `test_no_fetch_while_live_idle_says_no` in `tests/factory_dashboard/test_board.py`.

### Done when
- in the browser: with `window.liveIdle` made to say no, a card moved in the database doesn't show and the plate's `.fresh` reads "Refresh held while you scroll or type"; when liveIdle says yes again and `live-resume` is sent on `document`, the card shows in its new place within 2 s, without a reload, and the line reads "refreshes every 10 s"
- with moves not sent, the line still reads "Refresh held: your moves aren't sent yet", and `live-resume` fetches nothing
- the listed `tests:` pass, and the new ones fail without the change
- all gates pass (see `docs/workflow.md`)
