---
id: f222-01-approved-goes-last
milestone: f222-when-milestones-plans-get-approved-do
agent: lead
difficulty: 3
depends_on: [f222-02-one-order-file, f196-02-ready-needs-a-ticket]
files:
  - runner/requests.py
tests:
  - tests/runner/test_requests.py
---

### Goal
A card whose first plan the owner approves, and a bug they queue, goes to the very end of the queue, whatever its number or its earlier place.

### Context
Read `.softfield/cards/f222-when-milestones-plans-get-approved-do.md`: "What happens today", D1–D3, and `.softfield/adr/45-one-queue-order-no-priority.md` item 3.
- `runner/requests.py`: `_approve_plan` sets the state with `planner.ready_card`; the `QUEUE` branch calls `loop.move_to_ready`, which also serves Try again on a blocked ticket; `_reorder` writes the list and tells the database, since f222-02.
- `_board` reads the working tree, so read it after the squash merge. f196-02 changes the same lines, so that a card with no ticket keeps its state.

### Done when
- approving a plan with tickets on an `idea` or `planning` card puts it last in the list, behind every open card and bug, including one the list didn't name; every other card and bug keeps its order
- it is the approval's one commit: it holds the new state and the new list
- the database copy has the card last once the approval returns
- a replan, a second plan, a plan with no ticket, and a merge move nothing
- a refused approval leaves the list as it was
- queueing a bug from `.softfield/tasks/later/` puts it last; Try again on a bug from `.softfield/tasks/blocked/` leaves its place
- the result says it for a plan that moved: "F222 goes last on the board", and not otherwise
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
