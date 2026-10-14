---
id: f5-04-cards
milestone: f5-board
depends_on: []
agent: lead
difficulty: 5
files:
  - runner/milestone.py
  - runner/metrics.py
  - runner/loop.py
  - docs/task-format.md
tests:
  - tests/runner/test_milestone.py
  - tests/runner/test_metrics.py
---

### Goal
A milestone doc can carry a card's state, priority and area, and the runner records them in the database for the board.

### Context
Read `docs/adr/19-feature-board.md` items 1 and 3, D4 in `docs/milestones/f5-board.md`, `runner/milestone.py` (`milestone_doc`, `_section`), `runner/metrics.py` (`MIGRATIONS`, how milestones are upserted) and `docs/milestones/f5-board.md`'s header (the format, already written). Test-first.
- `_V5` adds `milestones.state`, `milestones.priority` and `milestones.area`. If f5-01 has already added `_V5`, add `_V6`.
- The runner syncs every doc in `docs/milestones/` at session start, as `sync_tickets` does for tickets: a card with no tickets yet (an idea) gets its row too.
- Document the header line in `docs/task-format.md` ("Milestone keys").

### Done when
- `card()` reads "**State:** building · **Priority:** 2 · **Area:** factory", derives `done` from "Status: done", defaults the priority to 100, and the area to factory for `f…` keys and product for `m…` keys
- an idea doc with no tickets gets a milestones row with its state and priority
- `uv run runner check-all --task f5-04-cards` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
