---
id: f222-02-one-order-file
milestone: f222-when-milestones-plans-get-approved-do
agent: lead
difficulty: 6
depends_on: []
files:
  - runner/order.py
  - runner/tasks.py
  - runner/loop.py
  - runner/requests.py
  - runner/metrics.py
tests:
  - tests/runner/test_order.py
  - tests/runner/test_requests.py
  - tests/runner/test_tasks.py
  - tests/runner/test_metrics.py
---

### Goal
The queue's order lives in one list per project, which the runner picks from and a drag writes, with today's order kept when the list is first made.

### Context
Read `.softfield/cards/f222-when-milestones-plans-get-approved-do.md`: D1, D4, D5, D9, and `.softfield/adr/45-one-queue-order-no-priority.md`.
- `runner/tasks.py`: `task_priority`, `run_order` and `pulls` take a map of short key to number. Give them the list's places: the sort stays place, milestone order, id, with what the list doesn't name after all it names.
- `runner/loop.py`: `_cards` builds that map today, from each card's doc. `sync_cards` keeps the database equal to the docs.
- `runner/requests.py`: `_reorder` and `_board`. The list is rewritten whole at a drag, open keys only. Keep writing the numbers too for now (D9): f222-04 removes them.
- `runner/metrics.py`: add the table as a new last step of `MIGRATIONS`.
- A plan branch may not change the list: `_outside` in `runner/requests.py` already refuses what isn't a draft; check it does.

### Done when
- with a list, the runner's pick and `softfield run --dry-run` take tickets in its order; a bug is placed by its id, a card's tickets by its short key
- what the list doesn't name comes after all it names; a line for a done or missing card is ignored, and dropped at the next write
- with no list and open cards, the first time requests are applied the runner writes one in the order `_reorder` starts from, in a commit of that file alone, and the pick's order is the same before and after
- with no open cards it writes nothing
- it does this for each project, not only Softfield
- a drag's list is the order sent, and the table equals the list after a drag and after a sync
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
