---
id: f296-04-code-plate-on-board-cards
milestone: f296-show-each-milestone-s-net-code
difficulty: 2
depends_on:
  - f296-02-code-lines-on-the-milestone-page
agent: developer
files:
  - factory_dashboard/board.py
  - factory_dashboard/templates/board.html
  - factory_dashboard/static/dashboard.css
  - tests/factory_dashboard/test_board.py
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
A milestone's card on the board carries a small "Code" plate with its net code lines once a ticket of it has merged, so the owner sees which milestones grew the code from the board.

### Context
Read `.softfield/cards/f296-show-each-milestone-s-net-code.md` (D3, D4). The picture to build is `.softfield/cards/f296-mockup/code-lines.html`, "The board", Proposed (the plate, not the calmer variant).
- `code_lines(conn, project)` in `factory_dashboard/queries.py` gives each milestone's (added, removed), by full key; call it once per board, not per card.
- A card is `Card` in `factory_dashboard/board.py` (it has `full_key`, `stage`, `bug`), drawn by `card_link` in `factory_dashboard/templates/board.html`.
- Style the plate after `.card-reserve` in `factory_dashboard/static/dashboard.css`: the floor, the rules' ink and the mono font; no agent or status colour.

### Done when
- a harvested or ripe card whose tickets come to +92 −13 shows "Code +79 lines"
- a planted card with some tickets merged shows its net with "so far"
- a card with nothing counted, and a bug card, shows no plate
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
