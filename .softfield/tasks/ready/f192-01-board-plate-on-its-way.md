---
id: f192-01-board-plate-on-its-way
milestone: f192-when-i-click-use-the-fast
difficulty: 3
depends_on: []
files:
  - factory_dashboard/board.py
  - factory_dashboard/templates/board.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
A card with an open fast lane request shows it on the board at once: "fast lane · on its way · at the runner's next pick", or "leaving the fast lane · on its way".

### Context
The picture to build is the board in `.softfield/cards/f192-mockup/lane-on-its-way.html`, Proposed (without its green marks and notes). Read D1 and D2 in `.softfield/cards/f192-when-i-click-use-the-fast.md`. Follow how `_cards` finds `setting_aside` for the query, and `_reserve_lever` in `factory_dashboard/milestones.py` for the request.

### Done when
- `Card.lane_asked` is `"on"` or `"off"` from the latest open `reserve` request with the card's short key as subject, on a planted card only, and None otherwise, also with a `week` request open
- a card with `lane_asked` `"on"` has the plate on its way, whether or not its doc is marked yet; `"off"` has the leaving plate, its stripe `--ghost`
- a card with no open request has today's plate or none, unchanged
- a request the runner has done (`done` set) shows nothing
- moving a card on the board leaves the plate showing
- the listed `tests:` pass, and fail without the change
