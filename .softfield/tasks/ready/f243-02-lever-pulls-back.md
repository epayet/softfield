---
id: f243-02-lever-pulls-back
milestone: f243-i-can-t-undo-a-fast
difficulty: 3
depends_on: [f243-01-latest-lane-pull-wins]
files:
  - factory_dashboard/milestones.py
  - factory_dashboard/overview.py
  - factory_dashboard/templates/milestone.html
  - factory_dashboard/templates/_partials/allowance.html
tests:
  - tests/factory_dashboard/test_milestones.py
  - tests/factory_dashboard/test_overview.py
---

### Goal
A fast lane lever on a card's page, or a "use reserve" lever on the Overview, pulled by mistake can be pulled again at once to take it back, before the runner takes it.

### Context
The picture to build is `.softfield/cards/f243-mockup/take-back.html`, Proposed (without its green marks and notes). Read D2 in `.softfield/cards/f243-i-can-t-undo-a-fast.md`. Read `_reserve_lever` in `factory_dashboard/milestones.py`, `reserve_switches` in `factory_dashboard/overview.py`, and the two `lever` buttons in `factory_dashboard/templates/milestone.html` and `factory_dashboard/templates/_partials/allowance.html`.

### Done when
- `ReserveLever.asked` and `Switch.asked` are the latest open request's value only when it differs from the state as it stands (the card's mark, the switch's `until`); otherwise None
- neither lever is ever `disabled` because a request is open
- the first pull draws the lever on its way and posts the other value; a pull while on its way draws it plain at once and posts the value as it stands; a third pull asks again
- while on its way the lever's `title` ends with "pull again to take it back"
- after a pull and a pull-back, a reload draws the lever plain
- the listed `tests:` pass, and fail without the change
