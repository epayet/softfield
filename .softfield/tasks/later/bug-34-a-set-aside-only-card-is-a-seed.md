---
id: bug-34-a-set-aside-only-card-is-a-seed
milestone: bugs
difficulty: 3
depends_on: []
area: factory
priority: 62
finding: f110-i-don-t-understand-why-there-F2
files:
  - factory_dashboard/board.py
tests:
  - tests/factory_dashboard/test_board.py
  - tests/factory_dashboard/test_line.py
---

### Goal
A card whose only tickets are set aside shows as a seed on the board, not as planted with tickets ready.

### Context
Read `def _milestone_stage` in `factory_dashboard/board.py`, `def _field` in `factory_dashboard/line.py`, and `test_only_set_aside_tickets_keeps_milestone_out` in `tests/factory_dashboard/test_line.py`, which asserts only where such a card isn't on the line's field.
- Today it is "Planted: tickets ready" on the board though none is ready, and on no part of the field. Call it a seed on the board, its words "idea or set aside" (as the board's other stages have words in `WORDS` at the top of `factory_dashboard/board.py`), and pin where it is in both places.

### Done when
- a building card whose tickets are all in `later/`: the board shows it among the seeds, with "set aside" in its words
- the same card on the line's field: the test asserts the part it is drawn in, not only where it isn't
- a card with one ready ticket and one set aside is planted, as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
