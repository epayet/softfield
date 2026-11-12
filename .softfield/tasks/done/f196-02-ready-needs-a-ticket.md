---
id: f196-02-ready-needs-a-ticket
milestone: f196-f58-is-in-progress-but-has
agent: lead
difficulty: 3
depends_on: []
files:
  - runner/requests.py
tests:
  - tests/runner/test_requests.py
---

### Goal
Approving a plan makes a card ready only when the card has a ticket, so the board never shows a planted card with nothing to run. Any card already in that state goes back to being an idea.

### Context
Read `.softfield/cards/f196-f58-is-in-progress-but-has.md`: "What happens today" and D1.
- `runner/requests.py`: `_approve_plan` calls `planner.ready_card` on every plan that isn't building. `_has_tickets` shows how a card's tickets are found. `_drop_seed` refuses a card that isn't an idea.
- `factory_dashboard/board.py`: `_milestone_stage` draws an idea as a seed, or as sprouting while its thread is open; anything past planning is planted.
- `factory_dashboard/thread.py`: `_header` offers Remove seed only on an idea.
- A plan that adds tickets, a replan, and a building card behave as they do today. So does a second plan on a card that already has tickets.

### Done when
- approving a plan with only a doc or a mock-up, on a card with no ticket in any folder of `.softfield/tasks/`, merges the drafts and leaves the card's state as it was
- approving a plan with a ticket, or on a card that has one, sets it ready as today
- the result still says "queued nothing" for a plan with no tickets
- in the same ticket, any non-done doc in `.softfield/cards/` whose state is `ready` and that has no ticket in any folder has its state edited to `idea`. Today that is only F58's, unless the owner has removed it. If it's gone, say so in the commit and change nothing
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
