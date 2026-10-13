---
id: f15-06-card-actions
milestone: f15-reprioritising-tickets
difficulty: 3
depends_on: [f15-05-replan, f73-02-set-aside-button]
files:
  - factory_dashboard/templates/board.html
  - factory_dashboard/board.py
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
A card's ⋯ menu on the board also leads to what the owner does with that card: its conversation, its sign-off, setting it aside, and its own page.

### Context
Read `docs/milestones/f15-reprioritising-tickets.md` (D7) and the picture, `docs/milestones/f15-mockup/board-edit.html` (the `sheet` function's buttons). In `factory_dashboard/templates/board.html`: the card's ⋯ menu f15-04 built. In `factory_dashboard/templates/proposal.html`: `#set-aside-button`, the example of the set-aside request (f73-02).
- Under the move row, the menu lists, as links at least 44 px tall, each keeping the page's project query:
  - "Open its conversation" to `/planning/<short key>`, for a milestone's card that has a planning thread (give the card that fact from `_cards` in `factory_dashboard/board.py`); not for a bug.
  - "Read the review and sign off" to the card's page at `#review`, on a ripe milestone only.
  - "Open the card" to the link the card has today.
- "Set aside", on a seed or sprouting card with a thread: a button posting the `archive` request for the thread, value `on`, as f73-02's button does; it shows on its way at once and can't be pressed twice.
- Planting is not on the board: it stays on the planning desk (D7).

### Done when
- a sprouting card's menu has "Open its conversation" to its thread and a "Set aside" button whose values are kind `archive`, the thread and `on`
- a seed with no thread has neither; a bug's menu has no conversation link
- a ripe milestone's menu has "Read the review and sign off" ending in `#review`; a planted card's has not
- every card's menu has "Open the card" with the card's own link
- in Chromium, pressing "Set aside" posts one request and the button is disabled
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
