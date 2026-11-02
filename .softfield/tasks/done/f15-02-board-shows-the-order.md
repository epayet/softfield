---
id: f15-02-board-shows-the-order
milestone: f15-reprioritising-tickets
difficulty: 5
depends_on: [f15-01-reorder-request, f110-03-sprouting-is-a-live-conversation]
agent: lead
files:
  - factory_dashboard/board.py
  - factory_dashboard/templates/board.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
Each card on the board shows its place in its stage, and an order the owner has sent shows at once, on its way, with where each moved card was.

### Context
Read `.softfield/cards/f15-reprioritising-tickets.md` (D1, D4) and the picture, `.softfield/cards/f15-mockup/board-edit.html` (Proposed: a card's `#3`, "on its way · was #7 · at the runner's next pick"). In `factory_dashboard/board.py`: `Card`, `_cards` and `board`. In `factory_dashboard/planning.py`: `coming`, the example of drawing an open request as on its way. `metrics.open_requests` in `runner/metrics.py`.
- **Place, not P number:** in the seed, sprouting, planted and growing stages a card shows `#1`, `#2`… (its place in its stage) where it showed `P<n>`. Ripe and harvested cards show neither, as today.
- **An order on its way:** when the project has an open `reorder` request, `board` orders the cards by the latest one's list (unlisted cards after, in their own order), and marks each card the request puts out of place with `on_its_way` and `was` (its place in its stage without the request). "Out of place" is worked out from the two orders, as the mock-up's `outOfPlace` does: the cards outside the longest run the two orders share; a card whose neighbours moved past it is not marked.
- Such a card has a dashed orange edge (the `on-its-way` look of the planning desk) and the line "on its way · was #7 · at the runner's next pick".
- Once the request is done the board is back to the stored priorities, which now give the same order, with no mark.
- No script and no button in this ticket: the page still posts nothing.

### Done when
- a planted card third by priority shows `#3` and no `P`; a ripe and a harvested card show neither
- with an open `reorder` listing F9 before F7 where priorities say F7 first, F9 comes first in its stage, is marked on its way and says "was #2"; F7 is not marked
- two open `reorder` requests: the later one's order shows
- a done `reorder` leaves no mark; a refused one (finished with an error) changes nothing shown
- a card the list doesn't name keeps its relative place after the listed ones
- `q` and `kind` still narrow the cards, and places are counted before narrowing
- on a phone the on-its-way line fits inside the card
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
