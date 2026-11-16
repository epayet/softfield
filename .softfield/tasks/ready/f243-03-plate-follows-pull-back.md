---
id: f243-03-plate-follows-pull-back
milestone: f243-i-can-t-undo-a-fast
difficulty: 2
depends_on: [f243-01-latest-lane-pull-wins]
files:
  - factory_dashboard/board.py
tests:
  - tests/factory_dashboard/test_board.py
  - tests/factory_dashboard/test_overview.py
---

### Goal
After the owner pulls a card's fast lane lever back, the board's plate and the Overview's "Fast lane:" line stop saying "on its way" at once.

### Context
The picture to build is the board in `.softfield/cards/f243-mockup/take-back.html`, Proposed (without its green marks and notes). Read D3 in `.softfield/cards/f243-i-can-t-undo-a-fast.md`, and F192's D1 and D4 in `.softfield/cards/f192-when-i-click-use-the-fast.md`. Read how `_cards` in `factory_dashboard/board.py` builds `lane_requests` and `lane_asked`, and how `reserve_marked` and `_live_context` in `factory_dashboard/overview.py` use it.

### Done when
- `Card.lane_asked` is None when the latest open `reserve` request on the card asks for what it already is (`on` on a marked card, `off` on one not marked); "first" (an open Approve first) is unchanged
- a card pulled in and back has no plate on the board and isn't named on the Overview's "Fast lane:" line nor marked on its way in Next in line
- a card pulled out and back keeps its plain "fast lane" plate
- the listed `tests:` pass, and fail without the change
