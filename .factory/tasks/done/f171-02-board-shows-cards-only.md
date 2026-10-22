---
id: f171-02-board-shows-cards-only
milestone: f171-there-are-dupliacted-tickets-on-the
difficulty: 3
priority: 3
depends_on: []
files:
  - factory_dashboard/board.py
  - factory_dashboard/milestones.py
tests:
  - tests/factory_dashboard/test_board.py
  - tests/factory_dashboard/test_milestones.py
---

### Goal
The board and the milestones list leave out a milestone row that is no card and has no tickets, so no untitled "F107" or second "F4" shows.

### Context
Read D3 in `.factory/cards/f171-there-are-dupliacted-tickets-on-the.md`, then `_cards` and `_placed` in `factory_dashboard/board.py`, and `milestone_rows` in `factory_dashboard/milestones.py`. Follow the tests in `tests/factory_dashboard/test_board.py` and `tests/factory_dashboard/test_milestones.py` for how they build rows.
- The rows to leave out have no `state` (no card doc was ever synced for them) and no ticket that isn't removed. Softfield's database holds three: `f107`, `f29`, `f44`, each made by a planner job on a card merged away; `f107` shows today in Planted as "F107" with no title.
- Old milestones without a card line still have a state (`done`) and stay; the `bugs` row is handled as today.
- `_placed` keys cards by their short key; with these rows gone two cards no longer share one, so no change there is needed.
- The jobs and their costs stay in the database and on the jobs pages: only the board and the list's rows change.

### Done when
- a milestone row with no state and no tickets is on neither the board nor the milestones list
- a row with no state but a ready ticket is still on both, as today
- a card (a row with a state) with no tickets is still on both, as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 1911
gate_failures: []
tokens: 2515844
```
