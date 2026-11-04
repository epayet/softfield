---
id: f209-03-field-refreshes-itself
milestone: f209-i-want-the-ticket-currently-being
difficulty: 5
depends_on: [f209-02-plate-working-now]
files:
  - factory_dashboard/static/board.js
  - factory_dashboard/templates/board.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
The open board follows the work by itself: every 10 s it fetches itself and swaps what changed, without disturbing what the owner is doing.

### Context
Read D4, D5 and D6 in `.softfield/cards/f209-i-want-the-ticket-currently-being.md`. The refresh messages are at the end of the plate's states in `.softfield/cards/f209-mockup/working-now.html`.

`factory_dashboard/static/board.js` already redraws after a send (the end of its send handler). Make that one function if `f192-02-board-back-redraws` hasn't yet, and use it, fetching with `{ cache: "no-cache" }`. Also bring each plot's count (its `<b>`, and the `ripe` class) up to date. Plots keep their listeners, so don't replace them. `setUp` builds the grips and ⋯ again only after a swap of `.stages`.

Compare the fetched parts with the last fetched text, not with the page: `setUp` changes the page's copy. `#board-now` and `.stages` swap apart, so a plate's minutes don't restart a card's lamp. `window.liveIdle` is in `factory_dashboard/templates/base.html`.

For browser tests, follow `tests/factory_dashboard/test_line.py`: its `page` fixture fails on any error the page throws. Route `/board` to answer different bodies, and use Playwright's clock rather than waiting 10 s.

### Done when
- a changed answer shows within one tick: the plate, the columns, the plot counts and `#board-line`, with each card's grip and ⋯ working and the phone's picked stage kept
- an unchanged answer leaves the same nodes in place
- no fetch while the page is hidden; one at once when it comes back
- no fetch during a drag, with the ⋯ menu open, or while `window.liveIdle()` is false
- a drag begun during a fetch isn't disturbed by its answer
- with moves not sent, no fetch, the moves stay, and the plate says "Refresh held: your moves aren't sent yet"
- after a failed fetch the plate says "Not updated since HH:MM: the dashboard doesn't answer", and the next good one clears it
- the listed `tests:` pass, and fail without the change
