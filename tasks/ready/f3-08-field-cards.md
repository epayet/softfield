---
id: f3-08-field-cards
milestone: f5-board
depends_on: [f3-01-factory-line, f5-15-board-data]
difficulty: 3
files:
  - factory_dashboard/line.py
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
The line's field shows the board's cards: seeds (ideas and set-aside bugs), planting (sprouting cards), planted and growing rows, ripe and the stash, with the same counts as the board.

### Context
Read `docs/milestones/f3.md` D11 ("The field counts come from the board"), `factory_dashboard/board.py` (`board`, f5-15) and `factory_dashboard/line.py` (`live_line`'s field, which f3-01 built from milestones and set-aside tickets alone).
- Replace the field's counts and names with the board's stages: seed → seeds, sprouting → planting, planted and growing → rows, ripe → ripe, harvested → stash. Same document keys, so the drawing doesn't change.

### Done when
- for a fixture with two ideas, a set-aside bug, a sprouting card, a growing card and a harvested one, each field station's count equals the board's for its stage
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
