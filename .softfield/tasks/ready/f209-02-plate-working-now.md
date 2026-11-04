---
id: f209-02-plate-working-now
milestone: f209-i-want-the-ticket-currently-being
difficulty: 3
depends_on: [f209-01-card-at-work]
files:
  - factory_dashboard/board.py
  - factory_dashboard/templates/board.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
A plate at the top of the board says what works now and links to it, wherever its card sits in the line.

### Context
Read D3 in `.softfield/cards/f209-i-want-the-ticket-currently-being.md`. The picture to build is Proposed in `.softfield/cards/f209-mockup/working-now.html`, with its `.board-now` rules and its other states, except the two refresh messages (the next ticket).

`Board.now` in `factory_dashboard/board.py` is built from the cards before `_matches` narrows them, so a search can't hide it. The plate is `#board-now` in `factory_dashboard/templates/board.html`, above `#plots`, with an empty `<span data-fresh>` where the next ticket writes its words. A planner's row links to `/planning/<short key>`, the others as `card_href` does.

Words: a ticket's row "Working now · the lead" or "· a developer"; a review's "Working now · the lead reviews it"; a planner's "Working now · the lead answers you". Elapsed as the Overview's Now shows it, with its `ago` filter.

### Done when
- a live ticket job shows its card's key and title, its ticket, its goal, its agent and attempt, how long it has run and its place, as `#23 in Planted`, linking to the card
- a live review links to the card, and a live planner job links to the card's conversation
- a job waiting for Claude's limit shows "Waits for Claude until HH:MM" and no lit lamp
- with a search that leaves out the card, the plate still shows it
- with no live job, one line says "Nothing is being worked on now" in the same place
- two live jobs give two rows
- the listed `tests:` pass, and fail without the change
