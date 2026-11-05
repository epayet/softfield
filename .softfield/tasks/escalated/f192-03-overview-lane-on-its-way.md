---
id: f192-03-overview-lane-on-its-way
milestone: f192-when-i-click-use-the-fast
difficulty: 4
depends_on: [f192-01-board-plate-on-its-way]
files:
  - factory_dashboard/board.py
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/allowance.html
  - factory_dashboard/templates/_partials/queue.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview shows a fast lane request at once: the "Fast lane:" line names the card, on its way, and Next in line already puts its tickets in the lane's bay.

### Context
The picture to build is the Overview in `.softfield/cards/f192-mockup/lane-on-its-way.html`, Proposed (without its green marks and notes). Read D4 in `.softfield/cards/f192-when-i-click-use-the-fast.md`. `reserve_marked` is in `factory_dashboard/board.py`, `fast_lane` and `_live_context` in `factory_dashboard/overview.py`. See `test_the_marked_cards_are_named_once_under_claude_s_meters` for how a marked card is set up.

### Done when
- a card with `lane_asked` `"on"` is named in `#reserve-cards` with "on its way"; one with `"off"` with "leaving · on its way"; a marked card with no request as today
- with `"on"` on the only card, the lane's bay shows its tickets, each row saying "on its way"
- with `"off"`, its tickets are out of the bay and back among the rest
- the same on `/` and `/live`
- the listed `tests:` pass, and fail without the change

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: task-tests)
attempts: 3
tokens: 7731086
logs: .softfield/var/runs/20261104-220212/f192-03-overview-lane-on-its-way
```
